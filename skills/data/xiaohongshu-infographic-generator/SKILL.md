---
name: xiaohongshu-infographic-generator
description: 小红书信息卡片风格提炼与生成。适合“提炼这组卡片风格”“用这个风格生成信息卡片”“生成小红书知识信息图”等请求。
allowed-tools: Read, Write, Bash
install_source: official
install_method: download
skill_id: official_uIdMFfhI
enabled_at: 1787230808950
version: 1.0.0
name_zh: 小红书信息图表生成器
---

# Xiaohongshu Infographic Generator

Follow shared NexTide rules in:

- `nextide-shared`

This skill has two related capabilities:

1. Style extraction from reference cards.
2. Infographic/card generation from topic + content + style preset.

## Capability A: Style Extraction

Capability id:

```text
xhs.infographic.style.extract
```

Use this when the user wants to analyze visual style from reference images.

CLI contract:

```bash
npm run nextide -- capability run xhs.infographic.style.extract \
  --input .nextide/input/xhs-style-extract.json \
  --output .nextide/output/xhs-style-extract-result.json \
  --mode submit \
  --user-api-key <NEX用户积分API_KEY>
```

Input JSON:

```json
{
  "referenceImages": ["/absolute/path/to/reference.png"],
  "styleName": "高密度知识卡",
  "styleGoal": "适合知识卡片/小红书封面风格",
  "sceneType": "图文讲解详情图"
}
```

The runner supports the first image from `referenceImages` as either a local file path or `http(s)` URL. Style extraction is async; the style preset is created immediately and Style DNA is written back after callback.

## Capability B: Infographic Generation

Capability id:

```text
xhs.infographic.generate
```

CLI contract:

```bash
npm run nextide -- capability run xhs.infographic.generate \
  --input .nextide/input/xhs-infographic-generate.json \
  --output .nextide/output/xhs-infographic-generate-result.json \
  --mode submit \
  --user-api-key <NEX用户积分API_KEY>
```

## Input JSON

```json
{
  "title": "为什么 30 岁后更需要抗炎护肤",
  "text": "正文内容...",
  "styleId": "style_preset_id",
  "imageCount": 3,
  "language": "简体"
}
```

Aliases accepted by runner:

- `topic` → `title`
- `content` / `markdown` → `text`
- `stylePresetId` → `styleId`
- `pageCount` → `imageCount`

## Workflow

1. Confirm whether the user wants style extraction or card generation.
2. For generation, require a `styleId` from NexTide style library.
3. Create `.nextide/input/xhs-infographic-generate.json`.
4. Run the capability command.
5. Report returned `taskId` and async status.
6. Tell the user that card images complete through NexTide callback/UI when the workflow finishes.

## Output Handling

Expected result shape:

```json
{
  "run": {
    "status": "waiting_callback",
    "result": {
      "data": {
        "taskId": "...",
        "summaryId": "..."
      },
      "queued": true,
      "note": "XHS infographic generation is async..."
    }
  }
}
```

## Rules

- Do not claim generated images are ready until callback completes.
- Do not invent style IDs.
- If user only gives reference images but no styleId, route to style extraction first.
- If content is too long, suggest fewer cards or a summarized card plan first.

<!-- BEGIN NEXTIDE AUTO-GENERATED -->

## NexTide Capability Contract

### 小红书信息卡片风格提炼

- Capability: `xhs.infographic.style.extract`
- Version: `0.2.0`
- Category: `xhs`
- Status: `available`
- Execution: `internal_api`
- Async: `true`
- Cost level: `medium`
- Required auth: `nexTideApiKey`
- Required env: `N8N_STYLE_WORKFLOW_WEBHOOK`
- Required plan: `none`
- Rate limit: `10/minute`, `60/hour`
- Estimated credits: 8
- Estimated duration: 180 seconds
- Tags: `xiaohongshu`, `style`, `infographic`, `style-dna`

Description:

从参考图中提炼小红书信息卡片 Style DNA、版式规则和 prompt kit。

Examples:

- none

Input fields:

- `referenceImages` (string[], required)：参考图片 URL 或已上传文件 URL。
- `styleName` (string)：风格名称。

Output fields:

- `stylePresetId` (string)：生成的风格预设 ID。
- `styleDna` (object)：风格 DNA 结构化结果。

CLI:

```bash
nextide capability run xhs.infographic.style.extract \
  --input .nextide/input/xhs.infographic.style.extract.json \
  --output .nextide/output/xhs.infographic.style.extract-result.json \
  --mode submit \
  --wait \
  --timeout 600 \
  --interval 5

RUN_ID=$(node -e "const r=require('./.nextide/output/xhs.infographic.style.extract-result.json'); console.log(r.run && r.run.runId)")
nextide run follow "$RUN_ID" \
  --output-dir .nextide/output/$RUN_ID \
  --timeout 600 \
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

### 小红书信息卡片生成

- Capability: `xhs.infographic.generate`
- Version: `0.2.0`
- Category: `xhs`
- Status: `available`
- Execution: `internal_api`
- Async: `true`
- Cost level: `medium`
- Required auth: `nexTideApiKey`
- Required env: `N8N_XHS_TEXT2IMG_WEBHOOK or XHS_TEXT2IMG_WEBHOOK`
- Required plan: `none`
- Rate limit: `10/minute`, `60/hour`
- Estimated credits: 10
- Estimated duration: 240 seconds
- Tags: `xiaohongshu`, `infographic`, `image-generation`

Description:

根据主题、正文和风格预设生成小红书信息卡片。

Examples:

- none

Input fields:

- `topic` (string, required)：卡片主题。
- `content` (string, required)：正文内容。
- `stylePresetId` (string)：风格预设 ID。
- `pageCount` (number)：生成页数。 默认：`6`

Output fields:

- `jobId` (string)：生成任务 ID。
- `cards` (array)：生成的卡片结果。

CLI:

```bash
nextide capability run xhs.infographic.generate \
  --input .nextide/input/xhs.infographic.generate.json \
  --output .nextide/output/xhs.infographic.generate-result.json \
  --mode submit \
  --wait \
  --timeout 900 \
  --interval 5

RUN_ID=$(node -e "const r=require('./.nextide/output/xhs.infographic.generate-result.json'); console.log(r.run && r.run.runId)")
nextide run follow "$RUN_ID" \
  --output-dir .nextide/output/$RUN_ID \
  --timeout 900 \
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
