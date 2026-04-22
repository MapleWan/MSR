# 告别 AI IDE 配置碎片化：用 MSR-cli 打造你的本地 MCP / Rules / Skills 统一仓库

> 你是否在不同 AI IDE 之间反复拷贝同一份 Rule？是否想把自己精心调试的 MCP 配置集中管理、按需分发？MSR-cli 就是为此而生 —— 它首先是你本地的 **AI 配置仓库管理工具**，其次才是跨 IDE 一键同步的桥梁。

## 先聊聊一个被忽视的问题

作为经常在 Trae、Qoder、Lingma、CodeBuddy 之间切换的开发者，你可能已经积累了：

- 十几条精心编写的 **Rules**（代码规范、架构约束、Git 提交规范...）
- 几个好用的 **Skills**（Code Review、文档生成、性能优化...）
- 若干 **MCP 工具配置**（Word 文档读取、Web 搜索、数据库查询...）

但这些配置散落在各个 IDE 的不同目录下：

```
# Trae 的配置在这里
.trae/rules/coding-standards.md
~/.trae-cn/skills/review-skill/

# Qoder 的配置在这里
.qoder/rules/coding-standards.md
~/.qoder/skills/review-skill/

# CodeBuddy 又在另一个路径
.codebuddy/rules/coding-standards.md
~/.codebuddy/rules/coding-standards.md    # CodeBuddy 还支持全局级
```

**更关键的是**：每个 IDE 的格式要求还不一样：

| IDE | Rules frontmatter 格式 | 说明 |
|-----|----------------------|------|
| Trae | 无头部 | 直接是纯 Markdown |
| Qoder | `trigger: always_on` | YAML 格式包裹 |
| Lingma | `trigger: always_on` | 与 Qoder 相同 |
| CodeBuddy | 5 个字段（含时间戳） | 最复杂，每次同步动态生成 |

同一条 Rule，在 4 个 IDE 里需要 4 种不同的格式。手动维护？不存在的。

## MSR-cli：你的本地 AI 配置仓库

MSR-cli（命令名 `msr-sync`）的核心思路很简单：

> **建一个统一的本地仓库（`~/.msr-repos`），把所有 Rules、Skills、MCP 配置集中管理，然后按需同步到任意 IDE。**

```
~/.msr-repos/                    # 你的 AI 配置中心
├── RULES/                       # 所有规则集中存放
│   ├── coding-standards/
│   │   ├── V1/coding-standards.md
│   │   └── V2/coding-standards.md
│   ├── git-commit-convention/
│   │   └── V1/git-commit-convention.md
│   └── code-review/
│       └── V1/code-review.md
├── SKILLS/                      # 所有技能集中存放
│   ├── review-skill/
│   │   └── V1/SKILL.md
│   └── doc-generator/
│       └── V1/SKILL.md
└── MCP/                         # 所有 MCP 配置集中存放
    ├── word-reader/
    │   └── V1/mcp.json
    └── web-search/
        └── V1/mcp.json
```

这个仓库就是你的 **Single Source of Truth**。所有配置的增删改查都在这里完成，IDE 端只是"分发目标"。

### 装备与安装

```bash
# Python 3.9+ 即可
pip install msr-sync
```

也支持从源码安装：

```bash
git clone https://github.com/MapleWan/MSR.git
cd MSR-v2/MSR-cli
pip install -e .
```

## 五分钟上手：从 0 到统一管理

### 第一步：初始化仓库

```bash
msr-sync init
# ✅ 统一仓库已创建: /Users/username/.msr-repos
# ✅ 已生成默认配置文件: /Users/username/.msr-sync/config.yaml
```

如果你已经在某些 IDE 中有配置了，加个 `--merge` 一键收入囊中：

```bash
msr-sync init --merge
# ✅ 统一仓库已创建: /Users/username/.msr-repos
#
# 🔍 正在扫描已有 IDE 配置...
#
# 📊 合并摘要（共导入 5 项配置）:
#   rules: trae: 2 项, codebuddy: 1 项
#   skills: qoder: 1 项
#   mcp: lingma: 1 项
```

它会自动扫描 Trae、Qoder、Lingma、CodeBuddy 四个 IDE 的用户级目录，把你已有的配置全部导入统一仓库。

### 第二步：导入你的配置

支持 **文件、目录、压缩包、URL** 四种导入方式：

```bash
# 导入单条 Rule
msr-sync import rules ./coding-standards.md
# ✅ 已导入: coding-standards (V1)

# 导入一个 Skill（含 SKILL.md 的目录）
msr-sync import skills ./review-skill/
# ✅ 已导入: review-skill (V1)

# 导入 MCP 配置
msr-sync import mcp ./word-reader/
# ✅ 已导入: word-reader (V1)

# 从 GitHub 仓库的压缩包批量导入
msr-sync import rules https://github.com/example/ai-rules/archive/refs/heads/main.zip
```

