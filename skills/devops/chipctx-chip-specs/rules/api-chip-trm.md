---
title: chip_trm Interface Guide
impact: HIGH
impactDescription: Provides authoritative register definitions critical for low-level code correctness
tags: api, chip_trm, trm, registers, technical-reference
---

## chip_trm Interface Guide

`chip_trm` queries the chip's Technical Reference Manual (TRM) content, providing register definitions, module functional descriptions, and configuration procedures.

## Interface Signature

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

## Section Filtering

### By Peripheral Name
Pass the peripheral name as `section` to get relevant chapters:
- `section: "UART"` or `"USART"` -> UART/USART module documentation
- `section: "GPIO"` -> GPIO port configuration
- `section: "RCC"` -> Reset and Clock Control
- `section: "TIM"` or `"Timer"` -> Timer modules
- `section: "ADC"` -> Analog-to-Digital Converter
- `section: "DMA"` -> Direct Memory Access
- `section: "SPI"` -> Serial Peripheral Interface
- `section: "I2C"` -> Inter-Integrated Circuit

### Without Filter
Omitting `section` returns a summary of all available TRM sections (table of contents style), not the full manual content.

## Register Data Format

### Reading Register Definitions
Each `Register` object contains the register name, address offset, and an array of `RegisterField` entries. Use these for:
- Calculating correct register addresses (base address + offset)
- Setting individual bit fields for peripheral configuration
- Understanding access constraints (read-only, write-only, read-clear)

### RegisterField Values
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

## Usage Guidelines

### When to Call
- User needs register addresses or bit field definitions
- Writing register-level (bare-metal) driver code
- Debugging peripheral configuration issues
- Understanding module functional behavior from official documentation

### Prerequisite
Always call `chip_identify` first to obtain `chipId`. Do NOT guess chipId values.

## Examples

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

## Error Handling

### TRM Not Available
When the chip has no TRM data in the database:
- Inform user: "TRM data is not yet available for [chipModel]"
- Suggest checking `chip_specs` for basic peripheral information
- Note that TRM coverage is expanding over time

### Section Not Found
When the requested section does not exist for this chip:
- Return the list of available sections so user can choose a valid one
- Suggest alternative section names (e.g., "USART" instead of "UART" for STM32)
- Some chips use different peripheral naming conventions
