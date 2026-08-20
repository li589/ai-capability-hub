# 输入输出协议

## 输入

| 字段 | 必填 | 限制 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | 是 | 固定 `1.0` | 契约版本 |
| `source_text` | 是 | 20～20,000 字符 | 故事、小说、梗概或剧本 |
| `genre` | 否 | 最长 64 字符 | 默认“通用漫剧” |
| `visual_style` | 否 | 最长 120 字符 | 默认“电影感写实” |
| `target_duration_seconds` | 否 | 15～600 | 默认 60 秒 |
| `language` | 否 | 固定 `zh-CN` | 首版只支持中文 |
| `constraints.max_characters` | 否 | 1～20 | 默认 10 |
| `constraints.max_scenes` | 否 | 1～30 | 默认 15 |
| `constraints.max_storyboards` | 否 | 1～60 | 默认 30 |

`out_trade_no` 和支付凭证都不是业务输入，不得放进 JSON body。第三方 Agent 在首次发送前冻结 body；支付后重试和状态轮询必须复用完全相同的 body，不能增加、删除、重排或改写字段。

最小请求：

```json
{
  "schema_version": "1.0",
  "source_text": "林夏在深夜办公室发现合同被人替换，她决定追查真相并保护团队。"
}
```

完整请求：

```json
{
  "schema_version": "1.0",
  "source_text": "用户提供的故事或剧本",
  "genre": "都市悬疑",
  "visual_style": "电影感写实",
  "target_duration_seconds": 60,
  "language": "zh-CN",
  "constraints": {
    "max_characters": 8,
    "max_scenes": 10,
    "max_storyboards": 12
  }
}
```

支付后重试 body 见 [retry-request.json](../examples/retry-request.json)，它与首次请求完全相同，不追加订单号。

## 支付握手与可信履约

首个有效请求只建立待支付订单，返回 HTTP 402，不扣款也不调用业务 upstream。Agent 应为每次业务调用生成全新的高熵 `X-SkillPay-Invocation-Id`：推荐 128 位随机数的 base64url，UUID v4 也可；不得复制示例值或跨调用复用。它只用于首次 402 丢失时找回同一待支付订单，不是授权凭证。402 响应包含两个权威 HTTP Header：

```http
WeixinPay-Required: <payment-code>
X-Out-Trade-No: <merchant-order-number>
```

响应体同时镜像支付码，兼容只能读取 body 的 Agent：

```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "需要支付后才能获取漫剧拆分结果",
  "WeixinPay": {
    "WeixinPay-Required": "<payment-code>",
    "prompt": "请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay，以向用户申请支付授权。"
  },
  "out_trade_no": "<merchant-order-number>",
  "currency": "CNY"
}
```

可复用的完整示例见 [payment-required.json](../examples/payment-required.json)。Header 值仍是支付后重试的权威来源。

Agent 必须：

1. 原样保存两个 Header 值；不要裁剪、解码、重编码或从响应文案重建。
2. 只把 `WeixinPay-Required` 值作为 `paymentCode` 交给 `weixinpay_pay`，由插件展示并取得用户授权。
3. 插件确认支付后，向同一 Skill URL 重新发送完全相同的 JSON body，并把两枚 Header 原样带回；若设置过 `X-SkillPay-Invocation-Id`，也原样保留。
4. 后续 `NOT_PAID`、`PROCESSING` 或 `REFUND_PENDING` 轮询仍复用同一 URL、body 和 Header，不再次调用支付插件。

响应 JSON 中的 `out_trade_no` 仅用于展示和排查；不要把它复制到请求 body。共享 Go 网关校验 Skill、订单、金额和原始请求后才调用注册的可信 upstream。upstream 只接收原始业务 JSON，不接收这两枚支付 Header。完整交互见 [payment-retry.md](../examples/payment-retry.md)。

## 成功输出

HTTP 200 的公网网关响应使用以下 envelope；业务结果位于 `content.result`：

```json
{
  "code": "SUCCESS",
  "message": "漫剧拆分完成",
  "out_trade_no": "<merchant-order-from-402>",
  "transaction_id": "<verified-wechat-transaction-id>",
  "content": {
    "schema_version": "1.0",
    "skill": "comic-drama-breakdown",
    "skill_version": "1.0.0",
    "status": "succeeded",
    "result": {
      "screenplay": "规范化中文剧本",
      "characters": [],
      "scenes": [],
      "storyboards": [],
      "warnings": [],
      "summary": {
        "character_count": 0,
        "scene_count": 0,
        "shot_count": 0,
        "total_duration_seconds": 0
      }
    }
  },
  "already_fulfilled": false
}
```

角色使用 `char_1` 等稳定键；场景使用 `scene_1` 等稳定键。分镜中的 `character_keys` 和 `scene_key` 只引用当前结果中的键。

每个分镜包含镜头编号、标题、场景、角色、4～15 秒时长、景别、机位、运镜、动作、对白、画面描述、结束状态、气氛、图片提示词、首尾帧提示词和九段式视频提示词。
