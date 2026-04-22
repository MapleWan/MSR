"""Kiro IDE 适配器

实现 Kiro（AWS）的路径解析、格式转换和配置扫描。

路径约定：
- 项目级 rules (steering): <project>/.kiro/steering/<name>.md
- 用户级 rules (steering): ~/.kiro/steering/<name>.md
- 项目级 skills: <project>/.kiro/skills/<name>/
- 用户级 skills: ~/.kiro/skills/<name>/
- MCP: macOS/Windows 均为 ~/.kiro/mcp.json（跨平台统一路径）
- 支持全局级 rules
"""

from pathlib import Path
from typing import Optional

from msr_sync.adapters.base import BaseAdapter
from msr_sync.core.platform import PlatformInfo


class KiroAdapter(BaseAdapter):
    """Kiro IDE 适配器"""

    @property
    def ide_name(self) -> str:
        return "kiro"

    # --- 路径解析 ---

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Kiro rule (steering) 文件的目标路径。

        Kiro 同时支持项目级和用户级 steering。

        Args:
            rule_name: 规则名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            rule 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".kiro" / "steering" / f"{rule_name}.md"
        return PlatformInfo.get_home() / ".kiro" / "steering" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Kiro skill 目录的目标路径。

        Args:
            skill_name: 技能名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            skill 目录的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".kiro" / "skills" / skill_name
        return PlatformInfo.get_home() / ".kiro" / "skills" / skill_name

    def get_mcp_path(self) -> Path:
        """获取 Kiro MCP 配置文件路径。

        Kiro 的 MCP 路径在 macOS 和 Windows 上相同：
        ~/.kiro/mcp.json

        Returns:
            MCP 配置文件的完整路径
        """
        return PlatformInfo.get_home() / ".kiro" / "mcp.json"

    # --- 格式转换 ---

    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 Kiro 格式。

        Kiro 不添加额外 frontmatter 头部，直接返回原始内容。

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            原始内容（不添加额外头部）
        """
        return raw_content

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """Kiro 支持全局级 rules (steering)。"""
        return True

    # --- 扫描已有配置 ---

    def scan_existing_configs(self) -> dict:
        """扫描 Kiro 已有的用户级配置。

        扫描范围：
        - rules: ~/.kiro/steering/ 下的 .md 文件
        - skills: ~/.kiro/skills/ 下的子目录
        - mcp: MCP 配置文件

        Returns:
            {"rules": [...], "skills": [...], "mcp": [...]}
        """
        result: dict = {"rules": [], "skills": [], "mcp": []}

        # 扫描用户级 rules (steering)
        rules_dir = PlatformInfo.get_home() / ".kiro" / "steering"
        if rules_dir.exists() and rules_dir.is_dir():
            for item in sorted(rules_dir.iterdir()):
                if item.is_file() and item.suffix == ".md":
                    result["rules"].append(item.stem)

        # 扫描用户级 skills
        skills_dir = PlatformInfo.get_home() / ".kiro" / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    result["skills"].append(item.name)

        # 扫描 MCP 配置
        mcp_path = self.get_mcp_path()
        if mcp_path.exists() and mcp_path.is_file():
            result["mcp"].append(str(mcp_path))

        return result
