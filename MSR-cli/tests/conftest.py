"""MSR-sync 测试共享 fixtures"""

import pytest
from pathlib import Path

from hypothesis import settings

# Hypothesis 配置：每个属性测试至少 100 次迭代
settings.register_profile("ci", max_examples=200)
settings.register_profile("default", max_examples=100)
settings.load_profile("default")


@pytest.fixture(autouse=True)
def _reset_global_config():
    """每个测试前后重置全局配置单例，避免状态泄漏。"""
    from msr_sync.core.config import reset_config
    reset_config()
    yield
    reset_config()


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """创建临时仓库目录，用于隔离文件系统操作"""
    repo_path = tmp_path / ".msr-repos"
    return repo_path


@pytest.fixture
def initialized_repo(tmp_repo: Path) -> Path:
    """创建已初始化的临时仓库（包含 RULES/SKILLS/MCP 子目录）"""
    for sub_dir in ["RULES", "SKILLS", "MCP"]:
        (tmp_repo / sub_dir).mkdir(parents=True, exist_ok=True)
    return tmp_repo
