---
name: career-personality
display_name: 职业性格测评
display_name_en: Career Personality Assessment
description: 当用户提到MBTI、职业性格、性格测试或性格特征时调用本Skill，用于分析性格倾向及其在工作环境中的表现。
description_zh: 结合MBTI等性格测评方法，分析用户的性格倾向、沟通方式、行为偏好与工作环境倾向。
description_en: Use when users mention MBTI, career personality, personality tests, or personality traits to analyze tendencies and workplace behaviors.
category: 15-Education
version: 1.0.0
author: 上海高顿教育科技有限公司
---

# MBTI 职业性格测评 Skill

## Overview

生成 MBTI 职业性格测评题目并计算结果，覆盖 4 对维度：

- EI：外倾（E） - 内倾（I）
- SN：实感（S） - 直觉（N）
- TF：思维（T） - 情感（F）
- JP：判断（J） - 知觉（P）

本测评共 44 题，每题二选一（A/B），每个选项归属一个维度字母。
8 个字母各均匀出现 11 次（共 88 个选项），保证 4 对维度的对称设计。

## When to Use This Skill

在以下场景触发本 skill：

- 用户明确说出“测MBTI”“做MBTI测试”“帮我测一下MBTI”“启动MBTI测评”这类完整指令
- 用户直接询问“我是什么MBTI”“生成我的MBTI人格报告”“帮我算我的MBTI类型”
- 用户主动提及“打开MBTI测评工具”“开始MBTI测评”
- 用户说“我要做人格测试，指定是MBTI的”“我想测MBTI的完整维度”
- 用户历史对话3轮内明确提过要做MBTI测评，当前轮次说“继续”“开始吧”“下一步”
- 用户直接发送“MBTI测评”“MBTI测试”作为唯一指令，无其他无关内容

在以下**边界场景**建议先与用户确认测评意图：用一句简短反问（例如"您是想做 44 题 MBTI 职业性格测评吗？"），用户明确确认后再启动测评流程。若当前对话模式不支持中途询问（如 Visualizer 一次性渲染 / 已直接加载题目卡片），按以下兜底规则处理：
- 同轮若还含其他无关任务（如"帮我查 MBTI，再做下测评"），不启动测评，等用户单独询问测评时再触发
- 用户连续两轮仍在同一边界场景徘徊且未明确确认，默认判定为非测评需求，按下方"When NOT to Use This Skill"处理，改用纯 MBTI 知识科普
- 7 类边界场景示例：
  - 用户只单独发送"MBTI"三个字，没有后续补充任何内容
  - 用户讨论某类MBTI人格特征后，说"我好像就是这种人""我感觉我符合这个类型"
  - 用户说"我想了解自己的性格类型""帮我做个性格测试"，没有明确指定是MBTI
  - 用户说"我想看看我的人格是什么样的""分析一下我的性格"，没有限定测评类型
  - 用户提到"我朋友说我是XX型MBTI，想验证一下"，没有直接说要启动测评
  - 用户在讨论MBTI相关话题后，说"帮我测测看"，没有明确指向其他测评工具
  - 用户说"我想做个测试看看我适合什么MBTI类型"，表述模糊未直接唤起测评

## When NOT to Use This Skill

以下场景**不触发**本 skill：

- 用户仅询问MBTI基础科普：“MBTI有多少种类型”“MBTI的四个维度是什么”“MBTI的起源是什么”
- 用户仅查询某类MBTI人格的特征：“INTJ的特点是什么”“INFP适合什么职业”“ESTP的恋爱观”
- 用户讨论MBTI的非测评应用场景：“MBTI面试技巧”“用MBTI做职场沟通”“MBTI社交指南”
- 用户在讨论其他完全无关的话题时，偶然提到MBTI：“我昨天和朋友聊到MBTI”“我同事是ISFJ”
- 用户明确要求其他类型的测试：“我要做九型人格测试”“帮我测DISC性格”“生成霍兰德职业测试”
- 用户的需求是内容生成类：“帮我写一篇MBTI主题的小红书文案”“生成MBTI相关的短视频脚本”
- 用户同时提出多个混合需求，且没有明确表示要做测评：“帮我查MBTI类型，再写一份职场沟通方案”
- 用户明确表示“我不想做测评”“我只是想了解MBTI的知识”，直接拦截所有测评唤起

## 题目元数据

```yaml
assessment_id: MBTI-44-001
assessment_name: "MBTI 职业性格测评"
question_total: 44
dimension_count: 8   # E/I/S/N/T/F/J/P
dimension_pairs: 4   # EI/SN/TF/JP
role_type_count: 16  # ISTJ...ESFJ
references_path: "references/questions.md"  # 数据文件形态 B（多文件，当前仓库采用）：题库在 questions.md；另有 profiles.md / dimensions.md / job_scores.md。脚本未指定任何路径时自动加载这 4 个文件；指定 --references-path 可回退单文件模式（含全部 4 个 H2 段的合并 mbti.md）
algorithm_path: "references/algorithm.md"
score_calculation_path: "scripts/calculate_mbti.py"
score_function: "calculate_scores"
entrypoint: "python scripts/calculate_mbti.py --answers '{\"1\":\"A\",\"2\":\"B\"}'"
```

## references 数据文件结构（关键，允许单文件或多文件）

测评数据（题库 / 16 型档案 / 维度对详情 / 职业匹配分）以 **4 个 H2 段** 组织，每段必须包含一段散文说明 + 一个 ```json 代码块，段顺序固定如下（**H2 标题改名会破坏脚本解析，禁止改名**）：

1. `## 题库` → 44 题题库数组
2. `## 16 型人格档案` → 16 型档案数组
3. `## 维度对详情` → 4 维度对 + 8 端详情数组
4. `## 职业匹配分` → 每型 66 个 jobId+score 列表

**文件形态（二选一，均受支持，按需选用）**：

- **形态 A：单文件（兼容保留，非当前采用）**：4 个 H2 段全部放在一个合并 md 文件内（如 `references/mbti.md`），脚本用 `--references-path` 指定。
- **形态 B：多文件拆分（默认，当前仓库采用）**：4 个 H2 段拆分为 4 个独立 md 文件：
  - `references/questions.md`（含 `## 题库`）
  - `references/profiles.md`（含 `## 16 型人格档案`）
  - `references/dimensions.md`（含 `## 维度对详情`）
  - `references/job_scores.md`（含 `## 职业匹配分`）
  - 每个拆分文件内**仍必须保留对应的 H2 标题与 ```json 代码块**（解析锚点不变），仅文件边界变化；
  - 脚本**不传任何路径时自动加载这 4 个文件**；也可用 `--questions-path` / `--profiles-path` / `--dimensions-path` / `--job-scores-path` 分别覆盖；传入 `--references-path` 则整体回退单文件模式。

脚本 `calculate_mbti.py` 的 `load_md_section(md_path, section_title)` 按 H2 标题定位段、提取 ```json 代码块、`json.loads` 解析；**单文件与多文件两种形态共用同一解析逻辑**。若任意一段缺失或代码块未闭合，脚本会抛 `ValueError`。拆分/合并只是文件组织方式，不影响评分逻辑与输出。

## 题目加载硬约束（关键）

1. 本 skill **仅有唯一测评流程**：展示 44 题 → 用户作答 → 输出完整测评报告。不存在其他题数或版本，不询问用户"要做多少题"、不提供任何"版本二选一"入口。
2. 触发测评后必须直接展示全部 44 题进入答题流程，不得插入任何"选择题目数量""选择版本"的中间步骤。
3. 题目必须从 references 数据文件的 `## 题库` 段内 ```json 代码块中读取 `questions` 数组，按 `id` 1→44 原序展示；**禁止模型自行编造或凭印象生成题目**。题库段的数据源形态见"references 数据文件结构"一节：当前仓库采用形态 B（多文件），题库从 `references/questions.md` 读取。
4. 题库共 44 题，每题必须包含 `id` / `question` / `prompt` / `options`（每个 option 含 `option` / `content` / `dimension`）四要素，渲染时不得遗漏任一字段，尤其不得省略 `options.content`。
5. 若题库读取失败或不足 44 题，必须直接报错说明，不得用"部分题目"凑数、不得用模型自拟题补齐。
6. 一次性展示全部 44 道题，不得分页、不得"先展示前几题"、不得逐题加载。

### 题目数据加载流程

模型在渲染交互卡片前，**必须先读取题库文件**，不得凭训练数据回忆题目：

1. 通过 Read 工具读取题库文件 `references/questions.md`（当前仓库采用形态 B 多文件，题库独立存放；此文件仅 21KB，渲染题目时**只读这一个文件**，不要读取 profiles.md / dimensions.md / job_scores.md），定位 `## 题库` 段下的 ```json 代码块，解析 `questions` 数组。
2. 按数组顺序（id 1→44）渲染全部 44 题，不得打乱、不得省略、不得改写题干/提示语/选项文本/维度归属；**渲染动作必须遵循本文件"题目卡片渲染规范"一节（§0.1 固定 CSS / §0.2 固定结构 / §0.3 固定交互行为）逐字输出，禁止自绘样式**。
3. 若 Read 工具调用失败、`## 题库` 段缺失、```json 代码块未闭合、返回内容不足 44 题、或解析报错，模型**必须**向用户返回明确的错误提示（如"题库文件读取失败，请检查 references/questions.md 中 `## 题库` 段是否存在且包含 44 题"），**不得**：
   - 用模型自拟/凭印象/从训练数据回忆的题目补齐
   - 用"部分题目"凑数渲染卡片
   - 返回空卡片或不做任何响应
   - 静默跳过题目渲染只输出其他元素（标题、进度条、维度标签等）


