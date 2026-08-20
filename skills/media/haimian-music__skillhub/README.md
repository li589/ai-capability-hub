# 海绵音乐 Skill

海绵音乐官方 AI 音乐生成 Skill，在 AI 助手里完成写歌、歌词成曲、BGM、参考改编、查询和下载。

海绵音乐 Skill 是面向专业创作者的 AI音乐生成工具，可在 AI 助手里完成 AI写歌、原创歌曲、歌词成曲、纯音乐 BGM 和参考音频改编。你只需描述风格、情绪、歌词或使用场景，就能生成作品，并获得试听、下载和项目链接；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `haimian-music`
- Package name: `haimian-music`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- 海绵音乐
- AI音乐生成
- AI写歌
- 生成音乐
- 歌词成曲
- BGM生成
- 背景音乐
- 参考音频改编
- 短视频配乐
- music generation
- song generator
- lyrics to song

## Use Cases

- 原创歌曲创作
- 歌词成曲
- 纯音乐 BGM
- 参考音频改编
- 短视频和商业内容配乐

## Examples

- 帮我写一首轻快的中文流行歌，主题是夏天旅行
- 把这段歌词做成一首完整歌曲
- 生成一段适合产品发布会开场的 BGM
- 参考这个 demo，做一个更抓耳的版本

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "写一首轻快的中文流行歌，主题是夏天旅行" --wait
node ./bin/aimv.js song create --lyrics "..." --title "夏天旅行" --style mandopop --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
