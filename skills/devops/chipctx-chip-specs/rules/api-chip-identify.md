---
title: chip_identify Interface Guide
impact: HIGH
impactDescription: Entry point for all chip queries; incorrect identification cascades to all downstream tools
tags: api, chip_identify, identification, matching
---

## chip_identify Interface Guide

`chip_identify` is the gateway tool for all ChipCtx queries. It validates and standardizes chip model input into a `chipId` used by all other tools.

## Interface Signature

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

## Matching Behavior

### Fuzzy Matching
Partial model strings match the entire series:
- `"STM32F4"` -> returns all STM32F4 series models
- `"ESP32"` -> returns all ESP32 variants (ESP32, ESP32-S2, ESP32-S3, ESP32-C3, etc.)
- `"nRF52"` -> returns all nRF52 series models

### Alias Recognition
Short names and common aliases are recognized:
- `"F407"` -> matches `"STM32F407"` variants
- `"S3"` (in embedded context) -> may match `"ESP32-S3"`
- Vendor-specific abbreviations are supported

### matchScore Sorting
Results are always sorted by `matchScore` in descending order:
- **1.0**: Exact match (e.g., query `"STM32F407VGT6"` matches model `"STM32F407VGT6"`)
- **0.8-0.99**: Strong match (series or partial model match)
- **0.5-0.79**: Moderate match (alias or fuzzy match)
- **< 0.5**: Weak match (may be unrelated)

## Usage Guidelines

### When to Call
- **Always call first** before any other ChipCtx MCP tool
- Call whenever a new chip model is mentioned in conversation
- Call when chip context needs to be established from project files

### How to Use the Response
1. Check `total` — if 0, handle as "model not found"
2. Evaluate top result's `matchScore` (see flow-chip-identify.md for thresholds)
3. Extract `id` field as `chipId` for subsequent tool calls
4. Use `model` field to confirm with user which chip was matched

## Examples

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

## Error Handling

### Model Not Found (total = 0)
```
chip_identify({ query: "XXXXNONEXISTENT" })
-> { chips: [], total: 0 }
```
**Action:** Inform user the model was not found. Suggest:
- Check spelling (common mistakes: "STM32F4O7" vs "STM32F407")
- Try a broader search (series name instead of full part number)
- Verify the chip is from a supported family (STM32, ESP32, nRF52)

### Ambiguous Input (many low-score results)
```
chip_identify({ query: "MCU" })
-> { chips: [...many results with matchScore < 0.5...], total: 100 }
```
**Action:** Ask user to provide a more specific model name. Present top 3-5 candidates if any score above 0.5.

### Network Error
**Action:** Report connection failure. Suggest checking:
- MCP server endpoint configuration (`https://mcp.chipctx.com`)
- Network connectivity
- Retry the request
