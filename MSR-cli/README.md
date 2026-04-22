# MSR-cli (`msr-sync`)

统一管理多款国内 AI IDE 的 rules、skills、MCP 配置的轻量化命令行工具。

## 为什么需要 MSR-cli？

随着国内 AI IDE 生态的快速发展，开发者往往需要在多款 AI IDE（如 Trae、Qoder、Lingma、CodeBuddy）之间切换使用。然而，这些 IDE 的配置体系存在以下痛点：

- **配置相互隔离**：每个 IDE 都有独立的 rules、skills、MCP 配置目录，互不相通。在一个 IDE 中精心调试好的配置，无法直接用于另一个 IDE。
- **跨 IDE 迁移成本高**：不同 IDE 的配置路径、文件格式、frontmatter 规范各不相同，手动迁移需要逐一理解每个 IDE 的约定，极易出错。
- **配置格式不统一**：Trae 不需要 frontmatter 头部、Qoder/Lingma 需要 `trigger: always_on`、CodeBuddy 需要 `alwaysApply` + `updatedAt` 时间戳——同样的规则内容，需要为每个 IDE 生成不同格式。
- **版本管理缺失**：IDE 本身不提供配置版本管理能力，更新配置后无法回滚到历史版本。
- **团队协作困难**：团队成员之间难以共享统一的基础配置，每人各自维护一套，容易产生不一致。

MSR-cli 正是为了解决这些问题而生——通过建立统一的本地仓库作为配置的"Single Source of Truth"，一次导入、多端同步，自动处理各 IDE 的格式差异，并提供版本管理能力。

## 简介

MSR-cli 是一个基于 Python 开发的命令行工具，命令名为 `msr-sync`，旨在解决国内主流 AI IDE 之间配置相互独立、跨 IDE 迁移需手动复制、配置格式与路径不统一等核心痛点。

通过建立统一的本地仓库（默认 `~/.msr-repos`），MSR-cli 提供配置的导入、同步、查看、删除等完整生命周期管理能力，让你在多款 AI IDE 之间轻松共享和迁移配置。工具支持全局配置文件，可自定义仓库路径、忽略模式、默认 IDE 和同步层级。

### 导入时支持的格式

`msr-sync import` 命令支持多种来源格式，不同配置类型的格式要求如下：

#### Rules（规则）

| 来源格式 | 说明 | 示例 |
|---------|------|------|
| 单个 `.md` 文件 | 导入为一条 rule，名称取文件名（去除扩展名） | `msr-sync import rules ./my-rule.md` |
| 包含 `.md` 文件的目录 | 扫描目录下所有 `.md` 文件，每个文件作为一条 rule | `msr-sync import rules ./rules-dir/` |
| 压缩包（`.zip` / `.tar.gz` / `.tgz`） | 自动解压后按目录规则扫描 | `msr-sync import rules ./rules-pack.zip` |
| URL | 下载远程压缩包后按压缩包规则处理 | `msr-sync import rules https://example.com/rules.zip` |

#### Skills（技能）

| 来源格式 | 说明 | 示例 |
|---------|------|------|
| 含 `SKILL.md` 的目录 | 视为单个 skill，名称取目录名 | `msr-sync import skills ./my-skill/` |
| 包含多个子目录的目录 | 每个子目录视为一个独立 skill（需各含 `SKILL.md`） | `msr-sync import skills ./skills-pack/` |
| 压缩包（`.zip` / `.tar.gz` / `.tgz`） | 自动解压后按目录规则扫描 | `msr-sync import skills ./skills-pack.zip` |
| URL | 下载远程压缩包后按压缩包规则处理 | `msr-sync import skills https://example.com/skills.zip` |

> **Skill 识别规则：** 目录根目录存在 `SKILL.md` 文件时，视为单个 skill；否则将每个子目录视为独立 skill。

#### MCP（Model Context Protocol）

| 来源格式 | 说明 | 示例 |
|---------|------|------|
| 含 `mcp.json` 的目录 | 根目录含非子目录文件时，视为单个 MCP 配置，**同步时必须包含 `mcp.json`** | `msr-sync import mcp ./my-mcp/` |
| 包含多个子目录的目录 | 每个子目录视为一个独立 MCP 配置（需各含 `mcp.json`） | `msr-sync import mcp ./mcp-pack/` |
| 压缩包（`.zip` / `.tar.gz` / `.tgz`） | 自动解压后按目录规则扫描 | `msr-sync import mcp ./mcp-pack.zip` |
| URL | 下载远程压缩包后按压缩包规则处理 | `msr-sync import mcp https://example.com/mcp.zip` |

