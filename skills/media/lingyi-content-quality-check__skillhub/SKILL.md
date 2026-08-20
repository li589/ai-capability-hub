---
name: 爆款内容预检（付费版）【零一数科·出品】
description: 【零一数科·出品】：爆款内容预检。发前先测会不会违规、能不能爆、人群买不买——把发布从赌运气变成心里有底。视频号/公众号文案一键过三关：①
  敏感词+广告法违禁词合规检测，命中词直接给替换建议；② 模拟目标人群真实观看反应与评论区原声；③
  爆款概率预测，逐维度打分说清依据。合规要准、爆款看依据，发出去前帮你把最后一道关。触发词：内容质检、敏感词检测、广告法检测、违禁词扫描、发布前审核、爆款预测、人群模拟。需要
  python3 和技能目录下 config.json 中的 LY_API_KEY。
metadata:
  slug: lingyi-content-quality-check
  version: v0.3.0
  author: 小风、CoderPig、Awen
  requires:
    bins:
      - python3
disable-model-invocation: true
---

# 爆款内容预检（付费版）【零一数科·出品】

> 版本：v0.3.0 · 作者：小风、CoderPig、Awen

视频内容发布前的质检审核工具，三大能力独立可选：

| 模块 | modules 取值 | 特点 |
|------|--------------|------|
| **合规检测**（敏感词 + 广告法） | `compliance` | 词库匹配（权威）+ LLM 改写，秒级，**要准** |
| **人群反馈 + 用户评论** | `persona` | LLM 模拟，秒~十几秒，**辅助参考** |
| **爆款概率预测** | `burst` | LLM 打分，秒级，**辅助参考** |

通过 **异步统一任务接口** 提交所选模块：`POST .../tasks` **立即返回 `task_id`**，再通过 `GET .../tasks/{id}` 轮询进度与结果。服务端按固定顺序执行，任务级结算扣点；脚本从 `data.results.<module>.markdown` 拼接报告，从 `data.billing.total_points` 读实扣。接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

## 执行流程

按以下顺序执行，每一步都对应后续章节的细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **收集信息**：与用户确认待检文本、发布平台、要跑哪几个模块（缺项给默认）。详见「信息收集」。
3. **扣点确认**：跑脚本**前**，向用户说明「本次任务较复杂，预计扣点约 38 点，实际扣点视任务复杂程度而定，以最终完成任务时的实际点数为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
4. **拆分轮询（关键，防会话中断）**：异步任务跑 1–2 分钟，WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成（会被中段打断、用户不知是否还在跑）。改成「创建 + 多次短轮询」：

   a. **创建**：跑 `python3 scripts/quality_check.py --text "..." --only-create ...`，立即拿 `CONTENT_QUALITY_TASK_ID` + `CONTENT_QUALITY_STATUS` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。**

   b. **告知用户**：用拿到的 task_id 诚实告知，例如「质检已提交，任务 ID xxx，三模块全跑预计 1–2 分钟。我会持续跟踪进度，有进展同步给你。」**不要**说「完成后自动取回报告」之类的承诺——单轮阻塞做不到自动续接，会话会被打断；要靠你主动循环轮询来续接。

   c. **循环轮询**：立即跑 `python3 scripts/quality_check.py --poll-task <id> --text "<同 a 的待检文本>" --out ...`（单次 ≤90s）。**`--poll-task` 必须带 `--text`**——它用于生成报告标题「质检报告：<内容开头>」；不带会退化为「任务 xxx」。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态 succeeded）：进入「输出交付」，渲染报告 + 告知扣点 + 告知查看方式。
      - **退出码 13**（仍进行中，**非失败**）：取出 stdout 的 `CONTENT_QUALITY_STATUS` / `CONTENT_QUALITY_PROGRESS` / `CONTENT_QUALITY_EAPSED`，转述给用户（如「已约 45 秒，合规完成、人群反馈进行中」），**立刻再跑一次 `--poll-task <id> --text "..."`**（同样带 `--text`）继续。不要停、不要等用户追问——会话保持有输出就不中断。
      - **退出码 12**（任务真失败/部分失败）：按「退出码处理」走失败话术 + 可 `--retry-task`。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。

   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」，循环直到拿到终态报告。轮询期间用户可随时插话，你用最新一次 `--poll-task` 的结果自然回应即可。
