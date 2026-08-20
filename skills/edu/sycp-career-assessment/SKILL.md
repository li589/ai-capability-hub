---
name: sycp-career-assessment
display_name: 生涯测评
display_name_en: Career Path Assessment
description: 当用户提到生涯测评、生涯规划、大学生涯方向、公考/考研/留学/打工人/自由职业/躺平倾向时调用本Skill，用于分析大学生的生涯方向倾向。
description_zh: 生成 10 道题的生涯方向测评，通过 6 选一答题方式分析用户在公考/央国企、自由职业、打工人、留学、保研/考研、躺平六大方向的倾向……
description_en: Use when users mention career path assessment, college student
  life planning, or choices between public servant exam / central state-owned
  enterprises……
category: business-productivity
version: 1.0.0
author: 上海高顿教育科技有限公司
disable-model-invocation: true
---

# 生涯测评 Skill

## Overview

生成生涯测评题目并计算结果，覆盖 6 个生涯方向：

- A：公考/央国企
- B：自由职业
- C：打工人
- D：留学
- E：保研/考研
- F：躺平

本版本为 10 题简版，每题 6 选一（A-F），每个选项归属一个生涯方向标签。
6 个标签均匀分布，共 60 个选项，适合做早期演示、训练和平台上传使用。

## When to Use This Skill

在以下场景触发本 skill：

- 用户明确说出"做生涯测评""测生涯方向""启动生涯规划测评"这类完整指令
- 用户直接询问"我大学适合走哪条路""我适合公考还是考研""帮我测一下我的生涯方向"
- 用户主动提及"打开生涯测评""开始生涯测评"
- 用户说"我想了解自己的生涯方向""帮我做个生涯测试"
- 用户历史对话3轮内明确提过要做生涯测评，当前轮次说"继续""开始吧""下一步"
- 用户直接发送"生涯测评""生涯规划测评"作为唯一指令，无其他无关内容

在以下场景需要二次确认后才触发（命中后先弹出确认话术，用户同意再启动）：
- 用户只单独发送"生涯"两个字，没有后续补充
- 用户讨论某类生涯方向后，说"我好像就是这种人""我感觉我符合这个方向"
- 用户提到"我朋友说适合走公考，想验证一下"，没有直接说要启动测评
- 用户在讨论生涯规划相关话题后，说"帮我测测看"，没有明确指向其他工具

## When NOT to Use This Skill

以下场景**不触发**本 skill：

- 用户仅询问生涯规划科普："大学四年应该怎么规划""公考和考研哪个难"
- 用户仅查询某类方向的介绍："公考需要准备什么""留学申请流程""考研科目"
- 用户讨论生涯规划的非测评应用场景："如何写大学规划书""生涯规划面试技巧"
- 用户在讨论其他完全无关的话题时，偶然提到生涯方向："我室友天天躺平""我朋友考研上岸了"
- 用户明确要求其他类型的测试："我要做MBTI测试""帮我测霍兰德职业兴趣""生成九型人格测试"
- 用户的需求是内容生成类："帮我写一篇大学生活规划小红书文案""生成考研复习短视频脚本"
- 用户同时提出多个混合需求，且没有明确表示要做测评
- 用户明确表示"我不想做测评""我只是想了解大学规划知识"

## 题目元数据

```yaml
assessment_id: SYCP-10-001
assessment_name: "生涯测评（10题简版）"
question_total: 10
tag_count: 6   # A/B/C/D/E/F
tag_list:
  - {tag: A, name: 公考/央国企, priority: 2}
  - {tag: B, name: 自由职业, priority: 5}
  - {tag: C, name: 打工人, priority: 4}
  - {tag: D, name: 留学, priority: 3}
  - {tag: E, name: 保研/考研, priority: 1}
  - {tag: F, name: 躺平, priority: 6}
question_bank_path: "sycp-career-assessment/references/questions.md"
tag_profiles_path: "sycp-career-assessment/references/tag_profiles.md"
algorithm_path: "sycp-career-assessment/references/algorithm.md"
score_calculation_path: "sycp-career-assessment/scripts/calculate_sycp.py"
score_function: "calculate_scores"
entrypoint: "python sycp-career-assessment/scripts/calculate_sycp.py --answers '{\"1\":\"A\",\"2\":\"B\"}'"
config_source: "需求方提供的 sycpData.json + 6 段固定文案；落盘到 references/tag_profiles.md"
```

## 题目加载硬约束（关键）

1. 本 skill **仅提供 10 题简版**，不在任何场景下询问用户"要做几题"、不提供版本二选一入口。
2. 触发测评后必须直接进入 10 题答题流程，不得插入"选择题目数量"的中间步骤。
3. 题目必须从 `sycp-career-assessment/references/questions.md` 的 `## 题目 N` 小节读取，按 `id` 1→10 原序展示；**禁止模型自行编造或凭印象生成题目**。
4. 题库共 10 题，每题必须包含 `id` / `question` / `prompt` / `options`（每个 option 含 `option` / `content` / `tag`）四要素，渲染时不得遗漏任一字段，尤其不得省略 `options.content`。
5. 若题库读取失败或不足 10 题，必须直接报错说明，不得用"部分题目"凑数、不得用模型自拟题补齐。
6. 一次性展示全部 10 道题，不得分页、不得"先展示前几题"、不得逐题加载。

### 题目数据加载流程

模型在渲染交互卡片前，**必须先读取题库文件**，不得凭训练数据回忆题目：

1. 通过 Read 工具读取 `sycp-career-assessment/references/questions.md`：顶部 `> key: value` 行为元数据（含 `version` / `assessment_id` / `assessment_name` / `total`）；`## 标签说明` 表格列出 6 个方向标签；每个 `## 题目 N` 小节含 `**题干**`、`**提示语**` 与选项表 `| 选项 | 内容 | 标签 |`（表内每行含 `option` / `content` / `tag`）。
2. 按数组顺序（id 1→10）渲染全部 10 题，不得打乱、不得省略、不得改写题干/提示语/选项文本/标签归属。
3. 若 Read 工具调用失败、`questions.md` 不存在、题库结构缺失（元数据 `total` 不足 10、`## 题目 N` 小节不足 10 个、任一题目缺 `**题干**` / `**提示语**` / 选项表、或任一选项行缺 `option` / `content` / `tag` 列），模型**必须**向用户返回明确的错误提示（如"题库文件读取失败，请检查 sycp-career-assessment/references/questions.md 是否存在且包含 10 道完整题目（每题含题干/提示语/选项表，每个选项含 option/content/tag）"），**不得**：
    - 用模型自拟/凭印象/从训练数据回忆的题目补齐
    - 用"部分题目"凑数渲染卡片
    - 返回空卡片或不做任何响应
    - 静默跳过题目渲染只输出其他元素（标题、进度条、标签图例等）
    - **把题目/模板写到学员电脑 HTML 文件（`.html`）或任何文件让学员去打开作答**——题库加载失败时唯一正确的行为是向用户报错并停止，绝不允许用"生成 html 文件到学员电脑"来绕过渲染
4. 读题库成功但 show_widget 渲染失败/不可用时，同样**禁止**生成 HTML 文件到学员电脑兜底，直接向用户报错说明渲染失败。

## 工作流程

1. 判断用户是否需要"开始测评"或"已有答案直接算分"。
2. 如为新测评：先 Read `references/questions.md` 加载题库 → **用 show_widget 将 §5.1 模板（10 题全量内联卡片）渲染到当前对话流**，收集作答（每题 A/B/C/D/E/F 之一）。**禁止**把题目或卡片写到学员电脑 `.html` 文件让学员打开作答。
3. 对答案进行校验，确保题目编号、答案类型、标签映射正确。
4. 调用评分脚本计算 6 个标签计数 + 胜出标签 + display_score。
5. 返回用户报告：胜出生涯方向 + 各标签计数/百分比 + 4 段文案。

## WorkBuddy 视觉化交互卡片约束（关键）

本 skill 在 Workbody / WorkBuddy 场景下，不仅需要返回结构化 JSON，也必须支持可视化内联交互卡片：即在对话中直接渲染一个 HTML/CSS/JS 组件，模拟真实测评页面。

### 1. 渲染目标

当用户触发"开始测评"或"生涯测评"时，必须返回一个可渲染的内联卡片，而不是纯文本说明。

**渲染通道唯一化（关键，禁止生成 HTML 文件到学员电脑）**：测评卡片**只能**通过 WorkBuddy 的 show_widget（Visualizer）工具以内联 HTML 片段（`<style>` + `<div>` + `<script>`）形式渲染到**当前对话流中**。**绝对禁止**以下行为：
- 禁止用 Write / Bash 等任何方式把测评 HTML 写入学员电脑磁盘（生成 `.html` 文件、保存到任意目录）
- 禁止引导学员"打开学员电脑上的 html 文件作答""下载/保存测评文件后浏览器打开"等
- 禁止在题库读取失败、show_widget 渲染失败或任何异常场景下，退化为"生成 html 文件到学员电脑让学员作答"
- 禁止把 §5 模板整体输出为 Markdown 代码块让用户复制

唯一合法渲染路径：模型先 Read 题库 → 用 show_widget 输出 §5.1 模板（10 题全量内联卡片）到对话流。若 show_widget 不可用或渲染失败，**必须**向用户明确报错说明"测评卡片渲染失败"，不得改用写文件到学员电脑的方式兜底。

该内联卡片必须包含：

- 顶部标题：`生涯测评`
- 二级说明：`共 10 题，请根据真实想法选择 A/B/C/D/E/F 中的一个`
- 顶部进度条：显示已答题数/总题数，例如 `3 / 10`
- 题目列表：每一题显示编号 + 题干 + 提示语（prompt）
- 每道题的答题区域：6 个单选按钮，分别对应 A-F
    - 选项按钮文本必须显示选项内容（content），而不是仅显示字母
- 当前题目高亮：当前题对应的题目区域、标签和按钮状态应明显区分
- 底部交互：**始终提供可点击的"提交"入口**（无论是否已答完，均不置灰、不隐藏）
- 允许用户在同一对话流中直接答题，不需要跳转到其他页面

### 2. 视觉结构要求

