---
name: gf-fund-invest
version: 1.0.0
description: 基于广发证券接口，支持多种定投策略回测，测算基金历史定投收益，用于定投方案回测与策略对比。
description_zh: 基于广发证券接口，支持多种定投策略回测，测算基金历史定投收益，用于定投方案回测与策略对比。
description_en: GF Securities fund investment calculator, supporting multi-strategy DCA (Dollar Cost Averaging) backtesting to calculate historical fund investment returns. Suitable for investment plan backtesting and strategy comparison.
---
# 鉴权规则
- 鉴权环境变量：GF_SKILLS_APIKEY
- 无KEY则终止调用，引导前往 http://hd.gf.com.cn/skills-market 申请配置

# 接口信息
service_name: fund_invest
tool_name: finance_api_product_invest_compute_post
请求方式: POST
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "fund_invest",
  "tool_name": "finance_api_product_invest_compute_post",
  "args": {
    "tradeCode": "001643",
    "balance": 1000,
    "rate": "0",
    "startDate": "20200101",
    "endDate": "20250101",
    "enFundDate": "1",
    "strategyList": [{
      "prodAIRationType": "4",
      "prodIndexType": "0",
      "prodAverageType": "0",
      "expectIncomeRatio": "0.2"
    }]
  }
}'