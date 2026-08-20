# 通用列表查询快速路径

## 使用条件

对象是已注册业务模块的列表数据，且请求含"筛选 / 以上以下 / 大于小于 / 分组 / 汇总 / 合计 / 排行 / Top N / 前 N"之一时走本路径。普通单条明细、完整账单、写操作 → 回对应业务模块。

## 硬规则

1. 只经 `sh ./scripts/yc-cloud.sh` 调用（执行前先读 `runtime.md`）；`--query-plan` 只用于下方"已接入数据源"，不得加到其他命令。
2. 模型只生成 JSON 查询计划；筛选/算术/聚合/排序全由 Go CLI 执行。**禁止**临时写或跑 Python、`jq`、JS、shell 分析脚本，禁止存全量 JSON 再分析。
3. **直接跑聚合命令**（`--require-page=false`，**不加 `--output`/`--json`**）：stdout 就是排好的紧凑 markdown 表 → **原样贴给用户 + 一句话结论**。**严禁**：`--json` 再自排表、写文件、`present_files`、`read_file`、重定向、合并多项目。`--json` 仅当把结果喂给下一条命令时才用。
4. **不加 `--limit`**：query-plan 内部自动翻页取全量再聚合，手动 `--limit` 会被拒；JSON 计划里的 `limit` 是聚合结果截断数（与取数无关）。
5. **范围（项目）缺失** → **先跑 `sms-task list-projects` 拿项目清单，再调 `ask_clarification` 把每个项目作为 `options` 传入**让用户选（`options=["项目名 (id)", …, "全部项目"]`，见 SKILL.md rule 5）。**严禁没跑 list-projects、拿不到项目名就抽象问"查哪些项目"而不给 `options`**（那样前端没得选）。别默认全查；范围只预检一次，已定就不重复。用户已说清范围（含"全选"）就照办。
6. 范围确定后只执行一次命令。CLI 失败按错误停止，不改直连 API 或临时脚本。
7. **`collection sms-task preview --query-plan` 取数按页最多 500 条**：命令内部按每页 500 自动翻页拼全量再聚合（处理上限 `50000` 条）。**禁止**手动传 `--limit` 试探更大页、禁止自己写翻页循环、禁止绕过 CLI。Agent 只需发**一条** `preview --query-plan`；不要把「每页 500」误当成「全项目只能查 500 户」。

## 已接入数据源

| 意图 | 命令 | 必要范围 | 取数口径 |
|---|---|---|---|
| 欠费客户筛选 / 汇总 / 排行 | `collection sms-task preview` | `--project-id` | `--query-plan` 模式按每页 500 自动翻页，最多处理 `50000` 条项目内客户/房屋级欠费聚合行 |

只用于欠费统计分析，**不取代**"查某客户完整欠费明细"的 `checkout-desk list-arrears` / `receivable arrears-list`。

允许字段：

- number：`projectId` `houseId` `userCustomerId` `arrearsCount` `arrearsPrincipal` `arrearsLate` `arrearsAmount`
- string：`projectName` `houseName` `userName` `mobile`

## Query Plan 合同

执行顺序固定：`where → groupBy/aggregates → having → orderBy → limit → select`。

操作限制：

- number：`eq ne gt gte lt lte in`；string：`eq ne contains in`；bool：`eq ne`
- 聚合：`sum count min max avg first collectDistinct`
- **`count` 只计组内行数，禁止带 `field`**：合法 `{"op":"count","as":"行数"}`；非法 `{"op":"count","field":"userCustomerId",...}`（CLI 报 `count does not accept a field`）。要「欠费笔数」用 `sum` + `arrearsCount`，不要写成 SQL 风格的 `count(字段)`。
- 多个 `where` / `having` 均为 AND；`orderBy.direction` 只能 `asc` / `desc`；排序须加稳定次级键（如金额降序后再按 ID 升序）
- `limit` 默认 20、最大 200；禁止未声明字段、字段路径、正则、函数、脚本或额外 JSON 属性
- **表头 = `select` 的列名，务必中文**：给聚合起**中文 `as` 别名**再 `select` 这些别名（`as` 不限字符集，中文合法）。`groupBy` 原字段是英文，**别直接 `select`**；要展示它就用 `first` 起中文别名（如 `{"op":"first","field":"userName","as":"业主"}`）。`having` / `orderBy` 也用别名引用。
- **大整数 ID 不要 `select`**：`userCustomerId` / `projectId` / `houseId` 是 16 位大整数，`select` 出来会被 CLI 当 Number 渲染成**科学计数**（且精度不可靠）。**展示表不 select 原始 ID**（业主名 + 房号已够识别）；需要拿 ID 做**排序次级键**时，直接 `orderBy` 那个 `groupBy` 原字段（如 `userCustomerId`，不 `select`、不显示即可）。确需把 ID 交给下一条命令，才单独用 `--json` 取。
- **展示列用标量聚合（`first` / `sum` / `count` …），别用 `collectDistinct`**：`collectDistinct` 出的是 list，CLI 单元格**只渲染成 `…`**（嵌套结构不铺开）。要展示项目名 / 房号等就用 `first` 取一个代表值（如 `{"op":"first","field":"houseName","as":"房号"}`）。

## 欠费大户示例（照抄，改阈值 / Top N 即可；中文 `as` 别名 = 中文表头）

```bash
sh ./scripts/yc-cloud.sh collection sms-task preview --project-id <id> --require-page false --query-plan '{"version":1,"groupBy":["userCustomerId"],"aggregates":[{"op":"first","field":"userName","as":"业主"},{"op":"first","field":"projectName","as":"项目"},{"op":"first","field":"houseName","as":"房号"},{"op":"sum","field":"arrearsCount","as":"欠费笔数"},{"op":"sum","field":"arrearsAmount","as":"欠费总额"}],"having":[{"field":"欠费总额","op":"gte","value":1000}],"orderBy":[{"field":"欠费总额","direction":"desc"},{"field":"userCustomerId","direction":"asc"}],"limit":20,"select":["业主","项目","房号","欠费笔数","欠费总额"]}'
```

跑完 stdout 就是排好的中文表头紧凑表 → 原样贴出 + 一句话结论（命中总数、阈值、范围；`truncated` 时说"仅前 N 条"）。
