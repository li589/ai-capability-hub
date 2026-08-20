---
name: alice-deep-research
description: 对任何主题进行结构化、多阶段的深度研究。它会先澄清用户的问题，确定研究范围和分析维度，制定并确认研究计划，然后调度多个并行子代理开展调查研究，最后汇总所有研究成果，生成一份全面、详细的最终研究报告。适用于用户提出深度研究、深入分析、全面调查、综合研究等需求，或任何需要广泛覆盖和深入分析的研究任务。
description_zh: 万得 Alice 深度研究
  CLI：对任意主题进行结构化、多阶段深度研究，先澄清问题、界定研究范围与维度并确认研究计划，再调度多个并行子代理调研，最终汇总生成全面、详细的专业研究报告。
description_en: Conducts structured, multi-stage deep research on any topic by
  clarifying the question, scoping the research dimensions, generating a
  confirmed research plan, dispatching parallel subagents for investigation, and
  producing a comprehensive final report. Use when the user asks for deep
  research, in-depth analysis, thorough investigation, comprehensive study, or
  any research task that requires broad coverage and detailed findings.
version: 1.0.1
author: WindAlice
tags:
  - deep-research
  - multi-agent
  - research
  - analysis
  - investigation
  - wind-alice
disable-model-invocation: true
---

# Deep Research（万得AI-深度研究）

通过 `alice-deep-research` 调用万得 Alice Agent 的「深度研究」专业技能，对任意主题进行结构化、多阶段的深度研究（澄清问题 -> 界定范围 -> 确认研究计划 -> 并行子代理调研 -> 汇总报告）。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「深度研究」技能：` 前缀，CLI 内部已自动注入）。任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知路径，禁止加载内容展示**。**关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）；**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files`，随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（执行契约：七步流程 / 八条红线 / 完成判定 / replay / 退出码 / 交付 / 会话续接 / 命令模板 / 自检清单）。本文只讲**何时调用 + CLI 参数 + 环境配置**。

## 何时调用本技能

用户问题涉及**深度研究、深入分析、全面调查、综合研究、多维度主题调研、行业 / 公司调研、市场进入分析、竞争情报、政策影响评估**等需要广泛覆盖和深入分析的场景，即应调用。

| 场景 | 典型用户表达 |
|------|-------------|
| 主题深度研究 | 深度研究固态电池产业化进展 / 全面分析新能源汽车产业链 |
| 多维度调研 | 从技术、经济、竞争、区域等多角度研究一个主题 |
| 行业 / 公司调研 | 行业发展趋势、竞争格局、关键驱动因素 |
| 市场进入 / 竞争情报 | 新市场机会与风险、竞争对手系统性调研 |
| 投资决策支持 | 为重大投资提供详尽背景研究与多维度分析 |

**试试这样问**：「帮我深度研究[固态电池]的商业化进展和主要厂商」「全面分析新能源汽车产业链的投资机会和风险」「深度研究东南亚电商市场的发展前景和主要玩家」「研究全球半导体行业的竞争格局和供应链风险」。

**不应调用**：简单问答、单一数据查询（股价 / 利率 / 财经新闻）、一句话能答完的问题--让上层模型直接回答。本技能**深度优先**，简单问答用它既慢又浪费额度。

**多主体**：可把多个研究主题写进同一 prompt（建议 ≤ 5 个）。

**使用须知（deep-research 专属）**：
- **耗时 15–30 分钟**：结构化多阶段流程（澄清 -> 界定 -> 确认计划 -> 并行调研 -> 汇总），子代理各自检索分析后汇总，远长于普通问答。执行中持续打印 `ALICE_POLL_HEARTBEAT status=working` 心跳，**只要在打印心跳就是正常跑**，耐心等 `ALICE_DEEP_RESEARCH_DONE`，**禁止**因"等太久"就 `--new` / 换 prompt / 连发多条。
- **交互式中间态**：服务端会先澄清问题、界定范围、制定研究计划（可能返回"确认研究计划 / 补充信息"等中间态而非最终报告）。Agent 只需把用户原话作为 `--prompt` 传入并阻塞等待；**中间态原样交给用户**由其回复确认即可，**不要**当成失败而 `--new` 重跑（会丢上下文、重复扣费）。
- **中途别改方向**：研究一旦确认计划开始执行，中途换 prompt 会被当成新任务（原任务仍跑完扣费），还可能命中 exit=76。等当前 DONE 交付后，**在同一会话里追问**（同话题什么都不加，自动续接 contextId）让服务端基于上文深入或补充。
- **终端超时短于 15 分钟**：把超时调到 ≥1800s（30min）只发一条 `--no-wait`；做不到则用 `--detach` + 相同 prompt `--no-wait` 续接（详见 `AGENT.md`「沙箱 / 短超时宿主」）。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```
**macOS / Linux**：
```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```

| 参数 | 说明 |
|------|------|
| `--prompt`, `-p` | 用户提问（自然语言原话）。**必填**；直接把用户原话传入，不要改写措辞 |
| `--no-wait` | **Agent 默认必带**--CLI 内部自旋 `tasks/get` 直到终态。默认 60s 探针、每轮 45min、全程 90min；到轮上限 CLI 自动续轮；Agent 禁止外层 `Start-Sleep` 或连发多条 |
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
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" apikey-set <KEY>   # KEY 裸值不加引号
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" apikey-get         # 查看是否已配置 + 脱敏末四位
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

1. **`scripts/adr.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
