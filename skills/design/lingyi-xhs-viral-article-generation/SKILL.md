---
name: lingyi-xhs-viral-article-generation
display_name: 小红书爆款图文生成
display_name_en: "viral-article-generation"
description_zh: "【零一数科·出品】小红书爆款图文生成（付费版）。写不出抓人的种草文、憋标题憋正文半天发不出去？给它产品/话题和几条卖点，选好平台、种草结构和品牌调性，几分钟出一版可直接发布的种草图文方案：钩子标题 + 能种草的正文文案，还能顺手出 AI 生图方案和提示词。支持小红书、公众号等平台，可选上传参考图让生成更贴你的实拍。把「写种草」从自己憋变成按几下就有底稿。触发词：小红书种草、公众号种草、种草文案、种草图文生成、AI种草。需要 python3 和技能目录下 config.json 中的 LY_API_KEY。"
description_en: "[Lingyi Tech] viral-article-generation. Struggling to write seeding copy that actually converts, or stuck on headlines and body for hours? Give it your product/topic and a few selling points, pick the platform, seeding structure, and brand tone — get a ready-to-publish seeding article plan in minutes: a hook title plus body copy that sells, with an optional AI image plan and prompts on the side. Supports Xiaohongshu, WeChat Official Accounts, and more; upload reference images (up to 3) to make the output match your real product shots. Turn writing seeding posts from a painful grind into a few clicks to a solid draft. Triggers: 小红书种草, 公众号种草, 种草文案, 种草图文生成, AI种草. Requires python3 and LY_API_KEY in skill config.json."
category: content-creation
version: 0.2.0
author: 小风、CoderPig、Awen
---

# 小红书爆款图文生成
> 版本：v0.2.0 · 作者：小风、CoderPig、Awen

输入产品或话题（`product_or_topic`）、核心卖点（`selling_points`），并选定目标平台（`target_platform`）、种草正文结构型（`seeding_structure`）、品牌调性（`brand_tone`），调用 01Claw 后端异步任务接口生成「**可发布的种草图文方案**」：钩子标题 + 正文文案 +（可选）AI 生图方案与生图 Prompt。开启 `generate_images` 时会实际生图并按 `image_count_config`（封面与配图张数）出图；关闭（默认）时只产方案与生图 Prompt。后端把整篇方案渲染成一段 Markdown 直接交付，同时附实际扣点 `total_points`。可选上传最多 3 张参考图辅助生成。

通过 **异步任务接口** 提交：`POST /api/v1/content/seeding-article-generation` **立即返回 `task_id`**，再通过 `GET /api/v1/content/seeding-article-generation/{id}` 轮询进度与结果。`completed` 后从 `data.markdown` 取报告、从 `data.total_points` 取实扣。接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

## 执行流程

按以下顺序执行，每一步都对应后续章节细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **取枚举（必做前置）**：跑 `python3 scripts/seeding_article.py --fetch-config` 拉取 `target_platform` / `seeding_structure` / `brand_tone` 三组实时枚举，把对应 `value` 记下，供用户选定后传入创建参数。**不要凭文档示例值硬填**——后端枚举可能随运营配置变化。
3. **收集信息**：与用户确认必填输入（缺项给默认）。详见「信息收集」。
4. **扣点确认（必做，跳过不得）**：跑脚本**前**向用户说明「本次任务预计扣点约 100 点起步（账户需 ≥100 点门槛，不足创建前会被 402 拦截），实际扣点以最终完成任务时的实际点数为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
5. **拆分轮询（关键，防会话中断）**：异步任务通常跑 1–10 分钟（开启 `generate_images` 时更耗时），WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成。改成「创建 + 多次短轮询」：
   a. **创建**：`python3 scripts/seeding_article.py --text "<产品或话题>" --target-platform <value> --seeding-structure <value> --brand-tone <value> --selling-points "卖点1" --selling-points "卖点2" --only-create`（有参考图就加 `--ref-image <路径>`，可多次），立即拿 `SEEDING_ARTICLE_TASK_ID` + `SEEDING_ARTICLE_STATUS` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。** 若带了 `--ref-image`，脚本会在此步先完成参考图上传再创建任务（上传失败按退出码 3/8/10/11，见下）。
   b. **告知用户**：用 task_id 诚实告知，例如「已提交，任务 ID xxx，约 1–10 分钟（开启生图更久）。我会持续跟踪进度，有进展同步给你。」**不要**承诺「完成后自动取回」——单轮阻塞做不到自动续接，要靠你主动循环轮询续接。
   c. **循环轮询**：立即跑 `python3 scripts/seeding_article.py --poll-task <id> --text "<同 a 的话题>" --out ./种草图文方案.md`（单次 ≤90s）。**`--poll-task` 必须带 `--text`**。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态成功）：进入「输出交付」。
      - **退出码 13**（仍进行中，**非失败**）：取 stdout 的 `SEEDING_ARTICLE_STATUS` / `SEEDING_ARTICLE_PROGRESS` / `SEEDING_ARTICLE_EAPSED` 转述，**立刻再跑一次 `--poll-task <id> --text "..."`** 继续。不要停。
      - **退出码 12**（任务真失败）：按「退出码处理」走失败话术；本 API 无 /retry，可重新创建（独立扣费，见偏差）。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。
   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」。
