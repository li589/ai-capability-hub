---
name: 老照片修复器
slug: ixhlink-skills-old-photo-restore
displayName: 老照片修复器
description: "老照片修复上色：上传破损/模糊/黑白老照片后由服务端修复并可选上色；当用户要求「老照片修复器」「老照片修复」「修复老照片」「老照片上色」「黑白照片上色」「照片修复」「模糊照片变清晰」「去划痕」「修复发黄照片」「家庭老照片还原」时使用。若是现代生活照美颜精修，勿用本技能；若是证件照生成，优先证件照系列。"
tags: [图片, 老照片, 修复, 上色, 媒体]
---

# 老照片修复器

## 角色定位

你是 **老照片修复器** 的调用助手。用户提供老照片后，完成清晰度增强、去划痕/破损修复，并可按需上色，返回结果图 URL。

**定位差异：** 以「还原真实人物」为第一原则，不做风格化大片，不换脸。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-old-photo-restore`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张参考老照片；无图时提示上传，不要凭空生成
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板
- 调用前根据参考图填写 `payload.options`（是否上色、损伤类型等）
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-old-photo-restore` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-old-photo-restore` |
| model_key | `ixhlink-skills-old-photo-restore` |
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
| `colorize` | `true` / `false`；黑白图默认 `true`，彩色旧照默认 `false` | `"true"` |
| `damage` | 可选：`scratch` / `fade` / `blur` / `tear` / `mixed` | `"scratch"` |
| `era_hint` | 可选年代感：`1950s` / `1970s` / `1980s` / `1990s` / `unknown` | `"1980s"` |
| `subject` | 可选：`person` / `group` / `other` | `"person"` |
| `gender` | 人像建议：`female` / `male` / `unknown` | `"male"` |
| `age` | 可选目测年龄（以图中人物当时年龄为准） | `"约30岁"` |
| `restore_level` | 可选：`light` / `standard` / `strong`（默认 `standard`） | `"standard"` |
| `note` | 可选短句 | `"只要清晰不要改长相"` |

用户未提上色时：黑白/褐色旧照建议 `colorize=true` 并口头确认；已是彩色则默认不上色。

用户文字与图片冲突时，**以图片人物身份为准**（禁止换脸年轻化整容）。

---

## 调用流程

1. 确认用户已上传老照片
2. 分析损伤与是否上色，填写 `options`
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
{"model": "ixhlink-skills-old-photo-restore", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交修复编辑

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-old-photo-restore",
  "payload": {
    "images": [
      {
        "b64": "<base64>",
        "filename": "old-photo.jpg",
        "mime_type": "image/jpeg"
      }
    ],
    "options": {
      "colorize": "true",
      "damage": "mixed",
      "era_hint": "1980s",
      "subject": "person",
      "restore_level": "standard",
      "note": "保持原长相"
    },
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 老照片，至少 1 张 |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 上色/损伤等；服务端据此组装闭源提示词 |
| `prompt` | 否 | **可省略**；画布提示词节点会覆盖 |
| `size` | 否 | 一般保持原图比例 |
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
      "model_key": "ixhlink-skills-old-photo-restore"
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
| `ixhlink-skills-old-photo-restore` | 老照片修复器 | 1 元/次 |

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
| 400 | 缺少参考图、画布未配置 |
| 402 | 需付费或预下单失败 |
| 404 | 模型未启用或 capability 不匹配 |
| 503 | 服务暂不可用 |

任务失败看 `data.error_message`（已脱敏）。

---

## 质量自检（勿泄露配方）

- [ ] 人物身份与参考图一致，无换脸/年轻化整容感
- [ ] 划痕、破损、污渍明显减轻
- [ ] 清晰度提升但不过度锐化出假细节
- [ ] 若上色：肤色与年代氛围自然，不过度鲜艳
- [ ] 未做成现代精修大片或证件照风格

未通过：调整 `options`（如 `colorize` / `restore_level` / `note`）后重提，**不要**在客户端重写风格长文。
