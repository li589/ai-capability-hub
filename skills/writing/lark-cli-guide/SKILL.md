---
name: lark-cli-guide
description: lark-cli 飞书命令行工具使用指南，涵盖安装配置与日常使用。当用户说「安装 lark-cli」「配置 lark-cli」「lark-cli 安装」「飞书 CLI 安装」「lark-cli 环境搭建」或遇到 lark-cli command not found 时，可参考此技能完成安装配置。当涉及飞书文档读写、知识库访问、云盘上传下载、消息发送等飞书相关操作时，也可参考此技能。
install_source: official
install_method: download
skill_id: f0447c9a-0436-41dc-ab28-736e84baa962
enabled_at: 1787232740832
version: 1.0.0
name_zh: 飞书CLI
---

# lark-cli 飞书命令行工具

lark-cli 可用于飞书相关操作的命令行处理，可作为日常飞书操作的一种工具选择。

## 环境前置检查（每次会话首次使用 lark-cli 前必须执行）

在执行任何 lark-cli 命令之前，先完成以下检查：

```bash
lark-cli --version && lark-cli auth status
```

判断逻辑：

| 检查结果 | 处理方式 |
|---|---|
| `command not found` | 进入下方「安装与配置」章节，引导用户完成从零安装 |
| 版本输出正常但 auth status 报错（未登录/token 过期） | 执行 `lark-cli auth login`；lark-cli 返回授权链接时，仅在当前安全会话中提供给授权本人使用，避免转发或公开，并由授权本人在浏览器完成认证 |
| 版本输出正常且 auth status 有效 | 环境就绪，继续执行用户请求的 lark-cli 命令 |

---

## 安装与配置

引导用户完成飞书 lark-cli 从零到可用的全流程。按顺序执行以下步骤，每步确认通过后再进入下一步。

### Step 1: 检测 Node.js 环境

```bash
node --version
```

- 如果输出 v18+ 版本号 → 跳到 Step 2
- 如果 command not found → 执行 Node.js 安装引导

#### Node.js 安装引导

根据用户操作系统选择方案（先问用户系统，或通过 `uname -s` 判断）：

