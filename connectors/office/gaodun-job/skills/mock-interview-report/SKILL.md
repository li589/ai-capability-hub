---
name: mock-interview-report
display_name: 模拟面试报告
display_name_en: Mock Interview Report
description: 模拟面试抽题与评估报告生成。通过 mcp 工具 draw_questions 一次性抽取最多 3 道面试题，一次性展示题目并收集用户全部回答后，按 服务端单题评估逻辑 的逻辑生成单题评分与面试建议，再按 服务端报告聚合逻辑 / 报告排序与展示逻辑 的结构聚合并输出 HTML 分析报告。当用户要求「抽面试题」「模拟面试」「面试题分析报告」「评估我的面试回答」时使用。
description_zh: 模拟面试抽题与评估报告生成。通过 mcp 工具 draw_questions 一次性抽取最多 3 道面试题，一次性展示题目并收集用户全部回答后，按 服务端单题评估逻辑 的逻辑生成单题评分与面试建议，再按 服务端报告聚合逻辑 / 报告排序与展示逻辑 的结构聚合并输出 HTML 分析报告。当用户要求「抽面试题」「模拟面试」「面试题分析报告」「评估我的面试回答」时使用。
description_en: Generates mock-interview question drawing and evaluation reports. Uses the draw_questions MCP tool to draw up to three interview questions at once, presents them together, collects the user's answers, then produces per-question scores and coaching advice following the server-side evaluation logic, and aggregates everything into an HTML analysis report aligned with the server-side report structure. Use when the user asks to draw interview questions, run a mock interview, get an interview analysis report, or evaluate their interview answers.
category: 15-Education
version: 1.0.0
author: 上海高顿教育科技有限公司
---

# Mock Interview Report（模拟面试抽题与评估报告）

## Overview

完整走一遍「抽题 -> 作答 -> 评估 -> 报告」流程，逻辑严格对齐服务端线上实现，不绑定真实用户/面试信息：

1. 抽题：`服务端抽题接口`（纯抽题接口，不依赖用户/面试信息）。**抽题动作由 mcp 工具 `draw_questions` 代为执行**——工具内部组装请求、解析岗位、拼接维度并返回标准化题目 JSON，本 skill 不再直接调接口。
2. 评估：`服务端单题评估逻辑`
   - 面试建议：`面试建议入参装配` -> `面试建议生成` -> `面试建议解析规则`
   - 单题评分：`单题评分入参装配` -> `单题评分生成` -> `单题评分解析规则`
3. 报告：`服务端报告聚合逻辑`（每题分数、维度聚合、总分、总评）+ `报告排序与展示逻辑`（排序与展示）

所有输出格式、分数计算、排序规则必须与 `references/report-logic.md` 完全一致，不得自行发明格式（如用 `#` 切分单题评分——线上解析并不是这样）。

## 前置检查（必读）

开始流程前依次检查：

1. **岗位定位**：抽题工具 `draw_questions` 支持定位方式：
   
   - `job_description`（自然语言描述，推荐）：如「银行/柜员」「公务员/省考/山东」「事业单位/北京/省直」。命中后自动确定 jobId/projectId/industryId 及对应 prompt 变体。
   
   用户未指定岗位时，需要引导用户指定岗位抽题。
   **注意（多岗位重名）**：同一项目下不同行业可能有同名岗位（如公务员项目「山东」同时存在于省考行业与选调行业），自然语言解析可能落到错误行业（且该行业题库可能为空）。应尽量用「项目/行业/岗位」三级限定描述（如 `job_description="公务员/省考/山东"`），命中多岗位时提示用户确认。
   **注意（题库为空）**：服务端返回 `组题失败，题库无可用题目`（status=10006060）表示该岗位在环境内无可用题库。此时不要伪造题目：先换行业/岗位探测（多换几种 `job_description` 组合），仍为空则告知用户并让其选择：用公考真题手动出题 / 换有题库的项目（如银行）继续 。
2. **Prompt 变体**：直接取自抽题返回的 `meta.promptIds`（`advice`/`generalComment`/`overall`），无需手动查表。已内置线上 prompt 正文（见 references 三个 prompt 文件）：
   
   - 100520929 公务员：advice=2167 / generalComment=893 / overall=2147
   - 1000648 银行：advice=2169 / generalComment=585
   - 100534841 央国企：advice=2169 / generalComment=585
   - 100535479（注：此 projectId 当前不在岗位映射表中）：advice=2177 / generalComment=1874
   - 100523443 事业单位：暂用通用版 2169/585（线上配置未提供，待确认）
   `meta.promptIds.overall` 为 null 时（银行/央国企等），总评按同一输入/输出契约直接生成。若用户提供了更新的 prompt 文本，替换对应「Prompt 正文」区域（输入/输出格式契约已按线上解析代码固化，不得改动）。

