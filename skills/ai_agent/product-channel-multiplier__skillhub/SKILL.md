---
name: "资料方向整理助手"
description: "输入一段说明文字，付费后整理适用场景、信息要点、呈现方式和表达建议。"
tags: ["资料整理"]
version: "1.0.2"
capability: "text_generation"
pricing:
  model: per_call
  amount_fen: 300
---

# 资料方向整理助手

本技能按调用量计费，每次 3 元。输出用于资料整理和写作参考，不承诺平台审核、流量、交易或收益结果。

本技能只有在公开支付 Prompt 与商户 X402 后端服务都可用时才能完成付费调用；两部分缺一不可。

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已经安装并可调用 `weixinpay` 插件。

- 已安装且可调用：继续执行下面的工作流程。
- 未安装或不可调用：提示“当前 Agent 暂不支持微信支付付费能力”，立即终止。不得请求商户服务，不得创建订单，也不得继续任何付费调用。

## 工作流程

### 第一步：请求资源

向商户服务发起：

`POST https://api.skillpayapi.top/v1/skills/product-channel-multiplier/invoke`

`Content-Type: application/json`

Body 必须为：

`{"skill_id":"product-channel-multiplier","input":"<用户本次完整需求>","mode":"full"}`

只发送履约所必需的本次任务信息；不要发送账号密码、支付凭证、私钥、无关文件或其他敏感数据。

### 第二步：处理 402 响应

若返回 HTTP 402，提取并保存响应 Header 中的 `WeixinPay-Required` 与 `X-Out-Trade-No`。两者都必须保存；任一字段缺失都终止，不模拟支付成功。

### 第三步：发起支付

把 `WeixinPay-Required` 的值作为 `paymentCode` 调用 `weixinpay_pay`，由用户确认授权支付。用户未授权、取消或支付失败时终止，不交付收费内容，也不免费代答。

### 第四步：支付成功后获取资源

支付成功后，必须向完全相同的 URL 重发完全相同的 Body，并原样带回 `WeixinPay-Required` 与 `X-Out-Trade-No` 两个 Header。

- 返回 HTTP 200 且 Body 含 `content`：完整交付 `content`。
- 返回其他非 200 响应：不交付收费内容，按服务端真实错误提示终止或稍后使用同一请求重试。

### 长耗时履约扩展

官方核心链路是 402 -> `weixinpay_pay` -> 原请求重试 -> HTTP 200。本服务模板为避免长耗时任务被重复执行，额外实现了 HTTP 202 `FULFILLING` 扩展。收到该状态时，保留原 URL、原 Body、`WeixinPay-Required` 和 `X-Out-Trade-No` 两个 Header，稍后继续重试，直到获得 HTTP 200 且 Body 含可用 `content`。

同一订单重复请求必须返回一致的缓存结果；`already_fulfilled:true` 时不得再次收费。未收到可用的 HTTP 200 `content` 前，不得本地履约、输出部分成品或免费代答。

## 输入

提供完成任务所需的主题、资料、约束和目标。

## 输入传输契约

商户服务的 `input` 字段只接受文本。不得上传文件，不得发送本地文件路径、图片 URL 或 Base64。若任务必须读取图片，应停止并说明当前版本未声明视觉摘要契约，不得假装已经看图。

## 输出

支付成功并收到服务端 HTTP 200 且正文含 `content` 后，完整返回该内容。结果范围以公开描述和服务端实际能力为准。

## 版本与变更

- `1.0.2`：进一步收窄公开描述，保留 X402 付费流程与后端履约契约。
