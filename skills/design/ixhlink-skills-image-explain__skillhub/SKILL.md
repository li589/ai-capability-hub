---
name: 智绘图片理解
description: "智能图片理解助手，支持对单张或多张图片进行内容描述、视觉问答、文字识别与对比分析；当用户要求「识图」「看图」「描述图片」「分析图片」「图中有什么」「提取图片文字」「对比图片」「视觉问答」时使用。"
tags: [图片, 媒体, 视觉]
---

# 智绘图片理解

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-image-explain` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-image-explain` |
| model_key | `ixhlink-skills-image-explain` |
| capability | `vision` |

## 服务地址

Base URL：`https://iskills.ixhlink.com`

下文接口均写路径（如 `/api/v1/llm/invoke`），完整地址 = Base URL + 路径。

统一响应格式：

```json
{"success": true, "code": 0, "message": "ok", "data": {}}
```

## 调用流程

`vision` 为**同步**能力，典型流程：

1. （可选）`GET /api/v1/llm/models` 确认模型已启用
2. `POST /api/v1/llm/invoke` 提交图片理解请求（`messages` 中含图片与文字）
3. 若返回 402：调起微信支付，成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required` 与 `X-Payment-Id`
4. 从 `data.choices[0].message.content` 读取模型回复文本

---

### 1. 查询模型（可选）

```http
GET /api/v1/llm/models
Accept: application/json
```

确认返回的 `items` 中包含：

```json
{"model": "ixhlink-skills-image-explain", "capability": "vision"}
```

---

### 2. 提交图片理解

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

**请求体（URL 图片）：**

```json
{
  "capability": "vision",
  "model": "ixhlink-skills-image-explain",
  "payload": {
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "请详细描述这张图片的内容、主体、场景与氛围"},
          {
            "type": "image_url",
            "image_url": {"url": "https://example.com/photo.jpg"}
          }
        ]
      }
    ]
  }
}
```

**请求体（Base64 图片）：**

```json
{
  "capability": "vision",
  "model": "ixhlink-skills-image-explain",
  "payload": {
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "图中有什么文字？请逐条列出"},
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/png;base64,<base64>"
            }
          }
        ]
      }
    ]
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `messages` | 是 | OpenAI 兼容对话数组；`user` 消息的 `content` 可混合 `text` 与 `image_url` |
| `messages[].content[].type` | 是 | `text` 或 `image_url` |
| `messages[].content[].image_url.url` | 图片时必填 | 公网 `https` URL，或 `data:image/...;base64,...` |
| `system` / `system_prompt` | 否 | 系统提示（也可放在 `messages` 首条 `role: system`） |
| `max_tokens` | 否 | 最大输出 token 数 |
| `temperature` | 否 | 采样温度 |

**简写（仅文字问题时）：** 若只传 `prompt` 且无图片，服务端会转为单轮 `messages`：

```json
{
  "capability": "vision",
  "model": "ixhlink-skills-image-explain",
  "payload": {
    "prompt": "你好"
  }
}
```

带图片时请使用上文 `messages` + `image_url` 格式。

**多图理解示例：**

```json
{
  "capability": "vision",
  "model": "ixhlink-skills-image-explain",
  "payload": {
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "对比这两张图的差异"},
          {"type": "image_url", "image_url": {"url": "https://example.com/a.jpg"}},
          {"type": "image_url", "image_url": {"url": "https://example.com/b.jpg"}}
        ]
      }
    ]
  }
}
```

**调用成功响应（同步）：**

```json
{
  "success": true,
  "code": 0,
  "message": "调用成功",
  "data": {
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "这是一张……"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 1200,
      "completion_tokens": 180,
      "total_tokens": 1380
    },
    "_billing": {
      "call_log_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

模型回复文本在 `data.choices[0].message.content`；排查日志可用 `data._billing.call_log_id`。

---

## 付费前置检查

调用本 Skill 前，必须检查当前 Agent 是否已安装支付能力（`weixinpay` extension）：

- ✅ **已安装**：可继续提供付费创作服务
- ❌ **未安装**：向用户提示「当前 Agent 暂不支持付费创作能力」，终止流程

## 服务与定价

| 产品ID | 服务内容 | 单价 |
|--------|----------|------|
| `ixhlink-skills-image-explain` | 智绘图片理解 | 0.3 元/次 |

> 价格以 SkillHub 后台配置为准。命中创作意图后，向用户展示服务名称和价格，由用户确认后进入付费流程。

## 付费说明

当 `amount_fen > 0` 且未完成支付时，首次 `POST /api/v1/llm/invoke` 会返回 HTTP 402，响应中携带：

- Header：`WeixinPay-Required: <payment_code>`、`X-Payment-Id: <payment_id>`
- Body：`WeixinPay` 对象（含 `payment_id`、`prompt` 等）

**客户端流程（Agent / MCP / Web）：**

```
首次 invoke → 402 → weixinpay_pay(payment_code) → 支付成功后重试 invoke
```

**「原样重试」的含义：**

- **JSON body 不变**：`model`、`capability`、`payload` 必须与首次请求完全一致
- **订单参数单独带上**：将 402 中的 `payment_code`、`payment_id` 通过 Header 传入（推荐），或写入 body 的 `WeixinPay`；勿改 `payload` 业务字段来传订单号

**重试请求示例：**

```http
POST /api/v1/llm/invoke
Content-Type: application/json
WeixinPay-Required: <payment_code>
X-Payment-Id: <payment_id>

{"model":"ixhlink-skills-image-explain","capability":"vision","payload":{...}}
```

`amount_fen = 0` 时可跳过支付，直接调用。每笔订单按次消费，使用后不可复用。

---

## 错误处理

| HTTP | 常见原因 |
|------|----------|
| 400 | 缺少 `model`、`payload` 非法、`messages` 为空或未包含图片 |
| 402 | 需付费或 X402 预下单失败 |
| 404 | 模型未启用或 `capability` 不匹配 |
| 503 | 模型站点未启用 |

上游失败时查看响应 `message` 与 `_billing.call_log_id` 对应后台调用日志。
