---
name: 紫微斗数命盘解读
version: 1.0.0
description: 基于紫微斗数理论，根据出生时间生成专业命盘解读，包含性格、事业、财运、感情等全方位分析
author: 熵海领航
category: 命理预测
tags:
  - 紫微斗数
  - 命盘解读
  - 命理分析
  - 运势预测
pricing:
  type: paid
  price: 9.90
  currency: CNY
  unit: 次
---

# 紫微斗数命盘解读

基于传统紫微斗数理论，结合现代 AI 技术，为用户提供专业、详细的命盘解读服务。

## 功能特性

- **精准排盘**：阳历转农历，准确计算命宫、身宫、十二宫位
- **十四主星**：安紫微星及其他十三颗主星
- **专业解读**：调用 DashScope LLM 生成通俗易懂的命盘解读
- **全方位分析**：涵盖性格特质、事业运势、财运分析、感情婚姻、健康提示

## 付费前置检查

在调用此技能前，Agent 必须检查是否已安装 `weixinpay` 插件：

```python
# 检查 weixinpay 插件是否可用
if not has_extension("weixinpay"):
    return "请先安装 weixinpay 插件以使用付费技能"
```

## 工作流程

### 第一步：提交出生信息

**请求方式**：POST  
**请求地址**：`https://meihua.astrakairos.com/ziwei/api/resource`

**请求参数**：
```json
{
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

**参数说明**：
- `year` (int): 出生年份（公历），范围 1900-2100
- `month` (int): 出生月份（公历），范围 1-12
- `day` (int): 出生日期（公历），范围 1-31
- `hour` (int): 出生时辰（24小时制），范围 0-23
- `gender` (str): 性别，"男" 或 "女"

**首次响应**（402 Payment Required）：
```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "请支付后获取紫微斗数命盘解读",
  "out_trade_no": "ZW1722678400ABCD1234",
  "WeixinPay": {
    "WeixinPay-Required": "payment_code_xxx",
    "prompt": "请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay"
  }
}
```

**响应头**：
- `X-Out-Trade-No`: 订单号
- `WeixinPay-Required`: 支付码

### 第二步：调用微信支付

使用第一步返回的 `WeixinPay-Required` 值调用微信支付插件：

```python
# 调用 weixinpay 插件完成支付
payment_result = weixinpay_pay(paymentCode="payment_code_xxx")
```

### 第三步：重试请求（携带订单号）

支付成功后，**必须**使用相同的请求参数，并在请求头中携带订单号重新发起请求：

**请求方式**：POST  
**请求地址**：`https://meihua.astrakairos.com/ziwei/api/resource`

**请求头**：
```
X-Out-Trade-No: ZW1722678400ABCD1234
```

**请求参数**（与第一步完全相同）：
```json
{
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

**成功响应**（200 OK）：
```json
{
  "code": "SUCCESS",
  "message": "命盘解读生成完成",
  "out_trade_no": "ZW1722678400ABCD1234",
  "result": {
    "birth_info": {
      "year": 1990,
      "month": 5,
      "day": 15,
      "hour": 14
    },
    "lunar_info": {
      "year": 1990,
      "month": 4,
      "day": 21
    },
    "year_stem_branch": "庚午",
    "ming_gong": {
      "position": 5,
      "branch": "巳"
    },
    "shen_gong": {
      "position": 11,
      "branch": "亥"
    },
    "main_stars": {
      "紫微": "巳",
      "天机": "辰",
      "太阳": "卯"
    },
    "interpretation": "# 紫微斗数命盘解读\n\n## 命宫特质\n您的命宫位于巳宫..."
  }
}
```

### 第四步：展示结果

将 `result.interpretation` 内容以 Markdown 格式展示给用户，包含：
- 命宫特质（性格、天赋、人生格局）
- 事业运势（行业方向、发展趋势）
- 财运分析（财运特点、理财建议）
- 感情婚姻（感情特质、择偶建议）
- 健康提示（易患疾病、养生建议）
- 流年运势（今年整体运势）
- 人生建议（核心建议、开运方法）

### 第五步：异常处理

根据返回的 `code` 字段处理不同情况：

| code | 含义 | 处理方式 |
|------|------|---------|
| `SUCCESS` | 解读生成完成 | 展示 `result.interpretation` 给用户 |
| `PAYMENT_REQUIRED` | 需要支付 | 引导用户完成支付 |
| `NOT_PAID` | 支付未完成 | 提示用户"支付尚未完成，请重新支付" |
| `FAILED` | 处理失败 | 告知用户"服务异常，请稍后重试或联系客服" |

## 技术实现

### 核心算法

1. **阳历转农历**：使用 `lunardate` 库进行精确转换
2. **命宫计算**：`(14 - 农历月份 + 时辰地支序号) % 12`
3. **身宫计算**：`(农历月份 + 时辰地支序号) % 12`
4. **紫微星定位**：根据农历日期和年干查表确定
5. **其他主星**：基于紫微星位置推算天府星系和紫微星系

### AI 解读生成

- 调用 DashScope Qwen-Plus 模型
- 输入：命盘数据（命宫、身宫、主星分布、十二宫位）
- 输出：通俗易懂的专业解读（约 1000-1500 字）
- 超时时间：60 秒

### 降级策略

当 DashScope API 不可用时，返回简化版解读模板，确保服务可用性。

## 示例

### 示例 1：男性命盘

**请求**：
```json
{
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

**解读摘要**：
- 年柱：庚午
- 命宫：巳宫
- 身宫：亥宫
- 主星：紫微在巳、天机在辰、太阳在卯

### 示例 2：女性命盘

**请求**：
```json
{
  "year": 1995,
  "month": 8,
  "day": 20,
  "hour": 9,
  "gender": "女"
}
```

**解读摘要**：
- 年柱：乙亥
- 命宫：申宫
- 身宫：寅宫
- 主星：天府在申、太阴在未、贪狼在午

## 注意事项

1. **出生时间准确性**：命盘解读的准确性取决于出生时间的准确性，建议使用精确到小时的出生时间
2. **时辰划分**：中国传统时辰以 2 小时为一个单位（子时 23-1 点，丑时 1-3 点，依此类推）
3. **仅供参考**：命理分析仅供娱乐和参考，不应作为重大决策的唯一依据
4. **隐私保护**：用户的出生信息仅用于命盘计算，不会存储或泄露

## 部署说明

### 环境要求

- Python 3.8+
- FastAPI
- Uvicorn
- lunardate
- httpx
- python-dotenv

### 配置文件

创建 `.env` 文件：

```bash
MODE=live
PRICE=990
BASE_URL=https://meihua.astrakairos.com/ziwei
MCH_ID=你的商户号
APP_ID=你的应用ID
MCH_SERIAL=你的证书序列号
MCH_APIV3_KEY=你的APIv3密钥
MCH_PRIVATE_KEY_PATH=/path/to/apiclient_key.pem
SKILLHUB_DEVELOPER_ID=sh-你的开发者ID
SKILLHUB_PUB_KEY_ID=你的公钥ID
SKILLHUB_PRIVATE_KEY_PATH=/path/to/skillhub_private_key.pem
DASHSCOPE_API_KEY=你的DashScope API Key
```

### 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8101 --reload
```

## 版本历史

### v1.0.0 (2026-08-03)

- ✨ 初始版本发布
- ✅ 支持紫微斗数命盘计算
- ✅ 集成 DashScope LLM 生成解读
- ✅ 支持微信支付
- ✅ 支持 X402 协议
- ✅ 部署到生产环境
