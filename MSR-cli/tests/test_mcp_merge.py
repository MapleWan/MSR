"""MCP 合并属性测试 — Property 8: MCP JSON 合并保留已有条目

验证对任意合法 mcp.json 和不冲突的新 MCP 条目，合并后同时包含所有原有条目和新条目，
原有条目内容不变。
"""

import json
import tempfile
from pathlib import Path

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from msr_sync.commands.sync_cmd import _merge_mcp_config


# ============================================================
# Hypothesis 策略：生成合法的 MCP server 配置
# ============================================================

# 生成合法的 server 名称（非空字母数字字符串）
_server_name_st = st.from_regex(r"[a-z][a-z0-9\-]{0,19}", fullmatch=True)

# 生成合法的 server 配置值
_server_config_st = st.fixed_dictionaries(
    {
        "command": st.sampled_from(["node", "python", "npx", "uvx", "deno"]),
        "args": st.lists(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-./"), min_size=0, max_size=3),
    },
    optional={"env": st.dictionaries(
        keys=st.from_regex(r"[A-Z_]{1,10}", fullmatch=True),
        values=st.text(min_size=1, max_size=20),
        min_size=0,
        max_size=3,
    )},
)

# 生成合法的 servers 字典
_servers_dict_st = st.dictionaries(
    keys=_server_name_st,
    values=_server_config_st,
    min_size=0,
    max_size=5,
)


# ============================================================
# Property 8: MCP JSON 合并保留已有条目
# ============================================================


# Feature: msr-cli, Property 8: MCP JSON 合并保留已有条目
# **Validates: Requirements 6.2**
@settings(max_examples=100)
@given(
    existing_servers=_servers_dict_st,
    new_servers=_servers_dict_st,
)
def test_mcp_merge_preserves_existing_entries(
    existing_servers: dict,
    new_servers: dict,
) -> None:
    """Property 8: 对任意合法 mcp.json 和不冲突的新 MCP 条目，
    合并后同时包含所有原有条目和新条目，原有条目内容不变。

    **Validates: Requirements 6.2**
    """
    # 确保新条目名称与已有条目不冲突
    assume(not set(existing_servers.keys()) & set(new_servers.keys()))

    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = Path(tmp_dir) / "mcp.json"

        # 创建目标 mcp.json（已有条目）
        if existing_servers:
            target_data = {"mcpServers": dict(existing_servers)}
            target_path.write_text(
                json.dumps(target_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        # 执行合并（不冲突，不会触发 click.confirm）
        synced = _merge_mcp_config(
            source_servers=new_servers,
            target_path=target_path,
            ide_name="test_ide",
        )

        # 验证：成功同步的数量等于新条目数量
        assert synced == len(new_servers)

        if not existing_servers and not new_servers:
            # 两者都为空时，不会写入文件
            return

        if not new_servers:
            # 没有新条目时，文件不应被修改（如果原来存在的话）
            if existing_servers:
                result_data = json.loads(target_path.read_text(encoding="utf-8"))
                assert result_data["mcpServers"] == existing_servers
            return

        # 读取合并后的结果
        assert target_path.is_file(), "合并后目标文件应存在"
        result_data = json.loads(target_path.read_text(encoding="utf-8"))
        result_servers = result_data.get("mcpServers", {})

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
        assert len(result_servers) == len(existing_servers) + len(new_servers)
