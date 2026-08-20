---
name: 攻击安全技能库
slug: claude-red
version: 1.0.0
displayName: 攻击安全技能库
description: >
  ClaudeRed专用技能，帮助AI Agent高效完成相关任务。
summary: "ClaudeRed专用技能，帮助AI Agent高效完成相关任务。"
license: MIT
category: 开发者工具
framework:
  - Claude Code
  - Codex
  - Hermes Agent
  - OpenClaw
  - QClaw
  - WorkBuddy
platform: multi-platform
homepage: "https://github.com/1991513ccie-png"
repository: "https://github.com/1991513ccie-png"
---



# Claude-Red — 攻击安全技能库

## 概述

Claude-Red 是一个精心策划的攻击安全技能库，专为 Claude Skills 系统设计。每个技能都是一个结构化的 `SKILL.md` 文件，为特定攻击面提供专家级方法论——从 SQLi 到 shellcode，从 EDR 规避到 ADCS 滥用。

**核心定位**：将 Claude 从聊天机器人变成具备攻击能力的安全操作员。技能按需加载，无需为不使用的技能支付上下文成本。

**适用场景**：授权红队演练、Bug Bounty 分诊、安全研究、CTF 备战、培训操作员、系统化攻击面探索。

## 适用场景

- 需要特定攻击面的专家级方法论和工具链
- 执行渗透测试需要标准化操作流程
- 进行漏洞研究和利用开发
- 需要 58 个专业安全模块中任意一个的深度指导

## 使用方法

### 安装方式

```bash
# Claude Skills 系统（推荐）
git clone https://github.com/SnailSploit/claude-red ~/.claude/skills/claude-red

# 或仅安装特定类别
git clone --filter=blob:none --sparse https://github.com/SnailSploit/claude-red
cd claude-red && git sparse-checkout set Skills/web Skills/active-directory
```

### 按需加载

Claude 会根据对话触发器自动加载匹配技能（例如提到 SQLi 会加载 `offensive-sqli`）。

## 技能分类索引

### Web 应用（16 个技能）
SQL 注入、XSS、SSRF、SSTI、XXE、IDOR、文件上传、RCE、反序列化、竞态条件、请求走私、开放重定向、参数污染、GraphQL、WAF 绕过、业务逻辑

### 认证与身份（2 个技能）
JWT 攻击（alg:none、密钥混淆、密钥破解）、OAuth 滥用（开放重定向、令牌泄露、PKCE 绕过）

### Active Directory（1 个技能）
Kerberoasting、ASREProast、ACL 滥用、ADCS ESC1-15、委派、持久化、混合 AAD

### 无线安全（13 个技能）
802.11、WPA2/3、EAP、WPS、Evil Twin、BLE、Zigbee、Z-Wave、LoRa、sub-GHz

### 云安全（1 个技能）
AWS/Azure/GCP —— 权限提升、IMDS、跨账户、持久化、CSPM 规避

### 移动安全（1 个技能）
Android + iOS 渗透（Frida、证书固定、存储、生物识别、深度链接）

### IoT 与嵌入式（1 个技能）
硬件侦察、固件、RTOS、ICS/OT、MQTT/CoAP

### 基础设施与红队（7 个技能）
初始访问、EDR 规避、Shellcode、键盘记录架构、Windows 缓解措施、Windows 边界突破

### 漏洞开发（6 个技能）
栈/堆、ROP 链、缓解措施、崩溃分析、TOCTOU

### 模糊测试与漏洞研究（4 个技能）
libFuzzer、AFL++、漏洞分类、Bug 识别

### 侦察（2 个技能）
OSINT 工具链、OSINT 方法论

### AI 安全（1 个技能）
Prompt 注入、越狱、RAG 投毒

### 工具（2 个技能）
快速分诊、专业渗透报告

## 常见问题与陷阱

| 问题 | 解决方案 |
|------|----------|
| 不确定从哪个技能开始 | 使用分类索引表按攻击面定位 |
| 技能加载过多 | 仅按需加载，对话触发器自动管理 |
| 需要组合多个技能 | 从基础设施类开始，逐步深入具体攻击面 |

## 验证清单

- [ ] 已确认目标资产在授权范围内
- [ ] 选择的技能与当前攻击面匹配
- [ ] 已理解技能中的安全边界和法律约束
- [ ] 测试报告格式符合 CVSS 标准