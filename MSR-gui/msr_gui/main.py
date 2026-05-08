"""MSR Sync Manager GUI 应用入口。"""

import argparse
import sys
from pathlib import Path

from nicegui import app, ui


def _try_set_macos_dock_icon(png_path: Path) -> None:
    """macOS 下将 Dock 图标替换为指定 PNG。

    pywebview 的 ``icon`` 参数在 macOS 上不会更改 Dock 图标，
    需借助 AppKit 主动设置。任何异常都静默忽略，
    避免影响启动流程。
    """
    if sys.platform != 'darwin':
        return
    try:
        from AppKit import NSApplication, NSImage  # type: ignore
        NSApplication.sharedApplication().setApplicationIconImage_(
            NSImage.alloc().initWithContentsOfFile_(str(png_path))
        )
    except Exception:
        pass


def run():
    """应用入口函数。

    解析命令行参数，导入页面路由模块（通过 ``@ui.page`` 装饰器自动注册），
    然后启动 NiceGUI 应用。
    """
    parser = argparse.ArgumentParser(description='MSR Sync Manager GUI')
    parser.add_argument(
        '--browser',
        action='store_true',
        help='在浏览器中打开（而非原生窗口）',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='服务端口（默认: 8765）',
    )
    args, _ = parser.parse_known_args()

    # 导入页面路由模块 —— @ui.page 装饰器会自动注册各页面路由
    from msr_gui.pages import dashboard, browse, import_page, sync, settings

    # 注册静态资源目录（IDE 图标等）
    from msr_gui.utils import register_static_assets, ASSETS_DIR
    register_static_assets()

    # 图标：
    #   - 浏览器标签页 favicon 用 SVG（矢量、清晰）
    #   - 原生窗口（pywebview）仅支持 PNG/ICO，用 app-icon.png
    favicon_svg = ASSETS_DIR / 'favicon.svg'
    app_icon_png = ASSETS_DIR / 'app-icon.png'

    if not args.browser and app_icon_png.exists():
        # native 模式：pywebview 窗口图标（任务栏 / Dock / 标题栏）
        app.native.window_args['icon'] = str(app_icon_png)
        _try_set_macos_dock_icon(app_icon_png)

    ui.run(
        title='MSR Sync Manager',
        favicon=str(favicon_svg) if favicon_svg.exists() else None,
        port=args.port,
        native=not args.browser,
        reload=False,
        dark=False,
    )


if __name__ == '__main__':
    run()
