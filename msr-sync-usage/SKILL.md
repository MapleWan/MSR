---
name: msr-sync-usage
description: MSR-sync CLI 工具使用指南，用于统一管理多款国内 AI IDE（Trae、Qoder、Lingma、CodeBuddy）的 rules、skills、MCP 配置
---

# MSR-sync CLI 使用指南

你是 MSR-sync (`msr-sync`) 命令行工具的使用专家。MSR-sync 是一个统一管理多款国内 AI IDE（Trae、Qoder、Lingma、CodeBuddy）的 rules、skills、MCP 配置的 Python CLI 工具。

## 核心概念

- **统一仓库：** `~/.msr-repos`，存储所有配置的中心化本地仓库，包含 `RULES/`、`SKILLS/`、`MCP/` 三个子目录
- **配置类型：** `rules`（Markdown 规则文件）、`skills`（含 SKILL.md 的目录）、`mcp`（JSON 配置）
- **版本管理：** 每个配置支持多版本（V1、V2、V3…），导入同名配置自动递增版本号
- **全局配置：** `~/.msr-sync/config.yaml`，可自定义仓库路径、忽略模式、默认 IDE 和同步层级
- **支持的 IDE：** `trae`（字节）、`qoder`（阿里）、`lingma`（阿里）、`codebuddy`（腾讯）

## 命令速查

### 初始化

```bash
# 初始化仓库（同时生成默认配置文件 ~/.msr-sync/config.yaml）
msr-sync init

# 初始化并合并已有 IDE 配置
msr-sync init --merge
```

### 导入配置

```bash
# 导入单个 rule 文件
msr-sync import rules ./my-rule.md

# 导入 skill 目录
msr-sync import skills ./my-skill/

# 导入 MCP 配置目录
msr-sync import mcp ./my-mcp/

# 从压缩包导入
msr-sync import skills ./skills-pack.zip

# 从 URL 导入（自动转换 GitHub blob 链接为 raw 链接）
msr-sync import rules https://github.com/user/repo/raw/main/rules.zip
```

### 同步配置

```bash
# 同步所有配置到所有 IDE（全局级，默认最新版本）
msr-sync sync

# 同步到指定 IDE
msr-sync sync --ide trae --ide codebuddy

# 同步指定类型
msr-sync sync --type rules

# 项目级同步
msr-sync sync --scope project --project-dir /path/to/project

# 同步指定配置的指定版本
msr-sync sync --type rules --name my-rule --version V1
```

### 查看和删除

```bash
# 查看所有配置（树形结构）
msr-sync list

# 按类型过滤
msr-sync list --type skills

# 删除指定版本
msr-sync remove rules my-rule V1
```

## 全局配置文件

位置：`~/.msr-sync/config.yaml`（`msr-sync init` 时自动生成）

```yaml
# 统一仓库路径
# repo_path: ~/.msr-repos

# 导入扫描时忽略的目录和文件模式
ignore_patterns:
  - __MACOSX
  - .DS_Store
  - __pycache__
  - .git

# 默认同步目标 IDE（可选: trae, qoder, lingma, codebuddy, all）
# default_ides:
#   - all

# 默认同步层级（global 或 project）
# default_scope: global
```

配置优先级：命令行参数 > 配置文件 > 内置默认值。修改配置后下次执行命令自动生效。

## 同步版本行为

- 未指定 `--version` 时，默认同步**最新版本**（版本号最大的）
- 同步提示会显示实际版本号，如：`✅ 已同步 skill 'my-skill' (V2) 到 qoder (global)`

## IDE 路径映射（macOS）

| IDE | Rules (project) | Skills (global) | MCP |
|-----|----------------|-----------------|-----|
| Trae | `<project>/.trae/rules/<name>.md` | `~/.trae-cn/skills/<name>/` | `~/Library/Application Support/Trae CN/User/mcp.json` |
| Qoder | `<project>/.qoder/rules/<name>.md` | `~/.qoder/skills/<name>/` | `~/Library/Application Support/Qoder/SharedClientCache/mcp.json` |
| Lingma | `<project>/.lingma/rules/<name>.md` | `~/.lingma/skills/<name>/` | `~/Library/Application Support/Lingma/SharedClientCache/mcp.json` |
| CodeBuddy | `<project>/.codebuddy/rules/<name>.md` | `~/.codebuddy/skills/<name>/` | `~/.codebuddy/mcp.json` |

注意：只有 CodeBuddy 支持全局级 rules（`~/.codebuddy/rules/`），其他 IDE 全局同步 rules 时会跳过并输出警告。

## Rules 同步时的 Frontmatter 处理

同步 rule 时，工具自动剥离原始 frontmatter 并添加 IDE 特定头部：
- **Qoder / Lingma：** 添加 `trigger: always_on`
- **Trae：** 不添加头部，直接写入纯内容
- **CodeBuddy：** 添加含 `alwaysApply: true`、`enabled: true`、`updatedAt` 时间戳的头部

## 常见问题

- **导入压缩包出现 `__MACOSX` 目录：** 已通过全局配置的 `ignore_patterns` 自动过滤
- **GitHub URL 导入失败：** 使用 `raw` 链接（`/raw/main/...`），工具会自动转换 `blob` 链接
- **全局 rules 同步被跳过：** Trae/Qoder/Lingma 不支持全局 rules，改用 `--scope project`
- **MCP 同步冲突：** 目标已有同名条目时会提示确认，拒绝则跳过
