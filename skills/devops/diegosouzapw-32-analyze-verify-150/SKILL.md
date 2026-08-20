---
name: 32-analyze-verify-150
description: "[32] ANALYZE. Ensure every critical claim has verifiable evidence with confidence levels. Each fact must have source + confidence percentage. If confidence <85%, enter Loop150 to find more sources. Use for critical decisions, factual claims, legal/compliance work, or any situation where unverified claims are dangerous."
install_source: official
install_method: download
skill_id: official_KmQVFVl5
enabled_at: 1787231743504
version: 1.0.0
name_zh: 法律验证助手
---

# Analyze-Verify 150 Protocol

**Core Principle:** No claim without proof. Every critical fact needs: source + confidence level. If unsure, keep digging until confident or escalate to user.

## What This Skill Does

When you invoke this skill, you're asking AI to:
- **Source every claim** — Trace facts to verifiable sources
- **Quantify confidence** — Express certainty as percentage
- **Verify independently** — Cross-check from multiple sources
- **Loop until confident** — Keep researching if <85% confidence
- **Escalate when stuck** — Ask user if sources exhausted

## The 150% Proof Rule

| Dimension | 100% Core | +50% Enhancement |
|-----------|-----------|------------------|
| **Source** | Primary source identified | + Independent confirmation |
| **Confidence** | Percentage stated | + Reasoning documented |
| **Verification** | Single source check | + Multi-source cross-validation |
| **Gaps** | Note uncertainties | + Active Loop150 to fill gaps |

## Confidence Level Framework

| Level | % Range | Description | Action Required |
|-------|---------|-------------|-----------------|
| **Verified** | 95-100% | Multiple primary sources, no contradictions | Use in critical decisions |
| **Strong** | 85-94% | Reliable sources, minor uncertainties | Safe for most purposes |
| **Moderate** | 75-84% | Limited sources, some gaps | Flag for verification |
| **Weak** | 50-74% | Insufficient evidence, major gaps | Do not use without confirmation |
| **Insufficient** | <50% | Contradictory or missing | Reject, research further |

## When to Use This Skill

- **Critical decisions** — Where wrong facts cause real damage
- **Legal/compliance** — Where accuracy has legal implications
- **Architecture decisions** — Where claims drive major choices
- **Stakeholder communication** — Where credibility matters
- **Any high-stakes claim** — When you can't afford to be wrong

## Execution Protocol

### Step 1: CLAIM FORMULATION
State the fact clearly:
```
🔍 **Claim:** [Precise factual statement]
**Context:** [Why this matters]
**Critical Level:** [High/Medium/Low]
```

### Step 2: PRIMARY SOURCE
Find the original source:
- Locate primary evidence
- Verify authenticity
- Extract direct quote/data

### Step 3: SECONDARY CONFIRMATION
Find independent corroboration:
- Different source type
- Cross-reference data
- Check consistency

### Step 4: CONFIDENCE ASSESSMENT
Calculate confidence:
```
**Evidence Evaluation:**
├── Primary Source: [Quality assessment]
├── Secondary Sources: [Count and quality]
├── Contradictions: [Any found?]
└── Gaps: [What's missing?]

**Confidence:** [X]%
**Reasoning:** [Why this percentage]
```

### Step 5: DECISION
```
Confidence ≥85%? 
├─ YES → Use fact with stated confidence
└─ NO → Enter Loop150
```

## Loop150 Continuous Verification

When confidence <85%:

```
🔄 **LOOP150 ACTIVATED** (Current: [X]%)

ITERATION 1: EXPAND SOURCES
├── Identify new source types
├── Use alternative research methods
├── Broaden search scope
↓
ITERATION 2: DEEPER ANALYSIS
├── Drill into source details
├── Verify source credibility
├── Check contextual factors
↓
ITERATION 3: CROSS-VALIDATION
├── Compare against known facts
├── Test logical consistency
├── Seek expert corroboration
↓
RECALCULATE: New confidence = [Y]%

Continue loop until:
├─ ≥90% achieved → EXIT, proceed with confidence
└─ Sources exhausted → ESCALATE to user
```

## Source Quality Criteria

**🔍 RELIABILITY FACTORS:**
- **Authority:** Official, expert, or primary source?
- **Currency:** How recent and up-to-date?
- **Objectivity:** Free from bias or agenda?
- **Methodology:** Sound research methods used?
- **Independence:** Not dependent on other sources?

**📊 EVIDENCE STRENGTH:**
| Type | Strength | Example |
|------|----------|---------|
| **Primary** | High | Original data, first-hand |
| **Secondary** | Medium | Analysis of primary |
| **Tertiary** | Low | Summaries, reviews |
| **Statistical** | High | Large sample, proper method |
| **Anecdotal** | Variable | Personal experience |

## Output Format

```
🔍 **PROOF-GRADE 150 VERIFICATION**

**Claim:** [Precise factual statement]

**Primary Source:** 
- [File/location/date]
- "[Direct quote or data]"

**Secondary Sources:**
- [Source 2]: [Confirmation]
- [Source 3]: [Confirmation]

**Confidence Level:** [X]% 
**Reasoning:** [Why this level]

**Validation Method:** [How verified]
**Outstanding Issues:** [Any uncertainties]

**Status:** ✅ VERIFIED | ⚠️ NEEDS CONFIRMATION | ❌ INSUFFICIENT
```

## Operational Rules

1. **EVERY CRITICAL CLAIM:** Requires proof-grade validation
2. **SOURCE FIRST:** Identify source before using fact
3. **CONFIDENCE REQUIRED:** Every fact has percentage
4. **LOOP150 MANDATORY:** <85% triggers verification loop
5. **TRANSPARENCY:** Document all sources and reasoning
6. **ESCALATE HONESTLY:** If sources exhausted, ask user

## Failure Modes & Recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| **Unverified Claims** | Facts without sources | Immediate verification, Loop150 |
| **Overconfidence** | Inflated percentages | Recalculate with scrutiny |
| **Source Bias** | Only confirming sources | Actively seek contradictions |
| **Incomplete Docs** | Missing source trail | Document all sources now |

## Examples

### ❌ Without Proof-Grade
```
AI: "The API response time is fast enough"
Source: "Feels fast to me"
Result: Performance issues in production
```

### ✅ With Proof-Grade 150
```
🔍 PROOF-GRADE 150 VERIFICATION

Claim: "API response time is consistently under 200ms"

Primary Source:
- /tests/performance/load_test_results.json
- "p99 latency: 187ms across 10,000 requests"

Secondary Sources:
- Production monitoring (last 7 days): avg 156ms
- APM dashboard: p95 = 178ms

Confidence Level: 95%
Reasoning: Multiple measurement sources, consistent results,
production data confirms test environment findings.

Validation Method: Cross-referenced test data with production metrics

Status: ✅ VERIFIED FOR USE
```

## Relationship to Other Skills

- **research-deep-150** → Gathers evidence
- **proof-grade-150** → Validates and quantifies confidence
- **integrity-check-150** → Final quality verification

---

**Remember:** Proof-grade isn't about being slow — it's about being trustworthy. A 95% confidence claim is more valuable than an unverified assertion. When stakes are high, proof-grade protects everyone.

