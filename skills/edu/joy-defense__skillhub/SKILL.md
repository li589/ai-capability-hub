```yaml
---
name: defense-thesis
description: 输入一篇论文，输出多位导师的差异化审阅意见。模拟答辩委员会的多视角评审。
argument-hint: "[论文文件路径或文本内容]"
version: "1.0.0"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---
```

## 1. 核心设计
- 这是一个多顾问协调器（multi-advisor coordinator）。输入论文后，系统会解析论文结构、提取关键信息，然后并行驱动每位导师进行评审，最后将各导师意见汇总成差异化的审阅报告。
- 流程：论文输入 → 解析论文结构 → 逐位导师并行评审（判断、管理、 persona 三个维度） → 汇总输出。

## 2. 触发短语
- /defense-thesis
- 帮我审这篇论文
- 多导师审阅
- 模拟答辩委员会评审

## 3. 协调流程（ASCII 流程图）
```
论文输入 → [Step1]解析论文结构 → [Step2]并行驱动每位导师
导师A: Judgment + Management + Persona
导师B: Judgment + Management + Persona  
导师C: Judgment + Management + Persona
→ [Step3]整合输出 → 多导师差异化审阅报告
```

## 4. 已注册导师列表
 | 代号 | 研究方向 | 审阅侧重 | 追问风格 |
 |---|---|---|---|
 | zhang  | 方法论/实验设计 | 统计严谨性、可重复性 | 精确追问、数据驱动 |
 | li | 创新性 | 新颖性、与现有工作对比 | 直接对比、挑战创新点 |
 | wang | 写作/结构 | 清晰度、逻辑流、图表 | 建设性建议 |

> 注：正式部署请把表格中的代号与具体审阅侧重点对齐，确保一致性。

## 5. Step 1: 论文解析
- 论文解析将论文内容分解为：标题（title）、摘要（abstract）、研究问题（research problem）、创新点（innovation）、方法/实验设计（methodology）、结果（results）、图表（figures/tables）、写作质量（writing quality）、参考文献（references）。
- 解析输出将用于后续的多导师评审输入结构化阶段。

## 6. Step 2: 多导师评审（并行）
- 针对每位导师，评审分为三部分：
  - Part A：Judgment（判断）
  - Part B：Management（管理，评审过程、关注点、可操作性）
  - Part C：Persona（ persona，即导师的评审风格与互动偏好）
- 评审应以并行方式进行，确保时间效率与多样化观点。

## 7. Step 3: 整合输出
- 汇总的差异化审阅报告将包含：
  - 论文信息（标题、作者、期刊/会议、提交日期）
  - 各导师意见（按代号列出，含判断、管理、 persona 三部分）
  - 共识点
  - 分歧点
  - 最高优先级修改项

## 8. 导师注册与管理命令
- /add-advisor {代号} — 添加新导师
- /remove-advisor {代号} — 移除导师
- /list-advisors — 列出所有已注册导师
- /update-advisor {代号} — 更新某导师的评审标准

## 11. 自动蒸馏命令（新增）

### /update-advisor {代号} --input <论文文本> --audio <录音文本路径>

当有新录音转写文本或审阅意见时，使用此命令自动更新对应导师的文件。

**输入规则：**
- `--audio`（必需）：录音转写文本（.txt, .json from audio_transcriber.py）
- `--input`（可选但推荐）：对应论文文本（.txt, .md, .pdf）
- 如果同时提供论文和录音，蒸馏效果更好——系统会理解"这位导师审阅这类论文时的风格"
- 如果只提供录音，也可以蒸馏，但不包含论文上下文

**⚠️ 重要：每次只更新一位导师**

蒸馏时会询问用户「这是哪位老师的审阅意见？」，用户选择后只更新该导师的文件，不会批量更新多位导师。

**工作流：**
1. 用户提供输入（录音必填，论文可选）
2. 系统询问：「这是哪位老师的审阅意见？选项：张三 / 李四 / 王五」
3. 用户选择导师
4. 如果提供了论文，解析论文结构（使用 thesis_parser.py）
5. 解析录音文本，提取导师的评审偏好与风格
6. 结合论文上下文（如果有），提炼该导师对此类论文的特有追问风格
7. 将新模式智能合并到该导师文件中（追加新内容，不覆盖原有内容）
8. 将当前版本备份到 versions/ 目录
9. 输出更新摘要
10. 将该导师的 meta.json 中 `is_trained` 字段标记为 `true`

**未更新导师的兜底策略：**
- 未被更新的导师保持原状态
- 如果某导师 `is_trained: false`（从未被蒸馏过），该导师的回复使用 `prompts/generic_advisor_style.md` 中的通用评审风格
- 通用风格提供全面的评审维度覆盖，确保即使没有个性化训练也能给出有用的评审意见

**最终输出内容（每次答辩审阅）：**
- 每位导师的个性化追问问题（使用该导师的风格/喜好生成）
- 针对每位导师的回应策略（如何准备、如何回复该导师的问题）

**示例：**
```bash
# 只更新张三导师的档案（同时提供论文和录音）
python tools/advisor_updater.py --advisor zhang --input thesis.pdf --audio review.txt

# 只更新李四导师的档案（只提供录音）
python tools/advisor_updater.py --advisor li --audio li_review.txt
```

**输入格式：**
- 论文：.txt, .md, .pdf（使用 thesis_parser.py 解析）
- 录音：.txt, .json（来自 audio_transcriber.py）

**输出：**
- 仅更新指定导师的 judgment.md、management.md、persona.md、meta.json
- versions/ 目录中的版本备份
- 更新摘要（新增条目数、修改说明）
- meta.json 中 `is_trained` 更新为 `true`

**未更新导师兜底策略：**
- 未被更新的导师保持原状态
- 如果某导师 `is_trained: false`，该导师的回复使用通用评审风格
- 通用风格确保有用的对话

## 9. 已注册导师列表（更新后）
- 张三（zhang）
- 李四（li）
- 王五（wang）

## 10. 索引与版本管理
- 版本备份在 versions/ 目录中。
- 每次更新后请创建一个新的版本条目。
