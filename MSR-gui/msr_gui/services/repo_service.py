"""仓库管理服务 — 封装 Repository 和 Config 的异步调用"""

import json
import tempfile
from pathlib import Path

import yaml
from nicegui import run
from msr_sync.adapters.registry import get_all_adapters
from msr_sync.core.config import (
    CONFIG_FILE_PATH,
    generate_default_config,
    get_config,
    reset_config,
)
from msr_sync.core.exceptions import MSRError
from msr_sync.core.repository import Repository

from msr_gui.state import app_state


class RepoService:
    def __init__(self):
        self.repo = Repository()

    async def get_repo_status(self) -> dict:
        """获取仓库状态概览"""

        def _get_status():
            path = self.repo.base_path
            return {
                "path": str(path),
                "exists": self.repo.exists(),
                "breakdown": {
                    "RULES": (path / "RULES").is_dir() if path.exists() else False,
                    "SKILLS": (path / "SKILLS").is_dir() if path.exists() else False,
                    "MCP": (path / "MCP").is_dir() if path.exists() else False,
                },
            }

        return await run.io_bound(_get_status)

    async def list_configs(self, config_type=None) -> dict:
        """获取配置列表"""

        def _list():
            if not self.repo.exists():
                return {"rules": {}, "skills": {}, "mcp": {}}
            return self.repo.list_configs(config_type)

        return await run.io_bound(_list)

    async def read_rule_content(self, name: str, version: str = None) -> dict:
        """读取 rule 内容"""

        def _read():
            return {
                "success": True,
                "content": self.repo.read_rule_content(name, version),
            }

        try:
            return await run.io_bound(_read)
        except MSRError as e:
            return {"success": False, "error": str(e)}

    async def remove_config(self, config_type: str, name: str, version: str) -> dict:
        """删除配置"""

        def _remove():
            self.repo.remove_config(config_type, name, version)
            return {"success": True}

        try:
            result = await run.io_bound(_remove)
            app_state.add_log(f"已删除 {config_type}/{name}/{version}", "success")
            return result
        except MSRError as e:
            app_state.add_log(f"删除失败: {e}", "error")
            return {"success": False, "error": str(e)}

    async def init_repo(self, merge: bool = False) -> dict:
        """初始化仓库"""

        def _init():
            is_new = self.repo.init()
            config_created = generate_default_config()
            result = {
                "success": True,
                "repo_created": is_new,
                "config_created": config_created,
                "repo_path": str(self.repo.base_path),
            }

            if merge:
                summary = {"rules": {}, "skills": {}, "mcp": {}}
                total_imported = 0
                adapters = get_all_adapters()

                for adapter in adapters:
                    ide_name = adapter.ide_name
                    try:
                        configs = adapter.scan_existing_configs()
                    except Exception:
                        continue

                    # 导入 rules
                    for rule_name in configs.get("rules", []):
                        try:
                            rules_path = adapter.get_rules_path(rule_name, "global")
                            if rules_path.exists() and rules_path.is_file():
                                content = rules_path.read_text(encoding="utf-8")
                                self.repo.store_rule(rule_name, content)
                                summary["rules"].setdefault(ide_name, 0)
                                summary["rules"][ide_name] += 1
                                total_imported += 1
                        except Exception:
                            pass

                    # 导入 skills
                    for skill_name in configs.get("skills", []):
                        try:
                            skill_path = adapter.get_skills_path(skill_name, "global")
                            if skill_path.exists() and skill_path.is_dir():
                                self.repo.store_skill(skill_name, skill_path)
                                summary["skills"].setdefault(ide_name, 0)
                                summary["skills"][ide_name] += 1
                                total_imported += 1
                        except Exception:
                            pass

                    # 导入 mcp
                    for mcp_item in configs.get("mcp", []):
                        try:
                            mcp_path = Path(mcp_item)
                            if mcp_path.exists() and mcp_path.is_file():
                                raw_text = mcp_path.read_text(encoding="utf-8").strip()
                                if not raw_text:
                                    continue
                                mcp_content = json.loads(raw_text)
                                servers = mcp_content.get("servers", {})
                                for mcp_name in servers:
                                    with tempfile.TemporaryDirectory() as tmp_dir:
                                        tmp_path = Path(tmp_dir)
                                        mcp_json_file = tmp_path / "mcp.json"
                                        mcp_json_file.write_text(
                                            json.dumps(
                                                {"servers": {mcp_name: servers[mcp_name]}},
                                                ensure_ascii=False,
                                                indent=2,
                                            ),
                                            encoding="utf-8",
                                        )
                                        self.repo.store_mcp(mcp_name, tmp_path)
                                        summary["mcp"].setdefault(ide_name, 0)
                                        summary["mcp"][ide_name] += 1
                                        total_imported += 1
                        except Exception:
                            pass

                result["merge_summary"] = summary
                result["total_imported"] = total_imported

            return result

        try:
            result = await run.io_bound(_init)
            msg = f"仓库初始化完成: {result['repo_path']}"
            if merge and result.get("total_imported", 0) > 0:
                msg += f"，合并 {result['total_imported']} 项配置"
            app_state.add_log(msg, "success")
            return result
        except MSRError as e:
            app_state.add_log(f"仓库初始化失败: {e}", "error")
            return {"success": False, "error": str(e)}

    async def get_config(self) -> dict:
        """获取全局配置"""

        def _get():
            return get_config().to_dict()

        return await run.io_bound(_get)

    async def get_all_ide_info(self) -> list:
        """获取所有 IDE 适配器信息"""

        def _get_info():
            adapters = get_all_adapters()
            return [
                {
                    "name": adapter.ide_name,
                    "supports_global_rules": adapter.supports_global_rules(),
                }
                for adapter in adapters
            ]

        return await run.io_bound(_get_info)

    async def save_config(
        self,
        repo_path: str,
        default_ides: list,
        default_scope: str,
        ignore_patterns: list,
    ) -> dict:
        """保存全局配置到 YAML 文件"""

        def _save():
            config_data = {
                "repo_path": repo_path,
                "default_ides": list(default_ides),
                "default_scope": default_scope,
                "ignore_patterns": list(ignore_patterns),
            }
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE_PATH.write_text(
                yaml.dump(config_data, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )
            reset_config()
            return {"success": True}

        try:
            result = await run.io_bound(_save)
            app_state.add_log("配置保存成功", "success")
            return result
        except Exception as e:
            app_state.add_log(f"配置保存失败: {e}", "error")
            return {"success": False, "error": str(e)}


repo_service = RepoService()
