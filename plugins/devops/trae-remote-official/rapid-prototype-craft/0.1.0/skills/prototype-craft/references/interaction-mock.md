# interaction-mock · Interaction Patterns & Mock-Data Conventions

Goal: make the prototype **truly clickable, switchable, and stateful**, while using mock data + stubbed APIs to demonstrate the "future backend" look — never introducing a real backend.

## 1. Interaction Realism Floor

A prototype is not a static image; interactive elements must actually respond:

- **Navigable**: real navigation between pages (multi-file cross-links, or a single-page SPA switching via hash/state).
- **State management**: a lightweight state object (plain JS object / module variable) centrally manages current tab, selection, form values, modal open/close, countdowns, pagination, etc.; when state changes, the UI follows.
- **Usable forms**: controlled inputs, validation feedback, and a clear result state after submit (success/failure/loading).
- **Common interactions covered**: tab switching, modal/drawer toggling, dropdown/multi-select, sort/filter, pagination, collapse, toast, loading skeletons.
- **Persistence as needed**: streaks, drafts, theme, etc. persisted via `localStorage`, surviving refresh.
- **Feedback motion**: transitions on hover, click, and switch; restrained, not flashy.

## 2. Mock-Data Conventions

- Keep mock centralized in one place (e.g. `mock.js` or a top-of-page `const DB = {...}`); **pages read from mock, no scattered hard-coding.**
- Data is **business-appropriate and voluminous enough to fill the UI** (8~20 items per list, covering long/short text, empty states, edge cases); realistic copy, no "sample 1/lorem".
- Write the mock schema into the design contract, shared across pages, ensuring cross-page data consistency (e.g. usernames, order numbers match across pages).

```js
// mock.js — single source of data example
export const DB = {
  users: [{ id: 1, name: "Zhang Ming", role: "Sales", store: "Beijing Chaoyang" }, ...],
  orders: [{ id: "SO2026-0012", user: 1, amount: 3980, status: "Closed" }, ...],
};
```

## 3. API Stubbing (key: demonstrate "backend-ready" without really connecting)

Users often say "write the API for the model/backend first, don't call it." The approach is to **keep a layer of async service functions** that return mock internally, but whose signature, latency, and loading/error match a real API — later just swap the implementation to connect the real API:

```js
// api.js — API stubs; the shape IS the future real API
async function fetchOrders({ page = 1 } = {}) {
  await delay(400);                 // simulate network latency so the loading state is visible
  // TODO: replace with fetch('/api/orders') — keep the shape identical
  return { code: 0, data: DB.orders.slice((page-1)*10, page*10), total: DB.orders.length };
}
async function askAI(prompt) {
  await delay(600);
  // TODO: replace with a real model call; currently returns a canned demo reply
  return { reply: mockReplyFor(prompt) };
}
```

Conventions:
- Name and parameterize stub functions **per the real API design**, marking the integration point with `// TODO: replace with ...`.
- Annotate each stub with its intended **HTTP method + path + request/response shape** (in the `// TODO` comment or a header block), so a later backend handoff can mechanically extract a neutral contract (see `backend-handoff.md`).
- Include `delay()` so loading/skeleton states actually appear, making the demo more convincing.
- For AI features, return **canned, scenario-relevant** demo replies; don't call a real model or pretend to reason.
- Never introduce a database, server process, or auth backend; "login" uses front-end mock validation (e.g. demo account 1234/1234).

## 4. Code Organization (for easy iteration and later upgrades)

- Clear, modular structure. **Static projects**: `index.html` / `styles.css` / `state.js` / `mock.js` / `api.js` / component fragments. **Build-type projects**: the equivalent modules under `src/` — a state layer (store / hooks / context), `src/mock/` (the single data source), `src/api/` (the async stub service layer), and component files; the file names differ but the **three-way separation of state / data / view and the API-stub layering are identical**.
- The API-stub principle (§3) is stack-neutral: keep one async service layer returning mock with real-API-shaped signatures, whatever the stack. In build-type projects this is `src/api/*` modules; the `// TODO: replace with ...` markers and HTTP method/path/shape annotations still apply so a later handoff can extract the contract mechanically.
- Separate state, data, and view so that under the iterate intent you can **change locally without disturbing everything.**
- Add brief comments on key interactions explaining data source and integration points, so the user can later hand it to an engineering team.
