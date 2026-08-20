---

name: 攻击性JWT
slug: offensive-jwt
version: 1.0.0
displayName: 攻击性JWT
description: >
  攻击性JWT专用技能，帮助AI Agent高效完成相关任务。
summary: "攻击性JWT专用技能，帮助AI Agent高效完成相关任务。"
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





## Overview

Comprehensive JWT attack checklist for offensive security engagements. Follow steps in order; apply each technique to the current target context and track which items have been completed.

## Quick Reference: Misconfigurations to Check

- Algorithm set to `none` — signature verification bypassed entirely
- Algorithm switching between `RSA` and `HMAC` (confusion attack)
- Weak or guessable HMAC secret (brute-forceable)
- `kid`, `jku`, `jwk`, `x5u` header parameters accepted without validation
- Expired or tampered tokens accepted by server
- Sensitive data stored unencrypted in payload

Useful tool: [JWT Tool](https://github.com/1991513ccie-png)

## Mechanisms

JWTs (RFC 7519) consist of three Base64URL-encoded parts: `header.payload.signature`.

**Signing algorithms:**

| Algorithm | Type | Notes |
|