# MSR-gui：基于 NiceGUI 的可视化管理界面技术方案

## 架构总览

```
MSR-v2/
├── MSR-cli/              # 现有 CLI 核心（作为 Python 包被引用）
│   └── msr_sync/         # 核心业务逻辑
├── MSR-gui/              # 新建 GUI 项目
│   ├── msr_gui/
│   │   ├── __init__.py
│   │   ├── main.py           # 入口：NiceGUI app 启动
│   │   ├── state.py          # 全局状态管理（响应式）
│   │   ├── pages/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py  # 仪表盘/首页
│   │   │   ├── browse.py     # 配置浏览与搜索
│   │   │   ├── import_page.py# 导入向导
│   │   │   ├── sync.py       # 同步面板
│   │   │   └── settings.py   # 全局配置编辑
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── sidebar.py    # 左侧导航栏
│   │   │   ├── config_tree.py# 配置树形组件
│   │   │   ├── version_timeline.py # 版本时间线
│   │   │   ├── ide_selector.py     # IDE 多选器
│   │   │   ├── log_viewer.py       # 操作日志输出
│   │   │   └── rule_editor.py      # Rule 内容查看器
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── repo_service.py     # 封装 Repository API
│   │       ├── sync_service.py     # 封装 sync 逻辑（异步）
│   │       └── import_service.py   # 封装 import 逻辑（异步）
│   ├── pyproject.toml
│   └── README.md
```

## 核心设计决策

### 1. 与 MSR-cli 的集成方式

**直接 Python import（非子进程调用）**：MSR-gui 将 MSR-cli 作为 Python 依赖包，直接 import 核心模块：

```python
# msr_gui/services/repo_service.py
from msr_sync.core.repository import Repository
from msr_sync.core.config import get_config, GlobalConfig
from msr_sync.adapters.registry import get_all_adapters, get_adapter
```

pyproject.toml 中通过本地路径依赖引用：

```toml
[project]
name = "msr-gui"
version = "0.1.0"
dependencies = [
    "nicegui>=2.0",
    "msr-sync",  # 从 PyPI 安装，或开发模式用本地路径
]

[project.scripts]
msr-gui = "msr_gui.main:run"
```

### 2. 服务层封装

在 `services/` 下封装一层薄服务，解决两个问题：
- **异步化**：NiceGUI 的 UI 线程不能被阻塞，文件 I/O 操作需要用 `run.io_bound()` 包装
- **数据转换**：将 Repository 返回的原始数据转为 GUI 友好的结构

```python
# msr_gui/services/repo_service.py
from nicegui import run
from msr_sync.core.repository import Repository

class RepoService:
    def __init__(self):
        self.repo = Repository()

    async def list_configs(self, config_type=None):
        """异步获取配置列表"""
        return await run.io_bound(self.repo.list_configs, config_type)

    async def get_repo_status(self):
        """获取仓库状态概览"""
        exists = await run.io_bound(self.repo.exists)
        configs = await run.io_bound(self.repo.list_configs) if exists else {}
        return {
            "path": str(self.repo.base_path),
            "exists": exists,
            "breakdown": {t: sum(len(v) for v in items.values()) for t, items in configs.items()}
        }
```

### 3. 状态管理

使用 NiceGUI 的 `app.storage` + 响应式变量管理全局状态：

```python
# msr_gui/state.py
from nicegui import app

class AppState:
    def __init__(self):
        self.repo_status = {}        # 仓库状态
        self.config_list = {}        # 配置列表缓存
        self.selected_ide = []       # 当前选中的 IDE
        self.operation_logs = []     # 操作日志
```

## 页面功能设计

### 页面 1：仪表盘（Dashboard）

**路由**：`/`

**展示内容**：
- 仓库状态卡片（路径、是否初始化、配置数量统计）
- 三个数字卡片：Rules 数 / Skills 数 / MCP 数
- 已支持的 IDE 列表（7 个图标 + 名称）
- 快捷操作按钮：初始化仓库、导入配置、快速同步

**调用 API**：
- `Repository.exists()` / `Repository.list_configs()` → 统计数据
- `get_all_adapters()` → IDE 列表

### 页面 2：配置浏览（Browse）

**路由**：`/browse`

**展示内容**：
- 左侧：三列 Tab（Rules / Skills / MCP），每列下显示配置名称列表
- 右侧：选中配置后展示详情
  - 版本时间线（V1 → V2 → V3）
  - Rule 类型：Markdown 内容预览（用 `ui.markdown()`）
  - Skill/MCP 类型：文件树展示
- 操作按钮：删除版本、同步到 IDE

**调用 API**：
- `Repository.list_configs()` → 左侧树
- `Repository.read_rule_content(name, version)` → Rule 内容
- `Repository.get_config_path()` → 文件路径
- `Repository.remove_config()` → 删除操作

### 页面 3：导入向导（Import）

**路由**：`/import`

