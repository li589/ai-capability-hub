---
name: wuyun-liuqi-analysis
description: 五运六气年度运势分析 - 基于中医五运六气理论，生成年度健康与运势报告
version: 1.0.0
author: 熵海领航
pricing:
  analysis: ¥4.99/次
---

# 五运六气年度运势分析（付费版）

基于中医五运六气理论的专业年度运势分析系统，结合用户体质类型，生成个性化的年度健康与运势报告。

## 功能说明

| 服务 | 价格 | 内容 |
|------|------|------|
| 年度运势分析 | ¥4.99/次 | 五运六气分析 + 运势评分 + 养生建议 |

### 分析内容

**🔮 五运六气分析**
- 年度天干地支推算
- 五运（木、火、土、金、水）属性分析
- 五运强度（太过/不及）评估
- 六气（风、寒、暑、湿、燥、火）变化预测

**📊 运势评估**
- 综合运势评分（0-100分）
- 健康运势评分
- 整体运势评分
- 运势概要说明

**💡 养生指导**
- 基于体质的年度调养方案
- 饮食调理方向
- 运动保健建议
- 注意事项

## 付费前置检查

**重要：在调用此技能之前，必须确认当前 Agent 已安装 weixinpay 插件（extension）。**

- ✅ 已安装：继续调用技能
- ❌ 未安装：停止调用，提示用户"当前 Agent 暂不支持微信支付付费能力，请先安装 weixinpay 插件后再使用此技能"

## 工作流程

### 第一步：检查 weixinpay 插件
确认 Agent 已安装 weixinpay 插件，如未安装则停止并提示用户。

### 第二步：调用技能 API
```
POST https://meihua.astrakairos.com/wuyun/api/resource
Content-Type: application/json

{
  "year": 2025,
  "constitution_type": "气虚质"
}
```

首次调用会返回 402 Payment Required 状态码，包含：
- `WeixinPay-Required` header：支付凭证码
- `X-Out-Trade-No` header：商户订单号

### 第三步：调用 weixinpay_pay 完成支付
使用第二步返回的 `WeixinPay-Required` 值调用 `weixinpay_pay` 插件：
```
weixinpay_pay(paymentCode="返回的WeixinPay-Required值")
```

### 第四步：重试调用技能 API（必须）
支付成功后，**必须**使用相同的请求 body 和订单号重新调用技能 API：
```
POST https://meihua.astrakairos.com/wuyun/api/resource
Content-Type: application/json
X-Out-Trade-No: 第二步返回的订单号

{
  "year": 2025,
  "constitution_type": "气虚质"
}
```

**注意**：
- 请求 body 必须与第二步完全一致
- 必须在 header 中传递 `X-Out-Trade-No`（商户订单号）
- 这一步才能获取真正的分析结果

### 第五步：异常处理
如果返回的 `code` 字段包含以下值，按对应方式处理：

| code | 含义 | 处理方式 |
|------|------|---------|
| `SUCCESS` | 分析完成 | 正常展示结果给用户 |
| `NOT_PAID` | 支付未完成 | 提示用户"支付尚未完成，请重新支付"，不要重试 |
| `REFUNDED` | 已自动退款 | 告知用户"服务异常，已自动退款至原支付账户"，不要再次请求 |
| `FULFILL_AND_REFUND_FAILED` | 服务异常且退款失败 | 告知用户"服务异常，请联系客服处理退款" |

## 输入参数

- `year`（必填）：要分析的年份，支持 2024-2028
- `constitution_type`（可选）：用户体质类型（如"气虚质"、"阳虚质"等）

## 输出内容

### 1. 五运六气基础信息
- 年份天干地支
- 五运属性（木、火、土、金、水）
- 五运强度（太过/不及）
- 六气属性（风、寒、暑、湿、燥、火）

### 2. 运势分析
- 综合运势评分（0-100分）
- 健康运势评分
- 整体运势评分
- 运势概要说明

### 3. 养生建议
- 基于体质和五运六气的年度养生建议
- 饮食调理方向
- 运动保健建议
- 注意事项

## 示例

输入：
```json
{
  "year": 2025,
  "constitution_type": "气虚质"
}
```

输出：
```json
{
  "code": "SUCCESS",
  "wuyun_liuqi": {
    "wuyun": "水运",
    "wuyun_strength": "太过",
    "liuqi": "少阴君火"
  },
  "summary": "2025年（乙巳年）为水运太过之年，司天之气为少阴君火...",
  "score": {
    "overall": 72.5,
    "health": 70,
    "fortune": 75
  }
}
```

## 注意事项

- 本分析基于中医五运六气理论，仅供参考
- 建议结合体质辨识服务获取准确的体质类型
- 运势评分为理论推演，实际生活需综合考虑多种因素
- **必须严格按照使用流程操作，特别是支付后的重试步骤**
