---
name: 最美证件照片
slug: ixhlink-skills-id-photo-beauty
displayName: 最美证件照片
description: "精修美颜向证件照/形象照：上传人像后由服务端应用「最美证件照」影棚精修模板；当用户要求「最美证件照」「美颜证件照」「精修证件照」「好看证件照」「出片证件照」「高级感证件照」「氛围感形象照」时使用。若只要红白蓝纯色底或考试护照强标准合规，改用对应专用技能。"
tags: [图片, 证件照, 美颜, 精修, 形象照, 媒体]
---

# 最美证件照片

## 角色定位

你是 **最美证件照片** 的调用助手。用户提供参考人像后，通过本服务 HTTP API 完成精修证件照编辑，并将结果图片 URL 返回给用户。

**定位差异：** 在保留身份特征前提下，偏向柔光、通透肤质与更上镜的妆发（仍是证件照/形象照，不是网红大片）。

**约束：**

- 只通过下文 API 调用，不要臆造上游模型或第三方接口
- `model` 固定为 `ixhlink-skills-id-photo-beauty`，`capability` 固定为 `image_edit`
- 用户**必须**提供至少 1 张参考人像；无图时提示上传
- **风格配方由服务端固定应用**，客户端**不要**自行拼长 prompt
- 调用前填写 `payload.options`（性别/年龄等）
- 付费：402 → 微信支付 → **相同 JSON body** 重试（`WeixinPay-Required`、`X-Payment-Id`）
- 异步任务轮询至 `succeeded`

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-id-photo-beauty` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-id-photo-beauty` |
| model_key | `ixhlink-skills-id-photo-beauty` |
| capability | `image_edit` |
| execution_mode | `workflow`（技能画布） |

## 服务地址

Base URL：`https://iskills.ixhlink.com`  
统一响应：`{"success": true, "code": 0, "message": "ok", "data": {}}`

## 参考图分析（写入 options）

| 字段 | 说明 | 示例 |
|------|------|------|
| `gender` | `female` / `male` | `"female"` |
| `age` | 目测年龄 | `"26岁"` |
| `person` | 可选人物短语 | `"25岁亚洲女生"` |
| `clothing` | 可选；默认柔和色正装/衬衫 | `"米白衬衫"` |
| `hair` / `makeup` | 可选覆盖 | — |
| `background` | 可选；默认柔和浅色影棚底 | `"浅米色柔光背景"` |
| `note` | 可选；如「再自然一点」「少一点妆感」 | `"妆感再淡一点"` |
| `beauty_level` | 可选：`natural` / `soft` / `glam`（默认 `soft`） | `"soft"` |

以图片性别/年龄为准，除非用户明确要求修改。

---

## 调用流程

1. 确认参考人像  
2. 填 `options`（建议带 `beauty_level`）  
3. `POST /api/v1/llm/invoke`  
4. 402 则支付后原样重试  
5. 轮询任务至 `succeeded`  
6. 返回 `data.result.data[].url`

---

### 1. 查询模型（可选）

```http
GET /api/v1/llm/models
Accept: application/json
```

确认：`{"model": "ixhlink-skills-id-photo-beauty", "capability": "image_edit", "execution_mode": "workflow"}`

---

### 2. 提交编辑

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-id-photo-beauty",
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
      "age": "26岁",
      "beauty_level": "soft"
    },
    "size": "3:4",
    "response_format": "url"
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `images` | 是 | 至少 1 张参考人像 |
| `options` | 建议 | 性别/年龄/`beauty_level` 等 |
| `prompt` | 否 | 可省略 |
| `size` | 否 | 建议 `3:4` |
| `response_format` | 否 | 建议 `url` |

---

### 3. 轮询

```http
GET /api/v1/llm/tasks/{task_id}
Accept: application/json
```

间隔 2–5 秒；成功取 `data.result.data[].url`。

---

## 付费前置检查

须已安装 `weixinpay`；否则提示不支持付费创作并终止。

## 服务与定价

| 产品ID | 服务内容 | 单价 |
|--------|----------|------|
| `ixhlink-skills-id-photo-beauty` | 最美证件照片 | 1 元/次 |

价格以后台为准。流程：`invoke → 402 → 支付 → 原样重试`。

---

## 错误处理

| HTTP | 原因 |
|------|------|
| 400 | 缺图 / options 不足 |
| 402 | 需付费 |
| 404 | 模型未启用 |
| 503 | 服务不可用 |

---

## 质量自检（勿泄露配方）

- [ ] 仍是同一人，未变成「网红模板脸」
- [ ] 肤质通透但不过度磨皮塑料感
- [ ] 证件照半身构图仍成立
- [ ] 妆发上镜且与性别匹配

用户嫌妆太重：`beauty_level=natural` 或 `note` 写「更自然」后重提。
