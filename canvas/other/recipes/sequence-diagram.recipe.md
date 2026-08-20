---
name: sequence-diagram
description: Core Canvas TSX pattern for clean sequence diagrams with participant lanes, compact role cards, thin sync calls, dashed return or async calls, activation bars, legend, and process summary. Use for service interactions, auth flows, order flows, and critical path handoffs.
category: visualization
---

Use this when the canvas needs to show an ordered interaction between services,
agents, users, queues, databases, or APIs. Prioritize a clean SVG sequence view
over cards or tables.

Core Canvas TSX pattern. Keep these pieces; build the surrounding page with
normal Canvas primitives only as needed.

```tsx
import { useHostTheme } from "qoder/canvas";

type Participant = {
  name: string;
  role: string;
  color: string;
  fill: string;
};

type Message = {
  step: number;
  from: number;
  to: number;
  label: string;
  kind: "sync" | "return";
};

type Activation = {
  lane: number;
  start: number;
  end: number;
};

const { tokens } = useHostTheme();

const participants: Participant[] = [
  { name: "Client", role: "Browser / App", color: tokens.chart.lightBlue, fill: tokens.status.infoBg },
  { name: "API Gateway", role: "Routing", color: tokens.accent.control, fill: tokens.primary.bg },
  { name: "Auth Service", role: "Identity", color: tokens.chart.green, fill: tokens.status.successBg },
  { name: "Database", role: "Users", color: tokens.chart.goldenYellow, fill: tokens.status.warningBg },
];

const messages: Message[] = [
  { step: 1, from: 0, to: 1, label: "POST /login", kind: "sync" },
  { step: 2, from: 1, to: 2, label: "validateToken()", kind: "sync" },
  { step: 3, from: 2, to: 3, label: "SELECT user", kind: "sync" },
  { step: 4, from: 3, to: 2, label: "User record", kind: "return" },
];

const activations: Activation[] = [
  { lane: 1, start: 1, end: 4 },
  { lane: 2, start: 2, end: 4 },
  { lane: 3, start: 3, end: 4 },
];
```

Layout math and arrow markers:

```tsx
const laneLeft = 132;
const laneGap = 228;
const rowTop = 154;
const rowGap = 50;
const laneX = (index: number) => laneLeft + index * laneGap;
const rowY = (step: number) => rowTop + (step - 1) * rowGap;

<defs>
  <marker id="syncArrow" markerWidth={7} markerHeight={7} refX={6.2} refY={3.5} orient="auto" markerUnits="strokeWidth">
    <path d="M 1 1 L 6 3.5 L 1 6" fill="none" stroke={tokens.text.secondary} strokeWidth={1.15} strokeLinecap="round" strokeLinejoin="round" />
  </marker>
  <marker id="returnArrow" markerWidth={7} markerHeight={7} refX={6.2} refY={3.5} orient="auto" markerUnits="strokeWidth">
    <path d="M 1 1 L 6 3.5 L 1 6" fill="none" stroke={tokens.accent.control} strokeWidth={1.15} strokeLinecap="round" strokeLinejoin="round" />
  </marker>
</defs>
```

Participant lanes and activation bars:

```tsx
{participants.map((participant, index) => (
  <g key={participant.name}>
    <rect x={laneX(index) - 70} y={38} width={140} height={54} rx={8} fill={participant.fill} stroke={participant.color} />
    <circle cx={laneX(index) - 54} cy={54} r={4} fill={participant.color} />
    <text x={laneX(index)} y={64} textAnchor="middle" fill={tokens.text.primary} fontSize={13} fontWeight={650}>{participant.name}</text>
    <text x={laneX(index)} y={80} textAnchor="middle" fill={tokens.text.tertiary} fontSize={10.5}>{participant.role}</text>
    <path d={`M ${laneX(index)} 112 L ${laneX(index)} 742`} stroke={participant.color} strokeDasharray="4 7" opacity={0.72} />
  </g>
))}

{activations.map((activation, index) => {
  const participant = participants[activation.lane];
  return (
    <rect
      key={index}
      x={laneX(activation.lane) - 5}
      y={rowY(activation.start) - 18}
      width={10}
      height={rowY(activation.end) - rowY(activation.start) + 36}
      rx={5}
      fill={participant.fill}
      stroke={participant.color}
    />
  );
})}
```

Message renderer:

```tsx
function renderMessage(message: Message) {
  const y = rowY(message.step);
  const fromX = laneX(message.from);
  const toX = laneX(message.to);
  const direction = toX > fromX ? 1 : -1;
  const isReturn = message.kind === "return";
  const lineColor = isReturn ? tokens.accent.control : tokens.text.secondary;

  return (
    <g key={message.step}>
      <path
        d={`M ${fromX + direction * 13} ${y} L ${toX - direction * 17} ${y}`}
        fill="none"
        stroke={lineColor}
        strokeWidth={1.25}
        strokeLinecap="round"
        strokeDasharray={isReturn ? "5 6" : undefined}
        markerEnd={isReturn ? "url(#returnArrow)" : "url(#syncArrow)"}
      />
      <text x={(fromX + toX) / 2 - 18} y={y - 19} fill={tokens.text.primary} fontSize={12}>
        {message.step}. {message.label}
      </text>
    </g>
  );
}
```

Implementation notes:

- Use one compact participant card per lane. Prefer a small color dot and text; avoid large icons.
- Use color tokens only. Good defaults: `tokens.text.secondary` for sync calls, `tokens.accent.control` for return or async calls, each participant's `tokens.chart.*` or `tokens.status.*` color for its lane.
- Keep call lines thin. Use open arrowheads around 7px, with line width around 1.25px.
- Put step number and label slightly above the line, not inside a heavy pill.
- Render sync calls as solid lines and return or async calls as dashed lines.
- Render activation bars as narrow vertical rounded rectangles on the receiver lane.
- Do not add large phase boxes unless the flow has many independent phases. If needed, use a separate summary strip below the diagram.
- Keep the diagram horizontally scrollable on narrow canvases; do not shrink text with viewport width.
