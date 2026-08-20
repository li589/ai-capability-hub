# 对账类 字段取数契约

---

## 平台团购对账

**路径**：`/open/standard/report/groupCoupon/reconciliation`
**授权**：品牌授权
**数据路径**：`response.result.data.item.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | Long | — | — |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 日期 | couponDate | String | — | 格式：yyyy/MM/dd |
| 券来源 | couponSource | String | — | 如"美团" |
| 券来源英文 | couponSourceEn | String | — | 如"MEITUAN" |
| 券名称 | couponName | String | — | — |
| 核销次数 | couponCheckCnt | Long | 次 | — |
| 验券张数 | couponCnt | Long | 张 | — |
| 券合计面额 | faceAmt | String | **分** | ⚠️ 单位是分！ |
| 单个券面额 | singleFaceAmt | String | **分** | ⚠️ 单位是分！ |
| 券售价 | couponSaleAmount | String | **分** | ⚠️ 单位是分！ |
| 顾客购买价 | actualPayAmt | String | **分** | ⚠️ 单位是分！ |
| 平台抽佣 | platformServiceAmt | String | **分** | ⚠️ 单位是分！ |
| 商家应得 | actualReceivedAmt | String | **分** | ⚠️ 单位是分！ |
| 抵扣金额 | deductAmt | String | **分** | ⚠️ 单位是分！ |
| 平台优惠 | platformPromoAmt | String | **分** | ⚠️ 单位是分！ |
| 预计到账金额 | estimatedActualReceivedAmt | String | **分** | ⚠️ 单位是分！ |
| 商户优惠金额 | merchantPromoAmt | String | **分** | ⚠️ 单位是分！ |

### ⚠️ 关键提醒：金额单位为「分」

此接口所有金额字段单位为 **分**，展示时必须 **÷100** 转为元。

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| faceAmt vs singleFaceAmt | faceAmt=合计面额(张数×单张)，singleFaceAmt=单张面额 |
| actualPayAmt vs actualReceivedAmt | actualPayAmt=顾客付的，actualReceivedAmt=商家到手的(扣佣后) |
| couponCheckCnt vs couponCnt | checkCnt=核销次数，couponCnt=券张数（通常一致，团购券可能不同） |
| platformServiceAmt vs platformPromoAmt | service=平台抽佣(平台收走的)，promo=平台补贴(平台给商家的) |

### 校验规则

- actualReceivedAmt ≈ actualPayAmt - platformServiceAmt + platformPromoAmt
- faceAmt = singleFaceAmt × couponCnt

---

## 平台外卖对账

**路径**：`/open/standard/report/takeout/reconciliation/query`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店名称 | shopName | String | — | — |
| 门店ID | shopId | String | — | 可能为"null"字符串 |
| 日期 | date | String | — | 格式：yyyy/MM/dd |
| 平台名称 | platformName | String | — | 如"美团外卖""饿了么" |
| 订单笔数 | orderCnt | Long | 笔 | — |
| 订单金额 | orderAmt | String | 元 | — |
| 订单收入金额 | orderReceivedAmt | String | 元 | 扣优惠后 |
| 商品总价 | itemSaleAmt | String | 元 | — |
| 商家优惠 | shopPromoAmt | String | 元 | 负数 |
| 配送费用 | deliveryAmt | String | 元 | — |
| 平台抽佣 | platformServiceAmt | String | 元 | 负数 |
| 包装费用 | packAndExtraAmt | String | 元 | — |
| 支出合计 | totalExpenseAmt | String | 元 | 配送+其他支出 |
| 其他支出金额 | otherExpenseAmt | String | 元 | — |
| 部分退笔数 | partRefundCnt | Long | 笔 | — |
| 部分退提示 | subRefundTip | String | — | 提示文案 |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| orderAmt vs orderReceivedAmt | orderAmt=订单原价总金额，orderReceivedAmt=扣除优惠后实际收入 |
| totalExpenseAmt vs otherExpenseAmt | total=总支出(配送+其他)，other=仅其他部分 |
| shopPromoAmt vs platformServiceAmt | shopPromo=商家自己出的优惠，platformService=平台抽的佣金 |

### 校验规则

- orderReceivedAmt ≈ itemSaleAmt + shopPromoAmt（shopPromo为负数）
- 金额单位为**元**（与团购对账不同！）

### ⚠️ 与团购对账的关键区别

| 差异点 | 团购对账 | 外卖对账 |
|--------|---------|---------|
| 金额单位 | **分** | **元** |
| 数据路径 | result.data.item.values | result.data.values |
| 日期格式 | yyyy/MM/dd | yyyy/MM/dd |
