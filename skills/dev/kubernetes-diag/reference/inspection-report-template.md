# Inspection Report Template

Use this template for mode C (proactive health inspection) output. Do NOT use the postmortem template for inspections.

---

## Report Structure

```markdown
# Cluster Health Inspection Report

**Date**: <YYYY-MM-DD HH:MM>
**Nodes inspected**: <count> (<node list>)
**Collector version**: kubernetes-diag skill
**Overall health score**: <0-100> / 100

## Score Summary

| Dimension | Score | Status |
|-----------|-------|--------|
| Runtime Config Consistency | <score> | <HEALTHY/WARNING/CRITICAL> |
| Certificate Expiry | <score> | <status> |
| Resource Pressure | <score> | <status> |
| Time Sync | <score> | <status> |
| Container Restart Anomalies | <score> | <status> |
| CNI / Service Network | <score> | <status> |
| etcd Cluster Health | <score> | <status> |
| Package Version Consistency | <score> | <status> |
| Stale / Orphan Pods | <score> | <status> |
| **Overall** | **<total>** | |

## Per-Node Summary

| Node | Role | Score | Deviations |
|------|------|-------|------------|
| <hostname> | <master/worker> | <score> | <brief> |

## Risk Items

### CRITICAL (immediate action required)

- [ ] <description + affected node(s) + evidence file reference>

### WARNING (action recommended within 7 days)

- [ ] <description + affected node(s) + evidence file reference>

### INFO (observed, no action needed)

- <observation, e.g. stale Pods classified as STALE>

## Stale Pod Inventory

| Namespace | Pod | Status | AGE | Verdict | Recommended Action |
|-----------|-----|--------|-----|---------|-------------------|
| <ns> | <name> | <status> | <age> | STALE | `kubectl delete pod <name> -n <ns> --force --grace-period=0` |

## Recommended Actions (prioritized)

1. <highest priority action with specific command or config path>
2. <next action>
3. ...

## Prevention Measures

*(For WARNING and CRITICAL risk items, propose concrete preventive actions)*

| Risk Item | Prevention |
|-----------|------------|
| <risk description from above> | <concrete action: monitoring alert, config validation, periodic check script, version pinning> |

### Long-term Improvements

- <process/tooling change that would catch similar issues before they become incidents>
- <recommended monitoring or alerting to add>

## Next Inspection Suggestion

- Recommended interval: <based on findings>
- Focus areas for next round: <dimensions that scored WARNING>
```

---

## Usage Rules

1. Always fill ALL 9 dimensions. If data is unavailable for a dimension, mark as `N/A (data not collected)` and exclude from scoring denominator.
2. Risk items must reference the specific evidence file (e.g. `see 27c-cert-dates.txt on node01`).
3. Stale Pods go in their own section with explicit STALE verdict. Do NOT list them under CRITICAL or WARNING unless GC is broken.
4. Recommended actions must be concrete: include commands, file paths, or config keys. No vague "investigate further".
5. If overall score >= 90 and no CRITICAL items, state explicitly: "Cluster is healthy. No immediate action required."
6. If overall score < 60 or any CRITICAL exists, recommend switching to diagnosis mode (A or B) for the affected dimension.
