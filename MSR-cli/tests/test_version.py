"""版本管理模块单元测试与属性测试"""

import pytest
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from msr_sync.core.version import (
    parse_version,
    format_version,
    get_versions,
    get_latest_version,
    get_next_version,
)


# --- parse_version 测试 ---


class TestParseVersion:
    """parse_version 单元测试"""

    def test_parse_v1(self):
        assert parse_version("V1") == 1

    def test_parse_v10(self):
        assert parse_version("V10") == 10

    def test_parse_v999(self):
        assert parse_version("V999") == 999

    def test_invalid_empty_string(self):
        with pytest.raises(ValueError):
            parse_version("")

    def test_invalid_no_prefix(self):
        with pytest.raises(ValueError):
            parse_version("1")

    def test_invalid_lowercase_prefix(self):
        with pytest.raises(ValueError):
            parse_version("v1")

    def test_invalid_no_number(self):
        with pytest.raises(ValueError):
            parse_version("V")

    def test_invalid_negative(self):
        with pytest.raises(ValueError):
            parse_version("V-1")

    def test_invalid_zero(self):
        with pytest.raises(ValueError):
            parse_version("V0")

    def test_invalid_leading_zero(self):
        with pytest.raises(ValueError):
            parse_version("V01")

    def test_invalid_non_numeric(self):
        with pytest.raises(ValueError):
            parse_version("Vabc")

    def test_invalid_float(self):
        with pytest.raises(ValueError):
            parse_version("V1.5")


# --- format_version 测试 ---


class TestFormatVersion:
    """format_version 单元测试"""

    def test_format_1(self):
        assert format_version(1) == "V1"

    def test_format_10(self):
        assert format_version(10) == "V10"

    def test_format_999(self):
        assert format_version(999) == "V999"


# --- get_versions 测试 ---


class TestGetVersions:
    """get_versions 单元测试"""

    def test_empty_directory(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        assert get_versions(config_dir) == []

    def test_nonexistent_directory(self, tmp_path):
        config_dir = tmp_path / "nonexistent"
        assert get_versions(config_dir) == []

    def test_single_version(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        assert get_versions(config_dir) == ["V1"]

    def test_multiple_versions_sorted(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V3").mkdir()
        (config_dir / "V1").mkdir()
        (config_dir / "V2").mkdir()
        assert get_versions(config_dir) == ["V1", "V2", "V3"]

    def test_ignores_non_version_dirs(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        (config_dir / "V2").mkdir()
        (config_dir / "readme.txt").touch()
        (config_dir / "backup").mkdir()
        assert get_versions(config_dir) == ["V1", "V2"]

    def test_numeric_sort_not_lexicographic(self, tmp_path):
        """确保 V10 排在 V2 之后（数字排序而非字典序）"""
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V10").mkdir()
        (config_dir / "V2").mkdir()
        (config_dir / "V1").mkdir()
        assert get_versions(config_dir) == ["V1", "V2", "V10"]


# --- get_latest_version 测试 ---


class TestGetLatestVersion:
    """get_latest_version 单元测试"""

    def test_empty_directory(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        assert get_latest_version(config_dir) is None

    def test_nonexistent_directory(self, tmp_path):
        config_dir = tmp_path / "nonexistent"
        assert get_latest_version(config_dir) is None

    def test_single_version(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        assert get_latest_version(config_dir) == "V1"

    def test_multiple_versions(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        (config_dir / "V3").mkdir()
        (config_dir / "V2").mkdir()
        assert get_latest_version(config_dir) == "V3"


# --- get_next_version 测试 ---


class TestGetNextVersion:
    """get_next_version 单元测试"""

    def test_empty_directory_returns_v1(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        assert get_next_version(config_dir) == "V1"

    def test_nonexistent_directory_returns_v1(self, tmp_path):
        config_dir = tmp_path / "nonexistent"
        assert get_next_version(config_dir) == "V1"

    def test_after_v1(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        assert get_next_version(config_dir) == "V2"

    def test_after_v3(self, tmp_path):
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        (config_dir / "V2").mkdir()
        (config_dir / "V3").mkdir()
        assert get_next_version(config_dir) == "V4"

    def test_with_gaps(self, tmp_path):
        """即使版本号有间隔，也应基于最大版本号递增"""
        config_dir = tmp_path / "my-rule"
        config_dir.mkdir()
        (config_dir / "V1").mkdir()
        (config_dir / "V5").mkdir()
        assert get_next_version(config_dir) == "V6"


# =============================================================================
# 属性基测试 (Property-Based Tests)
# =============================================================================

import tempfile


# Feature: msr-cli, Property 1: 版本号格式往返一致性
# Validates: Requirements 13.1
class TestVersionFormatRoundTrip:
    """Property 1: 对任意正整数 n，parse_version(format_version(n)) == n"""

    @given(n=st.integers(min_value=1, max_value=10000))
    def test_format_then_parse_round_trip(self, n: int):
        """**Validates: Requirements 13.1**"""
        formatted = format_version(n)
        parsed = parse_version(formatted)
        assert parsed == n


# Feature: msr-cli, Property 2: 版本递增正确性
# Validates: Requirements 2.5, 3.7, 4.7
class TestVersionIncrementCorrectness:
    """Property 2: 对任意非空版本目录集合，get_next_version 返回最大版本号 +1；空目录返回 V1"""

    @given(version_nums=st.lists(
        st.integers(min_value=1, max_value=1000),
        min_size=1,
        max_size=20,
        unique=True,
    ))
    def test_next_version_is_max_plus_one(self, version_nums: list):
        """**Validates: Requirements 2.5, 3.7, 4.7**"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            config_dir.mkdir()

            for num in version_nums:
                (config_dir / format_version(num)).mkdir()

            expected_next = format_version(max(version_nums) + 1)
            assert get_next_version(config_dir) == expected_next

    @given(st.just(None))
    def test_empty_directory_returns_v1(self, _):
        """**Validates: Requirements 2.5, 3.7, 4.7**"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            config_dir.mkdir()
            assert get_next_version(config_dir) == "V1"


# Feature: msr-cli, Property 3: 最新版本选择正确性
# Validates: Requirements 13.2
class TestLatestVersionSelection:
    """Property 3: 对任意包含至少一个版本目录的配置目录，get_latest_version 返回数字最大的版本"""

    @given(version_nums=st.lists(
        st.integers(min_value=1, max_value=1000),
        min_size=1,
        max_size=20,
        unique=True,
    ))
    def test_latest_version_is_max(self, version_nums: list):
        """**Validates: Requirements 13.2**"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            config_dir.mkdir()

            for num in version_nums:
                (config_dir / format_version(num)).mkdir()

            expected_latest = format_version(max(version_nums))
            assert get_latest_version(config_dir) == expected_latest
