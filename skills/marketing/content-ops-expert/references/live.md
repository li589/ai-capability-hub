# 直播域（live）

本文件覆盖直播运营能力：直播管理、讲师、签到、红包、抽奖、任务奖励、自动营销、预告、直播间模块、优惠券、互动词/模板、互动表单、通知。

> 通用流程模式、工具发现、确认规范见 @references/common.md。本文件只写直播域特有流程与坑。✎ 表示写工具，需 `confirmed=true`。

## 直播域工具总览

| 子域 | 工具（read / ✎write） |
|---|---|
| 直播管理 | `live_list` / `live_detail` / `live_edit`✎ / `live_create`✎ |
| 讲师 | `live_teacher_list` / `live_teacher_search_candidates` / `live_teacher_search_user_by_phone`✎ / `live_teacher_batch_add`✎ / `live_teacher_edit`✎ / `live_teacher_delete_check` / `live_teacher_delete`✎destructive / `live_teacher_recent_list` |
| 签到 | `live_sign_interact_info` / `live_sign_timed_list` / `live_sign_set_switch`✎ / `live_sign_timed_add`✎ / `live_sign_timed_edit`✎ / `live_sign_timed_delete`✎ |
| 红包 | `query_red_packet_state` / `query_member_rate_switch` / `query_red_packet_level_membership_candidates` / `query_red_packet_tag_candidates` / `set_red_packet_on_after_confirmation`✎ / `set_point_red_packet_on_after_confirmation`✎ / `set_red_packet_default_config_after_confirmation`✎ / `set_red_packet_rule_after_confirmation`✎ |
| 抽奖 | `query_live_prize_info` / `query_live_prize_list` / `query_live_prize_history_list` / `create_live_prize_after_confirmation`✎ / `update_live_prize_after_confirmation`✎ / `disable_live_prize_after_confirmation`✎ / `set_live_prize_switch_after_confirmation`✎ |
| 任务奖励 | `live_task_reward_list` / `live_task_reward_detail` / `live_task_reward_toggle`✎ / `live_task_reward_create`✎ / `live_task_reward_edit`✎ / `live_task_reward_update_state`✎ |
| 自动营销 | 9 read：`live_auto_marketing_template_list`/`_template_message_list`/`_template_relation_list`/`_timed_message_list`/`_template_copy_check`/`_agreement_get` + `live_preview_config_get`/`live_teacher_recent_list`；8 ✎write：`_template_upsert`/`_template_message_upsert`/`_template_relation_create`/`_timed_message_upsert`/`_template_copy`/`_agreement_sign`/`_switch_update` + `live_room_module_config_update` |
| 优惠券 | `query_live_coupon_list` / `query_shop_coupon_catalog` / `query_live_market_config` / `set_coupon_switch`✎ / `add_coupon_to_live`✎ / `send_coupon_to_live`✎ / `remove_coupon_from_live`✎ / `update_coupon_state`✎ / `update_live_coupon_conf`✎ |
| 互动词/模板 | `live_interaction_comment_word_list`/`_add`✎/`_edit`✎/`_delete`✎ / `live_interaction_instructor_word_list`/`_add`✎/`_delete`✎ / `live_interaction_template_list`/`_add`✎/`_edit`✎/`_delete`✎ / `live_interaction_word_template_bind`✎/`_rebind`✎ |
| 互动表单 | `live_interaction_form_list`/`form_detail`/`answer_user_list`/`export_status`(read) / `form_create`✎/`form_update`✎/`form_publish`✎/`form_close`✎/`feature_update`✎/`export_create`✎ / `form_delete`✎destructive(暂不暴露) |
| 通知 | `live_notice_get_setting`/`_get_sms_balance`/`_get_msg_channel_state`(read) / `_set_sms`✎/`_set_wechat`✎/`_set_app`✎ |

> 多数子域工具为 `InvokableOnly`，不进 `tools/list`，先 `search_tools(domain="live.*")` 再 `invoke_tool`。直播间优惠券属 `live.coupon`（区别于店铺优惠券 `marketing.coupon`，见 @references/marketing.md）。

## 直播编辑流程

1. **查当前值**：`live_detail`（`alive_id` 前缀 `l_`）拿当前直播完整数据（`resource_info`/`goods_info`/`alive_module_conf` 等）。
2. **收集修改 + 合并**：`live_edit` 是**网关适配器内部 fetch-before-patch**（适配器自己先 `data.get` 再合并你传的 patch），你只传要改的字段即可；但你仍要拿步骤1结果做前后对比给用户。
3. **输出方案对比**：列"字段|当前值→修改后"表，停止等用户明确"确认"。
4. **调写工具 confirmed**：`live_edit`(confirmed=true)。

