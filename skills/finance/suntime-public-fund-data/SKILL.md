---
name: suntime-public-fund-data
display_name: 朝阳永续-AI-公募基金数据
display_name_en: Suntime-Public-Fund-Data
description: 朝阳永续公募基金数据技能连接专业公募基金数据库，覆盖基金基础档案与费率、分红和份额变动、历史净值与多周期收益风险指标、业绩排名、持仓穿透与资产配置、风格和行业归因、多基金横向比较、基金经理筛选与综合画像、基金公司规模及产品矩阵、基金公告列表与文本语义检索。凡用户需要查询或比较公募基金、分析收益回撤和夏普等指标、查看重仓股债与仓位变化、研究投资风格和行业暴露、筛选基金产品或基金经理、了解基金公司、检索定期报告及经理变更等公告内容时优先调用；同时支持按照自然语言条件从产品、持仓和资产配置等维度筛选基金。
description_zh: 朝阳永续公募基金数据查询与专业分析技能，覆盖基金档案、费率、净值业绩、收益风险、持仓配置、风格归因、多基金对比、基金经理、基金公司和公告检索。
description_en: Suntime Public Fund Data provides professional mutual-fund data
  and analysis covering fund profiles and fees, NAV and performance, risk
  metrics and rankings, holdings and asset allocation, style and industry
  attribution, multi-fund comparisons, manager screening and profiles, fund
  companies, and announcement retrieval. Use it to query, compare, screen, and
  analyze public funds, managers, organizations, portfolios, or disclosure
  documents.
category: professional
version: 0.0.12
author: 朝阳永续
disable-model-invocation: true
---

# public-fund-data-mcp

**依赖：** suntime-mcp-cli — 本技能只负责 public-fund-data-mcp MCP 服务的工具调用指南，不重复 suntime-mcp-cli 的安装、配置和调用基础。

## 前置条件

- suntime-mcp-cli 已安装：`npm install -g suntime-mcp-cli`
- API Key 通过环境变量配置（推荐）：`export SUNTIME_API_KEY=sk-suntime-xxxxx`
- MCP 地址 base URL 优先从环境变量 `SUNTIME_BASE_URL` 读取，默认 `https://sntp-opendata.go-goal.cn`
- public-fund-data-mcp 服务已注册：
  ```bash
  suntime-mcp-cli config set-url public-fund-data-mcp ${SUNTIME_BASE_URL:-https://sntp-opendata.go-goal.cn}/s/100046/m/public-fund-data-mcp/mcp
  ```
- 查询某工具的具体入参 Schema，先用 `tool_list` 查看：
  ```bash
  suntime-mcp-cli public-fund-data-mcp tool_list
  ```

## 通用调用格式

```bash
suntime-mcp-cli public-fund-data-mcp <工具名> --params '<JSON参数>'
```

## 参数说明

复杂参数（数组、嵌套对象、百分比字符串）一律用 `--params` 传 JSON：

```bash
# ✅ 推荐：--params JSON
--params '{"fund_code":"162201"}'
--params '{"fund_code":["162201","000311"]}'
--params '{"fund_code":"162201","period":"y3"}'

# ❌ fund_code 为纯数字字符串时会被自动转成整数，建议用 --params
```

## 工具速查（按功能域）

各工具的具体入参 Schema 可通过 `tool_list` 命令实时查看。

### 📄 单只基金基础信息

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_base_info` | 基金全面基础档案 | fund_code |
| `public_fund_fee_info` | 运营与交易费率 | fund_code |
| `public_fund_member_info` | 历任及现任基金经理 | fund_code |
| `public_fund_bonus` | 历史分红记录 | fund_code |
| `public_fund_split` | 份额折算与拆分事件 | fund_code |

### 📈 业绩与净值

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_nav_index` | 多周期收益风险指标（可多只） | fund_code[] |
| `public_fund_graph_interval_index` | 深度走势+归因（Sharpe/Alpha等） | fund_code, period/start/end |
| `public_fund_nav_data` | 历史净值序列 | fund_code, start_date/end_date/rows |
| `public_fund_month_return` | 月度收益拆解 | fund_code, period |
| `public_fund_index_rank` | 各周期业绩排名 | fund_code |
| `public_fund_index_year_rank` | 历年自然年度排名 | fund_code |

