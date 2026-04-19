# Project Structure

## Workspace Layout

```
.kiro/                  # Kiro IDE configuration
├── specs/              # Feature specs
│   └── msr-cli/        # Main feature spec (requirements, design, tasks)
└── steering/           # Steering rules (this directory)

MSR-cli/                # Source code root (currently empty, implementation pending)
```

## Architecture Patterns

### Adapter Pattern

Each supported IDE has an adapter responsible for:
- Resolving platform-specific config paths (macOS vs Windows)
- Converting unified repo format to IDE-specific format (e.g., adding frontmatter headers)
- Reading/writing to the correct IDE directories

Supported adapters: `trae`, `qoder`, `lingma`, `codebuddy`

### Config Types

Three distinct config types, each with its own import/sync logic:
- **rules** — Single Markdown files
- **skills** — Directories (identified by containing `SKILL.md`)
- **mcp** — JSON config directories

### Versioning

Configs are versioned with `V<n>` directories. On import, if a name collision occurs, the version number increments. On sync, the latest version is used by default unless `--version` is specified.

### Scope

- **global** — User-level IDE config paths (default)
- **project** — Project-level IDE config paths (requires `--project-dir` or uses cwd)

## Key Design Decisions

- The unified repository is always at `~/.msr-repos` (not configurable)
- Import from URLs downloads to a temp location, extracts, then imports
- Bulk imports (folders/archives with multiple items) require user confirmation
- MCP sync merges into existing `mcp.json` rather than overwriting the whole file
- Rule sync strips source frontmatter and applies IDE-specific frontmatter templates