## 工作流程

本 skill 只有一条流程：**展示 44 题 → 用户在卡片内作答 → 点击"提交测评" → 模型直接输出完整测评报告**。具体步骤：

1. 渲染完整交互卡片展示全部 44 题，用户在卡片内完成作答（每题仅 A 或 B）。
2. 用户点击"提交测评"时：
   - 存在未作答题目 → 卡片内自动滚动到第一个未答题并高亮提示，**不提交、不出报告**；
   - 已答完全部 44 题 → 卡片内 JS 通过宿主回传机制（`sendPrompt()`）将答案 JSON 自动作为用户消息发送。
3. 模型收到答案后对答案进行校验，确保题目编号、答案类型、维度映射正确。
4. 调用评分脚本计算 8 个维度字母计数 + 4 对维度百分比 + dominant_type。
5. **直接**返回用户完整测评报告：16 型人格代码 + 各维度得分/百分比 + 特点分析（优势/缺点）+ 推荐职业。

**强制约束（不允许有其他链路）**：用户点击"提交测评"且答完全部题目后，模型必须**直接输出完整测评报告**。禁止以下任何行为：要求用户复制/粘贴答案回传、要求用户手动输入答案、先输出答案 JSON 等待用户确认、把出报告推迟到用户再次追问之后、以任何形式要求用户参与答案传递。

## WorkBuddy 视觉化交互卡片约束（关键）

本 skill 在 Workbody / WorkBuddy 场景下，不仅需要返回结构化 JSON，也必须支持可视化内联交互卡片：即在对话中直接渲染一个 HTML/CSS/JS 组件，模拟真实测评页面，且在聊天窗口中保持稳定的视觉结构。

### 0. 题目卡片渲染规范（强制，100% 一致）

为保证**每个用户、每次会话**触发本 skill 时，题目展示的格式与样式**完全一致**，禁止模型自行设计或自由发挥。本 skill **不依赖任何外部 HTML 模板文件**，渲染规范直接固化在本文件：模型必须按下方"§0.1 固定 CSS""§0.2 固定结构"逐字输出，任何用户渲染结果必须彼此完全一致。

#### 0.1 固定 CSS（强制，逐字照抄，禁止改动任何属性/值/类名）

```css
#mbti-card{font-family:var(--font-sans);color:var(--color-text-primary);max-width:680px;margin:0 auto}
#mbti-card .q-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:2px}
#mbti-card .q-title{font-size:18px;font-weight:500;margin:0}
#mbti-card .q-sub{font-size:13px;color:var(--color-text-secondary);margin:2px 0 12px}
#mbti-card .q-count{font-size:13px;font-weight:500;color:var(--color-text-secondary)}
#mbti-card .q-track{height:6px;border-radius:999px;background:var(--color-background-secondary);overflow:hidden;margin-bottom:16px}
#mbti-card .q-track i{display:block;height:100%;width:0;border-radius:999px;background:var(--color-text-info);transition:width .2s}
#mbti-card .q-sec{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:12px 16px;margin:14px 0}
#mbti-card .q-sec-t{font-size:14px;font-weight:500;margin:0 0 4px}
#mbti-card .q-sec-d{font-size:12px;color:var(--color-text-secondary);line-height:1.6;margin:0}
#mbti-card .q-item{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:12px 16px;margin-top:10px;scroll-margin-top:12px}
#mbti-card .q-item.miss{border-color:var(--color-text-danger);box-shadow:0 0 0 1px var(--color-text-danger)}
#mbti-card .q-top{display:flex;gap:10px;align-items:flex-start}
#mbti-card .q-num{flex:none;min-width:26px;height:26px;border-radius:999px;background:var(--color-background-secondary);color:var(--color-text-secondary);font-size:13px;font-weight:500;display:flex;align-items:center;justify-content:center;margin-top:1px}
#mbti-card .q-body{flex:1;min-width:0}
#mbti-card .q-text{font-size:14px;font-weight:500;line-height:1.5;margin:0}
#mbti-card .q-prompt{font-size:12px;color:var(--color-text-tertiary);line-height:1.6;margin:4px 0 10px}
#mbti-card .q-opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
#mbti-card .q-opt{font-family:inherit;font-size:13px;line-height:1.5;text-align:left;padding:9px 12px;border-radius:var(--border-radius-md);cursor:pointer;background:#F5F6F8;border:1px solid #E5E7EB;color:#3A3F47;transition:background .15s,border-color .15s,color .15s}
#mbti-card .q-opt:hover{border-color:var(--color-border-secondary)}
#mbti-card .q-opt.on{background:#E8F1FF;border:1px solid #4E8CFF;color:#1E4FB8;box-shadow:inset 3px 0 0 #4E8CFF}
#mbti-card .q-foot{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:16px;flex-wrap:wrap}
#mbti-card .q-tip{font-size:13px;color:var(--color-text-danger);display:none}
#mbti-card .q-submit{font-family:inherit;font-size:14px;font-weight:500;padding:10px 22px;border-radius:var(--border-radius-md);cursor:pointer;background:#4E8CFF;color:#FFFFFF;border:1px solid #4E8CFF;transition:background .15s}
#mbti-card .q-submit:hover{background:#3A78E0}
@media (max-width:560px){#mbti-card .q-opts{grid-template-columns:1fr}}
```

#### 0.2 固定结构（强制）

模型渲染时必须以 `#mbti-card` 为根容器，依次输出：标题区（`.q-head` 内 `.q-title` + `.q-count`）、副标题（`.q-sub`）、进度条（`.q-track` 内含 `<i>`）、题目列表（`#mbti-list`）、底部（`.q-foot` 内 `.q-tip` + `.q-submit` 提交按钮）。44 题按"每 11 题一段"插入 4 个 `.q-sec` 分段块（标题 `.q-sec-t` + 提示词 `.q-sec-d`，文案见 §3 分段提示词要求），每题一个 `.q-item`（`.q-num` 顺序编号 = 数组下标 +1、`.q-text` 题干、`.q-prompt` 提示语、`.q-opts` 内两个 `.q-opt` 选项按钮，按钮文本为 `A. 选项内容` / `B. 选项内容`）。

#### 0.3 固定交互行为（强制）

- 选项点击：仅切换当前题选中态，选中按钮加 `.on` 类（互斥，同一题两端不可同时高亮），并实时更新 `.q-count` 文本（`已答 / 44`）与 `.q-track i` 宽度（已答数/44×100%）。
- 提交按钮（文案固定为 `提交测评`，始终可见可点）：存在未作答题目 → 在 `.q-tip` 显示"还有 N 题未作答，请先完成第 X 题"，给第一个未答题 `.q-item` 加 `.miss` 类并 `scrollIntoView` 滚动到该题，约 1.6s 后移除 `.miss`；已答完 → 调用宿主回传 `sendPrompt('[MBTI测评提交] 我的答案如下：' + JSON.stringify(答案对象))`，答案对象 key 使用**顺序号 1→44**（数组下标 +1），value 为 A/B。

- **渲染流程（强制）**：
  1. 通过 Read 工具读取数据文件 `## 题库` 段，解析 `questions` 数组（44 题，见"题目数据加载流程"）；
  2. 严格按 §0.1 CSS、§0.2 结构、§0.3 行为、§3 分段文案渲染完整 HTML 交互卡片，作为交互组件（Visualizer show_widget）的 `widget_code` 输出。
- **唯一可变量**：题目数据（题干/提示语/选项内容）。除此之外 CSS、类名、颜色、布局、分段文案、按钮行为均不得改动。
- **禁止事项**：
  - 禁止自行编写或改动 CSS（含选中态 `#E8F1FF`/`#4E8CFF`/`#1E4FB8`、未选中态 `#F5F6F8`/`#E5E7EB`/`#3A3F47` 等固定色值）；
  - 禁止更换类名、调整布局、修改四段分组标题与提示词文字；
  - 禁止在规范结构外再包裹自定义样式或追加额外脚本；
  - 禁止"凭印象"重画题目卡片或每次输出不同样式。

### 1. 渲染目标

当用户触发"开始测评"或"MBTI 测评"时，必须返回一个可渲染的内联卡片，而不是纯文本说明。

该内联卡片必须包含：

