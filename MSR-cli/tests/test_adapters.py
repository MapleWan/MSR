"""跨适配器属性测试与单元测试

Property 10: IDE 路径解析正确性
单元测试: 跨适配器一致性验证

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.6, 11.1 - 11.21**
"""

import pytest
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from msr_sync.adapters.base import BaseAdapter
from msr_sync.adapters.registry import (
    get_adapter,
    get_all_adapters,
    resolve_ide_list,
)
from msr_sync.adapters.qoder import QoderAdapter
from msr_sync.adapters.lingma import LingmaAdapter
from msr_sync.adapters.trae import TraeAdapter
from msr_sync.adapters.codebuddy import CodeBuddyAdapter
from msr_sync.adapters.cursor import CursorAdapter


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Valid config names: alphanumeric + hyphens, non-empty
config_name_strategy = st.from_regex(r"[a-z][a-z0-9\-]{0,29}", fullmatch=True)

ide_name_strategy = st.sampled_from(["qoder", "lingma", "trae", "codebuddy", "cursor"])

scope_strategy = st.sampled_from(["project", "global"])

config_type_strategy = st.sampled_from(["rules", "skills"])


# ---------------------------------------------------------------------------
# Expected path patterns per IDE
# ---------------------------------------------------------------------------

def _expected_rules_path(
    ide: str, name: str, scope: str, project_dir: Path, home: Path
) -> Path:
    """Return the expected rules path based on requirements 11.1-11.21."""
    ide_dot_dirs = {
        "qoder": ".qoder",
        "lingma": ".lingma",
        "trae": ".trae",
        "codebuddy": ".codebuddy",
        "cursor": ".cursor",
    }
    dot_dir = ide_dot_dirs[ide]
    if scope == "project":
        return project_dir / dot_dir / "rules" / f"{name}.md"
    else:
        return home / dot_dir / "rules" / f"{name}.md"


def _expected_skills_path(
    ide: str, name: str, scope: str, project_dir: Path, home: Path
) -> Path:
    """Return the expected skills path based on requirements 11.1-11.21."""
    if scope == "project":
        ide_dot_dirs = {
            "qoder": ".qoder",
            "lingma": ".lingma",
            "trae": ".trae",
            "codebuddy": ".codebuddy",
            "cursor": ".cursor",
        }
        return project_dir / ide_dot_dirs[ide] / "skills" / name
    else:
        # Global skills paths differ per IDE
        global_skills_dirs = {
            "qoder": ".qoder",
            "lingma": ".lingma",
            "trae": ".trae-cn",       # Trae uses .trae-cn for global
            "codebuddy": ".codebuddy",
            "cursor": ".cursor",
        }
        return home / global_skills_dirs[ide] / "skills" / name


# ---------------------------------------------------------------------------
# Property 10: IDE 路径解析正确性
# ---------------------------------------------------------------------------

class TestProperty10IDEPathResolution:
    """Property 10: IDE 路径解析正确性

    对任意合法的 (IDE, 配置类型, 层级, 项目目录) 组合，
    适配器解析出的路径与需求文档定义的路径模式完全匹配。

    **Validates: Requirements 11.1 - 11.21**
    """

    @given(
        ide_name=ide_name_strategy,
        config_name=config_name_strategy,
        scope=scope_strategy,
    )
    @settings(max_examples=100)
    def test_rules_path_matches_expected_pattern(
        self, ide_name: str, config_name: str, scope: str
    ):
        """Rules 路径应与需求文档定义的模式匹配。

        **Validates: Requirements 11.1, 11.6, 11.11, 11.16, 11.17**
        """
        home = Path("/mock/home")
        project_dir = Path("/mock/project")

        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter(ide_name)
            if scope == "project":
                actual = adapter.get_rules_path(config_name, scope, project_dir)
            else:
                actual = adapter.get_rules_path(config_name, scope)

            expected = _expected_rules_path(
                ide_name, config_name, scope, project_dir, home
            )
            assert actual == expected, (
                f"IDE={ide_name}, scope={scope}, name={config_name}: "
                f"expected {expected}, got {actual}"
            )

    @given(
        ide_name=ide_name_strategy,
        config_name=config_name_strategy,
        scope=scope_strategy,
    )
    @settings(max_examples=100)
    def test_skills_path_matches_expected_pattern(
        self, ide_name: str, config_name: str, scope: str
    ):
        """Skills 路径应与需求文档定义的模式匹配。

        **Validates: Requirements 11.2, 11.3, 11.7, 11.8, 11.12, 11.13, 11.18, 11.19**
        """
        home = Path("/mock/home")
        project_dir = Path("/mock/project")

        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter(ide_name)
            if scope == "project":
                actual = adapter.get_skills_path(config_name, scope, project_dir)
            else:
                actual = adapter.get_skills_path(config_name, scope)

            expected = _expected_skills_path(
                ide_name, config_name, scope, project_dir, home
            )
            assert actual == expected, (
                f"IDE={ide_name}, scope={scope}, name={config_name}: "
                f"expected {expected}, got {actual}"
            )


