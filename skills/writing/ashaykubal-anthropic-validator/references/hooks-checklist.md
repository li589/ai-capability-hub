# Hooks Validation Checklist (Fallback)

This checklist is used when dynamic documentation fetch fails. May be outdated - prefer fetched standards.

**Last Updated**: 2026-01-17

---

## Hook Types

| Type | Trigger | Use Case |
|------|---------|----------|
| `PreToolUse` | Before tool execution | Validation, blocking |
| `PostToolUse` | After tool execution | Logging, side effects |
| `SubagentStart` | When subagent spawns | Tracking, setup |
| `SubagentStop` | When subagent completes | Finalization, cleanup |
| `Notification` | System notifications | Alerts, logging |

---

## Configuration Format

### settings.json Structure (Project Hooks)

**Events WITH matcher support** (PreToolUse, PostToolUse, PermissionRequest):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "script.sh", "timeout": 5000 }
        ]
      }
    ]
  }
}
```

**Events WITHOUT matcher support** (SubagentStart, SubagentStop, Stop, UserPromptSubmit):
```json
{
  "hooks": {
    "SubagentStart": [
      {
        "hooks": [
          { "type": "command", "command": "script.sh", "timeout": 5000 }
        ]
      }
    ]
  }
}
```

**Note**: The `hooks` array wrapper is REQUIRED for all event types, even without a matcher.

### Field Requirements

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `matcher` | **Only for PreToolUse/PostToolUse** | string | Regex pattern for matching |
| `hooks` | Yes | array | Array of hook definitions |
| `type` | Yes | string | `command` or `prompt` |
| `command` | Yes (if type=command) | string | Shell command to execute |
| `timeout` | No | number | Timeout in milliseconds |
| `once` | No | boolean | Run only once per session |

### Matcher Support by Event Type

| Event | Supports Matcher? |
|-------|-------------------|
| PreToolUse | Yes |
| PostToolUse | Yes |
| PermissionRequest | Yes |
| SubagentStart | **No** |
| SubagentStop | **No** |
| Stop | **No** |
| UserPromptSubmit | **No** |

---

## Environment Variables

### PreToolUse / PostToolUse

| Variable | Description |
|----------|-------------|
| `$CLAUDE_TOOL_NAME` | Name of the tool |
| `$CLAUDE_TOOL_INPUT` | JSON input to tool |
| `$CLAUDE_TOOL_OUTPUT` | JSON output (PostToolUse only) |

### SubagentStart / SubagentStop

| Variable | Description |
|----------|-------------|
| `$CLAUDE_SUBAGENT_TYPE` | Type/name of subagent |
| `$CLAUDE_SUBAGENT_PROMPT` | Prompt given to subagent (Start only) |

### Plugin Hooks

| Variable | Description |
|----------|-------------|
| `$CLAUDE_PLUGIN_ROOT` | Plugin root directory |
| `$CLAUDE_PROJECT_DIR` | Project directory |

---

## Critical Rules

- [ ] Event type is valid (PreToolUse, PostToolUse, SubagentStart, etc.)
- [ ] `hooks` array wrapper is present (required for ALL event types)
- [ ] Each hook has `type` field (`command` or `prompt`)
- [ ] Each hook has `command` field (if type=command)
- [ ] JSON syntax is valid
- [ ] For PreToolUse/PostToolUse: `matcher` is valid regex pattern
- [ ] For SubagentStart/SubagentStop: NO `matcher` field (not supported)

## High Priority

- [ ] `once: true` used appropriately (SessionStart scenarios)
- [ ] `timeout` specified (recommended 5000ms for scripts)
- [ ] Script paths are correct (use `$CLAUDE_PROJECT_DIR` or `$CLAUDE_PLUGIN_ROOT`)
- [ ] Exit codes used correctly (0=success, 1=warning, 2=block)

## Medium Priority

- [ ] Matcher patterns are specific (not overly broad)
- [ ] Commands are efficient (avoid long-running)
- [ ] Error handling in scripts

## Low Priority

- [ ] Comments/documentation for complex hooks
- [ ] Consistent naming conventions

---

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Invalid event type | Critical | Use valid event from list |
| Invalid JSON | Critical | Fix JSON syntax |
| Missing `hooks` array wrapper | Critical | Wrap hook definitions in `"hooks": [...]` |
| Missing `type` in hook | Critical | Add `"type": "command"` |
| Missing `command` in hook | Critical | Add `"command": "script.sh"` |
| `matcher` on non-matcher event | High | Remove `matcher` from SubagentStart/SubagentStop/Stop |
| Script not found | High | Check path, use env variables |
| No `once: true` for SessionStart | Medium | Add if hook should run once |
| No `timeout` specified | Low | Add `"timeout": 5000` for predictable behavior |
