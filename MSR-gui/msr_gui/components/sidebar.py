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
        primary='#2563eb',
        secondary='#059669',
        accent='#7c3aed',
        positive='#059669',
        negative='#dc2626',
        warning='#d97706',
        info='#3b82f6',
    )

    # 注入全局样式（NiceGUI 3.x 多页面模式下必须在 @ui.page 函数内部调用）
    ui.add_head_html('''
    <style>
      /* 页面背景 */
      body { background-color: #f1f5f9 !important; }
      .q-page { background-color: #f1f5f9 !important; }

      /* 侧边栏 */
      .q-drawer { background: #0f172a !important; }

      /* 统一卡片样式 */
      .msr-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: box-shadow 0.15s ease-out, border-color 0.15s ease-out;
      }
      .msr-card-hover:hover {
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-color: #cbd5e1;
      }

      /* 侧边栏导航按钮 */
      .msr-nav-btn {
        color: #94a3b8 !important;
        border-radius: 0.5rem !important;
        transition: all 0.15s ease-out !important;
        border-left: 3px solid transparent !important;
        padding: 0.375rem 0.75rem !important;
        text-transform: none !important;
        justify-content: flex-start !important;
      }
      .msr-nav-btn:hover {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #e2e8f0 !important;
      }
      .msr-nav-btn-active {
        background: rgba(37, 99, 235, 0.15) !important;
        color: #60a5fa !important;
        border-left-color: #3b82f6 !important;
      }

      /* 终端风格日志 */
      .msr-terminal {
        background: #0f172a;
        color: #e2e8f0;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.8125rem;
        border-radius: 0.5rem;
        padding: 1rem;
        line-height: 1.6;
      }

      /* 左边框强调 */
      .msr-border-blue { border-left: 4px solid #2563eb; }
      .msr-border-green { border-left: 4px solid #059669; }
      .msr-border-violet { border-left: 4px solid #7c3aed; }
      .msr-border-amber { border-left: 4px solid #d97706; }

      /* IDE 卡片 */
      .msr-ide-card {
        border: 1.5px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
        cursor: pointer;
        transition: all 0.15s ease-out;
        background: white;
      }
      .msr-ide-card:hover {
        border-color: #94a3b8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
      }
      .msr-ide-card-selected {
        background: #eff6ff;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }

      /* 配置列表项 */
      .msr-config-item {
        border-left: 2px solid transparent;
        transition: all 0.15s ease-out;
      }
      .msr-config-item:hover {
        background: #f1f5f9;
      }
      .msr-config-item-selected {
        background: rgba(239, 246, 255, 0.5);
        border-left-color: #3b82f6;
      }

      /* 版本 chip */
      .msr-chip {
        background: #dbeafe;
        color: #1d4ed8;
        border-radius: 9999px;
        padding: 0.125rem 0.625rem;
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s ease-out;
      }
      .msr-chip:hover {
        background: #bfdbfe;
      }
      .msr-chip-selected {
        background: #2563eb;
        color: white;
      }

      /* 表格头部 */
      .msr-table-header {
        background: #f8fafc;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
      }

      /* Stepper 左侧指示条 */
      .q-stepper--vertical .q-stepper__tab--active,
      .q-stepper--vertical .q-stepper__tab--done {
        color: #2563eb !important;
      }
      .q-stepper--vertical .q-stepper__dot {
        background: #2563eb !important;
      }
      .q-stepper--vertical .q-stepper__tab--done .q-stepper__dot {
        background: #059669 !important;
      }

      /* markdown 预览区 */
      .msr-markdown-preview {
        background: #f8fafc;
        border-radius: 0.5rem;
        padding: 1rem;
        border: 1px solid #e2e8f0;
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
                ui.button(
                    label,
                    icon=icon,
                    on_click=lambda p=path: ui.navigate.to(p),
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
