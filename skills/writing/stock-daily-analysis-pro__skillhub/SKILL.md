---
name: a-share-daily-analysis
description: 为当前工作区生成每日 A 股筛选报告、5 只候选股、执行价位和手工条件单清单。
---

# A 股每日分析

当用户在这个工作区里提出以下需求时，使用这个 skill：

- 生成每日 A 股分析报告
- 输出当前值得跟踪的 5 只交易候选股
- 给出突破买点、回踩买点、止损位、止盈位
- 重新生成券商可手工录入的条件单清单
- 配置每日定时生成报告

## 工作区事实

- 主工作流脚本: `trade_candidate_pipeline.py`
- 每日报告生成脚本: `generate_daily_report.py`
- 执行计划脚本: `trade_execution_plan.py`
- 手工条件单导出脚本: `manual_order_ticket.py`
- 全市场缓存评分文件: `a_share_scores.csv`
- Python 解释器应使用当前工作区虚拟环境
- Windows 常见路径: `.venv/Scripts/python.exe`
- Linux 服务器常见路径: `.venv/bin/python`

## 工作规则

1. 除非用户明确要求刷新市场数据，否则优先使用 `a_share_scores.csv` 中的缓存评分。
2. 如果实时行情或历史数据获取失败，保持当前的回退执行方案，不要让整个流程直接失败。
3. 除非用户已经配置了邮件、webhook、聊天通道等真实推送方式，否则不要声称已经具备外部推送能力。
4. 如果用户要求在 Windows 上定时生成报告，优先复用现成的 PowerShell 计划任务脚本。
5. 除非用户明确要求修改阈值、因子或筛选标准，否则沿用当前工作区既有的选股逻辑。
6. 如果当前运行环境是 Linux 服务器，不要使用 PowerShell 计划任务脚本；优先使用 OpenClaw cron 或系统 cron。

## 默认工作流程

### 1. 生成完整的每日报告包

在 Windows 上执行：

```powershell
d:/pythonfile/uderestimate/.venv/Scripts/python.exe d:/pythonfile/uderestimate/generate_daily_report.py
```

在 Linux 服务器上执行：

```bash
./.venv/bin/python ./generate_daily_report.py
```

这一步应当刷新以下输出：

- `a_share_agent_top5.csv`
- `a_share_agent_execution_plan.csv`
- `a_share_manual_order_sheet.csv`
- `reports/a_share_daily_report_YYYYMMDD.md`
- `a_share_daily_report_latest.md`

### 2. 只重跑选股和执行价位

在 Windows 上执行：

```powershell
d:/pythonfile/uderestimate/.venv/Scripts/python.exe d:/pythonfile/uderestimate/trade_candidate_pipeline.py
```

在 Linux 服务器上执行：

```bash
./.venv/bin/python ./trade_candidate_pipeline.py
```

### 3. 注册 Windows 工作日定时任务

执行：

```powershell
powershell -ExecutionPolicy Bypass -File d:/pythonfile/uderestimate/register_daily_report_task.ps1
```

如果要自定义时间：

```powershell
powershell -ExecutionPolicy Bypass -File d:/pythonfile/uderestimate/register_daily_report_task.ps1 -RunTime 14:40
```

### 4. Linux 服务器定时运行

如果 OpenClaw 当前运行时支持 cron 工具，优先通过 OpenClaw cron 定时触发这个工作区流程。

如果 OpenClaw 当前运行时没有 cron 工具，则使用系统 cron，例如：

```bash
50 14 * * 1-5 cd /srv/uderestimate && ./.venv/bin/python ./generate_daily_report.py >> /srv/uderestimate/logs/daily_report.log 2>&1
```

## 输出时必须说明的内容

当你完成一次报告生成后，需要明确说明：

- 使用的是缓存评分，还是重新刷新了市场数据
- Markdown 报告写到了哪里
- 执行价位来自实时数据，还是回退模板模式
- 候选股清单、执行计划、手工条件单分别写到了哪里

如果用户要求设置定时任务，还需要补充说明：

- 注册的任务名
- 任务执行时间
- 当前实现是本地生成文件，不等于已经接入外部消息推送

## 如果用户要求 OpenClaw 原生定时

如果当前 OpenClaw 运行时暴露了 cron 工具，优先创建一个 cron 任务来执行这个工作区流程，并返回一段简短结果摘要。

如果当前运行时没有 cron 工具，就回退到现有的 Windows 计划任务脚本，并明确说明当前交付目标仍然是本地报告文件，而不是外部消息通道。

如果当前环境是 Linux 服务器，则回退目标应改为系统 cron，而不是 Windows 计划任务。