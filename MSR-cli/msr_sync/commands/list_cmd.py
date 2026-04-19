"""list 命令处理器 — 查看统一仓库中的配置列表"""

from pathlib import Path
from typing import Optional

import click

from msr_sync.core.exceptions import RepositoryNotFoundError
from msr_sync.core.repository import Repository


def list_handler(
    config_type: Optional[str] = None, base_path: Optional[Path] = None
) -> None:
    """执行 list 命令逻辑。

    以树形结构按配置类型分组展示统一仓库中的配置条目，
    显示名称和版本号。

    Args:
        config_type: 可选的配置类型过滤（rules/skills/mcp）
        base_path: 仓库根目录路径（用于测试注入），默认为 None 使用默认路径
    """
    repo = Repository(base_path=base_path)

    try:
        configs = repo.list_configs(config_type=config_type)
    except RepositoryNotFoundError:
        click.echo("❌ 统一仓库未初始化，请先执行 `msr-sync init`")
        raise SystemExit(1)

    # 检查是否有任何配置
    has_any = any(names for names in configs.values())
    if not has_any:
        if config_type:
            click.echo(f"📦 统一仓库中没有 {config_type} 类型的配置")
        else:
            click.echo("📦 统一仓库为空，暂无配置")
        return

    click.echo("📦 统一仓库配置列表")

    # 过滤出有内容的类型
    active_types = [
        (ct, names) for ct, names in configs.items() if names
    ]

    for type_idx, (ct, names) in enumerate(active_types):
        is_last_type = type_idx == len(active_types) - 1
        type_prefix = "└── " if is_last_type else "├── "
        child_prefix = "    " if is_last_type else "│   "

        click.echo(f"{type_prefix}{ct}")

        sorted_names = sorted(names.keys())
        for name_idx, name in enumerate(sorted_names):
            versions = names[name]
            is_last_name = name_idx == len(sorted_names) - 1
            name_prefix = "└── " if is_last_name else "├── "

            version_str = ", ".join(versions)
            click.echo(f"{child_prefix}{name_prefix}{name} [{version_str}]")
