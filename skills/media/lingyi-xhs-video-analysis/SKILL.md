---
name: lingyi-xhs-video-analysis
display_name: 小红书爆款短视频拆解
display_name_en: Xiaohongshu Viral Video Teardown
description_zh: 【零一数科·出品】小红书爆款短视频拆解（付费版）。输入一条小红书视频笔记链接（或本地视频文件），异步拆解爆款结构并输出
  Markdown 拆解报告。拆小红书爆款、小红书视频拆解、小红书爆款拆解、短视频拆解、拆解小红书爆款。需要 python3 和技能目录下
  config.json 中的 LY_API_KEY。
description_en: "[Lingyi Tech] Xiaohongshu Viral Video Teardown. Submit a
  Xiaohongshu (RED) video note by share-link or local file; the backend tears
  down the viral structure asynchronously and returns a Markdown report.
  Triggers: 小红书视频拆解, 小红书爆款拆解, 短视频拆解. Requires python3 and LY_API_KEY in skill
  config.json."
category: 内容
version: 0.1.0
author: 小风、CoderPig、Awen
disable-model-invocation: true
---

# 小红书爆款短视频拆解
> 版本：v0.1.0 · 作者：小风、CoderPig、Awen

<!-- 偏差说明：本 API 与标准「01Claw 异步任务」范式基本一致（创建/轮询/扣点结算），有三点差异，脚本已据实适配，详见 references/api.md：
1) 任务 id 字段为 `data.analysis_task_id`（非 `task_id`）——脚本统一经该字段读取。
2) 无 `data.billing.total_points`/`data.recharge_url` 字段——扣点为前置约定「每次新创建任务成功完成扣 128 点」，余额不足以 HTTP 402 + 服务端 message 透出（无充值链接）；脚本 `XHS_VIDEO_POINTS_USED` 常为空，按「约 128 点」回退说明。
3) 重试端点 `POST .../{id}/retry` 未在本 API 文档中明示——脚本按统一异步范式保留 `--retry-task`，若服务端不支持会以 4xx 透出，届时优先 `--poll-task` 续查或重新创建。 -->

给一条小红书视频笔记链接，或一段本地视频文件，拆出爆款的套路结构。后端把视频转写后做结构化拆解，渲染成一段 Markdown 报告（基础信息、内容结构、节奏与钩子、亮点与可复用点等），直接交付给用户，同时回告本次扣点。本地视频走预签名上传三步换 `video_id` 后再拆，链接则直拆。

通过 **异步拆解接口** 提交：`POST /api/v1/social-analytics/collector/xiaohongshu-video-analyses` **立即返回 `analysis_task_id`**，再通过 `GET .../xiaohongshu-video-analyses/{analysis_task_id}` 轮询进度与结果。`completed` 后从 `data.result.markdown` 取报告。接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

## 执行流程

按以下顺序执行，每一步都对应后续章节细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **收集信息**：与用户确认输入——小红书视频笔记链接（首选）或本地视频文件路径；可选行业/活动类型/账号体量（可引导不强制、缺省不传）。详见「信息收集」。
3. **扣点确认（必做，跳过不得）**：跑脚本**前**向用户说明「本次任务预计扣点约 128 点，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
4. **拆分轮询（关键，防会话中断）**：异步拆解通常跑 1–2 分钟，WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成。改成「创建 + 多次短轮询」：
   a. **创建**：
      - 链接：`python3 scripts/analyze_xhs_video.py --share-url "https://www.xiaohongshu.com/explore/..." --only-create`
      - 本地视频：`python3 scripts/analyze_xhs_video.py --video-file "/path/to/note.mp4" --only-create`（脚本会在此步先走预签名上传三步拿 `video_id` 再创建任务）

      立即拿 `XHS_VIDEO_TASK_ID` + `XHS_VIDEO_STATUS` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。**
   b. **告知用户**：用 task_id 诚实告知，例如「已提交，任务 ID xxx，约 1–2 分钟。我会持续跟踪进度，有进展同步给你。」**不要**承诺「完成后自动取回」——单轮阻塞做不到自动续接，要靠你主动循环轮询续接。
   c. **循环轮询**：立即跑 `python3 scripts/analyze_xhs_video.py --poll-task <id> --share-url "<同 a 的链接>" --out ./小红书拆解报告.md`（单次 ≤90s）。**`--poll-task` 建议带上与创建时相同的 `--share-url`（或用 `--title` 指定），用于生成报告标题摘要**。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态成功）：进入「输出交付」。
      - **退出码 13**（仍进行中，**非失败**）：取 stdout 的 `XHS_VIDEO_STATUS` / `XHS_VIDEO_PROGRESS` / `XHS_VIDEO_EAPSED` 转述，**立刻再跑一次 `--poll-task <id> --share-url "..."`** 继续。不要停。
      - **退出码 12**（任务真失败）：按「退出码处理」走失败话术；有 task_id 可先 `--retry-task` 试，或重新创建。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。
   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」。
