"""来源解析器属性测试与单元测试"""

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from msr_sync.core.source_resolver import SourceResolver


# =============================================================================
# 辅助策略 (Helper Strategies)
# =============================================================================

# 合法的文件/目录名称策略：字母数字加连字符下划线，长度 1-20
# 排除默认忽略模式中的名称，避免被 _should_ignore 过滤
_DEFAULT_IGNORE_NAMES = {"__MACOSX", ".DS_Store", "__pycache__", ".git"}
_valid_name_chars = st.text(
    alphabet=st.sampled_from(
        "abcdefghijklmnopqrstuvwxyz0123456789_-"
    ),
    min_size=1,
    max_size=20,
).filter(lambda s: s.strip("-_") != "" and not s.startswith(".") and s not in _DEFAULT_IGNORE_NAMES)


# =============================================================================
# 属性基测试 (Property-Based Tests)
# =============================================================================


# Feature: msr-cli, Property 5: 来源解析器检测完整性
# Validates: Requirements 2.2, 3.3, 4.3
class TestSourceResolverDetectionCompleteness:
    """Property 5: 对任意包含 N 个匹配配置项的目录，解析器恰好检测到 N 个配置项，
    名称与原始文件/目录名一致"""

    @given(
        names=st.lists(
            _valid_name_chars,
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    def test_rules_directory_detects_all_md_files(self, names: list):
        """**Validates: Requirements 2.2**

        对任意包含 N 个 .md 文件的目录，rules 解析器恰好检测到 N 个配置项。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / "rules_src"
            src_dir.mkdir()

            # 创建 N 个 .md 文件
            for name in names:
                (src_dir / f"{name}.md").write_text(f"# {name}")

            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(src_dir), "rules")

                # 恰好检测到 N 个配置项
                assert len(items) == len(names)

                # 名称与原始文件名一致
                detected_names = {item.name for item in items}
                expected_names = set(names)
                assert detected_names == expected_names
            finally:
                resolver.cleanup()

    @given(
        names=st.lists(
            _valid_name_chars,
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    def test_skills_directory_detects_all_subdirs(self, names: list):
        """**Validates: Requirements 4.3**

        对任意包含 N 个子目录（无 SKILL.md 在根目录）的目录，
        skills 解析器恰好检测到 N 个配置项。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / "skills_src"
            src_dir.mkdir()

            # 创建 N 个子目录（不在根目录放 SKILL.md，使其被视为多个 skill）
            for name in names:
                sub = src_dir / name
                sub.mkdir()
                (sub / "SKILL.md").write_text(f"# {name}")

            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(src_dir), "skills")

                # 恰好检测到 N 个配置项
                assert len(items) == len(names)

                # 名称与原始目录名一致
                detected_names = {item.name for item in items}
                expected_names = set(names)
                assert detected_names == expected_names
            finally:
                resolver.cleanup()

    @given(
        names=st.lists(
            _valid_name_chars,
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    def test_mcp_directory_detects_all_subdirs(self, names: list):
        """**Validates: Requirements 3.3**

        对任意仅包含 N 个子目录的目录（无非目录文件），
        mcp 解析器恰好检测到 N 个配置项。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / "mcp_src"
            src_dir.mkdir()

            # 创建 N 个子目录（根目录不放文件，使其被视为多个 MCP）
            for name in names:
                sub = src_dir / name
                sub.mkdir()
                (sub / "mcp.json").write_text("{}")

            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(src_dir), "mcp")

                # 恰好检测到 N 个配置项
                assert len(items) == len(names)

                # 名称与原始目录名一致
                detected_names = {item.name for item in items}
                expected_names = set(names)
                assert detected_names == expected_names
            finally:
                resolver.cleanup()


# Feature: msr-cli, Property 6: MCP 单/多配置分类正确性
# Validates: Requirements 3.6
class TestMCPSingleMultipleClassification:
    """Property 6: 根目录含非子目录文件则为单个 MCP，仅含子目录则为多个 MCP"""

    @given(
        dir_name=_valid_name_chars,
        file_names=st.lists(
            _valid_name_chars,
            min_size=1,
            max_size=5,
            unique=True,
        ),
    )
    def test_directory_with_files_is_single_mcp(self, dir_name: str, file_names: list):
        """**Validates: Requirements 3.6**

        根目录含非子目录文件则 _is_single_mcp 返回 True。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / dir_name
            src_dir.mkdir()

            # 在根目录放置非目录文件
            for fname in file_names:
                (src_dir / fname).write_text("content")

            assert SourceResolver._is_single_mcp(src_dir) is True

    @given(
        sub_names=st.lists(
            _valid_name_chars,
            min_size=1,
            max_size=5,
            unique=True,
        ),
    )
    def test_directory_with_only_subdirs_is_multiple_mcp(self, sub_names: list):
        """**Validates: Requirements 3.6**

        根目录仅含子目录则 _is_single_mcp 返回 False。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / "mcp_multi"
            src_dir.mkdir()

            # 仅创建子目录，不放任何文件
            for name in sub_names:
                (src_dir / name).mkdir()

            assert SourceResolver._is_single_mcp(src_dir) is False


# Feature: msr-cli, Property 7: Skill 单/多配置分类正确性
# Validates: Requirements 4.6
class TestSkillSingleMultipleClassification:
    """Property 7: 根目录含 SKILL.md 则为单个 skill，否则为多个 skill"""

    @given(
        dir_name=_valid_name_chars,
        extra_files=st.lists(
            _valid_name_chars.filter(lambda s: s.upper() != "SKILL"),
            min_size=0,
            max_size=5,
            unique=True,
        ),
    )
    def test_directory_with_skill_md_is_single_skill(self, dir_name: str, extra_files: list):
        """**Validates: Requirements 4.6**

        根目录含 SKILL.md 则 _is_single_skill 返回 True。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / dir_name
            src_dir.mkdir()

            # 创建 SKILL.md 标识文件
            (src_dir / "SKILL.md").write_text("# Skill description")

            # 可选：添加额外文件
            for fname in extra_files:
                (src_dir / fname).write_text("extra content")

            assert SourceResolver._is_single_skill(src_dir) is True

    @given(
        sub_names=st.lists(
            _valid_name_chars,
            min_size=1,
            max_size=5,
            unique=True,
        ),
    )
    def test_directory_without_skill_md_is_multiple_skill(self, sub_names: list):
        """**Validates: Requirements 4.6**

        根目录不含 SKILL.md 则 _is_single_skill 返回 False。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = Path(tmp_dir) / "skills_multi"
            src_dir.mkdir()

            # 仅创建子目录，不放 SKILL.md
            for name in sub_names:
                sub = src_dir / name
                sub.mkdir()
                # 子目录内可以有 SKILL.md，但根目录没有
                (sub / "SKILL.md").write_text(f"# {name}")

            assert SourceResolver._is_single_skill(src_dir) is False


# =============================================================================
# 单元测试 (Unit Tests)
# =============================================================================

import tarfile
import zipfile
from unittest.mock import patch

import pytest

from msr_sync.core.exceptions import InvalidSourceError
from msr_sync.core.source_resolver import ResolvedItem, SourceType


class TestResolveSingleFile:
    """测试单文件解析（需求 2.1）"""

    def test_single_md_file_resolves_to_one_item(self, tmp_path):
        """单个 .md 文件应解析为 1 个配置项，needs_confirm=False"""
        md_file = tmp_path / "my-rule.md"
        md_file.write_text("# My Rule\nSome content")

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(md_file), "rules")

            assert len(items) == 1
            assert items[0].name == "my-rule"
            assert items[0].path == md_file
            assert items[0].source_type == SourceType.FILE
            assert needs_confirm is False
        finally:
            resolver.cleanup()


class TestResolveDirectory:
    """测试多文件目录解析（需求 2.2）"""

    def test_directory_with_multiple_md_files(self, tmp_path):
        """包含多个 .md 文件的目录应解析为 N 个配置项，needs_confirm=True"""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "rule-a.md").write_text("# Rule A")
        (rules_dir / "rule-b.md").write_text("# Rule B")
        (rules_dir / "rule-c.md").write_text("# Rule C")

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(rules_dir), "rules")

            assert len(items) == 3
            names = {item.name for item in items}
            assert names == {"rule-a", "rule-b", "rule-c"}
            assert needs_confirm is True
        finally:
            resolver.cleanup()


class TestResolveZipArchive:
    """测试 ZIP 压缩包解析（需求 2.3, 3.2, 3.4, 4.2, 4.4）"""

    def test_zip_with_md_files(self, tmp_path):
        """ZIP 压缩包中包含 .md 文件应正确解压并解析"""
        # 创建 ZIP 压缩包
        zip_path = tmp_path / "rules.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rules/alpha.md", "# Alpha")
            zf.writestr("rules/beta.md", "# Beta")

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(zip_path), "rules")

            assert len(items) == 2
            names = {item.name for item in items}
            assert names == {"alpha", "beta"}
            assert needs_confirm is True
        finally:
            resolver.cleanup()

    def test_zip_with_skill_directories(self, tmp_path):
        """ZIP 压缩包中包含 skill 目录应正确解压并解析"""
        zip_path = tmp_path / "skills.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            # 多个 skill 子目录（顶层目录无 SKILL.md）
            zf.writestr("skills/skill-a/SKILL.md", "# Skill A")
            zf.writestr("skills/skill-b/SKILL.md", "# Skill B")

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(zip_path), "skills")

            assert len(items) == 2
            names = {item.name for item in items}
            assert names == {"skill-a", "skill-b"}
            assert needs_confirm is True
        finally:
            resolver.cleanup()

    def test_zip_with_mcp_directories(self, tmp_path):
        """ZIP 压缩包中包含 MCP 目录应正确解压并解析"""
        zip_path = tmp_path / "mcps.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            # 多个 MCP 子目录（顶层目录仅含子目录）
            zf.writestr("mcps/mcp-a/mcp.json", '{"servers": {}}')
            zf.writestr("mcps/mcp-b/mcp.json", '{"servers": {}}')

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(zip_path), "mcp")

            assert len(items) == 2
            names = {item.name for item in items}
            assert names == {"mcp-a", "mcp-b"}
            assert needs_confirm is True
        finally:
            resolver.cleanup()


class TestResolveTarGzArchive:
    """测试 tar.gz 压缩包解析（需求 2.3, 3.4, 4.4）"""

    def test_tar_gz_with_md_files(self, tmp_path):
        """tar.gz 压缩包中包含 .md 文件应正确解压并解析"""
        # 先创建临时文件用于打包
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        rules_dir = src_dir / "rules"
        rules_dir.mkdir()
        (rules_dir / "gamma.md").write_text("# Gamma")
        (rules_dir / "delta.md").write_text("# Delta")

        tar_path = tmp_path / "rules.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            tf.add(rules_dir, arcname="rules")

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(tar_path), "rules")

            assert len(items) == 2
            names = {item.name for item in items}
            assert names == {"gamma", "delta"}
            assert needs_confirm is True
        finally:
            resolver.cleanup()


class TestResolveURL:
    """测试 URL 下载解析（mock HTTP）（需求 2.4, 3.5, 4.5）"""

    def test_url_download_and_resolve(self, tmp_path):
        """URL 指向的压缩包应下载后正确解析"""
        # 先创建一个真实的 ZIP 文件用于 mock 下载
        zip_path = tmp_path / "remote-rules.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("pkg/rule-x.md", "# Rule X")
            zf.writestr("pkg/rule-y.md", "# Rule Y")

        def fake_urlretrieve(url, dest):
            """模拟下载：将预先创建的 ZIP 复制到目标路径"""
            import shutil
            shutil.copy2(zip_path, dest)
            return dest, {}

        resolver = SourceResolver()
        try:
            with patch("msr_sync.core.source_resolver.urllib.request.urlretrieve", side_effect=fake_urlretrieve):
                items, needs_confirm = resolver.resolve(
                    "https://example.com/remote-rules.zip", "rules"
                )

            assert len(items) == 2
            names = {item.name for item in items}
            assert names == {"rule-x", "rule-y"}
            assert needs_confirm is True
        finally:
            resolver.cleanup()


class TestInvalidSourceErrors:
    """测试无效来源错误处理"""

    def test_nonexistent_file_raises_error(self, tmp_path):
        """不存在的文件应抛出 InvalidSourceError"""
        fake_path = tmp_path / "nonexistent.md"

        resolver = SourceResolver()
        try:
            with pytest.raises(InvalidSourceError):
                resolver.resolve(str(fake_path), "rules")
        finally:
            resolver.cleanup()

    def test_non_md_file_raises_error(self, tmp_path):
        """非 .md 文件应抛出 InvalidSourceError"""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("not a markdown file")

        resolver = SourceResolver()
        try:
            with pytest.raises(InvalidSourceError):
                resolver.resolve(str(txt_file), "rules")
        finally:
            resolver.cleanup()

    def test_nonexistent_directory_raises_error(self, tmp_path):
        """不存在的目录应抛出 InvalidSourceError"""
        fake_dir = tmp_path / "no-such-dir"

        resolver = SourceResolver()
        try:
            with pytest.raises(InvalidSourceError):
                resolver.resolve(str(fake_dir), "rules")
        finally:
            resolver.cleanup()


class TestResolveSingleSkillDirectory:
    """测试单个 skill 目录解析（需求 4.1, 4.6）"""

    def test_single_skill_directory_with_skill_md(self, tmp_path):
        """包含 SKILL.md 的目录应解析为单个 skill，needs_confirm=False"""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill")
        (skill_dir / "helper.py").write_text("# helper")

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(skill_dir), "skills")

            assert len(items) == 1
            assert items[0].name == "my-skill"
            assert items[0].path == skill_dir
            assert items[0].source_type == SourceType.DIRECTORY
            assert needs_confirm is False
        finally:
            resolver.cleanup()


class TestResolveSingleMCPDirectory:
    """测试单个 MCP 目录解析（需求 3.1, 3.6）"""

    def test_single_mcp_directory_with_files(self, tmp_path):
        """根目录含非子目录文件的目录应解析为单个 MCP，needs_confirm=False"""
        mcp_dir = tmp_path / "my-mcp"
        mcp_dir.mkdir()
        (mcp_dir / "mcp.json").write_text('{"servers": {}}')

        resolver = SourceResolver()
        try:
            items, needs_confirm = resolver.resolve(str(mcp_dir), "mcp")

            assert len(items) == 1
            assert items[0].name == "my-mcp"
            assert items[0].path == mcp_dir
            assert items[0].source_type == SourceType.DIRECTORY
            assert needs_confirm is False
        finally:
            resolver.cleanup()

# =============================================================================
# 忽略模式过滤测试 (Ignore Pattern Filtering Tests)
# =============================================================================

from msr_sync.core.config import reset_config, init_config, GlobalConfig
import fnmatch


@pytest.fixture(autouse=False)
def _reset_config_singleton():
    """重置全局配置单例，避免状态泄漏。"""
    reset_config()
    yield
    reset_config()


# Feature: global-config, Property 2: 忽略模式匹配正确性
# **Validates: Requirements 2.2, 2.3, 2.5**
class TestPropertyIgnorePatternMatching:
    """Property 2: 对于任意文件名和任意忽略模式列表，
    _should_ignore(name) 应返回 True 当且仅当名称匹配至少一个模式。"""

    @given(
        name=st.text(
            min_size=1, max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_."),
        ),
        patterns=st.lists(
            st.one_of(
                # 精确匹配模式
                st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_.")),
                # 通配符模式
                st.from_regex(r"\*\.[a-z]{1,5}", fullmatch=True),
            ),
            min_size=0,
            max_size=5,
        ),
    )
    def test_should_ignore_matches_correctly(self, name, patterns):
        """_should_ignore 应与手动 fnmatch/精确匹配逻辑一致。"""
        from unittest.mock import patch

        # 手动计算期望结果
        expected = False
        for pattern in patterns:
            if any(c in pattern for c in ('*', '?', '[')):
                if fnmatch.fnmatch(name, pattern):
                    expected = True
                    break
            else:
                if name == pattern:
                    expected = True
                    break

        # Mock get_config to return our custom patterns
        mock_config = GlobalConfig(ignore_patterns=patterns)
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            result = resolver._should_ignore(name)

        assert result == expected


# 单元测试：忽略过滤
class TestIgnoreFilteringUnit:
    """需求 2.2, 2.3, 2.4, 2.5: SourceResolver 忽略模式过滤"""

    def test_rules_directory_skips_exact_match(self, tmp_path, _reset_config_singleton):
        """需求 2.2: 目录扫描跳过精确匹配忽略模式的条目（如 __MACOSX、.DS_Store）"""
        from unittest.mock import patch

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "good-rule.md").write_text("# Good Rule")
        (rules_dir / "__MACOSX").mkdir()
        (rules_dir / ".DS_Store").write_text("")

        mock_config = GlobalConfig(ignore_patterns=["__MACOSX", ".DS_Store"])
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(rules_dir), "rules")
                names = {item.name for item in items}
                assert "good-rule" in names
                assert "__MACOSX" not in names
                assert ".DS_Store" not in names
            finally:
                resolver.cleanup()

    def test_rules_directory_skips_wildcard_match(self, tmp_path, _reset_config_singleton):
        """需求 2.3: 目录扫描跳过通配符匹配的条目（如 *.pyc）"""
        from unittest.mock import patch

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "good-rule.md").write_text("# Good Rule")
        (rules_dir / "cache.pyc").write_text("")

        mock_config = GlobalConfig(ignore_patterns=["*.pyc"])
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(rules_dir), "rules")
                names = {item.name for item in items}
                assert "good-rule" in names
                assert "cache" not in names
            finally:
                resolver.cleanup()

    def test_archive_applies_same_ignore_filtering(self, tmp_path, _reset_config_singleton):
        """需求 2.4: 压缩包解压后扫描应用相同的忽略过滤"""
        from unittest.mock import patch

        zip_path = tmp_path / "rules.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rules/good-rule.md", "# Good Rule")
            zf.writestr("rules/.DS_Store", "")

        mock_config = GlobalConfig(ignore_patterns=[".DS_Store"])
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(zip_path), "rules")
                names = {item.name for item in items}
                assert "good-rule" in names
                assert ".DS_Store" not in names
            finally:
                resolver.cleanup()

    def test_filter_applies_to_name_only_not_full_path(self, tmp_path, _reset_config_singleton):
        """需求 2.5: 过滤仅作用于条目名称，不作用于完整路径"""
        from unittest.mock import patch

        # Create a directory structure where the parent path contains the pattern
        # but the entry name does not
        rules_dir = tmp_path / "__pycache__" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "my-rule.md").write_text("# My Rule")

        mock_config = GlobalConfig(ignore_patterns=["__pycache__"])
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(rules_dir), "rules")
                # my-rule.md should NOT be filtered because its name doesn't match
                names = {item.name for item in items}
                assert "my-rule" in names
            finally:
                resolver.cleanup()

    def test_skills_directory_skips_ignored_entries(self, tmp_path, _reset_config_singleton):
        """需求 2.2: skills 目录扫描跳过忽略模式的条目"""
        from unittest.mock import patch

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "good-skill").mkdir()
        (skills_dir / "good-skill" / "SKILL.md").write_text("# Good")
        (skills_dir / "__pycache__").mkdir()

        mock_config = GlobalConfig(ignore_patterns=["__pycache__"])
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(skills_dir), "skills")
                names = {item.name for item in items}
                assert "good-skill" in names
                assert "__pycache__" not in names
            finally:
                resolver.cleanup()

    def test_mcp_directory_skips_ignored_entries(self, tmp_path, _reset_config_singleton):
        """需求 2.2: mcp 目录扫描跳过忽略模式的条目"""
        from unittest.mock import patch

        mcp_dir = tmp_path / "mcps"
        mcp_dir.mkdir()
        (mcp_dir / "good-mcp").mkdir()
        (mcp_dir / "good-mcp" / "mcp.json").write_text('{"servers": {}}')
        (mcp_dir / ".git").mkdir()

        mock_config = GlobalConfig(ignore_patterns=[".git"])
        with patch("msr_sync.core.config.get_config", return_value=mock_config):
            resolver = SourceResolver()
            try:
                items, _ = resolver.resolve(str(mcp_dir), "mcp")
                names = {item.name for item in items}
                assert "good-mcp" in names
                assert ".git" not in names
            finally:
                resolver.cleanup()
