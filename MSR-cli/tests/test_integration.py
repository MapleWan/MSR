"""端到端集成测试 — 验证完整的 CLI 工作流

使用 monkeypatch 将 Path.home() 重定向到临时目录，
通过 click.testing.CliRunner 调用 CLI 命令，
验证 init --merge、压缩包导入、URL 导入、import → sync 完整流程。
"""

import io
import json
import shutil
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from msr_sync.cli import main
from msr_sync.core.repository import Repository


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """将 Path.home() 重定向到临时目录，实现测试隔离。"""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


@pytest.fixture
def initialized_home(fake_home):
    """在 fake_home 下创建已初始化的仓库。"""
    repo = Repository()
    repo.init()
    return fake_home


# ============================================================
# Test 1: init --merge 扫描并导入已有 IDE 配置 (Req 1.3, 1.4)
# ============================================================


class TestInitMerge:
    """init --merge 端到端集成测试"""

    def test_init_merge_imports_codebuddy_rules(self, fake_home):
        """init --merge 应扫描 CodeBuddy 用户级 rules 并导入到统一仓库 (Req 1.3, 1.4)

        CodeBuddy 是唯一支持全局级 rules 的 IDE，因此 scan_existing_configs
        会在 ~/.codebuddy/rules/ 下发现 .md 文件。
        """
        # 设置 CodeBuddy 用户级 rules
        cb_rules_dir = fake_home / ".codebuddy" / "rules"
        cb_rules_dir.mkdir(parents=True)
        (cb_rules_dir / "existing-rule.md").write_text(
            "# Existing CodeBuddy Rule\nSome content here.",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--merge"])

        assert result.exit_code == 0
        assert "合并摘要" in result.output

        # 验证 rule 被导入到统一仓库
        repo_path = fake_home / ".msr-repos"
        rule_dir = repo_path / "RULES" / "existing-rule" / "V1"
        assert rule_dir.is_dir()
        rule_file = rule_dir / "existing-rule.md"
        assert rule_file.is_file()
        assert "Existing CodeBuddy Rule" in rule_file.read_text(encoding="utf-8")

    def test_init_merge_imports_qoder_skills(self, fake_home):
        """init --merge 应扫描 Qoder 用户级 skills 并导入到统一仓库 (Req 1.3, 1.4)"""
        # 设置 Qoder 用户级 skills
        qoder_skill_dir = fake_home / ".qoder" / "skills" / "existing-skill"
        qoder_skill_dir.mkdir(parents=True)
        (qoder_skill_dir / "SKILL.md").write_text(
            "# Existing Qoder Skill",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--merge"])

        assert result.exit_code == 0
        assert "合并摘要" in result.output

        # 验证 skill 被导入到统一仓库
        repo_path = fake_home / ".msr-repos"
        skill_dir = repo_path / "SKILLS" / "existing-skill" / "V1"
        assert skill_dir.is_dir()
        assert (skill_dir / "SKILL.md").is_file()

    def test_init_merge_summary_shows_counts(self, fake_home):
        """init --merge 合并摘要应显示每种配置类型和来源 IDE 的导入数量 (Req 1.4)"""
        # 设置 CodeBuddy rules
        cb_rules_dir = fake_home / ".codebuddy" / "rules"
        cb_rules_dir.mkdir(parents=True)
        (cb_rules_dir / "rule-a.md").write_text("# Rule A", encoding="utf-8")
        (cb_rules_dir / "rule-b.md").write_text("# Rule B", encoding="utf-8")

        # 设置 CodeBuddy skills
        cb_skill_dir = fake_home / ".codebuddy" / "skills" / "skill-x"
        cb_skill_dir.mkdir(parents=True)
        (cb_skill_dir / "SKILL.md").write_text("# Skill X", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--merge"])

        assert result.exit_code == 0
        assert "合并摘要" in result.output
        # 验证摘要中包含 codebuddy 的导入信息
        assert "codebuddy" in result.output


# ============================================================
# Test 2: ZIP 压缩包导入 rules (Req 2.3, 3.2, 4.2)
# ============================================================


class TestZipArchiveImport:
    """ZIP 压缩包导入端到端集成测试"""

    def test_zip_import_rules(self, initialized_home, tmp_path):
        """从 ZIP 压缩包导入多个 rules 文件 (Req 2.3)"""
        # 创建包含多个 .md 文件的 ZIP
        zip_path = tmp_path / "rules-pack.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rule-alpha.md", "# Rule Alpha\nAlpha content.")
            zf.writestr("rule-beta.md", "# Rule Beta\nBeta content.")

        runner = CliRunner()
        # 输入 "y\ny\n" 确认导入每个 rule
        result = runner.invoke(
            main,
            ["import", "rules", str(zip_path)],
            input="y\ny\n",
        )

        assert result.exit_code == 0
        assert "导入完成" in result.output

        # 验证 rules 被导入到统一仓库
        repo_path = initialized_home / ".msr-repos"
        assert (repo_path / "RULES" / "rule-alpha" / "V1" / "rule-alpha.md").is_file()
        assert (repo_path / "RULES" / "rule-beta" / "V1" / "rule-beta.md").is_file()

    def test_zip_import_skills(self, initialized_home, tmp_path):
        """从 ZIP 压缩包导入多个 skills 目录 (Req 4.2)"""
        # 创建包含多个 skill 子目录的 ZIP
        zip_path = tmp_path / "skills-pack.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("skill-one/SKILL.md", "# Skill One")
            zf.writestr("skill-one/helper.py", "# helper")
            zf.writestr("skill-two/SKILL.md", "# Skill Two")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["import", "skills", str(zip_path)],
            input="y\ny\n",
        )

        assert result.exit_code == 0
        assert "导入完成" in result.output

        repo_path = initialized_home / ".msr-repos"
        assert (repo_path / "SKILLS" / "skill-one" / "V1" / "SKILL.md").is_file()
        assert (repo_path / "SKILLS" / "skill-two" / "V1" / "SKILL.md").is_file()


# ============================================================
# Test 3: tar.gz 压缩包导入 skills (Req 3.4, 4.4)
# ============================================================


class TestTarGzArchiveImport:
    """tar.gz 压缩包导入端到端集成测试"""

    def test_targz_import_skills(self, initialized_home, tmp_path):
        """从 tar.gz 压缩包导入多个 skills 目录 (Req 4.4)"""
        # 先在临时目录创建 skill 目录结构
        src_dir = tmp_path / "skills-src"
        skill_a = src_dir / "skill-a"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text("# Skill A", encoding="utf-8")

        skill_b = src_dir / "skill-b"
        skill_b.mkdir(parents=True)
        (skill_b / "SKILL.md").write_text("# Skill B", encoding="utf-8")
        (skill_b / "utils.py").write_text("# utils", encoding="utf-8")

        # 创建 tar.gz 压缩包
        tar_path = tmp_path / "skills-pack.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            tf.add(str(src_dir), arcname="skills-src")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["import", "skills", str(tar_path)],
            input="y\ny\n",
        )

        assert result.exit_code == 0
        assert "导入完成" in result.output

        repo_path = initialized_home / ".msr-repos"
        assert (repo_path / "SKILLS" / "skill-a" / "V1" / "SKILL.md").is_file()
        assert (repo_path / "SKILLS" / "skill-b" / "V1" / "SKILL.md").is_file()

    def test_targz_import_mcp(self, initialized_home, tmp_path):
        """从 tar.gz 压缩包导入多个 MCP 配置目录 (Req 3.4)"""
        # 创建 MCP 目录结构（多个子目录 = 多个 MCP）
        src_dir = tmp_path / "mcp-src"
        mcp_a = src_dir / "mcp-server-a"
        mcp_a.mkdir(parents=True)
        (mcp_a / "mcp.json").write_text(
            json.dumps({"servers": {"server-a": {"command": "node", "args": ["a.js"]}}}),
            encoding="utf-8",
        )

        mcp_b = src_dir / "mcp-server-b"
        mcp_b.mkdir(parents=True)
        (mcp_b / "mcp.json").write_text(
            json.dumps({"servers": {"server-b": {"command": "python", "args": ["b.py"]}}}),
            encoding="utf-8",
        )

        tar_path = tmp_path / "mcp-pack.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            tf.add(str(src_dir), arcname="mcp-src")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["import", "mcp", str(tar_path)],
            input="y\ny\n",
        )

        assert result.exit_code == 0
        assert "导入完成" in result.output

        repo_path = initialized_home / ".msr-repos"
        assert (repo_path / "MCP" / "mcp-server-a" / "V1").is_dir()
        assert (repo_path / "MCP" / "mcp-server-b" / "V1").is_dir()


