---
name: alice-commodity-research-assistant
description: 输入期货品种或 Wind
  Code，生成涵盖价格、基差、基本面、远期曲线、资金、仓单、宏观多维度的商品智能日报或专项分析，提炼核心驱动逻辑并给出结论。适用于商品日报、基本面分析、基差、远期曲线、仓单等场景。
description_zh: 万得 Alice 商品智研助手 CLI：输入期货品种名称或 Wind
  Code，自动生成涵盖价格、基差、基本面、远期曲线、资金、仓单、宏观等多维度的商品智能日报或专项分析，输出含核心驱动逻辑与明确结论的结构化报告。
description_en: Wind Alice Commodity Research Assistant CLI — enter a commodity
  name or Wind Code to auto-generate smart research reports distilling core
  drivers across price, structure, capital flow, and fundamentals, with clear
  conclusions for institutional investors and professional traders.
version: 1.0.3
author: WindAlice
tags:
  - commodity
  - futures
  - basis
  - forward-curve
  - warehouse-receipt
  - capital-flow
  - macro
  - wind-alice
display_name: 商品智研助手
display_name_en: Commodity Research Assistant
visibility: public
disable-model-invocation: true
---

# Commodity Research Assistant（万得AI-商品智研助手）

## 技能介绍

### 官方技能：万得AI-商品智研助手

一站式期货品种研究分析工具。输入一个期货品种名称或代码，自动生成涵盖价格、基差、基本面、远期曲线、资金流向、仓单、宏观等维度的完整日报；也可指定单一维度（如"基差""库存""远期曲线"）输出专项分析。

**适用场景：**

- 快速了解某个期货品种的当日全貌 — 一键生成多维度日报
- 追踪特定维度变化 — 只看价格走势、基差变化、资金动向或仓单情况
- 境内外品种覆盖 — 支持上期所、大商所、郑商所、广期所、中金所、能源中心及 LME、COMEX、NYMEX、CBOT、ICE、SGX、TOCOM、BMD 等境外交易所
- 投研晨会准备 — 快速获取品种核心矛盾与关键跟踪变量
- 产业链基本面梳理 — 供需、库存、利润、成本等关键事实提炼

**试试这样问：**

- 沪铜日报
- CU.SHF daily report
- 铁矿石最近怎么样？
- 帮我分析一下原油的基差
- 黄金的远期曲线如何？
- 豆粕基本面分析
- 螺纹钢沉淀资金和仓单情况
- COMEX黄金 outlook
- 碳酸锂价格走势分析
- 棕榈油日报

**💡 提示：**

- **输入方式灵活** — 支持中文名（如"沪铜""铁矿石""PTA"）、标准品种代码（如 `CU.SHF`、`I.DCE`）、或月合约代码（如 `CU2607.SHF`）
- **默认输出完整日报** — 只说品种名，自动生成含价格、基差、基本面、远期曲线、资金、仓单、宏观的全维度报告
- **也可指定单一维度** — 在品种后加上"基差""库存""远期曲线""沉淀资金""仓单""宏观""现货价格"等，只输出该板块分析
- **境内品种覆盖 7 大板块** — 价格、基差、基本面、远期曲线、沉淀资金、注册仓单、宏观
- **境外品种精简板块** — 价格、基本面、宏观（远期曲线有数据时保留）
- **支持中英文输出** — 中文提问出中文报告；英文提问或使用 `daily report`、`report`、`analysis`、`outlook` 等触发词出英文报告
- **数据驱动，不编造** — 所有分析基于实际数据，无数据的板块自动跳过不展示
- **仅作研究参考** — 不提供买卖方向、目标价位、止损建议或收益承诺

### 输出形式

- **Agent 向用户展示的内容**：CLI stdout 中的 `agentResult.value` 正文（服务端流式返回）
- 自动生成的结构化内容包含：**当日核心驱动逻辑、价格与结构变化、资金或基本面关键事实、明确结论**
- 多维度分析：价格、基差、基本面、远期曲线、沉淀资金、注册仓单、宏观（按品种与数据可用性自动裁剪）
- 部分场景下 CLI 会**静默**把完整报告附件下载到当前工作空间（`process.cwd()`，供用户本地查阅）；**Agent 向用户展示时只用 `agentResult.value`，不要粘贴附件正文**
- 数据受限时在对应模块明确标注

---

## Agent 调用红线（必读）

Agent 调用本技能时，**一律**用下列单条命令（CLI 内部自旋直到拿到结果）。**按操作系统选写法——禁止在 Windows PowerShell 里用 `cd ... && node ...`（`&&` 会 ParserError，命令根本不会执行）。**

**Windows PowerShell（Trae / Cursor 默认 shell，**一律**用方案 A）**：

> `<SKILL_DIR>` = 本 `SKILL.md` 所在目录的绝对路径（例：`C:\Users\<用户名>\.agents\skills`）。

```powershell
# ✅ 方案 A（唯一推荐）：acra.ps1 绝对路径，无需 cd，自带 UTF-8 代码页
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>"
```

```powershell
# ❌ 禁止：PowerShell 5.x 不支持 &&，整条命令解析失败
cd "<SKILL_DIR>" && node scripts/cli.mjs --prompt "..." --no-wait

# ❌ 禁止：裸 node 相对路径（易因 cwd 不对而失败；且无 UTF-8 包装）
Set-Location "<SKILL_DIR>"; node scripts/cli.mjs --prompt "..." --no-wait
```

**macOS / Linux（bash / zsh）**：

```bash
node /path/to/alice-commodity-research-assistant/scripts/cli.mjs --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>"
```

判定与红线（CLI 程序层已强制，但 Agent 仍须能识别这些信号、不被 stdout 文案误导）：

