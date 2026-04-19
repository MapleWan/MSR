# Tech Stack & Build

## Language

- Python (CLI application)

## CLI Framework

- Command name: `msr-sync`
- Subcommands: `init`, `import`, `sync`, `list`, `remove`

## Key Libraries (Expected)

- Archive handling (zip/tar extraction)
- HTTP client for downloading archives from URLs
- JSON parsing for MCP config files
- YAML frontmatter parsing for rule Markdown files
- Cross-platform path resolution (`pathlib` or `os.path`)

## Data Formats

- **Rules**: Markdown files with optional YAML frontmatter
- **Skills**: Directories containing `SKILL.md` and related files
- **MCP configs**: JSON files (`mcp.json`)

## Unified Repository Layout

```
~/.msr-repos/
├── RULES/
│   └── <rule-name>/
│       ├── V1/
│       └── V2/
├── SKILLS/
│   └── <skill-name>/
│       ├── V1/
│       └── V2/
└── MCP/
    └── <mcp-name>/
        ├── V1/
        └── V2/
```

## Common Commands

```bash
# Initialize the unified repository
msr-sync init

# Initialize and merge existing IDE configs
msr-sync init --merge

# Import a rule
msr-sync import rules <source>

# Sync all configs to all IDEs (global scope)
msr-sync sync

# Sync rules to a specific IDE at project scope
msr-sync sync --type rules --ide trae --scope project

# List all configs
msr-sync list

# Remove a specific version
msr-sync remove <type> <name> <version>
```

## Notes

- All user-facing messages should be in Chinese (the target audience is Chinese developers)
- The project is in early development; the `MSR-cli/` directory is the source root
