# 用户指南 v10.0

fund-advisor 基金投资智能顾问 — 快速上手。**纯本地运行，零配置，下载即用。**

## 1. 安装

只需 Python 3.8+，无需 pip install：

```bash
# Windows：双击 install.bat 一键完成
# 或手动执行：
python -m fund_advisor check    # 自检 -> 确认环境正常
python -m fund_advisor mcp      # 启动 MCP Server
python -m fund_advisor test     # 运行测试
```

## 2. 启动

### MCP Server（推荐）

```json
{
  "mcpServers": {
    "fund-advisor": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/fund-advisor"
    }
  }
}
```

### MCP 工具（48 个）

| 类别 | 工具 |
|------|------|
| 持仓导入 | `import_holdings_screenshot`, `import_holdings_docx`, `import_holdings_pdf`, `import_holdings_url`, `auto_import_file` |
| 持仓导出 | `export_holdings_excel`, `export_holdings_csv` |
| 客户管理 | `list_clients`, `get_client_holdings`, `get_import_history`, 🆕`chat_with_client` |
| 基金查询 | `query_fund`, `query_manager` |
| 多源数据 | `get_fund_multi_source`, `get_macro_real`, `get_fund_ratings` |
| 风格定制 | `build_style_portfolio` |
| 跟仓调仓 | `track_portfolio_returns`, `get_rebalance_advice` |
| 投顾分析 | `run_portfolio_healthcheck`, `get_attribution_analysis`, `score_risk_profile`, `get_advisor_report`, `compare_managers` |
| 组合配置 | `build_allocation_plan`, `plan_dca_investment`, `estimate_rebalance_cost` |
| 投后检视 | `get_portfolio_metrics`, `generate_review_report` |
| 预测引擎 | `predict_fund_trend`, `predict_portfolio_trend` |
| 自学习 | `log_advice`, `get_learning_report` |
| 🆕v10 经理对话 | `chat_with_manager`, `get_manager_persona`, `get_manager_news` |
| 🆕v10 基金跟仓 | `compare_holdings_change`, `build_mirror_portfolio`, `track_mirror_portfolio`, `get_follow_signals` |
| 🆕v10 行为心理 | `assess_client_profile`, `get_client_communication_guide` |
| 🆕v10 定制报告 | `generate_custom_report`, `generate_batch_reports` |

### v10 新功能快速示例

```bash
# 经理对话（需先 update_data.py full；可选 .env 配 DeepSeek key 启用 LLM 蒸馏）
# MCP: chat_with_manager(manager_name="张坤", question="你对后市怎么看？")

# 基金跟仓（首次刷新建立基线，下一季起可对比）
# MCP: compare_holdings_change(fund_code="110011")
# MCP: build_mirror_portfolio(fund_code="110011", mode="weighted", total_amount=100000)

# 客户行为画像（10 题问卷可选）
# MCP: assess_client_profile(client_id="张先生", answers='{"q1":0,"q2":2}')
# MCP: get_client_communication_guide(client_id="张先生")

# 定制报告（8 模块自由组合 + 批量）
# MCP: generate_custom_report(client_id="张先生", report_type="weekly",
#       modules="news,holdings,manager_views,psychology,follow,risk", template="professional")
# MCP: generate_batch_reports()   # 批量生成名下所有客户周报
```

## 3. 常见问题速查

### 运行报错

| 症状 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: mcp` | 未装 MCP 包 | `pip install mcp` |
| 数据文件 TOO SMALL | 数据文件损坏 | 运行 `python scripts/data_collection/full_data_refresh.py` |
| 查询返回空 | 列式压缩格式未解码 | 使用 `load_json_data()` 而非 `json.load()` |
| 截图 OCR 失败 | 未装 Tesseract | 参考 [OCR 配置](https://github.com/UB-Mannheim/tesseract/wiki) |
| MCP 工具列表为空 | mcp 包未装 | `pip install mcp` |

### 使用问题

| 问题 | 回答 |
|------|------|
| **需要联网吗？** | 查询/分析/对话全部纯本地。仅"实时估值"和"数据更新"需要网络。 |
| **需要配置吗？** | 不需要。下载即用。 |
| **数据多久更新？** | 每月运行更新脚本获取最新数据。 |
| **数据来源？** | 天天基金网（东方财富），国内最大基金数据平台。 |
| **安全吗？** | 100% 本地存储，不上传云端，不调用外部 API。 |
| **支持哪些 LLM？** | DeepSeek / 通义千问 / 智谱 GLM / Kimi / 豆包 / 混元 / 星火 / MiniMax，编辑 `.env` 配置。 |

## 4. 可选：启用 LLM 智能对话

```bash
# 1. 复制配置模板
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux

# 2. 编辑 .env，填入 API Key
DEEPSEEK_API_KEY=sk-你的key

# 3. 验证
python -c "from scripts.analysis.config import is_offline_mode; print('offline' if is_offline_mode() else 'online')"
```

不填也能用：量化分析等功能会走 OFFLINE 占位模式。

## 5. 安全

- 所有数据 100% 本地存储，不上传云端
- 无后门、无遥测、无第三方追踪
- 网络请求仅用于：天天基金行情查询（可选）和数据更新（可选）

## 6. 反馈

- 先运行 `python -m fund_advisor check` 确认环境正常
- 提 Issue 时附带自检输出和错误信息
