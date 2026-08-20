# Canvas Recipes

A recipe is an optional, single-file reference pattern for a recurring Canvas
output. Read this index when a known output shape may help. Select at most one
recipe whose description directly matches the requested deliverable; otherwise
continue without a recipe.

Recipes are prompt/layout references, not runtime SDK modules or visual authorities.
Explicit user instructions and supplied visual sources take precedence.

## Optional Recipe Selection

Recipes are not an exhaustive taxonomy. Do not choose the nearest recipe merely
because it is the only one with a similar topic or visual language. Match the
user's requested output shape, not just the input file, subject matter, or a
request to preserve styling.

Open a recipe only when the requested deliverable and the recipe's source
assumptions both match. If no row matches directly, use the SDK declarations
and the supplied source without opening another recipe.

When converting or recreating an HTML page, screenshot, mockup, prototype, app,
or product workflow, preserve that artifact's structure and behavior. A request
to preserve or continue its visual style is not a request for a design system.

If the user wants to view, open, or embed an existing artifact whose format may
have a provisioned viewer, open `format-viewer.recipe.md` before deciding how to
render it. Do not select that recipe solely because a file or extension is
mentioned when the file is instead a source to transform or reproduce.

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

## Index

| Name | Category | Description | File |
| --- | --- | --- | --- |
| code-review | engineering | One-page DX-first code review canvas recipe for summary, prioritized actionable comments, full diff evidence, and inline AI fix actions. Use when reviewing pull requests, commits, patches, or generated code changes. | code-review.recipe.md |
| design-system | design | One-page visual design-system preview recipe. Use only when the requested output is a design system, style guide, token catalog, or component specimen based on DESIGN.md, a getdesign/design-md preview, brand style analysis, or design-system notes. Do not use it to recreate a page, prototype, app, or workflow, even when the user asks to preserve its visual style. | design-system.recipe.md |
| format-viewer | integration | Host-resolved Canvas format viewer recipe. Use when a Canvas should embed an existing local artifact whose format may have a provisioned viewer manifest. | format-viewer.recipe.md |
| presentation | communication | Interactive slide presentation recipe with horizontal narrative slides, optional vertical detail stacks, staged fragments, keyboard navigation, overview, fullscreen, and deep links. Use for talks, pitches, demos, lessons, and guided walkthroughs. | presentation.recipe.md |
| report | communication | Constrained report-page recipe for research summaries, status reports, evidence reviews, timelines, metric overviews, and mixed chart/table narratives. Use when the output is primarily read rather than operated. | report.recipe.md |
| sequence-diagram | visualization | Core Canvas TSX pattern for clean sequence diagrams with participant lanes, compact role cards, thin sync calls, dashed return or async calls, activation bars, legend, and process summary. Use for service interactions, auth flows, order flows, and critical path handoffs. | sequence-diagram.recipe.md |
