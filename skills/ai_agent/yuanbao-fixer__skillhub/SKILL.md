---
name: yuanbao-fixer
slug: yuanbao-fixer
description: 元宝插件安装与配置技能。用于在 QClaw 环境下安装和配置 openclaw-plugin-yuanbao 插件。触发场景：用户需要安装元宝插件、配置元宝凭证、修复元宝插件失效问题，或直接说"安装元宝插件"、"修复元宝插件"。
version: 1.0.0
author: QClaw
license: MIT
keywords: [元宝, yuanbao, 插件安装, 配置修复, 腾讯元宝]
---

# 元宝插件安装与配置技能

## 背景

QClaw 环境下，`openclaw` 不在全局 PATH，且 `openclaw plugins install` 可能因 npm 问题失败。本技能通过 `gateway.config.patch` 工具直接写入配置，绕过 CLI 限制。

## 首次使用配置

在使用本技能前，您需要准备以下凭证：

| 参数 | 说明 | 获取方式 |
|------|------|----------|
| `appKey` | 元宝应用 Key | 从腾讯元宝开放平台获取 |
| `appSecret` | 元宝应用 Secret | 从腾讯元宝开放平台获取 |

> **提示**：请前往 [腾讯元宝开放平台](https://yuanbao.tencent.com/) 申请应用凭证。

## 修复流程

### 方案 A：config.patch 写入（推荐）

调用 gateway 工具，**替换 `<YOUR_APP_KEY>` 和 `<YOUR_APP_SECRET>` 为您的实际凭证**：

```json
{
  "action": "config.patch",
  "raw": {
    "plugins": {
      "allow": ["wechat-access", "qclaw-plugin", "openclaw-qqbot", "skill-interceptor", "queue-guard", "lossless-claw", "memory-tencentdb", "openclaw-plugin-yuanbao"],
      "entries": {
        "openclaw-plugin-yuanbao": { "enabled": true, "config": {} }
      }
    },
    "channels": {
      "yuanbao": {
        "enabled": true,
        "appKey": "<YOUR_APP_KEY>",
        "appSecret": "<YOUR_APP_SECRET>"
      }
    }
  },
  "note": "元宝插件配置已写入，插件已启用"
}
```

Gateway 自动热加载（SIGUSR1），无需手动重启。

### 方案 B：手动安装（方案 A 失败时）

执行 scripts/install-plugin.sh 脚本：

```bash
bash scripts/install-plugin.sh
```

脚本会：
1. 下载插件 tarball
2. 解压到 extensions 目录
3. 安装依赖（uuid, ws, protobufjs, cos-nodejs-sdk-v5）
4. 提示用方案 A 写入配置

### 验证

调用 gateway 工具验证配置：

```json
{ "action": "config.get", "path": "plugins.entries.openclaw-plugin-yuanbao.enabled" }
```

应返回 `true`。

## 关键路径

| 项目 | 路径 |
|-----|------|
| 配置文件 | `~/.qclaw/openclaw.json` |
| 插件目录 | `~/Library/Application Support/QClaw/openclaw/config/extensions/openclaw-plugin-yuanbao` |
| openclaw wrapper | `~/Library/Application Support/QClaw/openclaw/config/skills/qclaw-openclaw/scripts/openclaw-mac.sh` |
