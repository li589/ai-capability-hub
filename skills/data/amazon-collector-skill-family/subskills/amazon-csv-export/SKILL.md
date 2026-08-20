---
name: amazon-csv-export
description: Convert existing Amazon list, detail, and review stage data into contract-compliant UTF-8-BOM CSV files without creating collection tasks. Use for export-only requests or as the final stage of the Amazon keyword orchestrator. Do not call task-creation MCP tools.
---

# Amazon CSV Export

## Mission

Produce validated `list.csv`, `details.csv`, and `reviews.csv` artifacts from existing stage data while preserving search rank, ASIN identity, coverage status, and extra template fields.

## When to use

Use this Skill after collection stages or for re-export of an existing run. Require stage-result files or their referenced raw JSON rows.

## Hard constraints

- Announce `amazon-csv-export` before writing files.
- Create no cloud task and call none of `execute_task`, `get_task_status`, or `start_or_stop_task`.
- Accept only version `1.0` stage contracts with explicit statuses, row paths, warnings, and errors.
- Write RFC 4180 CSV using UTF-8 with BOM.
- Place fixed core fields first and append extra source fields in stable lexical order.
- Preserve embedded commas, quotes, Unicode text, and newlines through CSV quoting.
- Derive status and counts from stage data, not prose.
- Write no API key, MCP session ID, or signed export URL secret.

## Core workflow

1. Load `stage-list.json`, `stage-details.json`, and `stage-reviews.json` when available.
2. Validate contract version, stage name, status, raw path, counts, and task identities.
3. Load every referenced raw JSON array.
4. Normalize metadata keys to `search_rank`, `keyword`, `site`, `collection_status`, and `error` while preserving source fields.
5. Use the fixed field sets in `../../contracts/csv-fields.json`; append unknown fields lexically.
6. Write filenames `amazon_<SITE>_<KEYWORD>_<UTCSTAMP>_list.csv`, `_details.csv`, and `_reviews.csv` inside the run directory.
7. Re-open each file as UTF-8-BOM CSV, verify header width and row width, and reconcile row counts.
8. Save `stage-export.json`; update `run-state.json` to `CSV_READY` only after successful verification.

## Output format

```json
{
  "contract_version": "1.0",
  "stage": "export",
  "status": "CSV_READY|PARTIAL|FAILED",
  "files": {"list": "...csv", "details": "...csv", "reviews": "...csv"},
  "row_counts": {"list": 30, "details": 30, "reviews": 3000},
  "encoding": "utf-8-sig",
  "warnings": [],
  "errors": []
}
```

## Done criteria

- Every available valid stage produced its corresponding CSV.
- Each CSV begins with the UTF-8 BOM and passes a read-back width check.
- Core fields appear in contract order and extra fields are preserved.
- Row counts match loaded raw arrays.
- No collection task was created or changed.
- `stage-export.json` truthfully records files, counts, warnings, and errors.