### 🏗️ 持仓与资产配置

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_asset_config` | 最新大类资产配置 | fund_code |
| `public_fund_interval_asset_config` | 历史各季度资产配置演变 | fund_code |
| `public_fund_asset_detail` | 最新底层持仓明细 | fund_code |
| `public_fund_interval_asset_detail` | 近三年历史持仓快照 | fund_code |
| `public_fund_possessor_scale` | 持有人结构 | fund_code |

### 🎯 风格归因

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_attribution_style_overview` | 综合风格标签与稳定性 | fund_code, period |
| `public_fund_attribution_style_alloc` | CNE6因子配置风格解构 | fund_code, period |
| `public_fund_attribution_style_industry` | 申万行业暴露与贡献 | fund_code, period |
| `public_fund_attribution_style_operate` | 选股 vs 择时能力 | fund_code, period |
| `public_fund_attribution_style_mkt` | 不同市道适应度 | fund_code, end_date |

### 🔄 多基金对比

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_compare_basic_info` | 静态要素横向对比 | fund_code[] |
| `public_fund_compare_graph_interval_index` | 收益风险矩阵对比 | fund_code[], period |
| `public_fund_compare_nav_index` | 多周期收益率/回撤/夏普对比 | fund_code[] |
| `public_fund_compare_assest_consist` | 大类资产配置比例对比 | fund_code[] |
| `public_fund_compare_stock_bond_top` | 重仓股/债/基金交叉比对 | fund_code[] |
| `public_fund_compare_asset_hold_industrys` | 行业仓位暴露对比 | fund_codes[] |
| `public_fund_compare_asset_config` | 历史AUM与规模变动对比 | fund_codes (逗号分隔) |

### 👤 基金经理

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_member_screening` | 多维漏斗筛选基金经理（自然语言） | question |
| `public_member_search_info` | 模糊检索基金经理 | member_keyword |
| `public_member_get` | 姓名→member_id | member_name |
| `public_member_info` | 个人综合画像 | member_id |
| `public_member_nav_graph` | 经理指数走势与风险收益 | member_id, period |
| `public_member_manager_fund` | 在管/历史基金列表 | member_id |
| `public_member_interval_asset_detail` | 近三年持仓详情 | member_id |

### 🏢 基金公司

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_org_screening` | 多维漏斗筛选基金公司（自然语言） | question |
| `public_org_search_info` | 模糊检索基金公司 | org_keyword |
| `public_org_search_hold` | 基于持仓穿透筛选公司 | index_list |
| `public_org_get` | 名称→org_id | org_name |
| `public_org_info` | 公司全景档案与排名 | org_id |
| `public_org_fund_list` | 旗下产品矩阵 | org_id |
| `public_org_hold_ind_theme` | 资产偏好与持仓结构 | org_id |
| `public_org_fund_num_scale` | 历史AUM与产品数量演变 | org_id |

### 📢 公告检索

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_announcement_search` | 基于公告文本知识库的语义与关键词检索，可搜索分红公告、经理变更公告、定期报告等，支持公告ID精准召回 | question, fund_code, date_range, ann_id |
| `public_fund_announcement_list` | 按分类获取指定基金的公告列表（支持定期报告/招募/重要事项等筛选） | fund_code, first_class, second_class, date_range |

**公告搜索协作模式**：可先通过 `public_fund_announcement_list` 按分类获取公告清单，确认需要检索的公告，然后拿到这些公告ID后，再调用 `public_fund_announcement_search` 并传入 `ann_id` 参数精准检索指定公告的详细内容，避免在全量公告中模糊搜索。

**调用优先级说明**：对于结构化的数据查询（如前十大持仓、资产配置、业绩指标等），应**优先调用对应的数据查询工具**（如 `public_fund_asset_detail`、`public_fund_asset_config`、`public_fund_nav_index` 等），它们返回的结构化 JSON 数据更规范、更易解析。在数据工具无法覆盖或需要搜索非结构化文本内容（如公告原文、持仓变动解读、经理变更说明等）时，再使用公告检索工具作为补充。

### 🔍 高级筛选

| 工具名 | 用途 | 核心入参 |
|--------|------|---------|
| `public_fund_screening` | 多维度筛选基金产品（自然语言） | question |
| `public_search_fund_position` | 通过持仓特征筛选（自然语言） | question |
| `public_search_fund_asset` | 通过资产配置特征筛选（自然语言） | question |

