---
name: invest-calendar
version: 1.0.0
description: 财经事件日历技能。查询CPI/PPI/GDP/PMI/非农/PCE等宏观数据发布时间、FOMC/MLF/LPR等央行决议、财报/IPO/解禁日程，一键生成可交互财经日历，提供重大事件市场影响分析。即使用户没说"财经日历"，只要问"什么时候发布""本周有什么事件""非农几号"等即触发。
metadata:
  display_name: 投资财经日历
  display_name_en: Invest Calendar
  description_zh: 财经事件日历技能。查询宏观数据发布时间、央行决议、财报日程，生成财经日历，分析事件影响。
  description_en: Financial calendar skill for tracking macro data releases,
    central bank decisions, earnings schedules.
  category: 金融投资
  author: invest-calendar-team
disable-model-invocation: true
---

# 投资财经日历

## 能力概述

帮用户回答"未来某个时间点会发生什么财经事件"——投资决策中的高频痛点。三层能力：

1. **查询事件**：某天/某周/某月有哪些宏观数据发布、央行决议、财报披露
2. **构建日历**：生成可交互的 HTML 财经日历
3. **影响分析**：重大事件（FOMC/非农/CPI）对市场的典型影响规律

## 能力边界

### 能做
- 查询未来 1-3 个月的财经事件时间安排
- 按日期/区间/国家/重要性/关键词筛选事件
- 生成可交互 HTML 日历（月历 + 列表双视图）
- 提供重大事件的市场影响参考（基于历史规律）
- 按历史发布规律预排 API 未覆盖的远期月份

### 不能做
- 查询已发生的行情数据（用 westock-data / ad-api）
- 做技术指标分析（用 ad-technical-analysis）
- 做因子分析（用 ad-factor-analysis）
- 提供投资建议或预测涨跌（仅提供事件信息与历史影响参考）
- 实时行情推送（本技能是事件日历，不是行情终端）

## 数据源

按优先级使用，确保任何月份都不空白：

| 优先级 | 数据源 | 覆盖范围 | 特点 |
|--------|--------|---------|------|
| 主源 | 华尔街见闻 API | 未来 1-2 个月 | 结构化，含前值/预期/实际/4星评级，覆盖 20+ 国家 |
| 兜底 | 历史规律预排 | 未来 3 个月 | 基于各指标月度发布规律生成，远期月份兜底 |
| 校准 | 官方源 | 关键事件 | 国家统计局/BLS/BEA/央行官网 |

### 华尔街见闻 API

公开 API，无需鉴权：
```
GET https://api-one-wscn.awtmt.com/apiv1/finance/macrodatas?start={unix_ts}&end={unix_ts}
```
返回字段：public_date(秒级时间戳)、country、title、importance(1-4星)、calendar_type(FD数据型/FE事件型)、actual、forecast、previous、unit。

详细调用方法见 `references/data-sources.md`。

### 历史规律预排

当 API 无数据时，基于各指标月度发布规律生成预排。完整规律见 `references/recurrence-rules.md`，核心规律：

| 指标 | 发布日 | 时间(北京) | 重要性 |
|------|--------|-----------|--------|
| 中国 CPI/PPI | 每月9-10日 | 09:30 | ★★★ |
| 中国官方PMI | 每月最后一天 | 09:00 | ★★★ |
| 中国 MLF | 每月15日 | 09:20 | ★★★ |
| 中国 LPR | 每月20日 | 09:15 | ★★★ |
| 中国社融/M2 | 每月10-15日 | — | ★★★ |
| 美国非农 | 每月第一个周五 | 20:30 | ★★★★ |
| 美国 CPI | 每月11-14日 | 20:30 | ★★★★ |
| 美国 PCE | 每月最后一个周五 | 20:30 | ★★★★ |
| FOMC 决议 | 每年8次 | 02:00 | ★★★★ |
| Jackson Hole | 每年8月22-24日 | 22:00 | ★★★ |

## 事件分类体系

共 9 大类（详见 `references/event-taxonomy.md`）：

| 类别 | 代码 | 典型事件 |
|------|------|---------|
| 宏观经济 | macro | CPI/PPI/GDP/PMI/非农/PCE |
| 央行政策 | monetary | FOMC/MLF/LPR/ECB/BOJ决议 |
| 重要会议 | meeting | OPEC+/G20/Jackson Hole/两会 |
| 财报披露 | earnings | 苹果/台积电/A股定期报告 |
| IPO新股 | ipo | 申购日/上市日 |
| 公司事件 | corporate | 分红/解禁/增发/重组 |
| 指数调整 | index | MSCI/沪深300调整 |
| 政策法规 | policy | 新规实施/关税调整 |
| 重大国际 | geopolitical | 选举/贸易谈判/地缘冲突 |

## 重要性评级

采用 4 星制（对齐华尔街见闻）：

| 星级 | 定义 | 典型事件 |
|------|------|---------|
| ★★★★ | 直接影响货币政策预期，引发全市场剧烈波动 | FOMC决议、非农、CPI、PCE |
| ★★★ | 影响特定板块或高关注度 | PMI、GDP、MLF/LPR、OPEC+ |
| ★★ | 常规数据/重要事件 | 零售销售、PPI、重点财报 |
| ★ | 次要数据/小国数据 | 外汇储备、初请失业金 |

