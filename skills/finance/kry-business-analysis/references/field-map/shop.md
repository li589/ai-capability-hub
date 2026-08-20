# 门店/桌台/服务费 字段取数契约

---

## 门店详情

**路径**：`/open/standard/shop/MerchantOrgReadService/queryById`
**授权**：门店授权
**数据路径**：`response.result`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 门店ID | shopId | Long | — | 客如云门店唯一标识 |
| 门店名称 | name | String | — | — |
| 联系人 | contact | String | — | — |
| 联系电话 | contactMobile | String | — | 已脱敏 |
| 服务电话 | serviceMobile | String | — | ≠ contactMobile |
| 地址详情 | addressDetail | String | — | — |
| 省名称 | provinceName | String | — | — |
| 市名称 | cityName | String | — | — |
| 区名称 | areaName | String | — | — |
| 经度 | longitude | String | — | — |
| 纬度 | latitude | String | — | — |
| 机构模式 | orgMode | String | — | SINGLE=单店，CHAIN=连锁 |
| 机构类型 | orgType | String | — | STORE=门店 |
| 主营业态 | mainMeal | String | — | 业态编码 |
| 附营业态 | viceMeals | String | — | 业态编码 |
| 门店图片 | detailPictures | String | — | JSON格式字符串 |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| contactMobile vs serviceMobile | contactMobile=联系人手机，serviceMobile=对外服务电话 |
| addressProvince vs provinceName | addressProvince=省编码，provinceName=省中文名 |

---

## 门店桌台列表

**路径**：`/open/standard/shop/ShopTableClient/pageQuery`
**授权**：门店授权
**数据路径**：`response.result.tableList`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 桌台ID | tableId | String | — | — |
| 桌台名称 | tableName | String | — | — |
| 所属区域ID | areaId | String | — | — |
| 所属区域名称 | areaName | String | — | — |
| 用餐人数 | tablePersonCount | Long | 人 | 桌台容纳人数 |
| 是否支持预订 | supportBookFlag | Boolean | — | true=支持 |
| 桌台类型 | tableTypeCode | Long | — | -1=散台，-2=包厢，-3=宴会，-4=备用 |

### 分页字段

| 业务含义 | 字段名 | 类型 |
|---------|--------|------|
| 当前页码 | pageNum | Long |
| 每页条数 | pageSize | Long |
| 总条目数 | totalNum | Long |
| 总页数 | totalPage | Long |

---

## 桌台详情

**路径**：`/open/standard/shop/ShopTableClient/getShopTable`
**授权**：门店授权
**数据路径**：`response.result`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 桌台ID | tableId | String | — | — |
| 桌台名称 | tableName | String | — | — |
| 所属区域ID | areaId | String | — | — |
| 所属区域名称 | areaName | String | — | — |
| 用餐人数 | tablePersonCount | Long | 人 | — |
| 是否支持预订 | supportBookFlag | Boolean | — | true=支持，false=不支持 |
| 桌台类型 | tableTypeCode | Long | — | -1=散台，-2=包厢，-3=宴会，-4=备用 |

---

## 门店服务费列表

**路径**：`/open/standard/shop/ShopExtraChargeQueryClient/listQuery`
**授权**：门店授权
**数据路径**：`response.result.extraChargeList`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 服务费ID | extraChargeId | String | — | — |
| 服务费名称 | name | String | — | — |
| 服务费类型 | extraChargeType | String | — | SERVICE_CHARGE=服务费，BJF=包间费，TAKE_OUT_CHARGE=外卖服务费 |
| 计算方式 | calcWay | String | — | PERCENT=按比例，PERSON=按人数，FIXED=固定金额 |
| 计算数额 | calcAmount | Long | — | 比例/金额/每人金额，取决于calcWay |
| 是否自动加入订单 | autoAddOrderFlag | String | — | ON=是，OFF=否 |
| 是否优惠后计算 | discountAfterCalcFlag | String | — | ON=是，OFF=否 |
| 是否参与优惠分摊 | allowDiscountShareFlag | String | — | ON=是，OFF=否 |
| 是否参与折扣 | allowDiscountFlag | String | — | ON=是，OFF=否 |
| 启用状态 | enabledFlag | String | — | ON=启用，OFF=禁用 |

---

## 服务费详情

**路径**：`/open/standard/shop/ShopExtraChargeQueryClient/getExtraChargeById`
**授权**：门店授权
**数据路径**：`response.result.extraChargeList`

### 核心字段

与「门店服务费列表」字段完全一致，见上方表格。

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| calcAmount 的含义 | 取决于 calcWay：PERCENT时为百分比值，PERSON时为每人金额，FIXED时为固定金额 |
| autoAddOrderFlag 缺失 | 字段未返回时默认为 OFF |
