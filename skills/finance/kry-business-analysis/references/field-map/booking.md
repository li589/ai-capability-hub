# 预订分析 字段取数契约

---

## 预订商品排行

**路径**：`/open/standard/report/booking/goodsRanking`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 商品名称 | itemSkuName | String | — | — |
| 预订商品类型 | itemType | String | — | SINGLE=单品 |
| 预订商品数量 | quantity | Long | — | — |
| 单位名称 | unitName | String | — | 如"份" |
| 门店ID | shopId | Long | — | — |
| 创建营业日 | finishBusiDate | String | — | yyyy-MM-dd |

---

## 预订客户排行

**路径**：`/open/standard/report/booking/customerRanking`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 预订人手机号 | customerPhoneNo | String | — | 已脱敏 |
| 客户名称 | customerName | String | — | — |
| 预订单数量 | bookingOrderNo | Long | 笔 | — |
| 已到店预订单笔数 | measureArrivedResvCount | Long | 笔 | — |
| 已取消预订单笔数 | measureResvCancelCount | Long | 笔 | — |
| 未到店预订单笔数 | measureResvNoshowCount | Long | 笔 | — |
| 已逾期预订单笔数 | measureResvOverdueCount | Long | 笔 | — |
| 到店占比 | arrivedResvRatio | Number | — | 小数形式(0~1) |
| 门店ID | shopId | Long | — | — |
| 创建营业日 | finishBusiDate | String | — | yyyy-MM-dd HH:mm:ss |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| bookingOrderNo | 是预订单总数量，不是订单号 |
| arrivedResvRatio | 是小数(0.9)不是百分比，展示时×100 |

### 校验规则

- bookingOrderNo ≥ measureArrivedResvCount + measureResvCancelCount + measureResvNoshowCount + measureResvOverdueCount

---

## 预订业绩排行

**路径**：`/open/standard/report/booking/performanceRanking`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 创建员工名称 | creatorName | String | — | ⚠️ 字段名不同于客户排行 |
| 预订单数量 | bookingOrderNo | Long | 笔 | — |
| 已到店预订单笔数 | measureArrivedResvCount | Long | 笔 | — |
| 已取消预订单笔数 | measureResvCancelCount | Long | 笔 | — |
| 未到店预订单笔数 | measureResvNoshowCount | Long | 笔 | — |
| 已逾期预订单笔数 | measureResvOverdueCount | Long | 笔 | — |
| 到店占比 | arrivedResvRatio | Number | — | 小数形式 |
| 门店ID | shopId | Long | — | — |
| 创建营业日 | finishBusiDate | String | — | — |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| creatorName vs customerName | creatorName=创建预订的员工名，customerName=预订客户名（仅在客户排行中） |

---

## 预订门店排行

**路径**：`/open/standard/report/booking/shopRanking`
**授权**：品牌授权
**数据路径**：`response.result.data.values`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店ID | shopId | Long | — | — |
| 预订单数量 | bookingOrderNo | Long | 笔 | — |
| 已到店预订单笔数 | measureArrivedResvCount | Long | 笔 | — |
| 已取消预订单笔数 | measureResvCancelCount | Long | 笔 | — |
| 未到店预订单笔数 | measureResvNoshowCount | Long | 笔 | — |
| 已逾期预订单笔数 | measureResvOverdueCount | Long | 笔 | — |
| 到店占比 | arrivedResvRatio | Number | — | 小数形式 |
| 创建营业日 | finishBusiDate | String | — | — |

### ⚠️ 注意

- 此接口没有门店名称字段，需通过 shopId 关联门店详情接口获取名称
- 四个预订接口字段命名一致，仅主维度不同（商品/客户/员工/门店）
