# 单元测试报告

## 测试环境

| 项目 | 信息 |
|------|------|
| 平台 | macOS (darwin) |
| Python | 3.12.11 |
| pytest | 9.0.2 |
| hypothesis | 6.151.11 |
| 执行时间 | 7.22s |

## 测试结果总览

| 指标 | 数值 |
|------|------|
| **总测试数** | 328 |
| **通过** | 328 ✅ |
| **失败** | 0 |
| **错误** | 0 |
| **跳过** | 0 |
| **警告** | 3（tarfile DeprecationWarning，Python 3.14 兼容性提示） |
| **通过率** | 100% |

## 按模块分布

| 测试文件 | 测试数 | 覆盖模块 |
|---------|--------|---------|
| `test_adapters.py` | 55 | 跨适配器属性测试 + 单元测试（Property 10） |
| `test_adapters_base.py` | 16 | BaseAdapter 抽象类 + Registry |
| `test_cli_integration.py` | 9 | CLI 入口集成测试 |
| `test_codebuddy_adapter.py` | 24 | CodeBuddy 适配器 |
| `test_commands.py` | 26 | init/list/remove/import 命令处理器 |
| `test_exceptions.py` | 20 | 异常层次结构 |
| `test_frontmatter.py` | 28 | Frontmatter 解析与生成（Property 4） |
| `test_integration.py` | 12 | 端到端集成测试 |
| `test_lingma_adapter.py` | 17 | Lingma 适配器 |
| `test_mcp_merge.py` | 1 | MCP JSON 合并（Property 8） |
| `test_platform.py` | 11 | 平台检测 |
| `test_qoder_adapter.py` | 17 | Qoder 适配器 |
| `test_repository.py` | 22 | 仓库操作（Property 9） |
| `test_source_resolver.py` | 19 | 来源解析器（Property 5/6/7） |
| `test_trae_adapter.py` | 17 | Trae 适配器 |
| `test_version.py` | 34 | 版本管理（Property 1/2/3） |

## 属性基测试 (Property-Based Tests)

| Property | 描述 | 迭代次数 | 状态 |
|----------|------|---------|------|
| P1 | 版本号格式往返一致性 | 100 | ✅ |
| P2 | 版本递增正确性 | 100 | ✅ |
| P3 | 最新版本选择正确性 | 100 | ✅ |
| P4 | Frontmatter 剥离与 IDE 头部转换 | 100×5 | ✅ |
| P5 | 来源解析器检测完整性 | 100×3 | ✅ |
| P6 | MCP 单/多配置分类正确性 | 100×2 | ✅ |
| P7 | Skill 单/多配置分类正确性 | 100×2 | ✅ |
| P8 | MCP JSON 合并保留已有条目 | 100 | ✅ |
| P9 | 配置列表输出完整性 | 100×3 | ✅ |
| P10 | IDE 路径解析正确性 | 100×2 | ✅ |

## 已知警告

```
DeprecationWarning: Python 3.14 will, by default, filter extracted tar archives 
and reject files or modify their metadata. Use the filter argument to control this behavior.
```

影响范围：`source_resolver.py` 中的 `tf.extractall(extract_dir)`，3 个测试触发。建议在 Python 3.14 发布前添加 `filter` 参数。
