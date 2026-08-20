# fund-advisor v8.2

> 基金投资智能顾问 — 口语化对话 / 专业投顾建议 / 组合配置 / 投后检视 / 量化分析 / 自进化学习



## 零依赖:core skill 只需 Python 3.8+

本 skill 是公开分发的，每个人用自己的 DeepSeek key（或换其他 OpenAI 兼容端点）。

```bash
# 1. 复制模板
cp .env.example .env       # macOS / Linux
copy .env.example .env     # Windows PowerShell

# 2. 编辑 .env，填入你自己的 key
DEEPSEEK_API_KEY=sk-你的key
```

- key 从 [DeepSeek 控制台](https://platform.deepseek.com/api_keys) 申请
- `.env` 已在 `.gitignore` 中，**不会被提交**
- **不填也能跑**：量化分析等需要 LLM 的功能会走 OFFLINE 占位模式，其它功能（数据查询、风格匹配、持仓导入）完全可用
- 切换其他模型：编辑 `scripts/llm_providers.py`，支持 9 大国产模型（DeepSeek / 通义 / 智谱 / Kimi / 豆包 / 混元 / 星火 / 小米 / MiniMax）+ 自定义 OpenAI 兼容端点


## 一句话介绍

一个**完全独立运行**的基金投资智能顾问 skill：内置 4,270 位基金经理档案、164 家公司分析、7 维量化信号模型、对话引擎、MCP Server（48 个工具）、9 大国产大模型适配层。v10.0 新增基金经理对话（蒸馏观点/范围/新闻采访）、基金跟仓（持仓变动对比/镜像组合/跟仓信号/经理变动监控）、客户行为心理画像（6 维偏差+沟通策略）、模块化定制报告（8 模块×3 模板+批量订阅）、公募产品档案增强（投资范围/费率/业绩序列）；**v10.0.1 彻底轻量化（包体 2.1MB）**：真实数据（4,288 经理等，共 8.2MB）备份于包外 `fund-advisor-data-backup/`，首次 `update_data.py full` 联网重建（约 8-10 分钟）；v8.0 新增回测/因子/情景模拟；v7.3 新增趋势预测。所有数据存本地，不依赖云端服务。

**任意 agent 拿到这个目录，3 行命令就能跑起来**：

```bash
python clean.py            # 上传/打包前清理（__pycache__/pyc、nav_cache、reports）
python -m fund_advisor check    # 自检
python scripts/update_data.py full   # 首次联网重建数据（约 8-10 分钟）
```

```bash
cd fund-advisor
./install.sh        # 或 Windows: install.bat
python -m fund_advisor
```

## 30 秒上手

```bash
# 1. 一键自检 — 看环境是否就绪
python -m fund_advisor check

# 2. 作为 MCP Server（stdio 协议）
python -m fund_advisor mcp

# 3. 跑全部测试
python -m fund_advisor test
```

可执行命令清单：

| 命令 | 作用 |
|------|------|
| `python -m fund_advisor mcp` | 启动 MCP Server（stdio 协议） |
| `python -m fund_advisor check` | 自检：依赖/数据/配置 |
| `python -m fund_advisor test` | 跑全部测试 |
| `python -m fund_advisor version` | 显示版本 |

## 三种部署模式

### 零依赖:core skill 什么都不装

```bash
git clone <repo>            # 或下载 zip
cd fund-advisor
python -m fund_advisor check    # 自检
python -m fund_advisor mcp      # MCP Server
```

如需 pip 安装后使用 console 脚本:

```bash
pip install -e .                # 可选，core 不装也能跑
fund-advisor mcp
```

## 零依赖 / 零配置

**core skill 什么包都不装**。v8.2 包轻量化（约 5MB 季度数据不随包，首次 `python scripts/update_data.py full` 联网重建）；v8.1 修复实时净值跟踪、基金预测稳定随机种子、数据缓存失效；v8.0 新增回测/因子/情景模拟；v7.3 新增趋势预测。重建后内置 4,270 位经理、164 家公司、27,304 只产品、52 条经理观点，所有量化分析、对话、查询、统计功能都不需要联网。

只有"接入 LLM 做智能对话"才需要 API Key（可选）：

```bash
# 设置环境变量
export DEEPSEEK_API_KEY=sk-your-key-here
# 或编辑 .env 文件（已在 .gitignore）

# 验证
python -c "from analysis.config import is_offline_mode; print('offline' if is_offline_mode() else 'online')"
```

## 主要能力

| 能力 | 入口 | 说明 |
|------|------|------|
| 智能对话 | `ClientManager().chat(user_id, message)` | 17 类意图识别 + 情感回复 + 口语化 |
| 持仓导入 | `HoldingsImporter().import_from_*` | 截图OCR / Word / PDF / Excel / CSV / URL |
| 量化分析 | `FundQuantAnalyzer().analyze_fund(code)` | 7 维信号：均线偏离/RSI/布林带/动量/波动率/趋势/持仓集中度 |
| 基金对比 | `ComparisonEngine().compare_managers([...])` | 横向对比 + 归一化走势图 |
| 组合推荐 | `PortfolioRecommenderV2().recommend_portfolio_v2(...)` | 5 套餐 × 多维度推荐 |
| 基金经理话术 | `FundAdvisorSpeech().ask(question, manager_name=...)` | 基于经理档案数据 + 模板生成第一人称口吻回复 |
| 用户画像 | `UserQuantitativeAssessment().assess_investment_profile(...)` | 8 维量化评估 |
| 心态跟踪 | `EmotionalTracker().record_emotion(...)` | 投资情绪记录 + 趋势分析 |
| 止盈止损 | `AlertSystem().daily_check(...)` | 阈值告警 + 历史回看 |
| 资产配置 | `build_allocation_plan(...)`（asset_allocator） | 问卷打分/SAA/下滑曲线/核心卫星/优化器/适当性 |
| 投后检视 | `ReviewEngine().weekly/monthly_review(...)` | 六维Dashboard + 归因 + 告警 + 检视日 |
| 指标分析 | `perf_metrics.compute_all_metrics(...)` | 夏普/索提诺/卡玛/IR/Beta/滚动指标 |
| 自学习 | `LearningEngine().log_advice/calibrate(...)` | 建议留痕→回填→校准→策略进化 |

MCP 工具列表（48 个，stdio 协议）：

```
# 持仓导入/导出与客户管理
import_holdings_screenshot   从截图OCR识别持仓
import_holdings_docx         从 Word 导入
import_holdings_pdf          从 PDF 导入
import_holdings_url          从链接爬取
export_holdings_excel        导出 Excel
export_holdings_csv          导出 CSV
auto_import_file             智能导入（按扩展名）
list_clients                 列出客户
get_client_holdings          查客户持仓
get_import_history           查导入历史
# 查询与多源数据
query_fund                   查询基金详情（按代码）
query_manager                查询基金经理档案（按姓名）
get_fund_multi_source        多源聚合查询
get_macro_real               真实宏观数据
get_fund_ratings             多源评级聚合
# 投顾/配置/跟踪
build_style_portfolio        风格定制组合
track_portfolio_returns      持仓收益跟踪
get_rebalance_advice         调仓建议
run_portfolio_healthcheck    8维健康评分(80分)
get_attribution_analysis     绩效归因分析
score_risk_profile           风险问卷打分
build_allocation_plan        一站式配置方案
get_portfolio_metrics        组合全指标
generate_review_report       周/月投后检视
plan_dca_investment          定投规划(v7.1)
estimate_rebalance_cost      调仓成本测算(v7.1)
get_advisor_report           投顾报告(v7.2)
compare_managers             经理对比(v7.2)
# 自学习
log_advice                   建议留痕
get_learning_report          学习报告(命中率/校准参数)
```

完整 API 见 [SKILL.md](./SKILL.md)。

## 数据文件

> **v8.2 轻量化**：以下数据库（合计约 5MB）不随 skill 包分发，`data/` 为占位骨架。
> 首次使用前运行 `python scripts/update_data.py full` 联网重建，重建后各表数量恢复下述水平。

| 文件 | 内容 | 数量 | 大小 |
|------|------|------|------|
| `data/fund_managers_distilled.json` | 基金经理档案 | 4,270 | 390 KB |
| `data/fund_companies_distilled.json` | 基金公司档案 | 164 | 103 KB |
| `data/fund_products.json` | 基金产品目录 | 27,304 | 2.4 MB |
| `data/holdings_database.json` | 全市场经理现任基金十大重仓（2,598 只基金，v7.2 紧凑 h/m 格式，季度更新，当前 2026Q2） | 季度更新 | 977 KB |
| `data/manager_views.json` | 经理观点（定期报告 PDF 摘录） | 52 | 119 KB |
| `data/external_data.json` | 基金评级 + 分析 + 盈利概率 | 18,111 | 1.1 MB |
| `data/style_profiles.json` | 风格画像 | 6 类 | 1 KB |

**月度更新**：每月第 1 工作日自动执行 `python -m fund_advisor` 启动后，调用 `python -c "from scripts.maintenance.monthly_updater import run; run()"` 即可从天天基金网更新全量数据。

## 目录结构

```
fund-advisor/
├── fund_advisor/                 # 统一入口包
│   ├── __init__.py
│   ├── __main__.py               # python -m fund_advisor
│   └── fund_advisor_bootstrap.py # 零依赖自检
├── SKILL.md                      # skill 描述与触发词
├── README.md                     # 本文件
├── CHANGELOG.md                  # 变更日志
├── LICENSE                       # MIT
├── pyproject.toml                # Python 打包 + console_scripts
├── pytest.ini                    # 测试配置
├── requirements.txt              # 依赖
├── install.sh                    # macOS/Linux 一键安装
├── install.bat                   # Windows 一键安装
├── Dockerfile                    # 容器镜像
├── docker-compose.yml            # 一键容器启动
├── .github/workflows/test.yml    # CI: 3 OS × 5 Python 版本
├── _meta.json                    # skill 元数据
├── .skillhub.json                # SkillHub 发布清单
├── .claude-plugin/plugin.json    # Claude Code 插件清单
├── mcp_server.py                 # MCP Server 入口（48 个工具）
├── scripts/                      # 业务代码
│   ├── fund_advisor_paths.py     # 统一路径
│   ├── llm_providers.py          # 大模型统一适配层
│   ├── client_manager/           # 客户端/对话/持仓 (11 个)
│   ├── analysis/                 # 量化分析/配置/检视 (19 个)
│   ├── learning/                 # 自进化学习闭环 (v7.0)
│   ├── data_collection/          # 数据采集 (26 个)
│   └── maintenance/              # 维护 (6 个)
├── data/                         # 本地 JSON 数据库
├── assets/                       # 图标资源
├── tests/                        # 单元测试 (116 个)
└── references/                   # API 文档
```

## 运行测试

```bash
pip install pytest
python -m pytest tests/ -v
```

**全部通过**（跨平台 CI：Windows × Python 3.11）

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `python: command not found` | 未装 Python | 安装 Python 3.8+，macOS：`brew install python@3.11`，Win：从 python.org 下载 |
| `mcp` 包缺失 | 未装依赖 | `pip install mcp` |
| MCP 工具列表为空 | mcp 包未装 | `pip install mcp` |
| 截图 OCR 失败 | 未装 Tesseract | 见 [OCR 配置](https://github.com/UB-Mannheim/tesseract/wiki) |
| `auto_import_file` 不识别 .xlsx | 老版本 | 升级到 v5.3.2 |

## 安全说明

- **数据 100% 本地**：所有基金经理/公司/持仓数据存 `data/`，不上传云端
- **API Key 存系统目录**：`%APPDATA%\FundAdvisor\llm_config.json`（跨平台标准位置）
- **截图/Word/PDF 上传后立即处理**：处理完不入库，除非用户指定 `client_id`
- **不构成投资建议**：本工具仅供辅助研究，投资决策由用户自行承担

## 许可证

MIT — 见 [LICENSE](./LICENSE)

## 贡献

欢迎提交 Issue / PR。修改前请：

1. 跑 `python -m fund_advisor test` 确认全绿
2. 新功能补测试
3. 公开 API 变更请更新 `SKILL.md`
