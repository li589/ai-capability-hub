# Alice 券商金股追踪 — 宿主 Agent 执行契约

> **任何宿主 Agent（Cursor / Trae / Codex / 自建等）在调用本技能前必须先读完本文。**  
> 产品与参数细节见同目录 `SKILL.md`；本文只规定**怎么跑、怎么判定完成、怎么交付**。

`<SKILL_DIR>` = 本文件所在目录的绝对路径。

---

## 🔴 最重要规则:结果必须由你复述成正文,否则用户看不到

> **这是本技能最容易出错、且后果最严重的一点,务必首先理解并执行。**
>
> 宿主 UI(WorkBuddy 等)的折叠规则:**你亲自打字输出的文本正文(`type=text`)永远正常显示;任何工具调用的输出(含 Bash 命令的 stdout、read_file 的文件内容、present_files 的卡片)在回合结束后会被折叠进「已完成」块,用户必须点开才看得到。**
>
> 因此,CLI 通过 `abtpt.ps1` 跑完后,服务端返回的 `agentResult.value` 完整结果**会停留在 Bash 工具的 stdout 输出里,被折叠进「已完成」块**。**你不能指望用户去点开那个折叠块**。
>
> **你必须做的动作**:从 CLI stdout 提取 `agentResult.value:` 后面的正文,**亲自把它作为你自己的回复文本逐字打出来**给用户(可去掉 `agentResult.value:` 行首标记)。这一步是「你打字回复用户」,不是「工具自己显示」。只有你亲自打字输出的内容,才会作为 `type=text` 正文正常显示、不被折叠。
>
> - **正确**:跑完 CLI -> 你在回复里写下「分析完成:」+ agentResult.value 全文(逐字,不概括)。
> - **错误(会被折叠)**:跑完 CLI 就结束,让 stdout 自己显示;或只说「分析完成,详见已完成块」;或用 `Out-File` 把结果重定向到文件让用户自己看。
> - **`present_files` 与分析正文必须分两条消息**：`present_files` 单独一条（折叠成卡片可接受）；分析正文必须在**另一条不含任何工具调用**的纯文本消息里--含工具调用的整条消息会被 WorkBuddy 折叠、藏住正文。
>
> 自检:交付前问自己--「我有没有亲自把 agentResult.value 全文打字说出来?」没有,就不算交付完。CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒框(醒目 `⚠️ 交付提醒`),见到即把上面的 `agentResult.value` 逐字复制成正文。

## 🔴 第二重要规则:同会话追问默认自动续接,切话题才用 `--new-session`

> **机制（默认自动续接——防串号）**:CLI **默认在工作区内自动复用**上次 `contextId`——你**无需**手动传 `--context-id`。会话状态落在 `<工作区>/.wind-alice/current-session.json`（工作区 = `process.cwd()`），空闲窗口（默认 30 分钟）内下一轮调用自动复用上一轮的 `contextId`。**同一工作区 = 同一会话文件**，不同工作区 / 不同宿主各自独立文件，**物理上不串号**。所以「忘了传 `--context-id`」不再导致断会话。
>
> **什么时候要你动手**：只有**切到完全无关的新话题**时，加 `--new-session` 强制开新会话，避免无关上文污染。同话题追问（哪怕换月份、加维度）**什么都不用加**，自动续接。
>
> **`--context-id` 仍可用但通常不需要**：显式传 `--context-id <id>`（从上一轮 `ALICE_BROKER_TOP_PICKS_TRACKER_DONE` 行取）优先级最高，用于跨工作区或精确指定续接；同工作区内同话题续接已由自动机制覆盖。旧的 `--continue-session` / `--session-scope` 已废弃（自动续接 + 工作区隔离已取代它们），可不传。
>
> **确认续接生效**：CLI stdout 会打印 `[CLI] 会话续接：复用 contextId = ...（工作区自动续接）`（或 `--context-id 显式续接`）。无需向用户提及任何会话 / contextId 细节，直接交付结果。
>
> **常见场景**:
> - 用户先「2026年5月有哪些券商金股？」-> 交付 -> 「**那医药行业的金股呢**」：同话题延伸，**什么都不加**，自动续接。
> - 「**那热度排行呢 / 后市怎么看**」：同话题追加维度，**什么都不加**。
> - 「**宁德时代信用怎么样**」：完全无关新主题，加 `--new-session`。
> - 距上次超过 30 分钟：服务端上下文可能已过期，CLI 自动按新会话处理（无需你操作）。
>
> **拿不准时**：倾向**不加 `--new-session`**（即自动续接）。续接错了代价小（服务端多带点上文）；误切新会话代价大（丢上下文、答非所问）。**宁滥勿缺。** 详见下方「会话续接判断」专节。

---

## 七步流程（按顺序，不可跳步）

> 注：旧版「主调用前 `check-conflict` 预检」已移除--主调用 `--no-wait` 已内置去重，无需额外预检命令（也省掉一次权限确认）：同 prompt **running** 自动续接；本地 **completed** 自动重放（`ALICE_NO_SERVER_CALL=1`，不扣费）；同主体相似 prompt 命中退出码 `76`。replay 仍须在交付前按下方「replay 重放处理」一节询问用户。

