---
name: lingyi-article-sticker-viral-generator
display_name: 公众号贴图号爆款生成
display_name_en: "Article & Sticker Viral Generator"
description_zh: "【零一数科·出品】公众号贴图号爆款生成（付费版）。输入选题、产品卖点、目标受众，一键生成可直接发布的贴图号/公众号爆款图文（封面图+内文配图+正文+候选标题，渲染成 Markdown）。贴图号生成、公众号图文生成、爆款图文生成。需要 python3 和技能目录下 config.json 中的 LY_API_KEY。"
description_en: "[Lingyi Tech] Generate ready-to-publish viral WeChat article and sticker content (cover, inline images, body copy, candidate titles) from topic, product selling points and target audience."
category: content-creation
version: 0.1.0
author: 小风、CoderPig、Awen
---

# 公众号贴图号爆款生成
> 版本：v0.1.0 · 作者：小风、CoderPig、Awen

> ⚠️ **偏差声明（本 API 与标准范式的差异，运行脚本前请知悉）**
>
> 1. **无重试接口**：本 API **没有 `POST /{id}/retry`**。任务 `failed`/`timeout` 后，需用**原始参数整体重新创建**新任务。脚本的 `--retry-task` 入口保留（保持三模式一致），但**实现是「重新创建新任务」**（拿到新的 `task_id`），而非原地续跑——调用时必须重供 `--text` 与全部业务参数以重建请求体。
> 2. **每次重提独立扣费**：失败后重新创建是一次新的可计费提交，**不**享受「已成功模块不重跑」。向用户转述失败重试时须如实说明「重新提交会再计费」。
> 3. **扣点字段为 `data.total_points`**（顶层整数，如 15），非标准 `data.billing.total_points`；脚本已兼容，成功后回告此值。
> 4. **有 `GET /config` 接口**拉取 `tone`（内容调性）枚举，文档**禁止硬编码示例值**。脚本提供 `--fetch-config` 拉取实时枚举；`tone` 默认不传，走后端默认。
> 5. **后端 `data.markdown` 自带一级标题**（`# 标题`），文档要求「原样使用、不重新组织」。脚本检测到 H1 即原样输出、不前置脚本标题、不插分隔线（避免两个 H1）；仅无 H1 时才前置 `# 爆款图文：<选题摘要>` 兜底。
> 6. **本 API 无幂等机制**：文档无 `idempotency` 字段，§3.2「只能含参数表声明字段、否则 422」。标准 §9 的「`X-Idempotency-Key` 头 + body `idempotency_key`」**不适用**——脚本不发幂等头、不注入 body `idempotency_key`、无 `--idempotency-key` CLI。重复提交会新建任务、独立计费，防重复扣点由人/调用方「同一意图不重复 POST」保证。
>
> 上述偏差已写入脚本与 [references/api.md](references/api.md)。

输入选题（topic）、正文字数、产品信息（名称+卖点）和目标受众（描述+痛点），调用 01Claw 后端异步任务接口生成「**可直接发布的爆款图文**」：封面图 + 正文配图 + 正文文案 + 候选标题，后端按 `content_format`（贴图号 `xiaolvshu` 或公众号 `image_message`）渲染成一段 Markdown 直接交付。支持两种内容形式：

- **贴图号（默认）**：朋友圈式紧凑图文编排，封面/配图比例 3:4（默认）或 1:1。
- **公众号**：封面+正文配图，封面固定 2.35:1，配图 16:9（默认）/3:4/1:1。

通过 **异步任务接口** 提交：`POST /api/v1/content/article-generation` **立即返回 `task_id`**，再通过 `GET /api/v1/content/article-generation/{id}` 轮询进度与结果。`completed` 后从 `data.markdown` 取报告、从 `data.total_points` 取实扣。接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

## 执行流程

