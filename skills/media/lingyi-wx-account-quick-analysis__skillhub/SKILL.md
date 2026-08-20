---
name: 微信视频号账号拆解（付费版）【零一数科·出品】
description: 【零一数科·出品】：发一个视频号账号名，几分钟拿到一份账号快拆报告——账号总览/受众画像/内容矩阵/爆款公式/对标竞品/运营建议，照着爆款路径抄起号模板。触发词：视频号账号快拆、账号快拆、快速拆解视频号账号、快拆账号。
metadata:
  slug: lingyi-wx-account-quick-analysis
  version: v0.1.0
  author: 小风、CoderPig、Awen
  requires:
    bins:
      - python3
---

# 微信视频号账号拆解（付费版）【零一数科·出品】

> 版本：v0.1.0 · 作者：小风、CoderPig、Awen

## 偏差（与标准异步任务范式的不同）

本 API 与「后端异步任务」标准范式有以下差异，已在脚本与流程中相应调整：

1. **输入是账号名不是文本**：CLI 用 `--account-name`（新建必填）取代 `--text`；`--poll-task <id>` 携带 `--account-name` 用于生成报告标题。
2. **终态枚举为 `pending`/`running`/`completed`/`failed`**：成功终态是 `completed`（非 `succeeded`），无 `partial_failed`/`billing_failed`。
3. **报告 markdown 由后端预渲染、自带一级标题**：完成态 `data.markdown` 已是 `# 微信视频号账号拆解报告\n## ...`，脚本原样使用，不再叠加标题（避免双一级标题）。
4. **扣点字段在 `data.total_points`**（number，顶层），非 `data.billing.total_points`（string）。
5. **本接口无重试端点**：文档只列了「创建 + 查询」两个接口。任务失败（退出码 12）由助手用原账号名重新 `--only-create` 发起（重新计费），不调用任何 `/retry`。

## 能力概述

输入一个微信视频号**账号名称**（昵称），付费远端「账号快拆」几分钟出一份 Markdown 报告：账号总览、受众画像、内容矩阵、爆款公式、对标竞品、运营建议。比全量「视频号爆款账号拆解」更轻、更快，适合快速判断一个账号该不该、怎么抄。

通过 **异步任务接口** 提交：`POST /api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis` **立即返回 `task_id`**，再通过 `GET .../wx-video-account-quick-analysis/{id}` 轮询进度与结果。完成态 `data.markdown` 已由后端渲染好，脚本从其取报告、从 `data.total_points` 读实扣。接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

> 该接口为「账号**快拆**」，与全量「账号拆解」是两套独立路径，`task_id` **互不通用**，不要拿拆解接口的 task_id 来查快拆，反之亦然。

## 执行流程

按以下顺序执行，每一步都对应后续章节细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **收集信息 + 账号名核对**：确认必填输入「视频号账号名称（昵称）」（可选 `platform`，缺省不传）。账号名是按名称定位拆解的，错一个字就可能拆到别的账号或拆不出来——**先简短复述确认账号名准确**，建议用户从微信视频号里复制准确昵称。详见「信息收集」。
3. **扣点确认（必做，跳过不得）**：跑脚本**前**向用户说明「本次任务预计扣点约 120 点，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
4. **拆分轮询（关键，防会话中断）**：异步任务跑 1–2 分钟，WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成。改成「创建 + 多次短轮询」：
   a. **创建**：`python3 scripts/quick_analysis.py --account-name "央视新闻" --only-create`，立即拿 `WX_ACCOUNT_QUICK_TASK_ID` + `WX_ACCOUNT_QUICK_STATUS` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。**
   b. **告知用户**：用 task_id 诚实告知，例如「已提交快拆，任务 ID xxx，约 1–2 分钟。我会持续跟踪进度，有进展同步给你。」**不要**承诺「完成后自动取回」——单轮阻塞做不到自动续接，要靠你主动循环轮询续接。
   c. **循环轮询**：立即跑 `python3 scripts/quick_analysis.py --poll-task <id> --account-name "央视新闻" --out ...`（单次 ≤90s）。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态成功）：进入「输出交付」。
      - **退出码 13**（仍进行中，**非失败**）：取 stdout 的 `WX_ACCOUNT_QUICK_STATUS` / `WX_ACCOUNT_QUICK_PROGRESS` / `WX_ACCOUNT_QUICK_EAPSED` 转述，**立刻再跑一次 `--poll-task <id> --account-name "央视新闻"`** 继续。不要停。
      - **退出码 12**（任务真失败）：按「退出码处理」走失败话术——本接口无重试端点，可询问是否用原账号名重新发起。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。
   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」。
