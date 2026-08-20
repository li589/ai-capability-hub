---
name: "prototype-craft"
description: "Turn an idea/PRD/screenshot/URL/existing prototype into a high-fidelity, interactive, style-consistent prototype (plain HTML/CSS/JS by default; build-type stacks like React/Vite/Three.js when the need requires; mock data, stubbed APIs, no real backend). Invoke when the user wants to generate/iterate a prototype or Demo, recreate a reference page, or do fidelity/format conversion."
---

# Prototype Craft · High-Fidelity Interactive Prototype Orchestration

Turn an idea/PRD/screenshot/URL/existing prototype into a high-fidelity, interactive, style-consistent prototype (mock data, stubbed APIs, no real backend). The tech stack is routed per need (plain HTML/CSS/JS by default; build-type stacks like React/Vite/Three.js when the need requires). Writing code, reading files, scraping pages, and generating images all reuse base Agent capabilities; this skill supplies the standard of "doing it right" (design spec + anti-AI-slop), multi-page consistency via one Design Contract, and capability orchestration. **The skill does not visually preview the result: no browser, no screenshots — verification is static code review (build-type projects may run one `npm run build` compile check), and the task ends once that passes.**

## Boundaries (important)

- ✅ Do: high fidelity, interactivity, mock data, style consistency, multi-page consistency, static code review, exporting shareable static artifacts, fidelity/format conversion, prototype↔document, exporting an architecture-neutral **backend-handoff contract** (see `references/backend-handoff.md`).
- ❌ Don't: real backend / database / real deployment pipeline / user-behavior analytics / taking over full engineering / **opening a browser or taking screenshots for visual runtime verification** (a one-shot `npm run build` compile check for build-type projects is allowed — it verifies compilation, not visuals). When the user explicitly wants to "go live with real data," export the neutral handoff contract + three-tier onboarding guidance (per `backend-handoff.md`), then hand the decision back to the user; do not implement the backend inside this skill.

## Overall Orchestration Flow

`① Intent detection → ①.5 Tech-stack routing → ② Freeze the Design Contract (incl. App Shell + canonical Nav) → ③ Implement → ③.5 Static self-review → ④ Wrap-up.` Load the matching reference on demand per the routing table (do not read all at once).

## Intent Routing Table (the core of this skill — judge intent before acting)

| Intent | Trigger signals | Load reference | Orchestration action |
|---|---|---|---|
| **new** generate from scratch | "generate a prototype/demo" "build from zero" "design an X system/App/admin" | design-spec + interaction-mock + (if multi-page) multipage-system | Run full ②③④ |
| **iterate** modify existing | "change it to…" "add a button/field" "make this modal like…" | first read existing artifact + interaction-mock + design-spec (for token/style rules) | Precisely locate the changed page, rewrite locally, keep other pages 1:1; no fan-out |
| **convert** conversion | "high-fi to low-fi" "mockup compositing" "generate PRD from demo" "reverse a backend/dev doc from the prototype" | io-and-convert | Single-step conversion, no multi-page pipeline |
| **reference** recreate from reference | given a URL/screenshot/existing html "build/recreate like…" | io-and-convert + design-spec + interaction-mock (since it runs the full ②③ with interactivity & mock) | First scrape/read image → distill the design language into the contract → then run ②③ |
| **handoff** wire up a backend | "MVP looks good, how do I get a backend" "go live with real data" "connect a real API" | backend-handoff | Export an architecture-neutral `contract/` + three-tier onboarding guidance; do not implement the backend |

> When intent is unclear, default to **new**, but first restate in one sentence your understanding of the goal and page list before acting.

## ①.5 Tech-Stack Routing (decide the stack BEFORE freezing the contract)

The default is plain static, but some prototypes are physically impossible in vanilla JS (3D/simulation/shaders, heavy SPA state, etc.). Do **not** hardcode one stack — pick the **simplest stack that can satisfy the need** using a two-layer method. Two hard rules first:

1. **User named a stack → use it verbatim, no second-guessing.** (e.g. a prompt that says "React 19 + Three.js + Vite + Tailwind" is followed exactly.)
2. **User did NOT name one → infer via the dimensions below, choose the simplest sufficient stack, and state the choice in one sentence before writing code.**

