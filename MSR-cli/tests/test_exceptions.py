"""异常层次结构单元测试"""

import pytest

from msr_sync.core.exceptions import (
    MSRError,
    RepositoryNotFoundError,
    ConfigNotFoundError,
    InvalidSourceError,
    UnsupportedPlatformError,
    NetworkError,
    ConfigParseError,
)


ALL_SUBCLASSES = [
    RepositoryNotFoundError,
    ConfigNotFoundError,
    InvalidSourceError,
    UnsupportedPlatformError,
    NetworkError,
    ConfigParseError,
]


class TestExceptionHierarchy:
    """测试异常继承关系"""

    def test_msr_error_is_exception(self):
        assert issubclass(MSRError, Exception)

    @pytest.mark.parametrize("cls", ALL_SUBCLASSES)
    def test_subclass_inherits_msr_error(self, cls):
        assert issubclass(cls, MSRError)

    @pytest.mark.parametrize("cls", ALL_SUBCLASSES)
    def test_subclass_caught_by_msr_error(self, cls):
        with pytest.raises(MSRError):
            raise cls("测试错误信息")

    @pytest.mark.parametrize("cls", ALL_SUBCLASSES)
    def test_subclass_preserves_message(self, cls):
        msg = "具体的错误描述"
        with pytest.raises(cls, match=msg):
            raise cls(msg)

    def test_msr_error_with_message(self):
        err = MSRError("基础错误")
        assert str(err) == "基础错误"