- 整体是一个白色/浅灰背景的卡片容器，边框柔和、圆角适中
- 标题采用大字号、黑色/深灰字体
- 子标题采用中等字号、灰色字体，位置在标题下方
- 顶部右侧显示进度文本，如 `3 / 10`
- 进度条位于标题区下方，长度为卡片宽度的主内容区域
- 题目行高统一，题干左对齐，选项按钮右对齐
- 6 个选项按钮是单选互斥，选中态必须使用如下固定色值：
    - 未选中：浅灰底 `background: #F5F6F8`，边框 `1px solid #E5E7EB`，字色 `#3A3F47`
    - 已选中：淡蓝底 `background: #E8F1FF`，边框 `1px solid #4E8CFF`，字色 `#1E4FB8`，并可加左侧细色条 `box-shadow: inset 3px 0 0 #4E8CFF`
    - 同一题 6 个按钮互斥：选中一个时其余必须退回浅灰底，禁止两端同时高亮
    - 已选中按钮必须有可感知的视觉差异，用户一眼能看出选的是哪一个
    - 上述色值由 §5.1 模板顶部 `<style>` 块的 `.option-btn` / `.option-btn.selected` 规则注入，不在 HTML 写 inline style
- 题目行之间用浅边框分隔
- 在页面底部可以显示辅助说明，例如 `今天帮你做些什么？@引用对话文件 / 调用技能与指令`
- 10 道题必须按完整列表展示，不得分段或混排

### 3. 交互约束

- 一次性展示全部 10 道题，不能分页、不能逐题加载、不能"先展示前几题再继续"
- 题目须按题库原顺序从 1 到 10 连续展示，不得打乱顺序
- 每题必须只有一个有效答案：`A` / `B` / `C` / `D` / `E` / `F`
- 用户点击任一选项时，必须只切换当前题在该题目的选中状态，不应同时多选
- 当前题号必须和题目编号一一对应，且每道题都有明确的题目编号
- 进度条长度和文本必须依据已答题/总题数自动更新，但整个评测仍然保持 10 题全量展示
- **提交按钮始终可见且始终可点击（关键）**：`提交` 按钮必须在卡片渲染的同一帧就出现在卡片最下方 `card-footer` 内，**不得加 `disabled` 属性、不得置灰、不得隐藏**，无论已答几题均可点击。按钮的可见性与可点击性只依赖"测评卡片已渲染"这一条件，不依赖答题进度。
- 点击"提交"按钮时（无论已答几题，按钮都可点击），前端必须按以下契约执行（**禁止退化为"在提交下方显示作答答案列表"或"展示答案串让用户复制回对话"等非评分行为**）：
    1. **收集作答**：扫描 10 个 `question-row`，对每个 `data-qid` 取其内部 `.option-btn.selected` 的 `data-tag`，组装成 `answers` JSON 对象，键为 qid 字符串（"1".."10"）、值为对应 `data-tag`（"A".."F"）
    2. **校验完整性**：若 `answers` 键数 < 10 或任一题未选中，**不**进入评分，按 §3 未答跳转规则自动滚动聚焦到第一个未答题（按 qid 1→10 顺序扫描，命中第一道无 selected 的题即为目标），目标题行加可感知高亮态（背景色变化或外边框加色）；**不**弹窗、**不**报错、**不**在下方显示作答答案、**不**显示"答案串让用户复制回对话"
    3. **触发评分（前端 JS 嵌入算法，关键）**：10 题全选后，前端**不**调用 Python 脚本（避免跨进程依赖），由模板底部内嵌 `<script>` 直接执行嵌入算法。算法与 `scripts/calculate_sycp.py` 的 `calculate_scores` 一一对应：
        - 嵌入数据：`<script>` 顶部固定嵌入 3 个常量对象：`OPTION_TO_TAG`（10 题选项→标签映射，源自 `references/questions.md`）、`TAG_PROFILES`（6 标签档案字典，源自 `references/tag_profiles.md`，含 4 段 section 文案）、`PRIORITY`（平局优先级 `{E:1, A:2, D:3, C:4, B:5, F:6}`，与脚本 `PRIORITY` 表逐字节一致）；常量 `TOTAL=10`
        - **计数**：遍历 qid 1..10，用 `OPTION_TO_TAG[qid][ans]` 查 ans 对应的 tag，对应 tag 计数 +1
        - **胜出**：`max_count = max(counts[A..F])`；`candidates = [t for t in [A..F] if counts[t]==max_count]`；`dominant = min(candidates, key=PRIORITY)`
        - **display_score**：`round(dominant_count*100/TOTAL)`（ROUND_HALF_UP）
        - **查表**：`TAG_PROFILES[dominant]` 取 4 段 section + 4 段 title（与 `tag_profiles.md` 原文字符串完全一致，含 `\n`）
    4. **渲染结果卡片**：前端按 §5.2 结果卡片模板（与 §5.1 顶部 `<style>` 块共用）渲染完整结果卡片，**写入** `.sycp-assessment-card .answers-output` 区域（在答题卡片下方追加结果卡片，不是替换）。占位符从嵌入算法计算结果取值：`dominant_name` ← `TAG_PROFILES[dominant].name`、`display_score` ← `Math.round(dominant_count*100/TOTAL)`、`analysis_summary` ← 固定中文模板 `"用户在 10 道题中，{dominant_name} 方向选了 {counts[dominant]} 次（最多），生涯测评结果为：{dominant_name}。"`、`section_X_title` / `section_X` ← `TAG_PROFILES[dominant]["section_X_title"]` / `TAG_PROFILES[dominant]["section_X"]`（**原样输出生产原文**，含 `\n` 换行，由 `.section-body` 的 `white-space:pre-wrap` 规则渲染换行）。**结果卡片顶部不渲染大字母（`dominant-letter`）、不渲染「各方向得分」6 行 `stat-row`**，报告结构为：`result-header`（`h2` 方向名 + `score-display` + `summary`）→ `tag-detail`（4 段 section）→ `footer-hint`。
    5. **进度条更新**：提交成功后，进度条 `.progress-bar-inner` 的 width 设为 `100%`、`.progress-text` 文本设为 `10 / 10`
    6. **滚动聚焦**：结果写入 `.answers-output` 后，立即 `scrollIntoView({behavior:'smooth',block:'start'})` 滚动聚焦到结果卡片顶部（必须用 try/catch 包裹 `scrollIntoView` 调用，避免沙箱不支持抛错）
    - 滚动聚焦行为不得跳过中间未答题、不得停留在已答题上；始终定位"第一个"未答题
- 进度条长度和文本必须依据已答题/总题数自动更新，但整个评测仍然保持 10 题全量展示
- 交互必须发生在当前对话流的内联组件中，而不是返回普通纯文本

### 4. HTML / Visualizer 输出要求

**测评卡片的唯一渲染通道是 show_widget 工具的内联渲染**（将 §5.1 模板作为 HTML 片段交给 show_widget 渲染进当前对话流）。返回内容必须满足：

- 必须以 show_widget 内联 HTML 片段形式输出（`<style>` 块 + 答题卡片 DOM + 内嵌 `<script>`），而不是纯 Markdown、纯文本说明、JSON
- **绝对禁止把 HTML 写到学员电脑**：不得调用 Write/Bash 生成 `.html` 文件、不得把文件路径发给学员、不得让学员"打开学员电脑上的文件作答"、不得以"保存为网页"方式兜底
- 必须保留视觉层结构：标题、进度、题目列表、6 选按钮
- 不能出现散乱的自然语言说明替代卡片
- 不能直接输出仅有 JSON 字段而没有交互容器
- 不能让前端自行"自由发挥"生成不同布局
- 只允许按本 skill 规定的结构渲染，不允许引入无关内容
- 若 show_widget 渲染失败或不可用：重试一次；仍失败则**直接向用户报错**（"测评卡片渲染失败，请重试"），**不得**退化为生成 HTML 文件到学员电脑让学员自行打开作答

### 5. 固定渲染模板（关键：byte-stable）

为保证不同用户每次触发本 skill 看到的样式一致，答题卡片与结果卡片**必须严格按下述固定 HTML 模板 + 内联样式输出**，模型不得自行设计布局、不得改写 class、不得调整色值/字号/间距/圆角，**只能**对模板中标记为 `{...}` 的占位符做数据替换。模板字段对齐 `references/questions.md` 与评分脚本返回 JSON。

#### 5.1 答题卡片模板（10 题全量展示）

> 占位符：`{qid}` 题号 1-10、`{question}` 题干、`{prompt}` 提示语、`{optX}` 与 `{contentX}` 分别为该题 6 个选项字母与内容文本（X = A/B/C/D/E/F）。
> 模型必须为 10 道题**逐题**渲染完整的 `question-row`，禁止省略、禁止用占位省略号（如 `A. 办公室/秘书部...`）替代真实 content。

