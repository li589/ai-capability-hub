---
name: sciencepal
description: Professional agent for research in material, plasma, biology, protein and patent et al. Returns contains reports, codes, figures from corresponding agent.
homepage: https://sciencepal.ai/dashboard
metadata: {"clawdbot":{"emoji":"🔍","requires":{"bins":["python"], "env":["SCIENCEPAL_ACCESS_TOKEN"]},"primaryEnv":"SCIENCEPAL_ACCESS_TOKEN"}}
disable-model-invocation: true
---

# SDK Agent Run Download

## Overview

SciencePal is an agent for science for ai research, which includes general, biology, material, protein, plasma and patent agents. Use this skill when the user wants executable SciencePal SDK automation, not a generic API explanation. Prefer running or adapting the bundled scripts in `scripts/` instead of rewriting the same logic in chat.

## Prerequisites

Before using any scripts in this skill, you MUST ensure the sciencepal SDK is installed:

### Check Installation

```bash
python -c "import sciencepal" 2>/dev/null && echo "已安装" || echo "未安装"
```

### Install from Local WHL

If sciencepal is not installed, install it from the bundled whl file:

Here, "skill root" means the extracted package directory that contains `SKILL.md`, `scripts/`, `whl/`, and `.env`.

```bash
# Run from the extracted skill root directory
pip install $(find . -name "sciencepal_sdk-0.1.1-py3-none-any.whl")
```

**IMPORTANT**: Always verify installation succeeds before proceeding to run any scripts.

## Scripts

Use these scripts directly unless the user asks for a different interface:

1. `scripts/start_agent_run.py`
   Create a new agent run with `client.runs.initiate(...)` and print `thread_id` and `agent_run_id`.
2. `scripts/get_agent_run_status.py`
   Query current run status with `client.runs.get(agent_run_id)`.
3. `scripts/stop_agent_run.py`
   Stop a running agent task with `client.runs.stop(agent_run_id)`.
4. `scripts/download_sandbox_files.py`
   Resolve `sandbox_id` from `thread_id`, recursively list sandbox files, and download them to a local directory.
5. `scripts/poll_and_download.py`
   **One-click Script**: Polls task status until completion and automatically downloads sandbox files. Runs in the background without requiring user wait time.
6. `scripts/poll_with_notify.py`
   **Polling Script with Notifications**: Starts notifications, updates status every 60 seconds, and sends completion alerts. Notifications are written to the notifications/directory and pushed after heartbeat checks.
7. `scripts/common.py`
   Shared helpers for environment loading, client creation, terminal status checks, and recursive file download.

## Usage Rules

Follow this order:

1. Prefer adapting the existing bundled scripts over generating new code from scratch.
2. Print or persist both `thread_id` and `agent_run_id` immediately after task creation.
3. Query status from the SDK API only. Do not rely on Redis keys, SSE control events, or direct database reads for polling logic.
4. Treat `completed`, `failed`, and `stopped` as terminal statuses. Only trigger sandbox download for `completed`.
5. Report the running status every five minutes util task finishes or fails.
6. Resolve `sandbox_id` from `thread_id` through `client.sandbox.get_thread_sandbox(thread_id)`.
7. Preserve sandbox directory structure under the local output directory.
8. Fail clearly on missing token, missing `agent_run_id`, failed runs, or absent sandbox.

## Typical Workflow

When user wants to run a task and get results:

**Step 1: Start the task**
```bash
python scripts/start_agent_run.py --prompt "user's question"
```
Output: `{"thread_id": "xxx", "agent_run_id": "yyy"}`

**Step 2: Run poll_with_notify.py in background**
```bash
python scripts/poll_with_notify.py \
  --agent-run-id yyy \
  --thread-id xxx \
  --session-key "user:xxx" \
  --output-dir ./downloads/yyy \
  --status-file ./downloads/yyy/status.json &
```

This script will:
- Send startup notification immediately
- Poll status every 20 seconds
- Write notifications to `notifications/` directory on status changes
- Auto-download files when status is `completed`
- Send completion notification

**Step 3: Notify user immediately**
Tell user: "Task has started, ID=xxx. Running in the background, I will provide regular progress updates."

**Step 4: Heartbeat checks notifications**
Heartbeat will check `notifications/` directory and push messages to user.

**Step 5: Upload result zip file**
When task finishes successfuly, zip result files and send to user via messager.

## Implementation Rules

- Prefer the bundled scripts in this skill first. Only create repository-local example files when the user explicitly asks for code in the current repo.
- Use environment variables for secrets and endpoint configuration.
- Download files with binary-safe writes.
- Keep changes minimal and script-oriented. Do not introduce unnecessary abstractions, workers, or streaming unless the user explicitly asks for them.

## Output Expectations

When using or adapting this skill:

- explain which script is being used and why
- keep the scripts executable with `python`
- `SCIENCEPAL_BASE_URL` is `https://sciencepal.ai/api`
- print structured output that includes IDs, status, and downloaded file count where applicable
- keep comments brief and in the repository’s prevailing comment language
