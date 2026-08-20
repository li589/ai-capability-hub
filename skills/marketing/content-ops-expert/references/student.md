# 学员/会员域（student）

本文件覆盖用户查询（`user.*`）、权益（`user.entitlement`）、会员卡/超级会员。

> 通用流程模式、工具发现、确认规范见 @references/common.md。✎ 表示写工具，需 `confirmed=true`。权益/会员工具 `InvokableOnly`，走 `search_tools`→`invoke_tool`。

## 学员/会员域工具总览

| 子域 | 工具 |
|---|---|
| 用户查询(只读) | `user_list` / `user_basic_info` / `user_entitlement_list` / `user_course_progress` / `user_learning_data` |
| 权益(只读) | `user_entitlement_resource_users` / `user_entitlement_range_config` / `user_entitlement_range_list` / `user_entitlement_live_users` |
| 权益(写) | `user_entitlement_extend_expiration`✎ / `user_entitlement_range_update`✎ |
| 会员卡(只读) | `membership_card_list` / `super_member_list` |

## 用户查询流程

1. `user_list` 查用户列表（支持 `user_type_ext`=会员等级ID、来源、消费、访问、组织、状态筛选排序分页）。
2. `user_basic_info`(`target_user_id`) 查详情基本信息。
3. 按需深入：
   - `user_entitlement_list`(`target_user_id`, 权益状态 0/1/2, 分页 1..50) 查权益；
   - `user_course_progress`(`target_user_id`) 查课程进度（返回 `total + goods_list`）；
   - `user_learning_data`(`target_user_id`) 查学习总览+按日趋势（默认近 7 天、最多 30 天、截至昨天；聚合 num=1 与 num=2，任一失败整体失败）。

> `target_user_id` 是业务字段，adapter 内映射到后端 `user_id`；`app_id`/登录 `user_id`/`b_user_id`/`user_merchant_id` 由网关 session 派生注入，不暴露也不向用户索要。`user_basic_info` 走 `getUserInfo`（管理台 V2 的门店归属等新字段暂不可用，属已知缺口）。

## 权益管理流程

1. `user_entitlement_resource_users`/`range_list`/`live_users` 查当前权益范围与用户。
2. 对比→等确认。
3. `user_entitlement_extend_expiration`✎(confirmed) 延长有效期 / `user_entitlement_range_update`✎(confirmed) 更新范围。

> 延长有效期有上限，超限可能异步处理，以工具返回为准；永久有效用户会被自动剔除。AI 侧 fetch-merge：编辑前先查完整范围再合并。

## 会员卡与超级会员流程

1. `membership_card_list` 查会员卡（返回 `svip_id + type` 卡片项；同 `svip_id` 的体验/正式卡可区分）。
2. `super_member_list`(`svip_id` + `card_type`) 查所选卡片下会员列表。

> **字段映射**（adapter 固定派生，AI 不传 `identity_type`）：
> - `membership_card_list` 的 `svip_id + type` → `super_member_list` 的 `svip_id + card_type`；
> - `card_type=1` → `identity_type=2`，`card_type=2` → `identity_type=1`。
> - URL 无选择时管理台自动选中首卡；剩余有效期钳制 `0..3650`；未选卡片/反向生日区间/`is_wework_customer=3` 但未选员工会在派发前拒绝。

## 可能未暴露的能力（以 search_tools 实时为准）

以下能力编写时为 Internal design guard 或未暴露，但以 `search_tools` 实时为准——遇到诉求先搜：搜到照常走流程，搜不到告诉用户"当前未找到对应工具，可能尚未迁移或未对当前账号开放"，不假设永久不支持：

- **权益撤销/取消**（`batch_revoke_equity` 等 destructive）。
- **购买记录删除**（destructive）。
- **添加/导出/贴标签/联系/移除等按钮能力**（write/export，本批仅 read）。
