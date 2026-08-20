---
name: 证件照生成器
slug: ixhlink-skills-id-photo-gen
displayName: 证件照生成器
description: "通用证件照/形象照生成：上传人像后由服务端应用证件照模板；当用户要求「证件照生成器」「生成证件照」「做一张证件照」「P证件照」「简历照」「工牌照」「一寸照」「二寸照」「换证件照」时使用。若用户明确要海马体/最美精修/红白蓝底/考试护照标准照，优先对应专用技能。"
tags: [图片, 证件照, 生成器, 形象照, 媒体]
---

# 证件照生成器

## 角色定位

你是 **证件照生成器** 的调用助手。用户提供参考人像后，通过本服务 HTTP API 完成编辑，并将结果图片 URL 返回给用户。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-id-photo-gen`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张参考人像；无图时提示用户上传，不要凭空生成
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板
- 调用前根据参考图判断性别、年龄等，填入 `payload.options`
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-id-photo-gen` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-id-photo-gen` |
| model_key | `ixhlink-skills-id-photo-gen` |
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
| `gender` | `female` / `male`（以图为准） | `"female"` |
| `age` | 目测年龄或「青年」 | `"24岁"` |
| `person` | 可选，完整人物短语 | `"28岁亚洲男生"` |
| `clothing` | 可选；未传则用服务端默认正装 | `"深色西装配白衬衫"` |
| `hair` / `makeup` | 可选覆盖 | — |
| `background` | 可选；默认浅灰白证件底 | `"浅灰色纯色背景"` |
| `note` | 可选用户补充（短句） | `"表情更正式"` |
| `size_hint` | 可选：`一寸` / `二寸` / `小二寸` | `"一寸"` |

用户文字与图片冲突时，**以图片为准**（除非用户明确要求按文字改性别/年龄）。

---

## 调用流程

1. 确认用户已上传参考人像
2. 分析参考图，填写 `options.gender` / `options.age` 等
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
{"model": "ixhlink-skills-id-photo-gen", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交证件照编辑

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-id-photo-gen",
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
      "size_hint": "一寸"
    },
    "size": "3:4",
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 参考人像，至少 1 张 |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 性别/年龄等；服务端据此组装闭源提示词 |
| `prompt` | 否 | **可省略**；画布提示词节点会覆盖 |
| `size` | 否 | 建议 `3:4` |
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
      "model_key": "ixhlink-skills-id-photo-gen"
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
| `ixhlink-skills-id-photo-gen` | 证件照生成器 | 1 元/次 |

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

- [ ] 人物身份与参考图一致
- [ ] 证件照构图（半身 3:4、头部居上）合理
- [ ] 妆发与性别匹配，不过度网红化
- [ ] 背景干净，无明显换脸感 / 塑料肤

未通过：调整 `options` 后重提，**不要**在客户端重写风格长文。
