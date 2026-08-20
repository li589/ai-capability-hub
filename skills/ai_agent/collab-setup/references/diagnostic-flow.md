# Diagnostic Flow

## Purpose

Provide a repeatable first-response flow for collaboration setup, repair, and onboarding requests.

Use this when the user says things like:
- `帮我配置多 agent 协作`
- `分工处理为什么不生效`
- `帮我配置协作群`
- `为什么群里不回复`
- `帮我检查当前能不能分工处理`

## Default strategy

Do not start by asking broad open-ended questions.
Do not start by editing config blindly.

Start by determining:
1. what the user wants to achieve
2. what capability level exists now
3. what the next blocking layer is
4. whether it is safer to execute now, guide now, or ask one focused question

## Step 1: Classify the request

Map the request into one primary class:

### A. Fresh setup
Examples:
- `帮我配置多 agent 协作`
- `帮我从头弄好多机器人协作`
- `帮我配置协作群`

Primary goal:
- build missing collaboration capability from current state

### B. Repair / troubleshooting
Examples:
- `分工处理为什么不生效`
- `为什么群里不回复`
- `为什么同步到群失败`

Primary goal:
- recover a previously expected behavior

### C. Workflow policy / behavior design
Examples:
- `默认同步到哪个群更合理`
- `分工处理默认要不要发群`
- `超时后应该怎么处理`

Primary goal:
- refine collaboration behavior rules

### D. Mixed request
Examples:
- user wants both configuration and workflow-policy design

Primary goal:
- resolve the blocking runtime/config layer first
- then refine policy

## Step 2: Inspect current environment

Minimum inspection set:
- OpenClaw version or status signal
- gateway health
- current channel(s)
- whether the relevant channel plugin is installed/configured at all
- whether the user is currently operating only through TUI/webchat/backend surfaces
- whether `main` works in direct chat
- whether extra agents exist
- whether a collaboration group exists
- whether the target bot is in that group
- whether visible sync is already working
- whether each agent has both workspace layers when the local pattern expects them:
  - an agent-side runtime workspace (often under agent/agents folders)
  - a project/business workspace (the normal working project path)
- whether those workspace layers are present and consistent across agents
- whether background plugins (memory-reflection, self-improvement) are healthy:
  - check for repeated timeout or abort errors in logs
  - check whether plugin timeouts have caused gateway disconnection or message loss
  - verify plugin model and timeout configuration are appropriate (e.g. a dedicated lightweight agent for reflection)

## Step 3: Determine capability level

Use these levels:
- Level 0: single-agent only
- Level 1: multi-agent internal only
- Level 2: multi-agent + one visible collaboration group
- Level 3: multi-agent + multiple sync groups / default sync group set

## Step 4: Decide interaction mode

### Execute immediately

Do this when:
- the user asked for a fix
- the missing step is obvious
- the change is low-risk or rollback-safe
- the intended target is unambiguous

Examples:
- repairing one known Feishu routing bug
- adding one known group to allowlist
- restoring a broken config from last-known-good backup

### Ask one focused question

Do this when one key selector is missing and guessing would be risky.

Examples:
- multiple candidate groups and no default sync group set
- multiple agents could match a nickname
- the user wants visible sync but has several possible group targets

Question style should be short and selectable.

### Guide first, then offer execution

Do this when:
- the environment is too incomplete for the requested capability
- risky setup is required and current value is uncertain
- the user appears to be starting from scratch

Examples:
- only one agent exists but the user asks for true multi-agent collaboration
- no collaboration group exists but the user asks for visible group sync

## Step 5: Choose the next action by capability gap

### If Level 0 and user wants collaboration

Do:
- degrade to single-agent execution for the current task if possible
- explain that multi-agent collaboration is not yet enabled
- offer next setup milestone: extra agents and optional group setup

### If Level 1 and user wants visible sync

Do:
- allow internal delegation if possible
- explain that visible sync is not configured yet
- offer next setup milestone: collaboration group creation / routing

### If Level 2 and user wants multi-group sync

Do:
- use current visible sync if only one group is needed
- explain that multiple sync groups/default sync group set are the next layer

### If Level 3 and behavior is still unsatisfactory

Do:
- inspect workflow policy, naming resolution, and sync behavior rules
- treat this as orchestration refinement, not basic setup

## Step 6: Apply safety rules

Before risky config edits:
- read `config-change-safety-checklist.md`
- read `config-backup-rollback-playbook.md`
- back up first
- patch minimally
- validate and verify after restart

## Step 7: Verify the exact user-critical path

Do not stop after generic health checks.
Verify the exact behavior the user cares about.

Examples:
- `main` replies in target Feishu group without `@`
- delegated agent finishes and `main` properly收口
- sync to selected group(s) works
- current-group deduplication works

## Step 8: End with one of three outcomes

### Outcome A: Working now
- state clearly what now works
- mention any remaining optional improvements

### Outcome B: Working in degraded mode
- state clearly what works now
- state which higher layer is still missing
- offer the next configuration step

### Outcome C: Blocked pending one user choice
- state the exact selector needed
- ask one short question with choices

## Anti-patterns

Avoid:
- asking many vague setup questions before checking runtime state
- jumping into full config rewrites before classifying capability level
- mixing runtime repair with large design refactors in one risky step
- telling the user to memorize raw IDs when readable names are available
