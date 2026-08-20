# Auth Guard（所有业务命令前必须执行）

> **本文件相对上游有改动。** 上游 STEP 2 使用 `meegle auth login --host <host>`（浏览器
> Authorization Code 流程）。该流程需要真实 TTY 和本地 HTTP 回调，在 Agent 环境中会直接被CLI
> 拒绝并返回 `INTERACTIVE_BROWSER_REQUIRED`。这里改为 CLI 自身支持的**分离式 Device Code**
> 流程。改动理由与完整清单见 [../NOTICE.md](../NOTICE.md)。

## 触发条件

- **主动登录**：用户说"登录 Meegle"、"连接飞书项目"、"login meegle"等。
- **被动拦截**：用户请求任何 Meegle 业务操作（查询待办、查工作项、创建任务等），优先执行 Auth Guard。
- **URL 触发**：用户发送了飞书项目/Meegle URL。处理流程：
  1. 先调 `url decode` 拿到结构化字段（`url_kind`、`host`、`simple_name`、`work_item_id` 等）。**禁止**自己从 URL 截取路径段作参数。字段含义与 kind 分支见 [url-kinds.md](url-kinds.md)。
  2. 保存 `$host` = response.host、`$url_kind`、`$simple_name`、`$work_item_id`。
  3. 执行 Auth Guard（下面的 STEP 0 起）。
  4. 登录成功后按 `$url_kind`分支：
     - `workitem_detail` → `project search` 得权威 `$project_key`，再 `workitem get` 查询详情
     - `workitem_homepage` / `view_*` / `unknown` 等非详情页 → 按 url-kinds.md 的指引拒绝或追问
     - 其他 kind → 参考 url-kinds.md 对应处理方式

按以下 STEP 顺序执行。每个 STEP 结尾的 GOTO 指明下一步，严格遵循跳转。

---

### STEP 0 — 确认 CLI 已安装

优先用父技能自带的预检脚本，一次调用同时回答"装了没"和"登录了没"：

```bash
STATUS=$(find ~/.workbuddy/skills ./.workbuddy/skills -name meegle_status.py 2>/dev/null | head -1)
OUT=$($STATUS 2>&1 || python3 "$STATUS"); RC=$?
```

| 退出码 | 状态 | 跳转 |
|--------|------|------|
| 0 | 已装且已登录 | GOTO STEP DONE |
| 3 | 未安装 | 先装二进制（见下），再回 STEP 1 |
| 4 | 已装未登录 | GOTO STEP 1 |
| 5 | 输出无法解析 | 手工执行 `meegle auth status --format json` 排查 |

拿不到脚本时退化为：

```bash
OUT=$(meegle --version 2>&1); RC=$?
```

未安装时按父技能 [lark-unified 第 0.3 节](../../../SKILL.md) 的按需安装流程装好二进制
（`npx -y @lark-project/meegle@latest install --no-skills --no-auth --host <host> --lang zh`），
再回到 STEP 1。**不要**省略 `--no-skills`，否则官方向导会往全局技能目录再装一份 meegle 技能，
与本子技能重复。

---

### STEP 1 — 检查登录状态

```bash
OUT=$(meegle auth status --format json 2>&1); RC=$?
echo "rc=$RC"; echo "$OUT"
```

> **务必同行捕获退出码**（`OUT=$(...); RC=$?`）。写成 `meegle auth status | head` 之后再取 `$?`
> 拿到的是 `head` 的退出码，会把未登录误判成已登录。

返回值示例：
- 已登录：`{ "authenticated": true, "host": "project.feishu.cn", "source": "token_store", "expires_in_minutes": 42 }`
- 未登录：`{ "authenticated": false, "host": null, "reason": "no local token" }`（退出码 **1**）

解析返回值，保存变量：
- `$authenticated` = response.authenticated
- `$host` = response.host

**判据以 `authenticated` 字段为准**，退出码只作辅助。

**URL 触发时的 host 覆盖**：如果用户发送了飞书项目/Meegle URL 触发本流程，且 `$host` 为 null，则使用上一步 `url decode` 返回的 `host` 字段作为 `$host`。

**跳转：**
- IF `$authenticated == true` → GOTO STEP DONE
- IF `$host != null` → GOTO STEP 2
- IF `$host == null` → GOTO STEP HOST

---

### STEP HOST — 选择站点

ASK user（等待用户回复）：

> 你要连接哪个站点？
> 1) 飞书项目 (project.feishu.cn)
> 2) Meegle (meegle.com)
> 3) 自定义域名（请直接输入域名）

SAVE `$host` from user reply → GOTO STEP 2

