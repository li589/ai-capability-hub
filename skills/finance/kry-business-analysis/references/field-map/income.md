# 营收/收入/优惠 字段取数契约

---

## 店内营收统计

**路径**：`/open/standard/report/business/income/v3/list`
**授权**：品牌授权
**数据路径**：`response.result.data.list`

### 请求参数要点

必填：`dateRange` + `shopIds`(String数组) + `periodType` + `couponStatisticalType` + `storeStatisticalType` + `pageBean`
可选：`orgStatisticsType`(默认BY_BRAND，按门店传BY_SHOP)

### orgStatisticsType 维度差异（全部4个营收接口通用）

| 参数值            | 行为               | shopId/shopName | list 条数            |
| ----------------- | ------------------ | --------------- | -------------------- |
| 不传 / `BY_BRAND` | 所有门店汇总为一条 | **null**        | 1（按日期维度）      |
| `BY_SHOP`         | 每个门店独立一条   | **有值**        | N（门店数 × 日期数） |

⚠️ **重要**：当 `orgStatisticsType=BY_BRAND` 时，返回的 `shopId` 和 `shopName` 为 **null**，不能用于门店维度取值。

### periodType 对 date 字段的影响

| periodType | date 格式示例               | 说明     |
| ---------- | --------------------------- | -------- |
| `BY_DAY`   | `"2026-06-29"`              | 单日     |
| `BY_WEEK`  | `"2026-06-23 ~ 2026-06-29"` | 周范围   |
| `BY_MONTH` | `"2026-06"`                 | 月份     |
| `BY_TOTAL` | `"2026-06-25 ~ 2026-06-30"` | 汇总范围 |

### 数据校验关系

- `BY_BRAND` 的单条汇总值 = 所有门店 `BY_SHOP` 之和（已验证完全一致）
- `storeStatisticalType`（COMBINE/SEPARATE）仅影响储值收入拆分方式，不影响营收字段结构和数值

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | Long | — | — |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期 | date | String | — | 格式：yyyy-MM-dd 或 yyyy-MM |
| 营业额（折前） | saleAmt | String | 元 | 订单折前原价金额 |
| 优惠金额 | totalPromoAmt | String | 元 | 包含商户+支付优惠+订单支出 |
| 优惠占比 | promoAmtProportion | String | % | — |
| 营业收入（实收） | businessIncomeAmt | String | 元 | = 营业额 - 优惠金额 |
| 菜品收入 | itemActualReceivedAmt | String | 元 | 营业收入中的菜品部分 |
| 服务费收入 | extraFeeActualAmt | String | 元 | 营业收入中的服务费部分 |
| 订单笔数 | orderCnt | Long | 笔 | 已结账订单数 |
| 折前单均价 | avgTradeAmtPreDiscount | String | 元 | = 营业额 / 订单笔数 |
| 折后单均价 | avgTradeAmtAfterDiscount | String | 元 | = 营业收入 / 订单笔数 |
| 就餐人数 | orderPeopleCnt | Long | 人 | — |
| 折前客单价 | avgCustomerAmtPreDiscount | String | 元 | = 营业额 / 就餐人数 |
| 折后客单价 | avgCustomerAmtAfterDiscount | String | 元 | = 营业收入 / 就餐人数 |
| 平均就餐时长 | avgDiningDuration | String | — | 含中文单位，如"3分钟" |
| 开台数 | openTableCnt | Long | — | — |
| 开台率 | openTableRate | String | % | — |
| 翻台率 | reopenTableRate | String | % | 小于0取0 |
| 订单类型构成 | orderTypeItems | Object | — | 动态列结构，见下方 |

### 动态列：orderTypeItems（二级嵌套结构）

```
orderTypeItems.itemList[]                     → 订单类型列表
  .code                                       → 订单类型编码（FOR_HERE/TAKE_OUT/PLATFORM_TAKE_OUT等）
  .name                                       → 类型名称（堂食/外带/外卖）
  .amount                                     → null（一级无金额）
  .itemList[]                                 → 该类型下的指标列表（二级嵌套）
    .code                                     → 指标编码（orderAmt/promoAmt/orderReceiveAmt/orderCnt/openTableCnt等）
    .name                                     → 指标名称（营业额/优惠/营业收入/订单数/开台次数等）
    .amount                                   → 指标值（字符串）
    .textVal                                  → 展示文本值（带%或中文单位）
    .defaultVal                               → 默认值（无数据时取此值）
orderTypeItems.subTotal                       → null（汇总不在此层）
```

### ⚠️ orderTypeItems 取值注意

