"""命令处理器单元测试 — init、list、remove、import"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from msr_sync.commands.init_cmd import init_handler
from msr_sync.commands.import_cmd import import_handler
from msr_sync.commands.list_cmd import list_handler
from msr_sync.commands.remove_cmd import remove_handler
from msr_sync.core.repository import Repository


# ============================================================
# init_handler 测试
# ============================================================


class TestInitHandler:
    """init 命令处理器测试"""

    def test_init_creates_repo(self, tmp_repo: Path) -> None:
        """新建仓库时应输出创建成功信息"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_init(tmp_repo, merge=False), catch_exceptions=False
        )
        assert "✅ 统一仓库已创建" in result.output
        assert (tmp_repo / "RULES").is_dir()
        assert (tmp_repo / "SKILLS").is_dir()
        assert (tmp_repo / "MCP").is_dir()

    def test_init_idempotent(self, initialized_repo: Path) -> None:
        """仓库已存在时应输出跳过提示"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_init(initialized_repo, merge=False), catch_exceptions=False
        )
        assert "统一仓库已初始化，跳过创建" in result.output

    def test_init_merge_no_configs(self, tmp_repo: Path) -> None:
        """--merge 无现有配置时应输出合并摘要（全部为无）"""
        # Mock all adapters to return empty configs
        mock_adapter = MagicMock()
        mock_adapter.ide_name = "test_ide"
        mock_adapter.scan_existing_configs.return_value = {
            "rules": [],
            "skills": [],
            "mcp": [],
        }

        with patch(
            "msr_sync.commands.init_cmd.get_all_adapters",
            return_value=[mock_adapter],
        ):
            runner = CliRunner()
            result = runner.invoke(
                _wrap_init(tmp_repo, merge=True), catch_exceptions=False
            )
            assert "合并摘要" in result.output
            assert "共导入 0 项" in result.output

    def test_init_merge_imports_rules(self, tmp_repo: Path, tmp_path: Path) -> None:
        """--merge 应导入发现的 rules"""
        # 创建一个模拟的 rule 文件
        rule_file = tmp_path / "test-rule.md"
        rule_file.write_text("# Test Rule\nSome content", encoding="utf-8")

        mock_adapter = MagicMock()
        mock_adapter.ide_name = "test_ide"
        mock_adapter.scan_existing_configs.return_value = {
            "rules": ["test-rule"],
            "skills": [],
            "mcp": [],
        }
        mock_adapter.get_rules_path.return_value = rule_file

        with patch(
            "msr_sync.commands.init_cmd.get_all_adapters",
            return_value=[mock_adapter],
        ):
            runner = CliRunner()
            result = runner.invoke(
                _wrap_init(tmp_repo, merge=True), catch_exceptions=False
            )
            assert "共导入 1 项" in result.output
            assert "rules: test_ide: 1 项" in result.output
            # 验证 rule 确实被存储了
            assert (tmp_repo / "RULES" / "test-rule" / "V1" / "test-rule.md").is_file()

    def test_init_merge_imports_skills(self, tmp_repo: Path, tmp_path: Path) -> None:
        """--merge 应导入发现的 skills"""
        # 创建一个模拟的 skill 目录
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill", encoding="utf-8")

        mock_adapter = MagicMock()
        mock_adapter.ide_name = "test_ide"
        mock_adapter.scan_existing_configs.return_value = {
            "rules": [],
            "skills": ["my-skill"],
            "mcp": [],
        }
        mock_adapter.get_skills_path.return_value = skill_dir

        with patch(
            "msr_sync.commands.init_cmd.get_all_adapters",
            return_value=[mock_adapter],
        ):
            runner = CliRunner()
            result = runner.invoke(
                _wrap_init(tmp_repo, merge=True), catch_exceptions=False
            )
            assert "共导入 1 项" in result.output
            assert "skills: test_ide: 1 项" in result.output
            assert (tmp_repo / "SKILLS" / "my-skill" / "V1" / "SKILL.md").is_file()

    def test_init_merge_imports_mcp(self, tmp_repo: Path, tmp_path: Path) -> None:
        """--merge 应导入发现的 MCP 配置"""
        # 创建一个模拟的 mcp.json 文件
        mcp_file = tmp_path / "mcp.json"
        mcp_content = {
            "servers": {
                "my-server": {
                    "command": "node",
                    "args": ["server.js"],
                }
            }
        }
        mcp_file.write_text(
            json.dumps(mcp_content, ensure_ascii=False), encoding="utf-8"
        )

        mock_adapter = MagicMock()
        mock_adapter.ide_name = "test_ide"
        mock_adapter.scan_existing_configs.return_value = {
            "rules": [],
            "skills": [],
            "mcp": [str(mcp_file)],
        }

        with patch(
            "msr_sync.commands.init_cmd.get_all_adapters",
            return_value=[mock_adapter],
        ):
            runner = CliRunner()
            result = runner.invoke(
                _wrap_init(tmp_repo, merge=True), catch_exceptions=False
            )
            assert "共导入 1 项" in result.output
            assert "mcp: test_ide: 1 项" in result.output
            assert (tmp_repo / "MCP" / "my-server" / "V1" / "mcp.json").is_file()

    def test_init_merge_adapter_error_skipped(self, tmp_repo: Path) -> None:
        """--merge 适配器扫描出错时应跳过并继续"""
        mock_adapter = MagicMock()
        mock_adapter.ide_name = "broken_ide"
        mock_adapter.scan_existing_configs.side_effect = RuntimeError("boom")

        with patch(
            "msr_sync.commands.init_cmd.get_all_adapters",
            return_value=[mock_adapter],
        ):
            runner = CliRunner()
            result = runner.invoke(
                _wrap_init(tmp_repo, merge=True), catch_exceptions=False
            )
            assert "扫描 broken_ide 配置时出错" in result.output
            assert "共导入 0 项" in result.output


# ============================================================
# list_handler 测试
# ============================================================


class TestListHandler:
    """list 命令处理器测试"""

    def test_list_repo_not_initialized(self, tmp_repo: Path) -> None:
        """仓库未初始化时应输出错误提示"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_list(tmp_repo, config_type=None), catch_exceptions=False
        )
        assert "统一仓库未初始化" in result.output
        assert result.exit_code == 1

    def test_list_empty_repo(self, initialized_repo: Path) -> None:
        """空仓库应输出暂无配置"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_list(initialized_repo, config_type=None),
            catch_exceptions=False,
        )
        assert "暂无配置" in result.output

    def test_list_with_configs(self, initialized_repo: Path) -> None:
        """有配置时应以树形结构展示"""
        repo = Repository(base_path=initialized_repo)
        repo.store_rule("my-rule", "# Rule content")
        repo.store_rule("my-rule", "# Rule content v2")
        repo.store_rule("other-rule", "# Other rule")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_list(initialized_repo, config_type=None),
            catch_exceptions=False,
        )
        assert "统一仓库配置列表" in result.output
        assert "rules" in result.output
        assert "my-rule" in result.output
        assert "V1" in result.output
        assert "V2" in result.output
        assert "other-rule" in result.output

    def test_list_with_type_filter(self, initialized_repo: Path) -> None:
        """--type 过滤应只显示指定类型"""
        repo = Repository(base_path=initialized_repo)
        repo.store_rule("my-rule", "# Rule content")

        # 创建一个 skill
        skill_dir = initialized_repo / "temp-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")
        repo.store_skill("my-skill", skill_dir)

        runner = CliRunner()
        result = runner.invoke(
            _wrap_list(initialized_repo, config_type="rules"),
            catch_exceptions=False,
        )
        assert "my-rule" in result.output
        assert "my-skill" not in result.output

    def test_list_empty_type_filter(self, initialized_repo: Path) -> None:
        """过滤类型无配置时应输出提示"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_list(initialized_repo, config_type="mcp"),
            catch_exceptions=False,
        )
        assert "没有 mcp 类型的配置" in result.output

    def test_list_tree_format(self, initialized_repo: Path) -> None:
        """验证树形结构格式"""
        repo = Repository(base_path=initialized_repo)
        repo.store_rule("alpha-rule", "# Alpha")
        repo.store_rule("beta-rule", "# Beta")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_list(initialized_repo, config_type=None),
            catch_exceptions=False,
        )
        # 验证树形结构字符存在
        assert "├── " in result.output or "└── " in result.output


