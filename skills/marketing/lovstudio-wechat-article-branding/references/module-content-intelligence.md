---
name: "lovstudio-wechat-branding-content-intelligence"
description: "基于真实公众号文章生成 TOC、结构调整、摘要和可选润色计划；用于“生成目录”“优化文章结构”、\"improve this article structure\"，不直接操作编辑器。"
version: "0.1.0"
author: "lovstudio"
source_type: "git"
git_url: "https://github.com/lovstudio/wechat-article-branding-skill"
---

# Content Intelligence

理解文章后生成结构化、可审阅的内容变更计划。只产出文章内容，不直接控制公众号编辑器。

## Triggers

### Activate when

- 用户要求“生成 TOC”“优化章节结构”“改摘要”或明确要求润色。
- Branding 管线需要从文章内容推导新增区块。
- The user asks to "improve this article structure" or generate a table of contents.

### Do not activate when

- 用户只要求封面或品牌尾注，正文结构已经稳定。
- 用户只要求把已确定内容写回页面，应交给文章访问模块。

## Workflow (MANDATORY)

1. 从文章状态提炼主题、受众、主要论点、现有章节和作者语气。
2. 把输入分为文章事实、内部背景和证据缺口。
3. 选择最小必要处理：TOC、标题层级、摘要、代码或 Prompt 块、明确要求的润色。
4. TOC 只引用真实章节，不创造正文不存在的承诺。
5. 可复制资产使用“章节标题 + 内容块”，不补写背景和过程。
6. 润色时保留事实、引语、专有名词、链接、立场和信息密度；初版默认关闭润色。
7. 输出带锚点、唯一标记、预期文本和允许变化字段的变更计划。

## Product-manager guardrail

沟通中的人名、括号说明、私人关系、操作原因和临时判断默认只用于理解。只有读者需要的信息才进入最终文章。

## Validation

- TOC 与真实章节一一对应。
- 新增内容不重复文章已经说明的观点。
- 代码、Prompt 或清单可以直接选择复制。
- 未启用的处理器不产生任何正文变化。

## Dependencies

None.
