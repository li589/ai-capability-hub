---
name: taobao-1688-fetcher
slug: taobao-1688-fetcher
title: 淘宝1688商品素材拉取
display_name: 淘宝1688商品素材拉取
version: 1.0.0
description: 根据淘宝/天猫/1688 商品链接拉取标题、主图、SKU图、详情图、自带视频、规格价格、卖点等公开商品素材。付费技能，每次调用前需用户微信支付授权。
triggers:
  - "淘宝"
  - "天猫"
  - "1688"
  - "商品素材"
  - "选品"
  - "代发货"
priority: 50
requires:
  network: true
license: MIT
compatibility: 通过 HTTPS 调用托管接口，无需本地依赖
metadata:
  author: taobao-1688-fetcher
  tags:
    - e-commerce
    - product-fetch
    - taobao
    - 1688
    - sourcing
    - paid-skill
    - x402
---

# 淘宝 / 天猫 / 1688 商品素材拉取（Pay Skill）

## 何时使用

用户给出一个淘宝、天猫或 1688 的商品链接，想要获取该商品的标题、图片、SKU 信息、视频等素材时，调用本技能。

**本技能为付费技能**，每次调用前需要用户通过微信支付完成授权。

## 重要：这是托管式接口

服务端已由开发者部署并持续运行。你只需要发 HTTPS 请求即可，**不要**尝试：

- ❌ 安装依赖、运行本地脚本
- ❌ 向用户索要或尝试配置任何 API 密钥、商户号、私钥
- ❌ 部署服务端

所有密钥都在开发者的服务器上，**用户和你都不需要提供任何密钥**。用户唯一需要做的是在微信中确认支付。

接口地址：

```
https://sxsai.cn/skill/taobao-fetcher/api/resource
```

## 付费前置检查

调用本技能前，检查当前 Agent 是否已安装 weixinpay 插件：
- 已安装：可继续提供付费服务
- 未安装：提示"当前 Agent 暂不支持微信支付付费能力，请先安装 weixinpay 插件"，终止流程

## 工作流程

### 第一步：请求资源

```
POST https://sxsai.cn/skill/taobao-fetcher/api/resource
Content-Type: application/json

{"query": "https://detail.1688.com/offer/xxxxxxx.html"}
```

### 第二步：处理 402 响应

首次请求会返回 HTTP 402，提取以下两个值（**必须保存**）：
- `WeixinPay.WeixinPay-Required` → 作为 `paymentCode`
- `out_trade_no` → 订单号，后续重试必须携带

响应中的 `amount` 是本次调用价格（元），可以先告知用户。

### 第三步：发起支付

```
weixinpay_pay(paymentCode="第二步获取的 payment_code")
```

用户在微信中确认支付后，支付完成。支付授权 5 分钟内有效。

### 第四步：支付成功后获取资源（⚠️ 必须执行）

**支付成功后，必须携带 `out_trade_no` 重新请求**，否则永远拿不到付费内容：

```
POST https://sxsai.cn/skill/taobao-fetcher/api/resource
Content-Type: application/json

{
  "query": "原始商品链接",
  "out_trade_no": "第二步保存的订单号"
}
```

若返回 402 `PAYMENT_NOT_COMPLETE`，等待 1-2 秒后用**同一个** `out_trade_no` 重试，最多 3 次。不要重新下单，否则用户可能被重复扣费。

### 第五步：返回商品素材

验证通过后返回统一 schema 的 JSON，数据在 `content` 字段中：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 商品标题 |
| `main_images` | string[] | 主图 URL 数组 |
| `sku_images` | string[] | SKU 图 URL 数组 |
| `detail_images` | string[] | 详情长图 URL 数组 |
| `video` | string | 商品自带视频直链，无则为空串 |
| `sku_list` | object[] | 规格清单，含 key / name / price / image |
| `selling_points` | string[] | 卖点关键词数组 |
| `source_platform` | string | 来源平台（1688 / taobao 等） |
| `product_id` | string | 平台商品 ID |
| `source_url` | string | 原始链接 |

详细接口文档见 `references/api-reference.md`，X402 流程详情见 `references/x402-protocol.md`。

## 错误处理

| 状态码 | 场景 | 处理建议 |
|--------|------|----------|
| 400 | 参数错误 | 检查是否传入了有效的商品链接 |
| 402 | 需要支付 / 支付尚未确认 | 按第二步~第四步流程完成支付，或用同一订单号稍后重试 |
| 404 | 订单不存在 | 重新从第一步开始 |
| 409 | 订单已因履约失败自动退款 | 终态，重新从第一步发起新请求 |
| 410 | 支付授权已过期（超过 5 分钟未完成支付） | 重新从第一步开始，获取新的支付授权 |
| 502 | 上游采集失败 | 商品下架或受限；已自动退款（见 `refunded` 字段），建议更换链接后重新下单 |

完整错误码说明见 `references/error-codes.md`。

## 注意事项

- 每次成功调用收费，价格以 402 响应中的 `amount` 为准
- 同一 `out_trade_no` 只履约一次，重复请求返回 `already_fulfilled: true`，不重复扣费
- 30 秒内同一链接的重复调用会被上游幂等拦截
- 图片与视频均为直链，如需二次编辑可传给图像模型处理
- 支付确认后若采集失败，服务端会自动退款，响应中 `refunded` 字段标明退款是否成功
- 建议客户端请求超时设为 60 秒
