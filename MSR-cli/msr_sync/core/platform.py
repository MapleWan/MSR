"""平台检测模块 — 检测操作系统并提供平台特定路径"""

import platform
from pathlib import Path

from msr_sync.core.exceptions import UnsupportedPlatformError


class PlatformInfo:
    """平台信息检测与路径解析"""

    @staticmethod
    def get_os() -> str:
        """返回当前操作系统标识。

        Returns:
            'macos' 或 'windows'

        Raises:
            UnsupportedPlatformError: 当前操作系统不受支持时抛出
        """
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        else:
            raise UnsupportedPlatformError(
                f"不支持的操作系统: {platform.system()}"
            )

    @staticmethod
    def get_home() -> Path:
        """获取用户主目录。

        Returns:
            用户主目录的 Path 对象
        """
        return Path.home()

    @staticmethod
    def get_app_support_dir() -> Path:
        """获取应用数据目录。

        macOS: ~/Library/Application Support
        Windows: ~/AppData/Roaming

        Returns:
            应用数据目录的 Path 对象

        Raises:
            UnsupportedPlatformError: 当前操作系统不受支持时抛出
        """
        os_name = PlatformInfo.get_os()
        home = PlatformInfo.get_home()
        if os_name == "macos":
            return home / "Library" / "Application Support"
        else:  # windows
            return home / "AppData" / "Roaming"
