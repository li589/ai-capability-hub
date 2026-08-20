---
name: fund-advisor
version: 10.1.0
description: |
  基金投资智能顾问 v10.0 — 在 v9 七大能力体系之上新增：基金经理对话（蒸馏观点/范围/新闻采访）、
  基金跟仓（持仓变动对比/镜像组合/跟仓信号/经理变动监控）、客户行为心理画像（6 维偏差+沟通策略）、
  模块化定制报告（8 模块×3 模板+批量订阅）、公募产品档案增强（投资范围/费率/业绩序列）。
  纯本地运行，零配置；可选 DeepSeek key 启用 LLM 观点蒸馏。
author: 社区开发者
license: MIT
triggers:
  keywords: [客户经理, 持仓怎么样, 亏了, 推荐基金, 晚报, 周报, PPT报告,
    量化分析, 导入持仓, 导出Excel, 上传持仓, 上传截图,
    上传文件, 基金查询, 市场行情, 净值走势, 基金经理, 风险评测,
    风格问卷, 风格定制, 调仓, 再平衡, 多源评级, 宏观经济, 持仓跟踪,
    配置方案, 风险问卷, 适当性, 检视, 学习, 校准,
    回测, 历史模拟, 压力测试, 因子分析, 情景分析, What-If,
    集中度, 相关性, Tushare, 动量策略, 风险平价, 轮动, 重建数据,
    基金经理对话, 经理访谈, 经理人设, 经理观点, 经理新闻, 跟仓, 跟投, 镜像组合,
    持仓变动, 经理变动, 心理画像, 行为偏差, 投资风格, 损失厌恶, 沟通策略,
    定制报告, 批量报告, 报告订阅, 投资范围, 基金费率, 季报观点]
  patterns:
    - "导(入|出) (持仓|Excel|CSV|截图)"
    - "(上传|识别) (截图|文件|持仓)"
    - "(推荐|分析) (基金|经理|公司)"
    - "(量化|持仓|基金) (分析|评测|对比)"
    - "经理 (档案|介绍|分析|怎么样|对话|访谈|观点|人设)"
    - "(跟仓|跟投|镜像).*(经理|基金|持仓)"
    - "(持仓|经理).*(变动|变更|换仓)"
    - "(生成|导出) (报告|PPT|周报|晚报|月报|定制报告)"
    - "(风格|问卷|心理|行为) (定制|组合|画像|偏差)"
    - "(调仓|再平衡|跟踪|检视) (持仓|收益|组合)"
    - "(多源|晨星|好买) 评级"
    - "(风险|问卷|心理|行为) (评测|打分|画像)"
    - "(配置|组合) (方案|规划|优化)"
    - "(学习|校准) (建议|参数|报告)"
    - "(回测|模拟).*(动量|均值回归|风险平价|轮动|策略)"
    - "(重建|更新).*(数据|持仓|净值)"
---

# 基金投资 AI 客户经理 v10.0

> 口语化对话 | 专业投顾建议 | 六维组合跟踪 | 三层配置体系 | 量化回测 | 多因子分析 | 情景模拟 | 自进化学习
> 🆕v10.0：基金经理对话 | 基金跟仓 | 客户行为心理画像 | 模块化定制报告 | 产品档案增强

## When to Use

- 基金话题：持仓、净值、基金经理、推荐、亏损、止盈止损、组合配置
- 导入/导出持仓（截图、Excel、CSV、Word、PDF）
- 量化分析、基金对比、组合推荐、回测、因子、情景
- 🆕与基金经理「对话」（蒸馏其季报观点/投资范围/新闻采访，以经理口吻回答）
- 🆕基金跟仓（持仓季度变动、镜像组合、跟仓信号、经理变动监控）
- 🆕客户心理与投资风格把控（行为偏差画像 + 沟通策略）
- 🆕按客户要求生成定制定期报告（8 模块自由组合 + 批量订阅）
- 生成报告（周报、月报、PPT、定制报告）

**Don't use for**：股票短线交易、非基金理财、需持牌资质的投顾业务、未经授权的实盘跟单。

## 快速上手

```bash
# 只需 Python 3.8+ 标准库，零 pip 依赖
python -m fund_advisor check    # 自检（含 v10 新功能模块）
python -m fund_advisor mcp      # 启动 MCP Server（48 工具）
python -m fund_advisor test     # 运行测试（~223）
python scripts/update_data.py full   # 全量重建（v9 零依赖 + v10 产品档案增强）
```

