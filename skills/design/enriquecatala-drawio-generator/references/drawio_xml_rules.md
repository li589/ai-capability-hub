# Draw.io (mxGraph) XML Quick Reference

## Root Structure

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel dx="1000" dy="600" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- shapes and edges here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Shape (Vertex)

```xml
<mxCell id="UNIQUE_ID" value="Label" style="STYLE_STRING" vertex="1" parent="1">
  <mxGeometry x="X" y="Y" width="W" height="H" as="geometry" />
</mxCell>
```

## Edge (Connector)

```xml
<mxCell id="UNIQUE_ID" style="STYLE_STRING" edge="1" parent="1" source="SRC_ID" target="TGT_ID">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

## Common Style Strings

| Component           | Style                                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Rounded box         | `rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;shadow=1;`                                       |
| Database (cylinder) | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#ffe6cc;strokeColor=#d79b00;` |
| Cloud               | `ellipse;shape=cloud;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;`                                      |
| Hexagon             | `shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;`                                          |
| Diamond             | `rhombus;whiteSpace=wrap;html=1;`                                                                                        |
| Container/Group     | `rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;dashed=1;container=1;`                           |
| Zone (solid)        | `rounded=1;fillColor=#BAC8D3;strokeColor=none;opacity=60;`                                                               |
| Zone (dashed)       | `rounded=1;dashed=1;dashPattern=8 8;fillColor=none;strokeColor=#0BA5C4;`                                                 |
| Edge (orthogonal)   | `edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#666666;`      |

## Edge Styles

| Type           | Style                                                         |
| -------------- | ------------------------------------------------------------- |
| Directional    | `endArrow=classic;html=1;`                                    |
| Dashed         | `dashed=1;endArrow=classic;html=1;`                           |
| Network link   | `endArrow=none;endFill=0;html=1;`                             |
| Inheritance    | `endArrow=block;endFill=0;html=1;`                            |
| Implementation | `endArrow=block;endFill=0;dashed=1;html=1;`                   |
| Association    | `endArrow=open;endFill=1;html=1;`                             |
| Dependency     | `endArrow=open;dashed=1;html=1;`                              |
| Aggregation    | `startArrow=diamondThin;startFill=0;endArrow=classic;html=1;` |
| Composition    | `startArrow=diamondThin;startFill=1;endArrow=classic;html=1;` |

## Edge Routing Patterns

### Bidirectional (separate paths)
```xml
<mxCell id="e1" value="Request" style="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.3;entryX=0;entryY=0.3;endArrow=classic;html=1;" edge="1" parent="1" source="nodeA" target="nodeB">
  <mxGeometry relative="1" as="geometry"/></mxCell>
<mxCell id="e2" value="Response" style="edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.7;entryX=1;entryY=0.7;endArrow=classic;html=1;" edge="1" parent="1" source="nodeB" target="nodeA">
  <mxGeometry relative="1" as="geometry"/></mxCell>
```

### Top-down connection
```xml
<mxCell style="exitX=0.5;exitY=1;entryX=0.5;entryY=0;endArrow=classic;html=1;" edge="1" parent="1" source="top" target="bottom">
  <mxGeometry relative="1" as="geometry"/></mxCell>
```

## Shape Modifiers

| Modifier        | Values                             | Effect                    |
| --------------- | ---------------------------------- | ------------------------- |
| `rounded`       | 0, 1                               | Rounded corners           |
| `fillColor`     | hex                                | Background color          |
| `strokeColor`   | hex                                | Border color              |
| `strokeWidth`   | num                                | Border width              |
| `dashed`        | 0, 1                               | Dashed border             |
| `opacity`       | 0-100                              | Transparency              |
| `fontColor`     | hex                                | Text color                |
| `fontSize`      | num                                | Text size                 |
| `fontStyle`     | 0=normal, 1=bold, 2=italic, 3=both | Text weight               |
| `align`         | left, center, right                | Horizontal text alignment |
| `verticalAlign` | top, middle, bottom                | Vertical text alignment   |
| `shadow`        | 0, 1                               | Drop shadow               |
| `container`     | 0, 1                               | Can hold children         |

## Stencil Usage

Read `stencils/*.md` for exact shape names. Common patterns:

```xml
<!-- AWS (need fillColor) -->
<mxCell style="shape=mxgraph.aws4.lambda;html=1;fillColor=#ED7100;verticalLabelPosition=bottom;verticalAlign=top;" vertex="1" parent="1">

<!-- Cisco (need fillColor + strokeColor) -->
<mxCell style="shape=mxgraph.cisco.routers.router;html=1;fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;" vertex="1" parent="1">

<!-- Kubernetes (need fillColor) -->
<mxCell style="shape=mxgraph.kubernetes.pod;html=1;fillColor=#326CE5;strokeColor=#ffffff;" vertex="1" parent="1">
```

## Critical Rules

1. Every `mxCell` must have a **unique** `id`
2. Shapes: `vertex="1" parent="1"`
3. Edges: `edge="1" parent="1"` with valid `source` and `target`
4. No newlines in `value` attributes
5. Grid alignment: position at multiples of 10/20
6. Start margin: x=40, y=40
7. Spacing: 40-60px within groups; 150-200px for routing channels
8. ALL mxCell must be siblings under `<root>` — never nest
9. Escape: `&lt;` `&gt;` `&amp;` `&quot;`

## ⚠️ Forbidden Patterns

```xml
<!-- NEVER DO THIS — crashes draw.io -->
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="300" y="200" />
  </Array>
</mxGeometry>

<!-- ALWAYS DO THIS instead -->
<mxGeometry relative="1" as="geometry" />
```

Also NEVER include `<!-- ... -->` XML comments in generated diagrams.