按以下顺序执行，每一步都对应后续章节细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **收集信息**：与用户确认必填输入（缺项给默认）。详见「信息收集」。
3. **扣点确认（必做，跳过不得）**：跑脚本**前**向用户说明「本次任务预计扣点 60 点起步，最终以服务端实际扣除为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
4. **拆分轮询（关键，防会话中断）**：异步任务通常跑 1–2 分钟，WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成。改成「创建 + 多次短轮询」：
   a. **创建**：`python3 scripts/article_generation.py --text "<话题>" --word-count ... --product-name ... --selling-points ... --audience-desc ... --pain-points ... --only-create`，立即拿 `ARTICLE_GEN_TASK_ID` + `ARTICLE_GEN_STATUS` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。**
   b. **告知用户**：用 task_id 诚实告知，例如「已提交，任务 ID xxx，约 1–2 分钟。我会持续跟踪进度，有进展同步给你。」**不要**承诺「完成后自动取回」——单轮阻塞做不到自动续接，要靠你主动循环轮询续接。
   c. **循环轮询**：立即跑 `python3 scripts/article_generation.py --poll-task <id> --text "<同 a 的话题>" --out ./爆款图文.md`（单次 ≤90s）。**`--poll-task` 必须带 `--text`**。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态成功）：进入「输出交付」。
      - **退出码 13**（仍进行中，**非失败**）：取 stdout 的 `ARTICLE_GEN_STATUS` / `ARTICLE_GEN_PROGRESS` / `ARTICLE_GEN_EAPSED` 转述，**立刻再跑一次 `--poll-task <id> --text "..."`** 继续。不要停。
      - **退出码 12**（任务真失败）：按「退出码处理」走失败话术；本 API 无 /retry，可重新创建（独立扣费，见偏差）。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。
   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」。
5. **进度应答**：用户中途问进度时，取最近一次 `--poll-task` 返回的状态自然转述；距上次轮询过一会儿可再跑一次现查。**禁止**回复「查不了任务状态 / 没有 task_id」。
6. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知实际扣点与查看方式。报告 markdown 由后端按内容形式渲染，直接呈现，不二次加工。
7. **失败处理**：见「退出码处理」——非发起阶段失败（2/3/4/8）按对应话术；已发起但失败（11/12）告知「因网络原因本次任务执行失败，相应点数已返还」。退出码 13 **不是失败**，按第 4c 步续轮询。

任一步异常按「退出码处理」表对号入座，**不要自行判定失败**。

## 鉴权

Token 取「技能目录」（SKILL.md 所在目录）下 `config.json` 的 `LY_API_KEY` 字段，回退环境变量 `LY_API_KEY`。请求头 `Authorization: Bearer <api_key>` + ``。`config.json` 形如：

```json
{ "LY_API_KEY": "你的密钥" }
```

运行前先确认 key：

1. **检查是否已有 key**：读 `config.json` 的 `LY_API_KEY` 是否非空；无则看环境变量 `LY_API_KEY`。任一有值即就绪。
2. **缺失则引导用户获取**：前往 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy` 取 API Key，把 key 直接发给你；收到后写入 `config.json` 的 `LY_API_KEY` 字段（保留其它内容）再继续。该文件已被 `.gitignore` 忽略。
3. **鉴权失败（退出码 8）**：key 失效或过期，重新获取并覆盖写 `config.json` 后重试，不反复用同一失效 key。
4. **SSL 错误**：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用）。

## 信息收集

收集必填项与可选增强项。可选项「可引导但不强制、缺省不传」（走后端默认）。**不要向用户暴露内部枚举值**（如 `xiaolvshu`/`image_message`/`knowledge`），用自然语言代替。详见 [references/usage-notes.md](references/usage-notes.md)。

**必填**：

| 信息 | 说明 | CLI |
|------|------|-----|
| 选题/话题 | 文章核心主题 | `--text` |
| 正文字数 | 100–50000 | `--word-count` |
| 产品名称 | 要推的产品 | `--product-name` |
| 产品卖点 | ≥1 条 | `--selling-points`（可多次） |
| 目标受众描述 | 人群画像 | `--audience-desc` |
| 受众痛点 | ≥1 条 | `--pain-points`（可多次） |

**可选增强**（缺省走后端默认，不传即可）：

| 信息 | 说明 | CLI |
|------|------|-----|
| 内容形式 | 贴图号（默认）/公众号 | `--content-format` |
| 封面比例 | 需与内容形式匹配 | `--cover-ratio` |
| 配图比例 | 需与内容形式匹配 | `--body-ratio` |
| 内容调性 | 「知识型」等，需先 `--fetch-config` 拉取实时枚举 | `--tone` |
| 主图/封面数量 | 1–5，默认 1 | `--main-image-count` |
| 正文配图数量 | 1–5，默认 1 | `--inset-image-count` |
| 候选标题数量 | 1–5，默认 3 | `--title-count` |
| 产品价格 / 价格带 / 决策类型 | 增强 product | `--product-price` / `--price-band` / `--decision-type` |
| 受众年龄段 / 性别 | 增强 target_audience | `--audience-age` / `--audience-gender` |

**调性（tone）说明**：内容调性为可选项，默认不传走后端默认调性。若用户要指定调性，先跑 `--fetch-config` 拉取后端实时枚举展示给用户选，选定后用 `--tone` 传入。**严禁硬编码文档示例值**——后端枚举可能变化。

**收集流程建议**（1 轮问清，缺省不阻塞）：
1. 触发后先看必填是否齐全。
2. 有缺失 → 一次性追问缺失项（只问 1 轮）。
3. 仍不给 → 用默认继续，不阻塞。要点：一次问清、不挤牙膏、不展示技术字段名。

## 扣点与确认

本技能每次「新发起」任务会消耗点数（任务成功结算一次），整条链路对用户的扣点感知由你（assistant）贯穿：

- **执行前确认（必做，跳过不得）**：信息收集完成、API Key 就绪后，运行脚本**前**向用户说明并请其确认：
  > 本次任务预计扣点 **60 点起步**，最终以服务端实际扣除的为准（任务越复杂可能越高）。是否继续？
  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。
- **执行成功后回告实际扣点**：把脚本透出的 `ARTICLE_GEN_POINTS_USED` 告诉用户（如「本次实际扣除 15 点」），为空时按「预计 60 点起步（实际以服务端扣点为准，可在 01Claw 账户查看）」说明，并给出查看报告方式。
- **执行失败后告知点数返还**：任务已发起但未成功产出报告时（退出码 11/12），告知用户「因网络原因本次任务执行失败，相应点数已返还」并询问是否重试。
- **重试扣点提示（偏差）**：本 API 无 /retry，重试即重新创建**新任务**，**独立扣费**。问用户是否重试时如实说明「重新提交会再计费」。

> 扣点口径：脚本优先读服务端 `data.total_points`；未命中留空。约定估值仅作「60 点起步」提示，**不当作实扣数字**；最终以服务端实际扣除为准，真正实扣可在 01Claw 账户查看。

## 运行方式

```bash
# 0) 可选：拉取内容调性（tone）实时枚举（不创建任务、不扣点）
python3 scripts/article_generation.py --fetch-config

# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1) 创建（立即拿 task_id，退出0）
python3 scripts/article_generation.py --text "<选题>" \
  --word-count 800 --product-name "产品名" --selling-points "卖点1" --selling-points "卖点2" \
  --audience-desc "25-35岁职场女性" --pain-points "痛点1" --pain-points "痛点2" \
  --only-create
# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
#    ⚠️ --poll-task 必须带上和创建时相同的 --text
python3 scripts/article_generation.py --poll-task <task_id> --text "<同上选题>" --out ./爆款图文.md
#   ↓ 退出13就再跑一次（同样带 --text），循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态，Web 端易被打断，慎用）——
python3 scripts/article_generation.py --text "<选题>" --word-count 800 --product-name "..." \
  --selling-points "..." --audience-desc "..." --pain-points "..." --out ./爆款图文.md

# 失败后重新创建（偏差：本 API 无 /retry，--retry-task 实为重建新任务、独立扣费；须重供全部参数）
python3 scripts/article_generation.py --retry-task <旧task_id参考> --text "<选题>" \
  --word-count 800 --product-name "..." --selling-points "..." --audience-desc "..." --pain-points "..." \
  --out ./爆款图文.md
```

可选参数：

- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `爆款图文-<task_id>.md`。
- `--insecure`：跳过 SSL 校验。
- `--timeout 90`：单次轮询等待上限秒数（默认 90）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- `--text -`：从 stdin 读选题文本。
- 业务参数见「信息收集」表（`--content-format` / `--cover-ratio` / `--body-ratio` / `--tone` / `--main-image-count` / `--inset-image-count` / `--title-count` / `--product-price` / `--price-band` / `--decision-type` / `--audience-age` / `--audience-gender`）。

## 输出交付

成功时 stdout 形如：

```text
ARTICLE_GEN_POINTS_USED=<本次实际扣点，可能为空>
ARTICLE_GEN_PLAN_POINTS=60
ARTICLE_GEN_REPORT_FILE=<报告文件绝对路径或空>
ARTICLE_GEN_TASK_ID=<任务 id，便于重试>
=== ARTICLE_GEN_REPORT_START ===
<后端渲染的爆款图文 Markdown：标题/封面图/内文配图/正文/行动引导/标签>
=== ARTICLE_GEN_REPORT_END ===
```

交付时**按顺序**做三件事（缺一不可）：

1. **渲染报告（最重要）**：截取两个分隔符**之间**的 Markdown 正文，作为 Markdown 渲染呈现给用户——让用户看到真正的标题/图片/段落/标签排版，而不是带分隔符或 `\n` 字面的原始文本。
   - 不要展示分隔符行、`ARTICLE_GEN_*= ` 协议行。
   - 不要只说「报告已生成」却不渲染正文。**正文必须出现在回复里**。过长至少完整渲染前 2–3 个二级标题段并说明完整报告已落盘。
   - 正文由后端按 `content_format` 渲染，**直接渲染，不要二次加工、不本地改写/总结/重排**（文档明确：`completed` 后输出 `data.markdown` 原样，不要让本地模型 rewrite/summarize/reorganize）。`completed` 但缺 markdown → 透出「结果暂不可用」，**不本地伪造正文**。后端 `markdown` 已自带一级标题（`# 标题`），脚本检测到 H1 即原样输出、不再前置标题、不插分隔线（避免两个 H1）；仅无 H1 时脚本才补 `# 爆款图文：<选题摘要>` 兜底。
