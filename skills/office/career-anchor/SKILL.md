---
name: career-anchor
display_name: 职业锚测评
display_name_en: Career Anchor Assessment
description: 当用户提到职业价值观、职业锚、工作长期发展取向时调用本Skill，用于识别其核心职业价值取向并解读测评结果。
description_zh: 评估技术职能、管理、自主独立、安全稳定、创业创造等职业价值取向，并输出职业锚类型解读。
description_en: Use when users mention career anchors, work values, or long-term
  development orientations to identify core career values.
category: business-productivity
version: 1.0.0
author: 上海高顿教育科技有限公司
disable-model-invocation: true
---

# 职业锚测评 Skill

## Overview

生成职业锚测评题目并计算结果，覆盖 8 个维度：

- TF：技术职能型
- GM：管理型
- AU：自主型
- SE：安全型
- EC：创造型
- SV：服务型
- CH：挑战型
- LS：生活型

本测评共 40 题，每题评分 1-6 分，每个维度均匀分布 5 道题目。最终结果为得分最高的前三个维度组合（如 TF+GM+AU）。

## When to Use This Skill

在以下场景触发本 skill：

- 用户明确说出"测职业锚""做职业锚测试""帮我测一下职业锚""启动职业锚测评"这类完整指令
- 用户直接询问"我是什么职业锚""生成我的职业锚报告""帮我算我的职业锚类型"
- 用户主动提及"打开职业锚测评工具""开始职业锚测评"
- 用户说"我要做职业倾向测试，指定是职业锚的""我想测职业锚的完整维度"
- 用户历史对话3轮内明确提过要做职业锚测评，当前轮次说"继续""开始吧""下一步"
- 用户直接发送"职业锚测评""职业锚测试"作为唯一指令，无其他无关内容

在以下场景需要二次确认后才触发职业锚测评 Skill（命中后先弹出确认话术，用户同意再启动）：

- 用户只单独发送"职业锚"三个字，没有后续补充任何内容
- 用户讨论某类职业锚特征后，说"我好像就是这种人""我感觉我符合这个类型"
- 用户说"我想了解自己的职业倾向""帮我做个职业测试"，没有明确指定是职业锚
- 用户说"我想看看我的职业价值观是什么样的""分析一下我的职业倾向"，没有限定测评类型
- 用户提到"我朋友说我是XX型职业锚，想验证一下"，没有直接说要启动测评
- 用户在讨论职业锚相关话题后，说"帮我测测看"，没有明确指向其他测评工具
- 用户说"我想做个测试看看我适合什么职业锚类型"，表述模糊未直接唤起测评

## When NOT to Use This Skill

以下场景**不触发**本 skill：

- 用户仅询问职业锚基础科普："职业锚有多少种类型""职业锚的八个维度是什么""职业锚的起源是什么"
- 用户仅查询某类职业锚的特征："技术职能型的特点是什么""管理型适合什么职业""自主型的优缺点"
- 用户讨论职业锚的非测评应用场景："职业锚面试技巧""用职业锚做职业规划""职业锚职场应用"
- 用户在讨论其他完全无关的话题时，偶然提到职业锚："我昨天和朋友聊到职业锚""我同事是管理型"
- 用户明确要求其他类型的测试："我要做MBTI测试""帮我测霍兰德职业兴趣""生成九型人格测试"
- 用户的需求是内容生成类："帮我写一篇职业锚主题的小红书文案""生成职业锚相关的短视频脚本"
- 用户同时提出多个混合需求，且没有明确表示要做测评："帮我查职业锚类型，再写一份职业规划方案"
- 用户明确表示"我不想做测评""我只是想了解职业锚的知识"，直接拦截所有测评唤起

## 题目元数据

```yaml
assessment_id: CAREER-ANCHOR-40-001
assessment_name: "职业锚测评"
question_total: 40
dimension_count: 8   # TF/GM/AU/SE/EC/SV/CH/LS
dimension_distribution: 每个维度5题
result_dimensions: 3  # 取得分最高的前三个维度
references_path: "career-anchor-assessment/references/questions.md"
algorithm_path: "career-anchor-assessment/references/algorithm.md"
score_calculation_path: "career-anchor-assessment/scripts/calculate_career_anchor.py"
score_function: "calculate_scores"
entrypoint: "python career-anchor-assessment/scripts/calculate_career_anchor.py --answers '{\"1\":5,\"2\":4}'"
```

## references 数据文件结构

测评数据（题库 / 8 维度详情）以 **2 个 H2 段** 组织，每段必须包含一段散文说明 + 一个 ```json 代码块，段顺序固定如下（**H2 标题改名会破坏脚本解析，禁止改名**）：

1. `## 题库` → 40 题题库数组
2. `## 维度详情` → 8 维度详情数组

