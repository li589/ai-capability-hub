---
name: meihua-yishu
description: 梅花易数专业起卦解卦 — 邵雍正宗先天数算法，体用生克+互卦变卦+月令旺衰，64卦全维度解读，大师档含AI深度解读
version: 2.0.0
author: 熵海领航
pricing:
  divination: ¥1.99/次
---

# 梅花易数专业解卦（付费版）

北宋邵雍《梅花易数》正宗算法，支持时间起卦、报数起卦、字数起卦三种方式，提供基础/详细/大师级三种解读深度。

## 功能说明

| 等级 | 价格 | 内容 |
|------|------|------|
| `basic` | ¥1.99/次 | 本卦 + 体用五行 + 吉凶判断 + 建议 |
| `detailed` | ¥1.99/次 | 本卦 + 互卦 + 变卦 + 月令旺衰 + 事业/感情/财运/健康 + 应期 |
| `premium` | ¥1.99/次 | 全维度 + 流年运势 + 五行调理 + 深度建议 + **AI大师深度解读（约500-800字）** |

## 付费前置检查

调用本 Skill 前，检查当前 Agent 是否已安装 `weixinpay` 插件（extension）：

- 已安装：可继续提供付费服务
- 未安装：向用户提示"当前 Agent 暂不支持微信支付付费能力，请安装 weixinpay 插件后再使用"，终止流程

## 工作流程

### 第一步：请求解卦

向以下 URL 发起 POST 请求：

```http
POST https://meihua.astrakairos.com/api/resource
Content-Type: application/json

{
    "query": "这个月工作能升职吗",
    "tier": "detailed",
    "method": "time"
}
```

参数说明：
- `query`（必填）：所问事项，1-200字
- `tier`（可选）：`basic` / `detailed` / `premium`，默认 `detailed`
- `method`（可选）：起卦方式
  - `time`：时间起卦（默认，邵雍正宗法）
  - `number`：报数起卦（需提供 `numbers` 参数，如 `[3, 7]`）
  - `char`：字数起卦（需提供 `text` 参数）
- `numbers`（可选）：报数列表
- `text`（可选）：字数起卦文字

### 第二步：处理 402 响应（支付触发）

如果收到 HTTP 402 响应，表示需要付费后才能获取完整解卦结果。

402 响应中包含：
- Header `WeixinPay-Required`：支付凭证码（payment_code）
- Header `X-Out-Trade-No`：商户订单号（out_trade_no）
- Body `WeixinPay` 字段：包含支付信息
- Body `preview`：卦象预览（卦名、吉凶等级）

此时应将 `WeixinPay-Required` 的值作为 paymentCode，调用 `weixinpay_pay` 插件完成微信支付。

### 第三步：支付成功后重试（重试机制 + 订单号传递）

支付成功后，**必须**重新发起请求获取完整解读。重试规则：

- **JSON body 不变**：与首次请求完全一致
- **通过 Header 传递订单号**：将 402 响应中的 `X-Out-Trade-No` 值放入请求 Header

重试请求示例：

```http
POST https://meihua.astrakairos.com/api/resource
Content-Type: application/json
X-Out-Trade-No: <out_trade_no>

{
    "query": "这个月工作能升职吗",
    "tier": "detailed",
    "method": "time"
}
```

> 注意：body 与第一步完全一致，不要修改 body 中的任何字段。订单号通过 Header `X-Out-Trade-No` 传递。

### 第四步：异常处理

根据返回的 `code` 字段处理不同情况：

| code | 含义 | 处理方式 |
|------|------|---------|
| `SUCCESS` | 解卦成功 | 展示结果给用户 |
| `NOT_PAID` | 支付未完成 | 提示用户"支付尚未完成，请稍后重试"，等待3-5秒后重试第二步 |
| `REFUNDED` | 已自动退款 | 告知用户"服务异常，已自动退款至原支付账户"，不要再次请求 |
| `FULFILL_AND_REFUND_FAILED` | 服务异常且退款失败 | 告知用户"服务异常，请联系客服处理退款" |

## 返回内容示例

```json
{
    "code": "SUCCESS",
    "content": {
        "tier": "detailed",
        "question": "这个月工作能升职吗",
        "timestamp": "2026-07-21 14:30:00",
        "ben_hex": {
            "name": "火天大有",
            "brief": "元亨",
            "judgment": "光明普照，大有收获",
            "lines": [1,1,1,1,0,1],
            "dong_yao": 5
        },
        "hu_hex": {"name": "泽天夬", "brief": "扬于王庭"},
        "bian_hex": {"name": "乾为天", "brief": "元亨利贞"},
        "ti": {"gua": "乾", "element": "金", "wangshuai": "相"},
        "yong": {"gua": "离", "element": "火", "wangshuai": "旺"},
        "wuxing": {"relation": "火克金", "level": "凶"},
        "prediction": {
            "overall": "【有惊无险】虽受克制，但体卦当令有力，可化险为夷...",
            "career": "...",
            "love": "...",
            "finance": "...",
            "health": "...",
            "advice": "...",
            "timing": "应期约在秋季..."
        }
    },
    "out_trade_no": "MH20260721...",
    "already_fulfilled": false
}
```

## 展示要求

拿到结果后，用通俗语言展示给用户：

1. 先说卦名和结论 — "为你起得XX卦，整体XX"
2. 解释体用关系 — 用比喻，不堆术语
3. 针对性回答用户问题
4. 给具体可操作建议
5. 说应期（什么时候有结果）
6. **若为 `premium` 档且返回含 `ai_reading` 字段，务必完整呈现这段 AI 大师深度解读（这是大师档的核心增值内容）**
7. 语气像朋友聊天，不像老师上课
8. 结尾加一句"仅供娱乐参考"

## 注意事项

1. 必须先通过"付费前置检查"确认 weixinpay 插件已安装
2. 收到 402 响应时，调用 weixinpay_pay 完成支付
3. 支付成功后必须重试请求，body 不变，Header 携带 X-Out-Trade-No
4. 如果返回 NOT_PAID，等待后重试
5. 如果返回 REFUNDED，告知用户并终止流程
6. 如果返回 FULFILL_AND_REFUND_FAILED，建议用户联系客服
7. 本服务仅供娱乐参考，不构成任何决策建议
