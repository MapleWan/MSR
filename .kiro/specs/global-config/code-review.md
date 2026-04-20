# 代码评审报告 — 全局配置 (Global Config)

## 变更范围

本次需求新增 1 个模块，修改 4 个模块，新增 1 个异常类：

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `msr_sync/core/config.py` | **新增** | GlobalConfig 类、load_config、单例管理 |
| `msr_sync/core/exceptions.py` | 修改 | 新增 ConfigFileError |
| `msr_sync/core/source_resolver.py` | 修改 | 新增 `_should_ignore` 方法和过滤逻辑 |
| `msr_sync/core/repository.py` | 修改 | `Repository.__init__` 改为从配置读取默认路径 |
| `msr_sync/cli.py` | 修改 | sync 命令默认值改为从配置读取 |
| `pyproject.toml` | 修改 | 新增 `pyyaml>=6.0` 依赖 |
| `tests/conftest.py` | 修改 | 新增 autouse fixture 重置配置单例 |

## 整体评价

实现质量良好，设计文档中的接口定义被忠实执行。向后兼容性处理到位——无配置文件时行为与之前完全一致。以下按优先级列出发现的问题。

---

## 🔴 需要修复的问题

### 1. `_should_ignore` 中 `_is_single_mcp` 的判断可能被忽略模式干扰

**文件：** `source_resolver.py`

`_is_single_mcp` 通过检查根目录是否有非子目录文件来判断是单个还是多个 MCP。但 `_should_ignore` 过滤只在 `_resolve_mcp_directory` 的多 MCP 分支中生效，不在 `_is_single_mcp` 中生效。

考虑这个场景：一个目录只包含 `.DS_Store` 文件和若干子目录。`_is_single_mcp` 会因为 `.DS_Store` 的存在返回 `True`，将整个目录视为单个 MCP，而不是预期的多个 MCP。

**建议修复：** 在 `_is_single_mcp` 中也应用忽略模式过滤：

```python
@staticmethod
def _is_single_mcp(path: Path) -> bool:
    for entry in path.iterdir():
        if not entry.is_dir():
            # 被忽略的文件不应影响分类判断
            if not self._should_ignore(entry.name):
                return True
    return False
```

注意：这需要将 `_is_single_mcp` 从 `@staticmethod` 改为普通方法。同理 `_is_single_skill` 也可能受影响（如果 `SKILL.md` 恰好在忽略列表中，虽然实际不太可能）。

### 2. `CONFIG_FILE_PATH` 在模块加载时求值

**文件：** `config.py:16`

```python
CONFIG_FILE_PATH = Path.home() / ".msr-sync" / "config.yaml"
```

`Path.home()` 在模块导入时就被求值了。如果测试中 monkeypatch 了 `Path.home()`，这个常量不会跟着变。当前测试通过 `load_config(config_path)` 显式传入路径绕过了这个问题，但如果有人直接调用 `get_config()` 而没有先 `init_config()`，会读取真实的 home 目录。

**建议修复：** 将 `CONFIG_FILE_PATH` 改为函数：

```python
def _default_config_path() -> Path:
    return Path.home() / ".msr-sync" / "config.yaml"
```

---

## 🟡 建议改进

### 3. `_validate_ides` 和 `_validate_scope` 中的延迟 import click

```python
@staticmethod
def _validate_ides(raw):
    ...
    for ide in raw:
        if ide in VALID_IDES:
            valid.append(ide)
        else:
            import click  # ← 每次无效条目都执行
            click.echo(...)
```

虽然 Python 会缓存模块，但在 `@staticmethod` 中延迟 import 不够规范。建议将 `import click` 移到文件顶部。`config.py` 已经是一个会被 CLI 工具使用的模块，依赖 click 是合理的。

### 4. `_resolve_repo_path` 手动处理 `~/` 前缀

```python
if path_str.startswith("~/") or path_str == "~":
    return Path.home() / path_str[2:] if len(path_str) > 2 else Path.home()
return Path(path_str).expanduser()
```

这里手动拆分 `~/` 是为了让 monkeypatch `Path.home()` 在测试中生效（`Path.expanduser()` 不受 monkeypatch 影响）。逻辑正确，但建议加一行注释说明原因，否则后续维护者可能会"简化"为 `Path(raw).expanduser()` 导致测试失败。

### 5. `_should_ignore` 每次调用都读取 `get_config()`

```python
def _should_ignore(self, name: str) -> bool:
    from msr_sync.core.config import get_config
    patterns = get_config().ignore_patterns
    ...
```

在批量扫描大目录时，每个文件都会调用一次 `get_config()`。虽然单例模式保证了不会重复加载文件，但可以考虑在 `SourceResolver.__init__` 中缓存一次 `ignore_patterns`，减少函数调用开销。对于当前规模的使用场景影响不大，但如果未来处理包含数千文件的目录会有差异。

### 6. 缺少 `msr-sync config` 子命令

当前用户需要手动创建 `~/.msr-sync/config.yaml`。可以考虑后续添加：
- `msr-sync config init` — 生成带注释的默认配置文件
- `msr-sync config show` — 显示当前生效的配置

这不是本次需求的范围，但值得记录为后续改进。

### 7. `ignore_patterns` 不支持递归匹配

当前 `_should_ignore` 只匹配文件名/目录名，不支持路径模式（如 `**/node_modules`）。对于当前需求足够，但如果用户需要更复杂的忽略规则（类似 `.gitignore`），可能需要扩展。

---

## 🟢 做得好的地方

1. **向后兼容性完美** — 无配置文件时所有行为与之前完全一致，328 个原有测试零回归
2. **单例生命周期管理** — `get_config` / `init_config` / `reset_config` 三件套设计清晰，`conftest.py` 的 autouse fixture 确保测试隔离
3. **优雅降级策略** — 文件不存在、空文件、非字典 YAML、部分配置缺失都能正确回退到默认值，只有 YAML 语法错误才终止
4. **校验与警告分离** — 无效 IDE 名称和无效 scope 输出中文警告但不终止，过滤后继续工作
5. **属性测试覆盖全面** — 6 个 Property 覆盖了配置加载、路径展开、IDE 过滤、scope 回退、往返一致性等核心正确性属性
6. **集成点改动最小化** — `repository.py` 只改了 `__init__` 的 3 行，`cli.py` 只改了 sync 命令的默认值处理，`source_resolver.py` 只在 3 个目录扫描循环中各加了 2 行过滤
7. **延迟导入避免循环依赖** — `_should_ignore` 和 `Repository.__init__` 中使用函数内 import 避免了 `config.py` ↔ 其他模块的循环导入
8. **pyyaml 选型合理** — 使用 `yaml.safe_load` 而非 `yaml.load`，避免了 YAML 反序列化安全风险

---

## 总结

本次全局配置功能实现质量高，向后兼容性处理到位，测试覆盖充分（34 个新测试，含 6 个属性测试）。主要需要关注的是 `_is_single_mcp` 中忽略模式未生效的问题（可能导致 `.DS_Store` 干扰 MCP 分类判断），以及 `CONFIG_FILE_PATH` 模块级常量在测试中的潜在问题。其余建议为代码风格和可维护性改进，不影响功能正确性。
