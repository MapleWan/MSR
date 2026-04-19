# 需求文档

## 简介

MSR-cli（`msr-sync`）是一个基于 Python 开发的轻量化命令行工具，用于统一管理多款国内 AI IDE（字节 Trae、阿里 Qoder/Lingma、腾讯 CodeBuddy）的 rules、skills、MCP 配置。该工具通过建立统一的本地仓库（`~/.msr-repos`），解决各 AI IDE 配置相互独立、跨 IDE 迁移需手动复制、配置格式与路径不统一等核心痛点，提供初始化、导入、同步、查看、删除等完整的配置生命周期管理能力。

代码实现位于工作区根目录下的 `MSR-cli/` 文件夹中。

## 术语表

- **MSR_CLI**: 命令行工具主程序，命令名为 `msr-sync`，负责统一管理多款 AI IDE 的配置
- **统一仓库（Unified_Repository）**: 位于 `~/.msr-repos`，存储所有 rules、skills、MCP 配置的中心化本地仓库
- **Rule（规则）**: AI IDE 中的规则配置，以 Markdown 文件形式存在，用于指导 AI 行为
- **Skill（技能）**: AI IDE 中的技能配置，以目录形式存在，包含 SKILL.md 等文件
- **MCP 配置**: Model Context Protocol 配置，以 JSON 文件形式存在，定义 AI IDE 可用的外部工具
- **IDE 适配器（IDE_Adapter）**: 负责将统一仓库中的配置转换为特定 IDE 所需的格式和路径
- **配置类型（Config_Type）**: 取值为 rules、skills 或 mcp 之一
- **配置版本（Config_Version）**: 以 "V" 加递增数字命名（如 V1、V2、V3）
- **同步层级（Scope）**: 取值为 project（项目级）或 global（用户级/全局级）
- **目标 IDE（Target_IDE）**: 取值为 trae、qoder、lingma、codebuddy 或 all
- **Frontmatter**: Markdown 文件头部以 `---` 包裹的 YAML 元数据块
- **导入来源（Import_Source）**: 可以是单个文件、文件夹、压缩包或压缩包 URL

## 需求列表

### 需求 1：统一仓库初始化

**用户故事：** 作为开发者，我希望通过命令初始化统一配置仓库，以便拥有一个集中管理所有 AI IDE 配置的本地存储。

#### 验收标准

1. 当用户执行 `msr-sync init` 时，MSR_CLI 应在 `~/.msr-repos` 下创建包含 `RULES`、`SKILLS`、`MCP` 三个子目录的统一仓库目录结构
2. 当用户执行 `msr-sync init` 且统一仓库已存在时，MSR_CLI 应输出仓库已初始化的提示信息并跳过创建
3. 当用户执行 `msr-sync init --merge` 时，MSR_CLI 应创建统一仓库目录结构，并扫描所有支持的 IDE 用户级配置路径下的现有配置
4. 当使用 `--merge` 参数且发现现有 IDE 配置时，MSR_CLI 应将发现的配置导入统一仓库，并输出包含每种配置类型和来源 IDE 导入数量的合并摘要

### 需求 2：Rules 导入

**用户故事：** 作为开发者，我希望从多种来源导入 rule 配置到统一仓库，以便集中管理来自不同渠道的规则文件。

#### 验收标准

1. 当用户提供单个 `<rule-name>.md` 文件路径作为导入来源时，MSR_CLI 应将该文件导入到 `~/.msr-repos/RULES/<rule-name>/V1/`
2. 当用户提供包含多个 `<rule-name>.md` 文件的文件夹路径时，MSR_CLI 应检测每个 `.md` 文件并展示列表供用户选择性确认后再导入
3. 当用户提供包含多个 `<rule-name>.md` 文件的压缩包路径时，MSR_CLI 应解压压缩包、检测每个 `.md` 文件并展示列表供用户选择性确认后再导入
4. 当用户提供指向压缩包的 URL 地址时，MSR_CLI 应下载压缩包、解压、检测每个 `.md` 文件并展示列表供用户选择性确认后再导入
5. 当导入的 rule 名称与统一仓库中已有的 rule 名称冲突时，MSR_CLI 应在最大版本号基础上加一创建新版本

### 需求 3：MCP 配置导入

**用户故事：** 作为开发者，我希望从多种来源导入 MCP 配置到统一仓库，以便集中管理各种 MCP 工具配置。

#### 验收标准