```html
<style>
    /* === 答题卡片静态样式 === */
    .sycp-assessment-card{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:24px;max-width:720px;margin:0 auto;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:#3A3F47;}
    .sycp-assessment-card h2{font-size:22px;font-weight:600;color:#1A1D24;margin:0 0 8px 0;}
    .sycp-assessment-card .subtitle{font-size:14px;color:#6B7280;margin:0 0 16px 0;}
    .sycp-assessment-card .progress-row{display:flex;align-items:center;gap:12px;margin:0 0 20px 0;}
    .sycp-assessment-card .progress-bar{flex:1;height:8px;background:#F5F6F8;border-radius:4px;position:relative;overflow:hidden;}
    .sycp-assessment-card .progress-bar-inner{height:100%;width:0;background:#4E8CFF;border-radius:4px;transition:width 0.2s;}
    .sycp-assessment-card .progress-text{font-size:13px;color:#6B7280;min-width:48px;text-align:right;}
    .sycp-assessment-card .question-row{padding:16px 0;border-top:1px solid #F0F1F3;}
    .sycp-assessment-card .question-row:first-of-type{border-top:none;}
    .sycp-assessment-card .question-header{display:flex;align-items:baseline;gap:8px;margin-bottom:4px;}
    .sycp-assessment-card .question-number{font-size:14px;font-weight:600;color:#4E8CFF;flex-shrink:0;}
    .sycp-assessment-card .question-text{font-size:15px;color:#1A1D24;font-weight:500;line-height:1.5;flex:1;}
    .sycp-assessment-card .question-prompt{font-size:13px;color:#9CA3AF;line-height:1.4;margin-bottom:12px;}
    .sycp-assessment-card .answer-options{display:grid;grid-template-columns:1fr;gap:8px;}
    .sycp-assessment-card .card-footer{text-align:center;margin-top:20px;}
    .sycp-assessment-card .answers-output{margin-top:16px;}
    .sycp-assessment-card .footer-hint{margin-top:16px;font-size:12px;color:#9CA3AF;text-align:center;}
    .sycp-assessment-card .incomplete-tip{padding:14px;background:#FFF5EB;border:1px solid #F0D5A3;border-radius:8px;font-size:13px;color:#3A3F47;line-height:1.6;text-align:left;}

    /* === 结果卡片静态样式 === */
    .sycp-result-card{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:24px;max-width:720px;margin:0 auto;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:#3A3F47;}
    .sycp-result-card .result-header{text-align:center;padding-bottom:20px;border-bottom:1px solid #F0F1F3;margin-bottom:20px;}
    .sycp-result-card .result-header h2{font-size:24px;font-weight:600;color:#1A1D24;margin:0 0 8px 0;}
    .sycp-result-card .score-display{font-size:28px;font-weight:600;color:#1A1D24;margin-bottom:8px;}
    .sycp-result-card .score-display .score-max{font-size:16px;color:#9CA3AF;font-weight:400;}
    .sycp-result-card .summary{font-size:14px;color:#6B7280;line-height:1.5;}
    .sycp-result-card .tag-detail .section{margin-bottom:20px;}
    .sycp-result-card .section-title{font-size:15px;font-weight:600;color:#1A1D24;margin-bottom:8px;padding-left:10px;border-left:3px solid #4E8CFF;}
    .sycp-result-card .section-body{font-size:14px;color:#3A3F47;line-height:1.7;white-space:pre-wrap;}
    .sycp-result-card .footer-hint{margin-top:20px;font-size:12px;color:#9CA3AF;text-align:center;border-top:1px solid #F0F1F3;padding-top:16px;}
</style>
<div class="sycp-assessment-card assessment-card">
    <h2>生涯测评</h2>
    <div class="subtitle">共 10 题，请根据真实想法选择 A/B/C/D/E/F 中的一个</div>
    <div class="progress-row">
        <div class="progress-bar"><div class="progress-bar-inner"></div></div>
        <span class="progress-text">0 / 10</span>
    </div>
    <!-- ↓ 以下 question-row 必须为 10 道题逐题重复输出，不得省略、不得用省略号替代 content -->
    <div class="question-row" data-qid="{qid}">
        <div class="question-header">
            <div class="question-number">{qid}</div>
            <div class="question-text">{question}</div>
        </div>
        <div class="question-prompt">{prompt}</div>
        <div class="answer-options">
            <button class="option-btn" data-tag="A" style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;">A. {contentA}</button>
            <button class="option-btn" data-tag="B" style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;">B. {contentB}</button>
            <button class="option-btn" data-tag="C" style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;">C. {contentC}</button>
            <button class="option-btn" data-tag="D" style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;">D. {contentD}</button>
            <button class="option-btn" data-tag="E" style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;">E. {contentE}</button>
            <button class="option-btn" data-tag="F" style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;">F. {contentF}</button>
        </div>
    </div>
    <!-- ↑ 重复 10 次：qid=1..10，每次从 questions.md 取对应题 -->
    <div class="card-footer">
        <button class="submit-btn" style="padding:10px 32px;background:#4E8CFF;border:1px solid #4E8CFF;border-radius:8px;color:#FFFFFF;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;outline:none;transition:background 0.15s,border-color 0.15s;">提交</button>
    </div>
    <div class="answers-output"></div>
    <div class="footer-hint">今天帮你做些什么？@引用对话文件 / 调用技能与指令</div>
</div>
<script>
    (function(){
        try{
            /* === 嵌入数据：6 个标签档案（与 references/tag_profiles.md 一一对应，禁止改写） === */
            var TAG_PROFILES={
                "A":{"name":"公考/央国企","section_1_title":"天选公考/央国企圣体","section_1":"【天选公考/央国企圣体】\n生来就是为了报效祖国！未来国家建设的中坚力量非你莫属！\n","section_2_title":"大学四年规划","section_2":"公考/央国企人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n身份：入党；竞选学生会/社团主席\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩","section_3_title":"备考路径","section_3":"备考：\n大一--了解公考/央国企的报考要求及考试内容\n大二--明确公考/央国企入职路径与目标\n大三--复习申论、行测、公基等考试内容\n大四--参加公考/央国企笔试、面试，成功上岸","section_4_title":"寄语","section_4":"志当存高远，慎始而敢行！"},
                "B":{"name":"自由职业","section_1_title":"独步天下的自由职业者","section_1":"【独步天下的自由职业者】\n生性自由的你，做自己的老板吧！","section_2_title":"大学四年规划","section_2":"自由职业者的大学四年规划：\n绩点：大学四年不挂科\n技能：通过英语四六级、国家计算机二级考试\n提升：学习商科证书，如ACCA、CFA，提升商业思维、经营意识\n论文：写完毕业论文并通过答辩","section_3_title":"实践路径","section_3":"实践：\n大一--探索个人兴趣与能力优势，参加兼职、实习\n大二--思考兴趣/能力变现方式，尝试变现\n大三--了解国家及学校创业政策，申请创业启动资金\n大四--成立工作室，拓展业务，美美做老板","section_4_title":"寄语","section_4":"真正的自由，不是随心所欲，而是自我主宰！"},
                "C":{"name":"打工人","section_1_title":"天选打工人","section_1":"【天选打工人】\n成为CEO走向人生巅峰不是梦！","section_2_title":"大学四年规划","section_2":"打工人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级考试、国家计算机二级考试\n证书：考取ACCA、CFA、CPA等专业证书\n身份：竞选学生会/社团主席\n背提：参加专业相关或名企商赛\n论文：写完毕业论文并通过答辩","section_3_title":"实习路径","section_3":"实习：\n大一--明确职业规划\n大二--参加目标岗位寒暑假实习\n大三--参加名企目标岗位实习\n大四--提升求职技巧，参加校招，收获offer","section_4_title":"寄语","section_4":"打工人，打工魂，打工人都是人上人！！"},
                "D":{"name":"留学","section_1_title":"留学届的翘楚","section_1":"【留学届的翘楚】\n你的目标是星辰大海，跨越重洋你会看到更广阔的天地！","section_2_title":"大学四年规划","section_2":"留学人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n外语：考雅思/托福，达到梦想院校申请标准\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩","section_3_title":"申请路径","section_3":"申请：\n大一--收集留学信息，了解不同国家/院校要求、费用\n大二--明确留学国家/院校/专业目标\n大三--准备留学申请材料，依据要求考GRE/GMAT\n大四--提交留学申请；拿到梦校offer，完成签证准备","section_4_title":"寄语","section_4":"放眼望乾坤，身行万里半天下；探手取知识，必成一大家!"},
                "E":{"name":"保研/考研","section_1_title":"保研考研大赢家","section_1":"【保研考研大赢家】\n学术大咖！不读研读博你都亏了","section_2_title":"大学四年规划","section_2":"保研/考研人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n科研：参加学科竞赛、科研项目，争取获奖、发表论文\n论文：写完毕业论文并通过答辩","section_3_title":"备考路径","section_3":"备考：\n大一--收集考研信息，了解保研考研政策\n大二--明确目标院校/专业，了解招生简章与考核内容\n大三--保研人准备保研材料；考研人系统复习各科知识点\n大四--保研人申请保研资格；考研人参加初试复试，摘取胜利果实","section_4_title":"寄语","section_4":"登峰造极的成就源于自律，保研/考研人，加油！！！"},
                "F":{"name":"躺平","section_1_title":"躺平族代言人","section_1":"【躺平族代言人】\n躺平也是一种人生态度，我还能再躺几年！","section_2_title":"毕业任务","section_2":"想要大学顺利毕业，躺平族也要完成一些任务哦：\n绩点：不挂科，60分万岁\n学分：按时参加必修与辅修课，修满毕业所需学分\n技能：通过英语四六级、国家计算机二级考试\n论文：写完毕业论文并通过答辩","section_3_title":"额外任务","section_3":"额外任务：\n\n规划：发现自己的兴趣与使命所在\n升学：了解考研/保研、留学等升学路径，探索升学意向\n就业：了解考公、央国企、校招等就业路径，探索就业意向\n提升：了解证书、科研、实习、兴趣变现，探索提升方向","section_4_title":"寄语","section_4":"躺平其实只是不再向外拼命内卷，而是向内自我探索，给足时间发掘自己热爱的事物。追求美好的生活，没有时间限制，任何时候开始都不晚。"}};

            /* === 嵌入数据：选项→标签 映射（10 题×6 选项，与 references/questions.md 一一对应） === */
            var OPTION_TO_TAG={
                "1":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "2":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "3":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "4":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "5":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "6":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "7":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "8":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "9":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "10":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"}
            };

            /* === 评分常量 === */
            var TAGS=["A","B","C","D","E","F"];
            var PRIORITY={"E":1,"A":2,"D":3,"C":4,"B":5,"F":6};
            var TOTAL=10;

            /* === 工具函数 === */
            function esc(s){ if(s===undefined||s===null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

            /* === 找卡片 === */
            var cards=document.querySelectorAll('.sycp-assessment-card');
            if(!cards.length) return;
            var card=cards[cards.length-1];

            var answers={};
            var rows=card.querySelectorAll('.question-row');
            var barInner=card.querySelector('.progress-bar-inner');
            var barText=card.querySelector('.progress-text');
            var submit=card.querySelector('.submit-btn');
            var out=card.querySelector('.answers-output');

            function refresh(){
                var n=Object.keys(answers).length;
                barText.textContent=n+' / '+TOTAL;
                barInner.style.width=(n/TOTAL*100)+'%';
            }

            /* === 选项点击：互斥切换 + 记录答案 === */
            for(var i=0;i<rows.length;i++){
                (function(row){
                    var qid=row.getAttribute('data-qid');
                    var btns=row.querySelectorAll('.option-btn');
                    for(var j=0;j<btns.length;j++){
                        (function(btn){
                            btn.onclick=function(){
                                for(var k=0;k<btns.length;k++){
                                    var b=btns[k];
                                    b.className=b.className.replace(/\s*selected/g,'');
                                    b.style.background='#F5F6F8';
                                    b.style.borderColor='#E5E7EB';
                                    b.style.color='#3A3F47';
                                    b.style.boxShadow='none';
                                }
                                btn.className=btn.className+' selected';
                                btn.style.background='#E8F1FF';
                                btn.style.borderColor='#4E8CFF';
                                btn.style.color='#1E4FB8';
                                btn.style.boxShadow='inset 3px 0 0 #4E8CFF';
                                answers[qid]=btn.getAttribute('data-tag');
                                if(out) out.innerHTML='';
                                refresh();
                            };
                        })(btns[j]);
                    }
                })(rows[i]);
            }

            /* === 提交：算分 + 渲染结果卡片 === */
            submit.onclick=function(){
                var n=Object.keys(answers).length;
                if(n<TOTAL){
                    var miss=0;
                    for(var i=1;i<=TOTAL;i++){ if(!answers[String(i)]){ miss=i; break; } }
                    var missRow=card.querySelector('.question-row[data-qid="'+miss+'"]');
                    try{ if(missRow && missRow.scrollIntoView) missRow.scrollIntoView({behavior:'smooth',block:'center'}); }catch(e){}
                    out.innerHTML='<div class="incomplete-tip"><b style="color:#E89B3F;">还有 '+(TOTAL-n)+' 题未答（从第 '+miss+' 题起未答），请补完再提交。</b></div>';
                    return;
                }
                /* 1) 统计 6 标签计数 */
                var counts={A:0,B:0,C:0,D:0,E:0,F:0};
                for(var i=1;i<=TOTAL;i++){
                    var qid=String(i);
                    var ans=answers[qid];
                    var m=OPTION_TO_TAG[qid];
                    if(m && m[ans]){ counts[m[ans]]++; }
                }
                /* 2) 找胜出标签：最大计数 + PRIORITY 升序 */
                var maxCount=0;
                for(var k=0;k<TAGS.length;k++){ if(counts[TAGS[k]]>maxCount) maxCount=counts[TAGS[k]]; }
                var candidates=[];
                for(var k=0;k<TAGS.length;k++){ if(counts[TAGS[k]]===maxCount) candidates.push(TAGS[k]); }
                var dominant=null;
                var bestP=999;
                for(var m=0;m<candidates.length;m++){
                    var p=PRIORITY[candidates[m]];
                    if(p<bestP){ bestP=p; dominant=candidates[m]; }
                }
                /* 3) display_score：胜出标签百分比取整 ROUND_HALF_UP */
                var domCount=counts[dominant];
                var ds=Math.round(domCount*100/TOTAL);
                /* 4) 胜出标签名称与固定文案 summary */
                var domName=TAG_PROFILES[dominant].name;
                var summary='用户在 10 道题中，'+domName+' 方向选了 '+domCount+' 次（最多），生涯测评结果为：'+domName+'。';

                /* 5) 拼接 4 段 section */
                var prof=TAG_PROFILES[dominant];
                var sectionsHtml='';
                for(var s=1;s<=4;s++){
                    var tk='section_'+s+'_title';
                    var bk='section_'+s;
                    sectionsHtml+='<div class="section"><div class="section-title">'+esc(prof[tk])+'</div><div class="section-body">'+esc(prof[bk])+'</div></div>';
                }

                /* 6) 拼整张结果卡片 HTML（顶部无大字母、无「各方向得分」区块） */
                var html=
                    '<div class="sycp-result-card">'+
                        '<div class="result-header">'+
                            '<h2>'+esc(domName)+'</h2>'+
                            '<div class="score-display">'+ds+'<span class="score-max"> / 100</span></div>'+
                            '<div class="summary">'+esc(summary)+'</div>'+
                        '</div>'+
                        '<div class="tag-detail">'+sectionsHtml+'</div>'+
                        '<div class="footer-hint">今天帮你做些什么？@引用对话文件 / 调用技能与指令</div>'+
                    '</div>';

                /* 7) 写入 .answers-output 区域 + 进度条满 */
                out.innerHTML=html;
                barText.textContent=TOTAL+' / '+TOTAL;
                barInner.style.width='100%';
                try{ out.scrollIntoView({behavior:'smooth',block:'start'}); }catch(e){}
            };

            refresh();
        }catch(e){}
    })();
</script>
```

