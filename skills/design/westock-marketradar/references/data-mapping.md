# westock-marketradar 数据映射

> 结构化数据只通过 `westock-data` 获取；原文核对只通过 `westock-finsearch query` 获取；禁止 HTTP 直连和凭记忆补数。完整合规底线见 SKILL.md。

## 调用方式

```bash
westock <command> [args] [flags]
westock-finsearch query "公告标题或id"
```

## 代码格式

| 市场 | 格式 | 示例 | radar 能力 |
|---|---|---|---|
| 沪市 / 科创板 | `sh` + 6 位 | `sh600519`、`sh688981` | 完整 |
| 深市 | `sz` + 6 位 | `sz000001` | 完整 |
| 北交所 | `bj` + 6 位 | `bj430047` | 筹码可用；两融 / 陆股通按返回标注 |
| 港股 | `hk` + 5 位 | `hk00700` | 仅有限资金 / 公告信息 |
| 美股 | `us` + 代码 | `usAAPL` | 仅有限卖空 / 公告信息 |

未知代码先执行 `westock search <名称>`；多个名称同轮并发 search，不要猜代码。

## 资金分析命令

| 维度 | 命令 | 批量 | 说明 |
|---|---|---:|---|
| 行情上下文 | `westock quote <code>` | 支持逗号批量 | 用于价格、换手、流通市值等上下文 |
| 主力资金 | `westock fund flow <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` | 支持逗号批量 | A 股主力资金趋势；港股同命令返回港股资金；美股不支持 flow |
| 南下持仓（港股） | `westock fund south-holding <code>` | 单股为主 | 仅港股降级分支使用，用于补充南向资金持仓口径；无法返回时标注不适用 |
| 龙虎榜 | `westock lhb --type institution,hotmoney,activeseat` | 否 | 榜单数据，不以个股为位置参数；若标的未出现，写“未见近期龙虎榜记录” |
| 两融 | `westock fund margin <code>` | 单股为主 | 仅沪深；北交所 / 港美股标注不适用 |
| 筹码 | `westock chip <code>` | 单股为主 | 仅沪深京 A 股 |
| 北向标的池 | `westock connect --exchange sh` / `westock connect --exchange sz` | 分页 | 只判断陆股通标的池，不等同北向资金流量 |

## 事件雷达命令

| 维度 | 命令 | 批量 | 说明 |
|---|---|---:|---|
| 事件总览 | `westock events <code>` | 支持逗号批量 | 泛问事件 / 风险时先看全貌 |
| 风险明细 | `westock risk <code> --types pledge,unlock,lawsuit,specialtrade,seasonedissue` | 支持逗号批量 | 质押、解禁、诉讼、ST、增发；默认只写当前标准类型名 |
| 增发公告 | `westock notice list <code> --type 3` | 单股为主 | 配股 / 增发相关公告 |
| 股权变动公告 | `westock notice list <code> --type 4` | 单股为主 | 股权变动、增减持线索 |
| 重大公告 | `westock notice list <code> --type 5` | 单股为主 | 重组、合同、重大事项 |
| 风险公告 | `westock notice list <code> --type 6` | 单股为主 | 风险提示、处罚、诉讼等 |
| 公告全文 | `westock notice detail <notice_id>` 或 `westock-finsearch query "<notice_id或标题>"` | 否 | 有 id 时优先 detail；需要跨文档检索时用 westock-finsearch |
| 披露日历 | `westock disclosure <code>` | 单股为主 | 财报披露 / 预约披露；配合公告和事件标签识别预增 / 预减 / 扭亏 / 首亏等业绩方向 |
| 分红线索 | `westock dividend list <code> --all` | 单股为主 | 分红、除权除息线索 |
| 市场日历补充 | `westock calendar --event financial_report,dividend,trading_halt,meeting,lockup_release,rights_issue --market hs` | 市场级 | 仅用于补充日历视角，不能替代个股事件总览 |

## 并发与终止条件

- `westock search <名称>` 之后，资金命令和事件命令互不依赖，尽量同轮并发。
- 多标的对比优先使用逗号批量：`westock fund flow sh600519,sz000001`、`westock risk sh600519,sz000001 --types pledge,unlock`、`westock events sh600519,sz000001`。
- 命令报错、认证失败、代码无法解析，或业务所需维度无法返回数据时，停止当前分析并告知用户；不用其它来源补数。
- 空结果最多补查 1 次，例如扩大日期范围或缩窄事件类型；仍为空就停止并等待用户决定是否降低分析深度、更换标的或接受数据不足。

## 已知限制

| 限制 | 处理 |
|---|---|
| 龙虎榜、风险事件主要适用于 A 股 | 港美股先说明产品边界 |
| 两融仅沪深，筹码仅沪深京 A 股 | 不适用时标注，不做替代推断 |
| `westock connect` 是陆股通标的池，不是资金流量 | 北向资金判断需结合 `westock fund flow` 和标的池资格 |
| 公告 / 事件原文不在结构化列表中完整展开 | 需要原文时用 `westock notice detail <notice_id>` 或 `westock-finsearch query "<notice_id或标题>"` |

## 跨 Skill 边界

| 需求 | 入口 |
|---|---|
| 单个结构化数据查询 | `westock-data` |
| 公告 / 研报 / 新闻原文核对 | `westock-finsearch query` |
| 条件选股 / 筛选 | `westock screen condition` |
| 排行榜 / TOP | `westock screen ranking --type <指标名>` |
