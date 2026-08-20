---

name: 开放重定向
slug: open-redirect
version: 1.0.0
displayName: 开放重定向
description: >
  开放重定向专用技能，帮助AI Agent高效完成相关任务。
summary: "开放重定向专用技能，帮助AI Agent高效完成相关任务。"
license: MIT
category: 安全与渗透测试
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





# SKILL: Open Redirect Vulnerabilities

## Metadata
- **Skill Name**: open-redirect
- **Folder**: offensive-open-redirect
- **Source**: https://github.com/1991513ccie-png

## Description
Open redirect vulnerability checklist: parameter identification, bypass techniques (URL encoding, double slashes, CRLF injection, protocol handlers), chaining with OAuth/SSRF, and impact escalation paths. Use for web app testing and bug bounty open redirect discovery.

## Trigger Phrases
Use this skill when the conversation involves any of:
`open redirect, URL redirect, redirect bypass, URL encoding bypass, CRLF, protocol handler, redirect chain, OAuth redirect, SSRF chain, open redirection`

## Instructions for Claude

When this skill is active:
1. Load and apply the full methodology below as your operational checklist
2. Follow steps in order unless the user specifies otherwise
3. For each technique, consider applicability to the current target/context
4. Track which checklist items have been completed
5. Suggest next steps based on findings

