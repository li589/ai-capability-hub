# Alice 资产配置-战略基准组合 - 宿主 Agent 执行契约

> **任何宿主 Agent（Cursor / Trae / Codex / 自建等）调用本技能前必须先读完本文。** 产品与参数见 `SKILL.md`；本文规定**怎么跑、怎么判定完成、怎么交付**。`<SKILL_DIR>` = 本文件所在目录绝对路径。

---

## 🔴 最重要规则:结果必须由你复述成正文,否则用户看不到

宿主 UI（WorkBuddy 等）折叠规则：**你亲自打字输出的文本正文（`type=text`）永远正常显示；工具调用输出（含 Bash stdout、present_files 卡片）回合后折叠进「已完成」块，用户须点开才看得到。** CLI 跑完后 `agentResult.value` **停在 stdout 被折叠**。

**必须做**：从 stdout 提取 `agentResult.value:` 后的正文，**亲自作为回复文本逐字打出来**（可去行首前缀）。自检：「我有没有亲自把 agentResult.value 全文打字说出来？」没有就不算交付完。CLI 在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1`，见到即执行。

- **正确**：跑完写「报告如下:」+ agentResult.value 全文（逐字）；**错误（被折叠）**：跑完就结束、只说「详见已完成块」、`Out-File` 重定向。
- **`present_files` 与正文分两条消息**：`present_files` 独立一条；正文在**另一条不含任何工具调用**的纯文本消息--含工具调用的整条被折叠、藏住正文。

## 🔴 第二重要规则:同会话追问默认自动续接,切话题才用 `--new-session`

CLI **默认工作区内自动复用**上次 `contextId`（30 分钟窗口），**无需手动传 `--context-id`**。会话状态落 `<工作区>/.wind-alice/current-session.json`（工作区 = `process.cwd()`），**同一工作区 = 同一会话文件**，不同工作区/宿主各自独立，**不串号**。只有**切完全无关新话题**加 `--new-session`；同话题追问（哪怕换风险偏好/加维度）**什么都不加**。`--context-id` 仍可用但通常不需要；`--continue-session`/`--session-scope` 废弃。拿不准**倾向不加**。

| 情形 | Agent 动作 |
|------|-----------|
| 本工作区首次调用 | 自动开新会话（无需参数） |
| 与上一轮有任何话题关联 | **什么都不加** |
| 完全无关新主题 / 用户明说「换个话题」 | 加 `--new-session` |
| 上一轮返回错误配置主题/风险偏好（replay 命中但主体不匹配） | 加 `--new-session`，用含风险偏好的明确 Prompt 新开 |
| 距上次超 30 分钟 | CLI 自动按新会话处理 |

判定详见上表；拿不准**倾向不加**（同配置主题/风险偏好）。用户明说要「重新分析」时同时加 `--new`（语义正交）。

---

## 七步流程（按顺序，不可跳步）

| 步 | 动作 | 对用户怎么说 |
|----|------|-------------|
| 0 | **API Key 配置**：从 `agent_md` 读 Key，有则 `apikey-set`；无则问用户，存 `agent_md` 后再 `apikey-set` | 有 Key 静默；无 Key：「使用资产配置-战略基准组合需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」 |
| 1 | 拼自然语言 `--prompt`（**禁**加 `使用「资产配置-战略基准组合」技能：` 前缀）；同步判断续接：同话题**什么都不加**；无关新话题加 `--new-session` | （无需说话） |
| 2 | 告知耗时 **2–15 分钟** | 「好的，我来帮你分析。资产配置-战略基准组合通常需要 2–15 分钟，请稍等。」 |
| 3 | **主调用**：**一条** `--no-wait -d "<WORKSPACE_DIR>"`，**阻塞等待**进程结束 | 「已提交分析，正在等待结果，请稍候……」 |
| 4 | 核对完成信号；若 stdout 含 `ALICE_NO_SERVER_CALL=1`（replay），按「replay 三档」处理 | 见 replay 话术 |
| 4.5 | **图表 HTML 生成（SAA 特有）**：CLI 已把图表 PNG 下载到工作空间。用 Glob 查 `saa_correlation_heatmap.png`/`saa_efficient_frontier.png`/`saa_risk_contribution.png`/`saa_weight_pie.png`。若有：① Write 存 `agentResult.value` 为 `_report_text.md`；② 跑 `<python> "<SKILL_DIR>\scripts\generate_chart_html.py" -d "<WORKSPACE_DIR>" -r "<WORKSPACE_DIR>\_report_text.md" -o "<WORKSPACE_DIR>\<标题>.html" -t "<标题>" --text-output "<WORKSPACE_DIR>\_report_fixed.md"`（`-r`/`--text-output` 必传，**禁纯图片模式**）；③ HTML 供步骤 5，`_report_fixed.md` 供步骤 6。无图表跳过。依赖 Pillow | （静默） |
| 5 | **若 DONE 含 `reportFullFile=` 或步骤 4.5 生成了 HTML**：路径已在工作空间（`process.cwd()`），**无需 `cp`**。独立消息调 `present_files`（含报告路径 + 步骤 4.5 HTML）。**禁写正文、禁任何其它工具调用**（尤其 Edit/Write `.workbuddy/memory`） | （静默调用） |
| 6 | 🔴 **立即**：纯文本消息（**禁任何工具调用**）里把 `agentResult.value` **全文逐字复制**（若有 `_report_fixed.md` 则读其交付）。**禁**只说「分析完成」、**禁**概括。CLI 打印 `ALICE_DELIVER_AS_TEXT=1` | 交付报告 |

> ⚠️ **交付方式铁律**：🔴 `present_files` 那条**零其它工具调用**（禁 Edit/Write/Bash/Read）；记忆写入在主调用回合（步骤 4.5 同回合）完成、先于 present_files。顺序：① 主调用+同回合内存写入 -> ②（若 `reportFullFile=`/有 HTML）独立消息调 `present_files`（本回合只能 present_files）-> ③ 纯文本消息输出 `agentResult.value`（禁任何工具调用）。🔴 **每轮独立调 `present_files`**：本轮 DONE 含 `reportFullFile=`/`attachmentFile=` 就必须调，禁因「上一轮已调过」跳过。

### API Key 配置（步骤 0）

沙箱每次会话重置清空 `config.env`，Key 存 `agent_md` 跨会话记忆。1. `memory_recall(scope="agent_md")` 查 Key；2. **有**：`apikey-set <KEY>`（Win: `aasbp.ps1 apikey-set <KEY>`；Mac: `node cli.mjs apikey-set <KEY>`），**静默**；3. **无**：问「使用资产配置-战略基准组合需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」-> `apikey-set` -> `memory_write(file="agent_md", content="...Wind Alice API Key = <KEY>")`。**红线**：**禁**已有 Key 时再问/硬编码 Key/每次让用户重提供；Key 真缺失时 CLI 退出码 `2`+stderr `KEY_MISSING`，按红线 8。

### 话术红线

**禁止**暴露内部细节（CLI、自旋、task_id、进程、shell、exit code）。「已提交分析，正在等待结果，请稍候……」（✅）；「分析任务已在后台启动，CLI 内部自旋」（❌）。replay 主体一致时问「该问题已有最近的分析结果，你想怎么处理？」；主体明显不同**静默重跑**。已有 Key 静默执行。不问用户「想接着刚才话题继续吗」。

### 工具调用 `description` 用中文

`description` 是**权限确认框标题**。步骤 3 填「调用万得 Alice 进行资产配置-战略基准组合」；`status` 填「查询本地任务落盘路径」。禁写 CLI/task_id/exit code。

---

## 命令模板

> ⚠️ **命令拼装铁律（照抄，禁自由发挥）**：逐字照抄，只替换占位符，**禁增删参数、禁重定向输出、禁 cd**。
> 1. **Windows 必须用 `aasbp.ps1`，禁裸 `node scripts/cli.mjs`**（中文乱码 + 沙箱兼容性）。
> 2. **禁 `cd` 到 `<SKILL_DIR>`**。`aasbp.ps1` 绝对路径调用，`process.cwd()` 保持工作区。状态目录**固定 `~/.wind-alice/`**。
> 3. **`-d` 必传，指向当前工作区根**（`process.cwd()`），**禁**指向工作区外或 skill 目录；`-d` 决定**附件落盘位置**（路径含空格加双引号）。
> 4. **禁 `Out-File`/`>` 重定向 stdout**。完成信号在 stdout，Agent 必须直接捕获。

**Windows**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\aasbp.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--context-id <上一轮contextId>] [--new-session]
```
**macOS / Linux**：
```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--context-id <上一轮contextId>] [--new-session]
```