同名配置重复导入时，**自动创建新版本**：

```bash
# 再次导入同名 Rule
msr-sync import rules ./coding-standards-v2.md
# ✅ 已导入: coding-standards (V2)
```

### 第三步：一键同步到所有 IDE

```bash
# 全量同步到所有 IDE（全局级）
msr-sync sync
# ✅ 已同步 rule 'coding-standards' (V2) 到 trae (global)
# ✅ 已同步 rule 'coding-standards' (V2) 到 qoder (global)
# ✅ 已同步 rule 'coding-standards' (V2) 到 lingma (global)
# ✅ 已同步 rule 'coding-standards' (V2) 到 codebuddy (global)
# ...
```

也可以精确控制同步范围：

```bash
# 只同步 Rules 到 Trae
msr-sync sync --type rules --ide trae

# 项目级同步（同步到当前项目的 .trae/rules/ 等目录）
msr-sync sync --scope project

# 同步指定版本
msr-sync sync --type rules --name coding-standards --version V1
```

就这么简单。你的配置仓库和各 IDE 之间，只剩一条命令的距离。

## 查看与版本管理

### 查看仓库全貌

```bash
msr-sync list
# 📦 统一仓库配置列表
# ├── rules
# │   ├── coding-standards [V1, V2]
# │   └── code-review [V1]
# ├── skills
# │   └── review-skill [V1]
# └── mcp
#     └── word-reader [V1, V2, V3]
```

### 版本管理

每次导入同名配置都会自动递增版本（V1 -> V2 -> V3...），同步时默认使用最新版本，也可以指定历史版本：

```bash
# 同步最新版本（默认行为）
msr-sync sync --type rules --name coding-standards
# ✅ 已同步 rule 'coding-standards' (V2) 到 qoder (global)

# 回滚到旧版本
msr-sync sync --type rules --name coding-standards --version V1
# ✅ 已同步 rule 'coding-standards' (V1) 到 qoder (global)
```

不再需要的版本可以随时清理：

```bash
msr-sync remove rules coding-standards V1
# ✅ 已删除配置: rules/coding-standards/V1
```

## 同步时发生了什么？—— 格式自动转换

这是 MSR-cli 最核心的能力。当你执行 `msr-sync sync` 时，工具会针对每个目标 IDE 做不同的处理。

### Rules 的格式转换

以同一条 `coding-standards` Rule 为例，同步到不同 IDE 后的文件内容：

**Trae** — 直接写入纯 Markdown，无任何头部：

```markdown
# 编码规范

## 命名规则
- 类名使用 PascalCase
- 函数名使用 camelCase
...
```

**Qoder / Lingma** — 自动添加 `trigger: always_on` 头部：

```markdown
---
trigger: always_on
---
# 编码规范

## 命名规则
- 类名使用 PascalCase
- 函数名使用 camelCase
...
```

**CodeBuddy** — 自动添加包含时间戳的完整头部：

```markdown
---
description:
alwaysApply: true
enabled: true
updatedAt: 2026-04-21T08:38:00.123456+00:00
provider:
---
# 编码规范

## 命名规则
- 类名使用 PascalCase
- 函数名使用 camelCase
...
```

你在统一仓库中只维护一份纯 Markdown，格式转换由工具自动完成。

### MCP 的智能合并

MCP 同步采用 **JSON 合并策略**，而不是简单覆盖：

- 目标 `mcp.json` 不存在 → 自动新建
- 无同名 server → 追加到 `mcpServers` 字段
- 有同名 server → 提示确认是否覆盖

同时，工具会自动重写 MCP server 配置中的 `cwd` 字段，指向统一仓库中该配置版本的路径，确保 MCP 服务能在正确目录下启动。

### Skills 的目录拷贝

Skills 同步是直接的目录拷贝（`shutil.copytree`），不涉及格式转换。如果目标已存在同名 skill，会提示确认覆盖。

## 全局配置：按你的习惯来

`~/.msr-sync/config.yaml` 让你自定义默认行为：

```yaml
# 统一仓库路径（支持 ~ 展开，默认 ~/.msr-repos）
# repo_path: ~/.msr-repos

# 导入时忽略的目录和文件
ignore_patterns:
  - __MACOSX
  - .DS_Store
  - __pycache__
  - .git

# 默认同步目标 IDE（不用每次都 --ide）
default_ides:
  - trae
  - codebuddy

# 默认同步层级
default_scope: global
```

