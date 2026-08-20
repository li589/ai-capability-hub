# 加料/做法/规格/优惠/毛利 字段取数契约

---

## 加料销售统计

**路径**：`/open/standard/report/order/orderitem/ingredient/page`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义            | 字段名                    | 类型   | 单位 | 易错说明 |
| ------------------- | ------------------------- | ------ | ---- | -------- |
| 门店ID              | shopId                    | Long   | —    | —        |
| 门店名称            | shopName                  | String | —    | —        |
| 加料名称            | ingredientName            | String | —    | —        |
| 单独销售-点菜数量   | ingredientSingleQuantity  | String | —    | —        |
| 单独销售-销售数量   | ingredientSingleQty       | String | —    | —        |
| 单独销售-销售金额   | ingredientSingleAmt       | String | 元   | —        |
| 单独销售-优惠金额   | ingredientSinglePromo     | String | 元   | —        |
| 单独销售-收入       | ingredientSingleIncome    | String | 元   | —        |
| 单独销售-附加费收入 | ingredientSingleExtraFee  | String | 元   | —        |
| 单独销售-退菜数量   | ingredientSingleReturnCnt | String | —    | —        |
| 单独销售-退菜金额   | ingredientSingleReturnAmt | String | 元   | —        |
| 关联销售-点菜数量   | ingredientCombineQuantity | String | —    | —        |
| 关联销售-销售数量   | ingredientCombineQty      | String | —    | —        |
| 关联销售-销售金额   | ingredientCombineAmt      | String | 元   | —        |
| 关联销售-优惠金额   | ingredientCombinePromo    | String | 元   | —        |
| 关联销售-收入       | ingredientCombineIncome   | String | 元   | —        |

### ⚠️ 易混字段对照

| 容易混淆的字段    | 正确区分                                                    |
| ----------------- | ----------------------------------------------------------- |
| Single vs Combine | Single=加料单独点（独立菜品），Combine=随主菜一起点（附属） |
| Quantity vs Qty   | Quantity=点菜数量，Qty=实际销售数量（扣退菜后）             |

---

## 菜品做法统计

**路径**：`/open/standard/report/order/orderitem/practice/page`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义           | 字段名                    | 类型   | 单位 | 易错说明              |
| ------------------ | ------------------------- | ------ | ---- | --------------------- |
| 门店ID             | shopId                    | Long   | —    | —                     |
| 门店名称           | shopName                  | String | —    | —                     |
| 菜品名称           | itemName                  | String | —    | —                     |
| 规格名称           | specName                  | String | —    | —                     |
| 做法名称           | practiceName              | String | —    | 如"椒盐""微辣"        |
| 做法分组名称       | practiceTypeName          | String | —    | 如"口味""烹饪方式"    |
| 订单类型           | orderType                 | String | —    | 中文名称（堂食/外带） |
| 菜品销售数量       | itemSaleQty               | String | —    | 该菜品总销售量        |
| 菜品销售金额       | itemSaleAmt               | String | 元   | —                     |
| 做法销售数量       | practiceSaleQty           | String | —    | 该做法被选次数        |
| 做法销售金额       | practiceSaleAmt           | String | 元   | 做法加价金额          |
| 做法优惠金额       | practicePromoAmt          | String | 元   | —                     |
| 做法服务费分摊收入 | practiceExtraApportionAmt | String | 元   | —                     |
| 做法收入金额       | practiceActualAmt         | String | 元   | —                     |

### ⚠️ 易混字段对照

| 容易混淆的字段                 | 正确区分                                              |
| ------------------------------ | ----------------------------------------------------- |
| itemSaleQty vs practiceSaleQty | item=菜品总量，practice=该做法选择次数                |
| itemSaleAmt vs practiceSaleAmt | item=菜品金额，practice=做法加价金额（大部分做法为0） |

---

## 规格销售统计

**路径**：`/open/standard/report/order/orderitem/spec/page`
**授权**：品牌授权
**数据路径**：`response.result.data.orderItemSpecListVoPage.values`

### 核心字段

