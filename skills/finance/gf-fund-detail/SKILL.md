---
name: gf-fund-detail
version: 1.0.0
description: 本Skill基于广发证券权威数据接口构建，支持查询基金完整详情，包含净值、收益率、风险等级、申赎规则、基金经理、基金公司与综合评价，用于基金资料查询与基本面对比。
description_zh: 本Skill基于广发证券权威数据接口构建，支持查询基金完整详情，包含净值、收益率、风险等级、申赎规则、基金经理、基金公司与综合评价，用于基金资料查询与基本面对比。
description_en: GF Securities fund detail query tool, supporting comprehensive
  fund information including NAV, return rate, risk level,
  subscription/redemption rules, fund manager, fund company, and comprehensive
  evaluation. Suitable for fund research and fundamental comparison.
disable-model-invocation: true
---

# 鉴权规则
- 鉴权环境变量：GF_SKILLS_APIKEY
- 无KEY则终止调用，引导前往 http://hd.gf.com.cn/skills-market 申请配置

# 接口信息
service_name: jijin_info
tool_name: finance-api_product_fund_detail_get
请求方式: POST
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "jijin_info",
  "tool_name": "finance-api_product_fund_detail_get",
  "args": {
    "tradeCode": "519002"
  }
}'