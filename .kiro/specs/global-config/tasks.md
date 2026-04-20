# 实现计划：全局配置 (Global Config)

## 概述

为 MSR-cli 引入全局配置文件 `~/.msr-sync/config.yaml`，按以下顺序递增实现：先搭建核心配置模块和异常类，再逐步集成到 Repository、SourceResolver 和 CLI 层，最后通过集成测试验证端到端行为。每一步都在前一步基础上构建，不会产生孤立代码。

## 任务列表

- [ ] 1. 添加 pyyaml 依赖和 ConfigFileError 异常
  - [ ] 1.1 在 `MSR-cli/pyproject.toml` 的 `dependencies` 中添加 `pyyaml>=6.0`
    - 在 `[project] dependencies` 列表中，与现有的 `"click>=8.0"` 并列添加 `"pyyaml>=6.0"`
    - 在 `MSR-cli/` 目录下执行 `pip install -e .` 安装新依赖
    - _需求: 7.1_

  - [ ] 1.2 在 `MSR-cli/msr_sync/core/exceptions.py` 中添加 `ConfigFileError` 异常
    - 添加 `class ConfigFileError(MSRError)`，文档字符串为 `"""配置文件解析错误（YAML 语法错误等）"""`
    - _需求: 1.4_

- [ ] 2. 实现核心 GlobalConfig 模块
  - [ ] 2.1 创建 `MSR-cli/msr_sync/core/config.py`，实现 `GlobalConfig` 类和 `load_config` 函数
    - 定义常量：`DEFAULT_REPO_PATH`、`DEFAULT_IGNORE_PATTERNS`、`DEFAULT_IDES`、`DEFAULT_SCOPE`、`VALID_SCOPES`、`VALID_IDES`、`CONFIG_FILE_PATH`
    - 实现 `GlobalConfig.__init__`，接受可选参数 `repo_path`、`ignore_patterns`、`default_ides`、`default_scope`
    - 实现 `_resolve_repo_path`：展开 `~`，空字符串回退到默认值
    - 实现 `_validate_ides`：过滤无效 IDE 名称并通过 `click.echo` 输出中文警告，空列表回退到默认值
    - 实现 `_validate_scope`：无效值输出警告并回退到默认值
    - 实现 `to_dict` 用于序列化
    - 实现 `load_config(config_path)`：处理文件不存在（返回默认值）、空文件（返回默认值）、YAML 解析错误（抛出 `ConfigFileError` 并包含文件路径的中文错误信息）、合法 YAML（与默认值合并）、非字典 YAML（返回默认值）
    - 实现 `config_to_yaml` 用于往返序列化
    - 实现模块级单例：`get_config()`、`init_config()`、`reset_config()`
    - 严格按照设计文档中的接口定义实现
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 3.1, 3.2, 3.4, 4.1, 4.4, 4.5, 5.1, 5.4, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3_

  - [ ] 2.2 编写 GlobalConfig 单元测试 (`MSR-cli/tests/test_config.py`)
    - 测试：配置文件不存在时返回全部默认值（需求 1.2）
    - 测试：空配置文件返回全部默认值（需求 1.3）
    - 测试：YAML 语法错误时抛出 ConfigFileError 并包含文件路径（需求 1.4）
    - 测试：`ignore_patterns` 默认值为 `["__MACOSX", ".DS_Store", "__pycache__", ".git"]`（需求 2.1）
    - 测试：`repo_path` 默认值为 `~/.msr-repos` 展开后的路径（需求 3.1）
    - 测试：`repo_path` 空字符串回退到默认值（需求 3.4）
    - 测试：`default_ides` 默认值为 `["all"]`（需求 4.1）
    - 测试：`default_ides` 空列表回退到默认值（需求 4.5）
    - 测试：`default_scope` 默认值为 `"global"`（需求 5.1）
    - 测试：包含注释的 YAML 正确解析（需求 6.1）
    - 测试：带引号和不带引号的 YAML 字符串正确解析（需求 7.3）
    - 测试：单例 `get_config`/`init_config`/`reset_config` 生命周期
    - _需求: 1.2, 1.3, 1.4, 2.1, 3.1, 3.4, 4.1, 4.5, 5.1, 6.1, 7.3_

  - [ ] 2.3 编写属性测试：配置加载正确性（部分配置与未知键）
    - **Property 1: 配置加载正确性（部分配置与未知键）**
    - **验证: 需求 1.1, 1.5, 6.3**
    - 生成合法配置键的随机子集（含有效值）以及随机未知键
    - 写入 YAML 文件，通过 `load_config` 加载，断言已知键与输入一致、缺失键使用默认值、未知键被忽略

  - [ ] 2.4 编写属性测试：仓库路径波浪号展开
    - **Property 3: 仓库路径波浪号展开**
    - **验证: 需求 3.2**
    - 生成随机 `~/...` 路径字符串
    - 断言 `GlobalConfig(repo_path=input).repo_path` 等于 `Path(input).expanduser()` 且不包含 `~`

  - [ ] 2.5 编写属性测试：无效 IDE 名称过滤
    - **Property 4: 无效 IDE 名称过滤**
    - **验证: 需求 4.4, 4.5**
    - 生成混合有效和无效 IDE 名称的随机字符串列表
    - 断言结果仅包含有效 IDE 名称；全部无效或空输入回退到 `["all"]`

  - [ ] 2.6 编写属性测试：无效同步层级回退
    - **Property 5: 无效同步层级回退**
    - **验证: 需求 5.4**
    - 生成不等于 `"global"` 和 `"project"` 的随机字符串
    - 断言 `GlobalConfig(default_scope=input).default_scope == "global"`

  - [ ] 2.7 编写属性测试：配置 YAML 往返一致性
    - **Property 6: 配置 YAML 往返一致性**
    - **验证: 需求 7.2**
    - 生成随机合法 `GlobalConfig` 对象（有效的 repo_path、ignore_patterns、default_ides、default_scope）
    - 通过 `config_to_yaml` 序列化，写入文件，通过 `load_config` 加载，断言 `to_dict()` 一致

