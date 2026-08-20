---
name: midu-writing
version: 1.2.0
license: MIT
author: 上海蜜度云智能科技有限公司
description: >-
  当用户需要进行写作任务时使用此 Skill，包括但不限于：撰写文章、报告、文案、邮件、总结等。

  支持多轮对话，可在同一写作任务中持续补充或修改内容。

  采用「对话内手机号短信验证码登录」获取鉴权，无需打开官网取 Key。

  首次使用会引导：填手机号 → 下发验证码 → 提交验证码拿 appSecret 并写入 ~/.midu_keys，之后直接写作；已有凭证则跳过授权直接写作。

  Use this Skill when the user needs to perform writing tasks, including but not
  limited to:

  writing articles, reports, copywriting, emails, summaries, etc.

  Supports multi-turn conversation; uses in-chat SMS auth for credentials.
display_name: 蜜度公文写作
display_name_en: Midu Document Writing
description_zh: 多轮对话式公文写作助手，支持简报、报告、邮件、总结等多种文体，可基于上下文持续修改内容。
description_en: "Multi-turn conversational assistant for official document
  writing: briefs, reports, emails, summaries, with context-aware refinement."
visibility: public
disable-model-invocation: true
---

# 蜜度写作 Skill（短信授权版）

此 Skill 调用蜜度写作接口完成写作任务，支持多轮对话。

鉴权方式为「对话内手机号短信验证码登录」拿 `appSecret` / `userId`，**禁止**再引导用户打开 `ai.mdata.net` / `ai-beta.mdata.net` 手动取 Key；业务请求头须携带 `Authorization`、`X-Skill-Code`、`X-User-Id`。

## 前置条件（鉴权凭证）

业务接口需要三个请求头：`Authorization: Bearer <appSecret>`、`X-Skill-Code: MIDU-WRITING`、`X-User-Id: <userId>`。凭证来自短信登录：

- `MIDU_APP_SECRET` ← 登录返回的 `appSecret`（`primaryEnv`）
- `MIDU_USER_ID` ← 登录返回的 `userId`（供 `X-User-Id`）

优先级：显式 `--api-key` / `--user-id` 参数 > 环境变量 `MIDU_APP_SECRET` / `MIDU_USER_ID` > 本地文件 `~/.midu_keys`。

执行脚本前确保已安装依赖：

```bash
pip3 install requests
```

## 脚本定义

- `scripts/midu_auth.py` — 短信验证码登录/注册：`--action send` 下发验证码、`--action verify` 校验并返回 `appSecret` / `userId`，成功后写入 `~/.midu_keys`。
- `scripts/midu_write.py` — 业务写作：读取凭证（env 或 `~/.midu_keys`）→ 调用写作接口（带 `X-User-Id`）→ 输出 `thread_id` / `article_url` 等。

## 工作流程

### Auth Workflow（仅首次授权一次）

> 只在「首次安装 / 首次使用且尚未写入凭证」时触发一次。**环境变量或 `~/.midu_keys` 已有 `MIDU_APP_SECRET` / `MIDU_USER_ID` 时跳过本流程，直接走 Write Workflow**；授权成功写入 `~/.midu_keys` 后，禁止再次索要手机号/验证码（除非业务返回 401/403 凭证失效）。
> 凭证持久化：必须写入本地文件 `~/.midu_keys`（勿依赖 `export`；子进程改不了父 shell 环境变量，命令结束即丢失）。

1. **判断是否需要授权**：环境变量已有 `MIDU_APP_SECRET` / `MIDU_USER_ID`，**或** `~/.midu_keys` 中已有对应字段 → 跳过全部授权步骤。两者皆无 → 进入下列步骤。
2. **提醒用户填写手机号**（仅支持手机号，不支持邮箱）。
3. 用户回复手机号后，**下发短信验证码**：
   ```bash
   python3 scripts/midu_auth.py --action send --mobile <手机号>
   ```
4. **提醒用户填写收到的验证码**。
5. 用户回复验证码后，**校验并获取 appSecret / userId**：
   ```bash
   python3 scripts/midu_auth.py --action verify --mobile <手机号> --sms_code <验证码>
   ```
6. 从响应取出 `appSecret`、`userId`，由脚本**自动写入 `~/.midu_keys`**（键名 `MIDU_APP_SECRET` / `MIDU_USER_ID`）。禁止只依赖 `export`。
7. 告知用户授权完成（已写入 `~/.midu_keys`），进入 Write Workflow；后续调用只走业务脚本，请求头自动从 env 或 `~/.midu_keys` 组装。

