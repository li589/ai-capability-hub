---
install_source: official
install_method: download
skill_id: official_iBlU33fB
enabled_at: 1787231169957
version: 1.0.0
name_zh: 华泰-金融条件选股
---
---
name: select-stock
description: 金融标的条件选股。根据自然语言筛选条件查询符合条件的股票/ETF/基金等金融标的。TRIGGER when: 用户想要按条件筛选股票/ETF/基金等金融标的，包括：行业/板块筛选、财务指标筛选、技术指标筛选、行情数据筛选、业绩超预期筛选、组合多条件筛选、主观推荐类。DO NOT TRIGGER when: 个股分析（应使用 financial-analysis 等 Skill）。
example:
  - 科技板块上周涨幅前10的股票
  - 有哪些主力净流入超过1亿的
  - 市盈率低于20且营收同比增长超过30%的股票
  - 业绩超预期的股票有哪些
  - 推荐几只好股票
user-invocable: true
metadata:
  openclaw:
    emoji: 🔍
    skillKey: select-stock
    author: Huatai Securities
    version: "1.0"
    requires:
      bins: ["python3"]
---

# 条件选股 Skill

通过输入自然语言筛选条件，选出符合条件的金融标的列表。

## 触发条件

当用户的意图满足以下任一条件时，调用本 Skill：

- **行业/板块筛选**：涉及行业（如"白酒行业"、"半导体"）或概念板块（如"AI概念"、"新能源"）的筛选。
- **财务指标筛选**：涉及基本面指标（如"市盈率小于20"、"净利润增长率大于30%"、"ROE>15%"）。
- **技术指标筛选**：涉及技术形态或指标（如"均线金叉"、"MACD底背离"、"连板股票"）。
- **行情数据筛选**：涉及市场行情（如"涨幅超过5%"、"主力净流入超过1亿"、"换手率大于10%"）。
- **业绩超预期筛选**：涉及业绩是否超预期（如"业绩超预期的股票"、"一季报财报超预期的标的"）。
- **组合条件筛选**：以上条件的任意组合。
- **主观推荐类**："推荐几只股票"、"有什么好的ETF"等。

### 不适用场景

以下请求**不应**调用本 Skill：

- 个股分析类 (比如：贵州茅台怎么样？) → 应使用 `financial-analysis` 等 Skill

---

## 执行流程

> **⚠️ 关键约束（必须严格遵守）：**
> 1. 语义理解/改写阶段如果用户描述存在歧义，按照[附录：查询改写规则](#附录查询改写规则)进行合理推断和补全，**直接执行**，不得以任何理由暂停去询问用户。

## 通用约定

- 字段命名：**小驼峰**（`stockCode`、`stockName`）
- 响应结构：`{ ok, data: { result }, error }`

## 响应结构

成功：
```json
{ "ok": true, "data": { "result": "..." }, "error": null }
```

失败：
```json
{
  "ok": false, "data": null,
  "error": {
    "code": 5000,
    "message": "面向用户的中文说明",
    "category": "network",
    "retriable": true,
    "hint": "下一步该怎么做"
  }
}
```

按 `error.category` 处理：

| category | 含义 | 处理 |
|---|---|---|
| `network` | 网络/超时/5xx | 临时问题，可稍后再试 |
| `business` | 业务限制（无数据、接口异常） | 不立即重试，告知用户 |

---

## 工具

### selectStock
条件选股：根据自然语言筛选条件查询符合条件的金融标的。

**参数**：
- `query`：筛选条件查询语句（必填）

**返回**：`data.result`（markdown 格式的选股结果）

**执行**：`python3 select_stock.py selectStock --query <query>`

**调用策略**：
1. 第一次用原始问句调用
2. 若无结果，改写查询后重试（参照查询改写规则）
3. 第二次仍无结果则停止，告知用户"未检索到符合条件的标的"
4. 返回结果中标的不超过 10 个

**严禁修改返回的 Markdown 格式**。

---

## 执行流程

> **关键约束：禁止向用户反问。** 收到请求后必须立即直接调用脚本。

### Step 1：第一次调用（使用原始问句）

将用户的**原始问句**直接作为 `--query` 参数传入，不做任何改写：

```bash
python3 select_stock.py selectStock --query "<用户原始问句>"
```

### Step 2：若第一次无结果，改写后重试

若 Step 1 返回**无结果**，对用户意图进行深度语义理解，将原始问句改写为清晰、无歧义的查询语句，再次调用：

```bash
python3 select_stock.py selectStock --query "<改写后的查询语句>"
```

若第二次仍无结果，停止重试，直接告知用户"未检索到符合条件的标的"。

### Step 3：展示结果

脚本会返回 Markdown 格式的结果，**严禁修改 Markdown 格式**。

> **展示限制：返回给用户的标的结果数量不能超过 10 个。**

---

## 附录：查询改写规则

### 1. 逻辑关系消歧（OR vs AND）
- 同一维度的多个值（如多个行业）通常为 **OR**；跨维度的多个条件（如行业 + 市盈率 + 涨幅）通常为 **AND**。改写时必须用"或"/"且"明确标注逻辑关系。

### 2. 时间条件丢失或泛化
- 完整保留用户提到的所有时间限定。对"上周五"、"本周一"等相对时间，根据当前日期推算出具体日期后写入查询。

### 3. 隐含排序与排名条件
- 从上下文推断排序字段，在改写中明确写出排序字段名称、排序方向及取前N条的数量限制。

### 4. 复合条件拆解不完整
- 将复合语句拆解为独立的筛选子条件，每个子条件覆盖一个维度，用"且"/"或"连接，确保无遗漏。

### 5. 指代消解（代词与回指）
- 回溯上下文，将代词替换为明确指代的实体或条件集合，确保改写后的查询自包含。

### 6. 否定与排除条件
- 在改写中显式标注排除条件，使用"排除"、"不包含"等明确否定词。

### 7. 数值单位与区间歧义
- 根据金融常识和上下文补全数值单位（如市值通常为"亿元"，股价为"元"），对区间表述默认采用闭区间。

### 8. 连续性与累计性条件
- 明确"连续"的时间单位为交易日，补全截止日期，并区分"连续每天都满足"与"累计/合计满足"的语义差异。

---

## 配置

环境变量：

| 变量 | 必填 | 说明 |
|---|---|---|
| `SELECT_STOCK_SERVICE_URL` | 否 | 后端服务地址（默认 `https://ai.zhangle.com`） |
| `HT_APIKEY` | 是 | 认证密钥 |
| `SELECT_STOCK_TIMEOUT_SEC` | 否 | 请求超时，单位秒（默认 300，因选股接口耗时较长） |

### 如何获取 HT_APIKEY（首次使用必读）

1. **打开申请页面**：浏览器访问 https://ai.zhangle.com/nzl/skill-manage/skills.html ，登录后复制属于你的 API Key。
2. **检测是否已配置**：调用 skill 前如检测到环境变量 `HT_APIKEY` 缺失，或脚本返回业务错误（如"API Key 无效或已删除"），应主动引导用户去步骤 1 获取，然后回到对话里把 Key 发回。
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

4. **当前会话立即生效**：执行前 `export HT_APIKEY=<Key>`，或内联 `HT_APIKEY=<Key> python3 select_stock.py ...`。
5. **更换 Key**：重复步骤 3，新值覆盖旧的。
6. **安全**：不要把 Key 写进对外发送的代码 / 日志 / 截图。