1. 当用户提供单个 `<mcp-name>` 文件夹路径作为导入来源时，MSR_CLI 应将该文件夹导入到 `~/.msr-repos/MCP/<mcp-name>/V1/`
2. 当用户提供包含单个 `<mcp-name>` 文件夹的压缩包时，MSR_CLI 应解压并将该文件夹导入到 `~/.msr-repos/MCP/<mcp-name>/V1/`
3. 当用户提供包含多个 `<mcp-name>` 子文件夹的文件夹路径时，MSR_CLI 应检测每个子文件夹并展示列表供用户确认后再导入
4. 当用户提供包含多个 `<mcp-name>` 子文件夹的压缩包时，MSR_CLI 应解压压缩包、检测每个子文件夹并展示列表供用户确认后再导入
5. 当用户提供指向压缩包的 URL 地址时，MSR_CLI 应下载压缩包、解压、检测 MCP 文件夹并展示列表供用户确认后再导入
6. 在判断导入来源包含单个还是多个 MCP 配置时，MSR_CLI 应以根目录下是否存在除 `<mcp-name>` 子文件夹之外的其他文件为依据——有其他文件则视为单个 MCP 配置，否则视为多个 MCP 配置
7. 当导入的 MCP 名称与统一仓库中已有的 MCP 名称冲突时，MSR_CLI 应在最大版本号基础上加一创建新版本

### 需求 4：Skills 导入

**用户故事：** 作为开发者，我希望从多种来源导入 skill 配置到统一仓库，以便集中管理各种技能配置。

#### 验收标准

1. 当用户提供单个 `<skill-name>` 文件夹路径作为导入来源时，MSR_CLI 应将该文件夹导入到 `~/.msr-repos/SKILLS/<skill-name>/V1/`
2. 当用户提供包含单个 `<skill-name>` 文件夹的压缩包时，MSR_CLI 应解压并将该文件夹导入到 `~/.msr-repos/SKILLS/<skill-name>/V1/`
3. 当用户提供包含多个 `<skill-name>` 子文件夹的文件夹路径时，MSR_CLI 应检测每个子文件夹并展示列表供用户确认后再导入
4. 当用户提供包含多个 `<skill-name>` 子文件夹的压缩包时，MSR_CLI 应解压压缩包、检测每个子文件夹并展示列表供用户确认后再导入
5. 当用户提供指向压缩包的 URL 地址时，MSR_CLI 应下载压缩包、解压、检测 skill 文件夹并展示列表供用户确认后再导入
6. 在判断导入来源包含单个还是多个 skill 配置时，MSR_CLI 应以根目录下是否存在 `SKILL.md` 文件为依据——有 `SKILL.md` 则视为单个 skill 配置，否则视为多个 skill 配置
7. 当导入的 skill 名称与统一仓库中已有的 skill 名称冲突时，MSR_CLI 应在最大版本号基础上加一创建新版本

### 需求 5：Rules 同步

**用户故事：** 作为开发者，我希望将统一仓库中的 rules 同步到指定 IDE，以便在不同 IDE 中使用相同的规则配置。

#### 验收标准

1. 同步 rule 到 Qoder 时，IDE 适配器应读取统一仓库中的 rule 内容（忽略 Frontmatter），添加 Qoder 模板头 `---\ntrigger: always_on\n---\n`，然后写入 Qoder 的 rules 路径
2. 同步 rule 到 Lingma 时，IDE 适配器应读取统一仓库中的 rule 内容（忽略 Frontmatter），添加 Lingma 模板头 `---\ntrigger: always_on\n---\n`，然后写入 Lingma 的 rules 路径
3. 同步 rule 到 Trae 时，IDE 适配器应读取统一仓库中的 rule 内容（忽略 Frontmatter），直接写入 Trae 的 rules 路径，不添加额外模板包装
4. 同步 rule 到 CodeBuddy 时，IDE 适配器应读取统一仓库中的 rule 内容（忽略 Frontmatter），添加 CodeBuddy 模板头 `---\ndescription: \nalwaysApply: true\nenabled: true\nupdatedAt: <当前时间戳>\nprovider: \n---\n`，然后写入 CodeBuddy 的 rules 路径
5. 当同步层级为 project 时，IDE 适配器应将 rule 文件写入目标 IDE 的项目级 rules 目录
6. 当同步层级为 global 且目标 IDE 不支持用户级 rules 时，MSR_CLI 应输出警告信息提示该 IDE 不支持全局级 rules，并跳过该 IDE 的同步

