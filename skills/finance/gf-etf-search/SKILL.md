---
name: gf-etf-search
version: 1.0.0
description: 本Skill基于广发证券权威数据接口构建，支持按收益率、回撤、夏普、估值温度、规模、赛道、交易属性等多维条件筛选ETF。适用于寻找特定主题ETF、做收益与风险条件过滤、构建ETF候选池的场景，提供权威实时ETF筛选数据。
description_zh: 本Skill基于广发证券权威数据接口构建，支持按收益率、回撤、夏普、估值温度、规模、赛道、交易属性等多维条件筛选ETF。适用于寻找特定主题ETF、做收益与风险条件过滤、构建ETF候选池的场景，提供权威实时ETF筛选数据。
description_en: GF Securities ETF screening tool, supporting multi-dimensional
  ETF filtering by return rate, drawdown, Sharpe ratio, valuation temperature,
  scale, sector, and trading attributes. Ideal for discovering thematic ETFs,
  filtering by return/risk criteria, and building ETF candidate pools.
disable-model-invocation: true
---

# 鉴权规则
- 鉴权环境变量：GF_SKILLS_APIKEY
- 无KEY则终止调用，引导前往 http://hd.gf.com.cn/skills-market 申请配置

# 接口信息
service_name: etf_search
tool_name: finance_api_inclusive_etf_list_get
请求方式: POST
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "etf_search",
  "tool_name": "finance_api_inclusive_etf_list_get",
  "args": {
    "trakType": "行业",
    "roc1m": "5~",
    "sort": "-roc1m",
    "limit": 20,
    "addRealTimeRoc": 1
  }
}'