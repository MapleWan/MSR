# MSR Sync Manager GUI

MSR Sync Manager 的可视化管理界面，基于 [NiceGUI](https://nicegui.io/) 构建。

## 功能

提供 MSR 配置同步的可视化管理，包括：

- 仪表盘 - 概览与状态监控
- 配置浏览 - 浏览和管理 IDE 配置
- 导入配置 - 从现有配置导入
- 同步面板 - 执行同步操作
- 设置 - 应用设置

## 启动方式

### 开发模式（浏览器）

```bash
msr-gui --browser
```

### 原生窗口模式

```bash
msr-gui
```

### 指定端口

```bash
msr-gui --port 8080
```

## 安装

```bash
pip install -e .
```

## 依赖

- Python >= 3.9
- nicegui >= 2.0
- msr-sync
