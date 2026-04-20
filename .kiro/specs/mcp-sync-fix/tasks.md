# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - mcpServers 键名与 cwd 路径重写
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate both bugs exist
  - **Scoped PBT Approach**: Scope the property to concrete failing cases for reproducibility
  - **Bug Condition from design**:
    - `isBugCondition(input)` returns true when:
      - `"mcpServers" IN source_mcp_json.keys() AND "servers" NOT IN source_mcp_json.keys()` (键名不匹配)
      - OR `ANY server_config WHERE "cwd" IN server_config.keys() AND server_config["cwd"] != expected_repo_path` (cwd 未重写)
  - **Test implementation details**:
    - Test 1a (键名读取): Construct source `mcp.json` with `{"mcpServers": {"test-server": {"command": "node", "args": ["index.js"]}}}`, set up a mock repo with this file, call `_sync_mcp()`, assert it returns 1 (successful sync) and target JSON uses `mcpServers` key. On UNFIXED code: `_sync_mcp()` reads `source_data.get("servers", {})` which returns `{}`, so it returns 0 and prints warning.
    - Test 1b (键名写入): Call `_merge_mcp_config()` with server configs, read target JSON, assert top-level key is `mcpServers` not `servers`. On UNFIXED code: writes to `target_data["servers"]`.
    - Test 1c (cwd 重写): Construct source server config with `"cwd": "/Users/someone/projects/my-mcp"`, call `_sync_mcp()`, assert target server config `cwd` equals `str(source_dir)` (the repo path `~/.msr-repos/MCP/<name>/V<n>/`). On UNFIXED code: `cwd` remains as original path.
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bugs exist)
  - Document counterexamples found to understand root cause
  - Mark task complete when tests are written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - 合并行为与原有条目保留
  - **IMPORTANT**: Follow observation-first methodology
  - **Observation targets** (run on UNFIXED code with non-bug-condition inputs):
    - Observe: `_merge_mcp_config({"s1": {"command": "node"}}, target_path, "test")` with empty target → creates file with all entries, returns count of new entries
    - Observe: `_merge_mcp_config(new_servers, target_path, "test")` with existing non-conflicting entries → appends new entries, preserves all existing entries unchanged
    - Observe: server configs without `cwd` field → synced as-is, no `cwd` added
  - **Property-based test details**:
    - Generate random valid MCP server configs (reuse existing `_server_name_st`, `_server_config_st` strategies from `test_mcp_merge.py`)
    - Property: for all non-conflicting existing + new server sets, `_merge_mcp_config()` returns `len(new_servers)`, result contains all existing entries unchanged, result contains all new entries, total count = existing + new
    - Property: for all server configs without `cwd` field, after merge no `cwd` field is added
    - Property: when target file does not exist, merge creates it correctly
  - **NOTE**: The existing `test_mcp_merge.py` uses `servers` key (matching current buggy code). The preservation test here should test `_merge_mcp_config()` directly with server dicts (which is key-agnostic at the function interface level), so it works on both unfixed and fixed code.
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for mcpServers 键名不匹配与 cwd 路径未重写

  - [x] 3.1 Fix key name reading in `_sync_mcp()`: `servers` → `mcpServers`
    - In `MSR-cli/msr_sync/commands/sync_cmd.py`, function `_sync_mcp()`
    - Change `source_data.get("servers", {})` to `source_data.get("mcpServers", {})`
    - Change warning message from `"没有 servers 条目"` to `"没有 mcpServers 条目"`
    - _Bug_Condition: isBugCondition(input) where "mcpServers" IN source_mcp_json.keys() AND "servers" NOT IN source_mcp_json.keys()_
    - _Expected_Behavior: _sync_mcp() correctly reads server entries from mcpServers key_
    - _Preservation: Reading logic change does not affect merge behavior for non-bug inputs_
    - _Requirements: 1.1, 2.1_

  - [x] 3.2 Add cwd path rewriting logic in `_sync_mcp()`
    - In `MSR-cli/msr_sync/commands/sync_cmd.py`, function `_sync_mcp()`
    - After reading `source_servers` and before calling `_merge_mcp_config()`, iterate over all server configs
    - For each server config that contains a `cwd` key, replace its value with `str(source_dir)` (the resolved repo path `~/.msr-repos/MCP/<name>/V<n>/`)
    - Do NOT add `cwd` to server configs that don't have it
    - _Bug_Condition: isBugCondition(input) where "cwd" IN server_config.keys() AND server_config["cwd"] != expected_repo_path_
    - _Expected_Behavior: cwd is rewritten to str(source_dir) for all server configs containing cwd_
    - _Preservation: Server configs without cwd field are not modified_
    - _Requirements: 1.3, 2.3, 3.5_

  - [x] 3.3 Fix key name writing in `_merge_mcp_config()`: `servers` → `mcpServers`
    - In `MSR-cli/msr_sync/commands/sync_cmd.py`, function `_merge_mcp_config()`
    - Change `if "servers" not in target_data:` to `if "mcpServers" not in target_data:`
    - Change `target_data["servers"] = {}` to `target_data["mcpServers"] = {}`
    - Change all `target_data["servers"]` references to `target_data["mcpServers"]`
    - _Bug_Condition: target JSON uses "servers" key instead of standard "mcpServers"_
    - _Expected_Behavior: _merge_mcp_config() writes all entries under mcpServers key_
    - _Preservation: Merge logic (conflict detection, append, overwrite confirm) unchanged_
    - _Requirements: 1.2, 2.2_

  - [x] 3.4 Update existing test `test_mcp_merge.py` to use `mcpServers` key name
    - In `MSR-cli/tests/test_mcp_merge.py`
    - Change test data construction from `{"servers": dict(existing_servers)}` to `{"mcpServers": dict(existing_servers)}`
    - Change all assertions from `result_data["servers"]` / `result_data.get("servers", {})` to `result_data["mcpServers"]` / `result_data.get("mcpServers", {})`
    - _Requirements: 2.1, 2.2_

  - [x] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - mcpServers 键名与 cwd 路径重写
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied:
      - `_sync_mcp()` correctly reads `mcpServers` key
      - `_merge_mcp_config()` writes entries under `mcpServers` key
      - `cwd` field is rewritten to `str(source_dir)`
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bugs are fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - 合并行为与原有条目保留
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest MSR-cli/tests/test_mcp_merge.py` and the new bug condition / preservation tests
  - Ensure all tests pass, ask the user if questions arise
  - Verify no regressions in other test files by running `pytest MSR-cli/tests/`
