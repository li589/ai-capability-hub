# 互动域（interaction）

本文件覆盖打卡（`punch_card`）、考试（`exam`）、社区（`community.manage`）。投票问卷已部分迁移为 `live.interaction.form`（见 @references/live.md）。

> 通用流程模式、工具发现、确认规范见 @references/common.md。✎ 表示写工具，需 `confirmed=true`。所有工具 `InvokableOnly`，走 `search_tools`→`invoke_tool`。

## 互动域工具总览

| 子域 | 工具 |
|---|---|
| 打卡 | `add_and_configure_activity`✎ / `create_clock_chapter`✎ / `batch_add_task`✎ / `get_task_list` / `get_clock_activity_list` / `get_clock_conf` / `save_clock_conf`✎ |
| 考试 | `examination_list` / `create_exam`✎ / `paper_list` / `paper_detail` / `save_exam_paper`✎ / `publish`✎ |
| 社区 | 24 个（query/search/send_feeds/create/update/change_state/delete/owner/sell_config/member 系列，见 @references/common.md 元工具发现） |

## 打卡管理流程

1. `get_clock_activity_list` 查活动列表 → `get_clock_conf` 查当前配置 → `get_task_list` 查任务。
2. 对比→等确认。
3. `save_clock_conf`✎(confirmed) 保存配置 / `add_and_configure_activity`✎(confirmed) 创建活动 / `create_clock_chapter`✎(confirmed) 建章节 / `batch_add_task`✎(confirmed) 批量建任务。

> 坑：封面默认值固定；编辑前必须展示当前配置；`everyday_clock_count` 开关联动。`save_clock_conf` 是 AI 侧 fetch-merge——先 `get_clock_conf` 查完整配置再合并，未改字段透传。

## 考试创建发布 4 步链（核心）

来源：`xeclaw-exam-manage`。创建并发布考试是**多步骤流程，必须按顺序**：

1. **`create_exam`**✎(confirmed) 创建考试（`state=0` 草稿）。名称 ≤ 50 字；默认封面。
2. **`paper_list`** 查可选试卷 → **`paper_detail`** 看卷详情（需 `app_id`，从考试列表响应获取）。
3. **用户确认选哪张卷**（步骤间确认，不可跳）。
4. **`save_exam_paper`**✎(confirmed) 绑定试卷到考试。
5. **`publish`**✎(confirmed) 发布考试。

> 绑定试卷和发布考试之间，用户必须确认。名称 ≤ 50 字。

## 社区管理流程

1. `query_community_list`/`query_community_detail` 查。
2. 对比→等确认。
3. `create_community`✎/`update_community`✎/`change_community_state`✎/`change_community_owner`✎/`save_community_sell_config`✎/`update_community_member`✎/`extend_community_member_rights`✎/`add_community_member`✎/`remove_community_member`✎(confirmed)。
4. destructive（`delete_community`/`change_community_member_blacklist` 等）二次确认。

> 关联课程查询：`query_community_courses`/`query_community_course_overview`/`query_community_course_students`/`query_community_course_sections`（只读）。

## 可能未暴露的能力（以 search_tools 实时为准）

- **题库/练习册/练习题**：编写时尚未暴露，遇到诉求先 `search_tools` 探测；搜到照常走流程，搜不到告诉用户"当前未找到对应工具，可能尚未迁移或未对当前账号开放"，不假设永久不支持。
- **投票问卷**：已部分迁移为 `live.interaction.form`，流程在 @references/live.md「直播互动词与表单流程」。
