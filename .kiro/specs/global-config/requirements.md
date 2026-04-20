# 需求文档

## 简介

MSR-cli（`msr-sync`）当前的仓库路径、默认 IDE 列表、默认同步层级等参数均为硬编码常量，且导入/扫描流程缺少对操作系统元数据目录（如 macOS 的 `__MACOSX`）的过滤机制。本特性引入全局配置文件 `~/.msr-sync/config.yaml`，允许用户自定义上述参数及忽略模式，同时保持所有配置项的合理默认值，确保在无配置文件时工具行为不变。

代码实现位于工作区根目录下的 `MSR-cli/` 文件夹中。

## 术语表

- **Global_Config**: 全局配置模块，负责加载、解析和提供 `~/.msr-sync/config.yaml` 中的用户配置
- **Config_File**: 位于 `~/.msr-sync/config.yaml` 的 YAML 格式全局配置文件
- **Ignore_Pattern**: 在导入扫描和压缩包解压过程中需要跳过的目录名或文件通配符模式（如 `__MACOSX`、`*.pyc`）
- **Repo_Path**: 统一仓库的根目录路径，默认为 `~/.msr-repos`
- **Default_IDEs**: 用户偏好的默认同步目标 IDE 列表，默认为 `all`
- **Default_Scope**: 用户偏好的默认同步层级，默认为 `global`
- **Source_Resolver**: 导入来源解析器，负责将用户提供的导入来源解析为具体的配置项列表
- **MSR_CLI**: 命令行工具主程序，命令名为 `msr-sync`
- **YAML_Parser**: 用于解析 YAML 格式配置文件的解析器组件

## 需求列表

### 需求 1：配置文件加载与解析

**用户故事：** 作为开发者，我希望工具能从 `~/.msr-sync/config.yaml` 加载全局配置，以便通过一个配置文件自定义工具的各项行为。

#### 验收标准

1. 当 `~/.msr-sync/config.yaml` 文件存在且内容为合法 YAML 时，Global_Config 应解析该文件并返回包含所有已配置项的配置对象
2. 当 `~/.msr-sync/config.yaml` 文件不存在时，Global_Config 应返回包含所有默认值的配置对象，工具行为与未引入本特性前完全一致
3. 当 `~/.msr-sync/config.yaml` 文件存在但内容为空时，Global_Config 应返回包含所有默认值的配置对象
4. 当 `~/.msr-sync/config.yaml` 文件包含非法 YAML 语法时，Global_Config 应输出包含文件路径的中文错误提示信息并终止执行
5. 当配置文件中仅设置了部分配置项时，Global_Config 应对已设置的配置项使用用户值，对未设置的配置项使用默认值

### 需求 2：忽略模式配置

**用户故事：** 作为开发者，我希望配置忽略模式列表，以便在导入扫描和压缩包解压时自动跳过操作系统元数据目录和其他无关文件。

#### 验收标准

1. Global_Config 应提供 `ignore_patterns` 配置项，其值为字符串列表，默认值为 `["__MACOSX", ".DS_Store", "__pycache__", ".git"]`
2. 当 Source_Resolver 扫描目录以检测配置项时，Source_Resolver 应跳过名称与任一 Ignore_Pattern 精确匹配的目录和文件
3. 当 Source_Resolver 扫描目录以检测配置项时，Source_Resolver 应跳过名称与任一包含通配符的 Ignore_Pattern 匹配的文件（使用 `fnmatch` 语义）
4. 当 Source_Resolver 解压压缩包后扫描解压内容时，Source_Resolver 应使用相同的忽略模式过滤解压后的目录和文件
5. 忽略模式过滤应仅作用于条目的文件名或目录名部分，不作用于完整路径

### 需求 3：自定义仓库路径

**用户故事：** 作为开发者，我希望通过配置文件自定义统一仓库的存储路径，以便将仓库放置在我偏好的位置。

#### 验收标准

1. Global_Config 应提供 `repo_path` 配置项，其值为字符串类型的目录路径，默认值为 `~/.msr-repos`
2. 当 `repo_path` 配置项包含波浪号 `~` 前缀时，Global_Config 应将其展开为用户主目录的绝对路径
3. 当 Repository 实例化时未显式传入 `base_path` 参数时，Repository 应使用 Global_Config 提供的 `repo_path` 值作为仓库根目录
4. 当 `repo_path` 配置值为空字符串时，Global_Config 应使用默认值 `~/.msr-repos`

### 需求 4：默认 IDE 列表配置

**用户故事：** 作为只使用部分 IDE 的开发者，我希望配置默认的同步目标 IDE 列表，以便执行 `msr-sync sync` 时无需每次手动指定 `--ide` 参数。

#### 验收标准

1. Global_Config 应提供 `default_ides` 配置项，其值为字符串列表，默认值为 `["all"]`
2. 当用户执行 `msr-sync sync` 且未指定 `--ide` 参数时，MSR_CLI 应使用 Global_Config 提供的 `default_ides` 值作为目标 IDE 列表
3. 当用户执行 `msr-sync sync` 且显式指定了 `--ide` 参数时，MSR_CLI 应使用用户在命令行中指定的值，忽略 Global_Config 中的 `default_ides`
4. 当 `default_ides` 配置值包含不在支持列表（trae、qoder、lingma、codebuddy、all）中的 IDE 名称时，Global_Config 应输出包含无效 IDE 名称的中文警告信息并忽略该无效条目
5. 当 `default_ides` 配置值为空列表时，Global_Config 应使用默认值 `["all"]`

### 需求 5：默认同步层级配置

**用户故事：** 作为团队开发者，我希望配置默认的同步层级，以便执行 `msr-sync sync` 时无需每次手动指定 `--scope` 参数。

#### 验收标准

1. Global_Config 应提供 `default_scope` 配置项，其值为字符串类型，可选值为 `global` 或 `project`，默认值为 `global`
2. 当用户执行 `msr-sync sync` 且未指定 `--scope` 参数时，MSR_CLI 应使用 Global_Config 提供的 `default_scope` 值作为同步层级
3. 当用户执行 `msr-sync sync` 且显式指定了 `--scope` 参数时，MSR_CLI 应使用用户在命令行中指定的值，忽略 Global_Config 中的 `default_scope`
4. 当 `default_scope` 配置值不是 `global` 或 `project` 时，Global_Config 应输出包含无效值的中文警告信息并使用默认值 `global`

### 需求 6：配置文件格式与示例

**用户故事：** 作为开发者，我希望有清晰的配置文件格式说明和示例，以便快速上手配置。

#### 验收标准

1. Config_File 应使用 YAML 格式，支持以 `#` 开头的注释行
2. Config_File 应支持以下顶层配置键：`repo_path`（字符串）、`ignore_patterns`（字符串列表）、`default_ides`（字符串列表）、`default_scope`（字符串）
3. 当配置文件包含未识别的顶层配置键时，Global_Config 应忽略该键并继续正常加载其他配置项

### 需求 7：YAML 配置文件解析与序列化

**用户故事：** 作为开发者，我希望配置文件的解析是可靠的，以便工具能正确读取我的配置。

#### 验收标准

1. YAML_Parser 应能正确解析包含字符串、字符串列表、注释行的 YAML 配置文件
2. 对于所有合法的配置对象，将其序列化为 YAML 再解析回配置对象后，所有配置项的值应与原始配置对象一致（往返一致性）
3. YAML_Parser 应能正确处理 YAML 中带引号的字符串值（如 `"*.pyc"`）和不带引号的字符串值（如 `__MACOSX`）
