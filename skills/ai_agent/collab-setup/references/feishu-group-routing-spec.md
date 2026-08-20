# Feishu Group Routing Spec

Use this reference when configuring or troubleshooting visible multi-agent coordination on Feishu.

## Stable pattern

Goal:
- `main` can reply in the collaboration group without `@`
- `planner` and `moltbook` do not receive group messages unless explicitly enabled
- group behavior is configured in one place only

## Core rules

- control `main` group behavior at top-level `channels.feishu`
- keep non-main agents group-disabled by default unless visible multi-bot behavior is explicitly required
- do not duplicate group behavior keys under `channels.feishu.accounts.main`
- after routing changes, restart the gateway and verify live behavior

## Canonical structure

```jsonc
{
  "channels": {
    "feishu": {
      "enabled": true,
      "defaultAccount": "main",
      "defaultAgent": "main",
      "dmPolicy": "pairing",
      "connectionMode": "websocket",

      "groupPolicy": "allowlist",
      "groupAllowFrom": ["oc_COLLAB_GROUP"],
      "groups": {
        "oc_COLLAB_GROUP": {
          "enabled": true,
          "requireMention": false
        }
      },

      "accounts": {
        "main": {
          "appId": "cli_main",
          "appSecret": "xxx",
          "agentId": "main",
          "workspace": "/Users/USER/.openclaw/workspace",
          "streamResponse": true
        },
        "planner": {
          "appId": "cli_planner",
          "appSecret": "xxx",
          "agentId": "planner",
          "workspace": "/Users/USER/.openclaw/workspaces/feishu-planner",
          "streamResponse": true,
          "groupPolicy": "allowlist",
          "groupAllowFrom": []
        },
        "moltbook": {
          "appId": "cli_moltbook",
          "appSecret": "xxx",
          "agentId": "moltbook",
          "workspace": "/Users/USER/.openclaw/workspaces/feishu-moltbook",
          "streamResponse": true,
          "groupPolicy": "allowlist",
          "groupAllowFrom": []
        }
      }
    }
  }
}
```

## Main-agent routing

Use top-level Feishu keys for `main`:
- `channels.feishu.defaultAccount = "main"`
- `channels.feishu.groupPolicy`
- `channels.feishu.groupAllowFrom`
- `channels.feishu.groups.<chat_id>.requireMention`

Do not place these under `channels.feishu.accounts.main`:
- `groupPolicy`
- `groupAllowFrom`
- `requireMention`

## Non-main agents

To keep `planner` and `moltbook` out of all groups:
- keep `groupPolicy: "allowlist"`
- keep `groupAllowFrom: []`

This intentionally drops group messages for those accounts.

## Add a new collaboration group

1. Add the new Feishu `chat_id` to `channels.feishu.groupAllowFrom`
2. Add a matching `channels.feishu.groups.<chat_id>` block
3. Set `requireMention` according to expected behavior
4. Restart gateway and test in the target group

## Verification checklist

After changes:
- restart gateway
- verify gateway health
- verify target group `chat_id` exists in `groupAllowFrom`
- verify target group `requireMention` is correct
- verify `accounts.main` does not duplicate top-level group behavior keys
- verify `main` replies correctly in the intended group
- verify `planner` and `moltbook` still ignore group messages if that is the intended behavior

## Proven outcome in this workspace

This pattern was validated on 2026-03-22.
A stable fix was achieved by moving `main` group behavior from `accounts.main` to top-level `channels.feishu`.

## Feishu 内置命令

飞书对话框内可直接输入以下命令，发送后由 OpenClaw 拦截执行，不会传给 agent：

### `/reset`
- 作用：重置当前会话，清除当前 session 的对话上下文
- 场景：agent 回复异常、上下文混乱、想从头开始对话时使用
- 行为：触发 `runBeforeReset` hook（如果配置了 `session-memory` 等插件，会先执行记忆落盘），然后清空当前 session

### `/new`
- 作用：开启一个全新会话
- 场景：想切换话题、开始一个完全独立的新任务时使用
- 行为：与 `/reset` 类似，触发 `runBeforeReset` hook 后创建新 session

### 技术细节
- 两个命令在 `feishu-command-handler.ts` 中定义为 `DEFAULT_RESET_TRIGGERS`
- 匹配逻辑：精确匹配 `/reset` 或 `/new`，也支持带空格后缀（如 `/reset now`）
- 大小写不敏感
- 命令被消费后返回 `true`，消息不会进入正常 agent 对话流程
- 需要 `openclaw.json` 中 `commands.native` 设为 `"auto"` 或显式启用（默认已启用）
