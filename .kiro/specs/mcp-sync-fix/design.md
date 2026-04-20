# MCP 同步修复 Bugfix Design

## Overview

MCP 同步功能存在两个缺陷：(1) `_sync_mcp()` 和 `_merge_mcp_config()` 使用 `servers` 作为 JSON 键名，但标准 MCP 配置格式使用 `mcpServers`；(2) 同步时未将 server 配置中的 `cwd` 字段重写为统一仓库中的实际路径。修复策略是将所有键名从 `servers` 改为 `mcpServers`，并在 `_sync_mcp()` 中对含有 `cwd` 字段的 server 配置进行路径重写。

## Glossary

- **Bug_Condition (C)**: 触发 bug 的条件 — 源 MCP 配置使用 `mcpServers` 键名，或 server 配置中包含 `cwd` 字段
- **Property (P)**: 期望行为 — 正确读取 `mcpServers` 键名、正确写入 `mcpServers` 键名、`cwd` 被重写为统一仓库路径
- **Preservation**: 修复不应改变的行为 — 同名条目覆盖确认、无冲突追加、目标文件不存在时新建、原有条目保留不变、无 `cwd` 字段时不添加
- **`_sync_mcp()`**: `sync_cmd.py` 中负责读取源 MCP 配置并调用合并的函数
- **`_merge_mcp_config()`**: `sync_cmd.py` 中负责将 server 条目合并到目标 `mcp.json` 的函数
- **统一仓库路径**: `~/.msr-repos/MCP/<name>/V<n>/`，MCP 配置在统一仓库中的实际存储路径

## Bug Details

### Bug Condition

Bug 在以下两种情况下触发：

1. **键名不匹配**：源 MCP 配置文件使用标准 `mcpServers` 键名时，`_sync_mcp()` 使用 `source_data.get("servers", {})` 读取，返回空字典；`_merge_mcp_config()` 写入 `target_data["servers"]` 而非 `target_data["mcpServers"]`。
2. **cwd 路径未重写**：源 server 配置中包含 `cwd` 字段时，`_sync_mcp()` 直接传递原始路径，未重写为统一仓库中的实际路径。

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type { source_mcp_json: dict, server_configs: list[dict] }
  OUTPUT: boolean

  key_mismatch := "mcpServers" IN source_mcp_json.keys()
                  AND "servers" NOT IN source_mcp_json.keys()
  
  cwd_not_rewritten := ANY server_config IN server_configs
                       WHERE "cwd" IN server_config.keys()
                       AND server_config["cwd"] != expected_repo_path(mcp_name, version)

  RETURN key_mismatch OR cwd_not_rewritten