> 注：模板顶部**必须包含一个 `<style>` 块**，把**所有静态元素**（答题卡片：`.sycp-assessment-card` / `h2` / `.subtitle` / `.progress-row` / `.progress-bar` / `.progress-bar-inner` / `.progress-text` / `.question-row` / `.question-header` / `.question-number` / `.question-text` / `.question-prompt` / `.answer-options` / `.card-footer` / `.answers-output` / `.footer-hint` / `.incomplete-tip`；结果卡片：`.sycp-result-card` / `.result-header` / `h2` / `.score-display` / `.score-max` / `.summary` / `.section` / `.section-title` / `.section-body` / `.footer-hint`）的 CSS（背景/边框/圆角/padding/字号/字色/布局）写死在 `<style>` 块内，**不依赖平台 Visualizer 注入**。`<style>` 块的 CSS 文本在所有用户、所有触发轮次中必须逐字节一致，禁止为某用户改色值/间距/圆角/字号。`section-body` 的 `white-space:pre-wrap` 已写入 `.section-body` 规则，HTML 里不加 inline style。
>
> **交互元素的样式写在元素 `style` 属性里**，原因：实测 WorkBuddy 平台 Visualizer **不会自动接管** `.option-btn` / `.submit-btn` 的样式或行为；所有交互必须由模板底部内嵌的 `<script>` 块自己实现，因此样式也必须由模型写在元素 inline `style` 上才能保证视觉一致性。HTML 里逐元素输出：`style="width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;"`（option-btn）与 `style="padding:10px 32px;background:#4E8CFF;border:1px solid #4E8CFF;border-radius:8px;color:#FFFFFF;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;outline:none;transition:background 0.15s,border-color 0.15s;"`（submit-btn）。
>
> **所有交互由模板底部内嵌 `<script>` 块实现（关键）**：实测 WorkBuddy 平台 Visualizer 不会接管 `.option-btn` / `.submit-btn` 的 click 事件，也不会自动切换 `.selected` class。因此模板**必须**在 `</div>` 之后包含一段自包含的 `<script>`（用 IIFE + try/catch 包裹，不依赖外部 JS 库），完成以下交互：
> 1. **绝对不要用 `document.currentScript.previousElementSibling`**——在 widget 沙箱里 `currentScript` 可能为 `null`，第一行就抛 TypeError 被 try/catch 吞掉，整个脚本静默失败。改用 `document.querySelectorAll('.sycp-assessment-card')[cards.length-1]` 全局查找卡片容器（取最后一个匹配，防止页面有多个 sycp 卡片时拿到错的）；
> 2. **不要用 `Array.prototype.forEach` / `NodeList.forEach` / `addEventListener` / `classList.add`/`remove`**——部分 widget 沙箱对 ES5+ 方法支持不稳定。改用传统的 `for(var i;i<len;i++)` 循环 + 闭包 IIFE `(function(el){...})(el[i])` 帮每轮保留变量；用 `btn.onclick = function(){...}`（不是 `addEventListener`）绑事件；用 `el.className = el.className.replace(/\s*selected/g,''); el.className = el.className+' selected';` 替代 `classList`；
> 3. **嵌入计算数据**（关键，提交后算分+渲染结果卡片）：`<script>` 顶部必须嵌入 3 个常量对象，所有数据来自 skill 自带的 `references/questions.md` 与 `references/tag_profiles.md`：
     >    - **`TAG_PROFILES`**：6 个标签档案字典 `{A:{name,section_1_title,section_1,...,section_4_title,section_4}, B:..., F:...}`，每个字段值与 `tag_profiles.md` 原文字符串完全一致（含 `\n` 换行，4 段文案不得改写、不得截断、不得自行撰写）。`section_X` 内的换行用 JS 字符串字面量 `\n` 表示，HTML 渲染时由 `.section-body` 的 `white-space:pre-wrap` 还原。
>    - **`OPTION_TO_TAG`**：10 题选项→标签映射 `{qid:{A:tag, B:tag, C:tag, D:tag, E:tag, F:tag}}`。当前 10 题题库每个题 A-F 与 tag 一一对应（A→A,B→B...），但**必须按真实映射写入**——若未来题库改为"题 1 A→B, B→A"等，需同步更新此映射。映射来源：`references/questions.md` 各 `## 题目 N` 小节选项表的 `标签` 列。
>    - **`PRIORITY`**：平局优先级 `{E:1, A:2, D:3, C:4, B:5, F:6}`（数值越小越优先），与 `scripts/calculate_sycp.py` 的 `PRIORITY` 表逐字节一致。
>    - **`TOTAL=10`**：总题数（与题库实际题数一致）。
> 4. 每次答题后把 `answers[qid] = btn.getAttribute('data-tag')` 写入内存，并刷新 `.progress-text` 为 `已答题数 / 10`、给 `.progress-bar-inner` 设 `style.width = (已答/total*100)+'%'`；
> 5. 给 `.submit-btn` 绑 `click`：
     >    - **未答完**（`Object.keys(answers).length < TOTAL`）：在 `.answers-output` 区域显示一个 `.incomplete-tip`（橙色 `#FFF5EB` 底，提示「还有 N 题未答（从第 X 题起未答）」），并用 `scrollIntoView({behavior:'smooth',block:'center'})` 滚动聚焦到第一个未答的 `.question-row`（`scrollIntoView` 必须用 try/catch 包裹，避免沙箱不支持抛错）。**不弹窗、不显示答案串、不退化为其他行为**。
