---
name: alice-futures-research-opinion
description: 聚合国内商品期货机构研报多空观点，计算 Wind
  情绪评分，输出含评分、多空中性分布、机构观点摘要与情绪走势的结构化报告。仅支持国内商品期货。适用于查询品种机构多空看法、Wind 评分、研报观点统计等场景。
description_zh: 万得 Alice 期货研报观点 CLI：聚合国内商品期货机构研报多空观点，计算 Wind 情绪评分，输出含观点分布、研报摘要与情绪走势的结构化报告。
description_en: Wind Alice Futures Research Opinion CLI - aggregates research
  opinions on domestic commodity futures across major futures institutions,
  summarizes bullish, bearish, and neutral views by contract or commodity, and
  extracts the key investment logic behind each report. Enter a futures product
  and date to get a research-opinion report, institutional view distribution,
  Wind sentiment score, report summaries, and trend charts.
version: 1.0.5
author: WindAlice
tags:
  - futures
  - commodity
  - research-opinion
  - sentiment
  - wind-score
  - wind-alice
disable-model-invocation: true
---

# Futures Research Opinion（万得AI-期货研报观点）

通过 `alice-futures-research-opinion` 调用万得 Alice Agent，聚合国内商品期货机构研报观点，计算 Wind 情绪评分，生成观点统计图表与结构化研报摘要。

> **核心原则**：基础设施交给脚本；Agent 只负责把用户的期货品种研究问题拼成一句自然语言 prompt 传入。**默认就执行 Futures Research Opinion，无需也不要再指定其它 Skill。** 任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件**不要**读给用户看。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（执行契约：七步流程 / 八条红线 / 完成判定 / replay / 退出码 / 交付 / 会话续接 / 命令模板 / 自检清单）。本文只讲**何时调用 + CLI 参数 + 环境配置**。

## 何时调用本技能

用户问题只要涉及**国内商品期货的机构多空观点、Wind 情绪评分、研报观点统计、机构情绪走势**，即应调用。

| 场景 | 典型用户表达 |
|------|-------------|
| 机构观点 | 铜最近机构怎么看、某品种机构偏多还是偏空 |
| Wind 评分 | 沪铜 Wind 评分多少、铁矿石情绪评分 |
| 研报观点统计 | 纯碱研报观点统计、某品种多空分布 |
| 情绪走势 | 原油近期机构情绪走势、情绪变化趋势 |
| 品种对比 | 铜和铝的机构观点差异、黑色系整体情绪 |

**不应调用**：纯个股信用分析、纯债券利率研判、纯股票行情、境外品种（布伦特原油、伦铜等）、股指期货。

**品种支持**：仅**国内商品期货**（沪铜、螺纹钢、铁矿石、原油、纯碱、豆粕等）；直接说品种中文名；默认查当日，需特定日期在问题中注明。

