# cn-financial-scraper v7.2.0

> 中国大陆金融数据爬取与分析综合工具 v7.2.0 — 2270+ 机构 / 60+ 商业财经媒体源 / 64 MCP 工具

## ⚡ 快速上手（30 秒开始）

```bash
# 安装（自动使用国内镜像）
python setup_env.py --recommended

# 交互式对话（推荐）
python run_sentiment.py

# 命令行直接用
python run_sentiment.py "贵州茅台最近7天的舆情"
python run_sentiment.py "工银瑞信基金最近3天的负面新闻" --export excel
```

**Windows 用户**：`python run_sentiment.py` 一键启动（交互式对话）。

```python
# Python API
from scripts import parse_financial_product
result = parse_financial_product("https://fund.eastmoney.com/000001.html", "fund")
print(f"基金名称: {result['product_name']}")
```

---

## 🆕 v7.2.0 新增：爬取硬化与 bug 修复

| 特性 | 说明 | 模块 |
|------|------|------|
| **软拦截检测接线** | 200 反爬页（验证码/访问被拒等短 HTML）自动识别为失败并多策略重试，避免脏数据入库 | `http_utils.py` `anti_block_utils.py` |
| **Retry-After 遵从** | 429/503 重试等待优先取服务端 Retry-After 声明（限幅 60s） | `http_utils.py` |
| **URL 去重器** | 批量爬取去重：归一化（host 小写/默认端口/fragment/尾斜杠）+ 跨进程 JSON 持久化 + 按域名统计 | `anti_block_utils.py` `UrlDeduplicator` |
| **7 处 bug 修复** | 空 POST 退化为 GET；download_file 保存 4xx/5xx 错误页；HTTPError url property 冲突致 raise_for_status 崩溃；熔断 sleep 持全局锁阻塞其他域名；裸域名 reset 失效；过期 cookie 误保留 | 同上 |

---

## 🆕 v7.1.0 新增：定期报告分析解读

| 特性 | 说明 | 模块 |
|------|------|------|
| **财报自动解读** | 自动拉取东财 RPT_LICO_FN_CPD 财务数据（含同比/环比增速字段），规则引擎生成自然语言解读：业绩概览、盈利能力（ROE/毛利率）、现金流质量、✅亮点信号、⚠️风险提示、综合评分(0-100)与评级 | `report_interpreter.py` |
| **多路输入** | `interpret_stock`（股票代码直连）/ `interpret_data`（任意财务 dict，中英文字段兼容）/ 离线多期序列 | 同上 |
| **纯规则零依赖** | 阈值引擎 + 模板评语，无 LLM 依赖、无 pip 依赖，可嵌入批量巡检 | 同上 |
| **MCP 工具** | `interpret_financial_report`（64 个工具） | `mcp_server.py` |

<details>
<summary>📜 v7.0.0 核心升级（上一版本）</summary>

## v7.0.0 核心升级（上一版本）

| 特性 | 说明 | 模块 |
|------|------|------|
| **机构名单完成** | 1330 → 2270 家 / 33 大类；live 名录直连（基金 167/期货 181）+ 精选数据 + list 文件反向吸收；新增民营银行 19、外资法人银行 41、AMC 5、村镇银行 60、保险经纪 48、保险公估 36 等类型；名单数字口径与实际数据一致 | `institution_expander.py` `data/curated/*.json` |
| **网络拦截 / API 挖掘** | 监听页面 XHR/fetch，自动捕获背后 JSON 接口 + 分页规律 → `data/api_registry.json` 去重累积，接口可 HTTP 直连复用 | `browser_pro.py` `discover_api` |
| **操作宏** | JSON 操作序列录制（注入 JS 捕获真实交互）与 {{参数}} 回放；goto/click/fill/upload/download/drag/extract 等 15+ 动作 | `browser_pro.py` `MacroPlayer` |
| **文件上传/下载/拖拽** | set_input_files / expect_download 落盘 / 类人拖拽 / contenteditable 富文本 / 键盘组合键 | `browser_pro.py` |
| **异步并发标签池** | async_playwright + semaphore 多页并发批量抓取，sync 模式不变 | `browser_pro.py` `AsyncBrowserPool` |
| **gzip 自动解压** | urllib 响应自动解压 gzip/deflate/br（此前压缩流导致 json() 乱码） | `http_utils.py` |
| **A股名单双源容灾** | 东财 push2 多镜像轮换 + 新浪 Market_Center 兜底，5542 只入库（含北交所 335） | `stock_list_updater.py` |
| **宏观零依赖直连** | CPI/PPI/PMI/GDP/M2 纯 HTTP 序列（akshare 缺失也可用），消除"新浪宏观待上线" | `market_data_scraper.py` |
| **官网批量补全** | 多引擎搜索 + 可达性验证回填 URL，聚合域/政务域过滤，断点续跑 | `url_completer.py` |
| **MCP 工具 55→63** | discover_api / play_macro / browser_upload / browser_download / async_batch_fetch / expand_institutions / complete_institution_urls / update_stock_list | `mcp_server.py` |

