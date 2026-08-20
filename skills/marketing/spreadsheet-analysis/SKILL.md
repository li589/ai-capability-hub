---
name: spreadsheet-analysis
description: "Audits, designs, and restructures spreadsheet workbooks — validates data quality, traces and fixes formulas, designs pivot tables, and documents cross-sheet architecture. Trigger: \"audit this spreadsheet\", \"fix this formula\", \"pivot table design\", \"data validation\", \"spreadsheet architecture\", \"formula error\", \"variance analysis\", \"what-if scenario\", \"clean up this workbook\". Do NOT use for generating .xlsx files from scratch (use xlsx-generation), for database queries (use sqlite/postgresql), or for Python/pandas data analysis (use python)."
license: Apache-2.0
compatibility:
  clients:
    - openai-codex
    - gemini-cli
    - opencode
    - github-copilot
metadata:
  owner: codex
  domain: spreadsheet-analysis
  maturity: draft
  risk: low
  tags:
    - spreadsheet
    - data-validation
    - formula-audit
    - pivot-tables
    - workbook-design
install_source: official
install_method: download
skill_id: official_GzvOC9SY
enabled_at: 1787232886880
version: 1.0.0
name_zh: 电子表格分析
---

# Purpose

Provides a structured methodology for auditing, analyzing, and improving spreadsheet
workbooks. Covers data quality validation, formula auditing and error correction,
pivot table design, cross-sheet architecture, and common analytical patterns so that
workbook deliverables are reliable, maintainable, and well-documented.

# When to use this skill

- User asks to audit, review, or debug an existing spreadsheet or workbook
- Task requires formula tracing, error detection, or fixing circular references
- User needs help designing pivot tables, dashboards, or summary views
- Workbook architecture needs restructuring: naming conventions, sheet layout, data flow
- User requests variance analysis, trend analysis, cohort analysis, or what-if modeling
- Data quality concerns: duplicates, missing values, inconsistent formats, validation rules
- User asks "why is this formula returning #REF!" or "this spreadsheet is a mess"

# Do not use this skill when

- The task is to generate a new .xlsx file from structured data — use `xlsx-generation`
- The user needs to build a financial tracker from scratch — use `financial-tracker-ops`
- The analysis belongs in Python/pandas or SQL, not a spreadsheet — use `python` or `sqlite`
- The task is data visualization only (chart design without spreadsheet context) — use `spreadsheet` for basic charting
- The user wants to extract data from a PDF table — use `table-extraction` first, then this skill

# Operating procedure

## Step 1 — Workbook intake and orientation

1. Identify all sheets, their purpose, and the data flow between them (which sheets feed which).
2. Document the workbook's intended audience and decision it supports.
3. Note the file format (xlsx, Google Sheets, CSV collection) and any external data connections.
4. Count rows, columns, and approximate formula density per sheet.
5. Identify the "source of truth" sheets (raw data) vs. derived sheets (calculations, summaries).

## Step 2 — Data quality audit

Run these checks against every data sheet:

| Check | Method | Pass criteria |
|---|---|---|
| **Type consistency** | Verify each column has a single data type (text, number, date, boolean) | No mixed types in a column |
| **Range validation** | Check numeric columns for values outside expected bounds | No out-of-range values, or flagged with explanation |
| **Duplicate detection** | Check for duplicate rows on the primary key columns | Zero exact duplicates, near-duplicates flagged |
| **Completeness** | Calculate % populated for each column | Critical columns ≥ 95% populated |
| **Date format consistency** | Verify all dates use a single format (ISO 8601 preferred) | One format per column |
| **Trailing whitespace / invisible chars** | TRIM and CLEAN checks | No hidden characters affecting lookups |
| **Referential integrity** | VLOOKUP/INDEX-MATCH keys exist in source tables | Zero orphaned references |

Produce a **Data Quality Report** summarizing findings per sheet.

## Step 3 — Formula auditing

For each sheet with formulas:

