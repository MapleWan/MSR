"""同步任务服务 — 封装 sync 相关逻辑，直接调用底层方法避免 click 依赖"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from nicegui import run
from msr_sync.adapters.base import BaseAdapter
from msr_sync.adapters.registry import resolve_ide_list
from msr_sync.constants import ConfigType, MCP_CONFIG_FILE
from msr_sync.core.exceptions import ConfigNotFoundError, ConfigParseError, MSRError, RepositoryNotFoundError
from msr_sync.core.frontmatter import strip_frontmatter
from msr_sync.core.repository import Repository
from msr_sync.core.version import get_latest_version

from msr_gui.state import app_state


class SyncService:
    async def sync_configs(
        self,
        ide_names: list,
        scope: str,
        project_dir: str = None,
        config_type: str = None,
        name: str = None,
        version: str = None,
        confirm_overrides: dict = None,
    ) -> dict:
        """执行同步操作，返回结果摘要

        Args:
            ide_names: 目标 IDE 名称列表
            scope: 同步层级 ('global' 或 'project')
            project_dir: 项目目录路径，scope 为 'project' 时使用
            config_type: 配置类型过滤（rules/skills/mcp），None 表示全部
            name: 配置名称过滤，None 表示全部
            version: 指定版本，None 表示最新版本
            confirm_overrides: 用户确认覆盖的字典，key 格式为 "{config_type}/{name}/{ide_name}"

        Returns:
            同步结果摘要字典
        """
        confirm_overrides = confirm_overrides or {}

        def _sync():
            repo = Repository()
            if not repo.exists():
                raise RepositoryNotFoundError("统一仓库未初始化，请先执行 `msr-sync init`")

            resolved_project_dir: Optional[Path] = None
            if scope == "project":
                if project_dir is not None:
                    resolved_project_dir = Path(project_dir)
                else:
                    resolved_project_dir = Path.cwd()

            adapters = resolve_ide_list(tuple(ide_names))

            if config_type is not None:
                types_to_sync = [config_type]
            else:
                types_to_sync = [
                    ConfigType.RULES.value,
                    ConfigType.SKILLS.value,
                    ConfigType.MCP.value,
                ]

            try:
                all_configs = repo.list_configs()
            except RepositoryNotFoundError:
                raise

            total_synced = 0
            results = []

            for ct in types_to_sync:
                configs = all_configs.get(ct, {})

                if name is not None:
                    if name in configs:
                        configs = {name: configs[name]}
                    else:
                        results.append({
                            "config_type": ct,
                            "name": name,
                            "status": "skipped",
                            "reason": "配置不存在",
                        })
                        continue

                if not configs:
                    continue

                for config_name, versions in configs.items():
                    display_ver = version or (versions[-1] if versions else "?")

                    for adapter in adapters:
                        try:
                            count = self._sync_config(
                                repo=repo,
                                adapter=adapter,
                                config_type=ct,
                                config_name=config_name,
                                version=version,
                                scope=scope,
                                project_dir=resolved_project_dir,
                                confirm_overrides=confirm_overrides,
                            )
                            total_synced += count
                            results.append({
                                "config_type": ct,
                                "name": config_name,
                                "version": display_ver,
                                "ide": adapter.ide_name,
                                "status": "synced" if count > 0 else "skipped",
                                "count": count,
                            })
                        except ConfigNotFoundError as e:
                            results.append({
                                "config_type": ct,
                                "name": config_name,
                                "ide": adapter.ide_name,
                                "status": "error",
                                "error": str(e),
                            })
                        except Exception as e:
                            results.append({
                                "config_type": ct,
                                "name": config_name,
                                "ide": adapter.ide_name,
                                "status": "error",
                                "error": str(e),
                            })

            return {
                "success": True,
                "total_synced": total_synced,
                "results": results,
            }

        try:
            result = await run.io_bound(_sync)
            app_state.add_log(f"同步完成: 共 {result['total_synced']} 项", "success")
            return result
        except MSRError as e:
            app_state.add_log(f"同步失败: {e}", "error")
            return {"success": False, "error": str(e), "total_synced": 0, "results": []}

    def _sync_config(
        self,
        repo: Repository,
        adapter: BaseAdapter,
        config_type: str,
        config_name: str,
        version: Optional[str],
        scope: str,
        project_dir: Optional[Path],
        confirm_overrides: Dict[str, bool],
    ) -> int:
        """同步单个配置到单个 IDE"""
        resolved_version = version
        if resolved_version is None:
            config_dir = repo.base_path / repo._resolve_config_dir(config_type) / config_name
            resolved_version = get_latest_version(config_dir)

        if config_type == ConfigType.RULES.value:
            return self._sync_rule(
                repo, adapter, config_name, version, resolved_version, scope, project_dir
            )
        elif config_type == ConfigType.MCP.value:
            return self._sync_mcp(
                repo, adapter, config_name, version, resolved_version, confirm_overrides
            )
        elif config_type == ConfigType.SKILLS.value:
            return self._sync_skill(
                repo, adapter, config_name, version, resolved_version, scope, project_dir,
                confirm_overrides
            )
        return 0

    def _sync_rule(
        self,
        repo: Repository,
        adapter: BaseAdapter,
        rule_name: str,
        version: Optional[str],
        resolved_version: Optional[str],
        scope: str,
        project_dir: Optional[Path],
    ) -> int:
        """同步单个 rule"""
        if scope == "global" and not adapter.supports_global_rules():
            return 0

        raw_content = repo.read_rule_content(rule_name, version)
        stripped_content = strip_frontmatter(raw_content)
        formatted_content = adapter.format_rule_content(stripped_content)
        target_path = adapter.get_rules_path(rule_name, scope, project_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(formatted_content, encoding="utf-8")
        return 1

    def _sync_mcp(
        self,
        repo: Repository,
        adapter: BaseAdapter,
        mcp_name: str,
        version: Optional[str],
        resolved_version: Optional[str],
        confirm_overrides: Dict[str, bool],
    ) -> int:
        """同步单个 MCP 配置"""
        source_dir = repo.get_config_path(ConfigType.MCP.value, mcp_name, version)
        source_mcp_file = source_dir / MCP_CONFIG_FILE

        if not source_mcp_file.is_file():
            return 0

        try:
            source_data = json.loads(source_mcp_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError) as e:
            raise ConfigParseError(f"MCP 配置文件格式错误: {source_mcp_file}: {e}")

        source_servers = source_data.get("mcpServers", {})
        if not source_servers:
            return 0

        # cwd 路径重写
        for server_config in source_servers.values():
            if "cwd" in server_config:
                server_config["cwd"] = str(source_dir)

        target_path = adapter.get_mcp_path()
        return self._merge_mcp_config(source_servers, target_path, adapter.ide_name, confirm_overrides)

    def _merge_mcp_config(
        self,
        source_servers: Dict,
        target_path: Path,
        ide_name: str,
        confirm_overrides: Dict[str, bool],
    ) -> int:
        """合并 MCP 配置到目标 mcp.json"""
        synced = 0

        if target_path.is_file():
            try:
                target_data = json.loads(target_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError) as e:
                raise ConfigParseError(f"MCP 配置文件格式错误: {target_path}: {e}")
        else:
            target_data = {}

        if "mcpServers" not in target_data:
            target_data["mcpServers"] = {}

        for server_name, server_config in source_servers.items():
            key = f"mcp/{server_name}/{ide_name}"
            if server_name in target_data["mcpServers"]:
                if confirm_overrides.get(key, False):
                    target_data["mcpServers"][server_name] = server_config
                    synced += 1
                # 未确认则跳过
            else:
                target_data["mcpServers"][server_name] = server_config
                synced += 1

        if synced > 0:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                json.dumps(target_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return synced

    def _sync_skill(
        self,
        repo: Repository,
        adapter: BaseAdapter,
        skill_name: str,
        version: Optional[str],
        resolved_version: Optional[str],
        scope: str,
        project_dir: Optional[Path],
        confirm_overrides: Dict[str, bool],
    ) -> int:
        """同步单个 skill"""
        source_dir = repo.get_config_path(ConfigType.SKILLS.value, skill_name, version)
        target_path = adapter.get_skills_path(skill_name, scope, project_dir)
        key = f"skills/{skill_name}/{adapter.ide_name}"

        if target_path.exists():
            if confirm_overrides.get(key, False):
                shutil.rmtree(target_path)
                shutil.copytree(source_dir, target_path)
                return 1
            return 0
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_dir, target_path)
            return 1

    async def preview_sync(
        self,
        ide_names: list,
        scope: str,
        config_type: str = None,
        name: str = None,
        version: str = None,
        project_dir: str = None,
    ) -> list:
        """预览将要同步的操作列表

        Returns:
            预览项列表，每项包含 config_type, name, version, ide, action, key
            action 取值: sync, overwrite, conflict, skip_unsupported, skip_no_config, skip_no_servers
        """

        def _preview():
            repo = Repository()
            if not repo.exists():
                return []

            resolved_project_dir: Optional[Path] = None
            if scope == "project":
                if project_dir is not None:
                    resolved_project_dir = Path(project_dir)
                else:
                    resolved_project_dir = Path.cwd()

            adapters = resolve_ide_list(tuple(ide_names))

            if config_type is not None:
                types_to_sync = [config_type]
            else:
                types_to_sync = [
                    ConfigType.RULES.value,
                    ConfigType.SKILLS.value,
                    ConfigType.MCP.value,
                ]

            try:
                all_configs = repo.list_configs()
            except RepositoryNotFoundError:
                return []

            previews = []

            for ct in types_to_sync:
                configs = all_configs.get(ct, {})
                if name is not None:
                    configs = {name: configs[name]} if name in configs else {}

                for config_name, versions in configs.items():
                    display_ver = version or (versions[-1] if versions else "?")
                    for adapter in adapters:
                        action = self._preview_config_action(
                            repo, adapter, ct, config_name, version, scope, resolved_project_dir
                        )
                        if action:
                            key = f"{ct}/{config_name}/{adapter.ide_name}"
                            previews.append({
                                "config_type": ct,
                                "name": config_name,
                                "version": display_ver,
                                "ide": adapter.ide_name,
                                "action": action,
                                "key": key,
                            })

            return previews

        return await run.io_bound(_preview)

    def _preview_config_action(
        self,
        repo: Repository,
        adapter: BaseAdapter,
        config_type: str,
        config_name: str,
        version: Optional[str],
        scope: str,
        project_dir: Optional[Path],
    ) -> Optional[str]:
        """判断单个配置的同步动作类型"""
        if config_type == ConfigType.RULES.value:
            if scope == "global" and not adapter.supports_global_rules():
                return "skip_unsupported"
            target = adapter.get_rules_path(config_name, scope, project_dir)
            return "overwrite" if target.exists() else "sync"

        elif config_type == ConfigType.SKILLS.value:
            target = adapter.get_skills_path(config_name, scope, project_dir)
            return "overwrite" if target.exists() else "sync"

        elif config_type == ConfigType.MCP.value:
            source_dir = repo.get_config_path(ConfigType.MCP.value, config_name, version)
            source_mcp = source_dir / MCP_CONFIG_FILE
            if not source_mcp.is_file():
                return "skip_no_config"
            try:
                source_data = json.loads(source_mcp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError):
                return "skip_no_config"
            source_servers = source_data.get("mcpServers", {})
            if not source_servers:
                return "skip_no_servers"

            target_path = adapter.get_mcp_path()
            if target_path.is_file():
                try:
                    target_data = json.loads(target_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, ValueError):
                    return "overwrite"
                existing = target_data.get("mcpServers", {})
                if any(s in existing for s in source_servers):
                    return "conflict"
            return "sync"

        return None


sync_service = SyncService()