5. **进度应答（用户中途问进度时）**：若用户在循环轮询间隙问「好了吗 / 跑到哪了」，取出最近一次 `--poll-task` 返回的 `CONTENT_QUALITY_STATUS` / `CONTENT_QUALITY_PROGRESS` / `CONTENT_QUALITY_EAPSED` 自然转述；若距上次轮询已过一会儿，可再跑一次 `--poll-task <id>` 现查后转述。**禁止**回复「查不了任务状态 / 没有 task_id」——创建后立刻有 task_id 与进度。
6. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知本次实际扣点与报告查看方式。
7. **失败处理**：见「退出码处理」——非发起阶段失败（2/3/4/8）按对应话术处理；已发起但失败的（11/12）告知「因网络原因本次任务执行失败，相应点数已返还」，若有 `task_id` 可 `--retry-task` 重试。退出码 13 **不是失败**，按第 4c 步续轮询。

任一步异常按「退出码处理」表对号入座，**不要自行判定失败**。

## 鉴权

Token 取「技能目录」（SKILL.md 所在目录）下 `config.json` 的 `LY_API_KEY` 字段，回退环境变量 `LY_API_KEY`。请求头 `Authorization: Bearer <api_key>`（服务端也兼容裸 key）。`config.json` 形如：

```json
{ "LY_API_KEY": "你的密钥" }
```

运行前先确认 key：

1. **检查是否已有 key**：读 `config.json` 的 `LY_API_KEY` 是否非空；无则看环境变量 `LY_API_KEY`。任一有值即就绪。
2. **缺失则引导用户获取**：前往 <https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy> 取 API Key，把 key 直接发给你；收到后写入 `config.json` 的 `LY_API_KEY` 字段（保留其它内容）再继续。该文件已被 `.gitignore` 忽略。
3. **鉴权失败（退出码 8）**：key 失效或过期，重新获取并覆盖写 `config.json` 后重试，不反复用同一失效 key。
4. **SSL 错误**（`CERTIFICATE_VERIFY_FAILED` 等）：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用，有中间人风险）。

## 信息收集

质检前与用户确认以下信息（缺项给默认建议，必填缺失则一次性问清）：

| 字段 | 必填 | 说明 |
|------|------|------|
| 待检文本 | 是 | 口播文案 / 标题 / 字幕条 / 标签等文本（给文本或文件路径）|
| `platform` | 是 | 发布平台：视频号(`channels`) / 公众号(`mp`)，默认视频号 |
| 检测模块 | 否 | 想跑哪几块：合规 / 人群 / 爆款；不指定 = 三块全跑 |
| `personas` | 否 | 指定人群（年龄段-性别-职业-消费层级，如 `25-34-女-白领-高消费`），缺省后端默认 5 类典型人设 |
| `comment_count` | 否 | 其他声音评论条数，默认 6（每个人群已在卡片内带 1 条评论，超过人群数的名额作为卡片后「其他声音」补充） |

> 本 skill 仅做**文本层**质检（口播/标题/字幕/标签），不分析视频画面。检测范围仅文本/脚本。

### 检测模块选择

三大模块相互独立，用户可任意组合：

- **只跑合规**（默认最常见场景）：秒级返回，词库匹配，成本最低。适合快速过审。
- **合规 + 人群**：加一层「目标受众怎么看」的辅助参考。
- **合规 + 爆款**：加一层「值不值得发」的评分参考。
- **三块全跑**（默认）：完整报告。

用 `--only` 指定模块子集，缺省 = 三块全跑。支持中英文别名：`compliance/c/合规`、`persona/p/人群`、`burst/b/爆款`。

## 扣点与确认

本技能每次「新发起」质检会消耗点数（统一任务成功结算一次），整条链路对用户的扣点感知由你（assistant）来贯穿：

- **执行前确认（必做，跳过不得）**：信息收集完成、API Key 就绪后，运行脚本**前**向用户说明并请其确认：

  > 本次质检任务较复杂，预计扣点约 **38 点**，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准。是否继续？

  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。

- **执行成功后回告实际扣点**：见「输出交付」，把脚本透出的 `CONTENT_QUALITY_POINTS_USED` 作为实际扣点告诉用户（为空时按「约 38 点（实际以服务端扣点为准，可在 01Claw 账户查看）」说明），并给出查看报告的方式。

- **执行失败后告知点数返还**：见「退出码处理」，任务已发起但未成功产出报告时（退出码 11/12），告知用户「因网络原因本次任务执行失败，相应点数已返还」并询问是否重试；若有 `CONTENT_QUALITY_TASK_ID` 或 stderr 中的 `task_id`，可用 `--retry-task` 重试失败模块。

