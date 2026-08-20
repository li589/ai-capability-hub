---
name: store-competitor-analysis
description: 门店竞品分析——输入门店位置和经营品类，输出周边竞品分布与选址竞争分析报告。每次查询￥1.00。
version: 1.2.0
author: 北京柚转科技有限公司
---

# 门店竞品分析

## 功能描述

输入门店位置（地址/商圈）和经营品类，输出周边竞品全景分析报告，包含 8 个板块：

- 竞品总览（数量/连锁占比）
- 竞争激烈度评级（蓝海/适中/激烈/红海）
- 品类自适应价格带分析
- 头部 3 家竞品多维对比
- 距离分布与最近 5 家竞品详情
- 细分品类结构
- 口碑与评分分布
- 选址与经营建议

每次查询 1 元，数据来自实时地图 POI 检索。

## 支付引导（⚠️ 必须严格执行，禁止直接终止）

本 Skill 为付费服务（每次 1 元）。你的任务是**护送用户到达可支付状态**——任何时候都不要只说"请先安装插件/绑卡"然后终止流程。

### 第一步：先讲清楚用户买到什么

谈钱之前，先用一句话说清价值：

> "本次分析 1 元，你将得到：周边竞品数量与密度、竞争激烈度评级、价格带空隙分析和选址建议。数据来自实时地图 POI 检索的真实门店，约 30 秒出报告。"

### 第二步：检测支付能力并主动扫障

检查当前环境是否有 weixinpay 支付工具（`mcp__weixinpay__weixinpay_register`）：

**A. 工具存在** → 调用 `weixinpay_register` 查询绑定状态：
- 返回 `is_registered: true` → 直接进入付费流程
- 返回 `is_registered: false` → 把返回的绑定链接原样发给用户，并说：
  > "差一步就能用了：点这个链接跳到微信，绑定微信支付 AI 专属卡（约 30 秒）。绑好后回来告诉我一声，立刻为你出报告。"

**B. 工具不存在** → 告知用户：
> "本服务通过微信支付官方「AI 专属卡」付款。请使用 WorkBuddy 5.2.6 及以上版本（支付插件已内置，无需单独下载），打开新版后重试即可。"

### 第三步：支付安全说明（引导绑定/支付时必须展示）

> - AI 专属卡是微信支付官方产品，是你微信支付账户下的独立子账户，与主钱包隔离
> - 余额随时可转回主钱包，不用不亏
> - 每笔支付都需你本人确认，AI 无法擅自扣款
> - 本次仅 1 元；服务异常未交付会自动退款

### 第四步：余额不足 / 支付失败处理

- 支付时提示余额不足：引导用户在微信「AI 专属卡」里转入任意金额（随时可转回）
- 支付失败：引导用户重试一次；仍失败可通过 `weixinpay_feedback` 提交反馈，**不要直接终止流程**

## 输入要求

收集用户信息后，构造以下 JSON 作为 query：

```json
{
  "location": "望京SOHO",
  "city": "北京市",
  "category": "火锅",
  "radius": 1000
}
```

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| location | 地址/小区/商圈名称，支持任意写法（如"五道口""国贸""中关村大街27号"） | ✅ | — |
| city | 城市名称，如"北京市" | ✅ | — |
| category | 经营品类，如"火锅""奶茶店""健身房""便利店" | ✅ | — |
| radius | 分析半径（米） | 否 | 1000（1km），可选最大 3000 |

## 工作流程

### 第一步：请求资源

向商户服务发起 POST 请求（URL 由环境变量 `SKILL_API_BASE` 指定，默认 `https://store-canalysis-yrkacnmxhe.cn-beijing.fcapp.run`）：

```bash
curl -X POST ${SKILL_API_BASE:-https://store-canalysis-yrkacnmxhe.cn-beijing.fcapp.run}/api/resource \
  -H "Content-Type: application/json" \
  -d '{"query": "{\"location\":\"望京SOHO\",\"city\":\"北京市\",\"category\":\"火锅\",\"radius\":1000}"}'
```

**注意**：query 值是 JSON 字符串（需序列化），不是 JSON 对象。

### 第二步：处理 402 响应

如果收到 HTTP 402 响应，`weixinpay` 插件会拦截并完成支付流程，无需手动调用支付接口。

402 响应中包含：
- Header `WeixinPay-Required`：支付凭证码（weixinpay 插件用于完成支付）
- Header `X-Out-Trade-No`：商户订单号
- Body 中的 `amount`：本次费用金额（用户可见，展示在支付确认界面）

