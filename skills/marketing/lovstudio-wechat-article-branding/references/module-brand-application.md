---
name: "lovstudio-wechat-branding-brand-application"
description: "从可移植品牌 Profile 生成专业且不突兀的作者、工作室、产品和资源内容块；用于“增加品牌收尾”“加入产品介绍”、\"apply this brand to the article\"。"
version: "0.1.0"
author: "lovstudio"
source_type: "git"
git_url: "https://github.com/lovstudio/wechat-article-branding-skill"
---

# Brand Application

让品牌成为文章价值的自然延伸，而不是突然出现的广告或公司简介。

## Triggers

### Activate when

- 用户说“结尾做一些专业且不违和的 PR”“加入工作室和产品介绍”。
- Branding 管线需要应用 Logo、品牌语言、产品事实、链接或可复制资源块。
- The user asks to "apply this brand to the article" or add a subtle branded endcap.

### Do not activate when

- 没有经过验证的品牌 Profile，且用户没有提供可公开事实。
- 用户要强销售落地页或广告投放文案，而不是文章品牌化。

## Workflow (MANDATORY)

1. 完整读取根级品牌 Profile 与当前文章命题。
2. 只使用 `public_facts`、产品名称、结果承诺、公开 URL 和批准的视觉字段。
3. 选择与文章主题直接相关的最少品牌信息。
4. 用“为读者带来什么结果”描述产品，不罗列内部能力和技术数量。
5. 构建必要内容块：品牌尾注、产品介绍、作者信息、链接、可复制 Prompt 或代码。
6. 可复制资产只保留章节标题和内容块；删除背景、制作过程和复用说明。
7. 根据 Profile 应用 Logo、品牌色和层级，但不让品牌区压过文章结论。
8. 检查名称、链接、拼写、承诺和 `forbidden_context`。

## Editorial test

暂时移除品牌名称后，段落仍应能自然承接文章结论。若不能，说明品牌区缺少语义连接或仍像硬广。

## Validation

- 品牌内容比文章结论短且层级更低。
- 没有内部背景、私人说明和未验证主张。
- 产品承诺来自 Profile，并与文章主题相关。
- Prompt、代码或清单是直接可复制的内容块。
- 链接和品牌资产准确。

## Dependencies

Root brand Profile from `$SKILL_DIR/references/brand-profile.md`.
