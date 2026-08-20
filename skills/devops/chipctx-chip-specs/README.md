# ChipCtx MCU Specs

Authoritative MCU chip specification query Skill for AI coding agents. Provides real-time, accurate chip technical information.

## Features

- **Chip Identification** — Fuzzy matching, alias recognition, multi-candidate selection
- **Technical Reference Manual** — Register definitions, bit fields, module documentation
- **Chip Specifications** — Core parameters, electrical characteristics, peripheral lists
- **Hardware Information** — Pin definitions, alternate functions, package specifications
- **Programming Guides** — SDK/HAL code examples, initialization sequences, common pitfalls

## Supported Chip Families

| Vendor | Series |
|--------|--------|
| STMicroelectronics | STM32F0/F1/F2/F3/F4/F7/H7/L0/L1/L4/G0/G4/U5/WB/WL |
| Espressif | ESP32/ESP32-S2/S3/C3/C6/H2 |
| Nordic Semiconductor | nRF52810/832/833/840 |

## File Structure

```
chip-specs/
├── SKILL.md              # Core Skill definition (AI Agent entry point)
├── metadata.json         # Version and metadata
├── rules/                # Detailed rules (progressive loading)
│   ├── _sections.md          # Section index and loading strategy
│   ├── flow-chip-identify.md # Chip identification flow
│   ├── flow-context-inject.md# Context injection strategy
│   ├── api-chip-identify.md  # chip_identify interface guide
│   ├── api-chip-trm.md       # chip_trm interface guide
│   ├── api-chip-specs.md      # chip_specs interface guide
│   ├── api-chip-hardware.md   # chip_hardware interface guide
│   └── api-chip-programming.md# chip_programming_guide interface guide
├── AGENTS.md             # All rules compiled into single file
└── README.md             # This file
```

## Installation

### Claude Code Plugin (Recommended)

Install as a Claude Code Plugin — MCP server is auto-configured, no manual setup needed:

```
/plugin marketplace add chipctx/skills
/plugin install chipctx@chipctx-marketplace
```

After installation, restart Claude Code and start querying chips directly.

### npx skills

```bash
npx skills add chipctx/skills -a claude-code
```

## MCP Server Configuration

When using `npx skills` (not Plugin), you need to configure the MCP server separately:

**Claude Code** (one-liner):
```bash
claude mcp add --transport http chipctx --scope user https://mcp.chipctx.com
```

Or manually edit `~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "chipctx": {
      "type": "http",
      "url": "https://mcp.chipctx.com"
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "chipctx": {
      "url": "https://mcp.chipctx.com",
      "transport": "streamable-http"
    }
  }
}
```

> **Note:** When installed as a Claude Code Plugin, the MCP server is auto-configured via `.mcp.json` — no manual setup required.

## MCP Tools

| Tool | Description |
|------|-------------|
| `chip_identify` | Identify and validate chip models |
| `chip_trm` | Query Technical Reference Manual content |
| `chip_specs` | Query chip specifications and parameters |
| `chip_hardware` | Query pin definitions and package info |
| `chip_programming_guide` | Get programming guides and code examples |
