# 教育数据模型与字段语义

内部统一数据模型，用于对齐分析逻辑。**不是用户输入契约** —— 用户可以用宽表、长表、多工作表、Word 表格、试卷图片或混合材料。字段映射由模型推断。

## 核心实体

| 实体 | 关键字段 | 用途 |
|------|---------|------|
| Student | `student_id`, `student_name`, `class`, `grade`, `major`, `gender` | 学生与群体分析 |
| Assessment | `assessment_id`, `course`, `term`, `exam_type`, `full_score` | 考试/课程上下文 |
| Score | `student_id`, `assessment_id`, `subject`, `score`, `status` | 成绩分析（P0） |
| Item | `item_id`, `full_score`, `item_type`, `knowledge_point` | 试题分析 |
| ItemScore | `student_id`, `assessment_id`, `item_id`, `item_score` | 难度/区分度/错题（P1） |
| CourseObjective | `objective_id`, `objective_name`, `target_value` | 课程目标达成 |
| ObjectiveMapping | `item_id 或 component`, `objective_id`, `weight` | 考核项-目标映射 |

## 字段语义识别（模糊匹配）

| 内部字段 | 常见列名 |
|---------|---------|
| student_id | 学号、考号、编号、准考证号、ID |
| student_name | 姓名、名字、学生 |
| class | 班级、教学班、行政班、班 |
| grade | 年级、届 |
| major | 专业、系、方向 |
| gender | 性别 |
| assessment_id | 考试ID、考试编号、测评ID |
| subject | 科目、学科、课程、科 |
| score | 分数、成绩、得分、总分、总评 |
| exam_type | 考试类型、月考、期中、期末、测验 |
| term | 学期、学年、时间 |
| item_id / item_score | 题号列（如 "第1题"、"T1"、"1"、"Q1"）及对应得分 |
| item_type | 题型、类型 |
| knowledge_point | 知识点、考点 |
| full_score | 满分、总分值、卷面分 |

识别不确定且影响结果时才询问用户。

## 评分状态（关键）

分数与特殊状态**分开保存**，避免把缺考/免考当成 0 分污染统计：

```text
score:  数值 或 空
status: normal / absent(缺考) / exempt(免考) / cheating(作弊) / make_up(补考) / unknown
```

常见特殊标记：`缺考`、`缺`、`—`、`/`、`免`、`作弊`、`0(疑似缺考)`。
- 统计均分/分布时默认排除非 normal 状态，并说明排除了多少条
- 及格率分母是否含缺考需明确口径

## 评分口径统一

| 制度 | 处理 |
|------|------|
| 百分制 | 基准，直接用 |
| 150 分制 / 120 分制等 | 记录满分，需要跨制度对比时归一化到百分制或标准分 |
| 等级制（A/B/C/D、优良中差） | 需用户或规则提供等级-分数/绩点转换表；无表则按序数处理并说明 |
| GPA / 绩点 | 记录换算规则 |

跨科目、跨考试对比时，满分不同不能直接比原始分，需归一化或用标准分（Z 分数）。

## 常见表结构

1. **宽表**：一行一个学生，多列科目 → 分析多科时常需 melt 成长表
2. **长表**：一行一个"学生×科目"记录
3. **多工作表**：每个班/每次考试一个 sheet → 合并时加来源标记
4. **逐题表**：一行一个学生，列为题号 → P1 试卷分析
5. **成绩+逐题混合**：既有总分又有小分

## 常见脏数据

- 表头有合并单元格 / 多行表头 / 标题行
- 汇总行（"平均分""班级均分"混在学生行里）——需识别并剔除
- 学号被 Excel 当数字丢失前导零
- 同名学生需靠学号区分
- 分数含文本（"85（缓考）"）需拆分数值与状态
