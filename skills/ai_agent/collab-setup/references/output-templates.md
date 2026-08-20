# Output Templates

## Purpose

Provide short, stable response patterns for the most common collaboration setup states.

Use these to keep setup guidance compact, predictable, and easy to act on.

## Template A: Single-agent new user

Use when:
- only `main` exists
- no extra agents are configured
- no collaboration group exists

Pattern:
- `当前状态：你现在还是单 agent 模式。`
- `已可用：main 可直接处理当前任务。`
- `还缺：多 agent 角色和协作群。`
- `下一步：我可以先帮你补 agent，再决定是否配置协作群。`

## Template B: Multiple agents, no collaboration group

Use when:
- internal delegation is possible
- visible sync is not configured

Pattern:
- `当前状态：你已具备内部协作能力。`
- `已可用：可以内部派发并由 main 统一收口。`
- `还缺：可见协作群同步。`
- `下一步：如果你愿意，我可以继续帮你补协作群和路由。`

## Template C: Group exists, bot/group routing incomplete

Use when:
- a target group exists
- visible sync should work but routing or membership is incomplete

Pattern:
- `当前状态：协作群已存在，但群路由还没完全打通。`
- `已可用：当前可先按内部协作处理。`
- `还缺：机器人入群、群路由或最终回发链路。`
- `下一步：我先补齐最小缺口，再做一条真实收发验证。`

## Template D: Group inbound works, final outbound is broken

Use when:
- inbound group routing works
- final outbound reply is the failing layer

Pattern:
- `当前状态：群消息已进入主链路，但最终回发还不稳定。`
- `已可用：入站、执行、reply 生成已正常。`
- `还缺：最终发送链路验证或修复。`
- `下一步：我先只盯 final outbound，不再混查其他层。`

## Template E: Multiple groups, user has not chosen one

Use when:
- multiple groups exist
- no default sync group set is configured
- a group target is required

Pattern:
- `当前状态：你有多个可用同步群。`
- `还缺：本次任务的目标群选择。`
- `直接回复编号即可：`
- `1. 群A`
- `2. 群B`
- `3. 群C`

## Template F: Degraded but working

Use when:
- full requested capability is not available
- safe degraded execution is available

Pattern:
- `这次我先按可用的最高层能力处理。`
- `当前已可用：<当前层能力>`
- `暂未具备：<更高层能力>`
- `如果你愿意，我下一步可以继续帮你补齐。`

## Template G: Group-originated completion follow-up

Use when:
- task started in a group
- final reply has already been delivered in the current group
- user did not explicitly request sync to other groups

Pattern:
- `当前群已收到结果，是否同步到其他群？`
- `1. 同步到默认同步群（不含当前群）`
- `2. 选择其他群`
- `3. 不同步`

## Template H: Direct-chat completion follow-up

Use when:
- task started in direct chat
- user did not explicitly request sync earlier

Pattern:
- `如果要把这次结果同步到群里，直接回复：`
- `1. 同步到默认同步群`
- `2. 选择其他群`
- `3. 不同步`
