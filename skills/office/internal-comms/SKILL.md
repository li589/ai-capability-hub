---
name: internal-comms
description: Professional B2B email writing for Edge8 — personalised tone, clear CTAs, Malaysian business context, unsubscribe compliance, and delivery summary reporting
type: skill
agents:
  - 04-scheduler
  - 05-email-agent
install_source: official
install_method: download
skill_id: official36228373
enabled_at: 1785348241112
version: 1.0.0
name_zh: 内部通讯
---

# Skill: internal-comms

## Purpose
Write clear, professional, and personalised business emails for Edge8's weekly marketing campaign. Covers subscriber confirmation emails, follow-up outreach, rescheduling notifications, and Tommy's delivery summary reports.

## Invocation
- Agent 04: Step 5 (rescheduling notification) + Step 6 (subscriber confirmation emails)
- Agent 05: Step 3 (follow-up email copy) + Step 7 (Tommy's summary report)

## Voice & Tone

| Attribute | Guideline |
|-----------|-----------|
| **Register** | Professional but warm — not corporate-stiff |
| **Salutation** | Always use first name: "Hi {FIRST_NAME}," |
| **Length** | Short — subscribers scan, not read. Max 150 words per email |
| **CTAs** | Max 2 per email. Primary CTA first, booking CTA second |
| **Closing** | "Regards," + agent name. No "Best," or "Cheers," |
| **P.S.** | Use for next-week teasers — draws re-engagement |

## Email Templates

### Subscriber Follow-up (service-specific)

**Taxation:**
```
Subject: [Edge8] Did you catch this week's tax update?

Hi {FIRST_NAME},

This week: {HEADLINE}

{2-3 key takeaways as bullet points}

How this affects your business:
{1-2 sentence impact statement relevant to Malaysian SMEs}

→ Read full update: {LANDING_URL}
→ Book a 1-2-1 Tax Session: calendly.com/edge8/tax

P.S. Next week we're covering {TEASER_TOPIC} — stay tuned.

Regards,
Edge8 Advisory Team
```

**Audit:**
```
Subject: [Edge8] This week's audit insights from Jabatan Audit Negara

Hi {FIRST_NAME},

This week: {HEADLINE}

{2-3 key takeaways as bullet points}

Compliance action items:
• {ACTION_1}
• {ACTION_2}

→ Read full update: {LANDING_URL}
→ Book a 1-2-1 Audit Review: calendly.com/edge8/audit

Regards,
Edge8 Advisory Team
```

**Account:**
```
Subject: [Edge8] New ACCA Malaysia standard — are you ready?

Hi {FIRST_NAME},

This week: {HEADLINE}

{2-3 key takeaways as bullet points}

Next steps for your business:
{1-2 practical actions to take now}

→ Read full update: {LANDING_URL}
→ Book a 1-2-1 Accounting Session: calendly.com/edge8/account

Regards,
Edge8 Advisory Team
```

### Subscriber Confirmation (sent by Agent 04)

```
Subject: You're on the list — Edge8 Weekly coming {PUBLISH_DATE}

Hi {SUBSCRIBER_NAME},

You're confirmed for this week's Edge8 Weekly, arriving {PUBLISH_DATE}.

Here's what's coming:
• Taxation: {HEADLINE_TAX}
• Audit: {HEADLINE_AUDIT}
• Accounting: {HEADLINE_ACCOUNT}

We'll send it Wednesday at 10am (Kuala Lumpur time).

Regards,
Edge8 Advisory Team

---
Unsubscribe: {UNSUBSCRIBE_URL}
```

### Rescheduling Notification (sent by Agent 04)

```
Subject: [Edge8 Schedule] Campaign moved to {NEW_DATE}

Hi Tommy,

A scheduling conflict was detected for Wednesday {ORIGINAL_DATE}.
Reason: {CONFLICT_REASON}

Automatically rescheduled to: {NEW_DATE} at 10:00 AM (Kuala Lumpur)

Calendar events updated:
• Edge8 Taxation Weekly — {TAX_HEADLINE}
• Edge8 Audit Weekly — {AUDIT_HEADLINE}
• Edge8 Account Weekly — {ACCOUNT_HEADLINE}

No action required.

Regards,
Edge8 Scheduler Agent
```

## Unsubscribe Compliance

Every subscriber-facing email MUST include:
```html
<p style="font-size:12px;color:#64748B;margin-top:24px">
  You're receiving this because you subscribed to Edge8 Weekly.
  <a href="{UNSUBSCRIBE_URL}" style="color:#64748B">Unsubscribe</a>
</p>
```

And the email header:
```
List-Unsubscribe: <{UNSUBSCRIBE_URL}>
```

## Key Takeaway Generation

When writing 2–3 key takeaways from a news summary:
1. Start each with a verb: "Understand", "Note", "Prepare", "Check", "File"
2. Keep each to 1 sentence max
3. Make them actionable — what should the reader DO with this information?
4. Avoid jargon unless the audience is finance professionals

Example (Taxation):
```
• File your annual return before 30 June to avoid the RM50,000 penalty
• Check if your company falls under the new SME threshold (turnover < RM50M)
• Update your registered address in the SSM portal if it has changed
```
