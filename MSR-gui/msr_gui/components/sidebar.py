"""侧边栏与公共布局组件。"""

from nicegui import ui


def create_layout(title: str):
    """创建统一页面布局，返回主内容区域容器。

    每个页面通过 ``with create_layout('页面标题'):`` 使用，
    在 with 块内添加的组件会自动放入主内容区域。

    Args:
        title: 页面标题，用于后续可能的页面标识。

    Returns:
        主内容区域的 ui.column 容器，可作为上下文管理器使用。
    """
    # 先创建 drawer，确保 header 中的按钮可以引用它
    drawer = ui.left_drawer(value=True).classes('bg-blue-grey-1')
    with drawer:
        ui.label('MSR Sync Manager').classes('text-h6 q-mb-md')
        ui.separator()
        nav_items = [
            ('仪表盘', 'dashboard', '/'),
            ('配置浏览', 'folder_open', '/browse'),
            ('导入配置', 'file_upload', '/import'),
            ('同步面板', 'sync', '/sync'),
            ('设置', 'settings', '/settings'),
        ]
        with ui.column().classes('q-gutter-sm w-full'):
            for label, icon, path in nav_items:
                ui.button(
                    label,
                    icon=icon,
                    on_click=lambda p=path: ui.navigate.to(p),
                ).props('flat align=left').classes('full-width')

    # 顶部导航栏
    with ui.header().classes('bg-primary items-center justify-between'):
        with ui.row().classes('items-center'):
            ui.button(
                icon='menu',
                on_click=drawer.toggle,
            ).props('flat color=white')
            ui.label('MSR Sync Manager').classes('text-h6 text-white')

    # 返回主内容区域
    return ui.column().classes('w-full p-6')
