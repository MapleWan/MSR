"""CLI 集成测试 — 通过 click.testing.CliRunner 测试 CLI 命令

使用 monkeypatch 将 Path.home() 重定向到临时目录，
使 ~/.msr-repos 解析到测试位置，实现完整的 CLI 集成测试。
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from msr_sync.cli import main
from msr_sync.core.repository import Repository


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """将 Path.home() 重定向到临时目录，使 ~/.msr-repos 解析到测试位置。"""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


@pytest.fixture
def initialized_home(fake_home):
    """在 fake_home 下创建已初始化的仓库。"""
    repo = Repository()  # 使用默认路径，即 fake_home / .msr-repos
    repo.init()
    return fake_home


# ============================================================
# Test 1: msr-sync init 创建仓库 (Req 1.1)
# ============================================================


class TestInitCommand:
    """init 命令集成测试"""

    def test_init_creates_repo(self, fake_home):
        """msr-sync init 应创建统一仓库目录结构 (Req 1.1)"""
        runner = CliRunner()
        result = runner.invoke(main, ["init"])

        assert result.exit_code == 0
        assert "✅ 统一仓库已创建" in result.output

        repo_path = fake_home / ".msr-repos"
        assert (repo_path / "RULES").is_dir()
        assert (repo_path / "SKILLS").is_dir()
        assert (repo_path / "MCP").is_dir()

    def test_init_existing_repo_shows_skip(self, initialized_home):
        """msr-sync init 在已有仓库时应显示跳过信息 (Req 1.2)"""
        runner = CliRunner()
        result = runner.invoke(main, ["init"])

        assert result.exit_code == 0
        assert "统一仓库已初始化，跳过创建" in result.output


# ============================================================
# Test 2: msr-sync list 测试 (Req 9.1, 9.2, 9.3)
# ============================================================


class TestListCommand:
    """list 命令集成测试"""

    def test_list_uninitialized_repo_shows_error(self, fake_home):
        """msr-sync list 在未初始化仓库时应显示错误 (Req 9.1)"""
        runner = CliRunner()
        result = runner.invoke(main, ["list"])

        assert result.exit_code == 1
        assert "统一仓库未初始化" in result.output

    def test_list_shows_tree_format(self, initialized_home):
        """msr-sync list 应以树形结构展示配置 (Req 9.1, 9.3)"""
        repo = Repository()
        repo.store_rule("my-rule", "# My Rule")
        repo.store_rule("my-rule", "# My Rule V2")
        repo.store_rule("other-rule", "# Other Rule")

        runner = CliRunner()
        result = runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "统一仓库配置列表" in result.output
        assert "rules" in result.output
        assert "my-rule" in result.output
        assert "V1" in result.output
        assert "V2" in result.output
        assert "other-rule" in result.output
        # 验证树形结构字符
        assert "├── " in result.output or "└── " in result.output

    def test_list_type_filter(self, initialized_home):
        """msr-sync list --type rules 应只显示 rules 类型 (Req 9.2)"""
        repo = Repository()
        repo.store_rule("my-rule", "# My Rule")

        # 创建一个 skill
        skill_dir = initialized_home / "temp-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")
        repo.store_skill("my-skill", skill_dir)

        runner = CliRunner()
        result = runner.invoke(main, ["list", "--type", "rules"])

        assert result.exit_code == 0
        assert "my-rule" in result.output
        assert "my-skill" not in result.output


# ============================================================
# Test 3: msr-sync remove 测试 (Req 10.1, 10.2)
# ============================================================


class TestRemoveCommand:
    """remove 命令集成测试"""

    def test_remove_success(self, initialized_home):
        """msr-sync remove rules my-rule V1 应成功删除 (Req 10.1)"""
        repo = Repository()
        repo.store_rule("my-rule", "# My Rule")

        runner = CliRunner()
        result = runner.invoke(main, ["remove", "rules", "my-rule", "V1"])

        assert result.exit_code == 0
        assert "✅ 已删除配置: rules/my-rule/V1" in result.output
        repo_path = initialized_home / ".msr-repos"
        assert not (repo_path / "RULES" / "my-rule" / "V1").exists()

    def test_remove_nonexistent_shows_error(self, initialized_home):
        """msr-sync remove rules nonexistent V1 应显示错误 (Req 10.2)"""
        runner = CliRunner()
        result = runner.invoke(main, ["remove", "rules", "nonexistent", "V1"])

        assert result.exit_code == 1
        assert "未找到指定的配置版本" in result.output


# ============================================================
# Test 4: msr-sync sync --help 参数验证 (Req 8.1-8.7)
# ============================================================


class TestSyncCommand:
    """sync 命令集成测试"""

    def test_sync_help_shows_all_parameters(self):
        """msr-sync sync --help 应显示所有参数 (Req 8.1-8.7)"""
        runner = CliRunner()
        result = runner.invoke(main, ["sync", "--help"])

        assert result.exit_code == 0
        # Req 8.1: --ide 参数
        assert "--ide" in result.output
        assert "trae" in result.output
        assert "qoder" in result.output
        assert "lingma" in result.output
        assert "codebuddy" in result.output
        assert "cursor" in result.output
        assert "all" in result.output
        # Req 8.2: --scope 参数
        assert "--scope" in result.output
        assert "project" in result.output
        assert "global" in result.output
        # Req 8.3: --project-dir 参数
        assert "--project-dir" in result.output
        # Req 8.5: --type 参数
        assert "--type" in result.output
        assert "rules" in result.output
        assert "skills" in result.output
        assert "mcp" in result.output
        # Req 8.6: --name 参数
        assert "--name" in result.output
        # Req 8.7: --version 参数
        assert "--version" in result.output

    def test_sync_global_rules_unsupported_ide_warning(self, initialized_home):
        """msr-sync sync --scope global --type rules 对不支持全局 rules 的 IDE 应显示警告 (Req 5.6)"""
        repo = Repository()
        repo.store_rule("test-rule", "# Test Rule")

        runner = CliRunner()
        # 同步到 qoder（不支持全局 rules）
        result = runner.invoke(
            main, ["sync", "--scope", "global", "--type", "rules", "--ide", "qoder"]
        )

        assert result.exit_code == 0
        assert "不支持全局级 rules" in result.output
        assert "已跳过" in result.output


# ============================================================
# CLI sync 命令配置集成测试 (需求 4.2, 4.3, 5.2, 5.3)
# ============================================================

from unittest.mock import patch, MagicMock
from msr_sync.core.config import GlobalConfig, reset_config


@pytest.fixture
def _reset_config():
    """重置全局配置单例。"""
    reset_config()
    yield
    reset_config()


class TestSyncCommandConfigIntegration:
    """sync 命令从配置文件读取默认值的集成测试"""

    def test_sync_uses_config_default_ides_when_no_ide_flag(self, initialized_home, _reset_config):
        """需求 4.2: msr-sync sync 不指定 --ide 时使用配置文件中的 default_ides"""
        mock_config = GlobalConfig(default_ides=["trae"], default_scope="global")

        with patch("msr_sync.core.config.get_config", return_value=mock_config), \
             patch("msr_sync.commands.sync_cmd.sync_handler") as mock_handler:
            runner = CliRunner()
            result = runner.invoke(main, ["sync"])

        # sync_handler should have been called with ide=("trae",)
        assert mock_handler.called
        call_kwargs = mock_handler.call_args
        ide_val = call_kwargs.kwargs.get("ide") if call_kwargs.kwargs else call_kwargs[1].get("ide")
        assert ide_val == ("trae",)

    def test_sync_explicit_ide_overrides_config(self, initialized_home, _reset_config):
        """需求 4.3: msr-sync sync --ide trae 覆盖配置中的 default_ides"""
        mock_config = GlobalConfig(default_ides=["qoder"], default_scope="global")

        with patch("msr_sync.core.config.get_config", return_value=mock_config), \
             patch("msr_sync.commands.sync_cmd.sync_handler") as mock_handler:
            runner = CliRunner()
            result = runner.invoke(main, ["sync", "--ide", "trae"])

        assert mock_handler.called
        call_kwargs = mock_handler.call_args
        ide_val = call_kwargs.kwargs.get("ide") if call_kwargs.kwargs else call_kwargs[1].get("ide")
        assert ide_val == ("trae",)

    def test_sync_uses_config_default_scope_when_no_scope_flag(self, initialized_home, _reset_config):
        """需求 5.2: msr-sync sync 不指定 --scope 时使用配置文件中的 default_scope"""
        mock_config = GlobalConfig(default_ides=["all"], default_scope="project")

        with patch("msr_sync.core.config.get_config", return_value=mock_config), \
             patch("msr_sync.commands.sync_cmd.sync_handler") as mock_handler:
            runner = CliRunner()
            result = runner.invoke(main, ["sync"])

        assert mock_handler.called
        call_kwargs = mock_handler.call_args
        scope_val = call_kwargs.kwargs.get("scope") if call_kwargs.kwargs else call_kwargs[1].get("scope")
        assert scope_val == "project"

    def test_sync_explicit_scope_overrides_config(self, initialized_home, _reset_config):
        """需求 5.3: msr-sync sync --scope project 覆盖配置中的 default_scope"""
        mock_config = GlobalConfig(default_ides=["all"], default_scope="global")

        with patch("msr_sync.core.config.get_config", return_value=mock_config), \
             patch("msr_sync.commands.sync_cmd.sync_handler") as mock_handler:
            runner = CliRunner()
            result = runner.invoke(main, ["sync", "--scope", "project"])

        assert mock_handler.called
        call_kwargs = mock_handler.call_args
        scope_val = call_kwargs.kwargs.get("scope") if call_kwargs.kwargs else call_kwargs[1].get("scope")
        assert scope_val == "project"
