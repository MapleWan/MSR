"""导入配置服务 — 封装 import 相关逻辑"""

from pathlib import Path

from nicegui import run
from msr_sync.constants import ConfigType
from msr_sync.core.exceptions import MSRError, RepositoryNotFoundError
from msr_sync.core.repository import Repository
from msr_sync.core.source_resolver import SourceResolver

from msr_gui.state import app_state


class ImportService:
    def __init__(self):
        self._resolver = None

    def cleanup(self):
        """清理 SourceResolver 的临时资源。"""
        if self._resolver:
            self._resolver.cleanup()
            self._resolver = None

    async def resolve_source(self, source: str, config_type: str) -> dict:
        """解析导入来源，返回配置项列表

        Args:
            source: 导入来源字符串（文件路径/目录路径/压缩包路径/URL）
            config_type: 配置类型（rules/skills/mcp）

        Returns:
            解析结果字典，包含 items, needs_confirm, count
        """
        self.cleanup()
        self._resolver = SourceResolver()

        def _resolve():
            try:
                items, needs_confirm = self._resolver.resolve(source, config_type)
                return {
                    "success": True,
                    "items": [
                        {
                            "name": item.name,
                            "path": str(item.path),
                            "source_type": item.source_type.value,
                        }
                        for item in items
                    ],
                    "needs_confirm": needs_confirm,
                    "count": len(items),
                }
            except MSRError as e:
                return {"success": False, "error": str(e), "items": [], "needs_confirm": False, "count": 0}

        try:
            result = await run.io_bound(_resolve)
            if not result["success"]:
                self.cleanup()
            app_state.add_log(f"解析来源成功: 发现 {result['count']} 个配置项", "success")
            return result
        except MSRError as e:
            self.cleanup()
            app_state.add_log(f"解析来源失败: {e}", "error")
            return {"success": False, "error": str(e), "items": [], "needs_confirm": False, "count": 0}

    async def import_configs(self, config_type: str, items: list, callback=None) -> dict:
        """执行导入操作

        Args:
            config_type: 配置类型（rules/skills/mcp）
            items: 配置项列表，每个元素为 dict，需包含 name 和 path
            callback: 可选的进度回调，签名 callback(name: str, result: dict)

        Returns:
            导入结果字典，包含 success_count, total, results
        """

        def _import():
            repo = Repository()
            if not repo.exists():
                raise RepositoryNotFoundError("统一仓库未初始化，请先执行 `msr-sync init`")

            success_count = 0
            results = []

            for item in items:
                name = item.get("name")
                path = item.get("path")

                try:
                    version = self._store_item(repo, config_type, name, path)
                    if version:
                        success_count += 1
                        result_item = {
                            "name": name,
                            "status": "success",
                            "version": version,
                        }
                    else:
                        result_item = {
                            "name": name,
                            "status": "failed",
                            "reason": "存储失败",
                        }
                except Exception as e:
                    result_item = {
                        "name": name,
                        "status": "failed",
                        "reason": str(e),
                    }

                results.append(result_item)

                if callback:
                    callback(name, result_item)

            return {
                "success": True,
                "success_count": success_count,
                "total": len(items),
                "results": results,
            }

        try:
            result = await run.io_bound(_import)
            app_state.add_log(
                f"导入完成: 成功 {result['success_count']}/{result['total']} 项", "success"
            )
            return result
        except MSRError as e:
            app_state.add_log(f"导入失败: {e}", "error")
            return {
                "success": False,
                "error": str(e),
                "success_count": 0,
                "total": len(items),
                "results": [],
            }
        finally:
            self.cleanup()

    def _store_item(self, repo: Repository, config_type: str, name: str, path: str):
        """将单个配置项存储到仓库

        Args:
            repo: 仓库实例
            config_type: 配置类型
            name: 配置名称
            path: 配置项路径字符串

        Returns:
            版本号字符串（如 'V1'），失败时返回 None
        """
        item_path = Path(path)

        if config_type == ConfigType.RULES.value:
            content = item_path.read_text(encoding="utf-8")
            return repo.store_rule(name, content)
        elif config_type == ConfigType.SKILLS.value:
            return repo.store_skill(name, item_path)
        elif config_type == ConfigType.MCP.value:
            return repo.store_mcp(name, item_path)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")


import_service = ImportService()
