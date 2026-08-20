# MBTI 职业性格测评算法说明（44 题简版）

## 维度定义

MBTI 由 4 对二选一字母组成，每对（dimension pair）是同一倾向轴的两端：

| 维度对 | option1 | option2 | name1 | name2 | 说明 |
|--------|---------|---------|-------|-------|------|
| EI | E | I | 外倾 | 内倾 | 能量来源：外部社交 vs 内部独处 |
| SN | S | N | 实感 | 直觉 | 接收信息：具体事实 vs 抽象可能 |
| TF | T | F | 思维 | 情感 | 决策方式：逻辑分析 vs 价值感受 |
| JP | J | P | 判断 | 知觉 | 生活方式：计划有序 vs 灵活开放 |

每道题的两个选项（A/B）分别归属 `E/I/S/N/T/F/J/P` 中的一个字母。
本 44 题简版中，8 个字母各均匀出现 11 次（共 88 个选项）。

## 题目设计原则

- 每题二选一（A 或 B），没有中间项；
- 用户作答为 `A` 或 `B`（也接受 `Y`/`N`、`1`/`2`、`true`/`false`，统一归一为 A/B）；
- 每个选项归属一个维度字母，选中即把对应字母的计数 +1；
- 维度字母最终计数代表用户对该方向的倾向强度。

## 评分公式

### 1. 维度字母计数

```text
score[E] = count(question.option == "A" or "B" 且 option.dimension == "E" 且 用户选择了该 option)
score[I] = ... 同上，dimension == "I"
score[S], score[N], score[T], score[F], score[J], score[P] 同理
```

简化形式：

```text
score[dimension] = sum(1 for q in answered_questions
                       for opt in q.options
                       if opt.dimension == dimension and user_answer == opt.option)
```

8 个字母计数之和等于用户实际作答题数（满分 44 时，8 个字母计数和 = 44）。

### 2. 维度对百分比

每个维度对内部计算两端字母的百分比，公式：

```text
percent[option1] = score[option1] / (score[option1] + score[option2]) * 100   # 保留两位小数，四舍五入
percent[option2] = score[option2] / (score[option1] + score[option2]) * 100
```

例如：E=11, I=33 → E% = 25.00%, I% = 75.00%

### 3. 维度对结果字母

每个维度对取百分比更高的一端作为结果字母；当两端相等时取 option1（E/S/T/J）：

```text
result_letter[EI] = percent[E] >= percent[I] ? "E" : "I"
result_letter[SN] = percent[S] >= percent[N] ? "S" : "N"
result_letter[TF] = percent[T] >= percent[F] ? "T" : "F"
result_letter[JP] = percent[J] >= percent[P] ? "J" : "P"
```

### 4. 拼出 16 型人格代码

按固定顺序 EI → SN → TF → JP 拼接 4 个结果字母：

```text
dominant_type = result_letter[EI] + result_letter[SN] + result_letter[TF] + result_letter[JP]
```

例如 `E + N + F + P` → `"ENFP"`

### 5. 总分（display_score，0-100）

总分用于前端进度条/总体倾向强度展示，公式：

```text
dominant_letters = [result_letter[EI], result_letter[SN], result_letter[TF], result_letter[JP]]
display_score = round(mean(percent[dominant_letters[0..3]]) )
```

即：取 4 个维度对中"胜出端"的百分比，求平均，保留整数。例如 (75.00 + 80.00 + 60.00 + 65.00) / 4 = 70.00 → `70`。

### 6. 维度对详情（`dimension_details`）

每个维度对输出两侧的字母、名称、得分、百分比、结果字母，以及胜出端的描述（feature / traits / characteristics）。

### 7. 角色详情（`role_detail`）

依据 `dominant_type` 在 `ROLE_PROFILES` 中查表，输出：

- `name`：人格中文名（如"调停者"）
- `proportion`：该型人格在人群中的占比（小数，如 0.08 = 8%）
- `description`：人格描述长文本
- `advantages`：优势
- `disadvantages`：劣势
- `careers`：适配职业

16 型必须全部覆盖，缺一不可。

## 输出示例

```json
{
  "status": "completed",
  "dominant_type": "ENFP",
  "display_score": 70,
  "dimension_counts": {"E": 11, "I": 33, "S": 5, "N": 39, "T": 10, "F": 34, "J": 9, "P": 35},
  "dimension_pairs": [
    {"pair": "EI", "option1": "E", "name1": "外倾", "score1": 11, "percent1": 25.00,
     "option2": "I", "name2": "内倾", "score2": 33, "percent2": 75.00, "result": "I"},
    {"pair": "SN", "option1": "S", "name1": "实感", "score1": 5, "percent1": 11.36,
     "option2": "N", "name2": "直觉", "score2": 39, "percent2": 88.64, "result": "N"},
    {"pair": "TF", "option1": "T", "name1": "思维", "score1": 10, "percent1": 22.73,
     "option2": "F", "name2": "情感", "score2": 34, "percent2": 77.27, "result": "F"},
    {"pair": "JP", "option1": "J", "name1": "判断", "score1": 9, "percent1": 20.45,
     "option2": "P", "name2": "知觉", "score2": 35, "percent2": 79.55, "result": "P"}
  ],
  "role_detail": {
    "type": "ENFP",
    "name": "竞选者",
    "proportion": 0.08,
    "description": "...",
    "advantages": "...",
    "disadvantages": "...",
    "careers": "..."
  }
}
```

## 状态判定

- 全部 44 题作答：`status = "completed"`
- 未答完全：`status = "incomplete"`，输出 `missing_questions`（缺失题号列表），不得强行生成 `dominant_type` 与 `role_detail`

## 扩展说明

- 本 44 题简版题库固定，评分逻辑无需改动即可复用；
- 若需扩到 93 题完整版，只需替换 `references/mbti.md` 的 `## 题库` 段，评分逻辑无需改动；
- 算法按上文各节规则执行（计数 → 百分比 → 结果字母 → 拼接类型 → 查表输出）。