- 顶部标题：`MBTI 职业性格测评`
- 二级说明：`共 44 题，请根据真实感受选择"A"或"B"`
- 顶部进度条：显示已答题数/总题数，例如 `17 / 44`
- 维度标签：例如 `E/I · 外倾-内倾`（当前题所属维度对）
- 题目列表：每一题显示**顺序编号** + 题干 + 提示语（prompt）
  - 顺序编号必须按"从上到下依次递增"渲染：第 1 题显示 `1`、第 2 题显示 `2`、……、第 44 题显示 `44`
  - **禁止使用题库 JSON 里的 `id` 字段作为展示编号**（题库 `id` 仅用于内部作答映射，不直接呈现给用户）
  - 题目展示顺序必须与题库 `questions` 数组顺序一致，不打乱
  - 顺序号与题库 `id` 的对应关系在本次题库下恰好一致（`id=1` 即第 1 题、`id=44` 即第 44 题），但渲染层不得依赖该巧合，必须以"数组下标 +1"作为顺序号唯一来源
- 每道题的答题区域：左右两侧各有一个单选按钮，分别对应 `A` 与 `B`
  - 选项按钮文本必须显示选项内容（content），而不是仅显示 A/B 字母
- 当前题目高亮：当前题对应的题目区域、标签和按钮状态应明显区分
- 底部交互：可前后翻题，并提供始终可见的"提交测评"按钮（禁用/启用规则见 §4 交互约束）
- 允许用户在同一对话流中直接答题，不需要跳转到其他页面

### 2. 视觉结构要求

视觉结构必须遵循以下稳定版布局：

- 整体是一个白色/浅灰背景的卡片容器，边框柔和、圆角适中
- 标题采用大字号、黑色/深灰字体
- 子标题采用中等字号、灰色字体，位置在标题下方
- 顶部右侧显示进度文本，格式固定为 `已答题数 / 44`（如 `17 / 44`），数字含义为"已作答题数"，不是"当前题号"
- 进度条位于标题区下方，长度为卡片宽度的主内容区域，宽度比例 = 已答题数 / 44
- 当前维度对标签使用绿色/浅绿色浅底色，圆角和内边距稳定
- 题目行高统一，题干左对齐，选项按钮右对齐
- **题目顺序编号（关键）**：每题左侧的编号必须按"从上到下依次递增"渲染（第 1 题显示 `1`，第 2 题显示 `2`，……，第 44 题显示 `44`），**禁止使用题库 JSON 的 `id` 字段作为展示编号**。渲染器取数组下标 `index + 1` 作为顺序号；题库 `id` 仅在提交作答时用于内部映射，不参与展示。
- `A / B` 是两个二选一按钮，选中态必须使用如下固定色值，不允许模型自行挑选颜色：
  - 未选中：浅灰底 `background: #F5F6F8`，边框 `1px solid #E5E7EB`，字色 `#3A3F47`
  - 已选中：淡蓝底 `background: #E8F1FF`，边框 `1px solid #4E8CFF`，字色 `#1E4FB8`，并可加左侧细色条 `box-shadow: inset 3px 0 0 #4E8CFF`
  - 同一题两个按钮互斥：选中 A 时 B 必须退回浅灰底，反之亦然，禁止两端同时高亮
  - 已选中按钮必须有可感知的视觉差异（背景色明显比未选中更蓝、边框颜色变深、字色更蓝），用户一眼能看出选的是哪一个
- 题目行之间用浅边框分隔
- 在页面底部可以显示辅助说明，例如 `今天帮你做些什么？@引用对话文件 / 调用技能与指令`
- 44 道题必须按四段显示，每一段前方都有明确的分段标题和提示词，不得混合成一大段连续题目

### 3. 分段提示词要求（必须严格遵守）

44 道题必须按"维度对"分成 4 个部分，并且每个部分的标题和提示文案必须按以下固定文本输出，不得改写语义、删减内容或自由替换：

1. 第一部分标题：`第一部分 外倾-内倾（E/I）`
   - 提示词：`下面列举了若干情境，请根据你通常的思考和行为方式选择最接近的答案。选 A 即倾向外倾（E），选 B 即倾向内倾（I）。请按顺序回答本部分全部 11 题。`

2. 第二部分标题：`第二部分 实感-直觉（S/N）`
   - 提示词：`下面列举了若干情境，请根据你通常接收信息的方式选择最接近的答案。选 A 即倾向实感（S），选 B 即倾向直觉（N）。请按顺序回答本部分全部 11 题。`

3. 第三部分标题：`第三部分 思维-情感（T/F）`
   - 提示词：`下面列举了若干情境，请根据你通常做决策的方式选择最接近的答案。选 A 即倾向思维（T），选 B 即倾向情感（F）。请按顺序回答本部分全部 11 题。`

4. 第四部分标题：`第四部分 判断-知觉（J/P）`
   - 提示词：`下面列举了若干情境，请根据你通常的生活方式选择最接近的答案。选 A 即倾向判断（J），选 B 即倾向知觉（P）。请按顺序回答本部分全部 11 题。`

要求：

- 四段必须依次连续出现
- 每段上方都必须显示标题与提示词
- 标题和提示词必须原样保留，不得改成中文简写、删减或替换 A/B 表述
- 每段内部题目都必须属于对应维度对，不得跨段混排
- 题目顺序按 `references/questions.md` 中 `## 题库` 段 `questions` 数组 `id` 1-44 原序展示，不打乱

> 注：`references/questions.md` 中 `## 题库` 段每题的 `options` 已带 `dimension` 字段（E/I/S/N/T/F/J/P），渲染器需先按维度对（EI/SN/TF/JP）分组排序后再展示。若题库原序已满足"每 11 题一个维度对"，可直接按 id 顺序渲染。

### 4. 交互约束

- 一次性展示全部 44 道题，不能分页、不能逐题加载、不能"先展示前几题再继续"
- 题目须按题库原顺序从 1 到 44 连续展示，不得打乱顺序
- 每题必须只有一个有效答案：`A` 或 `B`
- 用户点击 `A` 或 `B` 时，必须只切换当前题在该题目的选中状态，不应同时多选
- 题目展示编号按"从上到下依次递增"（第 1 题显示 `1`、……、第 44 题显示 `44`），与题库 `id` 解耦；详见 §2 视觉结构要求
- 进度条长度和文本必须依据已答题/总题数自动更新，但整个评测仍然保持 44 题全量展示
- **提交按钮始终可见且始终可点击（关键）**：`提交测评` 按钮必须在卡片渲染的同一帧就出现在卡片最下方，**禁止"答完才显示""达到某条件才渲染"等延迟出现行为**，**禁止 `disabled` 置灰不可点**。无论是否答完，按钮都必须处于 `enabled` 可点击态。点击行为分两种：
  - 存在未作答题目 → **禁止提交、禁止出报告**，自动滚动到第一个未作答题目并高亮提示"还有 N 题未作答，请先完成第 X 题"（跳转规则见下条"未答跳转"）
  - 已答完全部 44 题 → 直接触发评分计算，**立即输出完整测评报告**（见"提交后直接出报告"一节），不允许任何中间链路
- **触发流程稳定性（关键）**：无论用户在第几轮对话、用什么措辞（"开始测评"/"做 MBTI"/"测测我的 MBTI"/"启动 MBTI 测评"等任一触发词）唤起本 skill，**首次返回的卡片必须完整包含标题、进度条、维度标签、44 题列表、A/B 双选按钮、提交按钮**全部要素。**禁止"先返回题目卡片，等下一轮再补提交按钮"**、**禁止"先返回部分题目，等用户催促再补全"**、**禁止"渲染时只返回 JSON 不返回交互卡片"**。若模型因上下文长度或工具限制无法一次渲染完整卡片，必须明确报错而非返回残缺卡片。
- **未答跳转（关键）**：用户点击 `提交测评` 按钮时，若存在未作答题目，**禁止提交并禁止直接出报告**，必须自动将焦点/视图滚动到第一个未作答的题目上，并高亮提示"还有 N 题未作答，请先完成第 X 题"。第一个未答题判定规则：按渲染顺序 1→44（即数组下标 +1）遍历，遇到第一道 `answers` 中对应位置为空（即未选 A/B）的题即为锚点题。跳转后该题的 `A/B` 双选按钮区域必须获得视觉焦点（边框高亮、自动滚入可见区），不得仅做文字提示而不滚动
- **提交后直接出报告（关键）**：用户点击 `提交测评` 且已答完全部 44 题时，卡片内 JS 必须调用宿主回传机制（`sendPrompt()`）将答案 JSON 以自动生成的用户消息形式回传给对话流，**模型收到答案后立即调用评分脚本计算并输出完整测评报告**。**禁止任何中间链路**：禁止要求用户复制/粘贴答案回传、禁止要求用户手动输入答案 JSON、禁止"先把答案发我"再等下一轮出报告、禁止输出答案 JSON 后等待用户确认。
- 交互必须发生在当前对话流的内联组件中，而不是返回普通纯文本
- 该组件的页面流必须保持"44 题一次性展示 + 全量答题 + 提交"的连续逻辑

### 5. HTML / Visualizer 输出要求

如果系统支持 WorkBuddy 的 Visualizer / 内联 HTML 渲染，返回内容必须满足：

- 以 HTML 片段或可渲染组件形式输出，而不是纯 Markdown
- 必须保留视觉层结构：标题、进度、维度对标签、题目列表、双选按钮
- 不能出现散乱的自然语言说明替代卡片
- 不能直接输出仅有 JSON 字段而没有交互容器
- 不能让前端自行"自由发挥"生成不同布局
- 只允许按本 skill 规定的结构渲染，不允许引入无关内容

