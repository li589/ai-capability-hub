# collab-setup

Configure, verify, and troubleshoot OpenClaw multi-agent collaboration.

## What it does

This skill guides you from your current environment to the highest safe collaboration mode available. It handles:

- **Capability detection**: automatically identifies your collaboration level (single-agent → multi-agent → visible group sync → multi-group)
- **Diagnostic routing**: maps your problem to the right fix path via decision tables
- **Multi-channel support**: Feishu (mature), Telegram, Discord, Slack, WhatsApp, Signal (framework-level)
- **Safety-first config changes**: backup before edit, validate syntax, verify after restart, rollback if broken

## When to use

- `帮我配置多 agent 协作`
- `分工处理为什么不生效`
- `帮我配置协作群` / `设置默认同步群`
- `为什么群里不回复`
- `configure multi-agent collaboration`
- `fix group routing`

## Capability levels

| Level | Description |
|---|---|
| 0 | Single-agent only |
| 1 | Multi-agent internal delegation |
| 2 | Multi-agent + one visible collaboration group |
| 3 | Multi-agent + multiple sync groups / default sync group |

## File structure

```
collab-setup/
├── SKILL.md                          # Main skill entry point
├── _meta.json                        # Skill metadata
├── README.md                         # This file
└── references/
    ├── decision-table.md             # Intent × Level → action routing
    ├── checklist.md                  # Pre-flight / post-change / regression checks
    ├── diagnostic-flow.md            # First-response diagnostic flow
    ├── workflow.md                   # Core workflow steps
    ├── conversation-templates.md     # Reusable wording patterns
    ├── output-templates.md           # Output format templates
    ├── task-dispatch-sync-modes.md   # Dispatch / sync / timeout rules
    ├── feishu-group-routing-spec.md  # Feishu stable routing pattern
    ├── multi-agent-onboarding-playbook.md  # Capability-aware onboarding
    ├── multi-agent-config-templates.md     # Reusable config patterns
    ├── multi-channel-differences.md  # Channel-specific config differences
    ├── workspace-model.md            # Workspace layer model
    ├── config-change-safety-checklist.md   # Safety before risky edits
    └── config-backup-rollback-playbook.md  # Backup and rollback
```

## Install

Copy the entire `collab-setup/` folder to `~/.openclaw/skills/`:

```bash
cp -r collab-setup ~/.openclaw/skills/
```

No additional dependencies required.

## Requirements

- OpenClaw 2026.3.x or later
- At least one configured channel (Feishu recommended for full feature support)

## License

MIT
