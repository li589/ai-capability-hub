# 六维评分规则（Scoring Rubric）

> **来源（1:1 还原）**：`评分计算逻辑` 及其 6 个 `computeXxxScore` 方法、`模型评分调用逻辑`、`资质分计算逻辑`。
>
> 总分 = 6 个维度得分直接求和（`sumScore = completeScore + descriptionScore + learningAbilityScore + professionalAbilityScore + creativeLeadershipScore + careerAbilityScore`）。

## 权重配置（真实值，已落盘）

所有权重/映射来自 `references/resume-score-config.json`（原样复制自 服务端评分配置 的真实配置）。

`moduleScoreMap`（6 维占比权重，合计 100）：

| 维度 | key | 权重 |
|---|---|---|
| 简历完整度 | `resumeComplete` | **20** |
| 经历描述 | `experienceDesc` | **50** |
| 学习能力 | `learningAbility` | **15** |
| 专业能力 | `professionalAbility` | **5** |
| 创新领导力 | `creativeLeadership` | **5** |
| 职场能力 | `workplaceAbility` | **5** |

所有乘除均为 **Java int 整数运算**（先乘后除、结果截断取整）。

> ⚠️ **注意**：`professionalAbilityScoreMap` / `creativeLeadershipScoreMap` / `workPlaceScoreMap` 的**实际配置值与 Java 代码注释不一致**（注释写 8/6/4、9/7/5/3，实际配置是 9/8/7、9/8/7、9/7/5/4）。**一律以本文件的真实配置值为准**。

---

## 维度 1：简历完整度（computeCompleteScore）

```java
return filledShowFields.size() * moduleScoreMap.get(RESUME_COMPLETE) / allShowFields.size();
```

- 分子：`showFields` 中 `dataFieldValue` 非空白的**记录数**（按 `XjPersonalResumeData` 行数计，同一字段 3 段实习算 3 条）。
- 分母：`showFields` 总记录数。
- 权重 key：`resumeComplete` = **20**。
- 异常 → 返回 0。

## 维度 2：经历描述（computeDescriptionScore，走 GPT 评分）

```java
averageScore = 各模块 GPT 分中 score>0 的均值;
return (int)(averageScore * moduleScoreMap.get(EXPERIENCE_DESC) / 100);
```

- 模块分来自 `getScoreFromGpt`（**一次** GPT 调用，不是逐字段调用），协议详见 `diagnose-prompts.md` "经历描述评分（getScoreFromGpt）" 一节：
  - 输入拼接：按 `scoreGptConfig.fieldList`（moduleName/moduleCode/dataFieldCode）组装，隐藏模块跳过；每个字段拼 `模块名{序号}：\n{字段值}\n`；
  - GPT 返回 `{"score": {"<模块名>": <int>}}`，按 moduleName→moduleCode 映射回填；
  - 只对 `score != null && score > 0` 的模块求均值；无有效模块分 → 返回 0。
- 权重 key：`experienceDesc` = **50**；除以 `Constants.ONE_HUNDRED = 100`。即 `经历描述分 = GPT模块均分 / 2`（int 截断）。
- 任何异常 → 返回 0。

## 维度 3：学习能力（computeLearningAbilityScore）

```java
qualificationScore = max(getQualificationScore(qualification));  // 取所有学历记录中的最高分
return qualificationScore * moduleScoreMap.get(LEARNING_ABILITY) / 10;  // Constants.TEN
```

- 只取 `dataFieldCode == qualification` 的记录，取**最高**学历分；无记录 → 0。
- **注意：代码未使用 `classRank`（成绩排名）**，尽管注释提到"学历分+成绩排名分"且配置中存在 `classRankScoreMap`。1:1 还原时不计入。
- ⚠️ **精确匹配的前置条件**：表中左列是**入库标准值**。Java 侧的 LLM parser 会把学历输出为枚举原文，因此 skill 在**解析阶段**就必须把自由文本归一化（"本科"→"大学本科"、"硕士"→"硕士研究生"、"大专"→"大学专科"，完整映射见 `analysis-resume-rules.md` §2.1）。**拿着"本科"原文来做这张表的精确匹配，永远得 0 分——这是曾造成总分差 10 分的真实缺陷。**
- 学历值 → 分数的映射链（服务端学历映射表 + 配置 `qualificationScoreMap`）：

