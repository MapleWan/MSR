"""平台检测模块单元测试"""

import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from msr_sync.core.exceptions import UnsupportedPlatformError
from msr_sync.core.platform import PlatformInfo


class TestGetOs:
    """测试 get_os() 方法"""

    @patch("msr_sync.core.platform.platform.system", return_value="Darwin")
    def test_macos_detected(self, _mock):
        assert PlatformInfo.get_os() == "macos"

    @patch("msr_sync.core.platform.platform.system", return_value="Windows")
    def test_windows_detected(self, _mock):
        assert PlatformInfo.get_os() == "windows"

    @patch("msr_sync.core.platform.platform.system", return_value="Linux")
    def test_linux_raises_unsupported(self, _mock):
        with pytest.raises(UnsupportedPlatformError, match="不支持的操作系统"):
            PlatformInfo.get_os()

    @patch("msr_sync.core.platform.platform.system", return_value="FreeBSD")
    def test_freebsd_raises_unsupported(self, _mock):
        with pytest.raises(UnsupportedPlatformError, match="不支持的操作系统"):
            PlatformInfo.get_os()

    @patch("msr_sync.core.platform.platform.system", return_value="Linux")
    def test_error_message_contains_os_name(self, _mock):
        with pytest.raises(UnsupportedPlatformError, match="Linux"):
            PlatformInfo.get_os()


class TestGetHome:
    """测试 get_home() 方法"""

    def test_returns_path_object(self):
        result = PlatformInfo.get_home()
        assert isinstance(result, Path)

    def test_returns_home_directory(self):
        assert PlatformInfo.get_home() == Path.home()


class TestGetAppSupportDir:
    """测试 get_app_support_dir() 方法"""

    @patch("msr_sync.core.platform.platform.system", return_value="Darwin")
    def test_macos_app_support(self, _mock):
        result = PlatformInfo.get_app_support_dir()
        expected = Path.home() / "Library" / "Application Support"
        assert result == expected

    @patch("msr_sync.core.platform.platform.system", return_value="Windows")
    def test_windows_appdata(self, _mock):
        result = PlatformInfo.get_app_support_dir()
        expected = Path.home() / "AppData" / "Roaming"
        assert result == expected

    @patch("msr_sync.core.platform.platform.system", return_value="Linux")
    def test_unsupported_os_raises(self, _mock):
        with pytest.raises(UnsupportedPlatformError):
            PlatformInfo.get_app_support_dir()

    @patch("msr_sync.core.platform.platform.system", return_value="Darwin")
    def test_returns_path_object(self, _mock):
        result = PlatformInfo.get_app_support_dir()
        assert isinstance(result, Path)
