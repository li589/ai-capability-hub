---
name: xiaohongshu-note-collector
description: 采集小红书笔记链接并沉淀到 NexTide 爆款广场/我的分类/viral references。适合“采集这个小红书链接”“把这条笔记加入爆款广场”“收集小红书爆款笔记”等请求。
allowed-tools: Read, Write, Bash
install_source: official
install_method: download
skill_id: official_XuPSCH9W
enabled_at: 1787232869846
version: 1.0.0
name_zh: 小红书笔记收集器
---

# Xiaohongshu Note Collector

Follow shared NexTide rules in:

- `nextide-shared`

Use this skill when the user wants to:

- 采集一个或多个小红书笔记链接
- 把小红书图文/视频保存到 NexTide 爆款广场或“我的”分类
- 为图文复刻、爆款拆解、卡片生成准备参考素材

MVP scope:

- Supports direct Xiaohongshu note URL collection.
- Keyword search collection is registered in NexTide capability registry but not wired to production runner yet.

## Capability

Capability id:

```text
xhs.note.collect
```

CLI contract:

```bash
npm run nextide -- capability run xhs.note.collect \
  --input .nextide/input/xhs-note-collect.json \
  --output .nextide/output/xhs-note-collect-result.json \
  --mode wait \
  --user-api-key <NEX用户积分API_KEY>
```

## Input JSON

Single URL:

```json
{
  "source": "url",
  "url": "https://www.xiaohongshu.com/explore/...",
  "saveToHotSquare": true
}
```

Multiple URLs:

```json
{
  "source": "url",
  "urls": [
    "https://www.xiaohongshu.com/explore/...",
    "https://xhslink.com/..."
  ],
  "saveToHotSquare": true
}
```

## Workflow

1. Extract Xiaohongshu URLs from user input.
2. Create `.nextide/input/xhs-note-collect.json`.
3. Run the capability command.
4. Read `.nextide/output/xhs-note-collect-result.json`.
5. Return saved task IDs, titles, statuses, video URLs if any, and errors if partial failure occurs.

## Output Handling

Expected result shape:

```json
{
  "run": {
    "status": "succeeded",
    "result": {
      "items": [
        {
          "url": "https://...",
          "result": {
            "taskId": "...",
            "status": "BREAKDOWN_PENDING",
            "title": "...",
            "videoUrl": null,
            "message": "采集成功，已加入“我的”分类"
          }
        }
      ],
      "errors": []
    }
  }
}
```

If the note is an image note, NexTide may asynchronously trigger image-text breakdown after collection.

If the note is a video note, status may be `VIDEO_COLLECTED`.

## Rules

- Do not invent note metadata if collection fails.
- Do not treat keyword search as available in MVP.
- For multiple URLs, report partial failures clearly.
- Do not ask the user to paste cookies; NexTide server handles downloader configuration.

<!-- BEGIN NEXTIDE AUTO-GENERATED -->

## NexTide Capability Contract

### 小红书笔记采集

- Capability: `xhs.note.collect`
- Version: `0.2.0`
- Category: `xhs`
- Status: `available`
- Execution: `internal_api`
- Async: `true`
- Cost level: `medium`
- Required auth: `nexTideApiKey`
- Required env: `XHS_DOWNLOADER_BASE_URL`
- Required plan: `none`
- Rate limit: `10/minute`, `60/hour`
- Estimated credits: 5
- Estimated duration: 60 seconds
- Tags: `xiaohongshu`, `collection`, `hot-square`, `viral-reference`

Description:

采集小红书链接并沉淀为爆款广场/viral references 可用的结构化数据。MVP 阶段已支持 URL 采集，关键词搜索采集仍为 planned。

Examples:

- none

Input fields:

- `source` (string, required)：采集来源类型：url 或 keyword。
- `urls` (string[])：小红书笔记链接列表，source=url 时使用。
- `keywords` (string[])：搜索关键词，source=keyword 时使用。
- `limit` (number)：目标采集数量。 默认：`30`
- `collectComments` (boolean)：是否同时采集评论。默认关闭以节省成本。 默认：`false`
- `saveToHotSquare` (boolean)：是否保存到爆款广场/素材库。 默认：`true`

Output fields:

- `items` (array)：归一化后的小红书笔记列表。
- `savedReferences` (array)：已保存的 viral reference 记录。

CLI:

```bash
nextide capability run xhs.note.collect \
  --input .nextide/input/xhs.note.collect.json \
  --output .nextide/output/xhs.note.collect-result.json \
  --mode submit \
  --wait \
  --timeout 300 \
  --interval 5

RUN_ID=$(node -e "const r=require('./.nextide/output/xhs.note.collect-result.json'); console.log(r.run && r.run.runId)")
nextide run follow "$RUN_ID" \
  --output-dir .nextide/output/$RUN_ID \
  --timeout 300 \
  --interval 5
```

Artifact-first reading order:

1. Read `.nextide/output/$RUN_ID/summary.json`.
2. Read `.nextide/output/$RUN_ID/manifest.json`.
3. Return `preview.html` / `gallery.html` with rich preview when supported.
4. Return `datatable.json` for data/table results.
5. Return local artifact paths when present.
6. If a remote URL artifact is present, return the URL from manifest.
7. Only inspect the full result JSON when manifest is insufficient.

## General Rules

- Use NexTide capability IDs, not internal n8n webhook URLs.
- Do not expose API secrets or internal webhook URLs in prompts or output.
- If status is not `available`, fail fast and explain what is missing.
- For async tasks, prefer `--wait` when the user wants a finished result in the same turn.
- After a finished run, use `nextide run artifacts <run-id> --output-dir .nextide/output/<run-id> --download --gallery --datatable` and read `summary.json` then `manifest.json`.
- For long-running runs, prefer `nextide run follow <run-id> --output-dir .nextide/output/<run-id> --timeout 1800 --interval 5`.
- Prefer returning `summary.recommendedResponse.message`, `preview.html`, `datatable.json`, and local artifact paths over pasting huge raw JSON.
- If the CLI output includes `explanation`, convert it into a clear user-facing failure message with next actions.

<!-- END NEXTIDE AUTO-GENERATED -->
