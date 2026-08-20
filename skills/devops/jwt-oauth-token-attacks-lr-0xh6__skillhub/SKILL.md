---

name: JWT/OAuth令牌攻击
slug: jwt-oauth-token-attacks
version: 1.0.0
displayName: JWT/OAuth令牌攻击
description: >
  JWT/OAuth令牌攻击专用技能，帮助AI Agent高效完成相关任务。
summary: "JWT/OAuth令牌攻击专用技能，帮助AI Agent高效完成相关任务。"
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





# SKILL: JWT and OAuth 2.0 Token Attacks — Expert Attack Playbook

> **AI LOAD INSTRUCTION**: Expert authentication token attacks. Covers JWT cryptographic attacks (alg:none, RS256→HS256, secret crack, kid/jku injection), OAuth flow attacks (CSRF, open redirect, token theft, implicit flow abuse), PKCE bypass, and token leakage via Referer/logs. This is critical for modern web applications.

## 0. RELATED ROUTING

Use this file for token-centric attacks and flow abuse. Also load:

- [oauth oidc misconfiguration](../oauth-oidc-misconfiguration/SKILL.md) for redirect URI, state, nonce, PKCE, and account-binding validation
- [cors cross origin misconfiguration](../cors-cross-origin-misconfiguration/SKILL.md) when browser-readable APIs or token leakage may exist cross-origin
- [saml sso assertion attacks](../saml-sso-assertion-attacks/SKILL.md) when the target uses enterprise SSO outside OAuth/OIDC

