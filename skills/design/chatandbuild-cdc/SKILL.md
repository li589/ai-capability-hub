---
id: cdc
name: CDC
description: Practical guidance for change data capture (CDC) design and implementation.
category: Data & AI
requires: []
examples:
  - Recommend a CDC architecture for syncing Postgres to a warehouse.
  - How should I handle deduplication and replay in a CDC pipeline?
install_source: official
install_method: download
skill_id: official_eCj3UX11
enabled_at: 1787232328701
version: 1.0.0
name_zh: CDC处理
---

# CDC

Help the agent provide practical guidance for CDC architectures and operations.

## When to Use

- The user needs help choosing a CDC pattern for replication or streaming.
- The user asks about consistency, ordering, deduplication, or replay behavior.
- The user wants implementation-ready advice for production pipelines.

## Instructions

1. Clarify source systems, latency targets, and downstream consumers.
2. Recommend a CDC pattern (log-based, trigger-based, or batch diff) with trade-offs.
3. Define schema evolution, idempotency, and exactly-once/at-least-once handling.
4. Include monitoring, backfill, and recovery procedures.
5. End with a rollout and verification checklist.

## Output

- Recommended CDC design with rationale
- Implementation checklist
- Risks, assumptions, and validation steps