2. **告知实际扣点**：非空说「本次实际扣除 N 点」；空说「预计 60 点起步（实际以服务端扣点为准，可在 01Claw 账户查看）」。可在正文外附「本次消耗 N 点」，但**不要把点数嵌进文章正文**。
3. **告知报告查看方式**：报告已渲染在上方对话中；同时已保存为 MD 文件，路径见 `ARTICLE_GEN_REPORT_FILE`（绝对路径）。脚本对落盘做了三级兜底（`--out` → 当前目录 → `/tmp`），只要终态有 markdown 就一定生成 md 文件。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，不涉扣点。 |
| 3 | 参数非法（含 400/422） | 补全后重试。如内容形式/比例不匹配、缺必填项、夹带禁止字段。任务未发起，不涉扣点。 |
| 4 | 余额不足（402） | 透出 `recharge_url`（若有），引导充值后重新创建。任务未发起，不涉扣点。 |
| 8 | 401 key 无效 | 重新获取覆盖 `config.json` 后重试。任务未发起，不涉扣点。 |
| 10 | 其他 4xx（含 403/404） | 403 为「当前 Key 无权访问该任务」，停止轮询、确认 Key；404 为任务不存在。透出服务端 message，按提示修正。4xx 一般未扣。 |
| 11 | 5xx / 网络错误 | 告知「因网络原因本次任务执行失败，相应点数已返还」，转述 stderr 原因，询问是否稍后重试。 |
| 12 | 已发起但任务未成功 | status 为 `failed`/`timeout` 等，或终态但无报告。告知「点数已返还」；本 API 无 /retry，可重新创建（独立扣费，见偏差），询问用户是否重试。 |
| 13 | 进行中，未到终态（**非失败**） | **不涉及扣点返还**——取 stdout 进度转述，立即再跑 `--poll-task` 续轮询，循环到终态(0)或真失败(12)。 |

> 任务已发起但未出报告（11、12）统一告知「点数已返还」并问是否重试；13 是「进行中、可续轮询」，既非失败也不返还；任务未发起到位（2/3/4/8）不涉扣点，正常引导修正。

未知错误**不要自行判定失败**；按表对号入座，按 stderr 透出的原因处理。

## 免责声明

生成的图文由模型依据选题、产品卖点与受众画像产出，封面图与配图均为 AI 生成，文案可能存在事实偏差或不符合品牌调性；**正式发布前请人工复核**信息准确性、合规性与品牌一致性，重大发布以人工把关为准。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 报告 markdown 由后端渲染，skill 不做模板、不本地改写；后端 `markdown` 自带 H1，脚本检测到 H1 即原样输出、不前置标题，仅无 H1 时才补 `# 爆款图文：<选题摘要>`。
- 最终 MD 由脚本一次性拼接覆写 `--out`，agent 不要手动追加/改写输出文件。
- **交付报告时务必把分隔符之间的 Markdown 真正渲染给用户**，这是硬性交付要求。
- 只使用异步接口：`POST /api/v1/content/article-generation` 创建 → `GET /{id}` 轮询 → 可选 `GET /config` 取调性枚举；**无 `/retry`**，见偏差，见 [references/api.md](references/api.md)。
