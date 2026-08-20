# Plugins Validation Checklist (Fallback)

This checklist is used when dynamic documentation fetch fails. May be outdated - prefer fetched standards.

**Last Updated**: 2026-01-17

---

## Plugin Structure

Plugins package skills, agents, and hooks for distribution.

### Required Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Manifest (ONLY file in .claude-plugin/)
├── agents/                  # At root, NOT in .claude-plugin/
│   └── *.md
├── skills/                  # At root, NOT in .claude-plugin/
│   └── skill-name/
│       └── SKILL.md
└── hooks/                   # At root, NOT in .claude-plugin/
    └── hooks.json
```

### Critical Rule

All component directories (`agents/`, `skills/`, `hooks/`) MUST be at plugin root, NOT inside `.claude-plugin/`.

---

## Plugin Manifest

### Location

`.claude-plugin/plugin.json`

### Format

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "What this plugin provides",
  "skills": [
    "skill-one",
    "skill-two"
  ],
  "agents": [
    "agent-one"
  ]
}
```

---

## Critical Rules

- [ ] `.claude-plugin/plugin.json` exists
- [ ] Manifest JSON is valid
- [ ] `name` field present and valid
- [ ] Component directories at root (not in .claude-plugin/)

## High Priority

- [ ] `version` follows semver
- [ ] `description` explains plugin purpose
- [ ] All skills listed in manifest exist in `skills/`
- [ ] All agents listed in manifest exist in `agents/`
- [ ] Skills follow flat directory structure (one level)

## Medium Priority

- [ ] README.md documents usage
- [ ] License file present
- [ ] No unused skills/agents
- [ ] Consistent naming

## Low Priority

- [ ] Example configurations
- [ ] Changelog maintained
- [ ] Contributing guidelines

---

## Skills Directory Structure

### Flat Structure (Required)

```
skills/
├── skill-one/
│   └── SKILL.md
├── skill-two/
│   ├── SKILL.md
│   └── references/
└── skill-three/
    └── SKILL.md
```

### Invalid Structure

```
skills/
├── atomic/              # NO nested categories
│   └── skill-one/
└── composite/           # NO nested categories
    └── skill-two/
```

---

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Missing plugin.json | Critical | Create `.claude-plugin/plugin.json` |
| Invalid JSON | Critical | Fix JSON syntax |
| Components in .claude-plugin/ | Critical | Move to root level |
| Nested skills structure | High | Flatten to single level |
| Missing manifest entry | High | Add to skills/agents array |
| Unlisted component | Medium | Add to manifest or remove |

---

## Installation

Plugins can be installed via:

1. Local path: `claude plugins add /path/to/plugin`
2. Git repository: `claude plugins add https://github.com/org/plugin`
3. npm package: `claude plugins add @org/plugin`

---

## Environment Variables

Plugins have access to:

| Variable | Description |
|----------|-------------|
| `$CLAUDE_PLUGIN_ROOT` | Absolute path to plugin directory |
| `$CLAUDE_PROJECT_DIR` | Absolute path to project directory |

Use these in hooks and scripts for portable paths.
