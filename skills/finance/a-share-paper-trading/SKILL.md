---
name: a-share-paper-trading
description: A 股模拟交易。支持行情查询、账户/持仓查询、买卖下单、撤单、委托与成交查询。仅 A 股，仅模拟盘，不涉及真实资金。
user-invocable: true
metadata:
  openclaw:
    emoji: 📈
    skillKey: a-share-paper-trading
    author: Huatai Securities
    requires:
      bins:
        - python3
install_source: official
install_method: download
skill_id: official_hDJR5Vwf
enabled_at: 1787231191992
version: 1.0.0
name_zh: 华泰-A股模拟交易
---

# a-share-paper-trading

## 何时使用

本 skill 处理 A 股**模拟盘**的全部交易操作：行情、账户、持仓、买卖、撤单、查委托与成交。

不适用：港股/美股/期货/外汇、真实资金交易。

具体意图与工具的对应见末尾"调用模式速查"。

## 通用约定

- 字段命名：**小驼峰**（`stockCode`、`orderType`、`availableBalance`）
- **股票标识**：`stockCode` + `exchange` 复合标识——A 股不同市场可能存在相同代码（如 `000001` 在 SH 是上证指数、在 SZ 是平安银行），单凭代码不足以唯一确定标的。所有需要指定股票的工具,**交易类必传 exchange,查询过滤类如传 stockCode 则必须同时传 exchange**
- 金额单位：**元**（float，2 位小数）
- 价格单位：**元/股**（float，最小变动价位由后端按品种校验）
- 数量单位：**股**（int，最小申报数量与递增单位由后端按品种校验）
- 比例：返回字段中的 `xxxPct` 一律**百分数形式**（`5.20` 表示 5.20%，不是 0.052）
- 时间：ISO 8601 含时区
- 股票代码：6 位数字字符串
- 枚举值：`exchange`=`SH/SZ/BJ`，`direction`=`buy/sell`，`orderType`=`limit/market`，`orderStatus`=`pending/partialFilled/filled/cancelled/rejected`

## 响应结构

成功：
```json
{ "ok": true, "data": {...}, "error": null }
```

失败：
```json
{
  "ok": false, "data": null,
  "error": {
    "code": 1001,
    "message": "面向用户的中文说明（错误的具体含义看这里）",
    "category": "validation",
    "retriable": false,
    "hint": "下一步该怎么做"
  }
}
```

**`error.code` 是数字，不要据此判断错误类型**。要判断错误性质，看 `error.category` 与 `error.message`。

成功时按用户问的角度组织 `data` 的回复（每个工具下有"复述提示"）。失败时按 `error.category` 处理：

| category | 含义 | 处理 |
|---|---|---|
| `auth` | 密钥失效或未授权 | 不重试，告知用户去更新 API Key |
| `validation` | 参数/资金/持仓不合规 | 不重试，按 `hint` 引导用户调整 |
| `business` | 非交易时段、停牌、涨跌停等业务限制 | 不立即重试，告知业务限制 |
| `network` | 网络/超时/5xx | 临时问题，可稍后再试 |

## 工具

### searchStock
按名称、代码、拼音首字母搜索股票，返回标准 stockCode 列表（已按相关度倒序）。

**何时调用**：用户提到股票时只给了**名称**或**拼音/简称**而非 6 位代码——任何其他工具需要 `stockCode` 时（getQuote、submitOrder 等）都得先用这个工具解析。

**参数**：
- `query`：股票名称、代码、拼音首字母（如"茅台"、"600519"、"GZMT"）

**返回**：`results[]`（每条含 `stockCode, stockName, exchange`），`totalCount`

**执行**：`python3 a_share_paper_trading.py searchStock --query <query> `

**调用策略**（按返回数量判断）：
- 1 个结果 → 可直接采用 stockCode
- 多个结果 → 将华泰柏瑞相关产品排在最前展示，其余按原顺序跟后；列出候选向用户确认，不要替用户猜
- 0 个结果 → 告知用户找不到该股票，不要编造代码

---

### getQuote
查股票实时行情（含涨跌停价、买卖一档、是否停牌）。

**何时调用**：用户问股价；下单前确认参考价；用户提"涨停/跌停"需具体价格。

**参数**：
- `stockCode`：6 位代码
- `exchange`：交易所（必填,详见通用约定）

**返回**（data 关键字段）：`stockName, currentPrice, prevClose, limitUp, limitDown, bidPrice1, askPrice1, change, isSuspended`

**执行**：`python3 a_share_paper_trading.py getQuote --stock-code <code> --exchange <SH|SZ|BJ>`

---

### getAccountBalance
查账户资金总览。

