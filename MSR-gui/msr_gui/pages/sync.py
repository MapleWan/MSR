"""同步面板页面 — 三栏布局：配置选择 / IDE 选择 / 选项与执行 + 底部日志。"""

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.repo_service import repo_service
from msr_gui.services.sync_service import sync_service
from msr_gui.state import app_state


# 动作类型 -> 中文标签
_ACTION_LABELS = {
    'sync': '同步',
    'overwrite': '覆盖',
    'conflict': '冲突',
    'skip_unsupported': '跳过（不支持全局Rules）',
    'skip_no_config': '跳过（无配置）',
    'skip_no_servers': '跳过（无服务）',
}

# 动作类型 -> 文本颜色类
_ACTION_COLORS = {
    'sync': 'text-emerald-600',
    'overwrite': 'text-amber-600',
    'conflict': 'text-red-600',
    'skip_unsupported': 'text-slate-400',
    'skip_no_config': 'text-slate-400',
    'skip_no_servers': 'text-slate-400',
}

# 配置类型 -> 显示名称
_TYPE_LABELS = {
    'rules': 'Rules',
    'skills': 'Skills',
    'mcp': 'MCP',
}

# Tab 名称 -> 配置类型键
_TAB_TO_TYPE = {
    'Rules': 'rules',
    'Skills': 'skills',
    'MCP': 'mcp',
}


