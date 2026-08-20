# a-share-paper-trading

华泰证券 A 股模拟交易 OpenClaw skill —— 让 LLM 用自然语言完成 A 股模拟买卖、行情查询、账户管理等操作。

通过本 skill,LLM 可以理解用户的交易意图("买 100 股茅台"、"今天赚了多少"、"撤掉所有平安的挂单"),并通过华泰模拟交易服务执行。所有金额单位为元、所有枚举为语义字符串、所有响应结构统一,对模型友好且对人类可读。

## 安装

前提：Python 3.9 或以上（系统 Python 需已安装 `requests` 包）。

```bash
clawhub install a-share-paper-trading
```

或克隆本仓库到 OpenClaw skills 目录后,通过 OpenClaw 自动识别。

## 配置

使用前需配置以下环境变量:

| 变量 | 必填 | 说明 |
|---|---|---|
| `PAPER_TRADING_API_URL` | 否 | 华泰模拟交易服务地址（默认 `https://ai.zhangle.com`） |
| `PAPER_TRADING_BASE_URL` | 否 | 网关路径前缀（默认 `/edge/entry/gate`） |
| `HT_APIKEY` | 是 | 华泰颁发的 API Key |
| `PAPER_TRADING_TIMEOUT_MS` | 否 | 请求超时(毫秒,默认 5000) |

```bash
export HT_APIKEY="<your-api-key>"
```

> API Key 获取:请联系华泰证券获取模拟交易服务的认证密钥。

## 工具一览

9 个工具,按职责切分:

| 工具 | 类别 | 说明 |
|---|---|---|
| `searchStock` | 解析 | 按名称/代码/拼音搜股票,输出标准 stockCode |
| `getQuote` | 行情 | 实时价格、涨跌停、买卖一档 |
| `getAccountBalance` | 账户 | 资金总览 |
| `getPositions` | 账户 | 持仓明细 |
| `submitOrder` | 交易 | 提交委托(含校验) |
| `cancelOrder` | 交易 | 按单号撤单 |
| `cancelAllPendingOrders` | 交易 | 一键撤单 |
| `listPendingOrders` | 查询 | 当日未成交委托 |
| `listTradeHistory` | 查询 | 历史成交 |

详细参数、返回字段、复述提示见 [`SKILL.md`](./SKILL.md)。

## 直接调用脚本

OpenClaw 内核会按 `SKILL.md` 中的"**执行**"指令调用本 skill。所有工具走统一入口:

```bash
python3 a_share_paper_trading.py <toolName> [args]
```

开发者也可直接命令行调用:

```bash
# 搜索股票
python3 a_share_paper_trading.py searchStock --query 茅台

# 查行情(必须同时给 stockCode 和 exchange)
python3 a_share_paper_trading.py getQuote --stock-code 600519 --exchange SH

# 模拟买入(market 单)
python3 a_share_paper_trading.py submitOrder --direction buy --stock-code 601318 \
    --exchange SH --quantity 200 --order-type market

# 查持仓
python3 a_share_paper_trading.py getPositions

# 查看某个工具的参数说明
python3 a_share_paper_trading.py submitOrder --help
```

所有调用输出统一的 JSON 结构 `{ ok, data, error }`,详见 SKILL.md "响应结构"段。

## 设计原则

### 单位统一
所有金额"元"、所有比例百分数形式、所有数量"股"、所有时间 ISO 8601。后端做完单位转换,模型不必处理放大整数或单位换算。

### 枚举语义化
不用魔数。`exchange: "SH"` 比 `市场代号: 1` 对模型友好得多——前者无歧义,后者每次都要查表。`direction`、`orderType`、`orderStatus` 等所有枚举值均为语义字符串。

### 复合主键 (stockCode, exchange)
A 股不同市场可能存在相同代码(如 SH 000001 是上证指数、SZ 000001 是平安银行),单凭代码不足以唯一确定标的。交易类工具必传 exchange;查询过滤类如传 stockCode 则必须同时传 exchange。

### 工具单一职责
按动词语义切分:查未成交和查历史是两个工具,撤单和一键撤单是两个工具。模型选工具时按用户意图直接命中。

### 错误结构化 + 可执行 hint
`error.category` 让模型立刻知道错误性质(认证/校验/业务/网络),决定是否重试;`error.hint` 是可直接给用户的下一步建议。

### 复述提示代替固定摘要
不在响应里塞后端组装好的 `summary` 字符串——那样会和原始数据冗余、固化措辞、锁死单位/精度/语言风格。在 SKILL.md 每个列表型工具下加"复述提示",告诉模型该重点说什么。

### 后端按品种校验,不在 skill 里写死规则
品种规则(小数位、最小申报数量、涨跌停)由后端按品种实时校验,违反时通过 `error.hint` 反馈;不在 skill 文档里写死,避免跨品种翻车(如科创板 200 股起、北交所规则不同)。

### 模拟盘不强制二次确认
模拟盘试错成本为零,用户期望操作流畅。`submitOrder` 一步下单,模型只在**信息不全**时追问(如用户没说数量),不做风险确认拦截。

## 仓库结构

```
a-share-paper-trading/
├── SKILL.md                    # 给 OpenClaw 内核 + LLM 的契约文档
├── README.md                   # 本文件
├── a_share_paper_trading.py    # 配置、HTTP 客户端、工具函数、CLI 调度入口
└── pyproject.toml
```

## 安全建议

- API Key 仅存于环境变量,不写进代码或日志(如必须打印,仅显示前 4 后 4)
- 每个 API Key 由华泰按账户隔离,不要在多人间共享
- 不持久化模拟账户数据到公共目录,不提交到版本控制

## 维护

本项目由华泰证券维护。

**Authors**: Huatai Securities

## 许可证

MIT