## Workflow

### Step 1: 抽题（最多 3 道）

调用 mcp 工具 `draw_questions`。参数均非必填：

| 参数 | 类型 | 说明 |
|---|---|---|
| `job_description` | string | 岗位自然语言描述（如「银行/柜员」「公务员/省考/山东」） |
| `interview_type` | string | 面试类型，默认 `REAL_QUESTION`，枚举 `REAL_QUESTION` |
| `question_configs` | array | 题目配置（顺序即题号顺序）；缺省为岗位特色题/英语题/专业题各一道。每项含 `id`(题号)、`question_type`(整数编码) |
| `dimension_ids` | array<int> | 考核维度 id 集合，缺省空 |
| `filter_question_ids` | array<string> | 需过滤（不再抽取）的题目 id 集合，缺省空 |
| `max_questions` | integer | 最多返回题目数，1~3，默认 3 |

`question_type` 编码：0 岗位特色题 / 1 英语题 / 2 专业题 / 4 行业常规题 / 42 自我介绍题 / 43 主题陈述题 / 44 综合面试题（**不可传 3 个性题——服务端不返回**）。

典型调用（不指定 question_configs，用缺省题型组合，抽 3 道）：

```
draw_questions(job_description="", max_questions=3)
```

返回单对象 JSON：

```
{
  "meta": { "jobId", "projectId", "projectName", "industryId", "jobName",
            "promptIds": {"advice", "generalComment", "overall"} },
  "questions": [{
    "questionNo", "questionId", "groupId", "bizId", "questionStem",
    "questionType"(int), "questionTypeName", "isProbe",
    "dimensionIds"(int[]), "dimensionNames"(中文逗号分隔),
    "assessmentLatitude"(评分标准全文), "evaluation"(维度简介拼接),
    "questionRefer"(array), "examineModule"
  }],
  "note": ""
}
```

- `meta.promptIds` 直接用于 Step 3 的 prompt 变体选择；`meta.projectId` 用于下文校验变体归属。
- 每题的 `assessmentLatitude`/`evaluation`/`dimensionNames` 已由工具按维度配置真实拼接（分别对齐 `带分维度列表拼装`/`维度列表拼装`/`generalDimensionListSimple`），下游评估直接取用，不得自行重拼。
- 服务端规则（见 `references/api.md`）：`interviewType` 不可为 `COMPOSE_QUESTION`；个性题（questionType=3）会被服务端跳过；同一场不会重复出题。
- 工具调用失败或返回空题库时直接报出并按前置检查 1 的换岗兜底处理，不要伪造题目。

### Step 2: 一次性展示题目并收集回答

将全部题目一次性展示给用户，每题包含：题号、题型名称、题干、考核维度（dimensionIds）。提示用户按题号逐题作答。

- 允许跳过：跳过的题不调用两个评估，单题分数记 0，各考核维度按 0 分参与维度平均（对齐线上缺失记录按 0 计的逻辑），辅导建议留空。

### Step 3: 逐题评估（两步独立，格式契约见 references/report-logic.md）

按 Step 1 返回的 `meta.promptIds` 选择 prompt 变体（见前置检查 2），后续两次评估均使用同一变体。

对每道已作答题目，先按 `joinQuestionWithAnswer` 格式拼接问答文本：

```
问题:{题干}
回答:{用户回答}
```

（本 skill 抽题配置 isProbe=false，无追问段落；追问格式见 report-logic.md 备注即可，不模拟。）

然后执行两个相互独立的评估（线上各自 try-catch，一个失败不影响另一个）：

1. **面试建议**（服务端面试建议生成逻辑）：使用 `references/prompt-coaching-advice.md` 所选变体的 prompt，替换 `{{$target_job}}`、`{{$evaluation}}`（取自抽题返回的同名字段，对齐 `维度列表拼装`）、`{{$student_resume}}`、`{{$question_refer}}`（逐条拼为 `参考范例1：xxx\n`）变量（2169/2177 的 `{{$skills}}`/`{{$goals}}`/`{{$rules}}` 见 `references/prompt-skill-map.md` 原样替换，2167 的 `{{$structure}}` 置空）。输出**为 JSON**：`{"你的回答优点在于":"...","不足之处及改进建议":"...","作答范例":"..."}`（服务端按中文 key 及其别名映射反序列化；JSON 不合法时 fallback 为 `回答优点#改进建议#参考作答` 按 `#` 切分三段）。展示时三段分别加前缀「你的回答优点在于：」「不足之处及改进建议：」「作答范例：」（对齐 `建议字段填充` 的 Constants 前缀）。
2. **单题评分**（服务端单题评估逻辑）：使用 `references/prompt-single-evaluation.md` 所选变体的 prompt，替换 `{{$target_job}}`、`{{$assessment_latitude}}`（取自抽题返回的同名字段，对齐 `带分维度列表拼装`；公考 893 为 `{{$evaluation}}`）变量。输出为**每个考核维度一段、段与段之间空行分隔**的三行结构（对齐 `单题评分解析` 的解析：按 `\n\n` 分段、段首须为数字）：

   ```
   1、维度名：
   分数：16分
   建议：评语内容
   ```

   每个维度满分 20 分。解析规则：维度名=首行 `、`/`.` 之后到 `：` 之间；分数=第二行 `：` 后到最后一个 `分` 之间（无「分」则取到行尾）；建议=第三行 `：` 之后；分数转数字失败记 0。回答跑题（输出含「你的回答与本题无关」）时该题各维度记 0 分。

