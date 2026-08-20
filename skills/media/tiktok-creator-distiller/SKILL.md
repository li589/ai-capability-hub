---
name: tiktok-creator-distiller
description: TikTok 博主蒸馏器。输入一个 TikTok 博主账号，采集其热门视频，筛选 TOP 视频，逐条拆解脚本/画面/钩子/节奏，输出账号定位、爆款规律、钩子公式、脚本结构、视觉风格、BGM 策略、选题方向和可复用创作 SOP。适合“帮我蒸馏这个 TK 博主”“分析这个 TikTok 账号为什么火”“把这个博主的爆款打法拆出来”“用 TA 的风格给我的产品写脚本”等请求。
allowed-tools: Read, Write, Bash
install_source: official
install_method: download
skill_id: official_YDWX0Hbc
enabled_at: 1787232874701
version: 1.0.0
name_zh: 抖音创作者蒸馏器
---

# TikTok Creator Distiller

Follow shared NexTide rules in:

- `nextide-shared`

## What this skill does

This is a NexTide workflow skill for creator-level TikTok research.

It turns one TikTok creator/account into a reusable content operating system:

```text
TikTok creator/account
  ↓
collect creator videos
  ↓
select TOP N by likes/views/comments/shares
  ↓
break down TOP videos
  ↓
generate creator distillation report
  ↓
optional: adapt formulas to the user's product/context
```

Use this skill when the user asks:

- “帮我蒸馏这个 TK 博主”
- “分析这个 TikTok 账号为什么火”
- “把这个博主的爆款打法拆出来”
- “提炼这个账号的钩子公式 / 脚本结构 / 画面风格”
- “用 TA 的风格给我的产品写短视频脚本”

Do **not** use this skill for:

- simple keyword hot-video search → use `social-data-collector`
- one video breakdown only → use `viral-breakdown-to-video-prompts`
- direct video generation only → use `viral-midform-video-generator`
- publishing to TikTok → currently unsupported / fail fast

## Current MVP status

This is an MVP workflow skill. It does not yet have one monolithic server-side capability.

It orchestrates existing capabilities:

```text
social.tiktok.collect
viral.breakdown.video_prompts
```

Current limitation:

- `social.tiktok.collect` must support `mode=creator` in the deployed `/api/social-scraper/start` workflow.
- If creator collection returns only a submitted `waiting_callback` task, do not invent video rows. Wait for the run result/artifacts or ask the user to retry later.
- If no stable video URL is available from collection artifacts, stop and explain that TOP video breakdown cannot continue.

## Input contract

Preferred input file:

```text
.nextide/input/tiktok-creator-distill-example.json
```

Example:

```json
{
  "creator": "@quinclips3",
  "creatorUrl": "https://www.tiktok.com/@quinclips3",
  "platform": "tiktok",
  "collectLimit": 20,
  "topN": 5,
  "sortBy": "likes",
  "language": "zh-CN",
  "includeVideoBreakdown": true,
  "includeScriptTemplates": true,
  "productContext": {
    "name": "便携榨汁杯",
    "sellingPoints": ["便携", "无线", "易清洗"]
  }
}
```

Fields:

- `creator`: TikTok username such as `@quinclips3`.
- `creatorUrl`: optional TikTok account URL.
- `collectLimit`: default 20. Keep bounded for first pass.
- `topN`: default 5. Do not exceed 8 unless user explicitly confirms cost.
- `sortBy`: `likes` / `views` / `comments` / `shares` / `recent`.
- `language`: report language, default `zh-CN`.
- `productContext`: optional; if present, adapt creator formulas to this product.

## Workflow

### Step 1 — Build creator collect input

Create:

```text
.nextide/input/tiktok-creator-collect.json
```

Shape:

```json
{
  "platform": "tiktok",
  "mode": "creator",
  "targets": ["@quinclips3"],
  "limit": 20,
  "sortBy": "likes"
}
```

If the user provided only a URL, put it into `targets` or `urls`.

### Step 2 — Collect creator videos

Run:

```bash
nextide capability run social.tiktok.collect \
  --input .nextide/input/tiktok-creator-collect.json \
  --output .nextide/output/tiktok-creator-collect-result.json \
  --mode submit \
  --wait \
  --timeout 900 \
  --interval 5
```

Then export artifacts:

```bash
RUN_ID=$(node -e "const r=require('./.nextide/output/tiktok-creator-collect-result.json'); console.log(r.run && r.run.runId)")
nextide run artifacts "$RUN_ID" \
  --output-dir .nextide/output/$RUN_ID
```

Read first:

```text
.nextide/output/$RUN_ID/manifest.json
```

If the collection run is still `waiting_callback`, return the runId and tell the user to query later:

```bash
nextide run status <run-id>
nextide run result <run-id> --output .nextide/output/<run-id>-result.json
```

Do not fabricate creator video data.

### Step 3 — Normalize and rank TOP videos