**文件形态**：
- `references/questions.md`（含 `## 题库`）
- `references/dimensions.md`（含 `## 维度详情`）
- 每个文件内**仍必须保留对应的 H2 标题与 ```json 代码块**（解析锚点不变）

## 题目加载硬约束（关键）

1. 本 skill **仅有唯一测评流程**：展示 40 题 → 用户作答 → 输出完整测评报告。不存在其他题数或版本，不询问用户"要做多少题"、不提供任何"版本二选一"入口。
2. 触发测评后必须直接展示全部 40 题进入答题流程，不得插入任何"选择题目数量""选择版本"的中间步骤。
3. 题目必须从 `references/questions.md` 文件中读取 `questions` 数组，按 `questionIndex` 1→40 原序展示；**禁止模型自行编造或凭印象生成题目**。
4. 题库共 40 题，每题必须包含 `questionIndex` / `questionText` / `dimensionCode` / `dimensionName` 四要素，渲染时不得遗漏任一字段。
5. 若题库读取失败或不足 40 题，必须直接报错说明，不得用"部分题目"凑数、不得用模型自拟题补齐。
6. 一次性展示全部 40 道题，不得分页、不得"先展示前几题"、不得逐题加载。

### 题目数据加载流程

模型在渲染交互卡片前，**必须先读取题库文件**，不得凭训练数据回忆题目：

1. 通过 Read 工具读取题库文件 `references/questions.md`，解析其 ```json 代码块为数组。
2. 按数组顺序（questionIndex 1→40）渲染全部 40 题，不得打乱、不得省略、不得改写题干/维度归属；**渲染动作必须遵循本文件"题目卡片渲染规范"一节（§0.1 固定 CSS / §0.2 固定结构 / §0.3 固定交互行为）逐字输出，禁止自绘样式**。
3. 若 Read 工具调用失败、返回内容不足 40 题、或解析报错，模型**必须**向用户返回明确的错误提示（如"题库文件读取失败，请检查 references/questions.md 文件是否存在且包含 40 题"），**不得**：
   - 用模型自拟/凭印象/从训练数据回忆的题目补齐
   - 用"部分题目"凑数渲染卡片
   - 返回空卡片或不做任何响应
   - 静默跳过题目渲染只输出其他元素（标题、进度条、维度标签等）


## 工作流程

本 skill 只有一条流程：**展示 40 题 → 用户在卡片内作答 → 点击"提交测评" → 模型直接输出完整测评报告**。具体步骤：

1. 渲染完整交互卡片展示全部 40 题，用户在卡片内完成作答（每题评分 1-6 分）。
2. 用户点击"提交测评"时：
   - 存在未作答题目 → 卡片内自动滚动到第一个未答题并高亮提示，**不提交、不出报告**；
   - 已答完全部 40 题 → 卡片内 JS 通过宿主回传机制（`sendPrompt()`）将答案 JSON 自动作为用户消息发送。
3. 模型收到答案后对答案进行校验，确保题目编号、答案值（1-6）正确。
4. 调用评分脚本计算 8 个维度得分 + 排序 + 取前三个维度。
5. **直接**返回用户完整测评报告（4 部分，严格按 §R 规范渲染）：报告头部（标签/主标题/副标题）→ 职业价值观类型（前三类型名称用 `+` 连接）→ 八维度雷达图 → 前三职业锚类型详解。

**强制约束（不允许有其他链路）**：用户点击"提交测评"且答完全部题目后，模型必须**直接输出完整测评报告**。禁止以下任何行为：要求用户复制/粘贴答案回传、要求用户手动输入答案、先输出答案 JSON 等待用户确认、把出报告推迟到用户再次追问之后、以任何形式要求用户参与答案传递。

## WorkBuddy 视觉化交互卡片约束（关键）

本 skill 在 Workbody / WorkBuddy 场景下，不仅需要返回结构化 JSON，也必须支持可视化内联交互卡片：即在对话中直接渲染一个 HTML/CSS/JS 组件，模拟真实测评页面，且在聊天窗口中保持稳定的视觉结构。

### 0. 题目卡片渲染规范（强制，100% 一致）

为保证**每个用户、每次会话**触发本 skill 时，题目展示的格式与样式**完全一致**，禁止模型自行设计或自由发挥。本 skill **不依赖任何外部 HTML 模板文件**，渲染规范直接固化在本文件：模型必须按下方"§0.1 固定 CSS""§0.2 固定结构"逐字输出，任何用户渲染结果必须彼此完全一致。

#### 0.1 固定 CSS（强制，逐字照抄，禁止改动任何属性/值/类名）

```css
#anchor-card{font-family:var(--font-sans);color:var(--color-text-primary);max-width:680px;margin:0 auto}
#anchor-card .q-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:2px}
#anchor-card .q-title{font-size:18px;font-weight:500;margin:0}
#anchor-card .q-sub{font-size:13px;color:var(--color-text-secondary);margin:2px 0 12px}
#anchor-card .q-count{font-size:13px;font-weight:500;color:var(--color-text-secondary)}
#anchor-card .q-track{height:6px;border-radius:999px;background:var(--color-background-secondary);overflow:hidden;margin-bottom:16px}
#anchor-card .q-track i{display:block;height:100%;width:0;border-radius:999px;background:var(--color-text-info);transition:width .2s}
#anchor-card .q-item{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:14px 18px;margin-top:12px;scroll-margin-top:12px}
#anchor-card .q-item.miss{border-color:var(--color-text-danger);box-shadow:0 0 0 1px var(--color-text-danger)}
#anchor-card .q-top{display:flex;gap:10px;align-items:flex-start}
#anchor-card .q-num{flex:none;min-width:28px;height:28px;border-radius:999px;background:var(--color-background-secondary);color:var(--color-text-secondary);font-size:13px;font-weight:500;display:flex;align-items:center;justify-content:center;margin-top:1px}
#anchor-card .q-body{flex:1;min-width:0}
#anchor-card .q-text{font-size:14px;font-weight:500;line-height:1.6;margin:0}
#anchor-card .q-dim{font-size:12px;color:var(--color-text-tertiary);line-height:1.5;margin:6px 0 10px}
#anchor-card .q-opts{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
#anchor-card .q-opt{font-family:inherit;font-size:13px;font-weight:500;line-height:1;text-align:center;padding:10px 8px;border-radius:var(--border-radius-md);cursor:pointer;background:#F5F6F8;border:1px solid #E5E7EB;color:#3A3F47;transition:background .15s,border-color .15s,color .15s}
#anchor-card .q-opt:hover{border-color:var(--color-border-secondary)}
#anchor-card .q-opt.on{background:#E8F1FF;border:1px solid #4E8CFF;color:#1E4FB8;box-shadow:inset 0 -2px 0 #4E8CFF}
#anchor-card .q-foot{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:18px;flex-wrap:wrap}
#anchor-card .q-tip{font-size:13px;color:var(--color-text-danger);display:none}
#anchor-card .q-submit{font-family:inherit;font-size:14px;font-weight:500;padding:10px 24px;border-radius:var(--border-radius-md);cursor:pointer;background:#4E8CFF;color:#FFFFFF;border:1px solid #4E8CFF;transition:background .15s}
#anchor-card .q-submit:hover{background:#3A78E0}
@media (max-width:560px){#anchor-card .q-opts{grid-template-columns:repeat(3,1fr)}}
```