**本题分数**（对齐 `单题得分计算`，百分制）：

```
本题分数 = Σ各维度 floor(维度分 / 20 × 权重)
```

权重等权分配（`维度分计算`）：`floor(100/维度数)`，最后一个维度取 `100 - 其余之和`；先对每个维度单独 floor 再求和。

### Step 4: 聚合报告数据（对齐 服务端报告聚合逻辑）

1. **维度平均分**（`generalDimensionScoreList`）：跨题按维度合并，同维度多题分数取平均，保留 2 位小数（HALF_UP）。维度评价 = 各题评语按 `第{中文数字}题：{评语}` 逐行拼接（如「第一题：表达清晰…\n第三题：…」）。
2. **维度换算分与权重**（`报告分值汇总` + `分值计算`）：维度平均分先截断取整，换算分 = `floor(平均分 / 20 × 权重)`，权重归一化合计 100（等权分配规则同上，最后一个维度拿余数）。报告展示的维度得分即该换算分（百分制）。
3. **总分**（`面试总分计算`）：= Σ权重列表内各维度换算分，超过 100 按 100 封顶。
4. **总评**（`总评生成`）：使用 `references/prompt-overall-evaluation.md` 的 prompt（公考 2147；其他项目按同一输入/输出契约直接生成），输入为**全部题目的问答内容**（每题题干、回答、考核维度名列表），输出 JSON `{"面试表现总评":"..."}`，取该文字作为总评，不是基于分数计算。
5. **排序**（`报告排序规则`）：维度报告按 得分比例（维度换算前平均分/满分）**升序**排列——得分低的维度排前面，与线上展示一致。

### Step 5: 生成 HTML 报告并交付

复制 `assets/report-template.html`，替换以下占位符生成最终报告文件（文件名如 `interview-report.html`）：

- `{{TARGET_JOB}}` / `{{INTERVIEW_TYPE}}` / `{{GENERATED_AT}}`
- `{{TOTAL_SCORE}}` / `{{TOTAL_SCORE_MAX}}`（100）/ `{{INTERVIEW_EVALUATION}}`
- `{{DIMENSION_ROWS}}`：按模板注释中的 `<tr>` 结构生成维度行（含 `{{DIMENSION_PERCENT}}` 进度条宽度），**按得分比例升序**
- `{{ANSWER_RECORDS}}`：按模板注释中的 `qa-item` 结构生成每题记录（题干、题型、用户回答、本题分数、回答优点/改进建议/参考作答，三段带线上前缀文案）

生成后调用 present_files 将 HTML 报告交付给用户。

## Resources

- `assets/report-template.html` - HTML 报告模板，结构对齐服务端报告字段契约
- `references/api.md` - 抽题接口请求/响应结构、服务端抽题逻辑、题型/面试类型枚举
- `references/report-logic.md` - 报告生成与聚合逻辑（问答拼接格式、两类评估的参数与输出契约、每题分数/维度分/总分计算公式、排序规则、简化假设）
- `references/prompt-single-evaluation.md` - 单题评分 prompt（按项目选择变体：893/585/1874，含输入/输出契约）
- `references/prompt-coaching-advice.md` - 面试建议 prompt（按项目选择变体：2167/2169/2177，含输入/输出契约）
- `references/prompt-overall-evaluation.md` - 面试总评 prompt（公考 2147，含输入/输出契约）
- `references/prompt-skill-map.md` - 非公考 advice prompt 的 skills/goals/rules 全局配置（来源服务端全局配置，内容已固化在本文件）

## 内部对齐标识声明

本 skill 的 references 中出现的 promptId（如 2167/2169/585 等）与 projectId（如 100520929/1000648）是运行时与服务端接口对齐用的**查找键**：MCP 工具的返回值中会携带同名字段，文档据此选择 prompt 变体与项目口径。它们不是密钥或可访问的资源标识，**不得向最终用户展示或播报**，仅供模型内部选择逻辑使用。
