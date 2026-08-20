# 菜品销售/分类营收/品项 字段取数契约

---

## 菜品销售统计

**路径**：`/open/standard/report/orderItem/list`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 请求参数要点

必填：`dateRange` + `shopIds` + `pageBean` + `countLatitude`(Object) + `sellLatitude`(Object) + `orderSourceCondition`(Object) + `orderTypeCondition`(Object) + `goodsTempFlag`(0)
❗ `countLatitude` 必须为 Object，禁止传字符串，格式：`{"countCollectType":0,"countType":1}`
  - countCollectType: Integer (0=按维度类型汇总, 1=按门店汇总)
  - countType: Integer (1=按菜名, 2=按大类, 3=按中类, 4=按菜名+规格)
❗ `sellLatitude` 必须为 Object，禁止使用已废弃的 `sellType` 字段，正确格式：
  `{"sellCollectType": false, "countType": "SINGLE_PACKAGE"}`
  - sellCollectType: Boolean (false=按单品和子项分行, true=汇总展示)
  - countType: String 枚举 (SINGLE/PACKAGE/PACKAGE_ITEM/SINGLE_PACKAGE/SINGLE_PACKAGE_ITEM)

### 核心字段（位于 values[].item[] 数组内）

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 大类名称 | bigTypeName | String | — | — |
| 中类名称 | midTypeName | String | — | — |
| 菜品名称 | name | String | — | — |
| 菜品规格 | itemSkuName | String | — | 如"标准""大份" |
| 菜品类型 | itemType | String | — | 单品/套餐/配料 |
| 菜品编码 | code | String | — | — |
| 菜品ID | itemId | String | — | — |

### 数值字段（同在 values[].item[] 内，扁平结构）

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 销售金额 | salePrice | String | 元 | ⚠️ 不是 saleAmtCompared |
| 点菜金额 | goodsSpotAmt | String | 元 | — |
| 点菜数量 | goodsSpotQty | String | — | — |
| 平均售价 | goodsSellAvg | String | 元 | — |
| 赠送数量 | giftCnt | String | — | — |
| 赠送金额 | giftAmt | String | 元 | — |
| 退菜数量 | returnCnt | String | — | — |
| 退菜金额 | returnAmt | String | 元 | — |
| 退菜率 | returnRatio | String | % | — |
| 做法变价 | practiceAmt | String | 元 | — |
| 加料变价 | excipientAmt | String | 元 | — |
| 菜品优惠金额 | dishPromoTotalAmt | String | 元 | — |
| 菜品收入 | actualAmt | String | 元 | 扣优惠后实收 |
| 收入占比 | actualRatio | String | % | — |
| 实际销售数量 | actualSaleQty | String | — | 扣退菜后 |
| 实际销售均价 | actualSalePrice | String | 元 | — |
| 服务费分摊 | extraApportionAmt | String | 元 | — |
| 打包盒费 | packingBoxAmt | String | 元 | — |
| 销售千次 | goodsSellThousandRatio | String | — | — |
| 成本价 | estimateCostPrice | String | 元 | — |
| 毛利 | grossProfitPrice | String | 元 | — |
| 毛利率 | grossProfitRatio | String | % | — |

### 汇总字段（values[].aggregation 和 values[].totalAggregation）

```
aggregation       → 当页汇总
totalAggregation  → 全量汇总
字段同 item[] 中的数值字段
```

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|--------|
| salePrice vs actualAmt | salePrice=折前销售金额，actualAmt=扣除优惠后的收入 |
| goodsSpotQty vs actualSaleQty | goodsSpotQty=点菜数量，actualSaleQty=实际销售数量(扣退菜) |
| aggregation vs totalAggregation | aggregation=当页合计，totalAggregation=全量合计 |

### 校验规则

- actualAmt ≤ salePrice（收入不可能大于销售额）
- actualSaleQty = goodsSpotQty - returnCnt

---

## 菜品分类营收统计

**路径**：`/open/standard/report/orderItem/itemType/list`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

结构与「菜品销售统计」一致，按分类（大类/中类）聚合。

主要区别：
- 聚合维度为 bigTypeName / midTypeName 而非单品
- 同样包含 item[] 数组和 Compared 对比结构

---

## 销售品项统计（部门维度）

**路径**：`/open/standard/report/orderItem/department/list`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

结构与「菜品销售统计」基本一致，额外包含：

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 出品部门名称 | departmentName | String | — | 如"热菜部""凉菜部" |
| 销售千次 | thousandsOfSales | String | — | — |
| 千元销量 | sellQtyPerThousand | String | — | — |

### ⚠️ 注意

- 此接口与 `/open/standard/report/order/department/query` 功能重叠
- orderItem/department/list 使用 Compared 对比结构
- order/department/query 使用扁平字段结构（见 dinner.md）
