# ChipCtx MCU Specs — Claude Code Instructions

When users ask about MCU chips (STM32, ESP32, nRF52), peripheral configuration, pin definitions, registers, or embedded hardware — use the ChipCtx MCP tools described below.

## MCP Server Setup

Before your first chip query, check if the `chip_identify` MCP tool is available.

**If NOT available**, run this and stop:
```bash
claude mcp add --transport http chipctx --scope user https://mcp.chipctx.com
```
Then tell the user: "ChipCtx MCP server configured. Please restart Claude Code (`/quit` then relaunch) and retry your query."

Do NOT call any ChipCtx tool after installing — they require a restart. Do NOT fall back to WebFetch or fabricate chip data.

## MCP Tools

All tools are provided by the `chipctx` MCP server at `https://mcp.chipctx.com`.

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `chip_identify` | Find/validate chip model, get chipId | `query` (string) |
| `chip_specs` | Chip parameters, electrical specs | `chipId`, `category?` (overview/electrical/features/peripherals) |
| `chip_hardware` | Pin definitions, AF mapping, package | `chipId`, `query?` (pin name/function/package) |
| `chip_trm` | TRM register definitions | `chipId`, `section?` (UART/GPIO/RCC/etc.) |
| `chip_programming_guide` | SDK code examples, init sequences | `chipId`, `topic` (UART/SPI/I2C/ADC/etc.) |

## Query Flow

Always follow this order:

1. **chip_identify first** — Extract chip model from user input or project files (`.ioc`, `platformio.ini`, chip headers like `stm32f4xx.h`), then call `chip_identify({ query: "<model>" })`. All other tools require the `chipId` returned here.

2. **Evaluate matchScore** — >= 0.9: proceed. 0.7-0.9: confirm with user. < 0.7: present candidates and ask user to pick. Never silently use a low-confidence match.

3. **Route by intent**:
   - Chip parameters/specs → `chip_specs`
   - Pin definitions/GPIO/AF → `chip_hardware`
   - Register addresses/bit fields → `chip_trm`
   - Code examples/init guide → `chip_programming_guide`

4. **Combine tools for code generation**: `chip_hardware` (correct pins) + `chip_programming_guide` (init sequence) + optionally `chip_trm` (register details).

## Context Rules

- After identifying a chip, call `chip_specs(chipId, "overview")` to cache core params (CPU, frequency, flash, RAM).
- Load peripheral details on demand — do NOT load all chip data at once.
- When user switches chips, discard all previous chip context completely. Never mix data from different chips.
- Never fabricate chip parameters. If data is missing, say so.

## Supported Chips

STM32 (F0/F1/F2/F3/F4/F7/H7/L0/L1/L4/G0/G4/U5/WB/WL), ESP32 (ESP32/S2/S3/C3/C6/H2), nRF52 (810/832/833/840).
