"""GlobalConfig 单元测试 + 属性测试"""

import pytest
from pathlib import Path

from msr_sync.core.config import (
    GlobalConfig,
    load_config,
    config_to_yaml,
    get_config,
    init_config,
    reset_config,
    generate_default_config,
    DEFAULT_REPO_PATH,
    DEFAULT_IGNORE_PATTERNS,
    DEFAULT_IDES,
    DEFAULT_SCOPE,
    VALID_IDES,
    VALID_SCOPES,
)
from msr_sync.core.exceptions import ConfigFileError


@pytest.fixture(autouse=True)
def _reset_singleton():
    """每个测试前后重置全局配置单例，避免状态泄漏。
    Note: conftest.py also has an autouse fixture for this, but keeping
    this for explicit clarity in this test file.
    """
    reset_config()
    yield
    reset_config()


# ============================================================
# 单元测试 (Example-Based Tests)
# ============================================================


class TestLoadConfigFileNotExists:
    """需求 1.2: 配置文件不存在时返回全部默认值"""

    def test_returns_defaults_when_file_missing(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.repo_path == Path(DEFAULT_REPO_PATH).expanduser()
        assert config.ignore_patterns == DEFAULT_IGNORE_PATTERNS
        assert config.default_ides == DEFAULT_IDES
        assert config.default_scope == DEFAULT_SCOPE


class TestLoadConfigEmptyFile:
    """需求 1.3: 空配置文件返回全部默认值"""

    def test_returns_defaults_when_file_empty(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("", encoding="utf-8")
        config = load_config(config_file)
        assert config.repo_path == Path(DEFAULT_REPO_PATH).expanduser()
        assert config.ignore_patterns == DEFAULT_IGNORE_PATTERNS
        assert config.default_ides == DEFAULT_IDES
        assert config.default_scope == DEFAULT_SCOPE

    def test_returns_defaults_when_file_whitespace_only(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("   \n\n  ", encoding="utf-8")
        config = load_config(config_file)
        assert config.default_scope == DEFAULT_SCOPE


class TestLoadConfigYAMLError:
    """需求 1.4: YAML 语法错误时抛出 ConfigFileError 并包含文件路径"""

    def test_raises_config_file_error_with_path(self, tmp_path):
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("invalid: yaml: [broken", encoding="utf-8")
        with pytest.raises(ConfigFileError) as exc_info:
            load_config(config_file)
        assert str(config_file) in str(exc_info.value)


class TestIgnorePatternsDefault:
    """需求 2.1: ignore_patterns 默认值"""

    def test_default_ignore_patterns(self):
        config = GlobalConfig()
        assert config.ignore_patterns == ["__MACOSX", ".DS_Store", "__pycache__", ".git"]


class TestRepoPathDefault:
    """需求 3.1: repo_path 默认值"""

    def test_default_repo_path(self):
        config = GlobalConfig()
        assert config.repo_path == Path("~/.msr-repos").expanduser()


class TestRepoPathEmptyFallback:
    """需求 3.4: repo_path 空字符串回退到默认值"""

    def test_empty_string_falls_back(self):
        config = GlobalConfig(repo_path="")
        assert config.repo_path == Path("~/.msr-repos").expanduser()

    def test_whitespace_string_falls_back(self):
        config = GlobalConfig(repo_path="   ")
        assert config.repo_path == Path("~/.msr-repos").expanduser()


class TestDefaultIdes:
    """需求 4.1: default_ides 默认值"""

    def test_default_ides(self):
        config = GlobalConfig()
        assert config.default_ides == ["all"]


class TestDefaultIdesEmptyFallback:
    """需求 4.5: default_ides 空列表回退到默认值"""

    def test_empty_list_falls_back(self):
        config = GlobalConfig(default_ides=[])
        assert config.default_ides == ["all"]


class TestDefaultScope:
    """需求 5.1: default_scope 默认值"""

    def test_default_scope(self):
        config = GlobalConfig()
        assert config.default_scope == "global"


class TestYAMLWithComments:
    """需求 6.1: 包含注释的 YAML 正确解析"""

    def test_comments_are_ignored(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "# 这是注释\n"
            "repo_path: ~/custom-repos\n"
            "# 另一个注释\n"
            "default_scope: project\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config.repo_path == Path("~/custom-repos").expanduser()
        assert config.default_scope == "project"


class TestYAMLQuotedStrings:
    """需求 7.3: 带引号和不带引号的 YAML 字符串正确解析"""

    def test_quoted_and_unquoted(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            'ignore_patterns:\n'
            '  - __MACOSX\n'
            '  - "*.pyc"\n'
            '  - \'.git\'\n',
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert "__MACOSX" in config.ignore_patterns
        assert "*.pyc" in config.ignore_patterns
        assert ".git" in config.ignore_patterns


class TestSingletonLifecycle:
    """单例 get_config/init_config/reset_config 生命周期"""

    def test_get_config_returns_same_instance(self):
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_init_config_replaces_singleton(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_scope: project\n", encoding="utf-8")
        c1 = get_config()
        assert c1.default_scope == "global"
        c2 = init_config(config_file)
        assert c2.default_scope == "project"
        assert get_config() is c2

    def test_reset_config_clears_singleton(self):
        c1 = get_config()
        reset_config()
        c2 = get_config()
        assert c1 is not c2


# ============================================================
# 属性测试 (Property-Based Tests)
# ============================================================

from hypothesis import given, settings, assume
import hypothesis.strategies as st


# Feature: global-config, Property 1: 配置加载正确性（部分配置与未知键）
# **Validates: Requirements 1.1, 1.5, 6.3**
class TestPropertyConfigLoadCorrectness:
    """Property 1: 对于任意合法配置键的子集和任意未知键，
    load_config 应正确合并已知键与默认值，并忽略未知键。"""

    @given(
        include_repo_path=st.booleans(),
        include_ignore_patterns=st.booleans(),
        include_default_ides=st.booleans(),
        include_default_scope=st.booleans(),
        repo_path_val=st.text(
            min_size=1, max_size=30,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_/"),
        ),
        ignore_patterns_val=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_.")),
            min_size=1, max_size=5,
        ),
        default_ides_val=st.lists(
            st.sampled_from(list(VALID_IDES)), min_size=1, max_size=3,
        ),
        default_scope_val=st.sampled_from(list(VALID_SCOPES)),
        unknown_keys=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L",))).filter(
                lambda k: k not in ("repo_path", "ignore_patterns", "default_ides", "default_scope")
            ),
            values=st.text(min_size=1, max_size=10),
            min_size=0, max_size=3,
        ),
    )
    def test_partial_config_and_unknown_keys(
        self,
        include_repo_path,
        include_ignore_patterns,
        include_default_ides,
        include_default_scope,
        repo_path_val,
        ignore_patterns_val,
        default_ides_val,
        default_scope_val,
        unknown_keys,
    ):
        import yaml
        import tempfile
        import os

        data = dict(unknown_keys)

        if include_repo_path:
            data["repo_path"] = repo_path_val
        if include_ignore_patterns:
            data["ignore_patterns"] = ignore_patterns_val
        if include_default_ides:
            data["default_ides"] = default_ides_val
        if include_default_scope:
            data["default_scope"] = default_scope_val

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config.yaml"
            config_file.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")

            config = load_config(config_file)

            # Known keys present → use user value
            if include_repo_path:
                assert config.repo_path == Path(repo_path_val).expanduser()
            else:
                assert config.repo_path == Path(DEFAULT_REPO_PATH).expanduser()

            if include_ignore_patterns:
                assert config.ignore_patterns == ignore_patterns_val
            else:
                assert config.ignore_patterns == DEFAULT_IGNORE_PATTERNS

            if include_default_ides:
                assert config.default_ides == default_ides_val
            else:
                assert config.default_ides == DEFAULT_IDES

            if include_default_scope:
                assert config.default_scope == default_scope_val
            else:
                assert config.default_scope == DEFAULT_SCOPE


# Feature: global-config, Property 3: 仓库路径波浪号展开
# **Validates: Requirements 3.2**
class TestPropertyRepoPathTildeExpansion:
    """Property 3: 对于任意以 ~ 开头的路径字符串，
    GlobalConfig 的 repo_path 应为不含 ~ 的绝对路径。"""

    @given(
        suffix=st.text(
            min_size=1, max_size=30,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
        ),
    )
    def test_tilde_expansion(self, suffix):
        path_str = f"~/{suffix}"
        config = GlobalConfig(repo_path=path_str)
        assert "~" not in str(config.repo_path)
        assert config.repo_path == Path.home() / suffix


# Feature: global-config, Property 4: 无效 IDE 名称过滤
# **Validates: Requirements 4.4, 4.5**
class TestPropertyInvalidIdeFiltering:
    """Property 4: 对于任意字符串列表作为 default_ides 输入，
    结果应仅包含有效 IDE 名称；全部无效或空输入回退到 ["all"]。"""

    @given(
        ides=st.lists(
            st.one_of(
                st.sampled_from(list(VALID_IDES)),
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=("L", "N"))).filter(
                    lambda s: s not in VALID_IDES
                ),
            ),
            min_size=1,
            max_size=8,
        ),
    )
    def test_only_valid_ides_remain(self, ides):
        config = GlobalConfig(default_ides=ides)
        valid_in_input = [i for i in ides if i in VALID_IDES]
        if valid_in_input:
            assert config.default_ides == valid_in_input
        else:
            assert config.default_ides == list(DEFAULT_IDES)
        # All results must be valid
        for ide in config.default_ides:
            assert ide in VALID_IDES


# Feature: global-config, Property 5: 无效同步层级回退
# **Validates: Requirements 5.4**
class TestPropertyInvalidScopeFallback:
    """Property 5: 对于任意不等于 "global" 和 "project" 的字符串，
    GlobalConfig 的 default_scope 应为 "global"。"""

    @given(
        scope=st.text(min_size=1, max_size=20).filter(
            lambda s: s not in VALID_SCOPES
        ),
    )
    def test_invalid_scope_falls_back_to_global(self, scope):
        config = GlobalConfig(default_scope=scope)
        assert config.default_scope == "global"


# Feature: global-config, Property 6: 配置 YAML 往返一致性
# **Validates: Requirements 7.2**
class TestPropertyConfigYAMLRoundTrip:
    """Property 6: 对于任意合法 GlobalConfig 对象，
    序列化为 YAML 再解析回来后，所有配置项值应完全一致。"""

    @given(
        repo_path=st.text(
            min_size=1, max_size=30,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_/"),
        ),
        ignore_patterns=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_.")),
            min_size=0, max_size=10,
        ),
        default_ides=st.lists(
            st.sampled_from(list(VALID_IDES)), min_size=1, max_size=5,
        ),
        default_scope=st.sampled_from(list(VALID_SCOPES)),
    )
    def test_round_trip(self, repo_path, ignore_patterns, default_ides, default_scope):
        import tempfile

        config = GlobalConfig(
            repo_path=repo_path,
            ignore_patterns=ignore_patterns,
            default_ides=default_ides,
            default_scope=default_scope,
        )
        yaml_str = config_to_yaml(config)
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config.yaml"
            config_file.write_text(yaml_str, encoding="utf-8")
            loaded = load_config(config_file)
            assert loaded.to_dict() == config.to_dict()