### 需求 6：MCP 配置同步

**用户故事：** 作为开发者，我希望将统一仓库中的 MCP 配置同步到指定 IDE，以便在不同 IDE 中使用相同的 MCP 工具。

#### 验收标准

1. 同步 MCP 配置时，如果目标 IDE 的 MCP 配置文件不存在，IDE 适配器应在目标 IDE 的 MCP 路径下新建 `mcp.json` 文件并写入 MCP 配置
2. 同步 MCP 配置时，如果目标 IDE 的 MCP 配置文件已存在但不包含同名 MCP 条目，IDE 适配器应将新的 MCP 配置条目追加到现有 `mcp.json` 文件中
3. 同步 MCP 配置时，如果目标 IDE 的 MCP 配置文件包含同名 MCP 条目，MSR_CLI 应提示用户确认后再覆盖
4. 当用户确认覆盖现有 MCP 条目时，IDE 适配器应用统一仓库中的新配置替换现有条目
5. 当用户拒绝覆盖现有 MCP 条目时，MSR_CLI 应跳过该 MCP 条目的同步并继续处理剩余条目

### 需求 7：Skills 同步

**用户故事：** 作为开发者，我希望将统一仓库中的 skills 同步到指定 IDE，以便在不同 IDE 中使用相同的技能配置。

#### 验收标准

1. 同步 skill 时，如果目标 IDE 的 skill 目录中不存在同名 skill，IDE 适配器应在目标 IDE 的 skill 路径下新建目录并拷贝统一仓库中的所有 skill 文件
2. 同步 skill 时，如果目标 IDE 的 skill 目录中存在同名 skill，MSR_CLI 应提示用户确认后再覆盖
3. 当用户确认覆盖现有 skill 时，IDE 适配器应用统一仓库中的 skill 文件替换现有 skill 目录内容
4. 当用户拒绝覆盖现有 skill 时，MSR_CLI 应跳过该 skill 的同步并继续处理剩余 skill
5. 当同步层级为 project 时，IDE 适配器应将 skill 目录写入目标 IDE 的项目级 skills 目录
6. 当同步层级为 global 时，IDE 适配器应将 skill 目录写入目标 IDE 的用户级 skills 目录

### 需求 8：同步命令参数

**用户故事：** 作为开发者，我希望通过命令参数精确控制同步范围，以便灵活地选择同步哪些配置到哪些 IDE。

#### 验收标准

1. MSR_CLI 应接受 `--ide` 参数，可选值为 trae、qoder、lingma、codebuddy 或 all，支持多次指定，默认值为 all
2. MSR_CLI 应接受 `--scope` 参数，可选值为 project 或 global，默认值为 global
3. 当 `--scope` 参数设为 project 时，MSR_CLI 应接受 `--project-dir` 参数指定项目目录路径，默认值为当前工作目录
4. 当 `--scope` 参数设为 global 时，MSR_CLI 应忽略 `--project-dir` 参数
5. MSR_CLI 应接受 `--type` 参数，可选值为 rules、skills 或 mcp，用于仅同步指定的配置类型
6. MSR_CLI 应接受 `--name` 参数，用于仅同步指定名称的配置条目
7. MSR_CLI 应接受 `--version` 参数，用于仅同步指定版本的配置条目

### 需求 9：配置列表查看

**用户故事：** 作为开发者，我希望查看统一仓库中的所有配置条目，以便了解当前仓库中有哪些可用配置。

#### 验收标准

1. 当用户执行 `msr-sync list` 时，MSR_CLI 应以树形结构按配置类型分组展示统一仓库中的所有配置条目
2. 当用户执行 `msr-sync list --type <配置类型>` 时，MSR_CLI 应仅以树形结构展示指定配置类型的条目
3. MSR_CLI 应展示每个配置条目的名称及其所有可用版本号

### 需求 10：配置删除

**用户故事：** 作为开发者，我希望删除统一仓库中的指定配置版本，以便清理不再需要的配置。

#### 验收标准

1. 当用户执行 `msr-sync remove <类型> <名称> <版本>` 时，MSR_CLI 应删除 `~/.msr-repos/<TYPE>/<name>/<version>/` 目录
2. 当指定的配置版本目录不存在时，MSR_CLI 应输出错误提示信息
3. 当删除成功时，MSR_CLI 应输出确认信息提示配置版本已被移除

