# Host Directive Contract

> Version: `1`
> Machine entry: `scripts/host-directive-contract.mjs`
> Intake JSON path: `firstResponseContext.hostDirectiveContract`

## Purpose

`hostDirective` turns service-led traction from a text hint into a machine-readable host action request. It covers four host-side requests:

| Type | Target kind | Purpose |
| --- | --- | --- |
| `launch_skill` | `skill` | Ask the host to start or route to another installed skill. |
| `launch_expert` | `expert` | Ask the host to start or route to a visible expert or agent role. |
| `invoke_builtin_capability` | `builtin_capability` | Ask the host to use a built-in capability such as `preview_url` or `open_result_view`. |
| `start_subtask` | `subtask` | Ask the host or worker layer to run a bounded background task and report an output path. |

The service or Skill only proposes the directive. The host or Agent executes it and must return a receipt. A directive alone does not prove that the host has executed anything.

## Directive Shape

```json
{
  "schemaVersion": "fbs.hostDirective.v1",
  "directiveId": "hd_<sha12>",
  "type": "launch_skill",
  "target": {
    "kind": "skill",
    "id": "humanizer",
    "displayName": "去 AI 味 / 风格统一 Skill"
  },
  "arguments": {
    "intent": "de_ai_polish",
    "inputRef": "deliverables/de-ai-diff.md",
    "outputRelativePath": ".fbs/host-directives/humanizer-result.json"
  },
  "sameBindingRequired": true,
  "permissionMode": "host_confirm",
  "fallback": {
    "type": "user_visible_instruction",
    "message": "宿主暂不支持该动作时，请把下一步操作说明展示给用户，并保留当前写作链路。"
  },
  "receiptEventType": "host_directive_receipt",
  "serviceExecutionClaim": false
}
```

## Receipt Shape

```json
{
  "schemaVersion": "fbs.hostDirectiveReceipt.v1",
  "directiveId": "hd_<sha12>",
  "directiveType": "launch_skill",
  "receiptEventType": "host_directive_receipt",
  "status": "accepted",
  "hostExecutor": "workbuddy",
  "executedAt": "2026-06-13T00:00:00.000Z",
  "sameBindingPreserved": true,
  "outputRef": ".fbs/host-directives/humanizer-result.json",
  "error": null
}
```

## Permission Rules

- `host_policy`: host may execute under its existing policy, usually for display actions.
- `host_confirm`: host or Agent must confirm capability availability and permission before execution.
- `user_confirm`: user-facing confirmation is required before execution.
- `dry_run_only`: only validate and render the action; do not execute.

## Evidence Boundary

- `directive_validation_pass`: the JSON contract is well formed.
- `host_receipt_seen`: the host accepted, skipped, executed, or failed the request.
- `frontstage_visible_result`: the user can see the result in the WorkBuddy frontstage.
- `service_same_binding_join`: the service-side natural attribution spine can join the sample.

Only the last item proves natural same-binding service closure. The first three are necessary integration evidence but cannot be reported as product-credit closure.

## CLI

```powershell
node scripts/host-directive-contract.mjs summary --json
node scripts/host-directive-contract.mjs suite --json
node scripts/host-directive-contract.mjs validate --from .\data\host-directive-suite.json --json
node scripts/host-directive-contract.mjs receipt --from .\data\host-directive-suite.json --status accepted --json
```

The suite command is a dry-run review fixture. It does not launch any skill, expert, built-in capability, or worker.
