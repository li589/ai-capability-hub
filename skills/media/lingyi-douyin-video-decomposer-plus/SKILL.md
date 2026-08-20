---
name: lingyi-douyin-video-decomposer-plus
display_name: 抖音爆款短视频拆解
display_name_en: "Lingyi Douyin Viral Video Teardown"
description_zh: "【零一数科·出品】抖音爆款短视频拆解（付费版）。一键把一条抖音视频拆成结构分段、爆款归因、评分和可借鉴策略，照着学照着抄。支持抖音分享链接和本地视频。拆解抖音视频/抖音爆款短视频拆解。需要 python3 和技能目录下 config.json 中的 LY_API_KEY。"
description_en: "[Lingyi Tech] One-click teardown of a viral Douyin short video into structured segments, virality attribution, scoring and reusable tactics. Supports Douyin share links and local video uploads."
category: 内容
version: 0.1.0
author: 小风、CoderPig、Awen
---

# 抖音爆款短视频拆解
> 版本：v0.1.0 · 作者：小风、CoderPig、Awen

> **偏差说明（本 API 与标准 01Claw 异步模板的差异，已据实调整）**
> 1. **无 `POST /retry` 接口**：脚本 `--retry-task <task_id>` 不调任何 retry 路由，而是**对同一 `analysis_task_id` 重新轮询**（等价 `--poll-task`，不重新创建、不重复扣点）。任务真失败（`failed`/`error`/`timeout`）后的“重试”= 经用户确认后用 `--input` **重新发起一次新拆解**（新 `analysis_task_id`、重新扣点）。
> 2. 任务 id 字段是 **`analysis_task_id`**（非通用 `task_id`）。
> 3. 报告 markdown 在 **`data.result.markdown`**（单一报告，非多模块 `results.<module>`）。
> 4. `status` **小写**，含标准集没有的 `timeout` 终态（已补入终态集合）。
> 5. **轮询响应不含 billing 字段**，`DY_VIDEO_POINTS_USED` 运行时常为空 → 按「约 128 点（实际以服务端为准）」回退。
> 6. 创建响应**不返回 `status`**，`--only-create` 合成 `pending` 透出。

一键拆解抖音视频。把一条抖音视频拆成结构分段、爆款归因、评分和可借鉴策略，照着学照着抄。支持两种输入：抖音分享链接，或本地视频文件路径。本地视频会先上传到服务端再发起拆解。脚本 [scripts/analyze_dy_video.py](scripts/analyze_dy_video.py) 负责全部 HTTP 调用，接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

通过 **异步任务接口** 提交：`POST /api/v1/social-analytics/collector/douyin-video-analyses` **立即返回 `analysis_task_id`**，再通过 `GET .../douyin-video-analyses/{id}` 轮询进度与结果。终态后从 `data.result.markdown` 取报告渲染；服务端按次结算扣点（约 128 点）。

## 执行流程

按以下顺序执行，每一步都对应后续章节细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **识别输入**：判断用户提供的是抖音分享链接还是本地视频文件路径。无效或缺失时，按「引导话术」对应场景引导用户更正；本地视频会先上传再发起拆解。详见「输入识别」。
3. **扣点确认（必做，跳过不得）**：跑脚本前向用户说明「本次拆解预计扣点约 128 点，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
4. **拆分轮询（关键，防会话中断）**：远端拆解跑 1–5 分钟，WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成。改成「创建 + 多次短轮询」：
   a. **创建**：`python3 scripts/analyze_dy_video.py --input "<抖音链接 或 本地路径>" --only-create`，立即拿 `DY_VIDEO_TASK_ID` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。**
   b. **告知用户**：用 task_id 诚实告知，例如「已提交，任务 ID xxx，约 1–5 分钟。我会持续跟踪进度，有进展同步给你。」**不要**承诺「完成后自动取回」——单轮阻塞做不到自动续接，要靠你主动循环轮询续接。
   c. **循环轮询**：立即跑 `python3 scripts/analyze_dy_video.py --poll-task <task_id> --input "<同 a 的源>" --out ...`（单次 ≤90s）。**`--poll-task` 必须带 `--input`**（与创建时相同的源，用于报告标题）。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态成功）：进入「输出交付」。
      - **退出码 13**（仍进行中，**非失败**）：取 stdout 的 `DY_VIDEO_STATUS` / `DY_VIDEO_PROGRESS` / `DY_VIDEO_EAPSED` 转述，**立刻再跑一次 `--poll-task <task_id> --input "..."`** 继续。不要停。
      - **退出码 12**（任务真失败）：按「退出码处理」走失败话术，可 `--retry-task` 重轮询续查。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。
   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」。
