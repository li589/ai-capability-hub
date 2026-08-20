---
name: ui-taste-guard
description: >
  Eliminates AI-generated UI patterns and template feel from web/UI output. Enforces use of
  existing design systems, checks for anti-patterns (purple gradients, glassmorphism, fake
  dashboards), and ensures all interactive states are handled. Use when generating or modifying
  any web UI, HTML, CSS, React components, or frontend code.
description_zh: >
  消除 Web/UI 输出中的 AI 感和模板感。强制使用现有设计系统，检查反模式（紫色渐变、
  玻璃拟态、假 dashboard），确保所有交互状态都被处理。在生成或修改任何 web UI、
  HTML、CSS、React 组件或前端代码时使用。
version: 1.0.0
user-invocable: false
---

# UI Taste Guard

## Core Principle

**Real product first.** Every page should look like a working product, not a marketing demo or AI template.

**Match the system.** If a design system exists, use it. Don't invent new styles.

## Configuration

```yaml
preferredDesignSystem: auto      # shadcn/ui | antd | mui | custom | auto (detect)
enableUiAntiAiReview: true       # Run anti-AI pattern check
forbiddenUiPatterns:             # Additional patterns to avoid
  - purple-gradient-hero
  - glassmorphism
  - fake-dashboard
```

## Pre-Generation Checklist

Before writing any UI code:

1. **Detect design system** — Check for shadcn/ui (components.json), Ant Design (antd in deps), MUI (@mui in deps), or custom components in src/components/ui/
2. **Read existing pages** — Understand the app's visual language (spacing, density, colors)
3. **Read existing components** — Know what primitives are available
4. **Check design tokens** — Read tailwind.config.ts, theme files, CSS variables
5. **Understand the context** — Is this a SaaS tool? Dashboard? Marketing site? Mobile app?

## Anti-AI Pattern Checklist

After generating UI code, self-review against these patterns:

### CRITICAL — Must Avoid

| Pattern | What It Looks Like | Do This Instead |
|---|---|---|
| Purple-blue gradient | `bg-gradient-to-r from-purple-600 to-blue-600` | Use brand colors from design system |
| Glassmorphism abuse | `backdrop-blur-xl bg-white/10` on everything | Use solid surfaces, subtle borders |
| Glowing blob/decoration | Floating colored circles as decoration | Remove. Use whitespace instead |
| Giant hero title | `text-6xl font-bold` for non-landing pages | `text-2xl` or `text-3xl` for app pages |
| Card-in-card nesting | Cards wrapping cards wrapping cards | Flatten hierarchy, use sections |
| Fake dashboard | Charts with lorem ipsum data | Real data or clearly placeholder states |
| All large border-radius | `rounded-2xl` or `rounded-3xl` on everything | Use `rounded-md` or `rounded-lg` consistently |
| Marketing landing for tools | Hero + features + CTA for a settings page | Direct, functional layout |

### IMPORTANT — Must Handle

| State | Requirement |
|---|---|
| Loading | Skeleton, spinner, or progress indicator |
| Empty | Helpful empty state with action CTA |
| Error | Clear error message + recovery action |
| Disabled | Visible disabled state, not just hidden |
| Hover | Subtle hover feedback on interactive elements |
| Focus | Visible focus ring for keyboard navigation |
| Mobile | No text overflow, no button content squishing |
| Responsive | Works at 375px, 768px, 1024px, 1440px |

## Layout Principles by Page Type

### SaaS / Dashboard / Admin / Tool Pages

```
DO:
- Compact, information-dense layouts
- Clear hierarchy: page title → actions → content
- Tables with real columns, not placeholder cards
- Sidebar navigation, not hamburger menus on desktop
- Forms with labels above inputs, clear validation
- Breadcrumbs for deep navigation

DON'T:
- Hero sections with call-to-action
- Gradient backgrounds
- Decorative illustrations on functional pages
- Excessive whitespace between sections
- Cards when a simple list would work
```

### Landing / Marketing Pages

```
DO:
- Clear value proposition above the fold
- Real screenshots or product images
- Social proof with specific numbers
- Clear, single primary CTA

DON'T:
- Generic "Revolutionize your workflow" copy
- Placeholder testimonials
- Stock photo vibes
```

### Settings / Form Pages

```
DO:
- Grouped sections with clear labels
- Save/cancel actions clearly placed
- Inline validation
- Current values pre-filled
- Confirmation for destructive actions

DON'T:
- Single giant form with no grouping
- Floating labels only (use persistent labels)
- Hidden save buttons
```

## Design System Integration

### Auto-Detection Logic

```
1. Check components.json → shadcn/ui detected
2. Check package.json for "antd" → Ant Design detected
3. Check package.json for "@mui" → MUI detected
4. Check src/components/ui/ directory → Custom component library
5. Check for CSS modules / styled-components / Tailwind
6. Fall back to: plain CSS matching existing styles
```

### Usage Rules

1. **Always import from the design system**, never recreate primitives
2. **Match the variant system** — if buttons have `variant="primary"`, use it
3. **Match the spacing scale** — if project uses 4px grid, don't use 5px margins
4. **Match the color tokens** — use CSS variables / Tailwind theme, not raw hex
5. **Match the typography** — use existing heading/body/label styles

## Typography & Spacing Rules

```
DO:
- Use the project's font stack (check CSS/Tailwind config)
- Heading hierarchy: h1 (page) > h2 (section) > h3 (subsection)
- Consistent spacing scale (4px or 8px grid)
- Line height 1.5 for body text, 1.2 for headings
- max-width for text blocks (65-75ch for readability)

DON'T:
- Mix font families without reason
- Use font-size below 14px for body text
- Use line-height below 1.4 for body text
- Create walls of text without breaks
```

## Color Rules

```
DO:
- Use existing color palette from design system
- Limit to 2-3 accent colors max
- Ensure WCAG AA contrast (4.5:1 for text)
- Use semantic colors (error=red, success=green) consistently
- Support dark mode if project has it

DON'T:
- Invent new colors outside the palette
- Use raw hex values when CSS variables exist
- Rainbow-colored UIs
- Low-contrast text (gray on gray)
```

## Post-Generation Review

After writing UI code, run through this checklist:

```
UI TASTE REVIEW — [page/component name]
─────────────────────────────────────────
[ ] No purple-blue gradients on non-landing pages
[ ] No glassmorphism unless project uses it
[ ] No decorative blobs/circles
[ ] Heading sizes appropriate for page type
[ ] No excessive card nesting
[ ] Design system components used (not custom recreations)
[ ] Colors from project palette (not invented)
[ ] Spacing matches project scale
[ ] Loading state handled
[ ] Empty state handled
[ ] Error state handled
[ ] Disabled states visible
[ ] Hover states on interactive elements
[ ] Focus styles present
[ ] No text overflow on mobile (375px)
[ ] Buttons have adequate padding
[ ] Form inputs have labels
[ ] Page looks like a real product, not a template
```

## Integration

- **Context Cartographer**: Read design system files with HIGH priority
- **Evidence Guard**: Design system claims must reference actual code
- **Verification Runner**: UI output must be browser-verified when possible

## Additional Resources

- For anti-pattern visual examples, see [anti-pattern-catalog.md](references/anti-pattern-catalog.md)
