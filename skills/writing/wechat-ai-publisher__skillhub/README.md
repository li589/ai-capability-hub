# wechat-article-publisher

通用微信公众号文章自动化发布流水线 skill。把「素材/选题/链接」变成一篇排版好的文章，压缩配图、上传微信素材库、转微信 HTML、存入指定公众号草稿箱并归档。

## 适用场景

- 自动写公众号文章并存草稿箱
- 做一张图配文发布
- 公众号发布流水线（写作环节可插拔）

## 六步流水线

1. **素材** — 选题 / 链接 / 文本素材输入
2. **写文章** — 可插拔：`wechat-article-writer`（通用 4 风格）或自定义人设 skill
3. **配图** — 图片压缩（封面 ≤800KB）+ 上传微信素材库
4. **转 HTML** — Markdown → 微信 HTML（doocs 风格，5 主题，按内容自动选色）
5. **建草稿** — 写入指定公众号草稿箱
6. **归档** — 本地留存

> 发布侧（Step 3-6）可用 `scripts/run_pipeline.py` 一键串联，详见下文。

## 安装

```bash
# 1. 解压到 skills 目录
unzip wechat-article-publisher.zip -d ~/.workbuddy/skills/

# 2. 安装依赖
pip install -r ~/.workbuddy/skills/wechat-article-publisher/requirements.txt

# 3. 配置凭证（二选一）
cp ~/.workbuddy/skills/wechat-article-publisher/.env.example ~/.workbuddy/skills/wechat-article-publisher/.env
# 编辑 .env 填入 WECHAT_APP_ID / WECHAT_APP_SECRET
```

## 配置

| 变量 | 说明 |
|------|------|
| `WECHAT_APP_ID` | 公众号 AppID（必填，写在 .env） |
| `WECHAT_APP_SECRET` | 公众号 AppSecret（必填，写在 .env） |
| `MARKDOWN_CONVERTER` | 转换器，默认 doocs |
| `MARKDOWN_THEME` | 主题：default/green/purple/orange/cyan，留空则按内容自动选 |

> **变量名对照**：`.env` 用 `WECHAT_APP_ID`/`WECHAT_APP_SECRET`；命令行参数用 `--app_id`/`--app_secret`（无 `WECHAT_` 前缀）；`run_pipeline.py` 同样支持 `--app_id/--app_secret` 覆盖 .env。
>
> 封面图请自备（本 skill 负责压缩与上传，不内置图像生成）。

凭证也可通过 CLI 参数传入，不写 `.env`。

## 一键发布（run_pipeline）

写作完成后，发布侧一步跑完：

```bash
PYTHON=/Users/chengdong/.workbuddy/binaries/python/envs/default/bin/python
SCRIPTS=~/.workbuddy/skills/wechat-article-publisher/scripts

$PYTHON $SCRIPTS/run_pipeline.py \
  --article article.md \
  --cover   cover.png \
  --title   "文章标题" \
  --author  "作者名" \
  --digest  "摘要（≤50字）" \
  --theme   cyan \            # 可选，留空自动选
  --body-images img1.png,img2.png   # 可选，自动上传并替换正文图
```

自动完成：压缩封面 → 上传封面拿 thumb_media_id → 上传正文图并替换本地路径 → MD 转 HTML → 建草稿 → 归档。输出 `media_id` 与归档路径。

## 依赖

- requests >= 2.28.0
- markdown >= 3.4.0
- Pillow >= 10.0.0

## 能力边界与限制

- **图片大小**：微信素材图片上限 **2MB**（超了报 `40006`/`45001`）。封面建议压缩 ≤800KB（脚本自动处理）；正文图也需 ≤2MB。
- **正文图外链**：微信草稿正文**不支持外链图片**，必须用微信素材库返回的 `url`（`run_pipeline.py --body-images` 自动处理）。
- **正文图数量**：单篇建议 ≤20 张。
- **文章长度**：草稿正文无硬性字数上限，建议单篇 ≤5 万字；超长可正常转换，必要时拆分。
- **网络**：需稳定访问 `api.weixin.qq.com`；网络抖动脚本**自动重试 3 次**（指数退避）。
- **API 配额**：公众号按等级有每日调用额度，超限返回对应 errcode，请稍后重试。
- **群发**：本 skill 只建草稿**不群发**（安全），群发需到公众号后台人工确认。

## 重试与故障排查

内置网络自动重试（`scripts/retry_util.py`，3 次指数退避），仅重试网络异常/5xx，不重试 4xx 业务错误。

| 现象 | 原因 | 处理 |
|---|---|---|
| 40001 / 40125 | app_id / app_secret 错误 | 检查 `.env` |
| 40006 / 45001 | 图片超过 2MB | 压缩封面/正文图 |
| 40007 | thumb_media_id 无效 | 确认封面上传返回的 media_id |
| 网络超时 | 网络不稳/代理 | 自动重试；仍失败检查防火墙 |

## 目录结构

```
wechat-article-publisher/
├── SKILL.md                          # skill 定义
├── README.md
├── requirements.txt
├── .env.example                      # 凭证模板
├── references/
│   └── writing-quality.md            # L4 反翻译腔终检 + 标题规范
└── scripts/
    ├── config.py                     # 读凭证 + 按内容选主题（仅5种）
    ├── retry_util.py                 # 网络请求自动重试
    ├── upload_material.py            # 上传图片素材（带重试）
    ├── markdown_to_wechat_doocs.py   # MD → 微信 HTML（5 主题）
    ├── create_draft.py               # 建草稿（带重试）
    ├── compress_image.py             # 图片压缩
    └── run_pipeline.py              # 一键串联发布侧
```

## 安全说明

- 脚本仅调用微信公众号官方 API + 本地 Pillow 图片处理
- 凭证走 `.env` 或 CLI 参数，不硬编码、不外发
- 打包已排除 `.env`（真实密钥），仅含 `.env.example` 模板
- AppSecret 不进日志/文章/prompt

## License

MIT
