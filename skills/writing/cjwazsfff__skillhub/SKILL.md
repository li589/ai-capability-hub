---
name: 超级文案助手
description: 你给我文案，我给你流量
tags: [效率, 写作]
metadata:
    slug: cjwazsff
    version: v1.0.2
    author: 流年
    requires:
        bins:
            - python3
---

# 超级文案助手

> 版本：v1.0.2 · 作者：流年

超级文案助手，输入主题，即可输出你想要的文案。脚本 [scripts/index.py](scripts/index.py) 负责全部 HTTP 调用，接口说明见 [references/api.md](references/api.md)。

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- 已安装：可继续提供付费服务
- 未安装：向用户提示"当前 Agent 暂不支持微信支付付费能力"，终止流程

## 工作流程

### 第一步：创建订单
向以下 URL 发起 POST 请求：

```text
 POST /api/orders/skillhub
```
返回结果
```
{
    "code": "PAYMENT_REQUIRED",
    "message": "需要支付后才能获取内容",
    "WeixinPay": {
        "WeixinPay-Required": "d4a32654-320f-4419-b350-3de9fd3cdfa6",
        "prompt": "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay，以向用户申请支付授权。"
    },
    "out_trade_no": "2026072917461841549",
    "amount": "0.01",
    "currency": "CNY",
    "description": "AI付费"
}
```

### 第二步：支付后查询订单

```text
 POST /api/orders/pay-status
```
- ** 获取上一步的  out_trade_no
返回结果
```
{
    "code": "PAID_NOT_USED",
    "message": "订单已支付，可使用",
    "out_trade_no": "2026072917412920032",
    "transaction_id": "weixin://wxpay/bizpayurl?pr=5QQN3BGO5XGZu9lh",
    "payment_time": null
}
```

### 第三步：携带支付成功的订单号执行任务

```text
 POST /api/analytics/wenan
```
- **  out_trade_no 订单号
- **  keyword 输入的关键词

返回结果
```
{
    "code": 200,
    "data": {
        "keyword": "YmdHis通天塔2026072917412920032"
    },
    "msg": ""
}
```


## 注意事项

1. 必须先通过"付费前置检查"确认 weixinpay 插件已安装，否则不要进入支付流程
2. 收到 402 响应时，支付由 weixinpay 插件完成，Skill 无需关心支付细节
3. 支付成功后必须主动发起重试请求，body 保持不变，通过 Header `X-Out-Trade-No` 传递订单号
4. 如果返回 "NOT_PAID"，说明支付尚未完成，请等待后重试
5. 如果返回 "REFUNDED"，说明服务异常已退款，告知用户并终止流程
6. 如果返回 "FULFILL_AND_REFUND_FAILED"，说明服务异常且退款失败，建议用户联系客服