5. **进度应答**：用户中途问进度时，取最近一次 `--poll-task` 返回的状态自然转述；距上次轮询过一会儿可再跑一次现查。**禁止**回复「查不了任务状态 / 没有 task_id」。
6. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知实际扣点与查看方式。报告 markdown 由后端渲染，直接呈现，不二次加工。
7. **失败处理**：见「退出码处理」——非发起阶段失败（2/3/4/8）按对应话术；已发起但失败（11/12）告知「因网络原因本次任务执行失败，相应点数已返还」。退出码 13 **不是失败**，按第 4c 步续轮询。

任一步异常按「退出码处理」表对号入座，**不要自行判定失败**。

## 鉴权

Token 取「技能目录」（SKILL.md 所在目录）下 `config.json` 的 `LY_API_KEY` 字段，回退环境变量 `LY_API_KEY`。请求头 `Authorization: Bearer <api_key>` + `X-Appbuilder-From: openclaw`。`config.json` 形如：

```json
{ "LY_API_KEY": "你的密钥" }
```

运行前先确认 key：

1. **检查是否已有 key**：读 `config.json` 的 `LY_API_KEY` 是否非空；无则看环境变量 `LY_API_KEY`。任一有值即就绪。
2. **缺失则引导用户获取**：前往 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy` 取 API Key，把 key 直接发给你；收到后写入 `config.json` 的 `LY_API_KEY` 字段（保留其它内容）再继续。该文件已被 `.gitignore` 忽略。
3. **鉴权失败（退出码 8）**：key 失效或过期，重新获取并覆盖写 `config.json` 后重试，不反复用同一失效 key。
4. **SSL 错误**：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用）。

## 信息收集

两条输入分支，**必填其一**：

- **分支一·小红书分享链接（首选）**：要小红书**视频笔记**链接。常见形态：
  - `https://www.xiaohongshu.com/explore/<note_id>`
  - `https://www.xiaohongshu.com/discovery/item/<note_id>`
  - `https://xhslink.com/...` 短链
  - ⚠️ 要**视频笔记**，图文笔记没有可拆的视频文件，任务可能失败。收到链接后转 `--share-url` 传入。
- **分支二·本地视频文件**：用户有本地视频，需先上传再拆解。引导用户将本地视频复制后在输入框粘贴（⌘V）提供文件路径；脚本经预签名上传三步自动换 `video_id`。扩展名支持 `.mp4`/`.mov`/`.m4v`/`.mkv`/`.webm`/`.avi`，上限 200MB（以服务端实际校验为准）。收到路径后转 `--video-file` 传入。

可选增强参数（**可引导但不强制、缺省不传**，走后端默认）：

- `industry`：行业（如 `beauty`），帮拆解读更贴合行业。
- `campaign_type`：活动类型。
- `account_size`：账号体量。

字段对照与节奏详见 [references/usage-notes.md](references/usage-notes.md)。

## 扣点与确认

本技能每次「新发起」拆解任务成功完成后扣点（前置约定 **128 点**），轮询已有任务不重复扣点，余额不足创建接口返回 402、任务不创建、不扣点：

- **执行前确认（必做，跳过不得）**：信息收集完成、API Key 就绪后，运行脚本**前**向用户说明并请其确认：
  > 本次任务预计扣点约 **128 点**，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准。是否继续？
  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。
- **执行成功后回告实际扣点**：把脚本透出的 `XHS_VIDEO_POINTS_USED` 告诉用户。本 API 无结算扣点字段，该值常为空——空时按「约 128 点（实际以服务端扣点为准，可在 01Claw 账户查看）」说明，并给出查看报告方式。
- **执行失败后告知点数返还**：任务已发起但未成功产出报告时（退出码 11/12），告知用户「因网络原因本次任务执行失败，相应点数已返还」并询问是否重试；有 task_id 可用 `--retry-task` 重试（若服务端支持）或重新创建。

> 扣点口径：本 API 不返回 `data.billing.total_points`，脚本 `XHS_VIDEO_POINTS_USED` 常为空，按「约 128 点」提示；约定估值仅作提示，**不当作实扣数字**，真正实扣以 01Claw 账户为准。

## 运行方式

```bash
# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1a) 创建·链接直拆（立即拿 task_id，退出0）
python3 scripts/analyze_xhs_video.py --share-url "https://www.xiaohongshu.com/explore/xxxx" --only-create
# 1b) 创建·本地视频上传（脚本先走预签名上传三步拿 video_id 再创建，退出0）
python3 scripts/analyze_xhs_video.py --video-file "/path/to/note.mp4" --only-create
# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
#    ⚠️ --poll-task 建议带上和创建时相同的 --share-url（或用 --title）用于报告标题
python3 scripts/analyze_xhs_video.py --poll-task <task_id> --share-url "https://www.xiaohongshu.com/explore/xxxx" --out ./小红书拆解报告.md
#   ↓ 退出13就再跑一次（同样带上 --share-url），循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态或单次超时，Web 端易被打断，慎用）——
python3 scripts/analyze_xhs_video.py --share-url "https://www.xiaohongshu.com/explore/xxxx" --out ./小红书拆解报告.md

# 失败后按 task_id 重试（异步，文档未明示该端点，按统一范式实现；不支持会 4xx 透出）
python3 scripts/analyze_xhs_video.py --retry-task <task_id> --share-url "https://www.xiaohongshu.com/explore/xxxx" --out ./小红书拆解报告.md
```

