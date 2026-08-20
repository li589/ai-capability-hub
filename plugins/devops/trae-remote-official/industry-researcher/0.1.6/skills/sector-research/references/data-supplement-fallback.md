# dataSupplement 本地冗余层

> 本地降级数据层。金融 MCP 不可用或返回失败时自动降级至此。定位为兜底补充，不替代金融 MCP。
>
> 相关文档：数据字典见 `financial-data-spec.md`，来源标注见 `source-resolution.md`。

---

## 启动方式

**推荐方式（一行调用）：**

```bash
bash {skill_root}/scripts/run_data_supplement.sh "from domains.quotes import realtime_quote; print(realtime_quote('600519'))"
```

脚本自动处理：
1. venv 不存在时自动创建 + 安装依赖
2. 检测 PYTHONHOME 劫持 → 自动用 `env -i` 隔离（TRAE 沙箱）
3. 本地终端无劫持 → 直接跑 venv python

**手动方式（RunCommand 直接调用）：**

```bash
env -i HOME=$HOME PATH="/usr/local/bin:/usr/bin:/bin:{skill_root}/.venv/bin" \
  PYTHONPATH="{skill_root}/dataSupplement" \
  "{skill_root}/.venv/bin/python" -c "
from domains.quotes import realtime_quote
result = realtime_quote('600519')
print(result)
"
```

> 依赖已预装在 `{skill_root}/.venv`（python3.12 + mootdx + akshare + pandas）。沙箱环境必须用 `env -i` 清除 PYTHONHOME。

---

## 工具清单与 TDX 映射

| TDX 工具 | dataSupplement 对等函数 | 导入路径 | 参数差异 |
|----------|-------------|----------|----------|
| tdx_quotes | realtime_quote / batch_quotes | domains.quotes | code 自动识别格式(600519/00700/AAPL)，无需 setcode |
| tdx_kline | get_kline | domains.kline | freq=day/week/5min/15min/30min/60min, count=N |
| tdx_indicator_select | key_metrics + financial_statements | domains.fundamentals | 需拆分为逐项调用，不支持 NLP |
| tdx_screener | multi_factor_screen | domains.screener | 显式参数(pe_max, roe_min, market_cap_min等) |
| tdx_security_deep_info | company_profile | domains.fundamentals | 仅基础公司信息，深度不及 F9 |
| wenda_report_query | stock_reports + industry_reports + consensus_eps | domains.research | 分三个函数，按需调用 |
| wenda_notice_query | search_announcements | domains.announcements | keyword 精确匹配 |
| wenda_news_query | stock_news + market_flash | domains.news | 个股/快讯分开 |
| wenda_macro_query | — | — | ❌ 不可降级，保持 WebSearch |

---

## 代码格式约定

dataSupplement 自动识别市场，无需传 setcode：
- A股：600519 / sh600519 / 600519.SH → 标准化为 "600519"
- 港股：00700 / 0700.HK → 标准化为 "00700"
- 美股：AAPL / AAPL.US → 标准化为 "AAPL"

---

## 调用规范

### 行情（替代 tdx_quotes）

```python
from domains.quotes import realtime_quote, batch_quotes

# 单只（含 PE/PB/市值/换手率）
quote = realtime_quote("600519")
# 返回: {code, name, price, change, change_pct, open, high, low, prev_close, volume, amount, pe, pb, market_cap, turnover_rate, market}

# 批量（A股走腾讯批量接口，非A股逐个）
quotes = batch_quotes(["600519", "000858", "601318"])
```

### K线（替代 tdx_kline）

```python
from domains.kline import get_kline

# 日K（默认120根）
bars = get_kline("600519", freq="day", count=120)
# 周K
bars = get_kline("600519", freq="week", count=52)
# 返回: [{date, open, high, low, close, volume, amount, turnover_rate}, ...]
```

### 基本面（替代 tdx_indicator_select）