# ---------------------------------------------------------------------------
# Helper to create fresh adapter instances (bypass registry cache)
# ---------------------------------------------------------------------------

def _create_fresh_adapter(ide_name: str) -> BaseAdapter:
    """Create a fresh adapter instance without using the registry cache."""
    adapters = {
        "qoder": QoderAdapter,
        "lingma": LingmaAdapter,
        "trae": TraeAdapter,
        "codebuddy": CodeBuddyAdapter,
        "cursor": CursorAdapter,
    }
    return adapters[ide_name]()


# ---------------------------------------------------------------------------
# Cross-adapter unit tests (Task 7.7)
# ---------------------------------------------------------------------------

class TestAllAdaptersAreBaseAdapter:
    """所有适配器应为 BaseAdapter 的实例"""

    @pytest.mark.parametrize("ide_name", ["qoder", "lingma", "trae", "codebuddy", "cursor"])
    def test_adapter_is_base_adapter_instance(self, ide_name):
        """每个注册的适配器都应是 BaseAdapter 的子类实例"""
        adapter = get_adapter(ide_name)
        assert isinstance(adapter, BaseAdapter)

    @pytest.mark.parametrize("ide_name", ["qoder", "lingma", "trae", "codebuddy", "cursor"])
    def test_adapter_ide_name_matches(self, ide_name):
        """适配器的 ide_name 属性应与注册名一致"""
        adapter = get_adapter(ide_name)
        assert adapter.ide_name == ide_name


