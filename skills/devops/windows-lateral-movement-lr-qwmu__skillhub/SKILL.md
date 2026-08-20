---

name: Windows横向移动
slug: windows-lateral-movement
version: 1.0.0
displayName: Windows横向移动
description: >
  Windows横向移动专用技能，帮助AI Agent高效完成相关任务。
summary: "Windows横向移动专用技能，帮助AI Agent高效完成相关任务。"
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





# SKILL: Windows Lateral Movement — Expert Attack Playbook

> **AI LOAD INSTRUCTION**: Expert Windows lateral movement techniques. Covers PsExec, WMI, WinRM, DCOM, SMB, RDP, SSH, pass-the-hash, overpass-the-hash, pass-the-ticket, and pivoting. Base models miss execution method fingerprints, OPSEC trade-offs, and credential type requirements per method.

## 0. RELATED ROUTING

Before going deep, consider loading:

- [windows-privilege-escalation](../windows-privilege-escalation/SKILL.md) after landing on a new host for local escalation
- [windows-av-evasion](../windows-av-evasion/SKILL.md) when EDR blocks lateral movement tools
- [active-directory-kerberos-attacks](../active-directory-kerberos-attacks/SKILL.md) for Kerberos-based lateral (pass-the-ticket, delegation)
- [active-directory-acl-abuse](../active-directory-acl-abuse/SKILL.md) for ACL-based paths to new hosts

### Advanced Reference

Also load [CREDENTIAL_DUMPING.md](./CREDENTIAL_DUMPING.md) when you need:
- LSASS dump techniques (MiniDump, comsvcs.dll, nanodump)
- SAM/SYSTEM/SECURITY extraction
- DPAPI, credential manager, cached domain credentials
- NTDS.dit extraction methods