#### 0.2 固定结构（强制）

模型渲染时必须以 `#anchor-card` 为根容器，依次输出：标题区（`.q-head` 内 `.q-title` + `.q-count`）、副标题（`.q-sub`）、进度条（`.q-track` 内含 `<i>`）、题目列表（`#anchor-list`）、底部（`.q-foot` 内 `.q-tip` + `.q-submit` 提交按钮）。40 题连续展示，每题一个 `.q-item`（`.q-num` 顺序编号 = questionIndex、`.q-text` 题干、`.q-dim` 维度信息、`.q-opts` 内六个 `.q-opt` 评分按钮，按钮文本为 `1` / `2` / `3` / `4` / `5` / `6`）。

#### 0.3 固定交互行为（强制）

- 选项点击：仅切换当前题选中态，选中按钮加 `.on` 类（互斥，同一题不可同时高亮多个），并实时更新 `.q-count` 文本（`已答 / 40`）与 `.q-track i` 宽度（已答数/40×100%）。
- 提交按钮（文案固定为 `提交测评 ↗`，始终可见可点）：存在未作答题目 → 在 `.q-tip` 显示"还有 N 题未作答，请先完成第 X 题"，给第一个未答题 `.q-item` 加 `.miss` 类并 `scrollIntoView` 滚动到该题，约 1.6s 后移除 `.miss`；已答完 → 调用宿主回传 `sendPrompt('[职业锚测评提交] 我的答案如下：' + JSON.stringify(答案对象))`，答案对象 key 使用**questionIndex**（1→40），value 为 1-6 的评分。

- **渲染流程（强制）**：
  1. 通过 Read 工具读取 `references/questions.md` 文件，解析为数组（40 题）；
  2. 严格按 §0.1 CSS、§0.2 结构、§0.3 行为渲染完整 HTML 交互卡片，作为交互组件（Visualizer show_widget）的 `widget_code` 输出。
- **唯一可变量**：题目数据（题干/维度名称）。除此之外 CSS、类名、颜色、布局、按钮行为均不得改动。
- **禁止事项**：
  - 禁止自行编写或改动 CSS（含选中态 `#E8F1FF`/`#4E8CFF`/`#1E4FB8`、未选中态 `#F5F6F8`/`#E5E7EB`/`#3A3F47` 等固定色值）；
  - 禁止更换类名、调整布局；
  - 禁止在规范结构外再包裹自定义样式或追加额外脚本；
  - 禁止"凭印象"重画题目卡片或每次输出不同样式。

### 1. 渲染目标

当用户触发"开始测评"或"职业锚测评"时，必须返回一个可渲染的内联卡片，而不是纯文本说明。

该内联卡片必须包含：

- 顶部标题：`职业锚测评`
- 二级说明：`共 40 题，请根据真实感受从 1-6 中选择一个数字`
- 顶部进度条：显示已答题数/总题数，例如 `17 / 40`
- 题目列表：每一题显示**顺序编号** + 题干 + 维度名称
  - 顺序编号必须按"从上到下依次递增"渲染：第 1 题显示 `1`、第 2 题显示 `2`、……、第 40 题显示 `40`
  - 题目展示顺序必须与题库 `references/questions.md` 数组顺序一致，不打乱
- 每道题的答题区域：六个评分按钮，分别对应 `1` / `2` / `3` / `4` / `5` / `6`
  - 按钮文本必须显示评分数字（1-6），而不是其他符号
- 底部交互：提供始终可见的"提交测评"按钮（禁用/启用规则见 §4 交互约束）
- 允许用户在同一对话流中直接答题，不需要跳转到其他页面

### 2. 视觉结构要求

视觉结构必须遵循以下稳定版布局：

- 整体是一个白色/浅灰背景的卡片容器，边框柔和、圆角适中
- 标题采用大字号、黑色/深灰字体
- 子标题采用中等字号、灰色字体，位置在标题下方
- 顶部右侧显示进度文本，格式固定为 `已答题数 / 40`（如 `17 / 40`），数字含义为"已作答题数"，不是"当前题号"
- 进度条位于标题区下方，长度为卡片宽度的主内容区域，宽度比例 = 已答题数 / 40
- 题目行高统一，题干左对齐，维度信息右对齐或下方显示
- **题目顺序编号（关键）**：每题左侧的编号必须按"从上到下依次递增"渲染（第 1 题显示 `1`，第 2 题显示 `2`，……，第 40 题显示 `40`）。
- `1-6` 是六个评分按钮，选中态必须使用如下固定色值，不允许模型自行挑选颜色：
  - 未选中：浅灰底 `background: #F5F6F8`，边框 `1px solid #E5E7EB`，字色 `#3A3F47`
  - 已选中：淡蓝底 `background: #E8F1FF`，边框 `1px solid #4E8CFF`，字色 `#1E4FB8`，并可加底部细色条 `box-shadow: inset 0 -2px 0 #4E8CFF`
  - 同一题六个按钮互斥：选中一个时其他必须退回浅灰底，禁止同时高亮多个
  - 已选中按钮必须有可感知的视觉差异（背景色明显比未选中更蓝、边框颜色变深、字色更蓝），用户一眼能看出选的是哪一个
