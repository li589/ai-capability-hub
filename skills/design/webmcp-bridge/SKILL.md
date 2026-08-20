---
name: webmcp-bridge
description: Discover and execute WebMCP tools on web pages via navigator.modelContextTesting API. Use when you need to interact with WebMCP-enabled pages, list registered tools, or call page tools through browser JavaScript evaluation. Requires chrome://flags/#enable-webmcp-testing to be enabled.
install_source: official
install_method: download
skill_id: official_HY0IHi6K
enabled_at: 1787232420824
version: 1.0.0
name_zh: WebMCP 浏览器桥接
---

# WebMCP Bridge

Interact with WebMCP tools registered on the current web page by evaluating
JavaScript through the browser's evaluate capability.

## How to Execute

All code in this skill must be run via **browser evaluate** tool.
The evaluate tool typically requires:

- `tabId` — the target browser tab ID
- `expression` — the JavaScript code string to execute

**Critical**: Browser evaluate does NOT support top-level `await`.
Always wrap async calls in an **async IIFE**:

```javascript
(async () => {
  const result = await navigator.modelContextTesting.listTools()
  return result
})()
```

## Check WebMCP Availability

```javascript
(async () => {
  const api = navigator.modelContextTesting || navigator.modelContext
  return { available: !!api }
})()
```

## List All Tools

```javascript
(async () => {
  const tools = await navigator.modelContextTesting.listTools()
  return tools.map(t => ({
    name: t.name,
    description: t.description,
    inputSchema: t.inputSchema,
    annotations: t.annotations
  }))
})()
```

Returns an array of tool definitions:
- `name` — identifier used when calling the tool
- `description` — what the tool does
- `inputSchema` — JSON Schema for arguments
- `annotations` — `readOnlyHint`, `destructiveHint`, `idempotentHint`

## Execute a Tool

Arguments must be passed as a **JSON string** (not a JS object):

```javascript
(async () => {
  const result = await navigator.modelContextTesting.executeTool(
    'tool_name',
    JSON.stringify({ param1: "value", param2: 42 })
  )
  return result
})()
```

## Parsing Results

Tool results follow MCP content format with nested JSON:

```json
{ "content": [{ "type": "text", "text": "{\"key\":\"value\"}" }] }
```

To get the actual data, parse `content[0].text`:

```javascript
(async () => {
  const raw = await navigator.modelContextTesting.executeTool(
    'code_read',
    JSON.stringify({ file: "html" })
  )
  const data = JSON.parse(raw.content[0].text)
  return data
})()
```

## Complete Workflow

1. **Check** — Verify `navigator.modelContextTesting` exists
2. **Discover** — `listTools()` to see available tools
3. **Read state** — Call tools with `readOnlyHint: true` annotations first
4. **Act** — Execute action tools with proper arguments
5. **Parse** — Extract data from `content[0].text` via `JSON.parse()`

## Argument Examples

### Simple parameters

```javascript
(async () => {
  const r = await navigator.modelContextTesting.executeTool(
    'code_read',
    JSON.stringify({ file: "html" })
  )
  return JSON.parse(r.content[0].text)
})()
```

### Array parameters

```javascript
(async () => {
  const r = await navigator.modelContextTesting.executeTool(
    'world_clock',
    JSON.stringify({ cities: ["北京", "东京"], format: "24小时制" })
  )
  return JSON.parse(r.content[0].text)
})()
```

### Nested object parameters

```javascript
(async () => {
  const r = await navigator.modelContextTesting.executeTool(
    'split_bill',
    JSON.stringify({
      total_amount: 256.5,
      participants: [{ name: "Alice", weight: 1 }, { name: "Bob", weight: 2 }],
      tip_percent: 10
    })
  )
  return JSON.parse(r.content[0].text)
})()
```

### No parameters

```javascript
(async () => {
  const r = await navigator.modelContextTesting.executeTool(
    'music_get_state',
    JSON.stringify({})
  )
  return JSON.parse(r.content[0].text)
})()
```

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| `await is only valid in async functions` | Top-level await not supported | Wrap in `(async () => { ... })()` |
| `Cannot read properties of undefined` | WebMCP API not available | Check `chrome://flags/#enable-webmcp-testing` is enabled |
| `listTools()` returns empty | Page tools not yet registered | Wait for page load, then retry |
| Tool call returns error | Arguments don't match schema | Check `inputSchema` from `listTools()` first |
| Result is nested JSON string | MCP content format | Parse via `JSON.parse(result.content[0].text)` |

## Tool Annotations Guide

| Annotation | Meaning | Strategy |
|-----------|---------|----------|
| `readOnlyHint: true` | No side effects | Safe to call anytime for context |
| `destructiveHint: true` | May delete/overwrite | Confirm with user before calling |
| `idempotentHint: true` | Repeatable safely | OK to retry on failure |

## Best Practices

1. **Always check schema first** — call `listTools()` and inspect `inputSchema`
   before constructing arguments
2. **Read before write** — call read-only tools to understand current state
3. **Re-discover after navigation** — tool set changes when the page URL changes
4. **Handle missing tools gracefully** — pages may dynamically unregister tools
