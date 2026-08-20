# 模式 D · 录入

执行前 **`Read`** `prompts/oa/guardrails.md`。

## 触发

用户提到：审查意见、意见陈述、OA 答复、补正通知书、案例入库、审查答复、`/oa`、`/审查答复`。

## 分流

| 意图 | 下一步 |
|------|--------|
| 入库 / 脱敏归档历史案 | **`Read`** `ingest_case.md` |
| 针对通知书写答复 | **`Read`** `respond_office_action.md` |
| 配置 / 开启向量 | **`Read`** `configure_embedding.md`（对话问答 → set → selftest） |
| 两者都要 | 先入库再答复 |

## 首次必问（向量 · 对话交互）

若 `user_confirmed: false`（`config.py status`）：

1. **`Read`** `configure_embedding.md`  
2. 按脚本问答（可跳过；可预设；可自定义 URL/模型/Key）  
3. 写配置 + secrets 后看 `selftest`；失败则请用户改参重试，仍可继续标签流程  

已确认则可跳过；用户中途要求开向量时再走 `configure_embedding.md`。
