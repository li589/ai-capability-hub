# 订单 字段取数契约

---

## 订单列表查询

**路径**：`/open/standard/order/queryList`
**授权**：门店授权
**数据路径**：`response.result.data.list`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | String | — | — |
| 门店ID | shopId | String | — | — |
| 订单ID | orderId | String | — | 系统唯一标识 |
| 业务订单号 | busiOrderNo | String | — | — |
| 订单状态 | orderStatus | String | — | 见下方枚举 |
| 订单类型 | orderType | String | — | 见下方枚举 |
| 订单金额 | orderAmt | String | **分** | ⚠️ 单位是分！ |
| 优惠金额 | promoAmt | String | **分** | ⚠️ 单位是分！ |
| 订单实收 | orderReceivedAmt | String | **分** | ⚠️ 单位是分！ |
| 下单时间 | openTime | String | — | yyyy-MM-dd HH:mm:ss |
| 完结时间 | finishTime | String | — | yyyy-MM-dd HH:mm:ss |
| 第三方订单号 | thirdOrderNo | String | — | — |
| 订单流水号 | serialNo | String | — | — |

### ⚠️ 关键提醒：金额单位为「分」

订单接口所有金额字段单位为 **分**，展示时必须 **÷100** 转为元。

### 订单状态枚举

| 编码 | 含义 |
|------|------|
| WAIT_PAY | 待支付 |
| PAID | 已支付 |
| WAIT_PROCESSED | 待处理 |
| SUCCESS | 已完成 |
| WAIT_SETTLED | 待结账 |
| SETTLED | 已结账 |
| REFUND | 已退单 |
| CLOSED | 已关闭 |
| INVALID | 已作废 |
| CANCELLED | 已取消 |
| ANTI_SETTLED | 已反结账 |

### 订单类型枚举

| 编码 | 含义 |
|------|------|
| FOR_HERE | 堂食 |
| TAKE_OUT | 外带 |
| PLATFORM_TAKE_OUT | 平台外卖 |
| SELF_TAKE_OUT | 自营外卖 |
| SELF_TAKE | 自提 |
| NO_ORDER_CASHIER | 无单收银 |
| MEMBER_STORE | 会员充值 |

### 分页字段

| 业务含义 | 字段名 | 类型 |
|---------|--------|------|
| 总数 | totalCount | String |
| 页号 | pageNo | String |
| 页大小 | pageSize | String |
| 总页数 | totalPage | String |

---

## 订单详情查询

**路径**：`/open/standard/order/queryDetail`
**授权**：门店授权
**数据路径**：`response.result.data`（注意：内部是嵌套结构，非扁平）

### 基础订单信息：data.orderBaseVO

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 订单ID | orderId | String | — | — |
| 业务订单号 | busiOrderNo | String | — | — |
| 订单状态 | orderStatus | String | — | 同上枚举 |
| 订单类型 | orderType | String | — | 同上枚举 |
| 订单金额 | orderAmt | Long | **分** | ⚠️ 分！可能为Long或String |
| 优惠金额 | promoAmt | String | **分** | ⚠️ 分！ |
| 订单实收 | orderReceivedAmt | String | **分** | ⚠️ 分！ |
| 下单时间 | openTime | String | — | yyyy-MM-dd HH:mm:ss |
| 结账时间 | settleTime | String | — | yyyy-MM-dd HH:mm:ss |
| 订单来源 | orderSource | String | — | POS/WECHAT_MINI_PROGRAM等 |
| 开单人 | openOperatorName | String | — | — |
| 结账人 | settleOperatorName | String | — | — |
| 就餐人数 | orderPeopleCnt | String | 人 | ⚠️ 不是 peopleCnt |
| 流水号 | serialNo | String | — | — |

### 桌台信息：data.orderTableVoList[]

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 桌台名称 | tableName | String | — | — |
| 桌台ID | tableId | String | — | — |

### 菜品明细：data.orderItemVoList[]

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 菜品名称 | itemName | String | — | — |
| 菜品数量 | quantity | String | — | ⚠️ 字符串如"1.0000" |
| 菜品销售金额 | itemSaleAmt | String | **分** | ⚠️ 不是 itemAmt |
| 菜品实收 | itemReceivedAmt | String | **分** | ⚠️ 分！ |
| 菜品类型 | itemType | String | — | SINGLE_DISH等 |
| 大类名称 | bigTypeName | String | — | — |
| 规格名称 | specNameConcat | String | — | — |
| 单位 | unitName | String | — | — |
| 菜品ID | itemId | String | — | SPU ID |
| SKU ID | itemSkuId | String | — | — |

### 支付信息：data.openPaymentDetailVoList[]

| 业务含义     | 字段名           | 类型   | 单位   | 易错说明         |
| ------------ | ---------------- | ------ | ------ | ---------------- |
| 支付方式名称 | payMethodName    | String | —      | 如"会员卡""现金" |
| 支付金额     | payAmt           | String | **分** | —                |
| 实收金额     | actualReceiveAmt | String | **分** | —                |
| 支付状态     | payDetailStatus  | String | —      | PAY_SUCCESS      |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|--------|
| orderAmt vs orderReceivedAmt | orderAmt=折前总金额，orderReceivedAmt=折后实收 |
| 订单接口金额 vs 报表接口金额 | 订单接口单位=分，报表接口单位=元！ |
| orderItemVoList vs orderItemList | ⚠️ 实际字段名是 orderItemVoList |
| openPaymentDetailVoList vs payInfoList | ⚠️ 实际字段名是 openPaymentDetailVoList |
| orderPeopleCnt 位置 | 在 orderBaseVO 内，不是顶层 data |

### 校验规则

- orderReceivedAmt = orderAmt - promoAmt
- 所有金额单位为「分」，与报表类接口（元）不同
