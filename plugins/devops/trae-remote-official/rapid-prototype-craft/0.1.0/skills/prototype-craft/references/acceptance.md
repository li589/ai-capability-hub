# acceptance · Static Review & Acceptance Checklist

The final step before every delivery. Goal: ensure the prototype **is high-fidelity, is multi-page consistent, and free of cheap AI slop**, then deliver a shareable artifact. **All checks are performed by static code review (reading the source); NEVER open a browser or take screenshots for visual verification. For build-type projects (React/Vite/Three.js…) ONE `npm install && npm run build` compile check is allowed** to confirm compilation — once the static review (and, for build type, the compile check) passes, the task is complete.

## 0. Static Code Review (③.5 — the FINAL verification, source-reading only)

A fast bug-sweep on the generated code to catch the obvious defects that most often break prototypes. **Do this by reading the source; no browser, no visual preview, no screenshots** (build-type projects may run one `npm run build` compile check — build verification, not a visual preview). Scope discipline: **fix only clearly-broken things; do not refactor or restyle working code.** Anything ambiguous → note it, don't silently rewrite.

**Nav integrity (highest priority — the recurring "nav moves/disappears" bug):**
- [ ] Every page contains the frozen App Shell + Nav from the contract, **byte-identical** — diff the shell/nav block across pages by reading the files; reject any drift in markup, order, hrefs, or positioning CSS.
- [ ] Nav positioning is deterministic (fixed/sticky or fixed grid column with matching content offset), so it cannot reflow with content height.
- [ ] Exactly one active-state mechanism is used, and each page marks the correct current item — no per-page hand-editing that shifts the look.
- [ ] If nav is JS-injected: every page calls the mount, it runs early/idempotently, and the mount is unconditional (no async-only appearance).

**JS / runtime correctness (by reading code, not by running it):**
- [ ] No references to undefined mock/state variables or functions; no calls to handlers that don't exist.
- [ ] Script/style tags and their `src`/`href` point to files that exist; no obviously broken includes.
- [ ] If Lucide CDN is used, `lucide.createIcons()` is actually called after DOM ready (else icons render blank).

**Build-type projects only (React/Vue/Vite/Three.js…):**
- [ ] All `import` paths resolve; every imported symbol is actually exported; no leftover imports of deleted modules.
- [ ] Every third-party lib used is declared in `package.json` `dependencies` (not just assumed present).
- [ ] Component props/types are consistent (TS types line up; no obvious prop-name mismatch between definition and usage).
- [ ] `vite.config.*` uses a relative `base` so the built `dist/` can be opened/hosted statically.
- [ ] Run the ONE allowed `npm install && npm run build` compile check; fix any compile/type errors it surfaces (do not preview the running app).

**Links & structure:**
- [ ] All in-prototype links/hrefs resolve to real files/anchors — no dead `#`-only links meant to navigate.
- [ ] No duplicate `id` attributes; `for`/`aria` references point to existing ids.
- [ ] Relative asset paths (css/js/images) point to files that actually exist in the project folder.
- [ ] **Offline integrity (pure-static)**: no external CDN `<script>`/`<link>`/`@import`/CDN `@font-face` (icons, fonts, libs) unless the user has explicitly given up the offline requirement — otherwise icons must be inline SVG and fonts system/self-hosted woff2 (per `design-spec.md` §3/§5). Any leftover CDN reference in an offline-required deliverable is a defect.

**Obvious code smells (fix if clearly wrong):**
- [ ] No leftover placeholder like `TODO fill`, empty `href=""`, `onclick="undefined"`, or commented-out broken blocks shipped as-is.
- [ ] Stub `api.js` functions are wired to the UI (not defined-but-never-called where the UI needs them).

> Detect by carefully reading the source files and cross-referencing (grep for undefined symbols, diff shell blocks). Fix, re-read, then proceed to §1 acceptance and §2 delivery. **Do not verify by previewing.**

