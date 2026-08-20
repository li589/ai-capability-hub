# Multi-Agent Config Templates

Use this reference to choose the right collaboration template based on the user's current maturity level.

## Template 1: Single-Agent Minimal

Use when:
- only one agent is needed
- no collaboration group exists
- the user wants a stable baseline that can grow later

Key behavior:
- `main` handles everything
- no visible collaboration-group sync
- `分工处理` degrades to single-agent execution

## Template 2: Multi-Agent, Internal Only

Use when:
- multiple agents exist
- internal delegation is wanted
- no visible collaboration group is configured yet

Key behavior:
- `main` can delegate internally
- no visible sync is assumed
- `分工处理` works only inside the agent system

## Template 3: Multi-Agent + One Collaboration Group

Use when:
- visible coordination is needed in one Feishu group
- `main` should reply in that group without `@`
- other agents should remain group-silent by default

Key behavior:
- top-level Feishu group config controls `main`
- `planner` and `moltbook` remain group-disabled unless explicitly enabled
- `同步到群` can use the single collaboration group automatically

## Template 4: Multi-Agent + Default Sync Group Set

Use when:
- multiple groups exist
- some tasks should sync to one or more default target groups
- group choice should be human-friendly and overridable per task

Key behavior:
- maintain a logical default sync group set in workflow rules
- explicit per-task targeting overrides the default for that task only
- current-group deduplication still applies when tasks start in a group

## Safe setup sequence

Regardless of template:
1. verify OpenClaw/gateway/channel health first
2. verify `main` direct-chat round trip
3. verify extra agents and workspaces
4. verify collaboration group membership and routing
5. run one small delegation test
6. run one small visible sync test if enabled
7. write the working pattern into docs

## Anti-patterns

Avoid:
- mixing `main` group behavior between top-level channel config and `accounts.main`
- assuming group sync exists just because multiple agents exist
- assuming timeout means failure
- making users select groups by raw IDs only
- requiring users to remember internal agent IDs instead of nicknames
- declaring setup complete before testing both inbound and final outbound reply behavior

## Template 5: Dedicated Reflection Agent

Use when:
- memory-reflection (triggered by `/reset` or `/new`) is too slow or times out on the main agent's model
- reflection timeouts cause gateway disconnection or message loss
- you want to isolate background plugin workload from the main conversation model

Setup:
1. Add a lightweight agent to `agents.list`:

```jsonc
{
  "id": "reflector",
  "name": "记忆回顾",
  "workspace": "~/.openclaw/workspace",
  "agentDir": "~/.openclaw/agents/reflector",
  "model": {
    "primary": "minimax/MiniMax-M2.7",
    "fallbacks": ["google/gemini-3-flash-preview"]
  },
  "tools": { "profile": "minimal" }
}
```

2. Set `memoryReflection.agentId` in the memory plugin config:

```jsonc
"memoryReflection": {
  "storeToLanceDB": true,
  "injectMode": "inheritance+derived",
  "messageCount": 80,
  "thinkLevel": "low",
  "agentId": "reflector",
  "timeoutMs": 60000,
  "maxInputChars": 100000
}
```

Key behavior:
- all agents' `/reset` and `/new` reflection runs use the reflector agent
- does not affect the main conversation model or thinking level
- prevents heavy models (e.g. opus) from being used for background tasks
- recommended parameter tuning: match `messageCount`, `maxInputChars`, and `timeoutMs` to the reflector model's speed and context window

Note:
- the reflector agent does not need channel bindings or group config
- it does not appear in any chat; it only runs background reflection tasks
- `mkdir -p ~/.openclaw/agents/reflector` is needed before first use