> 扣点口径：脚本优先读服务端 `data.billing.total_points`（正式字段，字符串）；未命中才留空。约定估值为三块各约 8/22/8 点、全跑约 38 点，仅作「约 N 点」提示用，**不当作实扣数字**；实际消耗以最终完成任务时的点数为准。真正实扣以 01Claw 账户为准。

## 运行方式

```bash
# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1) 创建（立即拿 task_id，退出0）
python3 scripts/quality_check.py --text "<口播文案或文件路径或->" --platform channels --only-create
# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
#    ⚠️ --poll-task 必须带上和创建时相同的 --text，否则报告标题会退化为「任务 xxx」，而非「质检报告：<内容>」
python3 scripts/quality_check.py --poll-task <task_id> --text "<同上待检文本>" --out ./质检报告.md
#   ↓ 退出13就再跑一次（同样带 --text），循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态，仅在单轮能撑够时用，Web 端易被打断）——
python3 scripts/quality_check.py \
  --text "<口播文案或文件路径或->" \
  --platform channels \
  --out ./质检报告.md

# 只跑合规（最快、最省）
python3 scripts/quality_check.py --text "..." --only compliance --only-create
python3 scripts/quality_check.py --poll-task <task_id> --text "..." --out ./质检报告.md

# 失败后按 task_id 重试（异步，已成功模块不重跑）
python3 scripts/quality_check.py --retry-task <task_id> --text "<待检文本>" --out ./质检报告.md
```

可选参数：

- `--only`：CSV，值 ⊆ `{compliance, persona, burst}`（支持别名 `c/p/b`、`合规/人群/爆款`）；缺省 = 三块全跑。
- `--personas "25-34-女-白领-高消费,35-44-女-宝妈-中消费"`：仅在启用 persona 模块时生效。
- `--comment-count 8`：其他声音评论条数（仅 persona 模块生效，超过人群数的名额作为卡片后「其他声音」）。
- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `质检报告-<task_id>.md`。给已有目录则写入该目录下 `质检报告.md`。
- `--insecure`：跳过 SSL 校验。
- `--only-create`：仅 POST 创建任务拿 task_id 后即退出（退出码 0，不轮询）；stdout 输出 `CONTENT_QUALITY_TASK_ID` / `CONTENT_QUALITY_STATUS` / `CONTENT_QUALITY_PROGRESS` + 空 report 分隔符。配合 `--poll-task` 实现拆分轮询。
- `--poll-task TASK_ID`：对已有 task_id 执行 GET 轮询。到终态(succeeded)交付报告(退出码0)；仍运行则 emit 进行中状态(退出码13，**非失败**)可续轮询；终态失败退出码12。**务必带上 `--text`（与创建时相同的待检文本）**，用于生成「质检报告：<内容开头>」标题，不带会退化为「任务 xxx」。
- `--timeout 90`：单次轮询等待上限秒数（默认 90，< WorkBuddy/Web 单轮上限）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- 单次 HTTP 超时固定 **60s**（创建 / 查询 / 重试，脚本内 `HTTP_TIMEOUT`，不可通过 CLI 改）。
- `--text -`：从 stdin 读文本。
- `--idempotency-key KEY`：幂等键；缺省自动生成 UUID。用户明确要求「同一任务再提交」时保持不变，避免重复建任务。
- `--retry-task TASK_ID`：对已有任务调用 `/tasks/{id}/retry`（异步），不需要 `--text`。
- `--allow-partial`：历史参数保留兼容。当前 `partial_failed` 只要有任一模块 markdown 即尽力拼接交付(exit0)，无需此参数；该参数仅在极少数需显式声明时使用。

脚本固定策略（纯异步）：

