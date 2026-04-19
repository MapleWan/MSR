"""MSR-sync 常量定义"""

from enum import Enum
from pathlib import Path


# 统一仓库路径
DEFAULT_REPO_PATH = Path.home() / ".msr-repos"

# 仓库子目录名称
RULES_DIR = "RULES"
SKILLS_DIR = "SKILLS"
MCP_DIR = "MCP"


class ConfigType(str, Enum):
    """配置类型枚举"""

    RULES = "rules"
    SKILLS = "skills"
    MCP = "mcp"

    @property
    def repo_dir_name(self) -> str:
        """返回在统一仓库中对应的目录名称"""
        return {
            ConfigType.RULES: RULES_DIR,
            ConfigType.SKILLS: SKILLS_DIR,
            ConfigType.MCP: MCP_DIR,
        }[self]


# 支持的 IDE 列表
SUPPORTED_IDES = ["trae", "qoder", "lingma", "codebuddy"]

# 版本号前缀
VERSION_PREFIX = "V"

# Skill 标识文件
SKILL_MARKER_FILE = "SKILL.md"

# MCP 配置文件名
MCP_CONFIG_FILE = "mcp.json"

# 支持的压缩包扩展名
SUPPORTED_ARCHIVE_EXTENSIONS = [".zip", ".tar.gz", ".tgz"]

# 支持的平台
SUPPORTED_PLATFORMS = ["macos", "windows"]