- 题目行之间用浅边框分隔
- 40 道题必须连续显示，不分段、不分页

### 3. 交互约束

- 一次性展示全部 40 道题，不能分页、不能逐题加载、不能"先展示前几题再继续"
- 题目须按题库原顺序从 1 到 40 连续展示，不得打乱顺序
- 每题必须只有一个有效答案：`1` - `6` 的评分
- 用户点击评分按钮时，必须只切换当前题在该题目的选中状态，不应同时多选
- 进度条长度和文本必须依据已答题/总题数自动更新，但整个评测仍然保持 40 题全量展示
- **提交按钮始终可见且始终可点击（关键）**：`提交测评` 按钮必须在卡片渲染的同一帧就出现在卡片最下方，**禁止"答完才显示""达到某条件才渲染"等延迟出现行为**，**禁止 `disabled` 置灰不可点**。无论是否答完，按钮都必须处于 `enabled` 可点击态。点击行为分两种：
  - 存在未作答题目 → **禁止提交、禁止出报告**，自动滚动到第一个未作答题目并高亮提示"还有 N 题未作答，请先完成第 X 题"（跳转规则见下条"未答跳转"）
  - 已答完全部 40 题 → 直接触发评分计算，**立即输出完整测评报告**（见"提交后直接出报告"一节），不允许任何中间链路
- **未答跳转（关键）**：用户点击 `提交测评` 按钮时，若存在未作答题目，**禁止提交并禁止直接出报告**，必须自动将焦点/视图滚动到第一个未作答的题目上，并高亮提示"还有 N 题未作答，请先完成第 X 题"。第一个未答题判定规则：按渲染顺序 1→40 遍历，遇到第一个未评分（即未选 1-6）的题即为锚点题。
- **提交后直接出报告（关键）**：用户点击 `提交测评` 且已答完全部 40 题时，卡片内 JS 必须调用宿主回传机制（`sendPrompt()`）将答案 JSON 以自动生成的用户消息形式回传给对话流，**模型收到答案后立即调用评分脚本计算并输出完整测评报告**。**禁止任何中间链路**。

### 4. HTML / Visualizer 输出要求

如果系统支持 WorkBuddy 的 Visualizer / 内联 HTML 渲染，返回内容必须满足：

- 以 HTML 片段或可渲染组件形式输出，而不是纯 Markdown
- 必须保留视觉层结构：标题、进度、题目列表、评分按钮
- 不能出现散乱的自然语言说明替代卡片
- 不能直接输出仅有 JSON 字段而没有交互容器
- 不能让前端自行"自由发挥"生成不同布局
- 只允许按本 skill 规定的结构渲染，不允许引入无关内容

### 5. 禁止事项

- 不允许输出纯文本描述替代卡片
- 不允许缺失评分按钮（必须为 1-6 六个按钮）
- 不允许没有进度条和题号
- 不允许使用题库 `questionIndex` 以外的编号方式
- **不允许提交按钮延迟出现**：提交按钮必须在卡片首次渲染的同一帧就出现在卡片最下方
- **不允许提交按钮置灰不可点击**：无论是否答完，提交按钮必须处于 `enabled` 可点击态
- **不允许首次渲染卡片时缺失提交按钮**
- 不允许在页面中出现无关长文案或随机推理内容
- 不允许模型自行更换布局结构，必须保持 WorkBuddy 交互卡片的稳定格式
- **不允许模型自绘题目卡片（关键）**：题目卡片必须严格遵循本文件"题目卡片渲染规范"（§0.1 固定 CSS / §0.2 固定结构 / §0.3 固定交互行为）输出

## 输出格式

### 报告渲染规范（强制，100% 一致）

为保证**每个用户、每次提交**测评后输出的报告格式与样式**完全一致**，禁止模型自行设计。本 skill **不依赖任何外部 HTML 模板文件**，报告渲染规范直接固化在本文件：模型必须按下方"§R.1 固定 CSS""§R.2 固定结构"逐字渲染。

**样式基调（全局锁定，禁止改动）**：透明背景 + 双色（绿 `#3B6D11` + 黑 `#222`）；无渐变横幅、无卡片边框、无装饰圆点、无得分/排名/字母代码/图例/序号等附加元素；所有"更浅/更深"的层次一律用 `#3B6D11` 的不同透明度实现，**不得引入第三种颜色**；唯一例外是雷达图前三名顶点用红点 `#EF4444`（用户明确要求的保留项）。

#### R.1 固定 CSS（强制，逐字照抄，禁止改动任何属性/值/类名）