### Write Workflow（写作）

#### 参数说明

| 参数           | 类型   | 必填 | 说明                                                         |
| :------------- | :----- | :--- | :----------------------------------------------------------- |
| `--user_input` | string | 是   | 写作指令或补充要求                                           |
| `--thread_id`  | string | 否   | 多轮对话时传入上一次返回的 `thread_id`；首次省略，脚本自动生成 |
| `--api-key`    | string | 否   | appSecret（覆盖环境变量 `MIDU_APP_SECRET`）                  |
| `--user-id`    | string | 否   | userId（覆盖环境变量 `MIDU_USER_ID`）                        |
| `--timeout`    | int    | 否   | 超时秒数，默认 600；长文生成建议保持此默认值                 |
| `--pretty`     | flag   | 否   | 格式化输出 JSON                                              |

#### 调用示例

**首次写作（自动生成 thread_id）：**

```bash
python3 scripts/midu_write.py \
  --user_input "帮我写一篇关于人工智能发展前景的文章，约 800 字" \
  --pretty
```

**多轮补充修改（复用 thread_id）：**

```bash
python3 scripts/midu_write.py \
  --user_input "修改一下第二段，语气更正式一些" \
  --thread_id "上一次返回的 uuid 字符串" \
  --pretty
```

**显式传凭证（覆盖环境变量，优先级最高）：**

```bash
python3 scripts/midu_write.py \
  --user_input "..." \
  --api-key "<appSecret>" \
  --user-id "<userId>" \
  --pretty
```

### 输出格式

```json
{
  "thread_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "article_url": ["生成内容的 URL 列表"],
  "token_usage": 1234
}
```

- `thread_id`：无论服务端是否返回，脚本始终在输出中携带本次使用的 `thread_id`，请务必保存以用于后续多轮对话。
- `article_url`：生成文章的链接列表，可直接访问查看内容。

## 接口说明

### 授权接口

| 项 | 约定 |
| :-- | :-- |
| 下发验证码 | `POST https://api.midu.com/ability/auth/send/sms` |
| 校验并获取凭证 | `POST https://api.midu.com/ability/auth/mobile/verify` |
| Content-Type | `application/x-www-form-urlencoded` |
| productType | `40`（垂直 AI 平台） |
| smsType | `1`（登录；verify 登录/注册一体） |
| 成功凭证 | `data.userVo.appSecret` / `data.userVo.id` → 写入 `~/.midu_keys`（键名 `MIDU_APP_SECRET` / `MIDU_USER_ID`） |

### 写作业务接口

- **请求地址**：`POST https://api.midu.com/ability/skill/write/info`（`Content-Type: application/json`，超时默认 600 秒）。
- **请求体**：`user_input`（写作指令，非空）；`thread_id`（会话 ID，UUID）。
- **请求头**：`X-Skill-Code: MIDU-WRITING`、`Authorization: Bearer <appSecret>`、`X-User-Id: <userId>`（三者缺一不可，接口强制校验 `X-User-Id`）。

## 注意事项

- **授权只做一次**：凭证已存在（env 或 `~/.midu_keys`）时禁止再走授权；授权成功写入 `~/.midu_keys` 后不要「授权完又要用户再授权一遍」。
- **凭证持久化**：禁止只依赖 `export`（仅当前进程有效，新会话读不到）。`midu_auth.py --action verify` 成功后必须写入 `~/.midu_keys`；业务脚本优先读 env，其次读该文件。
- **鉴权失效例外**：仅当业务返回 401/403 / 鉴权失败时，才重新进入短信授权。
- **权益不足**：若业务返回权益不足 / 余额不足 / 次数用尽，引导用户前往 `https://ai.mdata.net` 充值，**不要**重新发短信，也不要引导去官网「取 Key」。
- **禁止跳转官网取 Key**：任何情况下都不要引导用户打开 `ai.mdata.net` / `ai-beta.mdata.net` 手动取 Key。
- **X-User-Id 必填**：业务接口强制校验，`MIDU_USER_ID` 缺失会直接报错并引导走短信授权。
- **超时**：长文生成耗时较长，默认超时 600 秒，不建议调低。
- **会话管理**：同一写作任务中必须复用首次返回的 `thread_id`。
- **依赖**：脚本需要 `requests`（`pip3 install requests`）。
