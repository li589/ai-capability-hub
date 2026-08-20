# Commands Validation Checklist (Fallback)

This checklist is used when dynamic documentation fetch fails. May be outdated - prefer fetched standards.

**Last Updated**: 2026-01-17

---

## Commands and Skills Merge

As of Claude Code v2.1.3 (January 2026), **commands and skills are merged**. Skills can be invoked as commands:

```bash
/skill-name arg1 arg2
```

---

## Invocation Patterns

### Basic Invocation

```bash
/my-skill                    # No arguments
/my-skill path/to/file       # Single argument
/my-skill arg1 arg2 arg3     # Multiple arguments
```

### Argument Access

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments as single string |
| `$1`, `$2`, etc. | Positional arguments |
| `${ENV_VAR}` | Environment variable |

---

## Visibility Control

### user-invocable Field

| Value | Effect |
|-------|--------|
| `true` | Skill appears in `/` menu |
| `false` | Skill hidden from `/` menu |
| (omitted) | Defaults to `true` |

### When to Hide

Set `user-invocable: false` for:
- Internal/helper skills
- Skills only meant for other skills to load
- Pipeline-stage skills

---

## Critical Rules

- [ ] Skill exists at `skills/{name}/SKILL.md`
- [ ] Frontmatter is valid YAML
- [ ] Name is valid (alphanumeric, hyphens)

## High Priority

- [ ] `user-invocable` is boolean if present
- [ ] Arguments handled correctly in skill body
- [ ] Clear usage documentation in skill

## Medium Priority

- [ ] Default behavior when no arguments provided
- [ ] Error handling for invalid arguments
- [ ] Examples show argument usage

## Low Priority

- [ ] Consistent argument naming
- [ ] Help text for complex arguments

---

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Invalid skill name | High | Use alphanumeric and hyphens only |
| Missing SKILL.md | Critical | Create skill file |
| Invalid frontmatter | Critical | Fix YAML syntax |
| Undocumented arguments | Medium | Add usage examples |

---

## Migration from Legacy Commands

If migrating from separate `commands/` directory:

1. Create skill at `skills/{command-name}/SKILL.md`
2. Move command logic to skill body
3. Set `user-invocable: true`
4. Update any references to use `/skill-name` pattern
5. Remove old command file
