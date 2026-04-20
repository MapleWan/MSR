"""全局配置模块 — 加载和管理 ~/.msr-sync/config.yaml 中的用户配置"""

from pathlib import Path
from typing import List, Optional

import yaml

# 默认值常量
DEFAULT_REPO_PATH = "~/.msr-repos"
DEFAULT_IGNORE_PATTERNS = ["__MACOSX", ".DS_Store", "__pycache__", ".git"]
DEFAULT_IDES = ["all"]
DEFAULT_SCOPE = "global"
VALID_SCOPES = ("global", "project")
VALID_IDES = ("trae", "qoder", "lingma", "codebuddy", "all")
CONFIG_FILE_PATH = Path.home() / ".msr-sync" / "config.yaml"


class GlobalConfig:
    """全局配置对象

    保存从 ~/.msr-sync/config.yaml 加载的用户配置。
    所有属性均有合理默认值，确保无配置文件时行为不变。

    Attributes:
        repo_path: 统一仓库根目录路径（已展开 ~）
        ignore_patterns: 忽略模式列表
        default_ides: 默认同步目标 IDE 列表
        default_scope: 默认同步层级
    """

    def __init__(
        self,
        repo_path: Optional[str] = None,
        ignore_patterns: Optional[List[str]] = None,
        default_ides: Optional[List[str]] = None,
        default_scope: Optional[str] = None,
    ):
        self.repo_path: Path = self._resolve_repo_path(repo_path)
        self.ignore_patterns: List[str] = (
            ignore_patterns if ignore_patterns is not None
            else list(DEFAULT_IGNORE_PATTERNS)
        )
        self.default_ides: List[str] = self._validate_ides(default_ides)
        self.default_scope: str = self._validate_scope(default_scope)

    @staticmethod
    def _resolve_repo_path(raw: Optional[str]) -> Path:
        """解析仓库路径，展开 ~ 前缀，空字符串回退到默认值。"""
        if not raw or not raw.strip():
            raw = DEFAULT_REPO_PATH
        path_str = raw.strip()
        if path_str.startswith("~/") or path_str == "~":
            return Path.home() / path_str[2:] if len(path_str) > 2 else Path.home()
        return Path(path_str).expanduser()

    @staticmethod
    def _validate_ides(raw: Optional[List[str]]) -> List[str]:
        """校验 IDE 列表，过滤无效条目并输出警告，空列表回退到默认值。"""
        if raw is None or len(raw) == 0:
            return list(DEFAULT_IDES)
        valid = []
        for ide in raw:
            if ide in VALID_IDES:
                valid.append(ide)
            else:
                import click
                click.echo(f"⚠️ 配置文件中的 IDE 名称无效，已忽略: {ide}")
        return valid if valid else list(DEFAULT_IDES)

    @staticmethod
    def _validate_scope(raw: Optional[str]) -> str:
        """校验同步层级，无效值回退到默认值并输出警告。"""
        if raw is None:
            return DEFAULT_SCOPE
        if raw in VALID_SCOPES:
            return raw
        import click
        click.echo(f"⚠️ 配置文件中的 default_scope 值无效，已使用默认值 'global': {raw}")
        return DEFAULT_SCOPE

    def to_dict(self) -> dict:
        """将配置序列化为字典（用于测试和调试）。"""
        return {
            "repo_path": str(self.repo_path),
            "ignore_patterns": list(self.ignore_patterns),
            "default_ides": list(self.default_ides),
            "default_scope": self.default_scope,
        }


def load_config(config_path: Optional[Path] = None) -> GlobalConfig:
    """从 YAML 文件加载配置。

    Args:
        config_path: 配置文件路径，默认为 ~/.msr-sync/config.yaml。
                     支持注入自定义路径便于测试。

    Returns:
        GlobalConfig 实例

    Raises:
        ConfigFileError: YAML 语法错误时抛出
    """
    path = config_path or CONFIG_FILE_PATH

    if not path.is_file():
        return GlobalConfig()

    raw_text = path.read_text(encoding="utf-8")
    if not raw_text.strip():
        return GlobalConfig()

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        from msr_sync.core.exceptions import ConfigFileError
        raise ConfigFileError(f"配置文件 YAML 语法错误: {path}\n{e}")

    if not isinstance(data, dict):
        return GlobalConfig()

    return GlobalConfig(
        repo_path=data.get("repo_path"),
        ignore_patterns=data.get("ignore_patterns"),
        default_ides=data.get("default_ides"),
        default_scope=data.get("default_scope"),
    )


def config_to_yaml(config: GlobalConfig) -> str:
    """将 GlobalConfig 序列化为 YAML 字符串（用于往返测试）。"""
    return yaml.dump(config.to_dict(), default_flow_style=False, allow_unicode=True)


# ---- 模块级单例 ----

_global_config: Optional[GlobalConfig] = None


def get_config() -> GlobalConfig:
    """获取全局配置单例。首次调用时自动加载。"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def init_config(config_path: Optional[Path] = None) -> GlobalConfig:
    """显式初始化全局配置单例（用于启动时或测试注入）。"""
    global _global_config
    _global_config = load_config(config_path)
    return _global_config


def reset_config() -> None:
    """重置全局配置单例（仅用于测试）。"""
    global _global_config
    _global_config = None


# 默认配置文件模板（带中文注释）
_DEFAULT_CONFIG_TEMPLATE = """\
# MSR-sync 全局配置文件
# 文件位置: ~/.msr-sync/config.yaml

# 统一仓库路径（支持 ~ 展开，默认 ~/.msr-repos）
# repo_path: ~/.msr-repos

# 导入扫描时忽略的目录和文件模式
# 支持精确匹配（如 __MACOSX）和通配符匹配（如 *.pyc）
ignore_patterns:
  - __MACOSX
  - .DS_Store
  - __pycache__
  - .git

# 默认同步目标 IDE 列表
# 可选值: trae, qoder, lingma, codebuddy, all
# default_ides:
#   - all

# 默认同步层级（global 或 project）
# default_scope: global
"""


def generate_default_config(config_path: Optional[Path] = None) -> bool:
    """生成带注释的默认配置文件。

    如果配置文件已存在则跳过，不覆盖用户已有配置。

    Args:
        config_path: 配置文件路径，默认为 ~/.msr-sync/config.yaml。

    Returns:
        True 表示新建了配置文件，False 表示文件已存在。
    """
    path = config_path or CONFIG_FILE_PATH
    if path.is_file():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    return True
