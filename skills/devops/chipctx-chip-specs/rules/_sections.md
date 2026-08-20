---
title: Rule Sections Index
impact: HIGH
impactDescription: Defines the organization and loading order of all rule files
tags: index, sections, organization
---

## Rule Sections Index

All rules are organized into the following sections. Load rules progressively based on the current task context.

### Section Overview

| Order | Section ID | File | Impact | Description |
|-------|-----------|------|--------|-------------|
| 1 | flow-identify | flow-chip-identify.md | HIGH | Chip identification trigger conditions, 5-step flow, multi-candidate handling, error recovery |
| 2 | flow-inject | flow-context-inject.md | HIGH | Context injection timing, 3-layer strategy, context window management, chip switching |
| 3 | api-identify | api-chip-identify.md | HIGH | chip_identify interface: fuzzy matching, alias recognition, matchScore sorting |
| 4 | api-trm | api-chip-trm.md | HIGH | chip_trm interface: section filtering, register data format (Register/RegisterField) |
| 5 | api-specs | api-chip-specs.md | MEDIUM | chip_specs interface: 4 category queries, electrical specs with limit values |
| 6 | api-hardware | api-chip-hardware.md | HIGH | chip_hardware interface: pin filtering, AF multiplexing, package info |
| 7 | api-programming | api-chip-programming.md | MEDIUM | chip_programming_guide interface: SDK/HAL code, init sequences, dual implementations |

### Loading Strategy

- **Always load**: Section 1-2 (flow rules) — required for correct query behavior
- **Load on demand**: Section 3-7 (API rules) — load when the corresponding MCP Tool is about to be called