> **MCP 识别规则：** 目录根目录存在非子目录文件时，视为单个 MCP；否则将每个子目录视为独立 MCP 配置。
>
> **⚠️ 重要：** 同步 MCP 配置时，工具会查找目录下的 `mcp.json` 文件。如果该文件不存在，同步将被跳过并输出警告。

##### `mcp.json` 文件格式

`mcp.json` 采用标准 JSON 格式，顶层必须包含 `mcpServers` 字段，每个 server 条目定义一个 MCP 工具服务：

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "<启动命令>",
      "args": ["<参数1>", "<参数2>"],
      "cwd": "<工作目录（可选，同步时会自动重写为仓库路径）>",
      "env": {
        "<环境变量名>": "<值>"
      }
    }
  }
}
```

**字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `mcpServers` | ✅ | 顶层字段，包含所有 MCP server 定义 |
| `mcpServers.<name>.command` | ✅ | 启动 MCP 服务的命令（如 `python`、`node`、`npx`） |
| `mcpServers.<name>.args` | ✅ | 命令参数列表 |
| `mcpServers.<name>.cwd` | ❌ | 工作目录，同步时会自动重写为统一仓库中对应版本的路径 |
| `mcpServers.<name>.env` | ❌ | 环境变量字典 |

**完整示例：**

```json
{
  "mcpServers": {
    "word-reader": {
      "command": "python",
      "args": ["server.py"],
      "cwd": ".",
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    },
    "web-search": {
      "command": "npx",
      "args": ["-y", "@anthropic/web-search-mcp"]
    }
  }
}
```

> **cwd 重写机制：** 同步时，如果 server 配置中包含 `cwd` 字段，工具会自动将其替换为统一仓库中该配置版本的绝对路径（如 `~/.msr-repos/MCP/my-mcp/V1`），确保 MCP 服务能在正确的目录下启动。

#### 通用说明

- **压缩包格式：** 支持 `.zip`、`.tar.gz`、`.tgz` 三种格式
- **URL 导入：** 仅支持指向压缩包的 URL，工具会自动将 GitHub `blob` 链接转换为 `raw` 链接
- **忽略过滤：** 导入扫描时自动跳过 `__MACOSX`、`.DS_Store`、`__pycache__`、`.git` 等目录和文件，可通过全局配置文件自定义忽略模式
- **批量确认：** 当来源中包含多个配置项时，工具会逐一询问是否导入；单个配置项则直接导入

## 支持的 IDE

| IDE | 厂商 | Rules | Skills | MCP |
|-----|------|-------|--------|-----|
| **Trae** | 字节跳动 | ✅ | ✅ | ✅ |
| **Qoder** | 阿里巴巴 | ✅ | ✅ | ✅ |
| **Lingma** | 阿里巴巴 | ✅ | ✅ | ✅ |
| **CodeBuddy** | 腾讯 | ✅ | ✅ | ✅ |

## 支持的平台

- **macOS**
- **Windows**

工具会自动检测当前操作系统，并使用对应平台的路径规范解析所有文件路径。

## 安装

### 通过 pip 安装

```bash
pip install msr-sync
```

### 从源码安装

```bash
git clone <仓库地址>
cd MSR-cli
pip install -e .
```

### 开发环境安装（含测试依赖）

```bash
pip install -e ".[dev]"
```

**环境要求：** Python 3.9 或更高版本。

## 快速开始

### 1. 初始化统一仓库

```bash
msr-sync init
```

初始化时会自动在 `~/.msr-sync/config.yaml` 生成带注释的默认配置文件。

如果你已经在各 IDE 中有现有配置，可以使用 `--merge` 参数自动扫描并导入：

```bash
msr-sync init --merge
```

### 2. 导入配置

将 rule 文件导入到统一仓库：

```bash
msr-sync import rules ./my-rule.md
```

将 skill 目录导入：

```bash
msr-sync import skills ./my-skill/
```

将 MCP 配置导入：

```bash
msr-sync import mcp ./my-mcp-config/
```

也支持从压缩包或 URL 导入：

```bash
msr-sync import rules ./rules-pack.zip
msr-sync import rules https://example.com/rules.zip
```

### 3. 同步配置到 IDE

将所有配置同步到所有 IDE（全局级）：

```bash
msr-sync sync
```

同步指定类型的配置到指定 IDE：

```bash
msr-sync sync --type rules --ide trae
```

项目级同步：

```bash
msr-sync sync --scope project --project-dir /path/to/project
```

### 4. 查看配置列表

```bash
msr-sync list
```

按类型过滤：

```bash
msr-sync list --type rules
```

### 5. 删除配置

```bash
msr-sync remove rules my-rule V1
```

## 统一仓库目录结构

MSR-cli 使用 `~/.msr-repos` 作为统一仓库路径，目录结构如下：

```
~/.msr-repos/
├── RULES/                          # 规则配置
│   └── <rule-name>/
│       ├── V1/
│       │   └── <rule-name>.md      # 原始 Markdown 文件
│       └── V2/
│           └── <rule-name>.md
├── SKILLS/                         # 技能配置
│   └── <skill-name>/
│       ├── V1/
│       │   ├── SKILL.md
│       │   └── ...                 # 其他技能文件
│       └── V2/
│           └── ...
└── MCP/                            # MCP 配置
    └── <mcp-name>/
        ├── V1/
        │   └── mcp.json
        └── V2/
            └── mcp.json