@ui.page('/sync')
async def sync_page():
    """同步面板页面。"""
    with create_layout('同步面板'):
        # ==================== 加载数据 ====================
        configs = await repo_service.list_configs()
        ide_list = await repo_service.get_all_ide_info()

        # ==================== 页面状态 ====================
        selected_configs = {}       # {(type, name): version_or_None}
        selected_ides = set()       # set of ide names
        current_scope = 'global'
        current_project_dir = ''
        current_preview = []
        confirm_overrides = {}
        is_syncing = False

        has_any_config = any(configs.get(t) for t in ('rules', 'skills', 'mcp'))

        # ==================== 页面标题 ====================
        ui.label('同步面板').classes('text-2xl font-bold text-slate-800 q-mb-md')

        # ==================== 空状态 ====================
        if not has_any_config:
            with ui.card().classes('w-full msr-card'):
                with ui.column().classes('items-center p-8 gap-3'):
                    ui.icon('folder_open', size='48px').classes('text-slate-300')
                    ui.label('仓库暂无配置').classes('text-lg font-semibold text-slate-400')
                    ui.label('请先在设置页面初始化仓库或导入配置').classes('text-sm text-slate-400')
                    ui.button('去导入', icon='file_upload', on_click=lambda: ui.navigate.to('/import')).props('outline color=primary').classes('q-mt-sm')
            return

        # ---------- 辅助：构建单行配置选择 ----------
        def _build_config_row(ctype: str, name: str, versions: list):
            """在左栏创建一个配置项：checkbox + 版本选择。"""
            latest = versions[-1] if versions else '?'
            version_opts = ['最新'] + list(reversed(versions))

            with ui.row().classes('items-center q-my-xs w-full'):
                cb = ui.checkbox(f'{name} ({latest})', value=False)
                vs = ui.select(
                    version_opts,
                    value='最新',
                    label='',
                ).classes('q-ml-sm').style('min-width: 90px')

                def _on_change(checked: bool, _ctype=ctype, _name=name, _vs=vs):
                    if checked:
                        ver = None if _vs.value == '最新' else _vs.value
                        selected_configs[(_ctype, _name)] = ver
                    else:
                        selected_configs.pop((_ctype, _name), None)

                cb.on_value_change(
                    lambda e, _on_change=_on_change: _on_change(e.value)
                )
                vs.on_value_change(
                    lambda e, _cb=cb, _on_change=_on_change: _on_change(_cb.value) if _cb.value else None
                )

        # ==================== 三栏布局 ====================
        with ui.row().classes('w-full gap-5'):

            # ---------- 左栏：配置选择 ----------
            with ui.card().style('width: 30%').classes('p-4 msr-card'):
                with ui.row().classes('items-center gap-2 q-mb-sm'):
                    ui.icon('list', size='22px').classes('text-blue-600')
                    ui.label('配置选择').classes('text-sm font-semibold text-slate-700')

                with ui.tabs() as config_tabs:
                    tab_all = ui.tab('全部')
                    tab_rules = ui.tab('Rules')
                    tab_skills = ui.tab('Skills')
                    tab_mcp = ui.tab('MCP')
                panels = ui.tab_panels(config_tabs, value=tab_all)

                with panels:
                    # —— 全部 ——
                    with ui.tab_panel(tab_all):
                        for ctype, items in configs.items():
                            if not items:
                                continue
                            ui.label(_TYPE_LABELS.get(ctype, ctype)).classes(
                                'text-sm font-semibold text-blue-600 q-mt-sm'
                            )
                            for name, versions in items.items():
                                _build_config_row(ctype, name, versions)

                    # —— Rules ——
                    with ui.tab_panel(tab_rules):
                        items = configs.get('rules', {})
                        if not items:
                            ui.label('暂无 Rules 配置').classes('text-slate-400 text-sm')
                        else:
                            for name, versions in items.items():
                                _build_config_row('rules', name, versions)

                    # —— Skills ——
                    with ui.tab_panel(tab_skills):
                        items = configs.get('skills', {})
                        if not items:
                            ui.label('暂无 Skills 配置').classes('text-slate-400 text-sm')
                        else:
                            for name, versions in items.items():
                                _build_config_row('skills', name, versions)

                    # —— MCP ——
                    with ui.tab_panel(tab_mcp):
                        items = configs.get('mcp', {})
                        if not items:
                            ui.label('暂无 MCP 配置').classes('text-slate-400 text-sm')
                        else:
                            for name, versions in items.items():
                                _build_config_row('mcp', name, versions)

            # ---------- 中栏：IDE 选择 ----------
            with ui.card().style('width: 35%').classes('p-4 msr-card'):
                with ui.row().classes('items-center gap-2 q-mb-sm'):
                    ui.icon('devices', size='22px').classes('text-blue-600')
                    ui.label('目标 IDE').classes('text-sm font-semibold text-slate-700')

                with ui.row().classes('w-full gap-2 q-mb-sm'):
                    ui.button('全选', on_click=lambda: _select_all_ides()).props(
                        'flat dense size=sm'
                    )
                    ui.button('取消全选', on_click=lambda: _clear_all_ides()).props(
                        'flat dense size=sm'
                    )

                ide_grid = ui.row().classes('w-full gap-2')

                def _render_ide_grid():
                    ide_grid.clear()
                    with ide_grid:
                        for ide in ide_list:
                            name = ide['name']
                            is_sel = name in selected_ides
                            card_cls = 'msr-ide-card-selected' if is_sel else 'msr-ide-card'

                            with ui.card().on(
                                'click',
                                lambda _e, _name=name: _toggle_ide(_name)
                            ).classes(card_cls).style('width: 30%; min-width: 90px'):
                                with ui.column().classes('items-center w-full gap-1'):
                                    ui.label(name).classes('text-sm font-medium text-center text-slate-700')
                                    if not ide['supports_global_rules']:
                                        ui.label('无全局Rules').classes(
                                            'text-xs text-slate-400 text-center'
                                        )

                def _toggle_ide(name: str):
                    if name in selected_ides:
                        selected_ides.discard(name)
                    else:
                        selected_ides.add(name)
                    _render_ide_grid()

                def _select_all_ides():
                    for ide in ide_list:
                        selected_ides.add(ide['name'])
                    _render_ide_grid()

                def _clear_all_ides():
                    selected_ides.clear()
                    _render_ide_grid()

                _render_ide_grid()

            # ---------- 右栏：同步选项与执行 ----------
            with ui.card().style('width: 35%').classes('p-4 msr-card'):
                with ui.row().classes('items-center gap-2 q-mb-sm'):
                    ui.icon('tune', size='22px').classes('text-blue-600')
                    ui.label('同步选项').classes('text-sm font-semibold text-slate-700')

                # Scope 选择
                ui.label('Scope').classes('text-sm font-medium text-slate-600 q-mb-xs')
                scope_radio = ui.radio(
                    {'global': 'Global', 'project': 'Project'},
                    value='global',
                ).classes('q-mb-sm')
                scope_radio.on_value_change(lambda e: _update_scope(e.value))

                project_container = ui.column().classes('w-full')

                def _update_scope(val: str):
                    nonlocal current_scope
                    current_scope = val
                    project_container.clear()
                    if val == 'project':
                        with project_container:
                            ui.input(
                                label='项目目录',
                                value=current_project_dir,
                                on_change=lambda e: _set_project_dir(e.value),
                            ).classes('w-full')

                def _set_project_dir(val: str):
                    nonlocal current_project_dir
                    current_project_dir = val

                _update_scope('global')

                ui.separator().classes('q-my-md')

                # 预览按钮
                preview_btn = ui.button(
                    '预览同步', on_click=lambda: _run_preview()
                ).props('outline color=primary').classes('full-width')

                # 预览结果区域
                preview_area = ui.column().classes('w-full q-mt-sm')

                # 执行按钮 + loading
                with ui.row().classes('w-full items-center q-mt-sm gap-2'):
                    sync_btn = ui.button(
                        '执行同步', on_click=lambda: _run_sync()
                    ).props('color=primary').classes('full-width')
                spinner = ui.spinner('dots', size='24px')
                spinner.set_visibility(False)

                # ---------- 预览逻辑 ----------
                async def _run_preview():
                    if not selected_configs:
                        ui.notify('请先选择要同步的配置', type='warning')
                        return
                    if not selected_ides:
                        ui.notify('请选择目标 IDE', type='warning')
                        return

                    preview_btn.disable()
                    preview_area.clear()
                    current_preview.clear()
                    confirm_overrides.clear()

                    try:
                        for (ctype, cname), cver in list(selected_configs.items()):
                            previews = await sync_service.preview_sync(
                                ide_names=list(selected_ides),
                                scope=current_scope,
                                config_type=ctype,
                                name=cname,
                                version=cver,
                                project_dir=current_project_dir or None,
                            )
                            current_preview.extend(previews)
                    except Exception as e:
                        ui.notify(f'预览失败: {e}', type='negative')
                    finally:
                        _render_preview()
                        preview_btn.enable()

                def _render_preview():
                    preview_area.clear()
                    with preview_area:
                        if not current_preview:
                            ui.label('无操作需要执行').classes('text-slate-400 text-xs')
                            return

                        ui.label(f'预览结果：共 {len(current_preview)} 项').classes(
                            'text-sm font-semibold text-slate-700 q-mb-xs'
                        )

                        # 表头
                        with ui.row().classes(
                            'w-full msr-table-header q-mb-xs'
                        ):
                            ui.label('IDE').style('width: 22%')
                            ui.label('类型').style('width: 18%')
                            ui.label('名称').style('width: 25%')
                            ui.label('版本').style('width: 15%')
                            ui.label('动作').style('width: 20%')

                        # 列表
                        for item in current_preview:
                            action = item['action']
                            label = _ACTION_LABELS.get(action, action)
                            color = _ACTION_COLORS.get(action, '')

                            with ui.row().classes('w-full text-xs items-center'):
                                ui.label(item['ide']).style('width: 22%').classes('ellipsis text-slate-700')
                                ui.label(
                                    _TYPE_LABELS.get(item['config_type'], item['config_type'])
                                ).style('width: 18%').classes('text-slate-600')
                                ui.label(item['name']).style('width: 25%').classes('ellipsis text-slate-700')
                                ui.label(str(item['version'])).style('width: 15%').classes('text-slate-600')
                                ui.label(label).style('width: 20%').classes(color + ' font-medium')

                # ---------- 执行同步逻辑 ----------
                async def _run_sync():
                    nonlocal is_syncing
                    if not selected_configs:
                        ui.notify('请先选择要同步的配置', type='warning')
                        return
                    if not selected_ides:
                        ui.notify('请选择目标 IDE', type='warning')
                        return
                    if not current_preview:
                        ui.notify('请先点击「预览同步」查看操作列表', type='warning')
                        return

                    # 检查是否有覆盖/冲突项需要确认
                    need_confirm = [
                        p for p in current_preview if p['action'] in ('overwrite', 'conflict')
                    ]
                    if need_confirm:
                        confirmed = await _show_confirm_dialog(need_confirm)
                        if not confirmed:
                            return

                    is_syncing = True
                    sync_btn.disable()
                    preview_btn.disable()
                    spinner.set_visibility(True)
                    log_area.clear()

                    total_synced = 0
                    total_errors = 0

                    try:
                        for (ctype, cname), cver in list(selected_configs.items()):
                            result = await sync_service.sync_configs(
                                ide_names=list(selected_ides),
                                scope=current_scope,
                                project_dir=current_project_dir or None,
                                config_type=ctype,
                                name=cname,
                                version=cver,
                                confirm_overrides=confirm_overrides,
                            )

                            for r in result.get('results', []):
                                ide = r.get('ide', '?')
                                ct = r.get('config_type', '?')
                                nm = r.get('name', '?')
                                ver = r.get('version', '?')

                                if r['status'] == 'synced':
                                    total_synced += 1
                                    log_area.push(
                                        f'[OK] [{ide}] {_TYPE_LABELS.get(ct, ct)}/{nm} ({ver})'
                                    )
                                elif r['status'] == 'skipped':
                                    reason = r.get('reason', '已跳过')
                                    log_area.push(
                                        f'[SKIP] [{ide}] {_TYPE_LABELS.get(ct, ct)}/{nm} ({ver}) — {reason}'
                                    )
                                else:
                                    total_errors += 1
                                    err = r.get('error', '未知错误')
                                    log_area.push(
                                        f'[ERR] [{ide}] {_TYPE_LABELS.get(ct, ct)}/{nm} ({ver}) — {err}'
                                    )
                    except Exception as e:
                        ui.notify(f'同步异常: {e}', type='negative')
                        log_area.push(f'[ERR] 同步异常: {e}')
                    finally:
                        await app_state.refresh()

                        if total_errors == 0:
                            ui.notify(
                                f'同步完成: {total_synced} 项成功',
                                type='positive',
                            )
                        else:
                            ui.notify(
                                f'同步完成: {total_synced} 项成功, {total_errors} 项失败',
                                type='warning',
                            )

                        is_syncing = False
                        sync_btn.enable()
                        preview_btn.enable()
                        spinner.set_visibility(False)

                # ---------- 确认对话框 ----------
                async def _show_confirm_dialog(items: list) -> bool:
                    """弹出覆盖确认对话框，返回用户是否确认。"""
                    cb_refs = {}

                    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md msr-card'):
                        with ui.row().classes('items-center p-5 border-b border-slate-100 gap-2'):
                            ui.icon('warning', size='24px').classes('text-amber-500')
                            ui.label('确认覆盖').classes('text-lg font-semibold text-slate-700')
                        with ui.column().classes('p-5 gap-3'):
                            ui.label('以下配置将覆盖或合并 IDE 中的现有配置：').classes(
                                'text-sm text-slate-500'
                            )

                            for item in items:
                                key = item['key']
                                action_label = _ACTION_LABELS.get(item['action'], item['action'])
                                label = (
                                    f"{item['ide']} / "
                                    f"{_TYPE_LABELS.get(item['config_type'], item['config_type'])} / "
                                    f"{item['name']} ({action_label})"
                                )
                                cb_refs[key] = ui.checkbox(label, value=True)

                        with ui.row().classes('justify-end q-mt-md q-gutter-sm'):
                            ui.button('取消', on_click=lambda: dialog.submit(False)).props('flat')
                            ui.button('确认', on_click=lambda: dialog.submit(True)).props(
                                'color=primary'
                            )

                    confirmed = await dialog

                    if confirmed:
                        for key, cb in cb_refs.items():
                            if cb.value:
                                confirm_overrides[key] = True

                    return confirmed

        # ==================== 底部日志区 ====================
        with ui.card().classes('w-full mt-5 msr-card'):
            with ui.row().classes('items-center p-5 bg-slate-800 gap-2'):
                ui.icon('terminal', size='20px').classes('text-slate-300')
                ui.label('操作日志').classes('text-sm font-semibold text-slate-100')
            log_area = ui.log(max_lines=100).classes('w-full msr-terminal')
            log_area.style('height: 160px')
