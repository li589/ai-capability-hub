# 飞书CLI安装指南

## 目录

1. [安装前准备](#安装前准备)
2. [安装步骤](#安装步骤)
3. [安装后验证](#安装后验证)
4. [开始使用](#开始使用)

---

## 安装前准备

### 系统要求

- **操作系统**: Windows、macOS、Linux
- **Node.js**: 版本 16.0 或更高
- **包管理器**: npm 或 yarn
- **网络**: 能够访问 npm registry

### 检查环境

运行环境检测脚本：

```bash
python scripts/environment_checker.py
```

检测项包括：
- ✅ Node.js 版本
- ✅ npm/yarn 可用性
- ✅ 网络连接
- ✅ 系统权限

---

## 安装步骤

### 方式一：一键安装（推荐）

运行一键安装脚本，自动完成所有步骤：

```bash
python scripts/one_click_installer.py
```

### 方式二：分步安装

如果需要更精细的控制，可以分步执行：

#### 步骤1：安装 lark-cli

```bash
npm install -g @larksuite/cli
```

或使用 yarn：

```bash
yarn global add @larksuite/cli
```

#### 步骤2：安装 Skills

```bash
npx skills add https://github.com/larksuite/cli -y -g
```

#### 步骤3：初始化配置

```bash
lark-cli config init --new
```

这将创建一个新的飞书应用，并配置 CLI 使用该应用。

#### 步骤4：用户授权（可选）

如果需要以你的身份操作飞书，需要完成用户授权：

```bash
lark-cli auth login
```

打开显示的链接，在飞书中确认授权即可。

**注意**：不授权也可以使用部分功能，但无法访问你的个人数据（如日程、私信、收件箱）。

---

## 安装后验证

### 查看帮助

```bash
lark-cli help
```

### 查看登录状态

```bash
lark-cli auth status
```

### 查看配置

```bash
lark-cli config list
```

---

## 开始使用

### 在 AI 工具中使用

安装完成后，在你的 AI Agent 工具（如 Trae、Cursor、Codex、Claude Code）中：

1. 重启 AI 工具（确保 Skills 完整加载）
2. 发送自然语言指令：
   - "帮我创建一篇云文档"
   - "查看我今天的日程"
   - "搜索包含'项目'的群聊"

### 命令行中使用

```bash
# 查看所有命令
lark-cli help

# 查看具体命令帮助
lark-cli <command> --help

# 查看接口详情
lark-cli schema
```

---

## 下一步

- 📖 阅读 [常见问题](common_issues.md)
- 🔧 遇到问题？查看 [故障排查](troubleshooting.md)
- 📚 查看官方文档：https://github.com/larksuite/cli

---

## 相关链接

- [飞书CLI GitHub仓库](https://github.com/larksuite/cli)
- [飞书CLI官方文档](https://www.feishu.cn/content/article/7623291503305083853)
- [飞书开放平台](https://open.feishu.cn/)
