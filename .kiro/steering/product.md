# Product Overview

MSR-cli (`msr-sync`) is a lightweight Python CLI tool for unified management of AI IDE configurations across multiple Chinese AI IDEs: Trae (ByteDance), Qoder/Lingma (Alibaba), and CodeBuddy (Tencent).

## Core Problem

Each AI IDE stores rules, skills, and MCP configs in different formats and paths. Migrating or sharing configurations across IDEs requires manual copying and format conversion.

## Solution

A centralized local repository at `~/.msr-repos` with subdirectories `RULES/`, `SKILLS/`, and `MCP/`. The tool handles importing configs from various sources, converting formats per IDE, and syncing to the correct paths.

## Key Capabilities

- **Init**: Create/initialize the unified repository; optionally merge existing IDE configs
- **Import**: Import rules (.md files), skills (directories with SKILL.md), and MCP configs (JSON) from files, folders, archives, or URLs
- **Sync**: Push configs from the unified repo to one or more target IDEs, with format adaptation per IDE
- **List**: View all stored configs in a tree format
- **Remove**: Delete specific config versions
- **Versioning**: Each config supports multiple versions (V1, V2, V3…)

## Supported IDEs

| IDE | Vendor | Rules | Skills | MCP |
|-----|--------|-------|--------|-----|
| Trae | ByteDance | ✓ | ✓ | ✓ |
| Qoder | Alibaba | ✓ | ✓ | ✓ |
| Lingma | Alibaba | ✓ | ✓ | ✓ |
| CodeBuddy | Tencent | ✓ | ✓ | ✓ |

## Cross-Platform

Supports macOS and Windows with platform-specific path resolution.
