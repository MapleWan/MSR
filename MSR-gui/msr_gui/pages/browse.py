"""配置浏览页面。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service


@ui.page('/browse')
async def browse_page():
    """配置浏览页面。"""
    with create_layout('配置浏览'):
        ui.label('配置浏览').classes('text-2xl font-bold text-slate-800 q-mb-md')

        try:
            configs_data = await repo_service.list_configs()
        except Exception as e:
            ui.notify(f'加载配置失败: {e}', type='negative')
            return

        # 删除确认对话框（创建一次，复用）
        delete_target = {'type': None, 'name': None, 'version': None}

        with ui.dialog() as dialog, ui.card().classes('msr-card'):
            with ui.row().classes('items-center p-5 border-b border-slate-100 gap-2'):
                ui.icon('warning', size='24px').classes('text-red-500')
                ui.label('确认删除此版本?').classes('text-lg font-semibold text-slate-700')
            with ui.column().classes('p-5 gap-4'):
                dialog_info = ui.label('').classes('text-sm text-slate-500')
                with ui.row().classes('gap-3 justify-end'):
                    ui.button('取消', on_click=dialog.close).props('flat')

                    async def do_remove(_=None):
                        t = delete_target['type']
                        n = delete_target['name']
                        v = delete_target['version']
                        if not t or not n or not v:
                            dialog.close()
                            return
                        result = await repo_service.remove_config(t, n, v)
                        if result.get('success'):
                            ui.notify('删除成功', type='positive')
                            dialog.close()
                            # 刷新列表
                            nonlocal configs_data
                            try:
                                configs_data = await repo_service.list_configs()
                            except Exception as ex:
                                ui.notify(f'刷新失败: {ex}', type='negative')
                                return
                            _render_list(rules_list, 'rules', configs_data.get('rules', {}))
                            _render_list(skills_list, 'skills', configs_data.get('skills', {}))
                            _render_list(mcp_list, 'mcp', configs_data.get('mcp', {}))
                            await show_detail(None, None, None)
                        else:
                            ui.notify(f'删除失败: {result.get("error")}', type='negative')

                    ui.button('确认删除', on_click=do_remove, color='negative')

        # ---- 主布局：左侧列表 + 右侧详情 ----
        with ui.row().classes('w-full gap-5').style('min-height: 60vh;'):
            # 左侧面板
            with ui.card().style('width: 300px; min-width: 280px;').classes('msr-card bg-slate-50'):
                with ui.tabs().classes('w-full text-slate-700') as tabs:
                    tab_rules = ui.tab('Rules', icon='rule')
                    tab_skills = ui.tab('Skills', icon='build')
                    tab_mcp = ui.tab('MCP', icon='hub')

                with ui.tab_panels(tabs, value=tab_rules).classes('w-full bg-transparent'):
                    with ui.tab_panel(tab_rules):
                        rules_list = ui.column().classes('w-full gap-1')
                    with ui.tab_panel(tab_skills):
                        skills_list = ui.column().classes('w-full gap-1')
                    with ui.tab_panel(tab_mcp):
                        mcp_list = ui.column().classes('w-full gap-1')

            # 右侧详情面板
            with ui.card().classes('col msr-card').style('min-width: 400px;'):
                detail_container = ui.column().classes('w-full')

                async def show_detail(name, cfg_type, versions, selected_version=None):
                    detail_container.clear()
                    with detail_container:
                        if name is None:
                            with ui.column().classes('items-center justify-center w-full q-py-xl gap-3'):
                                ui.icon('folder_open', size='48px').classes('text-slate-300')
                                ui.label('请从左侧选择一个配置').classes('text-sm text-slate-400')
                            return

                        if selected_version is None and versions:
                            selected_version = versions[-1]

                        # 标题行
                        with ui.row().classes('items-center gap-3 p-5 border-b border-slate-100'):
                            ui.label(name).classes('text-xl font-bold text-slate-800')
                            ui.label(cfg_type.upper()).classes('text-xs uppercase tracking-wide text-slate-400 bg-slate-100 px-2 py-0.5 rounded')

                        with ui.column().classes('p-5 gap-4'):
                            # 版本芯片
                            with ui.row().classes('gap-2'):
                                for v in (versions or []):
                                    is_selected = v == selected_version
                                    chip_cls = 'msr-chip-selected' if is_selected else 'msr-chip'
                                    ui.button(
                                        v,
                                        on_click=lambda _=None, n=name, t=cfg_type, vs=versions, ver=v: show_detail(n, t, vs, ver),
                                    ).props('flat dense no-caps padding="xs sm"').classes(chip_cls)

                            # 内容预览
                            with ui.column().classes('w-full'):
                                if cfg_type == 'rules':
                                    with ui.row().classes('justify-center w-full q-py-md'):
                                        content_spinner = ui.spinner('dots', size='2rem')
                                    try:
                                        result = await repo_service.read_rule_content(name, selected_version)
                                        content_spinner.delete()
                                        if result.get('success'):
                                            with ui.column().classes('w-full msr-markdown-preview'):
                                                ui.markdown(result.get('content', '')).classes('text-sm text-slate-700')
                                        else:
                                            ui.label(f'读取失败: {result.get("error")}').classes('text-red-600 text-sm')
                                    except Exception as e:
                                        content_spinner.delete()
                                        ui.label(f'读取失败: {e}').classes('text-red-600 text-sm')
                                else:
                                    try:
                                        path = repo_service.repo.get_config_path(cfg_type, name, selected_version)
                                        with ui.column().classes('w-full msr-markdown-preview'):
                                            with ui.row().classes('items-center gap-2'):
                                                ui.icon('folder').classes('text-blue-600')
                                                ui.label(str(path)).classes('text-sm text-slate-700')
                                    except Exception as e:
                                        ui.label(f'获取路径失败: {e}').classes('text-red-600 text-sm')

                            # 操作按钮
                            with ui.row().classes('gap-3'):
                                def open_delete_dialog():
                                    delete_target['type'] = cfg_type
                                    delete_target['name'] = name
                                    delete_target['version'] = selected_version
                                    dialog_info.set_text(f'{name} / {selected_version}')
                                    dialog.open()

                                ui.button('删除此版本', icon='delete', on_click=open_delete_dialog).props('outline color=negative')
                                ui.button(
                                    '同步到 IDE',
                                    icon='sync',
                                    on_click=lambda: ui.navigate.to(f'/sync?name={name}&type={cfg_type}'),
                                ).props('outline color=primary')

                def _render_list(container, cfg_type, configs):
                    container.clear()
                    with container:
                        if not configs:
                            ui.label('暂无配置').classes('text-slate-400 text-center text-sm q-py-md')
                            return
                        for name, versions in sorted(configs.items()):
                            with ui.button(
                                on_click=lambda _=None, n=name, v=versions, t=cfg_type: show_detail(n, t, v)
                            ).props('flat no-caps').classes('full-width text-slate-700 hover:bg-slate-100'):
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(name).classes('text-sm font-medium')
                                    ui.badge(str(len(versions))).props('color=primary rounded')

                # 渲染列表
                _render_list(rules_list, 'rules', configs_data.get('rules', {}))
                _render_list(skills_list, 'skills', configs_data.get('skills', {}))
                _render_list(mcp_list, 'mcp', configs_data.get('mcp', {}))

                # 初始空状态
                await show_detail(None, None, None)
