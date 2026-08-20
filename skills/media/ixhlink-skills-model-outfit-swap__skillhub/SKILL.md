---
name: 智绘模特换衣
slug: ixhlink-skills-model-outfit-swap
displayName: 智绘模特换衣
description: "智绘模特换衣：上传模特图 + 服装图两张参考图，由服务端应用固定换装配方完成 AI 虚拟试穿；当用户要求「模特换衣」「模特换装」「虚拟试穿」「AI 试穿」「给模特换衣服」「服装上身效果」「一键换装」「平铺图上身」「服装上身图」时使用。"
tags: [图片, 电商, 服装, 模特, 换衣, 媒体]
---

# 智绘模特换衣

## 角色定位

你是 **智绘模特换衣** 的调用助手。用户提供模特图与服装图后，通过本服务 HTTP API 完成虚拟试穿换装，并将结果图片 URL 返回给用户。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-model-outfit-swap`，`capability` 固定为 `image_edit`
- 用户**必须**提供 2 张参考图：**第 1 张模特图、第 2 张服装图**（顺序固定）；缺图时提示用户补齐，不要凭空生成
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板
- 调用前根据参考图判断模特性别、年龄等，填入 `payload.options`（见下表）
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-model-outfit-swap` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-model-outfit-swap` |
| model_key | `ixhlink-skills-model-outfit-swap` |
| capability | `image_edit` |
| execution_mode | `workflow`（技能画布） |

## 服务地址

Base URL：`https://iskills.ixhlink.com`

下文接口均写路径，完整地址 = Base URL + 路径。

统一响应格式：

```json
{"success": true, "code": 0, "message": "ok", "data": {}}
```

## 参考图分析（写入 options，勿拼风格全文）

收到 2 张参考图后、调用 API 前，观察图片并填写 `payload.options`：

| 字段 | 说明 | 示例 |
|------|------|------|
| `gender` | `female` / `male`（以模特图为准） | `"female"` |
| `age` | 目测年龄或「青年」 | `"24岁"` |
| `person` | 可选，完整模特短语；有则优先生效 | `"28岁亚洲男生"` |
| `garment` | 可选，服装描述短词（辅助识别，勿替代第 2 张图） | `"米色针织开衫"` |
| `scene` | 可选：`keep`（默认保留模特图背景）/ `studio`（影棚纯色底） | `"keep"` |
| `pose` | 可选：`keep`（默认保持模特原姿势）/ `front` / `side` | `"keep"` |
| `note` | 可选用户补充要求（短句） | `"下摆塞进裤腰"` |

用户文字与图片冲突时，**以图片为准**；服装样式一律以第 2 张服装图为准。

---

## 调用流程

`image_edit` 为慢任务，**默认异步**。典型流程：

1. 确认用户已上传**模特图 + 服装图**两张参考图
2. 分析参考图，填写 `options.gender` / `options.age` 等
3. `POST /api/v1/llm/invoke`（**无需**也不应提交完整风格 prompt）
4. 若返回 402：调起微信支付，成功后用**相同 JSON body** 重试
5. 轮询 `GET /api/v1/llm/tasks/{task_id}` 直至 `succeeded`
6. 从 `data.result.data[].url` 取图返回用户

也可直接用 `POST /api/v1/llm/tasks` 创建异步任务。

---

### 1. 查询模型（可选）

```http
GET /api/v1/llm/models
Accept: application/json
```

确认返回的 `items` 中包含：

```json
{"model": "ixhlink-skills-model-outfit-swap", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交模特换衣

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

**请求体：**

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-model-outfit-swap",
  "payload": {
    "images": [
      {
        "b64": "<base64>",
        "filename": "model.png",
        "mime_type": "image/png"
      },
      {
        "b64": "<base64>",
        "filename": "garment.png",
        "mime_type": "image/png"
      }
    ],
    "options": {
      "gender": "female",
      "age": "24岁",
      "scene": "keep",
      "pose": "keep"
    },
    "size": "3:4",
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 固定 2 张：`images[0]` 模特图、`images[1]` 服装图，**顺序不可颠倒** |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 性别/年龄/场景等；服务端画布据此组装闭源提示词 |
| `prompt` | 否 | **可省略**；画布提示词节点会覆盖 |
| `size` | 否 | 建议 `3:4`（全身构图） |
| `response_format` | 否 | 建议 `url` |

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
      "capability": "image_edit",
      "model_key": "ixhlink-skills-model-outfit-swap"
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

建议间隔 2–5 秒轮询，超时可根据业务设为 3–5 分钟。输出图片 URL 在 `data.result.data[].url`。

---

## 付费前置检查

调用本 Skill 前，必须检查当前 Agent 是否已安装支付能力（`weixinpay` extension）：

- ✅ **已安装**：可继续提供付费创作服务
- ❌ **未安装**：向用户提示「当前 Agent 暂不支持付费创作能力」，终止流程

## 服务与定价

| 产品ID | 服务内容 | 单价 |
|--------|----------|------|
| `ixhlink-skills-model-outfit-swap` | 智绘模特换衣 | 0.5 元/次 |

> 价格以 SkillHub / 管理后台配置为准。命中创作意图后，向用户展示服务名称和价格，由用户确认后进入付费流程。

## 付费说明

当 `amount_fen > 0` 且未完成支付时，首次 `POST /api/v1/llm/invoke` 会返回 HTTP 402，响应中携带：

- Header：`WeixinPay-Required: <payment_code>`、`X-Payment-Id: <payment_id>`
- Body：`WeixinPay` 对象（含 `payment_id` 等）

**客户端流程：**

```
首次 invoke → 402 → weixinpay_pay(payment_code) → 支付成功后重试 invoke
```

**「原样重试」：** JSON body 与首次完全一致；订单参数走 Header（`WeixinPay-Required`、`X-Payment-Id`）。

`amount_fen = 0` 时可跳过支付。每笔订单按次消费，使用后不可复用。

---

## 错误处理

| HTTP | 常见原因 |
|------|----------|
| 400 | 参考图不足 2 张、画布未配置、`options` 不足 |
| 402 | 需付费或 X402 预下单失败 |
| 404 | 模型未启用或 `capability` 不匹配 |
| 503 | 服务暂不可用 |

任务失败时 `status = failed`，查看 `data.error_message`（已脱敏）。

---

## 质量自检（面向结果，勿泄露配方）

出图后快速核对：

- [ ] 模特五官、发型、姿势与第 1 张参考图一致，无换人感
- [ ] 服装版型、颜色、图案与第 2 张服装图一致
- [ ] 服装贴合身形，褶皱与光影自然
- [ ] 无明显换装拼接感 / 多余手指 / 塑料感皮肤

未通过时：调整 `options`（如 `garment`/`pose`/`note`）后重新提交，**不要**尝试在客户端重写风格长文。
