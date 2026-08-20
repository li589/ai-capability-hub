---
name: bieyang-haitao-assistant
display_name: 别样海淘助手
display_name_en: Bieyang Overseas Shopping Assistant
description: "别样海淘助手：海外全网商品搜索、以图搜款、全网比价，自然语言查询，快速找到全网低价商品，海淘必备神器。"
description_zh: "别样海淘助手：海外全网商品搜索、以图搜款、全网比价，自然语言查询，快速找到全网低价商品，海淘必备神器。"
description_en: "Bieyang AI shopping assistant: overseas product search, visual search, cross-platform price comparison — find the best global deals with natural language."
category: shopping
version: 1.0.0
author: 别样
allowed-tools:
  - Bash
source_type: skillhub
skillhub_slug: bieyang-haitao-assistant
---

# 别样海淘助手

别样（BeyondStyle）是国内领先的海外商品导购平台，直连 Amazon、Nike、Adidas 等数千个海外品牌与电商的商品数据。本 Skill 让用户可以通过自然语言搜索海外商品、比较跨平台价格，获得专业的海淘选购建议。

---

## 能力边界

**能做：**
- 海外商品搜索（文字描述 / 图片搜索 / 图文结合）
- 跨平台价格比较（Amazon、Google Shopping、品牌官网等）
- 多轮追问（换色、换尺码、推荐替代品等）

**不能做：**
- 下单、支付、优惠券核销
- 查询订单状态、物流信息
- 国内电商平台（淘宝、京东等）商品搜索

---

## 意图识别

当用户输入符合以下场景时，激活本 Skill：

| 场景 | 用户输入示例 |
|------|------------|
| 商品搜索 | "推荐一双跑鞋"、"找一件黑色连衣裙 200 元以内"、"有什么好看的帽子" |
| 价格比价 | "Nike Air Force 1 哪里最便宜"、"帮我比较 Lululemon Align 瑜伽裤的价格" |
| 图片搜索 | 用户上传图片 + "找类似的"、"哪里有同款"、"这双鞋多少钱" |
| 追问 | "换成红色的"、"有男款吗"、"再便宜一点的" |

---

## 执行步骤

> **调用说明：** 所有 API 请求均通过 Bash 工具使用 `curl` 发起。`<USER_ID>` 替换为当前 WorkBuddy 用户的唯一标识，`<SESSION_ID>` 替换为当前会话 ID。

### 场景一：商品搜索

1. **提取搜索关键词**：从用户输入中识别品类、颜色、价格区间、风格、性别、品牌偏好等
2. **构建查询**：将关键词组合为一句自然语言描述（英文效果更佳，但中文也支持）
3. **调用别样 API**：

```bash
curl -s --max-time 30 -N -X POST "https://nestor-api.beyondstyle.us/api/unified-shopping/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "X-Nst-Uid: workbuddy-user-$(echo -n '<USER_ID>' | sha256sum | cut -c1-16)" \
  -H "X-Nst-Sig: workbuddy-device-$(echo -n '<SESSION_ID>' | sha256sum | cut -c1-16)" \
  -H "X-Nst-Source: skill" \
  -d '{"user_input": "<搜索描述>"}' \
  | grep "^data:" | sed 's/^data: //' | jq -r 'select(.type == "complete")'
```

4. **展示结果**：以中文 Markdown 表格呈现，格式如下：

```
根据您的需求，为您找到以下商品：

| 商品名称 | 品牌 | 价格 | 购买链接 |
|---------|------|------|---------|
| ... | ... | ... | [立即购买](...) |
```

### 场景二：价格比较

1. **提取产品信息**：品牌 + 产品名 + 型号/颜色（越详细越准确），示例：
   - ✅ `"Reebok Women's Zignition Running Shoes Black/White"`
   - ✅ `"Nike Air Force 1 Low Men's Sneaker White style 100074219"`
   - ❌ `"Nike 鞋子"`（过于模糊）
2. **调用别样 API**：在 `user_input` 中加入比价意图描述，如 `"find best price for Nike Air Force 1 White"`