中国市场特殊加权：MLF/LPR/社融对中国市场的影响权重高于国际同类事件。

## 工作流

### 场景 1：查某事件何时发布

当用户问"非农什么时候发"时：
1. 调用 `scripts/query_events.py --keyword 非农` 查询
2. 若 API 有数据，直接返回日期时间
3. 若无数据，按规律（每月第一个周五 20:30）计算下次日期
4. 输出：日期 + 时间 + 重要性 + 关联资产

### 场景 2：查某时段事件列表

当用户问"本周有什么重要数据"时：
1. 计算本周一到周日日期
2. 调用 `scripts/query_events.py --start {周一} --end {周日}`
3. 按日期分组表格输出，高影响事件红色标注

### 场景 3：生成财经日历

当用户问"帮我做个8月财经日历"时：
1. 调用 `scripts/generate_calendar.py --month 2026-08 --output 8月日历.html`
2. 脚本自动：先试 API → 无数据走预排 → 注入 HTML 模板
3. 输出 HTML 文件给用户

### 场景 4：事件影响分析

当用户问"FOMC 降息对 A 股有什么影响"时：
1. 查询下次 FOMC 时间
2. 读取 `references/impact-playbook.md` 的 FOMC 章节
3. 输出：决议时间 → 历史影响规律 → 关联资产 → 风险提示

## 输出规范

### 查询型输出
用表格，必须包含：日期、时间、国家、事件、重要性、前值/预期/实际（如有）。

### 日历型输出
生成 HTML 文件，必须：浅色背景、月历+列表双视图、事件按重要性色块标注、含前值/预期/实际三值、默认显示今天。

### 分析型输出
结构：事件描述 → 重要性判断 → 关联资产 → 历史影响参考 → 风险提示。

## 辅助脚本

脚本位于 `scripts/` 目录，按需调用（纯文本提示词为主，脚本为辅）：

| 脚本 | 用途 | 用法示例 |
|------|------|---------|
| `query_events.py` | 统一查询入口（自动 fallback） | `--month 2026-08 --importance high` |
| `fetch_wscn.py` | 直调华尔街见闻 API | `--month 2026-07 --format table` |
| `prefill_month.py` | 按规律预排 | `--month 2026-08` |
| `generate_calendar.py` | 生成 HTML 日历 | `--month 2026-08 --output 日历.html` |

脚本依赖 Python 3，仅用标准库，无需额外安装包。

### 可选依赖

- **agent-browser**：当需要从财联社投资日历（`cls.cn/investkalendar`）抓取题材/展会事件作为补充数据源时使用。华尔街见闻 API（主源）已覆盖绝大部分宏观数据，agent-browser 仅用于补充财联社独有的行业展会、公司事件等。详见 `references/data-sources.md`。

## 参考文件

需要时按需读取（渐进式加载）：

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `references/data-sources.md` | API 调用方法、字段说明 | 需要调 API 时 |
| `references/event-taxonomy.md` | 9大类事件完整定义 | 需要分类判断时 |
| `references/recurrence-rules.md` | 各指标月度发布规律 | 需要预排远期时 |
| `references/impact-playbook.md` | 重大事件市场影响手册 | 做影响分析时 |

## 风险提示

所有涉及投资决策的输出，必须在末尾附：

> ⚠️ 本信息仅供投资参考，不构成任何投资建议。市场有风险，投资需谨慎。事件实际影响可能因市场环境、预期差、叠加效应等因素与历史规律不同。

## Playbook 案例

### 案例 1：晨会前快速查今日事件

**输入**："今天有哪些重要财经事件？"

**执行**：调用 `query_events.py --date 2026-07-22 --importance high`，返回当日高影响事件表格。

**输出**：
```
2026-07-22 共 5 个高影响事件
时间    | 国家   | 事件              | 重要性 | 前值    | 预期    | 实际
20:30   | 美国   | 6月成屋销售年化    | ★★★   | 390万   | 395万   | 待发布
02:00   | 美国   | FOMC利率决议      | ★★★★  | 4.50%   | 4.50%   | 待发布
```

### 案例 2：生成月度财经日历

**输入**："帮我做一个8月的财经日历"

**执行**：调用 `generate_calendar.py --month 2026-08`，自动拉取 API + 预排兜底，生成可交互 HTML 日历。

**输出**：HTML 文件，含月历视图（事件色块标注）+ 列表视图 + 事件详情面板。

### 案例 3：重大事件影响分析

**输入**："下周 FOMC 会议对 A 股有什么影响？"

**执行**：查询下次 FOMC 时间 → 读取 `impact-playbook.md` FOMC 章节 → 输出影响分析。

**输出**：
```
下次 FOMC 利率决议：2026-07-29 02:00（北京时间）
影响机制：利率决议 → 美元利率预期 → 美元汇率/美债收益率 → A股北向资金
关联资产：美元、美股、黄金、美债、A股北向资金
历史规律：加息超预期→A股偏空；降息超预期→A股偏多
⚠️ 仅供投资参考，不构成投资建议。
```