### 需求 11：IDE 配置路径适配

**用户故事：** 作为开发者，我希望工具自动适配各 IDE 的配置路径，以便不需要手动记忆和管理各 IDE 的配置文件位置。

#### 验收标准

1. IDE 适配器应将 Qoder 项目级 rules 路径解析为 `<项目目录>/.qoder/rules/<rule-name>.md`
2. IDE 适配器应将 Qoder 项目级 skills 路径解析为 `<项目目录>/.qoder/skills/<skill-name>/`
3. IDE 适配器应将 Qoder 用户级 skills 路径解析为 `~/.qoder/skills/<skill-name>/`
4. 在 macOS 上运行时，IDE 适配器应将 Qoder MCP 路径解析为 `~/Library/Application Support/Qoder/SharedClientCache/mcp.json`
5. 在 Windows 上运行时，IDE 适配器应将 Qoder MCP 路径解析为 `<用户目录>/AppData/Roaming/Qoder/SharedClientCache/mcp.json`
6. IDE 适配器应将 Lingma 项目级 rules 路径解析为 `<项目目录>/.lingma/rules/<rule-name>.md`
7. IDE 适配器应将 Lingma 项目级 skills 路径解析为 `<项目目录>/.lingma/skills/<skill-name>/`
8. IDE 适配器应将 Lingma 用户级 skills 路径解析为 `~/.lingma/skills/<skill-name>/`
9. 在 macOS 上运行时，IDE 适配器应将 Lingma MCP 路径解析为 `~/Library/Application Support/Lingma/SharedClientCache/mcp.json`
10. 在 Windows 上运行时，IDE 适配器应将 Lingma MCP 路径解析为 `<用户目录>/AppData/Roaming/Lingma/SharedClientCache/mcp.json`
11. IDE 适配器应将 Trae 项目级 rules 路径解析为 `<项目目录>/.trae/rules/<rule-name>.md`
12. IDE 适配器应将 Trae 项目级 skills 路径解析为 `<项目目录>/.trae/skills/<skill-name>/`
13. IDE 适配器应将 Trae 用户级 skills 路径解析为 `~/.trae-cn/skills/<skill-name>/`
14. 在 macOS 上运行时，IDE 适配器应将 Trae MCP 路径解析为 `~/Library/Application Support/Trae CN/User/mcp.json`
15. 在 Windows 上运行时，IDE 适配器应将 Trae MCP 路径解析为 `<用户目录>/AppData/Roaming/Trae CN/User/mcp.json`
16. IDE 适配器应将 CodeBuddy 项目级 rules 路径解析为 `<项目目录>/.codebuddy/rules/`
17. IDE 适配器应将 CodeBuddy 用户级 rules 路径解析为 `~/.codebuddy/rules/`
18. IDE 适配器应将 CodeBuddy 项目级 skills 路径解析为 `<项目目录>/.codebuddy/skills/<skill-name>/`
19. IDE 适配器应将 CodeBuddy 用户级 skills 路径解析为 `~/.codebuddy/skills/<skill-name>/`
20. 在 macOS 上运行时，IDE 适配器应将 CodeBuddy MCP 路径解析为 `~/.codebuddy/mcp.json`
21. 在 Windows 上运行时，IDE 适配器应将 CodeBuddy MCP 路径解析为 `<用户目录>/.codebuddy/mcp.json`

### 需求 12：跨平台支持

**用户故事：** 作为开发者，我希望工具在 macOS 和 Windows 上均能正常工作，以便在不同操作系统上使用相同的工具。

#### 验收标准

1. MSR_CLI 应检测当前操作系统，并使用对应平台的路径规范解析所有文件路径
2. 当运行在不支持的操作系统上时，MSR_CLI 应输出错误信息提示该操作系统不受支持

### 需求 13：版本管理

**用户故事：** 作为开发者，我希望仓库中的配置支持多版本管理，以便保留配置的历史版本并选择性同步。

#### 验收标准

1. MSR_CLI 应以 `V` 加递增正整数（V1、V2、V3）的格式命名每个配置条目的版本目录
2. 同步时如果未指定 `--version` 参数，MSR_CLI 应使用指定配置的最高可用版本
3. 同步时如果指定了 `--version` 参数，MSR_CLI 应使用用户指定的确切版本
4. 当指定的版本不存在时，MSR_CLI 应输出错误信息提示该版本未找到