1. **取 API Key**：读 `config.json` / 环境变量；缺失→退出码 2。
2. **校验参数**：文本非空且 ≤20000、`platform` ∈ {channels, mp}、`--only` 解析后 ⊆ `{compliance, persona, burst}`；非法→退出码 3。
3. **POST `/tasks`**：body 含 `text` / `platform` / `modules` / `options` / `idempotency_key`；**立即**拿 `task_id`（stderr 打印 `CONTENT_QUALITY_TASK_ID=` 与进度）。
4. **GET 轮询**：按 `--poll-interval` 查询直到终态或单次等待上限；stderr 输出 status / 当前模块 / 已用时。**单次到上限不是失败**——进行中任务退出码 13，可续 `--poll-task`。
5. **判任务 status**：`succeeded` 且能取出至少一个模块 markdown → 拼接交付(exit0)；`partial_failed` 有任一模块 markdown → 尽力拼接已成功模块 + 标注缺失，仍 exit0 交付；所有模块 markdown 均缺失或其它失败态 → 退出码 12。
6. **提取扣点**：优先 `data.billing.total_points`。
7. **拼接 Markdown**：从 `data.results.<module>.markdown` 取各模块 markdown（兼容 `{markdown}`/`{data:{markdown}}`/字符串等多形态，传入 modules 未命中时用 results 实际 key 兜底），按顺序拼接，顶部加 `# 质检报告：<内容开头>`，段间 `\n\n---\n\n`；缺模块追加「结果缺失」段。
8. **写盘 + stdout**：**三级兜底确保必生成 md** —— `--out` 指定路径 → 当前工作目录 `质检报告-<task_id>.md` → `/tmp/质检报告-<task_id>.md`，任一成功即把绝对路径写入 `CONTENT_QUALITY_REPORT_FILE=`；stdout 按协议输出。
9. **交付**：见「输出交付」。

### 用户问进度时

轮询循环期间用户若问「好了吗 / 跑到哪了」：

1. 取最近一次 `--poll-task` 返回的 `CONTENT_QUALITY_STATUS` / `CONTENT_QUALITY_PROGRESS` / `CONTENT_QUALITY_EAPSED` 自然转述，例如「还在跑，约 45 秒；合规检测已完成、人群反馈进行中；任务 ID xxx」。若距上次轮询已过一会儿，再跑一次 `--poll-task <id>` 现查后转述。
2. 转述后**立即继续轮询循环**（再跑 `--poll-task`），不要停下等用户——保持会话有输出。
3. **禁止**回复「查不了任务状态 / 没有 task_id」——创建后立刻有 task_id 与进度。

## 输出交付

成功时 stdout 形如：

```text
CONTENT_QUALITY_POINTS_USED=<本次实际扣点，可能为空>
CONTENT_QUALITY_PLAN_POINTS=<约定预估扣点，如 38>
CONTENT_QUALITY_REPORT_FILE=<报告文件绝对路径或空>
CONTENT_QUALITY_TASK_ID=<任务 id，便于重试>
=== CONTENT_QUALITY_REPORT_START ===
<合并后的 Markdown 报告>
=== CONTENT_QUALITY_REPORT_END ===
```

交付时**按顺序**做三件事（这三步缺一不可，尤其是第 1 步——报告必须真正呈现为 Markdown，不能只甩个文件路径或把分隔符原文贴给用户）：

1. **渲染报告（最重要，务必做对）**：截取 `=== CONTENT_QUALITY_REPORT_START ===` 与 `=== CONTENT_QUALITY_REPORT_END ===` 两个分隔符**之间**的 Markdown 正文，把它**作为 Markdown 渲染呈现给用户**——即对话里要让用户看到真正的「标题、表格、列表、分隔线」排版，而不是带有分隔符标记或 `\n` 字面的原始文本。
   - ⚠️ 不要把 `=== CONTENT_QUALITY_REPORT_START ===` / `=== CONTENT_QUALITY_REPORT_END ===` 这两行分隔符、或 `CONTENT_QUALITY_*=` 这些协议行展示给用户。
   - ⚠️ 不要只说「报告已生成」却不渲染正文。**正文必须出现在回复里**。若正文过长，至少完整渲染前 2–3 个二级标题段落并说明完整报告已落盘；但凡能放下，优先**完整渲染**。
   - 报告正文由**后端渲染**（各模块 `results.<module>.markdown`，从 `##` 二级标题起），skill 侧不做模板；顶级 `# 质检报告：<摘要>` 一级标题由脚本生成。直接渲染即可，不要二次加工、不要改写表格。
   - 高危违禁（`conclusion=❌`）在渲染后明确提示「不建议发布，建议修改」；`⚠️` 提示「需修改」；`✅` 提示「合规通过」。

2. **告知实际扣点**：若 `CONTENT_QUALITY_POINTS_USED` 非空，告诉用户「**本次任务实际扣除 {点数} 点**」（以最终完成任务时的实际点数为准）；为空时说「**本次任务约扣 38 点**（实际以服务端扣点为准，可在 01Claw 账户查看）」。