坑：
- `zb_stop_at`：fetch 响应是 string datetime，edit body 是 uint32 时长（秒），适配器负责转换；你传 datetime 字符串即可。
- live-bff 零值覆盖风险高（Go JSON 反序列化无法区分未传与显式置零），所以 fetch-before-patch 必需——但即便如此，你也应在步骤2只传真正要改的字段。

## 直播创建流程

1. 收集：`title`/`zb_start_at`/`zb_stop_at`(datetime) 等。
2. 对比/确认。
3. `live_create`(confirmed=true)。

约束：`channel_type` 默认 1、`operator_type` 注入 0（由 standard executor 注入，你不用传）；`zb_stop_at` datetime→秒由适配器转；`alive_id` 服务端生成，响应返回新 `alive_id`；后端无幂等键，重复创建生成新 `alive_id`。

## 直播讲师管理流程

来源：`eclaw-live-skills/packages/live-teacher`。4 场景：查询/添加/编辑/移除。

### 查询
`live_teacher_list`(alive_id) 拿讲师列表。

### 添加（手机号）
1. `live_teacher_search_user_by_phone`(confirmed) 按手机号查/补建用户。**坑：成功码是 `code=1` 不是 `0`**，别按 `code=0` 判成功。
2. 候选搜索走 `live_teacher_search_candidates`（read），不能用 `search_candidates` 替代 `search_user_by_phone` 的补建语义。
3. `live_teacher_batch_add`(confirmed) 批量添加。

### 编辑（先查再合并——核心坑）
1. **必须先 `live_teacher_list` 拿目标讲师完整原始 `role_info`**（无论用户是否给 user_id）。
2. 以原始 `role_info` 为基底，仅用用户提交值覆盖对应字段，**`role_info` 所有字段完整传入，不可遗漏未修改的必填字段**。
3. 对比→等确认。
4. `live_teacher_edit`(confirmed=true，参数 `{from_ai: true, alive_id, role_info: <合并后完整对象>}`)。

> 这是最容易翻车的点：只传要改的字段会导致后端清空未传字段。必须全字段透传。

### 移除（destructive，二次确认）
1. `live_teacher_delete_check` 预检查（返回能否删/影响）。
2. 复述"不可撤销"+ 二次确认。
3. `live_teacher_delete`(confirmed=true)。

## 直播签到设置流程

来源：`eclaw-live-skills/packages/live-sign`。5 场景：查询/设置开关与样式/添加定时签到/编辑/删除。

### 查询
`live_sign_interact_info`(alive_id) 拿当前签到设置（`is_sign_in_on`/`sign_in_type`/`sign_style.*` 等）。

### 设置开关与样式（先查当前值再合并——AI 侧 fetch-merge，核心坑）
1. `live_sign_interact_info` 查当前值作修改基础。
2. 根据用户意图确定要改的参数，在当前值基础上**仅覆盖用户指定字段，未提及字段保持当前值**，合并出完整参数。
3. 输出对比→等确认。
4. `live_sign_set_switch`(confirmed=true，参数为合并后的完整参数)。

> `live_sign_set_switch` 网关无内部合并适配器，必须 AI 自己合并完整参数，否则丢字段。

### 定时签到
- `live_sign_timed_list` 查列表。
- `live_sign_timed_add`(confirmed) / `live_sign_timed_edit`(confirmed) / `live_sign_timed_delete`(confirmed)。
- 坑：签到时长 ∈ [30 秒, 3 小时)；`start_at` 必须大于当前时间；只有 `act_status=1`（未开始）的定时签到才能编辑/删除；删除必须二次确认。

## 直播红包流程

1. 查：`query_red_packet_state`(alive_id) 查当前红包绑定状态；`query_red_packet_level_membership_candidates`/`query_red_packet_tag_candidates` 查候选人群；`query_member_rate_switch` 查会员等级开关。
2. 收集修改 + 合并（修改领取规则前必须先 `query_red_packet_state` 查当前绑定）。
3. 对比→等确认。
4. `set_red_packet_on_after_confirmation` / `set_point_red_packet_on_after_confirmation` / `set_red_packet_default_config_after_confirmation` / `set_red_packet_rule_after_confirmation`(confirmed=true)。

> Pangu 组件内部值（如 5/6/4）不能直接传后端，以后端枚举 `rule_type`(0/1/2/3) 为准。

## 直播抽奖流程

1. 查：`query_live_prize_info`/`query_live_prize_list`/`query_live_prize_history_list`。
2. 对比→等确认。
3. `create_live_prize_after_confirmation` / `update_live_prize_after_confirmation` / `disable_live_prize_after_confirmation` / `set_live_prize_switch_after_confirmation`(confirmed=true)。

