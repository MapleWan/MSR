# 实现计划: MSR-cli (`msr-sync`)

## 概述

基于需求文档和技术设计文档，将 MSR-cli 的实现拆分为从基础设施层到 CLI 层的递增式任务。每个任务构建在前一个任务之上，确保代码始终可集成、可测试。所有代码实现位于工作区根目录下的 `MSR-cli/` 文件夹中。

## 任务列表

- [x] 1. 搭建项目骨架与基础配置
  - [x] 1.1 创建项目目录结构和 `pyproject.toml`
    - 在 `MSR-cli/` 下创建 `msr_sync/` 包目录，包含 `__init__.py`、`constants.py`
    - 创建 `msr_sync/core/`、`msr_sync/commands/`、`msr_sync/adapters/` 子包（含 `__init__.py`）
    - 创建 `tests/` 目录及 `conftest.py`
    - 编写 `pyproject.toml`，声明 `click` 依赖、`msr-sync` 入口点、`pytest` + `hypothesis` 测试依赖
    - 在 `constants.py` 中定义统一仓库路径 `~/.msr-repos`、配置类型枚举（`rules`/`skills`/`mcp`）、支持的 IDE 列表等常量
    - _需求: 全局_

  - [x] 1.2 定义异常层次结构
    - 在 `msr_sync/core/` 下创建 `exceptions.py`
    - 实现 `MSRError`、`RepositoryNotFoundError`、`ConfigNotFoundError`、`InvalidSourceError`、`UnsupportedPlatformError`、`NetworkError`、`ConfigParseError` 异常类
    - _需求: 错误处理（设计文档）_

- [x] 2. 实现基础设施层 — 平台检测与版本管理
  - [x] 2.1 实现平台检测模块 (`core/platform.py`)
    - 实现 `PlatformInfo` 类，包含 `get_os()`（返回 `'macos'` 或 `'windows'`，不支持时抛出 `UnsupportedPlatformError`）、`get_home()`、`get_app_support_dir()` 方法
    - 所有错误信息使用中文
    - _需求: 12.1, 12.2_

  - [x] 2.2 实现版本管理模块 (`core/version.py`)
    - 实现 `parse_version(version_str) -> int`：解析 `'V1'` → `1`，无效格式抛出 `ValueError`
    - 实现 `format_version(version_num) -> str`：格式化 `1` → `'V1'`
    - 实现 `get_versions(config_dir) -> List[str]`：获取目录下所有版本号并按数字排序
    - 实现 `get_latest_version(config_dir) -> Optional[str]`：获取最新版本号
    - 实现 `get_next_version(config_dir) -> str`：获取下一个版本号（空目录返回 `'V1'`）
    - _需求: 13.1, 13.2, 2.5, 3.7, 4.7_

  - [x] 2.3 编写版本管理属性测试 (`tests/test_version.py`)
    - **Property 1: 版本号格式往返一致性** — 对任意正整数 n，`parse_version(format_version(n)) == n`
    - **验证: 需求 13.1**
    - **Property 2: 版本递增正确性** — 对任意非空版本目录集合，`get_next_version` 返回最大版本号 +1；空目录返回 V1
    - **验证: 需求 2.5, 3.7, 4.7**
    - **Property 3: 最新版本选择正确性** — 对任意包含至少一个版本目录的配置目录，`get_latest_version` 返回数字最大的版本
    - **验证: 需求 13.2**

- [x] 3. 实现基础设施层 — Frontmatter 处理
  - [x] 3.1 实现 Frontmatter 模块 (`core/frontmatter.py`)
    - 实现 `strip_frontmatter(content) -> str`：移除 Markdown 中以 `---` 包裹的 YAML frontmatter，返回纯内容
    - 实现 `parse_frontmatter(content) -> Tuple[Optional[dict], str]`：解析 frontmatter 并返回字典和正文
    - 实现 `build_qoder_header() -> str`：生成 `---\ntrigger: always_on\n---\n`
    - 实现 `build_lingma_header() -> str`：生成 `---\ntrigger: always_on\n---\n`
    - 实现 `build_codebuddy_header() -> str`：生成含当前时间戳的 CodeBuddy frontmatter
    - _需求: 5.1, 5.2, 5.3, 5.4_

  - [x] 3.2 编写 Frontmatter 属性测试 (`tests/test_frontmatter.py`)
    - **Property 4: Frontmatter 剥离与 IDE 头部转换** — 对任意含合法 YAML frontmatter 的 Markdown 内容，`strip_frontmatter` 后不包含原始 frontmatter，各 IDE 的 `format_rule_content` 以正确模板头部开始且包含原始正文
    - **验证: 需求 5.1, 5.2, 5.3, 5.4**

