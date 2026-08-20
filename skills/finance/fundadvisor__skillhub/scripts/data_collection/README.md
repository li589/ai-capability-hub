# 数据采集脚本说明

本目录包含 22 个采集脚本，各司其职，勿合并（功能分散，调用方分散）。

## 一线采集（推荐使用）

| 脚本 | 用途 | 调用方 |
|------|------|--------|
| `full_collector.py` | 全量数据采集入口（天天基金 + 基金业协会） | `monthly_updater.py` |
| `enhanced_collector.py` | 增强采集（天天基金 + 东方财富） | `monthly_updater.py` |
| `view_collector.py` | 经理观点采集（季报/年报） | `monthly_updater.py` |
| `extended_holdings_collector.py` | 持仓明细扩展采集 | `monthly_updater.py` |
| `report_opinion_collector.py` | 报告观点采集 | `monthly_updater.py` |

## 二线采集（专题用）

| 脚本 | 用途 |
|------|------|
| `amac_collector.py` | 基金业协会（AMAC）数据 |
| `eastmoney_collector.py` | 东方财富单一来源采集 |
| `extended_collector.py` | 天天基金扩展字段 |
| `external_data_collector.py` | 外部数据补充 |
| `news_collector.py` | 新闻情感分析（东方财富/新浪/凤凰） |
| `guba_comment_scraper.py` | 股吧评论采集 |
| `media_collector.py` | 媒体资讯采集 |
| `report_parser.py` | 报告解析 |
| `view_generator.py` | 观点生成（本地规则） |
| `update_humanized_speech.py` | 话术人性化更新（需 DeepSeek API） |

## 工具脚本（一次性使用）

| 脚本 | 用途 |
|------|------|
| `fix_data.py` | 修正持仓数据库类型字段 |
| `fill_style.py` | 根据持仓补充风格标签 |
| `database_builder.py` | 数据库构建（初始化用） |
| `enhanced_manager_updater.py` | 经理信息增强更新 |
| `manager_full_collector.py` | 全量经理采集（天天基金） |
| `company_product_collector.py` | 公司产品采集 |
| `media_collector.py` | 媒体资讯采集 |
| `fee_collector.py` | 费率数据采集 |
| `extended_collector.py` | 天天基金扩展字段 |
| `guba_comment_scraper.py` | 东方财富股吧评论 |
| `update_humanized_speech.py` | 话术拟人化（需 DeepSeek API，已废弃） |

## 说明

- **不要合并**：各采集脚本职责单一，调用方分布在不同模块，合并反而造成耦合
- **月度更新唯一入口**：`monthly_updater.py`（通过 cron job 调度），其余脚本均为辅助
- `update_humanized_speech.py` 依赖 DeepSeek API，已废弃不用
