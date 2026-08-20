# 导购交易/业绩明细查询参考（query_guider_trade_list_v2）

> 底层命令为 `woscli guide query_guider_trade_list_v2`，由 woscli 统一处理登录态、商户、门店上下文。

## 参数词典

| 参数 | 类型 | 说明 |
|---|---|---|
| `--performanceType` | integer | 业绩类型：`0=全部`、`1=销售业绩`、`2=专属业绩`、`3=发货业绩`（默认全部） |
| `--orderSource` | integer | 订单来源：`0=全部`、`1=内部订单`、`2=外部订单` |
| `--tradeNo` | integer | 订单号，按具体订单筛选 |
| `--goodsTitle` | string | 商品名称，支持模糊匹配 |
| `--nickname` | string | 用户昵称，支持模糊匹配 |
| `--pageNum` | integer | 页码，从 1 开始 |
| `--pageSize` | integer | 每页条数 |

> 该命令**不支持时间范围筛选**（无 startTime/endTime 参数）。

## 业绩类型（--performanceType）

| 值 | 含义 |
|---|---|
| `0` | 全部 |
| `1` | 销售业绩 |
| `2` | 专属业绩 |
| `3` | 发货业绩 |

## 订单来源（--orderSource）

| 值 | 含义 |
|---|---|
| `0` | 全部 |
| `1` | 内部订单 |
| `2` | 外部订单 |

## 返回结构

- `paginationData`：分页数据
  - `totalCount`：总记录数
  - `pageNum`：当前页码
  - `pageSize`：每页条数
  - `nextPage`：是否还有下一页
  - `pageList`：当前页数据列表（导购交易/业绩明细项）
- `categoryList`：业绩类型筛选项集合（含“全部”），每项含 `code`、`name`
- `performanceTypeList`：业绩类型筛选项集合（不含“全部”），每项含 `code`、`name`
- `orderSourceList`：订单来源筛选项集合，每项含 `code`、`name`

## 示例

```bash
# 全部导购交易明细（第一页）
woscli guide query_guider_trade_list_v2 --pageNum 1 --pageSize 20
# 按用户昵称查导购交易
woscli guide query_guider_trade_list_v2 --nickname '小明' --pageNum 1 --pageSize 20
# 按订单号查导购归属
woscli guide query_guider_trade_list_v2 --tradeNo 123456789
# 销售业绩明细
woscli guide query_guider_trade_list_v2 --performanceType 1 --pageNum 1 --pageSize 20
# 专属业绩 + 外部订单
woscli guide query_guider_trade_list_v2 --performanceType 2 --orderSource 2
# 发货业绩 + 按商品名
woscli guide query_guider_trade_list_v2 --performanceType 3 --goodsTitle '牛奶'
```
