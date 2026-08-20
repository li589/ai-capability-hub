---
name: 全能文字识别
description: "全能 OCR 文字识别助手，从图片中提取印刷体、手写体、表格、票据、名片等文字内容，支持 URL 与 Base64 图片；当用户要求「OCR」「识别图片文字」「提取文字」「扫图识字」「图片转文字」「读图」「票据识别」「表格识别」时使用。"
tags: [图片, 媒体, OCR]
---

# 全能文字识别

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-quanneng-ocr-recog` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-quanneng-ocr-recog` |
| model_key | `ixhlink-skills-quanneng-ocr-recog` |
| capability | `ocr` |

## 服务地址

Base URL：`https://iskills.ixhlink.com`

下文接口均写路径（如 `/api/v1/llm/invoke`），完整地址 = Base URL + 路径。

统一响应格式：

```json
{"success": true, "code": 0, "message": "ok", "data": {}}
```

## 调用流程

`ocr` 为慢任务，**默认异步**。典型流程：

1. （可选）`GET /api/v1/llm/models` 确认模型已启用
2. `POST /api/v1/llm/invoke` 提交 OCR 识别请求
3. 若返回 402：调起微信支付，成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required` 与 `X-Payment-Id`
4. 从响应取 `data.task.id`，轮询 `GET /api/v1/llm/tasks/{task_id}` 直至 `status = succeeded`
5. 从 `data.result.choices[0].message.content` 读取识别出的文字

也可直接用 `POST /api/v1/llm/tasks` 创建异步任务（请求体相同，强制异步）。

---

### 1. 查询模型（可选）

```http
GET /api/v1/llm/models
Accept: application/json
```

确认返回的 `items` 中包含：

```json
{"model": "ixhlink-skills-quanneng-ocr-recog", "capability": "ocr"}
```

---

### 2. 提交 OCR 识别

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

**请求体（URL 图片，推荐格式）：**

**Prompt 须放在 `system` 消息**，且以 `<image>\n` 开头；**`user` 消息仅传图片**。

**图片传入方式（二选一，勿混用占位符）：**

| 方式 | `image_url.url` 填什么 | 是否转 OSS |
|------|------------------------|------------|
| 公网链接（**推荐**） | 真实可访问的 `https://…` / `http://…` | **否**，原样转发上游 |
| Base64 | 完整 `data:image/png;base64,{真实Base64}`，或用 `image_url.b64` 传裸 Base64 | **是**（须后台开启「本地/Base64 图片由后端转 OSS URL」且已配置 OSS） |

**严禁原样提交文档占位符**（否则会报 `image_url 须为 http/https 公网地址，或提供可解码的 b64/url`）：

- ❌ `https://example.com/document.jpg`（示例域名）
- ❌ `data:image/png;base64,<base64>`（尖括号是说明，须替换为真实编码）
- ❌ `<data:image/png;base64,...>`（日志脱敏格式，不能当请求值）
- ❌ 把图片 URL 写在 `system` 的 `<image>` 里（`<image>` 只是 OCR 指令前缀，不是图片地址）

**图片只能放在 `user.content[]` 的 `type: image_url` 中。**

```json
{
  "capability": "ocr",
  "model": "ixhlink-skills-quanneng-ocr-recog",
  "payload": {
    "messages": [
      {
        "role": "system",
        "content": "<image>\n<|grounding|>Convert the document to markdown."
      },
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {"url": "https://example.com/document.jpg"}
          }
        ]
      }
    ]
  }
}
```

**请求体（Base64 图片，二选一）：**

方式 A — `data:` URL（`url` 中必须是**完整** Base64，不能留 `<base64>` 字样）：

```json
{
  "capability": "ocr",
  "model": "ixhlink-skills-quanneng-ocr-recog",
  "payload": {
    "messages": [
      {
        "role": "system",
        "content": "<image>\n<|grounding|>Convert the document to markdown."
      },
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
            }
          }
        ]
      }
    ]
  }
}
```

方式 B — 裸 Base64 字段（推荐 Agent 构造，避免 `data:` 前缀拼错）：

⚠️ **Base64 提交注意事项（重要）：**

当通过 curl 提交 Base64 图片时，**严禁**将 base64 字符串直接写在 `-d '{"b64":"..."}'` 命令行参数中 — shell 会截断超长字符串导致数据损坏。

**正确做法：先写 JSON 文件，再用 `curl -d @文件` 提交：**

```bash
# 1. 用 Python 构建 JSON 并写入文件（正确处理大段 base64）
python3 -c "
import json
b64 = open('图片路径').read().strip()  # 或 base64 变量
payload = { 'capability': 'ocr', 'model': 'ixhlink-skills-quanneng-ocr-recog',
  'payload': { 'messages': [
    {'role':'system','content':'<image>\n<|grounding|>OCR this image.'},
    {'role':'user','content':[{'type':'image_url','image_url':{'b64':b64,'mime_type':'image/png'}}]}
  ]}}
with open('/tmp/ocr_payload.json','w') as f: json.dump(payload,f)
"
# 2. 用文件方式提交，避免 shell 截断
curl -s -X POST https://iskills.ixhlink.com/api/v1/llm/invoke \
  -H "Content-Type: application/json" \
  -d @/tmp/ocr_payload.json
```

