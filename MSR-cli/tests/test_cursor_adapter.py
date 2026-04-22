"""Cursor 适配器单元测试

验证 Cursor 适配器的路径解析、格式转换和配置扫描。
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from msr_sync.adapters.cursor import CursorAdapter


@pytest.fixture
def adapter():
    """创建 Cursor 适配器实例"""
    return CursorAdapter()


class TestCursorAdapterProperties:
    """测试 Cursor 适配器基本属性"""

    def test_ide_name(self, adapter):
        """ide_name 应返回 'cursor'"""
        assert adapter.ide_name == "cursor"

    def test_supports_global_rules_false(self, adapter):
        """Cursor 不支持全局级 rules"""
        assert adapter.supports_global_rules() is False


class TestCursorRulesPath:
    """测试 Cursor rules 路径解析"""

    def test_project_scope(self, adapter):
        """项目级 rules 路径: <project>/.cursor/rules/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_rules_path("coding-style", "project", project)
        assert path == project / ".cursor" / "rules" / "coding-style.md"

    def test_project_scope_rules_dir(self, adapter):
        """项目级 rules 路径应在 .cursor/rules/ 目录下"""
        project = Path("/my/project")
        path = adapter.get_rules_path("my-rule", "project", project)
        assert path.parent == project / ".cursor" / "rules"

    def test_global_scope(self, adapter):
        """用户级 rules 路径: ~/.cursor/rules/<name>.md"""
        path = adapter.get_rules_path("coding-style", "global")
        assert path == Path.home() / ".cursor" / "rules" / "coding-style.md"

    def test_global_scope_rules_dir(self, adapter):
        """用户级 rules 路径应在 ~/.cursor/rules/ 目录下"""
        path = adapter.get_rules_path("my-rule", "global")
        assert path.parent == Path.home() / ".cursor" / "rules"


class TestCursorSkillsPath:
    """测试 Cursor skills 路径解析"""

    def test_project_scope(self, adapter):
        """项目级 skills 路径: <project>/.cursor/skills/<name>/"""
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".cursor" / "skills" / "my-skill"

    def test_global_scope(self, adapter):
        """用户级 skills 路径: ~/.cursor/skills/<name>/"""
        path = adapter.get_skills_path("my-skill", "global")
        assert path == Path.home() / ".cursor" / "skills" / "my-skill"


class TestCursorMcpPath:
    """测试 Cursor MCP 路径解析"""

    def test_mcp_path_uses_home(self, adapter):
        """MCP 路径: ~/.cursor/mcp.json（macOS 和 Windows 相同）"""
        path = adapter.get_mcp_path()
        assert path == Path.home() / ".cursor" / "mcp.json"

    def test_mcp_path_does_not_use_app_support(self, adapter):
        """MCP 路径不应使用 Application Support 或 AppData"""
        path = adapter.get_mcp_path()
        path_str = str(path)
        assert "Application Support" not in path_str
        assert "AppData" not in path_str

    @patch(
        "msr_sync.adapters.cursor.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_macos_mcp_path(self, mock_home, adapter):
        """macOS MCP 路径: ~/.cursor/mcp.json"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".cursor" / "mcp.json"

    @patch(
        "msr_sync.adapters.cursor.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_windows_mcp_path(self, mock_home, adapter):
        """Windows MCP 路径: <用户目录>/.cursor/mcp.json（与 macOS 相同）"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".cursor" / "mcp.json"


class TestCursorFormatRuleContent:
    """测试 Cursor format_rule_content"""

    def test_adds_cursor_header(self, adapter):
        """应添加 Cursor frontmatter 头部"""
        content = "# My Rule\nSome content here."
        result = adapter.format_rule_content(content)
        assert result.startswith("---\n")
        assert "alwaysApply: true" in result
        assert "enabled: true" in result
        assert "updatedAt:" in result
        assert "description:" in result
        assert "provider:" in result

    def test_preserves_original_content(self, adapter):
        """应保留原始内容"""
        content = "# My Rule\nSome content here."
        result = adapter.format_rule_content(content)
        assert result.endswith(content)

    def test_empty_content(self, adapter):
        """空内容也应添加头部"""
        result = adapter.format_rule_content("")
        assert result.startswith("---\n")
        assert "alwaysApply: true" in result
        assert result.endswith("---\n")

    def test_header_contains_timestamp(self, adapter):
        """头部应包含 updatedAt 时间戳"""
        result = adapter.format_rule_content("test")
        assert "updatedAt:" in result


class TestCursorScanExistingConfigs:
    """测试 Cursor scan_existing_configs"""

    def test_returns_correct_structure(self, adapter, tmp_path):
        """返回值应包含 rules、skills、mcp 三个键"""
        with patch(
            "msr_sync.adapters.cursor.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert "rules" in result
            assert "skills" in result
            assert "mcp" in result

    def test_does_not_scan_user_rules(self, adapter, tmp_path):
        """不应扫描 ~/.cursor/rules/ 下的 .md 文件（Cursor 不支持全局 rules）"""
        rules_dir = tmp_path / ".cursor" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rule-a.md").write_text("# Rule A")

        with patch(
            "msr_sync.adapters.cursor.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["rules"] == []

    def test_scans_user_skills(self, adapter, tmp_path):
        """应扫描 ~/.cursor/skills/ 下的子目录"""
        skills_dir = tmp_path / ".cursor" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-b").mkdir()
        # 文件不应被包含
        (skills_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.cursor.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["skills"]) == ["skill-a", "skill-b"]

    def test_no_skills_dir(self, adapter, tmp_path):
        """skills 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.cursor.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["skills"] == []

    def test_scans_mcp_file(self, adapter, tmp_path):
        """应检测 MCP 配置文件是否存在"""
        mcp_dir = tmp_path / ".cursor"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "mcp.json"
        mcp_file.write_text('{"servers": {}}')

        with patch(
            "msr_sync.adapters.cursor.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert len(result["mcp"]) == 1
            assert "mcp.json" in result["mcp"][0]

    def test_no_mcp_file(self, adapter, tmp_path):
        """MCP 文件不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.cursor.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["mcp"] == []
