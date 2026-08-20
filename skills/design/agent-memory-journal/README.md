# agent-memory-journal

Durable episodic memory for agents — file-based, inspectable, and easy to review.

`agent-memory-journal` helps keep daily notes, long-term memory, and compact review workflows in sync without requiring a database or external service. It is designed for agent setups that want durable memory with minimal moving parts.

Think of it as an agent's working journal: not just a fact store, but a durable record of what happened, what mattered, and what should be remembered.

## Why this exists

Many agent workflows have the same failure mode:
- useful facts are noticed but never written down
- daily notes turn into noise
- long-term memory becomes duplicated or bloated
- recall is possible in theory but painful in practice

`agent-memory-journal` is a pragmatic CLI for fixing that. It keeps memory in plain files, adds guardrails around duplication, and provides review commands that help turn recent logs into durable memory.

## Current status

This repository is the productization track.

The internal production version still lives separately in the main OpenClaw workspace. This repo is where cleanup, parameterization, packaging, tests, and public-facing documentation happen before any internal migration.

## Core capabilities

- append daily notes with duplicate protection
- optionally append long-term memory bullets
- search recent notes and long-term memory
- show recent activity and memory cadence
- surface recurring topics
- generate compact operational digests
- suggest likely long-term memory candidates from recent daily notes
- extract memory-worthy lines from raw text

## File layout

By default the tool expects a memory root with this structure:

```text
<root>/
├── MEMORY.md
└── memory/
    ├── 2026-03-28.md
    ├── 2026-03-29.md
    └── 2026-03-30.md
```

### Daily note format

Daily note entries are line-oriented and timestamped:

```text
- 08:15 Gmail watcher returned invalid_grant again.
- 17:01 Added topics command to memory maintenance tooling.
```

### Long-term memory format

`MEMORY.md` uses bullet points for durable facts, decisions, and policies:

```text
- Use use the app login path for live tee-time checks.
- Keep Gmail monitoring out of heartbeat to avoid duplicate notifications.
```

## Installation

For local development:

```bash
python3 -m venv .venv
.venv/bin/pip install pytest
```

Install in a virtual environment or editable dev mode:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
agent-memory-journal --help
```

## Bootstrap a new memory root

Initialize an empty memory root:

```bash
agent-memory-journal --root /path/to/root init
```

This creates:
- `MEMORY.md`
- `memory/`
- optional starter config if `--with-config` is used

## CLI usage

### Add a note

```bash
python3 agent_memory_journal.py --root /path/to/workspace add --note "Remember to renew the PAT before Friday"
```

### Add a note to long-term memory too

```bash
python3 agent_memory_journal.py --root /path/to/workspace add --note "Use playing golf app path for live tee time checks" --long
```

### Show recent notes

```bash
python3 agent_memory_journal.py --root /path/to/workspace recent --days 2
```

### Search memory

```bash
python3 agent_memory_journal.py --root /path/to/workspace search --query "playing golf"
```

### Review recurring patterns

```bash
python3 agent_memory_journal.py --root /path/to/workspace topics --days 14
python3 agent_memory_journal.py --root /path/to/workspace cadence --days 14
python3 agent_memory_journal.py --root /path/to/workspace digest --days 7
python3 agent_memory_journal.py --root /path/to/workspace candidates --days 7
```

### Extract likely memory-worthy lines from raw text

```bash
cat transcript.txt | python3 agent_memory_journal.py extract
```

## Configuration

The tool resolves its root in this order:

1. `--root /path/to/root`
2. `AGENT_MEMORY_ROOT=/path/to/root`
3. current working directory

Optional path settings:

- `--memory-dir memory`
- `--long-file MEMORY.md`


### Optional JSON config

You can provide a config file with `--config-file` or place `agent-memory-journal.json` in the root.

Example:

```json
{
  "triggers": [
    "\\bremember\\b",
    "\\bdecision\\b",
    "\\bfrom now on\\b"
  ]
}
```

The repository includes a starter file at `examples/config.example.json`.

## Alpha contract (0.1.x)

Stable for the alpha line:
- file layout: `<root>/MEMORY.md` and `<root>/memory/YYYY-MM-DD.md`
- commands: `add`, `extract`, `recent`, `search`, `stats`, `topics`, `cadence`, `digest`, `candidates`
- `--root`, `--config-file`, `--json`, and `--version`
- sentinel outputs such as `NO_MATCHES` and `NO_CANDIDATES`

Intended for automation:
- `recent --json`
- `search --json`
- `stats --json`
- `topics --json`
- `cadence --json`
- `digest --json`
- `candidates --json`

Platform note:
- current locking uses `fcntl`, so the alpha target is POSIX/Linux environments

## Design goals

- plain files, not a database
- easy to inspect manually
- safe against duplicate note spam
- useful both for agents and humans
- small enough to understand quickly


## Agent-oriented setup

If you want another agent to become productive from the repository URL alone, point it to:

- `SKILL.md` for procedural usage
- `examples/agent-install.md` for installation and first-run instructions

The intended flow is: clone repo -> create venv -> run tests -> use CLI with `--root`.

## Testing

Run tests with:

```bash
.venv/bin/pytest -q
```

Current coverage includes:
- repo smoke checks
- add + recent flow
- long-memory dedupe
- search flow
- digest flow
- temp-root execution

## Roadmap

Short-term:
- improve help text and examples
- add more focused unit tests
- clean up output contracts
- package for easier installation

Later:
- decide whether the CLI name and internal engine naming should fully converge
- publish a reusable skill/package around the standalone tool
- consider importable Python API if it stays small and coherent

## Repository layout

```text
agent-memory-journal/
├── agent_memory_journal.py
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── examples/
│   └── quickstart.md
└── tests/
    ├── test_smoke.py
    └── test_cli.py
```

## License

MIT


## Alpha release plan

Target first public milestone: `0.1.0`.

Release criteria:
- standalone execution without workspace-specific paths
- documented root/config model
- green test suite
- agent-facing setup instructions
- stable CLI for add/recent/search/topics/cadence/digest/candidates
