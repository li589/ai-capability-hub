# ChipCtx MCU Specs — Complete Rule Reference

> **Version:** 1.2.0 | **Organization:** chipctx | **Date:** 2026-03-07
>
> **Abstract:** Query authoritative MCU chip specifications including parameters, pin definitions, registers, and programming guides. Use when users mention chip models (STM32, ESP32, nRF52), ask about peripheral configuration, or work with embedded hardware design. This document contains the full content of all `rules/` files merged into a single document for platforms that support one-file loading.
>
> **Note:** This is an auto-compiled version. The canonical source for each rule is the individual file in `rules/`. When in doubt, refer to the source files.

---

## Table of Contents

1. [Chip Identification Flow](#1-chip-identification-flow) (HIGH)
2. [Context Injection Flow](#2-context-injection-flow) (HIGH)
3. [chip_identify Interface Guide](#3-chip_identify-interface-guide) (HIGH)
4. [chip_trm Interface Guide](#4-chip_trm-interface-guide) (HIGH)
5. [chip_specs Interface Guide](#5-chip_specs-interface-guide) (MEDIUM)
6. [chip_hardware Interface Guide](#6-chip_hardware-interface-guide) (HIGH)
7. [chip_programming_guide Interface Guide](#7-chip_programming_guide-interface-guide) (MEDIUM)

---

## 1. Chip Identification Flow

**Impact: HIGH** — Incorrect identification leads to wrong chip data in all subsequent queries

### Trigger Conditions

Activate the chip identification flow when ANY of the following conditions are detected:

#### 1. Explicit Trigger (User mentions chip model)
- User explicitly mentions a chip model: "STM32F407", "ESP32-S3", "nRF52840"
- User mentions a chip series: "STM32F4 series", "ESP32"
- User asks to find or compare chips: "which chip has BLE support?"

#### 2. Code Context Trigger (Chip-specific headers/APIs)
- Code contains chip-specific headers: `stm32f4xx.h`, `esp_system.h`, `nrf.h`, `nrf52840.h`
- Code uses chip-specific HAL/SDK functions: `HAL_GPIO_Init()`, `esp_wifi_init()`, `nrf_gpio_cfg_output()`
- Code references chip-specific registers or memory addresses

#### 3. Project Configuration Trigger (Build system files)
- `.ioc` files (STM32CubeMX projects)
- `platformio.ini` with `board = ...` configuration
- `Makefile` or `CMakeLists.txt` containing MCU definitions (`-DSTM32F407xx`)
- `sdkconfig` files (ESP-IDF projects)
- `prj.conf` files (Zephyr/nRF Connect SDK projects)

#### 4. Topic-Related Trigger (Hardware discussion)
- User discusses pin assignments, peripheral configuration, register operations
- User asks about GPIO, UART, SPI, I2C, ADC, DMA, timer configuration
- User mentions datasheet, TRM, or hardware design topics

### MCP Server Setup (MUST check before first query)

Before making any chip query, verify that `chip_identify` is available as an MCP tool in the current session.

**If `chip_identify` is NOT available:**
1. Run: `claude mcp add --transport http chipctx --scope user https://mcp.chipctx.com`
2. Tell the user: "ChipCtx MCP server has been configured. Please restart Claude Code (`/quit` then relaunch) for the MCP tools to become available. Then retry your query."
3. **STOP.** Do NOT attempt to call any ChipCtx MCP tool or fall back to WebFetch. The user MUST restart first.

**If `chip_identify` IS available:** Proceed to the identification flow below.

### Identification Flow

#### Step 1: Extract Chip Model Keywords
Extract chip model information from:
- User's message text (highest priority)
- Code files in the current context
- Project configuration files

#### Step 2: Call chip_identify
```
chip_identify({ query: "<extracted model string>" })
```

#### Step 3: Evaluate matchScore
Analyze the returned results:
- **matchScore >= 0.9**: High confidence, single match — proceed directly
- **matchScore 0.7-0.9**: Moderate confidence — confirm with user if only 1 result; if multiple, present top 3
- **matchScore < 0.7**: Low confidence — present candidates and ask user to confirm or clarify

#### Step 4: Confirm or Select
- **Single high-confidence match**: Use directly, inform user which chip was identified
- **Multiple candidates**: Present a numbered list with model, vendor, and series; ask user to select
- **No match**: Inform user and suggest checking the model name (see Error Handling below)

#### Step 5: Cache chipId
Store the confirmed `chipId` in session context for subsequent queries. All further MCP Tool calls use this cached chipId.

### Error Handling

#### Model Not Found
When `chips` array is empty or `total` is 0:
1. Inform the user: "Could not find chip model 'XXX' in the database"
2. Suggest checking spelling or trying a broader search (e.g., series name instead of full part number)
3. If the query is a partial match, suggest similar models from the same vendor

#### Ambiguous Input
When results contain many candidates with low matchScore:
1. Present the top 5 candidates with model, vendor, and description
2. Ask the user to select or provide a more specific model name
3. Do NOT proceed with a low-confidence match silently

#### MCP Tool Not Found
When `chip_identify` or other ChipCtx tools are not available in the session:
1. Run: `claude mcp add --transport http chipctx --scope user https://mcp.chipctx.com`
2. Inform the user to restart Claude Code for the tools to load
3. Do NOT fall back to WebFetch or other workarounds

#### Network Error
When the MCP call fails due to network issues:
1. Inform the user: "Unable to reach ChipCtx server. Please check your network connection."
2. Suggest verifying MCP server endpoint: `https://mcp.chipctx.com`
3. Suggest retry after checking connectivity

### Examples

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

---

## 2. Context Injection Flow

**Impact: HIGH** — Proper context injection ensures AI generates accurate chip-specific code

### Injection Timing

#### 1. On First Identification
When a chip model is first confirmed via chip_identify:
- Immediately call `chip_specs(chipId, "overview")` to load core parameters
- Cache the overview (CPU core, max frequency, flash, RAM) in session context
- This provides baseline knowledge for all subsequent interactions

#### 2. When Discussing Specific Peripherals
When the user asks about a specific peripheral (UART, SPI, I2C, ADC, etc.):
- Call `chip_hardware(chipId, query: "<peripheral>")` to load pin assignments
- Call `chip_trm(chipId, section: "<peripheral>")` for register details if needed
- Load only the relevant peripheral data, not all peripherals at once

#### 3. When Writing Code
When generating initialization code or driver implementations:
- Call `chip_programming_guide(chipId, topic: "<peripheral>")` for SDK/HAL examples
- Include prerequisites (clock configuration) and common pitfalls
- Reference the specific SDK version when available

### 3-Layer Injection Strategy

#### Layer 1: Always Inject (Core Parameters)
Always present in context after chip identification:
- Chip model name and vendor
- CPU core type (e.g., ARM Cortex-M4)
- Maximum clock frequency (e.g., 168 MHz)
- Flash and RAM capacity
- Operating voltage range

#### Layer 2: On-Demand Inject (Peripheral Details)
Load when user discusses specific hardware topics:
- Peripheral specifications (available interfaces, counts, features)
- Pin definitions and alternate functions for specific peripherals
- Package information (pin count, dimensions)

#### Layer 3: Deep Inject (Register-Level Details)
Load when writing low-level or register-direct code:
- TRM register definitions (name, address, bit fields, access type)
- Programming guide with complete initialization sequences
- Code examples with both HAL and register-level implementations

### Context Management Constraints

#### Avoid Context Window Overflow
- **Do NOT** load all chip data at once — TRM data alone can be thousands of lines
- Load only the data relevant to the current task
- Prefer summary/overview data first; load detailed data only when needed
- When context is large, summarize previously loaded data before adding new data

#### Prioritize Relevant Information
- When user asks about UART, load UART-related data — not SPI or I2C
- When user switches topics (e.g., from UART to ADC), load ADC data
- Keep the most recently discussed peripheral data readily accessible

#### Chip Switching Protocol
When the user switches to a different chip model:
1. Clear all cached chip context (chipId, specs, peripheral data)
2. Run the chip identification flow for the new chip
3. Load fresh overview data via `chip_specs`
4. Do NOT mix data from the old chip with the new chip — this leads to incorrect register addresses and pin assignments

### Project-Level Auto-Injection Flow

For project-wide chip context (when chip is detected from project files):

```
1. Scan project files -> detect chip model
2. chip_identify(query) -> confirm model
3. chip_specs(chipId, "overview") -> load core params
4. Cache chipId and overview in session
5. All subsequent queries auto-use cached chipId
6. On peripheral-specific questions -> load detailed data on demand
```

### Examples

**Correct: Progressive loading**
```
User: "I'm working with STM32F407"
Agent: chip_identify -> chip_specs(overview) -> cache core params
       [Only core params in context]

User: "Configure UART1 for 115200 baud"
Agent: chip_hardware(query: "UART1") -> chip_programming_guide(topic: "UART")
       [Add UART pin mapping and programming guide to context]
```

**Incorrect: Loading everything at once**
```
User: "I'm working with STM32F407"
Agent: chip_identify -> chip_specs(all) -> chip_trm(all sections)
       -> chip_hardware(all pins) -> chip_programming_guide(all topics)
       [Context overflow! Most data is irrelevant to user's actual task]
```

**Correct: Chip switching**
```
User: "Now I need to work with ESP32-S3 instead"
Agent: Clear STM32F407 context -> chip_identify("ESP32-S3")
       -> chip_specs(overview) -> fresh ESP32-S3 context
```

---

## 3. chip_identify Interface Guide

**Impact: HIGH** — Entry point for all chip queries; incorrect identification cascades to all downstream tools

### Interface Signature

```
chip_identify({ query: string })
```

**Parameter:**
- `query` (required): User-provided chip model string. Examples: `"STM32F407VGT6"`, `"ESP32-S3"`, `"nRF52840"`, `"F407"`

**Response:**
```typescript
{
  chips: ChipInfo[],  // Matched chips, sorted by matchScore descending
  total: number       // Total number of matches
}

ChipInfo {
  id: string,          // Unique chip identifier (chipId for other tools)
  model: string,       // Standardized model name, e.g. "STM32F407VGT6"
  vendor: string,      // Vendor name, e.g. "STMicroelectronics"
  series: string,      // Series name, e.g. "STM32F4"
  description: string, // Brief description
  matchScore: number   // Match confidence score (0-1)
}
```

### Matching Behavior

#### Fuzzy Matching
Partial model strings match the entire series:
- `"STM32F4"` -> returns all STM32F4 series models
- `"ESP32"` -> returns all ESP32 variants (ESP32, ESP32-S2, ESP32-S3, ESP32-C3, etc.)
- `"nRF52"` -> returns all nRF52 series models

#### Alias Recognition
Short names and common aliases are recognized:
- `"F407"` -> matches `"STM32F407"` variants
- `"S3"` (in embedded context) -> may match `"ESP32-S3"`
- Vendor-specific abbreviations are supported

#### matchScore Sorting
Results are always sorted by `matchScore` in descending order:
- **1.0**: Exact match (e.g., query `"STM32F407VGT6"` matches model `"STM32F407VGT6"`)
- **0.8-0.99**: Strong match (series or partial model match)
- **0.5-0.79**: Moderate match (alias or fuzzy match)
- **< 0.5**: Weak match (may be unrelated)

### Usage Guidelines

#### When to Call
- **Always call first** before any other ChipCtx MCP tool
- Call whenever a new chip model is mentioned in conversation
- Call when chip context needs to be established from project files

#### How to Use the Response
1. Check `total` — if 0, handle as "model not found"
2. Evaluate top result's `matchScore` (see Section 1 for thresholds)
3. Extract `id` field as `chipId` for subsequent tool calls
4. Use `model` field to confirm with user which chip was matched

### Examples

**Exact match query:**
```
chip_identify({ query: "STM32F407VGT6" })
-> { chips: [{ id: "stm32f407vgt6", model: "STM32F407VGT6",
       vendor: "STMicroelectronics", series: "STM32F4",
       description: "High-performance MCU with FPU...",
       matchScore: 1.0 }], total: 1 }
```

**Fuzzy match query:**
```
chip_identify({ query: "STM32F4" })
-> { chips: [
       { id: "stm32f407vgt6", model: "STM32F407VGT6", matchScore: 0.85, ... },
       { id: "stm32f405rgt6", model: "STM32F405RGT6", matchScore: 0.85, ... },
       ...
     ], total: 15 }
```

**Alias query:**
```
chip_identify({ query: "F407" })
-> { chips: [
       { id: "stm32f407vgt6", model: "STM32F407VGT6", matchScore: 0.75, ... },
       ...
     ], total: 5 }
```

### Error Handling

#### Model Not Found (total = 0)
```
chip_identify({ query: "XXXXNONEXISTENT" })
-> { chips: [], total: 0 }
```
**Action:** Inform user the model was not found. Suggest:
- Check spelling (common mistakes: "STM32F4O7" vs "STM32F407")
- Try a broader search (series name instead of full part number)
- Verify the chip is from a supported family (STM32, ESP32, nRF52)

#### Ambiguous Input (many low-score results)
```
chip_identify({ query: "MCU" })
-> { chips: [...many results with matchScore < 0.5...], total: 100 }
```
**Action:** Ask user to provide a more specific model name. Present top 3-5 candidates if any score above 0.5.

#### Network Error
**Action:** Report connection failure. Suggest checking:
- MCP server endpoint configuration (`https://mcp.chipctx.com`)
- Network connectivity
- Retry the request

---

## 4. chip_trm Interface Guide

**Impact: HIGH** — Provides authoritative register definitions critical for low-level code correctness

### Interface Signature

```
chip_trm({ chipId: string, section?: string })
```

**Parameters:**
- `chipId` (required): Chip identifier from `chip_identify` response
- `section` (optional): Section/module filter. Examples: `"UART"`, `"GPIO"`, `"RCC"`, `"DMA"`, `"ADC"`

**Response:**
```typescript
{
  chipModel: string,
  sections: TrmSection[]
}

TrmSection {
  title: string,       // Section title, e.g. "USART/UART Module"
  content: string,     // Section content in Markdown format
  registers?: Register[]
}

Register {
  name: string,        // Register name, e.g. "USART_CR1"
  address: string,     // Address offset, e.g. "0x00"
  description: string, // Function description
  fields: RegisterField[]
}

RegisterField {
  name: string,        // Field name, e.g. "UE"
  bits: string,        // Bit range, e.g. "13", "7:0", "31:16"
  access: string,      // Access type: "RW", "RO", "WO", "RC_W1"
  description: string, // Field description
  values?: Record<string, string>  // Optional enum values
}
```

### Section Filtering

#### By Peripheral Name
Pass the peripheral name as `section` to get relevant chapters:
- `section: "UART"` or `"USART"` -> UART/USART module documentation
- `section: "GPIO"` -> GPIO port configuration
- `section: "RCC"` -> Reset and Clock Control
- `section: "TIM"` or `"Timer"` -> Timer modules
- `section: "ADC"` -> Analog-to-Digital Converter
- `section: "DMA"` -> Direct Memory Access
- `section: "SPI"` -> Serial Peripheral Interface
- `section: "I2C"` -> Inter-Integrated Circuit

#### Without Filter
Omitting `section` returns a summary of all available TRM sections (table of contents style), not the full manual content.

### Register Data Format

#### Reading Register Definitions
Each `Register` object contains the register name, address offset, and an array of `RegisterField` entries. Use these for:
- Calculating correct register addresses (base address + offset)
- Setting individual bit fields for peripheral configuration
- Understanding access constraints (read-only, write-only, read-clear)

#### RegisterField Values
The optional `values` map provides enum-like descriptions:
```json
{
  "name": "OVER8",
  "bits": "15",
  "access": "RW",
  "description": "Oversampling mode",
  "values": { "0": "Oversampling by 16", "1": "Oversampling by 8" }
}
```

### Usage Guidelines

#### When to Call
- User needs register addresses or bit field definitions
- Writing register-level (bare-metal) driver code
- Debugging peripheral configuration issues
- Understanding module functional behavior from official documentation

#### Prerequisite
Always call `chip_identify` first to obtain `chipId`. Do NOT guess chipId values.

### Examples

**Query UART registers:**
```
chip_trm({ chipId: "stm32f407vgt6", section: "UART" })
-> Sections about USART module with CR1, CR2, BRR, SR registers and all fields
```

**Query without filter (get available sections):**
```
chip_trm({ chipId: "stm32f407vgt6" })
-> Summary list of all available TRM sections for this chip
```

### Error Handling

#### TRM Not Available
When the chip has no TRM data in the database:
- Inform user: "TRM data is not yet available for [chipModel]"
- Suggest checking `chip_specs` for basic peripheral information
- Note that TRM coverage is expanding over time

#### Section Not Found
When the requested section does not exist for this chip:
- Return the list of available sections so user can choose a valid one
- Suggest alternative section names (e.g., "USART" instead of "UART" for STM32)
- Some chips use different peripheral naming conventions

---

## 5. chip_specs Interface Guide

**Impact: MEDIUM** — Provides core chip parameters for context injection and code generation decisions

### Interface Signature

```
chip_specs({ chipId: string, category?: string })
```

**Parameters:**
- `chipId` (required): Chip identifier from `chip_identify`
- `category` (optional): One of `"overview"`, `"electrical"`, `"features"`, `"peripherals"`

**Response:**
```typescript
{
  chipModel: string,
  overview: ChipOverview,
  electrical?: ElectricalSpecs,
  peripherals?: PeripheralList
}

ChipOverview {
  core: string,             // e.g. "ARM Cortex-M4"
  maxFrequency: string,     // e.g. "168 MHz"
  flash: string,            // e.g. "1 MB"
  ram: string,              // e.g. "192 KB"
  operatingVoltage: string, // e.g. "1.8V - 3.6V"
  packages: string[],       // e.g. ["LQFP144", "LQFP100"]
  features: string[]        // Key feature list
}

ElectricalSpecs {
  supplyVoltage: { min: string, typical: string, max: string },
  ioPinVoltage: { min: string, max: string },
  operatingTemperature: { min: string, max: string },
  powerConsumption: Record<string, string>  // Per-mode power consumption
}

PeripheralList {
  peripherals: Peripheral[]
}

Peripheral {
  type: string,      // e.g. "UART", "SPI", "I2C"
  count: number,     // Number of instances
  features: string[] // Feature descriptions
}
```

### Category Queries

#### overview (default)
Returns core chip parameters. This is the most commonly used query and is the default when `category` is omitted.

Use for: Initial context injection, quick parameter lookups, chip comparison.

#### electrical
Returns detailed electrical specifications including supply voltage ranges, I/O pin voltage tolerance, operating temperature range, and power consumption per operating mode.

**Important:** Electrical specs include both typical and limit values (min/max). Always reference limit values when designing circuits or validating operating conditions.

Use for: Circuit design validation, power budget calculations, temperature range verification.

#### features
Returns the chip's key feature list (included in overview, but may contain additional detail).

Use for: Feature comparison, capability verification.

#### peripherals
Returns a detailed list of all available peripherals with instance counts and feature descriptions.

Use for: Peripheral availability checks, interface planning, determining how many UART/SPI/I2C instances are available.

### Usage Guidelines

#### When to Call
- After chip identification, call with `"overview"` to establish baseline context
- When user asks about chip parameters, frequencies, memory sizes
- When comparing chip capabilities
- When user needs electrical specifications for hardware design

#### Context Injection Role
`chip_specs(chipId, "overview")` is the primary tool for Layer 1 (Always Inject) context. Call it immediately after chip identification to populate core parameters.

### Examples

**Default overview query:**
```
chip_specs({ chipId: "stm32f407vgt6" })
-> { chipModel: "STM32F407VGT6", overview: { core: "ARM Cortex-M4F",
     maxFrequency: "168 MHz", flash: "1 MB", ram: "192 KB", ... } }
```

**Electrical specs query:**
```
chip_specs({ chipId: "stm32f407vgt6", category: "electrical" })
-> { ..., electrical: { supplyVoltage: { min: "1.8V", typical: "3.3V", max: "3.6V" },
     operatingTemperature: { min: "-40C", max: "85C" }, ... } }
```

### Error Handling

#### Incomplete Data
When some specification fields are unavailable:
- The response returns available data with missing fields omitted or marked
- Inform user which data is available and which is not yet in the database
- Do NOT fabricate or estimate missing specification values

#### Series-Level Query (Model Too Broad)
When `chipId` corresponds to a series rather than a specific model:
- Response returns series-common parameters (shared across the series)
- Inform user: "Showing series-level specs for [series]. For exact values (pin count, flash size), specify a full part number."
- Suggest using `chip_identify` to find specific models within the series

---

## 6. chip_hardware Interface Guide

**Impact: HIGH** — Incorrect pin assignments cause hardware damage or non-functional circuits

### Interface Signature

```
chip_hardware({ chipId: string, query?: string })
```

**Parameters:**
- `chipId` (required): Chip identifier from `chip_identify`
- `query` (optional): Filter by pin number (e.g., `"PA0"`), function name (e.g., `"SPI1"`), or dimension (e.g., `"pinout"`, `"package"`)

**Response:**
```typescript
{
  chipModel: string,
  package: PackageInfo,
  pins: PinDefinition[]
}

PackageInfo {
  type: string,          // e.g. "LQFP144"
  pinCount: number,      // e.g. 144
  dimensions: string,    // e.g. "20x20mm"
  pitch: string          // Pin pitch, e.g. "0.5mm"
}

PinDefinition {
  pinNumber: number | string,  // Physical pin number
  pinName: string,             // Pin name, e.g. "PA0"
  type: string,                // Pin type: "I/O", "Power", "Reset", "Boot"
  mainFunction: string,        // Primary function
  alternateFunctions: AlternateFunction[]
}

AlternateFunction {
  af: string,        // AF number, e.g. "AF7"
  function: string   // Function name, e.g. "USART1_TX"
}
```

### Query Modes

#### Filter by Function Name
Find all pins supporting a specific peripheral:
```
chip_hardware({ chipId: "...", query: "SPI1" })
-> Returns pins with SPI1 in mainFunction or alternateFunctions
```
Use for: Finding which pins to use for a peripheral, planning pin assignments.

#### Filter by Pin Number/Name
Look up what functions a specific pin supports:
```
chip_hardware({ chipId: "...", query: "PA0" })
-> Returns PA0's full definition including all alternate functions
```
Use for: Checking pin capabilities during PCB review, resolving pin conflicts.

#### Filter by Dimension
Get package information only:
```
chip_hardware({ chipId: "...", query: "package" })
-> Returns PackageInfo with type, dimensions, pitch
```

#### No Filter (Full Pinout)
```
chip_hardware({ chipId: "..." })
-> Returns complete pin table and package info
```
**Caution:** Full pinout can be very large (100+ pins). Use filtered queries when possible.

### Alternate Function (AF) Mapping

#### Understanding AF Numbers
Most MCUs support pin multiplexing through Alternate Functions:
- Each I/O pin can serve multiple peripheral functions
- AF numbers (AF0-AF15 for STM32) determine which function is active
- Only one AF can be active per pin at a time

#### Using AF Data for Code Generation
When generating pin configuration code, use the AF data to:
1. Select the correct GPIO alternate function mode
2. Set the correct AF number in GPIO configuration registers
3. Verify that the chosen pin actually supports the desired peripheral

### Usage Guidelines

#### When to Call
- User asks about pin definitions or GPIO assignments
- Before generating peripheral initialization code (to determine correct pins)
- During PCB design discussions (pin mapping, package selection)
- When resolving pin conflict issues

#### Common Patterns
```
1. User asks: "Which pins can I use for SPI1?"
   -> chip_hardware(chipId, query: "SPI1")

2. User asks: "What functions does PA9 support?"
   -> chip_hardware(chipId, query: "PA9")

3. User asks: "What package options are available?"
   -> chip_hardware(chipId, query: "package")
```

### Examples

**Query SPI pins on ESP32-S3:**
```
chip_hardware({ chipId: "esp32s3", query: "SPI" })
-> { pins: [
     { pinName: "GPIO11", mainFunction: "SPI2_MOSI", alternateFunctions: [...] },
     { pinName: "GPIO12", mainFunction: "SPI2_CLK", alternateFunctions: [...] },
     ...
   ], package: { type: "QFN56", pinCount: 56, ... } }
```

### Error Handling

#### Package Info Not Available
When package data is not in the database:
- Inform user which package types are available for this chip
- Suggest checking the chip's datasheet for detailed mechanical drawings
- Return available pin data even if package details are missing

#### Alternate Function Conflict
When multiple peripherals compete for the same pin:
- Flag the conflict: "Pin PA9 is shared between USART1_TX (AF7) and TIM1_CH2 (AF1)"
- Advise user to choose one function and find alternative pins for the other
- Suggest checking alternate pins for the conflicting peripheral

---

## 7. chip_programming_guide Interface Guide

**Impact: MEDIUM** — Programming guides ensure generated code follows chip vendor best practices

### Interface Signature

```
chip_programming_guide({ chipId: string, topic: string })
```

**Parameters:**
- `chipId` (required): Chip identifier from `chip_identify`
- `topic` (required): Programming topic. Examples: `"UART"`, `"I2C"`, `"SPI"`, `"ADC"`, `"DMA"`, `"Timer"`, `"GPIO"`, `"BLE"`, `"WiFi"`

**Response:**
```typescript
{
  chipModel: string,
  topic: string,
  guide: ProgrammingGuide
}

ProgrammingGuide {
  title: string,
  overview: string,
  prerequisites: string[],      // e.g. ["Enable RCC clock for UART peripheral"]
  steps: ProgrammingStep[],
  codeExample: CodeExample,
  pitfalls: string[],           // Common mistakes and warnings
  references: string[]          // Reference documentation links
}

ProgrammingStep {
  order: number,
  title: string,
  description: string,  // Markdown format
  code?: string          // Optional code snippet for this step
}

CodeExample {
  language: string,   // e.g. "c"
  framework: string,  // e.g. "STM32 HAL", "ESP-IDF", "nRF5 SDK", "Zephyr"
  code: string,       // Complete code example
  explanation: string  // Code explanation
}
```

### Code Generation Rules

#### Based on Official SDK/HAL
All code examples are based on the chip vendor's official SDK or HAL library:
- **STM32**: STM32 HAL Library / LL (Low-Layer) drivers
- **ESP32**: ESP-IDF framework
- **nRF52**: nRF5 SDK / nRF Connect SDK (Zephyr-based)

Code examples follow the vendor's recommended coding patterns and API usage.

#### Complete Initialization Sequence
Programming guides include the full initialization sequence in correct order:
1. **Clock configuration** — Enable peripheral and GPIO clocks
2. **GPIO configuration** — Set pin modes, alternate functions, pull-ups/downs
3. **Peripheral configuration** — Set peripheral-specific parameters (baud rate, data bits, etc.)
4. **Interrupt configuration** (if applicable) — NVIC priority, enable IRQ
5. **Enable peripheral** — Final enable step

#### Dual Implementation Approach
When applicable, guides provide two implementation styles:
- **HAL/SDK level**: Using high-level API functions (recommended for most users)
- **Register level**: Direct register manipulation (for advanced users or constrained environments)

Not all peripherals have both implementations. Some vendor SDKs only provide one approach.

### Usage Guidelines

#### When to Call
- User asks "how to initialize/configure [peripheral] on [chip]"
- Before generating peripheral driver code
- When debugging initialization issues ("my UART isn't working")
- To get the correct SDK function calls and parameters

#### Combining with Other Tools
For complete code generation, combine with:
1. `chip_hardware` — get correct pin assignments for the peripheral
2. `chip_trm` — get register details if register-level code is needed
3. `chip_programming_guide` — get the initialization sequence and example code

### Examples

**Query UART programming guide:**
```
chip_programming_guide({ chipId: "stm32f407vgt6", topic: "UART" })
-> { guide: {
     title: "UART Configuration Guide",
     prerequisites: ["Enable USART1 clock via RCC", "Configure GPIO pins PA9/PA10"],
     steps: [
       { order: 1, title: "Enable Clocks", code: "..." },
       { order: 2, title: "Configure GPIO", code: "..." },
       { order: 3, title: "Configure UART Parameters", code: "..." },
       { order: 4, title: "Enable UART", code: "..." }
     ],
     codeExample: { language: "c", framework: "STM32 HAL", code: "...", ... },
     pitfalls: ["Remember to enable GPIO clock before configuring pins", ...]
   } }
```

**Query BLE programming guide (nRF52840):**
```
chip_programming_guide({ chipId: "nrf52840", topic: "BLE" })
-> { guide: {
     title: "BLE Advertising Guide",
     prerequisites: ["SoftDevice S140 enabled", "..."],
     codeExample: { framework: "nRF5 SDK", ... },
     pitfalls: ["Set advertising interval >= 20ms for BLE spec compliance", ...]
   } }
```

### Error Handling

#### No Programming Guide Available
When no guide exists for the requested topic:
- Inform user: "No programming guide available for [topic] on [chipModel]"
- Return a list of available topics for this chip
- Suggest related topics (e.g., if "CAN" not available, suggest "CAN FD" or other communication interfaces)

#### SDK Version Differences
When code examples are version-specific:
- Clearly mark the applicable SDK version (e.g., "STM32 HAL v1.27.1", "ESP-IDF v5.1")
- Warn user if the API has changed in newer versions
- Note any known breaking changes between SDK versions
