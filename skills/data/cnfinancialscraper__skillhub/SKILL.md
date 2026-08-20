---
name: cn-financial-scraper
version: 7.2.0
description: |
  中国金融机构数据爬取与分析综合 Skill v7.2.0。全量机构名单（2270+家，33大类）、
  全网舆情（4 类 60+ 商业财经媒体源 + RSS 直连 + akshare 兜底）、A股报告/公告/研报、
  结构化市场数据（期货/宏观/Shibor/港股美股）、深度类人浏览器爬取、真实风险指标分析、
  定期报告解读（财报自动解读/同比环比/亮点风险/评分评级）。

  🆕 v7.2.0 爬取硬化：软拦截检测接线（200 反爬页自动识别重试）、Retry-After 遵从、
    URL 去重器（跨进程持久化）；修复空 POST 退化/下载存错页/HTTPError url 冲突等 7 处 bug。

  v7.1.0 核心升级（承接）：定期报告解读：财报自动解读（业绩概览/同比环比/ROE/毛利率/现金流/亮点/风险/评分评级），纯规则零依赖

  v7.0.0 核心升级（承接）：机构名单完成（1330→2270家/33类）、网络拦截 API 挖掘、
  操作宏录制回放、文件上传下载拖拽、异步并发标签池、gzip 解压、A股名单双源容灾、
  宏观 5 指标零依赖直连、机构官网批量补全。

  v6.0.0 核心升级（承接）：数据源全面商业化（移除 gov.cn 官媒源）、浏览器深度类人化、
  解析智能、真实 PDF/HTML 报告导出、zip 增量打包。

  触发词：爬取机构、舆情爬取、全网舆情、网页爬取、产品解析、公告下载、券商研报、
  批量爬取、定时爬取、文档分析、东方财富、龙虎榜、北向资金、监管动态、搜索引擎、
  网页归档、类人爬取、数据回测、性能优化、结构化数据、期货、宏观经济、港股美股、
  风险指标、组合复刻、夏普比率等（完整触发词见下方 auto_trigger）。
