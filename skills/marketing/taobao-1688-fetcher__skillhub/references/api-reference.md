# 接口参考

本技能是**托管式付费接口**：服务端已由开发者部署并运行，你只需要按下面的方式发起 HTTP 请求。
无需安装任何依赖、无需配置任何密钥、无需部署任何服务。

## 接口地址

```
POST https://sxsai.cn/skill/taobao-fetcher/api/resource
Content-Type: application/json
```

健康检查（可选，用于确认服务可用）：

```
GET https://sxsai.cn/skill/taobao-fetcher/health
→ {"skill":"taobao-1688-fetcher","status":"ok","version":"1.0.0"}
```

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 淘宝 / 天猫 / 1688 商品链接 |
| `out_trade_no` | string | 否 | 订单号。首次请求不传；支付完成后重试时必须携带 |

## 两种调用场景

### 场景一：首次请求（不带 out_trade_no）→ HTTP 402

```json
POST {"query": "https://detail.1688.com/offer/123456789.html"}
```

响应：

```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "需要支付后才能获取内容",
  "WeixinPay": {
    "WeixinPay-Required": "payment_code_xxx",
    "prompt": "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay，以向用户申请支付授权。"
  },
  "out_trade_no": "WX402_20260630120000abcdef",
  "amount": "0.50",
  "currency": "CNY"
}
```

**必须保存两个值**：`WeixinPay.WeixinPay-Required`（作为 paymentCode）和 `out_trade_no`。

### 场景二：支付完成后重试（带 out_trade_no）→ HTTP 200

```json
POST {
  "query": "https://detail.1688.com/offer/123456789.html",
  "out_trade_no": "WX402_20260630120000abcdef"
}
```

响应：

```json
{
  "code": "SUCCESS",
  "message": "商品素材",
  "out_trade_no": "WX402_20260630120000abcdef",
  "already_fulfilled": false,
  "content": {
    "title": "商品标题",
    "main_images": ["https://...", "https://..."],
    "sku_images": ["https://..."],
    "detail_images": ["https://..."],
    "video": "https://...",
    "sku_list": [
      {"key": "颜色:红色;尺码:M", "name": "红色 M", "price": "99.00", "image": "https://..."}
    ],
    "selling_points": ["卖点1", "卖点2"],
    "source_platform": "1688",
    "product_id": "123456789",
    "source_url": "https://detail.1688.com/offer/123456789.html"
  }
}
```

## content 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 商品标题 |
| `main_images` | string[] | 主图 URL 数组 |
| `sku_images` | string[] | SKU 图 URL 数组 |
| `detail_images` | string[] | 详情长图 URL 数组 |
| `video` | string | 商品自带视频直链，无则为空串 |
| `sku_list` | object[] | 规格清单，含 `key` / `name` / `price` / `image` |
| `selling_points` | string[] | 卖点关键词数组 |
| `source_platform` | string | 来源平台（1688 / taobao / tmall） |
| `product_id` | string | 平台商品 ID |
| `source_url` | string | 原始链接 |

图片与视频均为直链，可直接展示给用户，或传给图像模型做二次编辑。

## 幂等说明

同一 `out_trade_no` 只会履约一次。若重复携带同一订单号请求，返回 `already_fulfilled: true` 并附上此前已取得的内容，**不会重复扣费**。

## 超时

单次请求建议客户端超时设为 **60 秒**（上游采集商品素材通常需要数秒到十几秒）。