>    - **全答完**：用嵌入的 `OPTION_TO_TAG` 统计 6 标签计数；按 `PRIORITY` 升序取胜出标签；计算 `display_score = round(dominant_count*100/TOTAL)`；从 `TAG_PROFILES[dominant]` 取胜出标签的 4 段文案（含 `\n`）；拼接完整结果卡片 HTML（含 `h2` 方向名 / `score-display` / `summary` / 4 段 `section` / `footer-hint`，**不含顶部大字母、不含「各方向得分」区块**），写入 `.answers-output` 区域；最后把 `.progress-bar-inner` 宽度设为 `100%`、`.progress-text` 文本设为 `10 / 10`、并 `scrollIntoView` 滚动聚焦到结果卡片。
> 6. 进度条初始宽度 0%、文本 `0 / 10`；每次答题后实时刷新；提交后满 100%。`<script>` 文本在所有用户、所有触发轮次中必须逐字节一致（仅含上面 §5.1 列出的 IIFE 逻辑、`TAG_PROFILES` / `OPTION_TO_TAG` / `PRIORITY` 数据嵌入，**不含用户答案、不含时间戳、不含 `Math.random()` 等运行时变量**）。
>
> **进度条动态更新**：用 `.progress-bar-inner` 内部 div 实现（CSS `height:100%; width:0; background:#4E8CFF; transition:width 0.2s;`），`<script>` 在答题时给 `.progress-bar-inner` 设 `style.width`。所有用户的进度条初始态（`0 / 10`、宽度 0%）与更新逻辑必须一致。
>
> **submit-btn 始终可点击、始终可见**，不加 `disabled`；提交按钮的样式由 `<button class="submit-btn" style="...">提交</button>` inline `style` 写死。
>
> **结果卡片不依赖平台 Visualizer 注入**：结果卡片的 DOM 结构、class 名、`<style>` 块 CSS 全部与 §5.2 模板保持一致，由 `<script>` 在渲染时拼接 HTML 写入 `.answers-output`，不依赖平台接管。

#### 5.2 结果卡片模板（提交后展示）

> **结果卡片不再单独渲染**：实际渲染流程中，结果卡片**不是**由模型另起一段输出，而是由 §5.1 模板底部内嵌 `<script>` 在 `submit-btn` 点击时直接拼接 HTML 写入 `.sycp-assessment-card .answers-output` 区域（见 §5.1 注与 §3 提交流程）。本节作为**契约参考**：当模型按 §5.1 渲染答题卡片时，`<script>` 拼接结果卡片 HTML 必须严格遵循本节定义的 DOM 结构、class 名、`<style>` 规则、占位符来源与顺序——保证用户看到的最终结果卡片与"模型另起一段渲染"时的样式逐字节一致。
>
> 占位符全部来自嵌入 `<script>` 的算法计算结果（与 `scripts/calculate_sycp.py` 的 `calculate_scores` 逐字段对齐）：`{dominant_name}`、`{display_score}`、`{section_X_title}` / `{section_X}`（X = 1..4）、`{analysis_summary}`。**结果卡片不再展示顶部大字母（`dominant-letter`）与「各方向得分」6 行 `stat-row`**；禁止模型自行命名占位符、禁止把胜出标签以外的字段塞进结果卡片。
>
> `section_1..section_4` **必须原样取自 `TAG_PROFILES[dominant]`**（即 `references/tag_profiles.md` 的 `section_X` 字段原文字符串），含 `\n` 换行符；模型不得改写、不得截断、不得自行撰写；HTML 拼接时直接 `<div class="section-body">...</div>` 输出，由 `.section-body { white-space:pre-wrap; }` 规则保留换行。

```html
<style>
.sycp-result-card{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:24px;max-width:720px;margin:0 auto;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:#3A3F47;}
.sycp-result-card .result-header{text-align:center;padding-bottom:20px;border-bottom:1px solid #F0F1F3;margin-bottom:20px;}
.sycp-result-card .result-header h2{font-size:24px;font-weight:600;color:#1A1D24;margin:0 0 8px 0;}
.sycp-result-card .score-display{font-size:28px;font-weight:600;color:#1A1D24;margin-bottom:8px;}
.sycp-result-card .score-display .score-max{font-size:16px;color:#9CA3AF;font-weight:400;}
.sycp-result-card .summary{font-size:14px;color:#6B7280;line-height:1.5;}
.sycp-result-card .tag-detail .section{margin-bottom:20px;}
.sycp-result-card .section-title{font-size:15px;font-weight:600;color:#1A1D24;margin-bottom:8px;padding-left:10px;border-left:3px solid #4E8CFF;}
.sycp-result-card .section-body{font-size:14px;color:#3A3F47;line-height:1.7;white-space:pre-wrap;}
.sycp-result-card .footer-hint{margin-top:20px;font-size:12px;color:#9CA3AF;text-align:center;border-top:1px solid #F0F1F3;padding-top:16px;}
</style>
<div class="sycp-result-card">
  <div class="result-header">
    <h2>{dominant_name}</h2>
    <div class="score-display">{display_score}<span class="score-max"> / 100</span></div>
    <div class="summary">{analysis_summary}</div>
  </div>
  <div class="tag-detail">
    <div class="section">
      <div class="section-title">{section_1_title}</div>
      <div class="section-body">{section_1}</div>
    </div>
    <div class="section">
      <div class="section-title">{section_2_title}</div>
      <div class="section-body">{section_2}</div>
    </div>
    <div class="section">
      <div class="section-title">{section_3_title}</div>
      <div class="section-body">{section_3}</div>
    </div>
    <div class="section">
      <div class="section-title">{section_4_title}</div>
      <div class="section-body">{section_4}</div>
    </div>
  </div>
  <div class="footer-hint">今天帮你做些什么？@引用对话文件 / 调用技能与指令</div>
</div>
```

> 注：模板顶部**必须包含 `<style>` 块**，把结果卡片**静态元素**（`.sycp-result-card` / `.result-header` / `h2` / `.score-display` / `.score-max` / `.summary` / `.section` / `.section-title` / `.section-body` / `.footer-hint`）的 CSS（背景/边框/圆角/padding/字号/字色/布局）写死在 `<style>` 块内，不依赖平台 Visualizer 注入，确保所有用户/所有前端环境看到的静态布局样式逐字节一致。`<style>` 块的 CSS 文本在所有用户、所有触发轮次中必须逐字节一致，禁止为某用户改色值/间距/圆角。`section-body` 的 `white-space:pre-wrap` 已写入 `.section-body` 规则，HTML 里不加 inline style。
>
> **结果卡片不再展示「各方向得分」区块**：结果卡片顶部**不渲染**大字母（`.dominant-letter`），也不再渲染「各方向得分」标题与 6 行 `stat-row`；报告结构固定为：`result-header`（`h2` 方向名 + `score-display` + `summary`）→ `tag-detail`（4 段 section，按 1→2→3→4）→ `footer-hint`。`tag_stats` 数据仍由评分脚本在 JSON 输出中提供（契约不变），仅前端结果卡片不再展示。

#### 5.3 模板稳定性硬约束

- 模型只能替换 `{...}` 占位符，**不得**增删 DOM 节点、改写 class 名
- **`<style>` 块写死全部静态元素 CSS（关键）**：答题卡片的 HTML 顶部**必须包含一个 `<style>` 块**，把**所有静态元素**（答题卡片：`.sycp-assessment-card` / `h2` / `.subtitle` / `.progress-row` / `.progress-bar` / `.progress-bar-inner` / `.progress-text` / `.question-row` / `.question-header` / `.question-number` / `.question-text` / `.question-prompt` / `.answer-options` / `.card-footer` / `.answers-output` / `.footer-hint` / `.incomplete-tip`；结果卡片：`.sycp-result-card` / `.result-header` / `h2` / `.score-display` / `.score-max` / `.summary` / `.section` / `.section-title` / `.section-body` / `.footer-hint`）的 CSS（背景/边框/圆角/padding/字号/字色/布局）写死在同一个 `<style>` 块内，**不依赖平台 Visualizer 注入**，确保所有用户/所有前端环境看到的静态布局样式逐字节一致。`<style>` 块的 CSS 文本在所有用户、所有触发轮次中必须逐字节一致，禁止为某用户改色值/间距/圆角/字号。注意：**结果卡片不单独渲染**（不再起一段独立 HTML），其 `<style>` 规则与答题卡片共用 §5.1 顶部那个 `<style>` 块
- **交互元素的样式写在元素 inline `style` 属性里**：原因：实测 WorkBuddy 平台 Visualizer **不会自动接管** `.option-btn` / `.submit-btn` 的样式与 click 行为，所有交互由模板底部内嵌的 `<script>` 自己实现，因此样式也由模型写在 inline `style` 上，避免依赖平台注入。HTML 里写 `<button class="option-btn" data-tag="X" style="...">X. {contentX}</button>` / `<button class="submit-btn" style="...">提交</button>`。结果卡片不再渲染「各方向得分」`stat-row`，因此**不存在胜出行高亮**；`<style>` 块不写任何 `.option-btn` / `.option-btn:hover` / `.option-btn.selected` / `.submit-btn` / `.submit-btn:hover` / `.stat-row.selected` / `.stat-row.selected .stat-letter` 规则
- **模板底部必须包含自包含 `<script>` 块（关键）**：实测平台 Visualizer 不会接管 `.option-btn` / `.submit-btn` 的 click，也不会自动加 `.selected` class——所以模板**必须**在 `</div>` 之后嵌入一段 IIFE 包裹 + try/catch 兜底的 `<script>`，实现：
    - **选项点击**：option-btn 点击切换 `.selected` class + inline style、记录 answers、刷新进度条
    - **进度条更新**：每次答题时给 `.progress-bar-inner` 设 `style.width = (已答/total*100)+'%'`、`.progress-text` 文本同步刷新
    - **提交评分**：submit-btn 点击时校验完整性（未答完则在 `.answers-output` 显示 `.incomplete-tip` 并滚动聚焦第一个未答；全答完则用嵌入数据 `OPTION_TO_TAG` + `TAG_PROFILES` + `PRIORITY` 计算胜出标签与 display_score，原样拼接 §5.2 结果卡片 HTML 写入 `.answers-output`，含 `result-header`（h2 方向名 / score-display / summary，**无 dominant-letter**）+ 4 段 `section`（`section-body` 用 `white-space:pre-wrap` 还原 `\n` 换行）+ `footer-hint`，**不含「各方向得分」stat-row**），再把进度条设满并 `scrollIntoView` 聚焦到结果
    - **算法一致性**：`<script>` 内的计算逻辑必须与 `scripts/calculate_sycp.py` 的 `calculate_scores` 函数逐字段对齐——计数方式、胜出规则（`PRIORITY` 升序）、`display_score` ROUND_HALF_UP 取整、4 段 section 文本原样查表（`TAG_PROFILES[dominant].section_X`）
    - **嵌入数据来源**：`<script>` 顶部的 `TAG_PROFILES` / `OPTION_TO_TAG` / `PRIORITY` 必须与 `references/tag_profiles.md` / `references/questions.md` / `scripts/calculate_sycp.py` 的 `PRIORITY` 表**逐字节一致**；`TAG_PROFILES.section_X` 含 `\n` 换行，HTML 渲染时由 `.section-body { white-space:pre-wrap; }` 还原
