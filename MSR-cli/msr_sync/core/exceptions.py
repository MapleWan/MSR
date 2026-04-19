"""MSR-cli 异常层次结构"""


class MSRError(Exception):
    """MSR-cli 基础异常"""


class RepositoryNotFoundError(MSRError):
    """仓库未初始化"""


class ConfigNotFoundError(MSRError):
    """配置不存在"""


class InvalidSourceError(MSRError):
    """无效的导入来源"""


class UnsupportedPlatformError(MSRError):
    """不支持的操作系统"""


class NetworkError(MSRError):
    """网络错误"""


class ConfigParseError(MSRError):
    """配置解析错误"""