### 6. 参考示意结构

以下内容仅用于描述结构，不应被当作自由文本输出；真正交互时，应按本 skill 的稳定规则渲染：

```html
<div class="assessment-card">
  <h2>MBTI 职业性格测评</h2>
  <div class="subtitle">共 44 题，请根据真实感受选择"A"或"B"</div>
  <div class="progress-row">
    <div class="progress-bar" style="width: 38.6%;"></div>
    <span>17 / 44</span>
  </div>
  <div class="dimension-pill">E/I · 外倾-内倾</div>
  <div class="question-row">
    <div class="question-number">1</div>
    <div class="question-text">你心情不好的时候更倾向于如何处理</div>
    <div class="question-prompt">凭直觉作答，勿思对错和他人期望，只选实际会采取的行动。</div>
    <div class="answer-options">
      <button class="option-btn selected">A. 直接向好友倾诉</button>
      <button class="option-btn">B. 让我静静，我自己消化一下</button>
    </div>
  </div>
  <!-- 第 2~44 题略，结构同上；编号按从上到下依次递增 -->
  <div class="card-footer">
    <button class="submit-btn">提交测评</button>
  </div>
</div>
```

> 注：`question-number` 文本必须是"从上到下依次递增的顺序号"（数组下标 +1），不是题库 `id`；`progress-bar` 宽度 = 已答题数 / 44 × 100%；`submit-btn` 在卡片渲染的同一帧就出现且**始终可点击**：未答完点击则跳转到第一个未答题，已答完点击自动回传答案并直接输出完整测评报告。

### 7. 禁止事项

- 不允许输出纯文本描述替代卡片
- 不允许缺失"A / B"双选按钮
- 不允许没有维度对标签
- 不允许没有进度条和题号
- 不允许使用题库 `id` 作为题目展示编号，必须用"从上到下依次递增"的顺序号
- **不允许提交按钮延迟出现**：提交按钮必须在卡片首次渲染的同一帧就出现在卡片最下方，禁止"答完才显示""下一轮才补"
- **不允许提交按钮置灰不可点击**：无论是否答完，提交按钮必须处于 `enabled` 可点击态；未答完点击执行"未答跳转"，已答完点击直接出报告
- **不允许首次渲染卡片时缺失提交按钮**：无论用户在第几轮对话唤起测评，首次返回的卡片必须包含提交按钮
- **不允许"先返问题卡片、再补提交按钮"或"先返部分题目、再补全"的两段式渲染**：必须一次性返回完整卡片
- 不允许在页面中出现无关长文案或随机推理内容
- 不允许模型自行更换布局结构，必须保持 WorkBuddy 交互卡片的稳定格式
- **不允许模型自绘题目卡片（关键）**：题目卡片必须严格遵循本文件"题目卡片渲染规范"（§0.1 固定 CSS / §0.2 固定结构 / §0.3 固定交互行为）输出，禁止自行编写 CSS/布局/颜色，确保每个用户看到的题目格式与样式完全一致

## 输出格式

### 报告渲染规范（强制，100% 一致）

为保证**每个用户、每次提交**测评后输出的报告格式与样式**完全一致**，禁止模型自行设计。本 skill **不依赖任何外部 HTML 模板文件**，报告渲染规范直接固化在本文件：模型必须按下方"§R.1 固定 CSS""§R.2 固定结构"逐字渲染。

#### R.1 固定 CSS（强制，逐字照抄，禁止改动任何属性/值/类名）

```css
#mbti-rpt{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;color:#1F2937;max-width:680px;margin:0 auto}
#mbti-rpt .r-hdr{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:6px;background:linear-gradient(135deg,#4E8CFF 0%,#7C5CFF 55%,#A855F7 100%);border-radius:16px;padding:22px 22px 18px;color:#fff;box-shadow:0 4px 14px rgba(124,92,255,.25)}
#mbti-rpt .r-type{font-size:30px;font-weight:700;letter-spacing:2px;color:#fff}
#mbti-rpt .r-hdr .r-nm{font-size:15px;font-weight:500;color:rgba(255,255,255,.92)}
#mbti-rpt .r-meta{display:flex;gap:12px;margin:14px 0 16px;flex-wrap:wrap}
#mbti-rpt .r-mc{flex:1;border-radius:12px;padding:12px 16px;min-width:96px;color:#fff}
#mbti-rpt .r-mc:nth-child(1){background:linear-gradient(135deg,#4E8CFF,#3B82F6)}
#mbti-rpt .r-mc:nth-child(2){background:linear-gradient(135deg,#10B981,#0D9488)}
#mbti-rpt .r-mc:nth-child(3){background:linear-gradient(135deg,#F59E0B,#F97316)}
#mbti-rpt .r-mc b{display:block;font-size:22px;font-weight:700;line-height:1.3;color:#fff}
#mbti-rpt .r-mc span{font-size:12px;color:rgba(255,255,255,.9)}
#mbti-rpt .r-bar8{display:flex;gap:4px;margin:14px 0 4px}
#mbti-rpt .r-bar8 div{flex:1;border-radius:6px 6px 0 0;padding:6px 0 4px;text-align:center;font-size:11px;line-height:1.4;background:#F1F3F7;color:#6B7280}
#mbti-rpt .r-bar8 .v{font-weight:600;font-size:12px;color:#374151}
#mbti-rpt .r-bar8 div.win{background:#7C5CFF;color:#fff}
#mbti-rpt .r-bar8 div.win .v{color:#fff}
#mbti-rpt .r-bar8 div:nth-child(1).win,#mbti-rpt .r-bar8 div:nth-child(2).win{background:#3B82F6}
#mbti-rpt .r-bar8 div:nth-child(3).win,#mbti-rpt .r-bar8 div:nth-child(4).win{background:#10B981}
#mbti-rpt .r-bar8 div:nth-child(5).win,#mbti-rpt .r-bar8 div:nth-child(6).win{background:#8B5CF6}
#mbti-rpt .r-bar8 div:nth-child(7).win,#mbti-rpt .r-bar8 div:nth-child(8).win{background:#F59E0B}
#mbti-rpt .r-cap{font-size:11px;color:#9CA3AF;text-align:center;margin-bottom:2px}
#mbti-rpt .r-dim{background:#fff;border:1px solid #E6E9F0;border-radius:14px;padding:14px 16px;margin-top:14px}
#mbti-rpt .r-dim.t-ei{border-left:4px solid #3B82F6}
#mbti-rpt .r-dim.t-sn{border-left:4px solid #10B981}
#mbti-rpt .r-dim.t-tf{border-left:4px solid #8B5CF6}
#mbti-rpt .r-dim.t-jp{border-left:4px solid #F59E0B}
#mbti-rpt .r-dimh{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap}
#mbti-rpt .r-dn{font-size:13px;font-weight:600;color:#111827}
#mbti-rpt .r-win{font-size:12px;font-weight:600;border-radius:999px;padding:3px 12px;background:#EEF2FF;color:#4F46E5}
#mbti-rpt .r-dim.t-ei .r-win{background:#EFF6FF;color:#1D4ED8}
#mbti-rpt .r-dim.t-sn .r-win{background:#ECFDF5;color:#047857}
#mbti-rpt .r-dim.t-tf .r-win{background:#F5F3FF;color:#6D28D9}
#mbti-rpt .r-dim.t-jp .r-win{background:#FFFBEB;color:#B45309}
#mbti-rpt .r-pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
#mbti-rpt .r-side .r-nm{font-size:13px;font-weight:600;display:flex;justify-content:space-between;margin-bottom:6px;color:#111827}
#mbti-rpt .r-side .r-pct{color:#6B7280;font-weight:400}
#mbti-rpt .r-track{height:8px;border-radius:999px;background:#EEF0F4;overflow:hidden}
#mbti-rpt .r-track i{display:block;height:100%;border-radius:999px;background:#D8DCE3}
#mbti-rpt .r-side.win .r-track i{background:#7C5CFF}
#mbti-rpt .r-dim.t-ei .r-side.win .r-track i{background:#3B82F6}
#mbti-rpt .r-dim.t-sn .r-side.win .r-track i{background:#10B981}
#mbti-rpt .r-dim.t-tf .r-side.win .r-track i{background:#8B5CF6}
#mbti-rpt .r-dim.t-jp .r-side.win .r-track i{background:#F59E0B}
#mbti-rpt .r-side.win .r-pct{color:#111827;font-weight:600}
#mbti-rpt .r-feat{font-size:12px;color:#6B7280;margin-top:6px;line-height:1.6}
#mbti-rpt .r-side.win .r-feat{color:#7C5CFF}
#mbti-rpt .r-dim.t-ei .r-side.win .r-feat{color:#1D4ED8}
#mbti-rpt .r-dim.t-sn .r-side.win .r-feat{color:#047857}
#mbti-rpt .r-dim.t-tf .r-side.win .r-feat{color:#6D28D9}
#mbti-rpt .r-dim.t-jp .r-side.win .r-feat{color:#B45309}
#mbti-rpt details{margin-top:12px;border-top:1px dashed #E6E9F0;padding-top:10px}
#mbti-rpt summary{cursor:pointer;font-size:13px;font-weight:600;color:#7C5CFF}
#mbti-rpt summary:hover{color:#5B3FD4}
#mbti-rpt .r-txt{font-size:13px;line-height:1.75;margin:0;color:#374151}
#mbti-rpt .r-sec{font-size:12px;font-weight:600;margin:14px 0 6px;color:#7C5CFF;border-left:3px solid #7C5CFF;padding-left:8px}
#mbti-rpt .r-duo{display:grid;grid-template-columns:1fr 1fr;gap:12px}
#mbti-rpt .r-sc{border:1px solid #E6E9F0;border-left:3px solid #7C5CFF;border-radius:10px;padding:10px 12px;background:#FAFBFF}
#mbti-rpt .r-sc .h{font-size:13px;font-weight:600;margin-bottom:4px;color:#111827}
#mbti-rpt .r-sc .f{font-size:12px;color:#7C5CFF;margin-bottom:6px;font-weight:500}
#mbti-rpt .r-sc p{font-size:12px;line-height:1.7;margin:0 0 6px;color:#4B5563}
#mbti-rpt .r-feats{display:grid;grid-template-columns:1fr 1fr;gap:12px}
#mbti-rpt .r-feat2{border:1px solid #E6E9F0;border-radius:10px;padding:12px 14px}
#mbti-rpt .r-feat2 .h{font-size:13px;font-weight:600;margin-bottom:6px;color:#111827}
#mbti-rpt .r-feat2 p{font-size:12px;line-height:1.75;margin:0;color:#4B5563}
#mbti-rpt .r-feat2.adv{border-left:3px solid #10B981;background:#F0FDF4}
#mbti-rpt .r-feat2.adv .h{color:#047857}
#mbti-rpt .r-feat2.dis{border-left:3px solid #F97316;background:#FFF7ED}
#mbti-rpt .r-feat2.dis .h{color:#B45309}
#mbti-rpt .r-tags{display:flex;flex-wrap:wrap;gap:6px}
#mbti-rpt .r-tag{font-size:12px;border-radius:999px;padding:4px 12px;border:1px solid transparent;font-weight:500}
#mbti-rpt .r-tag:nth-child(6n+1){background:#EFF6FF;color:#1D4ED8;border-color:#BFDBFE}
#mbti-rpt .r-tag:nth-child(6n+2){background:#ECFDF5;color:#047857;border-color:#A7F3D0}
#mbti-rpt .r-tag:nth-child(6n+3){background:#F5F3FF;color:#6D28D9;border-color:#DDD6FE}
#mbti-rpt .r-tag:nth-child(6n+4){background:#FFFBEB;color:#B45309;border-color:#FDE68A}
#mbti-rpt .r-tag:nth-child(6n+5){background:#FFF1F2;color:#BE123C;border-color:#FECDD3}
#mbti-rpt .r-tag:nth-child(6n){background:#F0FDFA;color:#0F766E;border-color:#99F6E4}
#mbti-rpt .r-note{font-size:12px;color:#94A3B8;margin-top:16px;line-height:1.7;background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:10px;padding:10px 14px}
@media (max-width:560px){#mbti-rpt .r-pair,#mbti-rpt .r-duo,#mbti-rpt .r-feats{grid-template-columns:1fr}}
```

