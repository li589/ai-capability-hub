---
name: wx-md2html
skill_name: Markdown转公众号HTML
description: 把 Markdown 文本转换成微信公众号可直接粘贴的 HTML（内联样式，粘贴不乱码），支持 5 套模板。默认模板免收费，其他模板 ¥0.10/次（微信支付 AI 专属卡代扣）。支持扩展卡片语法（:::tip / :::info / :::warn / :::danger / :::note / :::card），直接写在 Markdown 中即可。触发词：Markdown 转公众号、md2html、公众号排版、公众号 HTML、微信排版、公众号编辑器、Markdown 排版、公众号样式、公众号文章排版、模板排版、秀米替代、135编辑器替代、Markdown 公众号、微信文章排版、公众号代码块、公众号表格。
version: 1.0.1
author: 日舍科技
tags: [公众号, Markdown, 排版, 微信公众号, HTML转换, 内容创作, 模板]
---

# Markdown转公众号HTML（wx-md2html · Pay Skill）

## 功能描述

把用户给的 **Markdown 文本** 转换成 **微信公众号可直接使用的 HTML**：

- 自动转成内联样式（粘贴进微信编辑器不会乱）
- 支持指定 5 套模板：`default`(默认·免收费) / `tech`(暗色科技) / `warm`(温暖故事) / `business`(商务专业) / `nature`(清新自然)
- 支持扩展卡片语法（`:::tip` / `:::info` / `:::warn` / `:::danger` / `:::note` / `:::card`），直接写在 Markdown 中即可，**无需单独调用接口**
- 返回完整 HTML 字符串，由调用方保存为 `.html` 文件交给用户

**收费说明**：
- `default` 模板：**免费**，直接返回结果，不经过支付流程
- `tech` / `warm` / `business` / `nature` 模板：每次调用收费 **¥0.10**（按次计费，由微信支付 AI 专属卡代扣）

## 扩展卡片语法（直接写在 Markdown 中）

本 Skill 支持以下扩展卡片语法，**LLM 应直接在 Markdown 内容中生成这些语法块**，由 Skill 自动识别并渲染为精美卡片样式。**不要将卡片内容拆成单独的 Skill 调用**。

### 支持的卡片类型

| 类型 | 语法 | 用途 |
|------|------|------|
| `tip` | `:::tip 提示` | 通用提示（蓝色主题） |
| `info` | `:::info 说明` | 补充说明（蓝绿色主题） |
| `warn` | `:::warn 注意` | 警告提醒（橙色主题） |
| `danger` | `:::danger 危险` | 危险警示（红色主题） |
| `note` | `:::note 备注` | 附加备注（灰色主题） |
| `card` | `:::card 卡片` | 自定义卡片（使用模板默认样式） |

### 语法格式

```markdown
:::tip 标题文字
这里是卡片的内容，支持 **Markdown** 格式，
可以包含列表、代码、链接等。
:::
```

### 使用规则

1. **直接嵌入 Markdown**：卡片块直接写在 Markdown 正文中，Skill 会自动解析并渲染
2. **不要单独调用**：不要为每个卡片创建单独的 Skill 调用，应在同一次调用中完整提交
3. **卡片可嵌套**：卡片内部可以使用标准 Markdown 语法（列表、代码、引用等）
4. **标题可选**：`:::tip` 后可跟标题文字，也可省略

### 示例

```markdown
# 我的文章标题

这是正文内容。

:::tip 使用提示
这是一条有用的提示信息，帮助读者更好地理解内容。
:::

更多正文...

:::warn 注意事项
- 第一条注意事项
- 第二条注意事项
:::
```

---

## 元数据自动提炼规则

**LLM 必须在调用 Skill 前，从用户提供的 Markdown 内容中自动提炼以下元数据字段。** 若无法提炼，可省略对应字段（服务端会自动处理）。

### 提炼规则

| 字段 | 提炼方法 | 示例 |
|------|----------|------|
| `title` | 取 Markdown 第一个 `# 一级标题` 的文本；若无一级标题，根据内容生成不超过 30 字的标题 | `"Spring Boot 内存优化实战"` |
| `subtitle` | **阅读全文后生成**一句话概括文章核心观点或价值，不要仅截取首段或二级标题；长度不超过 40 字 | `"从 60% 内存降到 30%，Spring Boot 内存优化实战"` |
| `series` | 若内容属于系列文章，从上下文提取系列名；不属于系列则省略 | `"Java 性能优化系列"` |
| `intro` | **通读全文后生成**一段简短的引入性文字，涵盖文章背景、核心问题和价值；不要仅截取首段内容；长度不超过 60 字 | `"EC2 内存爆满，Spring Boot 占 5GB，本文分享完整排查与优化方案。"` |
| `reading_time` | 根据正文字数估算：中文约 300 字/分钟，英文约 200 词/分钟；向上取整到整数分钟 | `"约 5 分钟"` |
| `date` | 若用户提供了日期则使用；否则取当前日期 | `"2026-07-31"` |

