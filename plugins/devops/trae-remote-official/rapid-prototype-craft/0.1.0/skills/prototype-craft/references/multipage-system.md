# multipage-system · Multi-Page / Multi-Surface Consistency & Parallel Orchestration

Goal: when a prototype spans multiple pages, multiple surfaces (client + guide/sales + PC/mobile sidebar), or "phase 2 references phase 1 to stay consistent," ensure they are produced as if from **one design system**, and use parallel sub-agents for speed — without sacrificing consistency.

## 1. The Single Source of Consistency: Design Contract + Shared Components

- All pages **must reference the same design contract** (see design-spec.md) and the **same mock** (see interaction-mock.md).
- Extract a **shared layer**: for static projects `styles.css` (tokens + component classes) + `components.js` (reusable fragments: nav, sidebar, header, card, table, modal…); for build-type projects the equivalent shared modules (a `Layout` component + design tokens + reusable components). Each page composes shared components rather than writing its own.
- Sidebar / top bar / colors / spacing / icons are **exactly identical** across all pages; only the main content area differs.

## 1.5 App Shell + Canonical Nav (mandatory — the fix for "nav moves / disappears")

The most common multi-page defect is the navigation **shifting position or vanishing** when switching pages. Root cause: each page (or each sub-agent) re-authors its own layout skeleton and nav markup, so structure and positioning drift, or a page forgets/ mis-mounts the nav. Eliminate it by freezing ONE shell and forbidding re-authoring.

**Rules:**
1. **Freeze one App Shell in the contract.** Define the exact outer skeleton once — a wrapper + the nav/sidebar/top-bar block + a single main-content slot — plus its positioning CSS. Every page uses this skeleton **verbatim (byte-identical)**; only the main-content slot changes. Sub-agents copy-paste it; they never rewrite it.
2. **Nav markup is copy-paste boilerplate, not generated per page.** The full list of nav items, their order, icons, and hrefs live in the contract. A page must not add/remove/reorder items or restyle the nav.
3. **Deterministic positioning.** The shell must reserve space for a fixed/sticky nav so content never overlaps or reflows it. For a sidebar layout: nav is `position: fixed` (or a CSS grid column of fixed width) and the content region has a matching `margin-left`/grid placement — identical values on every page. Never let nav be a normal in-flow block whose position depends on content height.
4. **One active-state rule.** Mark the current item by a single agreed mechanism — e.g. add `aria-current="page"` / an `.active` class to the `<a>` whose `data-nav` key matches the current page. Do NOT hand-edit a different item per page (a frequent cause of the nav "looking moved"). If using injected nav, set active from `document.body.dataset.page` after injection.
5. **If nav is JS-injected, guarantee it mounts.** Injecting the nav via `components.js` is fine, but the mount must be synchronous/early and idempotent, and every page must actually call it. Prefer inline shell HTML on each page (most robust, zero-JS-dependency) unless the project already uses SPA routing. A nav that only appears after an async call is a disappearing-nav risk.

**Minimal robust pattern (sidebar, inline shell — recommended default):**

```html
<body data-page="orders">           <!-- the only per-page difference in the shell -->
  <aside class="app-nav"> ... identical nav markup on every page ... </aside>
  <main class="app-content"> <!-- page-specific content ONLY goes here --> </main>
  <script src="nav-active.js"></script> <!-- sets .active from data-page; no layout work -->
</body>
```

```css
.app-nav     { position: fixed; inset: 0 auto 0 0; width: var(--sidebar-w); }
.app-content { margin-left: var(--sidebar-w); }  /* same on every page → nav can't move */
```

> Enforcement: the ③.5 static review (acceptance.md §0) diffs the shell/nav block across pages and rejects any drift.

**Build-type / SPA equivalent (React/Vue + router):** the same "freeze once, never re-author" principle applies, but the shell is **one shared `Layout` component** instead of copy-pasted HTML:
- Define a single `<Layout>` (or `AppShell`) component that renders the nav/sidebar once and a routed content outlet (`<Outlet/>` in React Router / `<router-view>` in Vue). Every route renders **inside** this one Layout — page components must NOT render their own nav.
- Nav items live in one shared config array (label/icon/path); the Layout maps over it. Active state comes from the router's current path (e.g. `NavLink` `isActive`), not hand-set per page — this is the SPA form of the "one active-state rule."
- Because the Layout is mounted once at the app root and only the outlet swaps, the nav **cannot remount or shift** between route changes — this is structurally why SPA layout avoids the "nav disappears" bug, provided pages never wrap themselves in a second shell.
- The ③.5 check for SPA: confirm there is exactly ONE Layout/shell component, the router nests all pages under it, and no page component re-declares nav markup.

## 2. Page Splitting & Information Architecture

Before writing code, define the page list in the contract:

```
page name | surface(client/admin/mobile) | responsibility | reused components | navigation
Home       | client | entry/overview         | Nav, Card      | → detail, → list
List       | admin  | data management        | Sidebar, Table | → detail, → edit modal
...
```

- Make explicit which "surface" each page belongs to; within a surface share one shell; surfaces may differ but tokens share the same source.
- Pages navigate via real, clickable links (multi-file cross-links or SPA routing).

## 3. Parallel Sub-Agent Orchestration (max 3 in parallel)

| Scale | Orchestration |
|---|---|
| 1~2 pages | Main agent writes directly, no fan-out |
| 3+ pages / multi-surface | Main agent first builds the shared layer (css + components + mock + contract), then fans out |

Fan-out rules:
1. **Main agent first produces and freezes the shared layer** — static: `styles.css` + the frozen App Shell/nav per §1.5 + `components.js` + mock + contract; build-type: the single `Layout` component + router setup + design tokens + shared components + mock + contract — ensuring sub-agents have stable dependencies.
2. Split tasks by page/surface among **no more than 3** sub-agents in parallel; each sub-agent's task **inlines the contract essentials + the frozen App Shell (or the `Layout` usage) + shared-component usage**, and explicitly states "static: paste the App Shell + Nav verbatim; build-type: render inside the shared `Layout`, never re-author nav; only fill the main-content slot / page component; only use tokens and shared components from the contract; do not invent styles or re-author navigation."
3. Each sub-agent handles only the main content area / page component of its assigned pages, outputting to designated files.
4. After collecting results, the main agent performs a **unified review**: run the ③.5 static review (acceptance.md §0) — including a shell/nav cross-page diff (static) or the single-`Layout` check (SPA) — then cross-page visual consistency, component reuse, and navigation connectivity.

> Sub-agents cannot see each other's output, so "shared layer first + App Shell frozen + contract inlined" is the guarantee of consistency; never let sub-agents each decide global styles or write their own nav.

## 4. Consistency Inheritance under the iterate Intent

- "Phase 2 references phase 1" / "this page references that page": **read the existing output first**, extract its tokens/components/layout into (or update) the contract, then generate new pages accordingly, keeping interaction logic and layout consistent.
- Local edits (add a field / add a button / change a modal): touch only the target area, keep all other pages and components **1:1 intact**, don't re-layout opportunistically.
- New pages must reuse existing shared components and colors, not start a fresh style.