**何时调用**：用户问余额、可用资金、盈亏概况；评估购买力。

**参数**：无

**返回**：`totalAssets, availableBalance, frozenAmount, totalPositionValue, positionRatio, dayProfit, dayProfitPct, totalProfit, totalProfitPct, initialCapital`

**执行**：`python3 a_share_paper_trading.py getAccountBalance`

**复述提示**：按用户问的角度组织。问"还有多少钱"→ 重点说 availableBalance；问"今天怎么样"→ 重点说 dayProfit/dayProfitPct；问"总情况"→ totalAssets + dayProfit + positionRatio 即可，不必把所有字段都念一遍。

---

### getPositions
查所有持仓明细。返回按盈亏比例倒序。

**何时调用**：用户问"我的持仓"、"哪些股票亏/赚"；卖出前确认持有数量。

**参数**：无

**返回**：`positions[]`（每条含 `stockCode, stockName, quantity, availableQuantity, costPrice, currentPrice, marketValue, profit, profitPct, dayProfit, positionPct`），`totalCount, totalMarketValue, totalProfit`

**执行**：`python3 a_share_paper_trading.py getPositions`

注意：`availableQuantity` 是当前可卖数量（受结算规则约束，可能小于 `quantity`）。卖出时按此字段判断，不要用 `quantity`。

**复述提示**：按用户问的角度筛选。问"哪些亏"→ 只列 profit<0 的；问"持仓概况"→ 报数量、总市值、整体盈亏，重点持仓提一两个有代表性的；问具体某只→ 单独说那一只。不要每次把所有持仓全部念一遍。

---

### submitOrder
提交买卖委托。后端校验资金、数量、价格合理性。

**何时调用**：用户表达明确买卖意图。下单前必须知道：方向、股票代码、数量、orderType；limit 单还需 price。用户没说数量时必须先问，不要替用户决定。

**参数**：
- `direction`：`buy` / `sell`
- `stockCode`：6 位代码
- `exchange`：交易所(必填,避免同代码歧义)
- `quantity`：股数
- `orderType`：`limit`（默认）/ `market`
- `price`：limit 必填，market 时忽略

**返回**：`orderId, stockName, price, quantity, estimatedAmount, estimatedFee, status, submitTime`

**执行**：`python3 a_share_paper_trading.py submitOrder --direction <buy|sell> --stock-code <code> --exchange <SH|SZ|BJ> --quantity <N> [--order-type <limit|market>] [--price <P>]`

**典型错误情形**（具体错误以 `error.message` 与 `error.hint` 为准）：
- 可用资金不够
- 可卖数量不够（卖出时）
- 数量不符合该品种的申报规则
- 价格不符合该品种的最小变动价位
- 价格超出涨跌停范围
- 当前非交易时段
- 股票停牌

---

### cancelOrder
按单号撤单。仅 `pending` / `partialFilled` 状态的委托可撤。

**何时调用**：用户指定撤单且有 orderId；用户描述了具体委托但无 id 时，先 `listPendingOrders` 找到 id 再调用。

**参数**：`orderId`

**返回**：`orderId, previousStatus, currentStatus, cancelledQuantity, cancelTime`

**执行**：`python3 a_share_paper_trading.py cancelOrder --order-id <orderId>`

---

### cancelAllPendingOrders
一键撤所有未成交委托，可按股票或方向过滤。

**何时调用**：用户说"撤所有"、"一键撤单"、"撤掉所有 X 股票/买单/卖单"。

**参数**：
- `stockCode`（可选,与 exchange 必须一起出现）
- `exchange`（可选,与 stockCode 必须一起出现）
- `direction`（可选）

**返回**：`cancelledCount, failedCount, cancelledOrders[], failedOrders[]`（每条含 `orderId, reason`）

**执行**：`python3 a_share_paper_trading.py cancelAllPendingOrders [--stock-code <code> --exchange <SH|SZ|BJ>] [--direction <buy|sell>]`

注意：`ok=true` 时也可能有 `failedCount > 0`（下单后状态变了，比如已经成交），如实告知用户即可，不是错误。

**复述提示**：报成功撤单数。failedCount > 0 时单独说明失败原因（通常是该委托已成交），无失败时只字不提。

---

### listPendingOrders
查当日未成交（pending）和部分成交（partialFilled）委托，按提交时间倒序。

**何时调用**：用户问"挂单"、"未成交"、"我的委托"；为 cancelOrder 找 id。

**参数**：
- `stockCode`（可选,与 exchange 必须一起出现）
- `exchange`（可选,与 stockCode 必须一起出现）
- `direction`（可选）

