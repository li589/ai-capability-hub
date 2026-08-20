---
name: gf-lhb-list
version: 1.0.0
description: 广发证券龙虎榜个股查询Skill，获取指定日期、沪深市场异常上榜个股数据
description_zh: 广发证券龙虎榜个股查询Skill，获取指定日期、沪深市场异常上榜个股数据
description_en: GF Securities Dragon-Tiger Board stock query skill, retrieving
  abnormal trading stock data for specified dates in Shanghai and Shenzhen
  markets.
disable-model-invocation: true
---

# 技能规则说明
## 鉴权配置
- 接口鉴权密钥从环境变量 GF_SKILLS_APIKEY 读取
- 未配置密钥时引导用户前往 http://hd.gf.com.cn/skills-market 申领

## 接口基础信息
service_name: lhb
tool_name: lhb_aborttrade_market_date_get
接口地址: https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call
请求方式: POST

## 入参规范
- date: 整型，必填，日期格式YYYYMMDD
- market: 字符串，必填，sh=沪市 / sz=深市

## 调用示例curl
```bash
curl -X POST 'https://mcp-api.gf.com.cn/gf-skills/skills/mcp/call' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${GF_SKILLS_APIKEY}" \
--data '{
  "service_name": "lhb",
  "tool_name": "lhb_aborttrade_market_date_get",
  "args": {
    "date": 20260313,
    "market": "sh"
  }
}'