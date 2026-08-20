# Task Dispatch Sync Modes

Use this reference when the user asks about delegation behavior, visible sync, sync groups, timeout handling, or how natural-language collaboration requests should behave.

## Core distinction

- Internal dispatch starts work through internal delegation paths.
- Group sync posts visible coordination updates into user-facing groups.
- These are related but separate actions; one should not imply the other automatically.

## Capability-aware dispatch

When collaboration is requested, do not assume the environment is fully configured.
Instead:
- detect the current collaboration capability level
- execute with the highest safe capability available
- degrade gracefully if some layers are missing
- guide the user to the next configuration step only when needed

Examples:
- only one agent exists -> degrade to single-agent execution
- multiple agents, no group -> allow internal delegation, skip visible sync
- group exists but routing incomplete -> continue with safe internal execution and explain the missing group layer

## Default behavior

If a task starts in direct chat and the user does not mention group sync:
- default to internal dispatch only
- do not automatically broadcast to a collaboration group

This protects privacy, reduces noise, and avoids exposing unstable plans.

## Reporting chain

Default chain:
- human -> `main`
- `main` -> child agent
- child agent -> `main`
- `main` decides whether to sync visible group state
- `main` owns final external delivery by default

Rules:
- delegated agents report to `main` first
- delegated agents do not independently take over final user-facing delivery unless explicitly instructed
- visible sync is normally posted by `main`, not by every delegated agent

## Timeout handling

A delegated send timeout is not the same as execution failure.

When a dispatch path times out:
- mark the task as `已派发` or `处理中`
- do not immediately assume failure
- do not immediately re-dispatch if duplicate execution is possible
- verify target-side evidence first

Verification order:
- target session alive and recently updated
- target session already produced a result
- external side effect already exists
- only then decide whether to re-dispatch, degrade, or mark failure

Preferred external wording:
- `已完成，回执链路异常`
- `回执超时，执行结果待核验`
- `已派发，暂未收到回执`

## Sync group selection

When the user asks to sync to groups:
- 0 groups available -> continue with internal dispatch and clearly say sync was skipped
- 1 group available -> use it automatically
- multiple groups and no default sync group set -> ask once, with human-readable group names
- default sync group set configured -> use the full default set automatically
- explicit per-task group targets override the default for that task only

The default sync group set may contain zero, one, or multiple groups.

## Group choice display

When asking the user to choose:
- show group nickname first
- include a short purpose label when available
- include raw IDs only as auxiliary identifiers
- let the user reply with a simple number

Prefer formats like:
- `1. AI工作室💡（默认同步群）[oc_xxxx...]`
- `2. 运营协作群 [oc_yyyy...]`
- `3. 产品讨论组 [oc_zzzz...]`

If names collide, disambiguate with role or short ID suffix.

## Post-completion sync prompt

After a delegated task finishes, the system may offer a lightweight follow-up sync choice instead of requiring the user to restate the whole instruction.

Direct-chat completion example:
- `如果要把这次结果同步到群里，直接回复：`
- `1. 同步到默认同步群`
- `2. 选择其他群`
- `3. 不同步`

Group-originated completion example:
- `当前群已收到结果，是否同步到其他群？`
- `1. 同步到默认同步群（不含当前群）`
- `2. 选择其他群`
- `3. 不同步`

Treat the current group as already covered; do not re-sync to the same group by default.

## Group name resolution

Do not rely only on exact raw group names.

Preferred resolution order:
- exact full group-name match
- match after removing emoji and decorative symbols
- common alias or shorthand match
- partial keyword match when still unambiguous
- ask once if ambiguity remains

Tolerate differences such as emoji presence, decorative punctuation, spacing, and full-width vs half-width symbol differences.

## Dispatch triggering

Dispatch should not depend only on exact keywords.

Strong explicit signals include phrases like:
- `分工处理`
- `同步到群`
- `派给 planner`
- `让学习伙伴去做`
- `这个任务拆开做`

Dispatch should also trigger semantically when the user clearly asks for:
- multiple roles
- task splitting
- coordination between agents
- one agent planning and another executing
- visible shared progress

Do not dispatch automatically when the task is simple and `main` can reasonably handle it directly.

## Agent name resolution

Do not rely only on internal agent IDs.

Preferred resolution order:
- internal `agentId`
- exact nickname match
- nickname match after removing emoji/symbols
- known alias match
- partial nickname match when still unambiguous
- ask once if ambiguity remains

Users should be able to use natural role names such as:
- `planner`
- `最强大脑`
- `最强大脑 🧠`
- `学习伙伴`
- `学习伙伴 📖`
- `智能管家`
- `智能管家 🤖`
