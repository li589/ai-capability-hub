---
name: alice-asset-allocation-strategic-baseline-portfolio
description: 用于制定3-5年战略资产配置基准组合，结合风险偏好、投资期限、约束与长期市场数据，输出大类资产权重、区域目标、指数映射和预期风险收益，作为行业轮动、TAA、目标组合构建与再平衡的上游基准。
description_zh: 万得 Alice 资产配置-战略基准组合 CLI：结合风险偏好、投资期限、约束与长期市场数据，制定 3-5 年战略资产配置基准组合，输出大类资产权重、区域目标、指数映射与预期风险收益。
description_en: Use when building a 3-5 year strategic asset allocation baseline from risk profile, horizon, constraints, and long-term market data, producing asset-class weights, regional targets, index mapping, and expected risk/return for downstream sector rotation, TAA, portfolio construction, and rebalancing.
version: 1.0.0
author: WindAlice
tags: [asset-allocation, saa, strategic-asset-allocation, baseline-portfolio, risk-budget, rebalancing, wind-alice]
---
# Asset Allocation - Strategic Baseline Portfolio（资产配置-战略基准组合）

通过 `alice-asset-allocation-strategic-baseline-portfolio` 调用万得 Alice Agent 的「资产配置-战略基准组合 (SAA)」专业技能，制定 3-5 年战略资产配置基准组合（大类资产权重 + 风险预算 + 再平衡区间）。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成自然语言 `--prompt` 传入（**禁**加 `使用「资产配置-战略基准组合」技能：` 前缀）。完成后**只把 stdout 的 `agentResult.value` 原文交给用户**；附件**仅告知路径，禁加载展示**。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（执行契约：七步流程 / 八条红线 / 完成判定 / replay / 退出码 / 交付 / 会话续接 / 命令模板 / 自检清单）。本文只讲**何时调用 + CLI 参数 + 环境配置**。

## 何时调用本技能

用户问题涉及**战略资产配置、战略基准组合、大类资产权重、风险预算、再平衡基准、长期资产配置、投资政策声明（IPS）**等场景，即应调用。

| 场景 | 典型用户表达 |
|------|-------------|
| 长期配置基准 | 为养老金设计 3-5 年战略资产配置方案 / 家族资产股债商品长期配置 |
| 风险偏好维度 | 制定保守型 SAA 基准组合 / 为高净值客户设计成长型配置 |
| 机构/IPS | 机构资金 SAA 框架 / 符合 IPS 的战略资产配置方案 |
| 再平衡/风险预算 | 投资组合再平衡长期基准权重 / 设定股债另类长期目标权重 |
| SAA vs TAA | 战略配置 (SAA) 和战术配置 (TAA) 区别？ |

**不应调用**：纯个股信用、纯债券利率、与战略资产配置无关的通用金融问答--除非用户明确要求。

**输入**：风险偏好（保守型 / 平衡型 / 成长型 / 激进型）+ 投资期限 / 约束。**风险偏好是主体维度**，不同风险偏好的 SAA 方案视为不同主体（如「平衡型 SAA」vs「成长型 SAA」= 不同主体）。

**输出**：长期大类资产目标权重 + 风险预算 + 区域目标 + 指数映射 + 预期风险收益 + 再平衡区间（3-5 年维度，区别于 1-6 个月 TAA；覆盖股/债/商品/另类）。可作为下游 TAA/行业轮动/组合构建/再平衡的基准输入。

**构造 prompt**：把风险偏好与约束拼成一句自然语言。**禁加 `使用「资产配置-战略基准组合」技能：` 前缀**，CLI 已自动注入。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\aasbp.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
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
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\aasbp.ps1" apikey-set <KEY>   # KEY 裸值不加引号
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\aasbp.ps1" apikey-get         # 查看是否已配置 + 脱敏末四位
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

Node 输出 UTF-8，PowerShell 5.x 管道按 GBK 解码 -> live 输出变 `鏈繘绨嬪皢闃诲...`，**不是 CLI 坏了**。三层防护：1. **`aasbp.ps1`** 切 UTF-8 代码页（Windows **优先用它**）；2. **`ALICE_SESSION_LOG=`** 非 TTY 时 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（UTF-8 BOM），**只读 stdout 打印的路径**（`Get-Content -Encoding UTF8`），禁 `view_folder logs/`；3. 落盘 `.md` 带 UTF-8 BOM。**禁止**：因乱码改 prompt 重试、连发多条、`Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱续接、replay、`present_files` 交付顺序、图表 HTML 生成等执行细节见 [`AGENT.md`](./AGENT.md)。
