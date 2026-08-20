# 课程内容域（course）

本文件覆盖课程、内容资产（视频/音频/图文/电子书）、章节、专栏、训练营的内容管理能力。

> 通用流程模式、工具发现、确认规范见 @references/common.md。✎ 表示写工具，需 `confirmed=true`。

## 课程内容域工具总览

| 子域 | 工具（read / ✎write） |
|---|---|
| 课程 | `course_list` / `course_detail` / `course_student_list` / `course_update`✎ / `course_create`✎ |
| 资产详情 | `video_detail` / `audio_detail` / `image_text_detail` / `ebook_detail` |
| 资产编辑 | `video_update`✎ / `audio_update`✎ / `image_text_update`✎ / `ebook_update`✎ |
| 资产创建 | `video_create`✎ / `audio_create`✎ / `image_text_create`✎ / `ebook_create`✎ |
| 资产列表 | `course_resource_list` |
| 章节 | `course_chapter_list` / `chapter_update`✎ / `chapter_sort_update`✎ / `chapter_create`✎ / `chapter_batch_create`✎ / `sub_course_create`✎ |
| 专栏(只读) | `course_column_list` / `course_column_detail` / `course_column_catalog` / `course_column_entitled_user_list` / `course_column_learning_summary` / `course_column_learning_product` / `course_column_learning_users` / `course_column_user_chapter_learning` |
| 训练营 | ~38 个（见下「训练营管理流程」，工具名以 `search_tools`/`describe_tool` 为准） |

> 旧脚本工具名（`get_course.sh`/`update_goods_info.sh`/`update_training_pro.sh`/`create_course.sh` 等）**已不存在，不得调用**，必须用网关工具名 `course_detail`/`course_update`/`course_create`。

## 课程编辑流程

来源：`xeclaw-create-course` 子流程C（旧 `get_course.sh`→`update_goods_info.sh`+`update_training_pro.sh`）。

1. **查当前值**：`course_detail`(resource_id, 前缀 `course_`) 拿当前课程完整内容（基本信息/售卖设置/课程目录）作基线。
2. **收集修改 + 合并**：`course_update` 是**网关适配器内部 fetch-before-patch**——适配器先调 `resource.detail.get`/`goods.info.get`/`belong.user.get`/`courseware.list.get` 读取现有完整数据，再合入你传的 patch，调 `training_pro.update`。你只传要改的字段即可（patch 语义）；但仍要用步骤1结果做前后对比。
3. **输出方案对比**：列"字段|当前值→修改后"表，停止等用户明确"确认"。
4. **调写工具 confirmed**：`course_update`(confirmed=true)。

> 适配器内部合并避免字段缺失导致覆盖；但提交前务必向用户确认变更。

## 课程创建流程

来源：`xeclaw-create-course` 子流程A（旧 `create_course.sh`）。

1. 收集：`title`、`sale_type`(1=付费)、`normal_price`(分，如 99 元=9900) 等。
2. 对比→等确认。
3. `course_create`(confirmed=true) → 返回新 `resource_id`。

约束：网关默认创建为 `sale_status=0` 暂不上架（避免 MCP 创建后意外上架）；`app_id`/`user_id`/`client_ip`/`request_source` 由 session 派生注入。

## 内容资产编辑流程

四类资产（video/audio/image_text/ebook）的 `_detail` 查 + `_update`✎ 改。`_update` 均为**网关适配器内部 fetch-before-patch**：适配器先调对应 `*.info.get`/`goods.info.get`/`belong.user.get` 读现有数据，重组为 `course`+`content` 对象，合入 patch，再调 `*.update`。

通用流程：
1. `video_detail`/`audio_detail`/`image_text_detail`/`ebook_detail`(resource_id) 拿当前值。
2. 合并 patch（只传要改字段）。
3. 对比→等确认。
4. `video_update`/`audio_update`/`image_text_update`/`ebook_update`(confirmed=true)。

**字段交叉映射坑（每类不同，必须记）**：

| 资产 | 坑 |
|---|---|
| `audio_update` | **audio_size 单位反转**：fetch 返回 KB，saveCourse 后端做 /1024，基底 `content.audio_size` 必须 fetch 值 ×1024，否则每次保存缩小 1024 倍。不支持换音频文件（涉及转码）。 |
| `image_text_update` | **字段重命名**：fetch 返回字段 `content` 需映射到 `course.descrb`（控制器再复制回 `course.content`）；**基底 `content_type` 必须取 fetch 真实值**（`content_type=0` 会触发控制器清空试看字段）。 |
| `ebook_update` | **字段交叉映射（与 video/audio 完全不同）**：fetch `author`→`course.summary`，fetch `summary`→`course.descrb`，fetch `org_summary`→`course.org_content`；`file_from` 不从 fetch 提取，后端从 `epub_url` 扩展名自动推导。 |
| `video_update` | fetch 返回扁平结构，适配器重组为 `course`+`content` 再合并 patch，避免 `course.title`/`img_url`/`descrb` 未传被写空。不支持换视频文件/课件资料/高级配置。 |

