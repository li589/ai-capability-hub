---
title: Chip Identification Flow
impact: HIGH
impactDescription: Incorrect identification leads to wrong chip data in all subsequent queries
tags: flow, identification, trigger, chip-model
---

## Chip Identification Flow

The chip identification flow is the entry point for all ChipCtx queries. A correct chipId is required before calling any other MCP Tool.

## Trigger Conditions

Activate the chip identification flow when ANY of the following conditions are detected:

### 1. Explicit Trigger (User mentions chip model)
- User explicitly mentions a chip model: "STM32F407", "ESP32-S3", "nRF52840"
- User mentions a chip series: "STM32F4 series", "ESP32"
- User asks to find or compare chips: "which chip has BLE support?"

### 2. Code Context Trigger (Chip-specific headers/APIs)
- Code contains chip-specific headers: `stm32f4xx.h`, `esp_system.h`, `nrf.h`, `nrf52840.h`
- Code uses chip-specific HAL/SDK functions: `HAL_GPIO_Init()`, `esp_wifi_init()`, `nrf_gpio_cfg_output()`
- Code references chip-specific registers or memory addresses

### 3. Project Configuration Trigger (Build system files)
- `.ioc` files (STM32CubeMX projects)
- `platformio.ini` with `board = ...` configuration
- `Makefile` or `CMakeLists.txt` containing MCU definitions (`-DSTM32F407xx`)
- `sdkconfig` files (ESP-IDF projects)
- `prj.conf` files (Zephyr/nRF Connect SDK projects)

### 4. Topic-Related Trigger (Hardware discussion)
- User discusses pin assignments, peripheral configuration, register operations
- User asks about GPIO, UART, SPI, I2C, ADC, DMA, timer configuration
- User mentions datasheet, TRM, or hardware design topics

## MCP Server Setup (MUST check before first query)

Before attempting any chip query, verify that `chip_identify` is available as an MCP tool in the current session.

**If `chip_identify` is NOT available:**
1. Run: `claude mcp add --transport http chipctx --scope user https://mcp.chipctx.com`
2. Tell the user: "ChipCtx MCP server has been configured. Please restart Claude Code (`/quit` then relaunch) for the MCP tools to become available. Then retry your query."
3. **STOP.** Do NOT attempt to call any ChipCtx MCP tool or fall back to WebFetch. The user MUST restart first.

**If `chip_identify` IS available:** Proceed to the identification flow below.

## Identification Flow

### Step 1: Extract Chip Model Keywords
Extract chip model information from:
- User's message text (highest priority)
- Code files in the current context
- Project configuration files

### Step 2: Call chip_identify
```
chip_identify({ query: "<extracted model string>" })
```

### Step 3: Evaluate matchScore
Analyze the returned results:
- **matchScore >= 0.9**: High confidence, single match — proceed directly
- **matchScore 0.7-0.9**: Moderate confidence — confirm with user if only 1 result; if multiple, present top 3
- **matchScore < 0.7**: Low confidence — present candidates and ask user to confirm or clarify

### Step 4: Confirm or Select
- **Single high-confidence match**: Use directly, inform user which chip was identified
- **Multiple candidates**: Present a numbered list with model, vendor, and series; ask user to select
- **No match**: Inform user and suggest checking the model name (see Error Handling below)

### Step 5: Cache chipId
Store the confirmed `chipId` in session context for subsequent queries. All further MCP Tool calls use this cached chipId.

## Error Handling

### Model Not Found
When `chips` array is empty or `total` is 0:
1. Inform the user: "Could not find chip model 'XXX' in the database"
2. Suggest checking spelling or trying a broader search (e.g., series name instead of full part number)
3. If the query is a partial match, suggest similar models from the same vendor

### Ambiguous Input
When results contain many candidates with low matchScore:
1. Present the top 5 candidates with model, vendor, and description
2. Ask the user to select or provide a more specific model name
3. Do NOT proceed with a low-confidence match silently

### MCP Tool Not Found
When `chip_identify` or other ChipCtx tools are not available in the session:
1. Run: `claude mcp add --transport http chipctx --scope user https://mcp.chipctx.com`
2. Inform the user to restart Claude Code for the tools to load
3. Do NOT fall back to WebFetch or other workarounds

### Network Error
When the MCP call fails due to network issues:
1. Inform the user: "Unable to reach ChipCtx server. Please check your network connection."
2. Suggest verifying MCP server endpoint: `https://mcp.chipctx.com`
3. Suggest retry after checking connectivity

## Examples

**Correct usage:**
```
User: "Help me configure UART on STM32F407"
Agent: Extract "STM32F407" -> chip_identify({query: "STM32F407"})
       -> matchScore 0.95 -> confirmed as STM32F407VGT6
       -> cache chipId for subsequent calls
```

**Correct usage (project context):**
```
User: "Help me implement a 1ms timer" (project contains stm32f4xx.h)
Agent: Detect stm32f4xx.h -> extract "STM32F4"
       -> chip_identify({query: "STM32F4"})
       -> multiple candidates -> ask user to specify exact model
```

**Incorrect usage:**
```
User: "Help me configure UART on STM32F407"
Agent: Directly calls chip_trm without first calling chip_identify
       -> ERROR: chipId is unknown, query will fail
```

**Incorrect usage:**
```
Agent: Gets matchScore 0.5 for "F4" query
       -> Silently picks first result without confirming
       -> ERROR: May use wrong chip's data
```
