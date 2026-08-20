# Scene: Universal (Fallback)

General-purpose extraction template for sessions that don't clearly fit the 4 core scenes, or that span multiple scene types.

## Detection Signals

This scene activates when:
- No other scene's total score exceeds **0.6**
- Content spans multiple scene types without a clear dominant one
- User explicitly selects "Universal" when overriding scene detection

| Signal Pattern | Weight | Examples |
|---------------|--------|----------|
| General knowledge sharing | 0.20 | "learned that", "discovered", "realized", "found out" |
| Decision making | 0.20 | "decided to", "chose", "went with", "opted for" |
| Problem solving | 0.20 | "solved by", "the trick is", "workaround", "approach" |
| Pattern recognition | 0.20 | "pattern", "always do", "convention", "best practice" |
| Any technical discussion | 0.20 | (catch-all for technical content not matching other scenes) |

## Extraction Dimensions

### 1. Key Findings

The most important discoveries or conclusions from the session:
- What was the core outcome?
- What surprised you or was non-obvious?
- What would you tell your past self before starting?

### 2. Critical Decisions with Rationale

Every significant choice made during the session:
- What was decided?
- What options were considered?
- Why this choice? What drove the decision?

### 3. Reusable Patterns

Methods, approaches, or code patterns worth remembering:
- The pattern (what)
- When to apply it (when)
- How to apply it (how)
- Why it works (why)

### 4. Caveats and Gotchas

Things to watch out for:
- Known limitations or edge cases
- Easy mistakes to make
- Environmental or version-specific issues

## Confidence Scoring Guidance

- **high**: Explicitly stated, directly supported by evidence in the session
- **medium**: Reasonably inferred from context, likely correct but not directly stated
- **low**: Speculative or tangentially mentioned, needs further validation

## Output Structure

```markdown
# <Title: Topic Summary>

> **One-line summary**: <Core takeaway from this session>

## Key Findings
- **[confidence]** <Finding>: <Explanation>
- ...

## Decisions
- **[confidence]** <Decision>: <Rationale>
  - Alternatives: ...

## Reusable Patterns
### <Pattern Name>
- **[confidence]** **What**: ...
- **When**: ...
- **How**: ...
- **Why**: ...

## Caveats
- **[confidence]** <Caveat>: <Details>
- ...

## Related
- [[related-doc-1]]
```

## Section Headers (zh)

When source language is Chinese, use these section headers:
- Key Findings → 核心发现
- Decisions → 关键决策
- Reusable Patterns → 可复用模式
- Caveats → 注意事项
- Related → 相关文档