- [x] 4. 实现基础设施层 — 统一仓库操作
  - [x] 4.1 实现仓库操作模块 (`core/repository.py`)
    - 实现 `Repository` 类，`base_path` 默认为 `~/.msr-repos`，支持注入自定义路径（便于测试）
    - 实现 `init() -> bool`：创建 `RULES/`、`SKILLS/`、`MCP/` 子目录，返回是否新建
    - 实现 `exists() -> bool`：检查仓库是否已存在
    - 实现 `store_rule(name, content) -> str`：存储 rule 文件到 `RULES/<name>/V<n>/`，返回版本号
    - 实现 `store_skill(name, source_dir) -> str`：拷贝 skill 目录到 `SKILLS/<name>/V<n>/`，返回版本号
    - 实现 `store_mcp(name, source_dir) -> str`：拷贝 MCP 目录到 `MCP/<name>/V<n>/`，返回版本号
    - 实现 `get_config_path(config_type, name, version=None) -> Path`：获取配置路径，version 为 None 时返回最新版本
    - 实现 `list_configs(config_type=None) -> Dict`：列出配置 `{config_type: {name: [versions]}}`
    - 实现 `remove_config(config_type, name, version) -> bool`：删除指定版本目录
    - 实现 `read_rule_content(name, version=None) -> str`：读取 rule 原始内容
    - 使用 `core/version.py` 进行版本号管理
    - _需求: 1.1, 2.1, 2.5, 3.1, 3.7, 4.1, 4.7, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 13.1, 13.2, 13.3, 13.4_

  - [x] 4.2 编写仓库操作属性测试 (`tests/test_repository.py`)
    - **Property 9: 配置列表输出完整性** — 对任意仓库状态，`list_configs` 返回所有配置条目及其版本号；指定 `--type` 时仅返回该类型
    - **验证: 需求 9.1, 9.2, 9.3**

  - [x] 4.3 编写仓库操作单元测试 (`tests/test_repository.py`)
    - 测试 `init` 创建目录结构（需求 1.1）
    - 测试 `init` 幂等性（需求 1.2）
    - 测试 `store_rule` 单文件导入（需求 2.1）
    - 测试 `store_skill` / `store_mcp` 单文件夹导入（需求 3.1, 4.1）
    - 测试 `remove_config` 成功和失败场景（需求 10.1, 10.2, 10.3）
    - 测试版本不存在时的错误处理（需求 13.4）
    - _需求: 1.1, 1.2, 2.1, 3.1, 4.1, 10.1, 10.2, 10.3, 13.4_

- [x] 5. 检查点 — 基础设施层验证
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 6. 实现基础设施层 — 来源解析器
  - [x] 6.1 实现来源解析器 (`core/source_resolver.py`)
    - 实现 `SourceType` 枚举（`FILE`/`DIRECTORY`/`ARCHIVE`/`URL`）
    - 实现 `ResolvedItem` 数据类（`name`、`path`、`source_type`）
    - 实现 `SourceResolver` 类：
      - `resolve(source, config_type) -> Tuple[List[ResolvedItem], bool]`：解析来源，返回配置项列表和是否需要用户确认
      - `_detect_source_type(source) -> SourceType`：检测来源类型（文件/目录/压缩包/URL）
      - `_resolve_file(path) -> List[ResolvedItem]`：解析单个 `.md` 文件
      - `_resolve_directory(path, config_type) -> List[ResolvedItem]`：解析目录，根据 config_type 检测配置项
      - `_resolve_archive(path, config_type) -> List[ResolvedItem]`：解压 zip/tar.gz 并解析
      - `_resolve_url(url, config_type) -> List[ResolvedItem]`：下载 URL 到临时目录后解析
      - `_is_single_skill(path) -> bool`：根目录含 `SKILL.md` 则为单个 skill
      - `_is_single_mcp(path) -> bool`：根目录含非子目录文件则为单个 MCP
    - 临时文件使用 `tempfile` 管理，确保清理
    - _需求: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 6.2 编写来源解析器属性测试 (`tests/test_source_resolver.py`)
    - **Property 5: 来源解析器检测完整性** — 对任意包含 N 个匹配配置项的目录，解析器恰好检测到 N 个配置项，名称与原始文件/目录名一致
    - **验证: 需求 2.2, 3.3, 4.3**
    - **Property 6: MCP 单/多配置分类正确性** — 根目录含非子目录文件则为单个 MCP，仅含子目录则为多个 MCP
    - **验证: 需求 3.6**
    - **Property 7: Skill 单/多配置分类正确性** — 根目录含 `SKILL.md` 则为单个 skill，否则为多个 skill
    - **验证: 需求 4.6**

  - [x] 6.3 编写来源解析器单元测试 (`tests/test_source_resolver.py`)
    - 测试单文件解析（需求 2.1）
    - 测试多文件目录解析（需求 2.2）
    - 测试压缩包解析（zip/tar.gz）（需求 2.3, 3.2, 3.4, 4.2, 4.4）
    - 测试 URL 下载解析（mock HTTP）（需求 2.4, 3.5, 4.5）
    - 测试无效来源错误处理
    - _需求: 2.1, 2.2, 2.3, 2.4, 3.2, 3.4, 3.5, 4.2, 4.4, 4.5_

