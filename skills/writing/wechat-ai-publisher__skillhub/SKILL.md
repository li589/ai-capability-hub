---
name: wechat-article-publisher
version: 1.1.0
description: 微信公众号文章自动化发布流水线 skill。把素材/选题/链接变成一篇排版好的文章，压缩配图、上传微信素材库、转微信 HTML、存入指定公众号草稿箱并归档。适用于「自动写公众号文章」「文章发到公众号草稿箱」「公众号发布流水线」「做一张图发文」等场景。写作步骤可插拔（通用版 wechat-article-writer 或人设版 laoluo-article-writer），已内置反翻译腔与标题质量规范。不用于：纯图片/海报设计（用图像生成 skill）、多源深度调研（先走 deep-research）、带引用的研究报告。
---

# 微信公众号文章自动化发布流水线

一句话：素材/选题 → 写文章 → 配图处理 → 转微信 HTML → 存草稿箱 → 归档。

本 skill 只管**发布流水线**，写作交给可插拔的写作 skill。所有账号配置（AppID/AppSecret）**参数化**，不绑定任何特定公众号。

## 配置（两种方式，任选）

### 方式 A：.env 文件（推荐，避免泄露密钥到命令历史）
在 skill 目录放 `.env`：
```
WECHAT_APP_ID=wx你的appid
WECHAT_APP_SECRET=你的appsecret
MARKDOWN_CONVERTER=doocs
MARKDOWN_THEME=   # 留空=由 Agent 按内容选；或填 default/green/purple/orange/cyan
```
脚本会自动读取（`scripts/config.py`）。

### 方式 B：命令行传参
每个脚本都接受 `--app_id` / `--app_secret`，优先级高于 .env。

> ⚠️ **变量名对照**（容易混淆，注意区分）：
> - `.env` 文件用：`WECHAT_APP_ID` / `WECHAT_APP_SECRET`
> - 命令行参数用：`--app_id` / `--app_secret`（**没有 WECHAT_ 前缀**）
> - `run_pipeline.py` 同样支持 `--app_id/--app_secret` 覆盖 .env
>
> ⚠️ AppSecret 是高危凭证，不要写进可被分享的 prompt / 文章 / 日志。建议用 .env 或环境变量。

## 依赖
```
pip install -r requirements.txt
# 或装到 WorkBuddy 受管 venv：
# /Users/chengdong/.workbuddy/binaries/python/envs/default/bin/pip install requests markdown Pillow
```
需要 `requests`（微信 API）、`markdown`（MD→HTML）、`Pillow`（图片压缩）。

## 工作流（六步）

### Step 1 收集与整理素材
- 链接 → 用 web_fetch 抓正文
- 文本/流水账 → 直接提炼要点（3-5 条干货，避免堆砌）
- PPT/文档 → 提取文字（python-docx / 对应解析器）
- 图片 → 挑 2-4 张优图备用

### Step 2 撰写文章（可插拔）
调用你已安装的中文写作 skill，按场景选：
- **通用号 / 无特定人设** → `wechat-article-writer`（4 风格：官号/技术博客/活动/评测）
- **强人设号（如老罗）** → `laoluo-article-writer`
- **都不装** → 按 `references/writing-quality.md` 自行撰写（含反翻译腔 L4 终检 + 标题规范）

产出 `article.md`（Markdown）。硬性：每篇过 `references/writing-quality.md` 的反翻译腔与标题检查。

### Step 3 配图处理
封面图 **必须**（公众号草稿强制要求）。配图每 500 字 1 张为佳。
```bash
PYTHON=/Users/chengdong/.workbuddy/binaries/python/envs/default/bin/python
SCRIPTS=<本skill目录>/scripts

# 跨平台压缩（PIL，封面建议 ≤800KB，配图 ≤600KB）
$PYTHON $SCRIPTS/compress_image.py --input cover.png --output cover.jpg --max-size 800
# macOS 用户也可： sips -s format jpeg -s formatOptions 80 cover.png --out cover.jpg

# 上传到微信素材库，拿到 thumb_media_id + url
$PYTHON $SCRIPTS/upload_material.py \
  --app_id "$APPID" --app_secret "$APPSECRET" \
  --image_path cover.jpg
# 输出 JSON：{"thumb_media_id":"...","url":"..."}
```
记录 `thumb_media_id`（封面）和正文中每张图的 `url`（微信草稿要求正文图必须用微信素材库的 url，不能直接外链）。

### Step 4 Markdown → 微信 HTML
```bash
$PYTHON $SCRIPTS/markdown_to_wechat_doocs.py \
  --input article.md --output article.html --theme cyan
```
主题按内容选（cyan 科技/商务、orange 温暖、green 清新、purple 高端、default 通用）。也可留空由 Agent 用 `config.select_theme_by_content()` 自动选（仅返回上述 5 种，不会选到不支持的主题）。

