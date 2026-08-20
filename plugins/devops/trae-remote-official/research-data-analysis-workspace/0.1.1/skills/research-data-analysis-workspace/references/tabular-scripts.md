# 通用表格脚本

仅在用户提供 CSV、TSV 或 Excel，且结构盘点或重复转换值得复用时使用。简单表格、非表格数据、领域专用格式或一次性小计算直接处理，不为调用脚本而调用脚本。

## 1. 结构盘点

`scripts/inspect_tabular_data.py` 只读输入，输出结构化 JSON：表规模、字段类型候选、缺失、唯一性、完全重复、候选缺失编码、数值范围以及候选主键/分类字段。所有判断都是候选，不自动确定变量语义。

```bash
python3 scripts/inspect_tabular_data.py data.csv --output work/dataset_profile.json
python3 scripts/inspect_tabular_data.py workbook.xlsx --all-sheets --output work/dataset_profile.json
```

- 默认不写出原始示例值；只有确有必要且隐私允许时使用 `--include-examples`。
- 大文件可传 `--max-rows N`；JSON 中会标记 `truncated`，不得把抽样盘点当全量计数。
- 结果用于辅助建立数据字典和提出必要问题，不直接决定缺失编码、主键或分析单位。

## 2. 显式标准化

`scripts/normalize_research_data.py` 根据 JSON 配置生成派生表，不覆盖原始文件。只支持明确声明的字段重命名、字符串去空格、缺失编码替换、类型转换、宽转长、完全重复删除和排序。

```json
{
  "input": {
    "path": "data/raw.xlsx",
    "sheet": "Sheet1",
    "read_options": {"dtype": {"受试者编号": "string"}}
  },
  "output": {
    "path": "output/derived.csv",
    "summary": "output/normalization_summary.json"
  },
  "rename": {
    "受试者编号": "subject_id",
    "访视日期": "visit_date",
    "指标值": "value"
  },
  "trim_strings": true,
  "missing_values": {
    "*": ["NA", "N/A"],
    "value": [-99]
  },
  "types": {
    "subject_id": "string",
    "visit_date": {"type": "date", "errors": "raise", "format": "%Y-%m-%d"},
    "value": {"type": "numeric", "errors": "coerce"}
  },
  "drop_exact_duplicates": false,
  "sort_by": ["subject_id", "visit_date"]
}
```

相对路径以配置文件所在目录为基准。类型转换默认 `errors: "raise"`；只有已经决定无法解析值应转为缺失时才显式使用 `coerce`。缺失编码和完全重复删除也必须显式配置，脚本不根据当前取值自动替用户裁定。

## 边界

- 脚本不选择统计方法、不解释字段、不决定纳排、不生成科研结论。
- 不把教学项目中的学生、成绩、考试状态或阈值带入科研数据。
- 不包含交付校验器、HTML 渲染器或图表样式。
- 中间 JSON 和标准化摘要按需保留，不默认塞入用户主报告。
