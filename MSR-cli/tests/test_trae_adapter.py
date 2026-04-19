"""Trae 适配器单元测试

验证需求: 5.3, 11.11, 11.12, 11.13, 11.14, 11.15
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from msr_sync.adapters.trae import TraeAdapter


@pytest.fixture
def adapter():
    """创建 Trae 适配器实例"""
    return TraeAdapter()


class TestTraeAdapterProperties:
    """测试 Trae 适配器基本属性"""

    def test_ide_name(self, adapter):
        """ide_name 应返回 'trae'"""
        assert adapter.ide_name == "trae"

    def test_supports_global_rules_false(self, adapter):
        """Trae 不支持全局级 rules"""
        assert adapter.supports_global_rules() is False


class TestTraeRulesPath:
    """测试 Trae rules 路径解析 (需求 11.11)"""

    def test_project_scope(self, adapter):
        """项目级 rules 路径: <project>/.trae/rules/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_rules_path("coding-style", "project", project)
        assert path == project / ".trae" / "rules" / "coding-style.md"

    def test_global_scope_returns_path(self, adapter):
        """全局 scope 仍返回路径（调用方负责警告）"""
        path = adapter.get_rules_path("coding-style", "global")
        assert path.name == "coding-style.md"
        assert ".trae" in str(path)
        assert "rules" in str(path)


class TestTraeSkillsPath:
    """测试 Trae skills 路径解析 (需求 11.12, 11.13)"""

    def test_project_scope(self, adapter):
        """项目级 skills 路径: <project>/.trae/skills/<name>/"""
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".trae" / "skills" / "my-skill"

    def test_global_scope(self, adapter):
        """用户级 skills 路径: ~/.trae-cn/skills/<name>/ (注意: trae-cn)"""
        path = adapter.get_skills_path("my-skill", "global")
        assert path == Path.home() / ".trae-cn" / "skills" / "my-skill"

    def test_global_scope_uses_trae_cn(self, adapter):
        """用户级 skills 路径必须使用 .trae-cn 而非 .trae"""
        path = adapter.get_skills_path("my-skill", "global")
        assert ".trae-cn" in str(path)
        # 确保不是 .trae/（不含 -cn）
        path_str = str(path)
        # 找到 .trae-cn 后确认它不是 .trae/
        assert "/.trae-cn/" in path_str or "\\.trae-cn\\" in path_str


class TestTraeMcpPath:
    """测试 Trae MCP 路径解析 (需求 11.14, 11.15)"""

    @patch("msr_sync.adapters.trae.PlatformInfo.get_os", return_value="macos")
    @patch(
        "msr_sync.adapters.trae.PlatformInfo.get_app_support_dir",
        return_value=Path.home() / "Library" / "Application Support",
    )
    def test_macos_mcp_path(self, mock_app_dir, mock_os, adapter):
        """macOS MCP 路径: ~/Library/Application Support/Trae CN/User/mcp.json"""
        path = adapter.get_mcp_path()
        expected = (
            Path.home()
            / "Library"
            / "Application Support"
            / "Trae CN"
            / "User"
            / "mcp.json"
        )
        assert path == expected

    @patch("msr_sync.adapters.trae.PlatformInfo.get_os", return_value="windows")
    @patch(
        "msr_sync.adapters.trae.PlatformInfo.get_app_support_dir",
        return_value=Path.home() / "AppData" / "Roaming",
    )
    def test_windows_mcp_path(self, mock_app_dir, mock_os, adapter):
        """Windows MCP 路径: %APPDATA%/Trae CN/User/mcp.json"""
        path = adapter.get_mcp_path()
        expected = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Trae CN"
            / "User"
            / "mcp.json"
        )
        assert path == expected


class TestTraeFormatRuleContent:
    """测试 Trae format_rule_content (需求 5.3)"""

    def test_no_header_added(self, adapter):
        """Trae 不添加额外头部，直接返回纯内容"""
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


class TestTraeScanExistingConfigs:
    """测试 Trae scan_existing_configs"""

    def test_returns_correct_structure(self, adapter, tmp_path):
        """返回值应包含 rules、skills、mcp 三个键"""
        with patch(
            "msr_sync.adapters.trae.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert "rules" in result
            assert "skills" in result
            assert "mcp" in result

    def test_rules_always_empty(self, adapter, tmp_path):
        """rules 列表始终为空（Trae 不支持全局 rules）"""
        with patch(
            "msr_sync.adapters.trae.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["rules"] == []

    def test_scans_user_skills(self, adapter, tmp_path):
        """应扫描 ~/.trae-cn/skills/ 下的子目录（注意: trae-cn）"""
        skills_dir = tmp_path / ".trae-cn" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-b").mkdir()
        # 文件不应被包含
        (skills_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.trae.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["skills"]) == ["skill-a", "skill-b"]

    def test_no_skills_dir(self, adapter, tmp_path):
        """skills 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.trae.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["skills"] == []

    def test_scans_mcp_file(self, adapter, tmp_path):
        """应检测 MCP 配置文件是否存在"""
        mcp_dir = tmp_path / "Trae CN" / "User"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "mcp.json"
        mcp_file.write_text('{"servers": {}}')

        with patch(
            "msr_sync.adapters.trae.PlatformInfo.get_app_support_dir",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert len(result["mcp"]) == 1
            assert "mcp.json" in result["mcp"][0]

    def test_no_mcp_file(self, adapter, tmp_path):
        """MCP 文件不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.trae.PlatformInfo.get_app_support_dir",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["mcp"] == []
