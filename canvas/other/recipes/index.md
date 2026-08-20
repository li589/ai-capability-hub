# Canvas Recipes

A recipe is a small, single-file reference pattern for a recurring Canvas output.
Agents should read this index first, pick the matching recipe by description,
then open only that recipe file for the concrete ASCII layout and content shape.

Recipes are not runtime SDK modules. They are prompt/layout references that help
agents choose structure, density, and evidence hierarchy for generated canvases.

## Mandatory Agent Routing

After reading this index, do not write Canvas TSX yet. First choose the best
matching row in the Index table, then open and follow the `File` listed for
that row.

If the request mentions an existing file, a file extension, or a format name
such as DOT, Graphviz, Mermaid, Structurizr, DSL, workbook, spreadsheet, XLSX,
CSV, JSONL, or "format viewer", open `format-viewer.recipe.md` before deciding
how to render it.

For format requests, prefer `<CanvasFormatViewer>` when a matching provisioned
viewer manifest exists. Only hand-draw SVG or custom JSX when no matching
viewer exists, no target file exists, or the user explicitly asks for a custom
diagram instead of embedding a file viewer.

## Post-Write Validation

After creating or editing a `.canvas.tsx` file, treat the host-provided
`Canvas TypeScript check` result as mandatory.

Rules:

- If the check reports `no errors`, continue to preview or final response.
- If the check reports TypeScript diagnostics, fix the canvas before final
  response. Read the local `canvas/*.d.ts` declarations in that project when
  the diagnostic mentions an unknown export, invalid prop, invalid token,
  missing default export, or non-component default export.
- If the host says the check is unavailable, say so briefly and use the
  narrowest available fallback such as a local `tsc --noEmit` check against the
  current SDK declarations before claiming the canvas is valid.

## Frontmatter Contract

Each `*.recipe.md` file must start with ASCII YAML frontmatter:

```yaml
---
name: lowercase-hyphen-name
description: What this recipe produces and when to use it.
category: optional-category
---
```

Rules:

- `name` and `description` are required.
- `name` uses lowercase letters, numbers, and single hyphens.
- `description` should explain both what the recipe does and when to use it.
- Recipe files should stay ASCII-only so they can be copied into constrained prompts.
- Keep recipe bodies focused; prefer compact ASCII wireframes over long prose.

## Index

| Name | Category | Description | File |
| --- | --- | --- | --- |
| code-review | engineering | One-page DX-first code review canvas recipe for summary, prioritized actionable comments, full diff evidence, and inline AI fix actions. Use when reviewing pull requests, commits, patches, or generated code changes. | code-review.recipe.md |
| design-system | design | One-page visual design-system preview recipe. Use when the user provides a DESIGN.md, getdesign/design-md preview, brand style analysis, or design-system notes and wants a Canvas that shows colors, typography, buttons, cards, forms, spacing, radius, elevation, and optional guardrails. | design-system.recipe.md |
| format-viewer | integration | Host-resolved Canvas format viewer recipe. Use when a Canvas should embed an existing local artifact whose format may have a provisioned viewer manifest. | format-viewer.recipe.md |
| sequence-diagram | visualization | Core Canvas TSX pattern for clean sequence diagrams with participant lanes, compact role cards, thin sync calls, dashed return or async calls, activation bars, legend, and process summary. Use for service interactions, auth flows, order flows, and critical path handoffs. | sequence-diagram.recipe.md |
