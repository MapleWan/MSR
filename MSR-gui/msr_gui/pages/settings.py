"""设置页面。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service


@ui.page('/settings')
async def settings_page():
    """设置页面。"""
    with create_layout('设置'):
        ui.label('设置').classes('text-2xl font-bold text-slate-800 q-mb-md')

        try:
            config = await repo_service.get_config()
            status = await repo_service.get_repo_status()
        except Exception as e:
            ui.notify(f'加载配置失败: {e}', type='negative')
            return

        # ---- 全局配置区 ----
        with ui.card().classes('w-full q-mb-md msr-card'):
            with ui.row().classes('items-center p-5 bg-slate-50 border-b border-slate-100 gap-2'):
                ui.icon('settings', size='24px').classes('text-blue-600')
                ui.label('全局配置').classes('text-lg font-semibold text-slate-700')

            with ui.column().classes('p-5 gap-4'):
                # 仓库路径
                with ui.column().classes('w-full gap-1'):
                    ui.label('仓库路径').classes('text-sm font-medium text-slate-600')
                    repo_path_input = ui.input(value=config.get('repo_path', '')).classes('w-full')

                # 默认 IDE
                with ui.column().classes('w-full gap-2'):
                    ui.label('默认 IDE').classes('text-sm font-medium text-slate-600')
                    with ui.row().classes('gap-4'):
                        current_ides = set(config.get('default_ides', ['all']))
                        ide_checkboxes = {}
                        for ide in ['trae', 'qoder', 'lingma', 'codebuddy', 'all']:
                            ide_checkboxes[ide] = ui.checkbox(ide, value=ide in current_ides)

                # 默认 Scope
                with ui.column().classes('w-full gap-2'):
                    ui.label('默认 Scope').classes('text-sm font-medium text-slate-600')
                    scope_radio = ui.radio(
                        {'global': 'Global', 'project': 'Project'},
                        value=config.get('default_scope', 'global'),
                    )

                # 忽略模式
                with ui.column().classes('w-full gap-2'):
                    ui.label('忽略模式（每行一个）').classes('text-sm font-medium text-slate-600')
                    ignore_text = '\n'.join(config.get('ignore_patterns', []))
                    ignore_input = ui.textarea(value=ignore_text).classes('w-full').props('rows=4')

                # 保存按钮
                async def save_settings(_=None):
                    selected_ides = [k for k, v in ide_checkboxes.items() if v.value]
                    patterns = [p.strip() for p in ignore_input.value.splitlines() if p.strip()]
                    result = await repo_service.save_config(
                        repo_path=repo_path_input.value,
                        default_ides=selected_ides,
                        default_scope=scope_radio.value,
                        ignore_patterns=patterns,
                    )
                    if result.get('success'):
                        ui.notify('配置保存成功', type='positive')
                    else:
                        ui.notify(f'保存失败: {result.get("error")}', type='negative')

                ui.button('保存配置', icon='save', on_click=save_settings, color='primary').classes('q-mt-sm')

        # ---- 仓库管理区 ----
        with ui.card().classes('w-full q-mb-md msr-card'):
            with ui.row().classes('items-center p-5 bg-slate-50 border-b border-slate-100 gap-2'):
                ui.icon('storage', size='24px').classes('text-blue-600')
                ui.label('仓库管理').classes('text-lg font-semibold text-slate-700')

            with ui.column().classes('p-5 gap-4'):
                exists = status.get('exists', False)
                status_color = 'text-emerald-600' if exists else 'text-red-600'
                status_text = '已初始化' if exists else '未初始化'
                with ui.row().classes('items-center gap-2'):
                    ui.icon('circle').classes(status_color).style('font-size: 10px;')
                    ui.label(f'仓库状态: {status_text}').classes(f'text-sm {status_color} font-medium')

                async def on_init(merge=False, _=None):
                    try:
                        result = await repo_service.init_repo(merge=merge)
                        if result.get('success'):
                            msg = '仓库初始化成功'
                            if merge and result.get('total_imported', 0) > 0:
                                msg += f'，合并了 {result["total_imported"]} 项配置'
                            ui.notify(msg, type='positive')
                        else:
                            ui.notify(f'初始化失败: {result.get("error")}', type='negative')
                    except Exception as e:
                        ui.notify(f'初始化失败: {e}', type='negative')

                with ui.row().classes('gap-3'):
                    async def handle_init(_=None):
                        await on_init(merge=False)

                    async def handle_init_merge(_=None):
                        await on_init(merge=True)

                    ui.button('初始化仓库', icon='folder_open', on_click=handle_init).props('outline color=primary')
                    ui.button('初始化并合并已有配置', icon='merge_type', on_click=handle_init_merge).props('outline color=primary')

        # ---- 主题设置 ----
        with ui.card().classes('w-full msr-card'):
            with ui.row().classes('items-center p-5 bg-slate-50 border-b border-slate-100 gap-2'):
                ui.icon('palette', size='24px').classes('text-blue-600')
                ui.label('主题设置').classes('text-lg font-semibold text-slate-700')

            with ui.row().classes('items-center p-5 gap-3'):
                ui.icon('dark_mode', size='20px').classes('text-slate-400')
                ui.label('暗色模式').classes('text-sm font-medium text-slate-600')
                ui.chip('即将支持', color='amber', text_color='white', icon='schedule').props('dense').classes('q-ml-sm')
                ui.tooltip('当前 UI 为浅色主题设计，暗色模式将在后续版本支持').classes('text-xs')
