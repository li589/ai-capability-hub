---
name: gf-etf-super-fund
version: 1.0.0
description: 本Skill基于广发证券权威数据接口构建，支持查询大幅流入、大幅流出、持续流入、持续流出超级资金异动ETF及近14日资金明细，跟踪ETF资金异动、研判市场资金方向。
description_zh: 本Skill基于广发证券权威数据接口构建，支持查询大幅流入、大幅流出、持续流入、持续流出超级资金异动ETF及近14日资金明细，跟踪ETF资金异动、研判市场资金方向。
description_en: GF Securities ETF super fund flow anomaly detection tool,
  supporting queries for major inflows, major outflows, continuous inflows, and
  continuous outflows with 14-day fund flow details. Track ETF capital anomalies
  and assess market fund direction.
disable-model-invocation: true
---

# 鉴权规则
- 鉴权环境变量：GF_SKILLS_APIKEY
- 无KEY则终止调用，引导前往 http://hd.gf.com.cn/skills-market 申请配置

# 接口信息
service_name: etf-super-fund
tool_name: gfmiddle_eits_super_fund_etf_superfund_get
请求方式: POST
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "etf-super-fund",
  "tool_name": "gfmiddle_eits_super_fund_etf_superfund_get",
  "args": {
    "type": "大幅流入"
  }
}'