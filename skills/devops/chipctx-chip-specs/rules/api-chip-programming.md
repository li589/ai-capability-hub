---
title: chip_programming_guide Interface Guide
impact: MEDIUM
impactDescription: Programming guides ensure generated code follows chip vendor best practices
tags: api, chip_programming_guide, programming, code-example, sdk, hal
---

## chip_programming_guide Interface Guide

`chip_programming_guide` retrieves programming guidance and code examples for specific chip peripherals, based on official SDK/HAL documentation.

## Interface Signature

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

## Code Generation Rules

### Based on Official SDK/HAL
All code examples are based on the chip vendor's official SDK or HAL library:
- **STM32**: STM32 HAL Library / LL (Low-Layer) drivers
- **ESP32**: ESP-IDF framework
- **nRF52**: nRF5 SDK / nRF Connect SDK (Zephyr-based)

Code examples follow the vendor's recommended coding patterns and API usage.

### Complete Initialization Sequence
Programming guides include the full initialization sequence in correct order:
1. **Clock configuration** — Enable peripheral and GPIO clocks
2. **GPIO configuration** — Set pin modes, alternate functions, pull-ups/downs
3. **Peripheral configuration** — Set peripheral-specific parameters (baud rate, data bits, etc.)
4. **Interrupt configuration** (if applicable) — NVIC priority, enable IRQ
5. **Enable peripheral** — Final enable step

### Dual Implementation Approach
When applicable, guides provide two implementation styles:
- **HAL/SDK level**: Using high-level API functions (recommended for most users)
- **Register level**: Direct register manipulation (for advanced users or constrained environments)

Not all peripherals have both implementations. Some vendor SDKs only provide one approach.

## Usage Guidelines

### When to Call
- User asks "how to initialize/configure [peripheral] on [chip]"
- Before generating peripheral driver code
- When debugging initialization issues ("my UART isn't working")
- To get the correct SDK function calls and parameters

### Combining with Other Tools
For complete code generation, combine with:
1. `chip_hardware` — get correct pin assignments for the peripheral
2. `chip_trm` — get register details if register-level code is needed
3. `chip_programming_guide` — get the initialization sequence and example code

## Examples

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

## Error Handling

### No Programming Guide Available
When no guide exists for the requested topic:
- Inform user: "No programming guide available for [topic] on [chipModel]"
- Return a list of available topics for this chip
- Suggest related topics (e.g., if "CAN" not available, suggest "CAN FD" or other communication interfaces)

### SDK Version Differences
When code examples are version-specific:
- Clearly mark the applicable SDK version (e.g., "STM32 HAL v1.27.1", "ESP-IDF v5.1")
- Warn user if the API has changed in newer versions
- Note any known breaking changes between SDK versions
