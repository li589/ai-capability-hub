# 基金经理对话与跟仓使用说明（v10.0）

本文件说明 v10.0 新增的「基金经理对话」与「基金跟仓」两大能力的设计、数据来源、使用方式与合规边界。

## 一、基金经理对话

### 设计目标
让客户经理能「对话」基金经理：把分散在定期报告、新闻采访、产品合同中的公开信息蒸馏为基金经理口吻的回答，用于客户沟通与投顾参考。

### 数据来源（逐源优雅降级）
| 人设维度 | 数据源 | 采集脚本 | 缺失时表现 |
|---|---|---|---|
| 履历/风格/股票池/风险提示 | `fund_managers_distilled.json`（本地蒸馏库） | `full_data_refresh.py` | 风格按基金名推断 |
| 投资范围/目标/基准 | `fund_products.json` v10 档案列 | `fund_profile_collector.py` | 给出补采提示 |
| 最新季报观点 | `manager_views.json`（季报 PDF 解析） | `view_collector.py` | 给出补采提示 |
| 新闻/采访 | `manager_news.json` | `manager_news_collector.py` | 给出补采提示 |

### 回答优先级
1. **LLM 蒸馏**（可选）：`.env` 配 `DEEPSEEK_API_KEY` 时，把季报观点/新闻改写为经理口吻（`manager_dialogue.ManagerDialogue._llm_distill`）
2. **规则组装**：按意图从人设卡抽取真实数据拼接（`_assemble_answer`）
3. **模板兜底**：复用 `invitation_engine` / `fund_advisor_speech` 现有话术

### 意图路由
`manager_dialogue.detect_intent`：自我介绍 / 风格 / 持仓 / 观点 / 范围 / 新闻 / 业绩 / 安抚 / general

### 使用
- MCP：`chat_with_manager(manager_name, question, fund_code="")`
- MCP：`get_manager_persona(manager_name, fund_code="")`（人设卡）
- MCP：`get_manager_news(manager_name, limit=5)`
- CLI：`python scripts/analysis/manager_dialogue.py --name 张坤 --question "你对后市怎么看？"`

### 免责声明
所有回答自带：**观点来源于该基金经理管理的基金定期报告及公开新闻/采访整理，非经理本人实时言论，仅供投顾参考，不构成投资建议。**

---

## 二、基金跟仓

### 设计目标
围绕「跟仓」场景提供：持仓季度变动对比、镜像组合构建、跟仓信号、经理变动监控。

### 数据基础：持仓历史
- `holdings_database.json` 只保留最新一季快照；`data/holdings_history/{YYYYQN}.json` 按 v10.0 起积累季度历史
- 每次 `update_data.py full` 后自动归档当前季度（`holdings_history.archive_current_holdings`）；同季度不重复归档（不覆写历史）
- **策略**：首次刷新建立基线，从下一季度起 `compare_holdings_change` 才有对比

### 核心能力
| 能力 | MCP 工具 / 函数 | 说明 |
|---|---|---|
| 持仓变动对比 | `compare_holdings_change(fund_code, q1, q2)` / `ManagerFollower.diff_fund_holdings` | 新增/剔除/加仓/减仓/换手率 |
| 镜像组合 | `build_mirror_portfolio(fund_code, mode, total_amount)` | 加权/等权 + 集中度 + 金额分解 + 合规提示 |
| 镜像跟踪 | `track_mirror_portfolio(fund_code, days)` | 基金净值近似 + 当日重仓股行情估算 |
| 跟仓信号 | `get_follow_signals(fund_codes)` | 持仓变动 + 经理变动，带级别/置信度 |
| 经理变动监控 | `maintenance/manager_change_monitor.py` | 本地档案对比 + 公告扫描 → `manager_changes.json` |

### 镜像组合模式
- `weighted`：按披露权重（未覆盖部分记为现金/其他）
- `equal`：十大重仓等权分摊

### 合规风险提示（自动附带）
> ⚠️ 跟仓风险提示：① 季报披露滞后（通常滞后 1-2 个季度），经理实际持仓可能已变动；
> ② 十大重仓仅覆盖组合一部分（其余为债券/现金/其他），镜像≠基金本身；
> ③ 跟仓涉及申赎成本与个股集中度风险，请结合客户风险承受能力评估；
> ④ 以上仅为投顾参考，不构成投资建议。

### 使用
```bash
# 经理变动监控（写入 data/manager_changes.json，供跟仓信号并入）
python scripts/maintenance/manager_change_monitor.py [--online]

# 跟仓引擎 CLI
python scripts/analysis/manager_follower.py diff --fund 110011
python scripts/analysis/manager_follower.py mirror --fund 110011 --mode weighted --amount 100000
python scripts/analysis/manager_follower.py signals
```

---

## 三、客户端客户行为画像（配合对话/报告使用）
- `assess_client_profile(client_id, answers)`：10 题行为问卷（可选）+ 情绪记录/持仓导入历史 → 6 维偏差 + 心理类型 + 沟通策略
- `get_client_communication_guide(client_id)`：渲染沟通策略建议
- `conversation_engine` 已叠加心理感知层（已评估画像的客户在情绪相关回复中自动附加个性化沟通提示）

详见 `scripts/client_manager/behavioral_profile.py` 与 `behavioral_questionnaire.json`。
