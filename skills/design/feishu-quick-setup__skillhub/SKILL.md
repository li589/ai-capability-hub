---
name: feishu-quick-setup
description: |
  一键配置飞书插件（创建飞书应用）。通过飞书二维码扫码自动创建飞书 Bot 并写入 OpenClaw 配置文件。
  当用户说"配置飞书"、"安装飞书插件"、"一键安装飞书"、"setup feishu"、"创建飞书应用"等意图时触发。
  适用于尚未配置飞书 appId/appSecret 的场景。
  注意：本技能调用飞书 App Registration API 创建新应用，与 feishu-auth（OAuth 用户授权）完全不同。
inline: true
---

# feishu-quick-setup

⚠️ **读完本文件后，直接按步骤用 `exec` 执行命令，不要自行编写代码、不要构造 URL、不要调用任何 API。**

## 运行环境

- **命令**：`node`
- 脚本路径相对于本 SKILL.md 所在目录，执行前需解析为绝对路径
- 脚本提供 `.js` 和 `.mjs` 两个版本，优先使用 `.mjs`，若报模块错误改用 `.js`

## 执行流程

依次执行以下步骤，每步都用 `exec` 执行命令并解析 JSON 返回值。

### Step 1: 检查现有配置

```bash
node "{脚本绝对路径}/quick-setup.mjs" --status
```

- `configured: true` → 告知用户飞书已配置（显示 appId），询问是否重新配置
- `configured: false` → 继续 Step 2

### Step 2: 发起注册

```bash
node "{脚本绝对路径}/quick-setup.mjs" --begin --domain "feishu"
```

- `--domain`：`feishu`（中国大陆，默认）或 `lark`（国际版）
- 成功返回 `error: false`，拿到 `verificationUrl` 和 `deviceCode`
- 失败返回 `error: true`，告知用户错误信息并停止

### Step 3: 展示链接给用户

将 Step 2 返回的 `verificationUrl` **原样**展示给用户：

> 请点击以下链接完成飞书授权：
> {verificationUrl}
>
> 点击后在飞书中点击"确认创建"即可。

**严禁修改、替换或自行构造链接。正确的链接格式为 `https://open.feishu.cn/page/openclaw?user_code=...`。**
**严禁提及二维码或扫码，本流程只通过链接完成。**

展示链接后**立即进入 Step 4 轮询**，不要等用户回复。

### Step 4: 轮询等待确认

展示链接后立即执行此命令。脚本会在内部自动每 5 秒轮询一次，直到用户完成授权或超时（默认 5 分钟）：

```bash
node "{脚本绝对路径}/quick-setup.mjs" --poll --wait --timeout 300
```

此命令会阻塞等待，直到返回结果：
- `status: "completed"` → 拿到 `appId` 和 `appSecret`，进入 Step 5
- `status: "error"` → 告知用户错误信息
  - `expired_token` → 链接已过期，需从 Step 2 重新开始
  - `access_denied` → 用户拒绝了创建
- `status: "timeout"` → 等待超时，建议用户重试

### Step 5: 保存配置

```bash
node "{脚本绝对路径}/quick-setup.mjs" --save --app-id "APP_ID" --app-secret "APP_SECRET" --domain "feishu"
```

将 APP_ID 和 APP_SECRET 替换为 Step 4 返回的值。

- `success: true` → **将返回 JSON 中的 `message` 字段内容原样展示给用户**（已包含权限配置链接和说明）
- `success: false` → 告知用户写入失败的原因

## 禁止事项

- **禁止**自行调用飞书 API 或构造任何 URL
- **禁止**使用 feishu-auth 或 OAuth 授权流程（那是用于已有应用的用户授权，不是创建应用）
- **禁止**只描述不执行，必须直接用 `exec` 执行上面的命令
- **禁止**跳过任何步骤
- **禁止**修改脚本返回的 verificationUrl
