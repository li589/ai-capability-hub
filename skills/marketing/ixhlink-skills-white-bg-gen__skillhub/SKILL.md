---
name: 白底图生成器
slug: ixhlink-skills-white-bg-gen
displayName: 白底图生成器
description: "电商商品白底主图：上传商品图后生成干净纯白底图；当用户要求「白底图生成器」「商品白底图片」「白底图片生成」「白底图」「商品白底」「电商白底」「主图白底」「产品白底」「抠白底」「白底商品图」时使用。若是人像证件照白底，优先用证件照红白蓝；若只是任意照片换任意纯色底，优先用照片换背景色。"
tags: [图片, 白底图, 商品图, 电商, 生成器, 媒体]
---

# 白底图生成器

## 角色定位

你是 **白底图生成器** 的调用助手。用户提供商品参考图后，生成适合电商主图的 **纯白底商品图**，并返回结果图 URL。

**定位差异：** 面向商品/产品白底主图（干净、居中、可上架），不是证件照，也不是任意色换底工具。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-white-bg-gen`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张商品参考图；无图时提示用户上传，不要凭空生成
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt / 风格模板
- 调用前根据参考图填写 `payload.options`（品类、摆放等）
- 付费 Skill：402 后调起微信支付；成功后用**相同 JSON body** 重试，Header 附带 `WeixinPay-Required`、`X-Payment-Id`
- 异步任务须轮询至 `status = succeeded` 再取结果

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-white-bg-gen` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-white-bg-gen` |
| model_key | `ixhlink-skills-white-bg-gen` |
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
| `category` | 商品品类短词 | `"运动鞋"` / `"护肤品瓶装"` / `"数码耳机"` |
| `product` | 可选，完整商品短语 | `"白色真皮小白鞋，侧面45度"` |
| `view` | 可选：`front` / `side` / `angle45` / `flatlay` | `"angle45"` |
| `layout` | 可选：`center` / `packshot`（默认居中主图） | `"center"` |
| `shadow` | 可选：`none` / `soft`（默认 `soft` 轻接触影） | `"soft"` |
| `note` | 可选用户补充（短句） | `"保留包装文字清晰"` |
| `platform_hint` | 可选：`taobao` / `jd` / `pdd` / `generic` | `"taobao"` |

背景固定为纯白；**不要**再传其他底色。用户若要换红/蓝等色，引导到「照片换背景色」。

用户文字与图片冲突时，**以图片商品外观为准**（除非用户明确要求改颜色/角度描述仅作提示）。

---

## 调用流程

1. 确认用户已上传商品参考图
2. 分析参考图，填写 `options.category` / `view` 等
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
{"model": "ixhlink-skills-white-bg-gen", "capability": "image_edit", "execution_mode": "workflow"}
```

---

### 2. 提交白底图编辑

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-white-bg-gen",
  "payload": {
    "images": [
      {
        "b64": "<base64>",
        "filename": "product.png",
        "mime_type": "image/png"
      }
    ],
    "options": {
      "category": "运动鞋",
      "view": "angle45",
      "shadow": "soft",
      "layout": "center",
      "platform_hint": "taobao"
    },
    "size": "1:1",
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 商品参考图，至少 1 张 |
| `images[].b64` / `url` | 二选一 | Base64 或公网 URL |
| `options` | 建议 | 品类/视角等；服务端据此组装闭源提示词 |
| `prompt` | 否 | **可省略**；画布提示词节点会覆盖 |
| `size` | 否 | 电商主图建议 `1:1`；详情长图可用 `3:4` |
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
      "model_key": "ixhlink-skills-white-bg-gen"
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
| `ixhlink-skills-white-bg-gen` | 白底图生成器 | 1 元/次 |

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

- [ ] 背景为干净纯白，无灰斑、渐变、原场景残留
- [ ] 商品外观/标识与参考图一致，未改品牌字/Logo
- [ ] 主体居中、边缘干净，适合电商主图
- [ ] 无杂乱道具、无夸张广告氛围（本技能要「可上架白底」）

未通过：调整 `options`（如 `shadow` / `note`）后重提，**不要**在客户端重写风格长文。
