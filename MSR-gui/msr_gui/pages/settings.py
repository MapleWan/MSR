"""设置页面。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service


@ui.page('/settings')
async def settings_page():
    """设置页面。"""
    with create_layout('设置'):
        ui.label('设置').classes('text-h4 q-mb-md')

        # 加载中
        with ui.row().classes('justify-center w-full q-py-xl'):
            spinner = ui.spinner('dots', size='3rem')

        try:
            config = await repo_service.get_config()
            status = await repo_service.get_repo_status()
        except Exception as e:
            ui.notify(f'加载配置失败: {e}', type='negative')
            spinner.delete()
            return

        spinner.delete()

        # ---- 全局配置区 ----
        with ui.card().classes('w-full q-mb-md'):
            ui.label('全局配置').classes('text-h6 q-pa-sm')

            # 仓库路径
            repo_path_input = ui.input('仓库路径', value=config.get('repo_path', '')).classes('w-full')

            # 默认 IDE
            with ui.column().classes('q-mt-sm'):
                ui.label('默认 IDE').classes('text-body2')
                with ui.row().classes('q-gutter-md q-mt-xs'):
                    current_ides = set(config.get('default_ides', ['all']))
                    ide_checkboxes = {}
                    for ide in ['trae', 'qoder', 'lingma', 'codebuddy', 'all']:
                        ide_checkboxes[ide] = ui.checkbox(ide, value=ide in current_ides)

            # 默认 Scope
            with ui.column().classes('q-mt-sm'):
                ui.label('默认 Scope').classes('text-body2')
                scope_radio = ui.radio(
                    {'global': 'Global', 'project': 'Project'},
                    value=config.get('default_scope', 'global'),
                ).classes('q-mt-xs')

            # 忽略模式
            with ui.column().classes('q-mt-sm'):
                ui.label('忽略模式（每行一个）').classes('text-body2')
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

            ui.button('保存配置', icon='save', on_click=save_settings).classes('q-mt-md')

        # ---- 仓库管理区 ----
        with ui.card().classes('w-full q-mb-md'):
            ui.label('仓库管理').classes('text-h6 q-pa-sm')

            exists = status.get('exists', False)
            status_color = 'text-positive' if exists else 'text-negative'
            status_text = '已初始化' if exists else '未初始化'
            ui.label(f'仓库状态: {status_text}').classes(f'text-body2 {status_color} q-pa-sm')

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

            with ui.row().classes('q-gutter-sm q-pa-sm'):
                async def handle_init(_=None):
                    await on_init(merge=False)

                async def handle_init_merge(_=None):
                    await on_init(merge=True)

                ui.button('初始化仓库', icon='folder_open', on_click=handle_init).props('outline')
                ui.button('初始化并合并已有配置', icon='merge_type', on_click=handle_init_merge).props('outline')

        # ---- 主题设置 ----
        with ui.card().classes('w-full'):
            ui.label('主题设置').classes('text-h6 q-pa-sm')

            dark = ui.dark_mode()
            current_dark = bool(dark.value) if dark.value is not None else False

            def on_dark_change(e):
                dark.set_value(e.value)

            ui.switch('暗色模式', value=current_dark, on_change=on_dark_change).classes('q-pa-sm')
