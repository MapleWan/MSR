"""Antigravity 适配器单元测试

验证 Antigravity 适配器的路径解析、格式转换和配置扫描。
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from msr_sync.adapters.antigravity import AntigravityAdapter


@pytest.fixture
def adapter():
    """创建 Antigravity 适配器实例"""
    return AntigravityAdapter()


class TestAntigravityAdapterProperties:
    """测试 Antigravity 适配器基本属性"""

    def test_ide_name(self, adapter):
        """ide_name 应返回 'antigravity'"""
        assert adapter.ide_name == "antigravity"

    def test_supports_global_rules_false(self, adapter):
        """Antigravity 不支持全局级 rules"""
        assert adapter.supports_global_rules() is False


class TestAntigravityRulesPath:
    """测试 Antigravity rules 路径解析"""

    def test_project_scope(self, adapter):
        """项目级 rules 路径: <project>/.agents/rules/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_rules_path("coding-style", "project", project)
        assert path == project / ".agents" / "rules" / "coding-style.md"

    def test_project_scope_rules_dir(self, adapter):
        """项目级 rules 路径应在 .agents/rules/ 目录下"""
        project = Path("/my/project")
        path = adapter.get_rules_path("my-rule", "project", project)
        assert path.parent == project / ".agents" / "rules"

    def test_global_scope(self, adapter):
        """全局级 rules 路径: ~/.gemini/rules/<name>.md（虽不支持但仍返回路径）"""
        path = adapter.get_rules_path("coding-style", "global")
        assert path == Path.home() / ".gemini" / "rules" / "coding-style.md"


class TestAntigravitySkillsPath:
    """测试 Antigravity skills (workflows) 路径解析"""

    def test_project_scope(self, adapter):
        """项目级 skills 路径: <project>/.agents/workflows/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".agents" / "workflows" / "my-skill.md"

    def test_global_scope(self, adapter):
        """用户级 skills 路径: ~/.gemini/workflows/<name>.md"""
        path = adapter.get_skills_path("my-skill", "global")
        assert path == Path.home() / ".gemini" / "workflows" / "my-skill.md"


class TestAntigravityMcpPath:
    """测试 Antigravity MCP 路径解析"""

    def test_mcp_path_uses_gemini(self, adapter):
        """MCP 路径: ~/.gemini/antigravity/mcp_config.json"""
        path = adapter.get_mcp_path()
        assert path == Path.home() / ".gemini" / "antigravity" / "mcp_config.json"

    def test_mcp_filename_is_mcp_config_json(self, adapter):
        """MCP 文件名应为 mcp_config.json"""
        path = adapter.get_mcp_path()
        assert path.name == "mcp_config.json"

    @patch(
        "msr_sync.adapters.antigravity.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_macos_mcp_path(self, mock_home, adapter):
        """macOS MCP 路径: ~/.gemini/antigravity/mcp_config.json"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".gemini" / "antigravity" / "mcp_config.json"

    @patch(
        "msr_sync.adapters.antigravity.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_windows_mcp_path(self, mock_home, adapter):
        """Windows MCP 路径: <用户目录>/.gemini/antigravity/mcp_config.json"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".gemini" / "antigravity" / "mcp_config.json"


class TestAntigravityFormatRuleContent:
    """测试 Antigravity format_rule_content"""

    def test_no_header_added(self, adapter):
        """Antigravity rules 不添加额外头部，直接返回纯内容"""
        content = "# My Rule\nSome content here."
        result = adapter.format_rule_content(content)
        assert result == content

    def test_does_not_start_with_frontmatter(self, adapter):
        """结果不应以 frontmatter 分隔符开头"""
        content = "# My Rule\nSome content here."
        result = adapter.format_rule_content(content)
        assert not result.startswith("---\n")

    def test_empty_content(self, adapter):
        """空内容应返回空字符串"""
        result = adapter.format_rule_content("")
        assert result == ""


class TestAntigravityScanExistingConfigs:
    """测试 Antigravity scan_existing_configs"""

    def test_returns_correct_structure(self, adapter, tmp_path):
        """返回值应包含 rules、skills、mcp 三个键"""
        with patch(
            "msr_sync.adapters.antigravity.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert "rules" in result
            assert "skills" in result
            assert "mcp" in result

    def test_does_not_scan_user_rules(self, adapter, tmp_path):
        """不应扫描 rules（Antigravity 不支持全局级多文件 rules）"""
        rules_dir = tmp_path / ".gemini" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rule-a.md").write_text("# Rule A")

        with patch(
            "msr_sync.adapters.antigravity.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["rules"] == []

    def test_scans_user_workflows(self, adapter, tmp_path):
        """应扫描 ~/.gemini/workflows/ 下的 .md 文件"""
        workflows_dir = tmp_path / ".gemini" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "workflow-a.md").write_text("# Workflow A")
        (workflows_dir / "workflow-b.md").write_text("# Workflow B")
        # 非 .md 文件不应被包含
        (workflows_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.antigravity.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["skills"]) == ["workflow-a", "workflow-b"]

    def test_no_workflows_dir(self, adapter, tmp_path):
        """workflows 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.antigravity.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["skills"] == []

    def test_scans_mcp_file(self, adapter, tmp_path):
        """应检测 MCP 配置文件是否存在"""
        mcp_dir = tmp_path / ".gemini" / "antigravity"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "mcp_config.json"
        mcp_file.write_text('{"servers": {}}')

        with patch(
            "msr_sync.adapters.antigravity.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert len(result["mcp"]) == 1
            assert "mcp_config.json" in result["mcp"][0]

    def test_no_mcp_file(self, adapter, tmp_path):
        """MCP 文件不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.antigravity.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["mcp"] == []
