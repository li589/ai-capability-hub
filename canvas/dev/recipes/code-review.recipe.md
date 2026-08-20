---
name: code-review
description: One-page review action canvas focused on what changed, what matters, and direct AI fix actions.
category: engineering
---

Generate a code review action canvas, not a commit digest, release note, or approval dashboard.

Goal:
Create one scannable page that helps the user answer three questions in this order:
1. What changed?
2. What problems matter?
3. What can AI fix directly?

The merge decision is secondary. It should be derived from the findings, not presented as the main content.

Primary user intent:
Users usually scan a review to understand:
- the functional change
- the important risks or defects
- the exact diff evidence (when the issue is P0)
- the fastest available AI fix action

Required layout:
1. Compact Header
   - Show review status, issue count, highest priority, and one optional "AI Fix All" action.
   - Do not make APPROVE / REJECT the visual focus.
   - Do not use large metric cards for added lines, deleted lines, file count, or author unless they are directly relevant to a finding.

2. What Changed
   - 2-4 concise bullets or short paragraphs.
   - Focus on functional behavior, removed/added capability, touched areas, and user/runtime impact.
   - Do not create a "positive evaluation" section.

3. Issues to Review
   - A compact prioritized list sorted by priority and severity.
   - Each issue row should show only:
     priority, title, severity, file/range, AI Fix.
   - AI Fix should be visible inline for every actionable P0/P1/P2 code issue.
   - P3 and Info may omit AI Fix unless the fix is obvious and low-risk.

4. Evidence & Fix Details
   - For every P0 code finding, show visible diff evidence directly below the issue list.
   - Do not hide evidence behind tabs, drawers, file trees, or sidebars.
   - Each detail block should include:
     summary, impact, suggestion, required verification, and diff evidence.
   - Use FileReview or DiffGroup for code findings instead of plain text diffs.

5. Verification
   - Briefly state the validation signal:
     tests run, tests missing, confidence level, or exact reason confidence is low.
   - Keep this small and below the actionable content.

Rules:
- Use one vertical page.
- Prioritize changed behavior, actionable issues, and AI fix actions.
- Do not include standalone sections like "Positive Evaluation", "Code Quality Highlights", or "Statistics" unless the user explicitly asks.
- Do not use large dashboard metric cards unless they support review decisions.
- Do not hide evidence behind tabs, drawers, file trees, or sidebars.
- Use priority labels: P0, P1, P2, P3, Info.
- Diff evidence must be visible below the issue list.
- For P0 code findings, use FileReview or DiffGroup instead of plain text diffs.
- If exact diff evidence is missing, say so, mark confidence as Low, and do not overstate the finding.
- Translate visible UI text to the user's language. Keep file paths, code, commands, and identifiers unchanged.

Canvas TSX requirements:
- Import all used components from qoder/canvas.
- Keep data arrays small.
- Render the issue list and detail section from the same issues array.
- Do not duplicate issue data across multiple arrays.