```css
#anchor-rpt{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;color:#222;max-width:680px;margin:0 auto;background:transparent}
#anchor-rpt .r-hdr{padding:6px 0 14px;text-align:left}
#anchor-rpt .r-tag{font-size:12px;font-weight:500;letter-spacing:2px;color:#3B6D11;opacity:.6;margin:0}
#anchor-rpt .r-title{font-size:28px;font-weight:700;letter-spacing:4px;color:#3B6D11;margin:6px 0 0}
#anchor-rpt .r-sub{font-size:14px;color:#3B6D11;margin:8px 0 0}
#anchor-rpt .r-line{display:block;width:56px;height:2px;background:#3B6D11;opacity:.5;margin-top:12px;border:0}
#anchor-rpt .r-type-row{font-size:34px;font-weight:700;letter-spacing:1px;color:#3B6D11;text-align:left;margin:20px 0 4px;line-height:1.3}
#anchor-rpt .r-type-row .r-plus{color:#3B6D11;opacity:.4;font-weight:400;margin:0 6px}
#anchor-rpt .r-radar{background:transparent;padding:10px 0;margin-top:8px}
#anchor-rpt .r-radar svg{display:block;width:100%;max-width:420px;height:auto;margin:0 auto}
#anchor-rpt .r-radar .r-grid{stroke:#3B6D11;stroke-opacity:.18;stroke-width:1;fill:none}
#anchor-rpt .r-radar .r-axis{stroke:#3B6D11;stroke-opacity:.35;stroke-width:1}
#anchor-rpt .r-radar .r-poly{fill:rgba(59,109,17,.12);stroke:#3B6D11;stroke-width:2;stroke-linejoin:round}
#anchor-rpt .r-radar .r-pt{fill:#3B6D11}
#anchor-rpt .r-radar .r-pt.win{fill:#EF4444}
#anchor-rpt .r-radar text{font-family:inherit}
#anchor-rpt .r-radar .r-lb{font-size:11px;font-weight:600;fill:#3B6D11}
#anchor-rpt .r-dim{padding:14px 0;margin:0}
#anchor-rpt .r-dim+.r-dim{border-top:1px solid rgba(59,109,17,.25)}
#anchor-rpt .r-dn{font-size:15px;font-weight:600;color:#3B6D11;margin:0 0 6px}
#anchor-rpt .r-desc{font-size:13px;line-height:1.7;color:#222}
```

#### R.2 固定结构（强制，4 部分，顺序固定缺一不可）

模型渲染时必须以 `#anchor-rpt` 为根容器，依次输出以下 **4 部分**：

**第一部分 · 报告头部（无背景色，整体左对齐）**：`.r-hdr` 内依次输出 `.r-tag`（文本固定 `职业锚测评`）、`.r-title`（文本固定 `职业锚测评报告`）、`.r-sub`（文本固定 `你的职业价值观类型`）、`.r-line`（一条 56px 短细线）。**禁止**添加任何背景色/渐变/边框/英文副标题。

**第二部分 · 职业价值观类型（左对齐，无附加文字）**：`.r-type-row`，内容 = **前三个维度名称用 `+` 连接**，每个 `+` 用 `<span class="r-plus">+</span>` 包裹（如 `创造型 <span class="r-plus">+</span> 安全型 <span class="r-plus">+</span> 服务型`）。**禁止**展示字母代码（如 EC+SE+SV）、得分、排名（第N名）、"第一核心/并列核心"等任何附加文字；**禁止**居中、**禁止**改字号。

**第三部分 · 八维度雷达图（无标题文字）**：`.r-radar` 容器内一个 SVG 雷达图（viewBox `0 0 320 320`，中心 (160,160)，半径 R=118），8 个轴按固定顺序 `TF→GM→AU→SE→EC→SV→CH→LS` 从 12 点方向起顺时针均布（每 45° 一个）。SVG 内必须包含（class 与 §R.1 一致，缺一不可）：
- 6 圈网格正八边形（class `r-grid`，对应得分比例 5/30、10/30、15/30、20/30、25/30、30/30，由内向外）；
- 8 条轴线（class `r-axis`，中心到各轴端）；
- 数据多边形（class `r-poly`，8 个顶点按各维度得分连线，闭合）；
- 8 个顶点圆点（class `r-pt`，半径统一 3；**得分前三的维度必须加 `win` 类，圆点填充红色 `#EF4444`**，其余填充绿色 `#3B6D11`）；
- 每个轴端一个标签（class `r-lb`）：**维度名称单行文本**（如 `服务型`），**不显示维度代码与得分数字**；
- **禁止**输出"八维度雷达图"等任何标题文字；**禁止**在雷达图下方输出 8 维度图例；**禁止**在顶点旁标注得分数字。
- **坐标公式**：第 i 个维度（i=0..7 按固定顺序）的顶点坐标 = `(160+118×得分/30×dx, 160+118×得分/30×dy)`；网格圈比例 k 的顶点坐标 = `(160+118×k/30×dx, 160+118×k/30×dy)`（k∈{5,10,15,20,25,30}）。
- **单位向量表**（固定，i 与维度对应）：i=0 `(0,-1)`、i=1 `(0.7071,-0.7071)`、i=2 `(1,0)`、i=3 `(0.7071,0.7071)`、i=4 `(0,1)`、i=5 `(-0.7071,0.7071)`、i=6 `(-1,0)`、i=7 `(-0.7071,-0.7071)`。
- **标签位置**：x=`160+118×1.05×dx`、y=`160+118×1.05×dy+3`；text-anchor 按 i 固定：i=0/4 `middle`、i=1/2/3 `start`、i=5/6/7 `end`。
- **得分范围**：每维度 5 题 × 1-6 分 = 5~30，网格从 0（圆心）到 30（外圈）每 5 分一圈。

