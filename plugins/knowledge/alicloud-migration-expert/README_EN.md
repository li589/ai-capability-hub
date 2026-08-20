# Alibaba Cloud Migration Expert Team

An end-to-end AI expert team for Alibaba Cloud migration. 7 specialists collaborate across the full lifecycle: requirement alignment, product selection & mapping, Landing Zone planning, target architecture design, migration delivery, operations handoff, and FDE pre-deployment. Ships with a 6-phase SOP pipeline, cross-cloud product mapping tables (AWS/Azure/GCP/Tencent Cloud/Huawei Cloud/self-hosted IDC → Alibaba Cloud), a 3-tier HA/DR decision model, MLPS 2.0 Level 3 compliance framework, a 40+ monitoring metrics catalog, 4 rollback trigger categories, and an 8-chapter PRCA emergency plan template. Delivers both Markdown chat summaries and formal documents (xlsx / HTML / Mermaid architecture diagrams).

> **Disclaimer:** This plugin assists professional migration decisions but does not replace human review. All output plans should be reviewed by an experienced Alibaba Cloud migration architect before production use.

## Target Roles

- **Cloud Migration Architect** — quickly generate target architecture, HA/DR matrix, and Mermaid topology with built-in Alibaba Cloud SLA data
- **Presales / Solutions Engineer** — one-shot product mapping table + TCO comparison + full migration proposal for customer presentations
- **Migration Delivery Engineer** — obtain six-layer migration breakdown, cut-over playbook, and rollback trigger checklist
- **Operations Engineer** — generate monitoring & alerting configs (40+ metrics), emergency runbooks, and inspection SOPs
- **Project Manager** — auto-orchestrate the 6-phase SOP with clear deliverables and timeline per phase

## Quick Commands

| Command | Description |
|---------|-------------|
| `@Chief Migration Expert` | Orchestrator entry: describe your migration need, auto-routed to the right workflow (direct answer / lean / full SOP) |
| `@Cloud Product Selection Expert` | Upload source-platform inventory, generates Alibaba Cloud product mapping + cost estimate |
| `@Landing Zone Expert` | Describe org structure and compliance needs, generates Landing Zone plan (13-sheet xlsx) |
| `@Cloud Architecture Expert` | Provide business needs and performance baseline, generates target architecture + HA/DR matrix + Mermaid |
| `@Migration Delivery Expert` | Provide the architecture plan, generates six-layer migration plan + cut-over steps + rollback contingency |
| `@Cloud Operations Expert` | Provide post-migration resource inventory, generates monitoring & alerts + emergency runbook + inspection SOP |
| `@FDE Deployment Expert` | Provide the Landing Zone plan, generates FDE environment deployment + self-check list |

## Skill Details

| Skill | Details |
|-------|---------|
| Chief Migration Expert | Orchestrator: 4-dimension requirement alignment (scope/constraints/architecture/team), 5 routing modes, 6-phase SOP orchestration, cross-expert context relay, Phase-6 TCO consolidation |
| Cloud Product Selection Expert | 4-tier input priority (AK/SK > Excel > architecture diagram > screenshot), 5-layer output structure, cross-cloud mapping, 3-tier cost estimation, real-time pricing via Alibaba Cloud API |
| Landing Zone Expert | 13-sheet xlsx standard output (RAM/VPC/tags/security baseline/compliance/cost/roadmap), MLPS 2.0 Level 3 nine-domain mapping, ISO 27001 coverage |
| Cloud Architecture Expert | 8 required inputs, 5 deliverable categories, 3-tier HA model (L1 multi-Region / L2 multi-AZ / L3 single-AZ), Alibaba Cloud product SLA data, Mermaid topology |
| Migration Delivery Expert | "Resource type × Migration phase" 6×6 matrix, 4 rollback trigger categories (technical/business/time-window/external-dependency), Gantt chart timeline |
| Cloud Operations Expert | 5 categories × 40+ monitoring metrics with dual thresholds, 8-chapter PRCA emergency runbook, daily/weekly/monthly inspection SOP, migration-phase watchlist, training plan |
| FDE Deployment Expert | 6 categories of FDE deployment components (network/resources/toolchain/permissions/monitoring/documentation), FDE vs Ops responsibility boundary, 33-item environment self-check |
| Alibaba Cloud Product Knowledge Base | Internal reference (invisible to users): ECS instance family cheatsheet, Region/AZ distribution, product SLA, BSS OpenAPI pricing calls, migration tool matrix |

## Connectors (optional enhancements)

| Scenario | Standalone | With connector |
|----------|-----------|----------------|
| Product mapping | Manual upload of Excel/screenshots | Auto-scan source resources + real-time pricing via Alibaba Cloud OpenAPI |
| Landing Zone | Manual org-structure input | Query existing account hierarchy via RAM OpenAPI |
| Migration execution | Manual resource inventory input | Query migration job progress via SMC/DTS API |
| Cloud operations | Manual resource list input | Auto-configure alert policies via CloudMonitor API |

> All skills work standalone without connectors; connectors upgrade the experience. See CONNECTORS.md for details.
