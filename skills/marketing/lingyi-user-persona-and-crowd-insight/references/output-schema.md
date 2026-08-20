# 用户画像与人群洞察 · 输出数据模型（JSON Schema）

> **单一事实源**。agent 生成 JSON 时逐字段照填；`render_output.py` 按此契约校验。
> 任何字段定义冲突时，以本文件为准，SKILL.md 与 render_output.py 不得与之矛盾。

## 顶层结构

```json
{
  "conclusion": "string — 一句话结论",
  "maturity": { ... },
  "dimensions": [ ... ],
  "tag_system": { ... },
  "segments": [ ... ],
  "personas": [ ... ],
  "applications": [ ... ],
  "insights": { ... },
  "projects": [ ... ],
  "assumptions": ["string"],
  "missing_data": ["string"]
}
```

## 字段定义

### conclusion
- 类型：`string`，必填，非空
- 含义：一句话结论——画像建设核心方向 + 最该先建的标签/分群/洞察

### maturity
- 类型：`object`，必填

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `score` | `number` | **1.0–5.0**，保留 1 位小数；**必须 = dimensions 六项 score 的算术平均** | 画像就绪度 |
| `stage` | `string` | 枚举：`起步期` \| `成长期` \| `成熟期` \| `卓越期`；由 score 决定（1.0–1.9→起步，2.0–2.9→成长，3.0–3.9→成熟，4.0–5.0→卓越） | 阶段定性 |
| `summary` | `string` | 非空 | 一句话阶段说明 |

### dimensions
- 类型：`array`，必填，**恰好 6 项**
- 6 项的 `name` 必须依次为：`数据基础`、`标签体系`、`分群建模`、`画像刻画`、`应用落地`、`治理迭代`（顺序固定）

每项结构：

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `name` | `string` | 枚举（上述 6 个，顺序匹配） | 维度名 |
| `status` | `string` | 非空 | 现状判断 |
| `current_value` | `string` | 可为「待补」 | 关键指标当前值 |
| `benchmark` | `string` | 可为「—」 | 行业基准/参考 |
| `problem` | `string` | 非空 | 主要问题 |
| `impact` | `string` | 非空 | 影响 |
| `score` | `int` | **1–5** | 成熟度评分 |
| `priority` | `string` | 枚举：`P0` \| `P1` \| `P2` | 优先级 |

### tag_system
- 类型：`object`，必填

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `layers` | `array` | **≥4 项**；`layer` 枚举为**标准 CDP 六类**：`基础属性` \| `行为` \| `消费价值` \| `生命周期` \| `渠道来源` \| `预测`；**至少覆盖 4 类**（对标 CDP/神策/袋鼠云标准业务域分类） | 标签分层 |
| `key_tags` | `array` | **≥3 项**；优先级 P0/P1/P2，**≥3 项时不能全 P0** | 优先级标签 |

`layers[].` 子字段：`layer`（枚举）/ `purpose`（非空）/ `example_tags`（非空）/ `data_source`（非空）。
`key_tags[].` 子字段：`tag`（非空）/ `definition`（非空）/ `rule`（非空）/ `priority`（枚举 P0|P1|P2）。

> 标签层统一用标准 CDP 六类（基础属性/行为/消费价值/生命周期/渠道来源/预测），不自行拆分"交易/偏好/价值"凑数。详见 [`tagging-rules.md`](tagging-rules.md) 轴②。

### segments
- 类型：`array`，必填，**≥3 项**

每项：

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `name` | `string` | 非空 | 分群名 |
| `definition` | `string` | 非空 | 分群定义 |
| `rule` | `string` | 非空，**必须含量化标记**（含数字 / 天 / 次 / Top / 待校准） | 判定规则 |
| `scale_estimate` | `string` | 非空 | 规模占比估算 |
| `value` | `string` | 非空 | 价值定位 |

### personas
- 类型：`array`，必填，**3–5 项**

每项：

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `name` | `string` | 非空 | 画像名（鲜活命名，如"精打细算的复购妈妈"） |
| `snapshot` | `string` | 非空 | 画像快照（人口统计/一句话画像） |
| `behaviors` | `string` | 非空 | 行为特征 |
| `needs` | `string` | 非空 | 需求 |
| `pain_points` | `string` | 非空 | 痛点 |
| `touchpoints` | `string` | 非空 | 触点偏好 |
| `value_potential` | `string` | 非空 | 价值潜力 |
| `linked_segment` | `string` | 非空，**必须在 `segments[].name` 中出现** | 关联分群 |

### applications
- 类型：`array`，必填，**≥3 项**

每项：

| 子字段 | 类型 | 约束 |
|---|---|---|
| `scenario` | `string` | 非空（推荐分群/精准营销/内容分发/产品决策/运营触达 等） |
| `how_to_use` | `string` | 非空 |
| `target` | `string` | 非空（关联画像/分群） |
| `metric` | `string` | 非空 |

