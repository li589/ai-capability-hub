---
name: gf-etf-rank
version: 1.0.0
description: 广发证券ETF排行查询工具，支持涨跌幅、换手率、主力资金、申赎、溢价率等多维度ETF榜单数据查询
description_zh: 广发证券ETF排行查询工具，支持涨跌幅、换手率、主力资金、申赎、溢价率等多维度ETF榜单数据查询
description_en: GF Securities ETF ranking query tool, supporting
  multi-dimensional ETF leaderboard data queries including price change,
  turnover rate, major capital flow, subscription/redemption, and premium rate
disable-model-invocation: true
---

# 一、鉴权规则
- 鉴权密钥取自环境变量：GF_SKILLS_APIKEY
- 无密钥时：终止调用，引导用户前往 http://hd.gf.com.cn/skills-market 申请密钥并配置环境变量

# 二、接口基础信息
service_name: etf_rank
tool_name: finance-api_product_etf_rank_get
request_method: POST
api_url: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call

# 三、入参说明
|参数|类型|必填|备注|
|----|----|----|----|
|type|int|是|排行类型：1涨幅、2跌幅、3换手率、4主力资金、12净申赎、13溢价率|
|page|int|否|页码，从0开始|
|size|int|否|每页条数，默认10|
|sameIndexFilter|int|否|同指数只展示1只：1开启/0关闭|
|continueRiseLimit|int|否|连涨连跌天数筛选|

# 四、curl调用示例
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "etf_rank",
  "tool_name": "finance-api_product_etf_rank_get",
  "args": {
    "type": 1,
    "size": 20
  }
}'