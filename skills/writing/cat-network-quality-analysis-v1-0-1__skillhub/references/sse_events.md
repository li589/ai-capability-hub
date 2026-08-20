# CAT SSE 事件参考

`ProcessAIEventsStream` API 返回的 SSE 事件类型清单。AI 无需直接解析 SSE（脚本已处理），仅供理解脚本内部行为。

## 事件类型总览

| 事件 Type | 作用 | 是否终止流 | 脚本行为 |
|----------|------|:---------:|---------|
| `agent.start` | 会话开始 | ❌ | 提取 `SessionID` |
| `agent_message_chunk` | 增量 Markdown 文本 | ❌ | 写入 `.md` 文件（静默，不输出 stdout） |
| `agent.done` | 分析完成（权威 `FullText`） | ✅ **仅此事件终止** | 用 `FullText` 覆盖重写 `.md` 文件 |
| `pcap_check.done` | 抓包候选清单 | ❌ | 记录 `tool_data`，结束后追加到 `.md` 末尾 |
| `tool.done` / 其他 `*.done` | 中间工具调用完成 | ❌ | 忽略并继续 |

## 事件字段详解

### agent.start

```json
{
  "Type": "agent.start",
  "RequestId": "xxx-xxx-xxx",
  "SessionID": "17f5753184bed224055354"
}
```

**关键字段**：
- `SessionID`：多轮对话会话 ID，脚本会记录并在 JSON 输出的 `session_id` 字段返回，AI 用于 pcap 跟进

### agent_message_chunk

```json
{
  "Type": "agent_message_chunk",
  "Content": "## 错误概况\n共发现 127 次错误",
  "FullText": "(到目前为止的完整文本)"
}
```

**关键字段**：
- `Content`：**增量**文本片段，脚本会逐片写入 `.md` 文件（全程静默）
- `FullText`：**累计**的完整文本，脚本不直接使用（以 done 事件的为准）

### agent.done

```json
{
  "Type": "agent.done",
  "SessionID": "17f5753184bed224055354",
  "FullText": "(完整 Markdown 文本)"
}
```

**关键字段**：
- `FullText`：**权威**的完整分析文本。脚本收到后会与增量累计比对，如果更完整则 `seek(0) + truncate()` 覆盖重写整个 `.md` 文件
- `SessionID`：与 `agent.start` 中的相同（备选来源）

**⚠️ 这是唯一会终止 SSE 消费的事件**。

### pcap_check.done

```json
{
  "Type": "pcap_check.done",
  "ToolName": "pcap_check",
  "Data": {
    "items": [
      {
        "city": "慕尼黑",
        "operator": "Germany_COLT",
        "error_id": "600",
        "task_id": "task-xxxxxxxx",
        "probe_time": 1773905195000,
        "code": "10970"
      }
    ]
  }
}
```

**关键字段**：
- `Data.items[]`：候选项数组，每项包含 `city` / `operator` / `error_id` / `task_id` / `probe_time`（**毫秒时间戳**）/ `code`
- 脚本会把这些字段渲染为 Markdown 表格追加到 `.md` 末尾，并导出独立 `_json.md` 清单

**脚本处理**（取决于是否为抓包场景）：

- **非抓包场景**（错误/整体/性能分析）：候选表格追加到 `.md` 末尾、导出独立 `_json.md` 清单、JSON 输出的 `json_file` 字段为该清单路径。
- **抓包场景**（命令行带 `--session-id`，或 `--query-text` 含 `<structured_json>`，或显式传 `--suppress-pcap-candidates`）：事件仍被消费，但**不**追加 `.md`、**不**导出 `_json.md`、JSON 中 `json_file` 为空。

此事件在非抓包场景下标志着用户需要从候选项中**选一个序号**进入 pcap 跟进分析（见 SKILL.md §5）。

## 脚本输出

脚本全程静默，最终只输出一行 JSON 到 stdout：

```json
{"code": 0, "report": "...", "md_path": "...", "session_id": "...", "json_file": "...", "pcap_candidates": [{...}], "incomplete": false}
```

AI 通过解析 JSON 的 `code` 字段判定成功/失败，**不需要关注 SSE 事件细节**。抓包跟进时直接从 `pcap_candidates` 取 `structured_json`，无需读文件。
