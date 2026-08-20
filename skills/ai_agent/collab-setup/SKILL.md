---
install_source: official
install_method: download
skill_id: official_2jZQrLul
enabled_at: 1787232017684
version: 1.0.0
name_zh: 协作设置
---
---
name: collab-setup
description: Configure, verify, and troubleshoot OpenClaw multi-agent collaboration, agent delegation, collaboration groups, sync-group defaults, and channel routing. Use when the user wants to enable or fix multi-agent协作, 分工处理, 协作群同步, 默认同步群, visible coordination, or delegated workflows in OpenClaw. Especially relevant for Feishu today, but also for future Telegram, Discord, WhatsApp, WeChat, and other channel-based collaboration setups. Trigger on requests like: “帮我配置多 agent 协作”, “分工处理为什么不生效”, “帮我配置协作群”, “设置默认同步群”, “为什么群里不回复”, “让 planner / 学习伙伴 / 智能管家 分工”, or when the user needs capability-aware onboarding from single-agent to full visible multi-agent collaboration.
---

# OpenClaw Collaboration Setup

Use this skill to guide users from their current environment to the highest safe collaboration mode available.

## Core workflow

1. Detect current capability level before proposing changes.
2. Protect the current working config before risky edits.
3. Verify local runtime and config first.
4. Prefer local docs before external lookup.
5. Align recommendations with the user's current OpenClaw version and current channel behavior.
6. Prefer one-pass setup over repeated partial fixes.
7. Validate with a minimal live test after changes.
8. If health regresses, restore the last known-good config.

## Capability ladder

- Level 0: single-agent only
- Level 1: multi-agent internal delegation only
- Level 2: multi-agent with one visible collaboration group
- Level 3: multi-agent with multiple sync groups / default sync group set

Always execute with the highest safe level currently available.
If the environment is incomplete, degrade gracefully and explain the missing next step.

## Channel policy

Current strongest support is for Feishu.
When the user asks for another channel, keep the same orchestration principles, but verify the channel's current config semantics and official docs before prescribing exact routing fields.

## Read these references as needed

- For the first-response check path and when to execute vs ask vs guide: read `references/diagnostic-flow.md`.
- For short, reusable setup and repair wording patterns: read `references/conversation-templates.md`.
- For dispatch behavior, sync prompts, timeout handling, sync-group selection, nickname matching, and group-name matching: read `references/task-dispatch-sync-modes.md`.
- For Feishu group routing and stable top-level config structure: read `references/feishu-group-routing-spec.md`.
- For capability-aware onboarding and one-pass setup flow: read `references/multi-agent-onboarding-playbook.md`.
- For reusable setup patterns by maturity level: read `references/multi-agent-config-templates.md`.
- For the practical workspace-layer model and how to reason about agent/runtime vs business workspaces: read `references/workspace-model.md`.
- For risky config edits, backup expectations, and rollback safety: read `references/config-change-safety-checklist.md` and `references/config-backup-rollback-playbook.md`.
- For intent + capability level → action path routing: read `references/decision-table.md`.
- For pre-flight, post-change, and regression verification steps: read `references/checklist.md`.
- For channel-specific config differences and Feishu→other migration: read `references/multi-channel-differences.md`.

## Execution expectations

- Do not assume the user already has a collaboration group.
- Do not assume the user already has multiple agents.
- Do not assume the relevant channel plugin is already installed/configured.
- Do not assume Feishu is the active channel; detect whether the user is currently on webchat/TUI or another channel.
- Do not assume one version's config semantics apply to all OpenClaw versions.
- Do not stop at config edits; verify runtime behavior.
- Check main workspace, child workspaces, and any local two-workspace pattern before declaring setup complete.
- If the environment uses both an agent-side runtime workspace and a project/business workspace, verify both layers explicitly.
- Prefer human-readable group names and agent nicknames over raw IDs in user-facing guidance.

## Output style

When helping the user configure collaboration:
- summarize current state
- identify missing capability layer
- propose the smallest complete next configuration step
- run one minimal verification test
- record the working pattern into workspace docs when a stable fix is found

## Related skill

For context management during multi-agent collaboration (task cards, checkpoints, overload prevention, resume flows), see `context-flow`. That skill handles the "how to manage context during collaboration" layer; this skill handles the "how to configure and fix multi-agent collaboration" layer. They are independent and can be used separately.
