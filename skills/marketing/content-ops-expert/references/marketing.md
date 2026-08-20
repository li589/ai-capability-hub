# 营销域（marketing）

本文件覆盖店铺优惠券（`marketing.coupon`）和商品分组（`goods.group`）。直播间优惠券属 `live.coupon`，见 @references/live.md。

> 通用流程模式、工具发现、确认规范见 @references/common.md。✎ 表示写工具，需 `confirmed=true`。

## 营销域工具总览

| 子域 | 工具 | 上线状态 |
|---|---|---|
| 优惠券只读 | `marketing_coupon_list`(Listed) / `marketing_coupon_group_list`(InvokableOnly) | ✅ 已上线 |
| 优惠券其余 | `marketing_coupon_group_relation_update`✎ / `marketing_coupon_price_display_get` / `marketing_coupon_price_display_update`✎ / `marketing_coupon_reissue`✎(Internal) / `marketing_coupon_effect_detail` / `marketing_coupon_effect_summary` / `marketing_coupon_effect_product_list` / `marketing_coupon_effect_user_list` / `marketing_coupon_settings_get` / `marketing_coupon_create`✎ / `marketing_coupon_update`✎ | 编写时可能未进生产可调用集，用前先 `search_tools` 确认；搜到照用，搜不到告诉用户当前未找到 |
| 商品分组 | `goods_group_list` / `goods_group_products` / `goods_group_create`✎ / `goods_group_update`✎ / `goods_group_batch_set_resources`✎（均 InvokableOnly） | ✅ 已上线 |

## 优惠券查询流程

`marketing_coupon_list` 查优惠券列表（支持 `activity_state` 活动状态、`discount_type` 折扣类型等筛选）→ `marketing_coupon_group_list` 查分组。

> 金额单位是**分**展示为元两位小数；折扣是 ×10（如 8.5 折 = 85）；`activity_state`/`discount_type` 枚举以工具返回为准。

## 优惠券创建流程（先确认工具是否可调）

1. `marketing_coupon_list` 查基线（看同类券参数）。
2. **先 `search_tools("coupon create")` 确认 `marketing_coupon_create` 是否可调**。若搜不到 → 答"优惠券创建暂未上线（待后续 Ticket）"，不要硬调、不要用其他工具硬套。
3. 若可调：`describe_tool("marketing_coupon_create")` 看必填 → 收集 → 对比 → `marketing_coupon_create`(confirmed=true)。

> 创建最小提交体；金额元→分；折扣×10；指定商品范围走商品分组能力（见下）。

## 优惠券编辑流程（先查基线再合并——AI 侧 fetch-merge）

1. `marketing_coupon_settings_get`(若可调) 查当前设置基线。
2. 合并：仅覆盖用户指定字段，**未改字段透传**。
3. 对比→等确认。
4. `marketing_coupon_update`(confirmed=true)。

> `marketing_coupon_update` 网关无内部合并适配器，必须 AI 自己合并完整提交体。若 `settings_get`/`update` 搜不到，答"优惠券编辑暂未上线"。

## 优惠券分组与价格展示

`marketing_coupon_group_list` 查 → `marketing_coupon_group_relation_update`✎(confirmed)/`marketing_coupon_price_display_update`✎(confirmed)。

## 优惠券效果分析（只读）

`marketing_coupon_effect_detail`/`effect_summary`/`effect_product_list`/`effect_user_list` 查效果数据（若可调）。

## 商品分组流程

1. `goods_group_list` 查列表 → `goods_group_products` 查分组内商品。
2. 对比→等确认。
3. `goods_group_create`✎/`goods_group_update`✎/`goods_group_batch_set_resources`✎(confirmed=true)。

> AI 侧 fetch-merge：编辑先查完整分组再合并全字段。

## 可能未暴露的能力（以 search_tools 实时为准）

以下能力编写时尚未在网关暴露，但 MCP 会持续迁移——遇到相关诉求**先 `search_tools` 探测**：搜到照常走流程，搜不到（1-2 次合理关键词后）告诉用户"当前未找到该能力对应的工具，可能尚未迁移为 MCP 或未对当前账号开放"，不假设永久不支持、不反复换词硬搜：

- **限时折扣**（`limit_discount_*`）、**秒杀**（`seckill_*`）、**邀请码**、**兑换码**、**优惠券作废/发放**（`reissue` 等 destructive，当前为 Internal design guard）。

> **关键**：不得用 `marketing_coupon_*`（店铺优惠券）硬套限时折扣/秒杀场景——它们是不同业务能力，参数语义不同。用户要限时折扣/秒杀时，先 `search_tools("limit_discount")`/`("seckill")` 探测；搜不到就说"当前未找到限时折扣/秒杀对应工具"，不要拿优惠券工具替代。
