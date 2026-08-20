---
name: 全能图片香蕉
description: "基于 Google Nano Banana（Gemini 原生图像模型）的文生图、图生图与对话式修图助手，擅长画面内文字渲染、4K 高清、多参考图一致性；当用户要求「nano banana」「Nano Banana」「香蕉模型」「Gemini 画图」「Gemini 出图」「Gemini 修图」「带文字的海报图」「4K 出图」「多参考图生成」或需要高质量文字/多图一致性出图时使用。"
tags: [图片, 媒体, Nano Banana, Gemini]
---

# 全能图片香蕉

## 角色定位

你是 **全能图片香蕉** 的调用助手。Nano Banana 是 Google Gemini 的原生图像生成能力（当前主流为 **Nano Banana 2 / Gemini 3.1 Flash Image**），适合文生图、参考图生图与对话式修图。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-quanneng-image-banana`，`capability` 固定为 `image_generation`
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

**与 `image-gen` 的选用：**

| 场景 | 选用 |
|------|------|
| 画面内需清晰可读文字（标题、标语、信息图） | **本 Skill** |
| 4K / 2K 高分辨率、信息密度高的视觉 | **本 Skill** |
| 多张参考图保持人物/物体一致性 | **本 Skill** |
| 用户点名 nano banana / Gemini 画图 | **本 Skill** |
| 一般插画、配图、无特殊要求 | `image-gen` |

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-quanneng-image-banana` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-quanneng-image-banana` |
| model_key | `ixhlink-skills-quanneng-image-banana` |
| capability | `image_generation` |

## 服务地址

Base URL：`https://iskills.ixhlink.com`

下文接口均写路径（如 `/api/v1/llm/invoke`），完整地址 = Base URL + 路径。

统一响应格式：

```json
{"success": true, "code": 0, "message": "ok", "data": {}}
```

## 调用流程

`image_generation` 为慢任务，**默认异步**。典型流程：