</details>

<details>
<summary>📜 v6.0.0 核心升级（上一版本）</summary>

## 🆕 v6.0.0 核心升级

| 特性 | 说明 | 模块 |
|------|------|------|
| **数据源商业化** | 监管资讯改由东财/新浪/巨潮商业 API 提供；移除政府网站与官方媒体源（含 gov.cn 域名全项目清除） | `regulatory_scraper.py` `scrapable_registry.py` |
| **媒体源扩充** | 新增和讯/金融界/凤凰财经/汇通/英为财情/智通/界面/蓝鲸/富途/阿思达克/上海有色等 12 家商业财经媒体 | `data/sentiment_sources.json` |
| **浏览器深度类人化** | 阅读停顿(2-8s) / 4 种滚动模式 / iframe 合并 / 会话保持 / 验证码人工接管 / 随机悬停 / 多标签切换 / 粘贴式输入 / 崩溃自愈 | `browser_scraper.py` |
| **反爬升级** | 封禁特征词库 20+ 中文/英文文案；UA 池与 Sec-CH-UA 更新至 Chrome 133 | `anti_block_utils.py` `http_utils.py` |
| **解析智能** | readability 风格正文抽取 `extract_main_content`；JSON-LD 文章类型；选择器缓存置信度衰减重学 | `web_parser.py` |
| **真实 PDF 导出** | Playwright 渲染 HTML → 真实 PDF（修复此前"仅提示手动转换"）；新增 HTML 网页版报告 | `report_exporter.py` |
| **zip 批量下载增强** | 并行爬取 / 进度回调 / 失败重试清单 failed.json / 增量去重打包 `package_incremental` | `crawl_packager.py` |
| **测试** | 脱敏回归断言（gov.cn 零残留）+ 新增浏览器/导出/zip 测试 | `tests/` |

</details>

<details>
<summary>📜 历史版本更新（v4.0 ~ v5.0）</summary>

### v5.0 — 媒体源扩充与结构化数据
- 媒体源 48 → 81 站点（后 v6.0 调整为 60+ 商业源）；结构化数据（期货/宏观/Shibor/港股美股）；浏览器 proxy/并发标签页；真实风险指标；新 MCP 工具 51→55

### v4.9 — 应对数据源被封
- akshare 兜底适配器 + RSS 数据源 + 反爬增强工具集（域限速/Cookie/错误码/TLS指纹/指数退避）

### v4.7 — 8类数据 + 对比回测
- 新增两融余额/大宗交易/ETF资金流/龙虎榜席位/股东增减持/LPR/国债收益率曲线/北交所
- 同类数据横向对比与回测（4 维质量评分）+ 监管政策文件下载 + 浏览器类人爬取加固

### v4.3 — 全网舆情爬虫（对话式）
- 对话式 NLU 入口 + 4 类 60+ 商业财经媒体源 + 11 类目标机构 + 情感分类 + 多格式导出 + 定时任务

### v4.2 — 浏览器自动化
- Playwright 集成 + STEALTH_JS 反检测 + 类人操作

### v4.1 — 海外机构 + 术语翻译
- 9 大类 210 家全球金融机构 + 600+ 金融术语词典 + 腾讯云 TMT 翻译

### v4.0 — 定时/打包/压缩/报告
- 定期自动爬取 + 批量 ZIP + 内容智能压缩 + 增强文件解析 + 金融写作引擎 + 6 套报告模板 + 研究报告全流程生成

</details>

