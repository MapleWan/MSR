"""Preservation Property Tests — 合并行为与原有条目保留

验证 _merge_mcp_config() 的核心合并行为在修复前后保持一致：
1. 无冲突追加：所有新条目被添加，所有原有条目保留且内容不变
2. 无 cwd 字段保留：不含 cwd 的 server 配置同步后不会被添加 cwd
3. 目标文件新建：目标不存在时正确创建文件并写入

这些测试直接调用 _merge_mcp_config() 并传入 server 字典，
在函数接口层面是键名无关的（key-agnostic），因此在修复前后均应通过。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
"""

import json
import tempfile
from pathlib import Path

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from msr_sync.commands.sync_cmd import _merge_mcp_config


# ============================================================
# 复用 test_mcp_merge.py 中的 Hypothesis 策略
# ============================================================

from tests.test_mcp_merge import _server_name_st, _server_config_st


# 生成不含 cwd 字段的 server 配置
_server_config_no_cwd_st = st.fixed_dictionaries(
    {
        "command": st.sampled_from(["node", "python", "npx", "uvx", "deno"]),
        "args": st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet="abcdefghijklmnopqrstuvwxyz0123456789-./",
            ),
            min_size=0,
            max_size=3,
        ),
    },
    optional={
        "env": st.dictionaries(
            keys=st.from_regex(r"[A-Z_]{1,10}", fullmatch=True),
            values=st.text(min_size=1, max_size=20),
            min_size=0,
            max_size=3,
        )
    },
)

# 生成 servers 字典（不含 cwd）
_servers_dict_no_cwd_st = st.dictionaries(
    keys=_server_name_st,
    values=_server_config_no_cwd_st,
    min_size=0,
    max_size=5,
)


def _get_servers_from_file(target_path: Path) -> dict:
    """从目标 mcp.json 中读取 server 条目，兼容 servers 和 mcpServers 键名。

    这使得测试在修复前（使用 servers 键）和修复后（使用 mcpServers 键）
    均能正确读取结果。
    """
    data = json.loads(target_path.read_text(encoding="utf-8"))
    return data.get("mcpServers", data.get("servers", {}))


