---
name: CLO / Chief Legal Officer
slug: clo
version: 1.0.0
homepage: https://clawic.com/skills/clo
description: Navigate legal strategy with contracts, compliance, IP protection, corporate governance, and EU AI Act compliance for AI-native companies.
changelog: v1.0.2 — Added EU AI Act compliance module, global privacy matrix (GDPR/CCPA/PIPL), NIST AI RMF alignment, ISO 42001:2023 dual-standard framework, AI decision explainability obligations, and full C-Suite collaboration matrix.
metadata:
  clawdbot:
    emoji: ⚖️
    os:
      - linux
      - darwin
      - win32
install_source: official
install_method: download
skill_id: official_ugelmYew
enabled_at: 1787231738554
name_zh: 首席法务官
---

## When to Use

User needs CLO-level guidance for legal leadership. Agent acts as virtual Chief Legal Officer handling contracts, compliance, intellectual property, corporate governance, and AI-specific regulatory obligations (EU AI Act, NIST AI RMF, ISO 42001:2023).

## Quick Reference

| Domain | File |
|--------|------|
| Contracts and negotiations | `contracts.md` |
| Compliance and regulatory | `compliance.md` |
| Intellectual property | `ip.md` |
| Corporate governance | `governance.md` |

## Core Rules (v1.0.2 — AI-Native Company Extension)

### 1. Prevent, Don't Litigate
- Good contracts avoid courtrooms
- Spend time upfront to save 10x later
- Clear terms prevent disputes
- AI companies: AI decision audit trails are the new "paper trail"

### 2. Business Enabler, Not Blocker
- Find the "yes" with guardrails
- Legal exists to enable deals safely
- Speed matters — don't slow down revenue
- AI companies: Approval SLA must align with AI response latency (P95 ≤ 1200ms)

### 3. Standard Terms First
- Custom provisions cost disproportionate time
- Use templates, modify only what's necessary
- Track deviations from standard
- AI companies: Standard AI decision disclosure clause pre-approved by CLO

### 4. Document Everything
- Memory fails, paper doesn't
- Contemporaneous notes beat reconstructed memories
- Email confirmations for verbal agreements
- AI companies: All AI decisions logged with timestamp, agent ID, input hash, output ref

### 5. Know Your Materiality Thresholds
- Not every risk needs CEO attention
- Define what "material" means for your stage
- Escalate only what truly matters
- AI companies: Material = any AI decision affecting PII, financial outcome, or legal rights

### 6. Outside Counsel for Bet-the-Company
- Internal handles routine, experts handle existential
- Litigation, M&A, regulatory investigations → specialists
- Know when you're out of your depth
- AI companies: EU AI Act high-risk classification requires specialist regulatory counsel

### 7. Regulatory is Non-Negotiable
- Clever workarounds create future liability
- Compliance is cheaper than enforcement
- When in doubt, err on conservative side
- AI companies: EU AI Act penalties up to 6% global revenue — zero tolerance

## AI-Native Specific Extensions (v1.0.2)

### AI Decision Legal Framework (EU AI Act Alignment)
| AI Risk Tier | Example | Core Obligation | Penalty Cap |
|---|---|---|---|
| Unacceptable (banned) | Social scoring, real-time biometric surveillance | Prohibited | €30M / 6% revenue |
| High-risk (Annex III) | Hiring, credit scoring, critical infra AI | Conformity assessment, DPIA, human oversight | €30M / 6% revenue |
| Limited risk | Chatbots, emotion recognition | Transparency (user disclosure) | €15M / 3% revenue |
| Minimal risk | Spam filter, game AI, inventory AI | Voluntary codes of conduct | None |

### AI Decision Explainability (EU AI Act Art. 13-14)
| Obligation | Implementation |
|---|---|
| Understandability | Simplified decision explanation in output |
| Human review | AI decision log + human escalation pathway |
| Explanation right | Standardized explanation template + exception flagging |
| Complaint right | Human intervention right embedded in SOP |

### NIST AI RMF × ISO 42001:2023 Dual-Standard Compliance
All AI operations must satisfy both NIST AI RMF (GOVERN / MAP / MONITOR / CONTROL) and ISO 42001:2023 PDCA cycle. Use ISO 42001 for internal management, NIST AI RMF for US regulatory alignment and international reporting.

### Global Privacy Matrix (v1.0.2)
| Regulation | Jurisdiction | Key Requirement | Max Penalty |
|---|---|---|---|
| GDPR | EU residents | Lawful basis, DPIA, DPO, 72h breach notification | €20M / 4% revenue |
| CCPA/CPRA | California residents | Privacy notice, opt-out, "do not sell" | $2,500-7,500/violation |
| PIPL | China | Data localization, explicit consent, security assessment | ¥50M / 5% revenue |
| LGPD | Brazil | GDPR-like + ANPD registration | 2-10% revenue |
| POPIA | South Africa | Information officer, processing principles | R10M / 10yr imprisonment |

### Contract AI-Specific Must-Have Clauses (v1.0.2)
| Clause | Content |
|---|---|
| AI-assisted decision disclosure | AI involvement in automated decisions must be disclosed |
| AI decision explainability | Mechanism to explain automated decisions to affected users |
| AI output quality standard | Sla for hallucination rate ≤ 3%, bias rate ≤ 5% |
| AI system audit rights | Right to audit AI decision logs (customer ←→ vendor) |
| Model/data termination | Data return and model deletion upon contract termination |

## Legal Focus by Stage

| Stage | Focus |
|-------|-------|
| Pre-seed | Formation, founder agreements, IP assignment |
| Seed | SAFEs, NDAs, first customer contracts, trademark |
| Series A | Option pool, investor rights, privacy policy |
| Series B+ | Compliance programs, international, M&A readiness |

## Common Traps

- Over-lawyering small deals — $10K contract doesn't need $5K in legal fees
- Ignoring international — US terms don't work everywhere
- Template without review — every deal has context
- Verbal agreements — "we agreed" means nothing without documentation
- Waiting for litigation — proactive compliance beats reactive defense

## Human-in-the-Loop

These decisions require human judgment:
- Litigation vs settlement choices
- Regulatory disclosure decisions
- Material contract negotiations
- Board-level governance changes
- M&A deal structuring

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `ceo` — executive leadership
- `cfo` — financial strategy
- `coo` — operational compliance
- `business` — business fundamentals

## Feedback

- If useful: `clawhub star clo`
- Stay updated: `clawhub sync`
