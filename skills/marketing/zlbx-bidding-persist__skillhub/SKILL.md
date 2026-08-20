---
name: zlbx-bidding-pay-persist
description: 全网招中标数据查询与分析助手（微信支付次数包·设备持久版）。当用户涉及以下任何场景时，必须使用此SKILL：查询招标/中标公告、搜索标讯、查找临期/即将到期项目、商机预测、推荐潜在投标供应商、分析公司主营业务/历史中标、查询公司上下游合作客户与供应商、分析竞争对手/竞对企业、查询Top采购单位/Top中标单位/Top中标品牌、招中标数据统计分析、查询品牌型号历史中标单价/价格趋势、市场分析/行业分析/采购寻源/渠道拓展等采购与投标相关场景。即使用户没有提到「知了标讯」，只要涉及招投标、采购、中标、供应商、竞争对手等关键词，都应使用本SKILL。本版本通过微信支付购买次数包，余额按设备持久化，同设备跨对话永久有效，无需注册或配置 API Key。
---

# 全网招中标数据查询（长期版）

> **计费方式**：不需要 API Key、不需要注册，**通过微信支付购买「次数包」，按接口调用扣积分使用**。
> 档位：¥10=100 积分 / ¥50=600 / ¥100=1500 / ¥500=10000（单价 ¥0.10/积分起）。
> 每次接口调用扣 1~5 积分（按工具），**桶内余额够就静默扣，用完才再弹支付**。
> ✅ 余额**按设备持久化**：同一台设备换对话、隔天再用，余额都续得上（永久有效）。

## API 概览

**基础 URL**: `https://mcp-server.zhiliaobiaoxun.com/api_pay/{工具名}`

**调用方式**: POST 请求
```
Headers:
  Content-Type: application/json
  X-Device-Id: <设备号，见下方「设备号」章节，每次调用都带>
```

> ⚠️ 本版本**不使用** `X-API-Key`。计费与鉴权由微信支付 X402 次数包完成。

---

## 🔑 设备号（进入付费流程前，必须先准备好）

余额靠设备号绑定，所以**每次接口调用都要带 `X-Device-Id`**。设备号按以下步骤获取（一次生成、长期复用）：

1. 读文件 `~/.zlbx_pay/device.json`：
   - 若存在且含 `device_id` → 直接用它。
2. 若不存在：
   - `mkdir -p ~/.zlbx_pay`
   - 生成一个 32 位十六进制随机串作为 `device_id`（如用 uuid4 去掉横杠）
   - 写入 `~/.zlbx_pay/device.json`：`{"device_id": "<刚生成的>", "created_at": "<ISO时间>"}`
3. 之后所有 `/api_pay/*` 请求都带 Header `X-Device-Id: <device_id>`。

> 设备号只是本机稳定标识，不含隐私信息。文件被删则余额无法关联到旧包，属正常。

---

## 💳 计费模型：次数包（预付积分，用完再充）

**不是每个问题都付费。** 用户付一次买一个次数包（如 ¥10=100 积分），之后每次接口调用按工具单价扣几个积分（1~5），**有余额就静默扣、不打断**；余额不足才再弹一次微信支付。体验等同"充值→用额度→用完再充"，且**同设备永久有效**。

## 💳 工作流程

### 第一步：发起数据请求
按用户意图选择工具，构造请求体，POST 到 `https://mcp-server.zhiliaobiaoxun.com/api_pay/{工具名}`，**始终带 Header `X-Device-Id`**。

### 第二步：处理 402（余额不足/首次，需购买）
收到 **HTTP 402** 说明该设备当前无可用余额、需购买次数包。响应返回：
- Header `WeixinPay-Required`（payment_code）、`X-Out-Trade-No`
- Body 含 `amount`、`description`（档位说明）

**默认按 ¥10 触发**。若让用户选档，先问「充值 ¥10/100次、¥50/600次、¥100/1500次？」，用户选定后在重试请求加 Header `X-Pay-Tier: 50`（10/50/100/500）再触发 402。

将 `WeixinPay-Required` 交给 `weixinpay_pay` 插件完成支付。购买的次数包会自动绑定到本设备号。

### 第三步：支付成功后重试
支付成功后，**重新发起刚才的请求，继续带 `X-Device-Id`**（body 不变）→ 返回 **200 + 数据**。

> 之后所有调用只要带同一个 `X-Device-Id` 即可，余额会从这张次数包里扣，**无需你手动记 `out_trade_no`**——换对话、隔天都能续上。余额用完时会再收到 402，重复第二步购买即可。

