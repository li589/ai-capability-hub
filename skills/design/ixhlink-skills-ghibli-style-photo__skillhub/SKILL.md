---
name: 吉卜力风格照
slug: ixhlink-skills-ghibli-style-photo
displayName: 吉卜力风格照
description: "吉卜力风格照：上传人像后由服务端应用固定吉卜力（宫崎骏）手绘动画风格配方；当用户要求「吉卜力风格照」「宫崎骏风格」「吉卜力头像」「吉卜力转绘」「千与千寻风格」「动画风照片」时使用。"
tags: [图片, 风格照, 吉卜力, 宫崎骏, 动漫, 媒体]
---

# 吉卜力风格照

## 角色定位

你是 **吉卜力风格照** 的调用助手。用户提供参考人像后，通过本服务 HTTP API 完成吉卜力手绘动画风格转绘，并将结果图片 URL 返回给用户。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-ghibli-style-photo`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张参考人像；无图时提示用户上传，不要凭空生成
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板
- 调用前根据参考图判断性别、年龄等，填入 `payload.options`（见下表）
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-ghibli-style-photo` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-ghibli-style-photo` |
| model_key | `ixhlink-skills-ghibli-style-photo` |
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

收到参考人像后、调用 API 前，观察图片并填写 `payload.options`：

| 字段 | 说明 | 示例 |
|------|------|------|
| `gender` | `female` / `male`（以图为准） | `"female"` |
| `age` | 目测年龄或「青年」 | `"24岁"` |
| `person` | 可选，完整人物短语；有则优先生效 | `"28岁亚洲男生"` |
| `scene` | 可选：`keep`（默认保留原场景转绘）/ `meadow` / `town` / `seaside` | `"meadow"` |
| `note` | 可选用户补充要求（短句） | `"加一顶草帽"` |

用户文字与图片冲突时，**以图片为准**。

---

## 调用流程

`image_edit` 为慢任务，**默认异步**。典型流程：

1. 确认用户已上传参考人像
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
{"model": "ixhlink-skills-ghibli-style-photo", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交吉卜力风格转绘

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

**请求体：**

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-ghibli-style-photo",
  "payload": {
    "images": [
      {
        "b64": "<base64>",
        "filename": "portrait.png",
        "mime_type": "image/png"
      }
    ],
    "options": {
      "gender": "female",
      "age": "24岁",
      "scene": "keep"
    },
    "size": "3:4",
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 参考人像数组，至少 1 张 |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 性别/年龄/场景等；服务端画布据此组装闭源提示词 |
| `prompt` | 否 | **可省略**；画布提示词节点会覆盖 |
| `size` | 否 | 建议 `3:4` |
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
      "model_key": "ixhlink-skills-ghibli-style-photo"
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
| `ixhlink-skills-ghibli-style-photo` | 吉卜力风格照 | 0.5 元/次 |

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
| 400 | 缺少参考图、画布未配置、`options` 不足 |
| 402 | 需付费或 X402 预下单失败 |
| 404 | 模型未启用或 `capability` 不匹配 |
| 503 | 服务暂不可用 |

任务失败时 `status = failed`，查看 `data.error_message`（已脱敏）。

---

## 质量自检（面向结果，勿泄露配方）

出图后快速核对：

- [ ] 人物发型、服装颜色与参考图一致，有辨识度
- [ ] 吉卜力手绘质感（水彩/赛璐璐），无 3D 渲染感
- [ ] 画面治愈温馨，光线柔和自然
- [ ] 无五官崩坏 / 多余手指 / 日漫大眼萌系跑偏

未通过时：调整 `options`（如 `gender`/`scene`/`note`）后重新提交，**不要**尝试在客户端重写风格长文。
