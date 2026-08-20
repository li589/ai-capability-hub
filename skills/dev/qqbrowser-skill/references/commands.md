# Command Reference

> Full command list for `qqbrowser-skill`. Load this when you need exact flag names, argument shapes, or command semantics.
>
> For Session commands see also [session-lifecycle.md](./session-lifecycle.md).

## Session Management

```bash
browser_start_session --sessionId <id> [--title "<title>"] [--color <color>] [--initialUrl <url>]
browser_end_session --sessionId <id>
```

> Isolation mode is fixed to `enforce` — `browser_start_session` does not accept an `--isolation` flag.

## Navigation

```bash
browser_go_to_url --url <url>
browser_go_back
browser_wait --seconds <n>              # Default 3s
```

## Snapshot & Screenshot

```bash
browser_snapshot                        # Element indices (for interaction)
browser_snapshot --markdown             # Markdown (for reading)
browser_screenshot [--full] [--annotate]
```

### 📖 `browser_snapshot --markdown`: Usage Guide

`--markdown` returns clean, human-readable Markdown of the page (ads/nav/scripts stripped, **no element indices**). It is designed to feed page content **into the AI's context for reading**, not to drive further browser commands.

**✅ Use it when:**

- **Reading / summarizing** page content (articles, docs, search results, product detail pages)
- **One-off Q&A** about a page ("what does this article say?", "summarize this doc")
- Running in **non-recording mode (Branch C)** — the output is consumed by the AI once and discarded

**❌ Do NOT use it when:**

- Inside `task_begin` / `task_end` (**recording mode, Branch B**) — Markdown output is a text snapshot and cannot be reliably replayed
- You need **structured data** (JSON, specific fields, machine-consumable output) → use `browser_eval_content_js`
- You need to **iterate** over a list, paginate, or extract many items → use `browser_eval_content_js` + `browser_find_and_act`
- You need to **click / input / interact** with elements → use `browser_snapshot` (default mode, returns indices)

**Rule of thumb:** `--markdown` output goes to the **AI's eyes** (read once, then discarded). If the output needs to be consumed by **code, a playbook, or a later step**, use `browser_eval_content_js` instead.

## Click & Input

```bash
browser_click_element --index <id>
browser_dblclick_element --index <id>
browser_focus_element --index <id>
browser_input_text --index <id> --text "<content>"
```

## Scroll

```bash
browser_scroll_down [--amount <px>]
browser_scroll_up [--amount <px>]
browser_scroll_to_text --text "<text>"
browser_scroll_to_top / browser_scroll_to_bottom
browser_scroll_by --direction <dir> --pixels <n> [--index <id>]
browser_scroll_into_view --index <id>
```

## Keyboard

```bash
browser_keypress --key <key>
browser_keyboard_op --action type --text "<content>"
browser_keyboard_op --action inserttext --text "<content>"
browser_keydown --key <key> / browser_keyup --key <key>
```

## Dropdown & Checkbox

```bash
browser_get_dropdown_options --index <id>
browser_select_dropdown_option --index <id> --text "<option>"
browser_check_op --index <id> --value / --no-value
```

## Find and Act (Semantic Locators)

```bash
browser_find_and_act --by <role|text|label|placeholder|testid|css> --value "<v>" --action <click|fill|type> [--actionValue "<v>"] [--name "<n>"] [--nth <n>]
```

> `--nth`: 1-based index for list iteration (`--nth 1` = first match, `--nth 2` = second). Use `by: "css"` + `--nth` for loops.

## Get Information & State

```bash
browser_get_info --type <text|url|title|html|value|attr|count|box|styles|list_selector> [--index <id>] [--attribute <name>]
browser_check_state --state <visible|enabled|checked> --index <id>
```

> **`list_selector`**: Auto-detect CSS selector for list iteration. Pass any list item's index → returns `{"selector": "...", "count": N, "samples": [...]}`. Use the returned selector in `find_and_act --by css --value <selector> --nth N`.

## JavaScript Evaluation

```bash
browser_eval_content_js --script "<js_code>"
browser_eval_content_js --script "<base64>" --base64
```

## Download

```bash
browser_download_file --index <id>
browser_download_url
```

## Tab Management

```bash
browser_tab_open --url <url>
browser_tab_list
browser_tab_switch --tabId <n>
browser_tab_close --tabId <n>
```

## Dialog

```bash
browser_dialog --action <accept|dismiss> [--text "<input>"]
```

## Replay & Playbook

```bash
playbook_list                              # List available playbooks
browser_replay --script <path> [--variables '{"key":"value"}']
```

> ⚠️ `browser_replay` can take **up to 10 minutes**. Wait patiently — do NOT interrupt.

### `browser_replay` Output Format

```json
{
  "success": true,
  "total_steps": 5,
  "completed_steps": 5,
  "step_results": [
    {
      "index": 0,
      "action": "browser_go_to_url",
      "description": "...",
      "success": true,
      "result": "Success! Navigated to ..."
    },
    {
      "index": 1,
      "action": "browser_eval_content_js",
      "description": "提取数据",
      "success": true,
      "result": "{\"title\":\"...\",\"content\":\"...\"}"
    }
  ],
  "duration_ms": 12345,
  "summary": "Replay completed successfully: 5/5 steps in 12345ms."
}
```

**How to use the output (especially for composite tasks):**

- `success`: Check overall success/failure. If `false`, check `failed_step` for error details.
- `step_results[N].result`: Contains the return value of each step. **For `browser_eval_content_js` steps, this is the extracted data (usually JSON string)** — parse it for use in subsequent AI processing or next playbook's variables.
- For composite pipelines: find all `eval_content_js` steps in `step_results`, parse their `result` field to get structured data for AI mediation.

## Task Recording

```bash
task_begin --description "<desc>"
task_end
task_latest                                # Get most recent recording
```

> After `task_end`, raw recordings are NOT replay-ready. See [playbook.md](./playbook.md) to generate a proper playbook.

## Utility

```bash
browser_done --success --text "<msg>"
status
list
```