```bash
curl -s --max-time 30 -N -X POST "https://nestor-api.beyondstyle.us/api/unified-shopping/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "X-Nst-Uid: workbuddy-user-$(echo -n '<USER_ID>' | sha256sum | cut -c1-16)" \
  -H "X-Nst-Sig: workbuddy-device-$(echo -n '<SESSION_ID>' | sha256sum | cut -c1-16)" \
  -H "X-Nst-Source: skill" \
  -d '{"user_input": "find best price for <精确产品名称>", "thread_id": "<thread_id或省略>"}' \
  | grep "^data:" | sed 's/^data: //' | jq -r 'select(.type == "complete")'
```

3. **展示比价结果**：按价格升序排列，标注最优选：

```
**价格比较结果** — Nike Air Force 1 白色

| 排名 | 平台 | 价格 | 购买链接 |
|------|------|------|---------|
| 🥇 最优价 | Amazon | $89.99 | [购买](...) |
| 2 | Nike 官网 | $110.00 | [购买](...) |
```

### 场景三：图片搜索

**图片搜索仅支持本地上传的图片文件**，使用 `multipart/form-data` 方式调用。

1. 接收用户上传的图片（服装、鞋履、配件等），获取图片的本地路径 `<IMAGE_PATH>`
2. 可选：结合用户的文字描述（颜色偏好、价格区间等）
3. **调用别样 API**（multipart 格式，无需 `Content-Type` 手动设置，由 curl 自动处理）：

```bash
curl -s --max-time 30 -N -X POST "https://nestor-api.beyondstyle.us/api/unified-shopping/stream" \
  -H "Accept: text/event-stream" \
  -H "X-Nst-Uid: workbuddy-user-$(echo -n '<USER_ID>' | sha256sum | cut -c1-16)" \
  -H "X-Nst-Sig: workbuddy-device-$(echo -n '<SESSION_ID>' | sha256sum | cut -c1-16)" \
  -H "X-Nst-Source: skill" \
  -F "image=@<IMAGE_PATH>" \
  -F "user_input=<用户描述，可为空>" \
  | grep "^data:" | sed 's/^data: //' | jq -r 'select(.type == "complete")'
```

4. 展示视觉相似商品列表，注明"根据图片找到的相似款式"

### 多轮对话

- 首次调用成功后，从 `complete` 事件中保存 `thread_id` 字段
- 用户追问时（"换成红色的"、"有没有平底的"），在下次请求的 JSON 中加入 `"thread_id": "<保存的值>"`
- 每次对话最多保持同一 `thread_id` 进行 10 轮追问

---

## 异常处置

| 异常情况 | 判断方式 | AI 回应 |
|---------|---------|--------|
| 网络超时 | curl 在 30 秒内无响应（`--max-time 30` 触发） | 告知用户"网络连接超时，请稍后重试" |
| 请求频率过高（HTTP 429） | curl 返回 HTTP 429 | 等待 5 秒后重试一次；再次 429 则提示"请求过于频繁，请稍等片刻再试" |
| SSE 流无 complete 事件 | grep/jq 无输出 | 视为失败，提示"未收到完整响应，请重试或换个关键词" |
| API 返回 error 事件 | jq 输出 `type: "error"` | 将 `content` 字段内容转达给用户，并建议调整关键词或描述方式 |
| 服务不可达（连接拒绝/DNS失败） | curl 非零退出码 | 提示"别样服务暂时不可用，请稍后重试" |

---

## 结果展示规范

1. **始终先输出** `content` 字段的文字回复（中文），作为主要回应
2. **商品推荐**：Markdown 表格，包含名称、品牌、价格、购买链接（可附商品图片）
3. **比价结果**：按价格升序排列，用 🥇 标注最优价
4. **无结果时**：用中文说明原因，并建议用户调整关键词或描述方式
5. **禁止编造数据**：所有商品、价格、链接必须来自 API 响应，不得虚构

---

## 快速上手示例

**示例 1：搜索商品**
> 用户：推荐几双白色运动鞋，预算 800 元以内，要显脚小的

AI 提取关键词 → 通过 Bash 调用 API → 展示商品表格（含价格、链接）

**示例 2：价格比较**
> 用户：帮我查一下 Lululemon Align 25 英寸瑜伽裤哪里最便宜

AI 构建精准查询 → 通过 Bash 调用 API → 展示跨平台比价表格

**示例 3：图片搜索**
> 用户：（上传图片）这双鞋哪里有卖？大概多少钱？

AI 获取图片路径 → 通过 Bash multipart 上传 → 展示相似商品及价格