`-d` **必传**指向工作区根；会话参数（`--new`/`--new-session`/`--context-id`）见上方「第二重要规则」与 [`SKILL.md`](./SKILL.md) 参数表。

---

## 八条红线

违反任一条可能导致**重复消耗积分、交付错误数据、编造指标**。

1. **阻塞等到 CLI 进程退出** - 禁 `check_command_status`/`Start-Sleep` 轮询/进程未结束前读 `results/`/`logs/`/`Downloads/` 猜结果。
2. **不要换 prompt 重试** - 续接/重放必须用**与首次完全一致**措辞；换句触发 exit `76`。
3. **没有 DONE 行 = 未完成** - `[任务已受理]`/`state=submitted`/`STATUS=COMPLETED`/`tasks.json` running 均不算。
4. **禁止手动翻目录猜报告** - 禁扫 `Downloads/`/`results/`/`logs/` 挑文件；`ALICE_ARTIFACT_GUARD`/`ORPHAN_DOWNLOAD_CANDIDATE`/`ALICE_FORBIDDEN_READ_UNTIL_DONE` 是**警告**非可交付路径。
5. **交付 `agentResult.value` 原文（附件路径已内联）** - 禁总结/改表格/重写大类资产权重/风险预算；**必须保留 markdown 链接格式**（`[文件名](file:///绝对路径) (绝对路径)`）禁改行内代码；**禁加载 `reportFullFile=`/`attachmentFile=` 内容展示**。
6. **禁止无完成信号时交付** - 无 `ALICE_ASSET_ALLOCATION_STRATEGIC_BASELINE_PORTFOLIO_DONE` 与 `agentResult.value` 时**不得交付**。
7. **禁止绕过/删除 CLI 防重复机制** - `~/.wind-alice/submit-locks/` 按 **promptHash+subjectKey** 建 PID 锁；**禁删锁**；exit `76` 应**等待**后用相同 prompt 续接。
8. **禁止凭猜测声称 API Key 缺失** - Key 缺失**唯一信号**：退出码 `2` **且** stderr 含 `"code":"KEY_MISSING"`。exit `4`/`6`/stdout"输出不完整"/`apikey-get`返回`configured` 都**不是** Key 问题。核实跑 `apikey-get` 读 `status`（`configured`/`missing`）。**禁**无 `KEY_MISSING` 时引导配 Key。

