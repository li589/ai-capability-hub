---

name: 攻击性Active Directory
slug: offensive-active-directory
version: 1.0.0
displayName: 攻击性Active Directory
description: >
  攻击性Active Directory专用技能，帮助AI Agent高效完成相关任务。
summary: "攻击性Active Directory专用技能，帮助AI Agent高效完成相关任务。"
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





# Active Directory — Offensive Testing Methodology

## Quick Workflow

1. Recon AD structure offline (BloodHound, ADExplorer snapshot) — minimize live queries
2. Harvest creds via poisoning, Kerberoasting, ASREProast, or LSASS where allowed
3. Map attack paths to Domain Admin / Enterprise Admin / Tier 0
4. Execute path with lowest detection cost, validate at each hop
5. Establish persistence and document every action with timestamps

