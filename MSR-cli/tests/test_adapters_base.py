"""适配器基类和注册表的单元测试"""

import pytest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from msr_sync.adapters.base import BaseAdapter
from msr_sync.adapters.registry import (
    get_adapter,
    get_all_adapters,
    resolve_ide_list,
    _adapter_instances,
    _ADAPTER_REGISTRY,
)


# --- 用于测试的具体适配器实现 ---


class FakeAdapter(BaseAdapter):
    """用于测试 BaseAdapter 接口的假适配器"""

    @property
    def ide_name(self) -> str:
        return "fake"

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        if scope == "project" and project_dir:
            return project_dir / ".fake" / "rules" / f"{rule_name}.md"
        return Path.home() / ".fake" / "rules" / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        if scope == "project" and project_dir:
            return project_dir / ".fake" / "skills" / skill_name
        return Path.home() / ".fake" / "skills" / skill_name

    def get_mcp_path(self) -> Path:
        return Path.home() / ".fake" / "mcp.json"

    def format_rule_content(self, raw_content: str) -> str:
        return f"---\nfake: true\n---\n{raw_content}"

    def scan_existing_configs(self) -> dict:
        return {"rules": [], "skills": [], "mcp": []}


class MinimalAdapter(BaseAdapter):
    """测试 supports_global_rules 默认值的适配器"""

    @property
    def ide_name(self) -> str:
        return "minimal"

    def get_rules_path(
        self, rule_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        return Path("/tmp/minimal/rules") / f"{rule_name}.md"

    def get_skills_path(
        self, skill_name: str, scope: str, project_dir: Optional[Path] = None
    ) -> Path:
        return Path("/tmp/minimal/skills") / skill_name

    def get_mcp_path(self) -> Path:
        return Path("/tmp/minimal/mcp.json")

    def format_rule_content(self, raw_content: str) -> str:
        return raw_content

    def scan_existing_configs(self) -> dict:
        return {"rules": [], "skills": [], "mcp": []}


# --- BaseAdapter 测试 ---


class TestBaseAdapter:
    """测试 BaseAdapter 抽象基类"""

    def test_cannot_instantiate_abstract_class(self):
        """不能直接实例化抽象基类"""
        with pytest.raises(TypeError):
            BaseAdapter()

    def test_concrete_adapter_ide_name(self):
        """具体适配器应返回正确的 ide_name"""
        adapter = FakeAdapter()
        assert adapter.ide_name == "fake"

    def test_supports_global_rules_default_false(self):
        """supports_global_rules 默认返回 False"""
        adapter = MinimalAdapter()
        assert adapter.supports_global_rules() is False

    def test_get_rules_path_project_scope(self):
        """项目级 rules 路径应包含项目目录"""
        adapter = FakeAdapter()
        project = Path("/my/project")
        path = adapter.get_rules_path("my-rule", "project", project)
        assert path == project / ".fake" / "rules" / "my-rule.md"

    def test_get_skills_path_project_scope(self):
        """项目级 skills 路径应包含项目目录"""
        adapter = FakeAdapter()
        project = Path("/my/project")
        path = adapter.get_skills_path("my-skill", "project", project)
        assert path == project / ".fake" / "skills" / "my-skill"

    def test_get_mcp_path(self):
        """MCP 路径应返回有效路径"""
        adapter = FakeAdapter()
        path = adapter.get_mcp_path()
        assert path.name == "mcp.json"

    def test_format_rule_content(self):
        """format_rule_content 应转换内容"""
        adapter = FakeAdapter()
        result = adapter.format_rule_content("# My Rule\nSome content")
        assert "fake: true" in result
        assert "# My Rule" in result
        assert "Some content" in result

    def test_scan_existing_configs_returns_dict(self):
        """scan_existing_configs 应返回包含三种配置类型的字典"""
        adapter = FakeAdapter()
        configs = adapter.scan_existing_configs()
        assert "rules" in configs
        assert "skills" in configs
        assert "mcp" in configs


# --- Registry 测试 ---


class TestRegistry:
    """测试适配器注册表"""

    def setup_method(self):
        """每个测试前清空适配器实例缓存"""
        _adapter_instances.clear()

    def test_registry_contains_all_supported_ides(self):
        """注册表应包含所有支持的 IDE"""
        expected_ides = {"qoder", "lingma", "trae", "codebuddy"}
        assert set(_ADAPTER_REGISTRY.keys()) == expected_ides

    def test_get_adapter_invalid_ide_raises_value_error(self):
        """获取不支持的 IDE 应抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的 IDE"):
            get_adapter("unknown-ide")

    def test_resolve_ide_list_with_all(self):
        """resolve_ide_list 传入 'all' 应返回所有适配器"""
        with patch(
            "msr_sync.adapters.registry._load_adapter_class"
        ) as mock_load:
            mock_load.return_value = FakeAdapter
            adapters = resolve_ide_list(("all",))
            assert len(adapters) == len(_ADAPTER_REGISTRY)

    def test_resolve_ide_list_with_specific_ides(self):
        """resolve_ide_list 传入具体 IDE 名称应返回对应适配器"""
        with patch(
            "msr_sync.adapters.registry._load_adapter_class"
        ) as mock_load:
            mock_load.return_value = FakeAdapter
            adapters = resolve_ide_list(("qoder", "trae"))
            assert len(adapters) == 2

    def test_get_adapter_caches_instances(self):
        """get_adapter 应缓存适配器实例"""
        with patch(
            "msr_sync.adapters.registry._load_adapter_class"
        ) as mock_load:
            mock_load.return_value = FakeAdapter
            adapter1 = get_adapter("qoder")
            adapter2 = get_adapter("qoder")
            assert adapter1 is adapter2
            # 只应加载一次
            mock_load.assert_called_once()

    def test_get_all_adapters_returns_list(self):
        """get_all_adapters 应返回所有适配器的列表"""
        with patch(
            "msr_sync.adapters.registry._load_adapter_class"
        ) as mock_load:
            mock_load.return_value = FakeAdapter
            adapters = get_all_adapters()
            assert isinstance(adapters, list)
            assert len(adapters) == len(_ADAPTER_REGISTRY)

    def test_resolve_ide_list_empty_tuple(self):
        """resolve_ide_list 传入空元组应返回空列表"""
        adapters = resolve_ide_list(())
        assert adapters == []

    def test_resolve_ide_list_invalid_ide_raises(self):
        """resolve_ide_list 传入无效 IDE 名称应抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的 IDE"):
            resolve_ide_list(("nonexistent",))
