---
name: "lovstudio-wechat-branding-quality-gate"
description: "验收公众号文章的内容、结构、审美、品牌准确性与保存持久化；用于“检查最终效果”“保存后验证”、\"review the branded WeChat article\"，并修复发现的问题。"
version: "0.1.0"
author: "lovstudio"
source_type: "git"
git_url: "https://github.com/lovstudio/wechat-article-branding-skill"
---

# Quality Gate

以读者可见结果和真实平台状态验收文章。除非用户明确只要报告，发现问题后直接修复并重新检查。

## Triggers

### Activate when

- Branding 管线进入最终验收或用户说“检查最终效果”“保存后确认一下”。
- 用户明确请求只读 `audit`。
- The user asks to "review the branded WeChat article" or verify the saved result.

### Do not activate when

- 上游还没有产出完整候选内容或封面。
- 用户只需要生成素材文件，不需要文章级验收。

## Workflow (MANDATORY)

1. 读取 `$SKILL_DIR/references/acceptance.md`。
2. 比较文章原始快照、变更计划和当前页面状态。
3. 检查内容命题、事实、引语、链接和作者语气。
4. 检查 TOC、标题、代码块、品牌区的顺序、数量与层级。
5. 检查封面横版、方形裁切、焦点和 Logo 完整性。
6. 检查品牌名称、产品承诺、URL、品牌色和禁止公开内容。
7. 检查测试文字、空壳节点、重复图片和非目标字段变化。
8. 保存并重新加载，再执行一次关键检查。
9. `audit` 管线只报告；其他管线修复根因后重复验收。

## Completion rule

以下状态均不等于完成：本地生成成功、上传完成、选择成功、DOM 已变化、页面出现成功提示。只有目标结果在真实预览中成立，并在保存后重载仍存在，才可以报告完成。

## Output

- 已观察到的文章状态；
- 运行的管线和模块；
- 计划内变化与保持不变的字段；
- 横版、方形和正文检查结果；
- 未运行或仍缺证据的能力。

## Dependencies

Authenticated browser preview and the before/after article state from the article-access module.
