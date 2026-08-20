---
name: merchant-store
description: 商户与门店查询助手，支持查询可访问商户列表、门店组织节点、店铺经营数据概览与店铺待办事项。触发词：查商户、查门店、看店铺概览、看待办、经营指标。
displayName:
  zh: 商户与门店查询
  en: Merchant and Store Search
displayDescription:
  zh: 查询可访问商户、门店组织节点、店铺经营概览和待办事项，帮助快速了解当前店铺状态。
  en: Search accessible merchants, store organization nodes, business overviews, and to-do items to quickly understand the current store status.
---

# 门店与商户

## 功能说明

本 skill 让 WAI 代表商家查询商户与门店基础信息，以及当前店铺的经营数据概览和待办事项，结果全部来自微盟商家后台真实接口（`woscli admin-api`）。

| 能力 | 命令 | 产出 |
|---|---|---|
| 商户列表 | `woscli admin-api query-merchants` | 可访问商户候选列表 |
| 门店列表 | `woscli admin-api query-stores` | 商户下门店/组织节点列表 |
| 店铺数据概览 | `woscli admin-api query-shop-data` | 当前或指定店铺经营指标 |
| 店铺待办 | `woscli admin-api query-shop-todo` | 当前或指定店铺待办事项 |

### 前置条件

- 当前登录态、商户、门店上下文由 Weimob Assistant 上层统一提供，woscli 自动注入。
- 本 skill 不负责获取或写入会话级上下文数据，只查询候选项或当前上下文下的数据。
- **重要：只能查询当前店铺的数据，禁止使用其他店铺的 bos_id、vid 等标识进行查询。**

## 触发场景

- 查商户、看有哪些商户、确认可选商户、按名称搜商户
- 查门店、看某商户下有哪些门店、按名称搜门店、看组织节点
- 看店铺概览、看当前店铺经营情况、店铺有哪些指标
- 看待办、今天有什么待办、待处理事项有多少

## 调用方式

```bash
woscli admin-api <command> [args]
```

### 通用调用约定

- 命令入口：`woscli admin-api <command> [args]`，底层为微盟商家后台真实接口，由 woscli 统一处理登录态、商户、门店上下文。
- 命令与能力对应：`query-merchants`、`query-stores`、`query-shop-data`、`query-shop-todo`。
- 依赖上层提供登录态、当前商户、当前门店；缺失时按命令返回提示上层补齐。

### 能力路由

| 用户意图 | 处理方式 |
|---|---|
| 查商户、确认可选商户 | `query-merchants`，可加 `--name` 模糊搜索 |
| 查门店、看某商户下门店 | `query-stores`，可加 `--vidName` |
| 看经营指标、店铺概览 | `query-shop-data`，默认使用当前上下文 |
| 看待办、待处理事项 | `query-shop-todo --merchantId <商户ID>`，必须显式传入商户 ID |
| 要趋势、同环比、排行分析 | 不属于本 skill，转数据分析能力 |

## 支持的操作

### 1. 商户列表查询（query-merchants）

用途：当用户要“查商户”“确认可选商户”时获取商户列表。

| 参数 | 说明 |
|---|---|
| `--name` | 商户名称关键词，可模糊搜索 |

```bash
woscli admin-api query-merchants --name '华东'
```

### 2. 门店列表查询（query-stores）

用途：当用户要“查门店”“看某商户下有哪些门店”时使用。

| 参数 | 说明 |
|---|---|
| `--vidName` | 门店/组织节点名称关键词 |

```bash
woscli admin-api query-stores --vidName '上海'
```

商户与门店命令的完整字段说明见 `@references/merchant-store.md`。

### 3. 店铺数据概览（query-shop-data）

用途：查看店铺经营数据概览，适合“看当前店铺经营概览”“店铺指标有哪些”。

| 参数 | 说明 |
|---|---|
| `--vidPath` | 节点路径（可选）；不传时使用当前上下文 |

```bash
woscli admin-api query-shop-data
```

### 4. 店铺待办查询（query-shop-todo）

用途：查看店铺待办事项，适合“今天有什么待办”“待处理事项有多少”。

| 参数 | 说明 |
|---|---|
| `--merchantId` | 商户 ID，**必填**；从当前上下文或 `query-merchants` 结果获取 |

```bash
woscli admin-api query-shop-todo --merchantId 2000000746837
```

店铺概览与待办的完整字段说明见 `@references/shop-overview.md`。

### 5. 工作流

1. 若用户要看当前店铺经营情况，直接查询 `query-shop-data` 或 `query-shop-todo --merchantId`，优先使用当前上下文。
2. 若用户要确认商户或门店范围，先用 `query-merchants` / `query-stores` 列出候选。
3. 若缺少商户或门店上下文，明确提示上层补齐后再继续。

## 输出格式

### query-merchants 返回字段

| 字段 | 说明 |
|---|---|
| `bosId` | 商户 ID |
| `merchantName` | 商户名称 |
| `migrated` | 是否已迁移 |

### query-stores 返回字段

| 字段 | 说明 |
|---|---|
| `vid` | 门店/节点 ID |
| `vidType` | 门店/节点类型 |
| `vidName` | 门店名称 |
| `vidTypeName` | 门店类型名称 |

### query-shop-data 返回字段

| 字段 | 说明 |
|---|---|
| `metrics` | 指标明细，含 `key`、`name`、`value`、`productId` |

### query-shop-todo 返回字段

| 字段 | 说明 |
|---|---|
| `todos` | 待办列表，含 `itemKey`、`name`、`count`、`order`、`jumpUrl` |

### 回复要求

- 仅基于命令返回结果作答，不捏造、不补全指标或待办数量。
- 不向用户暴露 token、bosId、vid。
- 若已知当前商户/门店名称，回答结尾附带当前商户与门店。

## 注意事项/边界

- 本 skill 只做查询，不做商户或门店的创建、修改、启停等写操作。
- `query-shop-data` 与 `query-shop-todo` 依赖完整的商户/门店上下文；`query-shop-todo` 的 `--merchantId` 为必填，缺失时不要猜测或用其他店铺标识补位，直接提示上层补齐。
- `query-merchants` / `query-stores` 返回的是候选列表，不代表已切换上下文；切换商户或门店由上层负责。
- 店铺概览指标是后台看板口径的即时值，不提供趋势、同环比、排行等分析；此类诉求转交数据分析能力。
- 不要把 `query-stores` 返回的组织节点一律当作实体门店，`vidType` / `vidTypeName` 可能表示区域或分组节点。
