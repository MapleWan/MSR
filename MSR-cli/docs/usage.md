# MSR-sync 命令使用文档

本文档详细介绍 `msr-sync` 命令行工具的所有子命令、参数和使用方法。

---

## 目录

- [msr-sync init — 初始化仓库](#msr-sync-init--初始化仓库)
- [msr-sync import — 配置导入](#msr-sync-import--配置导入)
- [msr-sync sync — 配置同步](#msr-sync-sync--配置同步)
- [msr-sync list — 查看配置列表](#msr-sync-list--查看配置列表)
- [msr-sync remove — 删除配置](#msr-sync-remove--删除配置)
- [IDE 配置路径参考表](#ide-配置路径参考表)
- [常见使用场景](#常见使用场景)
- [错误排查指南](#错误排查指南)

---

## msr-sync init — 初始化仓库

初始化统一配置仓库，在 `~/.msr-repos` 下创建标准目录结构。

### 命令格式

```bash
msr-sync init [--merge]
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--merge` | 标志 | 否 | 扫描所有支持的 IDE 现有配置并导入到统一仓库 |

### 使用示例

**基本初始化：**

```bash
msr-sync init
# 输出: ✅ 统一仓库已创建: /Users/username/.msr-repos
```

**重复初始化（幂等操作）：**

```bash
msr-sync init
# 输出: 统一仓库已初始化，跳过创建
```

**初始化并合并已有 IDE 配置：**

```bash
msr-sync init --merge
# 输出:
# ✅ 统一仓库已创建: /Users/username/.msr-repos
#
# 🔍 正在扫描已有 IDE 配置...
#
# 📊 合并摘要（共导入 5 项配置）:
#   rules: trae: 2 项, codebuddy: 1 项
#   skills: qoder: 1 项
#   mcp: lingma: 1 项
```

初始化后的目录结构：

```
~/.msr-repos/
├── RULES/
├── SKILLS/
└── MCP/
```

---

## msr-sync import — 配置导入

从多种来源导入配置到统一仓库。支持文件、文件夹、压缩包和 URL 四种导入来源。

### 命令格式

```bash
msr-sync import <config_type> <source>
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `config_type` | 选项 | 是 | 配置类型，可选值：`rules`、`skills`、`mcp` |
| `source` | 字符串 | 是 | 导入来源：文件路径、目录路径、压缩包路径或 URL |

### 支持的导入来源

| 来源类型 | 说明 | 示例 |
|---------|------|------|
| 单个文件 | `.md` 文件（仅 rules） | `./my-rule.md` |
| 文件夹 | 包含配置的目录 | `./my-skill/` |
| 压缩包 | `.zip`、`.tar.gz`、`.tgz` 格式 | `./configs.zip` |
| URL | 指向压缩包的下载链接 | `https://example.com/rules.zip` |

### Rules 导入示例

**导入单个 rule 文件：**

```bash
msr-sync import rules ./coding-standards.md
# 输出: ✅ 已导入: coding-standards (V1)
```

**导入包含多个 rule 的文件夹（需逐一确认）：**

```bash
msr-sync import rules ./my-rules/
# 输出:
# 发现 3 个 rules 配置项:
#   1. coding-standards
#   2. code-review
#   3. testing-guide
#
# 是否导入 'coding-standards'? [Y/n]: y
#   ✅ 已导入: coding-standards (V1)
# 是否导入 'code-review'? [Y/n]: y
#   ✅ 已导入: code-review (V1)
# 是否导入 'testing-guide'? [Y/n]: n
#   ⏭️ 已跳过: testing-guide
#
# 导入完成: 成功 2 项
```

**从压缩包导入：**

```bash
msr-sync import rules ./rules-collection.zip
```

**从 URL 导入：**

```bash
msr-sync import rules https://example.com/shared-rules.zip
```

### Skills 导入示例

**导入单个 skill 目录（需包含 SKILL.md）：**

```bash
msr-sync import skills ./code-review-skill/
# 输出: ✅ 已导入: code-review-skill (V1)
```

**导入包含多个 skill 的文件夹：**

```bash
msr-sync import skills ./all-skills/
```

### MCP 导入示例

**导入单个 MCP 配置目录：**

```bash
msr-sync import mcp ./my-mcp-server/
# 输出: ✅ 已导入: my-mcp-server (V1)
```

**导入包含多个 MCP 配置的文件夹：**

```bash
msr-sync import mcp ./mcp-configs/
```

### 版本冲突处理

当导入的配置名称与仓库中已有配置重名时，工具会自动创建新版本：

```bash
msr-sync import rules ./coding-standards.md
# 输出: ✅ 已导入: coding-standards (V1)

# 再次导入同名配置
msr-sync import rules ./coding-standards-v2.md
# 输出: ✅ 已导入: coding-standards (V2)
```

### 配置分类规则

- **Rules：** 以 `.md` 文件为单位，文件名（不含扩展名）作为配置名称
- **Skills：** 以目录为单位，根目录包含 `SKILL.md` 文件则视为单个 skill，否则视为包含多个 skill 的目录
- **MCP：** 以目录为单位，根目录包含非子目录的文件则视为单个 MCP 配置，仅包含子目录则视为包含多个 MCP 配置的目录

---

## msr-sync sync — 配置同步

将统一仓库中的配置同步到目标 IDE。支持多种参数组合精确控制同步范围。

### 命令格式

```bash
msr-sync sync [--ide IDE] [--scope SCOPE] [--project-dir DIR] [--type TYPE] [--name NAME] [--version VERSION]
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--ide` | 选项（可多次指定） | 否 | `all` | 目标 IDE，可选值：`trae`、`qoder`、`lingma`、`codebuddy`、`all` |
| `--scope` | 选项 | 否 | `global` | 同步层级，可选值：`project`（项目级）、`global`（全局级） |
| `--project-dir` | 路径 | 否 | 当前工作目录 | 项目目录路径，仅在 `--scope project` 时生效 |
| `--type` | 选项 | 否 | 全部 | 配置类型过滤，可选值：`rules`、`skills`、`mcp` |
| `--name` | 字符串 | 否 | 全部 | 仅同步指定名称的配置 |
| `--version` | 字符串 | 否 | 最新版本 | 仅同步指定版本（如 `V1`） |

### 使用示例

**同步所有配置到所有 IDE（全局级）：**

```bash
msr-sync sync
```

**同步 rules 到指定 IDE：**

```bash
msr-sync sync --type rules --ide trae
```

**同步到多个指定 IDE：**

```bash
msr-sync sync --ide trae --ide codebuddy
```

**项目级同步（使用当前目录）：**

```bash
msr-sync sync --scope project
```

**项目级同步（指定项目目录）：**

```bash
msr-sync sync --scope project --project-dir /path/to/my-project
```

**同步指定名称的配置：**

```bash
msr-sync sync --type rules --name coding-standards
```

**同步指定版本：**

```bash
msr-sync sync --type rules --name coding-standards --version V1
```

**组合示例 — 将指定 rule 的 V2 版本同步到 Trae 的项目级目录：**

```bash
msr-sync sync --type rules --name coding-standards --version V2 --ide trae --scope project --project-dir ./my-project
```

### 同步行为说明

#### Rules 同步

- 从仓库读取 rule 内容，自动剥离原始 frontmatter
- 根据目标 IDE 添加对应的 frontmatter 模板头部
- 写入目标 IDE 的 rules 路径
- 全局级同步时，若目标 IDE 不支持全局 rules（Trae、Qoder、Lingma），会输出警告并跳过

各 IDE 的 frontmatter 处理：

| IDE | 处理方式 |
|-----|---------|
| Qoder | 添加 `trigger: always_on` 头部 |
| Lingma | 添加 `trigger: always_on` 头部 |
| Trae | 不添加额外头部，直接写入纯内容 |
| CodeBuddy | 添加含 `description`、`alwaysApply`、`enabled`、`updatedAt`、`provider` 的头部 |

#### MCP 同步

- 目标 `mcp.json` 不存在时，自动新建文件
- 目标 `mcp.json` 存在但无同名条目时，追加到 `servers` 字段
- 目标 `mcp.json` 存在且有同名条目时，提示用户确认是否覆盖
- 用户拒绝覆盖时跳过该条目，继续处理其余条目

#### Skills 同步

- 目标不存在同名 skill 时，直接拷贝整个目录
- 目标存在同名 skill 时，提示用户确认是否覆盖
- 用户拒绝覆盖时跳过该 skill，继续处理其余 skill

---

## msr-sync list — 查看配置列表

以树形结构展示统一仓库中的所有配置条目及其版本号。

### 命令格式

```bash
msr-sync list [--type TYPE]
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--type` | 选项 | 否 | 仅展示指定类型的配置，可选值：`rules`、`skills`、`mcp` |

### 使用示例

**查看所有配置：**

```bash
msr-sync list
# 输出:
# 📦 统一仓库配置列表
# ├── rules
# │   ├── coding-standards [V1, V2]
# │   └── code-review [V1]
# ├── skills
# │   └── review-skill [V1]
# └── mcp
#     └── github-server [V1, V2, V3]
```

**按类型过滤：**

```bash
msr-sync list --type rules
# 输出:
# 📦 统一仓库配置列表
# └── rules
#     ├── coding-standards [V1, V2]
#     └── code-review [V1]
```

**仓库为空时：**

```bash
msr-sync list
# 输出: 📦 统一仓库为空，暂无配置
```

---

## msr-sync remove — 删除配置

删除统一仓库中指定的配置版本。

### 命令格式

```bash
msr-sync remove <config_type> <name> <version>
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `config_type` | 选项 | 是 | 配置类型，可选值：`rules`、`skills`、`mcp` |
| `name` | 字符串 | 是 | 配置名称 |
| `version` | 字符串 | 是 | 版本号（如 `V1`、`V2`） |

### 使用示例

**删除指定版本：**

```bash
msr-sync remove rules coding-standards V1
# 输出: ✅ 已删除配置: rules/coding-standards/V1
```

**删除不存在的配置版本：**

```bash
msr-sync remove rules non-existent V1
# 输出: ❌ 未找到指定的配置版本: rules/non-existent/V1
```

---

## IDE 配置路径参考表

以下是各 IDE 在不同平台上的配置路径。`msr-sync` 会自动根据当前平台解析正确的路径。

### Qoder（阿里巴巴）

| 配置类型 | 层级 | macOS | Windows |
|---------|------|-------|---------|
| Rules | project | `<项目目录>/.qoder/rules/<name>.md` | 同左 |
| Rules | global | ❌ 不支持 | ❌ 不支持 |
| Skills | project | `<项目目录>/.qoder/skills/<name>/` | 同左 |
| Skills | global | `~/.qoder/skills/<name>/` | 同左 |
| MCP | — | `~/Library/Application Support/Qoder/SharedClientCache/mcp.json` | `%APPDATA%\Qoder\SharedClientCache\mcp.json` |

### Lingma（阿里巴巴）

| 配置类型 | 层级 | macOS | Windows |
|---------|------|-------|---------|
| Rules | project | `<项目目录>/.lingma/rules/<name>.md` | 同左 |
| Rules | global | ❌ 不支持 | ❌ 不支持 |
| Skills | project | `<项目目录>/.lingma/skills/<name>/` | 同左 |
| Skills | global | `~/.lingma/skills/<name>/` | 同左 |
| MCP | — | `~/Library/Application Support/Lingma/SharedClientCache/mcp.json` | `%APPDATA%\Lingma\SharedClientCache\mcp.json` |

### Trae（字节跳动）

| 配置类型 | 层级 | macOS | Windows |
|---------|------|-------|---------|
| Rules | project | `<项目目录>/.trae/rules/<name>.md` | 同左 |
| Rules | global | ❌ 不支持 | ❌ 不支持 |
| Skills | project | `<项目目录>/.trae/skills/<name>/` | 同左 |
| Skills | global | `~/.trae-cn/skills/<name>/` | 同左 |
| MCP | — | `~/Library/Application Support/Trae CN/User/mcp.json` | `%APPDATA%\Trae CN\User\mcp.json` |

### CodeBuddy（腾讯）

| 配置类型 | 层级 | macOS | Windows |
|---------|------|-------|---------|
| Rules | project | `<项目目录>/.codebuddy/rules/` | 同左 |
| Rules | global | `~/.codebuddy/rules/` | 同左 |
| Skills | project | `<项目目录>/.codebuddy/skills/<name>/` | 同左 |
| Skills | global | `~/.codebuddy/skills/<name>/` | 同左 |
| MCP | — | `~/.codebuddy/mcp.json` | `~/.codebuddy/mcp.json` |

> **注意：** 在上述路径中，`~` 代表用户主目录，`%APPDATA%` 代表 Windows 的 `AppData\Roaming` 目录。

---

## 常见使用场景

### 场景一：从 Trae 迁移配置到 CodeBuddy

```bash
# 1. 初始化仓库并合并 Trae 的现有配置
msr-sync init --merge

# 2. 查看已导入的配置
msr-sync list

# 3. 将所有配置同步到 CodeBuddy
msr-sync sync --ide codebuddy
```

### 场景二：批量同步到所有 IDE

```bash
# 同步所有配置到所有支持的 IDE（全局级）
msr-sync sync

# 或者仅同步 rules
msr-sync sync --type rules
```

### 场景三：项目级配置同步

```bash
# 将 rules 同步到当前项目的所有 IDE 配置目录
msr-sync sync --type rules --scope project

# 指定项目目录
msr-sync sync --scope project --project-dir /path/to/my-project
```

### 场景四：管理多版本配置

```bash
# 导入初始版本
msr-sync import rules ./coding-standards-v1.md

# 导入更新版本（自动创建 V2）
msr-sync import rules ./coding-standards-v2.md

# 查看版本列表
msr-sync list --type rules

# 同步最新版本（默认行为）
msr-sync sync --type rules --name coding-standards

# 同步指定旧版本
msr-sync sync --type rules --name coding-standards --version V1

# 删除不需要的旧版本
msr-sync remove rules coding-standards V1
```

### 场景五：从压缩包批量导入共享配置

```bash
# 从团队共享的压缩包导入 rules
msr-sync import rules https://internal.example.com/team-rules.zip

# 确认导入后同步到所有 IDE
msr-sync sync --type rules
```

### 场景六：仅同步 MCP 配置到特定 IDE

```bash
msr-sync sync --type mcp --ide qoder --ide lingma
```

---

## 错误排查指南

### 常见错误信息及解决方法

#### ❌ 统一仓库未初始化，请先执行 `msr-sync init`

**原因：** 在执行 `sync`、`list`、`remove` 或 `import` 命令前，未初始化统一仓库。

**解决方法：**

```bash
msr-sync init
```

#### ❌ 未找到指定的配置版本: {type}/{name}/{version}

**原因：** 执行 `remove` 或 `sync` 时指定的配置名称或版本号不存在。

**解决方法：**

1. 使用 `msr-sync list` 查看当前仓库中的所有配置及版本
2. 确认配置类型、名称和版本号拼写正确

```bash
msr-sync list
```

#### ❌ 无效的导入来源: {source}

**原因：** `import` 命令指定的文件路径、目录路径不存在，或格式不受支持。

**解决方法：**

1. 确认文件或目录路径存在且拼写正确
2. 确认压缩包格式为 `.zip`、`.tar.gz` 或 `.tgz`
3. 确认 URL 地址可访问

#### ❌ 下载失败: {url}，请检查网络连接

**原因：** 从 URL 下载压缩包时网络请求失败。

**解决方法：**

1. 检查网络连接是否正常
2. 确认 URL 地址正确且可访问
3. 如有代理设置，确认代理配置正确

#### ❌ 压缩包解压失败: {path}

**原因：** 压缩包文件损坏或格式不受支持。

**解决方法：**

1. 确认压缩包文件完整未损坏
2. 确认压缩包格式为 `.zip`、`.tar.gz` 或 `.tgz`

#### ❌ MCP 配置文件格式错误: {path}

**原因：** MCP 的 `mcp.json` 文件不是合法的 JSON 格式。

**解决方法：**

1. 检查 `mcp.json` 文件内容是否为合法 JSON
2. 使用 JSON 校验工具验证文件格式

#### ❌ 不支持的操作系统: {os}

**原因：** 当前操作系统不是 macOS 或 Windows。

**解决方法：**

MSR-cli 目前仅支持 macOS 和 Windows 平台。

#### ⚠️ {ide} 不支持全局级 rules，已跳过

**原因：** Trae、Qoder、Lingma 不支持用户级（全局级）rules 配置。

**解决方法：**

- 这是正常的警告信息，不影响其他配置的同步
- 如需同步 rules 到这些 IDE，请使用项目级同步：

```bash
msr-sync sync --type rules --scope project
```

#### ❌ 权限不足，无法写入: {path}

**原因：** 当前用户没有目标路径的写入权限。

**解决方法：**

1. 检查目标目录的权限设置
2. 确认当前用户有写入权限
