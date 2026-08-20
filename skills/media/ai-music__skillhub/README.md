# AI音乐

中文 AI音乐创作入口，支持写歌、歌词成曲、BGM、短视频配乐和参考音频改编。

AI音乐适合需要 AI音乐生成、AI音乐创作、AI作曲、AI写歌和 ai music 工具的中文专业创作者。你只要描述主题、风格、情绪、歌词或使用场景，就可以在 AI 助手中生成可试听、可下载的歌曲或 BGM；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `ai-music`
- Package name: `ai-music`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- AI音乐
- ai音乐
- AI音乐创作
- AI音乐生成
- AI作曲
- AI写歌
- AI歌曲
- 生成音乐
- 音乐生成
- 中文AI音乐
- ai music
- AI music
- music AI

## Use Cases

- 根据一句中文需求生成歌曲或 BGM
- 为短视频、播客、广告和品牌内容生成原创音乐
- 把歌词或创意 brief 扩展成完整音乐作品
- 基于参考音频继续改编和探索风格方向

## Examples

- 用 AI音乐帮我生成一首轻快的中文流行歌，主题是夏天旅行
- 生成一段适合科技产品发布会开场的 AI 音乐
- 帮我做一段适合短视频开头的原创背景音乐

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "用 AI音乐帮我生成一首轻快的中文流行歌，主题是夏天旅行" --wait
node ./bin/aimv.js bgm create --brief "生成一段适合科技产品发布会开场的 AI 音乐" --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
