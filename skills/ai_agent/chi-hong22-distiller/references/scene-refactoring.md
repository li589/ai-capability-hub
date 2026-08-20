# Scene: Code Refactoring

Turn a refactoring session into distilled design wisdom — understand not just what changed, but why and how to apply the same thinking elsewhere.

## Detection Signals

Scan the source content for these patterns. Score each match; if total score exceeds **0.6**, classify as Code Refactoring.

| Signal Pattern | Weight | Examples |
|---------------|--------|----------|
| Refactoring actions | 0.30 | "refactor", "restructure", "rewrite", "clean up", "simplify" |
| Design principles | 0.25 | "SOLID", "DRY", "KISS", "single responsibility", "separation of concerns" |
| Code quality issues | 0.20 | "code smell", "tech debt", "duplication", "complexity", "coupling" |
| Performance optimization | 0.15 | "optimize", "performance", "bottleneck", "profiling", "O(n)" |
| Before/after comparison | 0.10 | "before", "after", "improved", "reduced", "cleaner" |

## Extraction Dimensions

### 1. Original Problem Diagnosis

What was wrong with the code before refactoring:
- Specific code smells or anti-patterns identified
- Metrics if available (complexity, duplication, coupling)
- Why it needed to change now (trigger: bug, feature request, readability)

### 2. Design Principles Applied

Which principles guided the refactoring:
- Name the principle (e.g., Single Responsibility, Open/Closed)
- How it was applied in this specific case
- Concrete before/after example showing the principle in action

### 3. Refactoring Decision Chain

Step-by-step decisions made during refactoring:
- Each step: what was changed and why
- Alternatives considered at each step
- Trade-offs accepted (e.g., more files but clearer responsibility)

### 4. Before-After Comparison

Tangible improvements:
- Readability: qualitative assessment
- Performance: measurements if available
- Maintainability: reduced coupling, clearer interfaces
- Testability: easier to test, better coverage

### 5. Best Practices Distilled

Generalizable patterns extracted from this refactoring:
- Reusable refactoring recipes ("When you see X, consider Y")
- Industry-standard patterns applied
- Personal conventions worth adopting

## Confidence Scoring Guidance

- **high**: Principle explicitly discussed, before/after clearly demonstrated, improvement confirmed
- **medium**: Principle implied by changes, improvement likely but not measured
- **low**: Inferred design intent, improvement assumed but not validated

## Output Structure

```markdown
# <Title: Refactoring Description>

> **One-line summary**: <What was refactored and the key improvement>

## Problem Diagnosis
- **[confidence]** Code smells: ...
- **[confidence]** Trigger: ...
- Metrics: ...

## Principles Applied
### <Principle Name>
- **[confidence]** Application: ...
- Before: `<code snippet>`
- After: `<code snippet>`

## Decision Chain
1. **[confidence]** <Step>: <What changed> — <Why>
   - Alternatives: ...
   - Trade-off: ...

## Before vs After
| Dimension | Before | After |
|-----------|--------|-------|
| Readability | ... | ... |
| Performance | ... | ... |
| Maintainability | ... | ... |
| Testability | ... | ... |

## Distilled Patterns
- **[confidence]** When you see <X>, consider <Y> because <reason>
- ...

## Related
- [[related-doc-1]]
```

## Section Headers (zh)

When source language is Chinese, use these section headers:
- Problem Diagnosis → 问题诊断
- Principles Applied → 应用的设计原则
- Decision Chain → 重构决策链
- Before vs After → 前后对比
- Distilled Patterns → 沉淀的模式
- Related → 相关文档