## 安装（三层依赖，按需选择）

```bash
python setup_env.py                # 核心层（零 pip 依赖，舆情/HTTP 可用）
python setup_env.py --recommended  # 推荐层 + bs4/lxml/docx/openpyxl（解析+导出）
python setup_env.py --full         # 全功能 + scrapling/playwright/mcp/akshare
```

| 你想做什么 | 需要的依赖层级 | 安装命令 |
|---|---|---|
| 舆情监控、机构查询、HTTP 爬取、行情数据 | 核心层 | `python setup_env.py` |
| PDF/Word/Excel 解析、报告导出 | 推荐层 | `python setup_env.py --recommended` |
| 动态页面爬取、浏览器自动化、类人操作 | Playwright | `pip install playwright && playwright install chromium` |
| 期货/宏观/Shibor/港股美股结构化数据 | akshare | `pip install akshare` |
| 全部功能 | 全功能 | `python setup_env.py --full` |

### 安装验证

```bash
python -c "from scripts import search_institution; print('安装成功！')"
```

## MCP 工具

通过 MCP 协议暴露 **64 个工具**，可直接在 Claude Code 中调用：

| 工具 | 功能 |
|------|------|
| `query_institution` | 查询机构名单（按类型/关键词） |
| `discover_api` | 🆕 网络拦截挖掘页面背后 JSON 接口（含分页规律） |
| `play_macro` | 🆕 回放网页操作宏（{{参数}} 替换） |
| `browser_upload` | 🆕 文件上传（选择器+提交） |
| `browser_download` | 🆕 文件下载落盘到 data/downloads/ |
| `async_batch_fetch` | 🆕 异步并发批量抓取（多标签页池） |
| `expand_institutions` | 🆕 机构名单扩充（live+精选+list 三路合并） |
| `complete_institution_urls` | 🆕 机构官网批量补全（断点续跑） |
| `update_stock_list` | 🆕 A股全量名单更新（双源容灾） |
| `interpret_financial_report` | 🆕 定期报告分析解读（业绩/盈利/现金流/亮点/风险/评分评级） |
| `scrape_webpage` | 爬取指定 URL |
| `scrape_institution` | 按机构名爬取官网 |
| `parse_financial_product` | 解析基金/ETF/股票/债券页面 |
| `crawl_financial_news` | 最新金融新闻 |
| `search_announcements` | 搜索公告 |
| `download_announcement` | 下载公告 PDF |
| `query_broker_reports` | 券商研报查询 |
| `get_company_reports` | 上市公司综合报告 |
| `parse_document` | PDF/Word/Excel 解析 |
| `export_stock_report` | 导出 PPT/PDF/Word/Excel |
| `batch_crawl_institutions` | 批量爬取机构 |
| `search_report_index` | 全量报告索引搜索 |
| `analyze_document` | 深度分析金融文档 |
| `organize_documents` | 批量整理文档目录 |
| `compare_documents` | 多文档并排对比 |
| `get_stock_realtime` | A 股实时行情 |
| `get_fund_nav_history` | 基金历史净值 |
| `crawl_cls_telegraph` | 财联社 7x24 电报 |
| `get_convertible_bond_data` | 可转债数据 |
| 🆕 `schedule_crawl_task` | 创建定期自动爬取任务 (v4.3 扩展支持 `crawl_sentiment` / `crawl_sentiment_export`) |
| 🆕 `list_scheduled_tasks` | 查看所有定时任务及状态 |
| 🆕 `cancel_scheduled_task` | 取消/暂停/恢复定时任务 |
| 🆕 `batch_crawl_and_package` | 批量爬取+自动打包 ZIP |
| 🆕 `compress_crawl_results` | 分析压缩爬取结果为 2-3 页摘要 |
| 🆕 `parse_file_enhanced` | 增强文件解析（PPT/HTML/Markdown） |
| 🆕 `analyze_file_deep` | 深度文件分析（主题/财务/风险） |
| 🆕 `generate_research_report` | 生成图文并茂的研究报告 |
| 🆕 `export_research_report` | 导出报告为 Word/PPT/HTML/PDF |
| 🆕 `quick_crawl_summary` | 一键快速爬取+压缩摘要 |
| 🆕 `crawl_global_sentiment` | **v4.3** 一键全网舆情爬取（单/多机构 + 多媒体 + 情感筛选） |
| 🆕 `export_sentiment_report` | **v4.3** 导出舆情快照为 Word/Excel/CSV/JSON |
| 🆕 `list_sentiment_targets` | **v4.3** 查看 12 大类目标机构库 |
| 🆕 `list_sentiment_sources` | **v4.3** 查看媒体源（4 类商业财经媒体） |
| 🆕 `add_sentiment_target` | **v4.3** 新增自定义舆情目标 |
| 🆕 `analyze_risk_metrics` | **v5.0** 真实风险指标分析（年化/波动/回撤/夏普/卡玛） |
| 🆕 `analyze_product` | **v5.0** 产品综合分析（风格/组合复刻/相似推荐） |
| 🆕 `analyze_portfolio_replication` | **v5.0** 组合复刻分析 |
| 🆕 `get_structured_data` | **v5.0** 结构化市场数据（期货/宏观/Shibor/港股美股） |

