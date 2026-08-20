---
name: alice-ppt-generator
description: 根据主题与结构化内容自动生成专业 PPT 报告，支持标题页、目录、章节页、图文排版与结论总结，适用于汇报、方案说明和项目复盘。
description_zh: 万得 Alice 幻灯片（PPT 生成）CLI：根据主题与结构化内容自动生成专业 PPT
  报告，支持标题页、目录、章节页、图文排版与结论总结，适用于投资与金融汇报、商业与管理汇报、产品与市场展示、培训与教育课件等场景。
description_en: Use this skill for gated PPTX delivery when the user needs a
  finance-grade or business-grade deck with multi-stage confirmation, structured
  quality gates, artifact-driven recovery, or controlled incremental revision.
  Use it for formal PPT generation and delivery workflows, not lightweight
  one-off PPT reading.
version: 1.0.0
author: WindAlice
tags:
  - ppt
  - pptx
  - slides
  - presentation
  - deck
  - report-generation
  - wind-alice
disable-model-invocation: true
---

# 幻灯片 / PPT 生成（万得AI-幻灯片）

通过 `alice-ppt-generator` 调用万得 Alice Agent 的「幻灯片」专业技能，根据主题与结构化内容自动生成专业 PPT 演示文稿（标题页 / 目录 / 章节页 / 图文排版 / 结论总结），输出可直接下载的 `.pptx` 文件。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「幻灯片」技能：` 前缀，CLI 内部已自动注入）。任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知路径，禁止加载内容展示**。**关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）；**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files`，随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（执行契约：七步流程 / 八条红线 / 完成判定 / replay / 退出码 / 交付 / 会话续接 / 命令模板 / 自检清单）。本文只讲**何时调用 + CLI 参数 + 环境配置**。

## 何时调用本技能

用户问题涉及**生成 PPT / 幻灯片 / 演示文稿、做一份 PPT 报告、商业计划书 PPT、公司介绍 PPT、行业研究 PPT、季度 / 年度汇报 PPT、培训课件 PPT** 等场景，即应调用。

| 场景 | 典型用户表达 |
|------|-------------|
| 投资 / 金融汇报 | 帮我做一份新能源汽车行业的投资研究 PPT / 公司分析 / 策略路演 / 晨会材料 |
| 商业 / 管理汇报 | 做一份商业计划书 PPT，面向投资人 / 项目汇报 / 季度年度总结 |
| 产品 / 市场展示 | 产品介绍 PPT / 市场分析 / 客户提案 |
| 培训 / 教育课件 | 内部培训材料 / 专题讲座 / 知识分享 |

**试试这样问**：「帮我做一份新能源汽车行业的投资研究 PPT，12 页，面向机构投资者」「做一份比亚迪公司介绍 PPT，包含业务概览、财务表现和竞争优势」「帮我生成一份 AI 大模型行业趋势报告 PPT，咨询风格」「做一份季度销售汇报 PPT，简洁商务风，包含数据图表」「帮我做一个商业计划书 PPT，10 页左右，面向投资人」。

**输入**：
- **必要**：PPT 主题（如「新能源汽车行业投资研究」「比亚迪公司介绍」）。主题是主体维度，不同主题视为不同主体。
- **可选**：页数（不填则 AI 自动规划）、受众与场景（投决会 / 客户路演 / 内部汇报）、视觉风格（简洁商务风 / 科技感 / 咨询风）、必含章节（如「一定要有风险提示页」）。

**输出**：`.pptx` 文件（标题页 + 目录 + 章节页 + 图文排版 + 结论总结），可在 PowerPoint 或 WPS 中直接打开编辑；支持 A 股、港股、美股等金融数据自动获取与图表生成。

**不应调用**：纯金融问答、纯数据查询、与 PPT 生成无关的通用问答--除非用户明确要求生成 PPT。

**使用须知（PPT 生成专属）**：
- **耗时 15–30 分钟**：内容规划 -> 数据收集 -> 图表设计 -> 排版，远长于普通问答。执行中持续打印 `ALICE_POLL_HEARTBEAT status=working` 心跳，**只要在打印心跳就是正常跑**，耐心等 `ALICE_PPT_GENERATOR_DONE`，**禁止**因"等太久"就 `--new` / 换 prompt / 连发多条。
- **中途别改方向**：PPT 生成一旦开始，中途换 prompt 会被当成新任务（原任务仍跑完扣费），还可能命中 exit=76。等当前 DONE 交付后，**在同一会话里追问**（同话题什么都不加，自动续接 contextId）让服务端基于上文加页 / 调风格 / 换图表。
- **终端超时短于 15 分钟**：把超时调到 ≥1800s（30min）只发一条 `--no-wait`；做不到则用 `--detach` + 相同 prompt `--no-wait` 续接（详见 `AGENT.md`「沙箱 / 短超时宿主」）。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\apg.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
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
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\apg.ps1" apikey-set <KEY>   # KEY 裸值不加引号
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\apg.ps1" apikey-get         # 查看是否已配置 + 脱敏末四位
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

1. **`scripts/apg.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
