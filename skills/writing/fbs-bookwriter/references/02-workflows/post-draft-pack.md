# 成稿后处理包

## 1. 适用意图

- 排版 / 导出 / 格式调整
- 去 AI 味 / 润色 / 质检
- 改写 / 本地化 / 翻译后重写

## 2. 最小执行链

1. 确认输入稿件与目标格式。
2. 跑轻量质检：`quality-auditor-lite.mjs`
3. 跑版式预检：`layout-preflight.mjs`
4. 如用户要求去 AI 味或改写，对比原稿与改写稿：`de-ai-diff.mjs`
5. 生成结果卡并写事件：`event-writer.mjs`
6. 如需预览，走 `host-consume-presentation.mjs`

## 3. 输入 / 输出

| 输入 | 输出 |
| --- | --- |
| `.md` / `.html` / `.txt` / `.docx` / `.pdf` | 预检报告、差异报告、导出卡、宿主预览入口 |
| 用户指定模板 | 结果卡中回显模板名 |
| 原稿 + 改写稿 | 修改前后对照和口吻词变化 |

## 4. 降级路径

- 输入为 `.docx` / `.pdf` 但没有同名伴随稿：
  `layout-preflight.mjs` 只做文件级检查，并显式提示需要人工预览。
- 没有改写稿：
  先输出质检与排版预检，不伪造去 AI 差异。
- API2 / 连接器不可用：
  用 `event-writer.mjs` 把事件落到 `.fbs/events/`。

## 5. 回归样稿

- [`../../fixtures/regression/post-draft/sample-layout.md`](../../fixtures/regression/post-draft/sample-layout.md)
- [`../../fixtures/regression/post-draft/sample-before.md`](../../fixtures/regression/post-draft/sample-before.md)
- [`../../fixtures/regression/post-draft/sample-after.md`](../../fixtures/regression/post-draft/sample-after.md)