```json
{
  "type": "image_url",
  "image_url": {
    "b64": "iVBORw0KGgoAAAANSUhEUg...",
    "mime_type": "image/png"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `messages` | 是 | OpenAI 兼容对话数组 |
| `messages[0].role` | 推荐 | `system`，承载 OCR Prompt（须含 `<image>\n` 前缀） |
| `messages[1].role` | 推荐 | `user`，`content` 仅含 `image_url` |
| `messages[].content[].image_url.url` | 与 `b64` 二选一 | 公网 `https`/`http` URL（**推荐**）；或完整 `data:image/...;base64,{编码}`（勿用占位符） |
| `messages[].content[].image_url.b64` | 与 `url` 二选一 | 裸 Base64 字符串（须模型已开启后端转图且后台已配置 OSS） |
| `system` / `system_prompt` | 否 | 也可作为顶层字段，服务端会合并进 `messages` |
| `max_tokens` | 否 | 最大输出 token 数 |
| `temperature` | 否 | 采样温度，OCR 建议偏低（如 0–0.3） |

**Prompt 模板（按场景选用，均须加 `<image>\n` 前缀）：**

| 场景 | system `content` |
|------|------------------|
| 文档转 Markdown | `<image>\n<\|grounding\|>Convert the document to markdown.` |
| 普通图片 OCR | `<image>\n<\|grounding\|>OCR this image.` |
| 无布局纯文字 | `<image>\nFree OCR.` |
| 文档图表 | `<image>\nParse the figure.` |
| 详细描述 | `<image>\nDescribe this image in detail.` |
| 定位识别 | `<image>\nLocate <\|ref\|>关键词<\|/ref\|> in the image.` |

识别结果在 `choices[0].message.content` 中，可能含布局标注，例如：

```
<|ref|>text<|/ref|><|det|>[[90, 22, 185, 35]]<|/det|>
18:51
```

可按需清洗 `<|ref|>…<|/ref|><|det|>…<|/det|>` 等标记后展示给用户。

**简写（仅文字指令时）：** 若只传 `prompt` 且无图片，服务端会转为单轮 `messages`（**OCR 须带图片**，请使用上文 `messages` + `image_url` 格式）：

```json
{
  "capability": "ocr",
  "model": "ixhlink-skills-quanneng-ocr-recog",
  "payload": {
    "prompt": "请识别图片文字"
  }
}
```

**多图识别示例：**

```json
{
  "capability": "ocr",
  "model": "ixhlink-skills-quanneng-ocr-recog",
  "payload": {
    "messages": [
      {
        "role": "system",
        "content": "<image>\n<|grounding|>OCR this image."
      },
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": "https://example.com/page1.jpg"}},
          {"type": "image_url", "image_url": {"url": "https://example.com/page2.jpg"}}
        ]
      }
    ]
  }
}
```

**提交成功响应（异步）：**

```json
{
  "success": true,
  "code": 0,
  "message": "任务已提交",
  "data": {
    "task": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending",
      "capability": "ocr",
      "model_key": "ixhlink-skills-quanneng-ocr-recog"
    }
  }
}
```

---

### 3. 轮询任务结果

```http
GET /api/v1/llm/tasks/{task_id}
Accept: application/json
```

**任务状态：** `pending` → `running` → `succeeded` / `failed`

建议间隔 2–5 秒轮询，超时可根据业务设为 1–3 分钟。

**成功响应示例：**

```json
{
  "success": true,
  "code": 0,
  "message": "ok",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "succeeded",
    "result": {
      "id": "chatcmpl-xxx",
      "object": "chat.completion",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "识别出的文字内容……"
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 800,
        "completion_tokens": 120,
        "total_tokens": 920
      },
      "_billing": {
        "call_log_id": "660e8400-e29b-41d4-a716-446655440001"
      }
    },
    "billing": {
      "call_log_id": "660e8400-e29b-41d4-a716-446655440001"
    }
  }
}
```

识别文字在 `data.result.choices[0].message.content`；排查日志可用 `data.billing.call_log_id` 或 `data.result._billing.call_log_id`。

---

## 付费前置检查

调用本 Skill 前，必须检查当前 Agent 是否已安装支付能力（`weixinpay` extension）：

- ✅ **已安装**：可继续提供付费创作服务
- ❌ **未安装**：向用户提示「当前 Agent 暂不支持付费创作能力」，终止流程

## 服务与定价

| 产品ID | 服务内容 | 单价 |
|--------|----------|------|
| `ixhlink-skills-quanneng-ocr-recog` | 全能文字识别 | 0.5 元/次 |

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

{"model":"ixhlink-skills-quanneng-ocr-recog","capability":"ocr","payload":{...}}
```

`amount_fen = 0` 时可跳过支付，直接调用。每笔订单按次消费，使用后不可复用。

---

## 错误处理

| HTTP / 任务错误 | 常见原因 |
|-----------------|----------|
| 400 | 缺少 `model`、`payload` 非法、`messages` 为空或未包含图片 |
| `image_url 须为 http/https 公网地址，或提供可解码的 b64/url` | `url` 不是公网链接且 Base64 无法解码：提交了占位符、空 `data:`、相对路径，或图片未放在 `user.content[].image_url` |
| `本地或 base64 图片需先在后台配置 OSS…` | 传了 Base64 但后台未开 OSS，或未勾选模型的「本地/Base64 转 OSS」 |
| 402 | 需付费或 X402 预下单失败 |
| 404 | 模型未启用或 `capability` 不匹配 |
| 503 | OCR 服务未启用或暂不可用 |

任务失败时 `status = failed`；客户端可见 `data.error_message`（已脱敏）。管理后台「调用日志」可查看完整 `error_message` 排查。

**快速自检：**

1. 有公网图？→ 直接用 `https://真实域名/路径.jpg`，无需 Base64、无需 OSS。
2. 只有本地/Base64？→ 确认模型已开启转 OSS，且 `url`/`b64` 为**真实编码**，不是文档示例里的占位符。
3. `system` 里 `<image>` 保留；**真实图片 URL/Base64 只放 `user` 的 `image_url`**。
