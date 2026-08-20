# Agent installation guide

This file is written for agents and operators who want a fast setup path.

## Option 1: direct repo use

```bash
git clone https://github.com/misolith/agent-memory-journal.git
cd agent-memory-journal
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/pytest -q
agent-memory-journal --root /path/to/memory-root recent --days 2
```

## Expected memory layout

```text
/path/to/memory-root/
├── MEMORY.md
└── memory/
    └── YYYY-MM-DD.md
```

## Minimal agent usage pattern

Store a note:

```bash
agent-memory-journal --root /path/to/memory-root add --note "Remember this decision"
```

Store a durable note:

```bash
agent-memory-journal --root /path/to/memory-root add --note "From now on, use the app login path" --long
```

Review recent notes:

```bash
agent-memory-journal --root /path/to/memory-root recent --days 2
```

Generate a compact review:

```bash
agent-memory-journal --root /path/to/memory-root digest --days 7
```

## Configurable triggers

Optional file:

```text
/path/to/memory-root/agent-memory-journal.json
```

Example:

```json
{
  "triggers": [
    "\\bremember\\b",
    "\\bdecision\\b",
    "\\bfrom now on\\b",
    "\\bpriority\\b"
  ]
}
```

## Recommended agent behavior

- prefer `--root` explicitly
- use `--long` only for real durable facts or policy
- use `candidates` before mass-promoting memory items
- keep files human-readable and easy to diff

## Reflection pattern

Before ending a task or session:

```bash
agent-memory-journal --root /path/to/memory-root digest --days 7
agent-memory-journal --root /path/to/memory-root candidates --days 7
```

If something is clearly durable, then store it with `--long`.
