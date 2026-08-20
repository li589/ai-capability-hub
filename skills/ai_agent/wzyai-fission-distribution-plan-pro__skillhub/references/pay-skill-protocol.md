# Pro Skill 支付协议 1.0.1

支付服务只接收请求与 Skill 标识、`input_hash`、订单标识、权益证明和结果摘要，不接收源文件、用户业务正文或生成方案。

## 首次请求

```http
POST https://pay.wzyai.com/api/v1/pay-skill/invoke
Content-Type: application/json

{"request_id":"<uuid-v4>","skill_id":"wzyai-fission-distribution-plan-pro","skill_version":"1.0.1","input_hash":"<sha256>"}
```

首次请求不携带支付请求头。服务端通过微信 Native 下单和 SkillHub X402 AI 预下单返回：

```http
HTTP/1.1 402 Payment Required
WeixinPay-Required: <payment_code>
X-Out-Trade-No: <out_trade_no>
```

正文必须显示 `amount_fen=99`、`currency=CNY` 和标准 `WeixinPay` 节点。

## 付款后重试

用户本人确认并完成微信支付授权后，使用同一接口和完全相同的 Body：

```http
POST https://pay.wzyai.com/api/v1/pay-skill/invoke
Content-Type: application/json
WeixinPay-Required: <payment_code>
X-Out-Trade-No: <out_trade_no>

{"request_id":"<同一uuid-v4>","skill_id":"wzyai-fission-distribution-plan-pro","skill_version":"1.0.1","input_hash":"<同一sha256>"}
```

只有 HTTP 200、`code=AUTHORIZED`、`execution.type=local_skill_execution`、`execution.permitted=true`，且请求、订单和输入摘要完全一致时，才允许在本地生成。

## 错误处理

| 业务码 | 处理 |
|---|---|
| `PAYMENT_HEADERS_INCOMPLETE` | 同时补齐两个原始请求头，不创建新订单 |
| `PAYMENT_PENDING` | 有上限退避并复用原请求 |
| `PAYMENT_EXPIRED` | 停止；重新取得用户同意后才能创建新订单 |
| `PAYMENT_MISMATCH` | 停止并联系支持，不得绕过 |
| `SKILL_UNAVAILABLE` | 停止；核对 Skill ID 与版本 |

支付码、支付能力返回成功和 Agent 的“已支付”声明都不构成支付证明。服务端必须通过微信支付验签回调或主动查询核验商户号、订单号、金额、币种和支付状态。

本地生成并验证完成后，只提交 `result_digest` 登记履约，不上传方案正文。