auto_trigger:
  keywords:
    - 爬取机构
    - 机构名单
    - 网页爬取
    - 产品解析
    - 公告下载
    - 券商研报
    - 研报导出
    - 批量爬取
    - 公司批量
    - 新闻资讯
    - 上市公司报告
    - 机构更新
    - 金融数据
    - 文档分析
    - 整理文档
    - 文档对比
    - 基金分析
    - 基金净值
    - 净值查询
    - 年报
    - 季报
    - 半年报
    - 股票分析
    - 产品对比
    - 机构查询
    - 定时爬取
    - 自动爬取
    - 打包下载
    - ZIP导出
    - 压缩摘要
    - 提取关键信息
    - 生成报告
    - 撰写报告
    - 研报生成
    - 研究报告
    - 图表生成
    - 报告导出
    - 文件解析
    - PPT解析
    - HTML解析
    - 金融写作
    - 全网舆情
    - 舆情爬取
    - 舆情监测
    - 网络舆情
    - 爬取舆情
    - 爬取负面
    - 爬取正面
    - 爬取利空
    - 利好新闻
    - 负面新闻
    - 对话式舆情
    - 舆情定时
    - 自定义目标
    - 增加目标
    - 东方财富
    - 龙虎榜
    - 北向资金
    - 监管动态
    - 监管处罚
    - 巨潮资讯
    - 基金净值排行
    - 主权基金
    - 全球金融机构
    - 网页归档
    - 全页抓取
    - 归档网页
    - 网页存档
    - 搜索爬取
    - 搜索抓取
    - 搜索引擎搜索
    - 数据回测
    - 回测验证
    - 确认爬取
    - 类人爬取
    - 模拟浏览
    - 并发爬取
    - 加速爬取
    - 回测过滤
    - 回测汇总
    - 样本预览
    - 输入校验
    - 风险提示
    - 结构化数据
    - 期货行情
    - 期货数据
    - 宏观经济
    - GDP数据
    - CPI数据
    - Shibor
    - 同业拆借
    - 港股行情
    - 美股行情
    - 风险指标
    - 夏普比率
    - 最大回撤
    - 组合复刻
    - 相似基金
    - API挖掘
    - 接口挖掘
    - 网络拦截
    - 操作宏
    - 宏录制
    - 宏回放
    - 宏文件
    - 文件上传
    - 文件下载
    - 网页拖拽
    - 富文本输入
    - 组合键
    - 并发抓取
    - 并发池
    - 名单扩充
    - 扩充机构
    - 官网补全
    - 补全官网
    - A股名单
    - 上市公司名单更新
    - 定期报告解读
    - 财报解读
    - 年报解读
    - 半年报解读
    - 季报解读
    - 业绩解读
    - 财报分析
    - 业绩分析
    - 财务解读
    - 年报分析
    - 中报解读
    - 一季报解读
    - 三季报解读
    - 财务点评
    - URL去重
    - 去重爬取
    - 软拦截
    - 反爬重试
    - 熔断限流
  patterns:
    - (爬取|获取|看下|看看|查)(机构|公司|银行|基金|券商|保险)(的|这|那)?(舆情|新闻|资讯|报道)?
    - (爬取|导出|生成)\s*\S*(word|excel|docx|xlsx|报告|表格)
    - (正面|负面|舆情|利空|利好|网评|新闻|资讯)\s*(信息|报道|新闻|消息|舆情)
    - (指定|设置)?(定时|每天|每周|每月|每小时)?\s*爬取.{0,8}舆情
    - (新增|添加|新建)\s*(自定义)?\s*(目标|机构|公司)
    - (舆情|新闻)\s*(导出|生成|报告)
    - (东方财富|龙虎榜|北向资金|监管|巨潮资讯|基金净值)
    - (查|搜|爬)(全球|海外|国外)\s*(金融机构|央行|监管|交易所)
    - (归档|保存|下载|抓取)\s*(网页|页面|文章|全文)
    - (搜索|查找|搜一下)\s*.{0,10}(新闻|资讯|舆情|报道|年报)
    - (回测|验证|核实)\s*.{0,5}(数据|内容|信息|新闻)
    - (并发|加速|多线程)\s*.{0,5}(爬|抓)
    - (过滤|丢弃|筛选)\s*.{0,5}(低质量|无效|失真)
    - (期货|宏观|港股|美股|Shibor|同业)\s*(数据|行情|利率|指标)
    - (风险指标|夏普|回撤|组合复刻|相似基金)\s*(分析|计算|推荐)?
disable-model-invocation: true
---

# cn-financial-scraper v7.2.0 — 全网金融数据爬取与分析

> **全量机构名单（2270+家/33大类）** | **全网舆情（60+ 商业财经媒体源 + RSS + akshare 兜底）** | **A股报告/公告/研报** | **结构化市场数据** | **深度类人浏览器爬取** | **真实风险指标分析**

## ⚡ 一键上手

直接对话即可触发，无需记忆命令：

```
帮我爬一下某上市公司最近7天的舆情
某基金公司最近3天的负面新闻，并导出 Excel
把这篇网页完整归档，包含图片和表格
搜索"贵州茅台2026半年报"然后把结果爬取下来
爬一下银行板块最近3天的舆情并导出 Word
```

**一键启动**（Windows 直接 `python run_sentiment.py` 或）：
```bash
python run_sentiment.py                          # 交互式对话
python run_sentiment.py "贵州茅台最近7天的舆情"     # 直接命令行
```

---

## 🧭 场景速查（想做什么 → 直接入口）

> 无需记忆命令，按「想做什么」直接找到入口。完整 API 与 MCP 工具表见 [README.md](README.md)。