**Linux / WSL（推荐 nvm）：**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc   # 或 source ~/.zshrc
nvm install 22
nvm use 22
```

**macOS（推荐 Homebrew）：**

```bash
brew install node@22
```

安装后再次验证：

```bash
node --version && npm --version
```

确认 node >= v18、npm 可用后继续。

### Step 2: 安装 lark-cli

```bash
npm install -g @larksuite/cli
```

验证安装：

```bash
lark-cli --version
```

如果提示权限不足（EACCES），引导用户：
- 推荐使用 nvm 管理 Node.js，避免全局安装权限问题
- 或修改 npm 全局目录：`npm config set prefix ~/.npm-global` 并将 `~/.npm-global/bin` 加入 PATH

### Step 3: 初始化应用配置

lark-cli 需要绑定一个飞书自建应用的凭证才能工作。

#### 3.1 获取应用凭证

告知用户需要在 [飞书开放平台](https://open.feishu.cn/app) 创建或选择一个自建应用，获取：
- App ID（格式：cli_xxxxx）
- App Secret

#### 3.2 执行初始化

```bash
lark-cli config init
```

交互式引导中：
- brand 选择 `feishu`（国内版）或 `lark`（海外版）
- 输入 App ID
- App Secret 通过 stdin 传入（不会明文显示）

非交互式写法（适合自动化）：

```bash
echo "YOUR_APP_SECRET" | lark-cli config init --app-id cli_xxxxx --app-secret-stdin --brand feishu
```

#### 3.3 验证配置

```bash
lark-cli config show
```

确认输出中包含正确的 app_id 和 brand。

### Step 4: 登录认证

```bash
lark-cli auth login
```

执行后会输出一个授权链接（Device Flow）。该链接仅在当前安全会话中提供给授权本人使用，避免转发或公开；引导授权本人：
1. 在浏览器中打开该链接
2. 使用飞书账号登录并授权
3. 授权完成后终端会自动完成认证

验证登录状态：

```bash
lark-cli auth status
```

确认输出中 token 状态为有效。

**注意：** 会话有效期约 7 天，过期后需重新执行 `lark-cli auth login`。

### Step 5: 环境验证

```bash
lark-cli doctor
```

所有 check 项应为 pass。常见 warn 及处理：
- `cli_update`：有新版本可用，执行 `lark-cli update`
- `scope_missing`：应用权限不足，需在飞书开放平台为应用添加对应 API 权限

### 故障排查速查

| 问题 | 解决方案 |
|---|---|
| `lark-cli: command not found` | 检查 npm global bin 是否在 PATH：`npm config get prefix` |
| `EACCES permission denied` | 使用 nvm 管理 Node.js，或 `npm config set prefix ~/.npm-global` |
| `auth login` 无响应 | 确认网络可访问 open.feishu.cn；尝试 `lark-cli auth login --verbose` |
| token 过期 | 重新执行 `lark-cli auth login` |
| 切换应用 | `lark-cli config remove` 后重新 `lark-cli config init` |

---

## 工具选择规则

| 场景 | 可用工具 | 说明 |
|---|---|---|
| 读取飞书文档/知识库 | **lark-cli** | `lark-cli docs +fetch --doc "URL" --format pretty`，保留完整超链接和文档结构 |
| 文档变更检测 | **lark-cli** | `lark-cli wiki +node-get --node-token "URL"` 返回 `obj_edit_time` 和 `updated_at` |
| 列出子文档节点 | **lark-cli** | `lark-cli wiki +node-list --parent-node-token "TOKEN" --space-id "SPACE_ID" --page-all` |
| 搜索群聊/发送消息 | **lark-cli** | `lark-cli im +chat-search` / `lark-cli im +send` |
| 云盘上传/下载/导出 | **lark-cli** | `lark-cli drive +upload` / `+download` / `+export` |
| 添加文档评论 | **lark-cli** | `lark-cli drive +add-comment --doc "URL" --content '[...]'` |
| 查看日历/任务/联系人 | **lark-cli** | `lark-cli calendar` / `lark-cli task` / `lark-cli contact` |
| 多维表格操作 | **lark-cli** | `lark-cli base` 相关命令（备用：飞书 MCP bitable） |
| 飞书 MCP（可选） | **飞书 MCP** | 可在 lark-cli 不适用时按实际情况选择 |

## 常用命令速查

| 操作 | 命令 |
|---|---|
| 读取文档 | `lark-cli docs +fetch --doc "URL" --format pretty` |
| 检测文档变更 | `lark-cli wiki +node-get --node-token "URL"` |
| 列出子文档节点 | `lark-cli wiki +node-list --parent-node-token "TOKEN" --space-id "SPACE_ID" --page-all` |
| 搜索群聊 | `lark-cli im +chat-search --query "关键词"` |
| 获取群聊消息 | `lark-cli im +chat-messages-list --chat-id "ID" --start "START" --end "END" --sort asc` |
| 上传文件到云盘 | `lark-cli drive +upload --file ./file.pdf --folder-token "FOLDER"` |
| 导出文档为 PDF | `lark-cli drive +export --doc "DOC_ID" --doc-type docx --file-extension pdf --output-dir ./` |
| 环境检查 | `lark-cli doctor` |

## 配置与登录备注

- 版本 v1.0.49+，品牌 feishu，支持多个飞书子能力模块
- 飞书应用凭证通过环境变量由用户自行配置，不要硬编码
- 首次使用或会话过期时执行登录命令；lark-cli 返回授权链接时，仅在当前安全会话中提供给授权本人使用，避免转发或公开，并由授权本人在浏览器中完成授权
- 会话有效期约 7 天，过期后需重新登录
- 消息搜索功能仅支持 `--as user` 身份
- 评论的 `--content` 参数必须是 JSON 数组格式
