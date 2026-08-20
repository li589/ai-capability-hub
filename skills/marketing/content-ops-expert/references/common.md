# 通用能力（common）

本文件是内容运营专家的通用底座：工具发现、短链解析、素材上传、微页面、数据分析、知识库问答、通用确认与错误恢复规范。其他域文件引用本文件的确认与路由规范。

## 元工具三步路由详解

网关 `xiaoe` 有约 200 个工具，`tools/list` 只直出常用，非常用走三步路由：

1. **`search_tools`**：按关键词搜当前会话可调用的内部工具，返回工具名、标题、描述、领域、风险等级。
   - `query`：匹配 `display_name`/`description`/`search_keywords`/`business_capability_id`，大小写不敏感。
   - `domain`：按 `business_capability_id` 前缀过滤（如 `user.entitlement`/`goods.group`/`live.interaction.form`/`data_analysis.live`），**大小写敏感**。
   - `limit`：最大 20。
2. **`describe_tool`**：按 `tool_name` 返回目标工具说明和 `input_schema`，用于组装参数。
3. **`invoke_tool`**：携带 `tool_name` + `arguments` 发起实际调用。
   - 目标为 write 时，`confirmed` 必须与 `tool_name`/`arguments` 同级传入；缺失或 `false` 只返回确认摘要且不派发业务调用，用户确认后传 `true`。
   - **`invoke_tool` 不允许以元工具（`search_tools`/`describe_tool`/`invoke_tool` 自身）为目标**，避免递归套娃。

可见性边界：
- `Internal`/不在默认能力集/`InvokableOnly` 的工具不进 `tools/list`，也不会在 `search_tools`/`describe_tool` 泄露 schema。合理关键词搜 1-2 次仍搜不到 = 该能力不在当前会话 Tool View，如实告诉用户"当前未找到该能力对应的工具，可能尚未迁移为 MCP 或未对当前账号开放"，不反复换词硬搜、不假设永久不支持（MCP 会持续迁移，下次可能就有）。
- 富 UI 工具：`invoke_ui_tool`（卡片入口）、`invoke_ui_panel_tool`（侧栏看板，仅 workbuddy channel；`_meta.workbuddy.ui.launchSurface: "panel"`）。

## 资源 ID 与短链解析

### `resource_surl_parse`
从短链或长链 URL 提取小鹅通资源 ID 并识别类型。

- 入参：`url`（必填）。`app_id` 由网关 session 派生注入 `Xe-Ad-Gw-Appid` header。
- 短链（含 `/s/`、`/st/`、`/sl/`）：调一次 `POST /xe.live.bff_b/surl/query/1.0.0` 拿 long_url，再本地前缀解析。
- 长链：直接本地前缀解析，不调上游（无 `business_upstream_call`）。
- 长链资源 ID 前缀识别：`l_`直播 / `i_`图文 / `a_`音频 / `v_`视频 / `e_`电子书 / `p_`专栏 / `g_`实物商品 / `term_`训练营期 / `c_`社群 / `ac_`打卡 / `cr_`分销商品 / `s_`超级会员 / `bclass_`大班课 / `course_`课程。

用户给的是链接而不是 ID 时，先调 `resource_surl_parse` 解析出 `{resource_id, resource_type}`，再喂给后续工具。

## 素材上传流程

### `material_select`（只读）
素材中心列表（图片/音频/视频/电子书/文档）。入参 `material_type=image|audio|video|ebook|document`（映射管理台 `type=1..5`）。

### `material_upload_prepare` + `material_upload_complete`（写，需 confirmed）
上传图片/音频/电子书/文档（视频上传编写时尚未支持，先 `search_tools("material upload")` 确认是否有视频上传工具；若调用返回视频不支持的错误，提示用户视频走素材中心管理台手动上传）：

1. `material_upload_prepare`（confirmed）→ 返回 COS 预签名上传凭证（`upload_mark`/`sign_mark`）。
2. 本地直传文件到腾讯 COS 对象存储。
3. `material_upload_complete`（confirmed）→ 用 prepare 返回的 `uploaded_url`（必须是 prepare 后本地上传得到的 HTTPS 腾讯 COS 对象域名，HTTP/非 COS/带凭证/可重定向 URL 会被出网前拒绝）+ 配套 `upload_mark`/`sign_mark` 登记完成。

约束：`source_id` 固定 `i1xet29Lvp6fF`（不暴露给 MCP input）；`app_id`/`user_id`/`b_user_id` 由网关派生注入。视频 `material_type=video` 在 prepare/complete 阶段返回参数错误，提示走管理台。

## 微页面流程