1. **Precedent tracing** — map which cells feed into each formula; document the dependency chain.
2. **Dependent tracing** — identify all cells that depend on a given input; flag single-point-of-failure inputs.
3. **Error detection** — scan for:
   - `#REF!` — broken references from deleted rows/columns/sheets
   - `#N/A` — failed lookups; check for type mismatches or trailing whitespace
   - `#VALUE!` — type errors in arithmetic
   - `#DIV/0!` — division by zero without IFERROR wrapper
   - `#NAME?` — misspelled function names or missing named ranges
   - `Circular references` — trace the loop and propose a resolution
4. **Volatile function identification** — flag `NOW()`, `TODAY()`, `RAND()`, `INDIRECT()`, `OFFSET()` usage; these recalculate on every edit and slow large workbooks.
5. **Hardcoded values in formulas** — identify magic numbers embedded in formulas that should be named ranges or input cells.
6. **Inconsistent formulas in ranges** — check that a formula copied down a column is consistent (no skipped rows or manually overridden cells).

Produce a **Formula Audit Report** with severity (Critical / Warning / Info) for each finding.

## Step 4 — Pivot table and summary design

When the user needs aggregated views:

1. **Dimension selection** — identify the categorical fields to group by (rows and columns).
2. **Aggregation choice** — select appropriate aggregation: SUM for amounts, COUNT for occurrences, AVERAGE for rates, MEDIAN for skewed distributions.
3. **Filter strategy** — define slicers or report filters (date range, category, region).
4. **Drill-down paths** — design hierarchy so users can expand from summary to detail (e.g., Year → Quarter → Month → Day).
5. **Calculated fields** — define any custom calculations (e.g., margin = revenue − cost).
6. **Refresh strategy** — document how and when the pivot source data gets updated.

## Step 5 — Cross-sheet architecture

Evaluate and improve workbook structure:

1. **Naming conventions** — sheets should have short, descriptive names (no "Sheet1"); named ranges for all key inputs and outputs.
2. **Reference strategy** — prefer structured table references (`Table1[Column]`) over cell references (`A2:A100`); use named ranges for constants.
3. **Data flow documentation** — create a sheet map showing: Source → Transform → Summary → Output flow.
4. **Input/output separation** — raw data on separate sheets from calculations; user-editable inputs clearly marked (e.g., colored cells, input sheet).
5. **Protection** — recommend sheet protection on formula sheets; lock structural elements while allowing input cells.
6. **Version control** — recommend a changelog sheet or header row with last-modified date.

## Step 6 — Analysis patterns

Apply the appropriate pattern based on the user's analytical need:

| Pattern | When to use | Key technique |
|---|---|---|
| **Variance analysis** | Compare actual vs. budget/forecast | ABS and % variance columns; conditional formatting for thresholds |
| **Trend analysis** | Identify direction over time | Period-over-period change; moving averages (3, 6, 12 period); sparklines |
| **Cohort analysis** | Compare groups by entry date | Pivot by cohort period; retention/churn rates per cohort |
| **What-if scenarios** | Test sensitivity to input changes | Data Tables (1-variable and 2-variable); Goal Seek; Scenario Manager |
| **Pareto analysis** | Identify the vital few | Sort descending, cumulative %; highlight 80% threshold |
| **Waterfall analysis** | Show cumulative contribution | Running total with positive/negative segments |

## Step 7 — Output formatting and visualization

1. **Conditional formatting rules**:
   - Red/amber/green for KPI thresholds (define the thresholds explicitly)
   - Data bars for quick magnitude comparison
   - Icon sets sparingly (only when 3-state status adds clarity)
2. **Chart type selection guide**:
   - **Bar/Column** → comparing categories (e.g., sales by region)
   - **Line** → trends over time (e.g., monthly revenue)
   - **Scatter** → correlation between two variables (e.g., spend vs. conversion)
   - **Pie** → avoid; use stacked bar if part-of-whole is needed
   - **Waterfall** → showing incremental changes (e.g., bridge from budget to actual)
   - **Combo** → dual-axis for different scales (e.g., revenue bars + margin % line)
3. **Formatting hygiene**: consistent number formats, aligned decimal points, frozen header rows, print area defined.

# Decision rules

