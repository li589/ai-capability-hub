---
name: "TRAE-browseruse"
description: "Browser automation guide. Invoke when user wants to browse websites, access URLs, scrape web content, test frontend UI, perform any browser interaction, or navigate to a specific URL and perform multi-step actions on it (click, verify elements, fill forms)."
user-invocable: false
---

# Browser Use Guide

Browser tools allow you to navigate the web, interact with pages, and extract data programmatically. Use this for browsing websites, accessing URLs, frontend/webapp development, and testing code changes.

Most browser operations are executed through the Exec tool (V8 sandbox), but some tools **must** be called as standalone toolcalls. See [Tool Calling Mode Reference](#tool-calling-mode-reference) for the complete classification.

---

## Tool Calling Mode Reference

### Tools callable via Exec (`await tools.*`)

These tools **MUST** be called inside Exec using `await tools.<name>(args)`:

| Category | Tools |
|----------|-------|
| Navigation | `browser_navigate`, `browser_navigate_back`, `browser_tabs` |
| Observation | `browser_snapshot`, `browser_take_screenshot`, `browser_get_attribute`, `browser_console_messages`, `browser_network_requests` |
| Interaction | `browser_click`, `browser_type`, `browser_hover`, `browser_scroll`, `browser_press_key`, `browser_select_option`, `browser_drag`, `browser_upload_file`, `browser_handle_dialog` |
| Advanced | `browser_evaluate`, `browser_wait_for` |
| Lock/Unlock | `browser_lock`, `browser_unlock` |

### Tools that MUST be called alone (one per turn)

| Tool | Reason |
|------|--------|
| `browser_waiting_for_user_interaction` | Requires pausing the AI execution flow and handing control to the user. You need its result to know when the user finishes. |

> **Rule**: These tools MUST be the **only** tool call in that turn. Do NOT combine them with other tool calls in the same response.

---

## CRITICAL - Lock/unlock workflow

> **Note:** If `browser_lock` and `browser_unlock` tools are not available in the current environment, skip this section entirely — proceed with browser operations directly without locking.

You and the user share the same Browser instance. Concurrent operations may cause state conflicts, operation failures, or other unpredictable behavior. To prevent control conflicts, you must strictly follow these rules:
1. Call `browser_lock` once at the beginning of your operation flow (e.g., before `browser_navigate`). You do NOT need to lock again for subsequent operations within the same flow.
2. Browser operations are allowed only after `browser_lock` has returned success.
3. If the lock is not successfully acquired, you must not perform any Browser operation.
4. Call `browser_unlock` only when you believe your entire operation flow is complete and the user can take over. Do NOT call unlock between individual operations.
5. Do NOT wrap every single Exec block with lock/unlock. The correct pattern is: `lock` → (all your operations across multiple Exec calls) → `unlock`.
6. The `browser_lock` and `browser_unlock` tool should not be called in parallel with other browser tools.

## CRITICAL - Need User Interaction

**`browser_waiting_for_user_interaction` MUST NOT be called inside Exec.** This is the one browser tool that must be called as a regular standalone toolcall, not through `await tools.*` in the Exec V8 sandbox.

**Note:** `browser_waiting_for_user_interaction` may not always be available in your tool list. If it is not provided, you do not need to use it — simply inform the user via text that their manual action is needed.

When you need the user to take over, directly call the `browser_waiting_for_user_interaction` tool with `reason` parameter as a normal toolcall.

Rules:
1. **NEVER** call `browser_waiting_for_user_interaction` inside Exec — it will not work. Always use it as a direct, independent toolcall.
2. Typical scenarios: logging in, completing CAPTCHAs, confirming sensitive actions, or performing actions that require human judgment.
3. This tool should not be called in parallel with other browser tools.
4. After the user completes the interaction, you may resume browser operations inside Exec as normal.

## IMPORTANT - Before interacting with any page

1. Use `browser_tabs` with action `"list"` to see open tabs and their URLs.
2. Use `browser_snapshot` to get the page structure and element refs before any interaction (click, type, hover, etc.).

## IMPORTANT - Waiting strategy

When waiting for page changes (navigation, content loading, animations, etc.), prefer short incremental waits (1-3 seconds) with `browser_snapshot` checks in between rather than a single long wait. For example, instead of waiting 10 seconds, do: wait 2s → snapshot → check if ready → if not, wait 2s more → snapshot again. This allows you to proceed as soon as the page is ready rather than always waiting the maximum time.

## Notes

- If two browser actions need to be performed sequentially, they should not be called in parallel.
- Iframe content is not accessible — only elements outside iframes can be interacted with.
- For nested scroll containers, use `browser_scroll` with `scrollIntoView: true` before clicking elements that may be obscured.

---

## Code Execution Tool

You have access to a code execution tool that runs JavaScript in an isolated V8 sandbox.

### CRITICAL: Always prefer Exec when the available tools can accomplish the task.

- ANY tool listed below MUST be called via `await tools.<name>(args)` inside Exec, NOT as a direct tool call.
- Use direct tool calls ONLY for tools that are NOT available inside Exec.
- Even for a single-step task, use Exec if that step involves an available tool.
- For multi-step tasks that share a clear linear flow (e.g., navigate → wait → snapshot → click → type), use a single Exec call.
- **However**, do NOT pack an entire long-running automation (polling loops, multi-minute waits, conditional branching across many pages) into one giant Exec block. Instead, split into multiple Exec calls so the LLM can inspect intermediate results and decide the next action.
- Exec gives you programmatic control: conditionals, error handling, sequential calls — use it for **short, focused sequences** (generally ≤ 20 lines). Do NOT use loops for polling or retrying.

### Call format

```
run_mcp(server_name="integrated_code_mode", tool_name="Exec", args={"code": "<your_js_code>"})
```

### Runtime environment

- Only ECMAScript standard built-ins are available (Array, Object, Math, JSON, Promise, etc.).
- The ONLY non-standard globals are: `tools`, `text`, `exit`.
- There is NO `console`, NO `fetch`, NO `require`, NO `process`, NO `setTimeout`, and NO file system or network access.
- Any attempt to call an undefined identifier will throw a ReferenceError.

### Instructions

- Use `await tools.<tool_name>(args)` to call tools — multiple calls in sequence are encouraged.
- Use `Promise.all([tools.a(x), tools.b(y)])` for concurrent tool calls.
- Use `text(value)` to output results to LLM (value will be stringified via JSON.stringify if not a string).
- Use `exit()` to stop execution early (already-produced text output is preserved).

### Error handling

- Tool call errors cause the Promise to reject — use `try/catch` to handle them gracefully.
- Unhandled exceptions terminate the script and return the error message as the result.
- If the script exceeds the execution time limit, it is forcibly terminated and an error is returned.
- `text()` output produced before an unhandled error is preserved in the response.

### Tool response structure

All browser tools return the same structure:

```typescript
interface BrowserToolResult {
  /** Array of content items */
  content: Array<{ type: "text"; text: string }>;
  /** 0 = success, non-zero = error */
  status: number;
}
```

- Most tools return a single `content` item with `type: "text"` containing the snapshot or result text.
- When `status !== 0`, the `text` field contains the error message.
- Access the text output: `result.content[0].text`

---

## Available Browser Functions

### Page Navigation

#### `browser_navigate` — Navigate to a URL and return a snapshot

```typescript
interface BrowserNavigateParams {
  /** Target URL */
  url: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
  /** Whether to open in a new tab */
  newTab?: boolean;
  /** Tab position: "active" (replace current) | "side" (open beside) */
  position?: "active" | "side";
  /** Custom HTTP headers for all requests in this tab (pass empty {} to clear) */
  extraHeaders?: Record<string, string>;
}
```

#### `browser_navigate_back` — Go back in browser history, return a snapshot

```typescript
interface BrowserNavigateBackParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_tabs` — Manage browser tabs (list/new/close/select/activate)

```typescript
interface BrowserTabsParams {
  /** Action type: "list" | "new" | "close" | "select" | "activate" */
  action: "list" | "new" | "close" | "select" | "activate";
  /** Tab index (required for close/select/activate). NOTE: this is the positional index, NOT tabId */
  index?: number;
}
```

> **`activate` vs `select`**: `select` switches to a tab but does NOT steal user focus. `activate` = select + bring the tab to foreground focus. Some pages only execute certain logic (e.g., timers, animations, event listeners) when they are the focused/active tab. If you notice a page not responding as expected after `select`, try `activate` instead.

### Page Observation (prefer snapshot over screenshot)

#### `browser_snapshot` — Get page accessibility snapshot (text tree with `[ref=N]` markers, includes URL/Title)

```typescript
interface BrowserSnapshotParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
  /** Snapshot strategy: "dom" (DOM mode) | "cdp" (Chrome AX Tree mode, default) */
  strategy?: "dom" | "cdp";
  /** Maximum traversal depth */
  maxDepth?: number;
  /** Maximum number of nodes */
  maxNodes?: number;
  /** Whether to include ignored nodes */
  includeIgnored?: boolean;
  /** Whether to return only interactive elements */
  interactive?: boolean;
  /** Whether to use compact output format */
  compact?: boolean;
  /** CSS selector to snapshot only the matching subtree */
  selector?: string;
}
```

#### `browser_take_screenshot` — Take a screenshot (use only when snapshot is insufficient, e.g. canvas, complex CSS, images)

```typescript
interface BrowserTakeScreenshotParams {
  /** Output filename */
  filename?: string;
  /** Whether to capture the full page (not just the viewport) */
  fullPage?: boolean;
  /** Capture only the element matching this ref */
  ref?: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_get_attribute` — Get an element attribute value

```typescript
interface BrowserGetAttributeParams {
  /** Element reference ID (from snapshot's [ref=N]) */
  ref: string;
  /** Attribute name to read (e.g. "href", "src", "class") */
  name: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_console_messages` — Get browser console log messages

```typescript
interface BrowserConsoleMessagesParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_network_requests` — Get captured network requests

```typescript
interface BrowserNetworkRequestsParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

### Element Interaction

#### `browser_click` — **Preferred click method.** Click an element by ref (supports double-click, mouse buttons, modifiers), returns snapshot

```typescript
interface BrowserClickParams {
  /** Element reference ID (from snapshot's [ref=N]) */
  ref: string;
  /** Whether to double-click */
  doubleClick?: boolean;
  /** Mouse button: "left" (default) | "right" | "middle" */
  button?: "left" | "right" | "middle";
  /** Modifier keys, e.g. ["Alt", "Control", "Meta", "Shift"] */
  modifiers?: string[];
  /** Horizontal offset from element's top-left corner in pixels. If omitted, clicks the horizontal center. */
  offsetX?: number;
  /** Vertical offset from element's top-left corner in pixels. If omitted, clicks the vertical center. */
  offsetY?: number;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_type` — Type text into an input element by ref, returns snapshot

```typescript
interface BrowserTypeParams {
  /** Element reference ID */
  ref: string;
  /** Text to type */
  text: string;
  /** Whether to clear existing content before typing. Use this to replace the current value instead of appending to it. Defaults to false. */
  clear?: boolean;
  /** Whether to press Enter after typing (submit form) */
  submit?: boolean;
  /** Whether to type character-by-character (simulates real typing for per-char event triggers) */
  slowly?: boolean;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_hover` — Hover over an element (triggers mouseenter/mouseover/mousemove), returns snapshot

```typescript
interface BrowserHoverParams {
  /** Element reference ID */
  ref: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_scroll` — Scroll the page or a specific element by direction/amount, returns snapshot

```typescript
interface BrowserScrollParams {
  /** Element reference to scroll (omit to scroll the page) */
  ref?: string;
  /** Scroll direction: "up" | "down" (default) | "left" | "right" */
  direction?: "up" | "down" | "left" | "right";
  /** Scroll amount in pixels */
  amount?: number;
  /** Horizontal scroll delta */
  deltaX?: number;
  /** Vertical scroll delta */
  deltaY?: number;
  /** Whether to scroll the ref element into the visible area */
  scrollIntoView?: boolean;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_press_key` — Dispatch a keyboard event to the currently focused element

```typescript
interface BrowserPressKeyParams {
  /** Key name. Common: "Enter", "Tab", "Escape", "Backspace", "ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight" */
  key: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_select_option` — Select option(s) in a select dropdown by value, returns snapshot

```typescript
interface BrowserSelectOptionParams {
  /** Select element reference ID */
  ref: string;
  /** Option value(s) to select (supports multi-select) */
  values: string[];
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_drag` — Drag from one element to another element or coordinate

```typescript
interface BrowserDragParams {
  /** Source element reference ID */
  sourceRef: string;
  /** Target element reference ID (mutually exclusive with targetX/targetY) */
  targetRef?: string;
  /** Target absolute X coordinate */
  targetX?: number;
  /** Target absolute Y coordinate */
  targetY?: number;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_upload_file` — Upload a file to a file input element

```typescript
interface BrowserUploadFileParams {
  /** File input element reference ID */
  ref: string;
  /** Element selector (alternative locator) */
  element?: string;
  /** File path to upload */
  filePath: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_handle_dialog` — Handle a browser dialog (alert/confirm/prompt)

```typescript
interface BrowserHandleDialogParams {
  /** Action: "accept" | "dismiss" */
  action?: "accept" | "dismiss";
  /** Text to enter in a prompt dialog */
  promptText?: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

### Advanced

#### `browser_evaluate` — Execute JavaScript in the page context

```typescript
interface BrowserEvaluateParams {
  /** JavaScript code to execute (use JSON.stringify for structured data extraction) */
  script: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_wait_for` — Wait for a condition (time/text appear/text disappear/selector appear)

> **Note**: The maximum value for `time` is **60 seconds**. For waits longer than 60s, use a loop (see [Polling Wait Pattern](#polling-wait-pattern)).

```typescript
interface BrowserWaitForParams {
  /** Seconds to wait (maximum: 60) */
  time?: number;
  /** Wait for this text to appear on the page */
  text?: string;
  /** Wait for this text to disappear from the page */
  textGone?: string;
  /** Wait for a CSS selector to match an element */
  selector?: string;
  /** Element state: "visible" | "hidden" | "attached" | "detached" */
  state?: string;
  /** Maximum timeout in milliseconds */
  timeout?: number;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_lock` — Lock the browser for exclusive control

```typescript
interface BrowserLockParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `browser_unlock` — Unlock the browser, release control

```typescript
interface BrowserUnlockParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
  /** Whether to hand control back to the user (waits for user confirmation before continuing) */
  handOverToUser?: boolean;
}
```

---

## Workflow Best Practices

### Snapshot-Driven Approach
1. **Snapshot first**: Always call `tools.browser_snapshot()` to understand the page before acting.
2. **Click by ref**: Use `tools.browser_click({ ref: N })` with the `[ref=N]` from snapshot output.
3. **Verify after action**: Snapshot again after critical actions to confirm the page state changed.
4. **Use evaluate() for data**: When you need structured data, prefer `tools.browser_evaluate({ script })` over parsing snapshot text.

### Cost Hierarchy (prefer top)

| Method | Cost | Use for |
|--------|------|---------|
| `browser_snapshot()` | Very low | Page understanding, finding elements |
| `browser_click`/`browser_type`/`browser_press_key` | Low | Interaction |
| `browser_evaluate()` | Low | Data extraction, DOM queries |
| `browser_take_screenshot()` | High | Visual-only info, canvas, layouts |

### Text Input Pattern
```javascript
const snap = await tools.browser_snapshot();
// Find the input ref from snapshot, e.g. [ref=3] textbox "Email"
await tools.browser_click({ ref: "3" });
await tools.browser_type({ ref: "3", text: "user@example.com" });
await tools.browser_press_key({ key: "Tab" });  // move to next field
await tools.browser_type({ ref: "4", text: "password123", submit: true });  // submit: true presses Enter
```

### Debugging White/Blank Pages
If a page appears blank (white screen) after navigation, use `tools.browser_console_messages()` to check for JavaScript errors or failed resource loads that explain why the page didn't render.

### After Navigation
Always wait after navigating before interacting:
```javascript
await tools.browser_navigate({ url: "https://example.com" });
await tools.browser_wait_for({ time: 2 }); // allow page to settle
const snap = await tools.browser_snapshot();
```

### Injecting Custom HTTP Headers
Use `extraHeaders` to add custom headers to all requests in the current tab (e.g., PPE environment headers):
```javascript
await tools.browser_navigate({
  url: "https://example.com",
  extraHeaders: { "x-use-ppe": "1", "x-tt-env": "ppe_xxx" }
});
await tools.browser_wait_for({ time: 2 });
const snap = await tools.browser_snapshot();
```
- Headers persist for the tab's lifetime — all subsequent requests (XHR, fetch, subresources) will carry them.
- To clear headers, navigate again with `extraHeaders: {}`.
- Headers only affect the current tab, not other tabs.

For SPA pages, `browser_wait_for` with a selector is more reliable:
```javascript
await tools.browser_click({ ref: "5" }); // SPA navigation link
await tools.browser_wait_for({ selector: ".page-content" }); // wait for content to render
const snap = await tools.browser_snapshot();
```

### Tab Activation Pattern
When a page requires foreground focus to function properly (e.g., timers, animations, event listeners), use `activate` instead of `select`:
```javascript
// 1. List all tabs to find the target
const tabs = await tools.browser_tabs({ action: "list" });
// tabs output example:
//   [0] https://example.com/dashboard
//   [1] https://example.com/settings  <-- we want this one

// 2. Activate by index (positional index from the list, NOT tabId)
await tools.browser_tabs({ action: "activate", index: 1 });

// 3. Snapshot to verify and get fresh refs
const snap = await tools.browser_snapshot();
```

### Data Extraction with browser_evaluate()
```javascript
// Get all links
const links = await tools.browser_evaluate({
  script: `JSON.stringify(Array.from(document.querySelectorAll('a[href]')).map(a => ({text: a.textContent.trim(), href: a.href})).filter(a => a.text).slice(0, 20))`
});
text(links);

// Get form values
const formData = await tools.browser_evaluate({
  script: `JSON.stringify({ email: document.querySelector('#email')?.value, name: document.querySelector('#name')?.value })`
});
text(formData);
```

### Multi-Step Orchestration
```javascript
await tools.browser_navigate({ url: "https://example.com" });
await tools.browser_wait_for({ time: 2 });
const snap = await tools.browser_snapshot();
// Parse snap to find the search input ref
await tools.browser_click({ ref: "3" });
await tools.browser_type({ ref: "3", text: "search query", submit: true });
await tools.browser_wait_for({ time: 2 });
const result = await tools.browser_snapshot();
text(result);
```

---

## Ref Lifecycle & Invalidation

Element refs (`[ref=N]`) are temporary identifiers generated at snapshot time. **They become invalid after any DOM change.** The common `ref not found in RefMap or DOM` error originates from this.

### Core Principles
- A ref is only valid **between the current snapshot and the next DOM mutation**
- Any operation that causes DOM reflow (navigation, AJAX, animations, dialog close) may invalidate refs

### Recommended Patterns

**Compact mode (preferred)** — act immediately after snapshot, no wait in between:
```javascript
const snap = await tools.browser_snapshot();
// Use the ref right away — do NOT insert a wait here
await tools.browser_click({ ref: "42" });
```

**Three-step pattern** — when you need to wait before acting:
```javascript
await tools.browser_wait_for({ text: "Loading complete" }); // 1. wait
const snap = await tools.browser_snapshot();                 // 2. snapshot
await tools.browser_click({ ref: "42" });                    // 3. act
```

**Fallback** — when refs are persistently unstable (e.g., frequently updating DOM), use `browser_evaluate`:
```javascript
await tools.browser_evaluate({
  script: `document.querySelector('.submit-btn').click()`
});
```

---

## Error Handling
- If a tool call fails, snapshot the page to understand current state before retrying.
- If an element ref is not found, the element may have been removed from DOM — re-snapshot to get fresh refs (see [Ref Lifecycle & Invalidation](#ref-lifecycle--invalidation)).
- After navigation that takes long, use `browser_wait_for({ selector })` to confirm page readiness instead of a fixed delay.
- If snapshot returns very few elements, the page may still be loading — wait and retry.

---

## Safety Rules
- Never type credentials. If a login page appears, call `browser_waiting_for_user_interaction` as a standalone toolcall (NOT inside Exec) with `reason: "Please log in"`.
- Never submit forms with sensitive data without user approval.
- Never bypass security prompts (CAPTCHAs, "site not secure" warnings).
- Never delete or modify user data without explicit approval.