先调 **`micro_page_guide`**（System Tool，不进 Registry，认证会话始终可见）取设计 prompt + 按当前会话可见工具生成的有序工作流数组 + 全局规则。读它再操作微页面：

- `micro_page_create`（write，`duplicate_tolerant`，confirmed）：当前店铺组件+全部图片素材校验→`page.save(micro_page_id=0)`→返回结果。
- `micro_page_get`（read）：`page.get`→严格反向投影完整 normalized PageSpec + `source_hash`。
- `micro_page_update`（write，`business_idempotent`，confirmed）：先 `page.get` + `expected_source_hash` 比较→净新增图片素材校验→`page.save(同一 micro_page_id)`。

关键约束：
- `update` 是**完整目标替换非 patch**；`source_conflict`（`source_hash` 冲突）必须重新 `page.get` 完整旧 PageSpec、本地合并、人工审阅，再重新取得摘要并确认。
- `unknown_result` 必须**停止自动 retry/save**并人工核验。
- 本地 HTML preview 不经过网关，不是保存成功/素材归属/业务有效性的证明；成功固定表达 `business_validity_status=not_verified`。

## 数据分析只读工具索引

`data_analysis.*` 共 15 个只读工具，全部 `InvokableOnly`，走 `search_tools(domain="data_analysis.*")` 发现。各子域：

- `data_analysis.live`：直播数据（select_alive_info、get_live_data）。
- `data_analysis.course_learning`：课程学习（query_course_students、query_learning_statistics、search_resource）。
- `data_analysis.clue`：线索（get_crm_info、get_valid_scope_users、get_clue_wechat_stats、get_alive_distribute_price）。
- `data_analysis.series_course`：系列课数据（list_data_apis 拿 catalog、query_data 按 domain+action 取数）。
- `data_analysis.member_catalog`：会员目录（query_course_student_list、get_column_catalog、get_sub_course_list）。
- `data_analysis.playback`：回放（get_lookback_file_list、get_lecturer_live_duration_list、get_all_guest_list）。

注意：`customization-data-export-tool`（远程沙箱导出 Excel）编写时尚未迁移；如用户要"导出数据成文件"，先 `search_tools("export")` 探测是否有导出工具；搜不到则告知用户当前未找到导出工具，可查询数据后自行整理。

## 知识库问答

- `knowledge_qa_retrieve`：知识库检索（`ai-knowledge` 服务）。
- `knowledge_qa_search_docs`：帮助中心搜索（`merchant-service`）。

均只读、`InvokableOnly`。用户问"店铺知识库/帮助文档"类问题走这两个。

## 通用确认与错误恢复规范

### confirmed 预检语义
- 写工具入参带 `confirmed`（走 `invoke_tool` 时与 `tool_name`/`arguments` 同级）。
- `confirmed=false`/缺省 → 网关返回 `confirmation_required` + 确认摘要，**零业务上游调用**。
- `confirmed=true` → 真正执行业务调用。
- 主流程：AI 自己出对比表→等用户明确"确认"→一次带 `confirmed=true` 调；不必先发 `confirmed=false` 试探（那只是网关兜底）。

### 参数变更重新确认
用户改了任何关键参数 → 重新对比、重新确认，不能拿旧 confirmed 提交。

### 错误恢复
- `unknown_result`：停止自动 retry/save，人工核验（可能已成功也可能未派发，需查上游实际状态）。
- `validation_failed`：停止自动重试，读错误摘要修正参数后重新走确认流程；注意该状态不保证零上游（已确认 update 可能先完成 `page.get`/组件读取再因动态校验终止）。
- `confirmation_required`：正常未确认状态，补 confirmed 即可，不算错误。

### destructive 操作
- 仅用户主动触发；先 `*_check` 预检查（如 `live_teacher_delete_check`/`check_training_camp_student_can_remove`）→复述"不可撤销"→二次确认→`confirmed=true`。
- destructive 能力（权益撤销/购买记录删除/商品分组删除/专栏写等）编写时为 `Internal` design guard，但以 `search_tools` 实时为准——遇到诉求先搜；搜到照常走流程，搜不到告诉用户"当前未找到对应工具，可能尚未迁移或未对当前账号开放"，不假设永久不支持。

### 旧脚本工具名已不存在
eclaw 源里的旧脚本型工具（`xeclaw-*`/`*.sh`，如 `get_course.sh`/`update_goods_info.sh`/`create_course.sh`）已不存在，**不得尝试调用**，必须用网关工具名（`course_detail`/`course_update`/`course_create` 等）。不确定工具名时先 `search_tools`。
