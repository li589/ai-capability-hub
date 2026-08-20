---
name: lingyi-copy-de-ai-human-comment
display_name: 文案去AI味+真人点评
display_name_en: "Copy De-AI with Human-Reader Review"
description_zh: "【零一数科·出品】文案去AI味+真人点评（付费版）。把小红书/视频号/公众号/抖音文案改写得像真人写、消除 AI 痕迹降 AI 率，并模拟真实人群画像的读者逐段评估「哪里还像 AI、哪里不像人写」，给出人味打分与残留痕迹定位。别人只改不验，本品改完让真人评估把关。触发词：文案去AI味、社媒文案去AI、去AI味、降AI率、AI去痕、过AI检测、人味改写、真人评估、读者验收、真人试读。"
description_en: "[Lingyi Tech] Rewrite social-media copy to sound human and lower your AI-detection rate, then let simulated real-reader personas score it paragraph by paragraph."
category: content-creation
version: 0.2.0
author: 小风、CoderPig、Awen
---

# 文案去AI味+真人点评
> 版本：v0.2.0 · 作者：小风、CoderPig、Awen

帮你把社媒文案改得像真人写的，改完还能让模拟读者来验收「还像不像 AI」。

| 环节 | 耗时 | 扣点 |
|------|------|------|
| **去 AI 味改写** | 长文案 1–3 分钟 | 约 12 点 |
| **真人评估** | 30 秒–2 分钟 | 约 15 点 |

**跟别的去 AI 味工具不一样的地方**：别人只改不验；本品改完让模拟真实读者来打分——给「人味分」0-10，指出哪里还像 AI，告诉你「能不能发」还是「建议再改一轮」。

⚠️ **对用户说话要说人话。** 技术字段（mode/task_id/退出码等）是你内部用的，永远不要对用户说。一句里只做一件事——问信息就问信息，报价格就报价格，别混着说。所有用户沟通话术见 [references/usage-notes.md](references/usage-notes.md)。

## 执行流程

1. **取 API Key**：读 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失引导用户获取。
2. **收集信息**：确认文案和平台（缺什么问什么，只问一轮）。详见「信息收集」。
3. **扣点确认 → 改写**：确认后跑改写（`--mode rewrite`），拆分轮询。
4. **交付改写稿**：渲染 Markdown，告知扣点。
5. **扣点确认 → 评估**：确认后跑评估（`--mode eval`），拆分轮询。
6. **交付评估报告**：渲染 Markdown，告知扣点，给闭环建议。

以上每步的用户话术见 [references/usage-notes.md](references/usage-notes.md)。任一步异常按「退出码处理」对号入座。

### 拆分轮询（防会话中断）

改写和评估各是独立异步任务，**禁止一次同步阻塞到完成**（WorkBuddy/Web 单轮有上限）。必须拆成「创建 + 多次短轮询」：

**改写轮询**：
1. `python3 scripts/human_eval.py --mode rewrite --text "<原文>" --platform xhs --only-create` → 拿 task_id（退出码 0）
2. 对用户说「在改写了，大概 1-3 分钟，好了直接给你看。」
3. 循环 `python3 scripts/human_eval.py --poll-task <id> --text "<原文>" --out ...`（单次 ≤90s）：
   - 退出码 0 → 交付改写稿
   - 退出码 13（进行中）→ 对用户说「还在改写，再等一会儿」，**立刻再跑** `--poll-task`
   - 退出码 12 → 失败处理
   - 其他 → 按「退出码处理」

**评估轮询**：同上模式，`--mode eval`、`--text` 传**改写终稿**。

### 用户问「好了吗」

用进度信息人话转述：「还在改写」「评估在跑，马上出」。**禁止说**「查不了」。转述后立即续轮询。

## 鉴权

读技能目录 `config.json` 的 `LY_API_KEY`（回退环境变量）。

1. 有 key → 继续
2. 没有 → 引导用户去 <https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy> 取 key 写入 `config.json`
3. key 失效（退出码 8）→ 重新获取覆盖后重试
4. SSL 报错 → `LY_SKIP_SSL_VERIFY=1` 或 `--insecure`

