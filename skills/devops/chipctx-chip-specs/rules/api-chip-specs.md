---
title: chip_specs Interface Guide
impact: MEDIUM
impactDescription: Provides core chip parameters for context injection and code generation decisions
tags: api, chip_specs, specifications, parameters, electrical
---

## chip_specs Interface Guide

`chip_specs` queries chip specification parameters including core info, electrical characteristics, features, and peripheral lists.

## Interface Signature

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

## Category Queries

### overview (default)
Returns core chip parameters. This is the most commonly used query and is the default when `category` is omitted.

Use for: Initial context injection, quick parameter lookups, chip comparison.

### electrical
Returns detailed electrical specifications including supply voltage ranges, I/O pin voltage tolerance, operating temperature range, and power consumption per operating mode.

**Important:** Electrical specs include both typical and limit values (min/max). Always reference limit values when designing circuits or validating operating conditions.

Use for: Circuit design validation, power budget calculations, temperature range verification.

### features
Returns the chip's key feature list (included in overview, but may contain additional detail).

Use for: Feature comparison, capability verification.

### peripherals
Returns a detailed list of all available peripherals with instance counts and feature descriptions.

Use for: Peripheral availability checks, interface planning, determining how many UART/SPI/I2C instances are available.

## Usage Guidelines

### When to Call
- After chip identification, call with `"overview"` to establish baseline context
- When user asks about chip parameters, frequencies, memory sizes
- When comparing chip capabilities
- When user needs electrical specifications for hardware design

### Context Injection Role
`chip_specs(chipId, "overview")` is the primary tool for Layer 1 (Always Inject) context. Call it immediately after chip identification to populate core parameters.

## Examples

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

## Error Handling

### Incomplete Data
When some specification fields are unavailable:
- The response returns available data with missing fields omitted or marked
- Inform user which data is available and which is not yet in the database
- Do NOT fabricate or estimate missing specification values

### Series-Level Query (Model Too Broad)
When `chipId` corresponds to a series rather than a specific model:
- Response returns series-common parameters (shared across the series)
- Inform user: "Showing series-level specs for [series]. For exact values (pin count, flash size), specify a full part number."
- Suggest using `chip_identify` to find specific models within the series