| 信号 | 含义 / Agent 必须怎么做 |
|------|------------------------|
| stdout 含 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE taskId=... promptHash=... reportFile=... reportFullFile=... attachmentFile=...` | **唯一**真正完成信号；**必须先核对 `promptHash=` 与本次 `--prompt` 一致**，再以 stdout 中的 `agentResult.value` 原文交付用户（stdout 被截断时读 `reportFile=` 兜底）；**若有 `reportFullFile=` 必须把绝对路径转告用户；若有 `attachmentFile=` 也必须把绝对路径转告用户** |
| stdout 含 `ALICE_SESSION_LOG=<path>`（Windows 管道场景） | live 中文可能乱码；**只读 stdout 打印的该 path**（含完整 promptHash）；禁止 `view_folder logs/`；读前核对 `ALICE_SESSION_LOG_BOUNDARY promptHash=` 与 `PROMPT_HASH=` 一致 |
| stdout 含 `ALICE_POLL_HEARTBEAT status=working` | 轮询中心跳 | **仍未完成**；即使其它 session.log 里有 DONE 行也无效 |
| 同一 taskId 多进程同时 completed | CLI 对附件 URL **跨进程加锁 + tasks.json 去重**；只下载 1 份，后续进程复用 `reportFullFile=`；**禁止**因此读 `download/` 附件内容展示给用户 |
| 退出码 `0` 但没有 DONE 行 | **视为未完成**；不要凭印象编造报告（strict 模式默认会改成 `6`） |
| 退出码 `4` / `6` | 进程未输出 DONE（触顶 / 沙箱被杀）；用**相同 prompt** 再发**一次** `--no-wait` 续接，禁止连发多条、禁止 `--new` |
| 退出码 `77`（`status` 误读风险） | 本地无此 prompt 记录，但存在相似 completed；**禁止**扫 `tasks.json` / `download/` 猜报告，须阻塞 `--no-wait` 等 DONE |
| 退出码 `76`（主调用相似度命中） | 10min 内已有**同主体**相似 prompt 任务（含措辞差异）；CLI 通常已**自动续接/重放**；若仍 exit=76 表示跨进程主体锁命中，用**原 prompt** `--no-wait` 续接，**禁止换措辞** |
| 退出码 `75`（并发上限 / 服务繁忙 / 积分不足） | 立即停止，**按原因分流话术**（见 §10）：积分不足 → 充值；并发上限 → 等已有任务执行完；服务繁忙 → 稍后重试；禁止换 prompt / `--new` 绕过 |
| 退出码 `78`（环境受限，无法保存任务状态） | 当前环境无法保存任务状态（未开启完全访问权限）；**未向服务端发请求**；告知用户「当前环境无法运行 商品智研助手，请在工具中开启完全访问权限后重试」；禁止换 prompt / `--new` / 反复重试 |
| stdout 含 `ALICE_NO_SERVER_CALL=1 reason=replay_completed` | 主调用 `--no-wait` 复用了本地已有的 completed 结果，**未向服务端发请求**；**这不是新建分析**。按三档规则处理：**主体明显不同**（跨行业/跨板块）→ 静默 `--new` 重跑，不打扰用户；**主体一致或拿不准** → 询问用户「该问题已有最近的分析结果，你想怎么处理？」，由用户在「查看已有结果 / 重新分析 / 取消」三选一。**禁止**在主体明显不同时仍停下来问用户 |

**五大红线（违反任一条都会导致重复消耗积分 / 编造结果 / 向用户交付错误数据）**：

1. **阻塞等待 CLI 进程结束**——禁止 `check_command_status` / `Start-Sleep` 替代。
2. **不要换 prompt 重试**——`"分析X"` 与 `"分析X，关注Y"` 会被识别为相似任务直接 exit=76。
3. **没有 DONE 行 = 未完成**——不要把 `STATUS=COMPLETED` 文案、`tasks.json` 中 running 记录或 `download/` 目录 mtime 当成"完成"。
4. **禁止手动翻目录猜报告**——不要用 `view_folder` / `view_files` 扫 `download/`、`results/` 或 `logs/`；若 CLI 未完成，stdout 会出现 `ALICE_ARTIFACT_GUARD` / `ALICE_POLL_HEARTBEAT` / `ALICE_MISLEAD_RISK` / `ORPHAN_DOWNLOAD_CANDIDATE` 提示，**这些只是警告，不是可交付的报告路径**。
5. **交付 agentResult.value + 告知报告路径**——将 CLI stdout 中的 `agentResult.value` **原文**交给用户；**禁止**自行总结、摘录、重写表格或「用自己的话」复述。若 stdout 被沙箱截断，读取 DONE 行 `reportFile=` 落盘正文（跳过 HTML 注释头）。**DONE 含 `reportFullFile=` 时必须告知完整路径**（**保留 CLI 内联的 markdown 链接格式**，如 `[商品智研助手报告.md](file:///<工作空间>/商品智研助手报告.md) (<工作空间>\商品智研助手报告.md)`）——CLI 已把链接内联到 `agentResult.value` 正文中，**原样输出即可**；**禁止**把链接改成行内代码 `` `C:\...\报告.md` ``，行内代码在 Cursor / Trae 等宿主里**不可点击**，用户无法直接打开文件。**DONE 含 `attachmentFile=` 时也必须保留 markdown 链接格式告知完整路径**（如 `[财务模型.xlsx](file:///<工作空间>/财务模型.xlsx) (<工作空间>\财务模型.xlsx)`）。**禁止加载 `reportFullFile=` / `attachmentFile=` 文件内容展示给用户**——`agentResult.value` 已是面向用户的核心分析摘要，完整报告和数据附件供用户本地查阅，不需要 Agent 读取并展示。 **交付 = Agent 亲自打字复述正文**（不折叠），不能只跑完 CLI 让 stdout 显示。**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files` 呈现报告文件为可点击卡片（CLI 已把附件下载到工作空间 `process.cwd()`，路径必在工作空间内，无需传 `-d`）；随后在另一条纯文本消息里输出 `agentResult.value`（本条禁任何工具调用，否则整条被折叠）**。

完整步骤、异常处理、典型现场复盘见下方 [Agent 调用流程](#agent-调用流程) 与 [常见问题](#常见问题)。

---

## 环境要求

### 1. Node.js 18+

CLI 基于 Node.js（18+ 自带 `fetch`）。`node -v` 检查，未达标到 [nodejs.org](https://nodejs.org/) 下载。

### 2. 获取并配置 `WIND_API_KEY`

**获取**：浏览器打开 [万得 Alice → 设置 → 账户](https://alice.wind.com.cn/settings?tab=account)，在「API Key」一栏点「生成」/「复制」（失效或泄漏点「重置」会让旧 Key 立即作废）。

**写入（推荐用 CLI 子命令）**：

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" apikey-set <KEY>
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" apikey-get
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" apikey-clear
```

```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" apikey-set <KEY>    # 写入（KEY 裸值，不加引号）
node "<SKILL_DIR>/scripts/cli.mjs" apikey-get          # 查看是否已配置 + 脱敏末四位
node "<SKILL_DIR>/scripts/cli.mjs" apikey-clear        # 清除
```

CLI 把 Key 写到 `~/.wind-alice/config.env`（Windows `%USERPROFILE%\.wind-alice\config.env`），dotenv 格式单行 `WIND_API_KEY=...`——**这是唯一受支持的位置**。历史无后缀的 `~/.wind-alice/config` 仍可读取，`apikey-set` 会自动迁移。

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

> 安全：CLI **不读**环境变量，也**不读** skill 目录内的 `config.json`——避免 Key 残留在 shell 历史 / CI 日志 / 提交记录。`apikey-set` / `apikey-get` stdout 仅回显脱敏 Key；macOS/Linux 会自动把文件权限收到 `600`。

### 3. API Key 持久化配置（跨会话，Agent 必看）

**背景**：远程沙箱每次会话都会重置，`/root/.wind-alice/config.env` 会被清空。若不持久化，用户每次新会话都要重新提供 Key。

**解决方案**：Wind Alice API Key 由用户首次提供后，Agent **必须**将其保存到 `agent_md`（跨会话记忆文件）。后续每次使用本技能时，Agent 从 `agent_md` 读取 Key 并执行 `apikey-set`，不再询问用户。

**流程**：

1. `memory_recall(action="load", scope="agent_md")` 检查是否已保存 Wind Alice API Key；
2. **有 Key** → 执行 `apikey-set <KEY>` → 继续后续步骤（**静默执行，不对用户提及**）；
3. **无 Key** → 向用户说「使用商品智研助手需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」→ 用户回复后 → 执行 `apikey-set <KEY>` → `memory_write(file="agent_md", content="增加/更新以下记忆：Wind Alice API Key = <KEY>")` → 继续后续步骤。

**红线**：

- **禁止**硬编码 Key 到 Skill 文件；
- **禁止**每次都让用户重新提供 Key（那是 `agent_md` 持久化没生效，应检查记忆调用是否正确）；
- **禁止**在已有 Key 的情况下再问用户提供 Key；
- `apikey-set` 执行后**无需额外验证**——后续主调用若 Key 真正缺失，CLI 会以退出码 `2` + stderr `KEY_MISSING` 明确报错，届时按红线 8 处理。

**用户体验**：

| 场景 | 发生了什么 |
|------|-----------|
| 首次使用 | Agent：「使用商品智研助手需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」→ 用户回复 → Key 保存到 `agent_md` → 自动配置 → 开始分析 |
| 后续使用 | Agent 静默从 `agent_md` 读 Key → `apikey-set` → 直接开始分析，用户无需再操作 |

---

## CLI 调用说明

> **Windows Agent 一律用方案 A**：`acra.ps1` 写绝对路径，**无需 `cd`**。macOS / Linux 用 `node "<SKILL_DIR>/scripts/cli.mjs"`（绝对路径，无需 `cd`）。

### Windows PowerShell 语法（Agent 必读）

Trae / Cursor 在 Windows 上默认使用 **PowerShell 5.x**，**不支持 `&&`**。Agent **只能**用方案 A：

```powershell
# ✅ 方案 A（唯一写法）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "沪铜日报？铁矿石有没有短线机会？" --no-wait -d "<WORKSPACE_DIR>"
```

```powershell
# ❌ 禁止
cd "<SKILL_DIR>" && node scripts/cli.mjs --prompt "..."
Set-Location "<SKILL_DIR>"; node scripts/cli.mjs --prompt "..."
```

其他注意：

- `<SKILL_DIR>` 替换为本技能目录绝对路径；路径含空格时必须加双引号。
- **禁止**在命令末尾拼接 `undefined` 等无效 token（部分 Agent 工具 bug）。
- bash 的 `&&` 仅适用于 macOS / Linux，**不要**在 Windows PowerShell 里照搬。

### 中文乱码（Windows 必读）

**根因**：Node 输出 UTF-8 字节，Trae / PowerShell 5.x 管道捕获时默认按 **GBK** 解码 → live 输出变成 `鏈繘绋嬪皢闃诲...`，**不是 CLI 坏了**。

**三层防护（由 CLI 自动提供）**：

1. **`scripts/acra.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下，CLI 会把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（**完整 64 位** promptHash，UTF-8 BOM）。**只能读 stdout 打印的那条路径**，禁止 `view_folder logs/` 扫描：

   ```powershell
   # ✅ 从本次 CLI stdout 复制 ALICE_SESSION_LOG= 的完整路径
   Get-Content -Path "$env:USERPROFILE\.wind-alice\logs\<promptHash>.session.log" -Encoding UTF8 -Tail 200 -Wait

   # ❌ 禁止：按 mtime 挑「最新」或只认 12 位前缀——不同 prompt（同公司）会落在不同文件
   ```
3. **落盘 `.md`**（`results/`、工作空间、`--detach` 日志）均带 **UTF-8 BOM**，`Get-Content` 即使不写 `-Encoding UTF8` 通常也能正确显示。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

### 查看 `--detach` 日志（避免中文乱码）

`~/.wind-alice/logs/<hash>.log` 由 CLI 以 **UTF-8** 写入。PowerShell 5.x 的 `Get-Content` **默认按 GBK 解码**，会把 UTF-8 中文显示成 `鏈繘绋嬪皢闃诲...` 这类乱码——**不是日志坏了，是读法错了**。

```powershell
# ✅ 正确：显式指定 UTF-8
Get-Content -Path "$env:USERPROFILE\.wind-alice\logs\969e4c647aae.log" -Encoding UTF8 -Tail 50 -Wait

# ❌ 错误：省略 -Encoding UTF8，中文 Windows 上几乎必乱码
Get-Content -Path "...\969e4c647aae.log" -Tail 50 -Wait
```

自新版 CLI 起，`--detach` 创建的日志文件会写入 **UTF-8 BOM**，部分环境下即使不写 `-Encoding UTF8` 也能正常显示；**仍建议 Agent 始终带 `-Encoding UTF8`**。

### 命令行调用

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```

```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```

### 参数

| 参数 | 说明 |
|------|------|
| `--prompt`, `-p` | 用户提问（自然语言原话）。**必填**；直接把用户原话作为 prompt 传入，不要改写措辞 |
| `--no-wait` | **Agent 默认必带**——CLI 内部自旋 `tasks/get` 直到终态。默认 60s 一次探针、每轮 30min、全程 60min；到轮上限 **CLI 自动续轮**；Agent 禁止外层 `Start-Sleep` 或连发多条 |
| `-d`, `--download-dir` | 保留兼容；**不影响下载目录**——所有附件统一落当前工作空间（`process.cwd()`）。同名冲突自动加 ` (1)` 后缀，**绝不覆盖** |
| `--new` | 用户明确要求**并行新建**时清除本地记录后新建（**须先经用户确认**） |
| `--context-id <id>` | **可选**（显式精确续接）：从上一轮 DONE 行的 `contextId=` 取值原样传回，CLI 直接复用该 contextId。优先级最高，用于跨工作区 / 精确指定续接。同工作区内同话题续接**已由默认自动续接覆盖，通常不需要传** |
| `--continue-session` | （兼容，已废弃 no-op）旧式读共享文件复用 contextId。现已被**工作区默认自动续接**取代，可不传 |
| `--new-session` | 显式强制新建会话上下文（不复用上次 `contextId`）。**完全无关的新话题 / 用户明说「换个话题」时加**，避免无关上文污染。同话题追问**不要加**（靠自动续接） |
| `--session-scope <ID>` | （兼容，已废弃 no-op）旧式宿主隔离标识。工作区隔离（`process.cwd()`）已取代它，可不传；也可用环境变量 `WIND_ALICE_SESSION_SCOPE` 统一设置 |
| `--once` | 配合 `--no-wait`，单次探针；**仅脚本调试**，Agent 禁止外层循环 |
| `--no-strict` | 关闭 strict 模式（默认开启：未输出 DONE 行时 exit=0 改成 6）；Agent 禁止传 |
| `--watch-interval` / `--watch-timeout` / `--watch-absolute-max` | 自旋节奏与上限调优（秒），通常默认即可 |
| `--help`, `-h` | 查看帮助 |

> 已废弃：`--watch` / `-w`（`--no-wait` 默认即内部自旋）。

### 调用示例

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" -p "沪铜日报？铁矿石有没有短线机会？" --no-wait -d "<WORKSPACE_DIR>"
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" -p "螺纹钢期货近期走势如何？库存压力大不大？" --no-wait -d "<WORKSPACE_DIR>"
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" -p "原油远期曲线如何？库存怎么变化？" --no-wait -d "D:\reports\commodity"
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" -p "重新分析沪铜走势" --no-wait --new   # 仅用户说"重新跑"才加
```

```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" -p "沪铜日报？铁矿石有没有短线机会？" --no-wait -d "<WORKSPACE_DIR>"
node "<SKILL_DIR>/scripts/cli.mjs" -p "螺纹钢期货近期走势如何？库存压力大不大？" --no-wait -d "<WORKSPACE_DIR>"
node "<SKILL_DIR>/scripts/cli.mjs" -p "原油远期曲线如何？库存怎么变化？" --no-wait -d "/reports/commodity"
node "<SKILL_DIR>/scripts/cli.mjs" -p "重新分析沪铜走势" --no-wait --new
```

附件用 `WIND_API_KEY` 自动鉴权下载到当前工作空间（`process.cwd()`，CLI 在 DONE 行给出 `reportFullFile=` 路径仅供落盘核对）；**Agent 交付用户时只用 `agentResult.value`，不要展示下载附件内容**。

### 多轮会话上下文（工作区默认自动续接，防串号）

商品智研助手支持多轮对话——同一话题下的连续追问，服务端可继承前一轮的分析上下文。CLI **默认在工作区内自动复用**上次 `contextId`（30 分钟空闲窗口内），**无需手动传 `--context-id`**：

- **默认自动续接**：会话状态写在 `<工作区>/.wind-alice/current-session.json`（工作区 = `process.cwd()`）。下一轮调用默认读它、在 30 分钟窗口内复用其 `contextId`。**同一工作区 = 同一会话文件**，不同工作区 / 不同宿主各自独立文件，**物理上不串号**。`taskId` 仍每次新生成（一条 prompt = 一个新任务）。
- **同话题追问**：什么都不加，自动续接。CLI 打印 `[CLI] 会话续接：复用 contextId = ...（工作区自动续接）`。
- **切到完全无关的新话题 / 用户明说「换个话题」**：加 `--new-session` 强制新会话，避免无关上文污染。
- **`--context-id <id>`（可选）**：显式精确续接，优先级最高，用于跨工作区 / 指定特定 contextId；同工作区内同话题续接通常不需要。
- **与 `--new` 的区别**：
  - `--new` = 清除本地任务记录、同一 prompt 重新分析（决定 **taskId** 是否新建）；
  - `--new-session` / 自动续接 = 决定 **contextId** 是否复用（多轮上下文）；
  - 二者正交，可组合。

**为什么不再需要 `--continue-session` / `--session-scope`**：旧版 CLI 默认不复用 contextId，必须由 Agent 从上一轮 DONE 行抓 `contextId=` 手动传 `--context-id` 接力，一旦忘了就断会话；而读共享文件的 `--continue-session` 又会按宿主切分导致同宿主多会话串号。现改为**工作区内默认自动续接**：会话文件落 `process.cwd()/.wind-alice/`，按工作区隔离防串号，Agent 无需手动接力。`--continue-session` / `--session-scope` 仍兼容旧脚本（no-op），但已废弃。

详见 [`AGENT.md` 的「会话续接判断」专节](./AGENT.md#会话续接判断agent-自动执行无需用户显式说)。

### 子命令

只读 / 配置类，不消耗服务端额度：

| 子命令 | 用途 |
|--------|------|
| `apikey-set <KEY>` / `apikey-get` / `apikey-clear` | 写入 / 查看（脱敏）/ 清除 `~/.wind-alice/config.env` 中的 API Key |
| `status --prompt <Q>` | 查询本地 tasks.json 中该 prompt 最近一条任务的落盘路径 |

---

## Agent 调用流程

> 上方「调用红线」已给出退出码识别与禁止动作；本节是分步操作流程。**唯一推荐命令永远是 `--no-wait`，CLI 内部自旋直到完成。**
>
> 注：旧版「主调用前 `check-conflict` 预检」已移除--主调用 `--no-wait` 已内置去重（同 prompt running 自动续接、本地 completed 自动重放 `ALICE_NO_SERVER_CALL=1`、同主体相似 prompt 命中 exit=76），无需额外预检命令，也省掉一次权限确认。replay 仍须在交付前按步骤 7.5 询问用户。

### 0. API Key 配置（跨会话持久化，每次会话开始时必做）

**背景**：远程沙箱每次会话都会重置，`/root/.wind-alice/config.env` 会被清空。通过 `agent_md` 跨会话记忆持久化 API Key，避免用户每次重新提供。

1. 调用 `memory_recall(action="load", scope="agent_md")` 检查是否已保存 Wind Alice API Key；
2. **若已保存**：提取 Key，执行 `powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" apikey-set <KEY>`（macOS/Linux 改用 `node "<SKILL_DIR>/scripts/cli.mjs" apikey-set <KEY>`），**静默完成，不对用户提及**；
3. **若未保存**：向用户说「使用商品智研助手需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」→ 用户回复后 → 执行 `apikey-set <KEY>` → 调用 `memory_write(file="agent_md", content="增加/更新以下记忆：Wind Alice API Key = <KEY>")` 持久化 → 继续。

**禁止**在已有 Key 的情况下再问用户提供 Key；**禁止**硬编码 Key 到 Skill 文件；**禁止**每次都让用户重新提供 Key。`apikey-set` 执行后无需额外验证——后续主调用若 Key 真正缺失，CLI 会以退出码 `2` + stderr `KEY_MISSING` 明确报错，届时按红线 8 处理。

### 1. 识别意图

用户问题只要涉及**商品期货走势、基差结构、库存与供需、远期曲线、宏观驱动、产业链研究**，即应调用本技能。

| 场景 | 典型用户表达 |
|------|-------------|
| 走势研判 | 沪铜日报、螺纹钢走势、原油价格展望 |
| 基差结构 | 基差是升水还是贴水、月差结构、跨期套利 |
| 库存与供需 | 库存压力大不大、供给端扰动、需求季节性 |
| 远期曲线 | 远期曲线形态、contango 还是 backwardation |
| 宏观驱动 | 美元指数影响、通胀预期、地产政策对黑色系 |
| 多视角切换 | 交易视角（1-2 周）、策略视角（1-6 月）、配置视角（6 月-2 年） |

不应调用本技能的场景：纯个股信用分析、纯股票行情、基金筛选、与商品期货无关的通用写作等；除非用户明确要求商品智研助手。

### 2. 构造 prompt

把研究对象和关注维度拼成一句自然语言。**不要加 `使用「商品智研助手」技能：` 前缀，CLI 内部已自动注入。**

### 3. 解析下载目录意图

扫描用户对话中是否说过"下载到 X / 保存到 X / 放到 X 目录"。

- 命中 → 用 `-d "<DIR>"` 传入（多次指定取**最近一次**，含空格的路径必须加双引号）。
- 未命中 → **不要传**该参数；CLI 落到当前工作空间（`process.cwd()`）。

### 4. 告知用户耗时

商品智研助手分析通常 **2-15 分钟**。**调用前必须用一句话告诉用户**这个耗时，并**禁止**中途取消或重复发起。

推荐话术：「好的，我来帮你分析。商品智研助手通常需要 2–15 分钟，请稍等。」

### 5. 执行命令并阻塞等待

对用户说：「已提交分析，正在等待结果，请稍候……」（**禁止**说「CLI 自旋」「进程」「shell」等技术细节）。

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<USER_QUESTION>" --no-wait [-d "<DIR>"]
```

```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait [-d "<DIR>"]
```

- **必须**前台运行，**阻塞等待**该命令返回，读完整 stdout/stderr 与退出码。
- **禁止** fire-and-forget 写法：`Start-Process`（含 `-NoNewWindow`）、`| Out-Null`、`nohup`、后台 job 等。
- **禁止**用 `check_command_status` / `Start-Sleep` / 轮询下载目录 / 轮询 `tasks.json` 替代等待 CLI 进程结束。
- **禁止**在命令末尾拼接 `undefined` 或其它无效参数；只传 SKILL 列出的参数。
- 终端必须配置 **≥1200 秒（20min）** 超时；若做不到（典型于 Trae `run_command` 数十秒就 kill），跳到下方第 7 步「沙箱被 kill 后的续接」即可——`--no-wait` 模式天然为此设计。
- **replay 检测**：进程退出后，若 stdout 含 `ALICE_NO_SERVER_CALL=1` / `reason=replay_completed`，说明复用了本地已有结果而非新建分析——**必须先询问用户**（见下方「replay 重放处理」）。

### 6. 判定完成的唯一标准

**stdout 含 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE taskId=... promptHash=... reportFile=... reportFullFile=... attachmentFile=...` 行** + **退出码 0** + **Agent 已把 `agentResult.value` 全文逐字写进正文回复**。三者同时满足才算完成；**`promptHash=` 必须与本次 `--prompt` 对应**（CLI 启动时会打印 `PROMPT_HASH=` 供核对）。第三条自检：用户**不点开「已完成 / Tool calls」折叠块**就能在你的回复正文里看到完整分析（表格、评级、链接）--否则**视为未完成**，不得结束回合。CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒。

以下情况**一律视为未完成**（即使 exit=0）：

- 只有 `ALICE_COMMODITY_RESEARCH_ASSISTANT_STATUS=COMPLETED` / `[任务已受理]` / `state=submitted`，没有 DONE 行；
- 退出码 `6`（strict 兜底，进程被沙箱杀）或 `76`（重复提交防护）；
- **只说「分析完成」/「详见已完成块」就结束回合，正文里没有 `agentResult.value` 全文**（被宿主折叠，用户看不到）。

### 7. 沙箱被 kill 后的续接（Trae / Codex 等受限终端）

**为何像「卡住」**：商品智研助手要 2–15 分钟，而 Trae/Cursor `run_command` 常只有 60–120s 超时。Agent 若用 `check_command_status` 轮询而非阻塞等待，终端会先杀 CLI（exit `4`/`6`），服务端任务却仍在跑——`results/` 尚未生成，Agent 误判为卡住。此时对用户说：「分析仍在进行中，我继续等待……」，**不要**向用户提及超时、被杀等技术细节。

**首选**：终端超时 **≥1200s**，只发**一条** `--no-wait` 阻塞等到 DONE。

**无法拉长超时**时，用 `--detach` 再续接：

```powershell
powershell ... acra.ps1 --prompt "<USER_QUESTION>" --detach
powershell ... acra.ps1 --prompt "<和首次完全一致的 prompt>" --no-wait -d "<WORKSPACE_DIR>"
```

退出码 `4` 或 `6`（未见到 DONE）——**任务在服务端可能仍在跑**。处理方式：

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<和首次完全一致的 prompt>" --no-wait -d "<WORKSPACE_DIR>"
```

```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<和首次完全一致的 prompt>" --no-wait
```

- 默认每 60s 探针一次；每轮最长 30min，CLI **自动续轮**；全程最长 60min。
- 退出码 `4` 触顶时：再发**一次**相同命令续接；**禁止**连发多条、**禁止** `--new`。
- 探针输出 `state=submitted` 是正常排队，**不要**因为连续几次 submitted 就 `--new` 或换 prompt。
- **禁止** `check_command_status`、`Test-Path results/`、`Get-Content` 扫 logs 猜进度——CLI 未输出 DONE 前这些都不能当交付依据。
- `replay_completed` 时 CLI 会把 `agentResult.value` **重新打印到 stdout**；Agent 应读 stdout 原样交付，**禁止** `view_files` 打开 `results/` 后自行概括。

### 7.5 replay 重放处理（**必须**，当 stdout 含 `ALICE_NO_SERVER_CALL=1`）

主调用 `--no-wait` 返回后，若 stdout 含 `ALICE_NO_SERVER_CALL=1` / `reason=replay_completed`，说明本次**未向服务端发请求**，直接复用了本地已有的 completed 结果——**这不是新建分析**。

Agent **必须在交付前检查**是否触发了 replay。

处理流程（三档判定）：

1. 检查 stdout 是否含 `ALICE_NO_SERVER_CALL=1`；
2. 若**是**：
   - 🔴 **首先检查是否同时带了 `--context-id`**：若本次调用带了 `--context-id` 但 CLI 仍然触发 replay（如 `matchKind=prefix`），说明 CLI 的 replay 机制在续接场景下存在误判——新 prompt 是对上一轮 Alice 追问的**用户回复**（如「使用默认值」），而非重复提问。此时 **replay 的结果一定不是用户想要的**（可能是参数确认页等中间结果），应**直接按「主体明显不同」处理：静默 `--new` 重跑**，不给用户重现参数确认页。
   - 若不涉及 `--context-id`，从 `agentResult.value` 正文中提取商品品种/维度关键词（如「沪铜」「铁矿石」「远期曲线」「基差结构」），与当前会话上下文对比：
     - **主体明显不同**（跨品种/跨视角，如缓存的「沪铜日报」vs 请求的「帮我分析宁德时代信用」；或缓存的「沪铜」vs 请求的「螺纹钢期货情绪」；主体完全不同、无任何字面重叠）→ **静默自动重跑**：用**原 prompt** 加 `--new --no-wait` 重新执行（将消耗积分）。**不向用户提及缓存/主体不匹配/重跑等任何技术细节**——用户不需要知道。重跑后按正常流程（步骤 8）交付。
     - **主体一致或高度相似**（同品种不同写法，如「沪铜」vs「铜期货」；同一商品话题的追问）→ 停下来告知用户：「该问题已有最近的分析结果。」然后统一列出选项：
     - **(A) 查看已有结果** — 直接交付 stdout 的 `agentResult.value` 原文（不扣费）；
     - **(B) 重新做一次分析** — 用**相同 prompt** 加 `--new --no-wait` 重新执行（将消耗积分）；
     - **(C) 取消**。
     - **禁止**未经用户明确选择 (B) 就执行 `--new --no-wait`。
   - **拿不准时**（主体模糊、仅行业关键词无具体公司、缩写无法判定是否与缓存为同一家）→ 按「主体一致」处理，停下来询问用户。
3. 若**否**：正常交付，按步骤 8 处理。

**禁止**在「主体明显不同」时还停下来询问用户——这属于误报，浪费用户时间且体验极差。
**禁止**在触发 replay 时（非明显不同场景）未经用户确认就直接交付旧结果或自行加 `--new` 重跑。
- 🔴 **`--context-id` + replay 冲突**：当 Agent 判断为同一会话追问而传了 `--context-id`，但 CLI 因前缀匹配（`matchKind=prefix`）误触发 replay 时，**不得**向用户展示 replay 的旧结果（旧结果往往是参数确认页等中间态，非用户所求）。Agent 应直接静默 `--new` 重跑，不在用户面前提「缓存」「replay」等词。

### 8. 交付给用户：只要 `agentResult.value`（必看）

> 🔴 **现在立即做**：在**另一条只含文本、不含任何工具调用**的消息里，把 stdout 里的 `agentResult.value` **全文逐字复制**（去掉 `agentResult.value:` 行首前缀）。**本条消息禁止调用任何工具**（present_files / Bash / Read / Edit / Write 等）--含工具调用的整条消息会被 WorkBuddy 折叠、藏住正文。CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒框，见到即执行。
> **禁止**只说「分析完成」就结束回合、**禁止**概括/摘录/改写。表格、评级、链接逐字保留。
> ⚠️ **内存写入陷阱**：WorkBuddy 系统会强制在任务完成后写工作记忆（Edit/Write 工具写 `.workbuddy/memory/`）。**这些操作必须在 CLI DONE 的同一回合里完成**（与解析 stdout 并行），**不得**拖到交付正文的回合——否则交付正文回合含工具调用，整个回合连带正文一起折叠。也**不得与 `present_files` 同回合**--否则 present_files 卡片会被一起折叠隐藏（用户看不到 present_file）；记忆写入必须在主调用回合（curl 下载同回合）完成、先于 present_files。
> **顺序**：① CLI DONE + 并行完成所有内存写入 -> ②（若 `reportFullFile=` 或存在走势图 PNG）在**独立消息**调 `present_files`（**本回合只能有 present_files 一个工具调用（禁 Bash/Read/Edit/Write/文件操作）**--否则卡片被折叠隐藏；这条折叠成卡片可接受；若两者都有则一次 `present_files` 合并传入）-> ③ 在**纯文本消息**里输出 `agentResult.value`（**本条禁任何工具调用**）。两者落在同一条消息会被整条折叠--这是结果被折叠的真正根因。

CLI 完成任务后，Agent **只**向用户交付服务端 `agentResult.value`，**不要**展示下载附件。

| 来源 | 路径 / 信号 | 内容 | Agent 该怎么用 |
|------|-------------|------|----------------|
| **首选** | CLI stdout 中的 `agentResult.value:` 行 | 服务端流式返回的分析正文 | **原样**交给用户（去掉行首 `agentResult.value:` 前缀即可）；CLI 已自动把 `/project/` 附件引用**就地替换**为本地下载路径，并去掉 `### …完整报告` 标题；其余正文禁止改写 |
| **兜底** | `reportFile=` → `~/.wind-alice/results/<taskId>.md` | `agentResult.value` 落盘副本（沙箱 stdout 被截断时用） | DONE 后若 stdout 读不全，读此文件**正文部分**（跳过 `<!-- ... -->` 注释头）原样输出 |
| **路径已内联** | `reportFullFile=` / `REPORT_FULL_FILE=` -> `工作空间/*.md` | CLI 静默下载的完整 Markdown 附件 | 路径已内联在正文中；**禁止加载文件内容展示给用户**（`agentResult.value` 已是面向用户的核心分析摘要） |
| **路径已内联** | `attachmentFile=` -> `工作空间/*.xlsx` 等 | CLI 静默下载的数据附件（Excel 等） | 路径已内联在正文中；**禁止加载文件内容展示给用户** |
| `ALICE_ARTIFACT_GUARD` 等 | stdout 警告 | 防误读提示 | 不是可交付正文；阻塞等到 DONE |

**正确流程（成功场景）**：

1. stdout 出现 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE` 且 `promptHash=` 与本次 `PROMPT_HASH=` 一致；
2. 从 CLI stdout 提取全部 `agentResult.value:` 正文，**原样**呈现给用户（CLI 已自动把 `/project/` 替换为本地下载路径，并去掉 `### …完整报告` 标题）；其余正文禁止改写；
3. 若 stdout 被沙箱截断、读不全，再读 DONE 行 `reportFile=` 兜底文件的正文部分；
4. **附件路径已内联在正文中**，不需在末尾再追加路径提示；
   - **禁止加载文件内容展示给用户**：`agentResult.value` 已是面向用户的核心分析摘要，完整报告附件（`reportFullFile=`）和数据附件（`attachmentFile=`）供用户本地查阅，Agent 不应读取并展示其内容；
   - **禁止**只说「已下载」「可本地查阅」等空话；
   - **注意**：`agentResult.value` 正文仍按原规则从 stdout 提取（或截断时读 `reportFile=` 兜底），不要从 `reportFullFile=` / `attachmentFile=` 附件中读取来替代。

5. **禁止**把 `results/` 称为「完整报告」——`results/` 只是 `agentResult.value` 摘要副本，**不是**服务端 `/project/*.md` 附件。

> 附件路径已由 CLI 内联在 `agentResult.value` 正文中，不需要在末尾再追加。

#### 8.1 用 `present_files` 把报告文件呈现为可点击卡片（DONE 含 `reportFullFile=` 时必做）

服务端返回可下载报告附件时（DONE 行含 `reportFullFile=`），在**独立一条消息**里调用宿主 `present_files` 工具把该文件呈现为可点击卡片--**必须在输出 `agentResult.value` 正文的那条消息之前**单独调用（见下方顺序）。

- **🔴 `present_files` 路径核对**：CLI 已把所有附件**统一下载到当前工作空间**（`process.cwd()`），`reportFullFile=` 路径必在工作空间内，**无需 `cp` 复制**。`present_files` 前：① 从 DONE 行提取 `reportFullFile=` 路径；② 直接用该路径调 `present_files`（在一条独立消息里，不写分析正文，会折叠成卡片）。无 `reportFullFile=` 时跳过本步。
- **顺序**：① 静默跑完主调用 + **同一回合内完成所有内存/日志写入** -> ②（若 `reportFullFile=`）检查路径 + 必要时复制到工作空间 -> ③ 在**独立消息**调 `present_files`（传工作空间内的路径；**本回合只能有 present_files 一个工具调用（禁 Bash/Read/Edit/Write/文件操作）**--否则卡片被折叠隐藏，用户看不到 present_file；这条可折叠成卡片）-> ④ 在**纯文本消息**里输出 `agentResult.value`（**本条禁任何工具调用**，否则整条被折叠）。旧版「正文输出之后再调 present_files」会让两者落在同一条消息、整条被折叠--已废弃。
- **`present_files` ≠ 加载文件内容**：上面的「禁止加载文件内容展示给用户」指不要把附件正文贴进文本回复；`present_files` 只是给文件一个可点击卡片入口，不把内容塞进正文，两者不冲突，该调用照常。
- 若 DONE **没有** `reportFullFile=` 且**没有**走势图 PNG，**不要**调 `present_files`，只交付 `agentResult.value` 正文即可。

#### 8.2 走势图 HTML 报告生成（服务端返回走势图 PNG 时必做）

商品智研助手分析完成后，CLI 会**把服务端返回的走势图 PNG 强制下载到工作空间（`process.cwd()`，即 `<WORKSPACE_DIR>`）**：作为兜底，即使宿主把 `-d` 传成工作空间外的临时目录，走势图也落工作空间供 `generate_chart_html.py` 扫描内嵌；报告附件（`reportFullFile=`）仍落 `-d` 目录。**必须**用 `generate_chart_html.py` 的 `-r` 参数生成**文字+图片混排**的完整 HTML 报告——**绝对禁止**使用纯图片模式（不传 `-r`）。

**文件命名规则**（品种前缀因品种而异）：

- `*_price.png` — 价格走势图
- `*_basis.png` — 基差走势图
- `*_forward_curve.png` — 远期曲线图
- `*_sunk_capital.png` — 沉淀资金走势图
- `*_warehouse_receipt.png` — 注册仓单走势图

**操作流程**：

1. **检查走势图是否存在**：CLI DONE 后，用 `Glob` 工具查找**工作空间 `<WORKSPACE_DIR>`（`process.cwd()`）**（CLI 把走势图 PNG 强制下载到此目录；若 `-d` 与工作空间不同，stdout 会另打印 `走势图 .png 兜底下载到工作空间：<目录>`）中匹配 `*_price.png` / `*_basis.png` / `*_forward_curve.png` / `*_sunk_capital.png` / `*_warehouse_receipt.png` 的 PNG 文件；
2. **若无走势图** → 跳过本步骤，无需生成 HTML；
3. **🔴 保存 agentResult.value 为临时 MD 文件**（必须！）：用 Write 工具将 `agentResult.value` 的完整正文保存到工作空间临时文件（如 `_report_text.md`），UTF-8 编码；
4. **生成文字+图片混排 HTML 报告**：

```powershell
# ⚠️ -r 和 --text-output 都是必传参数！
<python_path> "<SKILL_DIR>\scripts\generate_chart_html.py" -d "<WORKSPACE_DIR>" -r "<临时MD文件>" -o "<WORKSPACE_DIR>\<标题>.html" -t "<标题>" --text-output "<WORKSPACE_DIR>\_report_fixed.md"
```

   - `-r`：报告文本文件路径，脚本按章节自动匹配并内嵌对应走势图（**不传 `-r` 会退回纯图片模式——绝对禁止**）
   - `--text-output`：输出修复后纯文本，脚本将 `![...](/project/xxx.png)` 替换为本地可点击链接，供步骤 9 正文交付使用
   - 图片目录：**工作空间 `<WORKSPACE_DIR>`（`process.cwd()`）**：CLI 兜底把走势图 PNG 强制下载到此，即使 `-d` 指向工作空间外的临时目录也落工作空间（供 `generate_chart_html.py` 扫描）；与下方 `-o` 输出目录是同一个目录，**不要**用 `%USERPROFILE%\Downloads`

5. **present_files 呈现**：在**独立消息**里调 `present_files` 传入生成的 HTML 路径。若步骤 8.1 也有 `reportFullFile=`，合并为一次调用。

**完整示例**（DONE 后执行）：

```bash
# ① 用 Write 工具把 agentResult.value 保存为 _report_text.md（UTF-8）
# ② 生成文字+图片混排 HTML
python "<SKILL_DIR>\scripts\generate_chart_html.py" -d "<WORKSPACE_DIR>" -r "<WORKSPACE_DIR>\_report_text.md" -o "<WORKSPACE_DIR>\NYMEX原油日报.html" -t "NYMEX原油日报" --text-output "<WORKSPACE_DIR>\_report_fixed.md"
# ③ 修复后文本供步骤 9 交付（用 Read 工具读 _report_fixed.md）
```

> **依赖**：`generate_chart_html.py` 需要 Pillow 库（`pip install Pillow`）。若当前 Python 环境未安装，Agent 应在首次使用时自动安装。

### 9. 任务调度 / 续接 / 强制新建

- **默认（`--no-wait`）**：同 prompt 有 **running** → 自动续接；本地 **completed** → **重放落盘结果**（`replay_completed`，不消耗新额度）；无记录 → 新建。
- **默认（阻塞 SSE，无 `--no-wait`）**：同 prompt 有 **running** → 续接；本地 **completed** → 清除后**提交新分析**；无记录 → 新建。
- **`--new`**：用户明确要求并行新建（**须先经用户确认**）。
- **`prompt` 必须和首次提交时完全一致**（trim + 折叠空白后哈希相同），否则可能命中退出码 76（相似 prompt 检测）。

> **防重复扣费**：沙箱 kill 后 Agent **只应再发一条** `--no-wait` 续接。若本地已是 `completed`，CLI 会直接输出 DONE（重放），**不会**再调 `message/stream`。连发多条时，旧版会在第二条误触发新任务——现已修复。

### 10. 退出码 75（并发上限 / 服务繁忙 / 积分不足，立即停止）

stdout 含 `[严重] 并发上限` / `[严重] 服务繁忙` / `[严重] 积分不足`，或退出码 = 75 时，**按原因分流话术**（三者不能混）：

- **积分不足**（stderr 含 `积分不足` / `积分已用完`）：用温和口语告知用户——「很抱歉，这次的分析没能跑起来——您的 Alice 积分已用完。烦请您前往 [万得 Alice → 设置 → 充值](https://alice.wind.com.cn/settings?tab=recharge) 充值。充值完成后，请您把刚才的问题再发一遍，我立刻为您重新分析。」**不要**说「等任务执行完」或「稍后重试」（积分不足等再久也没用）；**不要**说「我直接接着跑 / 不用复述」——需用户充值后重新发送问题；**不提**退出码/prompt/CLI 等技术词。
- **并发上限**（stderr 含 `最大同步执行任务` / `并发` / `请等待其他任务执行完成`）：告知用户「您这边还有别的分析任务正在跑，已经达到同时进行的数量上限，这次没发起。等那些任务完成后，请您把刚才的问题再发一遍，我立刻为您重新分析。」强调「等已有任务执行完」，**不是**「稍等几分钟 / 稍后重试」；需用户在已有任务完成后重新发送问题。
- **服务繁忙**（stderr 含 `服务繁忙` / `系统繁忙` / `请稍后重试`）：告知用户「服务端现在比较忙，暂时没接上这次请求。请您稍等一会儿，把刚才的问题再发一遍，我立刻为您重新分析。」强调「稍后重试」，**不是**「等已有任务执行完」（那是并发上限的话术）；需用户稍后重新发送问题。
- 三种情况都**禁止**换 prompt、`--new`、改 `-d` 这些"绕过"动作；把 `[严重]` 横幅原文口语化转述给用户（不甩技术词）。

---

## 任务幂等性与停止行为

CLI 跨进程在 `~/.wind-alice/tasks.json` 按 **taskId** 记录任务，`~/.wind-alice/results/<taskId>.md` 存每条任务的 `agentResult.value` 落盘副本。基于 prompt 的 `promptHash`（trim + 折叠空白后 SHA-256）做幂等。

- **默认调度（`--no-wait`）**：同 prompt **running** → 续接；**completed** → 重放落盘（不新建）；无记录 → 新建。
- **默认调度（阻塞 SSE）**：同 prompt **running** → 续接；**completed** → 新建；无记录 → 新建。
- **`--new`**：用户明确要求并行新建（**须先经用户确认**）。
- **状态同步**：收到 `agentResult` → completed；服务端提示 / jsonrpc 错误 / 流静默结束 → failed；Ctrl+C → **保持 running**（服务端仍在跑，下次自动续接）。
- **attach 失败自动回退**：attach 模式下 60s 无 SSE / jsonrpc 错误 / 4xx → 自动删旧记录新建任务（单进程内最多 1 次）。
- **自动清理**：running > 6h 强清；completed > 6h 清；failed > 3d 清；总条数 > 200 裁到 100。

---

## 配置位置与环境变量

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-alice/config.env`（Win: `%USERPROFILE%\.wind-alice\config.env`） | dotenv：`WIND_API_KEY=<KEY>`，**唯一受支持位置**（不读环境变量、不读 skill 目录 `config.json`） | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务的 `agentResult.value` 落盘副本（stdout 截断时 Agent 可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://alice.wind.com.cn/Weaver/ChatAgent`，一般无需修改 | 否 |

> 兼容：历史无后缀的 `~/.wind-alice/config` 仍可读取，`apikey-set` 会自动迁移到 `config.env`。

---

## CLI 执行失败处理（核心红线）

**CLI 失败时，立即停止；绝不用 WebSearch 或其它信息源拿"近似的商品智研助手"敷衍用户。**

- `KEY_MISSING`（**仅当** exit=2 且 stderr 含 JSON `"code":"KEY_MISSING"` 时才成立）：按「环境要求」检查 Key 后重试。**禁止**在退出码不是 2、或 stderr 没有 `KEY_MISSING` 字段时，凭"进程被杀""输出不完整""apikey-get 返回 missing"等迹象猜测 Key 缺失——这些与 Key 无关（典型反例：exit=6 是 strict 兜底，Key 配得好好的）。若需核实 Key 状态，用 `apikey-get` 并读其 JSON 的 `status` 字段：`configured` = 正常，`missing` = 确实缺失；**禁止**把 `configured` 读成 `missing` 或凭空下结论。
- exit=75 / `[严重] 并发上限` / `[严重] 服务繁忙` / `[严重] 积分不足`：临时拒绝，**按原因分流**（见 §10）：积分不足 → 充值话术；并发上限 → 等已有任务执行完；服务繁忙 → 稍后重试；均用**相同 prompt**；禁止换 prompt / `--new`，把 `[严重]` 原文口语化转述给用户。
- 服务端用户提示（体验账户 / 数据受限）：原样转述，不要替换为外部信息源。
- macOS Gatekeeper / Windows SmartScreen / 企业安全软件拦截：按系统提示放行后重试。
- 网络 / 服务端 5xx：CLI 内置最多 10 次重连，耐心等。
- 仍失败：向用户展示完整错误，让用户处理；**绝不**回退到其它信息源伪造"看似合理"的商品智研助手。

---

## 常见问题

**Q1：提示「WIND_API_KEY 未配置」 / Key 失效怎么换？ / 每次新会话都要重新配？**

A：从 [万得 Alice → 设置 → 账户](https://alice.wind.com.cn/settings?tab=account) 复制（或点「重置」换新）Key，然后写入：Windows 用 `powershell ... -File "<SKILL_DIR>\scripts\acra.ps1" apikey-set <KEY>`；macOS/Linux 用 `node "<SKILL_DIR>/scripts/cli.mjs" apikey-set <KEY>`。`apikey-get` 验证脱敏末四位；`apikey-clear` 清除。CLI **不读**环境变量与 skill 目录内 `config.json`——只读 `~/.wind-alice/config.env`。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置会清空 `config.env`。Agent 应在首次获取 Key 后通过 `memory_write(file="agent_md", ...)` 持久化；后续每次会话开始时 `memory_recall(scope="agent_md")` 读取并 `apikey-set`，不再询问用户。详见「环境要求 → 3. API Key 持久化配置」与「Agent 调用流程 → 步骤 0」。

**Q2：能否同时分析多个公司？报告附件在哪？怎么改下载目录？**

A：(a) 可以——把多家主体写进同一个 prompt（建议 ≤ 5 家）。(b) 完整报告附件会静默落到当前工作空间（`process.cwd()`），供用户本地查阅；Agent **不要**把附件正文展示给用户，DONE 含 `reportFullFile=` 时**仅告知完整路径**。(c) `-d` 保留兼容但**不影响下载目录**，附件统一落工作空间。**向用户交付时只用 stdout 的 `agentResult.value` 原文**（截断时读 `reportFile=` 兜底），禁止读附件正文展示。

**Q3：PowerShell 报 `&& 不是有效语句分隔符` / 中文乱码？**

A：(a) PowerShell 5.x 不支持 `&&`——Windows **只能用方案 A**（`acra.ps1` 绝对路径，见「调用红线」）。(b) 若 live 仍乱码，读 CLI 输出的 `ALICE_SESSION_LOG=` 路径（`Get-Content -Encoding UTF8`），或直接用 Cursor / VS Code 打开 `.log` / `.md` 文件。

**Q4：用户 Ctrl+C 停掉后再发同样 prompt，会重新跑还是续接？**

A：**自动续接**。`tasks.json` 保留了 `taskId / contextId`，下次同 prompt 启动会通过 `tasks/resubscribe` 接续，**不重复扣额度**。若续接时旧任务已失败，CLI 会自动回退到新建任务（同一进程内最多 1 次）。想真正丢弃，用 `--new`。

**Q5：探针一直显示 `submitted`，可以 `--new` 吗？**

A：**不可以**。`submitted` 是排队态，高峰期几分钟内会转 `working → completed`。继续用**同一条** `--no-wait` 等即可（CLI 内部自旋，默认最长 60 分钟）。**只有**用户明确说"重新跑一遍"或服务端终态 `failed` 时才考虑 `--new`。

**Q6：退出码 75 是什么？**

A：服务端**临时拒绝**新任务（并发上限 / 服务繁忙 / 积分不足）。立即停止，**按原因分流话术**（见 §10）：积分不足 → 充值话术；并发上限 → 等已有任务执行完；服务繁忙 → 稍后重试。**禁止**换 prompt / `--new` / 改下载目录"绕过"——它们都会再占用并发槽。把 stdout 的 `[严重]` 原文口语化转述给用户。

**Q7：CLI exit=0 但 stdout 末尾只有 `[等待中]`，没看到 DONE 行，怎么办？**

A：这表示进程被沙箱 / 终端在 SSE 长连接中途 kill 了——`tasks.json` 永远停在 `running`、`results/<taskId>.md` 永远不出现。**唯一正确做法**：用**完全一致的 prompt** 再发**一条** `--no-wait`，让 CLI 内部自旋问服务端：

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<和首次完全一致的 prompt>" --no-wait -d "<WORKSPACE_DIR>"
```

```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<和首次完全一致的 prompt>" --no-wait
# exit=0 + DONE 行 = 完成；exit=4（60min 触顶）再发一次同命令
```

**禁止**做的事：反复 `Get-Content tasks.json` / `Get-ChildItem results/`（CLI 已死、永远不会更新）、`--new`（占新并发槽）、连发多条 `--no-wait`（Trae「模型循环」熔断）、`--no-wait --once` 外层手工循环（脚本调试专用）。

> 注：strict 模式（默认开启）会把这种「exit=0 但无 DONE」改成退出码 `6`，让 Agent 一眼识别。

**Q8：CLI 还没输出 DONE，但 Downloads/ 里已有同名报告，能直接读吗？**

A：**不能。** `(1)` / `(2)` 后缀只表示同名冲突自动重命名，不代表「本次 prompt 的第 N 次运行」。若 `status -p "<prompt>"` 返回 `ALICE_ARTIFACT_GUARD` 或列出 `SIMILAR_COMPLETED_TASK` / `ORPHAN_DOWNLOAD_CANDIDATE` / `STALE_REPORT_CANDIDATE`，说明本地没有本次 prompt 的登记记录，或存在其它 prompt / 其它会话留下的同名主体文件。**必须**阻塞等待 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE`（含匹配的 `promptHash=`），禁止用 `view_files` 扫目录猜报告。

**Q9：典型误读现场（海思科复盘）—— Agent 做了什么错事？**

A：下列组合几乎必然把**上一次**的报告当成**这一次**的结果（本次现场已复现）：

1. `run_command` 启动 `--no-wait` 后看到 `status: running`，转而用 `check_command_status` 轮询（**禁止**）；
2. `view_folder logs/` 后打开 `3c6ab9cc7835.session.log`——这是**另一句 prompt** 的旧会话（`promptHash=3c6ab9cc...`），不是本次 `帮我做一份海思科的信用分析报告`（`promptHash=f6013601...`）；
3. 旧 log 末尾有 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE`，Agent 未核对 `promptHash=` 与本次 `PROMPT_HASH=`；
4. 再 `view_files` 打开 `download/海思科信用分析报告_20260623.md`——磁盘上仍是旧附件；而 `tasks.json` 里本次 `taskId=019ef374-...` 仍是 **running**。

**正确做法**：阻塞等待 CLI 进程结束；stdout 必须含 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE` 且 `promptHash=` 与本次 `PROMPT_HASH=` **完全一致**，再交付 stdout 中的 `agentResult.value` 原文。若进程被沙箱 kill（exit `4`/`6`），用**完全相同 prompt** 再发**一条** `--no-wait` 续接——**不要**读 logs/、download/、`tasks.json` 猜正文。

**Q10：detach + 连发多条 `--no-wait` 为什么会在 Downloads/ 里出现 `(1)(2)(3)` 多份同名报告？**

A：CLI **绝不覆盖**已有同名文件——`苏美达信用分析报告.md` 已存在时，新下载自动落到 `(1).md`。本次现场 Agent 违规连发了：`--no-wait --watch` ×N → `--detach` → `--no-wait` ×N，多个进程几乎同时看到服务端 `completed`，在 `tasks.json` 写入 `downloadedFiles` 之前各自走 `resolveUniqueTargetPath`，于是 26 秒内连出 `(1)`–`(4)` 四份副本（旧版 `lockBypass` 路径会加剧此问题，已移除）。

**正确做法**：`--detach` 后**只**读 detach 打印的日志路径 + **最多一条** `status`/`--no-wait` 查 DONE；**禁止** detach 运行中再连发 `--no-wait`。本次 detach 的 DONE 行指向 `reportFullFile=...\苏美达信用分析报告 (1).md`，因 15:54:59 已有另一进程先落了无后缀 `.md`。

**Q11：兴业科技复盘——为什么连发 `--no-wait` 会调两次接口？**

A：Agent 对同一用户问题连发了 **8 次以上** `--no-wait`（还用了 `check_command_status`）。其中某次让任务 `019ef391` 在本地变成 **completed**；**下一次** `--no-wait` 按旧规则看到 completed 会 **清除记录并 `message/stream` 新建** `019ef39a`（第二次扣费）。**修复后**：`--no-wait` 遇到本地 **completed** 直接 **replay_completed**，不再误提交新任务。

**Q12：科思科技复盘——换了一句 prompt，为什么又读了旧报告？**

A：本次 Agent 用 `帮我生成科思科技的信用分析报告`，本地已完成的是 `帮我做一份科思科技的信用分析报告`——**promptHash 不同**（`0cba32fc…` vs `fb6fa9cd…`）。Agent 在 `--no-wait` 轮询期间说「先查看该报告，同时重新发起」并 `view_files` 读 `download/`——**明确违规**。CLI 启动时会打印 `SIMILAR_COMPLETED_REPORT` + `ALICE_FORBIDDEN_READ_UNTIL_DONE`；只有本次 `PROMPT_HASH=` 对应 DONE 后的 `agentResult.value` 才可交付。

**Q13：什么时候*不*该用本技能？**

A：用户只是普通金融问答（股价 / 利率 / 财经新闻），对违约概率 / 财务健康度 / 主体资质没有需求时，让上层模型直接回答；不要硬套本技能。

**Q14：泰山石油复盘——多 Agent 同时问同一主体为什么会「串台」？**

A：本次现场三个 Agent 用了**三种措辞**，产生**三个 promptHash**，服务端跑了**三次**分析，`download/` 里堆了多份 `泰山石油_*.md`，评分还不一致（A+ 72.3 vs AA- 78）。

**CLI 已加固（v1.0+）**：

1. **同主体 running 自动续接**：`resolveTaskDispatchPlan` 在本地无 exact 记录时，会按主体名（如「泰山石油」）匹配相似 running，**自动 attach**，不再新建第三条任务。
2. **同主体 completed 自动重放**：`--no-wait` 模式下，30min 内有相似 completed 会 **replay_completed**（`ALICE_NO_SERVER_CALL=1`），不发服务端请求。
3. **running 防护与 replay 统一**：`findSimilarRunning` 与 `findSimilarCompleted` 共用 `comparePromptsForReplay`（含 subject 匹配），「信用报告」vs「信用分析报告」视为同主体。
4. **跨进程主体锁**：除 promptHash 锁外，增加 `computeSubjectKey` 主体锁，防止三进程冷启动同时 submit。

**Agent 仍须遵守**（程序层不能替代 Agent 纪律）：

| Agent 措辞 | 典型错误 | 后果 |
|------------|----------|------|
| `给我一份泰山石油的信用报告` | `--detach` + 手工 `Get-Content` 日志 + 读 `download/` | 可能交付旧 prompt 的报告 |
| `给我做一份泰山石油的信用分析报告` | 连发 8 次 `--no-wait` / `--watch` + 读 `tasks.json` 挑 completed | 误读其它 taskId 的摘要 |
| `给我一份泰山石油的信用分析报告` | 相对规范，但仍可能与上两者并行扣费 | 用户看到三份不同结论 |

**共同违规**（违反任一条即可能串台）：

1. **没用 `acra.ps1` 方案 A**——`cd && node` / `Set-Location; node` 在 PowerShell 5.x 易失败；命令末尾拼 `undefined` 是 Agent 工具 bug。
2. **连发多条 CLI** / `check_command_status` / `--detach` 后轮询——应**只发一条** `--no-wait` 并阻塞等到 DONE。
3. **DONE 之前读 `download/`、`tasks.json`、`results/`**——`泰山石油_信用分析报告.md` 可能绑定**另一个 promptHash**；`ALICE_FORBIDDEN_READ_UNTIL_DONE` 不是报告路径。
4. **换措辞当「重试」**——`信用报告` vs `信用分析报告` 会被判为相似任务；应续接/重放**原 prompt**，不要换句。

**正确做法（单 Agent）**：**一条** `acra.ps1 ... --no-wait` 阻塞等待 → stdout `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE` 且 `promptHash=` 一致 → 交付 `agentResult.value` **原文**，禁止展示 `download/` 附件。

**Q15：永辉超市复盘——为什么 Agent 交付的 PD / 评级与真实报告不一致？**

A：Agent 违规组合：(1) 连发多条 `--no-wait` 且用 `check_command_status` 轮询，未阻塞等到 DONE；(2) 读 `results/` 或 `download/` 附件后**自行概括**成表格——定量指标会被改错。**正确做法**：阻塞等到 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE` → 将 stdout 的 `agentResult.value` **原文**交给用户（截断时读 `reportFile=` 兜底）→ 禁止概括 → DONE 含 `reportFullFile=` 时**仅告知完整路径**（禁止加载文件内容展示），禁止自行概括改写。

**Q16：苏美达复盘——任务明明成功了，为什么 Agent 却说"找不到 API Key"？**

A：这是**凭 stderr 噪声 / 子命令返回脑补出"Key 缺失"结论**的典型误判，本次现场已复现。真实情况：API Key 配得好好的（`config.env` 存在且有效），任务已在服务端成功完成、报告已落盘。Agent 错误链路：

1. `--no-wait` 主调用进程被沙箱 / IDE 终端在 SSE 长连接中途 kill（exit=6 strict 兜底，或 exit=0 无 DONE）；
2. Agent 不识别这是"被杀"，反复 `check_command_status` 说"输出似乎不完整"；
3. 转去跑 `status` / `apikey-get` 子命令想"排查"，却**没读懂返回值**（`apikey-get` 的 JSON `status: configured` 被忽略或误读成 `missing`）；
4. 最终向用户下结论"需要先配置 API Key"，引导用户做根本不必要的配置。

**为什么这是错的**：

- `request.js` 主路径在发请求**前**就会 `getApiKey()`（`request.js:877`），Key 真缺失会立刻 `die("KEY_MISSING")` exit=2，**绝不可能**"已经发了服务端请求再说没 Key"——这在逻辑上自相矛盾。
- strict 兜底输出（`request.js` `installStrictExitHook`）**只**说"未输出 DONE，请用相同 prompt 续接"，**不含**任何 Key 配置文案。
- `apikey-get`（`printApiKeyStatus`）是只读探针，返回 JSON：`status: configured`（正常，含脱敏 key）/ `missing`（缺失）/ `error`（读文件失败）。**必须按 `status` 字段判定**，禁止凭印象。

**正确做法**：

1. 退出码 **不是 2** 且 stderr **不含** `"code":"KEY_MISSING"` → **禁止**声称 Key 缺失；
2. 想核实 Key → 跑 `apikey-get`，**读 JSON 的 `status` 字段**：`configured` = Key 没问题，往别处查；
3. 进程被杀（exit=4/6）→ 任务**可能仍在服务端跑**，用**完全相同 prompt** 再发**一条** `--no-wait` 续接（见 Q7）；
4. 想确认任务真实状态 → 跑 `status --prompt "<原 prompt>"`，它会从本地 `tasks.json` 给出 `completed`/`running`/`failed` 及落盘路径，**不访问服务端**；
5. **禁止**把"输出不完整""进程退出""apikey-get 某行看不懂"等同于"Key 缺失"。

> 一句话：Key 缺失有**唯一的确定信号**（exit=2 + `KEY_MISSING` JSON）；其它一切"看起来不对劲"都**不是** Key 问题，应按对应的退出码 / 信号处理（续接、等 DONE、报真实错误），不要引导用户去配置一个根本没问题的 Key。

## Agent 执行摘要（Skill 注入后**最先读**，再动任何工具）

| 顺序 | 做什么 | 禁止 |
|------|--------|------|
| 0 | 读同目录 **[`AGENT.md`](./AGENT.md)** | 禁止 `search_codebase`、禁止查库猜商品/期货行情 |
| 1 | **一条** `acra.ps1 --prompt "<用户原话>" --no-wait -d "<WORKSPACE_DIR>"` [--context-id <上一轮contextId>] [--new-session] | 禁止裸 `node`、禁止 `cd` 到 skill 目录 |
| 2 | `run_command` / Shell **超时 ≥ 1200 秒**；**阻塞等到命令退出** | 禁止秒退后说「后台 PID / 稍后再问继续查」 |
| 3 | stdout 含 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE` | 无 DONE = 未完成，禁止编造 |
| 4 | **逐字**交付 `agentResult.value`；DONE 含 `reportFullFile=` 时先 `present_files` 再交付正文 | 禁止自行概括、禁止读附件正文 |
| 5 | **若存在走势图 PNG**（`*_price.png` 等）：用 `<SKILL_DIR>/scripts/generate_chart_html.py` 生成 base64 内嵌 HTML → `present_files`（与步骤 4 合并一次调用） | 禁止跳过——用户期望看到内嵌图表的报告 |

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>"
```

> 注：主调用 `--no-wait` 已内置去重/续接/重放，**无需**额外 `check-conflict` 预检。

见到 `ALICE_DELIVER_AS_TEXT=1` = 必须把上方 `agentResult.value` 逐字打成正文。

---

通过 `alice-commodity-research-assistant` 调用万得 Alice Agent 的「商品智研助手」专业技能，系统化输出商品期货智能研报（覆盖走势、基差、库存、供需、宏观驱动等维度）。

> **核心原则**：基础设施交给脚本处理；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「商品智研助手」技能：` 前缀，CLI 内部已自动注入）。任务完成后，**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知完整路径，禁止加载文件内容展示给用户**。 **关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）。**若 DONE 含 `reportFullFile=`，先在独立一条消息里调 `present_files`；随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（一页执行契约，与 IDE 无关，随 skill 包发布）。

## 🔴 最重要规则:结果必须由你复述成正文,否则用户看不到

> **宿主 UI(WorkBuddy 等)折叠规则:你亲自打字输出的文本正文(`type=text`)永远正常显示;任何工具调用的输出(含 Bash 命令的 stdout、read_file 内容、present_files 卡片)在回合结束后会被折叠进「已完成」块,用户必须点开才看得到。**
>
> 因此 CLI 跑完后,服务端返回的 `agentResult.value` 会停留在 Bash 工具 stdout 里被折叠。**你必须亲自把 `agentResult.value` 全文作为你自己的回复文本逐字打出来**(去掉 `agentResult.value:` 行首标记即可),才会作为 `type=text` 正文正常显示、不被折叠。
>
> - **正确**:跑完 CLI -> 回复里写下「分析完成:」+ agentResult.value 全文(逐字,不概括)。
> - **错误(被折叠)**:跑完 CLI 就结束让 stdout 自己显示;或只说「详见已完成块」。
> - **`present_files` 与分析正文必须分两条消息**：`present_files` 单独一条（折叠成卡片可接受）；分析正文必须在**另一条不含任何工具调用**的纯文本消息里。
> - ⚠️ **内存/日志写入陷阱**：WorkBuddy 会在每回合结束时强制写入工作记忆。**这些 Edit/Write 必须在交付 agentResult.value 正文之前完成，不得与正文放在同一回合**。
>
> 自检:交付前问--「我有没有亲自把 agentResult.value 全文打字说出来?」「这个回合有没有任何工具调用?」CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒框,见到即把上面的 `agentResult.value` 逐字复制成正文,禁止只说「分析完成」就结束。

## 🔴 第二重要规则:同会话追问默认自动续接,切话题才用 `--new-session`

> **常见错误**:用户先问「沪铜日报」,你交付后用户问「**那铁矿石呢**」--这是对上文结果的**追问/延伸**,同话题延伸**什么都不用加**,CLI 在工作区内自动续接。
>
> **机制（默认自动续接——防串号）**:CLI **默认在工作区内自动复用**上次 `contextId`（30 分钟空闲窗口内），你**无需**手动传 `--context-id`。会话状态落在 `<工作区>/.wind-alice/current-session.json`（工作区 = `process.cwd()`），按工作区隔离、物理上不串号。只有**切到完全无关的新话题**时才加 `--new-session` 强制新会话。旧的 `--continue-session` / `--session-scope` 已废弃（自动续接 + 工作区隔离已取代它们），可不传。
>
> **判断标准--有话题关联就续接,宁滥勿缺**:本次问题与上一轮技能调用**有任何话题关联**(同一市场/同一主体/追问原因/「XX 是不是因为 YY」「那 XX 呢」)就**什么都不加**(自动续接)。拿不准时**倾向不加 `--new-session`**——续接错代价小,误切新会话代价大(丢上下文/答非所问)。只有完全无关的新主题才加 `--new-session`。
>
> 详见 `AGENT.md`「会话续接判断」专节。

## 何时优先调用本技能

当用户问题涉及**商品期货走势研判、基差结构、库存与供需、远期曲线、宏观驱动、产业链研究**等场景时，应调用本技能。不应在纯个股信用分析、与商品无关的债市利率问题等场景硬套本技能。

---

