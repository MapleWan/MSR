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
    # 设置 Quasar 主题色（必须在 @ui.page 函数内部调用，NiceGUI 3.x 要求）
    ui.colors(
        primary='#7B8FA2',
        secondary='#8FA89B',
        accent='#9E8EA1',
        positive='#8FA89B',
        negative='#C08B7E',
        warning='#C4A882',
        info='#8E9EAC',
    )

    # 注入全局样式（NiceGUI 3.x 多页面模式下必须在 @ui.page 函数内部调用）
    ui.add_head_html('''
    <style>
      /* 页面背景 */
      body { background-color: #F0EDEA !important; }
      .q-page { background-color: #F0EDEA !important; }

      /* 侧边栏 */
      .q-drawer { background: #5A6872 !important; }

      /* 统一卡片样式 */
      .msr-card {
        background: white;
        border: 1px solid #DDD8D3;
        border-radius: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: box-shadow 0.15s ease-out, border-color 0.15s ease-out;
      }
      .msr-card-hover:hover {
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-color: #C5BFBA;
      }

      /* 侧边栏导航按钮 */
      .msr-nav-btn {
        color: #A0A8AE !important;
        border-radius: 0.5rem !important;
        transition: all 0.15s ease-out !important;
        border-left: 3px solid transparent !important;
        padding: 0.375rem 0.75rem !important;
        text-transform: none !important;
        justify-content: flex-start !important;
      }
      .msr-nav-btn:hover {
        background: rgba(74, 85, 94, 0.6) !important;
        color: #E8E4E0 !important;
      }
      .msr-nav-btn-active {
        background: rgba(123, 143, 162, 0.2) !important;
        color: #7B8FA2 !important;
        border-left-color: #7B8FA2 !important;
      }

      /* 终端风格日志 */
      .msr-terminal {
        background: #4A555E;
        color: #E8E4E0;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.8125rem;
        border-radius: 0.5rem;
        padding: 1rem;
        line-height: 1.6;
      }

      /* 左边框强调 */
      .msr-border-blue { border-left: 4px solid #7B8FA2; }
      .msr-border-green { border-left: 4px solid #8FA89B; }
      .msr-border-violet { border-left: 4px solid #9E8EA1; }
      .msr-border-amber { border-left: 4px solid #C4A882; }

      /* IDE 卡片 */
      .msr-ide-card {
        border: 1.5px solid #DDD8D3;
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
        cursor: pointer;
        transition: all 0.15s ease-out;
        background: white;
      }
      .msr-ide-card:hover {
        border-color: #B5AEA8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
      }
      .msr-ide-card-selected {
        background: #F0EDEA;
        border-color: #7B8FA2;
        box-shadow: 0 0 0 3px rgba(123, 143, 162, 0.15);
      }

      /* 配置列表项 */
      .msr-config-item {
        border-left: 2px solid transparent;
        transition: all 0.15s ease-out;
      }
      .msr-config-item:hover {
        background: #F0EDEA;
      }
      .msr-config-item-selected {
        background: rgba(240, 237, 234, 0.7);
        border-left-color: #7B8FA2;
      }

      /* 版本 chip（应用于 Quasar button，需强选择器权重覆盖默认样式） */
      .q-btn.msr-chip {
        background: #E2DDD9 !important;
        color: #5A6872 !important;
        border-radius: 9999px !important;
        padding: 0.125rem 0.625rem !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        min-height: unset !important;
        transition: all 0.15s ease-out;
      }
      .q-btn.msr-chip .q-btn__content {
        color: inherit !important;
      }
      .q-btn.msr-chip:hover {
        background: #D5CFCA !important;
      }
      .q-btn.msr-chip-selected {
        background: #7B8FA2 !important;
        color: #ffffff !important;
      }
      .q-btn.msr-chip-selected .q-btn__content {
        color: #ffffff !important;
      }

      /* 表格头部 */
      .msr-table-header {
        background: #F5F2EF;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #7A7570;
        font-weight: 600;
      }

      /* Stepper 左侧指示条 */
      .q-stepper--vertical .q-stepper__tab--active,
      .q-stepper--vertical .q-stepper__tab--done {
        color: #7B8FA2 !important;
      }
      .q-stepper--vertical .q-stepper__dot {
        background: #7B8FA2 !important;
      }
      .q-stepper--vertical .q-stepper__tab--done .q-stepper__dot {
        background: #8FA89B !important;
      }

      /* markdown 预览区 */
      .msr-markdown-preview {
        background: #F5F2EF;
        border-radius: 0.5rem;
        padding: 1rem;
        border: 1px solid #DDD8D3;
      }
    </style>
    ''')

    # 先创建 drawer，确保 header 中的按钮可以引用它
    drawer = ui.left_drawer(value=True).classes('bg-slate-900')
    with drawer:
        # Logo / 标题区域
        with ui.row().classes('items-center q-pa-md q-mb-sm'):
            ui.icon('sync', size='28px').classes('text-blue-400')
            ui.label('MSR Sync').classes('text-h6 text-white font-bold')
        ui.separator().classes('bg-slate-700 q-mb-md')

        nav_items = [
            ('仪表盘', 'dashboard', '/'),
            ('配置浏览', 'folder_open', '/browse'),
            ('导入配置', 'file_upload', '/import'),
            ('同步面板', 'sync', '/sync'),
            ('设置', 'settings', '/settings'),
        ]

        # 获取当前页面路径以高亮活跃导航
        try:
            current_path = ui.context.client.page.path
        except Exception:
            current_path = '/'

        with ui.column().classes('q-px-md w-full'):
            for label, icon, path in nav_items:
                is_active = path == current_path
                active_cls = 'msr-nav-btn-active' if is_active else ''

                def _nav(p=path, active=is_active):
                    # 已在当前页：不重复跳转，避免页面刷新
                    if active:
                        return
                    ui.navigate.to(p)

                ui.button(
                    label,
                    icon=icon,
                    on_click=_nav,
                ).props('flat no-caps').classes(f'full-width msr-nav-btn {active_cls}')

        # 底部版本号
        with ui.column().classes('absolute-bottom q-pa-md'):
            ui.label('v0.1.0').classes('text-xs text-slate-500 text-center w-full')

    # 顶部导航栏
    with ui.header().classes('items-center justify-between bg-slate-800'):
        with ui.row().classes('items-center'):
            ui.button(
                icon='menu',
                on_click=drawer.toggle,
            ).props('flat color=white')
            ui.label('MSR Sync Manager').classes('text-h6 text-white font-bold')

    # 返回主内容区域
    return ui.column().classes('w-full p-8')