3. **告知报告查看方式**：报告已渲染在上方对话中；同时**必定已保存为 Markdown 文件**，路径见 `CONTENT_QUALITY_REPORT_FILE`（绝对路径），直接打开该文件即可查看/归档。脚本对落盘做了三级兜底（`--out` 指定路径 → 当前工作目录 `质检报告-<task_id>.md` → `/tmp/质检报告-<task_id>.md`），只要任务 succeeded 且 results 里有 markdown，就一定生成 md 文件——`CONTENT_QUALITY_REPORT_FILE` 非空即落盘成功。仅当该字段为空（极端不可写环境）才说明「文件未落盘，正文已在上面对话中，可让我重新指定 `--out` 保存」。

   > 报告 markdown 由脚本从服务端 `data.results.<module>.markdown` 取出拼接（兼容 `{markdown}`/`{data:{markdown}}`/字符串等多种形态），部分模块结果缺失时仍会拼接已成功模块并在报告里标注「结果缺失」，确保用户总能拿到一份 md。

**若只跑了合规**，交付后可主动询问是否需要就某条违禁词给替换词；**仅当报告里含人群/评论/爆款段落**时，才追加免责（见「免责声明」），只跑合规不提模拟参考免责。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理（渲染报告 + 告知实际扣点 + 告知查看方式）。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，**不涉及扣点**。 |
| 3 | 参数非法（含 400/422） | 文本空 / 超长 / `platform` 非 channels\|mp / `--only` 非法 → 补全后重试。任务未发起，**不涉及扣点**。 |
| 4 | 余额不足（402） | 透出 `recharge_url`（若有），引导充值。任务未发起，**不涉及扣点**。 |
| 8 | 401 key 无效 | key 失效或过期，重新获取覆盖 `config.json` 后重试。任务未发起，**不涉及扣点**。 |
| 10 | 其他 4xx | 透出服务端 message，按提示修正。多为请求体/校验问题。按场景判断是否涉及扣点（4xx 一般未扣）。 |
| 11 | 5xx / 网络错误 | 远端内部错误或网络不可达。**告知用户「因网络原因本次任务执行失败，相应点数已返还」**，转述 stderr 原因，询问是否稍后重试。 |
| 12 | 已发起但任务未成功 | status 为 failed / billing_failed 等，或 succeeded 但所有模块 markdown 均缺失（实在拼不出报告）。**告知用户「因网络原因本次任务执行失败，相应点数已返还」**；若有 `task_id`，可执行 `python3 scripts/quality_check.py --retry-task <task_id> --out ...` 重试失败模块。注：`partial_failed` 只要有任一模块 markdown，脚本会尽力拼接并 exit 0 交付（不再走 12）。 |
| 13 | 进行中，未到终态（非失败） | 单次轮询到上限仍未终态。**这不是失败，不涉及扣点返还**——取出 stdout 的 `CONTENT_QUALITY_TASK_ID/STATUS/PROGRESS/EAPSED` 转述给用户，立即再跑 `python3 scripts/quality_check.py --poll-task <task_id> --out ...` 续轮询，循环到拿到终态（退出码 0）或真失败（12）。 |

> 一句话：任务已发起但未成功产出报告（退出码 11、12），统一告知用户「**因网络原因本次任务执行失败，相应点数已返还**」并询问是否重试；退出码 13 是「进行中、可续轮询」，**既非失败也不涉及扣点**，照第 4c 步循环轮询即可；任务未发起到位的（2、3、4、8）不涉及扣点，正常引导修正即可。

未知错误**不要自行判定失败**；按表对号入座，按 `stderr` 透出的原因处理。

## 免责声明

- **合规检测**（敏感词 + 广告法）基于后端词库，词库可热更新但仍可能滞后于平台规则/法律更新；**重大发布前建议人工复核**。
- **观众反应沙盘（人群反馈）/ 爆款概率预测**为**模拟参考，不承诺精确**，仅作「看起来很厉害的辅助参考」用途，不作为发布决策的唯一依据。仅当报告里含这些段落时才提这条免责。报告正文本身不再含 ⚠️ 字样，由本话术在交付时统一说明。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 报告完整 Markdown 由**后端渲染**（各模块 `results.<module>.markdown`），skill 侧不做模板。顶级 `# 质检报告：<摘要>` 一级标题由脚本生成。
- 最终 MD 由 `quality_check.py` 一次性拼接后覆写到 `--out`，agent 不要手动追加/改写输出文件。
- **交付报告时务必把分隔符之间的 Markdown 真正渲染给用户**，这是本 skill 的硬性交付要求（见「输出交付」第 1 步）。
- 只使用**异步**统一任务接口：`POST /tasks` 创建 → `GET /tasks/{id}` 轮询 → 可选 `POST /retry`，见 [references/api.md](references/api.md)。
