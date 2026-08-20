# Conversation Templates

## Purpose

Provide short, reusable question and response templates for onboarding, repair, and capability-guided collaboration setup.

Use these templates to keep replies compact, reduce ambiguity, and avoid over-questioning.

## Template 1: Fresh single-agent user

Use when:
- only `main` exists
- no visible collaboration group exists
- the user asks for collaboration or `分工处理`

Reply pattern:
- `我先按单 agent 模式把当前任务做掉。`
- `你现在还没启用多 agent 协作。`
- `飞书用户可以通过官方快速入口一键创建机器人并自动配好权限：`
  `https://open.feishu.cn/page/openclaw?form=multiAgent`
- `如果你愿意，我下一步可以继续帮你补：1. 子 agent 2. 协作群 3. 两者都补`

## Template 2: Multiple agents, no visible sync yet

Use when:
- internal delegation is possible
- visible sync is not ready

Reply pattern:
- `这次我先按内部协作处理。`
- `你当前已具备内部派发能力，但还没有可见协作群同步。`
- `如果你愿意，我下一步可以继续帮你补协作群和群路由。`

## Template 3: Channel/plugin missing

Use when:
- the user wants a specific channel workflow
- but the relevant plugin or channel config is not present

Reply pattern:
- `你当前还没把 <channel> 这条链路装好。`
- `这次我先按当前可用通道处理。`
- `如果你愿意，我下一步可以继续帮你补 <channel> 插件、账号配置和最小验证。`

## Template 4: Group exists, but routing is not ready

Use when:
- target group exists
- routing or membership is incomplete

Reply pattern:
- `协作群已经有了，但群路由还没完全打通。`
- `这次我先按内部协作处理，避免任务卡住。`
- `如果你愿意，我下一步直接补群路由并做一条真实收发验证。`

## Template 5: Need one focused choice

Use when:
- one critical selector is missing
- guessing would be risky

Reply pattern:
- `现在只差一个关键选择。`
- `你直接回编号就行：`
- `1. <选项A>`
- `2. <选项B>`
- `3. <选项C>`

## Template 6: Multiple groups, choose one or more

Use when:
- several groups are available
- no usable default sync group set exists

Reply pattern:
- `你现在有多个可用同步群。`
- `直接回复编号即可：`
- `1. 群A`
- `2. 群B`
- `3. 群C`
- `也可以直接说：同步到 1 和 3`

## Template 7: Degraded but working

Use when:
- the full requested capability is not available
- safe degraded execution is available

Reply pattern:
- `这次我先按当前可用的最高层能力处理。`
- `现在能做的是：<当前能力>`
- `还没完全具备的是：<更高层能力>`
- `如果你愿意，我可以继续帮你补齐。`

## Template 8: Repair succeeded

Use when:
- the requested fix now works

Reply pattern:
- `现在已经通了。`
- `这次真正修好的点是：<核心原因/修复点>`
- `如果你愿意，我可以顺手把这条稳定模式沉淀进文档/skill。`

## Template 9: Repaired by rollback

Use when:
- a risky change regressed health
- rollback restored service

Reply pattern:
- `我已经先把系统恢复到上一个可用状态。`
- `当前服务是健康的。`
- `刚才的问题更像是：<最可能原因>`
- `下一步我建议用更小的补丁重新试。`

## Template 10: Direct-chat completion follow-up

Use when:
- task started in direct chat
- user did not explicitly request sync earlier

Reply pattern:
- `如果要把这次结果同步到群里，直接回复：`
- `1. 同步到默认同步群`
- `2. 选择其他群`
- `3. 不同步`

## Template 11: Group-originated completion follow-up

Use when:
- task started in a group
- current group already received the final result
- user did not explicitly request sync to other groups

Reply pattern:
- `当前群已收到结果，是否同步到其他群？`
- `1. 同步到默认同步群（不含当前群）`
- `2. 选择其他群`
- `3. 不同步`

## Template 12: Workspace-model clarification

Use when:
- the user is confused about workspace paths and roles

Reply pattern:
- `先按层理解，不按目录名猜。`
- `agents/<agent> = 运行实例层`
- `workspace = 主控主工作区`
- `workspaces/<agent> = 子 agent 正式工作区`
- `像 workspace-main 这种目录，要先判断是不是历史兼容层。`

## Template 13: Feishu session commands

Use when:
- the user asks how to reset or start a new conversation in Feishu
- the user's session context is confused or stuck
- onboarding a new Feishu user

Reply pattern:
- `在飞书对话框里直接输入命令就行，不需要额外配置：`
- `/reset — 重置当前会话，清掉上下文从头来`
- `/new — 开一个全新会话，适合切换话题`
- `两个命令发出去后 agent 不会收到这条消息，OpenClaw 会直接处理。`
- `如果配了记忆插件，重置前会自动做一次记忆落盘。`
