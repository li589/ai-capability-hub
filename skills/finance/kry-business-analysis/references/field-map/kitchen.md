# 后厨出品/叫号/出餐 字段取数契约

---

## 取餐叫号统计

**路径**：`/open/standard/report/CdsOrderDetailClient/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 营业日期 | finishBusiDate | String | — | yyyy-MM-dd |
| 订单总数 | orderCnt | Long | 笔 | — |
| 已叫号订单数 | calledOrderCnt | Long | 笔 | — |
| 叫号率 | calledOrderRate | String | % | — |
| 待叫号订单数 | unCallOrderCnt | Long | 笔 | — |
| 已取餐订单数 | pickedOrderCnt | Long | 笔 | — |
| 取餐率 | pickedOrderRate | String | % | — |
| 手动取餐叫号订单数 | manualPickedOrderCnt | Long | 笔 | — |
| 手动取餐叫号率 | manualPickedOrderRate | String | % | — |
| 待取餐订单数 | unPickOrderCnt | Long | 笔 | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| calledOrderCnt vs pickedOrderCnt | called=已叫号(通知顾客)，picked=已取餐(顾客拿走) |
| calledOrderRate vs pickedOrderRate | 叫号率=已叫号/总数，取餐率=已取餐/已叫号 |

### 校验规则

- calledOrderCnt + unCallOrderCnt = orderCnt
- pickedOrderCnt + unPickOrderCnt = calledOrderCnt

---

## 后厨员工出品统计

**路径**：`/open/standard/report/kitchen/produced/statistics`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 营业日期 | finishBusiDate | String | — | yyyy-MM-dd |
| 门店ID | shopId | Long | — | — |
| 门店名称 | shopName | String | — | — |
| 品牌ID | loginBrandId | Long | — | 字段名不同，注意！ |
| 员工姓名 | operatorName | String | — | — |
| 制作数量 | actualSaleQty | Long | — | — |
| 菜品制作超时次数 | timeoutCount | Long | 次 | — |
| 出餐次数 | itemCount | Long | 次 | — |
| 超时占比 | timeoutRatio | Long | — | 非百分比，是比值 |
| 平均制作时长 | avgCompletionTime | Long | — | 单位可能为秒或分钟 |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| actualSaleQty vs itemCount | actualSaleQty=制作数量，itemCount=出餐次数（一次出餐可能多份） |
| loginBrandId | 此接口品牌ID字段名为loginBrandId，非brandId |

---

## 后厨菜品出餐统计

**路径**：`/open/standard/report/queryData`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 营业日期 | finishBusiDate | String | — | yyyy-MM-dd |
| 门店ID | shopId | Long | — | — |
| 商品名称 | itemName | String | — | — |
| 规格名称 | specNameConcat | String | — | — |
| 操作人名称 | operatorName | String | — | — |
| 大类名称 | bigTypeName | String | — | — |
| 中类名称 | midTypeName | String | — | — |
| 商品类型 | itemType | String | — | SINGLE_DISH等 |
| 实际销售数量 | actualSaleQty | String | — | — |
| 菜品制作超时次数 | timeoutCount | Long | 次 | — |
| 出餐次数 | id | Long | 次 | ⚠️ 字段名为id，实际含义是出餐次数 |
| 超时占比 | timeoutRatio | String | — | 小数形式 |
| 平均制作时长 | avgCompletionTime | String | — | 单位为秒（大数字如16965） |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| id | ⚠️ 此接口 id 字段实际含义是「出餐次数」，不是记录ID |
| avgCompletionTime 单位 | 此接口为秒，展示时可能需转换为分钟 |
| kitchen/produced vs queryData | produced=按员工统计，queryData=按菜品统计 |
