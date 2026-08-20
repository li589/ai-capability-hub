# 数据采集与降级策略

本文件承接 westock-brief 的数据采集细节。执行前仍以 `SKILL.md` 的核心护栏为准：资讯搜索必须执行，自选股涨跌幅只能来自 `westock quote`。

## 数据源优先级

| 数据类型 | 首选入口 | 替代入口 | 全部失败时 |
|---|---|---|---|
| 金融资讯 / 研报 / 宏观事件 | `westock-finsearch query “关键词组1” “关键词组2” “关键词组3”` | A股 `westock news list sh000001,sz399001,sz399006 --limit 10`；港股 `westock news list hkHSI,hkHSTECH --limit 10`；美股 `westock news list usDJI,usIXIC --limit 10` | Dashboard 标注“资讯搜索暂不可用，本期仅基于行情数据” |
| 指数 / 个股涨跌幅 | `westock quote <code1,code2,...>` | 遇到报错或不确定代码时，先用 `westock search <名称> --type index` 查代码 | 跳过行情区块或标注缺失，不能编造 |
| 外汇 / 大宗商品 | `westock quote fxDINIW,fxCNH,fuCL,fuGC` | 遇到报错或不确定品种时，先用 `westock search <名称> --type forex` 或 `--type futures` 查代码 | 跳过该品种，不能编造价格或涨跌幅 |
| 事件日历 | `westock calendar --date YYYY-MM-DD` | `westock ipo --market hs` 或搜索结果补充 | 无事件则跳过区块 |
| 核心股新闻 | `westock news list <code> --limit 5` | 资讯搜索中与该股票相关结果 | 无新闻则省略消息维度 |
| 资金流向 | `westock fund flow <同市场code1,code2,...>`（跨市场分开查） | 搜索结果中的资金主题 | 不展示资金维度 |
| 市场涨跌统计 / 两融 | `westock market-overview --type trade,updown,margin` | 搜索结果中的涨跌统计、两融或杠杆资金主题 | 不展示涨跌家数、涨跌停或两融 / 杠杆资金维度 |
| 板块榜 / 北向热门板块 | `westock sector ranking` | 搜索结果中的板块轮动或北向主题 | 不展示板块领涨领跌和北向偏好维度 |
| 龙虎榜 | `westock lhb --type institution,hotmoney` | 搜索结果中的龙虎榜主题 | 跳过龙虎榜区块 |

## 并发与批量

互不依赖的数据可以同轮并发：

- 盘前：资讯搜索、指数 / 全球资产行情、事件日历、自选股列表。
- 盘后：指数行情、指数 K 线、资讯搜索、自选股列表、市场涨跌统计、板块榜、龙虎榜总览。
- 拿到自选股代码后，再批量查询全部自选股行情。

批量规则：

```bash
# 多主题资讯搜索，一次传入至少 3 组关键词
westock-finsearch query "A股 盘前 利好 利空" "美股收盘 今日" "人民币汇率 美元指数 离岸"

# 指数或自选股行情，一次传入逗号分隔代码
westock quote sh000001,sz399001,sh000300,sz399006,sh000688,hkHSI,hkHSTECH,usINX,usIXIC,usDJI
westock quote fxDINIW,fxCNH,fuCL,fuGC
westock quote sh600519,hk00700,usAAPL

# 核心股资金流向支持同市场逗号批量；跨市场分开查
westock fund flow sh600519
westock fund flow hk00700
```

依赖关系：

- `openclaw cron enable/edit` 依赖 `openclaw cron list` 返回任务 ID，必须串行。
- 个股新闻、资金、K 线依赖核心股筛选结果，必须在筛选后执行。
- `westock market-overview --type trade,updown,margin` 和 `westock sector ranking` 不依赖自选股代码，可与盘后第一轮数据同轮执行。

用途边界：

- `westock market-overview --type trade,updown,margin` 用于判断涨跌家数、涨跌停、成交额与杠杆资金情绪；没有该数据时只省略对应维度，不用其它行情字段推断。
- `westock sector ranking` 用于板块领涨领跌、资金流入和北向热门板块；没有该数据时跳过板块和北向偏好维度，不编造北向净流入金额。

## 搜索策略

- 盘前和盘后都至少搜索 3 个主题。
- A 股 / 港股用中文关键词；全球市场 / 美股可用英文关键词。
- 用户关注领域要动态追加关键词，例如“半导体”追加“半导体 芯片 行业 最新消息”。
- 首次搜索为空或明显不足时，最多补查 1 轮同义关键词；仍不足则标注缺失，不继续试错。
- 搜索结果只提炼与 Dashboard 有关的 3-5 条证据，不复制全文。

## fallback 规则

默认入口失败时，按以下顺序处理：

1. `westock-finsearch query` 可用：必须优先使用。
2. `westock-finsearch query` 不可用：按市场尝试 A股 `westock news list sh000001,sz399001,sz399006 --limit 10`、港股 `westock news list hkHSI,hkHSTECH --limit 10`、美股 `westock news list usDJI,usIXIC --limit 10`（旧市场资讯入口已弃用）。
3. 以上全部失败：Dashboard 标注“资讯搜索暂不可用，本期仅基于行情数据”。

替代工具成功时视为正常资讯来源，不写“降级”“异常”或“数据质量较差”。只有所有搜索手段均失败时才标注缺失。

## 数据缺失处理

- 单个指数无数据：跳过该指数；全部指数无数据则跳过指数区块。
- 标普 500、纳斯达克、道指优先使用 `westock quote usINX,usIXIC,usDJI`；查询失败或遇到新的美股指数时，先用 `westock search <名称> --type index` 查代码，仍查不到再如实标注缺失。
- 无自选股：跳过核心自选股区块，提示用户添加自选股。
- 自选股列表来自 memory 或对话上下文：在 Dashboard 中标注“基于上次已知自选股，可能不是最新”。
- 核心股某一维度无数据：省略该维度，不写“暂无消息”“无明显变化”填充。
- 美股不支持 `westock fund flow` 时，资金维度跳过；不要用其它字段拼凑。
- `westock market-overview --type trade,updown,margin` 不可用时，跳过涨跌统计和两融 / 杠杆资金维度；不要用行情涨跌幅推断两融变化。
- `westock sector ranking` 不可用时，跳过板块表现和北向偏好维度；不要用新闻标题编造板块涨跌幅或北向金额。

## 自选股行情来源纠偏

- A 股、港股、美股一视同仁：拿到全部自选股代码后，必须用 `westock quote code1,code2,...` 一次查全。

## 禁止行为

- 不执行资讯搜索就输出报告。
- 只搜索 1 个主题就输出报告。
- 将 `westock news list <指数代码> --limit 10` 写成默认首选搜索入口；它只在 `westock-finsearch query` 不可用时使用（旧市场资讯入口已弃用）。
- 直接调用旧市场资讯命令、旧行情命令或裸子命令；只使用 `SKILL.md` 稳定命令集列出的完整入口。