5. **进度应答**：用户中途问进度时，取最近一次 `--poll-task` 返回的状态自然转述；距上次轮询过一会儿可再跑一次现查。**禁止**回复「查不了任务状态 / 没有 task_id」。
6. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知实际扣点与查看方式。
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

## 输入识别

单次只处理一条输入：

- **抖音分享链接**：短链 `https://v.douyin.com/xxxxx/`（推荐），或长链 `https://www.douyin.com/video/<aweme_id>`（长链须带 `/video/<id>`）。直接把链接传给脚本。
- **本地视频文件路径**：文件存在，扩展名为 `.mp4` `.mov` `.m4v` `.mkv` `.webm` `.avi`，且大小不超过 **200MB**。脚本会自动上传并换取 `video_id`。

不要处理其它平台链接。若用户给出非抖音链接（视频号、小红书、B 站、YouTube 等），按「引导话术 > 非抖音平台链接」引导。若未提供输入、本地文件不存在、格式不支持、文件超过 200MB，按「引导话术」对应场景引导。若一次给出多条或同时给出链接和本地文件，先让用户指定一条。

## 引导话术

当用户触发本技能但未提供有效输入、或输入有误时，按以下场景引导。语气亲和自然，不要罗列技术参数。

### 未提供输入

> 技能已就绪 ✅ 这个技能能帮你把一条抖音视频拆成一份爆款分析报告——包含结构分段、爆款归因、评分和可借鉴策略，直接照着学/抄 📊
>
> 随时可以开拆，把下面任意一种发给我即可：
>
> 1. **抖音分享链接** — 抖音 App 里打开要拆的视频，点「分享」→「复制链接」，把链接贴过来（短链 `https://v.douyin.com/...` 优先）
> 2. **本地视频文件** — 已下载到电脑的视频，直接把文件拖进来或把路径发给我（支持 mp4 / mov / m4v / mkv / webm / avi，200MB 以内）
>
> 拿到后我立刻提交拆解，通常 1–5 分钟出报告 📊

### 非抖音平台链接

> 目前这个技能只支持**抖音**的视频哦，暂时没法直接处理 [视频号/小红书/B站/YouTube 等] 的链接。
>
> 不过你可以先把视频下载到电脑上，然后把本地文件路径发给我，我一样可以帮你拆解分析 😊

### 文件问题（不存在 / 格式不对 / 太大）

- **文件不存在**：找不到这个文件，麻烦检查一下路径是否正确？可以直接把文件拖到对话框里试试。
- **格式不支持**：这个文件格式暂时处理不了，支持的视频格式有：mp4、mov、m4v、mkv、webm、avi。
- **文件过大**：这个视频有点大（超过 200MB 了），可以先用剪辑工具压缩或裁剪一下再发给我。

### 缺少 API Key

> 拆解视频需要调用远端的付费拆解服务，首次使用得配置一下 API Key 🔑
>
> 👉 打开这个链接登录/注册 01Claw 账号并获取 Key：https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy
>
> 拿到 Key 后直接粘贴发给我（一串字符即可），我会帮你存好，之后拆解视频就不用再管它了。这个服务按次计费（约 128 点一次），余额不足时我会提醒你充值。

