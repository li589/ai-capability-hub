# 诊断类别规则（Diagnose Categories）

> **来源（1:1 还原）**：
> - `PersonalResumeScoreComputeFacadeImpl#diagnoseReport`（诊断主流程）
> - `PersonalResumeScoreComputeFacadeImpl#diagnoseNoFillFields / diagnoseNoDataFields / diagnoseDescriptionSuggestFields`
> - `PersonalResumeScoreHelper#handleDiagnoseSuggest`（建议文案拼装）
> - `PersonalResumeScoreHelper#convertDiagnoseContentToScoreDetail`（GPT 结果解析）
>
> 诊断产出 3 大类问题，对应 `PersonalResumeDiagnoseTypeEnum`：`NO_DATA(0,无数据)` / `NO_FILL(1,未填写)` / `DESCRIPTION_SUGGEST(2,描述建议)`。

## 诊断主流程（diagnoseReport）

```
diagnoseReport(resumeScore):
  1. showFields = getShowFields(resumeId)          # 见下方"可见字段过滤"
  2. noFillDetails          = diagnoseNoFillFields(showFields)            # 类别 NO_FILL
  3. noDataDetails          = diagnoseNoDataFields(showFields, resumeScore) # 类别 NO_DATA
  4. descriptionSuggestDetails = diagnoseDescriptionSuggestFields(showFields, resumeScore) # 类别 DESCRIPTION_SUGGEST
  5. diagnoseDetails = unionAll(noFillDetails, noDataDetails, descriptionSuggestDetails)
  6. generateDiagnoseReport(resumeScore, diagnoseDetails)  # 落库，报告状态置为成功
```

> 注意顺序：Java 代码中**先算 NO_FILL、再算 NO_DATA、最后算 DESCRIPTION_SUGGEST**。最终报告的展示顺序不由这里决定，而由 `queryScoreDetail` 阶段的排序规则决定（见 `diagnose-output-template.md`）。

### 可见字段过滤（getShowFields）

诊断与评分的输入都是 `showFields`，过滤规则：

1. 模块维度：只保留 `moduleStatus == SHOW(1)` 的模块（`XjPersonalResumeModule`）。
2. 字段维度：只保留 `dataFieldStatus == SHOW(1)` 的字段记录（`XjPersonalResumeData`）。
3. 字段记录必须属于第 1 步筛出的显示模块。

> `moduleStatus` / `dataFieldStatus` 的赋值规则来自解析阶段 `analysisResume`，**不是**简单的"配置里 hidden/showOnPage"，必须按 `references/analysis-resume-rules.md` 还原：
> - 字段：`dataFieldStatus = SHOW ⟺ (值非空 || canHidden==false)`（有内容模块）；空模块分支为 `canHidden==false` 且非小马平台只生成 `showOnPage==true` 字段的记录。
> - 模块：不在 `visibleModuleMap[resumeType]` → HIDDEN；否则 `任一字段有值 || (!hidden && 非全字段canHidden)` → SHOW。
>
> 推论：**`canHidden==true` 的空白字段是 HIDDEN，不会进入 showFields** —— 不参与完整度分母，也不会被记 NO_FILL。

> ⚠️ **NO_DATA 空流 quirk（1:1 保留）**：`getNoDataModuleDetails` 中 `allMatch(isBlank)` 作用于"该 moduleCode 的 showFields 记录流"。若模块整体 HIDDEN（用户手动隐藏 / 不在 visibleModuleMap / 无任何记录），该流为**空流**，Java `Stream.allMatch` 对空流返回 **true** → 照样记一条 NO_DATA。即"没启用实习经历模块"也会报"【实习经历】可以为你加分哦，去完善"。

---

## 类别 1：NO_FILL（未填写）— `value=1`

**判定逻辑（diagnoseNoFillFields）**：

1. 把 `showFields` 按 `moduleCode + "-" + dataFieldCode` 分组。
2. 每组内只要**任意一条记录** `dataFieldValue` 为空白（`StrUtil.isBlank`），该字段记一条 NO_FILL。
3. 同一字段有多条记录（如 3 段实习）也只统计**一次**。

产出明细：

```json
{
  "moduleCode": "<moduleCode>",
  "fieldCode": "<dataFieldCode>",
  "diagnoseType": "NO_FILL"
}
```

> 此阶段**不填 suggestContent**；展示话术 `【{dataFieldName}】是简历中的重要信息，请完善` 在报告输出阶段统一拼装（见 `diagnose-output-template.md`）。

---

## 类别 2：NO_DATA（无数据）— `value=0`

**判定逻辑（diagnoseNoDataFields → getNoDataModuleDetails）**：

按 `resumeType`（`PersonalResumeTypeEnum`）确定检查模块组合，对每个模块：该模块下所有 `showFields` 记录的 `dataFieldValue` **全部为空白**（`allMatch isBlank`），记一条 NO_DATA。

| 简历类型 | value | code | 检查模块组合 |
|---|---|---|---|
| 零实习经验 | 0 | `noInternshipExperience` | `practicalExperience` + `professionalSkillsNonOnline` |
| 应届生求职（实习人群） | 1 | `havingInternshipExperience` | `internshipExperience` + `practicalExperience` + `professionalSkillsNonOnline` |
| 在线申请求职（网申人群） | 2 | `onlineApplication` | `internshipExperience` + `practicalExperience` + `professionalSkills`（网申版专业技能） |
| 职场人士求职（工作人群） | 3 | `havingWorkExperience` | `workExperience` + `projectExperience` + `professionalSkillsNonOnline` |

