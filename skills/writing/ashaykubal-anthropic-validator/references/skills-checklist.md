# Skills Validation Checklist (Fallback)

This checklist is used when dynamic documentation fetch fails. May be outdated - prefer fetched standards.

**Last Updated**: 2026-01-17

---

## Frontmatter Requirements

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill name, must match directory name |
| `description` | string | Concise explanation of skill purpose |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `user-invocable` | boolean | `true` to show in `/` menu, `false` to hide |
| `agent` | string | Model selection: `haiku`, `sonnet`, `opus` |
| `context` | string | `fork` for isolated execution |
| `skills` | array | Skills to load when this skill runs |
| `tools` | array | Tools allowed for this skill |
| `hooks` | object | Skill-scoped hooks |

---

## File Structure

### Required

- `SKILL.md` in `skills/{skill-name}/` directory
- Name in frontmatter matches directory name

### Optional

- `references/` subdirectory for supporting files
- Additional markdown files for sections

---

## Content Guidelines

### Critical Rules

- [ ] Frontmatter is valid YAML between `---` markers
- [ ] `name` field matches directory name exactly
- [ ] `description` field is present and non-empty
- [ ] SKILL.md is under 500 lines (recommended)

### High Priority

- [ ] `user-invocable` is boolean if present
- [ ] `agent` is one of: `haiku`, `sonnet`, `opus` if present
- [ ] `context` is `fork` if present (no other values)
- [ ] `skills` is array of strings if present
- [ ] `tools` is array of valid tool names if present

### Medium Priority

- [ ] Description explains when to use the skill
- [ ] Clear section structure with headers
- [ ] Examples provided where appropriate

### Low Priority

- [ ] Consistent formatting
- [ ] No dead links in references
- [ ] Related skills section included

---

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Missing `name` | Critical | Add `name: skill-name` to frontmatter |
| Missing `description` | Critical | Add `description: ...` to frontmatter |
| Name mismatch | Critical | Ensure name matches directory |
| Invalid `agent` value | High | Use `haiku`, `sonnet`, or `opus` |
| Non-boolean `user-invocable` | High | Use `true` or `false` |
| Missing frontmatter | Critical | Add `---` markers with YAML |
