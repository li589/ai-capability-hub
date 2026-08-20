# 桌均消费/就餐人数/部门销售 字段取数契约

---

## 桌均消费分析

**路径**：`/open/standard/report/order/table-avg/page`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 营业日期 | finishBusiDate | String | — | 范围格式如"2026-04-28~2026-04-28" |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 桌台区域ID | tableAreaId | Long | — | — |
| 桌台区域名称 | tableAreaName | String | — | — |
| 桌均消费区间 | range | String | — | 如"0.00~50.00" |
| 客流量 | orderPeopleCnt | String | 人 | — |
| 开台数 | openTableCnt | String | — | — |
| 订单数 | orderCnt | String | 笔 | — |
| 订单数占比 | orderCntRatio | String | % | — |
| 营业额 | orderAmt | String | 元 | 折前 |
| 营业额占比 | orderAmtRatio | String | % | — |
| 营业收入 | orderReceiveAmt | String | 元 | 折后实收 |
| 营业收入占比 | orderReceiveAmtRatio | String | % | — |
| 优惠金额 | promoAmt | String | 元 | 负数 |
| 优惠金额占比 | promoAmtRatio | String | % | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| orderAmt vs orderReceiveAmt | orderAmt=营业额(折前)，orderReceiveAmt=营业收入(折后) |
| range | 是字符串区间如"0.00~50.00"，不是数值 |

---

## 就餐人数分析（按人数）

**路径**：`/open/standard/report/dinner/numberAnalysis`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 完结营业日 | finishBusiDate | String | — | yyyy-MM-dd |
| 客流 | peopleCnt | Long | 人 | — |
| 营业收入 | orderReceivedAmt | String | 元 | — |
| 订单金额 | orderAmt | String | 元 | — |
| 优惠金额 | promoAmt | String | 元 | — |
| 订单笔数 | busiOrderNoCount | Long | 笔 | — |
| 折前人均 | perCapitaPre | String | 元 | = orderAmt / peopleCnt |
| 折后人均 | perCapitaPost | String | 元 | = orderReceivedAmt / peopleCnt |
| 开台数 | openTableCnt | String | — | — |
| 客流人数 | customerTrafficCnt | String | 人 | — |
| 堂食客流菜折后均价 | dineinPricePost | String | 元 | — |
| 堂食客流菜折前均价 | dineinPricePre | String | 元 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| peopleCnt vs customerTrafficCnt | peopleCnt=该就餐人数组的客流，customerTrafficCnt=订单客流人数 |
| perCapitaPre vs perCapitaPost | Pre=折前人均(含优惠)，Post=折后人均(实付) |
| busiOrderNoCount | 是订单笔数，不是订单号 |

---

## 就餐人数分析（按桌台类型）

**路径**：`/open/standard/report/dinner/tableTypeAnalysis`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 完结营业日 | finishBusiDate | String | — | — |
| 订单收入 | orderReceivedAmt | String | 元 | — |
| 订单金额 | orderAmt | String | 元 | — |
| 优惠总金额 | promoAmt | String | 元 | — |
| 订单笔数 | measure6r9p8zsdjok0 | Long | 笔 | ⚠️ 动态字段名！ |
| 桌台就餐人数 | orderPeopleCnt | String | 人 | — |
| 折前人均 | perCapitaPre | String | 元 | — |
| 折后人均 | perCapitaPost | String | 元 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| measure6r9p8zsdjok0 | ⚠️ 订单笔数字段名是动态生成的，不固定！按Long类型识别 |
| orderReceivedAmt vs orderAmt | 同上：received=折后，orderAmt=折前 |

---

## 部门销售统计

**路径**：`/open/standard/report/order/department/query`
**授权**：品牌授权
**数据路径**：`response.result.data.pageResult.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期 | businessDate | String | — | yyyy/MM/dd |
| 部门名称 | departmentName | String | — | — |
| 区域名称 | mainAreaName | String | — | — |
| 菜品编码 | orderItemCode | String | — | — |
| 菜品名称 | orderItemName | String | — | — |
| 销售类型名称 | sellTypeName | String | — | "单品""套餐" |
| 规格名称 | skuName | String | — | — |
| 单位名称 | unitName | String | — | — |
| 大类名称 | bigTypeName | String | — | — |
| 中类名称 | midTypeName | String | — | — |
| 点菜数量 | orderItemQty | String | — | — |
| 点菜金额 | orderItemAmt | String | 元 | — |
| 销售数量 | sellQty | String | — | 扣退菜后 |
| 销售金额 | sellAmt | String | 元 | — |
| 退菜数量 | returnQty | String | — | — |
| 退菜金额 | returnAmt | String | 元 | — |
| 退菜率 | returnRate | String | % | — |
| 赠送数量 | giftQty | String | — | — |
| 赠送金额 | giftAmt | String | 元 | — |
| 菜品优惠 | orderItemPromoAmt | String | 元 | 负数 |
| 菜品收入 | actualAmt | String | 元 | — |
| 服务费收入 | extraApportionAmt | String | 元 | — |
| 销售千次 | thousandsOfSales | String | — | — |
| 千元销量 | sellQtyPerThousand | String | — | — |

### 合计行（response.result.data.totalResult）

| 业务含义 | 字段名 |
|---------|--------|
| 合计点菜数量 | orderItemQty |
| 合计销售金额 | sellAmt |
| 合计退菜率 | returnRate |
| 合计菜品收入 | actualAmt |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| orderItemQty vs sellQty | orderItemQty=点菜数量(含退菜)，sellQty=实际销售数量(扣退菜后) |
| orderItemAmt vs sellAmt | 同上：点菜金额 vs 实际销售金额 |
| sellAmt vs actualAmt | sellAmt=销售金额(折前)，actualAmt=菜品收入(折后) |

### 校验规则

- sellQty = orderItemQty - returnQty
- sellAmt ≈ orderItemAmt - returnAmt
- actualAmt ≈ sellAmt + orderItemPromoAmt（promoAmt为负数）
