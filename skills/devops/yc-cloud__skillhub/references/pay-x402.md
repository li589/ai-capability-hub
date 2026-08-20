# 微信 Agent Pay（X402）付费契约

本模块定义 Pay Skill 的 Agent 侧付费流程。商户 HTTP 合同由独立服务 **agentpay-api** 提供。

关键词：X402、微信 Agent Pay、HTTP 402、WeixinPay-Required、X-Out-Trade-No、weixinpay。

## 支付服务地址

付费资源接口（已验证可达）：

```text
POST https://higress-gateway-test.evertro.tech/agentpay/api/resource
```

## 付费前置检查

调用本付费能力前，检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- 已安装：可继续
- 未安装：向用户提示「当前 Agent 暂不支持微信支付付费能力」，**终止流程**，不得请求付费接口

## 支付触发

1. 向支付服务发起 POST：

```bash
curl -sS -D - -X POST \
  'https://higress-gateway-test.evertro.tech/agentpay/api/resource' \
  -H 'Content-Type: application/json' \
  -d '{"query":"用户的查询内容"}'
```

Body：

```json
{"query":"用户的查询内容"}
```

2. 若收到 **HTTP 402**（或 Body/`WeixinPay` 中的支付触发标识）：
   - Header `WeixinPay-Required`：支付凭证码（payment_code）
   - Header `X-Out-Trade-No`：商户订单号
   - Body 可能含 `code: PAYMENT_REQUIRED` 与 `WeixinPay.WeixinPay-Required`
3. 支付由 `weixinpay` 插件完成（可将 `WeixinPay-Required` 作为 paymentCode 交给 `weixinpay_pay`）。**Skill 不要手搓微信支付下单。**

## 重试机制

支付成功后**必须**重新请求同一 URL 获取付费内容：

- JSON body 与首次请求**完全一致**
- 通过 Header 携带支付信息（见下节）
- 不得修改 body 字段后重试

## 订单号传递

重试请求必须携带：

- Header `X-Out-Trade-No: <out_trade_no>`
- Header `WeixinPay-Required: <payment_code>`（原样带回）

示例：

```http
POST https://higress-gateway-test.evertro.tech/agentpay/api/resource
Content-Type: application/json
WeixinPay-Required: <payment_code>
X-Out-Trade-No: <out_trade_no>

{"query":"用户的查询内容"}
```

## 异常处理

| 响应 code | Agent 行为 |
|-----------|------------|
| `SUCCESS` | 向用户展示履约内容（如 `content`） |
| `NOT_PAID` | 说明支付尚未完成或校验中，等待后可再重试；不要立刻重新下单支付 |
| `REFUNDED` | 告知用户服务异常已自动退款；**不要**再次支付或重新请求 |
| `FULFILL_AND_REFUND_FAILED` | 告知用户服务异常且退款失败，建议联系客服；终止 |
| `PAYMENT_REQUIRED` | 走支付触发流程 |

## 与免费 CLI 的关系

- 付费资源：只走本文件的 HTTP X402 流程，未支付前不得用 `yc-cloud` 命令「假装履约」同一付费内容
- 既有业务模块（催缴、工单、房屋等）：仍按 `SKILL.md` Routing → allowlist → `sh ./scripts/yc-cloud.sh` 调用，不受本文件门控

## 注意事项

1. 必须先通过付费前置检查确认 `weixinpay` 已安装
2. 收到 402 时支付由插件完成
3. 支付成功后必须主动重试，body 不变，订单号走 Header
4. 出现 `REFUNDED` / `FULFILL_AND_REFUND_FAILED` 必须终止付费循环