**三步向导流程**：

1. **选择来源**：
   - 配置类型选择（Rules / Skills / MCP）
   - 来源输入：文件选择器（`ui.upload`）/ 目录路径输入 / URL 输入
2. **预览确认**：
   - 调用 `SourceResolver.resolve()` 解析来源
   - 表格展示将导入的配置项（名称、类型、来源类型）
   - 勾选需要导入的项目
3. **执行导入**：
   - 逐一调用 `Repository.store_rule/skill/mcp()`
   - 实时显示进度和结果日志

### 页面 4：同步面板（Sync）

**路由**：`/sync`

**布局**：
- **左区 - 配置选择**：
  - 配置类型 Tab（Rules / Skills / MCP / 全部）
  - 配置名称多选列表
  - 版本选择（默认最新）
- **中区 - IDE 选择**：
  - IDE 卡片网格（7 个），可多选
  - 每个卡片显示 IDE 名称 + 是否支持全局 Rules 的标记
  - "全选" 按钮
- **右区 - 同步选项**：
  - Scope 选择：Global / Project
  - Project 目录选择（scope=project 时出现）
  - 同步预览：列出将执行的操作（N 条 rules → IDE X, Y）
  - "执行同步" 按钮
- **底部 - 日志区**：实时输出同步日志

**调用 API**：
- `Repository.list_configs()` → 配置列表
- `get_all_adapters()` → IDE 列表
- `adapter.supports_global_rules()` → 标记
- `sync_handler()` 或直接调用 `_sync_rule/_sync_skill/_sync_mcp` → 执行同步

### 页面 5：设置（Settings）

**路由**：`/settings`

**展示内容**：
- 全局配置编辑（repo_path、default_ides、default_scope、ignore_patterns）
- 仓库路径修改
- 仓库初始化/重置（含 --merge 选项）
- 主题切换（亮色/暗色）

**调用 API**：
- `get_config()` → 读取当前配置
- `generate_default_config()` → 重置配置
- `Repository.init()` → 初始化仓库

## 技术要点

### 1. NiceGUI 启动配置

```python
# msr_gui/main.py
from nicegui import ui, app

def run():
    # 注册所有页面路由
    from msr_gui.pages import dashboard, browse, import_page, sync, settings

    ui.run(
        title="MSR Sync Manager",
        port=8765,
        native=True,       # 原生窗口模式（pywebview）
        window_size=(1280, 800),
        reload=False,       # 生产模式关闭热重载
        dark=None,          # 跟随系统主题
    )

if __name__ == "__main__":
    run()
```

### 2. 异步 I/O 处理

NiceGUI 基于 asyncio，文件操作需要异步化避免阻塞 UI：

```python
from nicegui import run

async def on_sync_click():
    ui.notify("同步中...", type="info")
    result = await run.io_bound(sync_handler, ide=selected_ides, scope=scope, ...)
    ui.notify(f"同步完成：{result}", type="positive")
```

### 3. 跨平台打包

使用 PyInstaller 打包为单文件可执行程序：

```bash
# macOS
pyinstaller --onefile --windowed --name "MSR-Sync" msr_gui/main.py

# Windows
pyinstaller --onefile --windowed --name "MSR-Sync" --icon=icon.ico msr_gui/main.py
```

或使用 NiceGUI 官方推荐的打包方式（基于 PyInstaller 的封装）。

### 4. 原生窗口 vs 浏览器模式

NiceGUI 支持两种运行模式，通过参数切换：
- `native=True`：使用 pywebview 打开原生窗口，体验更好（需安装 pywebview）
- `native=False`：自动打开浏览器访问 localhost，兼容性更好

建议默认使用 native 模式，同时提供 `--browser` 参数回退到浏览器模式。

## 实施任务分解

### Task 1：项目脚手架搭建
- 在 `MSR-gui/` 下创建项目结构、pyproject.toml、依赖配置
- 配置 MSR-cli 作为本地开发依赖
- 实现 `main.py` 入口和基础布局框架（侧边栏 + 内容区）

### Task 2：服务层封装
- 实现 `repo_service.py`、`sync_service.py`、`import_service.py`
- 封装所有核心 API 的异步调用
- 实现 `state.py` 全局状态管理

### Task 3：仪表盘页面
- 仓库状态卡片、配置统计、IDE 列表
- 快捷操作按钮

### Task 4：配置浏览页面
- 配置树形列表、版本时间线
- Rule 内容预览、删除操作

### Task 5：导入向导页面
- 三步向导 UI、文件上传/路径输入
- 来源解析预览、批量导入执行

### Task 6：同步面板页面
- IDE 多选网格、配置选择、scope 选择
- 同步预览、执行同步、实时日志

### Task 7：设置页面
- 全局配置编辑、仓库管理
- 主题切换

### Task 8：打包与分发
- PyInstaller 打包脚本（macOS + Windows）
- 测试原生窗口和浏览器两种模式
