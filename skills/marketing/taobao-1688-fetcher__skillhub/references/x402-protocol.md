# X402 付费调用流程（调用方视角）

X402 是腾讯 Skill Pay 的付费调用协议。本技能已完整实现服务端，**你只需要走完下面 4 步客户端流程**。

## 前置检查

确认当前 Agent 已安装 `weixinpay` 插件：
- 已安装 → 继续
- 未安装 → 告知用户"当前 Agent 暂不支持微信支付付费能力，请先安装 weixinpay 插件"，终止流程

## 完整流程

```
① 你    → 技能服务   POST /api/resource {"query":"商品链接"}
② 技能服务 → 你       HTTP 402 + WeixinPay-Required + out_trade_no
③ 你    → 微信支付    weixinpay_pay(paymentCode=WeixinPay-Required 的值)
④ 用户  → 微信        在微信中确认支付
⑤ 你    → 技能服务   POST /api/resource {"query":"...","out_trade_no":"..."}
⑥ 技能服务 → 你       HTTP 200 + 商品素材
```

服务端与微信支付、SkillHub 之间的下单、签名、查单、退款全部由服务端完成，对你透明。

## 第一步：请求资源

```
POST https://sxsai.cn/skill/taobao-fetcher/api/resource
Content-Type: application/json

{"query": "https://detail.1688.com/offer/xxxxxxx.html"}
```

## 第二步：处理 402 响应

从响应中提取并**保存**两个值：

| 取值路径 | 用途 |
|----------|------|
| `WeixinPay.WeixinPay-Required` | 作为 `paymentCode` 传给 `weixinpay_pay` |
| `out_trade_no` | 订单号，第四步必须原样携带 |

响应里的 `amount` 是本次调用价格（元），可以展示给用户。

## 第三步：发起支付

```
weixinpay_pay(paymentCode="第二步取到的 WeixinPay-Required 值")
```

用户在微信中确认后完成支付。

⚠️ 支付授权 **5 分钟内有效**，超时未支付需要从第一步重新开始。

## 第四步：携带订单号重新请求（必须执行）

支付成功后，**必须**再发一次请求并带上 `out_trade_no`，否则拿不到内容：

```
POST https://sxsai.cn/skill/taobao-fetcher/api/resource
Content-Type: application/json

{
  "query": "原始商品链接",
  "out_trade_no": "第二步保存的订单号"
}
```

返回 HTTP 200 及 `content` 字段，即为商品素材。

## 重试建议

若第四步返回 402 `PAYMENT_NOT_COMPLETE`，说明服务端尚未查到支付成功（微信侧偶有延迟）。等待 1-2 秒后用同一 `out_trade_no` 重试，最多重试 3 次。

其余状态码含义见 `references/error-codes.md`。
