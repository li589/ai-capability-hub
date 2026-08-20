# 商品列表查询 Reference（woscli admin-api query-goods-list）

通过 `woscli admin-api query-goods-list` 查询商品列表，支持分页、搜索和多维度筛选。

## 调用方式

```bash
woscli admin-api query-goods-list [args]
```

## 请求参数（args 映射）

`args` 中的参数按顺序传递，最终映射为底层查询条件。

### 分页参数

| args 参数 | 说明 | 默认值 |
|-----------|------|--------|
| `--pageNum` | 页码 | 1 |
| `--pageSize` | 每页数量 | 20 |

### 搜索参数

| args 参数 | 说明 | 可选值 |
|-----------|------|--------|
| `--search` | 搜索关键词 | - |
| `--searchType` | 搜索类型 | `1`=名称，`2`=编码，`3`=规格条码，`4`=规格编码 |

### 筛选参数

| args 参数 | 说明 | 可选值 |
|-----------|------|--------|
| `--minSalePrice` | 最低价格 | - |
| `--maxSalePrice` | 最高价格 | - |
| `--goodsStatus` | 上下架状态 | `0`=上架，`1`=下架，`2`=已售罄 |
| `--isCanSell` | 可售状态 | `0`=不可售，`1`=可售 |

### 排序参数

| args 参数 | 说明 | 可选值 |
|-----------|------|--------|
| `--sort` | 排序方式 | `1`=销量，`2`=上下架时间，`3`=价格，`4`=排序值 |
| `--sortType` | 排序方向 | `0`=升序，`1`=降序 |

### 详情参数

| args 参数 | 说明 |
|-----------|------|
| `--goodsIdList` | 商品 ID 数组，如 `[102781859999837,102783709999837]`，用于按 ID 查详情 |

### 常用组合示例

```bash
# 基础分页
woscli admin-api query-goods-list --pageNum 1 --pageSize 20

# 按名称搜索
woscli admin-api query-goods-list --search "牛奶" --searchType 1

# 按编码搜索
woscli admin-api query-goods-list --search "SP001" --searchType 2

# 组合筛选：上架 + 可售 + 价格区间
woscli admin-api query-goods-list --goodsStatus 0 --isCanSell 1 --minSalePrice 10 --maxSalePrice 200

# 按销量降序
woscli admin-api query-goods-list --sort 1 --sortType 1
```

## 响应字段说明

### 商品列表字段

| 字段 | 说明 | 类型 |
|------|------|------|
| `goodsId` | 商品 ID | int |
| `title` | 商品标题 | string |
| `goodsCode` | 商品编码 | string |
| `goodsPrice.minSalePrice` | 最低销售价 | float |
| `goodsPrice.maxSalePrice` | 最高销售价 | float |
| `goodsStock.goodsStockNum` | 库存数量 | int |
| `isCanSell` | 是否可售 | bool |
| `isOnline` | 是否上架 | bool |
| `defaultImageUrl` | 商品图片 URL | string |
| `realSaleNum` | 商品销量 | int |
| `totalCount` | 总数量 | int |

## 使用场景

1. **搜索商品**: 通过关键词搜索商品（支持名称或编码）
2. **浏览商品列表**: 分页查询商品列表
3. **价格筛选**: 按价格区间筛选商品
4. **状态筛选**: 按上下架状态、可售状态筛选
5. **组合筛选**: 多条件组合查询（如：上架 + 可售 + 价格区间）
6. **销量排序**: 按销量排序查询商品（支持升序/降序）
