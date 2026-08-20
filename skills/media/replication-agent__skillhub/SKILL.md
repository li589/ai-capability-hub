---
name: replication-agent
description: Authorized static website replication workflow. Use when the user wants to mirror a website they own or are authorized to copy, crawl same-root-domain pages and subdomains, localize HTML/CSS/JS/images/fonts/video/document assets, preview the result on localhost, inspect quality reports, or generate Nginx deployment artifacts. Do not use for unauthorized copying, brand impersonation, login/payment cloning, bypassing access controls, or public redistribution without rights.
---

# Replication Agent

## Core Rule

Before running a mirror, confirm the user owns the target site or has explicit permission. If authorization is unclear, ask for confirmation and stop until it is provided. Refuse requests that copy private areas, bypass paywalls/authentication, clone login/payment flows, or impersonate another brand.

## Resources

- `scripts/replication_agent.py`: crawl, render, download assets, rewrite links, and generate reports.
- `scripts/serve_replica.py`: preview replicated output locally.
- `scripts/deploy_static_mirror.py`: upload generated static output and Nginx config over SSH.
- `configs/replication_agent.example.json`: minimal config template.
- `references/usage.md`: command examples and configuration details.
- `references/release-checklist.md`: release gate and deployment checks.

Use a project-local venv. If no venv exists, create `.venv` before installing dependencies.

## Workflow

1. Clarify the target URL and authorization.
2. Create or reuse `.venv`, then install `requirements.txt` and Playwright Chromium.
3. Run `replication_agent.py` with `--ack-authorized`.
4. Inspect `quality_report.json`, `crawl_table.json`, and `resource_table.json`.
5. Preview locally with `serve_replica.py`.
6. Deploy only when quality checks pass and the user explicitly requests deployment.

## Quick Start

From this skill directory or after copying the skill resources into a workspace:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/replication_agent.py https://www.example.com/ --ack-authorized --force-refresh
```

For incremental updates, omit `--force-refresh`:

```bash
.venv/bin/python scripts/replication_agent.py https://www.example.com/ --ack-authorized
```

Preview aggregated localhost output:

```bash
.venv/bin/python scripts/serve_replica.py output/example.com/original --localhost --port 8700
```

## Quality Gate

Open `quality_report.json` before calling a mirror complete. Do not recommend public deployment if:

- `ready_for_release` is false.
- Page success rate is below the configured threshold.
- CSS, JS, image, font, video, or document resources remain remote or missing.
- Internal links point back to the source host.
- Browser Network shows same-domain 404s.
- Console errors block rendering.

For detailed commands and deployment examples, read `references/usage.md` and `references/release-checklist.md`.