**第四部分 · 前三职业锚类型详解（无标题、无序号）**：按得分降序依次输出 3 个 `.r-dim`（**不加任何徽章/边框/背景**），相邻 `.r-dim` 之间由 CSS `border-top` 半透明绿细线自动分隔：`.r-dn`（维度名称，绿色）+ `.r-desc`（该维度描述**原文**，黑色，必须来自 `references/dimensions.md`，禁止改写/省略/截断）。**禁止**输出"职业锚类型详解"等标题、**禁止**在类型名前加数字序号、**禁止**展示得分与排名。

- **渲染流程（强制）**：
  1. 根据用户答案计算八个维度得分（每个维度 5 题，得分范围 5-30）；
  2. 按得分降序排序（同分按固定维度顺序 TF>GM>AU>SE>EC>SV>CH>LS），取前三个维度；
  3. 从 `references/dimensions.md` 读取维度详情（维度名称与描述原文）；
  4. 严格按 §R.1 CSS、§R.2 结构渲染 4 部分完整 HTML 报告，作为交互组件（Visualizer show_widget）的 `widget_code` 输出给用户。
- **唯一可变量**：维度得分值、维度名称、维度描述原文。除此之外 CSS、类名、颜色、布局、结构顺序均不得改动。
- **禁止事项**：
  - 禁止自行编写 CSS / 更换类名 / 调整颜色或布局；
  - 禁止引入第 3 种颜色（允许的仅有绿 `#3B6D11`、黑 `#222`、雷达图前三名红点 `#EF4444`）；
  - 禁止添加背景色、渐变横幅、卡片边框、圆点装饰、得分标注、图例、字母代码、数字序号、得分/排名等已删除元素；
  - 禁止改变 4 部分顺序、遗漏任何一部分；
  - 禁止改写、省略或截断维度描述原文；
  - 禁止用 Markdown 表格、纯文本替代报告渲染；
  - 禁止用图片 URL 或外部库（如 Chart.js CDN）绘制雷达图，雷达图必须为内联 SVG 手写生成；
  - 禁止"凭印象"画报告或每次输出不同样式。

## 确定性输出约束（关键）

为避免 Workbody 生成结果每次都变化，本 skill 必须执行严格的确定性规则：

1. 结果必须以计分规则计算为唯一准绳，不允许模型自由推断分数或职业锚类型。
2. 八个维度得分必须按固定顺序输出：`TF`、`GM`、`AU`、`SE`、`EC`、`SV`、`CH`、`LS`。
3. 职业锚类型为得分最高的前三个维度代码用 `+` 连接（如 `TF+GM+AU`）。
4. 排序规则：先按得分降序，分数相同时按固定维度顺序（TF > GM > AU > SE > EC > SV > CH > LS）。
5. 得分必须为整数（各题评分累加，保留原始计算结果）。
6. 维度描述必须从 `references/dimensions.md` 文件中按 `code` 查表得到，8 维度全覆盖；**字段值必须为原文，不允许模型自行撰写或改写维度描述**。
7. 任何场景都不允许输出随机、模糊、口语化的结论；必须稳定输出统一结构。
8. 如果题目不完整，必须返回 `incomplete`，并列出缺失题号；不得在有缺失时强行生成完整结论。
9. 评分脚本（`scripts/calculate_career_anchor.py`）输出计算结果时必须以纯 JSON 对象返回，不能夹杂 Markdown、自然语言说明、额外说明块或解释性文本；模型展示层在收到脚本 JSON 后，必须另行按 §R 报告渲染规范输出 HTML 报告（JSON 是"计算层"产物，HTML 是"展示层"产物，两者职责不同、均不可省略）。
10. 同一组 `answers` 必须在多次调用间产生 byte-equal 的 JSON 输出（无随机数、无时间戳、无外部网络/DB 依赖）。
11. 报告文案来源：`references/dimensions.md` 文件，**查表由评分脚本完成**——渲染报告时**只读脚本输出 JSON**，**禁止改写原文**。
12. **全量输出约束（关键）**：每一轮报告输出都必须包含完整 JSON 结构的全部字段，**严禁**在任何轮次出现"与上一轮一致""结果同上""向上翻阅"等省略式表述。

本 skill 的职责分两层：评分脚本负责在用户点击"提交测评"后**计算并输出结构化 JSON 结果**（供计分、校验与取值）；模型负责**按 §R 报告渲染规范将结果渲染为 HTML 测评报告**展示给用户。两层均不可省略——计算不得靠模型口算/推断，展示不得用纯 JSON 或 Markdown 替代 HTML 报告。脚本输出必须严格符合以下 JSON 结构：

```json
{
  "assessment_id": "CAREER-ANCHOR-40-001",
  "assessment_name": "职业锚测评",
  "status": "completed",
  "answered_count": 40,
  "total_questions": 40,
  "anchor_type": "TF+GM+AU",
  "dimension_scores": {
    "TF": 25,
    "GM": 23,
    "AU": 22,
    "SE": 18,
    "EC": 15,
    "SV": 20,
    "CH": 19,
    "LS": 17
  },
  "top_three_dimensions": [
    {
      "code": "TF",
      "name": "技术职能型",
      "score": 25,
      "description": "注重在特定技术或职能领域的专业成长与技能提升..."
    },
    {
      "code": "GM",
      "name": "管理型",
      "score": 23,
      "description": "致力于全面管理工作..."
    },
    {
      "code": "AU",
      "name": "自主型",
      "score": 22,
      "description": "强调工作方式的自由度..."
    }
  ],
  "analysis": {
    "summary": "您的职业锚类型为 TF+GM+AU（技术职能型+管理型+自主型），得分最高的三个维度分别为：技术职能型（25分）、管理型（23分）、自主型（22分）。",
    "recommendations": ["技术研发岗位", "技术专家岗位", "管理岗位", "项目经理", "自由职业"]
  }
}
```

