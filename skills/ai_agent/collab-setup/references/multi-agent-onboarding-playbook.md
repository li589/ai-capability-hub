# Multi-Agent Onboarding Playbook

Use this reference when the user wants to enable or repair multi-agent collaboration and you need a safe, capability-aware onboarding flow.

## Core principle

Do not assume the environment is already complete.
Instead:
1. detect the current capability level
2. execute with the highest safe capability currently available
3. guide the user to the next configuration milestone only when needed
4. prefer one-pass setup over repeated partial fixes
5. protect the current working config before risky changes

## Capability levels

### Level 0: Single-agent only
- one active bot/account
- no extra agents configured
- no collaboration group configured

Behavior:
- still accept `分工处理`
- degrade to single-agent execution
- explain that visible multi-agent collaboration is not enabled yet
- offer guided setup for extra agents and optional collaboration groups

Quick-start for Feishu:
- 飞书官方提供了 OpenClaw 多 agent 快速创建入口，可一键创建机器人并自动配好所需权限：
  `https://open.feishu.cn/page/openclaw?form=multiAgent`
- 引导用户先通过此链接创建所需的飞书机器人应用，再回来继续配置 agent binding 和协作群

### Level 1: Multiple agents, no collaboration group
- `main` plus one or more additional agents exist
- internal delegation is possible
- no visible sync target is configured

Behavior:
- allow internal delegation
- skip group sync by default
- offer group setup only if visible coordination is needed

### Level 2: Multiple agents with one collaboration group
- internal delegation works
- one collaboration group is configured and routable

Behavior:
- `同步到群` can use the single group automatically
- final replies in that group should not be duplicated as extra sync into the same group

### Level 3: Multiple agents with multiple sync groups
- internal delegation works
- one or more sync groups exist
- a default sync group set may or may not be configured

Behavior:
- support default sync group set
- support one-off multi-group sync
- show human-readable group names when selection is needed

## Version-aware setup flow

Before guiding setup, verify:
- current OpenClaw version/build
- enabled channels
- configured agents/accounts
- available collaboration groups
- current OS and host type
- whether the gateway is healthy

Suggested order:
1. local status/version checks
2. inspect current config and actual runtime state
3. consult local docs first
4. if version-specific behavior is unclear, align with official docs/source for that version line
5. only then generate setup guidance

## One-pass onboarding sequence

### Phase 0: Safety backup and rollback readiness
- detect whether the current setup is already working in any important way
- back up the current config before editing
- prefer reversible changes over destructive replacement
- keep a clear rollback path if gateway health degrades

Minimum safety actions:
- save a timestamped backup
- avoid removing working fields unless necessary
- verify edited config syntactically before restart
- restart only after the new config passes validation
- if restart or health checks fail, restore the last known-good config

### Phase 1: Baseline verification
Verify:
- OpenClaw CLI works
- gateway is running
- target channel is connected
- workspace is writable
- at least one model/provider is usable

### Phase 2: Agent capability verification
Verify:
- `main` exists and is routable
- extra agents such as `planner` / `moltbook` exist if requested
- each agent has a valid workspace
- intended agent names, nicknames, and identities are consistent

### Phase 3: Collaboration-group verification
If visible coordination is wanted, verify:
- a suitable group exists
- relevant bot(s) are already in the group
- current channel routing allows that group
- default sync group set is configured if appropriate

### Phase 4: Dry-run verification
Run the smallest safe test:
- one internal delegation test
- one visible group sync test if enabled
- one final result handoff test

### Phase 5: Stabilization
After tests pass:
- record the working routing pattern
- save collaboration conventions
- point future changes to stable docs instead of ad-hoc chat explanation

## Feishu-specific guidance

Before declaring Feishu collaboration healthy, verify:
- bot app is connected and published correctly (快速创建入口: `https://open.feishu.cn/page/openclaw?form=multiAgent`)
- gateway is healthy
- `main` can receive and reply in direct chat
- target collaboration group is reachable
- bot is in the target group
- top-level Feishu group routing is configured for `main`
- non-main agents are intentionally allowed or intentionally blocked from groups
- final group reply path is tested, not just inbound routing

Recommended stable pattern:
- keep `main` group behavior at top-level `channels.feishu`
- avoid duplicating the same behavior under `accounts.main`
- treat `planner` and `moltbook` as group-disabled unless visible multi-bot behavior is explicitly required

## Guidance behavior

When setup is incomplete:
- do not hard-fail if a safe degraded path exists
- explain what was done now
- explain what is still missing
- offer the next concrete setup step in one compact block

Preferred style:
- `这次我先按内部协作处理。`
- `当前还缺少可见协作所需的群配置。`
- `如果你愿意，我下一步可以继续帮你补齐。`
