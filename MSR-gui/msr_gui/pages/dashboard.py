"""仪表盘页面。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service


@ui.page('/')
async def dashboard_page():
    """仪表盘主页。"""
    with create_layout('仪表盘'):
        ui.label('仪表盘').classes('text-2xl font-bold text-slate-800 q-mb-md')

        try:
            status = await repo_service.get_repo_status()
            ide_list = await repo_service.get_all_ide_info()
            configs = await repo_service.list_configs()
        except Exception as e:
            ui.notify(f'数据加载失败: {e}', type='negative')
            return

        exists = status.get('exists', False)
        status_color = 'text-emerald-600' if exists else 'text-amber-600'
        status_icon = 'check_circle' if exists else 'error'
        status_text = '已初始化' if exists else '未初始化'

        # ---- 仓库状态卡片 ----
        status_border_cls = 'msr-border-green' if exists else 'msr-border-amber'
        with ui.card().classes(f'w-full q-mb-md msr-card {status_border_cls}'):
            with ui.row().classes('items-center justify-between p-5'):
                with ui.row().classes('items-center gap-4'):
                    ui.icon(status_icon).classes(f'{status_color}').style('font-size: 32px;')
                    with ui.column().classes('gap-1'):
                        ui.label('仓库路径').classes('text-xs uppercase tracking-wide text-slate-400')
                        ui.label(status.get('path', '未知')).classes('text-base text-slate-800 font-medium')
                        with ui.row().classes('items-center gap-1'):
                            ui.icon('circle').classes(f'{status_color}').style('font-size: 8px;')
                            ui.label(status_text).classes(f'text-sm {status_color} font-medium')

        # ---- 统计卡片 ----
        rules_count = len(configs.get('rules', {}))
        skills_count = len(configs.get('skills', {}))
        mcp_count = len(configs.get('mcp', {}))

        with ui.row().classes('w-full gap-5 q-mb-md'):
            with ui.card().classes('col msr-card'):
                with ui.column().classes('p-5 gap-3'):
                    ui.label('Rules').classes('text-xs uppercase tracking-wide text-slate-400')
                    ui.label(str(rules_count)).classes('text-3xl font-bold text-blue-600')
                    ui.icon('rule').classes('text-blue-400').style('font-size: 20px;')

            with ui.card().classes('col msr-card'):
                with ui.column().classes('p-5 gap-3'):
                    ui.label('Skills').classes('text-xs uppercase tracking-wide text-slate-400')
                    ui.label(str(skills_count)).classes('text-3xl font-bold text-emerald-600')
                    ui.icon('build').classes('text-emerald-400').style('font-size: 20px;')

            with ui.card().classes('col msr-card'):
                with ui.column().classes('p-5 gap-3'):
                    ui.label('MCP').classes('text-xs uppercase tracking-wide text-slate-400')
                    ui.label(str(mcp_count)).classes('text-3xl font-bold text-violet-600')
                    ui.icon('hub').classes('text-violet-400').style('font-size: 20px;')

        # ---- 已支持 IDE 列表 ----
        with ui.card().classes('w-full q-mb-md msr-card'):
            with ui.row().classes('items-center p-5 border-b border-slate-100 gap-2'):
                ui.icon('computer', size='22px').classes('text-blue-600')
                ui.label('已支持 IDE').classes('text-lg font-semibold text-slate-700')
            with ui.row().classes('gap-3 p-5 wrap'):
                for ide in ide_list:
                    name = ide.get('name', 'Unknown')
                    with ui.card().classes('msr-card-hover cursor-pointer').style('border: 1px solid #e2e8f0;'):
                        with ui.row().classes('items-center px-4 py-2 gap-2'):
                            ui.icon('computer').classes('text-blue-600')
                            ui.label(name).classes('text-sm text-slate-700 font-medium')

        # ---- 快捷操作区 ----
        with ui.card().classes('w-full msr-card'):
            with ui.row().classes('items-center p-5 border-b border-slate-100 gap-2'):
                ui.icon('bolt', size='22px').classes('text-amber-500')
                ui.label('快捷操作').classes('text-lg font-semibold text-slate-700')
            with ui.row().classes('gap-4 p-5'):
                async def do_init():
                    try:
                        result = await repo_service.init_repo()
                        if result.get('success'):
                            ui.notify('仓库初始化成功', type='positive')
                        else:
                            ui.notify(f'初始化失败: {result.get("error")}', type='negative')
                    except Exception as e:
                        ui.notify(f'初始化失败: {e}', type='negative')

                ui.button('初始化仓库', icon='folder_open', on_click=do_init).props('outline color=primary')
                ui.button('导入配置', icon='file_upload', on_click=lambda: ui.navigate.to('/import')).props('outline color=primary')
                ui.button('快速同步', icon='sync', on_click=lambda: ui.navigate.to('/sync')).props('outline color=primary')
