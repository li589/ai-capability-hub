# Agents Validation Checklist (Fallback)

This checklist is used when dynamic documentation fetch fails. May be outdated - prefer fetched standards.

**Last Updated**: 2026-01-17

---

## Agent Definition Format

Custom sub-agents are markdown files with YAML frontmatter:

```markdown
---
name: agent-name
description: What this agent does
model: sonnet
tools:
  - Read
  - Glob
  - Grep
skills:
  - skill-name
---

# Agent Name

Instructions for the agent...
```

---

## Frontmatter Requirements

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent name, should match filename |
| `description` | string | What the agent does |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | `haiku`, `sonnet`, or `opus` |
| `tools` | array | Allowed tools for this agent |
| `skills` | array | Skills to load |

---

## File Locations

### Lookup Priority (highest to lowest)

1. CLI flag: `--agent agent-name`
2. Project: `.claude/agents/{name}.md`
3. User: `~/.claude/agents/{name}.md`
4. Plugin: `agents/{name}.md` (at plugin root)
5. Built-in agents

### Invocation

```
Task tool with subagent_type: "agent-name"
```

---

## Critical Rules

- [ ] File is markdown with `.md` extension
- [ ] Frontmatter is valid YAML between `---` markers
- [ ] `name` field is present
- [ ] `description` field is present
- [ ] File is in valid location (see lookup priority)

## High Priority

- [ ] `model` is one of: `haiku`, `sonnet`, `opus`
- [ ] `tools` contains only valid tool names
- [ ] `skills` contains only existing skill names
- [ ] Name matches filename (without `.md`)

## Medium Priority

- [ ] Clear instructions in body
- [ ] Appropriate model for task complexity
- [ ] Tools are minimal (principle of least privilege)

## Low Priority

- [ ] Consistent formatting
- [ ] Example usage documented
- [ ] Related agents/skills referenced

---

## Valid Tools

Common tools that can be listed in `tools` array:

- `Read` - Read files
- `Write` - Write files
- `Edit` - Edit files
- `Glob` - Find files by pattern
- `Grep` - Search file contents
- `Bash` - Execute commands
- `Task` - Spawn sub-agents (note: sub-agents cannot spawn sub-agents)
- `WebFetch` - Fetch web content
- `WebSearch` - Search the web

---

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Missing frontmatter | Critical | Add `---` markers with YAML |
| Missing `name` | Critical | Add `name: agent-name` |
| Missing `description` | Critical | Add `description: ...` |
| Invalid `model` | High | Use `haiku`, `sonnet`, or `opus` |
| Invalid tool in `tools` | High | Use valid tool names |
| Wrong file location | High | Move to valid location |
| Name/filename mismatch | Medium | Align name with filename |

---

## Sub-Agent Constraints

**Important**: Sub-agents cannot spawn other sub-agents. If your workflow requires sequential agent invocation, use "Main Context Orchestration" pattern where the main Claude context orchestrates agents sequentially.
