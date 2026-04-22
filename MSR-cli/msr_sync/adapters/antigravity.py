"""Antigravity IDE 适配器

实现 Google Antigravity 的路径解析、格式转换和配置扫描。

路径约定：
- 项目级 rules: <project>/.agents/rules/<name>.md
- 用户级 rules: 不支持（Antigravity 全局 rules 为单文件 GEMINI.md，与 MSR 多文件模型不兼容）
- 项目级 skills (workflows): <project>/.agents/workflows/<name>.md
- 用户级 skills (workflows): ~/.gemini/workflows/<name>.md
- MCP: ~/.gemini/antigravity/mcp_config.json
- 不支持用户级 rules
"""

from pathlib import Path
from typing import Optional

from msr_sync.adapters.base import BaseAdapter
from msr_sync.core.frontmatter import build_antigravity_header
from msr_sync.core.platform import PlatformInfo


class AntigravityAdapter(BaseAdapter):
    """Antigravity IDE 适配器"""

    @property
    def ide_name(self) -> str:
        return "antigravity"

    # --- 路径解析 ---

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Antigravity rule 文件的目标路径。

        Antigravity 仅支持项目级 rules，全局 rules 为单文件 GEMINI.md，
        与 MSR 多文件模型不兼容，因此不支持全局级 rules。

        Args:
            rule_name: 规则名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            rule 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".agents" / "rules" / f"{rule_name}.md"
        # global scope: 虽然不支持，但仍返回一致路径
        return PlatformInfo.get_home() / ".gemini" / "rules" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Antigravity skill (workflow) 的目标路径。

        Antigravity 的 skills 对应 workflows，存储为 .md 文件。

        Args:
            skill_name: 技能名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            skill 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".agents" / "workflows" / f"{skill_name}.md"
        return PlatformInfo.get_home() / ".gemini" / "workflows" / f"{skill_name}.md"

    def get_mcp_path(self) -> Path:
        """获取 Antigravity MCP 配置文件路径。

        Antigravity 的 MCP 路径：
        ~/.gemini/antigravity/mcp_config.json

        Returns:
            MCP 配置文件的完整路径
        """
        return PlatformInfo.get_home() / ".gemini" / "antigravity" / "mcp_config.json"

    # --- 格式转换 ---

    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 Antigravity 格式。

        Antigravity rules 不添加额外 frontmatter 头部，直接返回原始内容。

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            原始内容（不添加额外头部）
        """
        return raw_content

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """Antigravity 不支持全局级 rules（全局 rules 为单文件 GEMINI.md）。"""
        return False

    # --- 扫描已有配置 ---

    def scan_existing_configs(self) -> dict:
        """扫描 Antigravity 已有的用户级配置。

        扫描范围：
        - rules: 不扫描（Antigravity 不支持全局级多文件 rules）
        - skills (workflows): ~/.gemini/workflows/ 下的 .md 文件
        - mcp: MCP 配置文件

        Returns:
            {"rules": [], "skills": [...], "mcp": [...]}
        """
        result: dict = {"rules": [], "skills": [], "mcp": []}

        # 扫描用户级 skills (workflows)
        skills_dir = PlatformInfo.get_home() / ".gemini" / "workflows"
        if skills_dir.exists() and skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                if item.is_file() and item.suffix == ".md":
                    result["skills"].append(item.stem)

        # 扫描 MCP 配置
        mcp_path = self.get_mcp_path()
        if mcp_path.exists() and mcp_path.is_file():
            result["mcp"].append(str(mcp_path))

        return result