**构造 prompt**：把品种与维度拼成一句自然语言。**禁加 `使用「期货研报观点」技能：` 前缀**，CLI 已自动注入。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afro.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```
**macOS / Linux**：
```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```

| 参数 | 说明 |
|------|------|
| `--prompt`, `-p` | 用户提问（自然语言原话）。**必填**；直接把用户原话传入，不要改写措辞 |
| `--no-wait` | **Agent 默认必带**--CLI 内部自旋 `tasks/get` 直到终态。默认 60s 探针、每轮 30min、全程 60min；到轮上限 CLI 自动续轮；Agent 禁止外层 `Start-Sleep` 或连发多条 |
| `-d`, `--download-dir` | 保留兼容；**不影响下载目录**--所有附件统一落当前工作空间（`process.cwd()`）。同名冲突自动加 ` (1)`，**绝不覆盖** |
| `--new` | 用户明确要求**并行新建**时清除本地记录后新建（**须先经用户确认**） |
| `--context-id <id>` | **可选**（显式精确续接）：从上一轮 DONE 行 `contextId=` 原样传回，优先级最高，用于跨工作区/精确指定。同工作区内同话题续接已由默认自动续接覆盖，通常不需要 |
| `--new-session` | 显式强制新建会话上下文。**完全无关新话题/用户明说「换个话题」时加**；同话题追问**不要加**（靠自动续接） |
| `--continue-session` / `--session-scope` | 已废弃（no-op），可不传 |
| `--once` | 配合 `--no-wait` 单次探针；**仅脚本调试**，Agent 禁止外层循环 |
| `--no-strict` | 关闭 strict 模式（默认开启：未输出 DONE 行时 exit=0 改成 6）；Agent 禁止传 |
| `--watch-interval` / `--watch-timeout` / `--watch-absolute-max` | 自旋节奏与上限调优（秒），通常默认即可 |
| `--help`, `-h` | 查看帮助 |

> 会话续接判断（同话题追问什么都不加 / 完全无关新话题加 `--new-session`）、`--new` 与 `--new-session` 的区别、命令拼装铁律见 [`AGENT.md`](./AGENT.md)。

### 子命令（只读/配置类，不消耗额度）

| 子命令 | 用途 |
|--------|------|
| `apikey-set <KEY>` / `apikey-get` / `apikey-clear` | 写入 / 查看（脱敏）/ 清除 `~/.wind-alice/config.env` 中的 API Key |
| `status --prompt <Q>` | 查询本地 tasks.json 中该 prompt 最近一条任务的落盘路径 |

## 环境与配置

**Node.js 18+**（自带 `fetch`）。`node -v` 检查，未达标到 [nodejs.org](https://nodejs.org/) 下载。

**API Key**：浏览器打开 [万得 Alice -> 设置 -> 账户](https://alice.wind.com.cn/settings?tab=account)，在「API Key」栏点「生成」/「复制」（失效或泄漏点「重置」会让旧 Key 立即作废）。

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afro.ps1" apikey-set <KEY>   # KEY 裸值不加引号
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afro.ps1" apikey-get         # 查看是否已配置 + 脱敏末四位
```
```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" apikey-set <KEY>
node "<SKILL_DIR>/scripts/cli.mjs" apikey-get
```

CLI 把 Key 写到 `~/.wind-alice/config.env`（Windows `%USERPROFILE%\.wind-alice\config.env`），dotenv 单行 `WIND_API_KEY=...`--**唯一受支持位置**（**不读**环境变量、**不读** skill 目录内 `config.json`，避免 Key 残留 shell 历史/CI 日志/提交记录）。历史无后缀的 `~/.wind-alice/config` 仍可读，`apikey-set` 自动迁移。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置清空 `config.env`。Agent 首次获取 Key 后 `memory_write(file="agent_md", ...)` 持久化；后续每次会话 `memory_recall(scope="agent_md")` 读取并 `apikey-set`，不再询问用户。详见 [`AGENT.md`](./AGENT.md)。

**手动写入**（无 Node）：`mkdir -p ~/.wind-alice && printf 'WIND_API_KEY=...\n' > ~/.wind-alice/config.env && chmod 600 ~/.wind-alice/config.env`（Win PowerShell 同理写 `config.env`）。

### 配置位置

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-alice/config.env`（Win: `%USERPROFILE%\.wind-alice\config.env`） | dotenv：`WIND_API_KEY=<KEY>`，**唯一受支持位置** | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务 `agentResult.value` 落盘副本（stdout 截断时可读） | 自动 |

### 中文乱码（Windows 必读）

Node 输出 UTF-8，PowerShell 5.x 管道按 GBK 解码 -> live 输出变 `鏈繘绨嬪皢闃诲...`，**不是 CLI 坏了**。三层防护：1. **`afro.ps1`** 切 UTF-8 代码页（Windows **优先用它**）；2. **`ALICE_SESSION_LOG=`** 非 TTY 时 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（UTF-8 BOM），**只读 stdout 打印的路径**（`Get-Content -Encoding UTF8`），禁 `view_folder logs/`；3. 落盘 `.md` 带 UTF-8 BOM。**禁止**：因乱码改 prompt 重试、连发多条、`Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱续接、replay、`present_files` 交付顺序、走势图 HTML 生成等执行细节见 [`AGENT.md`](./AGENT.md)。
