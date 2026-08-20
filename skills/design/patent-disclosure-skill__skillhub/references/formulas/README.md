# 公式推荐范式（外挂配置）

发明交底在写 **3.4.1** 前，须依据本目录配置**选题**，再填入案件符号与数值，避免临时发明抽象式子。

| 文件 | 作用 |
|------|------|
| [`paradigms.yaml`](paradigms.yaml) | 默认范式库 + 全局规则（禁装饰音、符号上限等） |
| [`../schemas/formula_plan.schema.yaml`](../schemas/formula_plan.schema.yaml) | 案件级 `formula_plan.yaml` 合同 |

## 加载顺序（后者覆盖同 `id`）

1. 仓库 `references/formulas/paradigms.yaml`
2. 环境变量 `PATENT_FORMULA_PARADIGMS` 指向的 YAML/JSON
3. 案件目录 `formula_paradigms.yaml` 或 `formula_paradigms.json`（与交底输出同级）

查看合并结果：

```bash
python tools/shared/formula_paradigms.py list
python tools/shared/formula_paradigms.py list --case-dir outputs/某案
python tools/shared/formula_paradigms.py show weighted_sum
```

校验案件公式计划：

```bash
python tools/shared/check_formula_plan.py -i outputs/某案/formula_plan.yaml
python tools/shared/check_formula_plan.py -i outputs/某案/formula_plan.yaml --eval
```

`--eval`：对可解析的简单式（`+ - * / min max`）代入 `numeric_example` 核对 `result`；求和/范数/分位等跳过并警告。  
`chemistry` 标签或 `\ce{` / 反应箭头：检查简单反应式原子守恒。`physics`/`si`：符号表单位族粗检（警告）。

## 如何扩展一条范式

在覆盖文件中追加（保留 `version` / 可选 `rules`）：

```yaml
version: 1
paradigms:
  - id: my_shop_floor_oee
    name_zh: 产线 OEE 合成
    tags: [score, manufacturing]
    when_zh: 可用率×表现×质量
    latex: 'OEE = A \\cdot P \\cdot Q'
    notes_zh: A,P,Q ∈ (0,1]
```

`id` 用小写+下划线；写清 `when_zh` / `notes_zh`，否则易被误选。  
`combos` 可同样追加，供 Agent 在调度/检索等场景一次选多式。

## 成文纪律（摘要）

- `formula_plan.paradigm_ids`（及可选 `combo_id`）必须∈合并后的库。  
- 默认 `rules.forbid_accents: true`：正文不要用 `\tilde`/`\hat`/`\bar` 等；平滑用 `ema_smooth` + 符号 `A`。  
- 须含可代入数值例；打分与限频触发尽量分式，参见 combo `match_then_rate_limit`。