6. **进度应答**：用户中途问进度时，取最近一次 `--poll-task` 返回的状态自然转述；距上次轮询过一会儿可再跑一次现查。**禁止**回复「查不了任务状态 / 没有 task_id」。
7. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知实际扣点与查看方式。报告 markdown 由后端渲染，直接呈现，不二次加工。
8. **失败处理**：见「退出码处理」——非发起阶段失败（2/3/4/8）按对应话术；已发起但失败（11/12）告知「因网络原因本次任务执行失败，相应点数已返还」。退出码 13 **不是失败**，按第 5c 步续轮询。

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
4. **SSL 错误**：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用；若直连后端 IP `http://120.77.156.6:8001` 也需此设置，因其走 http 无 SSL）。

## 信息收集

收集必填项与可选增强项。可选项「可引导但不强制、缺省不传」（走后端默认）。**不要向用户暴露内部枚举值**（如 `xhs`/`aida`/`premium`），用自然语言代替（如「小红书」「AIDA 型」「高级」），让用户用自然语言选定后，你再用 `--fetch-config` 拉到的对应 `value` 传入。详见 [references/usage-notes.md](references/usage-notes.md)。

**必填**（五项，缺一创建会被 422/400 拦截）：

| 信息 | 说明 | CLI |
|------|------|-----|
| 产品或话题 | 要种草的产品名或话题，≤30 字 | `--text` |
| 核心卖点 | 1–3 条，单条 >20 字后端截断 | `--selling-points`（可多次） |
| 目标平台 | 小红书/公众号等，须先拉 `--fetch-config` 取实时 value | `--target-platform` |
| 种草正文结构型 | AIDA 型/痛点型/干货型等，须先拉 `--fetch-config` | `--seeding-structure` |
| 品牌调性 | 高级/专业等，须先拉 `--fetch-config` | `--brand-tone` |

**可选增强**（缺省走后端默认，不传即可）：

| 信息 | 说明 | CLI |
|------|------|-----|
| 参考文案 | 用户补充/参考文案，≤500 字 | `--reference-text` |
| 是否实际生图 | 不传=false 只产方案+生图 Prompt；传=true 实际生图 | `--generate-images` |
| 文字画进图 | 允许把文字画进图；仅 `--generate-images` 时有意义 | `--render-text-on-image` |
| 封面张数 | 0–3，默认 1 | `--cover-count` |
| 配图张数 | 0–8，默认 1 | `--image-count` |
| 参考图 | 本地图片，最多 3 张，png/jpg/jpeg/webp/gif/bmp，单张 ≤10MB | `--ref-image`（可多次） |
| 参考图提示词 | 参考图附加提示词，≤100 字；仅在有 `--ref-image` 时写入 | `--ref-image-desc` |

**枚举拉取说明**：目标平台 / 种草结构 / 品牌调性 三者均**必填**，且 value 必须取自 `--fetch-config` 实时返回的 options。先跑一次 `--fetch-config` 把三组 value 展示给用户选（用自然语言转述 label，用户选定后你回查对应 value 传入）。**严禁硬编码文档示例值**（如直接写 `xhs`/`pain`/`premium`）——后端枚举可能随运营配置变化；若某组 options 为空，创建必失败，应提示配置缺失、联系管理员，不要硬填。

**收集流程建议**（1 轮问清，缺省不阻塞）：
1. 触发后先拉一次 `--fetch-config` 拿三组枚举，同时看必填是否齐全。
2. 有缺失 → 一次性追问缺失项（只问 1 轮），并把三组枚举用自然语言列给用户选。
3. 仍不给 → 必填项缺失则不能创建（五项都必填，无法用默认兜底）；可选项缺失用默认继续。要点：一次问清、不挤牙膏、不展示技术字段名。

## 扣点与确认

本技能每次「新发起」任务会消耗点数（任务成功结算一次），整条链路对用户的扣点感知由你（assistant）贯穿：

