# 事件字典

## 1. 核心事件

| 事件 | 说明 | 必填字段 |
| --- | --- | --- |
| `bookwriter_entry_seen` | 自然触发 Skill | `bindingId` `traceId` `benefitSource` |
| `first_value_completed` | 目录、素材清单、章节草稿等首值完成 | `assetType` `valueStage` |
| `continued_use_completed` | 恢复后继续动作完成 | `currentStage` `bindingId` |
| `post_draft_action_click` | 用户进入后处理 | `assetType` `valueStage` |
| `layout_export_request` | 请求排版导出 | `assetType` |
| `de_ai_polish_request` | 请求去 AI 味 | `assetType` |
| `credits_balance_seen` | 查询乐包余额或升级提示 | `benefitSource` `memberTier` `creditsState` |
| `member_tier_resolved` | 会员层级已确定 | `benefitSource` `memberTier` |
| `entitlement_gate_checked` | 场景包 / 权益门禁检查 | `benefitSource` `creditsState` |
| `api2_backend_fallback_used` | API2 不可用，转连接器或本地缓存 | `benefitSource` `notes` |
| `paid_intent` | 用户表达付费或交付意向 | `commercialStage` |

## 2. 本地兜底

API2 或连接器不可用时，用 `scripts/event-writer.mjs` 把事件写入：

`<bookRoot>/.fbs/events/bookwriter-events-YYYY-MM-DD.jsonl`
