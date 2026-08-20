# Mini App API Documentation

> 已接入的真实接口，新接口持续补充中。

## Overview

- **Base URL**: `https://7.wawo.cc`
- **图片 Base URL**: `https://img.wawo.cc`
- **Authentication**: `AccessToken` 请求头（需登录接口）
- **Response Format**: JSON，统一格式 `{ "code": "000", "message": "", "data": ..., "success": true }`
- **code = "000"** 表示成功

---

## Authentication

需登录的接口在请求头中携带：
```
AccessToken: <token>
```

Token 通过微信扫码登录获取（`scripts/api_client.py` 自动管理）。**无 refresh_token 机制**，token 过期后需用户重新扫码。

### 1. 获取登录二维码

```
GET /api/identity/pc/getQrImg
```

Response:
```json
{
  "code": "000",
  "message": "",
  "data": {
    "pcKey": "add31d181746465597e8a3611233f0b3",
    "qrImg": "/wxqr/2026-06-05/513a302a-d450-4682-a8ce-d3253d447169.jpg"
  },
  "success": true
}
```
- `pcKey`：轮询获取 token 时的唯一标识
- `qrImg`：二维码图片相对路径，拼上 `https://img.wawo.cc` 即为完整图片 URL

### 2. 轮询获取 Token

```
POST /api/identity/pc/getAccessToken
Content-Type: application/json

{ "pcKey": "add31d181746465597e8a3611233f0b3" }
```

Response（扫码成功）:
```json
{
  "code": "000",
  "message": "",
  "data": "qwjscjjnsdjkskmska",
  "success": true
}
```
- `data`：用户 access_token（字符串），后续请求放入 `AccessToken` 请求头
- 未扫码时 `data` 为 `null`，持续轮询即可

---

## Products

### Search Products（游客接口，无需登录）

```
POST /api/item/wx/launch/un/searchConvert
Content-Type: application/json

{
  "pageNum": 1,
  "pageSize": 20,
  "name": "水果",
  "fromSource": 2,
  "convert": 1,
  "searchWordType": "用户输入",
  "requestId": null
}
```

Response:
```json
{
  "code": "000",
  "data": {
    "total": 107,
    "records": {
      "goodsShowInfo": [
        {
          "name": "商品名称",
          "price": 9.90,
          "url": "/store/configure/2024-08-01/xxx.png",
          "splBrandName": "品牌名",
          "deliveryTime": "预计1-3天发货",
          "launchNo": 1726652920797
        }
      ]
    }
  },
  "success": true
}
```
⚠️ **商品数据位置（重要）**：
- `data` 是 dict
- `data.records` 是 dict（不是 list）
- `data.records.goodsShowInfo` **就是商品列表**，每个元素是一件商品
- `data.total` 是商品总数，用于分页

`api_client.py` 的 `search_products()` 已自动提取 `goodsShowInfo` 并附加 `image_url` 字段，返回结构为：
```python
{
    "goods": [{"name", "price", "launchNo", "image_url", ...}, ...],  # 来自 data.records.goodsShowInfo
    "total": 107,
    "page_num": 1,
    "page_size": 9,
    "has_more": True,
}
```

- `url`：商品图片相对路径，拼上 `https://img.wawo.cc` 即完整图片 URL（`api_client.py` 已自动处理为 `image_url` 字段）
- 分页默认每页 9 条

### Get Product Detail（游客接口，无需登录）

```
POST /api/item/wx/detail/un/info_v2
Content-Type: application/json

{
  "launchNo": "17001798730827",
  "moduleId": "",
  "marketCategoryId": "",
  "collectionType": ""
}
```

- `launchNo`：搜索商品返回的 `launchNo` 字段

Response（核心字段）:
```json
{
  "code": "000",
  "data": {
    "spuId": 2026052200005314,
    "launchNo": 17001798730827,
    "name": "辽宁丹东黄金蜜桃无毛黄油桃",
    "des": "软脆两吃，口感丰富，光滑无毛",
    "url": "/store/configure/2026-05-08/xxx.jpg",
    "msg": "<p><img src='https://img.wawo.cc/store/configure/xxx.jpg'/></p>",
    "splBrandName": "NONGCAIHUI/农彩汇",
    "stock": 4696,
    "shelfTags": {
      "titleLeft": [{"tagId": 0, "tagName": "爆品"}]
    },
    "skuList": [
      {
        "skuId": 106766,
        "price": 55.00,
        "specsV1": "4.5斤彩箱装 单果150g 中果",
        "stock": 1284,
        "unit": "件",
        "deliveryTime": "付款后2天内发货",
        "img": "/store/configure/xxx.jpg"
      }
    ],
    "scrollingVOS": [{"nickName": "Y**", "scrollingContent": "购买了该商品"}],
    "voucherVO": null
  }
}
```