- **执行前确认（必做，跳过不得）**：信息收集完成、API Key 就绪后，运行脚本**前**向用户说明并请其确认：
  > 本次任务预计扣点约 **100 点起步**，账户需 ≥100 点门槛（不足创建前会被 HTTP 402 拦截），实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准。是否继续？
  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。
- **执行成功后回告实际扣点**：把脚本透出的 `SEEDING_ARTICLE_POINTS_USED` 告诉用户（如「本次实际扣除 12 点」），为空时按「约 100 点起步（实际以服务端扣点为准，可在 01Claw 账户查看）」说明，并给出查看报告方式。
- **执行失败后告知点数返还**：任务已发起但未成功产出报告时（退出码 11/12），告知用户「因网络原因本次任务执行失败，相应点数已返还」并询问是否重试。
- **重试扣点提示（偏差）**：本 API 无 /retry，重试即重新创建**新任务**，**独立扣费**。问用户是否重试时如实说明「重新提交会再计费」。

> 扣点口径：脚本优先读服务端 `data.total_points`；未命中留空。约定估值仅作「约 100 点起步」提示，**不当作实扣数字**；最终以服务端实际扣除为准，真正实扣可在 01Claw 账户查看。

## 运行方式

```bash
# 0) 必做前置：拉取三组枚举（不创建任务、不扣点）
python3 scripts/seeding_article.py --fetch-config

# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1) 创建（立即拿 task_id，退出0）。⚠️ 三枚举 value 必须取自 --fetch-config
python3 scripts/seeding_article.py --text "<产品或话题>" \
  --target-platform <value> --seeding-structure <value> --brand-tone <value> \
  --selling-points "卖点1" --selling-points "卖点2" \
  --only-create
#   有参考图就追加（最多 3 张，脚本会先三步上传换 image_id 再创建）：
#   --ref-image /path/a.png --ref-image /path/b.jpg --ref-image-desc "白底正面"
#   要实际生图就追加：--generate-images --cover-count 1 --image-count 1

# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
#    ⚠️ --poll-task 必须带上和创建时相同的 --text
python3 scripts/seeding_article.py --poll-task <task_id> --text "<同上产品或话题>" --out ./种草图文方案.md
#   ↓ 退出13就再跑一次（同样带 --text），循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态，Web 端易被打断，慎用）——
python3 scripts/seeding_article.py --text "<产品或话题>" \
  --target-platform <value> --seeding-structure <value> --brand-tone <value> \
  --selling-points "卖点1" --selling-points "卖点2" --out ./种草图文方案.md

# 失败后重新创建（偏差：本 API 无 /retry，--retry-task 实为重建新任务、独立扣费；须重供全部参数）
python3 scripts/seeding_article.py --retry-task <旧task_id参考> --text "<产品或话题>" \
  --target-platform <value> --seeding-structure <value> --brand-tone <value> \
  --selling-points "卖点1" --selling-points "卖点2" --out ./种草图文方案.md
```

可选参数：

- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `种草图文方案-<task_id>.md`。
- `--insecure`：跳过 SSL 校验（直连后端 IP `http://120.77.156.6:8001` 时需此设置）。
- `--timeout 90`：单次轮询等待上限秒数（默认 90）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- `--text -`：从 stdin 读产品或话题。
- 业务参数见「信息收集」表（`--reference-text` / `--generate-images` / `--render-text-on-image` / `--cover-count` / `--image-count` / `--ref-image` / `--ref-image-desc` / `--origin` / `--origin-method`）。

## 输出交付

成功时 stdout 形如：

```text
SEEDING_ARTICLE_POINTS_USED=<本次实际扣点，可能为空>
SEEDING_ARTICLE_PLAN_POINTS=100
SEEDING_ARTICLE_REPORT_FILE=<报告文件绝对路径或空>
SEEDING_ARTICLE_TASK_ID=<任务 id，便于重试>
=== SEEDING_ARTICLE_REPORT_START ===
<后端渲染的种草图文方案 Markdown：钩子标题/正文文案/生图方案与 Prompt/标签等>
=== SEEDING_ARTICLE_REPORT_END ===
```

交付时**按顺序**做三件事（缺一不可）：

