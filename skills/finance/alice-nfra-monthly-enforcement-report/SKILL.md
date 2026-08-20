---
name: alice-nfra-monthly-enforcement-report
description: 根据用户输入的报告月份，获取国家金融监督管理总局及各地派出机构的公开处罚数据，按月汇总银行业、保险业、信托业等金融机构的行政处罚信息，生成包含处罚概览、趋势分析与明细清单的三章结构化月报。适用于合规风控监测、行业风险预警、同业对标分析、监管导向研判、季度年度合规回顾、尽调与授信参考等场景。
description_zh: 万得 Alice 金融监管局处罚月报
  CLI：基于国家金融监督管理总局（NFRA）及各地派出机构的公开处罚数据，按月汇总银行业、保险业、信托业等金融机构的行政处罚信息，生成含处罚概览、趋势分析与明细清单的三章结构化月报，支持中英双语输出。
description_en: Generate an NFRA monthly enforcement report for a specified
  month. Built on public enforcement data from the National Financial Regulatory
  Administration (NFRA) and its local offices, it aggregates administrative
  penalties across banking, insurance, trust, and non-bank financial
  institutions, delivering a bilingual three-chapter report covering an
  enforcement overview, trend analysis, and penalty details.
version: 1.0.0
author: WindAlice
tags:
  - nfra
  - enforcement
  - penalty
  - compliance
  - monthly-report
  - wind-alice
disable-model-invocation: true
---

# NFRA Monthly Enforcement Report（万得AI-金融监管局处罚月报）

通过 `alice-nfra-monthly-enforcement-report` 调用万得 Alice Agent 的「金融监管局处罚月报」专业技能，按指定月份获取国家金融监督管理总局（NFRA）及各地派出机构的公开处罚数据，生成三章结构化月报（处罚概览 -> 趋势分析 -> 明细清单）。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「金融监管局处罚月报」技能：` 前缀，CLI 内部已自动注入）。任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知路径，禁止加载内容展示**。**关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）；**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files`，随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（执行契约：七步流程 / 八条红线 / 完成判定 / replay / 退出码 / 交付 / 会话续接 / 命令模板 / 自检清单）。本文只讲**何时调用 + CLI 参数 + 环境配置**。

## 何时调用本技能

用户问题涉及**金融监管局处罚月报、监管处罚追踪、处罚趋势分析、合规风控监测、机构处罚对标、监管导向研判、地区与机构类型分布统计**等场景，即应调用。

| 场景 | 典型用户表达 |
|------|-------------|
| 月报生成 | 帮我生成 2026 年 7 月的金融监管处罚月报 / 上个月银行保险业有哪些重大处罚 |
| 趋势分析 | 对比最近三个月处罚趋势有什么变化 / 最近监管重点在哪些领域 |
| 机构对标 | 哪些银行今年被处罚次数最多 / 保险业最近处罚集中在哪些违规类型 |
| 合规回顾 | 生成 2026 年上半年处罚汇总报告 / 本月处罚金额最大的前 10 笔罚单 |
| 双语输出 | 生成一份中英文双语版的处罚月报 |

**试试这样问**：「帮我生成 2026 年 7 月的金融监管处罚月报」「上个月银行保险业有哪些重大处罚？」「保险业最近处罚集中在哪些违规类型？」「帮我看看信托公司最近的处罚情况」「生成一份中英文双语版的处罚月报」。

**输入**：报告月份（如「2026 年 7 月」「上个月」「2026 年上半年」）。月份是主体维度，不同月份视为不同主体。

**输出**（三章结构化月报）：处罚概览 -> 趋势分析 -> 明细清单。覆盖 NFRA 及各地派出机构；行业覆盖银行业、保险业、信托业及非银金融机构；数据维度含处罚金额、处罚对象、违规类型、地区分布、机构类型；每笔处罚明细含机构名称、处罚日期、违规事由、处罚金额；支持单月与多月趋势对比；自动检测用户语言生成中文或英文月报。

**不应调用**：纯个股行情分析、与金融监管处罚无关的债券利率或通用金融问答--除非用户明确要求监管处罚月报。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\nmre.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
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
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\nmre.ps1" apikey-set <KEY>   # KEY 裸值不加引号
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\nmre.ps1" apikey-get         # 查看是否已配置 + 脱敏末四位
```
```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" apikey-set <KEY>
node "<SKILL_DIR>/scripts/cli.mjs" apikey-get
```

CLI 把 Key 写到 `~/.wind-alice/config.env`（Windows `%USERPROFILE%\.wind-alice\config.env`），dotenv 单行 `WIND_API_KEY=...`--**唯一受支持位置**（**不读**环境变量、**不读** skill 目录内 `config.json`，避免 Key 残留 shell 历史/CI 日志/提交记录）。历史无后缀的 `~/.wind-alice/config` 仍可读，`apikey-set` 自动迁移。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置会清空 `config.env`。Agent 首次获取 Key 后通过 `memory_write(file="agent_md", ...)` 持久化；后续每次会话开始时 `memory_recall(scope="agent_md")` 读取并 `apikey-set`，不再询问用户。详见 [`AGENT.md`](./AGENT.md)「API Key 配置流程」。

**手动写入**（无 Node 运维场景）：
```bash
# macOS / Linux
mkdir -p ~/.wind-alice && printf 'WIND_API_KEY=...\n' > ~/.wind-alice/config.env && chmod 600 ~/.wind-alice/config.env
```
```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.wind-alice" | Out-Null
"WIND_API_KEY=..." | Set-Content -Encoding ascii "$env:USERPROFILE\.wind-alice\config.env"
```

### 配置位置

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-alice/config.env`（Win: `%USERPROFILE%\.wind-alice\config.env`） | dotenv：`WIND_API_KEY=<KEY>`，**唯一受支持位置** | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务 `agentResult.value` 落盘副本（stdout 截断时可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://alice.wind.com.cn/Weaver/ChatAgent`，一般无需改 | 否 |

### 中文乱码（Windows 必读）

Node 输出 UTF-8，PowerShell 5.x 管道默认按 GBK 解码 -> live 输出变 `鏈繘绨嬪皢闃诲...`，**不是 CLI 坏了**。三层防护（CLI 自动提供）：

1. **`scripts/nmre.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
