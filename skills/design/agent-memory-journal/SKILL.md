---
name: agent-memory-journal
description: Durable episodic memory for agents — file-based, inspectable, and easy to review. Use when an agent needs to keep a working journal of what happened, what mattered, and what should be remembered. Use when an agent needs to store important notes, search prior notes, prevent duplicate memory bullets, review recent activity, identify recurring topics, or suggest long-term memory candidates from daily notes. Useful for workflows involving MEMORY.md, daily journal files, lightweight memory systems, and agent continuity without a database.
install_source: official
install_method: download
skill_id: official_R6wZCllT
enabled_at: 1787231979963
version: 1.0.0
name_zh: 代理记忆日志
---

# Agent Memory Journal

Use the bundled CLI for durable memory operations.

## Core workflow

1. Choose a memory root.
   - Prefer `--root <path>` explicitly.
   - If omitted, the tool uses `AGENT_MEMORY_ROOT` or the current working directory.
2. Keep daily notes in `<root>/memory/YYYY-MM-DD.md`.
3. Keep long-term memory in `<root>/MEMORY.md`.
4. Use the CLI instead of manually appending when duplicate protection or review summaries matter.

## Commands

### Add a note

```bash
agent-memory-journal --root /path/to/root add --note "Remember to rotate the PAT before Friday"
```

Add to long-term memory too:

```bash
agent-memory-journal --root /path/to/root add --note "Use use the app login path for live tee-time checks" --long
```

### Review recent notes

```bash
agent-memory-journal --root /path/to/root recent --days 2
```

### Search memory

```bash
agent-memory-journal --root /path/to/root search --query "playing golf"
```

### Find patterns

```bash
agent-memory-journal --root /path/to/root topics --days 14
agent-memory-journal --root /path/to/root cadence --days 14
agent-memory-journal --root /path/to/root digest --days 7
agent-memory-journal --root /path/to/root candidates --days 7
```

### Extract memory-worthy lines from raw text

```bash
cat transcript.txt | agent-memory-journal --root /path/to/root extract
```

## Retrieval-first use

Before solving a new issue, check whether the journal already contains a similar failure, decision, or workflow.

Examples:

```bash
agent-memory-journal --root /path/to/root search --query "oauth token refresh failed"
agent-memory-journal --root /path/to/root search --query "playing golf booking flow"
```

Use this before starting a fresh fix when prior context might already exist.

## End-of-session reflection

At the end of a work session, prefer a small reflective write rather than many fragmented notes.

Good pattern:
1. Add 1-3 concrete notes for major decisions or failures during the work.
2. Run `digest` or `candidates` to review what stands out.
3. Promote only genuinely durable items into long-term memory.

Example:

```bash
agent-memory-journal --root /path/to/root digest --days 7
agent-memory-journal --root /path/to/root candidates --days 7
agent-memory-journal --root /path/to/root add --note "From now on, use the app login path for live tee-time checks" --long
```

Avoid spamming long-term memory with every operational note.

## Config

Optional config file:
- `<root>/agent-memory-journal.json`
- or pass `--config-file <path>`

Current config supports:
- `triggers`: regex list used by `extract` and `candidates`

See `examples/config.example.json`.

## Installation for agents

Use direct execution first. Do not assume packaging is installed.

### Minimal setup

```bash
git clone https://github.com/misolith/agent-memory-journal.git
cd agent-memory-journal
python3 -m venv .venv
.venv/bin/pip install pytest
```

Run tests:

```bash
.venv/bin/pytest -q
```

Run the tool directly:

```bash
agent-memory-journal --root /path/to/root recent --days 2
```

## Notes for agents

- Prefer explicit `--root` in automation.
- Use `--long` sparingly; not every note belongs in long-term memory.
- Use `candidates` before promoting many notes into `MEMORY.md`.
- Keep the memory system file-based and inspectable.
