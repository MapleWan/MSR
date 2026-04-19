"""IDE 适配器抽象基类"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseAdapter(ABC):
    """IDE 适配器抽象基类。

    每个支持的 IDE 需要实现此基类，提供：
    - 路径解析：rules、skills、MCP 配置在该 IDE 中的存储路径
    - 格式转换：将统一仓库中的原始内容转换为 IDE 特定格式
    - 能力查询：该 IDE 支持的配置层级（项目级/全局级）
    - 配置扫描：扫描该 IDE 已有的配置（用于 init --merge）
    """

    @property
    @abstractmethod
    def ide_name(self) -> str:
        """IDE 标识名称（如 'qoder'、'lingma'、'trae'、'codebuddy'）"""

    # --- 路径解析 ---

    @abstractmethod
    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 rule 文件的目标路径。

        Args:
            rule_name: 规则名称
            scope: 同步层级，'project' 或 'global'
            project_dir: 项目目录路径，scope 为 'project' 时必须提供

        Returns:
            rule 文件的完整目标路径
        """

    @abstractmethod
    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 skill 目录的目标路径。

        Args:
            skill_name: 技能名称
            scope: 同步层级，'project' 或 'global'
            project_dir: 项目目录路径，scope 为 'project' 时必须提供

        Returns:
            skill 目录的完整目标路径
        """

    @abstractmethod
    def get_mcp_path(self) -> Path:
        """获取 MCP 配置文件路径。

        Returns:
            MCP 配置文件（mcp.json）的完整路径
        """

    # --- 格式转换 ---

    @abstractmethod
    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 IDE 特定格式。

        对已剥离 frontmatter 的纯 Markdown 内容，添加该 IDE 所需的模板头部。

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            添加了 IDE 特定头部的完整内容
        """

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """是否支持用户级（全局级）rules。

        默认返回 False。仅 CodeBuddy 支持全局级 rules，
        其他 IDE（Qoder、Lingma、Trae）均不支持。

        Returns:
            True 表示支持全局级 rules，False 表示不支持
        """
        return False

    # --- 扫描已有配置（用于 init --merge）---

    @abstractmethod
    def scan_existing_configs(self) -> dict:
        """扫描该 IDE 已有的配置。

        用于 `msr-sync init --merge` 命令，扫描 IDE 用户级配置路径下的
        现有配置并返回。

        Returns:
            配置字典，格式为 {config_type: [config_items]}，
            其中 config_type 为 'rules'、'skills' 或 'mcp'，
            config_items 为该类型下发现的配置项列表
        """
