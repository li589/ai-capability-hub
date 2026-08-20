# 收款/支付/结算 字段取数契约

---

## 营业收款统计

**路径**：`/open/standard/report/paid/income/v6/list`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 请求参数要点

必填：`dateRange` + `shopIds` + `periodType` + `couponStatisticalType` + `storeStatisticalType` + `pageBean` + **`tabType`** + **`statisticsByBusi`**(Boolean) + **`statisticsByOrderType`**(Boolean)
tabType常用值：TOTAL_INCOME(总收款) / BUSINESS_INCOME(营业收款) / MEMBER_INCOME(会员充值)

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | String | — | — |
| 门店ID | shopId | String | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期范围 | busiDate | String | — | 格式：yyyy-MM-dd ~ yyyy-MM-dd |
| 业务类型编码 | busiType | String | — | BUSINESS_INCOME=营业收款 |
| 业务类型名称 | busiTypeName | String | — | — |
| 订单类型编码 | orderType | String | — | FOR_HERE/TAKE_OUT等 |
| 订单类型名称 | orderTypeName | String | — | — |
| 收款合计 | totalIncome | Object | — | 见下方结构 |
| 收款构成列表 | payMethodList | Array | — | 见下方结构 |

### totalIncome 子对象

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 支付笔数 | payCnt | Long | 笔 | — |
| 券张数量 | couponCnt | Long | 张 | — |
| 笔数/张数展示 | cntDisplay | String | — | 如 "9笔/1张" |
| 收款金额 | incomeAmt | String | 元 | — |
| 实储实收金额 | realStoreActualReceivedAmt | String | 元 | — |
| 赠储实收金额 | rewardStoreActualReceivedAmt | String | 元 | — |
| 占比 | percent | String | % | — |

### payMethodList[] 子对象

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 支付类型编码 | payType | String | — | CREDIT_AND_PREPAYMENT/CASH_AND_OTHERS/ONLINE等 |
| 支付类型名称 | payTypeName | String | — | "预付款抵扣"/"现金及其他"/"在线支付" |
| 支付类型提示 | payTypePrompt | String | — | 对该分类的解释说明（可能null） |
| 支付方式编码 | methodCode | String | — | 与 payType 一致 |
| 支付笔数 | payCnt | Long | 笔 | 可能为 null（汇总行） |
| 收款金额 | incomeAmt | String | 元 | — |
| 占比 | percent | String | % | 可能为 null |
| 子明细列表 | childList | Array | — | 见下方（部分支付类型有子级） |

### childList[] 子对象（payMethodList 的二级明细）

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 支付方式名称 | methodName | String | — | 如"会员卡-储值消费（实储）" |
| 支付方式编码 | methodCode | String | — | 如"-1:会员卡-储值消费（实储）" |
| 优惠卷名称 | couponName | String | — | 如"会员卡" |
| 储值类型 | storeType | String | — | REAL_STORE=实储, REWARD_STORE=赠储 |
| 支付笔数 | payCnt | Long | 笔 | — |
| 笔数展示 | cntDisplay | String | — | 如"1笔" |
| 收款金额 | incomeAmt | String | 元 | — |
| 实储实收 | realStoreActualReceivedAmt | String | 元 | — |
| 赠储实收 | rewardStoreActualReceivedAmt | String | 元 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| totalIncome.incomeAmt vs payMethodList[].incomeAmt | 前者是合计，后者是单个支付类型的金额 |
| realStoreActualReceivedAmt vs rewardStoreActualReceivedAmt | 前者=实储(真金白银充的)实收，后者=赠储(赠送余额)实收 |
| payMethodList vs childList | payMethodList=一级支付分类，childList=该分类下的具体支付方式明细 |
| payTypePrompt | 对分类的解释说明，如"会员卡支付、挂账支付、订金抵扣等支付方式，一般不计入实际收款" |

---

## 支付方式收款统计

**路径**：`/open/standard/report/paymethod/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 支付方式ID | payMethodId | Long | — | — |
| 支付方式名称 | payMethodName | String | — | 如"现金""微信""支付宝" |
| 支付笔数 | payCntTotal | Long | 笔 | 收款为正，退款为负 |
| 商户实收 | actualReceivedAmt | String | 元 | 顾客实付 + 平台补贴 - 平台抽佣 |
| 支付金额 | payDetailAmt | String | 元 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| actualReceivedAmt vs payDetailAmt | actualReceivedAmt=商户最终到手(扣佣后)，payDetailAmt=顾客实际支付金额 |
| payCntTotal 正负 | 正=收款笔数，负=退款笔数，净值=收款-退款 |

### 校验规则

- 所有支付方式 actualReceivedAmt 之和 ≈ 营收统计中的 businessIncomeAmt

---

## 支付结算统计

**路径**：`/open/standard/report/payment/reconciliation/v4/list`
**授权**：品牌授权
**数据路径**：`response.result.data.paymentPage.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 品牌ID | brandId | Long | — | — |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 支付营业日 | payFinishBusiDate | String | — | 汇总显示开始日~结束日 |
| 渠道名称 | channelName | String | — | 如"乐刷" |
| 渠道商户号 | merchantNo | String | — | — |
| 银行卡后四位 | last4DigitsOfCard | String | — | — |
| 开户行名称 | bankName | String | — | — |
| 业务类型 | busiType | String | — | — |
| 在线支付应打款金额 | actualReceivedAmt | String | 元 | 已扣除手续费 |
| 应到账笔数 | actualReceivedCnt | Long | 笔 | — |
| 手续费金额 | totalFeeAmt | String | 元 | — |
| 当期结算金额 | curReconciliationAmt | String | 元 | — |
| 当期结算笔数 | curReconciliationCnt | Long | 笔 | — |
| 当期未结算金额 | curOutstandingAmt | String | 元 | — |
| 当期未结算笔数 | curOutstandingCnt | Long | 笔 | — |
| 上期未结算金额 | lastOutstandingAmt | String | 元 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| actualReceivedAmt vs curReconciliationAmt | actualReceivedAmt=应打款总金额，curReconciliationAmt=本期已结算金额 |
| curOutstandingAmt vs lastOutstandingAmt | cur=当期未结，last=上期未结（历史遗留） |

### 校验规则

- actualReceivedAmt ≈ curReconciliationAmt + curOutstandingAmt
- actualReceivedCnt ≈ curReconciliationCnt + curOutstandingCnt