- 一级 itemList 是**订单类型维度**（堂食/外带/外卖），每个类型内嵌**二级 itemList** 存放该类型的各项指标
- 取某类型营业额：`orderTypeItems.itemList[code=FOR_HERE].itemList[code=orderAmt].amount`
- textVal 可能含中文单位如 "12分钟"、"100.00%"，数值计算用 amount

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| saleAmt vs businessIncomeAmt | saleAmt=营业额(折前原价)，businessIncomeAmt=营业收入(实收) |
| avgTradeAmtPreDiscount vs avgCustomerAmtPreDiscount | 前者按订单笔数算，后者按就餐人数算 |
| totalPromoAmt | 已是负数表示优惠减少，展示时注意正负 |

### 校验规则

- businessIncomeAmt ≈ saleAmt - |totalPromoAmt|（允许±0.01误差）
- businessIncomeAmt = itemActualReceivedAmt + extraFeeActualAmt
- avgTradeAmtAfterDiscount ≈ businessIncomeAmt / orderCnt

---

## 收入构成统计

**路径**：`/open/standard/report/business/income/constitute/v3/list`
**授权**：品牌授权
**数据路径**：`response.result.data.list`

### 请求参数要点

同「店内营收统计」必填参数（dateRange + shopIds + periodType + couponStatisticalType + storeStatisticalType + pageBean）

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | Long | — | — |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期 | date | String | — | — |
| 营业收入构成 | businessIncomeItems | Object | — | 动态列结构 |

### 动态列：businessIncomeItems

```
businessIncomeItems.itemList[].code   → 收入类型编码（如 CASH_VOUCHER）
businessIncomeItems.itemList[].name   → 收入类型名称（如 "抵用券"）
businessIncomeItems.itemList[].amount → 金额（元）
businessIncomeItems.subTotal          → 营业收入合计
```

### ⚠️ 注意

- 收入构成是动态的，不同商户配置不同，不能硬编码 code 值
- 必须遍历 itemList 获取全部收入项

---

## 优惠构成统计

**路径**：`/open/standard/report/business/income/promo/v3/list`
**授权**：品牌授权
**数据路径**：`response.result.data.list`

### 请求参数要点

同「店内营收统计」必填参数（dateRange + shopIds + periodType + couponStatisticalType + storeStatisticalType + pageBean）

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | Long | — | — |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期 | date | String | — | — |
| 订单优惠 | orderPromoItems | Object | — | 动态列结构 |
| 支付优惠 | paymentPromoItems | Object | — | 动态列结构 |
| 订单支出 | orderExpenseItems | Object | — | 动态列结构 |

### 动态列结构

```
orderPromoItems.itemList[].code   → 优惠类型编码（如 MERCHANT_PROMOTIONS）
orderPromoItems.itemList[].name   → 优惠类型名称（如 "商户优惠"）
orderPromoItems.itemList[].amount → 优惠金额（元，负数）
orderPromoItems.subTotal          → 订单优惠合计
```

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| orderPromoItems vs paymentPromoItems | orderPromoItems=订单层面优惠（折扣/活动），paymentPromoItems=支付层面优惠（支付宝红包等） |
| orderExpenseItems | 非优惠，是订单支出（如溢收）|

---

## 收入优惠统计

**路径**：`/open/standard/report/income/promo/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 请求参数要点

同「店内营收统计」必填参数（dateRange + shopIds + periodType + couponStatisticalType + storeStatisticalType + pageBean）

⚠️ **特殊注意**：
- 此接口**不支持门店维度**，无论 `orgStatisticsType` 传什么，返回的每条记录都不含 `shopId`/`shopName`
- 数据为空时，`values` key 可能不存在（仅返回 `{"totalSize":0}`），取值时必须先判断 key 是否存在

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 完结营业日 | finishBusiDate | String | — | 格式：yyyy-MM-dd |
| 优惠名称 | promoName | String | — | 具体优惠活动名 |
| 优惠二级类型编码 | promoSecType | String | — | 如 MERCHANT_PROMOTIONS |
| 优惠二级类型名称 | promoSecTypeName | String | — | 如 "商户优惠" |
| 优惠三级类型名称 | promoThirdTypeName | String | — | 如 "自定义记账" |
| 优惠类型编码 | promoType | String | — | PAY_PROMO=支付优惠，ORDER_PROMO=订单优惠 |
| 优惠类型名称 | promoTypeName | String | — | — |
| 优惠金额 | promoAmt | String | 元 | 负数表示优惠减少 |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| promoType vs promoSecType | promoType=一级分类(支付/订单)，promoSecType=二级分类(商户优惠/平台补贴等) |
| promoName vs promoSecTypeName | promoName=具体活动名称，promoSecTypeName=归类名称 |

### 校验规则

- promoAmt 通常为负数（表示优惠金额），正数可能是溢收
- 按 promoType 汇总后应与 income/promo/v3 中对应合计一致