- [ ] 3. 检查点 — 确保配置模块所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [ ] 4. 将忽略模式集成到 SourceResolver
  - [ ] 4.1 在 `MSR-cli/msr_sync/core/source_resolver.py` 中添加 `_should_ignore` 方法和过滤逻辑
    - 添加 `import fnmatch` 和从 `msr_sync.core.config` 导入 `get_config`
    - 实现 `_should_ignore(self, name: str) -> bool`：对 `get_config().ignore_patterns` 中的每个模式，不含通配符（`*`、`?`、`[`）的使用精确匹配，含通配符的使用 `fnmatch.fnmatch`；仅匹配文件名/目录名，不匹配完整路径
    - 在 `_resolve_rules_directory` 循环中添加 `self._should_ignore(entry.name)` 过滤
    - 在 `_resolve_skills_directory` 循环中添加过滤（单 skill 子扫描和多 skill 子扫描）
    - 在 `_resolve_mcp_directory` 循环中添加过滤（单 MCP 子扫描和多 MCP 子扫描）
    - 压缩包解压路径（`_resolve_archive`）已委托给 `_resolve_directory`，过滤自动继承
    - _需求: 2.2, 2.3, 2.4, 2.5_

  - [ ] 4.2 编写属性测试：忽略模式匹配正确性
    - **Property 2: 忽略模式匹配正确性**
    - **验证: 需求 2.2, 2.3, 2.5**
    - 生成随机文件名和随机忽略模式列表
    - 断言 `_should_ignore(name)` 返回 True 当且仅当名称匹配至少一个模式（非通配符精确匹配，通配符 fnmatch 匹配）

  - [ ] 4.3 编写 SourceResolver 忽略过滤单元测试
    - 测试：目录扫描跳过精确匹配忽略模式的条目（如 `__MACOSX`、`.DS_Store`）（需求 2.2）
    - 测试：目录扫描跳过通配符匹配的条目（如 `*.pyc`）（需求 2.3）
    - 测试：压缩包解压后扫描应用相同的忽略过滤（需求 2.4）
    - 测试：过滤仅作用于条目名称，不作用于完整路径（需求 2.5）
    - _需求: 2.2, 2.3, 2.4, 2.5_

- [ ] 5. 将 repo_path 配置集成到 Repository
  - [ ] 5.1 修改 `MSR-cli/msr_sync/core/repository.py` 中的 `Repository.__init__` 以使用配置
    - 当 `base_path` 为 `None` 时，从 `msr_sync.core.config` 导入 `get_config` 并使用 `get_config().repo_path` 替代硬编码的 `Path.home() / ".msr-repos"`
    - 当显式传入 `base_path` 时，仍使用传入值（保留测试注入能力）
    - _需求: 3.3_

  - [ ] 5.2 编写 Repository 使用配置 repo_path 的单元测试
    - 测试：不传 `base_path` 的 `Repository()` 使用 GlobalConfig 中的值（需求 3.3）
    - 测试：`Repository(base_path=custom)` 仍使用显式传入的路径
    - _需求: 3.3_

- [ ] 6. 将 default_ides 和 default_scope 集成到 CLI sync 命令
  - [ ] 6.1 修改 `MSR-cli/msr_sync/cli.py` 中的 `sync` 命令以从配置读取默认值
    - 将 `--ide` 选项的 `default` 从 `("all",)` 改为 `None`
    - 将 `--scope` 选项的 `default` 从 `"global"` 改为 `None`
    - 在 `sync` 函数体中：导入 `get_config`，若 `ide` 为 `None` 或空元组则使用 `cfg.default_ides`，若 `scope` 为 `None` 则使用 `cfg.default_scope`
    - 确保显式 CLI 参数仍覆盖配置值
    - _需求: 4.2, 4.3, 5.2, 5.3_

  - [ ] 6.2 编写 CLI sync 命令配置集成测试
    - 测试：`msr-sync sync` 不指定 `--ide` 时使用配置文件中的 `default_ides`（需求 4.2）
    - 测试：`msr-sync sync --ide trae` 覆盖配置中的 `default_ides`（需求 4.3）
    - 测试：`msr-sync sync` 不指定 `--scope` 时使用配置文件中的 `default_scope`（需求 5.2）
    - 测试：`msr-sync sync --scope project` 覆盖配置中的 `default_scope`（需求 5.3）
    - 使用 `click.testing.CliRunner` 和 mock `get_config` / `init_config` 进行测试
    - _需求: 4.2, 4.3, 5.2, 5.3_

- [ ] 7. 最终检查点 — 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

## 备注

- 每个任务引用了具体的需求编号，确保可追溯性
- 检查点任务用于阶段性验证，确保增量式开发的正确性
- 属性测试验证通用正确性属性，单元测试验证具体场景和边界条件
- 所有代码位于 `MSR-cli/` 目录下
- 所有面向用户的消息（警告、错误提示）均使用中文
