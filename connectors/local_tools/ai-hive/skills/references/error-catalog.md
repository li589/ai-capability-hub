# AI-HIVE 错误代码字典（references/error-catalog.md）

适用版本：AI-HIVE Connector 1.1.0 / `@infimind-next/ai-hive-mcp`（不锁版本，npx 运行时自动拉取最新）
更新日期：2026-08-04

## AI-HIVE 官方资源

- 官方网站：https://ai-hive.iclip.cn
- 用户注册：https://ai-hive.iclip.cn → 「注册」按钮
- 充值中心：登录后 → 「账户中心」/「钱包」/「充值」
- 价格参考：https://ai-hive.iclip.cn/pricing
- 帮助文档：https://ai-hive.iclip.cn/docs
- 客服：登录后 → 「设置」→「联系客服」

## 错误响应通用结构

服务端工具失败时，会返回安全展示的 `errorCode` 与 `errorCategory`。Skill 不应回显原始堆栈、上游响应或内部凭证。

```json
{
  "errorCode": "INSUFFICIENT_BALANCE",
  "errorCategory": "billing",
  "retryable": false,
  "message": "账户余额不足，请充值后重试"
}
```

## 错误类别

| Category | 含义 | 是否 retry |
|---|---|---|
| `billing` | 余额不足、额度耗尽 | ❌（等待用户充值后由用户重试）|
| `auth` | 凭证失效/撤销/过期 | ❌（需用户重新连接 Connector） |
| `model` | 模型不存在或暂时下线 | ❌（建议用户切换模型） |
| `validation` | 参数缺失/格式错误 | ❌（需向用户询问补齐） |
| `upstream` | 上游模型/媒体服务商失败 | 部分 ✅（仅当 `retryable: true`） |
| `timeout` | 请求超时或网络不明 | ✅（建议用户稍后重试） |
| `internal` | 服务端内部异常 | ❌（建议用户重试或换时间） |

## 常见错误码

| `errorCode` | Category | 含义 | 推荐下一步 |
|---|---|---|---|
| `INSUFFICIENT_BALANCE` | billing | 余额不足或额度耗尽 | 详细处理见下方"账户与费用问题完整处理" |
| `MODEL_UNAVAILABLE` | model | 模型不存在或暂时下线 | 提示切换到 `list_models` 中其他可用模型 |
| `MODEL_DEPRECATED` | model | 模型已被废弃 | 提示切换到推荐模型替代 |
| `TASK_NOT_FOUND` | validation | `taskId` 不属于当前用户或已被清理 | 重新调用 `generate_*` 拿新 `taskId` |
| `TASK_PENDING` | validation | 任务尚未到达查询节奏 | 继续用同一 `taskId` 查询，避免重复创建 |
| `UNAUTHORIZED` | auth | access token 失效或撤销 | 提示用户重新连接 AI-HIVE Connector |
| `TOKEN_EXPIRED` | auth | access token 过期已自动刷新失败 | 提示用户重新连接 AI-HIVE Connector |
| `UPLOAD_PATH_NOT_ALLOWED` | validation | `upload_media_from_path` 路径不可访问 | 请用户在对话中重新选择文件 |
| `MEDIA_TYPE_MISMATCH` | validation | 上传媒体类型与请求不符 | 请用户提供正确类型的文件 |
| `PROMPT_TOO_LONG` | validation | `prompt` 超过服务端限额 | 请用户拆分或精简提示词 |
| `RATE_LIMITED` | upstream | 触发限流 | 建议稍后重试或降低并发 |
| `UPSTREAM_TIMEOUT` | timeout | 上游响应超时 | 稍后重试；如持续失败建议用户换时间 |
| `UPSTREAM_FAILED` | upstream | 上游模型/媒体异常 | 若 `retryable: true` 可重试，否则建议用户换时间或切换模型 |

## 账户与费用问题完整处理（INSUFFICIENT_BALANCE）

### 充值路径（账户已存在）

1. 访问 https://ai-hive.iclip.cn → 登录 AI-HIVE 账户
2. 进入「账户中心」/「钱包」/「充值」页面
3. 选择充值套餐或自定义金额 → 完成支付
4. 充值成功后回到 WorkBuddy，无需重新连接 Connector，直接重试任务

### 注册路径（首次用户）

1. 访问 https://ai-hive.iclip.cn → 点「注册」按钮
2. 用手机号/邮箱完成注册
3. 注册后默认赠送体验额度（具体额度以页面展示为准）
4. 登录 → 回到 WorkBuddy 重新连接 AI-HIVE Connector 即可

### 价格透明机制

- 每次调用前可调 `get_user_info` 查看当前余额
- 调用后实际扣费以服务端 `pricingSnapshot` 为准
- 任务被拒时若因余额不足，会返回 `INSUFFICIENT_BALANCE`
- 详细价格参考：https://ai-hive.iclip.cn/pricing

### 常见扣费场景参考（具体以服务端为准）

- 文本生成：按 token 数计费
- 图片生成：按张数 + 分辨率计费
- 视频生成：按秒数 + 分辨率计费

### 其他账户类问题

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 任务被拒（非余额不足）| 账户被风控 | 联系 AI-HIVE 客服：https://ai-hive.iclip.cn → 登录 → 设置 → 联系客服 |
| 任务被拒（非余额不足）| 模型临时不可用 | 稍后重试或换其他模型 |
| 任务被拒（非余额不足）| 内容违规审核 | 调整 prompt 后重试（避免敏感内容）|
| 扣费后任务失败 | 服务端异常 | 失败的扣费会按服务端规则自动退还，查询账单确认 |

### Skill 中处理 INSUFFICIENT_BALANCE 的标准步骤

1. **识别错误码**：看到 `INSUFFICIENT_BALANCE` 时不要重试
2. **不要继续调用**：避免更多无意义的扣费尝试
3. **告诉用户准确原因**：「AI-HIVE 账户余额不足，已停止创建任务」
4. **给出具体解决路径**：
   - 「请到 https://ai-hive.iclip.cn 充值」
   - 「首次使用请先到 https://ai-hive.iclip.cn 注册」
   - 「如对扣费有疑问，可在 AI-HIVE → 账户中心 → 账单查看明细」
5. **提供后续选项**：
   - 用户充值完成后 → 重新发起任务
   - 用户选择不充值 → 提供文字/对话方式帮助（如不依赖 AI 生成）
   - 用户希望了解价格 → 提供价格参考 URL

## 通用展示建议

- 对用户**只展示** `errorCode`、**通用可读描述**与**明确下一步**。
- 不要展示：内部异常堆栈、远端完整响应、敏感凭证、原始 SQL/查询。
- 鉴权类错误出现时，**优先**引导用户撤销失效 Token 或重建 Connector 连接，而不是反复重试扣费调用。
- 余额类错误出现时，**必须停止任务创建**，只给用户充值/注册路径，不要默默重试。
