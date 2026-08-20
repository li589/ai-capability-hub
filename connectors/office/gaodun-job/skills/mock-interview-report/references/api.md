# 抽题接口参考（纯抽题，不依赖用户/面试信息）

来源：服务端面试系统线上接口
调用链：`服务端抽题接口` -> `服务端抽题接口` -> `服务端抽题逻辑`

## 接口定义

```
POST {baseUrl}/portal/v1/user/question/group/all
Content-Type: application/json
```

baseUrl 由 mcp 工具 `draw_questions` 内部管理（随部署环境自动解析），**本 skill 不直接调用该接口**，此处仅记录入参/出参契约供对齐。

## 请求体（组题请求）

| 字段 | 类型 | 说明 |
|---|---|---|
| jobId | Integer | 岗位 id（必填） |
| interviewType | String | 面试类型枚举。纯抽题仅支持 `REAL_QUESTION`（真题）/`SPECIAL_QUESTION`（专项）；**传 `COMPOSE_QUESTION`（自选组题）会报错** `GROUP_QUESTION_INTERVIEW_TYPE_ERROR`（自选组题依赖用户历史答题记录，纯抽题不支持） |
| questionList | Array | 题目配置集合，顺序即题号顺序 |
| questionList[].id | Integer | 题目配置 id，同时用于排序（sortMap：按下标生成题号 1..n） |
| questionList[].questionType | String | 题型编码（字符串形式的数字） |
| questionList[].isProbe | Boolean | 是否追问 |
| dimensionId | Integer[] | 考核维度 id 集合 |
| filterQuestionId | String[] | 需过滤（不再抽取）的题目 id 集合 |

Controller 层会强制设置 `questionCategory = STRUCTURE`，无需传入。

### 请求示例

```bash
curl --location '{baseUrl}/portal/v1/user/question/group/all' \
--header 'Content-Type: application/json' \
--data '{
  "jobId": 64066127,
  "interviewType": "REAL_QUESTION",
  "questionList": [
    { "id": 11, "questionType": "0", "isProbe": false },
    { "id": 22, "questionType": "1", "isProbe": false },
    { "id": 33, "questionType": "2", "isProbe": false }
  ],
  "dimensionId": [1,2,3,4,5,6,7,8,9],
  "filterQuestionId": []
}'
```

## 服务端抽题逻辑要点（服务端抽题逻辑）

1. 校验 interviewType，`COMPOSE_QUESTION` 直接抛 `GROUP_QUESTION_INTERVIEW_TYPE_ERROR`。
2. 生成 `groupId`（UUID 去横线）。
3. `可用题目获取` 从 ES 获取可用题目（不依赖用户最近答题记录）。
4. 按 questionList 顺序逐条抽题（`逐题抽取`）：
   - 按题型编码从可用题目中过滤；取列表第一题；若多题且 `lastGroupTime` 全部相同则随机取一题；
   - 抽中后从可用列表移除，**同一场不会重复出题**；
   - 设置 groupId、userId（纯抽题传 null）、bizId（=配置 id）、questionType、isProbe、questionNo（=sortMap 中该配置的题号）。
5. **题型为个性题（questionType=3，PERSONALITY_QUESTION）时跳过不返回**（个性化题依赖用户信息，纯抽题不支持）。
6. 返回题目数组，题数 = questionList 中非个性题配置的数量。本 skill 在其基础上截断为最多 5 题（maxQuestions）。

## 响应（直接返回题目数组，无外层包装）

| 字段 | 类型 | 说明 |
|---|---|---|
| groupId | String | 题组 id（本次抽题批次） |
| questionId | String | 题目 id |
| bizId | Integer | 业务 id（= questionList[].id） |
| questionStem | String | 题干 |
| questionType | String | 题型枚举名（实测返回枚举名字符串，如 `REGULAR_QUESTIONS`；脚本已归一化为 code + 中文名） |
| questionNo | int | 题号（按 questionList 顺序从 1 开始） |
| isProbe | Boolean | 是否追问 |
| dimensionIds | Integer[] | 本题考核维度 |
| questionRefer | String[] | 参考范例 |
| examineModule | String | 考核模块/评估要点 |
| isTrue | Boolean | 是否真题 |

## 题型枚举（QuestionTypeEnum）

| code | 说明 |
|---|---|
| 0 | 岗位特色题 |
| 1 | 英语题 |
| 2 | 专业题 |
| 3 | 个性题（纯抽题接口跳过） |
| 4 | 行业常规题 |
| 42 | 自我介绍题 |
| 43 | 主题陈述题 |
| 44 | 综合面试题 |

## 面试类型枚举（InterviewTypeEnum）

| 值 | 说明 |
|---|---|
| REAL_QUESTION | 真题 |
| SPECIAL_QUESTION | 专项 |
| COMPOSE_QUESTION | 自选组题（纯抽题不支持） |
