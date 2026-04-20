# 单元测试报告 — 全局配置 (Global Config)

## 测试环境

| 项目 | 信息 |
|------|------|
| 平台 | macOS (darwin) |
| Python | 3.12.11 |
| pytest | 9.0.2 |
| hypothesis | 6.151.11 |
| 执行时间 | 7.92s |

## 测试结果总览

| 指标 | 数值 |
|------|------|
| **总测试数** | 362 |
| **通过** | 362 ✅ |
| **失败** | 0 |
| **错误** | 0 |
| **跳过** | 0 |
| **警告** | 3（tarfile DeprecationWarning，与本次需求无关） |
| **通过率** | 100% |

## 本次新增测试

本次全局配置功能共新增 34 个测试（从 328 增长到 362），分布如下：

### 新增测试文件

| 测试文件 | 新增测试数 | 覆盖模块 |
|---------|-----------|---------|
| `test_config.py` | 21 | GlobalConfig 类、load_config、单例管理、属性测试 |

### 修改测试文件（新增测试）

| 测试文件 | 新增测试数 | 覆盖内容 |
|---------|-----------|---------|
| `test_source_resolver.py` | 7 | 忽略模式过滤（_should_ignore + 目录扫描集成） |
| `test_repository.py` | 2 | Repository 使用配置 repo_path |
| `test_cli_integration.py` | 4 | sync 命令配置默认值集成 |

### 修改基础设施文件

| 文件 | 修改内容 |
|------|---------|
| `tests/conftest.py` | 新增 `_reset_global_config` autouse fixture，防止单例状态泄漏 |

## 新增测试详情

### test_config.py — GlobalConfig 单元测试（16 个）

| 测试类 | 测试方法 | 覆盖需求 | 状态 |
|-------|---------|---------|------|
| TestLoadConfigFileNotExists | test_returns_defaults_when_file_missing | 1.2 | ✅ |
| TestLoadConfigEmptyFile | test_returns_defaults_when_file_empty | 1.3 | ✅ |
| TestLoadConfigEmptyFile | test_returns_defaults_when_file_whitespace_only | 1.3 | ✅ |
| TestLoadConfigYAMLError | test_raises_config_file_error_with_path | 1.4 | ✅ |
| TestIgnorePatternsDefault | test_default_ignore_patterns | 2.1 | ✅ |
| TestRepoPathDefault | test_default_repo_path | 3.1 | ✅ |
| TestRepoPathEmptyFallback | test_empty_string_falls_back | 3.4 | ✅ |
| TestRepoPathEmptyFallback | test_whitespace_string_falls_back | 3.4 | ✅ |
| TestDefaultIdes | test_default_ides | 4.1 | ✅ |
| TestDefaultIdesEmptyFallback | test_empty_list_falls_back | 4.5 | ✅ |
| TestDefaultScope | test_default_scope | 5.1 | ✅ |
| TestYAMLWithComments | test_comments_are_ignored | 6.1 | ✅ |
| TestYAMLQuotedStrings | test_quoted_and_unquoted | 7.3 | ✅ |
| TestSingletonLifecycle | test_get_config_returns_same_instance | — | ✅ |
| TestSingletonLifecycle | test_init_config_replaces_singleton | — | ✅ |
| TestSingletonLifecycle | test_reset_config_clears_singleton | — | ✅ |

### test_config.py — 属性基测试（5 个）

| 属性 | 测试类 | 迭代次数 | 覆盖需求 | 状态 |
|------|-------|---------|---------|------|
| P1: 配置加载正确性 | TestPropertyConfigLoadCorrectness | 100 | 1.1, 1.5, 6.3 | ✅ |
| P3: 仓库路径波浪号展开 | TestPropertyRepoPathTildeExpansion | 100 | 3.2 | ✅ |
| P4: 无效 IDE 名称过滤 | TestPropertyInvalidIdeFiltering | 100 | 4.4, 4.5 | ✅ |
| P5: 无效同步层级回退 | TestPropertyInvalidScopeFallback | 100 | 5.4 | ✅ |
| P6: 配置 YAML 往返一致性 | TestPropertyConfigYAMLRoundTrip | 100 | 7.2 | ✅ |

### test_source_resolver.py — 忽略模式测试（7 个）

| 测试类 | 测试方法 | 覆盖需求 | 状态 |
|-------|---------|---------|------|
| TestPropertyIgnorePatternMatching | test_should_ignore_matches_correctly (P2) | 2.2, 2.3, 2.5 | ✅ |
| TestIgnoreFilteringUnit | test_rules_directory_skips_exact_match | 2.2 | ✅ |
| TestIgnoreFilteringUnit | test_rules_directory_skips_wildcard_match | 2.3 | ✅ |
| TestIgnoreFilteringUnit | test_archive_applies_same_ignore_filtering | 2.4 | ✅ |
| TestIgnoreFilteringUnit | test_filter_applies_to_name_only_not_full_path | 2.5 | ✅ |
| TestIgnoreFilteringUnit | test_skills_directory_skips_ignored_entries | 2.2 | ✅ |
| TestIgnoreFilteringUnit | test_mcp_directory_skips_ignored_entries | 2.2 | ✅ |

