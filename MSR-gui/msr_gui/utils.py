"""通用工具：静态资源注册与 IDE 图标 URL 解析。"""

from __future__ import annotations

from pathlib import Path

from nicegui import app

# 资源根目录
_ASSETS_ROOT = Path(__file__).parent / 'assets'
ICONS_DIR = _ASSETS_ROOT / 'icons'

# 按优先级尝试的扩展名：矢量最佳，其次 PNG
_ICON_EXTS = ('svg', 'png', 'webp', 'ico')


def register_static_assets() -> None:
    """注册静态资源目录到 NiceGUI（仅需调用一次）。

    挂载后可通过 ``/icons/<file>`` 访问 ``msr_gui/assets/icons/`` 下的文件。
    """
    if ICONS_DIR.is_dir():
        app.add_static_files('/icons', str(ICONS_DIR))


def get_ide_icon_url(ide_name: str) -> str | None:
    """返回指定 IDE 的图标 URL，找不到返回 None。

    Args:
        ide_name: 适配器的 ``ide_name`` 值（如 ``'cursor'``、``'qoder'``）。

    Returns:
        形如 ``'/icons/cursor.png'`` 的前端可访问 URL；若无图标则返回 None。
    """
    if not ide_name:
        return None
    name = ide_name.lower()
    for ext in _ICON_EXTS:
        if (ICONS_DIR / f'{name}.{ext}').exists():
            return f'/icons/{name}.{ext}'
    return None
