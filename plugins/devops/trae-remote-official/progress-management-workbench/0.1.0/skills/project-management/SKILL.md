---
name: project-management
description: "Skill for lightweight project / task management via a self-contained HTML board. Triggers on 项目管理 / project management, 任务看板 / task board / kanban, 工作项 / work item / ticket tracking, 需求列表 / requirement list, 迭代管理 / sprint. Produces a single-file web app (HTML/CSS/vanilla JS, data in localStorage) with multiple views — a table list and a kanban board — in a clean light theme."
---

# Project Management

Ship a single-file project board the user can open in any browser. No build step, no backend — data lives in `localStorage`. The template supports two views (工作项列表 table + 看板视图 kanban), stat cards, filtering, search, and inline create/edit/delete.

> [!IMPORTANT]
> **Always state the storage limitation when delivering this board — in plain language.** Keep it short and direct; avoid jargon like `localStorage`, "seed data", "backend", "sync". Say it the way you'd tell a non-technical colleague, e.g.:
> - "换一台电脑、换个浏览器、或者清理了浏览记录，之前填的就没了。"
>
> If the user needs several people to share and update the same board, just tell them plainly this version can't do that.

## 1. Usage

1. Copy [scripts/board-template.html](scripts/board-template.html) to the target location (or hand it to the user directly).
2. Customize the `CONFIG` object at the top of the `<script>` block — that's the only section you normally touch.
3. Open the file in a browser. Data persists per-browser under `CONFIG.storageKey`.

The template is intentionally self-contained: one HTML file, no dependencies, safe to email or drop into any static host.

## 2. What to customize (the `CONFIG` block)

Everything user-specific lives in one object; the engine below it rarely needs edits.

- **`statuses`** — the workflow stages. These double as the kanban columns (order = column order). Each has a `label` and badge colors.
- **`priorities`** — priority levels (P0/P1/P2…) and their badge colors.
- **`columns`** — which fields show in the table view and their headers. `type: "status" | "priority"` renders a colored badge; omit `type` for plain text.
- **`seed`** — starter rows, used only when `localStorage` is empty. Replace with the user's real fields/data.
- **`stats`** — the top summary cards; each `calc(items)` returns the number to show.
- **`storageKey`** — the localStorage bucket. Bump it to force a clean reset.

To **add a field** (e.g. 业务线, 提出时间): add it to each `seed` item, add a `columns` entry to surface it in the table, and add the input to the modal if it should be editable.

## 3. Theme

Light theme by default. All colors, radius, and fonts are CSS variables under `:root` at the top of `<style>` — edit `--accent`, `--bg`, `--surface`, `--border` to re-skin. Badge colors are set per-status/priority in `CONFIG`.

## 4. Views

- **工作项列表** — dense table; click a row name to edit.
- **看板视图** — one column per status; drag a card between columns to change its status (auto-saved).

Add a new view by adding a `.tab` with a `data-view` and a matching render branch in `render()`.