# ============================================================
# Test 4: URL 下载并导入 (mock HTTP) (Req 2.4, 3.5, 4.5)
# ============================================================


class TestUrlImport:
    """URL 下载导入端到端集成测试"""

    def test_url_import_rules(self, initialized_home, tmp_path):
        """从 URL 下载 ZIP 并导入 rules (Req 2.4)"""
        # 预先创建一个 ZIP 文件
        zip_path = tmp_path / "remote-rules.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("url-rule-1.md", "# URL Rule 1\nDownloaded content.")
            zf.writestr("url-rule-2.md", "# URL Rule 2\nMore content.")

        # Mock urllib.request.urlretrieve 将 URL 下载重定向到本地文件
        def fake_urlretrieve(url, dest):
            shutil.copy2(str(zip_path), str(dest))
            return dest, None

        with patch("msr_sync.core.source_resolver.urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["import", "rules", "https://example.com/rules-pack.zip"],
                input="y\ny\n",
            )

        assert result.exit_code == 0
        assert "导入完成" in result.output

        repo_path = initialized_home / ".msr-repos"
        assert (repo_path / "RULES" / "url-rule-1" / "V1" / "url-rule-1.md").is_file()
        assert (repo_path / "RULES" / "url-rule-2" / "V1" / "url-rule-2.md").is_file()

    def test_url_import_skills(self, initialized_home, tmp_path):
        """从 URL 下载 ZIP 并导入 skills (Req 4.5)"""
        zip_path = tmp_path / "remote-skills.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("url-skill/SKILL.md", "# URL Skill")

        def fake_urlretrieve(url, dest):
            shutil.copy2(str(zip_path), str(dest))
            return dest, None

        with patch("msr_sync.core.source_resolver.urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["import", "skills", "https://example.com/skills-pack.zip"],
            )

        assert result.exit_code == 0
        assert "导入完成" in result.output

        repo_path = initialized_home / ".msr-repos"
        assert (repo_path / "SKILLS" / "url-skill" / "V1" / "SKILL.md").is_file()


