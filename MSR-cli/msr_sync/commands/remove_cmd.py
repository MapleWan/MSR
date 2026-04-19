"""remove 命令处理器 — 删除指定配置版本"""

from pathlib import Path
from typing import Optional

import click

from msr_sync.core.exceptions import ConfigNotFoundError, RepositoryNotFoundError
from msr_sync.core.repository import Repository


def remove_handler(
    config_type: str,
    name: str,
    version: str,
    base_path: Optional[Path] = None,
) -> None:
    """执行 remove 命令逻辑。

    删除统一仓库中指定的配置版本。

    Args:
        config_type: 配置类型（rules/skills/mcp）
        name: 配置名称
        version: 版本号（如 'V1'）
        base_path: 仓库根目录路径（用于测试注入），默认为 None 使用默认路径
    """
    repo = Repository(base_path=base_path)

    try:
        repo.remove_config(config_type, name, version)
        click.echo(
            f"✅ 已删除配置: {config_type}/{name}/{version}"
        )
    except RepositoryNotFoundError:
        click.echo("❌ 统一仓库未初始化，请先执行 `msr-sync init`")
        raise SystemExit(1)
    except ConfigNotFoundError:
        click.echo(
            f"❌ 未找到指定的配置版本: {config_type}/{name}/{version}"
        )
        raise SystemExit(1)