设置后，`msr-sync sync` 就等同于 `msr-sync sync --ide trae --ide codebuddy`，省心省力。

## 架构设计：适配器模式驱动扩展

对于感兴趣的同学，简单介绍一下 MSR-cli 的技术架构。

整体采用 **四层分层架构**：

```
CLI 层 (cli.py)
  ↓ Click 命令路由
Commands 层 (commands/)
  ↓ 业务编排
Core 层 (core/)
  ↓ 纯业务逻辑
Adapters 层 (adapters/)
  ↓ IDE 特定实现
各 IDE 文件系统
```

关键的 **适配器层** 使用策略模式 + 注册表模式实现：

```python
# 抽象基类
class BaseAdapter(ABC):
    def format_rule_content(self, raw_content: str) -> str: ...
    def get_rules_path(self, rule_name, scope, project_dir) -> Path: ...
    def supports_global_rules(self) -> bool: ...

# 每个IDE一个适配器实现
class TraeAdapter(BaseAdapter): ...
class QoderAdapter(BaseAdapter): ...
class LingmaAdapter(BaseAdapter): ...
class CodeBuddyAdapter(BaseAdapter): ...
```

新增一个 IDE 的支持，只需要：
1. 新建一个适配器文件，继承 `BaseAdapter`
2. 在注册表中注册
3. 实现路径解析和格式转换逻辑

核心业务层完全不感知具体 IDE 的存在。

**其他技术亮点：**

- **版本管理**：拒绝前导零（`V01` 非法）、负数、空字符串等边界情况
- **临时文件管理**：`SourceResolver` 统一管理临时目录，`finally` 确保清理
- **幂等操作**：`init` 重复执行不会破坏已有数据
- **平台检测**：自动适配 macOS（`~/Library/Application Support/`）和 Windows（`%APPDATA%/`）路径差异
- **异常体系**：8 个层级分明的异常类，中文错误信息友好

## 实战场景

### 场景一：团队共享配置

团队维护一个 GitHub 仓库，放一个打包好的压缩包：

```bash
# 成员拉取最新团队配置
msr-sync import rules https://internal.example.com/team-rules.zip

# 一键同步到自己的所有 IDE
msr-sync sync
```

### 场景二：从 Trae 切换到 CodeBuddy

```bash
# 一键收集 Trae 的所有配置
msr-sync init --merge

# 全部分发到 CodeBuddy
msr-sync sync --ide codebuddy
```

### 场景三：配置实验与回滚

```bash
# 导入实验版本的 Rule
msr-sync import rules ./coding-standards-experimental.md
# ✅ 已导入: coding-standards (V2)

# 同步到 IDE 试用
msr-sync sync --type rules --name coding-standards
# ✅ 已同步 rule 'coding-standards' (V2) 到 trae (global)

# 不好用？回滚到 V1
msr-sync sync --type rules --name coding-standards --version V1
# ✅ 已同步 rule 'coding-standards' (V1) 到 trae (global)
```

### 场景四：项目级配置统一

给团队的每个项目统一注入 Rules 和 Skills：

```bash
# 在项目根目录执行
msr-sync sync --type rules --scope project
msr-sync sync --type skills --scope project
```

配置会自动写入 `.trae/rules/`、`.qoder/rules/`、`.codebuddy/rules/` 等目录，团队成员各自用各自的 IDE 打开项目就能直接生效。

## 支持的 IDE 和平台

| IDE | 厂商 | Rules | Skills | MCP |
|-----|------|-------|--------|-----|
| Trae | 字节跳动 | ✅ | ✅ | ✅ |
| Qoder | 阿里巴巴 | ✅ | ✅ | ✅ |
| Lingma | 阿里巴巴 | ✅ | ✅ | ✅ |
| CodeBuddy | 腾讯 | ✅ | ✅ | ✅ |

- **macOS** / **Windows** 双平台支持，自动检测操作系统并使用对应路径规范
- Python 3.9+ 环境，仅依赖 `click` 和 `pyyaml`，轻量无负担

## 最后

MSR-cli 解决的不是一个复杂的技术问题，而是一个**真实存在的日常痛点**。

随着 AI IDE 越来越多，Rules、Skills、MCP 配置的碎片化只会越来越严重。把配置集中到一个本地仓库统一管理，按需同步到任意 IDE —— 这不仅省去了大量的重复劳动，更重要的是让你对所有的 AI 配置有了**清晰的掌控感**。

一条命令，配置归仓。

> **项目地址：** [https://github.com/MapleWan/MSR](https://github.com/MapleWan/MSR/tree/main)
>
> **安装：** `pip install msr-sync`
