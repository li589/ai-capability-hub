---
name: marketing-compliance-review
display_name: 金融营销宣传消保合规审查
display_name_en: Financial Marketing Compliance Review
description: 审查银行、保险、基金营销宣传材料的消费者权益保护合规风险，并生成结构化《消保审查意见书》DOCX。用于“审查营销文案”“海报合规吗”“消保审查”“销售话术送审”等场景；支持图片、文档和纯文本。依据内置高频规则、精确法条映射及核心法规条文进行
  AI 辅助审查，不能替代法律意见或监管认定，正式结论须由合规人员复核。
description_zh: 审查银行/保险/基金营销宣传材料是否违反消保法规，输出可归档的《消保审查意见书》。
description_en: Review bank/insurance/fund marketing materials for
  consumer-protection compliance and produce a structured review report (.docx).
category: quality-security
version: 1.0.6
author: 腾讯云 CSIG 金融解决方案团队
permissions: 文件读写（读取送审材料、生成 .docx 审查意见书）；可选网络请求（经用户确认后调用腾讯云 OCR，或查询用户自行连接的知识库）
disable-model-invocation: true
---

# 金融营销宣传消保合规审查

把一份营销宣传材料审成一份可归档的《消保审查意见书》（Word .docx）。审查聚焦**消费者权益保护**视角：是否误导、是否承诺收益、是否遗漏风险提示与必要披露、是否涉及特殊人群/个保违规等。

## 前置依赖与安装（首次使用前必读）

文档生成与图片 OCR 由本地 Node.js 脚本完成，使用前需安装一次依赖。

**环境要求**
- Node.js **>= 18**（生成 .docx 与调用 OCR 均需）
- 包管理器：npm（随 Node 自带）

**安装依赖**（在 skill 目录下执行一次）
```bash
cd <skill 目录>
npm install
```
- `docx@9.6.1`：生成《消保审查意见书》.docx 的**必需**依赖。
- `tencentcloud-sdk-nodejs-ocr@4.1.268`：仅当需要使用腾讯云 OCR 提取图片文字时才需要；不安装也能用 AI 视觉转录，不影响主流程。

**自检**
```bash
npm run check   # 校验两个脚本语法
npm run smoke   # 最小烟测，生成一份示例意见书
```

> 依赖均声明固定版本（无 `@latest` / 区间），可在离线或隔离环境安装，完整声明见 `package.json`。

## 能力边界

**能做什么**
- 审查银行 / 保险 / 基金的营销宣传材料（广告海报、宣传文案、销售话术、培训课件、H5、短视频脚本）是否违反消保相关法规；
- 输出结构化《消保审查意见书》（风险等级 / 维度 / 原文摘录 / 命中规则 / 法条依据 / 修改建议）；
- 支持图片（OCR / AI 视觉）、文档、纯文本多源素材；可引用内置监管处罚判例增强说服力。

**不能做什么（重要）**
- ❌ 不替代法律意见或监管认定：本工具为 AI 辅助审查，审查结论须经具备资质的人员 / 合规部门复核后方可作为正式意见；
- ❌ 不做任何投资推荐、收益预测或"能否购买"类决策建议；
- ❌ 不保证零遗漏：规则库与法条映射持续完善，罕见违规可能未被覆盖；
- ❌ 不自动发布或阻断业务系统：仅生成审查报告，是否发布由人工决定。

## 工作流（5 步）

```
1. 收材料  → 拿到送审材料（图片/文档/文本），确认读取方式并提取原文
2. 对规则  → 逐条对照 references/review-rules.md 的禁用词库 + 审查要点
3. 定问题  → 对每个命中项：风险等级 + 维度 + 原文摘录 + 命中规则 + 法条依据 + 修改建议
4. 填 JSON  → 把审查结果写成结构化 JSON（见 references/input-schema.md）
5. 出文档  → 运行 scripts/generate_review.js 渲染为 .docx
```

> 高风险（🔴）问题必须全部整改后才能发布；中风险（🟡）建议修改；低风险（🟢）可选。

## 第一步：收材料、提取原文