1. **渲染报告（最重要）**：截取两个分隔符**之间**的 Markdown 正文，作为 Markdown 渲染呈现给用户——让用户看到真正的标题/段落/列表/提示词排版，而不是带分隔符或 `\n` 字面的原始文本。
   - 不要展示分隔符行、`SEEDING_ARTICLE_*= ` 协议行。
   - 不要只说「报告已生成」却不渲染正文。**正文必须出现在回复里**。过长至少完整渲染前 2–3 个二级标题段并说明完整报告已落盘。
   - 正文由后端渲染，**直接渲染，不要二次加工、不本地改写/总结/重排**（文档明确：`completed` 后输出 `data.markdown` 原样）。`completed` 但缺 markdown → 透出「结果暂不可用」，**不本地伪造正文**。后端 `markdown` 已自带一级标题，脚本检测到 H1 即原样输出、不再前置标题、不插分隔线（避免两个 H1）；仅无 H1 时脚本才补 `# 种草图文方案：<产品或话题摘要>` 兜底。
2. **告知实际扣点**：非空说「本次实际扣除 N 点」；空说「约 100 点起步（实际以服务端扣点为准，可在 01Claw 账户查看）」。可在正文外附「本次消耗 N 点」，但**不要把点数嵌进方案正文**。
3. **告知报告查看方式**：报告已渲染在上方对话中；同时已保存为 MD 文件，路径见 `SEEDING_ARTICLE_REPORT_FILE`（绝对路径）。脚本对落盘做了三级兜底（`--out` → 当前目录 → `/tmp`），只要终态有 markdown 就一定生成 md 文件。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，不涉扣点。 |
| 3 | 参数非法（含 400/422） | 补全后重试。如缺必填枚举、卖点条数越界、参考图扩展名不支持/超 3 张/单张超 10MB、`--cover-count`/`--image-count` 越界、夹带未声明字段等。任务未发起，不涉扣点。 |
| 4 | 余额不足（402） | 账户可用点数低于创建门槛（100 点）。透出 `recharge_url`（若有，本 API 通常仅 message 提示），引导充值后重新创建。任务未发起，不涉扣点。 |
| 8 | 401 key 无效 | 重新获取覆盖 `config.json` 后重试。任务未发起，不涉扣点。 |
| 10 | 其他 4xx（含 403/404） | 403 为「当前 Key 无权访问该任务」，停止轮询、确认 Key（轮询须用创建时的同一 Key）；404 为任务不存在。透出服务端 message，按提示修正。4xx 一般未扣。 |
| 11 | 5xx / 网络错误 | 告知「因网络原因本次任务执行失败，相应点数已返还」，转述 stderr 原因，询问是否稍后重试。**注**：若发生在参考图上传阶段，任务未发起、未扣点（stderr 会注明「任务未发起、未扣点」）。 |
| 12 | 已发起但任务未成功 | status 为 `failed`/`timeout` 等，或终态但无报告，告知「点数已返还」；本 API 无 /retry，可重新创建（独立扣费，见偏差），询问用户是否重试。**特例**：若 stdout 正文是「⚠️ 任务已完成…报告正文暂未返回…续查指引」这类**兜底 md**（status=completed 但宽限 60s 后 markdown 仍未落库），**勿当真实种草图文渲染/发布**——文件已落盘仅作兜底，应据指引建议用户稍后 `--poll-task` 续查或重提。 |
| 13 | 进行中，未到终态（**非失败**） | **不涉及扣点返还**——取 stdout 进度转述，立即再跑 `--poll-task` 续轮询，循环到终态(0)或真失败(12)。 |

> 任务已发起但未出报告（11、12）统一告知「点数已返还」并问是否重试；13 是「进行中、可续轮询」，既非失败也不返还；任务未发起到位（2/3/4/8）不涉扣点，正常引导修正。

未知错误**不要自行判定失败**；按表对号入座，按 stderr 透出的原因处理。

## 免责声明

生成的种草图文由模型依据产品话题、卖点与创作参数产出，封面图与配图（开启 `generate_images` 时）均为 AI 生成，文案可能存在事实偏差或不符合品牌调性；**正式发布前请人工复核**信息准确性、合规性与品牌一致性，重大发布以人工把关为准。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 报告 markdown 由后端渲染，skill 不做模板、不本地改写；后端 `markdown` 自带 H1，脚本检测到 H1 即原样输出、不前置标题，仅无 H1 时才补 `# 种草图文方案：<产品或话题摘要>`。
- 最终 MD 由脚本一次性拼接覆写 `--out`，agent 不要手动追加/改写输出文件。
- **交付报告时务必把分隔符之间的 Markdown 真正渲染给用户**，这是硬性交付要求。
- 只使用异步接口：`POST /api/v1/content/seeding-article-generation` 创建 → `GET /{id}` 轮询 → 可选 `GET /config` 取三组枚举 → 可选「取预签名→PUT→确认」上传参考图；**无 `/retry`**，见偏差，见 [references/api.md](references/api.md)。