## 内容资产创建流程

四类 `_create`✎，无 fetch-before-patch，复用 `course_create` 模板。必填字段：

| 资产 | 必填字段 |
|---|---|
| `video_create` | `title`, `summary`, `description`, `cover_img_url`, sale 相关；content 首版不暴露视频文件替换 |
| `audio_create` | `title`, `audio_url`, `file_name`, `audio_size`(BYTES), `audio_length`, sale 相关 |
| `image_text_create` | `title`, `try_content`, `try_org_content`, `can_select`, `try_content_url`, `content_type`, sale 相关 |
| `ebook_create` | `title`, `epub_url`, `eigenvalue`, `total_chapters`, `words_count`, `total_size`, `is_try`, `try_chapters`, `summary`, `description`, `cover_img_url`, sale 相关 |

流程：收集→对比→`*_create`(confirmed=true)。`app_id`/`user_id`/`client_ip`/`request_source` 由 session 注入。

## 章节管理流程

5 个章节写工具，**全部无 fetch-before-patch，直接 POST**：

| 工具 | 接口 | Input 要点 | idempotent |
|---|---|---|---|
| `chapter_update`✎ | `camp_pro.chapter.update` | `chapter_id`, `course_id`, `chapter_title`(≤30字), `confirmed` | true（覆盖） |
| `chapter_sort_update`✎ | `camp_pro.chapter.sort.update` | `course_id`, `tree`(opaque JSON 全量), `sub_course_id`(默认""), `catalog_add_head`(可选), `confirmed` | true（全量 tree 覆盖） |
| `chapter_create`✎ | `camp_pro.chapter.create` | `course_id`, `chapter_title`, `sub_course_id`(可选), `confirmed` | false（不返回 chapter_id） |
| `chapter_batch_create`✎ | `camp_pro.chapter.batch.create` | `course_id`, `p_id`, `resource_type`, `chapter_info`([{chapter_id,chapter_title}], **max 200**), `sub_course_id`(可选), `confirmed` | false |
| `sub_course_create`✎ | `camp_pro.sub.course.create` | `course_id`, `sub_course_title`, `sub_course_img`(可选), `confirmed` | false |

查询：`course_chapter_list`(course_id 必填) 返回章节+小节扁平全量（含 `chapter_type:2` 小节）；`course_resource_list`(resource_type 必填 1=图文,2=音频,3=视频,20=电子书; page_size 1-50; sale_status∈{-1,0,1,2}) 查资产列表。

流程：`course_chapter_list` 拿当前目录→收集→对比→等确认→对应写工具(confirmed=true)。

## 专栏管理

8 个只读工具（见总览表）。专栏写操作（编辑/删除/上下架等）编写时尚未暴露，但以 `search_tools` 实时为准——遇到相关诉求先搜：搜到照常走流程，搜不到告诉用户"当前未找到专栏写操作对应工具，可能尚未迁移或未对当前账号开放"，不假设永久不支持。

## 训练营管理流程

约 38 个工具（`InvokableOnly`，工具名以 `search_tools(domain=...)`/`describe_tool` 为准）。典型流程：

1. **查询**：`query_training_camp_list` 查列表 → `query_training_camp_info` 查详情 → `query_training_camp_term_list`/`term_detail` 查期次 → `query_training_camp_student_list` 查学员 → `query_training_camp_single_user_progress`/`user_progress_detail` 查进度。
2. **创建**：`create_training_camp`(confirmed) → `save_training_camp_term`(confirmed) 建期。
3. **编辑**：`update_training_camp_title`(confirmed)/`update_training_camp_operation_settings`(confirmed)/`update_training_camp_share_diy`(confirmed)。
4. **期次管理**：`copy_training_camp_term`(confirmed)/`delete_training_camp_term`(confirmed)/`sort_training_camp_term`(confirmed)/`set_training_camp_term_recycle_state`(confirmed)/`save_training_camp_term`(confirmed)/`cancel_training_camp_audit`(confirmed)。
5. **学员管理**：`add_training_camp_student`(confirmed)/`extend_training_camp_student_expiration`(confirmed)/`check_training_camp_student_can_remove`→`remove_training_camp_student`(confirmed)。
6. **删除**：`delete_training_camp`(confirmed，destructive 二次确认)。

> 各流程均走"查基线→对比→confirmed=true"。`app_id` 等由 session 注入；学员移除前先 `check_*_can_remove` 预检查。
