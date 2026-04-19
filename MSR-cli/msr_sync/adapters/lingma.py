"""Lingma IDE 适配器

实现 Lingma（阿里）的路径解析、格式转换和配置扫描。

路径约定：
- 项目级 rules: <project>/.lingma/rules/<name>.md
- 项目级 skills: <project>/.lingma/skills/<name>/
- 用户级 skills: ~/.lingma/skills/<name>/
- MCP: macOS ~/Library/Application Support/Lingma/SharedClientCache/mcp.json
       Windows %APPDATA%/Lingma/SharedClientCache/mcp.json
- 不支持全局级 rules
"""

from pathlib import Path
from typing import Optional

from msr_sync.adapters.base import BaseAdapter
from msr_sync.core.frontmatter import build_lingma_header
from msr_sync.core.platform import PlatformInfo


class LingmaAdapter(BaseAdapter):
    """Lingma IDE 适配器"""

    @property
    def ide_name(self) -> str:
        return "lingma"

    # --- 路径解析 ---

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Lingma rule 文件的目标路径。

        Lingma 仅支持项目级 rules。当 scope 为 'global' 时仍返回路径
        （调用方负责检查 supports_global_rules() 并输出警告）。

        Args:
            rule_name: 规则名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            rule 文件的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".lingma" / "rules" / f"{rule_name}.md"
        # global scope: 返回用户主目录下的路径（调用方会检查 supports_global_rules）
        return PlatformInfo.get_home() / ".lingma" / "rules" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        """获取 Lingma skill 目录的目标路径。

        Args:
            skill_name: 技能名称
            scope: 'project' 或 'global'
            project_dir: 项目目录路径

        Returns:
            skill 目录的完整目标路径
        """
        if scope == "project" and project_dir is not None:
            return project_dir / ".lingma" / "skills" / skill_name
        # global scope: 用户级 skills
        return PlatformInfo.get_home() / ".lingma" / "skills" / skill_name

    def get_mcp_path(self) -> Path:
        """获取 Lingma MCP 配置文件路径。

        macOS: ~/Library/Application Support/Lingma/SharedClientCache/mcp.json
        Windows: %APPDATA%/Lingma/SharedClientCache/mcp.json

        Returns:
            MCP 配置文件的完整路径
        """
        app_support = PlatformInfo.get_app_support_dir()
        return app_support / "Lingma" / "SharedClientCache" / "mcp.json"

    # --- 格式转换 ---

    def format_rule_content(self, raw_content: str) -> str:
        """将原始 rule 内容转换为 Lingma 格式。

        添加 Lingma 的 frontmatter 模板头部：
        ---
        trigger: always_on
        ---

        Args:
            raw_content: 已剥离原始 frontmatter 的纯 Markdown 内容

        Returns:
            添加了 Lingma 头部的完整内容
        """
        return build_lingma_header() + raw_content

    # --- 能力查询 ---

    def supports_global_rules(self) -> bool:
        """Lingma 不支持全局级 rules。"""
        return False

    # --- 扫描已有配置 ---

    def scan_existing_configs(self) -> dict:
        """扫描 Lingma 已有的用户级配置。

        扫描范围：
        - rules: 空列表（Lingma 不支持全局级 rules）
        - skills: ~/.lingma/skills/ 下的子目录
        - mcp: MCP 配置文件

        Returns:
            {"rules": [], "skills": [...], "mcp": [...]}
        """
        result: dict = {"rules": [], "skills": [], "mcp": []}

        # Lingma 不支持全局级 rules，rules 列表始终为空

        # 扫描用户级 skills
        skills_dir = PlatformInfo.get_home() / ".lingma" / "skills"
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
