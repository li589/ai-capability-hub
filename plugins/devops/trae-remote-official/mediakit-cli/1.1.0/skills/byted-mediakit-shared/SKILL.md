---
name: byted-mediakit-shared
version: '1.0.0'
license: 'MIT'
description: '1. mediakit-cli: supports a variety of operations such as audio/video processing, editing, and images, with some capabilities covering both cloud and local modes;2. mediakit-cli shared: environment checks, initialization config, command structure, authentication config, async task responses, and error handling.'
permissions:
  - shell
metadata:
  requires:
    bins: ['mediakit-cli']
  cliHelp: 'mediakit-cli --help'
  product: mediakit-cli/skills
  domain: shared
  capability_count: 14
---

# MediaKit Shared Rules

This skill guides you on how to operate media resources via mediakit-cli, along with the common rules and considerations during invocation.

## Preflight Checks

### Dependency Installation

Before first use, confirm the CLI is installed:

```bash
# Install
npm install -g @volcengine/mediakit-cli

# Verify
mediakit-cli --version
```

### SKILL Installation

```bash
# One command installs the Skills into every supported agent on your machine
npx skills add volcengine/mediakit-cli -g -y
```

### Authentication Info Check

Priority: environment variables > config file (file path `~/.mediakit/config.json`)

#### Field Descriptions

- Environment variables / config file: `MEDIAKIT_API_KEY`, `MEDIAKIT_ENDPOINT`, `MEDIAKIT_SURFACE`, `MEDIAKIT_RUNTIME`

| Variable            | Required               | Description                                                                                                                                             |
| ------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MEDIAKIT_API_KEY`  | Required in cloud mode | API authentication token                                                                                                                                |
| `MEDIAKIT_ENDPOINT` | No                     | API endpoint                                                                                                                                            |
| `MEDIAKIT_SURFACE`  | No                     | Request source header `x-surface`; default `cli`, Skill recommends `skill`, Plugin recommends `plugin`, finally reported as `cli/skill` or `cli/plugin` |
| `MEDIAKIT_RUNTIME`  | No                     | Request source header `x-runtime`; set per host to `claude`, `arkclaw`, etc.; falls back to environment detection or `unknown` when not configured      |

When any required field is missing, terminate execution and output a list of all missing items along with remediation suggestions. Exception: in TRAE plugin runtime, a missing `MEDIAKIT_API_KEY` is handled by the platform Connector — see the next section.

#### API Key Hosting in TRAE (Connector)

When running as a TRAE plugin, `MEDIAKIT_API_KEY` is injected by TRAE's Connector credential hosting (`manual_token`). The user fills in the API Key once in TRAE's authorization form; the authorization is stored at the user-account level and reused across devices and cloud tasks.

Rules for the agent in TRAE plugin runtime:

- Do NOT treat cloud capabilities as unavailable, and do NOT switch to alternative non-MediaKit tools, just because an API Key looks missing. Invoke the cloud command directly: TRAE triggers the Connector authorization form on invocation when no credential is stored yet.
- If a cloud call fails with an authentication error, instruct the user to complete (or redo) the plugin's Connector authorization in TRAE. Do NOT ask the user to paste the API Key into the conversation, and do NOT write the key into shell profiles or config files.
- Never print, log, or echo the API Key value.

Cloud invocations automatically carry `x-surface` / `x-runtime`. Header priority is: environment variables > `~/.mediakit/config.json` > default value / environment detection. When this Skill/Plugin invokes cloud capabilities via `mediakit-cli`, the runtime environment should inject `MEDIAKIT_SURFACE=skill|plugin` and `MEDIAKIT_RUNTIME=<host>`; the CLI preserves the original artifact prefix and reports `x-surface=cli/skill|cli/plugin`. If not explicitly configured, the CLI defaults to `x-surface=cli`, and `x-runtime` falls back in order to `IDENTITY_NAME` / `OPENCLAW_SERVICE_MARKER` environment detection, and finally `unknown`.

### Source Reporting Constraints

- When a Skill invokes `mediakit-cli`, it must explicitly set `MEDIAKIT_SURFACE=skill`, and must not rely on the user's existing environment variables.
- When a Plugin invokes `mediakit-cli`, it must explicitly set `MEDIAKIT_SURFACE=plugin`, and must not reuse the Skill's value.
- It is recommended to also explicitly set the host environment identifier `MEDIAKIT_RUNTIME=<host>`; if not set, the CLI falls back to the environment detection value or `unknown`.

```bash
MEDIAKIT_SURFACE=skill MEDIAKIT_RUNTIME=<runtime> mediakit-cli editing add-image-to-video

MEDIAKIT_SURFACE=plugin MEDIAKIT_RUNTIME=<runtime> mediakit-cli editing add-image-to-video
```

## CLI Usage

### Initialization Config

For first-time use, it is recommended to run the initialization wizard first:

```bash
mediakit-cli init
```

For non-interactive Agent initialization, the request source and runtime config can be written explicitly:

```bash
mediakit-cli init --mode cloud-first --api-key <key> --runtime <runtime> --surface cli --yes
mediakit-cli init --mode local-first --api-key <key> --endpoint <url> --output-path ~/mediakit-output --runtime <runtime> --surface cli --credential-store config --yes
```

Common commands after initialization are as follows:

```bash
# View current config
mediakit-cli config show