## 1. Acceptance Checklist (self-check by reading the code; don't deliver until all pass)

> All items below are verified by **reading the source code**, not by previewing. E.g. "interactive elements respond" means the handler is wired in code; "states are rendered" means the loading/empty/error branches exist in the markup/JS.

**Interaction usability**
- [ ] Navigation between pages is genuinely reachable, no dead links.
- [ ] Interactive elements actually respond: tab/modal/dropdown/multi-select/sort/filter/pagination — at least those used in this prototype.
- [ ] Forms accept input, have validation feedback, and a submit result state (success/failure/loading).
- [ ] loading / empty / error states are rendered, not a blank screen.
- [ ] APIs go through stub functions (the `api` layer), marked with `// TODO replace`; no real backend/model connected.

**Fidelity & visuals**
- [ ] Strictly use the contract's tokens (colors/type sizes/radii/spacing), no invented styles.
- [ ] Passes design-spec's "Anti-AI-Slop Checklist" (type hierarchy, restrained shadows, ≤3 primary colors, systematic spacing, unified icons, realistic Chinese copy).
- [ ] Has hover/active/focus/disabled states.
- [ ] Icons unified via one icon system (Lucide inline/CDN for static, or an icon npm package for build-type), consistent size/stroke/color; **no emoji acting as icons**.
- [ ] Has a clear aesthetic direction (contract `aesthetic` realized): paired display+body fonts, non-default fonts; no "purple gradient on white" cliché.
- [ ] Has one well-choreographed page-load animation (staggered reveal) + key hover/transition; background is not a flat solid fill and has atmosphere.

**Multi-page consistency (when multi-page/multi-surface)**
- [ ] Sidebar/top bar/colors/components are exactly identical across all pages.
- [ ] Shared components are genuinely reused, not rewritten per page.
- [ ] Cross-page mock data matches (the same user/order is consistent across pages).

**Responsiveness**
- [ ] Mobile-first scenarios adapt to viewport and safe-area; desktop/admin windows don't collapse on resize.

**Code iterability**
- [ ] Modular structure (view/state/data/API separated), easy for later local iterate edits.
- [ ] Mock centralized in a single data source, key integration points commented.

## 2. Delivery

- **One project, one self-contained folder**: every prototype lives in its own `<delivery>/<project-slug>/` subfolder — never dumped into the delivery root and never mixed with another project's files.
- **Pure-static type**: verify the folder holds a complete, self-contained set (`index.html` entry + pages + `styles.css` + `mock.js` + `api.js` + `assets/`, plus `contract/` for handoff), all via relative paths, **zero external dependency and openable offline** by double-clicking `index.html`. Hand over via a `computer://` link.
- **Build type**: verify the folder is a runnable project (`package.json` + `vite.config.*` + `src/` + `index.html`) and that the ③.5 `npm run build` compile check passed. Deliver via a `computer://` link to the project folder, and note that running it requires `npm install && npm run build` (then open/host `dist/`); it is not double-click-offline like the static type. Do not commit `node_modules/`.
- Bitmap assets live in `<project-slug>/assets/`; give a separate `computer://` link per deliverable.
- If the user mentions "want an experience link / to post / show to others": for static type, explain it's an offline-openable artifact they can send directly or host on any static space; for build type, they build it and host the `dist/` output. This skill does not do real deployment.
- If the user signals moving toward a real backend (handoff intent): additionally export the `contract/` directory and three-tier onboarding guidance per `backend-handoff.md`; verify each stub in the `api` layer maps to one contract endpoint and the data model covers all mock entities.

## 3. Boundary Reminder (confirm once more at wrap-up)

If during the process the user asks for a real backend, real database, production deployment, or user-behavior analytics — apply the boundary rule in `SKILL.md`: export the neutral handoff contract + three-tier guidance (`backend-handoff.md`) if requested, but the prototype itself stops at "high-fidelity interactive + mock + shareable static artifact," and whether to build the backend is the user's call.