- [x] 7. 实现适配器层
  - [x] 7.1 实现适配器基类和注册表 (`adapters/base.py`, `adapters/registry.py`)
    - 实现 `BaseAdapter` 抽象基类，定义 `ide_name`、`get_rules_path`、`get_skills_path`、`get_mcp_path`、`format_rule_content`、`supports_global_rules`、`scan_existing_configs` 接口
    - 实现 `registry.py`：`get_adapter(ide_name)`、`get_all_adapters()`、`resolve_ide_list(ide_names)` 函数
    - _需求: 11（全部）_

  - [x] 7.2 实现 Qoder 适配器 (`adapters/qoder.py`)
    - 项目级 rules 路径: `<project>/.qoder/rules/<name>.md`
    - 项目级 skills 路径: `<project>/.qoder/skills/<name>/`
    - 用户级 skills 路径: `~/.qoder/skills/<name>/`
    - MCP 路径: macOS `~/Library/Application Support/Qoder/SharedClientCache/mcp.json`，Windows `%APPDATA%/Qoder/SharedClientCache/mcp.json`
    - `supports_global_rules()` 返回 `False`
    - `format_rule_content`：添加 `---\ntrigger: always_on\n---\n` 头部
    - _需求: 5.1, 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 7.3 实现 Lingma 适配器 (`adapters/lingma.py`)
    - 项目级 rules 路径: `<project>/.lingma/rules/<name>.md`
    - 项目级 skills 路径: `<project>/.lingma/skills/<name>/`
    - 用户级 skills 路径: `~/.lingma/skills/<name>/`
    - MCP 路径: macOS `~/Library/Application Support/Lingma/SharedClientCache/mcp.json`，Windows `%APPDATA%/Lingma/SharedClientCache/mcp.json`
    - `supports_global_rules()` 返回 `False`
    - `format_rule_content`：添加 `---\ntrigger: always_on\n---\n` 头部
    - _需求: 5.2, 11.6, 11.7, 11.8, 11.9, 11.10_

  - [x] 7.4 实现 Trae 适配器 (`adapters/trae.py`)
    - 项目级 rules 路径: `<project>/.trae/rules/<name>.md`
    - 项目级 skills 路径: `<project>/.trae/skills/<name>/`
    - 用户级 skills 路径: `~/.trae-cn/skills/<name>/`
    - MCP 路径: macOS `~/Library/Application Support/Trae CN/User/mcp.json`，Windows `%APPDATA%/Trae CN/User/mcp.json`
    - `supports_global_rules()` 返回 `False`
    - `format_rule_content`：不添加额外头部，直接返回纯内容
    - _需求: 5.3, 11.11, 11.12, 11.13, 11.14, 11.15_

  - [x] 7.5 实现 CodeBuddy 适配器 (`adapters/codebuddy.py`)
    - 项目级 rules 路径: `<project>/.codebuddy/rules/`
    - 用户级 rules 路径: `~/.codebuddy/rules/`
    - 项目级 skills 路径: `<project>/.codebuddy/skills/<name>/`
    - 用户级 skills 路径: `~/.codebuddy/skills/<name>/`
    - MCP 路径: macOS/Windows 均为 `~/.codebuddy/mcp.json`
    - `supports_global_rules()` 返回 `True`
    - `format_rule_content`：添加含当前时间戳的 CodeBuddy frontmatter 头部
    - _需求: 5.4, 11.16, 11.17, 11.18, 11.19, 11.20, 11.21_

  - [x] 7.6 编写适配器属性测试 (`tests/test_adapters.py`)
    - **Property 10: IDE 路径解析正确性** — 对任意合法的 (IDE, 配置类型, 层级, 平台) 组合，适配器解析出的路径与需求文档定义的路径模式完全匹配
    - **验证: 需求 11.1 - 11.21**

  - [x] 7.7 编写适配器单元测试 (`tests/test_adapters.py`)
    - 测试各 IDE 的 rules/skills/mcp 路径解析（project 和 global 层级）
    - 测试各 IDE 的 `format_rule_content` 输出格式
    - 测试 `supports_global_rules` 返回值
    - 测试 `resolve_ide_list` 对 `'all'` 的展开
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.6, 11.1 - 11.21_