| 你想做什么 | 直接入口 | 依赖 |
|---|---|---|
| 爬某公司/机构最近 N 天舆情 | `crawl_global_sentiment` 或 `python run_sentiment.py "XX最近7天舆情"` | 核心 |
| 查机构名单 / 机构信息 | `query_institution` / `search_institution` | 核心 |
| 爬单个网页内容 | `scrape_webpage(url)` | 核心 |
| 动态页面 / 类人浏览 / 验证码接管 | `browser_human_fetch(url)`（需 Playwright） | Playwright |
| 搜公告 / 券商研报 / 公司财报 | `search_announcements` | 推荐 |
| 股票 / 基金 / 可转债实时行情 | `get_stock_realtime` | 核心 |
| 期货 / 宏观(GDP·CPI·PPI·PMI) / Shibor / 港股美股 | `get_structured_data` | akshare |
| 风险指标（年化/波动/回撤/夏普/卡玛） | `analyze_risk_metrics` / `calculate_risk_metrics` | 推荐 |
| 定期报告 / 财报解读 | `interpret_stock_report("600519")` / `interpret_stock` | 核心 |
| 生成研究报告 / 多格式导出 | `generate_research_report` / `quick_report` | 推荐 |
| 批量爬取 + 打包下载 | `CrawlPackager().package_batch_crawl` | 核心 |
| 搜索引擎搜索（中文优先） | `search_web` / `quick_search` | 核心 |
| 网页全页归档 | `quick_archive(url)` | 核心 |
| 扩充机构名单 / 补全官网 / 更新A股名单 | `expand_institution_list` / `UrlCompleter` / `StockListUpdater` | 核心 |

## 📚 文档导航（找什么 → 去哪里）

| 找什么 | 去哪里 |
|---|---|
| 快速开始 + 场景入口 | 本文件「一键上手」+「场景速查」 |
| 完整功能 / 机构清单 / 媒体源 / MCP 工具表 / 版本历史 | [README.md](README.md) |
| 故障排查（返回空 / 限流 / 依赖缺失 / 成功率低） | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 安全审计 / 数据源合规 | [SECURITY.md](SECURITY.md) |
| 全部测试 | `python runtests.py`（630 个） |

---

## 能力矩阵

| 模块 | 能力 | 依赖层级 | 入口 |
|---|---|---|---|
| **机构名单** | 2270+ 金融机构，33 大类，URL 注册表 | 核心 | `query_institution` |
| **全网舆情** | 4 类 60+ 商业财经媒体源 + RSS 直连 + 搜索引擎 + akshare 兜底，情感/严重度分级，模糊去重 | 核心 | `crawl_global_sentiment` |
| **网页爬取** | 六级降级链（Scrapling→Playwright→HTTP），缓存+熔断+重试 | 核心 | `scrape_webpage` |
| **浏览器爬取** | 深度类人操作（阅读停顿/4种滚动模式/贝塞尔鼠标/悬停/多标签/iframe合并）、会话保持、验证码人工接管、proxy、单例复用 | Playwright | `browser_human_fetch` |
| **公告/研报** | 巨潮公告 PDF、券商研报、公司财报 | 推荐 | `search_announcements` |
| **行情/数据** | 股票/基金/可转债/两融/大宗/ETF流/龙虎榜/LPR/国债/北交所 | 核心 | `get_stock_realtime` |
| **结构化数据** | 期货/宏观(GDP·CPI·PPI·PMI)/Shibor/港股美股 | akshare | `get_structured_data` |
| **产品分析** | 真实风险指标（年化/波动/回撤/夏普/卡玛）、风格、组合复刻、相似推荐 | 推荐 | `analyze_risk_metrics` |
| **搜索** | 百度/搜狗/DDG/SearXNG 多引擎，中文优先 | 核心 | `search_web` |
| **定期报告解读** | 🆕 财报自动解读（业绩概览/同比环比/ROE/毛利率/现金流/亮点/风险/评分评级），纯规则引擎零依赖 | 核心 | `interpret_stock_report` |
| **报告** | 研究报告生成、文档分析、图表、多格式导出（含真实 PDF / HTML 网页版） | 推荐 | `generate_research_report` |

> **依赖层级说明**：**核心** = 零 pip 依赖即可用 | **推荐** = `--recommended` 安装后可用（bs4/lxml/docx） | **Playwright** = 需额外 `pip install playwright && playwright install chromium` | **akshare** = 需额外 `pip install akshare`

### ⚠️ 能力边界（重要）

