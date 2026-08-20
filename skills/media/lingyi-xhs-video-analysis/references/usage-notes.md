# 小红书爆款短视频拆解 · 信息收集与交付约定

本文件补充 SKILL.md 的「信息收集」「扣点与确认」「输出交付」细节，供 assistant 执行时对照。

## 1. 输入字段表

| 参数 | 必填 | CLI | 说明 |
|------|------|-----|------|
| 小红书分享链接 | 二选一 | `--share-url URL` | 小红书**视频笔记**链接。常见形态见 api.md §2.1。图文笔记会失败 |
| 本地视频文件 | 二选一 | `--video-file PATH` | 脚本自动走预签名上传三步换 `video_id`。扩展名 `.mp4`/`.mov`/`.m4v`/`.mkv`/`.webm`/`.avi`，上限 200MB |
| 已上传 video_id | 二选一 | `--video-id ID` | 已有 `video_id` 直传创建（已上传过时用） |
| industry | 否 | `--industry` | 行业，如 `beauty`。可引导不强制、缺省不传 |
| campaign_type | 否 | `--campaign-type` | 活动类型。可引导不强制、缺省不传 |
| account_size | 否 | `--account-size` | 账号体量。可引导不强制、缺省不传 |
| 报告标题 | 否 | `--title` | `--poll-task`/`--retry-task` 时显式指定；缺省按 `--share-url`（或 video 文件名）推断 |

> 三个输入参数（`--share-url` / `--video-file` / `--video-id`）**互斥**，给多个会被脚本拒绝（退出码 3）。

## 2. 两条输入分支流程

### 分支一·小红书分享链接（首选）
1. 收到用户的小红书视频笔记链接（视频笔记，非图文）
2. 扣点确认后创建：
   `python3 scripts/analyze_xhs_video.py --share-url "<链接>" --only-create`
3. 轮询：
   `python3 scripts/analyze_xhs_video.py --poll-task <id> --share-url "<链接>" --out ./小红书拆解报告.md`

### 分支二·本地视频文件
1. 引导用户提供本地视频文件路径（用户可在输入框粘贴 ⌘V 提供路径；中性文案，不写「检测是否在 WorkBuddy」）
2. 扣点确认后创建（脚本此步先走预签名上传三步拿 `video_id` 再创建任务）：
   `python3 scripts/analyze_xhs_video.py --video-file "<路径>" --only-create`
3. 轮询（建议带 `--share-url` 或 `--title` 做报告标题；本地文件分支可传 `--title "<文件名>"`）：
   `python3 scripts/analyze_xhs_video.py --poll-task <id> --title "<标题摘要>" --out ./小红书拆解报告.md`

> 本地上传任一步（预签名/直传/确认）失败，脚本按对应退出码终止（多为 3/8/10/11）。

## 3. 交互节奏（拆分轮询，防会话中断）

- **禁同步一把梭**：异步拆解约 1–2 分钟，WorkBuddy/Web 单轮对话有时长上限。一律「创建（`--only-create`）+ 多次短轮询（`--poll-task`，单次 ≤90s）」。
- **创建后立即告知用户**：用 task_id 诚实告知「已提交，任务 ID xxx，约 1–2 分钟，有进展同步给你」。**不承诺**「完成后自动取回」。
- **每轮轮询都先回一句话进度**，再决定下一步：
  - 退出码 0 → 进入「输出交付」
  - 退出码 13（进行中，**非失败、不返还**）→ 取 stdout 进度转述，**立刻再跑一次 `--poll-task`** 继续，循环到终态
  - 退出码 12 → 失败话术 + 可 `--retry-task`/重创建
  - 退出码 2/3/4/8/10/11 → 按退出码处理
- **用户问进度**：取最近一次 `--poll-task` 的 `XHS_VIDEO_STATUS`/`XHS_VIDEO_PROGRESS` 自然转述；过一会儿可再 `--poll-task` 现查。**禁止**「查不了/没有 task_id」。

## 4. 交付约定（成功时三步，缺一不可）

1. **渲染报告**：截 `=== XHS_VIDEO_REPORT_START ===` 与 `=== XHS_VIDEO_REPORT_END ===` 之间的 Markdown，**真正渲染**给用户（标题/表格/列表/分隔线），不展示分隔符行与 `XHS_VIDEO_*=` 协议行，不贴带 `\n` 的原文。过长至少完整渲染前 2–3 个二级标题段并说明完整报告已落盘。
2. **告知扣点**：看 `XHS_VIDEO_POINTS_USED`——非空「本次实际扣除 N 点」；空（本 API 常为空）「约 128 点（实际以服务端扣点为准，可在 01Claw 账户查看）」。
3. **告知查看方式**：报告已渲染上方 + 已保存为 MD 文件，路径见 `XHS_VIDEO_REPORT_FILE`（三级兜底落盘：`--out` → 当前目录 → `/tmp`，终态有 markdown 就一定生成 md 文件）。

> 报告正文由后端渲染，skill 不做模板、不改 table；顶级 `# 小红书拆解报告：<摘要>` 由脚本生成。最终 MD 由脚本一次性覆写 `--out`，agent 不手动追加/改写。

## 5. 失败处理口径

- **未发起到位（2/3/4/8/10）**：不涉扣点，引导修正/取 key/充值。
- **已发起未出报告（11/12）**：统一告知「因网络原因本次任务执行失败，相应点数已返还」并问是否重试；有 task_id 可 `--retry-task`（若服务端支持）或重新创建。
- **13（进行中）**：非失败、不返还，立即续 `--poll-task`。
- 未知状态/错误**不自行判定失败**，按退出码表对号入座、透出 stderr 原因。
