---
name: data-analysis-pro
description: |
  Production-grade tabular data analysis in Python: analytical pipeline and grain model (row unit, joins, lineage), EDA and cleaning discipline, descriptive statistics and honest visualization, pivot-style workflows, Parquet/CSV/SQLite IO, failure modes (join explosions, timezone bugs, lookahead leakage, Simpson’s paradox, p-hacking, Excel precision), decision trade-offs (pandas vs SQL pushdown, notebook vs pipeline, descriptive vs causal claims), reproducibility and anti-hallucination guardrails for numbers, spreadsheet delivery (openpyxl charts, validation, freeze panes), and integration with SQL, business analysis, and security for PII-safe exports.

  Use when analyzing CSV/Parquet/SQLite exports, profiling datasets, building aggregates and charts, or authoring Excel analytics — not for unstructured PDF/image semantic reading (content-analysis-pro).

  Use with content-analysis-pro, business-analysis-pro, postgresql-pro, sql-data-access-pro, security-pro, testing-pro as needed.

  Triggers: "analyze CSV", "pandas", "EDA", "Parquet", "pivot", "groupby", "matplotlib", "seaborn", "histogram", "missing values", "outliers", "correlation", "openpyxl", "data validation", "freeze panes", "SQLite", "profiling", "dtype", "leakage", "Simpson", "grain", "timezone", "reproducibility", "join", "many-to-many", "causation", "p-hacking", "cohort", "read_parquet".
metadata:
  short-description: Data analysis — pipeline/grain, EDA, viz, Excel, failure modes, reproducibility
  content-language: en
  domain: data-analysis
  level: professional
install_source: official
install_method: download
skill_id: official_MB3rdD8r
enabled_at: 1787232833894
version: 1.0.0
name_zh: 数据分析专业版
---

# Data analysis (professional)

Skill text is **English**; answer in the user’s preferred language when rules or the conversation specify it.

