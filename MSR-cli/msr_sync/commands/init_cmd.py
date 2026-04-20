"""init 命令处理器 — 初始化统一配置仓库"""

import json
from pathlib import Path
from typing import Optional

import click

from msr_sync.adapters.registry import get_all_adapters
from msr_sync.core.repository import Repository


def init_handler(merge: bool, base_path: Optional[Path] = None) -> None:
    """执行 init 命令逻辑。

    创建统一仓库目录结构。当指定 --merge 时，扫描所有 IDE 适配器的
    现有配置并导入到统一仓库。

    Args:
        merge: 是否合并已有 IDE 配置
        base_path: 仓库根目录路径（用于测试注入），默认为 None 使用默认路径
    """
    repo = Repository(base_path=base_path)
    is_new = repo.init()

    if is_new:
        click.echo("✅ 统一仓库已创建: {}".format(repo.base_path))
    else:
        click.echo("统一仓库已初始化，跳过创建")

    # 生成默认配置文件（如果不存在）
    from msr_sync.core.config import generate_default_config, CONFIG_FILE_PATH

    config_path = CONFIG_FILE_PATH
    if generate_default_config(config_path):
        click.echo("✅ 已生成默认配置文件: {}".format(config_path))
    elif is_new:
        click.echo("配置文件已存在，跳过生成: {}".format(config_path))

    if merge:
        _merge_existing_configs(repo)


def _merge_existing_configs(repo: Repository) -> None:
    """扫描所有 IDE 适配器的现有配置并导入到统一仓库。

    Args:
        repo: 仓库实例
    """
    click.echo("\n🔍 正在扫描已有 IDE 配置...")

    # 合并摘要统计: {config_type: {ide_name: count}}
    summary: dict = {"rules": {}, "skills": {}, "mcp": {}}
    total_imported = 0

    adapters = get_all_adapters()

    for adapter in adapters:
        ide_name = adapter.ide_name
        try:
            configs = adapter.scan_existing_configs()
        except Exception:
            click.echo(f"  ⚠️ 扫描 {ide_name} 配置时出错，已跳过")
            continue

        # 导入 rules
        for rule_name in configs.get("rules", []):
            try:
                # 尝试读取 rule 文件内容
                rules_path = adapter.get_rules_path(rule_name, "global")
                if rules_path.exists() and rules_path.is_file():
                    content = rules_path.read_text(encoding="utf-8")
                    repo.store_rule(rule_name, content)
                    summary["rules"].setdefault(ide_name, 0)
                    summary["rules"][ide_name] += 1
                    total_imported += 1
            except Exception as e:
                click.echo(f"  ⚠️ 导入 {ide_name} rule '{rule_name}' 时出错，已跳过: {e}")

        # 导入 skills
        for skill_name in configs.get("skills", []):
            try:
                skill_path = adapter.get_skills_path(skill_name, "global")
                if skill_path.exists() and skill_path.is_dir():
                    repo.store_skill(skill_name, skill_path)
                    summary["skills"].setdefault(ide_name, 0)
                    summary["skills"][ide_name] += 1
                    total_imported += 1
            except Exception as e:
                click.echo(f"  ⚠️ 导入 {ide_name} skill '{skill_name}' 时出错，已跳过: {e}")

        # 导入 mcp
        for mcp_item in configs.get("mcp", []):
            try:
                mcp_path = Path(mcp_item)
                if mcp_path.exists() and mcp_path.is_file():
                    raw_text = mcp_path.read_text(encoding="utf-8").strip()
                    if not raw_text:
                        # 空文件，跳过
                        continue
                    # 解析 mcp.json 中的 servers 条目
                    mcp_content = json.loads(raw_text)
                    servers = mcp_content.get("servers", {})
                    for mcp_name in servers:
                        # 为每个 MCP server 创建临时目录并存储
                        import tempfile

                        with tempfile.TemporaryDirectory() as tmp_dir:
                            tmp_path = Path(tmp_dir)
                            mcp_json_file = tmp_path / "mcp.json"
                            mcp_json_file.write_text(
                                json.dumps(
                                    {"servers": {mcp_name: servers[mcp_name]}},
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                                encoding="utf-8",
                            )
                            repo.store_mcp(mcp_name, tmp_path)
                            summary["mcp"].setdefault(ide_name, 0)
                            summary["mcp"][ide_name] += 1
                            total_imported += 1
            except Exception as e:
                click.echo(f"  ⚠️ 导入 {ide_name} MCP 配置时出错，已跳过: {e}")

    # 输出合并摘要
    click.echo(f"\n📊 合并摘要（共导入 {total_imported} 项配置）:")
    for config_type in ("rules", "skills", "mcp"):
        ide_counts = summary[config_type]
        if ide_counts:
            details = ", ".join(
                f"{ide}: {count} 项" for ide, count in ide_counts.items()
            )
            click.echo(f"  {config_type}: {details}")
        else:
            click.echo(f"  {config_type}: 无")