- `<script>` 文本在所有用户、所有触发轮次中必须逐字节一致（仅含 IIFE 逻辑 + 3 个嵌入常量，不含用户答案、时间戳、`Math.random()` 等任何运行时变量）。脚本**不得**引入外部 JS 依赖（jQuery 等），不得在 script 内修改卡片以外的 DOM
- **初始态禁止预选**：模型在初始 HTML 中**不得**给任何 `option-btn` 加 `selected` class 或内联 `selected` 态 inline style（背景 `#E8F1FF` 等），不论哪个用户触发、不论该用户是否曾作答过。选中态只能由 `<script>` 在用户点击时动态切换，不由模型在初始 HTML 写死。这一约束保证"所有用户首次触发看到的初始答题卡片 byte-equal"
- 未选中态色值（`#F5F6F8` 底 / `#E5E7EB` 边框 / `#3A3F47` 字色）由模型在每个 `<button class="option-btn">` 的 inline `style` 属性里写死；选中态色值（`#E8F1FF` 底 / `#4E8CFF` 边框 / `#1E4FB8` 字色 / `inset 3px 0 0 #4E8CFF`）由模板内嵌 `<script>` 在用户点击时切换 inline style。**所有用户色值相同**，禁止为不同用户使用不同色值
- 占位符替换后必须输出合法 HTML，禁止残留未替换的 `{xxx}` 字面量
- 答题卡片必须输出完整 10 个 `question-row`，禁止省略、禁止用 `...` 代替 content、禁止只渲染前 N 题
- 结果卡片 4 段 `section` 必须按 1→2→3→4 固定顺序输出，禁止打乱
- 任何额外的标题、说明、装饰元素、emoji、icon 均不得追加
- 输出后整份 HTML 在不同用户、不同会话、不同时间触发下必须结构一致（byte-stable）

#### 5.4 跨用户样式统一约束（关键）

不论哪个用户触发本 skill、不论用户的身份/历史/作答习惯如何、不论触发发生在哪个会话/哪个时间，**所有用户看到的题目样式、选项样式、按钮样式、作答后结果样式四者必须逐字节一致（cross-user byte-stable）**。任何用户的渲染输出不得因用户身份或触发上下文不同而产生结构、class、DOM 层级、占位符顺序、文案来源、色值、顺序的漂移。

**1. 题目样式跨用户统一（`question-row`）**

- 所有用户看到的 10 个 `question-row` 的 DOM 结构、class 名、子节点顺序（`question-number` → `question-text` → `question-prompt` → `answer-options`）必须完全一致
- `question-number` 文本必须为题库 `id` 1→10 原序，所有用户一致；禁止为某个用户改用数组下标 +1、补 `#` 前缀等
- `question-text` / `question-prompt` 必须原样取自 `references/questions.md` 各 `## 题目 N` 小节的 `**题干**` / `**提示语**`，所有用户看到的题干与提示语一字不差；禁止凭印象改写、禁止为某用户省略 prompt
- 题目顺序必须按 `id` 1→10 原序，所有用户一致；禁止按"该用户未答题优先"重排、禁止为某用户打乱
- 题目行之间的分隔、缩进、空格数量所有用户一致

**2. 选项样式跨用户统一（`option-btn`）**

- 所有用户看到的每题 6 个 `option-btn` 的 DOM 结构、`data-tag` 属性（A/B/C/D/E/F）、文本格式（`{字母}. {content}`）必须逐字节一致
- 选项按钮文本必须原样取自 `references/questions.md` 选项表的 `内容` 列，所有用户看到的选项文案一字不差；禁止为某用户截断、用省略号替代、改写
- 6 个选项必须按 A→B→C→D→E→F 固定顺序输出，所有用户一致；禁止为某用户按"上次选中优先"重排
- **初始态禁止预选**：模型在初始 HTML 中**不得**给任何 `option-btn` 加 `selected` class，也不写选中态 inline style（背景 `#E8F1FF` 等），不论哪个用户触发、不论该用户是否曾作答过。选中态只能由模板内嵌 `<script>` 在用户点击时动态切换，不由模型在初始 HTML 写死。这一约束保证"所有用户首次触发看到的初始答题卡片 byte-equal"
- 未选中态色值（`#F5F6F8` 底 / `#E5E7EB` 边框 / `#3A3F47` 字色）由模型在每个 `<button class="option-btn">` 的 inline `style` 属性里写死；选中态色值（`#E8F1FF` 底 / `#4E8CFF` 边框 / `#1E4FB8` 字色 / `inset 3px 0 0 #4E8CFF`）由模板内嵌 `<script>` 在用户点击时切换 inline style。**所有用户色值相同**，禁止为不同用户使用不同色值

**3. 按钮样式跨用户统一（`submit-btn`）**

- 所有用户看到的 `submit-btn` 的 DOM 结构、class 名、文本（`提交`）必须逐字节一致，色值/padding/圆角/字号/font-weight/cursor 由模型在 `<button class="submit-btn" style="...">提交</button>` 的 inline `style` 属性里写死（不依赖平台 Visualizer、不写在 `<style>` 块，避免与平台冲突）
- 提交按钮**始终可点击、始终可见、不加 `disabled`**，所有用户一致
- 禁止为某用户把按钮置灰、隐藏、挪位、改色值
- 按钮位置固定在 `card-footer` 内、卡片最下方，且 `card-footer` 由 `<style>` 块的 `.card-footer` 规则（`text-align:center; margin-top:20px;`）实现提交按钮**居中**，所有用户一致
- 提交按钮点击行为（10 题全答完触发评分；有未答题不弹窗、自动滚动聚焦到第一个未答题）所有用户一致

**4. 作答后结果样式跨用户统一（`sycp-result-card`）**

- 所有用户看到的结果卡片的 DOM 结构、class 名、子节点顺序（`result-header` → `tag-detail` → `footer-hint`）必须逐字节一致
- `dominant_name` / `display_score` / `analysis_summary` 占位符替换必须来自 `<script>` 内嵌算法计算结果（与 `scripts/calculate_sycp.py` 的 `calculate_scores` 逐字段对齐），所有用户一致；禁止为某用户改写或截断
- **结果卡片不渲染顶部大字母（`dominant-letter`）与「各方向得分」6 行 `stat-row`**：报告结构固定为 `result-header`（`h2` 方向名 + `score-display` + `summary`）→ `tag-detail`（4 段 section）→ `footer-hint`，所有用户一致；`tag_stats` 仍由评分脚本在 JSON 输出中提供（契约不变），仅前端结果卡片不再展示
- 4 段 `section` 必须按 1→2→3→4 固定顺序，所有用户一致；`section-body` 文案必须原样取自 `references/tag_profiles.md` 的 `section_1`~`section_4` 生产原文（含 `\n` 换行），所有用户看到的文案一字不差；`section-body` 的 `white-space:pre-wrap` 由 §5.2 模板顶部 `<style>` 块的 `.section-body` 规则注入，HTML 里不加 inline style；禁止为某用户省略、改写、自拟文案
- 同一组 `answers` 不论由哪个用户提交，结果卡片必须 byte-equal

**5. 跨用户样式统一总则**

- 所有用户触发本 skill 看到的答题卡片 DOM 结构、class、文案、顺序、内嵌 `<script>` 文本必须 byte-equal。允许随各用户答题进度变化的字段仅限以下三类：`option-btn` 的 `.selected` class 分布（由内嵌 `<script>` 切换）、`.progress-text` 的文本内容（已答题数/10）、`.progress-bar-inner` 的 `width`（已答题数/10 × 100%）；除此三类外，DOM 骨架、`<style>` 块 CSS、`<script>` 文本本身禁止变化
- 所有用户首次触发看到的初始答题卡片必须是同一份空白卡片：**不得**为某用户预填其历史答案、**不得**为某用户保留其上次选中态、**不得**为某用户改变题目顺序或省略题目
- 同一组 `answers` 由不同用户提交、在不同会话提交、在不同时间提交，结果卡片必须 byte-equal
- 不允许因"该用户已生成过""该用户结果同上""该用户缓存命中"等理由为该用户省略任一 `question-row` / `option-btn` / `section`；每个用户每次渲染都必须完整输出全部 10 题、每题 6 选项、结果 4 段 section
- 不允许为不同用户引入不同色值、不同顺序、不同装饰；色值与顺序必须固定如 §5.1 / §5.2 模板所示，所有用户共用同一套样式

### 6. 禁止事项

- **绝对禁止把测评 HTML 生成到学员电脑（关键）**：不得用 Write / Bash 等方式生成 `.html` 文件、不得把测评模板保存到学员电脑磁盘、不得向学员提供文件路径、不得引导学员"打开学员电脑上的 html 作答"、不得说"我生成了文件给你"；测评卡片**只能**通过 show_widget 内联渲染到当前对话流。题库加载失败或渲染失败时唯一正确行为是向用户报错，**不允许**用写文件方式兜底
- 不允许输出纯文本描述替代卡片
- 不允许缺失 6 选按钮中的任何一个
- 不允许没有进度条和题号
- **不允许点击"提交"后退化为"在下方显示作答答案列表""展示答案串让用户复制回对话"等非评分行为**：10 题全选后提交必须由前端 JS 用嵌入数据 `OPTION_TO_TAG` + `TAG_PROFILES` + `PRIORITY` 计算胜出标签与 display_score，**直接渲染 §5.2 结果卡片 HTML 写入 `.answers-output`**（含 `result-header`（h2 方向名 + score-display + summary）+ 4 段 `section` + `footer-hint`）；有未答题时必须滚动聚焦第一个未答题，不得在下方显示作答答案、不得让用户复制答案回对话
- 不允许在页面中出现无关长文案或随机推理内容
- 不允许模型自行更换布局结构，必须保持 WorkBuddy 交互卡片的稳定格式
- **不允许给静态元素加 inline style**：除交互元素 `.option-btn` / `.submit-btn` 外，其他元素（卡片容器、标题、题目行、进度条、section 等）一律用 `<style>` 块写样式，不得加 inline style，避免跨用户样式漂移

