# 店铺概览与待办参考（query-shop-data / query-shop-todo）

## 命令

| 命令 | 能力 |
|---|---|
| `woscli admin-api query-shop-data` | 查询当前或指定店铺经营数据概览 |
| `woscli admin-api query-shop-todo` | 查询当前或指定店铺待办事项（需 `--merchantId`） |

## query-shop-data

用途：查看店铺数据概览，适合“看当前店铺经营概览”“店铺指标有哪些”。

### 参数

| 参数 | 说明 |
|---|---|
| `--vidPath` | 节点路径（可选）；不传时使用当前上下文 |

### 返回字段

| 字段 | 说明 |
|---|---|
| `metrics` | 指标明细，包含 `key`、`name`、`value`、`productId` |

### 示例

```bash
woscli admin-api query-shop-data
woscli admin-api query-shop-data --vidPath '4000172354837/...'
```

## query-shop-todo

用途：查看店铺待办事项，适合“今天有什么待办”“待处理事项有多少”。

### 参数

| 参数 | 说明 |
|---|---|
| `--merchantId` | 商户 ID，**必填**；从当前上下文或 `query-merchants` 结果获取 |

### 返回字段

| 字段 | 说明 |
|---|---|
| `todos` | 待办列表，包含 `itemKey`、`name`、`count`、`order`、`jumpUrl` |

### 示例

```bash
woscli admin-api query-shop-todo --merchantId 2000000746837
```

## 注意

- `query-shop-todo` 的 `--merchantId` 为必填，缺失时不要猜测或用其他店铺标识补位。
- 概览指标为后台看板口径的即时值，不提供趋势、同环比、排行等分析。
