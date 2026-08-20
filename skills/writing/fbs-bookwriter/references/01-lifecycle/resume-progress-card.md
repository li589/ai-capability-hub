# 恢复/进度卡

## 1. 触发时机

- 用户输入“继续”“接着写”“上次写到哪了”。
- 第一次交付出目录、章节草稿、质检报告或导出文件后。
- 用户未明确下一步，但当前 `bookRoot` 已有 `.fbs/workbuddy-resume.json`。

## 2. 真源

- `.fbs/workbuddy-resume.json`
- `.fbs/smart-memory/session-resume-brief.md`
- `.fbs/chapter-status.md`
- `scripts/workbuddy-session-snapshot.mjs`
- `scripts/write-progress-snapshot.mjs`

禁止仅凭聊天上下文猜测恢复状态；优先读磁盘工件。

## 3. 用户可见要求

- 第一行必须明确“进度已保存”。
- 只展示 2-3 个下一步动作。
- 不重复追问已经能从恢复卡读出的背景。
- 如果恢复卡缺失，但 `chapter-status.md` / `esm-state.md` 在，则先补写恢复卡再继续。

## 4. 建议字段

```json
{
  "cardType": "resume_progress_card",
  "bookTitle": "AI+HR 行业白皮书",
  "currentStage": "S3",
  "wordCount": 12800,
  "chapterCount": 8,
  "completedCount": 3,
  "resumeHint": "下次输入“福帮手”或“继续”即可回到当前书稿",
  "nextOptions": [
    "继续写下一章",
    "先做去 AI 味和质检",
    "先做排版导出预检"
  ]
}
```

完整示例：[`../../assets/examples/resume-progress-card.json`](../../assets/examples/resume-progress-card.json)

## 5. 最小动作

1. 读取恢复卡和章节台账。
2. 补一句阶段摘要。
3. 给出 2-3 个后续动作。
4. 若用户离开，调用 `session-exit` 确保恢复卡与摘要更新。