```

### 配置类型说明

| 配置类型 | 存储形式 | 说明 |
|---------|---------|------|
| **Rules（规则）** | Markdown 文件 | AI IDE 中的规则配置，用于指导 AI 行为 |
| **Skills（技能）** | 目录（含 SKILL.md） | AI IDE 中的技能配置，包含技能定义和相关文件 |
| **MCP** | JSON 文件 | Model Context Protocol 配置，定义 AI IDE 可用的外部工具 |

## 版本管理

MSR-cli 为每个配置条目提供多版本管理能力：

- **版本命名格式：** `V` + 递增正整数（V1、V2、V3……）
- **导入时：** 若同名配置已存在，自动在最大版本号基础上加一创建新版本
- **同步时：** 未指定 `--version` 时，**默认同步最新版本**（即版本号最大的版本）；可通过 `--version` 参数指定特定版本
- **提示信息：** 同步时会在输出中显示实际使用的版本号，如 `✅ 已同步 skill 'my-skill' (V2) 到 qoder (global)`

```bash
# 同步最新版本（默认行为）
msr-sync sync --type rules --name my-rule
# 输出: ✅ 已同步 rule 'my-rule' (V3) 到 qoder (global)

# 同步指定版本
msr-sync sync --name my-rule --version V1
# 输出: ✅ 已同步 rule 'my-rule' (V1) 到 qoder (global)

# 查看所有版本
msr-sync list
```

## 全局配置

MSR-cli 支持通过全局配置文件自定义工具行为。执行 `msr-sync init` 时会自动生成默认配置文件。

### 配置文件位置

```
~/.msr-sync/config.yaml
```

### 配置项

```yaml
# MSR-sync 全局配置文件

# 统一仓库路径（支持 ~ 展开，默认 ~/.msr-repos）
# repo_path: ~/.msr-repos

# 导入扫描时忽略的目录和文件模式
# 支持精确匹配（如 __MACOSX）和通配符匹配（如 *.pyc）
ignore_patterns:
  - __MACOSX
  - .DS_Store
  - __pycache__
  - .git

# 默认同步目标 IDE 列表
# 可选值: trae, qoder, lingma, codebuddy, cursor, all
# default_ides:
#   - all

# 默认同步层级（global 或 project）
# default_scope: global
```

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `repo_path` | 字符串 | `~/.msr-repos` | 统一仓库根目录路径 |
| `ignore_patterns` | 字符串列表 | `[__MACOSX, .DS_Store, __pycache__, .git]` | 导入扫描时忽略的目录和文件模式 |
| `default_ides` | 字符串列表 | `[all]` | `sync` 命令的默认目标 IDE |
| `default_scope` | 字符串 | `global` | `sync` 命令的默认同步层级 |

### 使用说明

- 配置文件不存在时，工具使用内置默认值，行为不受影响
- 修改配置文件后，下次执行命令时自动生效
- 命令行参数（如 `--ide`、`--scope`）优先级高于配置文件
- 配置文件中注释掉的项使用默认值，按需取消注释即可启用

## 命令概览

| 命令 | 说明 |
|------|------|
| `msr-sync init` | 初始化统一配置仓库 |
| `msr-sync import <类型> <来源>` | 导入配置到统一仓库 |
| `msr-sync sync` | 同步配置到目标 IDE |
| `msr-sync list` | 查看统一仓库中的配置列表 |
| `msr-sync remove <类型> <名称> <版本>` | 删除指定配置版本 |

更多详细用法请参阅 [使用文档](docs/usage.md)。

## 许可证

MIT License