> 可选：复制 `.env.example` 为 `.env` 填 DeepSeek API Key 启用 LLM 观点蒸馏与智能对话。

## 能力总览

| 能力 | 说明 | 关键脚本 |
|---|---|---|
| **投顾** | 问卷打分 + 适当性校验 + 建议分级 + 定投规划 + 调仓成本 | `analysis/asset_allocator.py` `dca_planner.py` `fee_calculator.py` |
| **投后追踪** | 六维 Dashboard + 周/月检视 + 绩效/回撤归因 + 告警 | `analysis/performance_tracker.py` `review_engine.py` `position_tracker.py` |
| **配置** | SAA/TAA 三层架构 + 下滑曲线 + 核心卫星 + 风险平价/均值方差 | `analysis/asset_allocator.py` `portfolio_rebalancer.py` |
| **量化回测** 🆕 | 组合历史模拟 + 4 策略真实回测（动量/均值回归/风险平价/股债轮动）+ 压力测试 | `analysis/backtest_engine.py` |
| **多因子** 🆕 | 六维因子暴露（动量/波动/质量/价值/情绪/宏观）+ 同业强度（v9 价值/情绪真实穿透） | `analysis/factor_engine.py` |
| **情景模拟** 🆕 | 市场冲击/换仓/利率/通胀/板块领涨/汇率贬值 6 情景 What-If | `analysis/scenario_simulator.py` |
| **预测** | 基金/组合涨跌预测（多因子 + 蒙特卡洛 + VaR/CVaR） | `analysis/fund_predictor.py` |
| **自进化** | 建议留痕 → 事后回填 → 命中统计 → 参数校准 → 策略库进化 | `scripts/learning/` |
| **持仓导入** | 截图 OCR / Excel / CSV / Word / PDF / URL（沙箱校验） | `client_manager/holdings_importer.py` |
| **报告** | 周报/月报/PPT/Excel/Word/PDF 导出 | `client_manager/report_*` |
| **基金经理对话** 🆕 | 蒸馏经理履历/风格/投资范围/季报观点/新闻采访，以经理口吻回答（可选 LLM 蒸馏） | `analysis/manager_persona.py` `manager_dialogue.py` |
| **基金跟仓** 🆕 | 持仓季度变动对比 + 镜像组合（加权/等权）+ 跟仓信号 + 经理变动监控（含合规提示） | `analysis/manager_follower.py` `data_collection/holdings_history.py` `maintenance/manager_change_monitor.py` |
| **客户行为心理画像** 🆕 | 10 题行为问卷 + 情绪/持仓行为 → 6 维偏差 + 心理类型 + 沟通策略 | `client_manager/behavioral_profile.py` |
| **模块化定制报告** 🆕 | 8 模块×3 模板 + 批量订阅生成 | `client_manager/report_generator.py` `report_scheduler.py` |
| **产品档案增强** 🆕 | 投资目标/范围/费率/业绩序列入库 | `data_collection/fund_profile_collector.py` |

## 数据与重建（零依赖）

- **数据文件**：`data/` 下基金经理/产品/公司/持仓/评级/观点/新闻等 JSON（列式压缩，`is_columnar` 双变体兼容）
- **占位骨架（v10.0.1 轻量化）**：核心数据为空壳占位，包体 2.1MB；**真实数据备份于包外 `fund-advisor-data-backup/`**（4,288 经理/27,516 产品/212 持仓/595 新闻/2026Q2 跟仓基线）
- **全量重建**：`python scripts/update_data.py full` → 零依赖 stdlib 链路（约 8-10 分钟），产出蒸馏库统一列式格式 + 产品档案增强（投资范围/费率）
- **增量更新**：`update_data.py update` → `monthly_updater`（格式与全量一致）
- **数据新鲜度**：`update_data.py check` 检测占位（count==0 → 提示重建）与超期
- **净值缓存**：`data_collection/nav_cache.py` SQLite，`warm_cache` 在线拉取

## 核心 API

