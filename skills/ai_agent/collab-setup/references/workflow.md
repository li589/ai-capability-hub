# Workflow

## Goal

Turn `collab-setup` into a practical setup and troubleshooting flow that:
- works independently from `context-flow`
- can still benefit from `context-flow` ideas when useful
- handles incomplete environments gracefully
- prioritizes one-pass verification over repeated partial fixes

## Operating principle

Do not start by proposing config changes.
Start by classifying the current environment.

## Step 0: Safety first

Before risky config changes:
- determine whether the current environment is partially or fully working
- create a rollback-ready backup of the active config
- prefer patching over wholesale regeneration
- preserve a clear last-known-good state

If a proposed change could break startup or routing:
- validate syntax before restart
- verify gateway health immediately after restart
- if health fails, restore the backup first

## Step 1: Detect current state

Check the smallest useful set first:
- OpenClaw version / runtime status
- gateway status
- current channel(s)
- configured agents/accounts
- existing collaboration groups / sync targets
- whether visible group sync is already possible

Classify into one of these levels:
- Level 0: single-agent only
- Level 1: multi-agent internal only
- Level 2: multi-agent + one visible collaboration group
- Level 3: multi-agent + multiple sync groups / default sync group set

## Step 2: Determine the user's actual goal

Map the request into one of these intents:
- enable multi-agent collaboration
- fix delegation that is not working
- fix visible group sync that is not working
- configure default sync group set
- route visible collaboration to a different group/channel
- bootstrap a fresh collaboration environment from scratch

## Step 3: Choose the highest safe execution mode

- If only Level 0 is available, degrade to single-agent execution and explain what is missing.
- If Level 1 is available, allow internal delegation and skip visible sync.
- If Level 2 is available, enable visible sync to the single collaboration group.
- If Level 3 is available, support default sync group set and one-off group overrides.

## Step 4: Use the right reference

Read the smallest relevant reference file:
- dispatch/sync behavior -> `task-dispatch-sync-modes.md`
- Feishu routing -> `feishu-group-routing-spec.md`
- onboarding logic -> `multi-agent-onboarding-playbook.md`
- template selection -> `multi-agent-config-templates.md`

## Step 5: Propose the smallest complete next step

Good proposals should:
- fix the next blocking layer completely
- avoid mixing unrelated refactors
- prefer stable top-level routing patterns over scattered per-account tweaks
- preserve existing working behavior

## Step 6: Verify live

Always run a minimal verification after changes:
- one direct-chat test if direct chat is relevant
- one delegation test if multi-agent routing is relevant
- one visible group test if collaboration-group sync is relevant
- one final outbound reply test, not just inbound routing

## Step 7: Record the stable result

When a stable fix is found:
- update the relevant local doc(s)
- prefer canonical docs over repeated chat explanation
- keep the skill independent; do not assume `context-flow` is required for this step

## Independent use guarantee

This skill must stay useful even when `context-flow` is not loaded.

That means:
- it must explain capability-aware delegation on its own
- it must explain visible sync decisions on its own
- it must explain timeout verification and final ownership on its own

## Optional synergy with context-flow

If `context-flow` is present or relevant, it can strengthen:
- stage summaries
- thin-state group updates
- long-task recovery
- context compaction

But those are optional enhancements, not hard dependencies.