---

## 完成判定（唯一标准）

同时满足：stdout 含 **`ALICE_ASSET_ALLOCATION_STRATEGIC_BASELINE_PORTFOLIO_DONE`** 且 **`promptHash=`** 与 **`PROMPT_HASH=`** 一致；退出码 **`0`**；**已把 `agentResult.value` 全文逐字写进正文**。自检：用户不点开折叠块就能看到完整分析（含大类资产权重、链接）--否则视为未完成。`serverCallsThisProcess=0`（续接/重放）仍须有 DONE 行；不等于可改读 `Downloads/`。

---

## replay 重放处理（必须，当 stdout 含 `ALICE_NO_SERVER_CALL=1`）

`ALICE_NO_SERVER_CALL=1` = 未向服务端发请求、复用本地 completed（非新建），交付前必须检查。

1. 🔴 **先查 `--context-id`**：带了仍触发 replay（`matchKind=prefix`）= 误判（新 prompt 是对上轮追问的回复，如风险偏好确认）-> **静默 `--new` 重跑**，不展示旧结果、不提「缓存」「replay」。
2. 不涉及 `--context-id`，从 `agentResult.value` 提取配置主题/风险偏好关键词（如「养老金」「保守型」「成长型」）对比：
   - **主体明显不同**（跨配置主题/跨风险偏好，如「养老金保守型 SAA」vs「高净值成长型 SAA」）-> **静默 `--new --no-wait` 重跑**。
   - **主体一致/高度相似**（同一配置主题不同写法）-> 停下问「该问题已有最近的分析结果。」列 (A)查看/(B)重新分析/(C)取消；禁未选就交付或 `--new`。
   - **拿不准** -> 按「主体一致」询问。
3. 无 `ALICE_NO_SERVER_CALL=1`：正常交付。

禁「明显不同」时问用户；禁（非明显不同时）未确认就交付旧结果或 `--new`。

---

## 交付来源

| 优先级 | 来源 | Agent 用法 |
|--------|------|------------|
| ✅ 首选 | stdout `agentResult.value:` 正文 | **原样**交付（去行首前缀）；CLI 已把 `/project/` 引用替换为本地路径、去 `### …完整报告` 标题；其余禁改写 |
| ✅ 兜底 | `reportFile=` -> `results/<taskId>.md` | 仅当 stdout 截断；读正文（跳过 `<!-- -->` 头）原样输出 |
| ✅ 必须 | `reportFullFile=` -> `工作空间/*.md` | **必须告知完整路径**（保留 markdown 链接格式；禁行内代码）；禁加载内容展示；`.xlsx` 仅告知路径 |
| ❌ 禁止 | 自行概括/摘录/重制表格 | 大类资产权重/风险预算会被改错 |

无 `reportFullFile=` 时不编造路径；`reportFile=` 仅摘要副本（不称「完整报告」）。

---

## 退出码速查