| 业务含义     | 字段名            | 类型   | 单位 | 易错说明      |
| ------------ | ----------------- | ------ | ---- | ------------- |
| 规格编码     | specCode          | String | —    | —             |
| 规格名称     | specName          | String | —    | —             |
| 门店ID       | shopId            | Long   | —    | —             |
| 门店名称     | shopName          | String | —    | —             |
| 销售类型编码 | itemType          | String | —    | SINGLE_DISH等 |
| 销售类型名称 | itemTypeName      | String | —    | "单品""套餐"  |
| 销售金额     | actualSalePrice   | String | 元   | —             |
| 优惠金额     | dishPromoTotalAmt | String | 元   | 负数          |
| 销售数量     | actualSaleQty     | String | —    | —             |
| 退菜数量     | returnCnt         | String | —    | —             |
| 退菜金额     | returnAmt         | String | 元   | —             |
| 菜品收入     | actualAmt         | String | 元   | = 销售金额 -  | 优惠 |  |
| 销售占比     | actualRatio       | String | %    | —             |

### ⚠️ 注意

- 数据路径比其他接口多一层：`orderItemSpecListVoPage.values`
- 同时有汇总对象 `orderItemSpecAggVo` 提供合计数据

---

## 菜品优惠统计

**路径**：`/open/standard/report/order/orderitem/apportion/list`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义       | 字段名            | 类型   | 单位 | 易错说明 |
| -------------- | ----------------- | ------ | ---- | -------- |
| 门店ID         | shopId            | Long   | —    | —        |
| 门店名称       | shopName          | String | —    | —        |
| 菜品ID         | itemId            | String | —    | —        |
| 菜品名称       | name              | String | —    | —        |
| 销售数量       | actualSaleQty     | String | —    | —        |
| 销售金额       | actualSalePrice   | String | 元   | —        |
| 优惠金额       | dishPromoTotalAmt | String | 元   | 负数     |
| 服务费分摊收入 | extraApportionAmt | String | 元   | —        |
| 菜品收入       | actualAmt         | String | 元   | —        |
| 支付优惠分摊   | payApportion      | Object | —    | 见下方   |
| 订单优惠分摊   | orderApportion    | Object | —    | 见下方   |

### payApportion / orderApportion 子对象

```
.totalAmt                      → 分摊合计金额
.apportionItem[].apportionedName → 分摊项名称（如"商户优惠"）
.apportionItem[].apportionedAmt  → 分摊金额（负数）
```

### ⚠️ 易混字段对照

| 容易混淆的字段                             | 正确区分                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| dishPromoTotalAmt vs payApportion.totalAmt | dishPromoTotalAmt=菜品优惠总额，payApportion=支付优惠中分摊到该菜品的部分 |

---

## 菜品成本毛利统计

**路径**：`/open/standard/report/measure/dish/gross/profit`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义       | 字段名            | 类型   | 单位 | 易错说明             |
| -------------- | ----------------- | ------ | ---- | -------------------- |
| 营业日期       | finishBusiDate    | String | —    | yyyy-MM-dd           |
| 商品名称       | itemName          | String | —    | —                    |
| 规格名称       | specNameConcat    | String | —    | —                    |
| 单位名称       | unitName          | String | —    | 如"份""杯"           |
| 商品编码       | itemSkuCode       | String | —    | —                    |
| 商品类型       | itemType          | String | —    | SINGLE_DISH等        |
| 订单类型       | orderType         | String | —    | FOR_HERE等           |
| 实际销售数量   | actualSaleQty     | String | —    | —                    |
| 实际销售金额   | actualSalePrice   | String | 元   | 折前                 |
| 商品总优惠金额 | dishPromoTotalAmt | String | 元   | 负数                 |
| 商品实收金额   | actualAmt         | String | 元   | 折后收入             |
| 菜品成本价     | costPrice         | String | 元   | —                    |
| 毛利           | grossProfit       | String | 元   | = 实收 - 成本        |
| 毛利率         | grossProfitRate   | String | —    | 小数形式（非百分比） |
| 折前毛利       | profitPre         | String | 元   | = 销售金额 - 成本    |
| 折前毛利率     | profitPreRate     | String | —    | 小数形式             |

### ⚠️ 易混字段对照

| 容易混淆的字段           | 正确区分                                                       |
| ------------------------ | -------------------------------------------------------------- |
| grossProfit vs profitPre | grossProfit=折后毛利(基于实收)，profitPre=折前毛利(基于销售额) |
| grossProfitRate          | 是小数不是百分比，展示时需 ×100 加%                            |

### 校验规则

- grossProfit = actualAmt - costPrice × actualSaleQty
- 毛利率可能为负数（亏损菜品）
