---
name: "lovstudio-wechat-branding-cover-direction"
description: "将文章主题和参考图转为成熟的公众号品牌封面，管理素材来源、Logo 完整性与双比例裁切；用于“重做封面”“不要 AI 味”、\"create an editorial WeChat cover\"。"
version: "0.1.0"
author: "lovstudio"
source_type: "git"
git_url: "https://github.com/lovstudio/wechat-article-branding-skill"
---

# Cover Direction

把文章命题翻译为一个克制、可辨认并适合公众号真实裁切的视觉世界。

## Triggers

### Activate when

- 用户说“参考这个成熟账号重做封面”“封面不要像 AI”“加入品牌 Logo”。
- Branding 管线启用封面生成、重构或替换。
- The user asks to "create an editorial WeChat cover" or improve an AI-looking cover.

### Do not activate when

- 用户只要求提取参考图 Design DNA，不需要封面成品。
- 当前封面已经通过审美、品牌和裁切验收且用户未要求变化。

## Workflow (MANDATORY)

1. 读取文章命题、参考图和品牌 Profile。
2. 提取参考图的信息层级、焦点、留白、色彩、素材类型和品牌权重，不照抄其身份元素。
3. 选择素材策略：真实摄影、授权或公共领域作品、生成式画面；选择理由必须服务文章而非工具偏好。
4. 需要外部素材时记录作品、作者、来源、使用状态和原始 URL。
5. 使用官方 Logo；保持字形、字距、拼写和透明区域，不用生成模型重画品牌标识。
6. 先构图 `2.35:1`，同时保护中心 `1:1` 安全区。
7. 控制视觉焦点；默认避免模板化蓝紫渐变、机器人、代码 UI、霓虹和无意义科技粒子。
8. 在生成或合成前保存完整 Prompt；输出 PNG、上传用 JPG 和裁切预览。
9. 上传后检查平台实际预览和 CDN 成品，而不是只检查本地文件。

## Decision rule

当“生成得更精细”仍然保留明显模型审美时，优先改变素材策略和信息层级，不继续堆叠 Prompt。确定性裁切、调色和官方 Logo 合成可以优于再次生成。

## Validation

- 封面只有一个主要视觉焦点。
- 横版与方形裁切都保留主题和品牌。
- Logo 高对比且不变形。
- 素材来源可回溯。
- 文章标题由平台叠加时，画面仍留有可读区域。

## Dependencies

按任务选择图像生成、图像编辑、公共素材检索和真实页面预览能力。