- **Mixed data types in a column** → always flag and fix before any analysis; a single text value in a numeric column breaks SUM/AVERAGE silently.
- **Formula error count > 0** → resolve all Critical errors before delivering; Warning-level errors must be documented if not fixed.
- **Hardcoded values in formulas** → extract to named input cells in 100% of cases; zero tolerance for magic numbers.
- **Volatile functions** → replace with static alternatives where possible (e.g., paste-as-values for timestamps); if volatile is required, document the performance impact.
- **Merged cells detected** → unmerge and use "Center Across Selection" or reformat; merged cells break sorting, filtering, and formulas.
- **No data validation on input cells** → add validation rules (dropdowns, numeric ranges, date constraints) for every user-editable input.
- **Circular reference** → must be resolved or explicitly justified with iterative calculation settings documented.
- **Pivot table source is a fixed range** → convert to a structured Table so the pivot auto-expands with new data.
- **Charts without titles or axis labels** → always add; a chart without context is noise.

# Output structure

Deliver these sections as applicable:

## 1. Data Quality Report

Per-sheet summary table of validation checks with pass/fail status, row counts affected,
and recommended fixes.

## 2. Formula Audit Report

Table of findings: cell reference, issue type, severity, current formula, recommended fix.

## 3. Analysis Workbook Design

Architecture diagram (text-based sheet map) showing data flow, named ranges index,
and input/output cell inventory.

## 4. Pivot Table Specifications

For each pivot: source table, row/column dimensions, aggregations, filters, calculated fields.

## 5. Results Summary

Narrative summary of analytical findings with supporting data tables and chart recommendations.

## 6. Formatting Guide

Conditional formatting rules, chart specifications, and print layout settings for the final workbook.

# Anti-patterns

- **Hardcoded values in formulas** — embedding `1.08` for tax rate inside `=B2*1.08` instead of `=B2*TaxRate`; makes updates error-prone and auditing impossible.
- **Merged cells** — break sorting, filtering, VLOOKUP, and pivot tables; the single most destructive formatting choice in spreadsheets.
- **Inconsistent date formats** — mixing `MM/DD/YYYY` and `DD/MM/YYYY` in the same workbook causes silent misinterpretation; standardize to ISO 8601 or locale-consistent format.
- **No data validation on inputs** — allowing free-text entry in cells that should be constrained leads to garbage-in-garbage-out.
- **Fixed-range pivot sources** — using `A1:Z100` instead of a structured Table means new data rows are silently excluded.
- **VLOOKUP instead of INDEX-MATCH** — VLOOKUP breaks when columns are inserted; INDEX-MATCH is column-order independent.
- **Pie charts for more than 5 categories** — becomes unreadable; use a sorted bar chart instead.
- **No documentation** — a workbook without a README sheet, named ranges, or comments becomes unmaintainable within weeks.
- **Copy-paste instead of formulas** — static values that look like live calculations; breaks on data refresh.
- **One massive sheet** — cramming data, calculations, and presentation onto a single sheet; separate concerns into distinct sheets.

# Related skills

- `xlsx-generation` — creating new .xlsx files programmatically from structured data
- `spreadsheet` — basic spreadsheet operations and simpler tasks
- `financial-tracker-ops` — building and maintaining financial tracking workbooks
- `table-extraction` — extracting tabular data from PDFs or images to feed into spreadsheet analysis
- `csv-ready` — preparing clean CSV data for import into spreadsheets
- `document-to-structured-data` — converting unstructured documents into tabular format

# Failure handling

- If the user provides no file or data, ask for the workbook or a representative sample before proceeding.
- If the file format is unsupported or corrupted, state this clearly and suggest export to .xlsx or CSV.
- If the workbook is too large to analyze fully (>50 sheets, >100K rows), prioritize: audit the summary/output sheets first, then trace back to source data on demand.
- If formulas use platform-specific features (Google Sheets QUERY, Excel Power Query), note compatibility limitations and suggest portable alternatives.
- If the analysis request is ambiguous ("make this spreadsheet better"), run Step 1–3 (intake, data quality, formula audit) as a baseline and present findings before deeper work.
