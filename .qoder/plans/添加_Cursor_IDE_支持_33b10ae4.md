# 添加 Cursor IDE 支持

## 概述
为 MSR-cli 添加 Cursor IDE 适配器。Cursor 与 CodeBuddy 类似，配置存储在 `.cursor` 目录下，但不支持用户级（全局）rules。

## 任务列表

### 任务 1: 添加 Cursor frontmatter 生成函数
- **文件**: `MSR-cli/msr_sync/core/frontmatter.py`
- **操作**: 添加 `build_cursor_header()` 函数，生成 Cursor 格式的 frontmatter 头部（与 CodeBuddy 格式一致，含时间戳）

### 任务 2: 创建 Cursor 适配器
- **文件**: `MSR-cli/msr_sync/adapters/cursor.py`（新建）
- **内容**: 实现 `CursorAdapter` 类，继承 `BaseAdapter`：
  - `ide_name` 返回 `"cursor"`
  - `get_rules_path()`: 项目级路径为 `<project>/.cursor/rules/<name>.md`，全局级路径为 `~/.cursor/rules/<name>.md`
  - `get_skills_path()`: 项目级路径为 `<project>/.cursor/skills/<name>/`，全局级路径为 `~/.cursor/skills/<name>/`
  - `get_mcp_path()`: 返回 `~/.cursor/mcp.json`
  - `format_rule_content()`: 调用 `build_cursor_header()` 添加头部
  - `supports_global_rules()`: 返回 `False`（Cursor 不支持用户级 rules）
  - `scan_existing_configs()`: 扫描 `~/.cursor/` 下的 skills 和 mcp 配置（不扫描全局 rules，因为不支持）

### 任务 3: 注册 Cursor 适配器
- **文件**: `MSR-cli/msr_sync/adapters/registry.py`
- **操作**: 在 `_ADAPTER_REGISTRY` 字典中添加 `"cursor"` 的映射

### 任务 4: CLI 添加 Cursor 选项
- **文件**: `MSR-cli/msr_sync/cli.py`
- **操作**: 在 `sync` 命令的 `--ide` 参数的 `click.Choice` 中添加 `"cursor"`

### 任务 5: 添加 Cursor 适配器单元测试
- **文件**: `MSR-cli/tests/test_cursor_adapter.py`（新建）
- **内容**: 参照 `test_codebuddy_adapter.py` 的结构，测试 Cursor 适配器的：
  - 基本属性（ide_name、supports_global_rules 返回 False）
  - 项目级 rules/skills 路径
  - 全局级 rules/skills 路径（虽然不支持，但路径仍需正确解析）
  - MCP 路径
  - `format_rule_content()` 输出格式
  - `scan_existing_configs()` 扫描逻辑（不扫描 rules）

### 任务 6: 更新跨适配器测试
- **文件**: `MSR-cli/tests/test_adapters.py`
- **操作**: 在以下各处添加 `"cursor"`：
  - `ide_name_strategy` 采样列表
  - `_expected_rules_path()` 和 `_expected_skills_path()` 的 IDE 目录映射
  - `_create_fresh_adapter()` 的适配器映射
  - `TestAllAdaptersAreBaseAdapter` 的参数化列表
  - `TestResolveIdeList` 的断言（适配器数量从 4 变为 5）
  - `TestSupportsGlobalRules` 的参数化列表（cursor 返回 False）
  - `TestRulesPathProjectScope`、`TestRulesPathGlobalScope`、`TestSkillsPathProjectScope` 的参数化列表
  - `TestSkillsPathGlobalScope` 的参数化列表（cursor 使用 `.cursor`）
  - `TestMcpPathMacOS` 和 `TestMcpPathWindows` 中添加 Cursor 专用测试方法
  - `TestFormatRuleContent` 中添加 Cursor 的 format 测试
  - 所有 `@pytest.mark.parametrize("ide_name", [...])` 列表

### 任务 7: 更新 CLI 集成测试
- **文件**: `MSR-cli/tests/test_cli_integration.py`
- **操作**: 在 `test_sync_help_shows_all_parameters` 中断言 `--help` 输出包含 `"cursor"`

### 任务 8: 更新 README 与 usage
- **文件**: `MSR-cli/README.md` 与 `MSR-cli/docs/usage.md`
- **操作**: 在 `--ide` 参数说明中添加 `cursor` 选项

### 任务 9: 运行测试验证
- 运行 pytest 确保所有测试通过，特别关注新增的 Cursor 相关测试和修改后的跨适配器测试
