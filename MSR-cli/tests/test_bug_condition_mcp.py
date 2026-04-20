"""Bug Condition Exploration Tests — MCP 同步键名与 cwd 路径重写

验证三个 bug 条件在未修复代码上的存在性：
1. _sync_mcp() 使用 "servers" 键名读取，无法识别标准 "mcpServers" 键名
2. _merge_mcp_config() 写入 "servers" 而非标准 "mcpServers" 键名
3. _sync_mcp() 未将 server 配置中的 cwd 字段重写为统一仓库路径

**Validates: Requirements 1.1, 1.2, 1.3**
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from msr_sync.commands.sync_cmd import _sync_mcp, _merge_mcp_config
from msr_sync.constants import MCP_CONFIG_FILE
from msr_sync.core.repository import Repository


def _create_mock_repo_and_adapter(tmp_path: Path, mcp_name: str, mcp_data: dict):
    """创建模拟的仓库结构和 adapter，用于测试 _sync_mcp()。

    在 tmp_path 下构建：
      .msr-repos/MCP/<mcp_name>/V1/mcp.json

    返回 (repo, adapter, target_mcp_path, source_dir)
    """
    # 构建仓库目录结构
    repo_base = tmp_path / ".msr-repos"
    for sub in ["RULES", "SKILLS", "MCP"]:
        (repo_base / sub).mkdir(parents=True, exist_ok=True)

    # 创建 MCP 配置版本目录
    mcp_version_dir = repo_base / "MCP" / mcp_name / "V1"
    mcp_version_dir.mkdir(parents=True, exist_ok=True)

    # 写入源 mcp.json
    source_mcp_file = mcp_version_dir / MCP_CONFIG_FILE
    source_mcp_file.write_text(
        json.dumps(mcp_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 创建 Repository 实例
    repo = Repository(base_path=repo_base)

    # 创建目标 mcp.json 路径
    target_dir = tmp_path / "target_ide"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_mcp_path = target_dir / "mcp.json"

    # 创建 mock adapter
    adapter = MagicMock()
    adapter.ide_name = "test_ide"
    adapter.get_mcp_path.return_value = target_mcp_path

    return repo, adapter, target_mcp_path, mcp_version_dir


class TestBugConditionKeyRead:
    """Test 1a: 键名读取 — _sync_mcp() 应正确读取 mcpServers 键名

    Bug: _sync_mcp() 使用 source_data.get("servers", {}) 读取源配置，
    当源配置使用标准 mcpServers 键名时返回空字典，导致返回 0 并跳过同步。

    **Validates: Requirements 1.1**
    """

    def test_sync_mcp_reads_mcpServers_key(self, tmp_path: Path) -> None:
        """构造使用 mcpServers 键名的源配置，验证 _sync_mcp() 能正确读取。

        期望行为：_sync_mcp() 返回 1（成功同步 1 个条目）
        未修复代码：_sync_mcp() 返回 0（读取 "servers" 键得到空字典）
        """
        source_data = {
            "mcpServers": {
                "test-server": {
                    "command": "node",
                    "args": ["index.js"],
                }
            }
        }

        repo, adapter, target_mcp_path, source_dir = _create_mock_repo_and_adapter(
            tmp_path, "test-mcp", source_data
        )

        # 调用 _sync_mcp()
        result = _sync_mcp(
            repo=repo,
            adapter=adapter,
            mcp_name="test-mcp",
            version="V1",
            resolved_version="V1",
        )

        # 期望：成功同步 1 个条目
        assert result == 1, (
            f"_sync_mcp() 应返回 1（成功同步），但返回了 {result}。"
            "这说明 _sync_mcp() 未能正确读取 mcpServers 键名。"
        )

        # 期望：目标文件存在且使用 mcpServers 键名
        assert target_mcp_path.is_file(), "目标 mcp.json 应被创建"
        target_data = json.loads(target_mcp_path.read_text(encoding="utf-8"))
        assert "mcpServers" in target_data, (
            "目标 mcp.json 应使用 mcpServers 键名，"
            f"但实际键为: {list(target_data.keys())}"
        )


class TestBugConditionKeyWrite:
    """Test 1b: 键名写入 — _merge_mcp_config() 应使用 mcpServers 键名写入

    Bug: _merge_mcp_config() 写入 target_data["servers"] 而非 target_data["mcpServers"]，
    生成的配置文件不符合标准 MCP 格式。

    **Validates: Requirements 1.2**
    """

    def test_merge_mcp_config_writes_mcpServers_key(self, tmp_path: Path) -> None:
        """调用 _merge_mcp_config() 后，验证目标 JSON 使用 mcpServers 键名。

        期望行为：目标 JSON 顶层键为 mcpServers
        未修复代码：目标 JSON 顶层键为 servers
        """
        target_path = tmp_path / "mcp.json"

        source_servers = {
            "my-server": {
                "command": "node",
                "args": ["index.js"],
            }
        }

        # 调用 _merge_mcp_config()
        synced = _merge_mcp_config(
            source_servers=source_servers,
            target_path=target_path,
            ide_name="test_ide",
        )

        assert synced == 1, f"应成功同步 1 个条目，但返回了 {synced}"

        # 读取目标文件
        assert target_path.is_file(), "目标 mcp.json 应被创建"
        target_data = json.loads(target_path.read_text(encoding="utf-8"))

        # 期望：顶层键为 mcpServers，而非 servers
        assert "mcpServers" in target_data, (
            f"目标 mcp.json 应使用 mcpServers 键名，"
            f"但实际键为: {list(target_data.keys())}。"
            "这说明 _merge_mcp_config() 使用了错误的 servers 键名。"
        )
        assert "servers" not in target_data, (
            "目标 mcp.json 不应包含 servers 键名（应为 mcpServers）"
        )

        # 验证内容正确
        assert "my-server" in target_data["mcpServers"]
        assert target_data["mcpServers"]["my-server"]["command"] == "node"


class TestBugConditionCwdRewrite:
    """Test 1c: cwd 重写 — _sync_mcp() 应将 cwd 重写为统一仓库路径

    Bug: _sync_mcp() 直接传递原始 cwd 路径，未将其重写为
    统一仓库中的实际路径（~/.msr-repos/MCP/<name>/V<n>/）。

    **Validates: Requirements 1.3**
    """

    def test_sync_mcp_rewrites_cwd_to_repo_path(self, tmp_path: Path) -> None:
        """构造含 cwd 字段的源配置，验证同步后 cwd 被重写为 source_dir 路径。

        期望行为：目标 server 配置的 cwd 等于 str(source_dir)
        未修复代码：cwd 保留原始路径 "/Users/someone/projects/my-mcp"
        """
        original_cwd = "/Users/someone/projects/my-mcp"
        source_data = {
            "mcpServers": {
                "cwd-server": {
                    "command": "node",
                    "args": ["index.js"],
                    "cwd": original_cwd,
                }
            }
        }

        repo, adapter, target_mcp_path, source_dir = _create_mock_repo_and_adapter(
            tmp_path, "my-mcp", source_data
        )

        # 调用 _sync_mcp()
        result = _sync_mcp(
            repo=repo,
            adapter=adapter,
            mcp_name="my-mcp",
            version="V1",
            resolved_version="V1",
        )

        # 首先需要成功同步（如果键名 bug 也存在，这里可能返回 0）
        # 但我们主要关注 cwd 重写
        if result == 0:
            pytest.fail(
                "_sync_mcp() 返回 0（未同步任何条目），"
                "可能是因为键名读取 bug 导致无法读取 mcpServers。"
                "cwd 重写 bug 无法单独验证。"
            )

        # 读取目标文件
        assert target_mcp_path.is_file(), "目标 mcp.json 应被创建"
        target_data = json.loads(target_mcp_path.read_text(encoding="utf-8"))

        # 获取 server 配置（兼容 mcpServers 或 servers 键名）
        servers = target_data.get("mcpServers", target_data.get("servers", {}))
        assert "cwd-server" in servers, "目标应包含 cwd-server 条目"

        target_cwd = servers["cwd-server"].get("cwd")
        expected_cwd = str(source_dir)

        assert target_cwd == expected_cwd, (
            f"cwd 应被重写为统一仓库路径 '{expected_cwd}'，"
            f"但实际值为 '{target_cwd}'。"
            "这说明 _sync_mcp() 未对 cwd 字段进行路径重写。"
        )

        # 确保 cwd 不再是原始路径
        assert target_cwd != original_cwd, (
            f"cwd 不应保留原始路径 '{original_cwd}'"
        )