### 提炼示例

假设用户提供的 Markdown：

```markdown
# Spring Boot 内存优化实战

## 从 60% 内存降到 30% 的完整方案

昨天我的 AWS EC2 服务器内存爆了，Spring Boot 进程吃掉了 5GB 内存...
（假设全文约 1500 字中文）
```

LLM 应**通读全文后**自动提炼为：

```json
{
  "title": "Spring Boot 内存优化实战",
  "subtitle": "从 60% 内存降到 30%，Spring Boot 内存优化实战",
  "series": "Java 性能优化系列",
  "intro": "EC2 内存爆满，Spring Boot 占 5GB，本文分享完整排查与优化方案。",
  "reading_time": "约 5 分钟",
  "date": "2026-07-31"
}
```

> 💡 subtitle 和 intro 都是**读完全文后重新生成**的概括性文字，不是简单截取原文某一段落。

### 注意事项

1. **title 优先使用原文**：若 Markdown 中已有明确的一级标题 `#`，直接使用原文；若无则生成
2. **subtitle / intro 基于全文生成**：必须通读全文后重新提炼概括，不要仅截取首段或二级标题
3. **长度控制**：`subtitle` ≤ 40 字，`intro` ≤ 60 字，过长时截断并加省略
4. **reading_time 格式**：统一使用 `"约 N 分钟"` 格式
5. **不确定时省略**：无法合理提炼的字段（如 `series`），直接不传该字段，服务端会自动隐藏

---

## 付费前置检查

根据用户请求的模板类型，执行不同的前置检查：

### 使用默认模板（`template=default`，免费）

- **跳过支付检查**，直接进入工作流程第一步
- 无需 `weixinpay` 插件

### 使用付费模板（`tech` / `warm` / `business` / `nature`）

调用本 Skill 前，先检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- 已安装：继续
- 未安装：向用户提示"当前 Agent 暂不支持微信支付付费能力，如需使用付费模板请先安装 weixinpay 插件"，终止流程

> 💡 若用户未指定模板，默认使用 `default`（免费），无需支付能力即可使用。

## 工作流程

### 第一步：请求资源（⚠️ 中文必须用 UTF-8 文件传 body）

向商户服务发起 POST（已上线域名 <https://www.start-ai.cn）。>

> **编码铁律**：请求体含中文时，**绝不能**直接用 `curl -d '{"md":"中文..."}'`——Git Bash/部分 shell 会按 GBK 编码中文，后端收到乱码导致 HTML 错乱。**必须先把 JSON 写入 UTF-8 文件，再用 `curl -d @文件` 发送。**

正确做法（先把 body 写成 UTF-8 文件，再 curl）：

```bash
# 1. 把请求体写成 UTF-8 文件（由 Agent 用写文件工具保证 UTF-8 编码）
cat > /tmp/wxmd2html_body.json <<'EOF'
{
  "md": "用户给的 Markdown 文本",
  "template": "tech",
  "title": "可选标题（LLM 自动提炼）",
  "subtitle": "可选副标题（LLM 自动提炼）",
  "series": "可选系列名（LLM 自动提炼）",
  "intro": "可选简介（LLM 自动提炼）",
  "reading_time": "可选阅读时长（LLM 自动提炼）",
  "author": "可选作者(默认 8点虾聊AI)",
  "date": "可选日期",
  "qr_text": "可选扫码文案"
}
EOF

# 2. 用 -d @文件 发送（确保 UTF-8）
curl -s -i -X POST https://www.start-ai.cn/skillapi/skill/wx-md2html \
  -H "Content-Type: application/json; charset=utf-8" \
  -d @/tmp/wxmd2html_body.json
```

字段说明：

- `md`（必填）：要转换的 Markdown 文本
- `template`（可选，默认 default）：`default`(免费) / `tech` / `warm` / `business` / `nature`
- `title` / `subtitle` / `series` / `intro` / `reading_time` / `author` / `date` / `qr_text`（可选）：排版头部信息

> ⚠️ **LLM 自动提炼元数据**：调用前，LLM 应从用户的 Markdown 内容中自动提炼以下字段（详见下方"元数据自动提炼规则"），不需要用户手动提供。

### 第二步：处理 402 响应（仅付费模板，支付由插件完成，不要手动调）

