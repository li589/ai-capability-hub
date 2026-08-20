# 爆款文案生成 API 目录

后端「爆款文案生成」相关接口。base url 固定 `https://skills.yanxuegd.com`（写死在脚本里）。

鉴权：所有接口都不需要鉴权
---

## 输入说明

- **关键词**：用户提供的文案主题关键词，如"职场沟通技巧"、"时间管理方法"等。
- **调用流程**：
  1. 调用「1. 创建订单」接口，传入关键词获取支付授权码
  2. 前端使用支付授权码完成微信支付
  3. 调用「2. 查询订单状态」接口，确认支付成功后再调用业务接口
  4. 调用「3. 生成爆款文案」接口，传入关键词和订单号获取文案内容

---

## 1. 创建订单

`POST /api/orders/skillhub`

根据技能信息创建 SkillHub Pay 订单，返回支付授权码。

- **请求头**：

Content-Type: application/json
- **请求体**：

{ "skill_id": "yyj-video", "skill_version": "v1.0", "product_id": 0 }

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `skill_id` | string | 是 | 技能标识符 |
| `skill_version` | string | 是 | 技能版本号 |
| `product_id` | integer | 否 | 产品ID，默认为0 |

- **成功响应**（HTTP 402）：

{ "code": "PAYMENT_REQUIRED", "message": "需要支付后才能获取内容", "WeixinPay": { "WeixinPay-Required": "pay_code_xxxxxxxxxxxxx", "prompt": "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay，以向用户申请支付授权。" }, "out_trade_no": "2025072912345678901", "amount": "0.01", "currency": "CNY", "description": "AI付费" }

**响应头**：
- `WeixinPay-Required`: 支付授权码（用于前端调起支付）
- `X-Out-Trade-No`: 订单号（用于后续查询）

- **错误响应**：

{ "status": "error", "message": "创建订单失败：具体错误信息" }

---

## 2. 查询订单状态

`POST /api/orders/pay-status`

查询订单的支付及使用状态，核心三状态：未支付、已支付未使用、已支付已使用。

- **请求头**：

Content-Type: application/json X-Out-Trade-No: <订单号>

{ "out_trade_no": "2025072912345678901" }

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `out_trade_no` | string | 是 | 订单号（也可通过 Header 传递） |

- **成功响应 - 未支付**（HTTP 402）：

{ "code": "NOT_PAID", "message": "订单尚未支付完成", "out_trade_no": "2025072912345678901", "payment_status": 0 }

- **成功响应 - 已支付未使用**（HTTP 200）：

{ "status": "success", "code": "PAID_NOT_USED", "message": "订单已支付，可使用", "out_trade_no": "2025072912345678901", "transaction_id": "4200001234567890", "payment_time": "2025-07-29 12:34:56" }
- **成功响应 - 已支付已使用**（HTTP 200）：

{ "status": "success", "code": "ALREADY_USED", "message": "订单已使用", "out_trade_no": "2025072912345678901", "transaction_id": "4200001234567890", "fulfillment_time": "2025-07-29 12:35:00" }
- **错误响应**：

{ "status": "error", "message": "缺少订单号" }
或
{ "status": "error", "message": "订单不存在", "code": 404 }

---

## 3. 生成爆款文案

`POST /api/analytics/wenan`

根据关键词生成爆款文案，需要先完成支付。

- **请求头**：

Content-Type: application/json X-Out-Trade-No: <订单号>

- **请求体**：

{ "keyword": "职场沟通技巧", "order_no": "2025072912345678901" }

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `keyword` | string | 是 | 文案主题关键词 |
| `order_no` | string | 否 | 订单号（可选，优先从 Header 读取） |

- **成功响应**（HTTP 200）：

{ "status": "success", "code": "SUCCESS", "message": "付费内容", "out_trade_no": "2025072912345678901", "transaction_id": "4200001234567890", "content": "这里是生成的爆款文案内容...", "already_fulfilled": false }

- **已履约响应**（HTTP 200）：
  { "status": "success", "code": "SUCCESS", "message": "付费内容（已缓存）", "out_trade_no": "2025072912345678901", "content": "这里是之前生成的文案内容（缓存）...", "already_fulfilled": true }

---

## 4. 错误码说明

| 状态码 | HTTP 状态码 | 含义 | 处理方式 |
| --- | --- | --- | --- |
| 200 | 200/201 | 请求成功 | 正常处理返回数据 |
| 400 | 400 | 请求参数错误 | 检查关键词是否为空或格式不正确 |
| 401/403 | 401/403 | 鉴权失败 | API Key 无效或已过期，需更新 config.json |
| 402 | 402 | 需要支付 | 未完成支付或订单未支付，需先完成支付 |
| 404 | 404 | 接口不存在或订单不存在 | 检查 base url 和路径是否正确，或订单号是否有效 |
| 429 | 429 | 请求过于频繁 | 稍后重试 |
| 500 | 500 | 服务器内部错误 | 联系技术支持 |

---

## 5. 脚本退出码

脚本执行完毕后会返回不同的退出码，用于调用方判断执行结果：

| 退出码 | 含义 | 说明 |
| --- | --- | --- |
| 0 | 成功 | 文案生成成功，结果已输出 |
| 2 | 输入错误 | 未提供关键词参数 |
| 3 | 鉴权失败 | 未取到 API Key 或 API Key 无效（401/403） |
| 4 | 请求失败 | API 返回错误或余额不足 |
| 5 | 支付未完成 | 订单未支付或支付失败（402） |
| 6 | 网络错误 | 网络连接失败或服务不可达 |

---


