---
name: alice-fact-check
description: 核查外部渠道金融信息是否准确，粘贴含金融数据、公司声明或行业事件的文字，逐点验证并生成结构化核查报告，标明哪些准确、有出入或查不到。适用于核验数据准确性、fact
  check 新闻/研报/社媒信息等场景。
description_zh: 万得 Alice 事实核验 CLI：粘贴含金融数据、公司声明或行业事件的文字，逐点验证并生成结构化核查报告，标明哪些准确、哪些有出入、哪些查不到。
description_en: Wind Alice Fact Check CLI - verify financial information from
  external sources by pasting a passage with data, corporate claims, or industry
  events; get a structured report with point-by-point fact-checking showing
  what's accurate, off, or unverifiable.
version: 1.0.5
author: WindAlice
tags:
  - fact-check
  - verification
  - financial-data
  - corporate-claims
  - news
  - research
  - wind-alice
disable-model-invocation: true
---

# Fact Check（万得AI-事实核验）

通过 `alice-fact-check` 调用万得 Alice Agent，对从外部渠道获取的金融信息逐点核验，生成结构化核查报告。

> **核心原则**：基础设施交给脚本；Agent 只负责把用户想核验的内容拼成 `--prompt` 传入（可直接粘贴原文）。**默认就执行 Fact Check，无需也不要再指定其它 Skill。** 任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**不要**读给用户看。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（执行契约：七步流程 / 八条红线 / 完成判定 / replay / 退出码 / 交付 / 会话续接 / 命令模板 / 自检清单）。本文只讲**何时调用 + CLI 参数 + 环境配置**。
>
> **调用后**：若 stdout 含 `ALICE_NEEDS_USER_INPUT=1`，或 `agentResult.value` 是在向用户追问要核验的原文等必填项，**必须把追问原文转给用户并停止**；等用户回复后再用**补全后的 prompt** 发起下一次核验（通常须 `--new`）。**禁止**未经用户确认就假设内容完整并立刻第二次调用。

## 何时调用本技能

用户问题只要涉及**粘贴含金融数据、公司声明或行业事件的文字并要求逐点核查其中数据的准确性**，即应调用。

| 场景 | 典型用户表达 |
|------|-------------|
| 新闻/社媒信息核验 | 帮我校验这段话里的数据、核查这条新闻中的数字 |
| 研报公告核查 | 核对这篇研报摘要里的关键数据、验证公司声明中的数据 |
| AI 生成验证 | 帮我 fact check 这段 AI 生成的金融内容 |
| 路演/会议材料复核 | 这份会议纪要里的数据帮我交叉验证 |

**不应调用**：普通金融问答（如"茅台今天涨了多少"）、纯行情查询、需调用其它 Alice 技能的专项分析（信用/基金筛选/债券研判等）。

**构造 prompt**：把研究对象与数据点拼成一句自然语言。**不要加 `使用「事实核验」技能：` 前缀，CLI 内部已自动注入。** 原文越完整、数据点越具体，核验越精准。

**多主体**：可一家或多家写进同一 prompt（建议 ≤ 5 家）。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afc.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
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
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afc.ps1" apikey-set <KEY>   # KEY 裸值不加引号
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afc.ps1" apikey-get         # 查看是否已配置 + 脱敏末四位
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

1. **`scripts/afc.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、附件沙箱外下载、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
