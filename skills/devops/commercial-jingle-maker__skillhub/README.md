# 广告歌生成AI

为品牌、广告、活动和商业内容生成广告歌、品牌歌、宣传歌与声音 logo 方向。

广告歌生成AI适合品牌方、营销团队和商业内容创作者，用于生成广告歌、品牌歌、宣传歌、活动主题曲和声音 logo 方向。输入品牌定位、受众、卖点和传播场景后，AI 助手会生成可试听、可下载的音乐方案；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `commercial-jingle-maker`
- Package name: `commercial-jingle-maker`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- 广告歌
- 广告歌生成
- 品牌歌
- 商业配乐
- 品牌音乐
- 宣传歌
- 活动主题曲
- 声音logo
- commercial jingle
- jingle maker
- brand song
- ad music

## Use Cases

- 根据品牌 brief 生成广告歌
- 制作品牌歌 demo 和活动主题曲
- 探索声音 logo 和广告音乐方向
- 为营销方案产出商业音乐候选

## Examples

- 给一个运动饮料品牌写一首年轻、有记忆点的广告歌
- 给新咖啡品牌做一首明亮、好记的广告歌
- 为金融科技 App 生成一个简短声音 logo 方向

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "给新咖啡品牌做一首明亮、好记的广告歌" --wait
node ./bin/aimv.js song create --brief "年轻、有记忆点的运动饮料广告歌" --style pop energetic --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