> 抽奖写工具编写时为 `NotExposed + Internal`（创建缺少业务幂等证据），可能未对当前账号暴露；先 `search_tools("live_prize")` 探测，搜到照常走流程，搜不到告诉用户"当前未找到抽奖写操作对应工具"。

## 直播任务奖励流程

1. 查：`live_task_reward_list`/`live_task_reward_detail`。
2. 对比→等确认。
3. `live_task_reward_toggle`(confirmed) / `live_task_reward_create`(confirmed) / `live_task_reward_edit`(confirmed，仅未开始状态可编辑) / `live_task_reward_update_state`(confirmed，删除或结束任务)。

> 坑：活跃任务（`task_type=4`）和红包奖励（`reward_type=3`）在适配器 input validation 层拦截；组合任务子任务编码由适配器自动处理。会员等级/用户标签查询复用红包工具 `query_red_packet_level_membership_candidates`/`query_red_packet_tag_candidates`。

## 直播自动营销流程

9 read + 8 write，覆盖运营消息模板、定时消息、协议、总开关。典型流程：
- 模板：`live_auto_marketing_template_list` 查→`_template_upsert`(confirmed) 增改→`_template_message_list` 查消息→`_template_message_upsert`(confirmed)。
- 关联：`_template_relation_list` 查→`_template_relation_create`(confirmed)。
- 定时消息：`_timed_message_list`→`_timed_message_upsert`(confirmed)。
- 复制：`_template_copy_check`→`_template_copy`(confirmed)。
- 协议：`_agreement_get`→`_agreement_sign`(confirmed)。
- 总开关：`_switch_update`(confirmed)。
- 直播间模块配置：`live_room_module_config_update`(confirmed)。

## 直播预告流程

`live_preview_config_get`/`live_preview_list`/`live_preview_search` 查 → `live_preview_add`(confirmed)/`live_preview_remove`(confirmed)。

## 直播间优惠券流程

1. 查：`query_live_coupon_list`(alive_id) 查直播间已加券；`query_shop_coupon_catalog` 查店铺可选券；`query_live_market_config` 查营销互动配置。
2. 对比→等确认。
3. `add_coupon_to_live`(confirmed)/`send_coupon_to_live`(confirmed)/`remove_coupon_from_live`(confirmed)/`set_coupon_switch`(confirmed, 显示/隐藏)/`update_coupon_state`(confirmed)/`update_live_coupon_conf`(confirmed, 改默认配置)。

> 坑：`coupon_interact_set` 添加/删除/开关必须先查完整列表再提交完整列表（禁止只传增量）；`coupon_conf` 是字符串化 JSON；`couponSwitchOptimizeGray` 灰度场景注意。

## 直播互动词与表单流程

### 互动词/模板
`live_interaction_comment_word_list`/`_add`/`_edit`/`_delete`（评论词）；`live_interaction_instructor_word_list`/`_add`/`_delete`（讲师词）；`live_interaction_template_list`/`_add`/`_edit`/`_delete`（模板）；`live_interaction_word_template_bind`/`_rebind`（绑定/重绑）。均为 confirmed 写。

### 互动表单（投票/问卷，create→publish→close→export 链）
1. `live_interaction_form_list`/`form_detail` 查。
2. `live_interaction_form_create`(confirmed) 创建（草稿）。
3. `live_interaction_form_update`(confirmed) 编辑。
4. `live_interaction_form_publish`(confirmed) 发布。
5. `live_interaction_form_close`(confirmed) 关闭。
6. `live_interaction_answer_user_list`/`export_status` 查答题；`live_interaction_export_create`(confirmed) 导出。
7. `live_interaction_feature_update`(confirmed) 功能开关。
- `live_interaction_form_delete` 是 destructive，暂不暴露。

## 直播通知流程

1. `live_notice_get_setting` 查当前通知配置；`live_notice_get_sms_balance` 查短信余额；`live_notice_get_msg_channel_state` 查渠道状态。
2. 对比→等确认。
3. `live_notice_set_sms`(confirmed)/`live_notice_set_wechat`(confirmed)/`live_notice_set_app`(confirmed)。

## 可能未暴露的能力（以 search_tools 实时为准）

以下能力编写时尚未在网关暴露，但 MCP 会持续迁移——遇到相关诉求**先 `search_tools` 探测**：搜到照常走流程，搜不到（1-2 次合理关键词后）告诉用户"当前未找到该能力对应的工具，可能尚未迁移为 MCP 或未对当前账号开放"，不假设永久不支持、不找替代硬套：

- **复制直播**（`copy_live` 等）、**转播直播**、**直播场控**（field_control F1-F12）、**回放剪辑**（highlight_clip H1-H12）。

> 复制直播的"方案确认+异步轮询"范式已提炼进 SKILL.md 通用流程作参考。直播护航（start/stop/summary/health/list_escorts）属 `live-escort` Skill，不在本文件。