### voucherVO 示例（有优惠时）

当商品参与优惠活动时，`voucherVO` 不为空，包含 `skuPriceItemList`：

```json
{
  "voucherVO": {
    "voucherCouponVO": [],
    "skuPriceItemList": [
      {
        "skuId": 50319,
        "skuPrice": 5500,
        "promoPrice": 5200,
        "promoPriceStr": "52",
        "promoPriceTime": "2026-06-15 23:59:59",
        "promoMarketId": "199",
        "promoDiscountPrice": "3",
        "finalPrice": 5200,
        "finalPriceStr": "52",
        "discountPrice": 300,
        "discountPriceStr": "3",
        "finalPriceLaunchCouponCode": ""
      }
    ],
    "marketLinkInfos": [
      {
        "marketId": "199",
        "marketName": "12.8",
        "marketType": 2,
        "marketStatus": 1,
        "marketStartTime": "2025-12-08 00:00:00",
        "marketEndTime": "2026-06-15 23:59:59"
      }
    ]
  }
}
```

**⚠️ 价格取值规则（重要）**：
- 当 `voucherVO` 存在且有值时，SKU 展示价格和下单 `actualAmount` 应取 `skuPriceItemList` 中对应 `skuId` 的 `finalPriceStr` 字段
- 当 `voucherVO` 为 null 或不存在时，使用 `skuList[].price` 字段
- `api_client.py` 已自动将 `finalPriceStr` 合并到对应 SKU 对象中，调用方只需优先使用 `sku.finalPriceStr`，不存在时回退到 `sku.price`

关键字段说明：
- `name`：商品名称
- `des`：简短描述
- `url`：商品主图（相对路径，拼 `https://img.wawo.cc`）
- `msg`：商品详情 HTML（含多张详情大图）
- `skuList[]`：SKU 规格列表（不同规格不同价格）
  - `skuId`：加入购物车/下单用
  - `price`：价格（元）
  - `specsV1`：规格描述（如"4.5斤彩箱装 单果150g 中果"）
  - `stock`：该规格库存
  - `unit`：单位（件/箱等）
  - `deliveryTime`：预计发货时间
- `shelfTags`：标签（如"爆品"）
- `scrollingVOS`：最近购买滚动通知

---

## Address

### Get First Address（需登录，返回加密数据）

```
GET /api/account/wx/address/first
AccessToken: <token>
```

该接口返回**加密/脱敏后的**默认收货地址，直接回显即可，无需解密。

Response:
```json
{
  "code": "000",
  "message": "",
  "data": {
    "id": 2273,
    "name": "*",
    "phone": "155****8416",
    "address": "山东省济南市****立下小楼"
  },
  "success": true
}
```

**字段说明：**
- `id`：地址 ID（下单时传入 `orderAddressList[].id`）
- `name`：收件人姓名（加密，如 `*`）
- `phone`：收件人电话（脱敏，如 `155****8416`）
- `address`：详细地址（脱敏，如 `山东省济南市****立下小楼`）

**⚠️ data 为空或无 id 时**：抛出 `NoAddressError`，提示用户先去小程序中补充收货地址。

> `api_client.py` 的 `get_address()` 方法自动调用此接口，返回 `{"id", "name", "phone", "address"}` 四个字段。

---

## Orders

### Create Order（需登录）