```python
from domains.fundamentals import financial_statements, key_metrics, company_profile

# 关键指标（PE/PB/ROE/毛利率/净利率）
m = key_metrics("600519")
# 返回: {code, name, pe, pe_ttm, pb, roe, gross_margin, net_margin, revenue_growth, profit_growth, market_cap}

# 三表
fs = financial_statements("600519", report_type="income")  # income/balance/cashflow
# 返回: [{report_date, revenue, net_profit, ...}, ...]

# 公司简况
profile = company_profile("600519")
```

> ⚠️ tdx_indicator_select 的 NLP 能力（如"对比5家白酒的ROE"）在 dataSupplement 中需拆分为逐只调用 key_metrics 后手工合并。

### 研报（替代 wenda_report_query）

```python
from domains.research import stock_reports, industry_reports, consensus_eps

# 个股研报列表
reports = stock_reports("600519")
# 行业研报
ind_reports = industry_reports("白酒")
# 机构一致预期 EPS
eps = consensus_eps("600519")
```

### 新闻（替代 wenda_news_query）

```python
from domains.news import stock_news, market_flash

# 个股新闻
news = stock_news("600519", count=20)
# 7x24 市场快讯
flash = market_flash(count=30)
```

### 公告（替代 wenda_notice_query）

```python
from domains.announcements import search_announcements

ann = search_announcements("600519", keyword="分红")
```

### 选股（替代 tdx_screener）

```python
from domains.screener import multi_factor_screen, index_constituents

# 多因子筛选
results = multi_factor_screen(pe_max=30, roe_min=15, market_cap_min=100e8)
# 指数成分股
cons = index_constituents("000300")  # 沪深300
```

---

## 内置降级链

dataSupplement 每个 domain 函数已内置多源 fallback：
- 行情：腾讯 → 新浪 → 通达信(mootdx)
- K线：通达信(mootdx) → 腾讯 → 新浪
- 基本面：新浪 → Yahoo
- 龙虎榜：东财 → 交易所官方
- 资金流：东财 → 新浪 → akshare
- 公告：巨潮 → 东财 → 深交所
- 研报：东财 reportapi
- 一致预期：同花顺
- 舆情：东财 emappdata + 同花顺

调用 dataSupplement 函数时，内部 fallback 对调用方透明——只需捕获空返回（{} 或 []）即可判定该函数是否取到数据。

---

## 返回值约定

| 状态 | 返回值 | 后续处理 |
|------|--------|----------|
| 成功 | 非空 dict 或 list | 正常使用，标注 source: "dataSupplement" |
| 失败 | {} 或 [] | 进入 Layer 3（WebSearch 降级） |
| 异常 | 函数抛出 Exception | 捕获后进入 Layer 3 |

---

## 数据输出标注

dataSupplement 降级获取的数据在输出 JSON 中标记：
```json
{
  "source": "dataSupplement",
  "degradation_from": "tdx"
}
```

与 TDX 数据 `"source": "tdx"` 和 WebSearch 数据 `"source": "web"` 区分。

---

## 不可降级区域

以下数据 dataSupplement 无法提供，直接跳至 WebSearch 或标注 [UNAVAILABLE]：

| 数据类型 | 原因 | 处理 |
|----------|------|------|
| 宏观经济数据 | dataSupplement 无宏观模块 | WebSearch 降级 |
| F9/F10 完整深度资料 | dataSupplement 仅有 company_profile（简版） | WebSearch 补充 |
| NLP 横向多指标对比 | dataSupplement 无 NLP 入口 | 逐只 key_metrics + 手工合并 |

---

## 限流与防封

dataSupplement 内置统一限流：
- 东财全系：≥1.2s 间隔 + 随机抖动
- 通达信：TCP 长连接，10 台备选服务器自动切换
- 同花顺：正常 UA
- 腾讯/新浪：无限制

批量取数建议：A股用 batch_quotes 一次性获取（腾讯接口支持逗号拼接），避免逐只循环。
