---
name: gf-stock-f10
version: 1.0.0
description: 本Skill基于广发证券权威数据接口构建，查询股票基础信息，包含公司全称、板块、上市日期、主营业务、所属行业。
description_zh: 本Skill基于广发证券权威数据接口构建，查询股票基础信息，包含公司全称、板块、上市日期、主营业务、所属行业。
description_en: GF Securities stock basic information query tool, providing
  company full name, board, listing date, main business, and industry
  classification.
disable-model-invocation: true
---

# 鉴权规则
- 鉴权环境变量：GF_SKILLS_APIKEY
- 无KEY则终止调用，引导前往 http://hd.gf.com.cn/skills-market 申请配置

# 接口信息
service_name: wechat_f10
tool_name: f10_basic_post
请求方式: POST
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "wechat_f10",
  "tool_name": "f10_basic_post",
  "args": {
    "code": "000776",
    "market": "SZ"
  }
}'