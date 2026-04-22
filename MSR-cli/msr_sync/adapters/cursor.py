"""Cursor IDE 适配器

实现 Cursor 的路径解析、格式转换和配置扫描。

路径约定：
- 项目级 rules: <project>/.cursor/rules/<name>.md
- 项目级 skills: <project>/.cursor/skills/<name>/
- 用户级 skills: ~/.cursor/skills/<name>/
- MCP: macOS/Windows 均为 ~/.cursor/mcp.json（跨平台统一路径）
- 不支持用户级 rules（全局级 rules）
"""

from pathlib import Path
from typing import Optional

from msr_sync.adapters.base import BaseAdapter
from msr_sync.core.frontmatter import build_cursor_header
from msr_sync.core.platform import PlatformInfo


class CursorAdapter(BaseAdapter):
    """Cursor IDE 适配器"""

    @property
    def ide_name(self) -> str:
        return "cursor"

    # --- 路径解析 ---

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Cursor rule 文件的目标路径。

        Cursor 不支持用户级 rules，但路径解析仍需保持一致性。

        Args:
            rule_name: 规则名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            rule 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".cursor" / "rules" / f"{rule_name}.md"
        return PlatformInfo.get_home() / ".cursor" / "rules" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Cursor skill 目录的目标路径。

        Args:
            skill_name: 技能名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            skill 目录的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".cursor" / "skills" / skill_name
        return PlatformInfo.get_home() / ".cursor" / "skills" / skill_name

    def get_mcp_path(self) -> Path:
        """获取 Cursor MCP 配置文件路径。

        Cursor 的 MCP 路径在 macOS 和 Windows 上相同：
        ~/.cursor/mcp.json

        Returns:
            MCP 配置文件的完整路径
        """
        return PlatformInfo.get_home() / ".cursor" / "mcp.json"

    # --- 格式转换 ---

    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 Cursor 格式。

        添加 Cursor 的 frontmatter 模板头部（含当前时间戳）：
        ---
        description:
        alwaysApply: true
        enabled: true
        updatedAt: <current_timestamp>
        provider:
        ---

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            添加了 Cursor 头部的完整内容
        """
        return build_cursor_header() + raw_content

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """Cursor 不支持全局级 rules。"""
        return False

    # --- 扫描已有配置 ---

    def scan_existing_configs(self) -> dict:
        """扫描 Cursor 已有的用户级配置。

        扫描范围：
        - rules: 不扫描（Cursor 不支持全局级 rules）
        - skills: ~/.cursor/skills/ 下的子目录
        - mcp: MCP 配置文件

        Returns:
            {"rules": [], "skills": [...], "mcp": [...]}
        """
        result: dict = {"rules": [], "skills": [], "mcp": []}

        # 扫描用户级 skills
        skills_dir = PlatformInfo.get_home() / ".cursor" / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    result["skills"].append(item.name)

        # 扫描 MCP 配置
        mcp_path = self.get_mcp_path()
        if mcp_path.exists() and mcp_path.is_file():
            result["mcp"].append(str(mcp_path))

        return result
