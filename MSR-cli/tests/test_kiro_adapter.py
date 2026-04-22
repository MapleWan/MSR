"""Kiro 适配器单元测试

验证 Kiro 适配器的路径解析、格式转换和配置扫描。
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from msr_sync.adapters.kiro import KiroAdapter


@pytest.fixture
def adapter():
    """创建 Kiro 适配器实例"""
    return KiroAdapter()


class TestKiroAdapterProperties:
    """测试 Kiro 适配器基本属性"""

    def test_ide_name(self, adapter):
        """ide_name 应返回 'kiro'"""
        assert adapter.ide_name == "kiro"

    def test_supports_global_rules_true(self, adapter):
        """Kiro 支持全局级 rules (steering)"""
        assert adapter.supports_global_rules() is True


class TestKiroRulesPath:
    """测试 Kiro rules (steering) 路径解析"""

    def test_project_scope(self, adapter):
        """项目级 rules 路径: <project>/.kiro/steering/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_rules_path("coding-style", "project", project)
        assert path == project / ".kiro" / "steering" / "coding-style.md"

    def test_project_scope_steering_dir(self, adapter):
        """项目级 rules 路径应在 .kiro/steering/ 目录下"""
        project = Path("/my/project")
        path = adapter.get_rules_path("my-rule", "project", project)
        assert path.parent == project / ".kiro" / "steering"

    def test_global_scope(self, adapter):
        """用户级 rules 路径: ~/.kiro/steering/<name>.md"""
        path = adapter.get_rules_path("coding-style", "global")
        assert path == Path.home() / ".kiro" / "steering" / "coding-style.md"

    def test_global_scope_steering_dir(self, adapter):
        """用户级 rules 路径应在 ~/.kiro/steering/ 目录下"""
        path = adapter.get_rules_path("my-rule", "global")
        assert path.parent == Path.home() / ".kiro" / "steering"


class TestKiroSkillsPath:
    """测试 Kiro skills 路径解析"""

    def test_project_scope(self, adapter):
        """项目级 skills 路径: <project>/.kiro/skills/<name>/"""
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".kiro" / "skills" / "my-skill"

    def test_global_scope(self, adapter):
        """用户级 skills 路径: ~/.kiro/skills/<name>/"""
        path = adapter.get_skills_path("my-skill", "global")
        assert path == Path.home() / ".kiro" / "skills" / "my-skill"


class TestKiroMcpPath:
    """测试 Kiro MCP 路径解析"""

    def test_mcp_path_uses_home(self, adapter):
        """MCP 路径: ~/.kiro/mcp.json（macOS 和 Windows 相同）"""
        path = adapter.get_mcp_path()
        assert path == Path.home() / ".kiro" / "mcp.json"

    def test_mcp_path_does_not_use_app_support(self, adapter):
        """MCP 路径不应使用 Application Support 或 AppData"""
        path = adapter.get_mcp_path()
        path_str = str(path)
        assert "Application Support" not in path_str
        assert "AppData" not in path_str

    @patch(
        "msr_sync.adapters.kiro.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_macos_mcp_path(self, mock_home, adapter):
        """macOS MCP 路径: ~/.kiro/mcp.json"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".kiro" / "mcp.json"

    @patch(
        "msr_sync.adapters.kiro.PlatformInfo.get_home",
        return_value=Path("/mock/home"),
    )
    def test_windows_mcp_path(self, mock_home, adapter):
        """Windows MCP 路径: <用户目录>/.kiro/mcp.json（与 macOS 相同）"""
        path = adapter.get_mcp_path()
        assert path == Path("/mock/home") / ".kiro" / "mcp.json"


class TestKiroFormatRuleContent:
    """测试 Kiro format_rule_content"""

    def test_no_header_added(self, adapter):
        """Kiro 不添加额外头部，直接返回纯内容"""
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


class TestKiroScanExistingConfigs:
    """测试 Kiro scan_existing_configs"""

    def test_returns_correct_structure(self, adapter, tmp_path):
        """返回值应包含 rules、skills、mcp 三个键"""
        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert "rules" in result
            assert "skills" in result
            assert "mcp" in result

    def test_scans_user_rules(self, adapter, tmp_path):
        """应扫描 ~/.kiro/steering/ 下的 .md 文件"""
        rules_dir = tmp_path / ".kiro" / "steering"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rule-a.md").write_text("# Rule A")
        (rules_dir / "rule-b.md").write_text("# Rule B")
        # 非 .md 文件不应被包含
        (rules_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["rules"]) == ["rule-a", "rule-b"]

    def test_no_rules_dir(self, adapter, tmp_path):
        """steering 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["rules"] == []

    def test_scans_user_skills(self, adapter, tmp_path):
        """应扫描 ~/.kiro/skills/ 下的子目录"""
        skills_dir = tmp_path / ".kiro" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-b").mkdir()
        # 文件不应被包含
        (skills_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["skills"]) == ["skill-a", "skill-b"]

    def test_no_skills_dir(self, adapter, tmp_path):
        """skills 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["skills"] == []

    def test_scans_mcp_file(self, adapter, tmp_path):
        """应检测 MCP 配置文件是否存在"""
        mcp_dir = tmp_path / ".kiro"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "mcp.json"
        mcp_file.write_text('{"servers": {}}')

        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert len(result["mcp"]) == 1
            assert "mcp.json" in result["mcp"][0]

    def test_no_mcp_file(self, adapter, tmp_path):
        """MCP 文件不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.kiro.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["mcp"] == []