### test_repository.py — Repository 配置集成（2 个）

| 测试类 | 测试方法 | 覆盖需求 | 状态 |
|-------|---------|---------|------|
| TestRepositoryConfigIntegration | test_repository_uses_config_repo_path_when_no_base_path | 3.3 | ✅ |
| TestRepositoryConfigIntegration | test_repository_uses_explicit_base_path_when_provided | 3.3 | ✅ |

### test_cli_integration.py — CLI sync 配置集成（4 个）

| 测试类 | 测试方法 | 覆盖需求 | 状态 |
|-------|---------|---------|------|
| TestSyncCommandConfigIntegration | test_sync_uses_config_default_ides_when_no_ide_flag | 4.2 | ✅ |
| TestSyncCommandConfigIntegration | test_sync_explicit_ide_overrides_config | 4.3 | ✅ |
| TestSyncCommandConfigIntegration | test_sync_uses_config_default_scope_when_no_scope_flag | 5.2 | ✅ |
| TestSyncCommandConfigIntegration | test_sync_explicit_scope_overrides_config | 5.3 | ✅ |

## 需求覆盖矩阵

| 需求 | 验收标准 | 测试覆盖 |
|------|---------|---------|
| 1.1 配置文件加载 | 合法 YAML 正确解析 | P1 属性测试 |
| 1.2 文件不存在 | 返回全部默认值 | test_returns_defaults_when_file_missing |
| 1.3 空文件 | 返回全部默认值 | test_returns_defaults_when_file_empty, test_returns_defaults_when_file_whitespace_only |
| 1.4 YAML 语法错误 | 抛出 ConfigFileError | test_raises_config_file_error_with_path |
| 1.5 部分配置 | 已设置用用户值，未设置用默认值 | P1 属性测试 |
| 2.1 忽略模式默认值 | 默认 4 个模式 | test_default_ignore_patterns |
| 2.2 精确匹配过滤 | 跳过 __MACOSX 等 | test_rules/skills/mcp_directory_skips_exact_match |
| 2.3 通配符匹配过滤 | 跳过 *.pyc 等 | test_rules_directory_skips_wildcard_match, P2 属性测试 |
| 2.4 压缩包解压后过滤 | 同样应用忽略模式 | test_archive_applies_same_ignore_filtering |
| 2.5 仅匹配文件名 | 不匹配完整路径 | test_filter_applies_to_name_only_not_full_path, P2 属性测试 |
| 3.1 repo_path 默认值 | ~/.msr-repos | test_default_repo_path |
| 3.2 波浪号展开 | ~ 展开为绝对路径 | P3 属性测试 |
| 3.3 Repository 集成 | 使用配置值 | test_repository_uses_config_repo_path_when_no_base_path |
| 3.4 空字符串回退 | 回退到默认值 | test_empty_string_falls_back |
| 4.1 default_ides 默认值 | ["all"] | test_default_ides |
| 4.2 sync 使用配置 IDE | 未指定 --ide 时使用配置 | test_sync_uses_config_default_ides_when_no_ide_flag |
| 4.3 CLI 覆盖配置 IDE | --ide 覆盖配置 | test_sync_explicit_ide_overrides_config |
| 4.4 无效 IDE 过滤 | 过滤并警告 | P4 属性测试 |
| 4.5 空列表回退 | 回退到 ["all"] | test_empty_list_falls_back, P4 属性测试 |
| 5.1 default_scope 默认值 | "global" | test_default_scope |
| 5.2 sync 使用配置 scope | 未指定 --scope 时使用配置 | test_sync_uses_config_default_scope_when_no_scope_flag |
| 5.3 CLI 覆盖配置 scope | --scope 覆盖配置 | test_sync_explicit_scope_overrides_config |
| 5.4 无效 scope 回退 | 回退到 "global" | P5 属性测试 |
| 6.1 YAML 注释 | 正确忽略注释 | test_comments_are_ignored |
| 6.3 未知键忽略 | 静默忽略 | P1 属性测试 |
| 7.2 往返一致性 | 序列化再解析一致 | P6 属性测试 |
| 7.3 引号字符串 | 正确解析 | test_quoted_and_unquoted |

## 回归测试

原有 328 个测试全部通过，无回归。新增的 `conftest.py` autouse fixture 确保全局配置单例在每个测试前后重置，不影响已有测试的隔离性。
