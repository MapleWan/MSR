"""sync 命令处理器 — 同步配置到目标 IDE

实现 rules、skills、MCP 三种配置类型的同步逻辑，
支持按 IDE、scope、type、name、version 参数精确控制同步范围。
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import click

from msr_sync.adapters.base import BaseAdapter
from msr_sync.adapters.registry import resolve_ide_list
from msr_sync.constants import ConfigType, MCP_CONFIG_FILE
from msr_sync.core.exceptions import (
    ConfigNotFoundError,
    ConfigParseError,
    RepositoryNotFoundError,
)
from msr_sync.core.frontmatter import strip_frontmatter
from msr_sync.core.repository import Repository


def sync_handler(
    ide: tuple = ("all",),
    scope: str = "global",
    project_dir: Optional[str] = None,
    config_type: Optional[str] = None,
    name: Optional[str] = None,
    version: Optional[str] = None,
    base_path: Optional[Path] = None,
) -> None:
    """执行 sync 命令逻辑。

    将统一仓库中的配置同步到目标 IDE。支持按 IDE、scope、type、name、version
    参数精确控制同步范围。

    Args:
        ide: 目标 IDE 元组，如 ('trae', 'qoder') 或 ('all',)
        scope: 同步层级，'project' 或 'global'
        project_dir: 项目目录路径字符串，scope 为 'project' 时使用
        config_type: 配置类型过滤（rules/skills/mcp），None 表示全部
        name: 配置名称过滤，None 表示全部
        version: 指定版本，None 表示最新版本
        base_path: 仓库根目录路径（用于测试注入）
    """
    repo = Repository(base_path=base_path)

    # 确保仓库已初始化
    if not repo.exists():
        click.echo("❌ 统一仓库未初始化，请先执行 `msr-sync init`")
        raise SystemExit(1)

    # 解析项目目录
    resolved_project_dir: Optional[Path] = None
    if scope == "project":
        if project_dir is not None:
            resolved_project_dir = Path(project_dir)
        else:
            resolved_project_dir = Path.cwd()

    # 解析目标 IDE 列表
    adapters = resolve_ide_list(ide)

    # 确定要同步的配置类型
    if config_type is not None:
        types_to_sync = [config_type]
    else:
        types_to_sync = [
            ConfigType.RULES.value,
            ConfigType.SKILLS.value,
            ConfigType.MCP.value,
        ]

    # 获取仓库中的配置列表
    try:
        all_configs = repo.list_configs()
    except RepositoryNotFoundError:
        click.echo("❌ 统一仓库未初始化，请先执行 `msr-sync init`")
        raise SystemExit(1)

    total_synced = 0

    for ct in types_to_sync:
        configs = all_configs.get(ct, {})

        # 按名称过滤
        if name is not None:
            if name in configs:
                configs = {name: configs[name]}
            else:
                click.echo(f"⚠️ 未找到 {ct} 类型的配置: {name}")
                continue

        if not configs:
            continue

        for config_name, versions in configs.items():
            # 在同步前显示将要使用的版本
            if version is not None:
                display_ver = version
            else:
                display_ver = versions[-1] if versions else "?"
            click.echo(f"\n📌 {ct}/{config_name} — 使用版本: {display_ver}")

            for adapter in adapters:
                try:
                    count = _sync_config(
                        repo=repo,
                        adapter=adapter,
                        config_type=ct,
                        config_name=config_name,
                        version=version,
                        scope=scope,
                        project_dir=resolved_project_dir,
                    )
                    total_synced += count
                except ConfigNotFoundError as e:
                    click.echo(f"❌ {e}")
                except Exception as e:
                    click.echo(
                        f"❌ 同步 {ct}/{config_name} 到 {adapter.ide_name} 失败: {e}"
                    )

    if total_synced > 0:
        click.echo(f"\n✅ 同步完成: 共 {total_synced} 项")
    else:
        click.echo("\n⚠️ 没有配置被同步")


def _sync_config(
    repo: Repository,
    adapter: BaseAdapter,
    config_type: str,
    config_name: str,
    version: Optional[str],
    scope: str,
    project_dir: Optional[Path],
) -> int:
    """同步单个配置到单个 IDE。

    根据配置类型分发到对应的同步逻辑。

    Args:
        repo: 仓库实例
        adapter: IDE 适配器
        config_type: 配置类型
        config_name: 配置名称
        version: 指定版本，None 表示最新
        scope: 同步层级
        project_dir: 项目目录路径

    Returns:
        成功同步的条目数（0 或 1）
    """
    # 解析实际使用的版本号（用于提示信息）
    resolved_version = version
    if resolved_version is None:
        from msr_sync.core.version import get_latest_version
        config_dir = repo.base_path / repo._resolve_config_dir(config_type) / config_name
        resolved_version = get_latest_version(config_dir)

    if config_type == ConfigType.RULES.value:
        return _sync_rule(repo, adapter, config_name, version, resolved_version, scope, project_dir)
    elif config_type == ConfigType.MCP.value:
        return _sync_mcp(repo, adapter, config_name, version, resolved_version)
    elif config_type == ConfigType.SKILLS.value:
        return _sync_skill(repo, adapter, config_name, version, resolved_version, scope, project_dir)
    return 0


# ============================================================
# Rules 同步逻辑 (Task 11.2)
# ============================================================


def _sync_rule(
    repo: Repository,
    adapter: BaseAdapter,
    rule_name: str,
    version: Optional[str],
    resolved_version: Optional[str],
    scope: str,
    project_dir: Optional[Path],
) -> int:
    """同步单个 rule 到目标 IDE。

    从仓库读取 rule 内容，剥离原始 frontmatter，添加 IDE 特定头部，
    写入目标路径。全局级同步时，若 IDE 不支持全局 rules，输出警告并跳过。

    Args:
        repo: 仓库实例
        adapter: IDE 适配器
        rule_name: rule 名称
        version: 指定版本
        scope: 同步层级
        project_dir: 项目目录路径

    Returns:
        成功同步的条目数（0 或 1）
    """
    # 全局级同步时检查 IDE 是否支持全局 rules
    if scope == "global" and not adapter.supports_global_rules():
        click.echo(f"⚠️ {adapter.ide_name} 不支持全局级 rules，已跳过")
        return 0

    # 读取 rule 内容
    raw_content = repo.read_rule_content(rule_name, version)

    # 剥离原始 frontmatter
    stripped_content = strip_frontmatter(raw_content)

    # 添加 IDE 特定头部
    formatted_content = adapter.format_rule_content(stripped_content)

    # 获取目标路径
    target_path = adapter.get_rules_path(rule_name, scope, project_dir)

    # 确保父目录存在
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    target_path.write_text(formatted_content, encoding="utf-8")

    click.echo(
        f"  ✅ 已同步 rule '{rule_name}' ({resolved_version}) 到 {adapter.ide_name} ({scope})"
    )
    return 1


# ============================================================
# MCP 同步逻辑 (Task 11.3)
# ============================================================


def _sync_mcp(
    repo: Repository,
    adapter: BaseAdapter,
    mcp_name: str,
    version: Optional[str],
    resolved_version: Optional[str],
) -> int:
    """同步单个 MCP 配置到目标 IDE。

    读取仓库中的 MCP 配置（JSON），合并到目标 IDE 的 mcp.json 中。
    目标不存在时新建，存在同名条目时提示用户确认覆盖。

    Args:
        repo: 仓库实例
        adapter: IDE 适配器
        mcp_name: MCP 配置名称
        version: 指定版本

    Returns:
        成功同步的条目数（0 或 1）
    """
    # 获取仓库中的 MCP 配置路径
    source_dir = repo.get_config_path(ConfigType.MCP.value, mcp_name, version)
    source_mcp_file = source_dir / MCP_CONFIG_FILE

    if not source_mcp_file.is_file():
        click.echo(f"⚠️ MCP 配置 '{mcp_name}' 中未找到 {MCP_CONFIG_FILE}")
        return 0

    # 读取源 MCP 配置
    try:
        source_data = json.loads(source_mcp_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as e:
        raise ConfigParseError(f"MCP 配置文件格式错误: {source_mcp_file}: {e}")

    source_servers = source_data.get("servers", {})
    if not source_servers:
        click.echo(f"⚠️ MCP 配置 '{mcp_name}' 中没有 servers 条目")
        return 0

    # 获取目标 MCP 路径
    target_path = adapter.get_mcp_path()

    # 合并到目标
    return _merge_mcp_config(source_servers, target_path, adapter.ide_name)


def _merge_mcp_config(
    source_servers: Dict,
    target_path: Path,
    ide_name: str,
) -> int:
    """将源 MCP servers 合并到目标 mcp.json。

    1. 目标不存在时：新建文件写入
    2. 目标存在但无同名条目：追加
    3. 目标存在且有同名条目：提示用户确认覆盖

    Args:
        source_servers: 源 MCP servers 字典
        target_path: 目标 mcp.json 路径
        ide_name: IDE 名称（用于输出信息）

    Returns:
        成功同步的条目数
    """
    synced = 0

    if target_path.is_file():
        # 读取现有目标配置
        try:
            target_data = json.loads(target_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError) as e:
            raise ConfigParseError(f"MCP 配置文件格式错误: {target_path}: {e}")
    else:
        target_data = {}

    if "servers" not in target_data:
        target_data["servers"] = {}

    for server_name, server_config in source_servers.items():
        if server_name in target_data["servers"]:
            # 同名条目已存在，提示用户确认覆盖
            if click.confirm(
                f"  {ide_name} 的 MCP 配置中已存在 '{server_name}'，是否覆盖?",
                default=False,
            ):
                target_data["servers"][server_name] = server_config
                click.echo(f"  ✅ 已覆盖 MCP 条目 '{server_name}' 到 {ide_name}")
                synced += 1
            else:
                click.echo(f"  ⏭️ 已跳过 MCP 条目 '{server_name}'")
        else:
            # 无冲突，直接追加
            target_data["servers"][server_name] = server_config
            click.echo(f"  ✅ 已同步 MCP 条目 '{server_name}' 到 {ide_name}")
            synced += 1

    # 写入目标文件
    if synced > 0:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(target_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return synced


# ============================================================
# Skills 同步逻辑 (Task 11.4)
# ============================================================


def _sync_skill(
    repo: Repository,
    adapter: BaseAdapter,
    skill_name: str,
    version: Optional[str],
    resolved_version: Optional[str],
    scope: str,
    project_dir: Optional[Path],
) -> int:
    """同步单个 skill 到目标 IDE。

    拷贝仓库中的 skill 目录到目标 IDE 路径。
    目标不存在时直接拷贝，存在时提示用户确认覆盖。

    Args:
        repo: 仓库实例
        adapter: IDE 适配器
        skill_name: skill 名称
        version: 指定版本
        scope: 同步层级
        project_dir: 项目目录路径

    Returns:
        成功同步的条目数（0 或 1）
    """
    # 获取仓库中的 skill 路径
    source_dir = repo.get_config_path(ConfigType.SKILLS.value, skill_name, version)

    # 获取目标路径
    target_path = adapter.get_skills_path(skill_name, scope, project_dir)

    if target_path.exists():
        # 目标已存在，提示用户确认覆盖
        if click.confirm(
            f"  {adapter.ide_name} 中已存在 skill '{skill_name}'，是否覆盖?",
            default=False,
        ):
            shutil.rmtree(target_path)
            shutil.copytree(source_dir, target_path)
            click.echo(
                f"  ✅ 已覆盖 skill '{skill_name}' ({resolved_version}) 到 {adapter.ide_name} ({scope})"
            )
            return 1
        else:
            click.echo(f"  ⏭️ 已跳过 skill '{skill_name}'")
            return 0
    else:
        # 目标不存在，直接拷贝
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, target_path)
        click.echo(
            f"  ✅ 已同步 skill '{skill_name}' ({resolved_version}) 到 {adapter.ide_name} ({scope})"
        )
        return 1