#### R.2 固定结构（强制）

模型渲染时必须以 `#mbti-rpt` 为根容器，依次输出：标题区（`.r-hdr` 内 `.r-type` = `dominant_type` + `.r-nm` = `role_detail.name`；头部为品牌蓝紫渐变底 + 白字，模型不额外加类）、指标卡（`.r-meta` 内 3 个 `.r-mc`：倾向强度 `display_score`、人群占比 `proportion%`、胜出维度 `dimension_pairs[].result` 按 `·` 连接；第 1/2/3 张卡由 nth-child 自动上蓝/绿/橙渐变底、白字，模型不额外加类）、8 字母计数条（`.r-bar8`，按 E/I/S/N/T/F/J/P 固定顺序；每个字母格为一个 `<div>`，内部为字母 + 数值（数值用 `.v`）；**胜出字母的 div 必须加 `win` 类** → 自动按 nth-child 上维度色（E/I 蓝、S/N 绿、T/F 紫、J/P 橙）白字；非胜出字母不加类，灰底灰字）、4 个维度卡（`.r-dim`，按 EI/SN/TF/JP 顺序，**每个维度卡必须按维度对加主题类**：EI→`t-ei`、SN→`t-sn`、TF→`t-tf`、JP→`t-jp` → 自动获得左侧 4px 维度色边条；每卡含 `.r-dimh` 标题（`dimension_name` + `胜出：result result_name` 徽标 `.r-win`，徽标底色/字色随主题类自动变化）、`.r-pair` 两端对比条（`option+name1`、`score1 题 · percent1%`、宽度=percent 的 `.r-track i`；**胜出端的 `.r-side` 必须加 `win` 类** → 进度条自动变维度主色、feature 与百分比自动变维度深色；非胜出端不加类，进度条灰色）、`<details>` 展开区固定三段（模型必须按此顺序与文案输出）：`.r-sec` 标题 `胜出端特质` + 胜出端 `result_traits` 原文、`.r-sec` 标题 `维度解读` + `dimension_description`/`dimension_prompt` 原文、`.r-sec` 标题 `两端详情对比` + 两端 `option1_detail`/`option2_detail` 的 `.r-duo` 两卡 `.r-sc`（`name`/`feature`/`traits`/`characteristics` 原文，卡片带品牌紫左缘条））、特点分析卡（`.r-dim` 不加主题类：`.r-sec` 标题固定为 `特点分析`，内部 `.r-feats` 双卡并排——`.r-feat2 adv` 标题固定为 `优势` + `role_detail.advantages` 原文、`.r-feat2 dis` 标题固定为 `缺点` + `role_detail.disadvantages` 原文；**禁止展示 `role_detail.description`**）、职业推荐卡（`.r-dim` 不加主题类：`.r-sec` 标题固定为 `职业推荐` + `analysis.summary` 的 `.r-txt` + `analysis.recommendations` 的 `.r-tag` 标签列表，标签颜色由 nth-child 自动 6 色循环，模型不额外加类）、底部 `.r-note` 说明。

- **维度主题色映射表（强制，模型必须按此映射加类/判定胜出）**：EI → `t-ei`（主色 #3B82F6 蓝）、SN → `t-sn`（主色 #10B981 绿）、TF → `t-tf`（主色 #8B5CF6 紫）、JP → `t-jp`（主色 #F59E0B 橙）。维度卡主题类、`.r-bar8` 与 `.r-side` 的 `win` 类均由报告数据中的 `pair` 与胜出结果决定，同一份报告内必须保持一致。
- **渲染流程（强制）**：
  1. 调用 `scripts/calculate_mbti.py`（建议加 `--compact` 紧凑输出）得到报告 JSON（**唯一数据来源**，字段必须全量）；
  2. **只读脚本输出的报告 JSON 进行渲染，禁止再读取 `references/profiles.md` / `references/dimensions.md` / `references/job_scores.md`**：脚本输出已按查表结果透传全部渲染所需原文（`role_detail` 7 字段、`dimension_pairs` 8 端 `name/feature/traits/characteristics`、`dimension_name/description/prompt`、`result_traits/result_characteristics`、`analysis` 全量，合计仅约 13KB），渲染报告所需的每个字段都在其中，无需也不得再读 references 文件（合计约 131KB，纯属浪费上下文、拖慢响应）；
  3. 严格按 §R.1 CSS、§R.2 结构渲染完整 HTML 报告，作为交互组件（Visualizer show_widget）的 `widget_code` 输出给用户。
- **唯一可变量**：报告数据（各字段值）。除此之外 CSS、类名、颜色、布局、文案均不得改动；`t-ei`/`t-sn`/`t-tf`/`t-jp` 与 `win` 为规范类名，属 §R.2 固定结构的一部分，模型必须按映射表使用，不得增删或改色。
- **禁止事项**：
  - 禁止自行编写 CSS / 更换类名 / 调整颜色或布局；
  - 禁止改写、省略或截断 `role_detail`（7 字段原文）、`dimension_pairs` 两端 8 端详情（`name`/`feature`/`traits`/`characteristics` 原文）、`analysis`（summary + recommendations 全量）等字段；
  - 禁止用 Markdown 表格、纯文本替代报告渲染；
  - 禁止"凭印象"画报告或每次输出不同样式。

## 确定性输出约束（关键）

为避免 Workbody 生成结果每次都变化，本 skill 必须执行严格的确定性规则：