## 输出格式

## 确定性输出约束（关键）

为避免 Workbody 生成结果每次都变化，本 skill 必须执行严格的确定性规则：

1. 结果必须以脚本计算结果为唯一准绳，不允许模型自由推断分数或生涯方向。
2. `tag_counts` 必须按固定顺序输出 6 个标签：`{"A","B","C","D","E","F"}`。
3. `dominant_tag` 必须由评分脚本按"最高计数 + 平局优先级"规则得出，不能由模型自行命名或重写。
4. 平局优先级固定为：保研/考研(E) > 公考/央国企(A) > 留学(D) > 打工人(C) > 自由职业(B) > 躺平(F)。
5. 百分比必须保留两位小数，使用 `decimal.ROUND_HALF_UP`（与 Java `BigDecimal.ROUND_HALF_UP` 一致），不允许 Python 默认 banker's rounding。
6. `display_score` 为胜出标签百分比取整数，使用 `decimal.ROUND_HALF_UP`，不允许模型自由发挥。
7. `tag_detail` 必须从 `references/tag_profiles.md` 按 `dominant_tag` 查表得到，6 个方向全覆盖；**4 段文案必须为生产原文，不允许模型自行撰写或改写身份认同、大学规划、实施路径、寄语**。
8. `analysis.summary` 必须使用固定模板，且只基于 `dominant_name` 与 `counts[dominant_tag]` 生成。
9. `analysis.recommendation` 必须为 `tag_detail.name` 字符串，不允许模型自由发挥。
10. 任何场景都不允许输出随机、模糊、口语化的结论；必须稳定输出统一结构。
11. 如果题目不完整，必须返回 `incomplete`，并列出缺失题号；不得在有缺失时强行生成完整结论。
12. 生成结果时必须以 JSON 对象返回，不能返回 Markdown、自然语言说明、额外说明块或解释性文本。
13. 同一组 `answers` 必须在多次调用间产生 byte-equal 的 JSON 输出（无随机数、无时间戳、无外部网络/DB 依赖）。
14. 报告文案来源单一：需求方提供的 `sycpData.json` + 6 段固定文案；当文案需要变更时，须重新覆盖 `references/tag_profiles.md`，**禁止在覆盖前混入模型自拟内容**。

本 skill 只负责返回结构化的评测结果，不承担前端渲染。输出必须严格符合以下 JSON 结构：

```json
{
  "assessment_id": "SYCP-10-001",
  "assessment_name": "生涯测评（10题简版）",
  "status": "completed",
  "answered_count": 10,
  "total_questions": 10,
  "display_score": 40,
  "max_score": 100,
  "dominant_tag": "A",
  "dominant_name": "公考/央国企",
  "tag_counts": {"A": 4, "B": 1, "C": 2, "D": 1, "E": 1, "F": 1},
  "tag_stats": [
    {"tag": "A", "name": "公考/央国企", "score": 4, "percent": 40.00},
    {"tag": "B", "name": "自由职业", "score": 1, "percent": 10.00},
    {"tag": "C", "name": "打工人", "score": 2, "percent": 20.00},
    {"tag": "D", "name": "留学", "score": 1, "percent": 10.00},
    {"tag": "E", "name": "保研/考研", "score": 1, "percent": 10.00},
    {"tag": "F", "name": "躺平", "score": 1, "percent": 10.00}
  ],
  "tag_detail": {
    "tag": "A",
    "name": "公考/央国企",
    "priority": 2,
    "section_1_title": "天选公考/央国企圣体",
    "section_1": "【天选公考/央国企圣体】\n生来就是为了报效祖国！未来国家建设的中坚力量非你莫属！\n",
    "section_2_title": "大学四年规划",
    "section_2": "公考/央国企人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n身份：入党；竞选学生会/社团主席\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩",
    "section_3_title": "备考路径",
    "section_3": "备考：\n大一--了解公考/央国企的报考要求及考试内容\n大二--明确公考/央国企入职路径与目标\n大三--复习申论、行测、公基等考试内容\n大四--参加公考/央国企笔试、面试，成功上岸",
    "section_4_title": "寄语",
    "section_4": "志当存高远，慎始而敢行！"
  },
  "analysis": {
    "summary": "用户在 10 道题中，公考/央国企 方向选了 4 次（最多），生涯测评结果为：公考/央国企。",
    "recommendation": "公考/央国企"
  }
}
```

> 注：以上 `tag_detail.section_1` ~ `section_4` 全部来自 `references/tag_profiles.md` 的生产原文，模型不得自行撰写、改写或省略。6 个方向的 4 段文案必须按 `tag` 查表原样输出。

### 输出规范

- `status` 必须为 `completed` 或 `incomplete`
- `display_score` 为 0-100 的整数，且必须来自脚本计算结果
- `dominant_tag` 为 A-F 中的一个字母，不能自行更改为其他文本
- `dominant_name` 为胜出标签的中文名，与 `tag_detail.name` 一致
- `tag_counts` 必须按固定顺序输出 `A`、`B`、`C`、`D`、`E`、`F` 六个键
- `tag_stats` 必须按 `A/B/C/D/E/F` 顺序输出 6 条，每条含 `tag/name/score/percent`
- 胜出标签规则：取 `score` 最高的标签；并列时按 `priority` 数值升序取最优先者
- `display_score` = 胜出标签的百分比取整（ROUND_HALF_UP）
- `tag_detail` 必须从 `references/tag_profiles.md` 按 `tag` 查表，包含 `tag/name/priority/section_1_title/section_1/section_2_title/section_2/section_3_title/section_3/section_4_title/section_4` 十一个字段，**全部使用生产原文，不得改写、不得省略、不得由模型自行撰写**
- `analysis.summary` 必须使用固定中文模板：`"用户在 10 道题中，{dominant_name} 方向选了 {counts[dominant_tag]} 次（最多），生涯测评结果为：{dominant_name}。"`
- `analysis.recommendation` 必须为 `tag_detail.name` 字符串，不得截断或改写
- 若题目未完成，则返回 `incomplete`，并输出 `missing_questions`（缺失题号字符串数组）
- 输出必须为纯 JSON，不允许嵌套说明、Markdown 代码块或额外字段

### 渲染约束（关键）

本 skill 约束的是"生成结果的渲染契约"，而不是页面实现细节。具体要求如下：

- `dominant_tag` 必须作为页面主标签字段使用（如 `A`）
- `dominant_name`（中文名如 `公考/央国企`）必须作为页面主标题展示字段使用
- `display_score` 必须作为总分展示字段使用
- `tag_stats` 作为结构化数据在 JSON 输出中保留（评分契约不变），但**结果卡片前端不再渲染「各方向得分」区块**：学员作答后的报告仅展示方向名标题、总分、summary 与 4 段文案
- `tag_detail.section_1` 必须作为身份认同区域展示，使用生产原文（含换行符原样渲染）
- `tag_detail.section_2` 必须作为大学四年规划区域展示，使用生产原文（含换行符原样渲染）
- `tag_detail.section_3` 必须作为分年级实施路径区域展示，使用生产原文（含换行符原样渲染）
- `tag_detail.section_4` 必须作为底部寄语区域展示，使用生产原文
- 结果页必须按 `section_1 → section_2 → section_3 → section_4` 顺序展示 4 段文案，每段标题可用 `section_X_title` 作为小标题
- `analysis.summary` 必须作为结果说明文本展示
- `analysis.recommendation` 必须作为建议方向渲染数据
- 任何前端都不能自行生成新的字段名来替代上述结构
- 前端只能根据这几个字段进行展示，不能依赖自由文本解析
- 报告文案不得由前端或模型自行撰写，必须来自 `references/tag_profiles.md` 的生产原文

### 禁止事项

