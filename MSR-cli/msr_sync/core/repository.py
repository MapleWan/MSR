"""统一仓库操作模块 — 管理 rules、skills、MCP 配置的存储与检索"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional

from msr_sync.constants import ConfigType, RULES_DIR, SKILLS_DIR, MCP_DIR
from msr_sync.core.exceptions import ConfigNotFoundError, RepositoryNotFoundError
from msr_sync.core.version import get_latest_version, get_next_version, get_versions


# 配置类型字符串到仓库目录名的映射
_CONFIG_TYPE_DIR_MAP = {
    ConfigType.RULES.value: RULES_DIR,
    ConfigType.SKILLS.value: SKILLS_DIR,
    ConfigType.MCP.value: MCP_DIR,
}

# 仓库子目录列表
_REPO_SUBDIRS = [RULES_DIR, SKILLS_DIR, MCP_DIR]


class Repository:
    """统一仓库操作类

    管理 ~/.msr-repos 下的配置存储，支持 rules、skills、MCP 三种配置类型的
    导入、查询、删除等操作。每个配置条目支持多版本管理（V1, V2, V3…）。

    Args:
        base_path: 仓库根目录路径，默认为 ~/.msr-repos。支持注入自定义路径便于测试。
    """

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".msr-repos"

    def init(self) -> bool:
        """初始化仓库目录结构。

        创建仓库根目录及 RULES/、SKILLS/、MCP/ 子目录。

        Returns:
            True 表示新建了仓库，False 表示仓库已存在（幂等操作）。
        """
        is_new = not self.exists()
        for sub_dir in _REPO_SUBDIRS:
            (self.base_path / sub_dir).mkdir(parents=True, exist_ok=True)
        return is_new

    def exists(self) -> bool:
        """检查仓库是否已存在。

        Returns:
            仓库根目录存在且包含所有必需子目录时返回 True。
        """
        if not self.base_path.is_dir():
            return False
        return all(
            (self.base_path / sub_dir).is_dir() for sub_dir in _REPO_SUBDIRS
        )

    def _ensure_exists(self) -> None:
        """确保仓库已初始化，否则抛出异常。"""
        if not self.exists():
            raise RepositoryNotFoundError(
                "统一仓库未初始化，请先执行 `msr-sync init`"
            )

    def _resolve_config_dir(self, config_type: str) -> str:
        """将配置类型字符串解析为仓库目录名。

        Args:
            config_type: 配置类型字符串（rules/skills/mcp）

        Returns:
            对应的仓库目录名（RULES/SKILLS/MCP）

        Raises:
            ValueError: 配置类型无效时抛出
        """
        dir_name = _CONFIG_TYPE_DIR_MAP.get(config_type)
        if dir_name is None:
            raise ValueError(f"无效的配置类型: {config_type}")
        return dir_name

    def store_rule(self, name: str, content: str) -> str:
        """存储 rule 文件到统一仓库。

        将 rule 内容写入 RULES/<name>/V<n>/<name>.md，自动递增版本号。

        Args:
            name: rule 名称
            content: rule 的 Markdown 内容

        Returns:
            新创建的版本号字符串（如 'V1'）
        """
        self._ensure_exists()
        config_dir = self.base_path / RULES_DIR / name
        config_dir.mkdir(parents=True, exist_ok=True)

        next_ver = get_next_version(config_dir)
        version_dir = config_dir / next_ver
        version_dir.mkdir(parents=True, exist_ok=True)

        rule_file = version_dir / f"{name}.md"
        rule_file.write_text(content, encoding="utf-8")

        return next_ver

    def store_skill(self, name: str, source_dir: Path) -> str:
        """存储 skill 目录到统一仓库。

        将 source_dir 的内容拷贝到 SKILLS/<name>/V<n>/，自动递增版本号。

        Args:
            name: skill 名称
            source_dir: 源 skill 目录路径

        Returns:
            新创建的版本号字符串（如 'V1'）
        """
        self._ensure_exists()
        config_dir = self.base_path / SKILLS_DIR / name
        config_dir.mkdir(parents=True, exist_ok=True)

        next_ver = get_next_version(config_dir)
        version_dir = config_dir / next_ver

        shutil.copytree(source_dir, version_dir)

        return next_ver

    def store_mcp(self, name: str, source_dir: Path) -> str:
        """存储 MCP 配置目录到统一仓库。

        将 source_dir 的内容拷贝到 MCP/<name>/V<n>/，自动递增版本号。

        Args:
            name: MCP 配置名称
            source_dir: 源 MCP 目录路径

        Returns:
            新创建的版本号字符串（如 'V1'）
        """
        self._ensure_exists()
        config_dir = self.base_path / MCP_DIR / name
        config_dir.mkdir(parents=True, exist_ok=True)

        next_ver = get_next_version(config_dir)
        version_dir = config_dir / next_ver

        shutil.copytree(source_dir, version_dir)

        return next_ver

    def get_config_path(
        self, config_type: str, name: str, version: Optional[str] = None
    ) -> Path:
        """获取配置路径。

        Args:
            config_type: 配置类型（rules/skills/mcp）
            name: 配置名称
            version: 版本号（如 'V1'），为 None 时返回最新版本路径

        Returns:
            配置版本目录的 Path 对象

        Raises:
            RepositoryNotFoundError: 仓库未初始化
            ConfigNotFoundError: 配置或版本不存在
        """
        self._ensure_exists()
        dir_name = self._resolve_config_dir(config_type)
        config_dir = self.base_path / dir_name / name

        if not config_dir.is_dir():
            raise ConfigNotFoundError(
                f"未找到指定的配置: {config_type}/{name}"
            )

        if version is None:
            version = get_latest_version(config_dir)
            if version is None:
                raise ConfigNotFoundError(
                    f"配置 {config_type}/{name} 没有可用版本"
                )

        version_dir = config_dir / version
        if not version_dir.is_dir():
            raise ConfigNotFoundError(
                f"未找到指定的配置版本: {config_type}/{name}/{version}"
            )

        return version_dir

    def list_configs(
        self, config_type: Optional[str] = None
    ) -> Dict[str, Dict[str, List[str]]]:
        """列出仓库中的配置。

        Args:
            config_type: 可选的配置类型过滤（rules/skills/mcp），
                         为 None 时返回所有类型

        Returns:
            嵌套字典 {config_type: {name: [versions]}}
        """
        self._ensure_exists()

        if config_type is not None:
            types_to_scan = {config_type: self._resolve_config_dir(config_type)}
        else:
            types_to_scan = dict(_CONFIG_TYPE_DIR_MAP)

        result: Dict[str, Dict[str, List[str]]] = {}

        for ct, dir_name in types_to_scan.items():
            type_dir = self.base_path / dir_name
            configs: Dict[str, List[str]] = {}

            if type_dir.is_dir():
                for entry in sorted(type_dir.iterdir()):
                    if entry.is_dir():
                        versions = get_versions(entry)
                        if versions:
                            configs[entry.name] = versions

            result[ct] = configs

        return result

    def remove_config(
        self, config_type: str, name: str, version: str
    ) -> bool:
        """删除指定配置版本。

        Args:
            config_type: 配置类型（rules/skills/mcp）
            name: 配置名称
            version: 版本号（如 'V1'）

        Returns:
            删除成功返回 True

        Raises:
            RepositoryNotFoundError: 仓库未初始化
            ConfigNotFoundError: 配置版本不存在
        """
        self._ensure_exists()
        dir_name = self._resolve_config_dir(config_type)
        version_dir = self.base_path / dir_name / name / version

        if not version_dir.is_dir():
            raise ConfigNotFoundError(
                f"未找到指定的配置版本: {config_type}/{name}/{version}"
            )

        shutil.rmtree(version_dir)
        return True

    def read_rule_content(
        self, name: str, version: Optional[str] = None
    ) -> str:
        """读取 rule 原始内容。

        Args:
            name: rule 名称
            version: 版本号，为 None 时读取最新版本

        Returns:
            rule 文件的原始 Markdown 内容

        Raises:
            RepositoryNotFoundError: 仓库未初始化
            ConfigNotFoundError: rule 或版本不存在
        """
        version_dir = self.get_config_path(ConfigType.RULES.value, name, version)
        rule_file = version_dir / f"{name}.md"

        if not rule_file.is_file():
            raise ConfigNotFoundError(
                f"未找到 rule 文件: {name}.md"
            )

        return rule_file.read_text(encoding="utf-8")