| 码 | 场景 | Agent 怎么做 |
|----|------|--------------|
| `2` | 参数错误 **或** `KEY_MISSING`（stderr 含 `"code":"KEY_MISSING"`） | 参数错误看 stderr；Key 缺失按红线 8 核实后 `apikey-set`。**禁**退出码非 2 时声称 Key 缺失 |
| `0` | 正常（须有 DONE 行才算完成） | 按完成判定交付 |
| `4` / `6` | 沙箱杀进程 / 未输出 DONE | **相同 prompt** 再发**一条** `--no-wait` 续接；禁连发、禁 `--new` |
| `75` | 服务端临时拒绝（并发上限 / 服务繁忙 / 积分不足） | **停止**；按 stderr 分流话术（见下方）；禁换 prompt / `--new` |
| `76` | 同主体相似 prompt / 跨进程提交锁命中 | 用**原 prompt** `--no-wait` 续接；CLI 通常已 attach/replay；**禁换措辞**；**禁删 `submit-locks/*.pid`** |
| `77` | `status`：无本地记录但有相似 completed | 阻塞 `--no-wait`；禁扫 `Downloads/` |
| `78` | 环境受限，无法保存任务状态 | **未向服务端发请求**；告知「当前环境无法运行 资产配置-战略基准组合，请开启完全访问权限后重试」；禁换 prompt / `--new` / 反复重试 |

### exit 75 话术分流

三种原因话术不能混（积分不足不能说「等任务执行完」/「稍后重试」，必须充值）：

**① 积分不足**（`积分不足`/`points`）：「您的 Alice 积分已用完，烦请[充值](https://alice.wind.com.cn/settings?tab=recharge)后把刚才的问题再发一遍。」充值前禁重试/换 prompt。
**② 并发上限**（`最大同步执行任务`/`并发`）：「您这边还有别的任务在跑已达上限，等那些任务完成后请把刚才的问题再发一遍。」强调「等已有任务执行完」非「稍后重试」；禁换 prompt/`--new`/改 `-d`。
**③ 服务繁忙**（`服务繁忙`/`系统繁忙`）：「服务端现在比较忙，请稍等一会儿把刚才的问题再发一遍。」强调「稍后重试」非「等已有任务执行完」；禁连续重试/换 prompt。

---

## 沙箱 / 短超时宿主

通常 **2–15 分钟**。宿主超时仅数十秒～分钟时**第一条 `--no-wait` 会被强杀**（exit `4`/`6`，终端杀 CLI、服务端仍跑）：对用户说「分析仍在进行中，我继续等待……」（**禁**说「被杀」「超时」）。**优先**超时调 **≥1200 秒**只发**一条** `--no-wait` 阻塞等完；**无法拉长**（Trae/Cursor）用 `--detach`+续接（① `aasbp.ps1 --prompt "<Q>" --detach` -> ② 相同 prompt `--no-wait`）。已 exit `4`/`6`（无 DONE）任务**可能仍在服务端**，用**完全相同 prompt** 再发**一条** `--no-wait`；**禁** `check_command_status`/连发多条/读 `session.log`/`results/` 猜进度。

---

## CLI stdout 机器信号

| 信号 | 含义 |
|------|------|
| `ALICE_ASSET_ALLOCATION_STRATEGIC_BASELINE_PORTFOLIO_DONE` | **唯一**完成标记 |
| `ALICE_DELIVER_AS_TEXT=1` | **交付提醒**（DONE 前打印）：必须把 `agentResult.value` **逐字复制成正文** |
| `ALICE_NO_SERVER_CALL=1` | 本进程**未向服务端发请求**（replay 重放） |
| `ALICE_SANDBOX_NO_PERSIST=1` | 环境无法保存任务状态（exit 78）；告知用户开启完全访问权限 |

---

## 禁止写法（Windows）

```powershell
# ❌ && 解析失败（PS5.x）
cd "<SKILL_DIR>" && node scripts/cli.mjs --prompt "..." --no-wait
# ❌ check_command_status 轮询 / 删锁文件 / 裸 node 代替 aasbp.ps1
```

---

## 自检清单（交付前必做）

```
□ 步骤0：已从 agent_md 读 Key 并 apikey-set？
□ 续接判断：同话题什么都不加；无关新话题加 --new-session？
□ stdout 有 ALICE_ASSET_ALLOCATION_STRATEGIC_BASELINE_PORTFOLIO_DONE？promptHash= 一致？
□ 🔴 已把 agentResult.value 全文逐字写进正文？用户不点开折叠块就能看到？
□ 若 ALICE_NO_SERVER_CALL=1（replay），已按三档处理？
□ 正文来自 agentResult.value？未概括/改大类资产权重/风险预算？
□ 若有 saa_*.png：已用 generate_chart_html.py -r 生成混排 HTML？
□ 若 reportFullFile=：路径在工作空间，直接调 present_files？
□ 🔴 本轮已调 present_files？那条零其它工具调用？与正文分两条消息？
□ 附件保留 markdown 链接格式？未加载内容展示？
□ 话术未暴露 CLI/task_id/exit code？未删锁/扫 Downloads/？
□ 若说"Key 缺失"：退出码确为 2 且 stderr 含 KEY_MISSING？
```

任一为 **否** -> **不得交付**；续接 CLI 或向用户说明未完成。