Use **[pandas](https://pandas.pydata.org/docs/)** and your stack’s plotting docs for API truth; this skill encodes **analytical grain**, **pipeline discipline**, **honest descriptive statistics**, and **delivery patterns** — not notebook theater. Confirm **Python environment**, **data sensitivity** (PII), and **whether claims are descriptive or causal**. **`content-analysis-pro`** handles unstructured narrative/media interpretation.

## Boundary

**`data-analysis-pro`** owns **tabular** workflows: ingest → validate types → define grain → transform → aggregate → visualize → export (including **openpyxl** presentation). **`postgresql-pro`** owns **server-side database** product design beyond extracts. **`business-analysis-pro`** owns **business requirements** packaging from metrics. **`algorithm-pro`** is for heavy algorithmic theory — not typical EDA.

## Related skills (this repo)

| Skill | When to combine with `data-analysis-pro` |
|-------|----------------------------------------|
| **`content-analysis-pro`** | Unstructured PDF/image/video meaning — not pivot tables |
| **`business-analysis-pro`** | KPI definitions, BRD from metrics |
| **`postgresql-pro`** | Warehouse-scale SQL, indexing when analysis drives schema |
| **`sql-data-access-pro`** | SQLite extracts; parameterized SQL hygiene |
| **`security-pro`** | Anonymization, safe exports, notebook leakage |
| **`testing-pro`** | Regression tests on transform pipelines |
| **`market-research-pro`** | External validation of market assumptions |
| **`repo-tooling-pro`** | Batch orchestration for repeatable pipelines |

## When to use

- **EDA**, cleaning, profiling, aggregates, pivots.
- **Visualization** with labeled, honest axes.
- **Excel** analytics delivery (charts, validation).
- **Leakage/bias** sanity when metrics or splits appear.

## When not to use

- **“What does this scanned contract mean?”** — **`content-analysis-pro`**.
- **Kubernetes deployment** of pipelines — **`deployment-pro`** / **`ci-cd-pro`**.

## Required inputs

- **Data location**, **question**, **grain** if known, **privacy** constraints.

## Expected output

Follow **Suggested response format** strictly — pipeline through residual risks — with explicit **grain** and **denominators**.

## Workflow

Apply **Karpathy principles** throughout: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.

1. **Confirm** data source, analytical question, deliverable (figure, table, `.xlsx`), privacy. → verify: [context documented].
2. **State assumptions** about requirements, constraints (**Think Before Coding**).
3. **Apply** minimum solution first; escalate only when justified (**Simplicity First**).
4. **Make surgical changes** — only touch code directly related to the request (**Surgical Changes**).
5. **Define success criteria**; loop until verified (**Goal-Driven Execution**).
6. **Respond** using **Suggested response format**; note main risks.

### Operating principles

1. **Think Before Coding** — Confirm the analytical question, dataset grain, privacy constraints, and whether the claim is descriptive or causal. Ask before assuming denominators or join keys.
2. **Simplicity First** — Start with the smallest trustworthy transform and aggregate path. Do not build notebooks, dashboards, or models when a table or chart answers the question.
3. **Surgical Changes** — Touch only the data slice, transform, and output needed for the request. Avoid opportunistic reshaping of unrelated metrics.
4. **Goal-Driven Execution** — Done = the result is reproducible, denominators are explicit, and the numbers or charts answer the stated question.
5. **Grain is the contract** — Every metric depends on the row unit, join shape, and deduping policy being explicit.
6. **Numbers need lineage** — Derived fields, filters, and missing-value handling should be traceable, not implied.
7. **Honest charts over decorative charts** — Axes, labels, and comparison choices should avoid misleading magnitude or trend impressions.
8. **Causal language is rare** — Unless the evidence supports it, describe association, distribution, or change, not causation.

## Default recommendations by scenario

- **EDA request** — Start with schema, types, nulls, ranges, and grain checks before business conclusions.
- **Metric request** — Define denominator and cohort first, then aggregate.
- **Excel deliverable** — Build the smallest clean export with validation and frozen panes before adding charts.
- **Join-heavy analysis** — Prove key uniqueness and many-to-many behavior before trusting the result.

## Decision trees

Summary: choose analysis depth, SQL pushdown vs pandas, and output shape based on grain clarity, data volume, and decision stakes.

Details: [references/decision-tree.md](references/decision-tree.md)

## Anti-patterns

Summary: join explosions, hidden filters, misleading charts, accidental leakage, and causal claims from descriptive data.

Details: [references/anti-patterns.md](references/anti-patterns.md)

### Analysis pipeline and grain model (summary)

How ingest, typing, grain definition, transformation, aggregation, and export fit together so metrics stay explainable.

Details: [references/analysis-pipeline-and-grain-model.md](references/analysis-pipeline-and-grain-model.md)

### EDA and cleaning (summary)

How to inspect missingness, types, outliers, and quality issues before trusting downstream numbers.

Details: [references/eda-and-cleaning.md](references/eda-and-cleaning.md)

### Visualization and communication (summary)

How to choose charts and present analytical results without overstating precision or meaning.

Details: [references/visualization-and-communication.md](references/visualization-and-communication.md)

### Spreadsheets, charts, and validation (summary)

How to package outputs into trustworthy Excel deliverables when the result needs business-facing distribution.

Details: [references/spreadsheets-charts-and-validation.md](references/spreadsheets-charts-and-validation.md)

### Failure modes and mitigation (summary)

Timezone errors, Simpson’s paradox, leakage, Excel precision, and many-to-many join traps that can invalidate conclusions.

Details: [references/failure-modes-detection-mitigation.md](references/failure-modes-detection-mitigation.md)

### Versions (summary)

Version notes that affect pandas/plotting behavior, file IO, and compatibility expectations.

Details: [references/versions.md](references/versions.md)

## Suggested response format

1. **Context** — Data source, analytical question, grain, privacy constraints, and deliverable type.
2. **Analysis model** — Explain grain, key transforms, and why this analysis path is appropriate.
3. **Results** — Tables, aggregates, or chart findings with explicit denominators and assumptions.
4. **Verification** — How to reproduce the result and what checks confirm it is trustworthy.
5. **Residual risks** — Remaining data quality, bias, leakage, or interpretation caveats.

## Resources in this skill

| Topic | File |
|-------|------|
| Analysis pipeline and grain model | [references/analysis-pipeline-and-grain-model.md](references/analysis-pipeline-and-grain-model.md) |
| EDA and cleaning | [references/eda-and-cleaning.md](references/eda-and-cleaning.md) |
| Visualization and communication | [references/visualization-and-communication.md](references/visualization-and-communication.md) |
| Spreadsheets, charts, and validation | [references/spreadsheets-charts-and-validation.md](references/spreadsheets-charts-and-validation.md) |
| Failure modes and mitigation | [references/failure-modes-detection-mitigation.md](references/failure-modes-detection-mitigation.md) |
| Decision framework and trade-offs | [references/decision-framework-and-trade-offs.md](references/decision-framework-and-trade-offs.md) |
| Decision tree | [references/decision-tree.md](references/decision-tree.md) |
| Anti-patterns | [references/anti-patterns.md](references/anti-patterns.md) |
| Tips and tricks | [references/tips-and-tricks.md](references/tips-and-tricks.md) |
| Edge cases | [references/edge-cases.md](references/edge-cases.md) |
| Quality validation and guardrails | [references/quality-validation-and-guardrails.md](references/quality-validation-and-guardrails.md) |
| Integration map | [references/integration-map.md](references/integration-map.md) |
| Version notes | [references/versions.md](references/versions.md) |

## Quick example

**Input:** "Analyze this CSV for weekly conversion trend."
- Confirm the row grain and denominator before computing the trend.
- Start with a simple aggregate and labeled chart, not a full notebook rewrite.
- **Verify:** The weekly counts and conversion definition can be reproduced from the raw file.

**Input (tricky):** "Revenue doubled after a join, so the campaign worked."
- Check many-to-many duplication and causal overreach before accepting the conclusion.
- Fix the grain or join logic first, then restate the result descriptively.
- **Verify:** Post-join row counts and totals reconcile with source tables.

**Input (cross-skill):** "Turn SQLite extracts into an Excel KPI pack."
- Pair **`sql-data-access-pro`** for extraction hygiene and use **`data-analysis-pro`** for shaping and packaging the metrics.
- Keep privacy and denominator assumptions explicit.
- **Verify:** The export is reproducible and the KPI workbook matches the underlying aggregates.

## Checklist before calling the skill done

- [ ] Question, grain, and privacy constraints confirmed first (Think Before Coding)
- [ ] Minimum trustworthy analysis path chosen; no unnecessary analysis theater added (Simplicity First)
- [ ] Only the requested data slice and metric logic were changed (Surgical Changes)
- [ ] Success criteria, denominators, and reproducibility checks are explicit (Goal-Driven Execution)
- [ ] Join shape and deduping assumptions are stated where relevant
- [ ] Charts and summaries avoid misleading presentation
- [ ] Causal language is avoided unless supported
- [ ] Residual data-quality or interpretation risks are documented
