---
name: format-viewer
description: Host-resolved Canvas format viewer recipe. Use when a Canvas should embed an existing local artifact whose format may have a provisioned viewer manifest.
category: integration
---

Use this when a generated Canvas should show a local target file with an
existing host-provisioned viewer, such as Mermaid, Graphviz DOT, Structurizr,
workbooks, or another file format registered by the IDE.

This recipe is usually an embedded section, not the whole Canvas. Combine
`<CanvasFormatViewer>` with the user's domain context: architecture notes,
review findings, data explanation, migration steps, or other surrounding UI.

If the user asks for a Canvas "with dot", "with mermaid", "with xlsx", or with
any other concrete file format, treat that as a format-viewer request first.
Do not reinterpret it as a request to hand-draw a similar-looking SVG until
you have checked whether a provisioned viewer exists.

Before using it:

- Inspect `~/.qoder/canvas/canvases/**/manifest.json` to see which
  viewers are actually provisioned.
- Import only the generic shell from `qoder/canvas`.
- Pass a local file path. Relative paths resolve from the parent Canvas file
  directory.
- Add a useful fallback for missing, unsupported, or unavailable viewers.

Do not:

- Import a concrete viewer package.
- Import `canvases/<format>/index.canvas.tsx`.
- Hardcode `dot`, `mermaid`, `dsl`, `xlsx`, or any other viewer registry in SDK
  code.
- Assume every Markdown file has a format viewer. Manifests decide what is
  available.
- Replace the whole Canvas with only an iframe unless the user only asked for a
  plain file preview.

Architecture design pattern:

```tsx
import { CanvasFormatViewer, Grid, Stack, H2, Text, Card, CardBody } from "qoder/canvas";

export default function Canvas() {
  return (
    <Grid columns="320px minmax(0, 1fr)" gap={16}>
      <Stack gap={12}>
        <Card>
          <CardBody>
            <H2>Architecture overview</H2>
            <Text tone="secondary">
              Summarize the system boundary, critical services, and main data flow here.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <H2>Review focus</H2>
            <Text tone="secondary">
              Call out coupling, scaling risks, deployment boundaries, or open decisions.
            </Text>
          </CardBody>
        </Card>
      </Stack>

      <CanvasFormatViewer
        targetFilePath="./architecture.dot"
        height={560}
        title="Architecture DOT"
        fallback={<div>Viewer unavailable for this architecture file.</div>}
      />
    </Grid>
  );
}
```

Compact preview section:

```tsx
import { CanvasFormatViewer, Stack, H2, Text } from "qoder/canvas";

<Stack gap={12}>
  <H2>Data import preview</H2>
  <Text tone="secondary">Explain what the workbook contains and what to inspect.</Text>
  <CanvasFormatViewer targetFilePath="./input.xlsx" height={420} />
</Stack>
```

Use `format` only when the user explicitly asks for a specific provisioned
viewer and the matching manifest exists:

```tsx
<CanvasFormatViewer targetFilePath="./architecture.dsl" format="structurizr" />
```
