---
name: "TRAE-browseruse-external"
description: "Automate tasks in the user's own browser (Chrome on their machine). Invoke when the user says things like 'use my browser', 'open in my Chrome', 'use the browser on my computer', or wants to browse/interact/test web pages in their local Chrome."
user-invocable: false
---

# External Browser Use Guide

Browser tools that operate the user's **external Chrome browser** via the TRAE Chrome extension. All tools below are aliases of the standard browseruse tools, automatically routed to the external Chrome browser (native mode).

Most browser operations are executed through the Exec tool (V8 sandbox), but some tools **must** be called as standalone toolcalls. See [Tool Calling Mode Reference](#tool-calling-mode-reference) for the complete classification.

---

## Tool Calling Mode Reference

### Tools callable via Exec (`await tools.*`)

These tools **MUST** be called inside Exec using `await tools.<name>(args)`:

| Category | Tools |
|----------|-------|
| Navigation | `external_browser_navigate`, `external_browser_navigate_back`, `external_browser_tabs` |
| Observation | `external_browser_snapshot`, `external_browser_take_screenshot`, `external_browser_get_attribute`, `external_browser_console_messages`, `external_browser_network_requests` |
| Interaction | `external_browser_click`, `external_browser_type`, `external_browser_hover`, `external_browser_scroll`, `external_browser_press_key`, `external_browser_select_option`, `external_browser_drag`, `external_browser_upload_file`, `external_browser_handle_dialog` |
| Advanced | `external_browser_evaluate`, `external_browser_wait_for` |
| Lock/Unlock | `external_browser_lock`, `external_browser_unlock` |

### Tools that MUST be called alone (one per turn)

| Tool | Reason |
|------|--------|
| `browser_connect_plugin` | Connectivity check. Must run before any other browser tools in a session. You need its result to decide the next step. |
| `browser_setup_plugin` | Requires user interaction (confirm/skip). You need its result to decide whether to use external or built-in browser. |

> **Rule**: These tools MUST be the **only** tool call in that turn. Do NOT combine them with other tool calls in the same response. These tools do NOT use the `external_` prefix.

---

## CRITICAL - Tool Naming Convention

When operating the user's **external Chrome browser**, you MUST always use the `external_browser_*` prefix for ALL operational browseruse tool calls (e.g., `external_browser_navigate`, `external_browser_click`, `external_browser_snapshot`).

- **DO NOT** use `browser_navigate`, `browser_click`, or any unprefixed `browser_*` form for operational tools — those may target the built-in browser, NOT the user's external Chrome.
- Even if error messages or tool descriptions mention `browser_xxx` without the prefix, you must still use `external_browser_xxx` for operational tools to route the call to the external browser.
- The `external_` prefix is the **sole routing signal** that distinguishes external Chrome operations from built-in browser operations.

---

## CRITICAL - First-time Connection Check

Before using any external browser tools for the first time in a session, you MUST:

1. Call `browser_connect_plugin` to verify the Chrome extension is reachable.
2. If `browser_connect_plugin` returns `connected: false`, immediately call `browser_setup_plugin` to guide the user through setup.
3. Only proceed with browser operations after `browser_connect_plugin` succeeds or `browser_setup_plugin` completes.

If `browser_setup_plugin` returns that the user chose the built-in browser, stop using `external_*` tools and follow the `TRAE-browseruse` skill for standard browser usage.

> **CRITICAL**: `browser_connect_plugin` and `browser_setup_plugin` MUST each be called **alone** in a single turn — do NOT combine them with any other tool calls in the same response. Mixing them with other tools causes judgment issues because the AI cannot properly evaluate the connection/initialization result before deciding the next step.

> **NEVER** call `browser_waiting_for_user_interaction` when `connected: false`. That tool is for handing browser control to the user during an active session — it cannot fix a missing extension. The ONLY correct response to `connected: false` is `browser_setup_plugin`.

---

## CRITICAL - Before interacting with any page

1. Use `external_browser_tabs` with action `"list"` to see open tabs and their URLs.
2. Use `external_browser_snapshot` to get the page structure and element refs before any interaction (click, type, hover, etc.).

## IMPORTANT - Waiting strategy

When waiting for page changes (navigation, content loading, animations, etc.), prefer short incremental waits (1-3 seconds) with `external_browser_snapshot` checks in between rather than a single long wait. For example, instead of waiting 10 seconds, do: wait 2s → snapshot → check if ready → if not, wait 2s more → snapshot again. This allows you to proceed as soon as the page is ready rather than always waiting the maximum time.

## Notes

- If two browser actions need to be performed sequentially, they should not be called in parallel.
- Iframe content is not accessible — only elements outside iframes can be interacted with.
- For nested scroll containers, use `external_browser_scroll` with `scrollIntoView: true` before clicking elements that may be obscured.

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

#### `external_browser_navigate` — Navigate to a URL and return a snapshot

```typescript
interface ExternalBrowserNavigateParams {
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

#### `external_browser_navigate_back` — Go back in browser history, return a snapshot

```typescript
interface ExternalBrowserNavigateBackParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_tabs` — Manage browser tabs (list/new/close/select/activate)

```typescript
interface ExternalBrowserTabsParams {
  /** Action type: "list" | "new" | "close" | "select" | "activate" */
  action: "list" | "new" | "close" | "select" | "activate";
  /** Tab index (required for close/select/activate). NOTE: this is the positional index, NOT tabId */
  index?: number;
}
```

> **`activate` vs `select`**: `select` switches to a tab but does NOT steal user focus. `activate` = select + bring the tab to foreground focus. Some pages only execute certain logic (e.g., timers, animations, event listeners) when they are the focused/active tab. If you notice a page not responding as expected after `select`, try `activate` instead.

### Page Observation (prefer snapshot over screenshot)

#### `external_browser_snapshot` — Get page accessibility snapshot

```typescript
interface ExternalBrowserSnapshotParams {
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

#### `external_browser_take_screenshot` — Take a screenshot

```typescript
interface ExternalBrowserTakeScreenshotParams {
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

#### `external_browser_get_attribute` — Get an element attribute value

```typescript
interface ExternalBrowserGetAttributeParams {
  /** Element reference ID (from snapshot's [ref=N]) */
  ref: string;
  /** Attribute name to read (e.g. "href", "src", "class") */
  name: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_console_messages` — Get browser console log messages

```typescript
interface ExternalBrowserConsoleMessagesParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_network_requests` — Get captured network requests

```typescript
interface ExternalBrowserNetworkRequestsParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

### Element Interaction

#### `external_browser_click` — Click an element by ref, returns snapshot

```typescript
interface ExternalBrowserClickParams {
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

#### `external_browser_type` — Type text into an input element, returns snapshot

```typescript
interface ExternalBrowserTypeParams {
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

#### `external_browser_hover` — Hover over an element, returns snapshot

```typescript
interface ExternalBrowserHoverParams {
  /** Element reference ID */
  ref: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_scroll` — Scroll the page or a specific element, returns snapshot

```typescript
interface ExternalBrowserScrollParams {
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

#### `external_browser_press_key` — Dispatch a keyboard event

```typescript
interface ExternalBrowserPressKeyParams {
  /** Key name. Common: "Enter", "Tab", "Escape", "Backspace", "ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight" */
  key: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_select_option` — Select option(s) in a dropdown, returns snapshot

```typescript
interface ExternalBrowserSelectOptionParams {
  /** Select element reference ID */
  ref: string;
  /** Option value(s) to select (supports multi-select) */
  values: string[];
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_drag` — Drag from one element to another

```typescript
interface ExternalBrowserDragParams {
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

#### `external_browser_upload_file` — Upload a file to a file input element

```typescript
interface ExternalBrowserUploadFileParams {
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

#### `external_browser_handle_dialog` — Handle a browser dialog

```typescript
interface ExternalBrowserHandleDialogParams {
  /** Action: "accept" | "dismiss" */
  action?: "accept" | "dismiss";
  /** Text to enter in a prompt dialog */
  promptText?: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

### Advanced

#### `external_browser_evaluate` — Execute JavaScript in the page context

```typescript
interface ExternalBrowserEvaluateParams {
  /** JavaScript code to execute (use JSON.stringify for structured data extraction) */
  script: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_wait_for` — Wait for a condition

```typescript
interface ExternalBrowserWaitForParams {
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

#### `external_browser_lock` — Lock the browser for exclusive control

```typescript
interface ExternalBrowserLockParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_unlock` — Unlock the browser, release control

```typescript
interface ExternalBrowserUnlockParams {
  /** Whether to hand control back to the user (waits for user confirmation before continuing) */
  handOverToUser?: boolean;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

---

## Workflow Best Practices

### Snapshot-Driven Approach
1. **Snapshot first**: Always call `tools.external_browser_snapshot()` to understand the page before acting.
2. **Click by ref**: Use `tools.external_browser_click({ ref: N })` with the `[ref=N]` from snapshot output.
3. **Verify after action**: Snapshot again after critical actions to confirm the page state changed.
4. **Use evaluate() for data**: When you need structured data, prefer `tools.external_browser_evaluate({ script })` over parsing snapshot text.

### After Navigation
Always wait after navigating before interacting:
```javascript
await tools.external_browser_navigate({ url: "https://example.com" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
```

### Multi-Step Orchestration
```javascript
await tools.external_browser_navigate({ url: "https://example.com" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
await tools.external_browser_click({ ref: "3" });
await tools.external_browser_type({ ref: "3", text: "search query", submit: true });
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_snapshot();
text(result);
```

### Tab Activation Pattern
When a page requires foreground focus to function properly (e.g., timers, animations, event listeners), use `activate` instead of `select`:
```javascript
// 1. List all tabs to find the target
const tabs = await tools.external_browser_tabs({ action: "list" });
// tabs output example:
//   [0] https://example.com/dashboard
//   [1] https://example.com/settings  <-- we want this one

// 2. Activate by index (positional index from the list, NOT tabId)
await tools.external_browser_tabs({ action: "activate", index: 1 });

// 3. Snapshot to verify and get fresh refs
const snap = await tools.external_browser_snapshot();
```

### Data Extraction with external_browser_evaluate()
```javascript
// Get all links
const links = await tools.external_browser_evaluate({
  script: `JSON.stringify(Array.from(document.querySelectorAll('a[href]')).map(a => ({text: a.textContent.trim(), href: a.href})).filter(a => a.text).slice(0, 20))`
});
text(links);

// Get form values
const formData = await tools.external_browser_evaluate({
  script: `JSON.stringify({ email: document.querySelector('#email')?.value, name: document.querySelector('#name')?.value })`
});
text(formData);
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
const snap = await tools.external_browser_snapshot();
// Use the ref right away — do NOT insert a wait here
await tools.external_browser_click({ ref: "42" });
```

**Three-step pattern** — when you need to wait before acting:
```javascript
await tools.external_browser_wait_for({ text: "Loading complete" }); // 1. wait
const snap = await tools.external_browser_snapshot();                 // 2. snapshot
await tools.external_browser_click({ ref: "42" });                    // 3. act
```

**Fallback** — when refs are persistently unstable (e.g., frequently updating DOM), use `external_browser_evaluate`:
```javascript
await tools.external_browser_evaluate({
  script: `document.querySelector('.submit-btn').click()`
});
```

---

## Error Handling
- If a tool call fails, snapshot the page to understand current state before retrying.
- If an element ref is not found, the element may have been removed from DOM — re-snapshot to get fresh refs (see [Ref Lifecycle & Invalidation](#ref-lifecycle--invalidation)).
- After navigation that takes long, use `external_browser_wait_for({ selector })` to confirm page readiness instead of a fixed delay.
- If snapshot returns very few elements, the page may still be loading — wait and retry.

---

## Safety Rules
- Never submit forms with sensitive data without user approval.
- Never bypass security prompts (CAPTCHAs, "site not secure" warnings).
- Never delete or modify user data without explicit approval.