# ============================================================
# Test 5: 完整 import → sync 流程 (端到端验证)
# ============================================================


class TestImportThenSync:
    """完整 import → sync 端到端集成测试"""

    def test_import_rule_then_sync_to_codebuddy_project(self, initialized_home, tmp_path):
        """导入 rule 后同步到 CodeBuddy 项目级路径，验证文件内容和 frontmatter (端到端)"""
        # Step 1: 创建一个 rule 文件
        rule_file = tmp_path / "my-test-rule.md"
        rule_file.write_text(
            "---\nauthor: test\n---\n# My Test Rule\nThis is the rule body.",
            encoding="utf-8",
        )

        # Step 2: 导入 rule
        runner = CliRunner()
        import_result = runner.invoke(
            main,
            ["import", "rules", str(rule_file)],
        )
        assert import_result.exit_code == 0
        assert "已导入" in import_result.output

        # 验证 rule 在统一仓库中
        repo_path = initialized_home / ".msr-repos"
        stored_rule = repo_path / "RULES" / "my-test-rule" / "V1" / "my-test-rule.md"
        assert stored_rule.is_file()

        # Step 3: 创建项目目录
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()

        # Step 4: 同步到 CodeBuddy 项目级
        sync_result = runner.invoke(
            main,
            [
                "sync",
                "--ide", "codebuddy",
                "--scope", "project",
                "--project-dir", str(project_dir),
                "--type", "rules",
                "--name", "my-test-rule",
            ],
        )
        assert sync_result.exit_code == 0
        assert "已同步" in sync_result.output

        # Step 5: 验证同步后的文件
        synced_file = project_dir / ".codebuddy" / "rules" / "my-test-rule.md"
        assert synced_file.is_file()

        content = synced_file.read_text(encoding="utf-8")
        # 验证 CodeBuddy frontmatter 被添加
        assert content.startswith("---\n")
        assert "alwaysApply: true" in content
        assert "enabled: true" in content
        assert "updatedAt:" in content
        # 验证原始 frontmatter 被剥离（不包含 author: test）
        assert "author: test" not in content
        # 验证正文内容保留
        assert "# My Test Rule" in content
        assert "This is the rule body." in content

    def test_import_rule_then_sync_to_trae_project(self, initialized_home, tmp_path):
        """导入 rule 后同步到 Trae 项目级路径，验证 Trae 不添加 frontmatter (端到端)"""
        # Step 1: 创建 rule 文件（带 frontmatter）
        rule_file = tmp_path / "trae-rule.md"
        rule_file.write_text(
            "---\ntrigger: manual\n---\n# Trae Rule\nTrae rule body.",
            encoding="utf-8",
        )

        # Step 2: 导入
        runner = CliRunner()
        runner.invoke(main, ["import", "rules", str(rule_file)])

        # Step 3: 同步到 Trae 项目级
        project_dir = tmp_path / "trae-project"
        project_dir.mkdir()

        sync_result = runner.invoke(
            main,
            [
                "sync",
                "--ide", "trae",
                "--scope", "project",
                "--project-dir", str(project_dir),
                "--type", "rules",
            ],
        )
        assert sync_result.exit_code == 0

        # Step 4: 验证 Trae 同步结果（不添加额外 frontmatter）
        synced_file = project_dir / ".trae" / "rules" / "trae-rule.md"
        assert synced_file.is_file()

        content = synced_file.read_text(encoding="utf-8")
        # Trae 不添加 frontmatter，内容应为纯正文
        assert "trigger: manual" not in content  # 原始 frontmatter 被剥离
        assert "# Trae Rule" in content
        assert "Trae rule body." in content

    def test_import_skill_then_sync_to_qoder_project(self, initialized_home, tmp_path):
        """导入 skill 后同步到 Qoder 项目级路径 (端到端)"""
        # Step 1: 创建 skill 目录
        skill_src = tmp_path / "my-skill"
        skill_src.mkdir()
        (skill_src / "SKILL.md").write_text("# My Skill\nSkill description.", encoding="utf-8")
        (skill_src / "helper.py").write_text("def helper(): pass", encoding="utf-8")

        # Step 2: 导入 skill
        runner = CliRunner()
        import_result = runner.invoke(
            main,
            ["import", "skills", str(skill_src)],
        )
        assert import_result.exit_code == 0

        # Step 3: 同步到 Qoder 项目级
        project_dir = tmp_path / "qoder-project"
        project_dir.mkdir()

        sync_result = runner.invoke(
            main,
            [
                "sync",
                "--ide", "qoder",
                "--scope", "project",
                "--project-dir", str(project_dir),
                "--type", "skills",
            ],
        )
        assert sync_result.exit_code == 0

        # Step 4: 验证 skill 被同步到正确路径
        synced_skill = project_dir / ".qoder" / "skills" / "my-skill"
        assert synced_skill.is_dir()
        assert (synced_skill / "SKILL.md").is_file()
        assert (synced_skill / "helper.py").is_file()
