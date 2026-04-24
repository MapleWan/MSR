"""导入配置页面 — 三步向导。"""

import tempfile
from pathlib import Path

from nicegui import ui

from msr_gui.components.sidebar import create_layout
from msr_gui.services.import_service import import_service
from msr_gui.state import app_state


@ui.page('/import')
async def import_page():
    """导入配置向导页面。"""

    # ==================== 状态对象 ====================
    class State:
        config_type = 'rules'
        source_mode = 'path'          # 'path' | 'url' | 'upload'
        source_value = ''             # 路径或 URL
        uploaded_file_path = ''       # 上传后的临时文件路径
        resolved_items = []           # 解析结果列表
        selected_names = set()        # 用户勾选的配置名称集合
        is_resolving = False
        is_importing = False
        import_results = []           # 导入结果日志
        success_count = 0
        fail_count = 0
        total_count = 0
        resolve_error = ''

    state = State()

    # ==================== 辅助函数 ====================
    def get_source():
        """获取当前有效的来源字符串。"""
        if state.source_mode == 'upload':
            return state.uploaded_file_path
        return state.source_value

    def validate_step1():
        """验证 Step 1 输入是否有效。"""
        source = get_source()
        if not source:
            ui.notify('请输入或选择导入来源', type='negative')
            return False
        if state.source_mode == 'upload' and not Path(source).exists():
            ui.notify('请先上传文件', type='negative')
            return False
        return True

    async def do_resolve():
        """解析来源并填充表格。"""
        source = get_source()
        state.is_resolving = True
        state.resolve_error = ''
        state.resolved_items = []
        state.selected_names = set()
        resolve_spinner.set_visibility(True)
        result_table.set_visibility(False)
        error_label.set_visibility(False)

        result = await import_service.resolve_source(source, state.config_type)

        state.is_resolving = False
        resolve_spinner.set_visibility(False)

        if not result['success']:
            state.resolve_error = result.get('error', '解析失败')
            error_label.text = state.resolve_error
            error_label.set_visibility(True)
            ui.notify(f'解析失败: {state.resolve_error}', type='negative')
            return

        state.resolved_items = result['items']
        for item in state.resolved_items:
            state.selected_names.add(item['name'])

        # 刷新表格数据
        table_rows.refresh()
        result_table.set_visibility(True)

    async def on_next_to_step2():
        """从 Step 1 进入 Step 2：先验证，再解析，再跳转。"""
        if not validate_step1():
            return
        await do_resolve()
        # 如果有解析结果或至少没有阻塞错误，则进入下一步
        if state.resolved_items:
            stepper.next()
        elif not state.resolve_error:
            # 没有结果但也没有错误（空目录等）
            ui.notify('未找到可导入的配置项', type='negative')

    async def do_import():
        """执行导入操作。"""
        selected = [
            item for item in state.resolved_items
            if item['name'] in state.selected_names
        ]
        if not selected:
            ui.notify('请至少选择一项配置', type='negative')
            return

        state.is_importing = True
        state.import_results = []
        state.success_count = 0
        state.fail_count = 0
        state.total_count = len(selected)

        # 进入 Step 3
        stepper.next()

        # 初始化 UI
        import_progress.refresh()
        import_logs.refresh()

        # 启动定时器，每 200ms 刷新一次日志和进度 UI
        refresh_timer = ui.timer(0.2, lambda: (import_progress.refresh(), import_logs.refresh()))

        def progress_callback(name, result_item):
            """导入进度回调（在 IO 线程中执行）。"""
            state.import_results.append(result_item)
            if result_item['status'] == 'success':
                state.success_count += 1
            else:
                state.fail_count += 1

        result = await import_service.import_configs(
            state.config_type, selected, callback=progress_callback
        )

        # 停止定时器并做最终刷新
        refresh_timer.deactivate()

        state.is_importing = False
        # 最终结果可能和回调稍有不同，以返回值为准
        state.success_count = result.get('success_count', 0)
        state.fail_count = result['total'] - state.success_count
        state.total_count = result['total']

        import_progress.refresh()
        import_logs.refresh()

        # 刷新全局状态
        await app_state.refresh()

        if state.fail_count == 0:
            ui.notify(f'导入完成：成功 {state.success_count} 项', type='positive')
        else:
            ui.notify(
                f'导入完成：成功 {state.success_count} 项，失败 {state.fail_count} 项',
                type='warning',
            )

    def on_select_all(checked):
        """全选/取消全选。"""
        if checked:
            state.selected_names = {item['name'] for item in state.resolved_items}
        else:
            state.selected_names = set()
        table_rows.refresh()

    def on_item_toggle(name, checked):
        """单个配置项勾选切换。"""
        if checked:
            state.selected_names.add(name)
        else:
            state.selected_names.discard(name)
        table_rows.refresh()

    def reset_wizard():
        """重置向导状态，回到 Step 1。"""
        state.config_type = 'rules'
        state.source_mode = 'path'
        state.source_value = ''
        state.uploaded_file_path = ''
        state.resolved_items = []
        state.selected_names = set()
        state.import_results = []
        state.success_count = 0
        state.fail_count = 0
        state.total_count = 0
        state.resolve_error = ''
        config_radio.set_value('rules')
        source_tabs.set_value('path')
        path_input.set_value('')
        url_input.set_value('')
        select_all_cb.set_value(True)
        upload_label.text = '尚未选择文件'
        stepper.set_value('选择来源')

    # ==================== UI 构建 ====================
    with create_layout('导入配置'):
        ui.label('导入配置向导').classes('text-h4 q-mb-md')

        with ui.stepper().props('vertical').classes('w-full') as stepper:

            # ---------- Step 1: 选择来源 ----------
            with ui.step('选择来源') as step1:
                ui.label('请选择配置类型和导入来源').classes('text-subtitle1 q-mb-sm')

                # 配置类型选择
                with ui.row().classes('q-gutter-md q-mb-md'):
                    ui.label('配置类型:').classes('text-body1')
                    config_radio = ui.radio(
                        {'rules': 'Rules', 'skills': 'Skills', 'mcp': 'MCP'},
                        value='rules',
                        on_change=lambda e: setattr(state, 'config_type', e.value),
                    )

                # 来源方式切换
                ui.label('导入来源:').classes('text-body1 q-mt-sm')
                with ui.tabs().classes('w-full') as source_tabs:
                    tab_path = ui.tab('path', label='文件/目录路径')
                    tab_url = ui.tab('url', label='URL')
                    tab_upload = ui.tab('upload', label='上传文件')
                source_tabs.on_value_change(lambda e: setattr(state, 'source_mode', e.value))

                with ui.tab_panels(source_tabs, value='path').classes('w-full'):
                    # 面板: 文件/目录路径
                    with ui.tab_panel('path'):
                        path_input = ui.input(
                            label='文件或目录路径',
                            placeholder='输入绝对路径，如 /path/to/rules.md 或 /path/to/dir',
                            on_change=lambda e: setattr(state, 'source_value', e.value),
                        ).classes('w-full')

                    # 面板: URL
                    with ui.tab_panel('url'):
                        url_input = ui.input(
                            label='URL 地址',
                            placeholder='https://example.com/config.md',
                            on_change=lambda e: setattr(state, 'source_value', e.value),
                        ).classes('w-full')

                    # 面板: 上传文件
                    with ui.tab_panel('upload'):
                        async def on_upload(e):
                            """处理文件上传。"""
                            if not e.content:
                                return
                            # 保存到临时文件
                            suffix = Path(e.name).suffix if e.name else ''
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=suffix
                            ) as tmp:
                                tmp.write(e.content.read())
                                state.uploaded_file_path = tmp.name
                            ui.notify(f'已上传: {e.name}', type='positive')
                            upload_label.text = f'已选择: {e.name}'

                        ui.upload(
                            label='上传 .md / .zip / .tar.gz 文件',
                            auto_upload=True,
                            on_upload=on_upload,
                        ).props('accept=".md,.zip,.tar.gz"').classes('w-full')
                        upload_label = ui.label('尚未选择文件').classes('text-caption text-grey')

                with ui.stepper_navigation():
                    ui.button('下一步', on_click=on_next_to_step2, color='primary')

            # ---------- Step 2: 预览确认 ----------
            with ui.step('预览确认') as step2:
                ui.label('解析结果预览').classes('text-subtitle1 q-mb-sm')

                # 解析中 Loading
                with ui.row().classes('items-center q-gutter-sm') as resolve_spinner:
                    ui.spinner('dots', size='24px')
                    ui.label('正在解析来源，请稍候...')
                resolve_spinner.set_visibility(False)

                # 错误提示
                error_label = ui.label('').classes('text-negative text-body1 q-mb-md')
                error_label.set_visibility(False)

                # 解析结果表格区域
                result_table = ui.column().classes('w-full')
                result_table.set_visibility(False)

                with result_table:
                    # 全选按钮
                    with ui.row().classes('items-center q-mb-sm'):
                        select_all_cb = ui.checkbox(
                            '全选',
                            value=True,
                            on_change=lambda e: on_select_all(e.value),
                        )

                    # 表格头部
                    with ui.row().classes('w-full bg-grey-2 text-weight-bold q-pa-sm'):
                        ui.label('').classes('col-1')          # 勾选列
                        ui.label('配置名称').classes('col-5')
                        ui.label('来源类型').classes('col-3')
                        ui.label('路径').classes('col-3')

                    @ui.refreshable
                    def table_rows():
                        """动态刷新表格行。"""
                        if not state.resolved_items:
                            with ui.row().classes('w-full q-pa-sm text-grey'):
                                ui.label('暂无数据')
                            return

                        for item in state.resolved_items:
                            name = item['name']
                            source_type = item.get('source_type', '-')
                            path = item.get('path', '-')
                            checked = name in state.selected_names

                            with ui.row().classes('w-full q-pa-sm items-center border-bottom'):
                                with ui.column().classes('col-1'):
                                    ui.checkbox(
                                        value=checked,
                                        on_change=lambda e, n=name: on_item_toggle(n, e.value),
                                    )
                                ui.label(name).classes('col-5')
                                ui.label(source_type).classes('col-3')
                                with ui.column().classes('col-3'):
                                    ui.label(path).classes('text-caption text-grey ellipsis')

                    table_rows()

                with ui.stepper_navigation():
                    ui.button('上一步', on_click=stepper.previous).props('flat')
                    ui.button('开始导入', on_click=do_import, color='primary')

            # ---------- Step 3: 执行导入 ----------
            with ui.step('执行导入') as step3:
                ui.label('导入进度').classes('text-subtitle1 q-mb-sm')

                @ui.refreshable
                def import_progress():
                    """导入进度显示。"""
                    if state.total_count == 0 and not state.is_importing:
                        ui.label('等待开始导入...').classes('text-grey')
                        return

                    with ui.column().classes('w-full q-gutter-sm'):
                        # 进度文字
                        progress_text = (
                            f'进度: {state.success_count + state.fail_count}/{state.total_count}'
                            if state.total_count > 0
                            else '准备中...'
                        )
                        ui.label(progress_text).classes('text-body1').props('id="import-progress-text"')

                        # 线性进度条
                        if state.total_count > 0:
                            progress_val = (state.success_count + state.fail_count) / state.total_count
                            ui.linear_progress(
                                value=progress_val,
                                show_value=False,
                                size='12px',
                            ).classes('w-full')

                        # 汇总信息（导入完成后显示）
                        if not state.is_importing and state.total_count > 0:
                            with ui.row().classes('q-gutter-md q-mt-sm'):
                                ui.label(
                                    f'成功: {state.success_count} 项'
                                ).classes('text-positive text-weight-bold')
                                if state.fail_count > 0:
                                    ui.label(
                                        f'失败: {state.fail_count} 项'
                                    ).classes('text-negative text-weight-bold')

                import_progress()

                # 实时日志区域
                ui.label('导入日志:').classes('text-subtitle2 q-mt-md q-mb-sm')
                with ui.card().classes('w-full bg-grey-1').style('max-height: 300px; overflow-y: auto;'):
                    @ui.refreshable
                    def import_logs():
                        """导入日志列表。"""
                        if not state.import_results:
                            ui.label('暂无日志').classes('text-grey text-caption q-pa-sm')
                            return

                        for r in state.import_results:
                            status = r['status']
                            name = r['name']
                            if status == 'success':
                                version = r.get('version', '-')
                                msg = f'[成功] {name}  →  {version}'
                                color_class = 'text-positive'
                            else:
                                reason = r.get('reason', '未知错误')
                                msg = f'[失败] {name}  →  {reason}'
                                color_class = 'text-negative'

                            ui.label(msg).classes(f'{color_class} text-caption q-pa-xs')

                    import_logs()

                with ui.stepper_navigation():
                    ui.button('返回仪表盘', on_click=lambda: ui.navigate.to('/')).props('flat')
                    ui.button('继续导入', on_click=reset_wizard, color='primary')