> 组合内每个模块**独立判定**——任一模块全空就各记一条，不是"组合全空才记"。

产出明细（buildNoDataDetail）：

```json
{
  "moduleCode": "<moduleCode>",
  "fieldCode": "",
  "diagnoseType": "NO_DATA",
  "suggestContent": ""
}
```

> 展示话术 `【{moduleName}】可以为你加分哦，去完善` 在报告输出阶段拼装。

---

## 类别 3：DESCRIPTION_SUGGEST（描述建议）— `value=2`

**触发条件（diagnoseDescriptionSuggestFields 的 filter）**，两个条件**同时满足**：

1. `dataFieldValue` 非空白；
2. `dataFieldCode` 命中 `ResumeScoreConfig.diagnosePromptMap`（即配置了诊断 Prompt 的字段）。

**diagnosePromptMap 的 12 个字段**（与 `references/diagnose-prompts.md` 一一对应）：

| # | moduleCode | dataFieldCode | Prompt 文件 |
|---|---|---|---|
| 1 | `internshipExperience` | `internshipExperienceDesc` | 简历2.0-诊断-实习经历.txt |
| 2 | `workExperience` | `workExperienceDesc` | 简历2.0-诊断-工作经历.txt |
| 3 | `projectExperience` | `projectExperienceDesc` | 简历2.0-诊断-项目经历.txt |
| 4 | `practicalExperience` | `practicalExperienceDesc` | 简历2.0-诊断-实践经历.txt |
| 5 | `campusActivities` | `campusActivitiesDesc` | 简历2.0-诊断-校内工作.txt |
| 6 | `competitionExperience` | `competitionExperienceDesc` | 简历2.0-诊断-比赛经历.txt |
| 7 | `trainExperience` | `trainDesc` | 简历2.0-诊断-培训经历.txt |
| 8 | `hobbySpeciality` | `hobbySpecialityDesc` | 简历2.0-诊断-爱好特长.txt |
| 9 | `selfEvaluation` | `selfEvaluationDesc` | 简历2.0-诊断-自我评价.txt |
| 10 | `applicationReason` | `applicationReasonDesc` | 简历2.0-诊断-应聘理由.txt |
| 11 | `careerPlanning` | `careerPlanningDesc` | 简历2.0-诊断-职业规划.txt |
| 12 | `suitableJob` | `suitableJobDesc` | 简历2.0-诊断-适合的工作.txt |

> 未配置 Prompt 的描述字段（如 `educationExperienceDesc` 专业课程）不进入本类别。Java 对每条字段**并发**调用 GPT；本 skill 由 `emit-llm-tasks` 组装成**单次批量任务单**（每次调用的 (prompt, 值) 二元组逐字不变、条目间互不影响，判定结果与逐条调用等价），模型一次推理产出全部 suggestions。

**单字段诊断（diagnoseSuggestField）**：

1. 组装参数：botId = `diagnoseBotId`，prompt = `diagnosePromptMap[dataFieldCode]` 对应的 Prompt 原文，content = `dataFieldValue`（**只传字段值本身**，不拼模块名）。
2. 调用 LLM，得到 `botContent`。
3. 解析（convertDiagnoseContentToScoreDetail）：
   - `botContent` 空白 → 返回 null（该字段**不出现在诊断结果中**）；
   - 按 JSON 解析为 `{"suggestion": "..."}`；`suggestion` 空白 → 返回 null（跳过）；
   - 解析出 `suggestion` → 生成明细 `{moduleCode, fieldCode, dataId, dataSort, diagnoseType: DESCRIPTION_SUGGEST, suggestContent: suggestion}`。

**LLM 输出协议**（由 Prompt 末尾 `OutputFormat` + `Addition` 约束）：

| 情况 | LLM 输出 | 处理 |
|---|---|---|
| 满足 Rules | 纯文本 `暂无修改建议` | JSON 解析失败/suggestion 为空 → **跳过，不产生明细** |
| 内容与本字段无关 | `{"suggestion":"请认真完善哦～"}` | 正常产出明细 |
| 不满足 Rules | `{"suggestion":"1. ...\n2. ..."}` | 正常产出明细 |

**建议文案拼装（handleDiagnoseSuggest，1:1）**：

按 `fieldCode` 分组后处理：

- 组内只有 **1 条**记录：
  `suggestContent = "描述建议：\n" + suggestion去掉开头换行`
- 组内有 **多条**记录（同一字段多段经历）：先按 `dataSort` 升序排序，第 i 条（从 1 开始）：
  `suggestContent = "描述建议" + i + "：\n" + suggestion去掉开头换行`

模板常量（PersonalResumeScoreHelper）：

```java
NO_DATA_TEMPLATE = "【%s】可以为你加分哦，去完善";
NO_FILL_TEMPLATE = "【%s】是简历中的重要信息，请完善";
SUGGEST_TEMPLATE = "描述建议%s：\n%s";
```

---

## 诊断明细数据结构（PersonalResumeDiagnoseDetailDTO / XjPersonalResumeScoreDetail）

| 字段 | 说明 |
|---|---|
| `moduleCode` | 模块编码 |
| `fieldCode` | 字段编码（NO_DATA 时为空字符串） |
| `diagnoseType` | 0=NO_DATA / 1=NO_FILL / 2=DESCRIPTION_SUGGEST |
| `suggestContent` | 建议内容（NO_FILL 在计算阶段不填；DESCRIPTION_SUGGEST 为拼装后的"描述建议N：..."） |
| `dataId` / `dataSort` | 仅 DESCRIPTION_SUGGEST 携带，用于同字段多条记录排序 |
| `reportId` | 所属报告 id |
