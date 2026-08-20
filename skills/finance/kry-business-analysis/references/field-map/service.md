# 服务费/套餐/自助餐/出杯率 字段取数契约

---

## 服务费统计

**路径**：`/open/standard/report/extrafee/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期 | showDate | String | — | yyyy-MM-dd |
| 服务费ID | extraFeeId | String | — | — |
| 服务费名称 | extraFeeName | String | — | 如"配送费""包间费" |
| 服务费类型 | extraFeeType | String | — | 中文类型名 |
| 订单类型 | orderType | String | — | 如 SELF_TAKE_OUT |
| 服务费金额 | extraFeeAmt | String | 元 | 应收金额 |
| 服务费优惠金额 | promoTotalAmt | String | 元 | — |
| 服务费收入 | extraFeeActualAmt | String | 元 | = 金额 - 优惠 |
| 分摊金额 | apportionedAmt | String | 元 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| extraFeeAmt vs extraFeeActualAmt | extraFeeAmt=应收(折前)，extraFeeActualAmt=实收(折后) |

### 校验规则

- extraFeeActualAmt = extraFeeAmt - promoTotalAmt

---

## 套餐销售统计

**路径**：`/open/standard/report/combo/sale/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 套餐名称 | comboName | String | — | — |
| 子菜名称 | detailName | String | — | "合计"表示套餐整体 |
| 菜品ID | itemId | String | — | — |
| 菜品名称 | itemName | String | — | — |
| 大类名称 | bigTypeName | String | — | — |
| 中类名称 | midTypeName | String | — | — |
| 菜品销售金额 | itemSalePrice | String | 元 | — |
| 菜品销售数量 | itemSaleQty | String | — | — |
| 菜品优惠总金额 | promoAmt | String | 元 | — |
| 菜品收入 | actualAmt | String | 元 | — |
| 子菜列表 | subs | Array | — | 套餐内各子菜明细 |

### subs[] 子对象

与主字段结构相同，包含：comboName、detailName、itemSalePrice、itemSaleQty、promoAmt、actualAmt 等。

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| detailName="合计" | 表示套餐整体行，非子菜 |
| comboName vs itemName | comboName=套餐名，itemName也是套餐名（合计行时一致） |
| 主行 vs subs[] | 主行是套餐汇总，subs是子菜明细拆分 |

---

## 自助餐统计

**路径**：`/open/standard/report/order/orderitem/buffet/statistics/list`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段（位于 values[].items[] 内）

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 菜品名称 | itemName | String | — | — |
| 规格名称 | itemSkuName | String | — | 如"成人""儿童" |
| 商品编码 | itemSkuCode | String | — | — |
| 大类名称 | bigTypeName | String | — | — |
| 中类名称 | midTypeName | String | — | — |
| 规格全称 | specNameConcat | String | — | — |
| 销售份数 | actualSaleQty | String | — | — |
| 销售金额 | actualSaleAmt | String | 元 | — |
| 优惠金额 | dishPromoTotalAmt | String | 元 | — |
| 餐标金额 | buffetFlagAmt | String | 元 | 自助餐定价 |
| 餐标销售金额 | buffetFlagSaleAmt | String | 元 | — |
| 成人数量 | adultNum | Long | 人 | — |
| 儿童数量 | childNum | Long | 人 | — |
| 老人数量 | elderNum | Long | 人 | — |
| 退款数量 | refundQty | String | — | — |
| 退款金额 | refundAmt | String | 元 | — |

### ⚠️ 注意

- 数据嵌套在 `values[].items[]` 内，注意多一层 items
- adultNum/childNum/elderNum 为按人群分类的用餐人数

---

## 出杯率统计

**路径**：`/open/standard/report/measure/cup/yield/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店ID | shopId | String | — | 注意是String类型 |
| 营业日期 | finishBusiDate | String | — | yyyy-MM-dd |
| 进杯数 | cupsSaleCnt | String | 杯 | — |
| 出杯数 | cupsFinishCnt | String | 杯 | — |
| 出杯率 | cupOutRate | String | — | 小数形式（0~1） |
| 待出杯数 | pendingCupCnt | String | 杯 | — |

### 校验规则

- cupsFinishCnt + pendingCupCnt = cupsSaleCnt
- cupOutRate = cupsFinishCnt / cupsSaleCnt
