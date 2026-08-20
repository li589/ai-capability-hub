---
title: Context Injection Flow
impact: HIGH
impactDescription: Proper context injection ensures AI generates accurate chip-specific code
tags: flow, context, injection, context-window
---

## Context Injection Flow

After chip identification, inject relevant chip specification data into the AI's working context to enable accurate code generation and technical guidance.

## Injection Timing

### 1. On First Identification
When a chip model is first confirmed via chip_identify:
- Immediately call `chip_specs(chipId, "overview")` to load core parameters
- Cache the overview (CPU core, max frequency, flash, RAM) in session context
- This provides baseline knowledge for all subsequent interactions

### 2. When Discussing Specific Peripherals
When the user asks about a specific peripheral (UART, SPI, I2C, ADC, etc.):
- Call `chip_hardware(chipId, query: "<peripheral>")` to load pin assignments
- Call `chip_trm(chipId, section: "<peripheral>")` for register details if needed
- Load only the relevant peripheral data, not all peripherals at once

### 3. When Writing Code
When generating initialization code or driver implementations:
- Call `chip_programming_guide(chipId, topic: "<peripheral>")` for SDK/HAL examples
- Include prerequisites (clock configuration) and common pitfalls
- Reference the specific SDK version when available

## 3-Layer Injection Strategy

### Layer 1: Always Inject (Core Parameters)
Always present in context after chip identification:
- Chip model name and vendor
- CPU core type (e.g., ARM Cortex-M4)
- Maximum clock frequency (e.g., 168 MHz)
- Flash and RAM capacity
- Operating voltage range

### Layer 2: On-Demand Inject (Peripheral Details)
Load when user discusses specific hardware topics:
- Peripheral specifications (available interfaces, counts, features)
- Pin definitions and alternate functions for specific peripherals
- Package information (pin count, dimensions)

### Layer 3: Deep Inject (Register-Level Details)
Load when writing low-level or register-direct code:
- TRM register definitions (name, address, bit fields, access type)
- Programming guide with complete initialization sequences
- Code examples with both HAL and register-level implementations

## Context Management Constraints

### Avoid Context Window Overflow
- **Do NOT** load all chip data at once — TRM data alone can be thousands of lines
- Load only the data relevant to the current task
- Prefer summary/overview data first; load detailed data only when needed
- When context is large, summarize previously loaded data before adding new data

### Prioritize Relevant Information
- When user asks about UART, load UART-related data — not SPI or I2C
- When user switches topics (e.g., from UART to ADC), load ADC data
- Keep the most recently discussed peripheral data readily accessible

### Chip Switching Protocol
When the user switches to a different chip model:
1. Clear all cached chip context (chipId, specs, peripheral data)
2. Run the chip identification flow for the new chip
3. Load fresh overview data via `chip_specs`
4. Do NOT mix data from the old chip with the new chip — this leads to incorrect register addresses and pin assignments

## Project-Level Auto-Injection Flow

For project-wide chip context (when chip is detected from project files):

```
1. Scan project files -> detect chip model
2. chip_identify(query) -> confirm model
3. chip_specs(chipId, "overview") -> load core params
4. Cache chipId and overview in session
5. All subsequent queries auto-use cached chipId
6. On peripheral-specific questions -> load detailed data on demand
```

## Examples

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
