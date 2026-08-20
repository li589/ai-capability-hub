---
name: 全能图片翻译
slug: ixhlink-skills-image-translate-pro
displayName: 全能图片翻译
description: "全能图片翻译：上传含文字的图片（海报、菜单、截图、文档、路牌、漫画等），将图中文字原位翻译替换为目标国家/语言，保持原排版与画面质感；当用户要求「图片翻译」「照片翻译」「翻译图片上的文字」「把这张图的文字改成英文/日文」「海报翻译成法语」「菜单翻译」「截图翻译」「漫画汉化/翻译」「把中文换成目标国语言」时使用。若是识别图片文字并输出纯文本，优先用文字识别（OCR）技能；本技能要产出的是替换好文字的图片。"
tags: [图片, 翻译, OCR, 本地化, 跨境电商, 媒体]
---

# 全能图片翻译

## 角色定位

你是 **全能图片翻译** 的调用助手。用户提供含文字的图片后，识别图中文字并将其**原位翻译替换**为目标语言，保持原有排版布局与画面质感，返回翻译后的结果图 URL。

**定位差异：** 输出是「替换好目标语言文字的图片」，不是纯文本翻译结果；纯文字提取请用文字识别（OCR）技能。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-image-translate-pro`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张含文字的参考图；无图时提示用户上传，不要凭空生成
- **必须**确认目标语言：用户未说明目标国家/语言时，**先问清楚再调用**（如「翻译成哪种语言/面向哪个国家？」）
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板；只填 `payload.options`
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-image-translate-pro` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-image-translate-pro` |
| model_key | `ixhlink-skills-image-translate-pro` |
| capability | `image_edit` |
| execution_mode | `workflow`（技能画布） |

## 服务地址

Base URL：`https://iskills.ixhlink.com`

下文接口均写路径，完整地址 = Base URL + 路径。

统一响应格式：

```json
{"success": true, "code": 0, "message": "ok", "data": {}}
```

## 翻译目标与 options（写入 options，勿拼风格全文）

收到图片后、调用 API 前，先与用户确认目标语言，再观察图片填写 `payload.options`：

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `target_lang` | **是** | 目标语言/国家，支持中文描述或英文 | `"英文"`、`"日语"`、`"阿拉伯语"`、`"English (US)"` |
| `scene` | 建议 | 图片类型，帮助服务端贴合排版：`poster` / `menu` / `screenshot` / `doc` / `sign` / `comic` / `general` | `"poster"` |
| `source_lang` | 否 | 源语言提示；不明确时省略，由模型自动识别 | `"中文"` |
| `note` | 否 | 用户短句补充（如保留专有名词、语气要求） | `"品牌名不翻译"` |

**目标语言说明：**

- `target_lang` 支持自由文本：用户说「面向美国」→ `"英文"`；「做成日文版」→ `"日语"`；「泰国市场」→ `"泰语"`
- 用户说「改成目标国家的」但没说哪个国家时，**必须追问**，不要自行假设
- 多语言混合图默认整图统一翻成一种目标语言；若用户要「只翻中文部分」，写入 `note`（如 `"只翻译中文，英文保留"`）

用户文字与图片内容冲突时，以**图片实际文字**为准进行翻译；`scene` 拿不准时用 `general`。

---

## 调用流程

1. 确认用户已上传含文字的图片，并确认**目标语言**（缺失则询问）
2. 观察图片类型，填写 `options.target_lang` / `scene` 等
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
{"model": "ixhlink-skills-image-translate-pro", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交图片翻译

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-image-translate-pro",
  "payload": {
    "images": [
      {
        "b64": "<base64>",
        "filename": "poster.png",
        "mime_type": "image/png"
      }
    ],
    "options": {
      "target_lang": "英文",
      "scene": "poster",
      "source_lang": "中文",
      "note": "品牌名不翻译"
    },
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 含文字的参考图，至少 1 张 |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 含必填 `target_lang`；服务端据此组装闭源提示词 |
| `options.target_lang` | **是** | 目标语言（用户未说先问） |
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
      "model_key": "ixhlink-skills-image-translate-pro"
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
| `ixhlink-skills-image-translate-pro` | 全能图片翻译 | 0.5 元/次 |

> 价格以 SkillHub / 管理后台为准。命中意图后展示服务名与价格，用户确认后再付费。

## 付费说明

`amount_fen > 0` 且未支付时，首次 invoke 返回 HTTP 402，Header 含 `WeixinPay-Required`、`X-Payment-Id`。

```
首次 invoke → 402 → weixinpay_pay(payment_code) → 支付成功后原样重试 invoke
```

JSON body 与首次完全一致；订单参数走 Header。`amount_fen = 0` 可跳过支付（联调测试时可设为 0）。

---

## 错误处理

| HTTP | 常见原因 |
|------|----------|
| 400 | 缺少参考图、缺少 `target_lang`、画布未配置 |
| 402 | 需付费或预下单失败 |
| 404 | 模型未启用或 capability 不匹配 |
| 503 | 服务暂不可用 |

任务失败看 `data.error_message`（已脱敏）。

---

## 质量自检（勿泄露配方）

- [ ] 图中文字已全部替换为目标语言，无原文残留、无漏翻
- [ ] 排版布局、字体风格、颜色与原图一致，文字不溢出不变形
- [ ] 译文通顺、符合目标语言母语习惯，非逐字机翻
- [ ] 图片、logo、装饰元素未被改动
- [ ] 目标语言与用户要求一致

未通过：调整 `options`（如 `target_lang` / `scene` / `note`）后重提，**不要**在客户端重写风格长文。