# ============================================================
# remove_handler 测试
# ============================================================


class TestRemoveHandler:
    """remove 命令处理器测试"""

    def test_remove_success(self, initialized_repo: Path) -> None:
        """删除成功时应输出确认信息"""
        repo = Repository(base_path=initialized_repo)
        repo.store_rule("my-rule", "# Rule content")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_remove(initialized_repo, "rules", "my-rule", "V1"),
            catch_exceptions=False,
        )
        assert "✅ 已删除配置: rules/my-rule/V1" in result.output
        assert not (initialized_repo / "RULES" / "my-rule" / "V1").exists()

    def test_remove_config_not_found(self, initialized_repo: Path) -> None:
        """配置不存在时应输出错误提示"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_remove(initialized_repo, "rules", "nonexistent", "V1"),
            catch_exceptions=False,
        )
        assert "未找到指定的配置版本" in result.output
        assert result.exit_code == 1

    def test_remove_repo_not_initialized(self, tmp_repo: Path) -> None:
        """仓库未初始化时应输出错误提示"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_remove(tmp_repo, "rules", "my-rule", "V1"),
            catch_exceptions=False,
        )
        assert "统一仓库未初始化" in result.output
        assert result.exit_code == 1

    def test_remove_version_not_found(self, initialized_repo: Path) -> None:
        """版本不存在时应输出错误提示"""
        repo = Repository(base_path=initialized_repo)
        repo.store_rule("my-rule", "# Rule content")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_remove(initialized_repo, "rules", "my-rule", "V99"),
            catch_exceptions=False,
        )
        assert "未找到指定的配置版本" in result.output
        assert result.exit_code == 1


