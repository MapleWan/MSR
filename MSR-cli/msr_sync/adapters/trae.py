"""Trae IDE 适配器

实现 Trae（字节）的路径解析、格式转换和配置扫描。

路径约定：
- 项目级 rules: <project>/.trae/rules/<name>.md
- 项目级 skills: <project>/.trae/skills/<name>/
- 用户级 skills: ~/.trae-cn/skills/<name>/  (注意: trae-cn, 不是 trae)
- MCP: macOS ~/Library/Application Support/Trae CN/User/mcp.json
       Windows %APPDATA%/Trae CN/User/mcp.json
- 不支持全局级 rules
"""

from pathlib import Path
from typing import Optional

from msr_sync.adapters.base import BaseAdapter
from msr_sync.core.platform import PlatformInfo


class TraeAdapter(BaseAdapter):
    """Trae IDE 适配器"""

    @property
    def ide_name(self) -> str:
        return "trae"

    # --- 路径解析 ---

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Trae rule 文件的目标路径。

        Trae 仅支持项目级 rules。当 scope 为 'global' 时仍返回路径
        （调用方负责检查 supports_global_rules() 并输出警告）。

        Args:
            rule_name: 规则名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            rule 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".trae" / "rules" / f"{rule_name}.md"
        # global scope: 返回用户主目录下的路径（调用方会检查 supports_global_rules）
        return PlatformInfo.get_home() / ".trae" / "rules" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Trae skill 目录的目标路径。

        注意：用户级 skills 路径使用 ~/.trae-cn/（不是 ~/.trae/）。

        Args:
            skill_name: 技能名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            skill 目录的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".trae" / "skills" / skill_name
        # global scope: 用户级 skills（注意使用 .trae-cn）
        return PlatformInfo.get_home() / ".trae-cn" / "skills" / skill_name

    def get_mcp_path(self) -> Path:
        """获取 Trae MCP 配置文件路径。

        macOS: ~/Library/Application Support/Trae CN/User/mcp.json
        Windows: %APPDATA%/Trae CN/User/mcp.json

        Returns:
            MCP 配置文件的完整路径
        """
        app_support = PlatformInfo.get_app_support_dir()
        return app_support / "Trae CN" / "User" / "mcp.json"

    # --- 格式转换 ---

    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 Trae 格式。

        Trae 不添加额外头部，直接返回纯内容。

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            原始内容（不添加任何头部）
        """
        return raw_content

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """Trae 不支持全局级 rules。"""
        return False

    # --- 扫描已有配置 ---

    def scan_existing_configs(self) -> dict:
        """扫描 Trae 已有的用户级配置。

        扫描范围：
        - rules: 空列表（Trae 不支持全局级 rules）
        - skills: ~/.trae-cn/skills/ 下的子目录
        - mcp: MCP 配置文件

        Returns:
            {"rules": [], "skills": [...], "mcp": [...]}
        """
        result: dict = {"rules": [], "skills": [], "mcp": []}

        # Trae 不支持全局级 rules，rules 列表始终为空

        # 扫描用户级 skills（注意使用 .trae-cn）
        skills_dir = PlatformInfo.get_home() / ".trae-cn" / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    result["skills"].append(item.name)

        # 扫描 MCP 配置
        try:
            mcp_path = self.get_mcp_path()
            if mcp_path.exists() and mcp_path.is_file():
                result["mcp"].append(str(mcp_path))
        except Exception:
            # 平台不支持时忽略 MCP 扫描
            pass

        return result