def _write_target_with_existing(target_path: Path, existing_servers: dict) -> None:
    """写入包含已有条目的目标 mcp.json。

    使用 mcpServers 键名（匹配修复后代码），确保 _merge_mcp_config()
    能正确读取已有条目并进行合并。
    """
    target_data = {"mcpServers": dict(existing_servers)}
    target_path.write_text(
        json.dumps(target_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ============================================================
# Property 2a: 无冲突追加 — 合并后所有条目保留且内容不变
# ============================================================


# Feature: mcp-sync-fix, Property 2a: 无冲突追加保留
# **Validates: Requirements 3.2, 3.4**
@settings(max_examples=100)
@given(
    existing_servers=_servers_dict_no_cwd_st,
    new_servers=_servers_dict_no_cwd_st,
)
def test_merge_preserves_all_entries_on_non_conflicting_append(
    existing_servers: dict,
    new_servers: dict,
) -> None:
    """Property 2a: 对所有无冲突的 existing + new server 集合，
    _merge_mcp_config() 返回 len(new_servers)，
    结果包含所有原有条目（内容不变）和所有新条目，
    总数 = existing + new。

    **Validates: Requirements 3.2, 3.4**
    """
    # 确保新条目名称与已有条目不冲突
    assume(not set(existing_servers.keys()) & set(new_servers.keys()))

    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = Path(tmp_dir) / "mcp.json"

        # 创建目标 mcp.json（已有条目）
        if existing_servers:
            _write_target_with_existing(target_path, existing_servers)

        # 执行合并（不冲突，不会触发 click.confirm）
        synced = _merge_mcp_config(
            source_servers=new_servers,
            target_path=target_path,
            ide_name="test_ide",
        )

        # 验证：成功同步的数量等于新条目数量
        assert synced == len(new_servers), (
            f"synced 应为 {len(new_servers)}，但实际为 {synced}"
        )

        if not existing_servers and not new_servers:
            # 两者都为空时，不会写入文件
            return

        if not new_servers:
            # 没有新条目时，文件不应被修改
            if existing_servers:
                result_servers = _get_servers_from_file(target_path)
                assert result_servers == existing_servers
            return

        # 读取合并后的结果
        assert target_path.is_file(), "合并后目标文件应存在"
        result_servers = _get_servers_from_file(target_path)

        # 验证：所有原有条目仍然存在且内容不变
        for name, config in existing_servers.items():
            assert name in result_servers, f"原有条目 '{name}' 应保留在合并结果中"
            assert result_servers[name] == config, (
                f"原有条目 '{name}' 的内容不应被修改"
            )

        # 验证：所有新条目都已添加
        for name, config in new_servers.items():
            assert name in result_servers, f"新条目 '{name}' 应出现在合并结果中"
            assert result_servers[name] == config, (
                f"新条目 '{name}' 的内容应与源一致"
            )

        # 验证：合并后的条目总数等于原有 + 新增
        assert len(result_servers) == len(existing_servers) + len(new_servers), (
            f"总条目数应为 {len(existing_servers) + len(new_servers)}，"
            f"但实际为 {len(result_servers)}"
        )


# ============================================================
# Property 2b: 无 cwd 字段保留 — 不含 cwd 的配置同步后不添加 cwd
# ============================================================


# Feature: mcp-sync-fix, Property 2b: 无 cwd 字段保留
# **Validates: Requirements 3.5**
@settings(max_examples=100)
@given(
    new_servers=_servers_dict_no_cwd_st,
)
def test_merge_does_not_add_cwd_when_absent(
    new_servers: dict,
) -> None:
    """Property 2b: 对所有不含 cwd 字段的 server 配置，
    经过 _merge_mcp_config() 合并后，结果中不应出现 cwd 字段。

    **Validates: Requirements 3.5**
    """
    assume(len(new_servers) > 0)

    # 确认输入中确实没有 cwd 字段
    for config in new_servers.values():
        assert "cwd" not in config, "测试前提：输入 server 配置不应含 cwd"

    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = Path(tmp_dir) / "mcp.json"

        # 执行合并（目标不存在，新建）
        synced = _merge_mcp_config(
            source_servers=new_servers,
            target_path=target_path,
            ide_name="test_ide",
        )

        assert synced == len(new_servers)

        # 读取合并后的结果
        assert target_path.is_file(), "合并后目标文件应存在"
        result_servers = _get_servers_from_file(target_path)

        # 验证：所有 server 配置中不应出现 cwd 字段
        for name, config in result_servers.items():
            assert "cwd" not in config, (
                f"server '{name}' 不应含 cwd 字段，"
                f"但实际配置为: {config}"
            )


# ============================================================
# Property 2c: 目标文件新建 — 目标不存在时正确创建
# ============================================================


# Feature: mcp-sync-fix, Property 2c: 目标文件新建
# **Validates: Requirements 3.3**
@settings(max_examples=100)
@given(
    new_servers=_servers_dict_no_cwd_st,
)
def test_merge_creates_target_when_not_exists(
    new_servers: dict,
) -> None:
    """Property 2c: 当目标 mcp.json 不存在时，
    _merge_mcp_config() 应正确创建文件并写入所有条目。

    **Validates: Requirements 3.3**
    """
    assume(len(new_servers) > 0)

    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = Path(tmp_dir) / "mcp.json"

        # 确认目标文件不存在
        assert not target_path.exists(), "测试前提：目标文件不应存在"

        # 执行合并
        synced = _merge_mcp_config(
            source_servers=new_servers,
            target_path=target_path,
            ide_name="test_ide",
        )

        # 验证：返回值等于新条目数
        assert synced == len(new_servers), (
            f"synced 应为 {len(new_servers)}，但实际为 {synced}"
        )

        # 验证：目标文件被创建
        assert target_path.is_file(), "目标 mcp.json 应被创建"

        # 验证：文件内容是合法 JSON
        target_data = json.loads(target_path.read_text(encoding="utf-8"))
        assert isinstance(target_data, dict), "目标文件应为 JSON 对象"

        # 验证：所有新条目都已写入
        result_servers = _get_servers_from_file(target_path)
        for name, config in new_servers.items():
            assert name in result_servers, f"新条目 '{name}' 应出现在新建的文件中"
            assert result_servers[name] == config, (
                f"新条目 '{name}' 的内容应与源一致"
            )

        # 验证：条目总数正确
        assert len(result_servers) == len(new_servers), (
            f"新建文件中的条目数应为 {len(new_servers)}，"
            f"但实际为 {len(result_servers)}"
        )
