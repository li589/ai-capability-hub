# PPT Craft Master v2.0

这是对原 `ppt-craft-master` 的一次工程化升级。保留原有的 28 种版式、设计令牌、风格库、故事线、金句、数据和无障碍体系，同时修复关键逻辑问题。

## 已修复的关键问题

1. **页数不准确**：原版 `--pages 12` 可能因自动插入章节页而实际生成 13 页；v2 用总页数预算保证精确页数。
2. **版式规则过硬**：原版强制“每种版式最多 2 次”，长 deck 会失去内容适配；v2 改成软约束。
3. **静默截断**：原版文字放不下会自动剪掉尾部并加 `…`；v2 默认报错，避免内容悄悄丢失。
4. **段后距参数**：原版使用 `paraSpaceAfter`，与 PptxGenJS 常用的 `paraSpaceAfterPt` 不一致；v2 修正。
5. **检查器依赖系统 unzip**：v2 改为 JSZip，减少 Windows/macOS/Linux 环境差异。
6. **QA 范围不足**：新增安全区、placeholder、过小字号、保守文本高度检查。
7. **规则冲突**：弱化“每页必须 120 字”“每页必须有图片”等容易导致灌水的要求，改为内容与版式适配优先。

## 使用

```bash
npm install
node scripts/generate.js --title "2026 消费趋势" --style 商务简约 --pages standard
node scripts/check-overflow.js path/to/deck.pptx
```

生成后仍建议用 PowerPoint 或 LibreOffice 实际渲染，逐页做视觉检查。自动 QA 不能替代渲染检查。