## 信息收集

跟用户确认这些，**缺什么问什么，只问一轮**：

| 用户需要提供 | 说明 |
|-------------|------|
| **文案** | 贴过来或给文件路径 |
| **发哪儿** | 小红书/视频号/公众号/抖音（默认小红书） |
| **要不要评估** | 默认改完就评估；说「只改就行」就只改不评估 |
| **指定读者**（可选） | 比如「针对宝妈圈层」，不指定就用 5 类默认读者 |
| **评论条数**（可选） | 默认 6 条，一般不用改 |

> 只处理文案文本，不分析视频画面。

⚠️ **一句话只做一件事**：问信息就问信息，报价格就报价格，别混着说。

### 用户意图 → 你怎么接

| 用户说的 | 你做的 |
|----------|--------|
| "帮我改像人写的" / "去AI味" | 改写 + 评估（默认全流程） |
| "只改就行" | 只改写，不评估 |
| "帮我看看还像不像AI" | 直接评估（不改写） |
| "针对宝妈圈层" | 改写 + 评估（指定读者） |

详细话术见 [references/usage-notes.md](references/usage-notes.md) §1-2。

## 扣点与确认

**每跑一轮前都要用户确认，跳过不得。** 话术要简单，一句话只做一件事：

### 默认全流程（改写+评估）

开跑前一次确认：
> 帮你改写（约 12 点）+ 模拟读者验收（约 15 点），一共约 27 点，实际按用量算。可以吗？

改写完成后确认评估：
> 改好了 ✅ 实际扣了 {N} 点。接下来让模拟读者验一遍「还像不像 AI」，约 15 点。要验吗？

### 只改写

> 帮你改写，约扣 12 点，实际按用量算。可以吗？

### 直接评估

> 让模拟读者验收，约扣 15 点，实际按用量算。可以吗？

### 扣点相关规则

- 用户未确认/犹豫 → **不跑脚本**
- 确认词统一用「可以吗？」，别混用「开搞？」「确认？」「来？」
- 成功后告知实扣：`HUMAN_EVAL_POINTS_USED` 有值就说「实际扣了 N 点」，没值就说「约扣 N 点，以账户为准」
- 失败后告知：**「出了点问题，点数已退回来，要不要再试？」**

## 运行方式

```bash
# 改写
python3 scripts/human_eval.py --mode rewrite --text "<原文或文件路径或->" --platform xhs --only-create
python3 scripts/human_eval.py --poll-task <task_id> --text "<原文>" --out ./改写报告.md

# 评估（改写完成后）
python3 scripts/human_eval.py --mode eval --text "<改写终稿>" --platform xhs --only-create \
  --personas "25-34-女-白领-高消费,35-44-女-宝妈-中消费"
python3 scripts/human_eval.py --poll-task <task_id> --text "<改写终稿>" --out ./评估报告.md

# 失败重试
python3 scripts/human_eval.py --retry-task <task_id> --out ./报告.md

# 同步一把梭（Web 端易被打断，慎用）
python3 scripts/human_eval.py --mode rewrite --text "..." --platform xhs --out ./改写报告.md
python3 scripts/human_eval.py --mode eval --text "..." --platform xhs --out ./评估报告.md
```

脚本参数说明：

- `--mode rewrite|eval`：必填。改写或评估。两次必须用不同 `--idempotency-key`。
- `--platform xhs|channels|mp|dy`：默认 `xhs`
- `--personas`：读者（如 `25-34-女-白领-高消费`），仅 eval 生效
- `--comment-count`：评论条数 1–20，默认 6，仅 eval 生效
- `--out PATH`：输出路径，缺省 `报告-<task_id>.md`
- `--only-create`：仅创建拿 task_id，配合 `--poll-task`
- `--poll-task <id>`：轮询，建议带 `--text`
- `--retry-task <id>`：重试，沿用原 mode
- `--timeout 90` / `--poll-interval 5` / `--insecure` / `--idempotency-key`
- `--text -`：从 stdin 读

## 输出交付

脚本 stdout 协议（你内部用，不对用户展示）：