- **图片**（海报/JPG/JPEG/PNG）：优先使用 AI 视觉读取；只有用户明确同意把图片发送至腾讯云 OCR 后，才运行 OCR 脚本。
  ```bash
  # 方式 A：腾讯云 OCR（会把图片发送至腾讯云，必须先取得用户确认）
  OCR_UPLOAD_CONFIRMED=1 \
    TENCENTCLOUD_SECRET_ID=xxx TENCENTCLOUD_SECRET_KEY=yyy \
    node scripts/ocr_extract.js <图片路径> [输出.txt]
  # 方式 B：AI 原生视觉识别（无需腾讯云 OCR 密钥）
  # 直接由 AI 读取图片并逐字转录所有文案，标注视觉呈现（字号对比、位置、配色）。
  ```
  > ⚠️ 无论哪种方式，转录后须在 `meta.source` 中标注来源类型：
  > `"文字转录"` / `"图片OCR(腾讯云)"` / `"图片AI视觉"` / `"文档读取"`。
- **文档**（.docx/.pdf）：使用平台文档能力读取正文与图片；OCR 脚本不直接接收 PDF。
- **纯文本/粘贴**：直接作为原文；`meta.source` 填 `"文字转录"`。
- 同时记录：送审类型（海报/话术/课件…）、关联产品名、送审部门/人（缺省填"（待填）"）。

## 第二步：对规则（核心，优先本地速查）

读取 **`references/review-rules.md`**，它是高频命中项的速查版，覆盖：
- 6 个审查维度（合法合规 / 真实准确 / 风险提示 / 信息完整 / 公平诚信 / 个保）
- 禁用词库（绝对化用语🔴、收益承诺🔴、误导性表述🟡、品牌混用🔴、特殊人群🔴、个保🟡）
- 逐项审查要点（2.1–2.9，每条标了风险等级）
- 风险分级与处置标准

**逐条对照**：把材料原文与禁用词库、审查要点比对，命中即记录。

**全文核查（重要）**：42 篇知识库原文（30 部法规全文、审查规则、意见模板、7 个处罚案例、监管规定原文）已托管至**腾讯云 COS**，按需拉取全文（详见 `references/kb-index.md` 的「文件名→公网 URL」映射表）。
- 拉取方式：拼接 `https://marketing-compliance-review-1300122096.cos.ap-guangzhou.myqcloud.com/kb/` + 文件名得到公网 URL，用 **WebFetch** 直接读取；或在终端运行 `python3 scripts/fetch_kb.py <文件名> <COS_BASE_URL>` 取全文。
- 例如核对《广告法》第 28 条：取 `kb-index.md` 中 `法规_04-中华人民共和国广告法.md` 对应 URL，拉取全文后引用即可，无需本地存储。
- 内置核心规则 `review-rules / legal-mapping / legal-corpus` 已随包携带，覆盖高频风险；COS 不可达时退回这些本地规则兜底，并标注「原文待复核」。

**引用同类型判例（增强权威）**：若需强化审查意见说服力，可查阅 `references/penalty-cases.md`，检索与本次违规类型相同的**已定性监管处罚判例**（金监总局及派出机构官方源），在「审查依据」或「修改建议」中引用并注明处罚文号即可。

**法条引用优先查映射表**：撰写「审查依据」时，先查 `references/legal-mapping.md` 取**精确条号 + 关键措辞**（严禁以区间代替精确适用条款），再按需查 `references/legal-corpus.md` 核对已收录的核心条文。
- **覆盖边界**：内置速查资料（review-rules / legal-mapping / legal-corpus）覆盖高频风险；完整法规原文与全部案例见 COS 托管快照（见 `references/kb-index.md`）。COS 不可达、效力状态不明或无法逐字核对的内容必须标注「原文待复核」。
- **可选增强**：需要核验完整原文或覆盖罕见场景时，按 `references/knowledge-base.md` 接入用户自行管理的知识库或查询监管部门公开来源。

## 第三步：定问题（每个命中项的结构）

对每个问题，准备以下字段（对应意见书"二、审查发现"表格）：

| 字段 | 说明 |
|---|---|
| `no` | 序号 |
| `title` | 风险类别简述，如 `标题"富利成长"暗示收益` |
| `risk` | `🔴 高风险` / `🟡 中风险` / `🟢 低风险`（决定配色） |
| `dimension` | 6 维度之一 |
| `excerpt` | 「引用具体原文」 |
| `rule` | 命中规则，如 `禁用词库 - 收益承诺类` / `审查要点 2.2` |
| `basis` | 法条依据数组，如 `["《广告法》第 28 条：…"]`；先查映射表，再核对已收录条文，仍不确定则标注「原文待复核」 |
| `suggestion` | 具体、可执行的修改方案 |

