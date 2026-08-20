---
name: accounting-hardening
description: Use this skill when auditing, hardening, completing, reviewing, or validating an existing accounting module. Apply for journals, ledger, invoicing, receivables, payables, taxes, payments, reconciliation, fiscal periods, posting logic, and financial reporting.
install_source: official
install_method: download
skill_id: official_FzOWHKPC
enabled_at: 1787232888438
version: 1.0.0
name_zh: 会计强化
---

# Accounting Hardening Skill

## Purpose
This skill is for existing accounting systems that must be hardened and completed to production standards.

It is not a greenfield accounting design skill.
It assumes there is already a module in the codebase and starts from code reality first.

The objective is to:
- remove guesswork
- make accounting treatment explicit
- harden controls
- complete missing logic
- verify report integrity
- make the module production-ready

## When to use
Use this skill for any task involving:
- chart of accounts
- journal entries
- journal entry lines
- posting logic
- invoices
- vendor bills
- receivables
- payables
- customer payments
- vendor payments
- allocations
- credit notes
- debit notes
- refunds
- write-offs
- taxes
- bank / cash handling
- reconciliation
- fiscal periods
- financial reports
- audit trail validation
- accounting-related schema reviews
- accounting-related bug fixing

## Mandatory workflow
For every accounting task, follow this order exactly:

1. Inspect the existing implementation
2. Describe the current behavior factually
3. Identify the business event
4. Determine the correct accounting treatment
5. Identify gaps, missing controls, risky assumptions, and edge cases
6. Propose the minimal safe design changes required
7. Implement the changes
8. Add or update validation tests
9. Re-check report consistency and accounting invariants

Do not skip the current-behavior step.
Do not implement before stating the accounting treatment.

## Required output format
Always structure the response as follows:

### Current behavior
Describe what the current code actually does.
List affected models, services, controllers, APIs, jobs, queries, and reports.

### Business event
Describe the real-world accounting event being represented.

### Correct accounting treatment
State the debit / credit treatment explicitly.
Also state:
- recognition timing
- state transitions
- tax treatment if relevant
- reversal / cancellation behavior
- allocation behavior if relevant

### Gaps / risks
List all relevant risks, including:
- unbalanced entries
- duplicate posting
- posting into closed periods
- missing account mappings
- mutation of posted data
- broken traceability
- report inconsistency
- incomplete reversal logic
- allocation errors
- reconciliation gaps
- rounding errors
- permission issues
- audit trail weaknesses
- async retry / idempotency problems

### Proposed changes
List exact changes required in:
- schema
- models
- services
- posting engine
- APIs
- jobs
- validations
- reports
- tests
- UI states if relevant

### Validation
List exact invariants and tests to verify.

## Non-negotiable rules
- Never assume the existing accounting behavior is correct.
- Never implement accounting logic without stating the treatment explicitly.
- Never allow posted entries to be deleted, overwritten, or silently mutated.
- Never bypass journal creation when the event should affect the ledger.
- Never use ad hoc operational totals as the official basis for accounting reports.
- Never ignore reversal, cancellation, adjustment, and period-close behavior.
- Never leave posting idempotency ambiguous if repeated execution is possible.
- Never leave tax logic implied.
- Never leave account mapping implied.
- Never modify historical migrations by default.
- Assume old migrations were already executed.
- Use new forward-only migrations for schema corrections.
- If migration history seems wrong, report it first instead of rewriting it.
- Prefer additive migrations over destructive migration edits.

## Audit checklist for existing modules
When reviewing an existing accounting module, inspect:

### Foundation
- chart of accounts structure
- account types and normal balance logic
- journal entry header / line design
- fiscal period model
- document date vs posting date handling

### Posting
- posting trigger points
- posting service design
- duplicate posting prevention
- source-document traceability
- balancing validation
- status transitions
- reversal and adjustment handling

### Transaction flows
- customer invoices
- vendor bills
- customer receipts
- vendor payments
- credit notes
- debit notes
- write-offs
- refunds
- overpayments
- underpayments
- partial allocations

### Tax
- tax code mappings
- tax-inclusive vs tax-exclusive handling
- tax account mappings
- tax rounding
- tax reporting consistency

### Reconciliation
- AR allocations
- AP allocations
- bank linkage
- unapplied cash
- reconciliation hooks / states

### Controls
- period locking
- immutable posted entries
- audit fields
- created_by / posted_by / reversed_by
- authorization boundaries
- idempotency
- async safety

### Reporting
- trial balance
- general ledger
- balance sheet
- profit and loss
- AR aging
- AP aging
- tax summaries
- summary vs detail reconciliation

## Production hardening checklist
Whenever relevant, verify or implement:
- balanced-entry validation
- idempotent posting keys
- no posting to closed periods
- no orphaned journal lines
- no journal entries without source references
- no journal entries without posting metadata
- no silent edits to posted transactions
- explicit reverse vs void semantics
- explicit cancelled-document behavior
- partial payment allocation correctness
- discount treatment
- write-off treatment
- overpayment handling
- consistent rounding and precision rules
- reliable report derivation from posted data only

## Completion standard
An accounting hardening task is complete only if:
- current behavior is documented
- desired accounting treatment is explicit
- risks are identified
- safe changes are implemented
- controls are enforced
- reports remain consistent
- tests prove the invariants