1. 结果必须以脚本计算结果为唯一准绳，不允许模型自由推断分数或人格类型。
2. `dimension_pairs` 必须按固定顺序输出 4 对：`["EI", "SN", "TF", "JP"]`。
3. `dominant_type` 必须由 4 对维度结果字母按 EI → SN → TF → JP 顺序拼接，不能由模型自行命名或重写。
4. 每对维度的胜出字母规则：当两端计数相等时取 option1（即 E/S/T/J），即 `score1 >= score2 ? option1 : option2`。
5. 百分比必须保留两位小数，使用 `decimal.ROUND_HALF_UP`（与 Java `BigDecimal.ROUND_HALF_UP` 一致），不允许 Python 默认 banker's rounding。
6. `display_score` 为 4 个胜出端百分比的平均值取整数，使用 `decimal.ROUND_HALF_UP`，不允许模型自由发挥。
7. `role_detail` 必须从 `references/profiles.md` 的 `## 16 型人格档案` 段按 `dominant_type` 查表得到，16 型全覆盖；**字段值必须为原文，不允许模型自行撰写或改写人格描述、优势、劣势、职业推荐**（**该查表由评分脚本完成**，模型直接使用脚本输出 JSON 中已透传的原文，无需自行读文件）。
8. `dimension_pairs[].result_name/result_feature/result_traits/result_characteristics` 与 `option1_detail/option2_detail` 必须从 `references/dimensions.md` 的 `## 维度对详情` 段按 `dimension` + `option` 查表，使用原文（含 `title/feature/traits/characteristics` 字段），不允许模型自行撰写（**该查表由评分脚本完成**，模型直接使用脚本输出 JSON 中已透传的原文，无需自行读文件）。
9. `job_scores` 必须从 `references/job_scores.md` 的 `## 职业匹配分` 段按 `dominant_type` 查表，固定 66 条，顺序固定；不允许模型自行生成 jobId 或 score（**该查表由评分脚本完成**，模型直接使用脚本输出 JSON 中已透传的数据）。
10. `analysis.summary` 必须使用固定模板，且只基于 `dominant_type` 与 `role_detail.name` / `role_detail.careers` 前 5 项生成。
11. `analysis.recommendations` 必须为 `role_detail.careers` 字符串按顿号切分后的字符串数组，顺序固定，不得截断。
12. 任何场景都不允许输出随机、模糊、口语化的结论；必须稳定输出统一结构。
13. 如果题目不完整，必须返回 `incomplete`，并列出缺失题号；不得在有缺失时强行生成完整结论。
14. 生成结果时必须以 JSON 对象返回，不能返回 Markdown、自然语言说明、额外说明块或解释性文本。
15. 同一组 `answers` 必须在多次调用间产生 byte-equal 的 JSON 输出（无随机数、无时间戳、无外部网络/DB 依赖；经 4 组答案 × 10 次运行验证通过）。
16. 报告文案来源：`references/profiles.md`（16 型档案）/ `references/dimensions.md`（维度对详情）/ `references/job_scores.md`（职业匹配分）三个拆分文件，**查表由评分脚本完成**——脚本输出 JSON 已按查表结果透传全部原文字段（约 13KB），模型渲染报告时**只读脚本输出 JSON**，**禁止再读这三个 references 文件**（合计约 131KB，纯属浪费上下文、拖慢响应）；**禁止在生成结果时混入模型自拟内容**，所有 `role_detail` / `dimension_pairs[].result_*` / `dimension_*` / `option1_detail` / `option2_detail` / `job_scores` 字段直接使用脚本输出中的原文，不得改写。
17. **全量输出约束（关键）**：每一轮报告输出都必须包含完整 JSON 结构的全部字段，**严禁**在任何轮次出现"与上一轮一致""结果同上""向上翻阅""如前所述""参考前次输出"等省略式表述。无论同一组 `answers` 在同一对话流中被请求多少次，每次都必须输出一份**字段齐全、文案完整**的报告 JSON，包括但不限于：`dimension_counts`（8 键）、`dimension_pairs`（4 对，每对含 `option1_detail`/`option2_detail` 共 8 端详情）、`role_detail`（7 字段原文）、`job_scores`（66 条）、`analysis`（summary + recommendations 全量）。**禁止以"已生成过""缓存命中""结果不变"为由截断或省略任何字段**。
18. **禁止引用式表述**：禁止在报告 JSON 内或外层包裹文字中使用"见上文""参见第 N 轮""同前次""以上一轮为准"等指向历史轮次的表述。每轮报告必须是自包含的、可独立阅读的完整内容。
19. **样式确定性（强制）**：题目卡片必须遵循本文件"题目卡片渲染规范"（§0.1/§0.2/§0.3）、测评报告必须遵循本文件"报告渲染规范"（§R.1/§R.2）渲染，**对任何用户、任何轮次渲染结果必须逐字一致**（唯一差异仅为题目数据 / 报告数据）；禁止任何用户或任何轮次获得不同格式/样式的卡片或报告。

本 skill 负责在用户点击"提交测评"后**直接输出结构化的完整测评报告**，不承担前端渲染。输出必须严格符合以下 JSON 结构：

```json
{
  "assessment_id": "MBTI-44-001",
  "assessment_name": "MBTI 职业性格测评",
  "status": "completed",
  "answered_count": 44,
  "total_questions": 44,
  "display_score": 57,
  "max_score": 100,
  "dominant_type": "ESTP",
  "dimension_counts": {
    "E": 7, "I": 4, "S": 6, "N": 5, "T": 6, "F": 5, "J": 5, "P": 6
  },
  "dimension_pairs": [
    {
      "pair": "EI", "label": "外倾-内倾",
      "option1": "E", "name1": "外倾", "score1": 7, "percent1": 63.64,
      "option2": "I", "name2": "内倾", "score2": 4, "percent2": 36.36,
      "result": "E",
      "result_name": "外倾型E",
      "result_feature": "向外联结，破界而行",
      "result_traits": "与他人相处精力充沛，希望成为注意的焦点……（原文，全文见 references/dimensions.md 的 ## 维度对详情 段）",
      "result_characteristics": "你热爱参与社交，往往是社交活动的发起者……（原文，含换行）",
      "option1_detail": {"name": "外倾型E", "feature": "向外联结，破界而行", "traits": "……", "characteristics": "……"},
      "option2_detail": {"name": "内倾型I", "feature": "向内深耕，静思蓄能", "traits": "……", "characteristics": "……"},
      "dimension_name": "外倾E&内倾I",
      "dimension_description": "第一个维度：根据个人的能量更集中地指向哪里来区分……（原文）",
      "dimension_prompt": "人毕竟生活在社会中，有时会顺应外在环境的、工作的需要调整自己的行为……（原文）"
    },
    {"pair": "SN", "...": "..."},
    {"pair": "TF", "...": "..."},
    {"pair": "JP", "...": "..."}
  ],
  "role_detail": {
    "type": "ESTP",
    "name": "企业家",
    "proportion": 4.3,
    "description": "规则？那是用来打破再重建的乐高积木！",
    "advantages": "你是敏锐的发现者，善于看出眼前的需要……（原文，全文见 references/profiles.md 的 ## 16 型人格档案 段）",
    "disadvantages": "由于你关注外界各种变化信息……（原文）",
    "careers": "企业家、业务运作顾问、个人理财专家、证券经纪人、银行职员……（原文，顿号分隔，全 35 项）"
  },
  "job_scores": [
    {"jobId": 4, "score": 0.8},
    {"jobId": 3, "score": 0.3},
    {"jobId": 2, "score": 0.4}
  ],
  "analysis": {
    "summary": "用户在 E、S、T、P 四个维度胜出，人格类型为 ESTP（企业家），适合 企业家、业务运作顾问、个人理财专家、证券经纪人、银行职员 等方向。",
    "recommendations": ["企业家", "业务运作顾问", "个人理财专家", "证券经纪人", "银行职员", "..."]
  }
}
```

> 注：以上 `role_detail.*` 与 `dimension_pairs[].result_*` / `dimension_*` / `option1_detail` / `option2_detail` 字段全部来自 `references/profiles.md` 中 `## 16 型人格档案` 与 `references/dimensions.md` 中 `## 维度对详情` 段的原文，模型不得自行撰写、改写或省略。`job_scores` 长度固定为 66，源自 `references/job_scores.md` 的 `## 职业匹配分` 段。

### 输出规范