## 项目结构

### 核心模块（必装）

```
cn-financial-scraper/
├── SKILL.md                      # Skill 完整说明（含FAQ和场景演示）
├── README.md                     # 本文件
├── setup_env.py                  # 一键安装脚本
├── mcp_server.py                 # MCP 服务器（64 个工具）
├── requirements.txt              # Python 依赖
├── _meta.json                    # 元数据
│
├── scripts/                      # 核心脚本
│   ├── __init__.py              # 包初始化
│   ├── http_utils.py            # HTTP 公共基础设施（限流/重试/缓存）
│   ├── scraper.py               # 基础爬虫（三级降级+自动重试）
│   ├── web_parser.py            # 网页解析（基金/ETF/FOF/股票）
│   ├── institution_scraper.py   # 机构爬虫
│   ├── announcement_scraper.py  # 公告爬取
│   └── data_validator.py        # 数据完整性验证
│
└── data/                         # 数据文件
    ├── institution_registry.json # 1330 家机构注册表
    └── *_list.json              # 各类机构名单（27类）
```

### 扩展模块（按需使用）

```
scripts/
├── research_report_scraper.py    # 券商研报（评级/分析师/目标价）
├── comprehensive_report_scraper.py # 综合报告统一入口
├── company_report_scraper.py     # 上市公司年报/半年报/季报
├── news_scraper.py               # 新闻爬取（东方财富/同花顺）
├── document_parser.py            # 文档解析（PDF/Word/Excel）
├── document_analyzer.py          # 文档分析整理（深度分析+批量整理+对比）
├── report_exporter.py            # 报告导出（PPT/PDF/Word/Excel）
├── batch_institution_crawler.py  # 批量爬取（并发+断点续爬）
├── report_indexer.py             # 全量报告索引（SQLite+断点续扫）
├── analyzer.py                   # 产品分析（风险指标+投资风格）
├── visualization_reporter.py     # 可视化报告（ASCII图表）
├── realtime_monitor.py           # 实时监控（动态页面检测）
├── full_institution_crawler.py   # 全量爬虫（从监管机构获取）
├── institution_updater.py        # 季度自动更新
├── scrapable_registry.py         # 可爬取机构注册表

# 🆕 v4.0 新增模块
├── crawl_scheduler.py            # 定期自动爬取调度引擎
├── crawl_packager.py             # 批量爬取结果 ZIP 打包
├── content_compressor.py         # 内容智能压缩（2-3页精华摘要）
├── enhanced_parser.py            # 增强文件解析（PPT/HTML/Markdown/CSV）
├── financial_writer.py           # 金融分析写作引擎 + ChartBuilder
├── report_templates.py           # 6套金融报告模板库
├── research_report_generator.py  # 研究报告全流程生成器
├── sentiment_chat.py             # 对话式舆情 NLU 入口
├── sentiment_crawler.py          # 全网舆情爬虫（60+ 商业财经媒体源）
├── sentiment_exporter.py         # 舆情报告导出
├── search_engine.py              # 百度/搜狗/DDG 多引擎搜索
├── structured_market_data.py     # 结构化市场数据（期货/宏观/Shibor）
├── analyzer.py                   # 真实风险指标分析（v5.0 重写）
├── browser_scraper.py            # 浏览器类人爬取（v5.0 增强）
├── akshare_fallback.py           # akshare 兜底适配器
└── http_utils.py                 # HTTP 公共基础设施（限流/重试/缓存）
```

