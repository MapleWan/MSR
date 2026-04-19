"""import 命令处理器 — 导入配置到统一仓库"""

from pathlib import Path
from typing import List, Optional

import click

from msr_sync.constants import ConfigType
from msr_sync.core.exceptions import InvalidSourceError, NetworkError, RepositoryNotFoundError
from msr_sync.core.repository import Repository
from msr_sync.core.source_resolver import ResolvedItem, SourceResolver


def import_handler(
    config_type: str,
    source: str,
    base_path: Optional[Path] = None,
) -> None:
    """执行 import 命令逻辑。

    解析导入来源，将配置项导入到统一仓库。单个配置项直接导入，
    多个配置项展示列表供用户逐一确认。

    Args:
        config_type: 配置类型（rules/skills/mcp）
        source: 导入来源（文件路径/目录路径/压缩包路径/URL）
        base_path: 仓库根目录路径（用于测试注入），默认为 None 使用默认路径
    """
    repo = Repository(base_path=base_path)

    # 确保仓库已初始化
    if not repo.exists():
        click.echo("❌ 统一仓库未初始化，请先执行 `msr-sync init`")
        raise SystemExit(1)

    resolver = SourceResolver()

    try:
        items, needs_confirm = resolver.resolve(source, config_type)
    except InvalidSourceError as e:
        click.echo(f"❌ 无效的导入来源: {e}")
        raise SystemExit(1)
    except NetworkError as e:
        click.echo(f"❌ 网络错误: {e}")
        raise SystemExit(1)

    try:
        if needs_confirm:
            success_count = _import_with_confirmation(repo, config_type, items)
        else:
            success_count = _import_items(repo, config_type, items)

        click.echo(f"\n导入完成: 成功 {success_count} 项")
    finally:
        resolver.cleanup()


def _import_with_confirmation(
    repo: Repository,
    config_type: str,
    items: List[ResolvedItem],
) -> int:
    """展示配置项列表并逐一确认后导入。

    Args:
        repo: 仓库实例
        config_type: 配置类型
        items: 待导入的配置项列表

    Returns:
        成功导入的数量
    """
    click.echo(f"发现 {len(items)} 个 {config_type} 配置项:")
    for idx, item in enumerate(items, 1):
        click.echo(f"  {idx}. {item.name}")

    click.echo("")

    success_count = 0
    for item in items:
        if click.confirm(f"是否导入 '{item.name}'?", default=True):
            version = _store_item(repo, config_type, item)
            if version:
                click.echo(f"  ✅ 已导入: {item.name} ({version})")
                success_count += 1
        else:
            click.echo(f"  ⏭️ 已跳过: {item.name}")

    return success_count


def _import_items(
    repo: Repository,
    config_type: str,
    items: List[ResolvedItem],
) -> int:
    """直接导入配置项（无需确认）。

    Args:
        repo: 仓库实例
        config_type: 配置类型
        items: 待导入的配置项列表

    Returns:
        成功导入的数量
    """
    success_count = 0
    for item in items:
        version = _store_item(repo, config_type, item)
        if version:
            click.echo(f"✅ 已导入: {item.name} ({version})")
            success_count += 1

    return success_count


def _store_item(
    repo: Repository,
    config_type: str,
    item: ResolvedItem,
) -> Optional[str]:
    """将单个配置项存储到仓库。

    根据 config_type 调用对应的仓库存储方法。名称冲突时自动创建新版本。

    Args:
        repo: 仓库实例
        config_type: 配置类型
        item: 待存储的配置项

    Returns:
        版本号字符串（如 'V1'），失败时返回 None
    """
    try:
        if config_type == ConfigType.RULES.value:
            content = item.path.read_text(encoding="utf-8")
            return repo.store_rule(item.name, content)
        elif config_type == ConfigType.SKILLS.value:
            return repo.store_skill(item.name, item.path)
        elif config_type == ConfigType.MCP.value:
            return repo.store_mcp(item.name, item.path)
        else:
            click.echo(f"  ❌ 不支持的配置类型: {config_type}")
            return None
    except RepositoryNotFoundError:
        click.echo("❌ 统一仓库未初始化，请先执行 `msr-sync init`")
        return None
    except Exception as e:
        click.echo(f"  ❌ 导入 '{item.name}' 失败: {e}")
        return None
