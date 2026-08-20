---
name: guide-management
description: 导购交易与业绩明细查询助手，支持按业绩类型(销售/专属/发货)、订单来源、用户昵称、商品名称、订单号筛选。触发词：查导购线索、导购业绩、销售业绩、专属业绩、发货业绩、导购交易明细。
displayName:
  zh: 导购业绩管理
  en: Sales Associate Performance Management
displayDescription:
  zh: 查询导购交易与业绩明细，支持按业绩类型、订单来源、客户、商品和订单信息进行筛选。
  en: Review sales-associate transactions and performance details, filtered by performance type, order source, customer, product, and order information.
---

# 导购管理

## 功能说明

本 skill 让 WAI 代表商家查询导购交易与业绩明细，结果全部来自微盟商家后台真实接口（`woscli guide`），返回的是后台明细列表而非 BI 汇总分析。

| 能力 | 命令 | 产出 |
|---|---|---|
| 导购交易/线索明细 | `woscli guide query_guider_trade_list_v2` | 分页导购交易明细（按用户昵称/商品名/订单号筛选） |
| 导购业绩明细 | `woscli guide query_guider_trade_list_v2` | 分页导购业绩明细（按业绩类型分类） |

### 前置条件

- 当前登录态、商户、门店上下文由 Weimob Assistant 上层统一提供，woscli 自动注入。
- 本 skill 不负责获取或写入会话级上下文数据。
- **重要：只能查询当前店铺的数据，禁止使用其他店铺的 bos_id、vid 等标识进行查询。**

## 触发场景

- 查导购线索、导购交易明细、看某笔订单的导购归属
- 查导购业绩、销售业绩、专属业绩、发货业绩
- 按用户昵称查导购交易、按商品名查关联导购
- 按订单来源（内部/外部）筛选导购交易

## 调用方式

```bash
woscli guide query_guider_trade_list_v2 [args]
```

### 通用调用约定

- 命令入口：`woscli guide query_guider_trade_list_v2`，底层为微盟商家后台真实接口，由 woscli 统一处理登录态、商户、门店上下文。
- 该命令**不支持时间范围筛选**（无 startTime/endTime 参数）；如需按时间范围查看业绩汇总，转数据分析能力。
- 业绩类型通过 `--performanceType` 区分：`0=全部`、`1=销售业绩`、`2=专属业绩`、`3=发货业绩`。
- 依赖上层提供登录态、当前商户、当前门店；缺失时按命令返回提示上层补齐。

### 能力路由

| 用户意图 | 处理方式 |
|---|---|
| 导购线索、导购交易明细、某订单的导购 | `query_guider_trade_list_v2`，按 `--tradeNo`/`--nickname`/`--goodsTitle` 筛选 |
| 导购业绩、销售/专属/发货业绩 | `query_guider_trade_list_v2`，传 `--performanceType 1/2/3` |
| 按订单来源（内部/外部）筛导购交易 | `--orderSource 1/2` |
| 导购绩效汇总、同环比、BI 图表 | 不属于本 skill，转数据分析能力 |

## 支持的操作

### 1. 导购交易/线索明细查询

用途：查询导购交易明细，适合“导购线索”“某用户的导购交易”“某商品的关联导购”“某订单的导购归属”。

| 用途 | 关键参数 |
|---|---|
| 按用户昵称筛选 | `--nickname`（模糊匹配） |
| 按商品名称筛选 | `--goodsTitle`（模糊匹配） |
| 按订单号筛选 | `--tradeNo`（整数） |
| 按订单来源筛选 | `--orderSource`：`0=全部`、`1=内部订单`、`2=外部订单` |
| 业绩类型 | `--performanceType 0`（全部，默认） |
| 分页 | `--pageNum`、`--pageSize` |

```bash
# 全部导购交易明细（第一页）
woscli guide query_guider_trade_list_v2 --pageNum 1 --pageSize 20
# 按用户昵称查导购交易
woscli guide query_guider_trade_list_v2 --nickname '小明' --pageNum 1 --pageSize 20
# 按订单号查导购归属
woscli guide query_guider_trade_list_v2 --tradeNo 123456789
# 按商品名 + 内部订单
woscli guide query_guider_trade_list_v2 --goodsTitle '牛奶' --orderSource 1
```

### 2. 导购业绩明细查询

用途：按业绩类型查看导购业绩明细，适合“销售业绩”“专属业绩”“发货业绩”。

| 用途 | 关键参数 |
|---|---|
| 销售业绩 | `--performanceType 1` |
| 专属业绩 | `--performanceType 2` |
| 发货业绩 | `--performanceType 3` |
| 全部业绩 | `--performanceType 0`（默认） |
| 分页 | `--pageNum`、`--pageSize` |

```bash
# 销售业绩明细
woscli guide query_guider_trade_list_v2 --performanceType 1 --pageNum 1 --pageSize 20
# 专属业绩 + 按用户昵称
woscli guide query_guider_trade_list_v2 --performanceType 2 --nickname '小明'
# 发货业绩 + 外部订单
woscli guide query_guider_trade_list_v2 --performanceType 3 --orderSource 2
```

完整参数枚举与返回字段见 `@references/guide-trade-detail.md`。

### 3. 工作流

1. 判断用户意图是查交易明细还是业绩明细，选择对应筛选参数。
2. 执行命令，直接使用命令真实返回结果回复。
3. 若缺少认证、商户或门店上下文，明确提示上层补齐后再继续。

## 输出格式

### query_guider_trade_list_v2 返回

- `paginationData`：分页数据
  - `totalCount`：总记录数
  - `pageNum`、`pageSize`、`nextPage`
  - `pageList`：当前页数据列表（导购交易/业绩明细项）
- `categoryList`：业绩类型筛选项集合（含“全部”）
- `performanceTypeList`：业绩类型筛选项集合（不含“全部”）
- `orderSourceList`：订单来源筛选项集合

### 回复要求

- 只返回命令真实结果，交易/业绩数据不得自行补全或估算。
- 若已知当前商户/门店名称，回答结尾附带当前商户与门店。
- 业绩类查询回答中注明业绩类型口径（销售/专属/发货）。

## 注意事项/边界

- 本 skill 返回后台明细列表，**不是 ChatBI 汇总分析**；导购绩效汇总、同环比、图表类诉求转交数据分析能力。
- 该命令不支持时间范围筛选；用户提到“本周/本月业绩”时，说明此限制并转数据分析能力，或仅返回当前可查的全部明细。
- 交易/业绩数据包含用户昵称、订单号等敏感字段，自然语言回复只展示完成任务所需信息。
- 不向用户暴露 token、bosId、vid 等内部标识。
- 本 skill 不做写操作，不支持分配线索、修改跟进状态、调整业绩归属。
