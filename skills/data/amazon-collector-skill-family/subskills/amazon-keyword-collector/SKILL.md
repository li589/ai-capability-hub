---
name: amazon-keyword-collector
description: Orchestrate an end-to-end Amazon keyword collection through the configured Bazhuayu MCP and produce product-list, product-detail, and review CSV files. Use only when the user provides a keyword, desired product count, and Amazon site and wants the complete result. Route ASIN-only or export-only requests to the dedicated sibling Skills.
---

# Amazon Keyword Collector

## Mission

Produce three usable UTF-8-BOM CSV files from one Amazon keyword: the requested ranked product list, details for every collected ASIN, and customer-limited or default-100 reviews per product. Preserve `run-state.json` so another Agent can resume without repeating completed cloud tasks.

## When to use

Use this Skill for complete keyword-to-CSV requests with `keyword`, `quantity`, and `site`. Use `amazon-product-list` for list-only requests, `amazon-product-details` for ASIN details, `amazon-product-reviews` for ASIN reviews, and `amazon-csv-export` for an existing run.

## Hard constraints

- Announce `amazon-keyword-collector` and the four-stage workflow before any MCP call.
- Before the first MCP call, tell the user in Chinese: `免费版与个人版通过 MCP 调用每周最多 2000 条；团队版不限条数。`
- Require one non-empty keyword, an integer quantity from 1 through 1000, and one supported site.
- Accept optional `review_limit` and `review_start_date` values. Validate a supplied review start date as `yyyy-mm-dd`. Default an absent review limit to 100, and default an absent review start date for every site to one calendar year before the customer's request date.
- Use the customer's configured Bazhuayu MCP connection. Treat API keys as runtime secrets and never request, echo, log, or save them in chat or files.
- Use only these sibling Skill sources: `../amazon-product-list/SKILL.md`, `../amazon-product-details/SKILL.md`, `../amazon-product-reviews/SKILL.md`, and `../amazon-csv-export/SKILL.md`.
- Require every collection stage to submit its full normalized input to exactly one template task. Do not split ASINs or create fallback subtasks.
- Execute stages sequentially through their machine contracts. Accept no prose-only stage completion.
- Store every stage result under `amazon-collector-runs/<run_id>/` and update `run-state.json` after each terminal MCP response.
- Reuse recorded `taskId` and `lotNo` during resume. Create no replacement task for a completed stage.
- Report `COMPLETE`, `PARTIAL`, or `FAILED` exactly as recorded by the contracts.

## Core workflow

1. Normalize the request to `{keyword, quantity, site, review_limit?, review_start_date?}`. Resolve an absent review limit to 100; resolve an absent review start date for every site to one calendar year before the customer's request date, using February 28 for a leap-day fallback.
2. Call `search_templates` read-only for template IDs 3387, 3386, 3388, 3389, and 3339. Stop with `FAILED` if required templates or MCP access are unavailable.
3. Create `run-state.json` with status `PRECHECK`, a unique run ID, `api_key_configured: true`, empty task records, and no secret values.
4. Read and execute `amazon-product-list` as one template task with step length 1000. Require a valid `LIST_EXPORTED` result and ordered unique ASIN records.
5. Pass exactly the full list stage ASIN array, ranks, and normalized site to one `amazon-product-details` template task with step length 1000. Require `DETAILS_EXPORTED` or an explicit partial result.
6. Pass the same full ASIN array, ranks, site, resolved review limit, and resolved all-site `review_start_date` to one `amazon-product-reviews` template task with step length 1000 when its schema exposes that field. For US/JP with a defaulted review limit, require the child result to record the 30-minute stop policy. Require `REVIEWS_EXPORTED` or an explicit partial result.
7. Pass all three stage-result files to `amazon-csv-export`. Require `CSV_READY` and file-level row counts.
8. Reconcile requested products, actual products, detail coverage, per-ASIN review counts, task identities, and files.
9. Set final status to `PARTIAL` when any ASIN has a failed/no-data stage; set `COMPLETE` only when all required files and reconciliations pass.

## Output format

Write and return:

```json
{
  "contract_version": "1.0",
  "status": "COMPLETE|PARTIAL|FAILED",
  "run_id": "amazon-...",
  "run_dir": "absolute-or-workspace-relative path",
  "request": {"keyword": "cup", "quantity": 30, "site": "US", "review_limit": 100, "review_start_date": "2025-08-07"},
  "actual_products": 30,
  "detail_coverage": {"covered": 30, "missing": []},
  "review_coverage": {"per_asin_counts": {}},
  "files": {"list": "...csv", "details": "...csv", "reviews": "...csv"},
  "warnings": [],
  "errors": []
}
```

## Done criteria

- All four child stages produced valid versioned JSON results.
- Every MCP-created task records template ID, template name, task ID, lot number, terminal status, and exported row count.
- List ASINs are unique and preserve search rank.
- Detail and review coverage reconcile to the actual ASIN list.
- Three UTF-8-BOM CSV files exist and pass the export contract.
- `run-state.json` contains no API key, MCP session ID, or signed export URL secret.
- The user-facing status and warnings match the final JSON result.