- [x] 8. 检查点 — 适配器层验证
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 9. 实现命令处理器 — init 与 list 与 remove
  - [x] 9.1 实现 init 命令处理器 (`commands/init_cmd.py`)
    - 调用 `Repository.init()` 创建仓库目录结构
    - 仓库已存在时输出中文提示"统一仓库已初始化，跳过创建"
    - 支持 `--merge` 参数：扫描所有 IDE 适配器的 `scan_existing_configs()`，将发现的配置导入仓库，输出合并摘要
    - _需求: 1.1, 1.2, 1.3, 1.4_

  - [x] 9.2 实现 list 命令处理器 (`commands/list_cmd.py`)
    - 调用 `Repository.list_configs()` 获取配置列表
    - 以树形结构按配置类型分组展示，显示名称和版本号
    - 支持 `--type` 参数过滤
    - 仓库不存在时输出中文错误提示
    - _需求: 9.1, 9.2, 9.3_

  - [x] 9.3 实现 remove 命令处理器 (`commands/remove_cmd.py`)
    - 调用 `Repository.remove_config()` 删除指定版本
    - 配置不存在时输出中文错误提示
    - 删除成功时输出中文确认信息
    - _需求: 10.1, 10.2, 10.3_

- [x] 10. 实现命令处理器 — import
  - [x] 10.1 实现 import 命令处理器 (`commands/import_cmd.py`)
    - 接受 `config_type`（`rules`/`skills`/`mcp`）和 `source` 参数
    - 调用 `SourceResolver.resolve()` 解析来源
    - 单个配置项直接导入；多个配置项展示列表供用户选择性确认（使用 `click.confirm` 或交互式选择）
    - 根据 `config_type` 调用 `Repository` 的 `store_rule`/`store_skill`/`store_mcp`
    - 名称冲突时自动创建新版本
    - 输出导入结果摘要（中文）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 11. 实现命令处理器 — sync
  - [x] 11.1 实现 sync 命令处理器 (`commands/sync_cmd.py`)
    - 解析 `--ide`、`--scope`、`--project-dir`、`--type`、`--name`、`--version` 参数
    - `--scope` 为 `project` 时，`--project-dir` 默认为当前工作目录
    - `--scope` 为 `global` 时忽略 `--project-dir`
    - 调用 `resolve_ide_list` 解析目标 IDE 列表
    - 遍历配置类型和配置条目，调用对应适配器执行同步
    - _需求: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 11.2 实现 Rules 同步逻辑
    - 从仓库读取 rule 内容，调用 `strip_frontmatter` 去除原始 frontmatter
    - 调用各适配器的 `format_rule_content` 添加 IDE 特定头部
    - 根据 scope 写入项目级或全局级路径
    - 全局级同步时，若 IDE 不支持全局 rules，输出中文警告并跳过
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 13.2, 13.3_

  - [x] 11.3 实现 MCP 同步逻辑
    - 读取仓库中的 MCP 配置（JSON）
    - 目标 `mcp.json` 不存在时新建
    - 目标 `mcp.json` 存在但无同名条目时追加到 `servers` 字段
    - 目标 `mcp.json` 存在且有同名条目时提示用户确认覆盖
    - 用户拒绝覆盖时跳过该条目
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 11.4 实现 Skills 同步逻辑
    - 拷贝仓库中的 skill 目录到目标 IDE 路径
    - 目标不存在同名 skill 时直接拷贝
    - 目标存在同名 skill 时提示用户确认覆盖
    - 用户拒绝覆盖时跳过该 skill
    - 根据 scope 写入项目级或全局级路径
    - _需求: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x] 11.5 编写 MCP 合并属性测试 (`tests/test_commands.py`)
    - **Property 8: MCP JSON 合并保留已有条目** — 对任意合法 `mcp.json` 和不冲突的新 MCP 条目，合并后同时包含所有原有条目和新条目，原有条目内容不变
    - **验证: 需求 6.2**