END FUNCTION
```

### Examples

- **键名不匹配 — 读取失败**: 源 `mcp.json` 内容为 `{"mcpServers": {"my-server": {"command": "node", "args": ["index.js"]}}}`，`_sync_mcp()` 调用 `source_data.get("servers", {})` 返回 `{}`，提示"没有 servers 条目"并跳过同步。期望行为：正确读取 `mcpServers` 下的 `my-server` 条目。
- **键名不匹配 — 写入错误**: 合并后目标 `mcp.json` 内容为 `{"servers": {"my-server": {...}}}`，IDE 无法识别。期望行为：写入为 `{"mcpServers": {"my-server": {...}}}`。
- **cwd 未重写**: 源 server 配置 `{"command": "node", "args": ["index.js"], "cwd": "/Users/someone/projects/my-mcp"}` 同步后 `cwd` 仍为 `/Users/someone/projects/my-mcp`。期望行为：`cwd` 被重写为 `~/.msr-repos/MCP/my-mcp/V1/`（展开后的绝对路径）。
- **无 cwd 字段**: 源 server 配置 `{"command": "npx", "args": ["-y", "some-tool"]}` 不含 `cwd`，同步后不应添加 `cwd` 字段。

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 同名 server 条目存在时，系统继续提示用户确认是否覆盖（`click.confirm`）
- 无冲突的 server 条目继续直接追加
- 目标 `mcp.json` 不存在时继续新建文件并写入
- 合并后目标文件中所有原有 server 条目保留且内容不变
- 源 server 配置中不包含 `cwd` 字段时，正常同步且不添加 `cwd`

**Scope:**
所有不涉及键名读写和 `cwd` 路径的行为不受此修复影响。包括：
- Rules 和 Skills 的同步逻辑
- MCP 配置的导入（import）逻辑
- 版本管理逻辑
- IDE 适配器路径解析逻辑

## Hypothesized Root Cause

基于代码分析，两个 bug 的根因明确：

1. **键名硬编码为 `servers`**：
   - `_sync_mcp()` 第 193 行：`source_servers = source_data.get("servers", {})` — 应为 `source_data.get("mcpServers", {})`
   - `_merge_mcp_config()` 第 224 行：`if "servers" not in target_data:` — 应为 `if "mcpServers" not in target_data:`
   - `_merge_mcp_config()` 第 225 行：`target_data["servers"] = {}` — 应为 `target_data["mcpServers"] = {}`
   - `_merge_mcp_config()` 中所有 `target_data["servers"]` 引用 — 应改为 `target_data["mcpServers"]`

2. **缺少 cwd 路径重写逻辑**：
   - `_sync_mcp()` 在读取 `source_servers` 后直接传递给 `_merge_mcp_config()`，未对 server 配置中的 `cwd` 字段进行路径重写
   - 需要在传递前遍历 `source_servers`，将含有 `cwd` 的 server 配置的 `cwd` 值替换为 `source_dir`（即 `~/.msr-repos/MCP/<name>/V<n>/`）的绝对路径

3. **测试也使用了错误键名**：
   - `test_mcp_merge.py` 中的属性测试使用 `{"servers": ...}` 构造测试数据和断言，需同步更新为 `{"mcpServers": ...}`

## Correctness Properties

Property 1: Bug Condition - mcpServers 键名正确读写

_For any_ 源 MCP 配置使用 `mcpServers` 作为键名且包含至少一个 server 条目时，修复后的 `_sync_mcp()` SHALL 正确读取所有 server 条目，且 `_merge_mcp_config()` SHALL 将条目写入目标 JSON 的 `mcpServers` 键下，生成符合标准 MCP 格式的配置文件。

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition - cwd 路径重写

_For any_ 源 MCP server 配置中包含 `cwd` 字段时，修复后的 `_sync_mcp()` SHALL 将 `cwd` 值重写为该 MCP 配置在统一仓库中的实际路径（`~/.msr-repos/MCP/<name>/V<n>/` 的展开绝对路径），确保 MCP server 启动时能找到正确的工作目录。

**Validates: Requirements 2.3**

Property 3: Preservation - 合并行为与原有条目保留

_For any_ 不涉及键名读写和 cwd 路径的输入（无冲突追加、同名覆盖确认、目标文件新建、无 cwd 字段的 server 配置），修复后的函数 SHALL 产生与修复前相同的行为，保留所有原有 server 条目且内容不变，不对无 cwd 字段的 server 配置添加 cwd。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

假设根因分析正确：

**File**: `MSR-cli/msr_sync/commands/sync_cmd.py`

**Function**: `_sync_mcp()`

**Specific Changes**:
1. **修复键名读取**: 将 `source_data.get("servers", {})` 改为 `source_data.get("mcpServers", {})`
2. **修复提示信息**: 将"没有 servers 条目"改为"没有 mcpServers 条目"
3. **添加 cwd 路径重写**: 在获取 `source_servers` 后、调用 `_merge_mcp_config()` 前，遍历所有 server 配置，若含有 `cwd` 字段则将其值替换为 `str(source_dir)`（即统一仓库中该版本的绝对路径）

**Function**: `_merge_mcp_config()`

**Specific Changes**:
4. **修复键名写入**: 将所有 `target_data["servers"]` 替换为 `target_data["mcpServers"]`
5. **修复键名检查**: 将 `if "servers" not in target_data:` 改为 `if "mcpServers" not in target_data:`

**File**: `MSR-cli/tests/test_mcp_merge.py`

**Specific Changes**:
6. **更新测试数据键名**: 将测试中构造的 `{"servers": ...}` 改为 `{"mcpServers": ...}`
7. **更新断言键名**: 将断言中的 `result_data["servers"]` 和 `result_data.get("servers", {})` 改为 `result_data["mcpServers"]` 和 `result_data.get("mcpServers", {})`

## Testing Strategy

### Validation Approach

测试策略分两阶段：先在未修复代码上运行探索性测试以确认 bug 存在，再在修复后验证正确性和行为保留。

### Exploratory Bug Condition Checking

**Goal**: 在实施修复前，通过测试确认 bug 的存在和根因。

**Test Plan**: 编写测试用例，构造使用 `mcpServers` 键名的源 MCP 配置和包含 `cwd` 字段的 server 配置，在未修复代码上运行以观察失败。

**Test Cases**:
1. **mcpServers 键名读取测试**: 构造 `{"mcpServers": {"test-server": {"command": "node"}}}` 的源配置，调用 `_sync_mcp()`，验证是否正确读取（未修复代码将失败）
2. **mcpServers 键名写入测试**: 调用 `_merge_mcp_config()` 后检查目标 JSON 是否使用 `mcpServers` 键名（未修复代码将写入 `servers`）
3. **cwd 路径重写测试**: 构造含 `cwd` 字段的 server 配置，验证同步后 `cwd` 是否被重写（未修复代码将保留原始路径）

**Expected Counterexamples**:
- `_sync_mcp()` 对 `mcpServers` 键名的配置返回 0（跳过同步）
- 目标 JSON 中使用 `servers` 而非 `mcpServers` 键名
- `cwd` 字段保留原始路径而非统一仓库路径

### Fix Checking

**Goal**: 验证对所有满足 bug 条件的输入，修复后的函数产生期望行为。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := _sync_mcp_fixed(input)
  ASSERT result.target_json uses "mcpServers" key
  ASSERT result.servers_read == source_mcpServers_count
  IF server_config HAS "cwd" THEN
    ASSERT result.server_config["cwd"] == str(source_dir)
  END IF
END FOR
```

