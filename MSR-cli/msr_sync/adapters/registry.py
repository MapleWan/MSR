"""适配器注册表 — 管理和查找 IDE 适配器实例"""

from typing import Dict, List, Type

from msr_sync.adapters.base import BaseAdapter


# 适配器类的延迟加载映射表
# 键为 IDE 名称，值为 (模块路径, 类名) 元组
_ADAPTER_REGISTRY: Dict[str, tuple] = {
    "qoder": ("msr_sync.adapters.qoder", "QoderAdapter"),
    "lingma": ("msr_sync.adapters.lingma", "LingmaAdapter"),
    "trae": ("msr_sync.adapters.trae", "TraeAdapter"),
    "codebuddy": ("msr_sync.adapters.codebuddy", "CodeBuddyAdapter"),
}

# 适配器实例缓存
_adapter_instances: Dict[str, BaseAdapter] = {}


def _load_adapter_class(ide_name: str) -> Type[BaseAdapter]:
    """延迟加载适配器类。

    Args:
        ide_name: IDE 标识名称

    Returns:
        适配器类

    Raises:
        ValueError: IDE 名称不在支持列表中
        ImportError: 适配器模块尚未实现
    """
    if ide_name not in _ADAPTER_REGISTRY:
        supported = ", ".join(sorted(_ADAPTER_REGISTRY.keys()))
        raise ValueError(f"不支持的 IDE: {ide_name}，支持的 IDE: {supported}")

    module_path, class_name = _ADAPTER_REGISTRY[ide_name]
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_adapter(ide_name: str) -> BaseAdapter:
    """根据 IDE 名称获取适配器实例。

    使用缓存避免重复创建实例。

    Args:
        ide_name: IDE 标识名称（qoder、lingma、trae、codebuddy）

    Returns:
        对应的适配器实例

    Raises:
        ValueError: IDE 名称不在支持列表中
    """
    if ide_name not in _adapter_instances:
        adapter_class = _load_adapter_class(ide_name)
        _adapter_instances[ide_name] = adapter_class()
    return _adapter_instances[ide_name]


def get_all_adapters() -> List[BaseAdapter]:
    """获取所有已注册的适配器实例。

    Returns:
        所有适配器实例的列表
    """
    return [get_adapter(name) for name in _ADAPTER_REGISTRY]


def resolve_ide_list(ide_names: tuple) -> List[BaseAdapter]:
    """解析 --ide 参数，将 IDE 名称元组转换为适配器实例列表。

    当参数包含 'all' 时，展开为所有已注册的适配器。

    Args:
        ide_names: IDE 名称元组，如 ('trae', 'qoder') 或 ('all',)

    Returns:
        对应的适配器实例列表
    """
    if "all" in ide_names:
        return get_all_adapters()
    return [get_adapter(name) for name in ide_names]