Find video rows from the result/artifacts. Accept common field names:

```text
video_url / url / post_url / permalink / share_url
caption / description / title
views / play_count / playCount
likes / like_count / diggCount
comments / comment_count / commentCount
shares / share_count / shareCount
posted_at / create_time / createdAt
```

Rank by `sortBy`.

Default:

```text
topN = 5
max topN = 8 without explicit confirmation
```

Write a normalized datatable artifact manually if needed:

```text
.nextide/output/tiktok-creator-distiller/creator-videos.json
```

Suggested columns:

```text
rank
video_url
caption
views
likes
comments
shares
duration
posted_at
```

### Step 4 — Break down TOP videos

For each selected TOP video, create:

```text
.nextide/input/tiktok-creator-breakdown-01.json
.nextide/input/tiktok-creator-breakdown-02.json
...
```

Shape:

```json
{
  "platform": "tiktok",
  "sourcePlatform": "tiktok",
  "referenceVideo": "https://www.tiktok.com/@user/video/...",
  "sourceTitle": "TOP video 1",
  "language": "zh-CN"
}
```

Run one by one unless the user explicitly asks for parallel processing and accepts cost:

```bash
nextide capability run viral.breakdown.video_prompts \
  --input .nextide/input/tiktok-creator-breakdown-01.json \
  --output .nextide/output/tiktok-creator-breakdown-01-result.json \
  --mode submit \
  --wait \
  --timeout 900 \
  --interval 5
```

Export artifacts for each breakdown run:

```bash
RUN_ID=$(node -e "const r=require('./.nextide/output/tiktok-creator-breakdown-01-result.json'); console.log(r.run && r.run.runId)")
nextide run artifacts "$RUN_ID" \
  --output-dir .nextide/output/$RUN_ID
```

If a breakdown returns `waiting_callback`, save its runId. Continue only when enough finished breakdowns exist. If none finish, return pending run IDs.

### Step 5 — Generate creator distillation report

Write final report to:

```text
.nextide/output/tiktok-creator-distiller/creator-distillation-report.md
```

Report structure:

```markdown
# TikTok 博主蒸馏报告：@creator

## 1. 账号速览
- 博主定位
- 内容主题
- 核心数据概览
- 爆款率
- 更新频率推断

## 2. TOP 视频列表
| Rank | Link | Views | Likes | Comments | Shares | Caption |

## 3. 流量密码：为什么 TA 能爆
- TOP 视频共性规律
- 高互动视频 vs 低互动视频差异
- 分享率最高视频特征
- 完播率推断（必须说明只是基于时长/互动的推断）

## 4. 开头钩子公式
- 公式名
- 原视频钩子原文
- 可套用填空模板

## 5. 脚本结构模型
- 0-3s
- 3-8s
- 8-15s
- 15s+

## 6. 视觉与画面风格
- 拍摄方式
- 构图
- 转场
- 字幕/文字覆盖
- 产品露出方式

## 7. BGM 与声音策略
- BGM 类型
- 人声特点
- 语速/情绪/口头禅

## 8. TOP 视频逐条拆解
For each TOP video:
- 链接
- 数据表现
- 开头钩子
- 脚本结构摘要
- 画面手法
- 一句话归因

## 9. 选题方向 TOP10

## 10. 一条视频的完整创作 SOP

## 11. 用 TA 的风格帮你写脚本
If productContext exists, write 3 sample script directions.
Otherwise ask the user for product/theme/duration.

## 12. 可信度与限制
- 样本数量
- 哪些结论基于真实数据
- 哪些只是推断
- 不鼓励搬运抄袭，只学习方法论
```

Also write formulas JSON:

```text
.nextide/output/tiktok-creator-distiller/creator-formulas.json
```

Suggested shape:

```json
{
  "creator": "@creator",
  "sampleSize": 20,
  "analyzedTopN": 5,
  "hookFormulas": [],
  "scriptStructures": [],
  "visualPatterns": [],
  "topicDirections": [],
  "sop": []
}
```

## Cost rules

Default bounded pass:

```text
collectLimit = 20
topN = 5
```

Before `topN > 8`, warn the user:

```text
This will run many video breakdown jobs and may consume more credits. Continue?
```

Never silently run large batch breakdowns.

## Failure modes

- `unauthorized`: ask user to run `nextide auth login`.
- `insufficient_credits`: tell user to recharge NexTide credits.
- `plan_required`: tell user the capability requires a paid plan.
- `waiting_callback`: return runId and commands to check later.
- `run_not_finished`: do not invent results.
- `capability_unavailable`: explain which underlying capability is not available.
- no `video_url`: stop after collection and ask user to provide URLs or wait for normalized artifacts.

## Output requirements

Final answer to user should include:

1. Report file path.
2. Creator video table file path if created.
3. Formula JSON file path if created.
4. Pending run IDs if any.
5. A short summary of the top 3 insights.

Do not paste huge raw JSON. Prefer local artifact paths.
