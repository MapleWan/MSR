"""全局状态管理模块"""

from datetime import datetime
from typing import Dict, List

from nicegui import run


class AppState:
    """应用全局状态"""

    def __init__(self):
        self.repo_status: dict = {}          # 仓库状态 {path, exists, breakdown}
        self.config_list: dict = {}          # 配置列表缓存 {rules: {name: [versions]}, ...}
        self.selected_ides: List[str] = []   # 当前选中的 IDE
        self.operation_logs: List[dict] = [] # 操作日志列表

    def add_log(self, message: str, level: str = "info"):
        """添加操作日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.operation_logs.append({
            "timestamp": timestamp,
            "message": message,
            "level": level,
        })

    async def refresh(self):
        """刷新仓库状态和配置列表"""
        from msr_gui.services.repo_service import repo_service

        try:
            self.repo_status = await repo_service.get_repo_status()
            self.config_list = await repo_service.list_configs()
            self.add_log("状态刷新成功", "success")
        except Exception as e:
            self.add_log(f"状态刷新失败: {e}", "error")


# 全局单例
app_state = AppState()