### Preservation Checking

**Goal**: 验证对所有不满足 bug 条件的输入，修复后的函数与原函数行为一致。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT _merge_mcp_config_original(input) = _merge_mcp_config_fixed(input)
END FOR
```

**Testing Approach**: 推荐使用属性测试（Property-Based Testing）进行保留性验证，因为：
- 自动生成大量测试用例覆盖输入域
- 捕获手动单元测试可能遗漏的边界情况
- 对非 bug 输入的行为不变提供强保证

**Test Plan**: 先在未修复代码上观察非 bug 输入（无冲突追加、无 cwd 字段的 server 配置）的行为，再编写属性测试捕获该行为。

**Test Cases**:
1. **无冲突追加保留**: 验证不冲突的 server 条目在修复后仍被正确追加
2. **原有条目保留**: 验证目标文件中原有的 server 条目在合并后内容不变
3. **无 cwd 字段保留**: 验证不含 `cwd` 的 server 配置同步后不会被添加 `cwd` 字段
4. **目标文件新建保留**: 验证目标 `mcp.json` 不存在时仍能正确新建

### Unit Tests

- 测试 `_sync_mcp()` 正确读取 `mcpServers` 键名的源配置
- 测试 `_merge_mcp_config()` 输出使用 `mcpServers` 键名
- 测试 `cwd` 路径重写为 `source_dir` 绝对路径
- 测试无 `cwd` 字段时不添加 `cwd`
- 测试同名条目覆盖确认流程不受影响

### Property-Based Tests

- 生成随机合法 MCP server 配置（含/不含 `cwd`），验证键名始终为 `mcpServers`
- 生成随机不冲突的 existing + new server 集合，验证合并后所有条目保留且内容不变（更新现有 `test_mcp_merge.py` 中的属性测试）
- 生成随机 `cwd` 路径值，验证重写后的路径符合 `~/.msr-repos/MCP/<name>/V<n>/` 格式

### Integration Tests

- 端到端测试：从仓库中读取使用 `mcpServers` 键名的 MCP 配置，同步到目标 IDE，验证目标 `mcp.json` 格式正确
- 测试含 `cwd` 的 MCP 配置完整同步流程，验证目标中 `cwd` 指向统一仓库路径
- 测试多个 MCP 配置连续同步，验证目标文件累积合并正确
