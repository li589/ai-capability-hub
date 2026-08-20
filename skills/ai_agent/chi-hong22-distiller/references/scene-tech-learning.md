# Scene: Tech Learning

Turn fragmented learning into a systematic knowledge map — so new tech sticks instead of evaporating after one session.

## Detection Signals

Scan the source content for these patterns. Score each match; if total score exceeds **0.6**, classify as Tech Learning.

| Signal Pattern | Weight | Examples |
|---------------|--------|----------|
| New tech exploration | 0.30 | "new framework", "getting started", "first time using", "learning", "tutorial" |
| API/tool discovery | 0.25 | "API", "function", "method", "configuration", "how to use" |
| Concept understanding | 0.20 | "how does X work", "what is", "concept", "mechanism", "under the hood" |
| Comparison/evaluation | 0.15 | "vs", "compared to", "alternative", "better than", "trade-off" |
| Integration discussion | 0.10 | "integrate with", "works with", "compatible", "migration", "adopt" |

## Extraction Dimensions

### 1. Core Concept Map

The mental model for this technology:
- Fundamental concepts and how they relate to each other
- Key abstractions and their purpose
- The "aha moment" — what makes this tech click once you understand it

### 2. Essential API Quick-Reference

The 20% of the API that covers 80% of use cases:
- Function/method signature
- What it does (one line)
- Minimal usage example
- Common gotchas

### 3. Use-Case Judgment

When to use and when NOT to use:
- Ideal scenarios (where this tech shines)
- Anti-patterns (where it fails or is overkill)
- Comparison with alternatives (brief, focused on decision criteria)

### 4. Integration Points

How to combine with existing tech stack:
- Dependencies and compatibility requirements
- Configuration for common setups
- Migration path from current approach
- Known conflicts or incompatibilities

### 5. Progression Roadmap

From beginner to proficient:
- Level 1: Minimum viable knowledge (what to learn first)
- Level 2: Productive usage (common patterns and best practices)
- Level 3: Advanced mastery (optimization, extension, edge cases)
- Recommended resources at each level

## Confidence Scoring Guidance

- **high**: Concept verified by working code, API tested and confirmed, behavior observed
- **medium**: Understood from documentation or discussion but not personally verified
- **low**: Mentioned in passing, may be outdated or version-specific

## Output Structure

```markdown
# <Title: Technology/Framework Name — Learning Notes>

> **One-line summary**: <What this tech is and its core value proposition>

## Core Concepts
- **[confidence]** <Concept>: <Explanation>
  - Relates to: <other concepts>
- Key takeaway: ...

## API Quick-Reference
### <Category>
| API | Purpose | Example |
|-----|---------|---------|
| `function()` | ... | `code snippet` |

**Gotchas**:
- **[confidence]** ...

## When To Use
- **Ideal for**: ...
- **Avoid when**: ...
- **vs <Alternative>**: ...

## Integration Guide
- **Dependencies**: ...
- **Setup**: ...
- **Migration from <current>**: ...
- **Known conflicts**: ...

## Progression Roadmap
### Level 1: Getting Started
- **[confidence]** ...
### Level 2: Productive
- **[confidence]** ...
### Level 3: Advanced
- **[confidence]** ...

## Related
- [[related-doc-1]]
```

## Section Headers (zh)

When source language is Chinese, use these section headers:
- Core Concepts → 核心概念
- API Quick-Reference → API 速查
- When To Use → 适用场景
- Integration Guide → 集成指南
- Progression Roadmap → 进阶路线
- Related → 相关文档
