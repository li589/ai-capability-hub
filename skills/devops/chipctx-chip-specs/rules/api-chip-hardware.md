---
title: chip_hardware Interface Guide
impact: HIGH
impactDescription: Incorrect pin assignments cause hardware damage or non-functional circuits
tags: api, chip_hardware, pinout, package, gpio, alternate-function
---

## chip_hardware Interface Guide

`chip_hardware` queries chip pin definitions, alternate functions (AF), and package information. Critical for PCB design and peripheral pin assignment.

## Interface Signature

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

## Query Modes

### Filter by Function Name
Find all pins supporting a specific peripheral:
```
chip_hardware({ chipId: "...", query: "SPI1" })
-> Returns pins with SPI1 in mainFunction or alternateFunctions
```
Use for: Finding which pins to use for a peripheral, planning pin assignments.

### Filter by Pin Number/Name
Look up what functions a specific pin supports:
```
chip_hardware({ chipId: "...", query: "PA0" })
-> Returns PA0's full definition including all alternate functions
```
Use for: Checking pin capabilities during PCB review, resolving pin conflicts.

### Filter by Dimension
Get package information only:
```
chip_hardware({ chipId: "...", query: "package" })
-> Returns PackageInfo with type, dimensions, pitch
```

### No Filter (Full Pinout)
```
chip_hardware({ chipId: "..." })
-> Returns complete pin table and package info
```
**Caution:** Full pinout can be very large (100+ pins). Use filtered queries when possible.

## Alternate Function (AF) Mapping

### Understanding AF Numbers
Most MCUs support pin multiplexing through Alternate Functions:
- Each I/O pin can serve multiple peripheral functions
- AF numbers (AF0-AF15 for STM32) determine which function is active
- Only one AF can be active per pin at a time

### Using AF Data for Code Generation
When generating pin configuration code, use the AF data to:
1. Select the correct GPIO alternate function mode
2. Set the correct AF number in GPIO configuration registers
3. Verify that the chosen pin actually supports the desired peripheral

## Usage Guidelines

### When to Call
- User asks about pin definitions or GPIO assignments
- Before generating peripheral initialization code (to determine correct pins)
- During PCB design discussions (pin mapping, package selection)
- When resolving pin conflict issues

### Common Patterns
```
1. User asks: "Which pins can I use for SPI1?"
   -> chip_hardware(chipId, query: "SPI1")

2. User asks: "What functions does PA9 support?"
   -> chip_hardware(chipId, query: "PA9")

3. User asks: "What package options are available?"
   -> chip_hardware(chipId, query: "package")
```

## Examples

**Query SPI pins on ESP32-S3:**
```
chip_hardware({ chipId: "esp32s3", query: "SPI" })
-> { pins: [
     { pinName: "GPIO11", mainFunction: "SPI2_MOSI", alternateFunctions: [...] },
     { pinName: "GPIO12", mainFunction: "SPI2_CLK", alternateFunctions: [...] },
     ...
   ], package: { type: "QFN56", pinCount: 56, ... } }
```

## Error Handling

### Package Info Not Available
When package data is not in the database:
- Inform user which package types are available for this chip
- Suggest checking the chip's datasheet for detailed mechanical drawings
- Return available pin data even if package details are missing

### Alternate Function Conflict
When multiple peripherals compete for the same pin:
- Flag the conflict: "Pin PA9 is shared between USART1_TX (AF7) and TIM1_CH2 (AF1)"
- Advise user to choose one function and find alternative pins for the other
- Suggest checking alternate pins for the conflicting peripheral
