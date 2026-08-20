---
name: design-system
description: One-page visual design-system preview recipe. Use when the user provides a DESIGN.md, getdesign/design-md preview, brand style analysis, or design-system notes and wants a Canvas that shows colors, typography, buttons, cards, forms, spacing, radius, elevation, and optional guardrails.
category: design
---

Generate a design-system preview canvas, not an app, dashboard, report, landing
page, product workflow, or workbench shell.

The source is design reference material. The output should be a visual specimen
page that makes the rules inspectable: swatches, type rows, button states, card
samples, form states, spacing/radius scales, shadow/focus examples, and any
source-provided guardrails.

## Input Contract

Accept any of these as source:

- A `DESIGN.md` file with YAML tokens plus Markdown rationale.
- A getdesign/design-md preview page.
- A brand website style analysis with sections for color, typography, layout,
  components, elevation, shapes, and do/don't rules.
- User-provided design notes with exact tokens and visual constraints.

Read the source first. Extract concrete values and semantic rules before
writing TSX.

If the source follows DESIGN.md structure, preserve this reading order:

1. Overview or Brand & Style.
2. Colors.
3. Typography.
4. Layout or Layout & Spacing.
5. Elevation & Depth.
6. Shapes.
7. Components.
8. Do's and Don'ts.

This order is for understanding the design. The Canvas output should still be a
visual preview, not a markdown renderer.

## Required Canvas Shape

Use one scrollable page with a minimal top bar and normal document sections.
Favor the token-catalog shape used by getdesign previews: numbered sections,
compact uppercase labels, repeated specimens, and exact values visible beside
the visuals.

```text
+------------------------------------------------------------------------------+
| Brand / source link                                                          |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| Hero preview                                                                 |
| Small label                                                                  |
| H1: Design System Inspired by <source>                                       |
| 1-2 sentence source-faithful summary                                          |
| [Primary specimen button] [Secondary specimen button]                         |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| 01 - COLOR PALETTE                                                           |
| Brand / Neutral / Accent or Product / Semantic swatch groups                  |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| 02 - TYPOGRAPHY                                                              |
| Role, font, size, weight, line-height, letter-spacing, sample text            |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| 03 - BUTTONS or COMPONENTS                                                   |
| Primary, secondary, ghost, accent, badges, pills, and state specimens         |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| Cards                                                                        |
| Source-faithful card specimens with title, body, accent, and elevation        |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| Forms                                                                        |
| Inputs, textarea, select, checkbox, switch, focus/error/disabled states       |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| Later source sections                                                        |
| Layout & Spacing, Elevation & Depth, Shapes, Rules if present                 |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
| Rules                                                                        |
| Optional do/don't guardrails only when the source provides them               |
+------------------------------------------------------------------------------+
```

## Visual Rules

- The first screen must look like a design preview or styleguide.
- Use a plain max-width page container, usually 1120px to 1200px.
- Keep the hero editorial and sparse: top bar, title, summary, and 1-2 source
  buttons. Do not add IDE mockups, product screenshots, mini metric cards,
  token summary cards, or decorative panels before the first token section.
- The first token section should begin soon after the hero. In a getdesign-like
  preview, the page should move directly from hero to `01 - COLOR PALETTE`.
- Do not put the whole preview inside a framed rounded app card unless the host
  runtime requires it. The page background itself should carry the source
  surface color.
- Use source-specific colors only inside the specimen and preview CSS. Use
  `useHostTheme()` tokens for generic Canvas borders and fallback text.
- Raw hex values are allowed and expected for swatches, button specimens, focus
  rings, card accents, shadows, and dark/light preview areas.
- Render exact values as visible metadata: hex, font size, font weight,
  line-height, radius, spacing, shadow, and token names.
- Preserve source-specific oddities. If the source uses `9999px` pills, warm
  cream backgrounds, serif body text, AI timeline colors, or unusual font
  feature flags, show those as first-class specimens instead of normalizing them
  into a generic enterprise palette.
- Cards should represent repeated specimens. Do not wrap every section in a
  Card.
- Keep sections open, scannable, and vertically stacked.
- Do not invent decorative illustrations. If the source has no illustration
  language, use specimen blocks instead.
- Do not use generated business metrics. Design-system previews are about rules,
  not analytics.
- Top navigation should not be a section directory. It may mirror the source
  preview and show only a brand/source link. Avoid sticky internal nav when the
  official preview uses a simple document header.
- Never create a left or right sidebar for a design-system preview. Put every
  specimen section in the main vertical document flow.
- Preserve source section granularity. If the source has separate sections for
  Layout & Spacing, Elevation & Depth, and Shapes, do not collapse them into one
  generic `Layout System` section.