# ============================================================
# import_handler 测试
# ============================================================


class TestImportHandler:
    """import 命令处理器测试"""

    def test_import_single_rule(self, initialized_repo: Path, tmp_path: Path) -> None:
        """单个 rule 文件应直接导入，无需确认"""
        rule_file = tmp_path / "my-rule.md"
        rule_file.write_text("# My Rule\nContent here", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "rules", str(rule_file)),
            catch_exceptions=False,
        )
        assert "✅ 已导入: my-rule (V1)" in result.output
        assert "导入完成: 成功 1 项" in result.output
        assert (initialized_repo / "RULES" / "my-rule" / "V1" / "my-rule.md").is_file()

    def test_import_multiple_rules_confirm_all(
        self, initialized_repo: Path, tmp_path: Path
    ) -> None:
        """多个 rule 文件应展示列表并逐一确认"""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "alpha.md").write_text("# Alpha", encoding="utf-8")
        (rules_dir / "beta.md").write_text("# Beta", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "rules", str(rules_dir)),
            input="y\ny\n",
            catch_exceptions=False,
        )
        assert "发现 2 个 rules 配置项" in result.output
        assert "导入完成: 成功 2 项" in result.output
        assert (initialized_repo / "RULES" / "alpha" / "V1" / "alpha.md").is_file()
        assert (initialized_repo / "RULES" / "beta" / "V1" / "beta.md").is_file()

    def test_import_multiple_rules_skip_one(
        self, initialized_repo: Path, tmp_path: Path
    ) -> None:
        """用户拒绝某个配置项时应跳过"""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "alpha.md").write_text("# Alpha", encoding="utf-8")
        (rules_dir / "beta.md").write_text("# Beta", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "rules", str(rules_dir)),
            input="y\nn\n",
            catch_exceptions=False,
        )
        assert "导入完成: 成功 1 项" in result.output
        assert "已跳过: beta" in result.output
        assert (initialized_repo / "RULES" / "alpha" / "V1" / "alpha.md").is_file()
        assert not (initialized_repo / "RULES" / "beta").exists()

    def test_import_single_skill(self, initialized_repo: Path, tmp_path: Path) -> None:
        """单个 skill 目录应直接导入"""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "skills", str(skill_dir)),
            catch_exceptions=False,
        )
        assert "✅ 已导入: my-skill (V1)" in result.output
        assert "导入完成: 成功 1 项" in result.output
        assert (initialized_repo / "SKILLS" / "my-skill" / "V1" / "SKILL.md").is_file()

    def test_import_single_mcp(self, initialized_repo: Path, tmp_path: Path) -> None:
        """单个 MCP 目录应直接导入"""
        mcp_dir = tmp_path / "my-mcp"
        mcp_dir.mkdir()
        (mcp_dir / "mcp.json").write_text(
            json.dumps({"servers": {"test": {"command": "node"}}}),
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "mcp", str(mcp_dir)),
            catch_exceptions=False,
        )
        assert "✅ 已导入: my-mcp (V1)" in result.output
        assert "导入完成: 成功 1 项" in result.output
        assert (initialized_repo / "MCP" / "my-mcp" / "V1" / "mcp.json").is_file()

    def test_import_version_conflict_auto_increment(
        self, initialized_repo: Path, tmp_path: Path
    ) -> None:
        """名称冲突时应自动创建新版本"""
        repo = Repository(base_path=initialized_repo)
        repo.store_rule("my-rule", "# Version 1")

        rule_file = tmp_path / "my-rule.md"
        rule_file.write_text("# Version 2", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "rules", str(rule_file)),
            catch_exceptions=False,
        )
        assert "✅ 已导入: my-rule (V2)" in result.output
        assert (initialized_repo / "RULES" / "my-rule" / "V2" / "my-rule.md").is_file()

    def test_import_repo_not_initialized(self, tmp_repo: Path, tmp_path: Path) -> None:
        """仓库未初始化时应输出错误提示"""
        rule_file = tmp_path / "my-rule.md"
        rule_file.write_text("# Rule", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(tmp_repo, "rules", str(rule_file)),
            catch_exceptions=False,
        )
        assert "统一仓库未初始化" in result.output
        assert result.exit_code == 1

    def test_import_invalid_source(self, initialized_repo: Path) -> None:
        """无效来源应输出错误提示"""
        runner = CliRunner()
        result = runner.invoke(
            _wrap_import(initialized_repo, "rules", "/nonexistent/path"),
            catch_exceptions=False,
        )
        assert "无效的导入来源" in result.output
        assert result.exit_code == 1

    def test_import_cleanup_called(
        self, initialized_repo: Path, tmp_path: Path
    ) -> None:
        """无论成功失败，resolver.cleanup() 都应被调用"""
        rule_file = tmp_path / "my-rule.md"
        rule_file.write_text("# Rule", encoding="utf-8")

        with patch(
            "msr_sync.commands.import_cmd.SourceResolver"
        ) as MockResolver:
            mock_instance = MockResolver.return_value
            mock_item = MagicMock()
            mock_item.name = "my-rule"
            mock_item.path = rule_file
            mock_instance.resolve.return_value = ([mock_item], False)

            runner = CliRunner()
            runner.invoke(
                _wrap_import(initialized_repo, "rules", str(rule_file)),
                catch_exceptions=False,
            )
            mock_instance.cleanup.assert_called_once()


# ============================================================
# 辅助函数 — 将 handler 包装为 click 命令以便使用 CliRunner
# ============================================================

import click


def _wrap_init(base_path: Path, merge: bool):
    """将 init_handler 包装为 click 命令"""

    @click.command()
    def cmd():
        init_handler(merge=merge, base_path=base_path)

    return cmd


def _wrap_list(base_path: Path, config_type):
    """将 list_handler 包装为 click 命令"""

    @click.command()
    def cmd():
        list_handler(config_type=config_type, base_path=base_path)

    return cmd


def _wrap_remove(base_path: Path, config_type: str, name: str, version: str):
    """将 remove_handler 包装为 click 命令"""

    @click.command()
    def cmd():
        remove_handler(
            config_type=config_type,
            name=name,
            version=version,
            base_path=base_path,
        )

    return cmd


def _wrap_import(base_path: Path, config_type: str, source: str):
    """将 import_handler 包装为 click 命令"""

    @click.command()
    def cmd():
        import_handler(
            config_type=config_type,
            source=source,
            base_path=base_path,
        )

    return cmd
