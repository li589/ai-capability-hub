---
name: hosted-task
description: 查询与关闭已有托管任务，仅支持查询和关闭，不支持创建或开启。触发词：托管任务、查看托管、托管状态、关闭托管、取消托管、库存预警、待发货提醒、公众号托管、朋友圈托管、批量下架。
displayName:
  zh: 托管任务管理
  en: Managed Task Management
displayDescription:
  zh: 查询已有托管任务及其状态，并支持关闭或取消库存预警、待发货提醒、内容托管和批量下架等任务。
  en: View existing managed tasks and their status, then close or cancel inventory
    alerts, shipping reminders, content automation, and bulk unlisting tasks.
disable-model-invocation: true
---

# 托管任务查询与关闭

## 功能说明

本 skill 通过 `woscli hosted-task` 管理**已存在**的托管任务，能力范围只有两项：

| 操作 | 说明 |
|---|---|
| `QUERY` | 查询现有托管任务的配置与运行状态 |
| `CLOSE` | 在用户明确确认后，关闭现有托管任务 |

> **注意**：本 skill 名称在部分历史目录中包含 "creater"，属于命名遗留，与实际能力无关。**本 skill 不具备任何创建能力。**

### 明确不支持的意图（硬边界）

不支持创建、新建、开启、打开、启用、修改、编辑托管任务或托管配置。识别到这类意图时，直接说明当前端暂不支持该操作并终止流程：

- 不得收集任何创建/开启所需参数。
- 不得调用 `openHostModal`、`createScheduledTask` 或任何其他创建、开启、修改类工具（这些工具在本端不可用）。
- 不得把「开启/创建/修改」意图降级或改写成「先查询再继续操作」。

## 触发场景

- 查询类：我有哪些托管任务、托管任务开着吗、看下库存预警托管的状态、公众号托管配置是什么、查一下朋友圈托管。
- 关闭类：关闭库存预警托管、把待发货提醒托管停掉、取消小红书托管、关掉批量下架任务。
- 反向场景（应拒绝并终止）：开启公众号托管、新建一个客户关怀托管、帮我改一下托管的执行时间。

## 调用方式

本 skill 只允许使用以下两个命令，不得调用任何未在此列出的托管任务命令。

### 查询任务

```bash
woscli hosted-task queryScheduledTask --taskCode <任务编码> --taskCategory <任务分类>
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `--taskCode` | 是 | 任务编码，取值见「支持的操作」中的任务类型表 |
| `--taskCategory` | 是 | 任务分类，取值 `ASSET` / `CONTENT` / `CUSTOM` |

`taskCode` 与 `taskCategory` 必须同时传入。

### 关闭任务

按用户确认的实例关闭（推荐）：

```bash
woscli hosted-task closeTask --taskInstanceIdList '["task_xxx","task_yyy"]'
```

用户明确要求并确认关闭该类型的全部任务时，可按任务编码关闭：

```bash
woscli hosted-task closeTask --taskCode <任务编码>
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `--taskInstanceIdList` | 二选一 | JSON 数组字符串，ID 必须来自 `queryScheduledTask` 的实际返回 |
| `--taskCode` | 二选一 | 按任务编码整类关闭，需用户明确确认「全部关闭」 |

`taskCode` 与 `taskInstanceIdList` 至少传一个。

## 支持的操作

### 支持的托管任务类型（共 8 类）

| 任务编码 | 任务名称 | 任务分类 |
|---|---|---|
| `stock_warning` | 商品库存不足预警 | `ASSET` |
| `pending_shipment_reminder` | 待发货订单提醒 | `ASSET` |
| `after_sales_reminder` | 售后订单提醒 | `ASSET` |
| `customer_festival_reminder` | 客户关怀 | `ASSET` |
| `wechat_official_account` | 公众号托管 | `CONTENT` |
| `red_book` | 小红书托管 | `CONTENT` |
| `friend_circle` | 朋友圈托管 | `CONTENT` |
| `goods_batch_offline` | 批量下架商品 | `CUSTOM` |

无法从用户表述中确定任务类型时，向用户询问需要查询或关闭哪一种任务，**不得自行选择或推测**。

### QUERY 执行流程

1. 识别任务编码与任务分类；缺失或不明确时向用户追问。
2. 调用 `queryScheduledTask`。
3. 权限不足时立即终止（见下方权限规则）。
4. 如实返回查询结果，不得虚构任务、实例 ID、配置或状态。

### CLOSE 执行流程

1. 识别任务编码与任务分类；缺失或不明确时向用户追问。
2. 先调用 `queryScheduledTask` 获取最新任务列表。
3. 权限不足或没有可关闭任务时立即终止。
4. 只有一条记录时，展示该任务及其 `taskInstanceId`，并询问用户是否确认关闭。
5. 有多条记录时，逐条展示 `taskInstanceId` 供用户选择，要求用户明确指定；**不得代替用户选择**。
6. **仅在当前上下文中拿到用户明确确认后**才调用 `closeTask`。
7. 如实返回关闭结果。

### 权限规则

若 `queryScheduledTask` 返回内容包含「暂无权限」「暂无操作权限」或「无权限」，立即终止流程并返回 `PERMISSION_DENIED`，不得继续调用 `closeTask`，不得重试或绕行。

## 输出格式

- **查询结果**：以列表或表格呈现任务名称、`taskInstanceId`、运行状态与关键配置，字段值全部来自命令返回。
- **关闭确认**：关闭前必须先输出待关闭任务清单（含 `taskInstanceId`）并提出确认问题，不得在同一轮内自行确认并执行。
- **关闭结果**：如实说明成功/失败的任务实例，失败时给出返回的原因说明。
- **权限不足**：返回 `PERMISSION_DENIED` 并简要说明需要联系管理员开通权限，然后终止。
- **不支持的意图**：一句话说明「当前端暂不支持创建/开启/修改托管任务」，不追问参数、不给替代执行路径。

## 注意事项/边界

- 只允许执行 `QUERY` 和 `CLOSE` 两类操作。
- 关闭属于写操作，调用 `closeTask` 前必须获得当前上下文中的**明确二次确认**，历史轮次的确认不可复用。
- 所有 `taskInstanceId` 必须来自 `queryScheduledTask` 的实际返回结果，禁止编造或凭记忆填写。
- 禁止使用 `openHostModal`；该工具在本端不可用。
- 禁止调用未在本 skill 中定义的托管任务命令。
- 命令返回为空时如实告知「未查询到相关托管任务」，不得虚构结果。