- `status` 必须为 `completed` 或 `incomplete`
- `display_score` 为 0-100 的整数，且必须来自脚本计算结果
- `dominant_type` 为 4 个结果字母按 EI → SN → TF → JP 拼接，例：`"ESTP"`，不能自行更改为其他文本
- `dimension_counts` 必须按固定顺序输出 `E`、`I`、`S`、`N`、`T`、`F`、`J`、`P` 八个键
- `dimension_pairs` 必须按 `EI`、`SN`、`TF`、`JP` 顺序输出 4 对
- 每对维度的 `result` 字母规则：`score1 >= score2` 时取 `option1`（即 E/S/T/J），否则取 `option2`
- `percent1` + `percent2` 必须等于 100.00（仅当计数非零时）
- `role_detail` 必须从 `references/profiles.md` 的 `## 16 型人格档案` 段按 `type` 查表，包含 `type/name/proportion/description/advantages/disadvantages/careers` 七个字段，**全部使用原文，不得改写、不得省略、不得由模型自行撰写**
- `job_scores` 必须从 `references/job_scores.md` 的 `## 职业匹配分` 段按 `dominant_type` 查表，固定返回 66 条 `{jobId, score}`，顺序固定
- `dimension_pairs[].result_name/result_feature/result_traits/result_characteristics` 必须从 `references/dimensions.md` 的 `## 维度对详情` 段按 `dimension` + 胜出端 `option` 查表（`title` → `result_name`，`feature/traits/characteristics` 原样透传）
- `dimension_pairs[].option1_detail/option2_detail` 必须按对应维度对的 `option1/option2` 字母查 `## 维度对详情` 段，`name` 字段对应 `title`
- `dimension_pairs[].dimension_name/dimension_description/dimension_prompt` 必须从 `## 维度对详情` 段的 `name/description/prompt` 字段原样透传
- `analysis.summary` 必须使用固定中文模板：`"用户在 {4个胜出字母用顿号连接} 四个维度胜出，人格类型为 {dominant_type}（{role_name}），适合 {careers 前5项顿号连接} 等方向。"`
- `analysis.recommendations` 必须为 `role_detail.careers` 按顿号切分后的字符串数组，顺序固定，不得截断
- 若题目未完成，则返回 `incomplete`，并输出 `missing_questions`（缺失题号字符串数组）
- 输出必须为纯 JSON，不允许嵌套说明、Markdown 代码块或额外字段

### 渲染约束（关键）

本 skill 约束的是"生成结果的渲染契约"，而不是页面实现细节。具体要求如下：

- `dominant_type` 必须作为页面主标题字段使用（如 `ESTP`）。
- `role_detail.name`（中文名如 `企业家`）必须作为副标题或角色名展示字段使用。
- `role_detail.proportion` 必须作为占比展示字段使用（值为百分数，如 `4.3` 表示 4.3%，前端按需补 `%`）。
- `display_score` 必须作为总分展示字段使用。
- `dimension_pairs` 必须作为各维度得分表格/柱状图数据源。
  - 每对维度必须展示两侧字母、名称、计数与百分比，以及胜出端高亮
  - 每对维度必须展示 `dimension_name`（如 `外倾E&内倾I`）作为该对的展示名
  - 每对维度展开后必须展示 `dimension_description` 与 `dimension_prompt` 的原文（可作为该对的说明/作答引导）
  - 每对维度必须展示胜出端的 `result_name` / `result_feature` / `result_traits` / `result_characteristics` 四段原文
  - **8 端详情必须全部展示（关键）**：每对维度的 `option1_detail` 与 `option2_detail` 共 8 端（E/I/S/N/T/F/J/P 各一端），每端必须完整展示 `name` / `feature` / `traits` / `characteristics` 四段字段的原文。**禁止只展示胜出端**，**禁止省略 `option1_detail` 或 `option2_detail`**，**禁止只展示 `name`/`feature` 而省略 `traits`/`characteristics`**。两端必须左右并列或上下并列，便于用户对比两端倾向。
- `role_detail.advantages` / `disadvantages` 必须在"特点分析"卡中分别作为"优势"/"缺点"两块展示，使用原文（含换行符原样渲染）；`role_detail.description` 不在报告中展示（JSON 输出仍保留该字段，全量输出约束不变）
- `role_detail.careers` 必须作为职业推荐展示字段使用，按顿号切分后呈现为列表
- `job_scores`（66 条 jobId+score）可作为"职业匹配度"扩展数据源展示；前端如需展示 jobId 对应职业名，需另查 jobId→职业名映射，不在本 skill 范围内
- 结果页最底部必须按 `EI`、`SN`、`TF`、`JP` 的顺序展开展示，每对维度至少包含"胜出端"与"两端详情"两部分
- `analysis.summary` 必须作为结果说明文本展示
- `analysis.recommendations` 必须作为建议列表渲染数据
- 任何前端都不能自行生成新的字段名来替代上述结构
- 前端只能根据这几个字段进行展示，不能依赖自由文本解析
- 报告文案受"确定性输出约束"第 16 条统一约束：报告所有文案字段均已由 `scripts/calculate_mbti.py` 按数据文件查表后透传到脚本输出 JSON 中（约 13KB），前端/模型**只读脚本输出 JSON** 进行渲染，禁止再读 `references/profiles.md` / `references/dimensions.md` / `references/job_scores.md` 等 md 文件（合计约 131KB，纯属浪费上下文）；同时禁止模型自行撰写或改写任何字段（包括 `role_detail` / `dimension_pairs[].result_*` / `dimension_*` / `option1_detail` / `option2_detail` / `job_scores` 等），所有字段原文以脚本输出为准

### 禁止事项

- 不允许返回自由文本替代 JSON
- 不允许缺少 `dimension_pairs`
- 不允许缺少 `dominant_type`
- 不允许 `dimension_pairs` 中遗漏任一对维度
- 不允许 `role_detail` 缺失任一字段
- 不允许在 skill 中混合前端渲染逻辑
- 不允许前端自行扩展未定义字段覆盖结果解释
- 不允许使用 Python 默认 `round()`（banker's rounding），必须用 `decimal.ROUND_HALF_UP`
- 不允许模型自行撰写 `role_detail.description/advantages/disadvantages/careers`，必须使用评分脚本输出 JSON 中已查表透传的原文（源文件为 `references/profiles.md` 的 `## 16 型人格档案` 段）
- 不允许模型自行撰写 `dimension_pairs[].result_*/option1_detail/option2_detail/dimension_*`，必须使用评分脚本输出 JSON 中已查表透传的原文（源文件为 `references/dimensions.md` 的 `## 维度对详情` 段）
- 不允许模型自行生成 `job_scores` 中的 jobId 或 score，必须使用评分脚本输出 JSON 中已查表透传的数据（源文件为 `references/job_scores.md` 的 `## 职业匹配分` 段）
- **不允许只展示胜出端而省略非胜出端的 `option1_detail`/`option2_detail`**：8 端详情（E/I/S/N/T/F/J/P）必须全部展示，每端的 `name/feature/traits/characteristics` 四段缺一不可
- **不允许在任何轮次以"与上一轮一致""结果同上""向上翻阅"等省略式表述替代完整 JSON 输出**：每轮报告必须自包含、字段齐全、文案完整
- **不允许用户点击"提交"按钮时若有未答题就出报告**：必须先跳转到第一个未答题并提示，未答完毕前禁止触发评分
- **不允许"复制答案回传"链路（关键）**：用户点击"提交测评"且答完全部题目后，模型必须直接基于回传的答案立即计算并输出完整测评报告。禁止要求用户复制/粘贴答案、禁止要求用户手动输入答案 JSON、禁止"先把答案发我"或任何让用户参与答案传递的中间环节
- **不允许模型自绘题目卡片或报告样式（关键）**：题目卡片必须遵循本文件"题目卡片渲染规范"（§0.1/§0.2/§0.3）、报告必须遵循本文件"报告渲染规范"（§R.1/§R.2），禁止自行编写 CSS/布局/颜色替代，确保所有用户看到的格式与样式完全一致

## 题目结构说明

该评测题目以 4 对维度对为核心，采用"二选一强制选项"式答题。

- 第一部分：外倾-内倾（E/I），共 11 题
- 第二部分：实感-直觉（S/N），共 11 题
- 第三部分：思维-情感（T/F），共 11 题
- 第四部分：判断-知觉（J/P），共 11 题

每题的两个选项（A/B）分别归属维度对的两端字母。

### 题目示例

```json
{
  "id": 1,
  "question": "你心情不好的时候更倾向于如何处理",
  "prompt": "凭直觉作答，勿思对错和他人期望，只选实际会采取的行动。",
  "options": [
    {"option": "A", "content": "直接向好友倾诉", "dimension": "E"},
    {"option": "B", "content": "让我静静，我自己消化一下", "dimension": "I"}
  ]
}
```

字段说明：
- `id`：题目编号（1-44）
- `question`：题干文本
- `prompt`：作答提示语，渲染时显示在题干下方
- `options`：二选一选项数组
  - `option`：选项字母（A 或 B）
  - `content`：选项内容文本
  - `dimension`：该选项归属的维度字母（E/I/S/N/T/F/J/P）

## 评分入口

评分脚本位置：

- `scripts/calculate_mbti.py`
- 评分函数：`calculate_scores(answers, questions)`
- 输出：JSON 格式的分数与人格类型结果

示例命令：

```bash
# 不传任何路径：自动加载 references/questions.md / profiles.md / dimensions.md / job_scores.md
# 推荐加 --compact：紧凑输出，报告 JSON 约 13KB，渲染报告时模型只读它（无需再读 references 大文件）
python scripts/calculate_mbti.py \
  --answers '{"1":"A","2":"B","3":"A","4":"B"}' --compact
```

## 评分规则

### 1. 维度字母计数

每道题的每个选项归属一个维度字母（E/I/S/N/T/F/J/P）。用户作答归一化为 `A` 或 `B`，匹配到的选项所对应的 `dimension` 字母 +1：

- 答案归一：`Y/YES/TRUE/1` → `A`，`N/NO/FALSE/2` → `B`，`A`/`B` 直通
- 算法：
  ```text
  for q in questions:
      ans = normalize_answer(answers[str(q.id)])  # 'A' 或 'B' 或 ''
      for opt in q.options:
          if opt.option.upper() == ans:
              counts[opt.dimension] += 1
              break
  ```