**Layer 1 — Judgment dimensions (stable; reason with these, don't memorize scenarios):**
- Needs a **build tool / npm ecosystem** (ES modules, third-party libs)?
- Needs **component-based state management** (complex SPA, many interlocked views)?
- Needs a **specialized capability domain** — 3D/graphics, 2D canvas/game, maps, audio/video, rich-text editing, realtime/collaboration, heavy data-viz, or advanced animation?
- Delivery form: **pure-static & offline-openable**, or **build-then-deploy**?

**Layer 2 — Popular stack candidates (reference only; may age — prefer these, substitute as needed):**

| Capability need | Suggested stack | Delivery type |
|---|---|---|
| Static / light-interaction (landing, admin mock, forms, dashboards) | **plain HTML + CSS + vanilla JS** (default, simplest) | pure-static |
| Component-heavy SPA (complex state, multi-view apps) | React/Vue + Vite (+ Tailwind) | build |
| 3D / graphics / simulation / shaders / particles | Three.js (+ React + Vite if complex) | build (usually) |
| 2D game / canvas / whiteboard | Canvas API or Pixi.js | static or build |
| Maps / LBS / trajectories | Leaflet / Mapbox GL | static or build |
| Audio / video / media | Web Audio / Video API (+ framework if complex) | static or build |
| Rich-text / document editor | Tiptap / ProseMirror | build |
| Heavy data-visualization | + ECharts / D3 | static or build |
| Scroll-telling / animated marketing | + GSAP / Framer Motion | static or build |
| Realtime / collaboration UI | framework + WebSocket/mock event stream | build |

> These candidates will age; when a need isn't listed, fall back to the Layer-1 dimensions and choose the simplest sufficient stack. The stack decision drives **delivery type** (pure-static vs build), which every downstream rule (contract, shell, acceptance, delivery) branches on. Record the chosen stack + delivery type as the first field of the Design Contract.

## ② Design Contract (the linchpin of consistency)

Before fan-out or writing code, the main Agent writes the contract to a temp working directory (not polluting the delivery directory) as the single source of truth for all pages. Fields and value rules are in `references/design-spec.md`; at minimum it includes:

- **Tech stack + delivery type**: the stack chosen in ①.5 (e.g. `vanilla / pure-static` or `React+Vite / build`) — this drives shell, acceptance, and delivery branching;
- **Style tier**: pick one from the query (tech-dark / minimal-light / pixel / business-international / brand-themed…), set the tone;
- **design tokens**: primary/neutral color scales, type scale, radius, spacing, shadow;
- **Component spec**: unified styles and states for button/input/card/table/modal/nav-sidebar;
- **App Shell + canonical Nav (mandatory for multi-page)**: freeze ONE exact skeleton (static: an HTML shell wrapper + nav/sidebar/top-bar markup + positioning CSS; build-type/SPA: one shared `Layout` component with a routed outlet), plus the single rule for marking the active item. This is copy-paste/shared boilerplate — every page uses the identical shell verbatim (or renders inside the one Layout) and only fills the main-content slot. See `references/multipage-system.md` §1.5. This is the primary safeguard against the nav moving/disappearing between pages;
- **Page list**: information architecture + each page's responsibility + inter-page routing/navigation;
- **mock schema**: unified fake-data structure; the "stub only, don't call real models" API convention (see `interaction-mock.md`).

Once the contract is frozen, sub-agents **may only implement the assigned pages per the contract and must not improvise visuals, and must paste the frozen App Shell + Nav verbatim (never re-author navigation).**

## ③ Implementation & Sub-Agent Orchestration Rules

| Scenario | Orchestration |
|---|---|
| Single page / small prototype | Main Agent implements directly, **no fan-out** (avoid over-orchestration) |
| Multi-page / multi-surface (client + admin + sidebar, etc.) | Split by page, **up to 3 sub-agents in parallel**, each takes several pages, all strictly referencing the same contract |
| Iterative edits | No fan-out; rewrite only the changed region, keep other pages/components 1:1 |

**Speed principles (apply throughout ③):**
- **Shell-once, content-only**: the main Agent writes the shared shell once (static: `styles.css` + shell/nav markup + `mock.js` + `api.js`; build-type: the `Layout` component + tokens + `src/mock` + `src/api`); sub-agents and additional pages fill ONLY the main-content slot / page component. Not re-authoring the shell/nav per page is the single biggest speed win — and it also removes the root cause of the nav-drift bug (nav moving/disappearing between pages; see `multipage-system.md` §1.5).
- **Right-size orchestration**: don't fan out for 1-2 pages (sub-agent spin-up costs more than it saves); fan out only at 3+ pages, and give each sub-agent several pages rather than one-page-per-agent.
- **Inline only contract essentials** into each sub-agent task (tokens + shell snippet + its page's mock slice), not the whole contract, to keep prompts lean.
- **No premature polish**: build all pages first, then do one consolidated ③.5 static review + visual pass, instead of re-opening/re-editing each page repeatedly.

**Project layout — one project, one self-contained folder (mandatory):**
- Every prototype lives in its **own dedicated subfolder** under the delivery directory, e.g. `<delivery>/<project-slug>/`. Never scatter a project's files directly into the delivery root, and never mix two projects' files in one folder.
- **Pure-static type**: the folder is self-contained with `index.html` / pages / `styles.css` / `mock.js` / `api.js` / `assets/` (and, for handoff, `contract/`), referenced via relative paths, openable offline. Multi-page uses `index.html` as the entry; assets go in `<project-slug>/assets/`.
- **Build type**: the folder is a standard project — `package.json` + `vite.config.*` + `index.html` + `src/` (components/hooks/store, plus `mock`/`api` modules) + `assets/`; the built output goes to `dist/`. Use relative `base` in the build config so `dist/` can be opened/hosted as static. The `mock`/`api` stub layering rule is unchanged; only the file organization differs.
- When generating a **new** prototype, first create the project folder, then write all files into it. Under **iterate**, keep working inside the existing project folder — do not create a sibling copy.

Tech base is decided in ①.5, not fixed here. The **default** for static / light-interaction prototypes is plain HTML + CSS + vanilla JS with no build dependencies (mobile adaptation for viewport and safe-area); build-type stacks (React/Vue/Vite/Three.js…) are used when ①.5 routes to them. Delivery-type branching (pure-static vs build) is detailed in `acceptance.md`.

## ③.5 Static Self-Review (mandatory — the FINAL step; task ends here)

After code is written, the main Agent performs a fast **static code review** to catch the obvious, high-frequency bugs that break prototypes — do not skip this even for single pages. This is a focused bug-sweep, not a full audit: only fix clearly-broken things, do not refactor working code. **The review is source-reading only: do NOT launch a browser, start a preview server, or take screenshots for visual verification.** For **build-type** projects there is ONE exception: you may run a single `npm install && npm run build` **compile check** to confirm the project actually compiles (this is build verification, not a visual preview) — fix compile errors it surfaces, but still do not preview/screenshot the running app. Run the `references/acceptance.md` §0 "Static Review" pass:

- **Nav integrity first** (the recurring nav-drift bug): every page contains the frozen App Shell + Nav verbatim; the active item is marked by the single agreed rule; nav position/markup is byte-identical across pages (diff them by reading the files).
- Read the source to check: all in-prototype links point to real files/anchors (no 404 / dead hrefs); no duplicate `id`s; no references to undefined mock/state variables; no unbound event handlers; and — if Lucide CDN is used — `lucide.createIcons()` is actually called.
- Fix only clear, obvious defects; log anything ambiguous instead of silently rewriting.

Once the static review passes, go straight to ④ and deliver. **The task ends after delivery — no preview/screenshot verification step.**

Details and the concrete checklist live in `references/acceptance.md` §0.

## ④ Wrap-up

Always self-check against the `references/acceptance.md` checklist (interactions work / fidelity / multi-page consistency / anti-AI-slop / responsive) **by static code review only** (build-type projects may run one `npm run build` compile check per ③.5), then deliver the shareable artifact to the user with a `computer://` link. **Do NOT open a browser or take screenshots for visual verification — once the static review (and, for build type, the compile check) passes, the task is done.** When the user signals intent to move toward a real backend, follow `references/backend-handoff.md` to export the neutral contract and three-tier onboarding guidance.

## References (load on demand per intent routing, do not read all at once)

| Reference | When to read |
|---|---|
| `references/design-spec.md` | Any scenario needing visuals/contract writing (new / reference) |
| `references/interaction-mock.md` | Any scenario needing interactivity & fake data (new / iterate) |
| `references/multipage-system.md` | Multi-page / multi-surface / App Shell + canonical Nav / phase-2 inheriting phase-1 consistency |
| `references/io-and-convert.md` | Input parsing (URL/image/html/md), fidelity conversion, prototype↔document |
| `references/backend-handoff.md` | handoff intent, or when the user wants to wire up a real backend after MVP |
| `references/acceptance.md` | The ③.5 static code review (§0) and the pre-delivery acceptance checklist (static review; build-type may run one `npm run build` compile check, no visual preview) |
