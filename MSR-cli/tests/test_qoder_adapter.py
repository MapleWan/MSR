"""Qoder 适配器单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch

from msr_sync.adapters.qoder import QoderAdapter


@pytest.fixture
def adapter():
    """创建 Qoder 适配器实例"""
    return QoderAdapter()


class TestQoderAdapterProperties:
    """测试 Qoder 适配器基本属性"""

    def test_ide_name(self, adapter):
        """ide_name 应返回 'qoder'"""
        assert adapter.ide_name == "qoder"

    def test_supports_global_rules_false(self, adapter):
        """Qoder 不支持全局级 rules"""
        assert adapter.supports_global_rules() is False


class TestQoderRulesPath:
    """测试 Qoder rules 路径解析 (需求 11.1)"""

    def test_project_scope(self, adapter):
        """项目级 rules 路径: <project>/.qoder/rules/<name>.md"""
        project = Path("/my/project")
        path = adapter.get_rules_path("coding-style", "project", project)
        assert path == project / ".qoder" / "rules" / "coding-style.md"

    def test_global_scope_returns_path(self, adapter):
        """全局 scope 仍返回路径（调用方负责警告）"""
        path = adapter.get_rules_path("coding-style", "global")
        assert path.name == "coding-style.md"
        assert ".qoder" in str(path)
        assert "rules" in str(path)


class TestQoderSkillsPath:
    """测试 Qoder skills 路径解析 (需求 11.2, 11.3)"""

    def test_project_scope(self, adapter):
        """项目级 skills 路径: <project>/.qoder/skills/<name>/"""
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".qoder" / "skills" / "my-skill"

    def test_global_scope(self, adapter):
        """用户级 skills 路径: ~/.qoder/skills/<name>/"""
        path = adapter.get_skills_path("my-skill", "global")
        assert path == Path.home() / ".qoder" / "skills" / "my-skill"


class TestQoderMcpPath:
    """测试 Qoder MCP 路径解析 (需求 11.4, 11.5)"""

    @patch("msr_sync.adapters.qoder.PlatformInfo.get_os", return_value="macos")
    @patch(
        "msr_sync.adapters.qoder.PlatformInfo.get_app_support_dir",
        return_value=Path.home() / "Library" / "Application Support",
    )
    def test_macos_mcp_path(self, mock_app_dir, mock_os, adapter):
        """macOS MCP 路径: ~/Library/Application Support/Qoder/SharedClientCache/mcp.json"""
        path = adapter.get_mcp_path()
        expected = (
            Path.home()
            / "Library"
            / "Application Support"
            / "Qoder"
            / "SharedClientCache"
            / "mcp.json"
        )
        assert path == expected

    @patch("msr_sync.adapters.qoder.PlatformInfo.get_os", return_value="windows")
    @patch(
        "msr_sync.adapters.qoder.PlatformInfo.get_app_support_dir",
        return_value=Path.home() / "AppData" / "Roaming",
    )
    def test_windows_mcp_path(self, mock_app_dir, mock_os, adapter):
        """Windows MCP 路径: %APPDATA%/Qoder/SharedClientCache/mcp.json"""
        path = adapter.get_mcp_path()
        expected = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Qoder"
            / "SharedClientCache"
            / "mcp.json"
        )
        assert path == expected


class TestQoderFormatRuleContent:
    """测试 Qoder format_rule_content (需求 5.1)"""

    def test_adds_qoder_header(self, adapter):
        """应添加 Qoder frontmatter 头部"""
        content = "# My Rule\nSome content here."
        result = adapter.format_rule_content(content)
        assert result.startswith("---\ntrigger: always_on\n---\n")

    def test_preserves_original_content(self, adapter):
        """应保留原始内容"""
        content = "# My Rule\nSome content here."
        result = adapter.format_rule_content(content)
        assert result.endswith(content)

    def test_empty_content(self, adapter):
        """空内容也应添加头部"""
        result = adapter.format_rule_content("")
        assert result == "---\ntrigger: always_on\n---\n"


class TestQoderScanExistingConfigs:
    """测试 Qoder scan_existing_configs"""

    def test_returns_correct_structure(self, adapter, tmp_path):
        """返回值应包含 rules、skills、mcp 三个键"""
        with patch(
            "msr_sync.adapters.qoder.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert "rules" in result
            assert "skills" in result
            assert "mcp" in result

    def test_rules_always_empty(self, adapter, tmp_path):
        """rules 列表始终为空（Qoder 不支持全局 rules）"""
        with patch(
            "msr_sync.adapters.qoder.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["rules"] == []

    def test_scans_user_skills(self, adapter, tmp_path):
        """应扫描 ~/.qoder/skills/ 下的子目录"""
        skills_dir = tmp_path / ".qoder" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-b").mkdir()
        # 文件不应被包含
        (skills_dir / "readme.txt").touch()

        with patch(
            "msr_sync.adapters.qoder.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert sorted(result["skills"]) == ["skill-a", "skill-b"]

    def test_no_skills_dir(self, adapter, tmp_path):
        """skills 目录不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.qoder.PlatformInfo.get_home",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["skills"] == []

    def test_scans_mcp_file(self, adapter, tmp_path):
        """应检测 MCP 配置文件是否存在"""
        mcp_dir = tmp_path / "Qoder" / "SharedClientCache"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "mcp.json"
        mcp_file.write_text('{"servers": {}}')

        with patch(
            "msr_sync.adapters.qoder.PlatformInfo.get_app_support_dir",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert len(result["mcp"]) == 1
            assert "mcp.json" in result["mcp"][0]

    def test_no_mcp_file(self, adapter, tmp_path):
        """MCP 文件不存在时返回空列表"""
        with patch(
            "msr_sync.adapters.qoder.PlatformInfo.get_app_support_dir",
            return_value=tmp_path,
        ):
            result = adapter.scan_existing_configs()
            assert result["mcp"] == []