| 简历中的学历值（必须完全匹配） | map key | 分值 |
|---|---|---|
| 博士研究生 | `doctor` | 10 |
| MBA | `mba` | 9 |
| 硕士研究生 | `master` | 8 |
| 大学本科 | `undergraduate` | 7 |
| 大学专科 | `specialist` | 6 |
| 高中 | `highSchool` | 3 |
| 初中 | `juniorHighSchool` | 配置中无此 key → **0** |
| 小学 | `primarySchool` | 配置中无此 key → **0** |
| 其他/未匹配 | `""` | 0 |

- 例：大学本科 → 7 × 15 / 10 = **10**（int 截断）；硕士研究生 → 8 × 15 / 10 = **12**。
- 权重 key：`learningAbility` = 15；除以 `Constants.TEN = 10`。
- 异常 → 返回 0。

## 维度 4：专业能力（computeProfessionalAbilityScore，三项命中制）

命中判定（每类内任一字段非空白即命中 1 次，`findAny`）：

| 类别 | 命中字段（任一非空） |
|---|---|
| 语言 | `languageClassify` / `languageDesc` / `languageSkill` |
| 职业资格 | `certificateName` / `certificateDesc` / `qualificationCertificate` |
| 软件操作 | `softwareName` / `softwareDesc` / `softwareOperation` |

查表 `professionalAbilityScoreMap`（命中数 → 基础分，**真实配置值**）：

| 命中数 | 基础分 |
|---|---|
| 3 | 9 |
| 2 | 8 |
| 1 | 7 |
| 0 | 0 |

```java
return score * moduleScoreMap.getOrDefault(PROFESSIONAL_ABILITY, 0) / 10;
```

- 权重 key：`professionalAbility` = 5。例：3 项全中 → 9 × 5 / 10 = **4**（int 截断）。异常 → 0。

## 维度 5：创新领导力（computeCreativeLeadershipScore，四类模块命中制）

命中判定（每个模块内任一字段非空白即命中 1 次，`findAny`）：

1. `projectExperience`（项目经历）
2. `practicalExperience`（实践经历）
3. `competitionExperience`（比赛经历）
4. `campusActivities`（校内活动）

查表 `creativeLeadershipScoreMap`（命中类数 → 基础分，**真实配置值**）：

| 命中类数 | 基础分 |
|---|---|
| 4 | 9 |
| 3 | 9 |
| 2 | 8 |
| 1 | 7 |
| 0 | 0 |

```java
return score * moduleScoreMap.getOrDefault(CREATIVE_LEADERSHIP, 0) / 10;
```

- 权重 key：`creativeLeadership` = 5。例：中 2 类 → 8 × 5 / 10 = **4**。异常 → 0。

## 维度 6：职场能力（computeCareerAbilityScore，总月数阶梯）

**月数计算（computeCareerAbilityMonths）**——实习与工作分别计算后相加：

1. 取 `internshipStartTime` / `workStartTime` 非空记录；
2. 按 `dataId` 配对同一条记录的 endTime（`internshipEndTime` / `workEndTime`）；**无配对结束时间的记录不计月数**；
3. 起止时间按 `yyyy-MM` 解析，每段月数 = `betweenMonth(start, end, true) + 1`（含起止月）；解析失败该段跳过；
4. `months = 实习总月数 + 工作总月数`。

查表 `workPlaceScoreMap`（**真实配置值**）：key 格式 `"下限--上限"`，命中条件为 **`months > 下限 && months <= 上限`**（首个命中即停）：

| 配置 key | 区间（月） | 基础分 |
|---|---|---|
| `0--6` | 0 < X ≤ 6 | 4 |
| `6--12` | 6 < X ≤ 12 | 5 |
| `12--24` | 12 < X ≤ 24 | 7 |
| `24--99999999` | X > 24 | 9 |
| — | 无数据（0 个月） | 0（`0 > 0` 不成立，不匹配任何区间） |

```java
return score * moduleScoreMap.getOrDefault(WORKPLACE_ABILITY, 0) / 10;
```

- 权重 key：`workplaceAbility` = 5。例：共 8 个月 → 5 × 5 / 10 = **2**（int 截断）。异常 → 0。

---

## 总分与落库

```java
sumScore = completeScore + descriptionScore + learningAbilityScore
         + professionalAbilityScore + creativeLeadershipScore + careerAbilityScore;
// 更新 XjPersonalResumeScore.score = sumScore, runStatus = SUCCESS(1)
```

- 与诊断报告（diagnoseReport）是**两条并行异步链路**：分数链路与诊断链路互不影响，各自异常时仅把对应状态置为成功（容错，不阻断）。
- 报告阶段的分数区间话术（title/describe/beatPercent）见 `diagnose-output-template.md`。
