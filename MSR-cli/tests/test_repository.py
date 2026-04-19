"""仓库操作模块属性测试"""

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from msr_sync.core.repository import Repository
from msr_sync.core.version import format_version


# =============================================================================
# Hypothesis 策略定义
# =============================================================================

# 配置名称：简单字母数字字符串（合法目录名）
config_name_strategy = st.from_regex(r"[a-z][a-z0-9]{0,9}", fullmatch=True)

# 配置类型
config_type_strategy = st.sampled_from(["rules", "skills", "mcp"])

# 版本数量：1 到 5
version_count_strategy = st.integers(min_value=1, max_value=5)

# 单个配置条目：(name, type, version_count)
config_entry_strategy = st.tuples(
    config_name_strategy,
    config_type_strategy,
    version_count_strategy,
)

# 仓库状态：一组配置条目（1 到 10 个）
repo_state_strategy = st.lists(
    config_entry_strategy,
    min_size=1,
    max_size=10,
)


# =============================================================================
# 辅助函数
# =============================================================================

# 配置类型到仓库子目录名的映射
_TYPE_TO_DIR = {
    "rules": "RULES",
    "skills": "SKILLS",
    "mcp": "MCP",
}


def _create_repo_state(repo_path: Path, entries):
    """在临时仓库中创建指定的配置条目和版本目录。

    Args:
        repo_path: 仓库根目录路径
        entries: [(name, config_type, version_count), ...] 配置条目列表

    Returns:
        去重后的 {config_type: {name: [versions]}} 期望结果字典
    """
    # 初始化仓库目录结构
    for dir_name in _TYPE_TO_DIR.values():
        (repo_path / dir_name).mkdir(parents=True, exist_ok=True)

    # 去重：同一 (type, name) 只保留第一次出现的 version_count
    seen = {}
    for name, config_type, version_count in entries:
        key = (config_type, name)
        if key not in seen:
            seen[key] = version_count

    # 创建目录结构并构建期望结果
    expected = {"rules": {}, "skills": {}, "mcp": {}}
    for (config_type, name), version_count in seen.items():
        dir_name = _TYPE_TO_DIR[config_type]
        config_dir = repo_path / dir_name / name
        config_dir.mkdir(parents=True, exist_ok=True)

        versions = []
        for i in range(1, version_count + 1):
            ver = format_version(i)
            (config_dir / ver).mkdir(parents=True, exist_ok=True)
            versions.append(ver)

        expected[config_type][name] = versions

    return expected


# =============================================================================
# 属性基测试 (Property-Based Tests)
# =============================================================================


