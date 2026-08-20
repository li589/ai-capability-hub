# Execution Checklist

## Purpose

Minimal verification steps for every use of this skill.
Run through this list after any setup, repair, or config change.

## Pre-flight (before making changes)

- [ ] Confirmed current capability level (Level 0/1/2/3)
- [ ] Confirmed which channel the user is on (Feishu / Discord / Telegram / other)
- [ ] Confirmed target agent(s) exist in `agents.list`
- [ ] Confirmed target agent(s) have correct `binding` entries
- [ ] Backed up `openclaw.json` before risky edits (`cp openclaw.json openclaw.json.bak`)
- [ ] If workspace dual-layer pattern exists, confirmed both layers present

## Config change (during)

- [ ] Edited only the minimum necessary fields
- [ ] Validated JSON syntax (`python3 -c "import json; json.load(open('openclaw.json'))"`)
- [ ] Did not duplicate group behavior keys across top-level and per-account
- [ ] Kept stable routing pattern: top-level `channels.<ch>` controls group behavior, not `accounts.<id>`

## Post-change verification

### Gateway health
- [ ] Gateway is running (`openclaw gateway status` or `openclaw status`)
- [ ] No plugin load errors in logs after restart

### Direct chat (if relevant)
- [ ] `main` responds to DM without error
- [ ] Target agent responds to its own DM if it has a separate account

### Internal delegation (Level 1+)
- [ ] `sessions_send` from `main` to target agent succeeds (no timeout or error)
- [ ] Target agent returns a result
- [ ] `main` can receive and relay the result

### Visible group sync (Level 2+)
- [ ] Target bot is a member of the collaboration group
- [ ] `main` can receive messages in the group (with or without `@` per config)
- [ ] `main` can send replies to the group
- [ ] Other agents (planner/moltbook) do NOT respond directly in the group (unless explicitly configured)
- [ ] Delegation result is visible in the group via `main` 收口

### Multi-group / default sync group (Level 3)
- [ ] Default sync group is set and reachable
- [ ] Override to a different group works when specified
- [ ] No cross-group message leakage

## Regression check

- [ ] Previously working DM still works
- [ ] Previously working group reply still works
- [ ] No new plugin load errors
- [ ] No new `accounts.default` conflict (keep `enabled: false` if that was the stable state)

## Sign-off

After all checks pass:
- [ ] Record the working pattern in relevant workspace doc (if new or changed)
- [ ] State outcome to user: Working / Degraded / Blocked (per `diagnostic-flow.md` Step 8)

## Quick reference: common failure modes

| Symptom | First check |
|---|---|
| 群里不回复 | `groupPolicy` + `groupAllowFrom` + `requireMention` |
| DM 不回复 | gateway health + agent binding + model availability |
| 分工后无回执 | `sessions_send` connectivity + target agent model/timeout |
| 插件加载失败 | `openclaw.json` plugins entries + 文件路径是否存在 |
| Config 改完重启挂了 | JSON syntax + 恢复 `.bak` 备份 |
| 后台插件超时导致断连 | memory-reflection / self-improvement 超时参数 + 模型选择 |

## Minimum evidence rules

- `执行已确认` 至少要有对象 ID / URL / messageId / 第三方对象主键，或目标侧成功结果且对象可唯一定位。
- `禁止补派` 必须在 `执行已确认` 成立且已记录去重锚点后才能使用。
- `部分完成` 只适用于主线完成但治理缺口未闭环的情况，不能拿来包装未完成主线。
- `已完成` 必须同时满足：执行结果已确认、必要证据已取得、当前轮要求的收口项已完成。
- `失败` 不能因为"没回我"直接判定，必须经过核验与允许范围内的补派 / 降级尝试。