```
POST /api/cart/wx/order/wb_cr
AccessToken: <token>
Content-Type: application/json

{
  "vipLevel": 0,
  "actualAmount": 55.00,
  "orderAddressList": [{
    "id": 920512
  }],
  "orderGoodsList": [{
    "launchNo": "17001798730827",
    "num": 1,
    "launchSkuId": 168083,
    "skuId": 106766,
    "entranceSource": "会员商城-推荐",
    "activity": "FRESH_GROUP",
    "distributionCard": "",
    "distributionType": "",
    "requestId": "feb59b5f4be443e28f4e32d360d20b86",
    "addressId": 920512,
    "goodsType": 1,
    "primageVo": null
  }],
  "orderType": "order_shop",
  "scoreAmount": 0,
  "smoothScoreAmount": 0,
  "sourcePlat": 1,
  "shopOrderSubmit": {"type": 0, "sharedUserInfo": null, "inviterCardNo": ""},
  "threeTuanOrderSubmit": null,
  "orderUserCouponList": [],
  "useCoupon": true,
  "priExpr": 1
}
```

**关键字段说明：**
- `actualAmount`：用户支付的金额，取商详 `skuList[选中的SKU].price`
- `orderAddressList[0].id`：地址 ID（来自 `get_address()` 返回的 `id` 字段）
- `orderGoodsList[0].launchNo`：商品 `launchNo`（来自搜索/商详）
- `orderGoodsList[0].launchSkuId`：**SKU 的 `id` 字段**（商详 skuList 中的 `id`，非 `skuId`！）
- `orderGoodsList[0].skuId`：SKU 的 `skuId` 字段（商详 skuList 中的 `skuId`）
- `orderGoodsList[0].requestId`：随机 UUID（去连字符）

Response:
```json
{
  "code": "000",
  "data": {
    "mainOrderNo": "1020260605000014713891",  // 主订单号，展示给用户时必须取这个
    "subOrderNo": "1020260605043004953900"    // 子订单号，仅用于内部记录
  },
  "success": true
}
```

> ⚠️ **展示订单号时取 `mainOrderNo`**。

生单成功后，调用支付接口获取 `WeixinPay-Required` 支付码，然后通过微信AI支付 (`weixinpay_pay`) 完成付款。

### Create Payment — 获取 AI 支付码（需登录）

```
POST /api/transaction/wx/order/payment/agent
AccessToken: <token>
Content-Type: application/json

{
  "mainOrderNo": "1020260608000000268612",
  "paymentType": "nativePay"
}
```

**关键字段说明：**
- `mainOrderNo`：主订单号（`create_order` 返回的 `mainOrderNo`）
- `paymentType`：支付方式，固定为 `"nativePay"`

Response:
```json
{
  "WeixinPay-Required": "PAYCODE_xxxxxxxxxxxxxxxx",
  "prompt": "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给weixinpay_pay，以向用户申请支付授权。"
}
```

- `WeixinPay-Required`：AI 支付码，作为 `weixinpay_pay` 工具入参发起AI支付
- `api_client.py` 的 `pay_order()` 方法会自动提取 `WeixinPay-Required`，返回 `{"paymentCode": "PAYCODE_xxx"}`

**返回结构（api_client.py 已封装）：**
```python
{
    "paymentCode": "PAYCODE_xxxxxxxxxxxxxxxx",
}

### Poll Payment Result — 轮询支付结果（需登录）

```
POST /api/transaction/wx/order/wx_pay_result?mainOrderNo=1020260616000000090638
AccessToken: <token>
Content-Type: application/json

{}
```

**关键字段说明：**
- `mainOrderNo`：主订单号，通过 **query 参数**传递（非 body）
- body 为 `{}`

Response:
```json
{
  "code": "000",
  "message": "",
  "data": {
    "mainOrderNo": "1020260616000000090638",
    "subOrderNo": "1020260616000140150639",
    "payStatus": 1,
    "returnScore": "0",
    "actualAmount": "0.03",
    "actualScoreAmount": "0",
    "receiveConfirmReturnScore": 0,
    "combine": 0,
    "payMarketLink": null,
    "activity": "会员日活动-185",
    "threeGroupResult": null,
    "popUpStatus": true,
    "showStatus": true
  },
  "success": true
}
```

- `data.payStatus`：支付结果，`0` 失败，`1` 成功
- `api_client.py` 的 `poll_payment_result()` 方法会自动轮询此接口，每 3 秒查询一次，最长 10 分钟，支付成功（`payStatus == 1`）时返回 data

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | 请求参数错误 |
| 401 | 身份验证失败 |
| 404 | 商品/订单不存在 |
| 409 | 商品库存不足 |
| 500 | 服务器内部错误 |