### insights
- 类型：`object`，必填

人群洞察与动作回路——把画像资产闭环到可执行运营动作。含三个子数组：

#### opportunity_matrix（人群机会矩阵）
- 类型：`array`，必填，**≥3 项**

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `segment` | `string` | 非空，**必须在 `segments[].name` 中出现** | 目标分群 |
| `value_level` | `string` | 枚举：`高` \| `中` \| `低` | 价值定位 |
| `growth_potential` | `string` | 枚举：`高` \| `中` \| `低` | 增长潜力 |
| `opportunity_type` | `string` | 非空（如核心增长/价值守护/成长加速/召回决策/低优放弃） | 机会类型 |
| `rationale` | `string` | 非空 | 定位理由 |

#### action_map（洞察→动作映射）
- 类型：`array`，必填，**≥3 项**

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `insight` | `string` | 非空 | 洞察描述 |
| `target_segment` | `string` | 非空，**必须在 `segments[].name` 中出现** | 目标分群 |
| `action` | `string` | 非空 | 运营动作 |
| `channel` | `string` | 非空（如企微1v1/社群/短信/App/导购） | 触达渠道 |
| `expected_metric` | `string` | 非空，**必须含量化标记**（含数字 / % / 天 / 次 / 率） | 预期指标 |
| `priority` | `string` | 枚举 `P0` \| `P1` \| `P2`；**≥3 项时不能全 P0** | 优先级 |

#### priority_scores（机会优先级评分）
- 类型：`array`，必填，**≥3 项**

| 子字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `opportunity` | `string` | 非空，**应与 opportunity_matrix[].opportunity_type 或 action_map[].insight 对应** | 机会名 |
| `score` | `int` | **1–5** | 优先级得分 |
| `reasoning` | `string` | 非空 | 评分理由 |

### projects
- 类型：`array`，必填，**≥3 项**

每项：`name` / `priority`(P0|P1|P2) / `input` / `output` / `owner_role` / `dependency`（均非空）。

### assumptions
- 类型：`array[string]`，必填，**≥1 项**，每项非空

### missing_data
- 类型：`array[string]`，必填，**≥1 项**，每项非空

## 交叉校验规则

1. `maturity.score` = `dimensions` 六项 `score` 的算术平均，**偏差 ≤ 0.2**。
2. `maturity.stage` 与 `maturity.score` 分段一致。
3. `dimensions` 的 6 项 `name` 必须按固定顺序，不重不漏。
4. `tag_system.layers` ≥4 项，且 `layer` 覆盖标准 CDP 六类（基础属性/行为/消费价值/生命周期/渠道来源/预测）中**至少 4 类**。
5. `segments` 每项 `rule` **必须含量化标记**（数字 / 天 / 次 / Top / 待校准），禁纯定性。
6. `personas` **3–5 项**，每项 `linked_segment` 必须在 `segments[].name` 中出现（persona-分群一致性）。
7. `projects` **≥4 项时**，不能全部 P0（至少 1 项 P1 或 P2）；`key_tags` **≥3 项时**同理不能全 P0。
8. `insights.opportunity_matrix` 每项 `segment` 必须在 `segments[].name` 中出现（洞察-分群一致性）。
9. `insights.action_map` 每项 `target_segment` 必须在 `segments[].name` 中出现；`expected_metric` **必须含量化标记**（数字 / % / 天 / 次 / 率），禁纯定性。
10. `insights.action_map` **≥3 项时**不能全 P0；`insights.priority_scores` 每项 `score` 为 1–5 整数，`opportunity` 应与 `opportunity_matrix[].opportunity_type` 或 `action_map[].insight` 对应。

## 可选：`report` 块（HTML 报告呈现层，不强制）

`render_report.py` 渲染白皮书 HTML 时，若 JSON 顶层附带 `report` 块，封面 / 关键数据 / 执行摘要会更丰富；**不附带也会从 dimensions/projects 自动派生**，不影响产出。`render_output.py`（md）会忽略此块，不影响 md 校验。

```json
"report": {
  "title": "封面标题",
  "subtitle": "封面副标题（一句话）",
  "kpis": [ { "num": "9200万+", "label": "累计会员" } ],
  "exec": {
    "findings": [ { "icon": "📈", "title": "关键发现标题", "text": "一句话说明" } ],
    "recs":     [ { "pri": "P0", "title": "建议标题",   "text": "一句话说明" } ]
  }
}
```

派生兜底（未提供 `report` 块时）：`title/subtitle` 用 conclusion；`kpis` 从 maturity + dimensions 的 current_value 派生；`exec.findings` 从 score≤3 的 dimensions 派生（维度名 + problem + impact）；`exec.recs` 从 priority=P0 的 projects 派生（项目名 + output）。