## 第四步：填 JSON

把审查结果写成结构化 JSON（封面 `meta` + 摘要 `summary` + 问题数组 `problems` + 评估 `evaluation` + 整改 `remediation` + 审批 `approvals`）。**完整字段与取值约定见 `references/input-schema.md`**。

草稿模式最简可用：只填 `meta.material` + `problems`。正式归档模式须填写编号、日期、送审部门、送审人、结论和风险等级，完整约定见 `references/input-schema.md`。

## 第五步：出文档

```bash
cd <skill>
# 依赖安装见上文「前置依赖与安装」；首次使用前执行一次 npm install
node scripts/generate_review.js <input.json> [output.docx]
```

- 输入：上一步的 JSON 文件路径。
- 输出：`.docx`；缺省文件名按 `meta.material` 推导为 `消保审查意见书_<材料名>.docx`。
- 草稿模式缺少业务编号时显示「待编号」；归档模式缺少必填字段时停止生成并返回字段级错误。
- 输出后向用户交付文件，并提示：🔴 高风险须全部整改后重审；终版按你方流程归档（机构自有知识库 / 合规系统），本 Skill 不绑定特定知识库。

## 资源

- **`scripts/generate_review.js`** — JSON → 标准《消保审查意见书》.docx 生成器（封面/摘要/逐项问题/总体评估/整改要求/审批记录，蓝主题 + 风险配色 + 页眉页脚页码）。
- **`scripts/ocr_extract.js`** — 图片→文字提取器（腾讯云 GeneralAccurateOCR 高精度识别；无密钥时输出兜底指引供 AI 视觉转录）。
- **`references/review-rules.md`** — 禁用词库 + 审查要点速查（高频命中项，免查库）。
- **`references/input-schema.md`** — 脚本 JSON 输入完整字段与取值约定。
- **`references/opinion-template.md`** — 意见书结构模板说明（填表参考）。
- **`references/penalty-cases.md`** — 监管处罚案例线索（7 例）；正式引用前须回到监管机关公开决定核验。
- **`references/legal-mapping.md`** — 违规模式 → 精确法条映射表（禁用区间引用，写「审查依据」时优先查）。
- **`references/legal-corpus.md`** — 已核对的核心法规条文摘录和专项规章索引；不等同于完整法规库。
- **`references/knowledge-base.md`** — 知识库接入与 COS 托管说明（在线增强 + 离线核心规则兜底指引）。
- **`references/kb-index.md`** — 42 篇知识库原文的「文件名 → COS 公网 URL」映射表；需全文时按此拉取。
- **`references/`** — 核心规则（随包携带，离线可用）：
  - review-rules、input-schema、legal-mapping、legal-corpus、opinion-template、penalty-cases、knowledge-base、kb-index 等。
- **`scripts/fetch_kb.py`** — 按文件名从 COS 拉取知识库原文的小工具（WebFetch 的命令行替代）。
- **`references/input-schema.json`** — 生成器输入的机器可读 JSON Schema。
- **`examples/`** — 草稿和归档模式的脱敏示例输入。
- **`references/input-schema.json`** — 生成器输入的机器可读 JSON Schema。
- **`examples/`** — 草稿和归档模式的脱敏示例输入。

## 注意事项

- **不杜撰法条**：条号、法规名、原文措辞不确定时优先查 `references/legal-corpus.md`，仍不确定则标注「原文待复核」，绝不凭记忆编造。
- **风险判定有依据**：每个 🔴 必须对应违反法律强制性规定；🟡 对应监管指引/内部规范。
- **原文摘录要准**：问题必须附可定位的原文，方便送审方核对与整改。
- **修改建议要可执行**：给"改成什么"，而非只说"不合规"。
- **外发须确认**：调用云 OCR 前必须取得用户确认，不得把未经授权的敏感材料发送到外部服务。
- **正式归档须复核**：归档模式必须由合规人员补齐业务编号并复核全部结论。
