---
name: report
description: Constrained report-page recipe for research summaries, status reports, evidence reviews, timelines, metric overviews, and mixed chart/table narratives. Use when the output is primarily read rather than operated.
---

# Report Canvas Recipe

Use this recipe for a document-shaped Canvas whose main job is to communicate
findings, evidence, progress, recommendations, or a structured analysis.

Do not use it for an application workspace, presentation deck, freeform visual,
or interactive dashboard that genuinely needs the full viewport.

## Required page root

Every report must import and render `ReportShell` as its outermost component.
Do not emulate the page frame with a padded `Stack`, `div`, or fixture-specific
`maxWidth` style.

- Use `<ReportShell width="wide">` for reports containing grids, tables, or
  charts. The shared shell owns the centered 960px maximum width.
- Use `<ReportShell width="reading">` for prose-first reports. The shared shell
  owns the centered 640px reading width.
- Keep theme, density, responsive page padding, and browser-preview behavior in
  `ReportShell`; do not duplicate them in the generated file.

Organize major content blocks with `ReportSection`. Use its `title`,
`description`, `meta`, `divided`, and `compact` props instead of recreating
section headings and spacing with local styles.

## Minimal structure

```tsx
import {
  H1,
  ReportSection,
  ReportShell,
  Stack,
  Text,
} from "qoder/canvas";

export default function Report() {
  return (
    <ReportShell width="wide" ariaLabel="Report title">
      <Stack gap="section">
        <Stack gap="component">
          <H1>Report title</H1>
          <Text tone="secondary">Scope and reporting period</Text>
        </Stack>

        <ReportSection title="Findings" divided>
          <Text>Report content</Text>
        </ReportSection>
      </Stack>
    </ReportShell>
  );
}
```

## Shared semantics

- Use `Callout`/`Banner` tones for semantic notices; do not set notice colors
  locally.
- Use `<MetricsGrid variant="header">` for three to five short, peer headline
  metrics directly under a report title. Header metrics share the report header
  as their visual container and therefore do not receive individual cards.
- Use `<MetricsGrid variant="card">` only when each metric is an independently
  readable dashboard module with its own explanation, trend, state, or action.
  Do not mix header and card metrics in one row or nest metric cards inside an
  already bordered surface.
- Use `ChartContainer`, `ChartComparisonGrid`, and shared table primitives for
  aligned visual regions.
- Keep report content unchanged when migrating an existing report into the
  shared shell.
- A narrow Quest artifact panel and a wide browser preview must render the same
  hierarchy. Validate both; the browser preview must not expand report copy to
  the full viewport.

## Analytical report structure

For a report with headline metrics and charts, keep all four structural levels.
Borderless headline metrics do not make the whole report borderless:

```tsx
<ReportShell width="wide" ariaLabel="Report title">
  <Stack gap="sectionCompact">
    <header>
      <Stack gap="component">
        <H1>Report title</H1>
        <Text tone="secondary">Scope and reporting period</Text>
        <MetricsGrid
          variant="header"
          columns={4}
          items={headlineMetrics}
        />
      </Stack>
    </header>

    <ReportSection title="Distribution" divided>
      <ChartContainer ariaLabel="Distribution chart">
        <PieChart donut data={distribution} />
      </ChartContainer>
    </ReportSection>

    <ReportSection title="Trend" divided>
      <ChartContainer ariaLabel="Trend chart">
        <LineChart categories={periods} series={trendSeries} />
      </ChartContainer>
    </ReportSection>
  </Stack>
</ReportShell>
```

Do not replace this hierarchy with a root `Stack`, loose `H2` plus `Divider`
pairs, `Grid` plus raw `Stat`, or charts rendered directly against the page.

## Validation

Before finishing, verify that the source contains one outer `ReportShell`, that
major sections use `ReportSection`, and that the host Canvas TypeScript check
reports no errors.
