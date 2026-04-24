"""MSR Sync Manager GUI 应用入口。"""

import argparse

from nicegui import ui


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

    ui.run(
        title='MSR Sync Manager',
        port=args.port,
        native=not args.browser,
        reload=False,
        dark=None,
    )


if __name__ == '__main__':
    run()