# Feature: msr-cli, Property 9: 配置列表输出完整性
# Validates: Requirements 9.1, 9.2, 9.3
class TestListOutputCompleteness:
    """Property 9: 对任意仓库状态，list_configs 返回所有配置条目及其版本号；
    指定 --type 时仅返回该类型"""

    @given(entries=repo_state_strategy)
    def test_list_configs_returns_all_configs(self, entries):
        """**Validates: Requirements 9.1, 9.3**

        对任意仓库状态，list_configs() 返回的结果应包含仓库中所有配置条目，
        每个条目应包含其名称和所有可用版本号。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / ".msr-repos"
            expected = _create_repo_state(repo_path, entries)
            repo = Repository(base_path=repo_path)

            result = repo.list_configs()

            # 验证所有三种类型都存在于结果中
            assert set(result.keys()) == {"rules", "skills", "mcp"}

            # 验证每种类型下的配置名称集合完全匹配
            for config_type in ["rules", "skills", "mcp"]:
                assert set(result[config_type].keys()) == set(expected[config_type].keys()), (
                    f"类型 {config_type} 的配置名称不匹配: "
                    f"got {set(result[config_type].keys())}, "
                    f"expected {set(expected[config_type].keys())}"
                )

                # 验证每个配置条目的版本列表完全匹配
                for name in expected[config_type]:
                    assert result[config_type][name] == expected[config_type][name], (
                        f"配置 {config_type}/{name} 的版本列表不匹配: "
                        f"got {result[config_type][name]}, "
                        f"expected {expected[config_type][name]}"
                    )

    @given(
        entries=repo_state_strategy,
        filter_type=config_type_strategy,
    )
    def test_list_configs_with_type_filter(self, entries, filter_type):
        """**Validates: Requirements 9.2**

        指定 --type 过滤时，结果应仅包含该类型的条目。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / ".msr-repos"
            expected = _create_repo_state(repo_path, entries)
            repo = Repository(base_path=repo_path)

            result = repo.list_configs(config_type=filter_type)

            # 结果应仅包含指定类型
            assert set(result.keys()) == {filter_type}, (
                f"过滤类型 {filter_type} 后结果键不匹配: got {set(result.keys())}"
            )

            # 该类型下的配置名称和版本应完全匹配
            assert set(result[filter_type].keys()) == set(expected[filter_type].keys()), (
                f"过滤类型 {filter_type} 后配置名称不匹配: "
                f"got {set(result[filter_type].keys())}, "
                f"expected {set(expected[filter_type].keys())}"
            )

            for name in expected[filter_type]:
                assert result[filter_type][name] == expected[filter_type][name], (
                    f"配置 {filter_type}/{name} 的版本列表不匹配: "
                    f"got {result[filter_type][name]}, "
                    f"expected {expected[filter_type][name]}"
                )

    @given(filter_type=config_type_strategy)
    def test_list_configs_empty_repo(self, filter_type):
        """**Validates: Requirements 9.1, 9.2**

        空仓库时，list_configs 应返回空的配置字典。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / ".msr-repos"
            # 初始化空仓库
            for dir_name in _TYPE_TO_DIR.values():
                (repo_path / dir_name).mkdir(parents=True, exist_ok=True)

            repo = Repository(base_path=repo_path)

            # 无过滤：所有类型都应为空
            result_all = repo.list_configs()
            for ct in ["rules", "skills", "mcp"]:
                assert result_all[ct] == {}

            # 有过滤：指定类型应为空
            result_filtered = repo.list_configs(config_type=filter_type)
            assert result_filtered[filter_type] == {}


# =============================================================================
# 单元测试 (Unit Tests)
# =============================================================================

import pytest

from msr_sync.core.exceptions import ConfigNotFoundError, RepositoryNotFoundError


class TestInit:
    """测试仓库初始化功能"""

    def test_init_creates_directory_structure(self, tmp_path):
        """**Validates: Requirements 1.1**

        init() 应创建 RULES/、SKILLS/、MCP/ 子目录并返回 True。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        result = repo.init()

        assert result is True
        assert (repo_path / "RULES").is_dir()
        assert (repo_path / "SKILLS").is_dir()
        assert (repo_path / "MCP").is_dir()

    def test_init_idempotent_returns_false(self, tmp_path):
        """**Validates: Requirements 1.2**

        对已存在的仓库执行 init() 应返回 False（幂等操作）。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        first = repo.init()
        second = repo.init()

        assert first is True
        assert second is False
        # 目录结构仍然完整
        assert (repo_path / "RULES").is_dir()
        assert (repo_path / "SKILLS").is_dir()
        assert (repo_path / "MCP").is_dir()


class TestStoreRule:
    """测试 rule 存储功能"""

    def test_store_rule_creates_file(self, tmp_path):
        """**Validates: Requirements 2.1**

        store_rule 应将内容写入 RULES/<name>/V1/<name>.md。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()

        version = repo.store_rule("my-rule", "# My Rule Content")

        assert version == "V1"
        rule_file = repo_path / "RULES" / "my-rule" / "V1" / "my-rule.md"
        assert rule_file.is_file()
        assert rule_file.read_text(encoding="utf-8") == "# My Rule Content"

    def test_store_rule_increments_version(self, tmp_path):
        """**Validates: Requirements 2.5**

        同名 rule 再次导入应创建 V2。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()

        v1 = repo.store_rule("my-rule", "# Version 1")
        v2 = repo.store_rule("my-rule", "# Version 2")

        assert v1 == "V1"
        assert v2 == "V2"
        assert (repo_path / "RULES" / "my-rule" / "V1" / "my-rule.md").is_file()
        assert (repo_path / "RULES" / "my-rule" / "V2" / "my-rule.md").is_file()


class TestStoreSkill:
    """测试 skill 存储功能"""

    def test_store_skill_copies_directory(self, tmp_path):
        """**Validates: Requirements 4.1**

        store_skill 应将源目录拷贝到 SKILLS/<name>/V1/。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()

        # 创建源 skill 目录
        source_dir = tmp_path / "source-skill"
        source_dir.mkdir()
        (source_dir / "SKILL.md").write_text("# My Skill", encoding="utf-8")
        (source_dir / "helper.py").write_text("print('hello')", encoding="utf-8")

        version = repo.store_skill("my-skill", source_dir)

        assert version == "V1"
        skill_dir = repo_path / "SKILLS" / "my-skill" / "V1"
        assert skill_dir.is_dir()
        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "# My Skill"
        assert (skill_dir / "helper.py").read_text(encoding="utf-8") == "print('hello')"