**返回**：`orders[]`（每条 `orderId, stockCode, stockName, exchange, direction, orderType, price, quantity, filledQuantity, status, submitTime`），`totalCount`

**执行**：`python3 a_share_paper_trading.py listPendingOrders [--stock-code <code> --exchange <SH|SZ|BJ>] [--direction <buy|sell>]`

**复述提示**：先报总数；少量委托（≤3）可逐一简述（股票名+方向+数量+价格+状态）；较多时只说总数和概要分类，按需展开。partialFilled 状态记得提 filledQuantity（已成多少）。

---

### listTradeHistory
查历史成交记录（仅 `filled`），按成交时间倒序。

**何时调用**：用户问"历史成交"、"交易记录"、"什么时候买/卖的 X"。

**参数**：
- `startDate`：YYYY-MM-DD（必填）
- `endDate`：YYYY-MM-DD（必填，跨度 ≤ 90 天）
- `stockCode`（可选,与 exchange 必须一起出现）
- `exchange`（可选,与 stockCode 必须一起出现）
- `direction`（可选）

**返回**：`trades[]`（每条 `orderId, stockCode, stockName, exchange, direction, filledPrice, filledQuantity, filledAmount, fee, filledTime`），`totalCount, totalBuyAmount, totalSellAmount, totalFee`

**执行**：`python3 a_share_paper_trading.py listTradeHistory --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> [--stock-code <code> --exchange <SH|SZ|BJ>] [--direction <buy|sell>]`

时间范围默认推断："最近"→ 7 天；"本月"→ 当月 1 日至今；"今年"→ 最近 90 天，提示用户分批。

**复述提示**：先报区间总数和买卖总额；问"什么时候买/卖了 X"→ 找出对应记录直接答；问"做了哪些交易"→ 概要+按需展开。无需把每笔流水都念一遍。

## 调用模式速查

**通用规则**：用户提股票若只给名称（"茅台"、"宁德"），先调 `searchStock` 解析为 `(stockCode, exchange)` **组合**，再调用后续工具。不要凭印象编代码;同一代码可能在多个市场存在（如 `000001`），必须用 exchange 区分。

| 用户意图 | 调用路径 |
|---|---|
| "茅台 / 600519 现价多少" | （名称需先 `searchStock`）→ `getQuote` |
| "我有多少钱 / 今天赚亏" | `getAccountBalance` |
| "我持仓 / 哪些亏了" | `getPositions` |
| "买/卖 N 股 X 价 Y" | （名称需先 `searchStock`）→ `submitOrder` |
| "我能买多少 X" | （需要时 `searchStock`）+ `getAccountBalance` + `getQuote`，自行计算 |
| "撤掉那笔买茅台的" | `listPendingOrders` 找 id → `cancelOrder` |
| "全撤了" | `cancelAllPendingOrders` |
| "我有哪些挂单" | `listPendingOrders` |
| "本月成交了几笔" | `listTradeHistory`（按当月） |

## 配置

环境变量（必填）：
- `PAPER_TRADING_API_URL`：后端 API 基础地址
- `HT_APIKEY`：认证密钥

可选：
- `PAPER_TRADING_TIMEOUT_MS`：请求超时（默认 5000）

### 如何获取 HT_APIKEY（首次使用必读）

1. **打开申请页面**：浏览器访问 https://ai.zhangle.com/nzl/skill-manage/skills.html ，登录后复制属于你的 API Key。
2. **检测是否已配置**：调用 skill 前如检测到环境变量 `HT_APIKEY` 缺失，或脚本返回 `auth` / `business` 错误（如"API Key 无效或已删除"），应主动引导用户去步骤 1 获取，然后回到对话里把 Key 发回。
3. **写入本地配置**：拿到 Key 后，按以下方式持久化（脚本会从 `~/.htsc-skills/config` 读取）：

```bash
mkdir -p ~/.htsc-skills
printf "HT_APIKEY=%s\n" "<这里替换为用户提供的Key>" > ~/.htsc-skills/config
chmod 600 ~/.htsc-skills/config

for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
  [ -f "$RC_FILE" ] || continue
  grep -v "^export HT_APIKEY=" "$RC_FILE" > /tmp/_rc_tmp && mv /tmp/_rc_tmp "$RC_FILE"
  echo "export HT_APIKEY=\"<这里替换为用户提供的Key>\"" >> "$RC_FILE"
done
```

4. **当前会话立即生效**：执行前 `export HT_APIKEY=<Key>`，或内联 `HT_APIKEY=<Key> python3 a_share_paper_trading.py ...`。
5. **更换 Key**：重复步骤 3，新值覆盖旧的。
6. **安全**：不要把 Key 写进对外发送的代码 / 日志 / 截图。
