# Query Task

## Capability Description
Query async task result and task information by task_id.

## Execution

| Item | Description |
|------|------|
| Domain | `shared` |
| Tool | `query-task` |
| Async | `No` |
| Local supported | `No` |
| Mode notes | cloud only; this command is used to query the status of cloud async tasks. |
| Idempotency behavior | This command has no additional idempotency parameter requirements. |

## Parameters
| Parameter | CLI flag | Type | Required | Default | Description |
|------|----------|------|------|--------|------|
| task_id | `--task-id` | string | Yes | - | The ID of the task to query. |
| poll_interval_seconds | `--poll-interval-seconds` | number | No | 10 | Polling interval in seconds. |
| max_poll_attempts | `--max-poll-attempts` | integer | No | 0 | Maximum number of polls; 0 means no automatic polling. |
| poll_complete | `--poll-complete` | boolean | No | - | Whether to poll until the task completes. |

## Invocation Example
```bash
mediakit-cli shared query-task \
  --task-id task_demo_001 \
  --poll-interval-seconds 10 \
  --max-poll-attempts 12
```

## Acceptance Response
After an async media processing command is submitted successfully, it usually first returns an acceptance result as follows:

```json
{
  "task_id": "task_demo_001",
  "request_id": "req_demo_001"
}
```

## Output Format
```json
{
  "success": true,
  "task_id": "task_demo_001",
  "task_type": "extract-audio",
  "status": "completed",
  "result": {
    "audio_url": "https://example.com/audio.m4a"
  },
  "request_id": "req_demo_001"
}
```

## Task Result Query
This command is itself the task query entry point, so no further query is needed.

- Current command: `mediakit-cli shared query-task`