若收到 **HTTP 402**，说明需要支付。`weixinpay` 插件会**自动拦截** `WeixinPay-Required` 并完成支付流程，**无需手动调用支付接口**。

402 响应同时通过 Header 和 Body 返回支付信息：

- Header `WeixinPay-Required`：支付凭证码（插件用于完成支付）
- Header `X-Out-Trade-No`：商户订单号
- Body 中 `WeixinPay` 块：含 `WeixinPay-Required` 与 `prompt`，兼容只读 body 的 Agent

402 响应体示例：

```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "需要支付后才能获取内容",
  "WeixinPay": {
    "WeixinPay-Required": "<支付凭证码>",
    "prompt": "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay，以向用户申请支付授权。"
  },
  "out_trade_no": "PAY_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "amount": "0.10",
  "currency": "CNY",
  "description": "公众号排版: Markdown 转公众号 HTML: ..."
}
```

> ⚠️ 支付过程由 `weixinpay` 插件处理，Skill 无需关心支付细节。**禁止**向用户展示 `WeixinPay-Required` 的原始值（它是一次性支付凭据）。**不要**轮询或臆测支付状态，等插件支付卡片回传结果。

### 第三步：支付成功后获取资源（仅付费模板，⚠️ 必须执行）

支付成功后，**必须**重新发起请求获取付费内容。重试规则：

- **JSON body 与第一步完全一致**（不要修改任何字段，同样用 UTF-8 文件）
- **通过 Header 原样带上 402 响应里的 `WeixinPay-Required` 和 `X-Out-Trade-No`**

```bash
curl -s -i -X POST https://www.start-ai.cn/skillapi/skill/wx-md2html \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "WeixinPay-Required: <payment_code>" \
  -H "X-Out-Trade-No: <out_trade_no>" \
  -d @/tmp/wxmd2html_body.json
```

> 注意：body 与第一步完全一致，不要修改 body 中的任何字段。支付信息通过 Header 传递。

### 第四步：拿到结果并交付（所有模板通用）

返回 **HTTP 200**，Body 里 `content` 字段就是转换好的公众号 HTML 字符串：

```json
{
  "code": "SUCCESS",
  "message": "付费内容",
  "out_trade_no": "PAY_xxx",
  "transaction_id": "微信支付订单号",
  "content": "<...公众号 HTML...>",
  "already_fulfilled": false
}
```

- 把 `content` 字段（公众号 HTML）保存为 `.html` 文件（如 `公众号文章.html`）
- 将 html 文件交付给用户
- **不要**把整段 HTML 贴进对话，只报告：生成的 HTML 路径 + 所用模板

### 关于默认模板（免收费）

当请求使用默认模板（`template` 为 `default` 或未指定）时：
- **不需要支付**，直接返回结果
- 响应体 `free: true` 标识为免费内容
- 无需执行第二步、第三步的支付流程

响应示例：

```json
{
  "code": "SUCCESS",
  "message": "免费内容",
  "content": "<...公众号 HTML...>",
  "free": true
}
```

### 异常处理

| 返回 code | 含义 | 处理 |
| ----------- | ------ | ------ |
| `PAYMENT_REQUIRED` (402) | 首请求需支付 | 走第二步触发支付 |
| `NOT_PAID` (402) | 支付尚未完成 | 等待几秒后按第三步重试 |
| `SUCCESS` (200) | 履约成功 | 取 `content` 交付 |
| `REFUNDED` (200) | 服务异常已退款 | 告知用户"已自动退款"，终止，不要再次支付 |
| `FULFILL_AND_REFUND_FAILED` (500) | 异常且退款失败 | 建议用户联系客服 |

## 注意事项

1. **默认模板免收费**：`template=default` 时直接返回结果，不需要支付流程
2. **扩展语法直接写在 Markdown 中**：`:::tip`、`:::warn` 等卡片语法直接嵌入 Markdown 正文，不要拆成多次调用
3. 调用付费模板（`tech` / `warm` / `business` / `nature`）前，先通过"付费前置检查"确认 `weixinpay` 插件已安装
4. **中文 body 必须用 UTF-8 文件 + `curl -d @文件` 发送**，绝不能内联 `-d '中文'`（会乱码）
5. 收到 402 时支付由 `weixinpay` 插件自动完成，Skill 无需关心支付细节，**不要展示 `WeixinPay-Required` 原始值**
6. 支付成功后必须主动重试，body 不变、通过 Header 传 `WeixinPay-Required` 和 `X-Out-Trade-No`
7. 同一订单重复请求返回相同结果（幂等），`already_fulfilled:true` 表示已缓存
