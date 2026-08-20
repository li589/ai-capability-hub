---
name: todo-tracker
description: "Manages Sailor's todo list. Triggers on: 'add todo', 'add this to my list', 'new todo', 'remove todo', 'delete todo', 'done with [todo]', 'show todos', 'my todos', 'what's on my list'. Stores todos in todos.json with date, text, and priority (0 or 1)."
version: 1.0.0
author: rob
tags:
  - todo
  - list
  - reminders
install_source: official
install_method: download
skill_id: official_fvTbrPx8
enabled_at: 1787230929964
name_zh: 待办事项跟踪器
---

# todo-tracker

Manages a simple todo list stored in `todos.json` at the workspace root.

## Data File

`/data/.openclaw/workspace/todos.json`

```json
[
  {
    "id": 1,
    "date": "2026-04-19",
    "text": "Research neck hypertrophy exercises",
    "priority": "LOW"
  }
]
```

- `id` — two-digit integer (1–99). Display zero-padded (01, 02, etc.). Use max existing id + 1.
- `date` — `YYYY-MM-DD` or `null` if no date given.
- `text` — the todo description.
- `priority` — `"LOW"` (default) or `"HIGH"`. All todos are LOW unless Sailor says otherwise.

## Add a Todo

Trigger: "add todo", "add this to my list", "new todo", "remind me to", "put [X] on my list", or similar.

1. Read `todos.json` (create with `[]` if missing).
2. Parse the description and optional date from the message.
3. If no date provided, set `date` to `null`.
4. If no priority mentioned, set `priority` to `"LOW"`. If Sailor says "high priority", "important", or "priority high", set to `"HIGH"`.
5. Append the new item with the next available `id`.
6. Write the file.
7. Reply: `✅ Added: "[text]"`

## Remove a Todo

Trigger: "remove todo", "delete todo", "done with [X]", "cross off [X]", "finished [X]", or similar.

1. Read `todos.json`.
2. Match by text (fuzzy — partial match is fine) or by id if a number is given.
3. Remove the matching item.
4. Write the file.
5. Reply: `✅ Removed: "[text]"`

If ambiguous (multiple matches), list them and ask which one.

## Show Todos

Trigger: "show todos", "my todos", "what's on my list", "todo list", or similar.

1. Read `todos.json`.
2. Group by priority: HIGH first, then LOW. Within each group, sort by date ascending (nulls last).
3. Reply with a bulleted list grouped by section. Only show due dates if they exist.

Format:
```
📋 Todos

HIGH
[01] description
[02] description (2026-04-20)

LOW
[03] description
[04] description
```

If a section is empty, show "(none)" under it. Bold the section headers. IDs are always zero-padded to two digits. Due dates shown only when present — append after the description in parentheses.

## Rules

- Never overwrite the file — always read, modify, write.
- IDs are never reused. If item 3 is deleted, the next item is still max(ids) + 1.
- Keep replies to one line for add/remove. Show list only when asked.