```python
# 回测（v9 四策略真实模拟）
from analysis.backtest_engine import BacktestEngine
r = BacktestEngine().run_strategy_backtest("momentum", ["000001","000002"], "2026-01-01", "2026-12-31",
                                           params={"top_k": 2}, benchmark_code="000300")

# 因子（v9 价值/情绪真实穿透）
from analysis.factor_engine import FactorEngine
exp = FactorEngine().compute_factor_exposures("000001")
# exp["degraded"] 标记无数据回退的因子；exp["notes"] 说明

# 情景（v9 全模板）
from analysis.scenario_simulator import ScenarioSimulator
r = ScenarioSimulator().run_scenarios([{"fund_code":"000001","weight":50,"amount":50000}])

# 配置 / 投顾
from analysis.asset_allocator import build_allocation_plan
from analysis.dca_planner import plan_dca
```

## MCP 工具（48 个）

**持仓**：import_holdings_screenshot/docx/pdf/url、auto_import_file、export_holdings_excel/csv
**客户**：list_clients、get_client_holdings、get_import_history、🆕chat_with_client
**查询**：query_fund、query_manager、get_advisor_report、compare_managers
**预测**：predict_fund_trend、predict_portfolio_trend
**多源**：get_fund_multi_source、get_macro_real、build_style_portfolio、track_portfolio_returns、get_rebalance_advice、get_fund_ratings
**组合**：run_portfolio_healthcheck、get_attribution_analysis、score_risk_profile、build_allocation_plan、get_portfolio_metrics、generate_review_report、log_advice、get_learning_report
**定投**：plan_dca_investment、estimate_rebalance_cost
**回测/因子/情景**：run_backtest、stress_test_portfolio、analyze_factor_exposures、simulate_scenario
**🆕v10 经理对话**：chat_with_manager、get_manager_persona、get_manager_news
**🆕v10 跟仓**：compare_holdings_change、build_mirror_portfolio、track_mirror_portfolio、get_follow_signals
**🆕v10 心理画像**：assess_client_profile、get_client_communication_guide
**🆕v10 定制报告**：generate_custom_report、generate_batch_reports

## 版本历史

| 版本 | 要点 |
|---|---|
| v10.1 | 测试优化与健壮性升级：修复 PPT 生成器语法错误、全覆盖编译烟囱测试、取消弃用警告屏蔽、元数据一致性 |
| v10.0 | 🆕经理对话/跟仓/行为心理画像/模块化报告/产品档案增强；MCP 36→48；测试 ~145→~218 |
| v9.0 | 三件套完整实现 + 数据稳定性 + 重建零依赖 + 测试 117→~145 |
| v8.2 | 包轻量化（数据占位化）+ 测试适配 |
| v8.1 | 量化跟踪修复 + 预测可复现 + 缓存失效 + 性能优化 |
| v8.0 | 量化回测 + 多因子筛选 + 情景模拟 + Tushare |
| v7.x | 组合配置/定投/投后/预测引擎演进 |

## 目录速查

```
scripts/
├── analysis/        # 投顾/配置/回测/因子/情景/预测/经理对话/跟仓（v10 +3 文件）
├── client_manager/  # 持仓导入/对话/报告/告警/行为画像/报告调度（v10 +3 文件）
├── data_collection/ # 数据采集/重建/缓存 + 产品档案/经理新闻/持仓历史（v10 +3 文件）
├── learning/        # 自进化学习
├── maintenance/     # 增量/全量更新、调度、经理变动监控（v10 +1 文件）
├── fund_advisor_paths.py  # 路径 + 列式解码 + 持仓归一化 + 持仓历史（v10）
data/                # 占位骨架（update_data.py full 重建）
tests/               # ~223 测试（python -m pytest tests/）
```

## 常见问题

- **查询返回"未找到"**：数据为占位骨架，运行 `python scripts/update_data.py full` 重建（零依赖）
- **MCP 无法启动**：`pip install mcp`；48 工具注册需 mcp 包
- **经理对话/观点为空**：先跑 `view_collector.py`（季报观点）、`manager_news_collector.py`（新闻）、`update_data.py full`（档案）
- **跟仓无历史对比**：v10 首次刷新建立基线，下一季起 `compare_holdings_change` 可对比
- **LLM 对话**：需在 `.env` 配 DeepSeek API Key（离线降级为规则+真实数据回答）
- **导入 URL 被拒**：v9 沙箱仅允许 http/https + 基金平台白名单域名

## 免责声明

> ⚠️ **本工具仅供学习参考，不构成任何形式的投资建议。** 投资有风险，决策需谨慎。
