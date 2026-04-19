"""Qoder IDE 适配器

实现 Qoder（阿里）的路径解析、格式转换和配置扫描。

路径约定：
- 项目级 rules: <project>/.qoder/rules/<name>.md
- 项目级 skills: <project>/.qoder/skills/<name>/
- 用户级 skills: ~/.qoder/skills/<name>/
- MCP: macOS ~/Library/Application Support/Qoder/SharedClientCache/mcp.json
       Windows %APPDATA%/Qoder/SharedClientCache/mcp.json
- 不支持全局级 rules
"""

from pathlib import Path
from typing import Optional

from msr_sync.adapters.base import BaseAdapter
from msr_sync.core.frontmatter import build_qoder_header
from msr_sync.core.platform import PlatformInfo


class QoderAdapter(BaseAdapter):
    """Qoder IDE 适配器"""

    @property
    def ide_name(self) -> str:
        return "qoder"

    # --- 路径解析 ---

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Qoder rule 文件的目标路径。

        Qoder 仅支持项目级 rules。当 scope 为 'global' 时仍返回路径
        （调用方负责检查 supports_global_rules() 并输出警告）。

        Args:
            rule_name: 规则名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            rule 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".qoder" / "rules" / f"{rule_name}.md"
        # global scope: 返回用户主目录下的路径（调用方会检查 supports_global_rules）
        return PlatformInfo.get_home() / ".qoder" / "rules" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Qoder skill 目录的目标路径。

        Args:
            skill_name: 技能名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            skill 目录的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".qoder" / "skills" / skill_name
        # global scope: 用户级 skills
        return PlatformInfo.get_home() / ".qoder" / "skills" / skill_name

    def get_mcp_path(self) -> Path:
        """获取 Qoder MCP 配置文件路径。

        macOS: ~/Library/Application Support/Qoder/SharedClientCache/mcp.json
        Windows: %APPDATA%/Qoder/SharedClientCache/mcp.json

        Returns:
            MCP 配置文件的完整路径
        """
        app_support = PlatformInfo.get_app_support_dir()
        return app_support / "Qoder" / "SharedClientCache" / "mcp.json"

    # --- 格式转换 ---

    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 Qoder 格式。

        添加 Qoder 的 frontmatter 模板头部：
        ---
        trigger: always_on
        ---

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            添加了 Qoder 头部的完整内容
        """
        return build_qoder_header() + raw_content

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """Qoder 不支持全局级 rules。"""
        return False

    # --- 扫描已有配置 ---

    def scan_existing_configs(self) -> dict:
        """扫描 Qoder 已有的用户级配置。

        扫描范围：
        - rules: 空列表（Qoder 不支持全局级 rules）
        - skills: ~/.qoder/skills/ 下的子目录
        - mcp: MCP 配置文件

        Returns:
            {"rules": [], "skills": [...], "mcp": [...]}
        """
        result: dict = {"rules": [], "skills": [], "mcp": []}

        # Qoder 不支持全局级 rules，rules 列表始终为空

        # 扫描用户级 skills
        skills_dir = PlatformInfo.get_home() / ".qoder" / "skills"
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