> 注：以上 `top_three_dimensions[].description` 字段来自 `references/dimensions.md` 文件的原文，模型不得自行撰写、改写或省略。

### 输出规范

- `status` 必须为 `completed` 或 `incomplete`
- `anchor_type` 为前三个维度代码用 `+` 连接，例：`"TF+GM+AU"`
- `dimension_scores` 必须按固定顺序输出 `TF`、`GM`、`AU`、`SE`、`EC`、`SV`、`CH`、`LS` 八个键
- `top_three_dimensions` 必须按得分降序排列，包含 `code` / `name` / `score` / `description` 四个字段，**全部使用原文**
- `dimension_description` 必须从 `references/dimensions.md` 文件中按 `code` 查表，使用原文
- `analysis.summary` 必须使用固定中文模板
- `analysis.recommendations` 必须基于前三个维度给出合理的职业建议
- 若题目未完成，则返回 `incomplete`，并输出 `missing_questions`（缺失题号字符串数组）
- 输出必须为纯 JSON，不允许嵌套说明、Markdown 代码块或额外字段

### 渲染约束（关键）

本 skill 约束的是"生成结果的渲染契约"，而不是页面实现细节。具体要求如下：

- 第一部分标题固定为 `职业锚测评报告`（标签 `职业锚测评`、副标题 `你的职业价值观类型`，头部整体左对齐）
- `top_three_dimensions[].name` 用 `+` 连接（`+` 用 `.r-plus` 包裹），作为第二部分 `.r-type-row` 展示字段（如 `服务型+管理型+挑战型`），**不展示字母代码**
- `dimension_scores` 必须作为第三部分雷达图的八维度得分数据源
- `top_three_dimensions[].description` 必须作为第四部分维度描述展示字段使用，使用原文（含换行符原样渲染）
- 任何前端都不能自行生成新的字段名来替代上述结构
- 前端只能根据这几个字段进行展示，不能依赖自由文本解析
- 报告文案不得由前端或模型自行撰写，必须来自 `references/dimensions.md` 文件的原文

### 禁止事项

- 不允许返回自由文本替代 JSON
- 不允许缺少 `dimension_scores`
- 不允许缺少 `anchor_type`
- 不允许 `top_three_dimensions` 中遗漏任一字段
- 不允许在 skill 中混合前端渲染逻辑
- 不允许前端自行扩展未定义字段覆盖结果解释
- 不允许模型自行撰写维度描述，必须使用 `references/dimensions.md` 文件中的原文
- **不允许在任何轮次以"与上一轮一致""结果同上""向上翻阅"等省略式表述替代完整 JSON 输出**
- **不允许用户点击"提交"按钮时若有未答题就出报告**
- **不允许"复制答案回传"链路（关键）**
- **不允许模型自绘题目卡片或报告样式（关键）**

## 题目结构说明

该评测题目以 8 个维度为核心，采用"评分式"答题。40 题在 8 个维度间**交错分布**（每 8 题一轮，每轮每个维度出现 1 题），每个维度共 5 题：

- TF（技术职能型）：题目 1, 9, 17, 25, 33
- GM（管理型）：题目 2, 10, 18, 26, 34
- AU（自主型）：题目 3, 11, 19, 27, 35
- SE（安全型）：题目 4, 12, 20, 28, 36
- EC（创造型）：题目 5, 13, 21, 29, 37
- SV（服务型）：题目 6, 14, 22, 30, 38
- CH（挑战型）：题目 7, 15, 23, 31, 39
- LS（生活型）：题目 8, 16, 24, 32, 40

每题的评分范围为 1-6 分，分数越高表示该描述越符合用户的实际情况。

### 题目示例

```json
{
  "questionIndex": 1,
  "questionText": "我希望做我擅长的工作，这样我的内行建议可以不断被采纳。",
  "dimensionCode": "TF",
  "dimensionName": "技术职能型",
  "dimensionDescription": null
}
```

字段说明：
- `questionIndex`：题目编号（1-40）
- `questionText`：题干文本
- `dimensionCode`：该题归属的维度代码（TF/GM/AU/SE/EC/SV/CH/LS）
- `dimensionName`：该题归属的维度名称

## 评分入口

评分脚本位置：

- `career-anchor-assessment/scripts/calculate_career_anchor.py`
- 评分函数：`calculate_scores(answers, questions)`
- 输出：JSON 格式的分数与职业锚类型结果

示例命令：

```bash
# 根据答案计算八个维度得分并排序
python career-anchor-assessment/scripts/calculate_career_anchor.py \
  --answers '{"1":5,"2":4,"3":6,"4":3,"5":5}'
```

## 评分规则

### 1. 维度得分计算

每个维度的得分 = 该维度下所有题目评分的总和。

八个维度题目分布（每个维度5题）：

- TF（技术职能型）：题目 1, 9, 17, 25, 33
- GM（管理型）：题目 2, 10, 18, 26, 34
- AU（自主型）：题目 3, 11, 19, 27, 35
- SE（安全型）：题目 4, 12, 20, 28, 36
- EC（创造型）：题目 5, 13, 21, 29, 37
- SV（服务型）：题目 6, 14, 22, 30, 38
- CH（挑战型）：题目 7, 15, 23, 31, 39
- LS（生活型）：题目 8, 16, 24, 32, 40

