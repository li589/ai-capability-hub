# Dependency preflight and fallback contract

Run dependency preflight before price consent or payment:

```text
python scripts/check_dependencies.py
```

The script only inspects the runtime. It never installs software, elevates privileges, changes package sources, or writes secrets.

## Decision contract

| Result | Required behavior |
|---|---|
| `core_ready=false` | Stop. Payment cannot be safely invoked and must not be bypassed. |
| `core_ready=true`, `full_ready=true` | Offer full delivery and continue to fact, mode, and price confirmation. |
| `core_ready=true`, `full_ready=false` | List the exact missing optional capabilities and offer install, degraded delivery, or stop. |

Only run the fixed `install_commands` after explicit user approval. Never use `sudo`, administrator elevation, remote install scripts, or user-provided shell fragments. Explain that Mermaid browser components can be large and that hosted environments may prohibit installation. Re-run preflight after installation. If it still fails, return to degraded delivery or stop; do not create a payment order.

Agent capabilities such as `weixinpay`, image generation, DOCX/PDF creation, and image inspection are checked separately because a local Python script cannot discover Agent plugins.

## Full delivery

- Internal and external Markdown, DOCX, and PDF.
- Four Mermaid sources plus inspected SVG and PNG renders.
- Report cover, recruitment poster, and social square.
- Visual inspection of every document page and image.

## Degraded delivery

- Complete internal and external Markdown strategy.
- Conservative, base, and upside financial scenarios.
- Compliance decision, evidence register, assumptions, risk register, and stop conditions.
- Four Mermaid source blocks plus equivalent structured tables when rendering is unavailable.
- Exact marketing copy, canvas sizes, palette, composition, and image-generation briefs.

Never claim a missing DOCX, PDF, SVG, PNG, or marketing image was generated.

## Hash binding

Before payment, add `delivery_mode`, `dependency_report_digest`, and `promised_artifacts` to the confirmed stable-key UTF-8 JSON used for `input_hash`. A mode change requires a new hash and confirmation before order creation. After payment, never silently change the mode or hash. Restore the promised runtime within the entitlement window or use support/refund handling.