### 第四步：异常
- `"code": "NOT_PAID"` → 支付未完成，稍等重试（继续带 `X-Device-Id`）
- `"code": "REFUNDED"` → 已自动退款，告知用户并终止，不要重试
- `"code": "FULFILL_AND_REFUND_FAILED"` → 服务异常且退款失败，建议联系客服

---

## 📊 账户查询（查余额 / 查消耗）

用户问「我还剩多少次」「这几天用了多少」时调用。两个接口都是 **GET**、**免费、不扣积分、不会触发 402**，同样只需带 `X-Device-Id`。

### 查余额

```
GET https://mcp-server.zhiliaobiaoxun.com/api_pay/account/balance
Headers: X-Device-Id: <设备号>
```

返回 `data` 字段：

| 字段 | 说明 |
|---|---|
| `has_order` | 该设备是否买过次数包；`false` 表示尚未购买 |
| `balance_units` | **当前可用积分**（回答用户"还剩多少"用这个） |
| `status` | `PAID` 可用 / `UNPAID` 待支付 / `DEPLETED` 已用完 / `EXPIRED` 已过期 |
| `tier_yuan`、`total_units` | 当前次数包的档位（元）与总积分 |
| `total_units_purchased`、`total_units_consumed` | 该设备累计购买 / 累计消耗积分 |

> `balance_units` 只统计**当前生效的那张次数包**。次数包用完后会开新包，旧包不足一次调用的零头不会结转，所以别把历史次数包的余额加起来报给用户。

### 查每日消耗

```
GET https://mcp-server.zhiliaobiaoxun.com/api_pay/account/daily_consumption?days=15
Headers: X-Device-Id: <设备号>
```

参数（都可选）：`start_date` / `end_date` 用绝对日期 `YYYY-MM-DD`（闭区间）；不传区间时按 `days` 取最近 N 天（默认 15，范围 1~366）。

返回 `data` 字段：`start_date`、`end_date`（实际统计区间）、`total_consumed`（区间总消耗积分）、`total_calls`（区间总调用次数）、`daily`（逐日 `{date, consumed, calls}` 列表，**无消耗的日期补 0**，是连续日序列，可直接画图）。

> 流水从本次版本开始记录，更早的调用查不到，属正常。

---

## 工具列表（16个工具）

| 类别 | 工具名 | 功能 |
|------|--------|------|
| **标讯搜索** | `search_bids` | 按关键词/地区/金额/时间检索标讯 |
| | `query_bids_advanced` | 高级搜索：关键词分组、排除词、复杂逻辑 |
| | `get_bid_detail` | 获取单条标讯完整详情及正文 |
| | `search_expiring_projects` | 查询即将到期的周期性项目（商机预测） |
| **企业分析** | `search_company` | 按名称搜索公司列表，自动匹配总部+分子公司 |
| | `get_company_profile` | 公司基础工商信息、行业、招中标次数 |
| | `get_company_business_keywords` | 从中标记录提炼公司主营业务关键词 |
| | `get_company_partners` | 查询公司合作客户和供应商 |
| | `get_company_contacts` | 查询公司项目联系人信息 |
| | `find_competitors` | 基于投标重叠度分析竞争对手 |
| | `find_potential_bidders` | 推荐历史参与同类项目的潜在供应商 |
| **市场分析** | `get_top_purchasers` | 按关键词查询Top采购单位 |
| | `get_top_suppliers` | 按关键词查询Top中标单位 |
| | `get_top_brands` | 按产品/品类查询Top中标品牌及型号 |
| | `aggregate_bids_advanced` | 多维度聚合统计（月/季/年/省份/行业/品牌等） |
| | `get_price_trends` | 查询品牌+型号的历史中标单价记录 |

> 各工具的**详细参数、match_modes、关键词组合、bid_process、常见场景、响应结构、分页、错误码、互联网增强分析、回答后引导** —— 全部与 `zlbx-bidding` 一致，**复用 references/ 目录**。本版本仅替换"鉴权/收费"部分，业务能力和参数不变。

---

## 与其它版本的区别

| | 标准版（API Key） | 对话内版 | 本版本·设备持久 |
|---|---|---|---|
| 鉴权 | API Key | 微信次数包 | 微信次数包 |
| 余额归属 | 用户账户 | 当前对话（out_trade_no） | **设备（X-Device-Id），跨对话永久** |
| 换对话 | 续用 | 需重购 | **续用** |
| 适用 | B端高频、私域引流 | 临时/单次查询 | **常用/长期，一次充值持续用（推荐）** |
