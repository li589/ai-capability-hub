---
name: dataSupplement
description: "金融数据补充层：为 submit2 主 skill 提供 Layer 2 降级数据源。覆盖A股/港股/美股，13个业务域·60+数据端点·10大数据源·内置自动fallback降级·统一限流防封·零外部依赖(仅Python标准库)。通过 domains/ 下的函数调用，每个函数自动选择最优数据源并处理异常降级。"
origin: custom
version: 7.1.0
---

# dataSupplement 金融数据补充层

多市场金融数据原语集（A股·港股·美股），为 AI Agent 提供统一的结构化金融数据获取能力。

## 版本

V7.0.0 (2026-07-15)

## 能力概览

覆盖 **3大市场 · 13个业务域 · 60+ 数据端点**：

| 市场 | 覆盖领域 |
|------|----------|
| A股（沪深北） | 行情/K线/基本面/资金流/研报/信号/新闻/公告/涨跌停/ETF期权/舆情/技术指标/选股 |
| 港股 | 行情/K线/基本面/资金流/技术指标 |
| 美股 | 行情/K线/基本面/资金流/期权/SEC Filing/技术指标/搜索 |

## 架构

```
dataSupplement/
├── core/           # 基础设施（HTTP·缓存·限流·代码归一化）
├── providers/      # 数据源适配器（按提供商组织）
├── domains/        # 业务域接口（按主题组织，面向 Agent 调用）
└── tests/          # 冒烟测试
```

**调用约定**：Agent 通过 `domains/` 下的函数获取数据，每个 domain 函数自动选择最优 provider 并处理 fallback。

## 快速参考

### 行情（多市场）

```python
from domains.quotes import realtime_quote, batch_quotes
# A股
quote = realtime_quote("600519")        # 贵州茅台
# 港股
quote = realtime_quote("00700.HK")      # 腾讯控股
# 美股
quote = realtime_quote("AAPL")          # Apple
# 批量
quotes = batch_quotes(["600519", "000858", "601318"])
```

### K线

```python
from domains.kline import get_kline
# 日K（默认120根）
bars = get_kline("600519", freq="day", count=120)
# 分钟K
bars = get_kline("600519", freq="5min", count=48)
# 美股周K
bars = get_kline("AAPL", freq="week", count=52)
```

### 基本面

```python
from domains.fundamentals import financial_statements, key_metrics
# 三表
fs = financial_statements("600519", report_type="income")
# 关键指标
m = key_metrics("AAPL")  # PE/PB/ROE/毛利率/净利率
```

### 资金流

```python
from domains.capital_flow import fund_flow, margin_data, block_trade
flow = fund_flow("600519")              # 主力/大单/中小单
margin = margin_data("600519")          # 融资融券
trades = block_trade("600519")          # 大宗交易
```

### 信号

```python
from domains.signals import dragon_tiger, hot_stocks, northbound, lockup_calendar
dtb = dragon_tiger("600519")            # 龙虎榜
hot = hot_stocks()                      # 当日强势股+题材归因
nb = northbound()                       # 北向资金实时
lockup = lockup_calendar("600519")      # 解禁日历
```

### 新闻与公告

```python
from domains.news import stock_news, market_flash
from domains.announcements import search_announcements
news = stock_news("600519")             # 个股新闻
flash = market_flash()                  # 7x24 快讯
ann = search_announcements("600519", keyword="分红")
```

### 涨跌停（打板）

```python
from domains.limit_board import zt_pool, zb_pool, dt_pool, yesterday_zt, sentiment_score
pool = zt_pool("2026-07-15")            # 涨停池
sent = sentiment_score("2026-07-15")    # 情绪指标
```

### ETF期权

```python
from domains.options import option_chain, option_quote, option_greeks
chain = option_chain("510050")          # 50ETF期权合约清单
quote = option_quote("10007306")        # T型报价
greeks = option_greeks("10007306")      # Greeks+IV
# 美股期权
chain_us = option_chain("AAPL")         # Apple 期权链
```

### 舆情

```python
from domains.sentiment import hot_list, stock_popularity, investor_qa
hot = hot_list()                        # 人气热榜
pop = stock_popularity("600519")        # 个股人气排名
qa = investor_qa("600519")              # 互动易问答
```

### 技术指标

```python
from domains.tech_indicators import compute_indicators
# 基于K线自动计算
ind = compute_indicators("600519", indicators=["MA", "MACD", "KDJ", "RSI", "BOLL"])
```

### 研报

```python
from domains.research import stock_reports, industry_reports, consensus_eps
reports = stock_reports("600519")       # 个股研报
industry = industry_reports("白酒")     # 行业研报
eps = consensus_eps("600519")           # 机构一致预期
```

### 选股

```python
from domains.screener import multi_factor_screen
results = multi_factor_screen(
    pe_max=30, roe_min=15, market_cap_min=100e8
)
```

## Provider 优先级与可靠性

| Provider | 协议 | 封禁风险 | 覆盖市场 | 核心能力 |
|----------|------|----------|----------|----------|
| 腾讯财经 | HTTPS | 不封 | A/港/美 | 实时行情（首选） |
| 通达信 mootdx | TCP 7709 | 不封 | A股 | K线/盘口/财务（首选） |
| 新浪财经 | HTTPS | 极低 | A/港/美 | 财报/K线/期权 |
| 同花顺 | HTTPS | 低 | A股 | 热点/北向/涨停/预期 |
| 巨潮 cninfo | HTTPS | 低 | A股 | 公告/互动易 |
| 财联社 | HTTPS | 低 | A股 | 快讯（零key本地签名） |
| 东财 datacenter | HTTPS | 中 | A/港/美 | 龙虎榜/融资/解禁/资金流 |
| 东财 emappdata | HTTPS | 中 | A股 | 人气榜/概念命中 |
| Yahoo Finance | HTTPS | 境外 | 港/美 | K线/财报/期权/新闻 |
| SEC EDGAR | HTTPS | 境外 | 美股 | 10-K/10-Q/XBRL |
| akshare | Python包 | 不封 | A股 | 涨跌停池/板块/资金流（补缺） |

## 限流与防封策略

1. **东财全系**：统一限流器 ≥1.2s 间隔 + 随机抖动 0-0.5s，Session 复用
2. **通达信**：TCP 长连接复用，10 台备选服务器自动切换
3. **同花顺**：正常 UA，无额外限制
4. **Yahoo**：cookie+crumb 自动刷新机制
5. **SEC**：标准 User-Agent 头即可

## 数据源降级规则

每个 domain 内置 fallback 链，主源不可用时自动切换：
- 行情：腾讯 → 新浪 → 通达信
- 龙虎榜：东财 datacenter → 上交所/深交所官方
- 资金流：东财 → 新浪（备胎）→ akshare
- 公告：巨潮 → 东财 np-anotice → 深交所
- 涨跌停：akshare → 同花顺涨停揭秘
- 美港行情：腾讯 → 新浪 → Yahoo

## 注意事项

- 通达信 mootdx 需国内网络可达 TCP 7709 端口
- iwencai 语义搜索需 API Key（唯一付费源）
- Yahoo/SEC 为境外服务，国内直连可能需要代理
- 东财 push2/push2ex 域名已 IP 级封禁，相关能力已切换至 akshare/同花顺替代