# Switch the default mode to local-first
mediakit-cli config set mode local-first

# Switch the default mode to cloud-first
mediakit-cli config set mode cloud-first

# Refresh environment checks and view dependency status
mediakit-cli doctor
```

### Command Structure

MediaKit CLI uniformly uses the `domain + tool` invocation pattern:

```bash
mediakit-cli {domain} {tool} [flags]
```

Common help commands:

```bash
# View all domains
mediakit-cli --domains

# View the tool list under a specific group
mediakit-cli {domain} --help

# View the parameters of a specific tool
mediakit-cli {domain} {tool} --help

# Dynamically discover tool capabilities and return structures
mediakit-cli {domain} {tool} --schema
mediakit-cli --local {domain} {tool} --schema
```

The domains currently covered by the artifacts include: `editing`, `video`.

### Schema Discovery

Every capability command supports `--schema`, which lets the Agent dynamically read tool capabilities without requiring the mandatory business parameters to be passed.

The return structure includes:

- `name`: tool name, in snake_case, e.g. `add_image_to_video`
- `description`: tool description, automatically including `Mode` and `Async` information
- `input_schema`: input parameter JSON Schema
- `output_schema`: the return structure under the current execution mode

Output differentiation rules:

- By default, parse the return surface according to the global `mode` configuration
- `--local ... --schema` outputs the local-mode return surface; local mode directly returns the final result fields
- Cloud async tools output `task_id` / `request_id`, and describe the `query-task` completed-state result in `final_result`
- `query-task` is cloud only; the schema describes the task status and completed-state result

Examples:

```bash
mediakit-cli editing trim-video --schema
mediakit-cli --local editing trim-video --schema
```

### Single-Invocation Mode Override

In addition to setting the default mode via `config set mode`, a temporary override that only applies to the current command is also supported:

```bash
mediakit-cli --local editing add-image-to-video

mediakit-cli --cloud editing add-image-to-video
```

Additional rules:

- `--local` / `--cloud` only affect the current command and do not modify the global `config.mode`
- `--local` and `--cloud` are mutually exclusive and cannot be passed at the same time

## Async Tasks

After successfully submitting an async media processing task, a `task_id` field is returned. Query the result via the `shared query-task` command.

```bash
mediakit-cli shared query-task --task-id <task_id>
```

## local / cloud Constraints

- `query-task` is a **cloud only** tool
- query-task is not supported in local mode
- The capabilities of this round are mainly executed in the cloud; if explicit declaration is needed, prefer using `--cloud`

### Cloud Mode Media Input Supplement

- When a command executes with the `--cloud` or `cloud-first` strategy, media input parameters (such as `video_url`, `audio_url`, `image_url`, `subtitle_url`, `sub_image_url`, and their corresponding array/object subfields) can be passed as an `http://` / `https://` URL, a `mediakit://...` file_id, or a local file path
- `http://` / `https://` URLs and `mediakit://...` file_ids are submitted as-is; local file paths are first uploaded by the CLI as a `mediakit://...` file_id and then submitted to the cloud tool
- The parameter descriptions in each tool's reference come from the original APIHub/OpenAPI field descriptions; if a public URL or HTTP/HTTPS URL is written there, it indicates the resource form ultimately received by the cloud API, and does not restrict the CLI cloud mode's local-path preprocessing capability

### Local Mode Supplement

- Local output directory priority: `--output-path` > `MEDIAKIT_OUTPUT_PATH` > config `output_path` > `~/.mediakit/temp`
- When `--output-path` points to a specific media file name, it is used directly as the final output file; otherwise, `{original_filename}_{tool_name}.{ext}` is generated based on the input file name, with a 6-digit random number appended on collision
- When a file name cannot be extracted from the input URL or path, it falls back to `{tool_name}-{UnixNano}.{ext}`
- Local mode depends on `ffmpeg` / `ffprobe`; when missing, the error provides an `install_guide`
- Local mode media processing output must conform to the interface response schema, and outputting internal execution metadata is prohibited

### Error Responses

- CLI cloud mode passes through the original error object returned by the API as-is, without extracting `message`
- CLI local mode returns a structured error: `{"error":{"type":"...","code":"...","message":"..."}}`
- MCP error_response passes through the original error content as-is, with the dict used directly as the value of the `error` field

## Idempotency Parameter Maintenance

| Parameter       | Purpose                          | Maintenance Suggestion                                                                              |
| --------------- | -------------------------------- | --------------------------------------------------------------------------------------------------- |
| `client_token`  | Actively control idempotency     | Reuse the same value on request retry; pass a new unique value to force re-execution                |
| `callback_args` | Pass through callback parameters | Recommended to maintain together with `client_token` for callback reconciliation and retry tracking |

Additional rules:

- `client_token` length must not exceed 64 characters
- `callback_args` can be used for callback pass-through and reconciliation tracking

## Polling Strategy

| Parameter               | Description                       | Default |
| ----------------------- | --------------------------------- | ------- |
| `poll-interval-seconds` | Polling interval                  | 10s     |
| `max-poll-attempts`     | Number of polls; 0 means no query | 0       |
| `poll-complete`         | Block until terminal state        | -       |