# ============================================================
# generate_default_config 测试
# ============================================================


class TestGenerateDefaultConfig:
    """测试默认配置文件生成"""

    def test_creates_config_file_when_not_exists(self, tmp_path):
        """配置文件不存在时应创建并返回 True"""
        config_path = tmp_path / ".msr-sync" / "config.yaml"
        result = generate_default_config(config_path)
        assert result is True
        assert config_path.is_file()

    def test_config_file_contains_comments(self, tmp_path):
        """生成的配置文件应包含中文注释"""
        config_path = tmp_path / ".msr-sync" / "config.yaml"
        generate_default_config(config_path)
        content = config_path.read_text(encoding="utf-8")
        assert "# MSR-sync 全局配置文件" in content
        assert "ignore_patterns:" in content
        assert "__MACOSX" in content

    def test_config_file_is_valid_yaml(self, tmp_path):
        """生成的配置文件应为合法 YAML"""
        config_path = tmp_path / ".msr-sync" / "config.yaml"
        generate_default_config(config_path)
        config = load_config(config_path)
        assert config.ignore_patterns == DEFAULT_IGNORE_PATTERNS

    def test_skips_when_file_already_exists(self, tmp_path):
        """配置文件已存在时应跳过并返回 False"""
        config_path = tmp_path / ".msr-sync" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("default_scope: project\n", encoding="utf-8")

        result = generate_default_config(config_path)
        assert result is False
        # 原有内容不应被覆盖
        assert "project" in config_path.read_text(encoding="utf-8")

    def test_creates_parent_directories(self, tmp_path):
        """应自动创建父目录"""
        config_path = tmp_path / "deep" / "nested" / "config.yaml"
        generate_default_config(config_path)
        assert config_path.is_file()