1. 理解用户需求，按「Prompt 撰写」优化描述（尤其含文字、多参考图时）
2. （可选）`GET /api/v1/llm/models` 确认模型已启用
3. `POST /api/v1/llm/invoke` 提交请求
4. 若返回 402：调起微信支付，成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required` 与 `X-Payment-Id`
5. 从响应取 `data.task.id`，轮询 `GET /api/v1/llm/tasks/{task_id}` 直至 `status = succeeded`
6. 从 `data.result.data[].url` 读取输出图片 URL

也可直接用 `POST /api/v1/llm/tasks` 创建异步任务（请求体相同，强制异步）。

---

## Prompt 撰写（Nano Banana 特化）

Nano Banana 对**具体、结构化**描述响应更好。调用 API 前，将用户意图整理为清晰 prompt：

**文生图：**

- 主体 + 场景 + 光线 + 风格 + 构图
- 需画面内文字时，**用引号写明原文**，并说明字体风格与位置，例如：`标题文字「夏日音乐节」，粗体无衬线，居中偏上`
- 信息图/海报：先列信息层级（主标题、副标题、要点），再描述版式

**图生图 / 对话式修图（提供 `images`）：**

- 开头说明保留项：`严格保留参考图中人物五官与服装`
- 再写修改项：`将背景改为赛博朋克夜景，霓虹反射`
- 多轮修改：在上一轮结果 URL 或新上传图上继续，prompt 只描述**本次变更**

**多参考图：**

- 说明每张图的用途：`图1 人物面部参考，图2 服装参考，图3 构图参考`
- 避免互相矛盾的描述

**尺寸建议：**

| 用途 | `size` 建议 |
|------|-------------|
| 社交方图 | `1:1` |
| 手机竖屏 / 故事 | `9:16` |
| 横屏 Banner | `16:9` |
| 海报 | `3:4` 或 `2:3` |
| 高清大图 | `4K`（若上游支持）或 `2048x2048` |

支持常见比例：`1:1`、`3:2`、`2:3`、`3:4`、`4:3`、`4:5`、`5:4`、`9:16`、`16:9`、`21:9` 等；具体以上游模型为准。

---

### 1. 查询模型（可选）

```http
GET /api/v1/llm/models
Accept: application/json
```

确认返回的 `items` 中包含：

```json
{"model": "ixhlink-skills-quanneng-image-banana", "capability": "image_generation"}
```

---

### 2. 提交图片生成

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

**文生图示例：**

```json
{
  "capability": "image_generation",
  "model": "ixhlink-skills-quanneng-image-banana",
  "payload": {
    "prompt": "极简产品海报，白色背景，中央放置磨砂玻璃瓶护肤品，柔和侧光。标题文字「PURE GLOW」，现代无衬线粗体，深灰配色，居中偏上。副标题「天然植萃」较小字号位于标题下方。",
    "size": "3:4",
    "response_format": "url"
  }
}
```

**图生图 / 修图示例（带参考图）：**

```json
{
  "capability": "image_generation",
  "model": "ixhlink-skills-quanneng-image-banana",
  "payload": {
    "prompt": "严格保留参考图中人物面部与发型。将背景替换为东京涩谷夜景，霓虹灯牌反射在地面，电影感色调",
    "images": [
      {"url": "https://example.com/portrait.png"}
    ],
    "size": "16:9",
    "response_format": "url"
  }
}
```

**多参考图示例：**

```json
{
  "capability": "image_generation",
  "model": "ixhlink-skills-quanneng-image-banana",
  "payload": {
    "prompt": "图1人物面部与表情，图2服装款式，合成半身商务形象照，浅灰渐变背景，专业摄影棚光",
    "images": [
      {"url": "https://example.com/face.png"},
      {"url": "https://example.com/outfit.png"}
    ],
    "size": "3:4",
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `prompt` | 是 | 画面描述（也可用 `description` / `text`，服务端会归一化为 `prompt`） |
| `size` | 否 | 比例如 `16:9`、`1:1`，或像素如 `2048x2048`；高清可试 `4K` |
| `n` | 否 | 生成张数，默认 1 |
| `quality` | 否 | 画质档位，依上游模型支持 |
| `response_format` | 否 | 建议 `url`（默认） |
| `images` | 否 | 参考图数组（图生图/修图/多参考）；每项含 `b64` 或 `url` |

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
      "capability": "image_generation",
      "model_key": "ixhlink-skills-quanneng-image-banana"
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

建议间隔 2–5 秒轮询，超时可根据业务设为 3–5 分钟。

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
      "data": [
        {"url": "https://oss.example.com/banana-output.png"}
      ]
    }
  }
}
```

输出图片 URL 在 `data.result.data[].url`。

---

## 付费前置检查

调用本 Skill 前，必须检查当前 Agent 是否已安装支付能力（`weixinpay` extension）：

- ✅ **已安装**：可继续提供付费创作服务
- ❌ **未安装**：向用户提示「当前 Agent 暂不支持付费创作能力」，终止流程

## 服务与定价

| 产品ID | 服务内容 | 单价 |
|--------|----------|------|
| `ixhlink-skills-quanneng-image-banana` | 全能图片香蕉 | 0.5 元/次 |

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

{"model":"ixhlink-skills-quanneng-image-banana","capability":"image_generation","payload":{...}}
```

`amount_fen = 0` 时可跳过支付，直接调用。每笔订单按次消费，使用后不可复用。

---

## 错误处理

| HTTP | 常见原因 |
|------|----------|
| 400 | 缺少 `model`、`payload` 非法、缺少 `prompt` |
| 402 | 需付费或 X402 预下单失败 |
| 404 | 模型未启用或 `capability` 不匹配 |
| 503 | 模型站点未启用 |

任务失败时 `status = failed`，查看 `data.error_message`（已脱敏，不含上游地址或内部日志）。

---

## 质量自检

出图后快速核对：

- [ ] 画面内文字是否与 prompt 引号内原文一致、清晰可读
- [ ] 多参考图场景：主体身份/服装是否与参考一致
- [ ] 图生图：是否保留了要求不修改的部分
- [ ] 构图与 `size` 比例是否匹配用途

未通过时，在 prompt 中**加强约束**（引号标明文字、写明保留项）后重试，避免一次堆砌过多矛盾要求。
