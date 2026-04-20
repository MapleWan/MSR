# Bugfix Requirements Document

## Introduction

MCP 同步功能存在两个缺陷，导致从统一仓库同步 MCP 配置到 IDE 时无法正常工作：

1. **键名不匹配**：导入的 MCP 配置文件使用标准 MCP 格式的 `mcpServers` 作为键名，但 `_sync_mcp()` 和 `_merge_mcp_config()` 函数使用 `servers` 键名读取和写入，导致无法正确读取源配置中的 server 条目，也无法生成 IDE 可识别的目标配置。
2. **cwd 路径未重写**：同步 MCP 配置时，server 配置中的 `cwd` 字段仍然指向原始路径，未被修改为统一仓库中的实际路径（`~/.msr-repos/MCP/<name>/V<n>/`），导致 MCP server 启动时找不到正确的工作目录。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 源 MCP 配置文件使用 `mcpServers` 作为键名（标准 MCP 格式）THEN `_sync_mcp()` 函数使用 `source_data.get("servers", {})` 读取，返回空字典，导致提示"没有 servers 条目"并跳过同步

1.2 WHEN `_merge_mcp_config()` 将 server 条目写入目标 mcp.json THEN 使用 `target_data["servers"]` 作为键名，生成的配置文件不符合标准 MCP 格式（`mcpServers`），IDE 无法识别

1.3 WHEN 源 MCP server 配置中包含 `cwd` 字段 THEN `_sync_mcp()` 直接将原始 `cwd` 路径传递给目标配置，未将其重写为统一仓库中的实际路径（`~/.msr-repos/MCP/<name>/V<n>/`）

### Expected Behavior (Correct)

2.1 WHEN 源 MCP 配置文件使用 `mcpServers` 作为键名 THEN `_sync_mcp()` 函数 SHALL 使用 `mcpServers` 键名读取源配置中的 server 条目

2.2 WHEN `_merge_mcp_config()` 将 server 条目写入目标 mcp.json THEN SHALL 使用 `mcpServers` 作为键名，确保生成的配置文件符合标准 MCP 格式

2.3 WHEN 源 MCP server 配置中包含 `cwd` 字段 THEN `_sync_mcp()` SHALL 将 `cwd` 值重写为统一仓库中该 MCP 配置版本的实际路径（即 `~/.msr-repos/MCP/<name>/V<n>/`）

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 源 MCP 配置中存在与目标同名的 server 条目 THEN 系统 SHALL CONTINUE TO 提示用户确认是否覆盖

3.2 WHEN 源 MCP 配置中的 server 条目与目标无冲突 THEN 系统 SHALL CONTINUE TO 直接追加新条目

3.3 WHEN 目标 mcp.json 文件不存在 THEN 系统 SHALL CONTINUE TO 新建文件并写入配置

3.4 WHEN 合并 MCP 配置后 THEN 系统 SHALL CONTINUE TO 保留目标文件中所有原有的 server 条目且内容不变

3.5 WHEN 源 MCP server 配置中不包含 `cwd` 字段 THEN 系统 SHALL CONTINUE TO 正常同步该 server 配置，不添加 `cwd` 字段
