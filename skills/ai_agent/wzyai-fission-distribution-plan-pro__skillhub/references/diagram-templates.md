# Diagram Contracts

Create Mermaid source first, validate it, then render SVG and PNG. Diagram numbers, labels, roles, dates, and compensation paths must match the report.

## Distributor capability assessment

Use `graph TB` with the fixed structure `核心画像 → 五维 → 简评`. Center the confirmed target distributor group and connect social capital, content capability, direct-sales capability, available time, and learning/tool ability. Score 0–100 only when evidence or a labeled estimate supports it; otherwise display `暂不评分`. Add a short evidence-based note for each dimension.

## Compliant transaction and direct-commission path

Use `graph TB` with the fixed structure `顶层架构 → 垂直链路 → 旁侧红线`. Required nodes: company/system, direct promoter, end customer, payment account, fulfillment, refund-period gate, and direct commission settlement. Show full customer payment to the authorized merchant/account and commission only after a genuine completed order. Do not draw a downline-pay edge.

## User journey swimlane

Use `sequenceDiagram` with exactly four roles: customer, direct promoter, system, and fulfillment/customer service. Use three semantic color blocks for compliant reach, genuine purchase/fulfillment, and refund/settlement. Cover approved content exposure, click/scan, attribution disclosure, order, payment, fulfillment, refund window, and commission settlement.

## 90-day execution Gantt

Use `gantt`, `dateFormat YYYY-MM-DD`, and real dates based on the report generation date. Use the four fixed phases: 事实与合规、受控试点、验证放量、复盘止损. Include measurable milestones. Task labels must not contain raw half-width `:`; replace a display colon with the full-width `：` before rendering.

## Consultation-blue semantic palette

- Core/company: `#0B1F3A`.
- Facts/process: `#2563EB`, with light background `#EAF2FF`.
- Compliant completion: `#16A34A`, with light background `#E9F8EF`.
- Assumptions and gates: `#F59E0B`, with light background `#FFF4D6`.
- Risk and stop: `#DC2626`, with light background `#FDECEC`.

User brand colors may replace the primary brand color, but facts, completion, gates, and risk must retain distinct semantic meaning and readable contrast.

## Mermaid safety rules

- Quote labels containing punctuation, parentheses, emoji, or HTML breaks.
- Keep identifiers ASCII and unique.
- Close every code fence and subgraph.
- Avoid unescaped half-width colons in Gantt task names.
- Keep dates valid and dependencies resolvable.
- Run `scripts/render_mermaid.mjs` and inspect both SVG and PNG.
- If two repair attempts fail, deliver a structured table and report the rendering failure; never claim an unrendered diagram exists.