class TestResolveIdeList:
    """测试 resolve_ide_list 对 'all' 的展开和单个 IDE 的解析"""

    def test_all_expands_to_five_adapters(self):
        """'all' 应展开为所有 5 个适配器"""
        adapters = resolve_ide_list(("all",))
        assert len(adapters) == 5
        names = {a.ide_name for a in adapters}
        assert names == {"qoder", "lingma", "trae", "codebuddy", "cursor"}

    def test_single_ide(self):
        """单个 IDE 名称应返回对应的适配器"""
        adapters = resolve_ide_list(("trae",))
        assert len(adapters) == 1
        assert adapters[0].ide_name == "trae"

    def test_multiple_ides(self):
        """多个 IDE 名称应返回对应的适配器列表"""
        adapters = resolve_ide_list(("qoder", "codebuddy", "cursor"))
        assert len(adapters) == 3
        names = {a.ide_name for a in adapters}
        assert names == {"qoder", "codebuddy", "cursor"}

    def test_all_overrides_individual(self):
        """包含 'all' 时应忽略其他个别 IDE 名称，返回全部"""
        adapters = resolve_ide_list(("trae", "all"))
        assert len(adapters) == 5

    def test_invalid_ide_raises(self):
        """不支持的 IDE 名称应抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的 IDE"):
            resolve_ide_list(("nonexistent",))


class TestSupportsGlobalRules:
    """测试各 IDE 的 supports_global_rules 返回值

    **Validates: Requirements 5.6**
    """

    @pytest.mark.parametrize(
        "ide_name, expected",
        [
            ("qoder", False),
            ("lingma", False),
            ("trae", False),
            ("codebuddy", True),
            ("cursor", False),
        ],
    )
    def test_supports_global_rules(self, ide_name, expected):
        """只有 CodeBuddy 支持全局级 rules"""
        adapter = _create_fresh_adapter(ide_name)
        assert adapter.supports_global_rules() is expected


class TestRulesPathProjectScope:
    """测试各 IDE 的项目级 rules 路径解析

    **Validates: Requirements 11.1, 11.6, 11.11, 11.16**
    """

    @pytest.mark.parametrize(
        "ide_name, dot_dir",
        [
            ("qoder", ".qoder"),
            ("lingma", ".lingma"),
            ("trae", ".trae"),
            ("codebuddy", ".codebuddy"),
            ("cursor", ".cursor"),
        ],
    )
    def test_project_rules_path(self, ide_name, dot_dir):
        """项目级 rules 路径: <project>/.<ide>/rules/<name>.md"""
        adapter = _create_fresh_adapter(ide_name)
        project = Path("/test/project")
        path = adapter.get_rules_path("my-rule", "project", project)
        assert path == project / dot_dir / "rules" / "my-rule.md"


class TestRulesPathGlobalScope:
    """测试各 IDE 的全局级 rules 路径解析

    **Validates: Requirements 11.17**
    """

    @pytest.mark.parametrize(
        "ide_name, dot_dir",
        [
            ("qoder", ".qoder"),
            ("lingma", ".lingma"),
            ("trae", ".trae"),
            ("codebuddy", ".codebuddy"),
            ("cursor", ".cursor"),
        ],
    )
    def test_global_rules_path(self, ide_name, dot_dir):
        """全局级 rules 路径: ~/.<ide>/rules/<name>.md"""
        home = Path("/mock/home")
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter(ide_name)
            path = adapter.get_rules_path("my-rule", "global")
            assert path == home / dot_dir / "rules" / "my-rule.md"


class TestSkillsPathProjectScope:
    """测试各 IDE 的项目级 skills 路径解析

    **Validates: Requirements 11.2, 11.7, 11.12, 11.18**
    """

    @pytest.mark.parametrize(
        "ide_name, dot_dir",
        [
            ("qoder", ".qoder"),
            ("lingma", ".lingma"),
            ("trae", ".trae"),
            ("codebuddy", ".codebuddy"),
            ("cursor", ".cursor"),
        ],
    )
    def test_project_skills_path(self, ide_name, dot_dir):
        """项目级 skills 路径: <project>/.<ide>/skills/<name>/"""
        adapter = _create_fresh_adapter(ide_name)
        project = Path("/test/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / dot_dir / "skills" / "my-skill"


class TestSkillsPathGlobalScope:
    """测试各 IDE 的全局级 skills 路径解析

    **Validates: Requirements 11.3, 11.8, 11.13, 11.19**
    """

    @pytest.mark.parametrize(
        "ide_name, global_dot_dir",
        [
            ("qoder", ".qoder"),
            ("lingma", ".lingma"),
            ("trae", ".trae-cn"),       # Trae 全局 skills 使用 .trae-cn
            ("codebuddy", ".codebuddy"),
            ("cursor", ".cursor"),
        ],
    )
    def test_global_skills_path(self, ide_name, global_dot_dir):
        """全局级 skills 路径: ~/.<ide-global>/skills/<name>/"""
        home = Path("/mock/home")
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter(ide_name)
            path = adapter.get_skills_path("my-skill", "global")
            assert path == home / global_dot_dir / "skills" / "my-skill"


class TestMcpPathMacOS:
    """测试各 IDE 在 macOS 上的 MCP 路径解析

    **Validates: Requirements 11.4, 11.9, 11.14, 11.20**
    """

    @pytest.mark.parametrize(
        "ide_name, expected_subpath",
        [
            ("qoder", "Qoder/SharedClientCache/mcp.json"),
            ("lingma", "Lingma/SharedClientCache/mcp.json"),
            ("trae", "Trae CN/User/mcp.json"),
        ],
    )
    def test_macos_mcp_path_app_support(self, ide_name, expected_subpath):
        """macOS MCP 路径: ~/Library/Application Support/<IDE-specific>/mcp.json"""
        home = Path("/mock/home")
        app_support = home / "Library" / "Application Support"
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_app_support_dir",
            return_value=app_support,
        ):
            adapter = _create_fresh_adapter(ide_name)
            path = adapter.get_mcp_path()
            assert path == app_support / expected_subpath

    def test_codebuddy_macos_mcp_path(self):
        """CodeBuddy macOS MCP 路径: ~/.codebuddy/mcp.json"""
        home = Path("/mock/home")
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter("codebuddy")
            path = adapter.get_mcp_path()
            assert path == home / ".codebuddy" / "mcp.json"

    def test_cursor_macos_mcp_path(self):
        """Cursor macOS MCP 路径: ~/.cursor/mcp.json"""
        home = Path("/mock/home")
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter("cursor")
            path = adapter.get_mcp_path()
            assert path == home / ".cursor" / "mcp.json"


class TestMcpPathWindows:
    """测试各 IDE 在 Windows 上的 MCP 路径解析

    **Validates: Requirements 11.5, 11.10, 11.15, 11.21**
    """

    @pytest.mark.parametrize(
        "ide_name, expected_subpath",
        [
            ("qoder", "Qoder/SharedClientCache/mcp.json"),
            ("lingma", "Lingma/SharedClientCache/mcp.json"),
            ("trae", "Trae CN/User/mcp.json"),
        ],
    )
    def test_windows_mcp_path_appdata(self, ide_name, expected_subpath):
        """Windows MCP 路径: %APPDATA%/<IDE-specific>/mcp.json"""
        home = Path("/mock/home")
        appdata = home / "AppData" / "Roaming"
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_app_support_dir",
            return_value=appdata,
        ):
            adapter = _create_fresh_adapter(ide_name)
            path = adapter.get_mcp_path()
            assert path == appdata / expected_subpath

    def test_codebuddy_windows_mcp_path(self):
        """CodeBuddy Windows MCP 路径: ~/.codebuddy/mcp.json (跨平台统一)"""
        home = Path("/mock/home")
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter("codebuddy")
            path = adapter.get_mcp_path()
            assert path == home / ".codebuddy" / "mcp.json"

    def test_cursor_windows_mcp_path(self):
        """Cursor Windows MCP 路径: ~/.cursor/mcp.json (跨平台统一)"""
        home = Path("/mock/home")
        with patch(
            "msr_sync.core.platform.PlatformInfo.get_home",
            return_value=home,
        ):
            adapter = _create_fresh_adapter("cursor")
            path = adapter.get_mcp_path()
            assert path == home / ".cursor" / "mcp.json"


class TestFormatRuleContent:
    """测试各 IDE 的 format_rule_content 输出格式

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """

    def test_qoder_adds_trigger_header(self):
        """Qoder: 添加 trigger: always_on 头部 (需求 5.1)"""
        adapter = _create_fresh_adapter("qoder")
        result = adapter.format_rule_content("# Rule\nContent")
        assert result.startswith("---\ntrigger: always_on\n---\n")
        assert result.endswith("# Rule\nContent")

    def test_lingma_adds_trigger_header(self):
        """Lingma: 添加 trigger: always_on 头部 (需求 5.2)"""
        adapter = _create_fresh_adapter("lingma")
        result = adapter.format_rule_content("# Rule\nContent")
        assert result.startswith("---\ntrigger: always_on\n---\n")
        assert result.endswith("# Rule\nContent")

    def test_trae_no_header(self):
        """Trae: 不添加额外头部，直接返回原始内容 (需求 5.3)"""
        adapter = _create_fresh_adapter("trae")
        content = "# Rule\nContent"
        result = adapter.format_rule_content(content)
        assert result == content

    def test_codebuddy_adds_codebuddy_header(self):
        """CodeBuddy: 添加含时间戳的 frontmatter 头部 (需求 5.4)"""
        adapter = _create_fresh_adapter("codebuddy")
        result = adapter.format_rule_content("# Rule\nContent")
        assert result.startswith("---\n")
        assert "alwaysApply: true" in result
        assert "enabled: true" in result
        assert "updatedAt:" in result
        assert "provider:" in result
        assert result.endswith("# Rule\nContent")

    def test_cursor_adds_cursor_header(self):
        """Cursor: 添加含时间戳的 frontmatter 头部"""
        adapter = _create_fresh_adapter("cursor")
        result = adapter.format_rule_content("# Rule\nContent")
        assert result.startswith("---\n")
        assert "alwaysApply: true" in result
        assert "enabled: true" in result
        assert "updatedAt:" in result
        assert "provider:" in result
        assert result.endswith("# Rule\nContent")

    @pytest.mark.parametrize("ide_name", ["qoder", "lingma", "trae", "codebuddy", "cursor"])
    def test_format_preserves_content(self, ide_name):
        """所有适配器的 format_rule_content 应保留原始内容"""
        adapter = _create_fresh_adapter(ide_name)
        content = "# My Rule\n\nSome detailed content.\n\n- Item 1\n- Item 2"
        result = adapter.format_rule_content(content)
        assert result.endswith(content)

    @pytest.mark.parametrize("ide_name", ["qoder", "lingma", "trae", "codebuddy", "cursor"])
    def test_format_empty_content(self, ide_name):
        """所有适配器应能处理空内容"""
        adapter = _create_fresh_adapter(ide_name)
        result = adapter.format_rule_content("")
        # Should not raise; Trae returns empty, others return header only
        assert isinstance(result, str)