---

### STEP 2 — Device Code 登录 · 第一阶段（取授权链接）

**本 STEP 结束后必须结束回复轮次，把链接交给用户，不要在同一轮里继续轮询。**

优先用套件自带脚本（已封装下面的原始命令，并直接给出 `resume_command`）：

```bash
SETUP=$(find~/.workbuddy/skills ./.workbuddy/skills -name meegle_setup.py 2>/dev/null | head -1)
python3 "$SETUP" --host $host --print-url-only
```

输出（实测形状）：

```json
{
  "ok": true,
  "state": "awaiting_authorization",
  "verification_url": "https://project.feishu.cn/b/auth/mcp?channel=meegle-cli&mode=device&usercode=XXXXX-XXXXX",
  "user_code": "XXXXX-XXXXX",
  "device_code": "bcd3c3f9-...",
  "client_id": "cli_...",
  "expires_in": 1800,
  "interval": 5,
  "resume_command": "python3 meegle_setup.py --resume --device-code <dc> --client-id <cid>"
}
```

等价的原始 CLI 调用（脚本不可用时退化使用）：

```bash
meegle auth login --device-code --phase init --host $host --format json
# -> {"client_id","device_code","user_code","verification_uri",
#     "verification_uri_complete","expires_in","interval"}
```

保存 `$device_code`、`$client_id`、`$interval`。

把 **`verification_url`**（原始命令下对应 `verification_uri_complete`）原样发给用户——该链接已内嵌
user_code，用户点开即可授权。链接按不透明字符串处理：不要重新编码、不要拆装 query 参数。

SEND to user：授权链接 + `user_code` + 提示"授权完成后告诉我"。→ **END TURN**

---

### STEP 3 — Device Code 登录 · 第二阶段（轮询换 token）

用户回复已授权后，**由你执行**（不要让用户在终端里手敲）：

```bash
python3 "$SETUP" --resume --device-code $device_code --client-id $client_id
```

| 退出码 | 含义 | 跳转 |
|--------|------|------|
| 0 | 已换到 token | GOTO STEP OK |
| 2 | pending，用户还没点完 | 提示后重试；连续 3 次仍 pending 回 STEP 2 取新链接 |
| 4 | 设备码已过期 / 被拒 / 服务端错误 | 回 STEP 2 重新取链接 |
| 3 | 二进制不存在 | 回 STEP 0 |

等价的原始 CLI 调用：

```bash
OUT=$(meegle auth login --device-code --phase poll --once \
  --host $host \
  --device-code-value $device_code \
  --client-id $client_id \
  --format json 2>&1); RC=$?
echo "rc=$RC"; echo "$OUT"
```

> ⚠️ **裸用CLI 时，`--once` 在「尚未授权」时也返回退出码 0**，输出
> `{"status":"authorization_pending"}`。必须读 `status` 字段判断，不能只看退出码。脚本已经把这个
> 语义翻译成退出码 2，这也是优先用脚本的原因。

省略 `--once` 会进入阻塞轮询（`--interval` 秒一次，`--expires-in` 秒超时）。只在确认用户已经完成
授权、且当前环境允许长时间阻塞时才用阻塞模式，否则优先 `--once` / `--resume`。

---

### STEP OK — 通知登录成功

SEND to user: "登录成功！"

> ⚠️ 此消息**必须单独发送**，不要与后续业务查询结果合并到同一条回复中。用户需要第一时间看到授权状态变化。

→ GOTO STEP DONE

---

### STEP DONE — 执行业务命令

Auth 已通过，执行用户请求的操作。

## 错误处理

- **`unknown command "workitem"` 之类的报错不一定是命令写错了。** 未登录时 Meegle 只注册
  `auth` / `config` / `url` / `inspect` / `completion` / `version` 这几个基础命令，业务命令根本不
  注册，因此**未授权**和**命令不存在**的报错文本、退出码完全相同（都是 `unknown command ... for
  "meegle"`，RC=1）。遇到这个报错先回 STEP 1 查 `auth status`，确认不是未登录。
- 同理，未登录时 `meegle inspect` 会返回 `No commands available (not connected to server or cache is
  empty)` 且退出码为 **0**。这也是未登录的表现，不是 CLI 坏了。
- 如果 bash 返回 `command not found` 或 npx 不可用，提示用户安装 Node.js 18+，并回到 STEP 0。
- 浏览器流程（不带 `--device-code`的 `meegle auth login`）在无 TTY 环境会返回
  `INTERACTIVE_BROWSER_REQUIRED`。这是 CLI 的预期行为，**不要重试**，改用上面的 Device Code 流程。