8 个字母计数之和 = 已作答题数。

### 2. 维度对百分比

每个维度对（如 EI）内计算两端字母的百分比，公式（保留两位小数，`ROUND_HALF_UP`）：

```text
percent[E] = score[E] / (score[E] + score[I]) * 100
percent[I] = score[I] / (score[E] + score[I]) * 100
```

### 3. 维度对结果字母

取百分比更高的一端作为结果字母；两端相等时取 option1（E/S/T/J），即 `score1 >= score2 ? option1 : option2`。

### 4. 拼出 16 型人格代码

按固定顺序 EI → SN → TF → JP 拼接 4 个结果字母：

```text
dominant_type = result_letter[EI] + result_letter[SN] + result_letter[TF] + result_letter[JP]
```

例：`E + N + F + P` → `"ENFP"`

### 5. 总分（display_score，0-100）

```text
dominant_percents = [percent[胜出端] for 每个维度对]
display_score = round(mean(dominant_percents))
```

例：(63.64 + 54.55 + 63.64 + 72.73) / 4 = 63.64 → `64`

### 6. 角色详情

依据 `dominant_type` 在 `references/profiles.md` 的 `## 16 型人格档案` 段中按 `type` 查表，输出：

- `type`：人格代码（如 `"ESTP"`）
- `name`：人格中文名（如 `"企业家"`）
- `proportion`：该型在人群中的占比（值为百分数，如 `4.3` 表示 4.3%）
- `description`：人格描述长文本（原文，含换行符）
- `advantages`：优势（原文，含换行符）
- `disadvantages`：劣势（原文，含换行符）
- `careers`：适配职业（顿号分隔的原文，含 35 项左右）

16 型必须全部覆盖，缺一不可。

### 7. 职业匹配分

依据 `dominant_type` 在 `references/job_scores.md` 的 `## 职业匹配分` 段中按 `role`（大写）查表，输出 `job_scores` 数组（66 条 `{jobId, score}`），顺序固定。

## 报告示例

下面是一组真实作答（全 A）经评分脚本计算后的报告片段。所有非数值字段均来自数据文件（`references/profiles.md` / `references/dimensions.md` / `references/job_scores.md`）的原文，仅做截断展示：

```json
{
  "assessment_id": "MBTI-44-001",
  "status": "completed",
  "answered_count": 44,
  "total_questions": 44,
  "display_score": 57,
  "max_score": 100,
  "dominant_type": "ESTP",
  "dimension_counts": {"E": 7, "I": 4, "S": 6, "N": 5, "T": 6, "F": 5, "J": 5, "P": 6},
  "dimension_pairs": [
    {"pair": "EI", "option1": "E", "name1": "外倾", "score1": 7, "percent1": 63.64,
     "option2": "I", "name2": "内倾", "score2": 4, "percent2": 36.36, "result": "E",
     "result_name": "外倾型E", "result_feature": "向外联结，破界而行",
     "option1_detail": {"name": "外倾型E", "feature": "向外联结，破界而行", "traits": "...", "characteristics": "..."},
     "option2_detail": {"name": "内倾型I", "feature": "向内深耕，静思蓄能", "traits": "...", "characteristics": "..."},
     "dimension_name": "外倾E&内倾I", "dimension_description": "...", "dimension_prompt": "..."}
  ],
  "role_detail": {
    "type": "ESTP", "name": "企业家", "proportion": 4.3,
    "description": "规则？那是用来打破再重建的乐高积木！",
    "advantages": "你是敏锐的发现者，善于看出眼前的需要……",
    "disadvantages": "由于你关注外界各种变化信息……",
    "careers": "企业家、业务运作顾问、个人理财专家、证券经纪人、银行职员……"
  },
  "job_scores": [{"jobId": 4, "score": 0.8}, {"jobId": 3, "score": 0.3}, "...共66条"],
  "analysis": {
    "summary": "用户在 E、S、T、P 四个维度胜出，人格类型为 ESTP（企业家），适合 企业家、业务运作顾问、个人理财专家、证券经纪人、银行职员 等方向。",
    "recommendations": ["企业家", "业务运作顾问", "个人理财专家", "证券经纪人", "银行职员", "..."]
  }
}
```

## 重要原则

- 题库必须明确给出题目编号、题干、提示语和选项维度归属；
- 评分逻辑必须单独写在脚本文件中，不能隐含在对话里；
- 用户提交题目后，必须返回测试结果、得分和人格类型；
- 若题目缺失或答案格式不合法，先要求用户补全，不要直接伪造结果；
- 选项维度映射必须保持一一对应；
- 同一组作答必须产出 byte-equal 的 JSON（无随机性）。

## Demo 目录结构

```text
career-personality/
├── SKILL.md
├── references/
│   ├── algorithm.md
│   ├── questions.md            # 形态 B（当前仓库采用）：## 题库（44 题题库数组，渲染题目时只读此文件）
│   ├── profiles.md             # ## 16 型人格档案（16 型档案数组）
│   ├── dimensions.md           # ## 维度对详情（4 对 + 8 端详情数组）
│   └── job_scores.md           # ## 职业匹配分（每型 66 条 jobId+score 列表）
└── scripts/
    └── calculate_mbti.py
```

## 资源说明

- 题库 + 16 型档案 + 维度对详情 + 职业匹配分：**形态 B（多文件，当前仓库采用）**，拆分为 4 个独立文件，每段仍保留对应的 H2 标题 + 散文说明 + 一个 ```json 代码块：
  - `references/questions.md`：`## 题库` 段，44 题题库（**渲染题目卡片时只读此文件**，约 21KB，避免把其余数据读入上下文导致输出不稳定）
  - `references/profiles.md`：`## 16 型人格档案` 段
  - `references/dimensions.md`：`## 维度对详情` 段
  - `references/job_scores.md`：`## 职业匹配分` 段
  - 脚本不传路径自动加载 4 文件；`--questions-path` 等可分别覆盖；`--references-path` 可整体回退单文件模式
  - `## 题库` 段：44 道题的二选一职业性格测评题库
  - `## 16 型人格档案` 段：16 型人格档案
  - `## 维度对详情` 段：4 对维度对 + 8 端字母详情
  - `## 职业匹配分` 段：每型 66 条 jobId+score
- 渲染规范：题目卡片渲染规范见本文件"WorkBuddy 视觉化交互卡片约束 → §0 题目卡片渲染规范"（固定 CSS/结构/交互行为），测评报告渲染规范见本文件"输出格式 → §R 报告渲染规范"（固定 CSS/结构）；**渲染规范直接固化在 SKILL.md 内，不依赖任何外部 HTML 模板文件，模型必须逐字遵循，禁止自绘样式**
- 算法说明：`references/algorithm.md`
- 评分脚本：`scripts/calculate_mbti.py`，通过 `load_md_section(md_path, section_title)` 按 H2 标题切段、提取 ```json 代码块解析；支持多文件（默认，无参数自动加载 4 文件）与单文件（`--references-path`）两种形态；`--compact` 紧凑输出（渲染报告时推荐，输出约 13KB）
- **H2 标题文本（`## 题库` / `## 16 型人格档案` / `## 维度对详情` / `## 职业匹配分`）是 `calculate_mbti.py#load_md_section` 解析锚点，禁止改名**，否则脚本会抛 `ValueError`（拆分多文件时每个文件内同样必须保留对应 H2 标题）。

## 交互输出要求

用户完成题目后，系统应返回：

1. 测评 ID 与名称
2. 状态（completed / incomplete）
3. 16 型人格代码（dominant_type）
4. 4 对维度的计数与百分比
5. 角色详情（type / name / proportion / description / advantages / disadvantages / careers）
6. 4 对维度的详情（含胜出端 name/feature/traits/characteristics 与两端详情，及 dimension_name/description/prompt 原文）
7. 职业匹配分（job_scores，每型 66 条 jobId+score）
8. 总分（display_score）
9. 若未通过/未完成，给出缺失题号列表

本 skill 仅有唯一测评流程：展示 44 题 → 用户作答 → 输出完整测评报告。评分逻辑独立于题库内容；后续如需切换题库，只需替换 `references/questions.md` 中 `## 题库` 段的 ```json 代码块，无需改动评分脚本。报告文案（`role_detail` / `dimension_pairs[].result_*` / `dimension_*` / `job_scores`）全部来自数据文件的 `## 16 型人格档案` / `## 维度对详情` / `## 职业匹配分` 段（形态 B 下为 `references/profiles.md` / `references/dimensions.md` / `references/job_scores.md`，形态 A 下为合并的 mbti.md），如需更新文案，直接替换对应 H2 段的 ```json 代码块即可，无需改动评分脚本。**题目卡片与测评报告的展示格式/样式由本文件内固化规范锁定（题目见"§0 题目卡片渲染规范"，报告见"§R 报告渲染规范"），不依赖外部 HTML 模板文件**：任何用户、任何轮次的渲染结果必须与规范逐字一致，禁止自绘样式。