## SDK Use

- The generated `.canvas.tsx` must compile.
- Import every SDK component used from `qoder/canvas`.
- Prefer `Stack`, `Row`, `Grid`, `H1`, `H2`, `H3`, `Text`, `Card`,
  `CardHeader`, `CardBody`, `Button`, `Tag`, `Pill`, `Input`, `TextArea`,
  `Checkbox`, `Switch`, `Select`, `Table`, `Code`, `Spacer`, and
  `useHostTheme`.
- Use native `main`, `nav`, `section`, `div`, `h1`, `h2`, `button`, `input`,
  and `textarea` when exact source styling needs `className` or custom CSS.
- Do not pass unsupported props such as `className` to SDK primitives unless the
  declaration file explicitly allows them.
- Scope all custom CSS with `.ds-*`.
- Use arrays plus `.map()` for swatches, type rows, buttons, and scale chips.
- Keep all generated source stable: no random values, time-dependent labels, or
  viewport-scaled font sizes.

## Section Requirements

### Colors

Group swatches by semantic intent, not by raw hue alone:

- Brand primary.
- Neutral scale.
- Accent, product, or interaction colors.
- Semantic colors for success, warning, danger, info, links, or focus.

Each swatch should show name, value, and usage rule.

For getdesign-like previews, prefer large color-chip cards: a broad color block
on top, then token name, hex value, and one usage sentence below. Do not turn the
palette into tiny dashboard swatches.

### Typography

Render a table or stacked rows with:

- Role.
- Font family.
- Size.
- Weight.
- Line height.
- Letter spacing.
- Sample.

Use actual specimen text where safe. If a proprietary font is unavailable, show
the font name in metadata and use a stable fallback.

### Buttons

Show concrete specimen states:

- Primary and secondary buttons.
- Brand/accent buttons if present.
- Badges, pills, or labels if present.
- Ghost, surface, outline, or text buttons if present.
- Timeline/status pills if the source defines them.

### Cards

Show 2-4 source-faithful card specimens:

- Cards with title/body/accent.
- Use the exact source radius, border, background, and elevation.
- Do not add fake operational metrics to cards unless the source cards are
  metric cards.

### Forms

Show concrete form states:

- Light and dark form fields when both modes exist.
- Default, hover-like, focus, disabled, and error states when specified.
- Textarea or instruction field if the source includes long-form input.
- Preserve source-specific focus/error colors.

### Layout System

Show the spacing scale as chips or bars. Show radius as rectangles with the
actual corner radius. Show elevation as cards using the exact shadow or border
treatment from the source.

If the source separates layout, elevation, and shapes, render them as separate
numbered sections instead of one combined section.

### Rules

Include this only when the source provides explicit guardrails. Keep it compact.
Use two columns:

- Do: source-faithful positive rules.
- Don't: source-faithful constraints and misuse warnings.

## HashiCorp Source Notes

For a HashiCorp-inspired source, include these specimen requirements:

- Dark hero using `#15181e` or `#0d0e12`; light informational sections on
  `#ffffff` or `#f1f2f3`.
- Swatch groups: Brand Primary, Neutral Scale, Product Brand Colors, Semantic
  Colors.
- Product colors: Terraform `#7b42bc`, Vault `#ffcf25`, Waypoint `#14c6cb`,
  Vagrant `#1868f2`.
- Typography rows for Display Hero, Section Heading, Feature Heading,
  Sub-heading, Card Title, Small Title, Body Emphasis, Body Large, Body, Nav
  Link, Small Body, Caption, and Uppercase Label.
- Button specimens for Primary Dark, Secondary White, product-colored buttons,
  and purple badge/pill.
- Form specimens for dark input, checkbox, focus outline, and error state.
- Spacing chips for `2px`, `3px`, `4px`, `6px`, `8px`, `12px`, `16px`,
  `20px`, `24px`, `32px`, `40px`, and `48px`.
- Radius specimens for `2px`, `3px`, `4px`, `5px`, and `8px`.
- Elevation examples for Flat, Whisper shadow, and Focus outline.

Do not turn the HashiCorp source into an infrastructure dashboard. The preview
should resemble a design-system reference page.

## Cursor Source Notes

For a Cursor-inspired source, include these specimen requirements:

- Warm cream page background using values such as `#f2f1ed`, `#f7f7f4`, or
  nearby surface tokens instead of a generic white dashboard.
- Use a minimal document header and sparse editorial hero. Do not place an IDE
  mockup, code panel, agent timeline, or token metric cards in the hero. Those
  belong in Components only if the source includes such specimens.