### 2. 排序规则

1. 按维度得分降序排列
2. 分数相同时，按固定维度顺序：TF > GM > AU > SE > EC > SV > CH > LS

### 3. 确定职业锚类型

取得分最高的前三个维度代码，用 `+` 连接作为职业锚类型。

例：TF=25, GM=23, AU=22, SE=18, EC=15, SV=20, CH=19, LS=17

排序：TF(25) > GM(23) > AU(22) > SV(20) > CH(19) > SE(18) > LS(17) > EC(15)

职业锚类型：`TF+GM+AU`

### 4. 维度详情查询

从 `references/dimensions.md` 文件中按 `code` 查询维度详情，包含：

- `code`：维度代码（如 `"TF"`）
- `name`：维度名称（如 `"技术职能型"`）
- `description`：维度描述（完整版原文）
- `questionIndexes`：该维度包含的题目索引数组

### 5. 总分计算（可选）

总分 = 八个维度得分之和（范围 40-240）

## 报告示例

下面是一组真实作答经评分脚本计算后的报告片段：

```json
{
  "assessment_id": "CAREER-ANCHOR-40-001",
  "status": "completed",
  "answered_count": 40,
  "total_questions": 40,
  "anchor_type": "TF+GM+AU",
  "dimension_scores": {
    "TF": 25,
    "GM": 23,
    "AU": 22,
    "SE": 18,
    "EC": 15,
    "SV": 20,
    "CH": 19,
    "LS": 17
  },
  "top_three_dimensions": [
    {
      "code": "TF",
      "name": "技术职能型",
      "score": 25,
      "description": "注重在特定技术或职能领域的专业成长与技能提升，追求通过应用专业知识解决问题，通常不喜欢转向一般管理职位。"
    },
    {
      "code": "GM",
      "name": "管理型",
      "score": 23,
      "description": "致力于全面管理工作，偏好承担跨部门整合责任，将组织成功视为个人工作成果。"
    },
    {
      "code": "AU",
      "name": "自主型",
      "score": 22,
      "description": "强调工作方式的自由度，希望自主安排工作习惯与生活方式，可能放弃晋升机会以保持独立性。"
    }
  ],
  "analysis": {
    "summary": "您的职业锚类型为 TF+GM+AU（技术职能型+管理型+自主型），得分最高的三个维度分别为：技术职能型（25分）、管理型（23分）、自主型（22分）。",
    "recommendations": ["技术研发岗位", "技术专家岗位", "管理岗位", "项目经理", "自由职业"]
  }
}
```

## 重要原则

- 题库必须明确给出题目编号、题干和维度归属；
- 评分逻辑必须单独写在脚本文件中，不能隐含在对话里；
- 用户提交题目后，必须返回测试结果、得分和职业锚类型；
- 若题目缺失或答案格式不合法，先要求用户补全，不要直接伪造结果；
- 维度映射必须保持一一对应；
- 同一组作答必须产出 byte-equal 的 JSON（无随机性）。

## Demo 目录结构

```text
career-anchor-assessment/
├── SKILL.md
├── references/
│   ├── algorithm.md
│   ├── questions.md          # ## 题库（40 题题库数组，运行必需：单一数据源）
│   └── dimensions.md         # ## 维度详情（8 维度详情数组，运行必需：单一数据源）
└── scripts/
    └── calculate_career_anchor.py
```

## 资源说明

- 题库（唯一数据源）：`references/questions.md` 的 `## 题库` 段，40 道职业锚测评题库（```json 代码块内为纯 JSON 数组，供评分脚本提取解析）
- 维度详情（唯一数据源）：`references/dimensions.md` 的 `## 维度详情` 段，8 个维度的详细信息（```json 代码块内为纯 JSON 数组）
- **运行前置条件（关键）**：`references/questions.md` 与 `references/dimensions.md` 是评分脚本的默认数据源，必须存在且各自的 `## 题库` / `## 维度详情` 段各含一个 ```json 代码块；脚本 `_load_data()` 优先按纯 JSON 解析、失败则提取 ```json 代码块内容（兼容 .json / .md 两种文件）。**数据只有 references 下一份拷贝，无同步问题**；修改题库/文案只需改 md 一处。
- 渲染规范：题目卡片渲染规范见本文件"WorkBuddy 视觉化交互卡片约束 → §0 题目卡片渲染规范"（固定 CSS/结构/交互行为），测评报告渲染规范见本文件"输出格式 → §R 报告渲染规范"（固定 CSS/结构）；**渲染规范直接固化在 SKILL.md 内，不依赖任何外部 HTML 模板文件**
- 算法说明：`references/algorithm.md`
- 评分脚本：`scripts/calculate_career_anchor.py`

## 交互输出要求

用户完成题目后，系统应返回：

1. 测评 ID 与名称
2. 状态（completed / incomplete）
3. 职业锚类型（前三个维度组合）
4. 八个维度的得分
5. 前三个维度的详情（含维度代码、名称、得分、描述）
6. 职业建议
7. 若未完成，给出缺失题号列表

本 skill 仅有唯一测评流程：展示 40 题 → 用户作答 → 输出完整测评报告。评分逻辑独立于题库内容；后续如需切换题库，只需替换 `references/questions.md` 文件，无需改动评分脚本。报告文案（维度描述）全部来自 `references/dimensions.md` 文件，如需更新文案，直接替换该文件即可，无需改动评分脚本。**题目卡片与测评报告的展示格式/样式由本文件内固化规范锁定，不依赖外部 HTML 模板文件**。