class TestStoreMcp:
    """测试 MCP 配置存储功能"""

    def test_store_mcp_copies_directory(self, tmp_path):
        """**Validates: Requirements 3.1**

        store_mcp 应将源目录拷贝到 MCP/<name>/V1/。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()

        # 创建源 MCP 目录
        source_dir = tmp_path / "source-mcp"
        source_dir.mkdir()
        (source_dir / "mcp.json").write_text('{"servers": {}}', encoding="utf-8")

        version = repo.store_mcp("my-mcp", source_dir)

        assert version == "V1"
        mcp_dir = repo_path / "MCP" / "my-mcp" / "V1"
        assert mcp_dir.is_dir()
        assert (mcp_dir / "mcp.json").read_text(encoding="utf-8") == '{"servers": {}}'


class TestRemoveConfig:
    """测试配置删除功能"""

    def test_remove_config_deletes_version_directory(self, tmp_path):
        """**Validates: Requirements 10.1**

        remove_config 应删除指定版本目录。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()
        repo.store_rule("my-rule", "# content")

        result = repo.remove_config("rules", "my-rule", "V1")

        assert result is True
        assert not (repo_path / "RULES" / "my-rule" / "V1").exists()

    def test_remove_config_nonexistent_version_raises_error(self, tmp_path):
        """**Validates: Requirements 10.2**

        删除不存在的版本应抛出 ConfigNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()
        repo.store_rule("my-rule", "# content")

        with pytest.raises(ConfigNotFoundError):
            repo.remove_config("rules", "my-rule", "V99")

    def test_remove_config_nonexistent_name_raises_error(self, tmp_path):
        """**Validates: Requirements 10.3**

        删除不存在的配置名称应抛出 ConfigNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()

        with pytest.raises(ConfigNotFoundError):
            repo.remove_config("rules", "nonexistent", "V1")


class TestGetConfigPath:
    """测试配置路径获取功能"""

    def test_get_config_path_nonexistent_version_raises_error(self, tmp_path):
        """**Validates: Requirements 13.4**

        指定不存在的版本应抛出 ConfigNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()
        repo.store_rule("my-rule", "# content")

        with pytest.raises(ConfigNotFoundError):
            repo.get_config_path("rules", "my-rule", "V99")

    def test_get_config_path_nonexistent_name_raises_error(self, tmp_path):
        """**Validates: Requirements 13.4**

        指定不存在的配置名称应抛出 ConfigNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()

        with pytest.raises(ConfigNotFoundError):
            repo.get_config_path("rules", "nonexistent")

    def test_get_config_path_returns_latest_version(self, tmp_path):
        """**Validates: Requirements 13.2**

        version 为 None 时应返回最新版本路径。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()
        repo.store_rule("my-rule", "# V1")
        repo.store_rule("my-rule", "# V2")

        path = repo.get_config_path("rules", "my-rule")

        assert path == repo_path / "RULES" / "my-rule" / "V2"


class TestReadRuleContent:
    """测试 rule 内容读取功能"""

    def test_read_rule_content_returns_correct_content(self, tmp_path):
        """**Validates: Requirements 2.1**

        read_rule_content 应返回正确的文件内容。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()
        repo.store_rule("my-rule", "# Hello World\n\nThis is a rule.")

        content = repo.read_rule_content("my-rule")

        assert content == "# Hello World\n\nThis is a rule."

    def test_read_rule_content_specific_version(self, tmp_path):
        """**Validates: Requirements 13.3**

        指定版本时应读取对应版本的内容。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)
        repo.init()
        repo.store_rule("my-rule", "# Version 1")
        repo.store_rule("my-rule", "# Version 2")

        content_v1 = repo.read_rule_content("my-rule", "V1")
        content_v2 = repo.read_rule_content("my-rule", "V2")

        assert content_v1 == "# Version 1"
        assert content_v2 == "# Version 2"


class TestUninitializedRepo:
    """测试未初始化仓库的错误处理"""

    def test_store_rule_on_uninitialized_repo_raises_error(self, tmp_path):
        """**Validates: Requirements 1.1**

        在未初始化的仓库上执行 store_rule 应抛出 RepositoryNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        with pytest.raises(RepositoryNotFoundError):
            repo.store_rule("my-rule", "# content")

    def test_list_configs_on_uninitialized_repo_raises_error(self, tmp_path):
        """**Validates: Requirements 1.1**

        在未初始化的仓库上执行 list_configs 应抛出 RepositoryNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        with pytest.raises(RepositoryNotFoundError):
            repo.list_configs()

    def test_remove_config_on_uninitialized_repo_raises_error(self, tmp_path):
        """**Validates: Requirements 1.1**

        在未初始化的仓库上执行 remove_config 应抛出 RepositoryNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        with pytest.raises(RepositoryNotFoundError):
            repo.remove_config("rules", "my-rule", "V1")

    def test_get_config_path_on_uninitialized_repo_raises_error(self, tmp_path):
        """**Validates: Requirements 13.4**

        在未初始化的仓库上执行 get_config_path 应抛出 RepositoryNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        with pytest.raises(RepositoryNotFoundError):
            repo.get_config_path("rules", "my-rule")

    def test_read_rule_content_on_uninitialized_repo_raises_error(self, tmp_path):
        """**Validates: Requirements 1.1**

        在未初始化的仓库上执行 read_rule_content 应抛出 RepositoryNotFoundError。
        """
        repo_path = tmp_path / ".msr-repos"
        repo = Repository(base_path=repo_path)

        with pytest.raises(RepositoryNotFoundError):
            repo.read_rule_content("my-rule")