可选参数：

- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `小红书拆解报告-<task_id>.md`。
- `--insecure`：跳过 SSL 校验。
- `--timeout 90`：单次轮询等待上限秒数（默认 90）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- `--idempotency-key KEY`：幂等键；缺省自动生成 UUID。同任务重复提交保持不变。
- `--industry` / `--campaign-type` / `--account-size`：可选业务参数，可引导不强制、缺省不传。
- `--title`：`--poll-task`/`--retry-task` 时显式指定报告标题摘要；缺省按 `--share-url`（或 video 文件名）推断。

## 输出交付

成功时 stdout 形如：

```text
XHS_VIDEO_POINTS_USED=<本次实际扣点，常为空>
XHS_VIDEO_PLAN_POINTS=128
XHS_VIDEO_REPORT_FILE=<报告文件绝对路径或空>
XHS_VIDEO_TASK_ID=<任务 id，便于重试>
=== XHS_VIDEO_REPORT_START ===
<合并后的 Markdown 报告>
=== XHS_VIDEO_REPORT_END ===
```

交付时**按顺序**做三件事（缺一不可）：

1. **渲染报告（最重要）**：截取两个分隔符**之间**的 Markdown 正文，作为 Markdown 渲染呈现给用户——让用户看到真正的标题/表格/列表/分隔线排版，而不是带分隔符或 `\n` 字面的原始文本。
   - 不要展示分隔符行、`XHS_VIDEO_*=` 协议行。
   - 不要只说「报告已生成」却不渲染正文。**正文必须出现在回复里**。过长至少完整渲染前 2–3 个二级标题段并说明完整报告已落盘。
   - 正文由后端渲染，直接渲染，不要二次加工、不改 table。顶级 `# 小红书拆解报告：<摘要>` 一级标题由脚本生成。
2. **告知实际扣点**：非空说「本次实际扣除 N 点」；空（本 API 常为空）说「约 128 点（实际以服务端扣点为准，可在 01Claw 账户查看）」。
3. **告知报告查看方式**：报告已渲染在上方对话中；同时已保存为 MD 文件，路径见 `XHS_VIDEO_REPORT_FILE`（绝对路径）。脚本对落盘做了三级兜底（`--out` → 当前目录 → `/tmp`），只要终态有 markdown 就一定生成 md 文件。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，不涉扣点。 |
| 3 | 参数非法（含 400/422/未传输入/视频格式不支持） | 补全/改输入后重试。任务未发起，不涉扣点。 |
| 4 | 余额不足（402） | 透出服务端 message（如「需至少 128 点」），引导充值。任务未发起，不涉扣点。 |
| 8 | 401 key 无效 | 重新获取覆盖 `config.json` 后重试。任务未发起，不涉扣点。 |
| 10 | 其他 4xx（如 403 无权查该任务/404 任务不存在） | 透出服务端 message，按提示修正。4xx 一般未扣。 |
| 11 | 5xx / 网络错误 | 告知「因网络原因本次任务执行失败，相应点数已返还」，转述 stderr 原因，询问是否稍后重试。 |
| 12 | 已发起但任务未成功 | status 为 failed/error/timeout 等，或终态但无报告。告知「点数已返还」；有 `task_id` 可 `--retry-task` 重试（若服务端支持）或重新创建。**特例**：成功终态但报告经 60s 宽限仍未返回时，已落盘「兜底 md」（含续查指引，**非真实正文**）——据指引建议 `--poll-task` 续查/重试，勿把兜底 md 当真实报告渲染发布。 |
| 13 | 进行中，未到终态（**非失败**） | **不涉及扣点返还**——取 stdout 进度转述，立即再跑 `--poll-task` 续轮询，循环到终态(0)或真失败(12)。 |

> 任务已发起但未出报告（11、12）统一告知「点数已返还」并问是否重试；13 是「进行中、可续轮询」，既非失败也不返还；任务未发起到位（2/3/4/8/10）不涉扣点，正常引导修正。

未知错误**不要自行判定失败**；按表对号入座，按 stderr 透出的原因处理。

## 免责声明

拆解结果由后端基于视频内容分析生成，属于结构化解读参考，不构成对视频数据真实性的背书；具体数据（播放/互动等）以小红书平台实际为准。仅供内容创作与复盘参考，请勿用于违规用途。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 报告 markdown 由后端渲染，skill 不做模板；顶级 `# 小红书拆解报告：<摘要>` 由脚本生成。
- 最终 MD 由脚本一次性拼接覆写 `--out`，agent 不要手动追加/改写输出文件。
- **交付报告时务必把分隔符之间的 Markdown 真正渲染给用户**，这是硬性交付要求。
- 只使用异步拆解接口：`POST .../xiaohongshu-video-analyses` 创建 → `GET .../{analysis_task_id}` 轮询 → 可选 `POST .../{id}/retry`，见 [references/api.md](references/api.md)。