### 模块功能速查

| 需求 | 使用模块 | 示例 |
|------|----------|------|
| 查询机构名单 | `institution_scraper.py` | `search_institution("华夏基金")` |
| 解析基金/股票 | `web_parser.py` | `parse_financial_product(url, "fund")` |
| 下载公告 | `announcement_scraper.py` | `AnnouncementManager().search("贵州茅台")` |
| 查询研报 | `research_report_scraper.py` | `BrokerReportManager().query("600519")` |
| 批量爬取 | `batch_institution_crawler.py` | `BatchInstitutionCrawler().crawl_by_type("基金")` |
| 生成报告 | `report_exporter.py` | `ReportExporter().export_to_ppt(data)` |
| 文档分析 | `document_analyzer.py` | `DocumentAnalyzer().analyze("report.pdf")` |
| 数据验证 | `data_validator.py` | `python scripts/data_validator.py` |
| 🆕 定期自动爬取 | `crawl_scheduler.py` | `create_scheduled_task("每日新闻", "daily")` |
| 🆕 批量打包ZIP | `crawl_packager.py` | `batch_crawl_and_package(names="华夏基金")` |
| 🆕 内容压缩摘要 | `content_compressor.py` | `compress_content(source, focus="财务")` |
| 🆕 增强文件解析 | `enhanced_parser.py` | `parse_file_enhanced("slides.pptx")` |
| 🆕 金融写作 | `financial_writer.py` | `generate_report(data, template_id="stock_research")` |
| 🆕 报告模板 | `report_templates.py` | `render_template("fund_evaluation", data)` |
| 🆕 研究报告生成 | `research_report_generator.py` | `generate_research_report("600519", "stock_research")` |

## 全量金融机构名单（2270 家 / 33 大类）

| 文件 | 内容 | 数量 |
|------|------|------|
| `data/institution_registry.json` | 统一注册表（含 URL） | 2270 家 |
| `data/state_owned_bank_list.json` | 国有大型商业银行 | 9 家 |
| `data/joint_stock_bank_list.json` | 股份制商业银行 | 12 家 |
| `data/policy_bank_list.json` | 政策性银行 | 3 家 |
| `data/city_commercial_bank_list.json` | 城市商业银行 | 157 家 |
| `data/rural_commercial_bank_list.json` | 农村商业银行 | 167 家 |
| `data/private_bank_list.json` | 🆕 民营银行 | 19 家 |
| `data/foreign_bank_list.json` | 🆕 外资法人银行 | 41 家 |
| `data/fund_company_list.json` | 基金管理公司 | 167 家 |
| `data/securities_list.json` | 证券公司 | 131 家 |
| `data/insurance_list.json` | 保险公司 | 181 家 |
| `data/trust_company_list.json` | 信托公司 | 67 家 |
| `data/private_fund_list.json` | 私募基金管理公司 | 64 家 |
| `data/foreign_institution_list.json` | 外资金融机构 | 60 家 |
| `data/futures_list.json` | 期货公司 | 181 家 |
| `data/futures_risk_mgmt_list.json` | 期货风险管理子公司 | 94 家 |
| `data/finance_company_list.json` | 企业集团财务公司 | 201 家 |
| `data/insurance_asset_list.json` | 保险资产管理公司 | 34 家 |
| `data/consumer_finance_list.json` | 消费金融公司 | 40 家 |
| `data/financing_guarantee_list.json` | 融资担保公司 | 30 家 |
| `data/financial_lease_list.json` | 金融租赁公司 | 94 家 |
| `data/auto_finance_list.json` | 汽车金融公司 | 41 家 |
| `data/wealth_management_list.json` | 银行理财子公司 | 33 家 |
| `data/fund_subsidiary_list.json` | 基金子公司 | 41 家 |
| `data/financial_holding_list.json` | 金融控股公司 | 63 家 |
| `data/third_party_list.json` | 第三方销售机构 | 35 家 |
| `data/reinsurance_list.json` | 再保险公司 | 11 家 |
| `data/money_broker_list.json` | 货币经纪公司 | 6 家 |
| `data/aic_list.json` | 金融资产投资公司(AIC) | 5 家 |
| `data/amc_list.json` | 🆕 金融资产管理公司 | 5 家 |
| `data/village_bank_list.json` | 🆕 村镇银行 | 60 家 |
| `data/insurance_broker_list.json` | 🆕 保险经纪公司 | 48 家 |
| `data/insurance_assessor_list.json` | 🆕 保险公估公司 | 36 家 |
| `data/city_investment_list.json` | 城投机构 | 102 家 |

