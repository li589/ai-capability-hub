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





# SKILL: Open Redirect — Expert Attack Playbook

> **AI LOAD INSTRUCTION**: Open redirect techniques. Covers parameter-based redirects, JavaScript sinks, filter bypass, and chaining with phishing, CSRF Referer bypass, OAuth token theft, and SSRF. Often underrated but critical for phishing and as a building block in multi-step exploit chains.

## 1. CORE CONCEPT

Open redirect occurs when an application redirects users to a URL derived from user input without validation. The trusted domain acts as a "launchpad" for phishing or token theft.

```
https://trusted.com/redirect?url=https://evil.com
→ User sees trusted.com in the link → clicks → lands on evil.com
```