| 类别 | 说明 |
|---|---|
| ✅ **完全支持** | 机构名单查询、基金/ETF/FOF/股票产品解析、A股公告搜索下载、券商研报、新闻资讯、舆情监控、批量爬取（断点续爬）、文档解析（PDF/Word/Excel/PPT/HTML）、报告导出（Word/PPT/Excel）、风险指标分析、结构化市场数据（期货/宏观/Shibor） |
| ❌ **不支持** | 需登录的页面（如微信公众号后台、券商内部系统）、付费墙内容（如 Wind 终端数据）、实时 WebSocket 推送、移动端 APP 内嵌页面、验证码自动破解（需第三方打码服务） |
| ⚠️ **部分支持** | 动态渲染页面（需 Playwright，用 `mode="realtime"`）、反爬极严的网站（如某些银行官网，成功率 30-50%）、大批量爬取（需控并发 ≤5 + 断点续爬）、海外网站（需代理，部分有地域限制） |

**预期成功率**：天天基金 95%+ / 东方财富 90%+ / 同花顺 85%+ / 基金公司官网 70-90% / 银行官网 30-50% / 反爬严格的网站 20-40%。

---

## 安装（三层依赖）

```bash
python setup_env.py                # 仅核心（零 pip 依赖，舆情/HTTP 可用）
python setup_env.py --recommended  # + bs4/lxml/docx/openpyxl（解析+导出）
python setup_env.py --full         # + scrapling/playwright/mcp/akshare（全功能）
```

| 功能 | 需要的依赖 | 安装命令 |
|---|---|---|
| 舆情爬取 / 机构查询 / HTTP 爬取 | 无（核心自带） | `python setup_env.py` |
| PDF/Word/Excel 解析 + 报告导出 | bs4, lxml, python-docx, openpyxl | `python setup_env.py --recommended` |
| 浏览器自动化（动态页面/类人爬取） | playwright | `pip install playwright && playwright install chromium` |
| 结构化数据（期货/宏观/Shibor） | akshare | `pip install akshare` |
| 全功能 | 全部 | `python setup_env.py --full` |

---

## 🆕 v7.2.0 爬取硬化速查

```python
from scripts.http_utils import http_get, download_file
# 软拦截检测已接线：200 反爬页（验证码/访问被拒等短页面）自动识别并重试
# 429/503 自动遵从 Retry-After；熔断等待不再阻塞其他域名
from scripts.anti_block_utils import UrlDeduplicator
dedup = UrlDeduplicator("data/seen_urls.json")   # 跨进程持久化去重
if dedup.is_new(url):                            # 首次见到返回 True 并记录
    download_file(url, save_dir="data/downloads")  # 4xx/5xx 不再落盘
```

---

## 🆕 v7.1.0 新增模块速查

### 定期报告分析解读（`report_interpreter.py`，纯规则引擎零依赖）
```python
from scripts.report_interpreter import interpret_stock_report, interpret_data
text = interpret_stock_report("600519")        # 一站式：拉取+解读（年报/半年报/季报）
result = interpret_data({"营收": 100.0, "净利润": 20.0, "毛利率": 45.0,
                         "ROE": 15.0, "营收同比": 25.0, "净利同比": 35.0})
# 输出：业绩概览（营收/净利/同比/环比/EPS）、盈利能力（ROE/毛利率）、
#       现金流质量、✅亮点信号、⚠️风险提示、综合评分(0-100)+评级（积极/中性/谨慎）
# 数据源：东财 RPT_LICO_FN_CPD 直连（含 YSTZ/SJLTZ 同比、YSHZ/SJLHZ 环比增速字段）
```

---

## 📜 v7.0.0 新增模块速查

### 网络拦截 / API 挖掘（`browser_pro.py`）
```python
from scripts.browser_pro import discover_api
api = discover_api("https://fund.eastmoney.com/company/")   # 监听 XHR/fetch
# 自动识别分页规律 + 捕获 JSON 响应样本 → data/api_registry.json（去重累积）
# 挖掘到接口后即可 HTTP 直连，无需再开浏览器；ScrapableRegistry.suggest_api 可查
```

### 操作宏录制与回放（`browser_pro.py`）
```python
from scripts.browser_pro import record_macro, play_macro
record_macro("https://example.com/search", record_seconds=25)  # 可见模式录制
play_macro("recorded_xxx.json", params={"input": "贵州茅台"})   # {{参数}} 回放
# 宏动作：goto/click/fill/select/press/scroll/upload/download/drag/extract/…
```

