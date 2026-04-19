"""CodeBuddy 适配器单元测试

验证需求: 5.4, 11.16, 11.17, 11.18, 11.19, 11.20, 11.21
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from msr_sync.adapters.codebuddy import CodeBuddyAdapter


@pytest.fixture
def adapter():
    """创建 CodeBuddy 适配器实例"""
    return CodeBuddyAdapter()


class TestCodeBuddyAdapterProperties:
    """测试 CodeBuddy 适配器基本属性"""

    def test_ide_name(self, adapter):
        """ide_name 应返回 'codebuddy'"""
        assert adapter.ide_name == "codebuddy"

    def test_supports_global_rules_true(self, adapter):
        """CodeBuddy 支持全局级 rules（唯一支持的 IDE）"""
        assert adapter.supports_global_rules() is True


class TestCodeBuddyRulesPath:
    """测试 CodeBuddy rules 路径解析 (需求 11.16, 11.17)"""

    def test_project_scope(self, adapter):
        """项目级 rules 路径: <project>/.codebuddy/rules/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_rules_path("coding-style", "project", project)
        assert path == project / ".codebuddy" / "rules" / "coding-style.md"

    def test_project_scope_rules_dir(self, adapter):
        """项目级 rules 路径应在 .codebuddy/rules/ 目录下"""
        project = Path("/my/project")
        path = adapter.get_rules_path("my-rule", "project", project)
        assert path.parent == project / ".codebuddy" / "rules"

    def test_global_scope(self, adapter):
        """用户级 rules 路径: ~/.codebuddy/rules/<name>.md"""
        path = adapter.get_rules_path("coding-style", "global")
        assert path == Path.home() / ".codebuddy" / "rules" / "coding-style.md"

    def test_global_scope_rules_dir(self, adapter):
        """用户级 rules 路径应在 ~/.codebuddy/rules/ 目录下"""
        path = adapter.get_rules_path("my-rule", "global")
        assert path.parent == Path.home() / ".codebuddy" / "rules"


class TestCodeBuddySkillsPath:
    """测试 CodeBuddy skills 路径解析 (需求 11.18, 11.19)"""

    def test_project_scope(self, adapter):
        """项目级 skills 路径: <project>/.codebuddy/skills/<name>/"""
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".codebuddy" / "skills" / "my-skill"

    def test_global_scope(self, adapter):
        """用户级 skills 路径: ~/.codebuddy/skills/<name>/"""
        path = adapter.get_skills_path("my-skill", "global")
        assert path == Path.home() / ".codebuddy" / "skills" / "my-skill"


class TestCodeBuddyMcpPath:
    """测试 CodeBuddy MCP 路径解析 (需求 11.20, 11.21)"""

    def test_mcp_path_uses_home(self, adapter):
        """MCP 路径: ~/.codebuddy/mcp.json（macOS 和 Windows 相同）"""
        path = adapter.get_mcp_path()
        assert path == Path.home() / ".codebuddy" / "mcp.json"

    def test_mcp_path_does_not_use_app_support(self, adapter):
        """MCP 路径不应使用 Application Support 或 AppData"""
        path = adapter.get_mcp_path()
        path_str = str(path)
        assert "Application Support" not in path_str
        assert "AppData" not in path_str

    @patch(
        "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_macos_mcp_path(self, mock_home, adapter):
        """macOS MCP 路径: ~/.codebuddy/mcp.json"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".codebuddy" / "mcp.json"

    @patch(
        "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_windows_mcp_path(self, mock_home, adapter):
        """Windows MCP 路径: <用户目录>/.codebuddy/mcp.json（与 macOS 相同）"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".codebuddy" / "mcp.json"


class TestCodeBuddyFormatRuleContent:
    """测试 CodeBuddy format_rule_content (需求 5.4)"""

    def test_adds_codebuddy_header(self, adapter):
        """应添加 CodeBuddy frontmatter 头部"""
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
        # 时间戳格式应为 ISO 8601
        assert "updatedAt:" in result


class TestCodeBuddyScanExistingConfigs:
    """测试 CodeBuddy scan_existing_configs"""

    def test_returns_correct_structure(self, adapter, tmp_path):
        """返回值应包含 rules、skills、mcp 三个键"""
        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert "rules" in result
            assert "skills" in result
            assert "mcp" in result

    def test_scans_user_rules(self, adapter, tmp_path):
        """应扫描 ~/.codebuddy/rules/ 下的 .md 文件（CodeBuddy 支持全局 rules）"""
        rules_dir = tmp_path / ".codebuddy" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rule-a.md").write_text("# Rule A")
        (rules_dir / "rule-b.md").write_text("# Rule B")
        # 非 .md 文件不应被包含
        (rules_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["rules"]) == ["rule-a", "rule-b"]

    def test_no_rules_dir(self, adapter, tmp_path):
        """rules 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["rules"] == []

    def test_scans_user_skills(self, adapter, tmp_path):
        """应扫描 ~/.codebuddy/skills/ 下的子目录"""
        skills_dir = tmp_path / ".codebuddy" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-b").mkdir()
        # 文件不应被包含
        (skills_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["skills"]) == ["skill-a", "skill-b"]

    def test_no_skills_dir(self, adapter, tmp_path):
        """skills 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["skills"] == []

    def test_scans_mcp_file(self, adapter, tmp_path):
        """应检测 MCP 配置文件是否存在"""
        mcp_dir = tmp_path / ".codebuddy"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "mcp.json"
        mcp_file.write_text('{"servers": {}}')

        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert len(result["mcp"]) == 1
            assert "mcp.json" in result["mcp"][0]

    def test_no_mcp_file(self, adapter, tmp_path):
        """MCP 文件不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.codebuddy.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["mcp"] == []