> 口径说明：v7.0.0 起名单数字 = 实际 JSON 数据条数（此前部分类型 count 字段为宣称值，已修正）。
> 扩充引擎 `scripts/institution_expander.py` 支持 live 名录直连（基金/期货）、
> curated 精选数据（`data/curated/*.json`）与 list 文件反向吸收三路合并去重。

```bash
python -m scripts.scrapable_registry stat          # 统计
python -m scripts.scrapable_registry list 基金管理公司  # 按类列出
python -m scripts.scrapable_registry search 华夏     # 关键词搜索
```


## 🆕 v4.3 全网舆情爬虫 — 实战场景

### 场景 A — 单机构 + 单一情感（对话式）

> "帮我爬一下贵州茅台最近7天的舆情"

```python
from scripts import chat_handle
print(chat_handle("帮我爬一下贵州茅台最近7天的舆情")["reply"])
```

对话式触发后，引擎自动完成：
1. 抽取目标：贵州茅台（listed_company）
2. 媒体默认：authoritative + financial_vertical
3. 时间窗：7 天
4. 情感：负面优先（用户用了"舆情" 一词）
5. 输出：对话提示 + data/sentiment_snapshots/<id>.json

### 场景 B — 多机构 + 负面新闻 + 多格式导出

> "看下华夏基金、招商银行、中国人寿过去3天的负面新闻，并导出 Excel/Word"

```python
from scripts import crawl_sentiment, export_sentiment
snap = crawl_sentiment(
    targets=["华夏基金", "招商银行", "中国人寿"],
    days=3, negative_only=True,
    source_categories=["authoritative", "financial_vertical"],
)
outputs = export_sentiment(snap, fmt="all")
for k, v in outputs.items():
    print(k, v)
```

### 场景 C — 定时任务

> "每天早上 9 点爬一下银行的舆情并导出全部格式"

```python
schedule_crawl_task(
    name="每日银行舆情",
    frequency="daily",
    action="crawl_sentiment_export",
    sentiment_categories=["commercial_bank"],
    sentiment_source_categories=["authoritative", "financial_vertical"],
    sentiment_negative_only=True,
    sentiment_export_format="all",
)
```

### 场景 D — 类别查看 / 自定义目标

```python
from scripts import list_sentiment_targets, add_custom_sentiment_target
print(list_sentiment_targets())
add_custom_sentiment_target("custom", "恒生电子")
```

### CLI 调试

```bash
python -m scripts.sentiment_crawler --stats
python -m scripts.sentiment_crawler --list-sources
python -m scripts.sentiment_crawler --list-targets
python -m scripts.sentiment_crawler     --categories fund_company,listed_company     --source-categories authoritative,financial_vertical     --days 7 --negative-only --max 30
```

### 严重度阈值

| 严重度（正面） | 阈值（情感分数） |
|----------------|------------------|
| 低度利好 | 6 – 14 |
| 中度利好 | 15 – 29 |
| 重大利好 | ≥ 30 |

| 严重度（负面） | 阈值 |
|----------------|------|
| 低度关注 | 6 – 11 |
| 中度舆情 | 12 – 24 |
| 高危舆情 | ≥ 25 |

## 能力边界

| 类别 | 说明 |
|------|------|
| ✅ **完全支持** | 机构名单查询、基金/ETF/FOF/股票产品解析、A股公告搜索下载、券商研报、新闻资讯、舆情监控、批量爬取（断点续爬）、文档解析（PDF/Word/Excel/PPT/HTML）、报告导出（Word/PPT/Excel）、风险指标分析、结构化市场数据（期货/宏观/Shibor） |
| ❌ **不支持** | 需登录的页面（如微信公众号后台、券商内部系统）、付费墙内容（如 Wind 终端数据）、实时 WebSocket 推送、移动端 APP 内嵌页面、验证码自动破解（需第三方打码服务） |
| ⚠️ **部分支持** | 动态渲染页面（需 Playwright，用 `mode="realtime"`）、反爬极严的网站（如某些银行官网，成功率 30-50%）、大批量爬取（需控并发 ≤5 + 断点续爬）、海外网站（需代理，部分有地域限制） |

