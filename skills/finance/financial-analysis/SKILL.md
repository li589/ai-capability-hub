---
name: financial-analysis
description: 金融分析与资讯查询。支持分析诊断、市场洞察分析。当用户提出金融市场分析、资讯检索或分析诊断相关问题时，根据类别路由到对应工具获取专业结果。
user-invocable: true
metadata:
  openclaw:
    emoji: 📊
    skillKey: financial-analysis
    author: Huatai Securities
    requires:
      bins:
        - python3
install_source: official
install_method: download
skill_id: official_dH9T1ne1
enabled_at: 1787231176844
version: 1.0.0
name_zh: 华泰-金融分析
---

# 金融分析与资讯查询工具 Skill

当用户提出金融市场分析、金融资讯查询、分析诊断相关问题时，根据问题类别路由到对应的工具获取专业结果。

## 触发条件

当用户的问题属于以下任何类别时，应激活此 Skill：

- 个股分析：综合分析、投资价值、基本面、财报解读、事件分析、股价走势、机构观点、估值分析、建仓/出货时机、投资逻辑制定
- 大盘分析（A股/港美股）：走势预测、走势分析、资金流向、涨跌归因、事件催化、热门板块、事件影响、估值、大盘复盘
- 概念/板块/行业/ETF 分析：综合分析、投资价值、增长前景、生命周期、事件影响、走势分析与预测、资金面、机构观点、估值
- 股票多标的对比：同行业/跨行业综合对比、基本面对比、财务/财报对比、走势对比、指标对比
- 金融资讯查询：个股/多股相关新闻资讯检索、利好利空消息分类整理、指定时间范围内的资讯汇总、板块/行业/市场新闻聚合
- 宏观事件与选股/荐股：基于宏观经济、地缘政治、政策变化等事件分析其对金融市场的影响
- 分析诊断：个股分析诊断

详细的问题分类和示例请参阅 references/CATEGORIES.md

## 不应触发的场景

- 纯编程或技术开发问题
- 金融条件选股（如"帮我找PE低于20的股票"）
- 涉及具体交易操作指令（如"帮我买入XX"）
- 非金融类的新闻查询（如天气预报、体育赛事等）

## 响应结构

成功：
```json
{ "ok": true, "data": { "answer": "..." }, "error": null }
```

失败：
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": -2,
    "message": "面向用户的中文说明",
    "category": "business",
    "retriable": false,
    "hint": "下一步该怎么做"
  }
}
```

成功时直接展示 `data.answer`，已是结构化 Markdown 格式。失败时按 `error.category` 处理：

| category | 含义 | 处理 |
|---|---|---|
| `validation` | 参数不合规 | 不重试，按 `hint` 引导用户调整 |
| `business` | 接口返回业务错误 | 不重试，告知用户具体原因 |
| `network` | 网络/超时/5xx | 临时问题，可稍后再试 |

## 工具


### diagnosisStock
对个股、ETF、板块等进行分析诊断。

**何时调用**：用户要求对个股、ETF、板块等进行分析诊断、诊断报告。

**参数**：
- `query`：用户问题（必填）

**执行**：`python3 financial_analysis.py diagnosisStock --query <query>`

---

### marketInsight
市场洞察，覆盖个股分析、大盘分析、板块/行业分析、多标的对比、金融资讯、宏观事件与选股等。

**何时调用**：不属于分析诊断的其他金融问题。

**参数**：
- `query`：用户问题（必填）

**执行**：`python3 financial_analysis.py marketInsight --query <query>`

## 调用模式速查

| 用户意图 | 类别 | 调用路径 |
|---|---|---|
| "帮我分析一下比亚迪" | 分析诊断 | `diagnosisStock` |
| "帮我诊断一下招商中证1000指数增强A" | 分析诊断 | `diagnosisStock` |
| "今天大盘为什么跌了？" | 市场洞察 | `marketInsight` |
| "对比一下东方财富和华泰证券" | 市场洞察 | `marketInsight` |
| "整理长江电力最近48小时的利好利空资讯" | 市场洞察 | `marketInsight` |

## 配置

环境变量：

| 变量 | 必填 | 说明 |
|---|---|---|
| `FINANCIAL_ANALYSIS_SERVICE_URL` | 否 | 后端服务地址（默认 `https://ai.zhangle.com`） |
| `HT_APIKEY` | 是 | 认证密钥 |

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

4. **当前会话立即生效**：执行前 `export HT_APIKEY=<Key>`，或内联 `HT_APIKEY=<Key> python3 financial_analysis.py ...`。
5. **更换 Key**：重复步骤 3，新值覆盖旧的。
6. **安全**：不要把 Key 写进对外发送的代码 / 日志 / 截图。
