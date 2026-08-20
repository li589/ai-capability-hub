# 结果卡 schema

## 1. `resume_progress_card`

```json
{
  "cardType": "resume_progress_card",
  "bookTitle": "string",
  "currentStage": "S0-S6",
  "wordCount": 0,
  "chapterCount": 0,
  "completedCount": 0,
  "resumeHint": "string",
  "nextOptions": ["string", "string", "string"]
}
```

## 2. `post_draft_pack`

```json
{
  "cardType": "post_draft_pack",
  "inputFile": "path",
  "template": "default|custom",
  "layoutPreflightReport": "path",
  "diffReport": "path|null",
  "warnings": ["string"]
}
```

## 3. `benefit_status_card`

```json
{
  "cardType": "benefit_status_card",
  "benefitSource": "api2|connector|local_cache|offline_default",
  "memberTier": "T0|T1|T2|T3|unknown",
  "creditsState": "available|insufficient|offline_cache|unverified",
  "notes": "string|null"
}
```

## 4. `export_delivery_card`

```json
{
  "cardType": "export_delivery_card",
  "format": "md|html|docx|pdf",
  "outputFile": "path",
  "previewAction": "preview_url|open_result_view|null",
  "benefitStatus": "benefit_status_card|null"
}
```