### 文件上传 / 下载 / 拖拽 / 组合键（挂到 BrowserScraper）
```python
from scripts.browser_scraper import BrowserScraper
with BrowserScraper(headless=True) as bs:
    bs.upload_file(url, "input[type=file]", ["a.pdf"])      # 上传
    bs.download_file(url, click_selector=".btn", filename="r.xlsx")  # 下载
    bs.drag_and_drop(url, "#slider", "#target")             # 拖拽
    bs.press_keys(url, "Control+A", selector="#box")        # 组合键
    bs.type_contenteditable(url, "[contenteditable]", "正文")  # 富文本
```

### 异步并发标签池（`browser_pro.py`）
```python
from scripts.browser_pro import async_batch_fetch
res = async_batch_fetch(urls, concurrency=6)   # async Playwright 多页并发
```

### 机构名单扩充 / 官网补全 / A股名单（`institution_expander.py` `url_completer.py`）
```python
from scripts import expand_institution_list, UrlCompleter, StockListUpdater
expand_institution_list()      # 1330 → 2270 家 / 33 类（live+精选+list 反向吸收）
UrlCompleter().run(limit=100)  # 搜索引擎补官网（断点续跑）
StockListUpdater().run()       # A股全量 5542 只（东财→新浪双源容灾）
```

### 宏观 5 指标零依赖直连（`market_data_scraper.py`）
```python
from scripts.market_data_scraper import get_macro_indicator
get_macro_indicator("cpi", limit=24)   # CPI/PPI/PMI/GDP/M2，纯 HTTP，akshare 缺失也可用
```

---

## 📜 v6.0.0 新增模块速查

### 深度类人浏览器（`browser_scraper.py`）
```python
bs = BrowserScraper(headless=True)
html = bs.humanlike_fetch(url, think_time=True, hover=True, tab_switch=True,
                          include_iframes=True)   # 阅读停顿+悬停+多标签+iframe合并
# 会话保持：Cookie 自动持久化到 data/browser_state/，跨进程复用
# 验证码接管：检测到验证码自动截图到 data/screenshots/captcha_*.png 并返回 None
# 4 种滚动模式：fast_browse / slow_read / segmented / rewind 随机切换
```

### 真实 PDF 报告（`report_exporter.py`）
```python
from scripts.report_exporter import ComprehensiveExporter
exporter = ComprehensiveExporter()
files = exporter.export_all_formats(data, "600519")   # 含 pdf（Playwright 渲染）+ html
# HtmlExporter 生成带样式的网页版报告，PDF 链路：HTML → Chromium print to PDF
```

### zip 批量下载（`crawl_packager.py`）
```python
from scripts.crawl_packager import CrawlPackager
p = CrawlPackager()
zip_path = p.package_batch_crawl("贵州茅台,招商银行", parallel_workers=4,
                                 progress_callback=lambda d, t, n: print(f"{d}/{t} {n}"))
# 失败项自动重试 2 次并写入包内 failed.json；增量打包：
path, skipped = p.package_incremental(items, previous_zip="old.zip")
```

### 监管资讯（`regulatory_scraper.py`，商业数据源）
```python
from scripts.regulatory_scraper import get_regulatory_updates
news = get_regulatory_updates("all", limit=20)   # 东财宏观政策 + 新浪财经 + 巨潮公告
```

### 正文抽取与 JSON-LD（`web_parser.py`）
```python
from scripts.web_parser import extract_main_content, extract_jsonld, extract_product_from_jsonld
content = extract_main_content(html)          # readability 风格正文抽取
```

---

## 📜 v5.0.0 新增模块速查

### 结构化市场数据（`scripts/structured_market_data.py`）
akshare 低代码统一入口，覆盖期货/宏观/同业/港股美股，未装 akshare 自动返回空。
```python
from scripts import get_structured_data, list_data_types
df = get_structured_data("shibor")            # Shibor 同业拆借利率
df = get_structured_data("futures_spot")      # 全市场期货实时行情
df = get_structured_data("macro_cpi")         # CPI 同比
```

### 百度/搜狗搜索引擎（`search_engine.py`）
中文财经召回最佳，`MultiEngineSearch` 自动百度→搜狗→DDG→SearXNG 优先国内。
```python
from scripts import quick_search
quick_search("贵州茅台 2026半年报", engines=["baidu_html", "sogou_html"])
```