- 不允许返回自由文本替代 JSON
- 不允许缺少 `tag_stats`
- 不允许缺少 `dominant_tag`
- 不允许 `tag_stats` 中遗漏任一标签
- 不允许 `tag_detail` 缺失任一段文案
- 不允许在 skill 中混合前端渲染逻辑
- 不允许前端自行扩展未定义字段覆盖结果解释
- 不允许使用 Python 默认 `round()`（banker's rounding），必须用 `decimal.ROUND_HALF_UP`
- 不允许模型自行撰写 `tag_detail.section_1/section_2/section_3/section_4`，必须从 `references/tag_profiles.md` 查表
- **不允许脱离 §5 固定模板自行设计答题卡片或结果卡片布局**：必须使用 §5.1 答题模板（含顶部 `<style>` 块、10 道 `question-row`、选项按钮、提交按钮、内嵌 `<script>`）原样输出，**结果卡片 DOM 结构 / class / `<style>` 规则必须与 §5.2 契约参考模板逐字节一致**——`<script>` 拼接结果卡片 HTML 时必须按 §5.2 结构、顺序、占位符来源填充，不允许自行设计其他布局
- 不允许改写模板中的 class 名、DOM 层级；**静态元素（卡片容器/标题/题目行/progress-row/progress-bar/进度文本/section/section-title/section-body/footer-hint 等）一律用模板顶部 `<style>` 块写样式**，不得加 inline style，避免跨用户样式漂移；**交互元素**（`.option-btn` / `.submit-btn`）的样式写在元素 inline `style` 属性里，由模型在 `<button style="...">...</button>` 静态部分写初始样式，不依赖平台 Visualizer 接管
- **不允许省略模板顶部 `<style>` 块**：答题卡片 HTML 顶部必须包含一个 `<style>` 块，把**所有静态元素**（答题卡片 + 结果卡片共用一份 CSS）的 CSS 写死，不依赖平台注入；**结果卡片不再单独渲染**（不起一段独立 HTML），其 CSS 规则与答题卡片共用 §5.1 顶部那个 `<style>` 块
- 不允许在答题卡片中省略任一题的 `question-row`、不允许用 `...` 等省略号替代 `content`
- **结果卡片不再渲染「各方向得分」`stat-row`**：结果卡片顶部不渲染大字母（`dominant-letter`）、不渲染「各方向得分」6 行 `stat-row`；报告结构固定为 `result-header`（h2 方向名 + score-display + summary）→ `tag-detail`（4 段 section）→ `footer-hint`
- 不允许在结果卡片中打乱 `section_1→2→3→4` 顺序
- 不允许追加模板未定义的标题、说明、装饰元素、emoji、icon
- 同一组触发条件、同一份 answers 在不同会话/不同时间触发，输出 HTML 必须 byte-stable
- **不允许因用户身份或触发上下文不同而导致题目/选项/按钮/结果样式漂移**：所有用户渲染的答题卡片 DOM 骨架与 `<style>` 块静态 CSS 文本必须 byte-equal（允许随各用户答题进度变化的字段仅限：`option-btn` 的 `selected` class 分布、`progress-text` 的文本内容、`.progress-bar::after` 的 `width`；DOM 结构/class/文案/顺序/`<style>` 块静态 CSS 禁止变化）；同一组 answers 由不同用户提交，结果卡片必须 byte-equal
- **不允许在初始 HTML 中预选/预填某用户的历史作答**：模型不得给 `option-btn` 预加 `selected` class，不论哪个用户触发、不论该用户是否曾作答过；选中态只能由前端在用户点击时动态加，确保所有用户首次触发看到的初始答题卡片 byte-equal
- **不允许为不同用户使用不同色值、不同顺序、不同装饰**：未选中态/选中态色值由模型写在元素 inline `style` 与 `<script>` 切换的 inline style 里（**不依赖平台注入**，实测平台不会管），所有用户共用同一套色值；`section` 顺序必须固定为 1→2→3→4，所有用户一致
- **不允许以"该用户已生成过""该用户结果同上""该用户缓存命中"为由为该用户省略任一 `question-row` / `option-btn` / `section`**：每个用户每次渲染都必须完整输出全部 10 题、每题 6 选项、结果 4 段 section
- **不允许为新用户/老用户/有历史作答用户/无历史作答用户呈现不同的初始卡片**：所有用户首次触发看到的必须是同一份空白答题卡片，不得预填历史答案、不得保留上次选中态、不得改变题目顺序或省略题目

## 题目结构说明

该评测题目以 6 个生涯方向标签为核心，采用"6 选一强制选项"式答题。

每题的 6 个选项（A-F）分别归属 6 个标签：
- A = 公考/央国企
- B = 自由职业
- C = 打工人
- D = 留学
- E = 保研/考研
- F = 躺平

### 题目示例

```json
{
  "id": 1,
  "question": "开学了！学生会竞选启动！你最想加入的部门是？",
  "prompt": "凭直觉作答，选最接近真实想法的选项。",
  "options": [
    {"option": "A", "content": "办公室/秘书部，文书草拟小达人，综合事务你最行", "tag": "A"},
    {"option": "B", "content": "新媒体部，玩转互联网，捕捉热点创意无限", "tag": "B"},
    {"option": "C", "content": "主席团，领导者风范，学生会的核心力量", "tag": "C"},
    {"option": "D", "content": "外联部，社交达人，连接大学与社会的桥梁", "tag": "D"},
    {"option": "E", "content": "学习部/学术部，学霸集结，心无旁骛搞学习", "tag": "E"},
    {"option": "F", "content": "都没有兴趣，想做个普普通通的大学村平民", "tag": "F"}
  ]
}
```

字段说明：
- `id`：题目编号（1-10）
- `question`：题干文本
- `prompt`：作答提示语，渲染时显示在题干下方
- `options`：6 选一选项数组
    - `option`：选项字母（A-F）
    - `content`：选项内容文本
    - `tag`：该选项归属的生涯方向标签（A/B/C/D/E/F）

## 评分入口

评分脚本位置：

- `sycp-career-assessment/scripts/calculate_sycp.py`
- 评分函数：`calculate_scores(answers, questions, tag_profiles)`
- 输出：JSON 格式的分数与生涯方向结果

示例命令：

```bash
python sycp-career-assessment/scripts/calculate_sycp.py \
  --answers '{"1":"A","2":"B","3":"A","4":"B"}' \
  --questions-path sycp-career-assessment/references/questions.md \
  --tag-profiles-path sycp-career-assessment/references/tag_profiles.md
```

## 评分规则

### 1. 标签计数

每道题的每个选项归属一个标签（A-F）。用户作答归一化为 `A`-`F`，匹配到的选项所对应的 `tag` 字段 +1：

- 答案归一：`1-6` → `A-F`，`A-F` 直通
- 算法：
  ```text
  for q in questions:
      ans = normalize_answer(answers[str(q.id)])  # 'A'-'F' 或 ''
      for opt in q.options:
          if opt.option.upper() == ans:
              counts[opt.tag] += 1
              break
  ```

6 个标签计数之和 = 已作答题数。

### 2. 标签百分比

```text
percent[tag] = score[tag] / total_questions * 100   # 保留两位小数 ROUND_HALF_UP
```

### 3. 胜出标签

```text
max_count = max(score[A..F])
candidates = [t for t in [A,B,C,D,E,F] if score[t] == max_count]
dominant_tag = min(candidates, key=PRIORITY)
```

平局优先级：保研/考研(E=1) > 公考/央国企(A=2) > 留学(D=3) > 打工人(C=4) > 自由职业(B=5) > 躺平(F=6)

### 4. 总分（display_score，0-100）

```text
display_score = round(score[dominant_tag] / total_questions * 100)   # ROUND_HALF_UP 取整
```

例：胜出标签 A 计数 4 → 4/10*100 = 40.00 → `40`

### 5. 角色详情（4 段文案）

依据 `dominant_tag` 在 `references/tag_profiles.md` 中按 `tag` 查表，输出：

- `tag`：生涯标签字母（如 `"A"`）
- `name`：方向中文名（如 `"公考/央国企"`）
- `priority`：平局优先级（1-6）
- `section_1`：身份认同文案（如「【天选公考/央国企圣体】...」）
- `section_2`：大学四年规划文案
- `section_3`：分年级实施路径文案
- `section_4`：寄语文案

6 个方向必须全部覆盖，缺一不可。

## 报告示例

下面是一组真实作答（A=4, B=1, C=2, D=1, E=1, F=1）经评分脚本计算后的报告片段。非数值字段均来自 `references/tag_profiles.md` 的生产原文：

```json
{
  "assessment_id": "SYCP-10-001",
  "status": "completed",
  "answered_count": 10,
  "total_questions": 10,
  "display_score": 40,
  "max_score": 100,
  "dominant_tag": "A",
  "dominant_name": "公考/央国企",
  "tag_counts": {"A": 4, "B": 1, "C": 2, "D": 1, "E": 1, "F": 1},
  "tag_stats": [
    {"tag": "A", "name": "公考/央国企", "score": 4, "percent": 40.00},
    {"tag": "B", "name": "自由职业", "score": 1, "percent": 10.00},
    {"tag": "C", "name": "打工人", "score": 2, "percent": 20.00},
    {"tag": "D", "name": "留学", "score": 1, "percent": 10.00},
    {"tag": "E", "name": "保研/考研", "score": 1, "percent": 10.00},
    {"tag": "F", "name": "躺平", "score": 1, "percent": 10.00}
  ],
  "tag_detail": {
    "tag": "A", "name": "公考/央国企", "priority": 2,
    "section_1": "【天选公考/央国企圣体】\n生来就是为了报效祖国！未来国家建设的中坚力量非你莫属！\n",
    "section_2": "公考/央国企人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n身份：入党；竞选学生会/社团主席\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩",
    "section_3": "备考：\n大一--了解公考/央国企的报考要求及考试内容\n大二--明确公考/央国企入职路径与目标\n大三--复习申论、行测、公基等考试内容\n大四--参加公考/央国企笔试、面试，成功上岸",
    "section_4": "志当存高远，慎始而敢行！"
  },
  "analysis": {
    "summary": "用户在 10 道题中，公考/央国企 方向选了 4 次（最多），生涯测评结果为：公考/央国企。",
    "recommendation": "公考/央国企"
  }
}
```

## 重要原则

- 题库必须明确给出题目编号、题干、提示语和选项标签归属；
- 评分逻辑必须单独写在脚本文件中，不能隐含在对话里；
- 用户提交题目后，必须返回测试结果、得分和生涯方向；
- 若题目缺失或答案格式不合法，先要求用户补全，不要直接伪造结果；
- 选项标签映射必须保持一一对应；
- 同一组作答必须产出 byte-equal 的 JSON（无随机性）。

## Demo 目录结构

```text
sycp-career-assessment/
├── SKILL.md
├── references/
│   ├── algorithm.md
│   ├── questions.md        # 10 题题库（源自 sycpData.json）
│   └── tag_profiles.md   # 6 个生涯方向 × 4 段文案
└── scripts/
    └── calculate_sycp.py
```

## 资源说明

- 题库参考：`references/questions.md`（源自需求方提供的 `sycpData.json`）
- 生涯方向档案：`references/tag_profiles.md`（6 个方向 × 4 段文案，源自需求方固定文案）
- 算法说明：`references/algorithm.md`
- 评分脚本：`scripts/calculate_sycp.py`
- 报告文案单一来源：需求方提供的 6 段固定文案；文案需要变更时，重新覆盖 `references/tag_profiles.md` 即可生效，无需改动评分脚本

## 交互输出要求

用户完成题目后，系统应返回：

1. 测评 ID 与名称
2. 状态（completed / incomplete）
3. 胜出生涯方向（dominant_tag + dominant_name）
4. 6 个方向的计数与百分比
5. 角色详情（tag / name / priority / section_1 / section_2 / section_3 / section_4）
6. 总分（display_score）
7. 若未通过/未完成，给出缺失题号列表

本 skill 仅支持 10 题简版，评分逻辑独立于题库内容；后续如需切换题库，只需替换 `references/questions.md`，无需改动评分脚本。报告文案（`tag_detail.section_1` ~ `section_4`）全部来自 `references/tag_profiles.md`，单一来源为需求方提供的固定文案；文案变更后重新覆盖 `references/tag_profiles.md` 即可，无需改动评分脚本。
