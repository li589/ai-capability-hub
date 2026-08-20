# 错误与安全重试

| HTTP / code | Agent 处理 |
| --- | --- |
| `402 PAYMENT_REQUIRED` | 首个有效请求仅建立待支付订单，不扣款、不执行 upstream。原样保存 `WeixinPay-Required` 和 `X-Out-Trade-No`；只将前者交给 `weixinpay_pay` 取得用户授权。插件成功后用完全相同的 JSON body 和两枚原始 Header 重试。 |
| `402 NOT_PAID` | 微信支付尚未确认或查询暂时失败。保留同一 URL、body 和两枚 Header，退避后重试；不要再次支付或创建新订单。 |
| `202 PROCESSING` | 可信 upstream 已在履约或同一订单被另一请求占用。安全轮询同一请求；不要重复执行、支付或换订单。 |
| `200 SUCCESS` | 读取 `content`；`already_fulfilled: true` 表示网关返回同一订单的幂等缓存。终止轮询。 |
| `409 INVOCATION_CONFLICT` | Skill、订单、`X-SkillPay-Invocation-Id`、body 或两枚支付 Header 与首次响应不一致。支付后必须原样回放 `WeixinPay-Required` 和 `X-Out-Trade-No`；缺失或篡改 `WeixinPay-Required` 也会冲突。只有仍持有首次请求原始字节和两枚原始 Header 时才能恢复后重试，否则停止并排查；不得把订单移到另一个 Skill。 |
| `409 PAYMENT_AMOUNT_MISMATCH` | 停止履约和自动重试，保留订单号并联系商户支持。 |
| `502 PAYMENT_VERIFICATION_FAILED` | 微信支付结果缺少可信交易信息，网关无法确认完整支付。停止自动重试，保留订单号并联系商户支持；不得绕过校验调用 upstream。 |
| `400 INVALID_INPUT` | 支付前可修正后作为新的首次请求发送；取得 402 后不得修改原 body 或两枚支付 Header。 |
| `404 SKILL_NOT_FOUND` | 共享网关未注册该 Skill；停止支付和重试并报告配置错误。 |
| `404 ORDER_NOT_FOUND` | `X-Out-Trade-No` 不存在或不属于当前环境；停止自动重试，保留原始 402 响应供排查。 |
| `PAYMENT_ORDER_FAILED` | 微信预支付订单创建失败且未返回可支付凭证；保留同一 `X-SkillPay-Invocation-Id`，退避后重发首次请求。 |
| `SKILLPAY_PREORDER_FAILED` | 支付插件预下单失败；未授权、未扣款。使用同一调用 ID 退避重试，避免重复待支付订单。 |
| `ORDER_STORE_FAILED` | 订单账本状态不确定。停止自动重试，不创建新订单，联系商户支持。 |
| `202 REFUND_PENDING` | 业务履约失败后，退款已受理或微信最终状态尚未确认。网关后台会继续恢复；Agent 在线时可用同一 URL、body 和两枚 Header 轮询，不得再次支付、再次触发 upstream 或宣称退款成功。 |
| `200 REFUNDED` | 仅表示微信已确认退款 `SUCCESS`。告知用户全额退款已确认；这是终态。 |
| `503/502 REFUND_FAILED` | 只依据 `retryable`。为 `true` 时遵循 `Retry-After`，重放同一 URL、body 和两枚 Header；`CLOSED` 由网关在到期后更换退款号，`UNKNOWN`/`NOT_FOUND` 也由网关决定同号安全重试，最多 3 次。为 `false` 时停止；`CLOSED` 尝试耗尽或 `ABNORMAL` 都需联系商户支持。Agent 永不自行发起退款或选择退款号。 |

## 重试规则

1. 首次发送前保存 Skill URL、原始 JSON body 字节，并为本次调用生成高熵 `X-SkillPay-Invocation-Id`（推荐 128 位随机 base64url，UUID v4 也可）。收到 402 后再保存两枚响应 Header；同一调用中全部保持不变，调用 ID 不得跨调用复用，也不能替代两枚支付 Header。
2. 只有传输超时、`NOT_PAID`、`PROCESSING`、`REFUND_PENDING`，以及明确带 `retryable: true` 的 `REFUND_FAILED` 可以自动重试。退款响应优先且必须遵循 `Retry-After`；其余情况使用带抖动的有界指数退避，并遵守 Agent 的总超时。
3. 任何支付结果不确定的情况都不要再次调用支付插件。达到总超时后向用户报告当前状态和订单号，不得把“待确认”描述为成功。
4. 不要在 body 中增加 `out_trade_no`，不要更换或跨 Skill 使用两枚支付 Header，也不要通过新的首次请求绕开原订单。

不要把 `transaction_id`、支付凭证或订单号写入后续创作提示词。`WeixinPay-Required` 只交给支付插件和同一 HTTPS 网关，不写日志、不发给 upstream。排查时只向受信任的商户支持提供必要订单号，不发送支付凭证、Token 或完整敏感素材。
