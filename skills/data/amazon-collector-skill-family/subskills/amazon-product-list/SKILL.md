---
name: amazon-product-list
description: Collect a ranked Amazon product list for one keyword, quantity, and site by directly calling the configured Bazhuayu MCP. Use for list-only requests or when the Amazon keyword orchestrator invokes its list stage. Do not collect product details or reviews.
---

# Amazon Product List

## Mission

Produce an ordered, ASIN-deduplicated product list for one Amazon keyword and site, limited to the requested quantity, with a resumable `LIST_EXPORTED` stage result.

## When to use

Use this Skill for list-only keyword requests or as the first stage of `amazon-keyword-collector`. Require `keyword`, `quantity`, and `site`.

## Hard constraints

- Announce `amazon-product-list` before MCP execution.
- Before the first MCP call, tell the user in Chinese: `免费版与个人版通过 MCP 调用每周最多 2000 条；团队版不限条数。`
- Normalize site to one of `AU, CA, UK, US, IN, DE, SE, NL, BE, JP, IT, FR, ES, PL, TR, MX, AE, SA, IE, SG, BR, EG`.
- Use template ID 3387 only.
- Call `search_templates(id=3387)` immediately before execution and use the returned `inputSchema[].field` names exactly.
- For source-backed fields, pass only a `sourceTree.options[].key` returned in the same lookup.
- Use keyword mode when the site key is present. Use full-search-URL mode when the site key is absent.
- Create exactly one list-template task per request. Set the current step-length field to `1000`.
- Preserve first-seen search order and the first non-empty occurrence of each ASIN.
- Record actual count when fewer unique ASINs are returned.
- Store no API key, MCP session ID, or signed URL secret.

## Core workflow

1. Validate keyword and quantity `1–1000`; normalize the site.
2. Read template 3387 and resolve fields by their current labels: search term, marketplace, full search URL, product quantity, and step length.
3. For keyword mode, pass the keyword as a one-element array, the site as the current option key, the quantity as a number, and step length `1000`.
4. For URL mode, construct `https://<site-domain>/s?k=<URL-encoded-keyword>`, pass it as a one-element array, pass quantity as a number, and step length `1000`.
5. Use these domains: `US amazon.com; UK amazon.co.uk; JP amazon.co.jp; AU amazon.com.au; CA amazon.ca; IN amazon.in; DE amazon.de; SE amazon.se; NL amazon.nl; BE amazon.com.be; IT amazon.it; FR amazon.fr; ES amazon.es; PL amazon.pl; TR amazon.com.tr; MX amazon.com.mx; AE amazon.ae; SA amazon.sa; IE amazon.ie; SG amazon.sg; BR amazon.com.br; EG amazon.eg`.
6. Call `execute_task` with the exact template name, JSON-string parameters, and a unique task name containing run ID, site, and stage.
7. Poll `get_task_status(taskId)` every 10–30 seconds until `completed`, `stopped`, or failed. Record every terminal response.
8. Call `export_data(taskId, lotNo, page=N, pageSize=100)` from page 1 through `totalPages`. Use MCP-returned rows as stage data.
9. Extract ASIN and product URL from each row, deduplicate by ASIN, preserve first-seen order, and truncate to quantity.
10. Save raw rows and `stage-list.json`; update `run-state.json` to `LIST_EXPORTED`.

## Output format

```json
{
  "contract_version": "1.0",
  "stage": "list",
  "status": "LIST_EXPORTED|PARTIAL|FAILED",
  "input": {"keyword": "cup", "quantity": 30, "site": "US"},
  "template": {"template_id": 3387, "template_name": "..."},
  "task": {"task_id": "...", "lot_no": "...", "status": "completed", "exported_rows": 30},
  "records_path": "raw/list.json",
  "asins": [{"rank": 1, "asin": "B0CP9YB3Q4", "product_url": "..."}],
  "requested_count": 30,
  "actual_count": 30,
  "warnings": [],
  "errors": []
}
```

## Done criteria

- Template schema was refreshed in the current run.
- Task identity and terminal status are recorded.
- All export pages were read.
- Output ASINs are non-empty, unique, ordered, and no greater than quantity.
- Raw data and `stage-list.json` exist.
- Status and warnings match counts and MCP results.
