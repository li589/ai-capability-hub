# 数据库结构定义

## 压缩格式（实际存储）

所有 `data/` 下的主要 JSON 文件使用列式压缩格式（`_f: "c"`），不是展开的行式格式。

### 顶层结构

```json
{
  "_f": "c",
  "c": ["col1", "col2", ...],
  "d": [[val1, val2, ...], [val1, val2, ...], ...],
  "m": {"total_count": N, "last_update": "YYYY-MM-DD", "source": "..."}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `_f` | string | 格式标识，`"c"` = 列式压缩 |
| `c` | string[] | 列名数组（schema/header） |
| `d` | array[] | 数据行数组，每行按 `c` 索引对应列值 |
| `m` | object | 元数据：total_count / last_update / source |

### 读取方式

```python
import json

with open("data/fund_managers_distilled.json", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

columns = data["c"]      # 列名
rows = data["d"]          # 数据行
meta = data["m"]          # 元数据

# 按列名取值
name_idx = columns.index("name")
first_name = rows[0][name_idx]  # 第一条记录的 name

# 转为 dict 列表
records = [dict(zip(columns, row)) for row in rows]
```

---

## 各文件列定义

### fund_managers_distilled.json（4,241 条）

列名（25 列）：

| 列名 | 类型 | 说明 |
|------|------|------|
| raw_id | string | 天天基金原始 ID |
| manager_id | string | 经理 ID |
| name | string | 姓名 |
| company_name | string | 所属公司 |
| current_fund_code | string | 当前管理基金代码 |
| current_fund_name | string | 当前管理基金名称 |
| tenure_days | int | 任职天数 |
| total_scale | float | 管理规模（亿元） |
| best_return | string | 最佳收益（%） |
| last_updated | string | 更新日期 |
| funds | object[] | 管理基金列表 `[{fund_code, fund_name}, ...]` |
| investment_style | string | 投资风格（成长型/均衡型/价值型等） |
| stock_pool | array | 重仓股 |
| bond_pool | object | 重仓债（国债/企业债/可转债） |
| fund_pool | array | 重仓基金 |
| infrastructure_investment | bool | 基础设施投资 |
| sectors | array | 重仓行业 |
| sector_description | string | 行业配置描述 |
| fund_stage | string | 基金阶段（成熟期/成长期等） |
| stage_description | string | 阶段描述 |
| investment_advice | string | 投资建议 |
| risk_warning | string | 风险提示 |
| suitable_investors | string | 适合投资者类型 |
| investment_period | string | 建议投资周期 |
| strengths | string[] | 优势标签 |

### fund_companies_distilled.json（164 条）

列名（6 列）：

| 列名 | 类型 | 说明 |
|------|------|------|
| name | string | 公司名称 |
| manager_count | int | 基金经理数量 |
| total_scale | float | 管理总规模（亿元） |
| manager_ids | string[] | 经理 ID 列表 |
| style_code | string | 主风格代码（BALANCED/GROWTH/VALUE 等） |
| alt_style_codes | string[] | 备选风格代码列表 |

### holdings_database.json（2,000 条 stub）

| 列名 | 类型 | 说明 |
|------|------|------|
| （待补全） | | 实际列定义需查看数据 |

元数据：`version: "7.2.0"`, `data_freshness: "2026-07-23"`

### manager_views.json（3,000 条 stub）

元数据：`version: "7.2.0"`, `data_freshness: "2026-07-23"`

### external_data.json（800 条 stub）

元数据：`version: "7.2.0"`, `data_freshness: "2026-07-23"`

### fund_products.json（27,128 条）

元数据：`total_count: 27128`, `last_update: "2026-06-26"`, `source: "天天基金网"`

### style_profiles.json

非压缩格式，顶层结构：`{profiles: [...], _meta: {...}}`

---

## 数据索引设计

压缩格式下，按列名查询需要先建立索引：

```python
# 基金经理索引：按公司
from collections import defaultdict

columns = data["c"]
company_idx = columns.index("company_name")
manager_by_company = defaultdict(list)
for row in data["d"]:
    manager_by_company[row[company_idx]].append(row[columns.index("manager_id")])

# 基金经理索引：按风格
style_idx = columns.index("investment_style")
manager_by_style = defaultdict(list)
for row in data["d"]:
    manager_by_style[row[style_idx]].append(row[columns.index("manager_id")])
```
