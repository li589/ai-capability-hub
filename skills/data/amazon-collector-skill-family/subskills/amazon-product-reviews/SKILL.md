---
name: amazon-product-reviews
description: Collect Amazon reviews per supplied ASIN and site by directly calling the configured Bazhuayu MCP with site-specific template routing. Use for ASIN-only review requests or when the Amazon keyword orchestrator invokes its review stage. Do not discover products or collect product details.
---

# Amazon Product Reviews

## Mission

Produce review rows for every supplied ASIN in one template task. Default to 100 delivered reviews per ASIN, apply a recent-one-year start date for every site, and stop an unbounded US/JP default-limit task after 30 minutes.

## When to use

Use this Skill when a customer supplies ASINs and requests reviews, or after the list stage of `amazon-keyword-collector`. Default `review_limit` to 100. Accept an optional `review_start_date` for every supported site; when it is absent, default it to one calendar year before the customer's request date.

## Hard constraints

- Announce `amazon-product-reviews` and selected site route before MCP execution.
- Before the first MCP call, tell the user in Chinese: `免费版与个人版通过 MCP 调用每周最多 2000 条；团队版不限条数。`
- Validate ASINs, site, and review limit; preserve ASIN order. Record whether the review limit came from the customer or the default of 100.
- Route US to template 3389, JP to template 3339, and all other supported sites to template 3388.
- Refresh the selected template with `search_templates(id=...)` immediately before execution.
- Use returned `inputSchema[].field` names exactly and current `sourceTree` keys for source-backed fields.
- Create exactly one review-template task with the full normalized ASIN array. Never split the request into per-ASIN tasks.
- Set every current step-length field to `1000`. Do not invent a step parameter when the refreshed schema has none.
- For every site, validate a customer-supplied `review_start_date` as `yyyy-mm-dd`; otherwise derive it by subtracting one calendar year from the customer's request date, using February 28 for a leap-day fallback.
- For every site, resolve the current review-date field from the refreshed `inputSchema` and always send the resolved date. Fail the review stage when the template has no resolvable review-date field or rejects the full ASIN array; do not split and retry.
- For non-US/JP, send the customer review limit or default 100 to the current per-product-maximum field when the schema exposes it.
- For US/JP with a defaulted limit, start a 30-minute deadline when `execute_task` returns. At the deadline, call `start_or_stop_task(action="stop")`, wait for a terminal response, and export the collected rows. Do not apply this automatic stop when the customer explicitly supplied a limit.
- Detect `filterByStar` or equivalent filters in returned page URLs and expose them as warnings.
- Store no API key, MCP session ID, or signed URL secret.

## Core workflow

1. Normalize `{asins, site, review_limit?, review_start_date?}`. Resolve an absent limit to 100 and record `limit_source`. Resolve an absent review start date to one calendar year before the customer's request date and record its source in `run-state.json`.
2. Select and refresh template 3389 for US, 3339 for JP, or 3388 otherwise.
3. Resolve the exact review-date field for every route, the step-length field when present, and the non-US/JP per-product-maximum field when present. Stop with `FAILED` before task creation if the required date field is absent.
4. Call `execute_task` once with the full ASIN array, current marketplace key when present, resolved review start date, per-product maximum for non-US/JP when present, and step length `1000` when present.
5. For US/JP with `limit_source=default`, calculate `deadline_at = execute_task_response_time + 30 minutes`. Call `get_task_status(taskId)` every 10-30 seconds and stop the task immediately when the deadline is reached. Otherwise poll to a terminal state without the automatic deadline.
6. Record task ID, lot number, template ID, terminal status, parameter summary, limit source, deadline and stop reason when used, and row count.
7. Call `export_data(taskId, lotNo, page=N, pageSize=100)` for every terminal export page.
8. Group rows by ASIN, preserve export order, and retain at most the resolved review limit per ASIN.
9. Record zero-row and failed ASINs in coverage. Record detected star filters, page restrictions, and deadline stops in warnings.
10. Save raw rows and `stage-reviews.json`; update `run-state.json` to `REVIEWS_EXPORTED` or `PARTIAL`.

## Output format

```json
{
  "contract_version": "1.0",
  "stage": "reviews",
  "status": "REVIEWS_EXPORTED|PARTIAL|FAILED",
  "input": {"asins": ["B0CP9YB3Q4"], "site": "US", "review_limit": 100, "review_start_date": "2025-08-07"},
  "route": {"template_id": 3389, "mode": "single_task", "step_length": 1000},
  "runtime_policy": {"limit_source": "default", "max_runtime_minutes": 30, "stop_reason": "us_jp_default_limit_max_runtime"},
  "tasks": [{"task_id": "...", "lot_no": "...", "status": "stopped", "exported_rows": 100}],
  "records_path": "raw/reviews.json",
  "coverage": {"per_asin_counts": {"B0CP9YB3Q4": 100}, "failed": []},
  "warnings": [],
  "errors": []
}
```

## Done criteria

- The correct site-specific template and current schema were used.
- Exactly one cloud task contains the full normalized ASIN array; a rejected batch request is `FAILED` and is not split.
- Every current step-length field received `1000`.
- Every site received a `yyyy-mm-dd` review start date, sourced from the customer or the one-calendar-year default.
- Non-US/JP template inputs receive the customer limit or default 100 when their per-product-maximum field is present.
- A US/JP task with a defaulted limit is stopped at 30 minutes and records its deadline and stop reason; a customer-specified limit does not activate this automatic stop.
- Exported rows are truncated to the resolved limit for every ASIN.
- The task has a recorded terminal state and complete paginated export.
- Every ASIN has a count or failure outcome.
- Raw data and `stage-reviews.json` exist.