### 浏览器增强（`browser_scraper.py`）
```python
bs = BrowserScraper(headless=True, proxy="http://127.0.0.1:8080", ad_block=True)
results = bs.extract_many(["https://a.com/1", "https://b.com/2"])  # 并发标签页
```
舆情兜底与 web_parser 复用进程级单例浏览器（`_get_browser_scraper`），告别每源冷启动。

### 真实风险指标（`analyzer.py` 重写）
```python
from scripts.analyzer import calculate_risk_metrics
metrics = calculate_risk_metrics([{"date": "2026-01-01", "nav": 1.2}, ...])
# annualized_return / volatility / max_drawdown / sharpe / calmar（≥30 点才计算，不伪造）
```

### 舆情分类器增强
否定词处理（"否认业绩下滑"不再判负面）、相对时间（"3小时前/昨天"）、严重度阈值统一、模糊去重（标题相似 >0.85）。

---

## 关键命令

| 命令 | 用途 |
|---|---|
| `python run_sentiment.py` | 交互式舆情对话 |
| `python runtests.py` | 跑全部测试（当前 630 个） |
| `python setup_env.py --full` | 全功能安装 |
| `python mcp_server.py` | 启动 MCP Server（stdio，64 个工具） |
| `python scripts/scrapable_registry.py stat` | 机构名单统计 |
| `python scripts/structured_market_data.py` | 结构化数据自检 |

---

## 故障排查速查

| 症状 | 原因 | 解决 |
|---|---|---|
| cls/sina/jisilu/wallstreetcn 返回空 | 接口被封 | v5.0 已接线 akshare 自动兜底，无需手动处理 |
| 主站返回 200 但内容是验证码页 | 软封禁 | 自动检测并切浏览器兜底；`DomainRateLimiter` 按域限速 |
| 中文搜索召回差 | 默认引擎不合适 | 百度/搜狗优先（`baidu_html`/`sogou_html`） |
| 舆情抓取慢 | 每源冷启动 | v5.0 浏览器单例复用；`parallel_workers=4` 并发 |
| 行情/新闻请求被限流 | 频率过高 | 全部请求已统一走自适应限流（`RatelimitedSession`） |
| `ModuleNotFoundError: playwright` | 未装浏览器依赖 | `pip install playwright && playwright install chromium` |
| akshare 返回空 | 未装 akshare | `pip install akshare` |
| 更多 | — | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

---

## ❓ 常见问题（FAQ）

### Q1: 舆情爬取返回空怎么办？
**A**: 1）检查目标名称是否正确（用 `list_sentiment_targets` 查看）；2）尝试扩大时间范围（`days=7`）；3）增加媒体源类别（`source_categories=["authoritative", "financial_vertical", "self_media"]`）。

### Q2: 结构化数据（期货/宏观）返回 None？
**A**: 需要安装 akshare：`pip install akshare`。未安装时函数自动返回 None，不会报错。

### Q3: 动态渲染页面（SPA）爬不到内容？
**A**: 默认 `mode="static"` 只走 HTTP。SPA 页面需用 `mode="realtime"`（需 Playwright）：
```python
result = scrape_webpage(url="...", mode="realtime")
```

### Q4: 爬取银行官网成功率很低？
**A**: 银行官网普遍反爬严格（验证码/IP 封禁），预期成功率 30-50%。建议：1）用 `browser_human_fetch` 走浏览器；2）加 proxy 轮换；3）降低频率。

### Q5: 如何自定义舆情监控目标？
**A**: 两种方式：
```python
# 方式 1：对话式
chat_handle("新增自定义目标：恒生电子")

# 方式 2：API
add_custom_sentiment_target("custom", "恒生电子")
```

### Q6: pip 安装依赖很慢怎么办？
**A**: 使用国内镜像：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
# 或永久设置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

> 📘 更多故障排查见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 🔒 安全审计见 [SECURITY.md](SECURITY.md)

---

## 详细文档

完整功能说明、机构清单、媒体源/目标库、MCP 工具表（55 个）、实战场景、版本历史，见 [README.md](README.md)。