**后处理（必须）**：
- 把正文配图的本地标记替换为 Step 3 拿到的微信 `url`（`<img src="微信url">`）
- 在 HTML 末尾插入品牌签名块（可选）：放一张品牌签名图，或用 `--footer-file footer.md` 让 `create_draft.py` 追加
- 若老罗风排版习惯：将 `font-size:20px` 替换为 `17px`、`text-align:justify`→`left`

### Step 5 创建草稿
```bash
$PYTHON $SCRIPTS/create_draft.py \
  --app_id "$APPID" --app_secret "$APPSECRET" \
  --title "文章标题" \
  --content "$(cat article.html)" \
  --thumb_media_id "封面thumb_media_id" \
  --author "作者名" \
  --digest "摘要（≤50字）"
# 成功输出 {"media_id":"..."}
```
> 默认只建**草稿**，不自动群发（安全）。需要群发请用 `publish_draft.py`（手动确认后再发）。

### Step 6 归档
- 文章 → `articles/published/YYYYMMDD_标题.md`
- 元数据 → `articles/published/YYYYMMDD_meta.json`（含 media_id、thumb_media_id、theme）

### 一键串联（run_pipeline，推荐）
发布侧（Step 3-6）可用 `run_pipeline.py` 一步跑完，免去手动衔接：
```bash
$PYTHON $SCRIPTS/run_pipeline.py \
  --article article.md \
  --cover   cover.png \
  --title   "文章标题" \
  --author  "作者名" \
  --digest  "摘要（≤50字）" \
  --theme   cyan \            # 可选，留空自动选
  --body-images img1.png,img2.png   # 可选，自动上传并替换正文图
# 自动：压缩封面→上传封面→上传正文图并替换→转HTML→建草稿→归档
# 输出 media_id 与归档路径
```
> 写作（Step 1-2）仍在对话里由写作 skill 完成；`run_pipeline.py` 接管后续机械流程。CLI 同样可用 `--app_id/--app_secret` 覆盖 .env。

## 能力边界与限制

- **图片大小**：微信素材图片上限 **2MB**（超了报 `40006`/`45001`）。封面建议压缩 ≤800KB（`run_pipeline`/`compress_image` 自动处理）；正文图也需 ≤2MB。
- **正文图外链**：微信草稿正文**不支持外链图片**，必须用微信素材库返回的 `url`。`run_pipeline.py` 的 `--body-images` 会自动上传并替换。
- **正文图数量**：单篇建议 ≤20 张，过多影响 App 端加载。
- **文章长度**：微信草稿正文无硬性字数上限，但建议单篇 ≤5 万字；超长文章可正常转换，只是耗时略增，必要时建议拆分。
- **网络**：需稳定访问 `api.weixin.qq.com`。网络抖动脚本会**自动重试 3 次**（指数退避），仍失败请检查网络/代理。
- **API 配额**：公众号按等级有每日 API 调用额度（素材上传、草稿创建等），超限返回对应 errcode，请稍后或次日再试。
- **群发**：本 skill 只建草稿**不群发**（安全设计），群发需到公众号后台人工确认。

## 重试与故障排查

脚本已内置网络自动重试（`scripts/retry_util.py`，3 次指数退避），仅重试网络异常/5xx，不重试 4xx 业务错误。常见失败对照：

| errcode / 现象 | 原因 | 处理 |
|---|---|---|
| 40001 / 40125 | app_id / app_secret 错误 | 检查 `.env` 配置 |
| 40006 / 45001 | 图片超过 2MB | 压缩封面（≤800KB）/正文图（≤2MB） |
| 40007 | thumb_media_id 无效 | 确认封面上传成功返回的 media_id |
| 45001 | 多媒体文件过大 | 同图片大小限制 |
| 网络超时 / ConnectionError | 网络不稳/代理 | 脚本自动重试；仍失败检查防火墙/代理 |
| no_cover | 未传封面 | 公众号草稿强制要求封面，先上传封面拿 media_id |

> 凭证（AppSecret）绝不进入日志、文章或 prompt；失败信息只暴露 errcode 与可读原因。

## 铁律
- 封面图 **必须有**，否则微信拒收草稿。
- 正文图片必须用微信素材库 `url`，外链图片在 App 端不显示。
- 缩略图 ≤ 2MB，建议 JPEG。
- AppSecret 不进日志/文章/prompt。
- 默认只存草稿，群发需人工确认。

## 资源
- `scripts/config.py` — .env 配置读取 + 按内容自动选主题（仅返回支持的 5 种）
- `scripts/retry_util.py` — 网络请求自动重试（指数退避）
- `scripts/upload_material.py` — 上传图片素材，返回 thumb_media_id/url（带重试）
- `scripts/markdown_to_wechat_doocs.py` — MD→微信 HTML（5 主题）
- `scripts/create_draft.py` — 建草稿（支持可选 footer 追加，带重试）
- `scripts/compress_image.py` — 跨平台图片压缩（Pillow）
- `scripts/run_pipeline.py` — 一键串联发布侧（压缩封面→上传→转HTML→建草稿→归档）
- `references/writing-quality.md` — 反翻译腔 L4 终检 + 标题规范（通用版）
- `.env.example` — 配置模板