- [x] 12. 实现 CLI 入口与命令注册
  - [x] 12.1 实现 CLI 入口 (`cli.py`)
    - 使用 `click.group()` 创建 `main` 命令组
    - 注册 `init`、`import`、`sync`、`list`、`remove` 子命令
    - 定义所有命令参数（`--merge`、`--ide`、`--scope`、`--project-dir`、`--type`、`--name`、`--version`）
    - 在命令入口处捕获 `MSRError` 异常，输出中文错误信息并以退出码 1 退出
    - _需求: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 12.2 编写 CLI 集成测试 (`tests/test_commands.py`)
    - 使用 `click.testing.CliRunner` 测试各子命令
    - 测试 `init` 创建目录和幂等性（需求 1.1, 1.2）
    - 测试 `list` 输出格式（需求 9.1, 9.2, 9.3）
    - 测试 `remove` 成功和失败（需求 10.1, 10.2, 10.3）
    - 测试 `sync` 参数校验（需求 8.1 - 8.7）
    - 测试全局 rules 不支持警告（需求 5.6）
    - _需求: 1.1, 1.2, 5.6, 8.1 - 8.7, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3_

- [x] 13. 检查点 — 全功能验证
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 14. 端到端集成测试与收尾
  - [x] 14.1 编写端到端集成测试 (`tests/test_integration.py`)
    - 测试 `init --merge` 扫描并导入已有 IDE 配置（需求 1.3, 1.4）
    - 测试压缩包导入完整流程（zip/tar.gz）（需求 2.3, 3.2, 3.4, 4.2, 4.4）
    - 测试 URL 下载并导入（mock HTTP）（需求 2.4, 3.5, 4.5）
    - 测试完整 import → sync 流程（端到端验证）
    - _需求: 1.3, 1.4, 2.3, 2.4, 3.2, 3.4, 3.5, 4.2, 4.4, 4.5_

  - [x] 14.2 编写项目 `README.md` (`MSR-cli/README.md`)
    - 项目简介：MSR-cli 是什么、解决什么问题
    - 支持的 IDE 列表（Trae、Qoder、Lingma、CodeBuddy）
    - 安装方式（pip install、从源码安装）
    - 快速开始指南（init → import → sync 基本流程）
    - 统一仓库目录结构说明
    - 版本管理机制说明
    - 支持的平台（macOS、Windows）
    - 全部使用中文编写
    - _需求: 全局_

  - [x] 14.3 编写 `msr-sync` 命令使用文档 (`MSR-cli/docs/usage.md`)
    - 所有子命令的详细用法说明，包含命令格式、参数说明、使用示例：
      - `msr-sync init` — 初始化仓库（含 `--merge` 参数说明）
      - `msr-sync import` — 配置导入（rules/skills/mcp 三种类型的导入方式和示例）
      - `msr-sync sync` — 配置同步（`--ide`、`--scope`、`--project-dir`、`--type`、`--name`、`--version` 参数详解和组合示例）
      - `msr-sync list` — 查看配置列表（含 `--type` 过滤示例）
      - `msr-sync remove` — 删除配置（参数说明和示例）
    - 各 IDE 配置路径参考表（macOS/Windows）
    - 常见使用场景示例（如：从 Trae 迁移配置到 CodeBuddy、批量同步到所有 IDE）
    - 错误排查指南（常见错误信息及解决方法）
    - 全部使用中文编写
    - _需求: 全局_

- [x] 15. 最终检查点 — 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

## 备注

- 标记 `*` 的子任务为可选任务，可跳过以加速 MVP 开发
- 每个任务引用了具体的需求编号，确保可追溯性
- 检查点任务用于阶段性验证，确保增量式开发的正确性
- 属性测试验证通用正确性属性，单元测试验证具体场景和边界条件
- 所有面向用户的消息（CLI 输出、错误提示）均使用中文
