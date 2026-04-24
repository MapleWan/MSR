"""仪表盘页面。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service


@ui.page('/')
async def dashboard_page():
    """仪表盘主页。"""
    with create_layout('仪表盘'):
        ui.label('仪表盘').classes('text-h4 q-mb-md')

        # 加载中状态
        with ui.row().classes('justify-center w-full q-py-xl'):
            spinner = ui.spinner('dots', size='3rem')

        try:
            status = await repo_service.get_repo_status()
            ide_list = await repo_service.get_all_ide_info()
            configs = await repo_service.list_configs()
        except Exception as e:
            ui.notify(f'数据加载失败: {e}', type='negative')
            spinner.delete()
            return

        spinner.delete()

        exists = status.get('exists', False)
        status_color = 'text-positive' if exists else 'text-negative'
        status_icon = 'check_circle' if exists else 'error'
        status_text = '已初始化' if exists else '未初始化'

        # ---- 仓库状态卡片 ----
        with ui.card().classes('w-full q-mb-md'):
            with ui.row().classes('items-center q-pa-sm'):
                ui.icon(status_icon).classes(f'{status_color} text-h3')
                with ui.column().classes('q-ml-md'):
                    ui.label('仓库路径').classes('text-caption text-grey')
                    ui.label(status.get('path', '未知')).classes('text-subtitle1')
                    with ui.row().classes('items-center'):
                        ui.icon('circle').classes(f'{status_color}').style('font-size: 10px;')
                        ui.label(status_text).classes(f'text-body2 {status_color} q-ml-xs')

        # ---- 统计卡片 ----
        rules_count = len(configs.get('rules', {}))
        skills_count = len(configs.get('skills', {}))
        mcp_count = len(configs.get('mcp', {}))

        with ui.row().classes('w-full q-gutter-md q-mb-md'):
            with ui.card().classes('col text-center'):
                with ui.column().classes('items-center q-pa-md'):
                    ui.icon('rule').classes('text-primary text-h4')
                    ui.label(str(rules_count)).classes('text-h3 text-bold q-mt-sm')
                    ui.label('Rules').classes('text-caption text-grey')

            with ui.card().classes('col text-center'):
                with ui.column().classes('items-center q-pa-md'):
                    ui.icon('build').classes('text-secondary text-h4')
                    ui.label(str(skills_count)).classes('text-h3 text-bold q-mt-sm')
                    ui.label('Skills').classes('text-caption text-grey')

            with ui.card().classes('col text-center'):
                with ui.column().classes('items-center q-pa-md'):
                    ui.icon('hub').classes('text-accent text-h4')
                    ui.label(str(mcp_count)).classes('text-h3 text-bold q-mt-sm')
                    ui.label('MCP').classes('text-caption text-grey')

        # ---- 已支持 IDE 列表 ----
        with ui.card().classes('w-full q-mb-md'):
            ui.label('已支持 IDE').classes('text-subtitle1 q-pa-sm')
            with ui.row().classes('q-gutter-sm q-pa-sm wrap'):
                for ide in ide_list:
                    name = ide.get('name', 'Unknown')
                    with ui.card().classes('bg-blue-grey-1'):
                        with ui.row().classes('items-center q-px-md q-py-sm'):
                            ui.icon('computer').classes('text-primary')
                            ui.label(name).classes('text-body2 q-ml-sm')

        # ---- 快捷操作区 ----
        with ui.card().classes('w-full'):
            ui.label('快捷操作').classes('text-subtitle1 q-pa-sm')
            with ui.row().classes('q-gutter-md q-pa-sm'):
                async def do_init():
                    try:
                        result = await repo_service.init_repo()
                        if result.get('success'):
                            ui.notify('仓库初始化成功', type='positive')
                        else:
                            ui.notify(f'初始化失败: {result.get("error")}', type='negative')
                    except Exception as e:
                        ui.notify(f'初始化失败: {e}', type='negative')

                ui.button('初始化仓库', icon='folder_open', on_click=do_init).props('outline')
                ui.button('导入配置', icon='file_upload', on_click=lambda: ui.navigate.to('/import')).props('outline')
                ui.button('快速同步', icon='sync', on_click=lambda: ui.navigate.to('/sync')).props('outline')
