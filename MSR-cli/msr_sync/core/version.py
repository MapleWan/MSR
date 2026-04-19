"""版本管理模块 — 解析、格式化和管理配置版本号"""

from pathlib import Path
from typing import List, Optional

from msr_sync.constants import VERSION_PREFIX


def parse_version(version_str: str) -> int:
    """解析版本字符串为整数。

    Args:
        version_str: 版本字符串，格式为 'V1'、'V2' 等

    Returns:
        版本号对应的正整数

    Raises:
        ValueError: 版本字符串格式无效时抛出
    """
    if not isinstance(version_str, str):
        raise ValueError(f"无效的版本号格式: {version_str}")

    if not version_str.startswith(VERSION_PREFIX):
        raise ValueError(f"无效的版本号格式: {version_str}")

    num_part = version_str[len(VERSION_PREFIX):]

    if not num_part:
        raise ValueError(f"无效的版本号格式: {version_str}")

    if not num_part.isdigit():
        raise ValueError(f"无效的版本号格式: {version_str}")

    num = int(num_part)

    if num <= 0:
        raise ValueError(f"无效的版本号格式: {version_str}")

    # Reject leading zeros (e.g., "V01") — canonical form is "V1"
    if num_part != str(num):
        raise ValueError(f"无效的版本号格式: {version_str}")

    return num


def format_version(version_num: int) -> str:
    """格式化整数为版本字符串。

    Args:
        version_num: 正整数版本号

    Returns:
        格式化后的版本字符串，如 'V1'
    """
    return f"{VERSION_PREFIX}{version_num}"


def get_versions(config_dir: Path) -> List[str]:
    """获取配置目录下所有版本号，按数字升序排序。

    扫描 config_dir 下所有符合 'V<n>' 格式的子目录，
    返回按版本号数字排序的版本字符串列表。

    Args:
        config_dir: 配置条目的目录路径（如 ~/.msr-repos/RULES/my-rule/）

    Returns:
        排序后的版本字符串列表，如 ['V1', 'V2', 'V3']
    """
    if not config_dir.is_dir():
        return []

    versions = []
    for entry in config_dir.iterdir():
        if entry.is_dir():
            try:
                num = parse_version(entry.name)
                versions.append((num, entry.name))
            except ValueError:
                # 跳过不符合版本号格式的目录
                continue

    versions.sort(key=lambda x: x[0])
    return [v[1] for v in versions]


def get_latest_version(config_dir: Path) -> Optional[str]:
    """获取最新版本号（数字最大的版本）。

    Args:
        config_dir: 配置条目的目录路径

    Returns:
        最新版本字符串（如 'V3'），目录为空或不存在时返回 None
    """
    versions = get_versions(config_dir)
    if not versions:
        return None
    return versions[-1]


def get_next_version(config_dir: Path) -> str:
    """获取下一个版本号。

    如果目录为空或不存在，返回 'V1'；
    否则返回当前最大版本号 + 1。

    Args:
        config_dir: 配置条目的目录路径

    Returns:
        下一个版本字符串，如 'V1' 或 'V4'
    """
    latest = get_latest_version(config_dir)
    if latest is None:
        return format_version(1)
    return format_version(parse_version(latest) + 1)