**预期成功率**：天天基金 95%+ / 东方财富 90%+ / 同花顺 85%+ / 基金公司官网 70-90% / 银行官网 30-50% / 反爬严格的网站 20-40%。

> 💡 **提示**：如果你的目标网站反爬严格，建议先用 `mode="realtime"` 走浏览器，配合 proxy 和低频率（≥3 秒/请求）。

## 数据验证

```bash
# 验证数据完整性
python scripts/data_validator.py

# 验证结果示例
# ✅ institution_registry.json: 验证通过，共 1330 家机构
# ✅ fund_company_list.json: 验证通过，共 160 家机构
# ...
# 📈 汇总: 28/28 通过
```

## ❓ 常见问题（FAQ）

> 📘 更多故障排查见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)（9 个章节 / 30+ 个解法 / 错误码速查表）
> 🔒 安全审计与漏洞披露见 [SECURITY.md](SECURITY.md)

### 🔥 高频问题

| 问题 | 解决方案 |
|------|----------|
| 舆情爬取返回空 | 1）检查目标名称（`list_sentiment_targets`）；2）扩大时间范围（`days=7`）；3）增加媒体源类别 |
| 结构化数据返回 None | 需安装 akshare：`pip install akshare`，未装时自动返回 None 不报错 |
| 动态页面爬不到内容 | 默认 `mode="static"` 只走 HTTP，SPA 页面需 `mode="realtime"`（需 Playwright） |
| 银行官网成功率低 | 银行反爬严格（30-50%），建议：浏览器模式 + proxy + 低频率（≥3秒/请求） |
| pip 安装很慢 | 国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt` |
| `ModuleNotFoundError: playwright` | `pip install playwright && playwright install chromium` |

### 安装问题

| 问题 | 解决方案 |
|------|----------|
| playwright 安装失败 | 运行 `playwright install --with-deps chromium`，或设置镜像 `set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright` |
| 模块找不到 | 运行 `pip install -r requirements.txt` |
| 多 Python 环境冲突 | 详见 [TROUBLESHOOTING.md §1.4](TROUBLESHOOTING.md#14-不同-python-解释器混乱) |

### 爬取问题

| 问题 | 解决方案 |
|------|----------|
| 返回空数据 | 使用动态渲染：`mode="realtime"` |
| 频繁超时 | 增加超时时间：`timeout=60` |
| 验证码拦截 | 降低爬取频率，稍后重试；或接入第三方打码服务 |
| IP 被封 403 | 暂停 5-10 分钟 + 切换代理 + 降频（详见 [TROUBLESHOOTING.md §3.1](TROUBLESHOOTING.md#31-ip-被封--一直-403)） |
| 中文乱码 | 用 `decode_response()` 自动嗅探编码（详见 [TROUBLESHOOTING.md §4.1](TROUBLESHOOTING.md#41-中文乱码--unicodedecodeerror)） |

## 支持的数据源

| 类型 | 平台 |
|------|------|
| 实时行情 | 🆕 新浪财经 (hq.sinajs.cn) |
| 快讯电报 | 🆕 财联社 (cls.cn) |
| 深度分析 | 🆕 华尔街见闻 (wallstreetcn.com) |
| 可转债 | 🆕 集思录 (jisilu.cn) |
| 官方公告 | 上交所/深交所 (sse.com.cn/szse.cn) |
| 基金 | 天天基金、东方财富、各基金公司官网 |
| ETF | 各大交易所、天天基金 |
| 公告 | 天天基金、巨潮资讯 |
| 研报 | 东方财富研报中心 |
| 新闻 | 东方财富、同花顺、财联社 |
| 行情 | 雪球 (xueqiu.com) |
| 组合 | 且慢、蛋卷基金、雪球 |
| 宏观 | 🆕 CPI/PPI/PMI/GDP/M2 零依赖 HTTP 直连（东财 datacenter）+ akshare 兜底 |

## 许可证

MIT License