| 步 | 动作 | 对用户怎么说 |
|----|------|-------------|
| 0 | **API Key 配置**：从 `agent_md` 读取已保存的 Wind Alice API Key，若存在则执行 `apikey-set`；若不存在则询问用户提供 Key，保存到 `agent_md` 后再执行 `apikey-set` | （已有 Key 时静默执行）；无 Key 时：「使用券商金股追踪需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」 |
| 1 | 把用户问题拼成一句自然语言 `--prompt`（**不要**加 `使用「券商金股追踪」技能：` 前缀）；**同步判断是否切到完全无关的新话题**（见 [「会话续接判断」专节](#会话续接判断agent-自动执行无需用户显式说)）：同话题追问**什么都不加**（CLI 工作区内自动续接）；完全无关新话题才加 `--new-session` | （无需说话） |
| 2 | 告知用户：通常需 **2–15 分钟** | 「好的，我来帮你分析。券商金股追踪通常需要 2–15 分钟，请稍等。」 |
| 3 | **主调用**：**一条** `--no-wait -d "<WORKSPACE_DIR>"`，**阻塞等待**该 shell 进程结束 | 「已提交分析，正在等待结果，请稍候……」 |
| 4 | 核对 **完成信号**（见下节）；若 stdout 含 `ALICE_NO_SERVER_CALL=1`（replay 重放），按「replay 重放处理」三档规则处理：主体明显不同 → 静默 `--new` 重跑；主体一致/拿不准 → 询问用户 | （若触发 replay 询问则见下方话术） |
| 5 | **若 DONE 含 `reportFullFile=`**：CLI 已把附件**统一下载到当前工作空间**（`process.cwd()`），路径必在工作空间内，**无需 `cp`**。① 从 DONE 行提取 `reportFullFile=` 路径；② 在一条**独立消息**里调 `present_files`（直接传该路径）。**这条消息里不要写分析正文，也禁止任何其它工具调用**（尤其 Edit/Write 写 `.workbuddy/memory` 记忆日志）--否则整条被折叠、卡片被隐藏。记忆日志写入必须在步骤 4.5 回合（curl 下载同回合）完成。无 `reportFullFile=` 时跳过本步 | （静默调用，无需对用户解释） |
| 6 | 🔴 **现在立即**：在**另一条只含文本、不含任何工具调用**的消息里，把 stdout 里的 `agentResult.value` **全文逐字复制**（去掉 `agentResult.value:` 行首前缀）。**本条消息禁止调用任何工具**（present_files / Bash / Read 等）--含工具调用的整条消息会被 WorkBuddy 折叠、藏住正文。**禁止**只说「分析完成」、**禁止**概括/改写。附件路径已内联在正文中；禁止加载 `reportFullFile=` 内容展示。CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒框，见到即执行 | 交付报告（含内联路径） |

> ⚠️ **交付方式铁律（结果被折叠的根因：present_files 与正文必须分两条消息）**：
> 
> 1. **`agentResult.value` 必须由 Agent 作为「自己的文本回复正文」逐字打出来**给用户，不能留在 CLI 的工具调用输出里。宿主 UI 规则：`type=text` 正文永远不折叠、正常显示；`tool-call`（含其 stdout）回合结束后必然折叠成「已完成 / Tool calls」块。若 Agent 只跑完 CLI 就结束、把结果留在工具输出里，用户只能点开折叠块才看得到分析正文。
> 2. **`present_files` 与分析正文必须分两条消息**：WorkBuddy 会把**含工具调用的整条消息**折叠成「Tool calls」块、藏住其中的文本。因此 `present_files`（若需）在**独立一条消息**里调用（折叠成卡片可接受）；分析正文（`agentResult.value`）必须在**另一条不含任何工具调用**的纯文本消息里输出。旧版「正文输出之后再调 present_files」会让两者落在同一条消息、整条被折叠--已废弃。 🔴 **`present_files` 那条消息也必须零其它工具调用**--尤其禁止同回合 Edit/Write（写 `.workbuddy/memory` 记忆日志）、Bash、Read；否则整条被折叠、**文件卡片被一起藏起来**（用户看不到 present_file）。记忆日志写入必须在主调用回合（步骤 4.5，curl 下载同回合）完成、先于 present_files。
> 3. **顺序**：① 静默跑完主调用 -> ②（若 `reportFullFile=`）在**独立消息**调 `present_files`（**本回合只能有 present_files 一个工具调用（禁 Bash/Read/Edit/Write/文件操作）**--否则卡片被折叠隐藏；这条可折叠成卡片）-> ③ 在**纯文本消息**里输出 `agentResult.value`（**本条禁任何工具调用**，否则整条被折叠）。
> 4. 🔴 **`reportFullFile=` 路径已在工作空间**：CLI 已把所有附件**统一下载到当前工作空间**（`process.cwd()`），`reportFullFile=` 路径必在工作空间内，**无需 `cp` 复制**——直接用该路径调 `present_files` 即可。
> 5. 🔴 **每轮都要独立调 `present_files`**：只要**本轮** DONE 含 `reportFullFile=` / `attachmentFile=`，本轮就必须在独立消息里用**本轮** DONE 的路径调 `present_files`。**禁止**因为「上一轮已经调过 present_files」就跳过本轮--每轮的附件都是当轮新生成的，必须各自呈现，否则续问中后续轮的文件用户看不到。续问多少轮就调多少次 present_files。

### API Key 配置流程（步骤 0 详细说明）

**背景**：远程沙箱每次会话都会重置，`/root/.wind-alice/config.env` 会被清空。若不持久化，用户每次新会话都要重新提供 Key。解决方案：把 Key 保存到 `agent_md`（跨会话记忆），每次使用技能前自动读取并写入配置。

**流程**：

1. 调用 `memory_recall(action="load", scope="agent_md")` 检查是否已保存 Wind Alice API Key；
2. **若已保存**：提取 Key，执行 `powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\abtpt.ps1" apikey-set <KEY>`（macOS/Linux 改用 `node "<SKILL_DIR>/scripts/cli.mjs" apikey-set <KEY>`），**静默完成，不对用户提及**；
3. **若未保存**：
   - 向用户说：「使用券商金股追踪需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」
   - 用户回复 Key 后 → 执行 `apikey-set <KEY>` → 调用 `memory_write(file="agent_md", content="增加/更新以下记忆：Wind Alice API Key = <KEY>")` 持久化 → 继续后续步骤。

**红线**：

- **禁止**在已有 Key 的情况下再问用户提供 Key（静默读取 + `apikey-set` 即可）；
- **禁止**把 Key 硬编码到 Skill 文件中；
- **禁止**每次都让用户重新提供 Key（那是 `agent_md` 持久化没生效，应检查记忆调用是否正确）；
- `apikey-set` 执行后**无需额外验证**——后续主调用若 Key 真正缺失，CLI 会以退出码 `2` + stderr `KEY_MISSING` 明确报错，届时按红线 8 处理。

### 话术红线

**禁止**向用户暴露内部实现细节（CLI、自旋、task_id、进程、shell、exit code 等）。用户只需要知道「在做什么」和「大概等多久」。

| ❌ 僵硬 / 技术化 | ✅ 自然 / 友好 |
|-------------------|----------------|
| 「分析任务已在后台启动（task_id: 88MT9l），正在等待万得 Alice 返回结果。我持续等待进程完成。」 | 「已提交分析，正在等待结果，请稍候……」 |
| 「CLI 内部自旋直到终态」 | （不对用户说，只说「正在等待结果」） |
| 「exit code 0 表示成功」 | （不对用户说） |
| 「检测到 ALICE_NO_SERVER_CALL=1，这是 replay_completed，不是新建。」 | 「该问题已有最近的分析结果，你想怎么处理？」（仅主体一致时问；主体明显不同时**静默重跑，不对用户说任何话**） |
| 「正在从 agent_md 读取 API Key 并写入 config.env……」 | （已有 Key 时静默执行，不对用户说） |
| 「请提供 Wind Alice API Key 以便调用券商金股追踪服务端接口。」 | 「使用券商金股追踪需要配置一个 Key，你有 Wind Alice 的 API Key 吗？」 |
| 「已在同一分析会话中继续（工作区自动续接 / --context-id 续接，contextId = xxx）」 | （不对用户说 session 相关细节；判断是自动的，只需正常交付结果） |
| 「你想接着刚才那个话题继续吗？」 | （不要问用户；Agent 自己按承接信号判断即可） |

### 工具调用 `description` 字段用中文

宿主执行主调用 / status 等 Bash 工具调用时，会把你填在工具调用的 `description` 字段里的文字，作为**权限确认框的标题**展示给用户。请把该字段填**简短中文**，不要填英文（如「Call Wind Alice for financial analysis」→ 改填「调用万得 Alice 进行券商金股追踪」）。

对应七步流程的推荐 `description` 取值：

| 步骤 | 命令 | `description` 填写 |
|------|------|--------------------|
| 3 | 主调用 `--no-wait` | 调用万得 Alice 进行券商金股追踪 |
| - | `status`（若用） | 查询本地任务落盘路径 |

> 这只影响权限确认框标题文案，不影响命令本身、不影响输出。`description` 仍属内部字段，不要把 CLI / task_id / exit code 等技术细节写进 `description`（与话术红线一致）。

---

## 命令模板

> ⚠️ **命令拼装铁律（照抄下方模板，禁止自由发挥）**：
>
> 宿主 Agent 拼命令时**必须逐字照抄下方模板**，只替换占位符，**不准自行增删参数、不准重定向输出、不准 cd 到 skill 目录**。以下每一条违规都会导致 WorkBuddy 弹「工作空间外部文件修改」确认框、或中文乱码、或丢失完成信号：
>
> 1. **Windows 必须用 `abtpt.ps1`，禁止裸 `node scripts/cli.mjs`**（裸 node 在 PowerShell 5.x 下中文乱码 + 沙箱兼容性问题）。
> 2. **禁止 `Set-Location`/`cd` 到 `<SKILL_DIR>`**。`abtpt.ps1` 用绝对路径调用，**不 cd**，让 `process.cwd()` 保持当前工作区。数据目录(tasks.json/session.log/submit-locks)**固定在 `~/.wind-alice/`**（跨会话稳定，不跟 cwd 走），故 cd 不影响状态目录；但仍禁止 cd 到 skill 目录：避免污染 skill 目录、避免 `present_files` 路径错乱。
> 3. **`-d` 必须传，且必须指向当前工作区根目录**（即宿主当前打开的项目目录，`process.cwd()`/`workspace`），**禁止**指向 `C:\Users\<用户>\WorkBuddy\...` 这类工作区外的临时目录或 skill 目录。`-d` 决定**报告附件落盘位置**，`present_files` 只能呈现工作区内的文件，落工作区外既弹窗又无法呈现卡片。注意：`-d` **只管报告附件**，不管 tasks.json 等状态文件--状态固定走 `~/.wind-alice/`（见铁律 2），因为 WorkBuddy 的 `-d` 是 per-session 临时目录、跨会话不稳定，不能做状态锚点。
> 4. **禁止用 `Out-File`/`>`/`2>&1 | Out-File` 把 stdout 重定向到文件**。CLI 的完成信号(`ALICE_BROKER_TOP_PICKS_TRACKER_DONE`、`agentResult.value`)在 stdout，Agent 必须**直接捕获 stdout**，重定向到文件既把文件写到工作区外(弹窗)、又可能导致 Agent 读不到完成信号。
> 5. **`-d` 路径含空格必须加双引号**；路径用反斜杠(`\`)或正斜杠(`/)`均可，但 PowerShell 下建议反斜杠。
>
> **正确示例**（照抄，只替换 `<SKILL_DIR>`、`<USER_QUESTION>`、`<WORKSPACE_DIR>`）：
> ```powershell
> powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\abtpt.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>"
> ```
> **错误示例（禁止）**：`Set-Location <SKILL_DIR>; node scripts/cli.mjs ... -d "C:\Users\xxx\WorkBuddy\..." 2>&1 | Out-File ...` -- 同时犯了裸 node、cd、-d 指向外部、Out-File 重定向四个错。

**Windows（PowerShell 5.x 不支持 `&&`，一律用方案 A）**：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\abtpt.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--context-id <上一轮contextId>] [--new-session]
```

**macOS / Linux**：

```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--context-id <上一轮contextId>] [--new-session]
```

`-d "<WORKSPACE_DIR>"` **必传**（指向当前工作区根，见上方铁律第 3 条；仅当用户明确要求换保存目录时才改指别处，但仍须在工作区内）；用户明确要求重新分析时加 `--new`（须先经用户确认）；**同话题追问无需任何会话参数**（CLI 在工作区内默认自动续接上次 contextId），**完全无关的新话题才加 `--new-session`** 强制新会话（见下方专节）；`--context-id` 可选（显式精确续接，优先级最高）；`--continue-session` / `--session-scope` 已废弃，可不传。

---

## 会话续接判断（Agent 自动执行，无需用户显式说）

**核心原则**：CLI 在工作区内**默认自动续接**上次 `contextId`（30 分钟空闲窗口内）。Agent 唯一要做的判断是——**本次是否切到了完全无关的新话题**：是 → 加 `--new-session`；否 → **什么都不加**。无需从 DONE 行抓 contextId 手动接力，无需 `--continue-session`。

### 自动续接怎么生效

会话状态写在 `<工作区>/.wind-alice/current-session.json`（工作区 = `process.cwd()`）。下一轮调用默认读它、在 30 分钟窗口内复用其 `contextId`。CLI 打印 `[CLI] 会话续接：复用 contextId = ...（工作区自动续接）` 确认。第一轮（工作区内首次调用）无历史文件，自然开新会话。不同工作区 / 不同宿主各自独立文件，不会串号。

### 判断规则（只判"是否切换"，宁滥勿缺）

**核心导向**：默认续接；只有完全无关的新主题才加 `--new-session`。判断不准时**倾向不加 `--new-session`**——续接错了代价小（服务端多带点上文）；误切新会话代价大（丢上下文、答非所问）。

| 情形 | Agent 动作 |
|------|-----------|
| 本工作区内**第一次**调用本技能 | 无历史可续，自动开新会话（无需任何参数） |
| 本次问题与上一轮**有任何话题关联**（见下方「判定为续接」） | **什么都不加**（自动续接） |
| 本次问题**完全无关**新主题 / 用户明说「换个话题」 | 加 `--new-session` 强制新会话 |
| **上一轮返回了错误金股**（replay 命中但主体不匹配） | 加 `--new-session`（session 已污染）；用明确 Prompt（含金股名）新开会话 |
| 距上次超过 30 分钟 | 无需操作——CLI 自动按新会话处理（窗口已过期） |

**判定为续接（任一命中即什么都不加，靠自动续接）**:

- **追问上文结论/原因**:「是XX引起的吗」「是因为XX吗」「为什么会出现上面说的XX」「XX是好事还是坏事」--对上一轮结果发问,**必续接**。
- **省略式追问**:「XX 呢 / 那 XX / 换成 XX / XX 是多少」。
- **显式承接**:「接着刚才继续 / 基于上面这份 / 再看下 XX 方面 / 深入一步 / 再帮我加一段」。
- **代词/指代**:「它 / 这家 / 这只 / 上面那份能不能加 XX」。
- **相同主体追加维度**:上次分析 XX 的 A 维度,本次问 XX 的 B 维度(同一主体、不同角度)。
- **同一金股话题延伸**:上文分析「2026年5月有哪些券商金股？」,本次问「那医药行业的金股呢 / 热度排行呢 / 后市怎么看」--同属该金股话题,**必续接**。

**案例（必读）**:
- ✅ 用户先「2026年5月有哪些券商金股？」-> 你交付 -> 用户「**那医药行业的金股呢**」：同话题延伸追问，**什么都不加**，自动续接。
- ✅ 用户「贵州茅台被几家券商推荐」-> 「**那行业分布呢**」：同话题追加维度，**什么都不加**。
- ❌ 用户「2026年5月有哪些券商金股？」-> 「**宁德时代信用怎么样**」：完全无关新主题，加 `--new-session`。

**判定为切换（加 `--new-session`）**:
- 用户明说:「换个话题 / 忘掉刚才 / 新问题」。
- 主体/主题明显无关:上文聊券商金股,本次问个股信用或商品期货情绪。
- 用户明说要「重新分析」(同时加 `--new`,语义正交)。

### 为什么不再需要 `--context-id` / `--session-scope` / `--continue-session`

旧版 CLI **默认不复用** contextId，必须由 Agent 从上一轮 DONE 行抓 `contextId=` 原样传 `--context-id`，一旦忘了就断会话。现在改为**工作区内默认自动续接**：会话文件落 `<process.cwd()>/.wind-alice/`，按工作区隔离防串号，Agent 无需手动接力。故：

- `--context-id`：仍兼容，优先级最高，用于跨工作区 / 精确指定续接；同工作区内同话题续接**通常不需要**。
- `--continue-session` / `--session-scope`：已废弃（no-op），自动续接 + 工作区隔离已取代它们。

### Agent 交付时的话术

- CLI stdout 出现 `[CLI] 会话续接：复用 contextId = ...（工作区自动续接 / --context-id 显式续接）` → 无需向用户提及会话 / `contextId` 等细节，直接交付 `agentResult.value`。
- 加了 `--new-session`（新话题）→ 正常按新任务交付即可。

**禁止**：向用户暴露 `contextId` / `--context-id` / `--new-session` 等技术细节；禁止把 Agent 内部的会话续接判断包装成"我帮你续接了会话"这样的对话。

---

## 八条红线

违反任一条可能导致**重复消耗积分、交付错误数据、编造指标**。

1. **阻塞等到 CLI 进程退出** — 禁止 `check_command_status`、禁止 `Start-Sleep` 轮询、禁止在进程未结束前读 `results/`/`logs/`/`Downloads/`「猜结果」。
2. **不要换 prompt 重试** — 续接/重放必须用**与首次完全一致**的措辞；换句会触发相似任务防护（exit `76`）。
3. **没有 DONE 行 = 未完成** — `[任务已受理]`、`state=submitted`、`STATUS=COMPLETED`、本地 `tasks.json` 的 running、**均不算完成**。
4. **禁止手动翻目录猜报告** — 禁止扫 `Downloads/`、`results/`、`logs/` 按公司名或修改时间挑文件；`ALICE_ARTIFACT_GUARD`、`ORPHAN_DOWNLOAD_CANDIDATE`、`ALICE_FORBIDDEN_READ_UNTIL_DONE` 是**警告**，不是可交付路径。
5. **交付 `agentResult.value` 原文（附件路径已内联）** - 禁止自行总结、改表格、重写评级/PD；附件路径已由 CLI 内联在正文中，不需末尾再追加；**必须保留 CLI 生成的 markdown 链接格式**（`[文件名](file:///绝对路径) (绝对路径)`）——禁止改成行内代码 `` `路径` ``，行内代码在 Cursor / Trae 等宿主里不可点击；**禁止加载 `reportFullFile=` / `attachmentFile=` 文件内容展示给用户**（`agentResult.value` 已是面向用户的核心分析摘要，完整报告和数据附件供用户本地查阅）。
6. **禁止在无完成信号时交付** — 无 `ALICE_BROKER_TOP_PICKS_TRACKER_DONE` 与 `agentResult.value` 时**不得交付**任何分析结论。
7. **禁止绕过或删除 CLI 的防重复机制** — CLI 在 `~/.wind-alice/submit-locks/` 下按 **promptHash + 主体名（subjectKey）** 创建 PID 锁；**禁止手动删除锁文件**；exit `76` 表示检测到同主体任务正在执行，应**等待完成**后用相同 prompt 续接，而不是删锁或换措辞。
8. **禁止凭猜测声称 API Key 缺失** — Key 缺失有**唯一确定信号**：退出码 `2` **且** stderr 含 JSON `"code":"KEY_MISSING"`。退出码 `4`/`6`（strict 兜底 / 被沙箱杀）、stdout "输出不完整"、`apikey-get` 返回 `status: configured`——这些都**不是** Key 问题。核实 Key 只能跑 `apikey-get` 并读其 JSON `status` 字段（`configured`=正常 / `missing`=缺失）。**禁止**在无 `KEY_MISSING` 退出码时引导用户配置 Key（苏美达现场：任务已成功、Key 正常，Agent 却误报 Key 缺失）。

---

## 完成判定（唯一标准）

同时满足才算完成：

- stdout 含 **`ALICE_BROKER_TOP_PICKS_TRACKER_DONE`**，且其中 **`promptHash=`** 与本次 CLI 打印的 **`PROMPT_HASH=`** 一致；
- 退出码 **`0`**；
- **Agent 已把 `agentResult.value` 全文逐字写进正文回复**（CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒）。自检：用户**不点开「已完成 / Tool calls」折叠块**就能在你的回复正文里看到完整分析（含表格、评级、链接）--否则**视为未完成**，不得结束回合。

`serverCallsThisProcess=0`（续接 / 重放 / 跨进程复用）**仍须**满足上述 DONE 行；**不等于**可以改读 `Downloads/` 里的同名主体文件。

---

## replay 重放处理（**必须**，当 stdout 含 `ALICE_NO_SERVER_CALL=1`）

主调用 `--no-wait` 返回后，若 stdout 含 `ALICE_NO_SERVER_CALL=1` / `reason=replay_completed`，说明本次**未向服务端发请求**，直接复用了本地已有的 completed 结果——**这不是新建分析**。

Agent **必须在交付前检查**是否触发了 replay。

### 处理流程（三档判定）

1. 检查 stdout 是否含 `ALICE_NO_SERVER_CALL=1`；
2. 若**是**：从 `agentResult.value` 正文中提取金股/月份/行业关键词，与当前会话上下文对比：
   - **主体明显不同**（跨品种/跨视角，如缓存的「2026年5月有哪些券商金股？」vs 请求的「宁德时代信用分析」；或缓存的「贵州茅台」vs 请求的「螺纹钢期货情绪」）→ **静默自动重跑**：用**原 prompt** 加 `--new --no-wait` 重新执行（将消耗积分）。**不向用户提及缓存/主体不匹配/重跑等任何技术细节**——用户不需要知道自己引来了别的主题缓存。重跑后按正常流程交付。
   - **主体一致或高度相似**（同品种不同写法，如「贵州茅台」vs「茅台券商推荐」；同一金股话题的追问）→ 停下来告知用户：「该问题已有最近的分析结果。」然后列出：(A) 查看已有结果 / (B) 重新分析 / (C) 取消。**禁止**未经用户明确选择就交付或 `--new`。
   - **拿不准时**（主体模糊、仅泛化关键词如「金股」「券商」、缩写无法判定）→ 按「主体一致」处理，停下来询问用户。
3. 若**否**：正常交付，按步骤 5 处理。

**关键判断标准**：
- 明显不同：两个金股主体/话题完全不同、无任何字面重叠（如「2026年5月有哪些券商金股？」→「宁德时代信用」、「贵州茅台」→「螺纹钢期货情绪」）。这类情况直接静默重跑，**绝不打扰用户**。
- 需要停下来问：同一品种不同写法（「贵州茅台」→「茅台券商推荐」）、同一金股话题的细化追问、或 Agent 无法判断是否同一主题时。
- **禁止**在「明显不同」时还停下来询问用户——这属于误报，浪费用户时间且体验极差。

**禁止**在触发 replay 时（非明显不同场景）未经用户确认就直接交付旧结果或自行加 `--new` 重跑。

- 🔴 **`--context-id` + replay 冲突**：当 Agent 判断为同一会话追问而传了 `--context-id`，但 CLI 因前缀匹配（`matchKind=prefix`）误触发 replay 时，**不得**向用户展示 replay 的旧结果（旧结果往往是参数确认页等中间态，非用户所求）。Agent 应直接静默 `--new` 重跑，不在用户面前提「缓存」「replay」等词。

---

## 交付来源

| 优先级 | 来源 | Agent 用法 |
|--------|------|------------|
| ✅ 首选 | stdout 中 `agentResult.value:` 正文 | **原样**交给用户（仅去掉行首前缀）；CLI 已自动把 `/project/` 附件引用**就地替换**为本地下载路径，并去掉 `### …完整报告` 标题；其余正文禁止改写 |
| ✅ 兜底 | DONE 行 `reportFile=` → `~/.wind-alice/results/<taskId>.md` | 仅当 stdout 被截断；读文件**正文**（跳过 `<!-- ... -->` 头）原样输出 |
| ✅ **必须** | DONE 行 `reportFullFile=` → `工作空间/*.md` | **必须告知完整路径**（**保留 CLI 生成的 markdown 链接格式** `[文件名](file:///绝对路径) (绝对路径)`；**禁止**改成行内代码——行内代码不可点击）；**禁止加载文件内容展示给用户**（`agentResult.value` 已是核心分析摘要，完整报告附件供用户本地查阅）；`.xlsx` 等仅告知路径；禁止只说「已下载」而不写路径 |
| ❌ 禁止 | 自行概括、摘录、重制表格 | 定量指标会被改错 |

### 完整报告路径已内联在正文中

交付 `agentResult.value` 原文后，附件路径已由 CLI **内联到正文中**，格式为 **markdown 链接** `[文件名](file:///绝对路径) (绝对路径)`（原文里文件出现在哪，本地下载路径就填在哪）。不需要在回复末尾再单独追加路径提示。

1. **必须保留 markdown 链接格式**：CLI 生成的 `[文件名](file:///...) (绝对路径)` 是**可点击**的（Cursor / Trae / VS Code 等 IDE 会渲染成可直接打开的链接）；**禁止**改成行内代码 `` `绝对路径` ``——行内代码**不可点击**，用户无法打开文件。CLI 已把链接内联到 `agentResult.value`，**原样输出**即可；
2. **禁止加载文件内容展示给用户**：`agentResult.value` 已是面向用户的核心分析摘要，完整报告附件（`reportFullFile=`）和数据附件（`attachmentFile=`）供用户本地查阅，Agent 不应读取并展示其内容；
3. **禁止**在末尾再追加「已保存到：…」之类的提示--路径已在正文中内联展示；
4. **禁止**只说「已下载」「可本地查阅」等空话。

| 目录 / 字段 | 实际内容 | 对用户怎么说 |
|-------------|----------|--------------|
| `reportFile=` → `~/.wind-alice/results/<taskId>.md` | `agentResult.value` **摘要副本** | **不要**称为「完整报告」；一般不必主动转告 |
| `reportFullFile=` -> `工作空间/*.md` | 完整报告 Markdown 附件 | 路径已内联在正文中；**禁止加载文件内容展示给用户** |
| `attachmentFile=` -> `工作空间/*.xlsx` 等 | 数据附件（Excel 等） | 路径已内联在正文中；**禁止加载文件内容展示给用户** |

若 DONE 行**没有** `reportFullFile=`（服务端未返回可下载附件），**不要**编造下载路径；只交付 `agentResult.value` 即可。


---

## 退出码速查

| 码 | 场景 | Agent 怎么做 |
|----|------|--------------|
| `2` | 参数错误 **或** `KEY_MISSING`（stderr 含 `"code":"KEY_MISSING"`） | 参数错误 → 看 stderr 提示；Key 缺失 → 按红线 8 核实后 `apikey-set`。**禁止**在退出码不是 2 时声称 Key 缺失 |
| `0` | 正常（须另有 DONE 行才算完成） | 按完成判定交付 |
| `4` / `6` | 沙箱杀进程 / 未输出 DONE | **相同 prompt** 再发**一条** `--no-wait` 续接；禁止连发、禁止 `--new` |
| `75` | 服务端临时拒绝（并发上限 / 服务繁忙 / 积分不足） | **停止**；按 stderr 内容分流话术（见下方「exit 75 话术分流」）；禁止换 prompt / `--new` 绕过 |
| `76` | 同主体相似 prompt / 跨进程 **promptHash 或 subjectKey** 提交锁命中 | 用**原 prompt** `--no-wait` 续接；CLI 通常已自动 attach/replay；**禁止换措辞**；**禁止删除 `submit-locks/*.pid` 锁文件** |
| `77` | `status`：无本地记录但有相似 completed | 阻塞 `--no-wait`；禁止扫 `Downloads/` |
| `78` | 环境受限，无法保存任务状态 | **未向服务端发请求**；告知用户「当前环境无法运行 券商金股追踪，请在工具中开启完全访问权限后重试」；禁止换 prompt / `--new` / 反复重试 |

### exit 75 话术分流（按 stderr 内容选对用户说什么）

退出码 75 涵盖三种不同原因，**话术不能混用**——尤其积分不足不能说「等任务执行完」或「稍后重试」（您等再久也没用，必须充值）；并发上限与服务繁忙也各有各的说法，不要混。下面话术用「您」称呼用户，措辞已润色，可接近原样转述。

**① 积分不足**（stderr 含 `积分不足` / `积分已用完` / `points`）——话术：

> 很抱歉，这次的分析没能跑起来——您的 Alice 积分已用完。烦请您前往 [万得 Alice → 设置 → 充值](https://alice.wind.com.cn/settings?tab=recharge) 充值。充值完成后，请您把刚才的问题再发一遍，我立刻为您重新分析。

要点：给唯一动作（充值链接）；**明确请用户充值后重新发送问题**（不要说「我直接接着跑 / 不用复述」——需用户重新发问）；**不提**退出码 / prompt / CLI 等技术词；**不说**「等任务执行完」「稍后重试」。充值前禁止重试或换 prompt。

**② 并发上限**（stderr 含 `最大同步执行任务` / `并发` / `请等待其他任务执行完成` 等）——话术：

> 您这边还有别的分析任务正在跑，已经达到同时进行的数量上限，这次没发起。等那些任务完成后，请您把刚才的问题再发一遍，我立刻为您重新分析。

要点：强调「等已有任务执行完」，**不是**「稍后重试 / 过几分钟」；**需用户在已有任务完成后重新发送问题**；禁止换 prompt / `--new` / 改 `-d`（都会再占并发槽）。

**③ 服务繁忙**（stderr 含 `服务繁忙` / `系统繁忙` / `请稍后重试` 等）——话术：

> 服务端现在比较忙，暂时没接上这次请求。请您稍等一会儿，把刚才的问题再发一遍，我立刻为您重新分析。

要点：强调「稍后重试」，**不是**「等已有任务执行完」（那是并发上限的话术）；**需用户稍后重新发送问题**；禁止连续重试或换 prompt。

---


## 沙箱 / 短超时宿主

券商金股追踪通常 **2–15 分钟**。若宿主 `run_command` 只有数十秒～几分钟超时，**第一条 `--no-wait` 会被强杀**（exit `4`/`6`），看起来像「卡住」——其实是终端杀了 CLI，服务端往往仍在跑。此时对用户说：「分析仍在进行中，我继续等待……」，**不要**说「被杀」「超时」等技术细节。

**优先**：把 shell / `run_command` 超时调到 **≥1200 秒（20 分钟）**，只发**一条** `--no-wait` 并阻塞等到进程结束。

**若无法拉长超时**（Trae / Cursor 等），用 **`--detach` + 续接**：

```powershell
# ① 后台提交（父进程立刻退出，子进程继续跑）
powershell ... abtpt.ps1 --prompt "<USER_QUESTION>" --detach

# ② 相同 prompt 续接轮询（仍只发一条，阻塞等到 DONE）
powershell ... abtpt.ps1 --prompt "<USER_QUESTION>" --no-wait
```

若已 exit `4`/`6`（未见到 DONE）：

1. 任务**可能仍在服务端执行**；
2. 用**完全相同 prompt** 再发**一条** `--no-wait`；
3. **不要** `check_command_status`、**不要**连发多条 CLI、**不要**读 `session.log`/`results/` 猜进度。

**典型误操作（会表现为卡住）**：`--no-wait` 后反复 `check_command_status` → 终端超时杀进程 → 读 `Test-Path results/`（文件尚未生成）→ 再发第二条 `--no-wait`。

---

## CLI stdout 机器信号（辅助识别）

| 信号 | 含义 |
|------|------|
| `ALICE_BROKER_TOP_PICKS_TRACKER_DONE` | **唯一**完成标记 |
| `ALICE_DELIVER_AS_TEXT=1` | **交付动作提醒**（DONE 前打印，醒目 `⚠️ 交付提醒` 框）：必须把上面 stdout 里的 `agentResult.value` **逐字复制成正文回复**，否则被宿主折叠、用户看不到 |
| `ALICE_POLL_HEARTBEAT` | 仍在执行，未完成 |
| `ALICE_ARTIFACT_GUARD` / `ALICE_FORBIDDEN_READ_UNTIL_DONE` | 禁止读列出的旧报告路径 |
| `ALICE_USER_DOWNLOAD_HINT=` | 完整报告附件**可点击**的 markdown 链接（`[文件名](file:///...) (绝对路径)`，供 Agent 原样输出；已内联在 `agentResult.value` 正文中） |
| `ALICE_NO_SERVER_CALL=1` | 本进程**未向服务端发请求**（replay 重放） |
| `ALICE_SESSION_LOG=` | Windows 乱码时只读 stdout 给出的**完整**日志路径 |
| `ALICE_SANDBOX_NO_PERSIST=1` | 当前环境无法保存任务状态，已阻止提交（退出码 78）；**未向服务端发请求**；告知用户开启完全访问权限后重试 |

---

## 禁止写法（Windows）

```powershell
# ❌ PowerShell 5.x：&& 解析失败
cd "<SKILL_DIR>" && node scripts/cli.mjs --prompt "..." --no-wait

# ❌ 命令末尾拼 undefined 等垃圾参数
... abtpt.ps1 --prompt "..." --no-wait undefined

# ❌ 用 check_command_status 轮询代替阻塞等待
# （终端超时会杀 CLI，任务仍在服务端跑，Agent 却以为卡住）
... abtpt.ps1 --prompt "..." --no-wait
# 然后反复 check_command_status / Get-Content session.log / Test-Path results/

# ❌ 后台 / fire-and-forget（分析主路径禁止；仅 --detach 场景由 CLI 内部 detached 子进程）
Start-Process ... | Out-Null

# ❌ 删除 CLI 的防重复提交锁文件以绕过保护（会导致重复扣积分）
Remove-Item -Path "$env:USERPROFILE\.wind-alice\submit-locks\*.pid" -Force
Remove-Item -Path "$env:TEMP\alice-submit-locks\*.pid" -Force

# ❌ 用裸 node cli.mjs 代替 abtpt.ps1（Windows 上会导致中文乱码、沙箱兼容性问题）
node "...\scripts\cli.mjs" --prompt "..." --no-wait
```

---

## 自检清单（交付前必做）

```
□ 步骤 0 已完成：已从 agent_md 读取 API Key 并执行 apikey-set（或首次获取后已 memory_write 持久化）？
□ 步骤 1 会话续接判断已执行：同话题追问什么都不加（CLI 工作区内自动续接）；完全无关新话题才加 --new-session？
□ stdout 有 ALICE_BROKER_TOP_PICKS_TRACKER_DONE？
□ DONE 的 promptHash= 等于本次 PROMPT_HASH=？
□ 🔴 **已把 agentResult.value 全文逐字写进回复正文**（见到 `ALICE_DELIVER_AS_TEXT=1` 提醒即执行）？自检：用户**不点开折叠块**就能看到完整分析（表格/数字/链接）--若正文里没有完整结果、只说「分析完成」或「详见已完成块」，**视为未交付，不得结束回合**？
□ 若 stdout 含 ALICE_NO_SERVER_CALL=1（replay 重放），已按三档规则处理：主体明显不同 → 静默 --new；主体一致/拿不准 → 询问用户？
□ 正文来自 agentResult.value 或 reportFile=，而非 Downloads/ 附件正文？
□ 未自行概括、未改数字、未摘录（**整段逐字**，含所有表格行）？
□ CLI stdout 的 agentResult.value 中 `/project/` 已被替换为本地下载路径，`### …完整报告` 已过滤（CLI 自动处理）？
□ 若 DONE 含 reportFullFile=：路径已在工作空间（CLI 统一下载到 process.cwd()），直接用该路径调 present_files（无需 cp）？
□ 🔴 **本轮**（不是上一轮）已调 present_files？续问每轮都要独立调，不能因上一轮调过就跳过本轮的附件？
□ 🔴 **present_files 那条消息里有没有混入 Edit/Write（写 `.workbuddy/memory` 记忆日志）或其它工具调用**？若有，整条会被 WorkBuddy 折叠、文件卡片被隐藏--把记忆写入移到主调用回合（curl 下载同回合），让 present_files 单独一条、零其它工具调用？
□ 🔴 present_files 和分析正文分在**两条独立消息**（present_files 单独一条；正文在另一条不含任何工具调用的纯文本消息）--混在同一条会被 WorkBuddy 整条折叠、藏住文件卡片？
□ 附件路径已内联在正文中，不在末尾再追加？
□ **附件路径保留了 markdown 链接格式**（`[文件名](file:///...) (绝对路径)`），**没有**改成行内代码 `` `路径` ``（行内代码不可点击）？
□ 未加载 reportFullFile= / attachmentFile= 文件内容展示给用户（仅告知路径）？
□ 未把 results/ 说成完整报告？
□ 对用户说的话里没有暴露 CLI、自旋、task_id、进程、shell、exit code 等内部技术细节？
□ 没有删除 submit-locks/ 下的锁文件来绕过防重复提交保护？
□ 没有用 view_folder / view_files 扫描 Downloads/、results/、logs/ 目录来「猜」报告？
□ 若向用户说过"Key 缺失/需要配置 Key"——退出码确实是 2 且 stderr 含 KEY_MISSING？若否，已停止并改按真实退出码处理（红线 8）？
□ 没有在 agent_md 已保存 Key 的情况下再次询问用户提供 Key？
```

任一为 **否** → **不得交付**；续接 CLI 或向用户说明未完成。

---

更多 FAQ、环境配置、典型复盘见 `SKILL.md`。
