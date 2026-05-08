# 给 AI IDE 配置管理加个 GUI：MSR-GUI 可视化管理界面

> 命令行够用，但图形界面更直觉。MSR-GUI 让你用鼠标点点就能完成 Rules/Skills/MCP 的浏览、导入和同步 —— 同时保留 CLI 的全部能力。

## 为什么需要 GUI？

如果你已经在用 [MSR-cli](https://pypi.org/project/msr-sync/)（`msr-sync`）统一管理 AI IDE 配置，你可能体验过这样的日常：

```bash
# 看看仓库里有什么
msr-sync list

# 导入一条新 Rule
msr-sync import rules ./new-rule.md

# 同步到所有 IDE
msr-sync sync
```

三条命令搞定一切。但当你的仓库越来越大 —— 十几条 Rules、五六个 Skills、若干 MCP 配置，每个还有多个版本 —— 光看 `list` 输出的树形结构就需要费点眼神了。

**MSR-GUI** 就是给这个场景加一层可视化外衣：

- 仪表盘一眼看完仓库全貌
- 配置浏览支持点击查看内容和版本历史
- 导入向导引导你完成文件/URL/上传三种导入方式
- 同步面板精确控制同步目标和范围
- 实时日志让你知道每一步在做什么

## 安装

```bash
pip install msr-gui
```

就这么简单。`msr-gui` 依赖 `msr-sync`（CLI 核心）和 `nicegui`（UI 框架），会自动安装。

## 三种启动方式

```bash
# 默认：打开原生桌面窗口
msr-gui

# 浏览器模式：在默认浏览器中打开
msr-gui --browser

# 指定端口
msr-gui --port 9090
```

原生窗口模式使用 pywebview，看起来就像一个独立桌面应用；浏览器模式适合远程访问或不想装额外依赖的场景。

## 五大功能页面

### 1. 仪表盘 — 一眼掌控全局

打开应用首先看到的是仪表盘。三张统计卡片分别显示 Rules、Skills、MCP 的数量，下方展示各 IDE 的连接状态（配置路径是否存在）。

每个 IDE 都有对应的官方图标（Trae、Qoder、Lingma、CodeBuddy、Cursor、Kiro、Antigravity），一目了然。

### 2. 配置浏览 — 翻阅你的配置库

左侧是分类树（Rules / Skills / MCP），右侧是配置详情。点击任意配置项：

- 查看所有版本（V1、V2、V3...）
- 预览 Markdown 内容
- 查看文件路径和元信息

版本切换即点即看，比 `cat ~/.msr-repos/RULES/coding-standards/V2/coding-standards.md` 友好多了。

### 3. 导入向导 — 三步完成导入

导入页面提供三个 Tab：

| Tab | 适用场景 |
|-----|---------|
| 本地路径 | 输入文件/目录路径直接导入 |
| URL 下载 | 粘贴 GitHub 压缩包链接 |
| 文件上传 | 拖拽 .md / .zip / .tar.gz 文件 |

选择配置类型（Rules / Skills / MCP）→ 选择来源 → 点击导入。导入过程实时显示日志，成功后自动刷新仓库视图。

### 4. 同步面板 — 精确控制分发

同步页面让你可视化选择：

- **目标 IDE**：勾选要同步到的 IDE（支持全选）
- **同步层级**：全局级 / 项目级
- **配置范围**：全部 / 仅 Rules / 仅 Skills / 仅 MCP
- **指定版本**：选择特定版本同步

点击"开始同步"，下方日志区实时滚动显示每一条同步结果：

```
✅ 已同步 rule 'coding-standards' (V2) 到 trae (global)
✅ 已同步 rule 'coding-standards' (V2) 到 qoder (global)
✅ 已同步 skill 'review-skill' (V1) 到 codebuddy (global)
⚠️ trae 不支持全局级 rules，已跳过
```

### 5. 设置 — 管理全局配置

设置页面对应 `~/.msr-sync/config.yaml` 的可视化编辑：

- 统一仓库路径
- 默认同步目标 IDE
- 默认同步层级
- 忽略模式列表

修改即时保存，无需重启。

## 视觉设计：莫兰迪色系

MSR-GUI 采用**莫兰迪色系**（Morandi palette）—— 低饱和度、加入灰调的柔和配色：

| 用途 | 色值 | 风格 |
|------|------|------|
| 主色 | `#5B7185` | 深莫兰迪蓝 |
| 辅色 | `#5E8A76` | 深莫兰迪绿 |
| 强调 | `#7D6B80` | 深莫兰迪紫 |
| 页面背景 | `#F0EDEA` | 暖灰白 |
| 侧边栏 | `#5A6872` | 莫兰迪深灰蓝 |

整体视觉宁静优雅，长时间使用不累眼。配合微交互动效（卡片悬浮上浮、按钮平滑过渡），让工具类应用也能有"质感"。

## 技术栈

- **UI 框架**：[NiceGUI](https://nicegui.io/) 3.x —— Python 原生 Web UI 框架，基于 Quasar/Vue
- **原生窗口**：pywebview —— 跨平台桌面窗口包装
- **核心引擎**：msr-sync —— MSR-cli 的全部业务逻辑
- **打包发布**：PyPI —— `pip install msr-gui` 即装即用

架构上，GUI 是 CLI 的"薄前端"—— 所有业务逻辑（导入、同步、版本管理）复用 msr-sync 的 Python API，GUI 只负责交互和展示。

## 配合 MSR-cli Skill 使用：让 AI 帮你管配置

如果你在 Qoder、Trae 等 IDE 中使用 AI 编程助手，还可以给它装一个 **msr-sync-usage Skill**，让 AI 直接帮你执行配置管理操作。

### 什么是 msr-sync-usage Skill？

在[MSR仓库](https://github.com/MapleWan/MSR/tree/main)中可以下载

这是一个 Markdown 格式的 Skill 文件，教会 AI 助手如何使用 `msr-sync` 命令。安装后，你可以直接用自然语言指挥 AI：

> "帮我把这个 Rule 导入到统一仓库"
>
> "同步所有配置到 Trae 和 CodeBuddy"
>
> "查看仓库里有哪些 MCP 配置"

AI 会自动调用正确的 `msr-sync` 命令完成操作。

### Skill 核心内容

这个 Skill 涵盖了 MSR-cli 的完整使用知识：

**命令速查：**

```bash
# 初始化
msr-sync init [--merge]

# 导入（支持文件/目录/压缩包/URL）
msr-sync import <rules|skills|mcp> <source>

# 同步（精确控制目标和范围）
msr-sync sync [--ide IDE] [--scope global|project] [--type TYPE] [--name NAME] [--version VERSION]

# 查看
msr-sync list [--type TYPE]

# 删除
msr-sync remove <type> <name> <version>
```

**IDE 路径映射：**

| IDE | Rules (项目级) | MCP 配置路径 |
|-----|---------------|-------------|
| Trae | `.trae/rules/` | `~/Library/.../Trae CN/User/mcp.json` |
| Qoder | `.qoder/rules/` | `~/Library/.../Qoder/.../mcp.json` |
| CodeBuddy | `.codebuddy/rules/` | `~/.codebuddy/mcp.json` |
| Cursor | `.cursor/rules/` | `~/.cursor/mcp.json` |
| Kiro | `.kiro/steering/` | `~/.kiro/mcp.json` |
| Antigravity | `.agents/rules/` | `~/.gemini/.../mcp_config.json` |

**Frontmatter 自动转换规则：**

同步 Rule 时，工具自动根据目标 IDE 添加正确的头部格式：
- Qoder/Lingma → `trigger: always_on`
- CodeBuddy/Cursor → 完整 5 字段头部（含时间戳）
- Trae/Kiro/Antigravity → 纯 Markdown，无头部

**版本管理：**

- 导入同名配置自动递增版本（V1 → V2 → V3）
- 同步默认使用最新版本
- 支持指定历史版本同步（回滚）

### 如何安装这个 Skill

将 Skill 文件放到对应 IDE 的 skills 目录即可：

```bash
# 用 msr-sync 自己来管理（meta！）
msr-sync import skills ./msr-sync-usage/
msr-sync sync --type skills
```

或者手动拷贝到：
- Qoder：`~/.qoder/skills/msr-sync-usage/`
- Trae：`~/.trae-cn/skills/msr-sync-usage/`

安装后，AI 助手就能理解 MSR-cli 的全部命令语法和使用场景。

## CLI vs GUI：各取所需

| 场景 | 推荐 | 原因 |
|------|------|------|
| 脚本自动化 | CLI | 命令行天然适合脚本和 CI |
| 快速单次操作 | CLI | 三个字母比打开窗口快 |
| 日常管理和浏览 | GUI | 可视化浏览比记命令轻松 |
| 给不熟悉命令行的同事用 | GUI | 零学习成本 |
| 让 AI 助手代劳 | Skill | 自然语言驱动，最省心 |

三者并行不冲突 —— CLI 是引擎，GUI 是方向盘，Skill 是自动驾驶。

## 支持的 IDE

| IDE | 厂商 | Rules | Skills | MCP |
|-----|------|-------|--------|-----|
| Trae | 字节跳动 | ✅ | ✅ | ✅ |
| Qoder | 阿里巴巴 | ✅ | ✅ | ✅ |
| Lingma | 阿里巴巴 | ✅ | ✅ | ✅ |
| CodeBuddy | 腾讯 | ✅ | ✅ | ✅ |
| Cursor | Cursor Inc. | ✅ | ✅ | ✅ |
| Kiro | AWS | ✅ | ✅ | ✅ |
| Antigravity | Google | ✅ | ✅ | ✅ |

macOS / Windows 双平台支持。

## 总结

MSR-GUI 不是要替代 CLI，而是给它加了一个更友好的入口。

对于习惯命令行的人，CLI 依然是最高效的选择；对于更喜欢图形界面的人，GUI 提供了零记忆成本的操作体验；对于想偷懒的人，装个 Skill 让 AI 代劳就好。

**三种方式，同一个配置仓库，同一套管理逻辑。**

> **安装 GUI：** `pip install msr-gui`
>
> **安装 CLI：** `pip install msr-sync`
>
> **项目地址：** [https://github.com/MapleWan/MSR](https://github.com/MapleWan/MSR/tree/main)