- Primary dark text/background specimen `#26251e`, accent orange `#f54e00`,
  gold `#c08532`, error `#cf2d56`, and success `#1f8a65`.
- AI timeline color swatches for Thinking `#dfa88f`, Grep `#9fc9a2`, Read
  `#9fbbe0`, and Edit `#c0a8dd`.
- Typography rows for CursorGothic headings, `jjannon` serif body copy,
  `berkeleyMono` mono body, button label, caption, and uppercase system micro.
- Button specimens for Primary Dark, Primary Surface, Ghost, Pill Tag, and
  timeline pills.
- Card specimens for Tab Autocomplete, Chat with Codebase, and Agentic Editing.
- Form specimens for Default warm border, Focus accent orange, Error warm
  crimson, and Instructions textarea.
- Spacing chips for `2`, `3`, `4`, `5`, `6`, `8`, `10`, `12`, `16`, `24`,
  `32`, and `48`.
- Radius specimens for `1.5px`, `2px`, `3px`, `4px`, `8px`, `10px`, and
  `9999px`. Do not forbid pill shapes when the source explicitly includes them.
- Elevation examples for Flat, Border Ring, Medium, Ambient, Elevated, and
  Focus.
- Keep the first color cards large and document-like. Brand cards may be full
  width before the later grid groups, matching the official preview rhythm.

## Minimal Pattern

```tsx
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  Code,
  Grid,
  H1,
  H2,
  Row,
  Spacer,
  Stack,
  Text,
  useHostTheme,
} from "qoder/canvas";

const colors = [
  { group: "Brand", name: "Primary", value: "#f54e00", usage: "Primary CTAs and brand accent" },
  { group: "Surface", name: "Canvas", value: "#f7f7f4", usage: "Warm page floor" },
];

function Swatch({ item }: { item: (typeof colors)[number] }) {
  return (
    <div className="ds-swatch">
      <div className="ds-fill" style={{ background: item.value }} />
      <Text weight="semibold">{item.name}</Text>
      <Code>{item.value}</Code>
      <Text tone="secondary" size="small">{item.usage}</Text>
    </div>
  );
}

export default function DesignSystemPreview() {
  const { tokens } = useHostTheme();

  return (
    <main style={{ background: "#f7f7f4", color: "#26251e", minHeight: "100vh" }}>
      <style>{`
        .ds-page { max-width: 1120px; margin: 0 auto; padding: 0 20px 72px; }
        .ds-nav { display: flex; align-items: center; gap: 18px; height: 56px; border-bottom: 1px solid #e6e5e0; }
        .ds-hero { padding: 56px 0 48px; }
        .ds-section { border-top: 1px solid #e6e5e0; padding: 48px 0; }
        .ds-kicker { color: #807d72; font-size: 12px; font-weight: 600; letter-spacing: 0.88px; text-transform: uppercase; }
        .ds-swatch { border: 1px solid ${tokens.stroke.tertiary}; border-radius: 8px; padding: 12px; }
        .ds-fill { border-radius: 8px 8px 0 0; height: 90px; margin: -12px -12px 12px; }
      `}</style>

      <div className="ds-page">
        <nav className="ds-nav">
          <Text weight="semibold">getdesign.md</Text>
          <Spacer />
          <Button variant="secondary">Reference</Button>
        </nav>

        <Stack gap={0}>
          <section className="ds-hero">
            <Stack gap={18}>
              <H1 style={{ color: "#26251e", maxWidth: 760 }}>Design System Inspiration of Cursor</H1>
              <Text style={{ color: "#5a5852", maxWidth: 720 }}>
                Warm cream canvas, single orange accent, editorial display type, and hairline-only depth.
              </Text>
              <Row gap={10}><Button variant="primary">Download for macOS</Button><Button variant="secondary">All downloads</Button></Row>
            </Stack>
          </section>

          <section id="colors" className="ds-section">
            <Stack gap={18}>
              <Text className="ds-kicker">01 - Color Palette</Text>
              <H2>Cream canvas, warm ink, Cursor Orange</H2>
              <Grid columns="repeat(auto-fit, minmax(220px, 1fr))" gap={12}>
                {colors.map((item) => <Swatch key={item.name} item={item} />)}
              </Grid>
            </Stack>
          </section>

          <section id="typography" className="ds-section">
            <Card>
              <CardHeader title="02 - Typography" />
              <CardBody>
                <Text>Render type rows with role, font, size, weight, line-height, tracking, and sample text.</Text>
              </CardBody>
            </Card>
          </section>
        </Stack>
      </div>
    </main>
  );
}
```