## 扣点与确认

本技能每次「新发起」拆解任务会消耗点数（成功完成后结算一次），整条链路对用户的扣点感知由你（assistant）来贯穿：

- **执行前确认（必做，跳过不得）**：识别成有效输入、API Key 就绪后，运行脚本**前**向用户说明并请其确认：
  > 本次拆解预计扣点约 **128 点**，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准。是否继续？
  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。
- **执行成功后回告实际扣点**：把脚本透出的 `DY_VIDEO_POINTS_USED` 告诉用户。本 API 轮询响应不含 billing 字段，`DY_VIDEO_POINTS_USED` 常为空，此时按「约 128 点（实际以服务端扣点为准，可在 01Claw 账户查看）」说明，并给出查看报告方式。
- **执行失败后告知点数返还**：任务已发起但未成功产出报告时（退出码 11/12），告知用户「因网络原因本次任务执行失败，相应点数已返还」并询问是否重试；有 task_id 可先 `--retry-task` 重轮询续查，真失败可重新发起（新任务、重新扣点）。

> 恢复已有任务（`--poll-task` / `--retry-task`）时点数已在发起时扣除，本次仅继续轮询，不重复扣点、不需再次确认。`--retry-task` 不调任何 retry 路由，仅对同一 task_id 重新轮询。

## 本地视频上传

本地视频分支由脚本自动完成：

1. `POST /api/v1/content-ops/videos/public-upload-url` 获取预签名上传地址；
2. 直传文件字节到预签名地址（**不带平台鉴权**）；
3. `POST /api/v1/content-ops/videos/public-upload-confirm` 确认上传并取得 `video_id`（成功返回 201）；
4. 使用 `video_id` 发起拆解任务。

上传上限为 **200MB**。脚本会在上传前校验大小，超限以退出码 3 退出，不发任何请求。上传进度写到 stderr，必要时转述给用户。涉及视频上传时，引导用户把本地视频复制后在输入框粘贴（⌘V）上传，措辞中性，不写「检测是否在某个客户端」类判断方案。

## 运行方式

```bash
# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1) 创建（立即拿 analysis_task_id，退出0）
python3 scripts/analyze_dy_video.py --input "<抖音链接 或 本地视频路径>" --only-create
# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
#    ⚠️ --poll-task 必须带上和创建时相同的 --input（用于报告标题）
python3 scripts/analyze_dy_video.py --poll-task <task_id> --input "<同上源>" --out ./抖音视频拆解报告.md
#   ↓ 退出13就再跑一次（同样带 --input），循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态，Web 端易被打断，慎用）——
python3 scripts/analyze_dy_video.py --input "<..." --out ./抖音视频拆解报告.md

# 对同 task_id 重新轮询续查（本接口无 /retry，不重新创建、不重复扣点）
python3 scripts/analyze_dy_video.py --retry-task <task_id> --input "<同创建时的源>" --out ./抖音视频拆解报告.md
```

可选参数：

- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `抖音视频拆解报告-<task_id>.md`。
- `--insecure`：跳过 SSL 校验。
- `--timeout 90`：单次轮询等待上限秒数（默认 90）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- `--idempotency-key KEY`：幂等键；缺省自动生成 UUID。同任务重复提交保持不变。
- `--industry` / `--campaign-type` / `--account-size`：可选业务参数，可引导但不强制，缺省不传。

## 输出交付

成功时 stdout 形如：

```text
DY_VIDEO_POINTS_USED=<本次实际扣点，可能为空>
DY_VIDEO_PLAN_POINTS=128
DY_VIDEO_REPORT_FILE=<报告文件绝对路径或空>
DY_VIDEO_TASK_ID=<任务 id，便于续查>
=== DY_VIDEO_REPORT_START ===
<完整 Markdown 报告>
=== DY_VIDEO_REPORT_END ===
```

