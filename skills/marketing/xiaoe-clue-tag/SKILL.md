---
name: xiaoe-clue-tag
description: 小鹅通线索打标
  skill。当需要给客户/线索打标签、查看企微标签或店铺标签、创建店铺标签、编辑企微标签、校验标签名是否重复时使用。适用于"给这个客户打标""有哪些标签""建个标签""企微标签怎么改""标签名重了吗"等场景。含
  3 个写操作（带确认机制）与 4 个只读操作。
license: Internal
disable-model-invocation: true
---

# 小鹅通线索打标

## Overview

通过 xiaoe-cloud MCP 操作当前授权店铺的 CRM 标签体系，覆盖三个服务：企微标签（admin-wework-scrm）、店铺标签（crowd）、客户打标（scrm-customer-manage）。写操作带确认机制：不带 `confirmed` 只返回确认摘要不落库，带 `confirmed: true` 才真正派发。

## 调用方式

通过 xiaoe-cloud MCP 的 `invoke_tool` 调用，`tool_name` 传工具名，`arguments` 传参数对象。`app_id` / `b_user_id` 由网关 Session 自动注入，**不要**在参数中传店铺/操作者身份。

## 工具清单

### 读操作（4 个，无副作用，直接调用）

#### 1. crm_corp_tag_list — 企微标签列表

无必填参数。

**返回要点：** 标签组数组，每组含 `tag_group_id`、`tag_group_id_name`、`tags` 数组（每项含 `tag_id` / `tag_name`）。例：客户等级组（核心/重要/一般）。

#### 2. crm_corp_tag_edit_status — 企微标签编辑状态

无必填参数。

**返回要点：** 当前标签组状态，结构与 `crm_corp_tag_list` 相同（均为标签组列表）。

#### 3. crm_shop_tag_list — 店铺标签列表

无必填参数（分页默认 page=1 / page_size=20）。

**返回要点：** `tag_list` 数组 + `total_count` 总数。

#### 4. crm_shop_tag_name_check — 店铺标签重名校验

**必填参数：**
- `tag_name`：要校验的标签名

**返回要点：** `is_repeated`（0 = 不重复可创建，1 = 已重复）。

### 写操作（3 个，带确认机制）

#### 5. crm_shop_tag_create — 创建店铺标签

**必填参数：**
- `tag_name`：标签名
- `tag_type`：标签类型

**可选参数：**
- `tag_behavior_condition`：行为条件对象

#### 6. crm_corp_tag_edit — 编辑企微标签

**必填参数：**
- `tag_group_type`：标签组类型
- `tag_group_id`：标签组 ID（从 `crm_corp_tag_list` 获取真实值）
- `tag_group_id_name`：标签组名称
- `tag_add`：新增标签名数组
- `sort`：完整标签排序列表——**必须包含该组全部现有标签（带真实 `tag_id`/`tag_name`）+ 新增项**，否则参数校验失败

**示例：**
```json
{
  "tag_group_type": 1,
  "tag_group_id": "ettJxhBgAAV2MeWlUghIjHONE7iL3nQg",
  "tag_group_id_name": "客户等级",
  "tag_add": ["测mcp0818c"],
  "sort": [
    {"tag_id": "ettJxhBgAATg6kX0oQiBPlfCibKjSGqw", "tag_name": "核心"},
    {"tag_name": "测mcp0818c"}
  ]
}
```

#### 7. crm_tag_mark — 客户打标

**必填参数：**
- `external_id`：客户外部 ID
- `tags`：标签名数组

**示例：**
```json
{
  "external_id": 123456789,
  "tags": ["etXXX"]
}
```

## 确认机制（写操作通用）

1. 调用写操作时**不带** `confirmed` 字段 → 返回确认摘要（含将要执行的参数），**不真正落库**；
2. 将摘要展示给用户确认后，带 `confirmed: true` 重新调用 → 才真正派发执行。

## 业务流程

1. 查现有标签 → `crm_corp_tag_list`（企微）/ `crm_shop_tag_list`（店铺）；
2. 创建店铺标签前查重 → `crm_shop_tag_name_check`；
3. 创建店铺标签 → `crm_shop_tag_create`；
4. 编辑企微标签 → 先 `crm_corp_tag_list` 拿真实 `tag_id`，构造完整 `sort` 后调 `crm_corp_tag_edit`；
5. 给客户打标 → `crm_tag_mark`。

## 注意事项

- **连接器可能抖动**：并行调用可能触发重连断连（"reconnected but was disconnected again"），失败后**串行重试**；
- `crm_corp_tag_edit` 的 `sort` 必须完整（全部现有标签 + 新增项），`tag_id` 需先从 `crm_corp_tag_list` 获取真实值，不能凭空构造；
- `crm_shop_tag_name_check` 参数名是 `tag_name`（不是 `name`）；
- 写操作默认不带 `confirmed` 只返回摘要，**确认落库前务必向用户展示摘要**；
- 勿在测试店铺 `6986AI助理专用【勿动！！】`（app55kclpvt6986）执行真实落库操作。