## 常见查询模式

### 查询单只基金完整档案

```bash
# 基础信息
suntime-mcp-cli public-fund-data-mcp public_fund_base_info --params '{"fund_code":"162201"}'

# 业绩指标
suntime-mcp-cli public-fund-data-mcp public_fund_nav_index --params '{"fund_code":["162201"]}'

# 持仓明细
suntime-mcp-cli public-fund-data-mcp public_fund_asset_detail --params '{"fund_code":"162201"}'
```

### 多只基金对比

```bash
# 收益风险指标对比（需传数组）
suntime-mcp-cli public-fund-data-mcp public_fund_compare_nav_index --params '{"fund_code":["162201","000311","110011"]}'

# 持仓交叉比对
suntime-mcp-cli public-fund-data-mcp public_fund_compare_stock_bond_top --params '{"fund_code":["162201","000311"]}'
```

### 筛选基金产品/经理/公司

所有筛选工具均为自然语言参数，直接输入查询需求即可：

```bash
# 筛选基金产品
suntime-mcp-cli public-fund-data-mcp public_fund_screening --params '{"question":"近一年收益率大于50%且最大回撤小于10%的股票型基金"}'

# 按持仓特征筛选
suntime-mcp-cli public-fund-data-mcp public_search_fund_position --params '{"question":"重仓贵州茅台且规模大于50亿的基金"}'

# 按资产配置特征筛选
suntime-mcp-cli public-fund-data-mcp public_search_fund_asset --params '{"question":"股票仓位大于80%且规模大于100亿的基金"}'

# 筛选基金经理
suntime-mcp-cli public-fund-data-mcp public_member_screening --params '{"question":"从业10年以上的价值风格基金经理"}'

# 筛选基金公司
suntime-mcp-cli public-fund-data-mcp public_org_screening --params '{"question":"管理规模大于5000亿且产品数量超过100只的公司"}'
```

### 查找基金经理

```bash
# 模糊搜索
suntime-mcp-cli public-fund-data-mcp public_member_search_info --params '{"member_keyword":"张坤"}'

# 姓名→ID（用于后续查询）
suntime-mcp-cli public-fund-data-mcp public_member_get --params '{"member_name":"张坤"}'

# 查看画像（需要先获取 member_id）
suntime-mcp-cli public-fund-data-mcp public_member_info --params '{"member_id":123}'
```

### 搜索基金公告

```bash
# 语义搜索某只基金的公告
suntime-mcp-cli public-fund-data-mcp public_fund_announcement_search --params '{"question":"基金经理变更","fund_code":"162201"}'

# 按日期范围搜索
suntime-mcp-cli public-fund-data-mcp public_fund_announcement_search --params '{"question":"基金经理变更 离任 增聘","fund_code":"011369","date_range":"2025-01-01..2026-06-01"}'

# 先通过公告列表获取公告ID，再精准检索
suntime-mcp-cli public-fund-data-mcp public_fund_announcement_list --params '{"fund_code":"011369","first_class":"定期报告","second_class":"基金季报","date_range":"2025-01-01..2025-12-31"}'

# 用拿到的公告ID精准搜索内容
suntime-mcp-cli public-fund-data-mcp public_fund_announcement_search --params '{"question":"本报告期内基金的投资策略","fund_code":"011369","ann_id":"822387,145017"}'
```

## 注意事项

- **period 参数**：大多数工具支持 `total`（成立以来）、`year`（今年）、`m1/m3/m6`、`y1/y2/y3/y5`，仅允许传单个值
- **指数代码**：沪深300=000300、中证500=000905、创业板指=399006 等，用于基准对比
- **净值类型**：1=复权累计净值（默认）、4=累计净值
- **fund_code 取值**：查询单只传字符串，多只传数组（具体见各工具 schema）
- **筛选工具**：`public_fund_screening` / `public_search_fund_position` / `public_search_fund_asset` / `public_member_screening` / `public_org_screening` 均使用 `question` 参数，直接输入查询条件的自然语言描述即可
- **查看工具 Schema**：`suntime-mcp-cli public-fund-data-mcp tool_list` 会列出所有工具及入参
