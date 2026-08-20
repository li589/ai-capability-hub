# Scene: Project Wrap-up

Turn a completed project or feature module into a reusable knowledge asset — so next time you build something similar, you skip the wheel-reinvention.

## Detection Signals

Scan the source content for these patterns. Score each match; if total score exceeds **0.6**, classify as Project Wrap-up.

| Signal Pattern | Weight | Examples |
|---------------|--------|----------|
| Architecture/design decisions | 0.25 | "decided to use", "architecture", "chose X over Y", "design trade-off" |
| Module/component completion | 0.20 | "module complete", "feature done", "shipped", "merged", "deployed" |
| Project structure discussion | 0.20 | "folder structure", "module layout", "project scaffold", "directory organization" |
| Lessons learned | 0.20 | "lessons learned", "next time I would", "in hindsight", "takeaway" |
| Deployment/release | 0.15 | "deploy", "release", "CI/CD", "production", "go live" |

## Extraction Dimensions

### 1. Architecture Decision Records

Extract every significant design choice:
- What was decided?
- Why this approach over alternatives?
- What trade-offs were accepted?
- What constraints drove the decision?

### 2. Reusable Module Catalog

List modules, components, or code patterns worth reusing:
- Module name and purpose (one-line)
- Key dependencies
- How to adapt it for a different project
- Any gotchas when reusing

### 3. Pitfall Guide

Document every problem encountered during development:
- What happened (symptom)
- Why it happened (root cause)
- How it was fixed (solution)
- How to prevent it next time (prevention)

### 4. Generalized Implementation Steps

Distill the project into a reusable step-by-step playbook:
- Strip project-specific details, keep the transferable process
- Note decision points where the next project might diverge
- Include time estimates per step if available

## Confidence Scoring Guidance

- **high**: Decision was explicitly discussed, rationale clearly stated, outcome confirmed
- **medium**: Decision implied from code changes or conversation flow, rationale partially stated
- **low**: Inferred from context, not directly discussed, may be speculative

## Output Structure

```markdown
# <Title: Project/Feature Name — Wrap-up>

> **One-line summary**: <Core value of this distillation>

## Architecture Decisions
- **[confidence]** <Decision>: <Rationale>
  - Alternatives considered: ...
  - Trade-offs accepted: ...

## Reusable Modules
| Module | Purpose | Dependencies | Adaptation Notes |
|--------|---------|-------------|-----------------|
| ... | ... | ... | ... |

## Pitfall Guide
### <Pitfall Title>
- **Symptom**: ...
- **Root Cause**: ...
- **Fix**: ...
- **Prevention**: ...

## Implementation Playbook
1. <Step> — <Notes, decision points, time estimate>
2. ...

## Related
- [[related-doc-1]]
- [[related-doc-2]]
```

## Section Headers (zh)

When source language is Chinese, use these section headers:
- Architecture Decisions → 架构决策
- Reusable Modules → 可复用模块
- Pitfall Guide → 避坑指南
- Implementation Playbook → 实施步骤
- Related → 相关文档
