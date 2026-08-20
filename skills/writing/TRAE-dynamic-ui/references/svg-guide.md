# SVG Drawing Guide

## SVG Setup

`<svg width="100%" viewBox="0 0 680 H">` — 680px fixed width, flexible height. The 680 is load-bearing — do not change. Safe area: x=40 to x=640.

## ViewBox Safety Checklist

1. Find lowest element: max(y+height). Set viewBox height = that + 40px.
2. All content within x=0 to x=680.
3. `text-anchor="end"` extends LEFT — check overflow.
4. Never negative x or y coordinates.
5. Flowcharts: check box pairs have 20px+ gap.

**One SVG per tool call.**

## Arrow Marker

Include in every SVG `<defs>`:

```xml
<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>
```

## Font Calibration

At 14px, ~8px per Latin char. At 12px, ~7px per char. Verify: (text_width + 2×padding) < box_width.

## Stroke Width

1px for borders/edges. Connector paths need `fill="none"`.

## Diagram Types

**Two critical rules**:
1. Arrow intersection check — never cross unrelated boxes.
2. Box width from longest label: max(title_chars×8, subtitle_chars×7)+24.

**Pick by intent**: Reference diagrams (flowchart, structural) vs Intuition diagrams (illustrative). Route on the verb, not the noun.

### Flowchart

60px min between boxes, 24px padding inside, 12px text-to-edge. Every `<text>` inside box needs `dominant-baseline="central"`. Max 4-5 nodes per diagram. Cycles → HTML stepper, not ring.

### Structural Diagram

Large rounded rects as containers, smaller rects inside. 20px min padding inside containers. Max 2-3 nesting levels. Use distinct color ramps for nested levels.

### Illustrative Diagram

For building intuition. Physical subjects = simplified cross-sections. Abstract subjects = spatial metaphors. Color encodes intensity not category. Shapes are freeform. Layout follows subject geometry. One gradient permitted for continuous physical property. Interactive preferred over static.