交付时**按顺序**做三件事（缺一不可）：

1. **渲染报告（最重要）**：截取两个分隔符**之间**的 Markdown 正文，作为 Markdown 渲染呈现给用户——让用户看到真正的标题/表格/列表/分隔线排版，而不是带分隔符或 `\n` 字面的原始文本。
   - 不要展示分隔符行、`DY_VIDEO_*=` 协议行。
   - 不要只说「报告已生成」却不渲染正文。**正文必须出现在回复里**。过长至少完整渲染前 2–3 个二级标题段并说明完整报告已落盘。
   - 正文由后端渲染，直接渲染，不要二次加工、不改 table。顶级 `# 抖音视频拆解报告：<摘要>` 一级标题由脚本生成。
2. **告知实际扣点**：非空说「本次实际扣除 N 点」；空说「约 128 点（实际以服务端扣点为准，可在 01Claw 账户查看）」。
3. **告知报告查看方式**：报告已渲染在上方对话中；同时已保存为 MD 文件，路径见 `DY_VIDEO_REPORT_FILE`（绝对路径）。脚本对落盘做了三级兜底（`--out` → 当前目录 → `/tmp`），只要终态有 markdown 就一定生成 md 文件。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，不涉扣点。 |
| 3 | 参数非法（含 400/422） | 让用户更正链接、路径、格式或文件大小；超限时提示压缩或裁剪后重试。任务未发起，不涉扣点。 |
| 4 | 余额不足（402） | 透出服务端 message，引导前往 01Claw 账户充值。任务未发起，不涉扣点。 |
| 8 | 401 key 无效 | 重新获取覆盖 `config.json` 后重试。任务未发起，不涉扣点。 |
| 10 | 其他 4xx（含 403 跨平台/404 任务不存在） | 透出服务端 message，按提示修正。4xx 一般未扣。 |
| 11 | 5xx / 网络错误 | 告知「因网络原因本次任务执行失败，相应点数已返还」，转述 stderr 原因，询问是否稍后重试。 |
| 12 | 已发起但任务未成功 | status 为 failed/error/timeout 等，或终态但无报告。告知「点数已返还」；有 `task_id` 可先用 `--retry-task` 重轮询续查，仍失败则询问是否重新发起（新任务、重新扣点）。**特例**：成功终态但报告经 60s 宽限仍未返回时，已落盘「兜底 md」（含续查指引，**非真实正文**）——据指引建议 `--poll-task`/`--retry-task` 续查，勿把兜底 md 当真实报告渲染发布。 |
| 13 | 进行中，未到终态（**非失败**） | **不涉及扣点返还**——取 stdout 进度转述，立即再跑 `--poll-task`（带 `--input`）续轮询，循环到终态(0)或真失败(12)。 |

> 任务已发起但未出报告（11、12）统一告知「点数已返还」并问是否重试；13 是「进行中、可续轮询」，既非失败也不返还；任务未发起到位（2/3/4/8）不涉扣点，正常引导修正。

未知状态**不要自行判定失败**；脚本会原样透出 `progress_message`，继续按轮询结果处理。

## 免责声明

> 拆解结果由远端服务对视频内容分析生成，仅供参考、不承诺精确；重大发布或投放决策建议结合人工复核。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 报告 markdown 由后端渲染，skill 不做模板；顶级 `# 抖音视频拆解报告：<摘要>` 由脚本生成。
- 最终 MD 由脚本一次性拼接覆写 `--out`，agent 不要手动追加/改写输出文件。
- **交付报告时务必把分隔符之间的 Markdown 真正渲染给用户**，这是硬性交付要求。
- 只使用异步任务接口：`POST .../douyin-video-analyses` 创建 → `GET .../douyin-video-analyses/{id}` 轮询；本接口**无 `/retry`**，失败续查用 `--retry-task`/`--poll-task` 重轮询，真重试重新发起，见 [references/api.md](references/api.md)。
