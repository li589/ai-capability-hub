---
name: amazon-product-details
description: Collect Amazon product details for one or more supplied ASINs and a site by directly calling the configured Bazhuayu MCP. Use for ASIN-only detail requests or when the Amazon keyword orchestrator invokes its detail stage. Do not discover products or collect reviews.
---

# Amazon Product Details

## Mission

Produce complete product-detail rows and explicit per-ASIN coverage for a supplied ordered ASIN list on one Amazon site.

## When to use

Use this Skill when a customer supplies one or more ASINs and requests product details, or after the list stage of `amazon-keyword-collector`.

## Hard constraints

- Announce `amazon-product-details` before MCP execution.
- Before the first MCP call, tell the user in Chinese: `免费版与个人版通过 MCP 调用每周最多 2000 条；团队版不限条数。`
- Require one supported site and at least one 10-character alphanumeric ASIN.
- Normalize ASINs to uppercase, deduplicate them, and preserve first-seen order.
- Use template ID 3386 only.
- Call `search_templates(id=3386)` immediately before execution and use current `inputSchema[].field` names exactly.
- Pass the normalized site only when the current schema exposes the marketplace field; use its current `sourceTree` key when source-backed.
- Create exactly one detail-template task with the full normalized ASIN array. Set the current step-length field to `1000`.
- Preserve one success, no-data, or error coverage outcome per requested ASIN.
- Store no API key, MCP session ID, or signed URL secret.

## Core workflow

1. Validate and normalize `{asins, site}` and optional rank mappings.
2. Read template 3386 and resolve the current ASIN, marketplace, and step fields.
3. Build parameters with the full normalized ASIN array, normalized marketplace key, and step length `1000`.
4. Call `execute_task` with the exact template name and a unique detail-stage task name.
5. Poll `get_task_status` every 10–30 seconds to a terminal state.
6. Export every page with `export_data(..., pageSize=100)`.
7. Match exported rows back to requested ASINs using explicit ASIN fields, then the input field as fallback.
8. Add a `no_data` coverage entry for every requested ASIN without a returned row.
9. Save raw rows and `stage-details.json`; update `run-state.json` to `DETAILS_EXPORTED` or `PARTIAL`.

## Output format

```json
{
  "contract_version": "1.0",
  "stage": "details",
  "status": "DETAILS_EXPORTED|PARTIAL|FAILED",
  "input": {"asins": ["B0CP9YB3Q4"], "site": "UK"},
  "template": {"template_id": 3386, "template_name": "..."},
  "task": {"task_id": "...", "lot_no": "...", "status": "completed", "exported_rows": 1},
  "records_path": "raw/details.json",
  "coverage": {"requested": 1, "covered": 1, "missing": []},
  "warnings": [],
  "errors": []
}
```

## Done criteria

- Current template schema determined all submitted parameter keys.
- All export pages were read and associated with requested ASINs.
- Every ASIN has an explicit coverage outcome.
- Raw data, task identity, and `stage-details.json` exist.
- Missing products produce `PARTIAL`, not `COMPLETE`.