5. **进度应答**：用户中途问进度时，取最近一次 `--poll-task` 返回的状态自然转述；距上次轮询过一会儿可再跑一次现查。**禁止**回复「查不了任务状态 / 没有 task_id」。
6. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知实际扣点与查看方式。
7. **失败处理**：见「退出码处理」——非发起阶段失败（2/3/4/8）按对应话术；已发起但失败（11/12）告知「点数已返还」。退出码 13 **不是失败**，按第 4c 步续轮询。

任一步异常按「退出码处理」表对号入座，**不要自行判定失败**。

## 鉴权

Token 取「技能目录」（SKILL.md 所在目录）下 `config.json` 的 `LY_API_KEY` 字段，回退环境变量 `LY_API_KEY`。请求头 `Authorization: Bearer <api_key>` + `X-Appbuilder-From: openclaw`。`config.json` 形如：

```json
{ "LY_API_KEY": "你的密钥" }
```

运行前先确认 key：

1. **检查是否已有 key**：读 `config.json` 的 `LY_API_KEY` 是否非空；无则看环境变量 `LY_API_KEY`。任一有值即就绪。
2. **缺失则引导用户获取**：前往 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy` 取 API Key，把 key 直接发给你；收到后写入 `config.json` 的 `LY_API_KEY` 字段（保留其它内容）再继续。该文件已被 `.gitignore` 忽略。
3. **鉴权失败（退出码 8）**：key 失效或过期，重新获取并覆盖写 `config.json` 后重试，不反复用同一失效 key。
4. **SSL 错误**：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用）。

## 信息收集

本技能按**视频号账号名称（昵称）**定位并拆解对应账号。详见 [references/usage-notes.md](references/usage-notes.md) 的待检字段表。

| 字段 | 必填 | 说明 |
|------|------|------|
| 账号名称 `account_name` | 是 | 视频号账号昵称，如「央视新闻」「papi酱」。**务必准确**——错一个字就可能拆到别的账号或拆不出来。建议从微信视频号复制准确昵称 |
| 平台 `platform` | 否 | 可不传；本期固定按微信视频号处理。**可引导但不强制、缺省不传** |

- 拿到账号名后**先简短复述确认**：「我将拆解账号【<名称>】的……，对吗？」；名称含错别字/歧义/简称时主动核对完整昵称。
- 给的不是账号名称（链接 / 视频文件）→ 引导改发账号昵称：本技能按账号名称拆解，暂时没法直接吃链接或视频文件。
- 一次给多个名称 → 让用户指定一个。
- 缺 API Key 时按「鉴权」流程引导，引导话术见 [references/usage-notes.md](references/usage-notes.md)。

## 扣点与确认

本技能每次「新发起」快拆任务会消耗点数（统一任务成功结算一次），整条链路对用户的扣点感知由你（assistant）贯穿：

- **执行前确认（必做，跳过不得）**：账号名核对无误、API Key 就绪后，运行脚本**前**向用户说明并请其确认：
  > 本次任务预计扣点约 **120 点**，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准。是否继续？
  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。
- **执行成功后回告实际扣点**：把脚本透出的 `WX_ACCOUNT_QUICK_POINTS_USED` 告诉用户（为空时按「约 120 点（实际以服务端扣点为准，可在 01Claw 账户查看）」说明），并给出查看报告方式。
- **执行失败后告知点数返还**：任务已发起但未成功产出报告时（退出码 11/12），告知用户「点数已返还」并询问是否重试；本接口无重试端点，重试即用原账号名重新 `--only-create`。

> 扣点口径：脚本优先读服务端 `data.total_points`；未命中留空。约定估值（120）仅作「约 N 点」提示，**不当作实扣数字**；实际以最终完成任务时的点数为准，真正实扣以 01Claw 账户为准。

## 运行方式

```bash
# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1) 创建（立即拿 task_id，退出0）
python3 scripts/quick_analysis.py --account-name "央视新闻" --only-create
# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
#    ⚠️ --poll-task 建议带上和创建时相同的 --account-name（用于报告标题）
python3 scripts/quick_analysis.py --poll-task <task_id> --account-name "央视新闻" --out ./账号快拆报告.md
#   ↓ 退出13就再跑一次（同样带 --account-name），循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态，Web 端易被打断，慎用）——
python3 scripts/quick_analysis.py --account-name "央视新闻" --out ./账号快拆报告.md
```

可选参数：

- `--account-name NAME`：视频号账号名称（新建必填）；`--poll-task` 时用于生成报告标题。
- `--platform PLATFORM`：平台，可不传；本期固定按微信视频号处理。
- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `账号快拆报告-<task_id>.md`。
- `--insecure`：跳过 SSL 校验。
- `--timeout 90`：单次轮询等待上限秒数（默认 90）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- `--idempotency-key KEY`：幂等键；缺省自动生成 UUID。同任务重复提交保持不变。

## 输出交付

成功时 stdout 形如：

```text
WX_ACCOUNT_QUICK_POINTS_USED=<本次实际扣点，可能为空>
WX_ACCOUNT_QUICK_PLAN_POINTS=120
WX_ACCOUNT_QUICK_REPORT_FILE=<报告文件绝对路径或空>
WX_ACCOUNT_QUICK_TASK_ID=<任务 id，便于重试>
=== WX_ACCOUNT_QUICK_REPORT_START ===
<Markdown 报告（后端预渲染、自带一级标题）>
=== WX_ACCOUNT_QUICK_REPORT_END ===
```

交付时**按顺序**做三件事（缺一不可）：

1. **渲染报告（最重要）**：截取两个分隔符**之间**的 Markdown 正文，作为 Markdown 渲染呈现给用户——让用户看到真正的标题/表格/列表/分隔线排版，而不是带分隔符或 `\n` 字面的原始文本。
   - 不要展示分隔符行、`WX_ACCOUNT_QUICK_*=` 协议行。
   - 不要只说「报告已生成」却不渲染正文。**正文必须出现在回复里**。过长至少完整渲染前 2–3 个二级标题段并说明完整报告已落盘。
   - 报告由后端预渲染、自带一级标题，直接渲染，不要二次加工、不改 table。
2. **告知实际扣点**：非空说「本次实际扣除 N 点」；空说「约 120 点（实际以服务端扣点为准，可在 01Claw 账户查看）」。
3. **告知报告查看方式**：报告已渲染在上方对话中；同时已保存为 MD 文件，路径见 `WX_ACCOUNT_QUICK_REPORT_FILE`（绝对路径）。脚本对落盘做了三级兜底（`--out` → 当前目录 → `/tmp`），只要终态有 markdown 就一定生成 md 文件。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，不涉扣点。 |
| 3 | 参数非法（含 400/任务凭证无效） | 补全账号名后重试。任务未发起，不涉扣点。 |
| 4 | 余额不足（402） | 透出 `recharge_url`（若有），引导充值。任务未发起，不涉扣点。 |
| 8 | 401 key 无效 | 重新获取覆盖 `config.json` 后重试。任务未发起，不涉扣点。 |
| 10 | 其他 4xx（无权访问 403 / 任务不存在 404 等） | 透出服务端 message，按提示修正。4xx 一般未扣。 |
| 11 | 5xx / 网络错误 | 告知「点数已返还」，转述 stderr 原因，询问是否稍后重试。 |
| 12 | 已发起但任务未成功 | status 为 failed，或终态但无报告。告知「点数已返还」；**本接口无重试端点**，可询问是否用原账号名重新 `--only-create` 发起（重新计费）。 |
| 13 | 进行中，未到终态（**非失败**） | **不涉及扣点返还**——取 stdout 进度转述，立即再跑 `--poll-task` 续轮询，循环到终态(0)或真失败(12)。 |

> 任务已发起但未出报告（11、12）统一告知「点数已返还」并问是否重试；13 是「进行中、可续轮询」，既非失败也不返还；任务未发起到位（2/3/4/8）不涉扣点，正常引导修正。

未知错误**不要自行判定失败**；按表对号入座，按 stderr 透出的原因处理。

## 免责声明

账号快拆基于服务端远端分析，结果为模拟参考性质的拆解，不承诺精确到每一条数据；重大运营决策建议结合账号实际数据人工复核。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 报告 markdown 由后端渲染、自带一级标题，skill 不做模板、不改 table。
- 最终 MD 由脚本一次性写入 `--out`，agent 不要手动追加/改写输出文件。
- **交付报告时务必把分隔符之间的 Markdown 真正渲染给用户**，这是硬性交付要求。
- 只使用账号快拆接口：`POST /api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis` 创建 → `GET .../wx-video-account-quick-analysis/{id}` 轮询，见 [references/api.md](references/api.md)。本接口无重试端点。
