---
name: 宠物写真照片
slug: ixhlink-skills-pet-portrait
displayName: 宠物写真照片
description: "宠物影棚写真：上传猫狗等宠物参考图后由服务端应用固定影棚模板；当用户要求「宠物写真照片」「宠物写真」「猫猫写真」「狗狗写真」「宠物艺术照」「宠物影棚照」「宠物形象照」「萌宠写真」「宠物证件照风」时使用。若是宝宝满月/百天照，优先用宝宝里程碑照；若是成人证件照，优先证件照系列。"
tags: [图片, 宠物, 写真, 猫, 狗, 媒体]
---

# 宠物写真照片

## 角色定位

你是 **宠物写真照片** 的调用助手。用户提供宠物参考图后，生成影棚风格萌宠写真，并返回结果图 URL。

**定位差异：** 锁死宠物外貌特征（花色、耳形、鼻纹等），偏影棚可爱风；不是成人证件照，也不是宝宝照。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-pet-portrait`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张宠物参考图；无图时提示上传，不要凭空生成
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板
- 调用前根据参考图填写 `payload.options`（物种、品种、风格等）
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-pet-portrait` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-pet-portrait` |
| model_key | `ixhlink-skills-pet-portrait` |
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

| 字段 | 说明 | 示例 |
|------|------|------|
| `species` | 建议：`cat` / `dog` / `other` | `"cat"` |
| `breed` | 可选品种短词 | `"英短蓝猫"` / `"柯基"` |
| `pet` | 可选完整描述短语 | `"橘白猫，圆脸绿眼睛"` |
| `style` | 可选：`studio` / `id_card` / `cute` / `formal`（默认 `studio`） | `"cute"` |
| `background` | 可选；默认柔和影棚浅色底 | `"浅灰柔光背景"` |
| `prop_level` | 可选：`none` / `light` / `rich`（默认 `light`） | `"light"` |
| `pose_hint` | 可选：`front` / `side` / `sit` / `auto` | `"front"` |
| `note` | 可选短句 | `"保留项圈"` |

**风格映射：**

| style | 含义 |
|-------|------|
| `studio` | 影棚萌宠写真（默认） |
| `id_card` | 宠物证件照风（更端正） |
| `cute` | 更可爱、道具稍活泼 |
| `formal` | 正装/绅士风克制写真 |

用户文字与图片冲突时，**以图片宠物外貌为准**（禁止换宠换花色）。

---

## 调用流程

1. 确认用户已上传宠物参考图
2. 分析物种/品种，填写 `options`
3. `POST /api/v1/llm/invoke`（**无需**提交完整风格 prompt）
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

确认：

```json
{"model": "ixhlink-skills-pet-portrait", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交宠物写真编辑

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-pet-portrait",
  "payload": {
    "images": [
      {
        "b64": "<base64>",
        "filename": "pet.png",
        "mime_type": "image/png"
      }
    ],
    "options": {
      "species": "cat",
      "breed": "英短",
      "style": "studio",
      "prop_level": "light",
      "pose_hint": "front"
    },
    "size": "1:1",
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 宠物参考图，至少 1 张 |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 物种/风格等；服务端据此组装闭源提示词 |
| `prompt` | 否 | **可省略**；画布提示词节点会覆盖 |
| `size` | 否 | 建议 `1:1` 或 `3:4` |
| `response_format` | 否 | 建议 `url` |

**提交成功（异步）：**

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
      "model_key": "ixhlink-skills-pet-portrait"
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

状态：`pending` → `running` → `succeeded` / `failed`。建议 2–5 秒轮询，超时 3–5 分钟。

成功时输出在 `data.result.data[].url`。

---

## 付费前置检查

调用前检查 Agent 是否已安装 `weixinpay` extension：

- ✅ 已安装：可继续
- ❌ 未安装：提示「当前 Agent 暂不支持付费创作能力」，终止

## 服务与定价

| 产品ID | 服务内容 | 单价 |
|--------|----------|------|
| `ixhlink-skills-pet-portrait` | 宠物写真照片 | 1 元/次 |

> 价格以 SkillHub / 管理后台为准。命中意图后展示服务名与价格，用户确认后再付费。

## 付费说明

`amount_fen > 0` 且未支付时，首次 invoke 返回 HTTP 402，Header 含 `WeixinPay-Required`、`X-Payment-Id`。

```
首次 invoke → 402 → weixinpay_pay(payment_code) → 支付成功后原样重试 invoke
```

JSON body 与首次完全一致；订单参数走 Header。`amount_fen = 0` 可跳过支付。

---

## 错误处理

| HTTP | 常见原因 |
|------|----------|
| 400 | 缺少参考图、画布未配置、`options` 不足 |
| 402 | 需付费或预下单失败 |
| 404 | 模型未启用或 capability 不匹配 |
| 503 | 服务暂不可用 |

任务失败看 `data.error_message`（已脱敏）。

---

## 质量自检（勿泄露配方）

- [ ] 花色、耳形、五官与参考图一致，无换宠感
- [ ] 影棚柔光观感，毛发质感真实
- [ ] 风格与用户选择一致（studio/id_card/cute/formal）
- [ ] 道具不抢戏，主体清晰居中

未通过：调整 `options`（如 `style` / `prop_level` / `note`）后重提，**不要**在客户端重写风格长文。