```
HUMAN_EVAL_POINTS_USED=<实扣点>
HUMAN_EVAL_PLAN_POINTS=<预估点>
HUMAN_EVAL_REPORT_FILE=<文件路径>
HUMAN_EVAL_TASK_ID=<任务id>
HUMAN_EVAL_MODE=<rewrite或eval>
=== HUMAN_EVAL_REPORT_START ===
<Markdown 报告正文>
=== HUMAN_EVAL_REPORT_END ===
```

⚠️ **交付 = 用户必须直接在对话里看到报告全文。** 只告诉用户「报告已保存到 xxx」不算交付，用户根本看不到内容。

### 第一步：把报告内容渲染出来（唯一核心交付）

脚本 stdout 里 `=== HUMAN_EVAL_REPORT_START ===` 和 `=== HUMAN_EVAL_REPORT_END ===` 之间的内容就是完整 Markdown 报告。**你必须把这段 Markdown 直接输出到对话里**，让用户在对话里就能看到完整的标题、卡片、引用排版。

❌ **绝对不能**：
- ❌ 只说「报告已生成/已保存」却不在对话里输出正文
- ❌ 只告诉用户 MD 文件路径就认为交完了
- ❌ 把 `HUMAN_EVAL_*=` 协议行、`===` 分隔符展示给用户
- ❌ 把带 `\n` 的原文原样贴给用户

### 第二步：加上收尾话术

**改写交付**：输出 Markdown 后说——
> 改好了 ✅ 实际扣了 {N} 点。

如果预设要跑评估，接着说——
> 要让模拟读者来验一遍吗？约 15 点。

**评估交付**：输出 Markdown 后说——
> 上面就是模拟读者的验收结果，实际扣了 {N} 点。

然后给建议：
- 均分 ≥ 7 / 可发 → 「读者普遍觉得像真人写的，可以直接发了。」
- 均分 < 7 / 有 AI 嫌疑 → 「还有几个地方读者觉得像 AI，要不要我针对这几个点再改一轮？」

评估交付末尾附免责（见「免责声明」节）。

扣点数值取法：`HUMAN_EVAL_POINTS_USED` 有值说「实际扣了 N 点」，没值说「约扣 N 点，以账户为准」。

### 第三步（可选）：提一句文件位置

报告主体已经在对话里了，可以顺带说一句「MD 文件也存了一份在 {HUMAN_EVAL_REPORT_FILE}」，但**这步跳过也行，不能代替第一步**。

## 退出码处理

| 码 | 怎么了 | 你对用户说 |
|----|--------|-----------|
| 0 | 成功 | 渲染报告 + 告知扣点 |
| 2 | 没 API Key | 引导去 auth 页取 key |
| 3 | 参数不对 | 补全后重试 |
| 4 | 余额不足 | 引导充值 |
| 8 | Key 失效 | 重新获取 key |
| 10 | 其他 4xx | 按服务端提示修正 |
| 11 | 网络错误 | **「出了点问题，点数已退回来，要不要再试？」** |
| 12 | 任务失败 | **「出了点问题，点数已退回来，要不要再试？」** |
| 13 | 还在跑（不是失败） | 对用户说「还在处理」→ 立刻继续 `--poll-task`，别停 |

## 免责声明

评估交付时附一句（语气轻松）：
> 提醒一下，这个读者反应是模拟的，仅供参考哈，不能当发布决策的唯一依据。

改写本身是风格编辑，不声称「无法被 AI 检测器识别」。

## 通用原则

- 引用 reference 用相对路径
- 报告 Markdown 由后端渲染，skill 侧不做模板
- 最终 MD 由脚本覆写，agent 不要手动追加/改写输出文件
- **交付时务必把 Markdown 真正渲染给用户**
- 只使用异步任务接口：`POST /tasks` → `GET /tasks/{id}` → 可选 `POST /retry`
- 改写和评估是两次独立任务，各扣各的点，`--retry-task` 沿用原 mode
- 两次任务必须用不同 `--idempotency-key`
- **所有用户沟通话术的单一事实源**：[references/usage-notes.md](references/usage-notes.md) — 遇到不确定怎么说，去那里查
