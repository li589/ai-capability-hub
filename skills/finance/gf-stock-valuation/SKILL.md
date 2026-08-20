---
name: gf-stock-valuation
version: 1.0.0
description: 基于广发证券接口，查询多只股票市值、PE、PB、行业均值与估值百分位，用于个股估值横向财务对比。
description_zh: 基于广发证券接口，查询多只股票市值、PE、PB、行业均值与估值百分位，用于个股估值横向财务对比。
description_en: GF Securities financial comparison tool, querying market cap,
  PE, PB, industry averages, and valuation percentiles for multi-stock
  horizontal financial comparison.
disable-model-invocation: true
---

# 鉴权规则
- 鉴权环境变量：GF_SKILLS_APIKEY
- 无KEY则终止调用，引导前往 http://hd.gf.com.cn/skills-market 申请配置

# 接口信息
service_name: quant
tool_name: common_basic_post
请求方式: POST
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "quant",
  "tool_name": "common_basic_post",
  "args": {
    "stock_codes": ["SZ000776", "SZ000001"]
  }
}'