> 支付过程由 `weixinpay` 插件处理，Skill 无需关心支付细节。

### 第三步：支付成功后重新请求获取内容（⚠️ 必须执行）

支付成功后，**必须**重新发起请求获取付费内容。重试规则：

- **JSON body 与首次请求完全一致**
- **额外携带两个 Header**：将 402 响应中的 `WeixinPay-Required` 和 `X-Out-Trade-No` 原样带上

```http
POST ${SKILL_API_BASE:-https://store-canalysis-yrkacnmxhe.cn-beijing.fcapp.run}/api/resource
Content-Type: application/json
WeixinPay-Required: <payment_code>
X-Out-Trade-No: <out_trade_no>

{"query": "用户的原始 query（与第一步完全一致）"}
```

### 第四步：处理响应

| HTTP 状态 | code 字段 | 行为 |
|-----------|-----------|------|
| 200 | SUCCESS | 提取 `content` 字段中的 Markdown 报告，直接呈现给用户 |
| 402 | NOT_PAID | 告知用户"支付验证中，请稍后重试" |
| 200 | REFUNDED | 告知用户"该服务暂时无法提供内容，已自动退款" |
| 500 | FULFILL_AND_REFUND_FAILED | 告知用户"服务异常且退款失败，请联系客服 skillhub@tencent.com" |

### 完整的成功响应示例

```json
{
  "code": "SUCCESS",
  "message": "付费内容",
  "out_trade_no": "WX402_202607251430a1b2c3d4e5f6",
  "transaction_id": "4200001234567890",
  "content": "# 门店竞品分析报告\n\n**分析点位**：望京SOHO…",
  "already_fulfilled": false
}
```

将 `content` 字段中的 Markdown 原文直接呈现给用户即可。

## 输出说明

报告包含 8 个板块，均为 Markdown 格式：

1. **结论卡** — 竞争激烈度评级（蓝海/适中/激烈/红海）+ 一句话建议
2. **竞品总览** — 门店总数、连锁 vs 单体占比
3. **密度分析** — 每 km² 竞品数
4. **距离分布** — 圈层分布表 + 最近 5 家竞品详情
5. **细分品类结构** — 品类内部分布
6. **口碑与价格对比** — 品类自适应价格带 + 评分分布
7. **头部竞品深度拆解** — 最近 3 家竞品多维对比 + 定价策略分析
8. **选址与经营建议** — 可执行的差异化建议

## 错误处理

- 如果返回 `LOCATION_NOT_FOUND`：提示用户确认地点名称或换个写法
- 如果返回 `NO_COMPETITORS`：提示用户扩大半径、更换品类关键词或确认品类写法
- 如果返回 `BAD_QUERY`：按返回的 message 修正 query 后重试

## 使用示例

### 示例 1：火锅店选址

**用户**："我想在望京 SOHO 开火锅店，帮我看看周边竞争情况"

**Agent 操作**：
1. 构造 query：`{"location":"望京SOHO","city":"北京市","category":"火锅","radius":1000}`
2. 发起 POST 请求 → 收到 402 → weixinpay 插件完成支付
3. 携带 Header 重新请求 → 200 SUCCESS
4. 将 content 中的 Markdown 报告呈现给用户

### 示例 2：奶茶店摸底

**用户**："北京五道口附近的奶茶店竞争什么情况？"

**Agent 操作**：
1. 构造 query：`{"location":"五道口","city":"北京市","category":"奶茶","radius":1000}`
2. 发起 POST 请求 → 402 → 支付 → 重试 → 获取报告

### 示例 3：便利店加盟考察

**用户**："我在成都春熙路想加盟一家便利店，帮我分析一下"

**Agent 操作**：
1. 构造 query：`{"location":"春熙路","city":"成都市","category":"便利店","radius":1500}`
2. 发起 POST 请求 → 402 → 支付 → 重试 → 获取报告

## 注意事项

1. 必须按「支付引导」流程主动护送用户到达可支付状态，禁止看到未装插件/未绑卡就直接终止流程
2. 收到 402 响应时，支付由 weixinpay 插件完成，Skill 无需手动调用支付接口
3. 支付成功后必须主动发起重试请求，body 保持不变，通过 Header 传递支付信息
4. 如果返回 NOT_PAID，说明支付尚未完成，请提示用户稍等后重试
5. 如果返回 REFUNDED，说明服务异常已退款，告知用户并终止流程
6. query 必须是 JSON **字符串**，不是 JSON 对象
7. 不要缓存或修改商户返回的报告内容，原样呈现
