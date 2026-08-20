# 商品/菜品 字段取数契约

---

## 商品分类查询

**路径**：`/open/standard/dish/shop/listQueryCategory`
**授权**：门店授权
**数据路径**：`response.result.value`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 分类ID | categoryId | String | — | — |
| 父级分类ID | parentId | String | — | 顶级分类无父级 |
| 分类名称 | categoryName | String | — | — |
| 排序值 | sort | Long | — | — |
| 分类类型 | categoryType | String | — | DISH=菜品分类，SIDE_DISH_GROUP=加料分组 |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| categoryType | DISH=普通菜品分类，SIDE_DISH_GROUP=加料分组（不是菜品） |

---

## 商品分页查询

**路径**：`/open/standard/dish/shop/pageQueryBaseDish`
**授权**：门店授权
**数据路径**：`response.result.value.dataList`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 菜品ID | dishId | String | — | 全局唯一 |
| 菜品名称 | dishName | String | — | — |
| 菜品描述 | dishDesc | String | — | — |
| 分类ID | categoryId | String | — | — |
| 排序值 | sort | Long | — | — |
| 助记码 | helpCode | String | — | — |
| 菜品类型 | dishType | String | — | SINGLE=单菜，COMBO=套餐，SIDE=配料 |
| 菜品状态 | state | String | — | ONLINE=有效，PAUSE=停用，INVALID=删除 |
| 称重菜标识 | weighFlag | String | — | Y=是，N=否 |

### 分页字段

| 业务含义 | 字段名 | 类型 |
|---------|--------|------|
| 数据总数 | total | Long |

---

## 商品详情查询

**路径**：`/open/standard/dish/shop/listQueryDetailDish`
**授权**：门店授权
**数据路径**：`response.result.value`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 菜品ID | dishId | String | — | 全局唯一 |
| 菜品名称 | dishName | String | — | — |
| 菜品编码 | dishCode | String | — | 商家手动录入 |
| 菜品类型 | dishType | String | — | SINGLE/COMBO/SIDE |
| 分类ID | categoryId | String | — | — |
| 分类名称 | categoryName | String | — | — |
| 称重菜标识 | weighFlag | String | — | Y/N |
| 重量 | weight | Long | **毫克** | ⚠️ 单位是毫克！ |
| 单位名称 | unitName | String | — | 如"份""杯" |
| 助记码 | helpCode | String | — | — |

### 规格信息：dishSkuList[]

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 规格名称 | specName | String | — | — |
| 是否默认规格 | defaultSkuFlag | String | — | Y/N |
| 售卖价 | sellPrice | Long | **分** | ⚠️ 单位是分！÷100转元 |
| 条形码 | barCode | String | — | — |
| SKU ID | skuId | String | — | 全局唯一 |
| SKU编码 | dishSkuCode | String | — | — |

### 套餐分组：comboGroupList[]（仅套餐类型）

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 分组名称 | groupName | String | — | 如"3选2" |
| 最大选择数 | maxChoose | Long | — | — |
| 最小选择数 | minChoose | Long | — | — |
| 是否可重复选 | repeatable | String | — | Y/N |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| sellPrice 单位 | ⚠️ 菜品详情中售卖价单位为「分」，报表中为「元」 |
| weight 单位 | ⚠️ 单位为「毫克」，展示时需 ÷1000 转克 |
| dishId vs skuId | dishId=SPU级（红烧肉），skuId=SKU级（红烧肉-大份） |
