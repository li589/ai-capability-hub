---
name: ai-berkshire
description: AI Berkshire 四维投研分析 - 段永平、巴菲特、芒格、李录四位大师视角深度股票分析
version: 1.0.0
author: 熵海领航
pricing:
  analysis: ¥9.90/次
---

# AI Berkshire 四维投研分析（付费版）

融合四位投资大师视角的专业股票分析工具：段永平（商业模式）、巴菲特（财务分析）、芒格（行业格局）、李录（风险评估），提供深度投资研究报告。

## 功能说明

| 维度 | 分析师 | 核心内容 |
|------|--------|----------|
| 🏢 商业模式 | **段永平** | 生意本质、护城河、差异化、定价权、管理层评估 |
| 💰 财务分析 | **巴菲特** | 盈利能力、现金流、资产负债、成长性、估值、安全边际 |
| 🌍 行业格局 | **芒格** | 行业空间、竞争格局、产业链、行业趋势、护城河持续性 |
| ⚠️ 风险评估 | **李录** | 系统性风险、公司风险、估值风险、黑天鹅、风险收益比 |

## 定价

¥9.90/次 — 完整四维投资研究报告

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- 已安装：可继续提供付费服务
- 未安装：向用户提示"当前 Agent 暂不支持微信支付付费能力，请安装 weixinpay 插件后再使用"，终止流程

## 工作流程

### 第一步：发起分析请求

```
POST https://meihua.astrakairos.com/berkshire/api/resource
Content-Type: application/json

{
  "stock_code": "600519.SH",
  "company_name": "贵州茅台"
}
```

参数说明：
- `stock_code` (必填): 股票代码（支持 A股、港股、美股）
- `company_name` (必填): 公司名称

### 第二步：处理 402 支付响应

服务返回 HTTP 402 + `WeixinPay-Required` header：

```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "支付 ¥9.90 获取专业四维投研分析报告",
  "out_trade_no": "BK1627890123A1B2C3D4",
  "amount": "9.90",
  "WeixinPay": {
    "WeixinPay-Required": "payment_code_xxx",
    "prompt": "请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay"
  }
}
```

Agent 应调用 `weixinpay_pay(paymentCode=<WeixinPay-Required的值>)` 完成支付。

### 第三步：重试请求（必须带订单号）

支付完成后，用 **相同的请求体** + `X-Out-Trade-No` header 重新请求：

```
POST https://meihua.astrakairos.com/berkshire/api/resource
Content-Type: application/json
X-Out-Trade-No: BK1627890123A1B2C3D4

{
  "stock_code": "600519.SH",
  "company_name": "贵州茅台"
}
```

服务验证支付后返回 200，同时启动后台分析任务：

```json
{
  "code": "SUCCESS",
  "message": "分析任务已启动，预计需要 3-5 分钟",
  "out_trade_no": "BK1627890123A1B2C3D4",
  "task_id": "BK1627890123A1B2C3D4",
  "task_status": "processing",
  "report_url": "https://meihua.astrakairos.com/berkshire/report/BK1627890123A1B2C3D4"
}
```

### 第四步：轮询任务状态

分析需要 3-5 分钟，Agent 应轮询任务状态：

```
GET https://meihua.astrakairos.com/berkshire/api/task/{task_id}
```

响应示例（分析中）：
```json
{
  "task_id": "BK1627890123A1B2C3D4",
  "status": "processing",
  "progress": {
    "business": "段永平正在分析商业模式...",
    "financial": "巴菲特正在分析财务数据...",
    "industry": "行业格局分析完成",
    "risk": "风险评估进行中"
  }
}
```

响应示例（已完成）：
```json
{
  "task_id": "BK1627890123A1B2C3D4",
  "status": "completed",
  "report_url": "https://meihua.astrakairos.com/berkshire/report/BK1627890123A1B2C3D4",
  "result": {
    "stock_code": "600519.SH",
    "company_name": "贵州茅台",
    "dimensions": {
      "business": {
        "score": 4.5,
        "summary": "茅台拥有极强的品牌护城河和定价权...",
        "business_model": "...",
        "moat_analysis": {...},
        "conclusion": "..."
      },
      "financial": {...},
      "industry": {...},
      "risk": {...}
    },
    "synthesis": {
      "overall_score": 4.2,
      "score_level": "优秀",
      "investment_thesis": "...",
      "bull_case": [...],
      "bear_case": [...],
      "action_recommendation": {
        "type": "买入",
        "position_size": "10-15%",
        "entry_strategy": "...",
        "exit_conditions": "..."
      },
      "final_verdict": "..."
    }
  }
}
```

### 退款处理

分析失败时系统自动退款，可能收到以下响应：

- `REFUNDED`: 服务异常，已自动退款
- `NOT_PAID`: 支付尚未完成，请稍后重试
- `FULFILL_AND_REFUND_FAILED`: 服务异常且退款失败，请联系客服

## 如何向用户展示结果

收到完整分析结果后，按以下结构呈现给用户：

1. **📊 综合评分**: 总体评分（1-5分）+ 投资等级（优秀/良好/一般/较差）
2. **🏢 商业模式分析**: 段永平视角的核心结论 + 评分
3. **💰 财务分析**: 巴菲特视角的核心结论 + 评分
4. **🌍 行业格局**: 芒格视角的核心结论 + 评分
5. **⚠️ 风险评估**: 李录视角的核心结论 + 评分
6. **💡 投资论点**: 看多理由 vs 看空理由
7. **🎯 投资建议**: 操作建议、仓位比例、建仓策略、退出条件
8. **✅ 最终结论**: 100字投资结论

## 支持的股票市场

- **A股**: 沪深两市（如 600519.SH, 000858.SZ）
- **港股**: 香港联交所（如 00700.HK, 09988.HK）
- **美股**: 纳斯达克、纽交所（如 AAPL, MSFT, TSLA）
