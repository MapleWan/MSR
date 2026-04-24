"""配置浏览页面。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service


@ui.page('/browse')
async def browse_page():
    """配置浏览页面。"""
    with create_layout('配置浏览'):
        ui.label('配置浏览').classes('text-h4 q-mb-md')

        # 加载中
        with ui.row().classes('justify-center w-full q-py-xl'):
            spinner = ui.spinner('dots', size='3rem')

        try:
            configs_data = await repo_service.list_configs()
        except Exception as e:
            ui.notify(f'加载配置失败: {e}', type='negative')
            spinner.delete()
            return

        spinner.delete()

        # 删除确认对话框（创建一次，复用）
        delete_target = {'type': None, 'name': None, 'version': None}

        with ui.dialog() as dialog, ui.card():
            ui.label('确认删除此版本?').classes('text-h6')
            dialog_info = ui.label('').classes('text-body2 text-grey')
            with ui.row().classes('q-gutter-sm justify-end q-mt-md'):
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
        with ui.row().classes('w-full gap-md').style('min-height: 60vh;'):
            # 左侧面板
            with ui.card().style('width: 300px; min-width: 280px;'):
                with ui.tabs().classes('w-full') as tabs:
                    tab_rules = ui.tab('Rules', icon='rule')
                    tab_skills = ui.tab('Skills', icon='build')
                    tab_mcp = ui.tab('MCP', icon='hub')

                with ui.tab_panels(tabs, value=tab_rules).classes('w-full'):
                    with ui.tab_panel(tab_rules):
                        rules_list = ui.column().classes('w-full q-gutter-sm')
                    with ui.tab_panel(tab_skills):
                        skills_list = ui.column().classes('w-full q-gutter-sm')
                    with ui.tab_panel(tab_mcp):
                        mcp_list = ui.column().classes('w-full q-gutter-sm')

            # 右侧详情面板
            with ui.card().classes('col').style('min-width: 400px;'):
                detail_container = ui.column().classes('w-full')

                async def show_detail(name, cfg_type, versions, selected_version=None):
                    detail_container.clear()
                    with detail_container:
                        if name is None:
                            ui.label('请从左侧选择一个配置').classes('text-grey text-center q-pa-xl')
                            return

                        if selected_version is None and versions:
                            selected_version = versions[-1]

                        # 标题
                        ui.label(name).classes('text-h5')
                        ui.label(f'类型: {cfg_type.upper()}').classes('text-caption text-grey q-mb-md')

                        # 版本芯片
                        with ui.row().classes('q-gutter-sm q-mb-md'):
                            for v in (versions or []):
                                color = 'primary' if v == selected_version else 'grey'
                                ui.chip(
                                    v,
                                    color=color,
                                    on_click=lambda _=None, n=name, t=cfg_type, vs=versions, ver=v: show_detail(n, t, vs, ver),
                                )

                        # 内容预览
                        with ui.column().classes('w-full q-mb-md'):
                            if cfg_type == 'rules':
                                with ui.row().classes('justify-center w-full q-py-md'):
                                    content_spinner = ui.spinner('dots', size='2rem')
                                try:
                                    result = await repo_service.read_rule_content(name, selected_version)
                                    content_spinner.delete()
                                    if result.get('success'):
                                        with ui.card().classes('w-full bg-grey-1'):
                                            ui.markdown(result.get('content', '')).classes('q-pa-md')
                                    else:
                                        ui.label(f'读取失败: {result.get("error")}').classes('text-negative')
                                except Exception as e:
                                    content_spinner.delete()
                                    ui.label(f'读取失败: {e}').classes('text-negative')
                            else:
                                try:
                                    path = repo_service.repo.get_config_path(cfg_type, name, selected_version)
                                    with ui.card().classes('w-full bg-grey-1'):
                                        with ui.row().classes('items-center q-pa-md'):
                                            ui.icon('folder').classes('text-primary q-mr-sm')
                                            ui.label(str(path)).classes('text-body2')
                                except Exception as e:
                                    ui.label(f'获取路径失败: {e}').classes('text-negative')

                        # 操作按钮
                        with ui.row().classes('q-gutter-sm'):
                            def open_delete_dialog():
                                delete_target['type'] = cfg_type
                                delete_target['name'] = name
                                delete_target['version'] = selected_version
                                dialog_info.set_text(f'{name} / {selected_version}')
                                dialog.open()

                            ui.button('删除此版本', icon='delete', on_click=open_delete_dialog).props('outline')
                            ui.button(
                                '同步到 IDE',
                                icon='sync',
                                on_click=lambda: ui.navigate.to(f'/sync?name={name}&type={cfg_type}'),
                            ).props('outline')

                def _render_list(container, cfg_type, configs):
                    container.clear()
                    with container:
                        if not configs:
                            ui.label('暂无配置').classes('text-grey text-center q-py-md')
                            return
                        for name, versions in sorted(configs.items()):
                            with ui.button(
                                on_click=lambda _=None, n=name, v=versions, t=cfg_type: show_detail(n, t, v)
                            ).props('flat no-caps').classes('full-width'):
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(name).classes('text-body2')
                                    ui.badge(str(len(versions))).props('color=primary')

                # 渲染列表
                _render_list(rules_list, 'rules', configs_data.get('rules', {}))
                _render_list(skills_list, 'skills', configs_data.get('skills', {}))
                _render_list(mcp_list, 'mcp', configs_data.get('mcp', {}))

                # 初始空状态
                await show_detail(None, None, None)
