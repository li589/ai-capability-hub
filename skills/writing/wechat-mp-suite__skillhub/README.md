# 微信公众号终极工作台

> `v1.0.2` — 纯 Python · 零 Node.js · 一键初始化

一站式公众号内容工具链：搜选题 → 抓文章 → AI 写作 → 洗稿 → 排版 → 发布。

**从 v1.0.1 升级？** → [迁移指南](./MIGRATION.md)

---

## 30 秒上手

```bash
python setup.py                              # 一键检测 + 安装依赖 + 配置凭证
python check.py                              # 随时查看环境状态

python scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx    # 爬文章
python scripts/typeset/cli.py output/文章.md --theme ocean          # 排版
```

爬虫和排版无需凭证，开箱即用。搜索和发布需额外配置，`setup.py` 会引导你完成。

---

## 模块一览

| # | 模块 | 一句话 | 入口 |
|:--|------|--------|------|
| 1 | 爬虫 | URL → Markdown + 本地图片，多线程下载 | `scripts/spider/main.py` |
| 2 | 搜索 | 搜狗微信关键词搜索 | `scripts/search/index.py` |
| 3 | 下载 | 完整下载单篇文章（含图片） | `scripts/downloader/download.py` |
| 4 | 排版 | Markdown → 微信 HTML，5 主题 + 5 代码高亮 | `scripts/typeset/cli.py` |
| 5 | 发布 | 本地 / 远程发布到公众号草稿箱 | `scripts/publisher/publish.py` |
| 6 | 写作 | AI 辅助：刘润/爆款/真人/财经 4 风格 | 自然语言指令 |
| 7 | 洗稿 | AI 去痕迹 + 原创改写 | 自然语言指令 |
| 8 | 配图 | AI 生成封面 + 配图 Prompt | 自然语言指令 |

模块 1-5 为可执行脚本；模块 6-8 为 AI prompt 驱动，通过对话触发。

---

## 环境要求

| 你需要 | 版本 | 必选？ |
|--------|------|:-----:|
| Python | ≥ 3.12 | 必须 |
| pip | 任意 | 必须 |

**不再需要 Node.js、npm、Chrome、curl、jq**。全部功能改为纯 Python 实现。

---

## 安装

```bash
git clone <repo-url>
cd wechat-mp-suite

pip install -r requirements.txt    # requests, bs4, lxml, python-dotenv, pyyaml

# 可选：代码高亮增强
pip install pygments

# 仅发布功能需要
cp .env.example .env
```

### 配置依赖范围

| 功能 | 需要的配置 |
|------|-----------|
| 爬虫、下载、排版 | **零配置**，装完即用 |
| 搜索 | `.env` 中配置 `SOGOU_COOKIE` |
| 发布 | `.env` 中配置 `WECHAT_APP_ID` + `WECHAT_APP_SECRET` |

---

## 模块详解

### 爬虫 — `scripts/spider/`

```bash
python scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx
python scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx ./my_articles
```

- 多线程并行下载图片（默认 5 线程，`config.yaml` 可调）
- 下载失败自动重试 3 次（指数退避 1s → 3s → 7s）
- 文件名自动缩减（≤ 50 字符，去特殊字符）

```
输出:
output/
├── 文章标题.md
└── images/  (全部图片本地化)
```

---

### 搜索 — `scripts/search/`

> 需要 `SOGOU_COOKIE`，[获取方法](#获取-sogou_cookie)

```bash
python scripts/search/index.py "AI 写作" -n 5        # 搜 5 条
python scripts/search/index.py "ChatGPT" -n 3 -c      # 搜 + 抓正文
python scripts/search/index.py "运营" -n 10 -r         # 解析真实 URL
python scripts/search/index.py "新媒体" -n 20 -o out.json
```

| 参数 | 作用 | 默认值 |
|:-----|:-----|:------:|
| `-n` | 返回结果数 | 10（最大 50） |
| `-c` | 获取每篇正文 | 关闭 |
| `-r` | 解析跳转链接 → 原文 URL | 关闭 |
| `-o` | 输出到 JSON 文件 | 控制台 |

---

### 下载 — `scripts/downloader/`

```bash
python scripts/downloader/download.py https://mp.weixin.qq.com/s/xxxxx
python scripts/downloader/download.py https://mp.weixin.qq.com/s/xxxxx --output ./articles --no-image
```

与爬虫的区别：爬虫侧重批量处理 + Markdown 输出；下载器侧重单篇完整 HTML 保存。

---

### 排版引擎 — `scripts/typeset/`

纯 Python 手写 Markdown → 微信 HTML 转换器，零外部依赖。

```bash
python scripts/typeset/cli.py article.md --theme ocean --code-theme monokai
cat article.md | python scripts/typeset/cli.py > article.html
python scripts/typeset/cli.py --list-themes
```

#### 5 种页面主题

| 主题 | 风格 | 适合 |
|:-----|:-----|:-----|
| `lapis` | 青金石蓝，清爽商务 | 科技、商业 |
| `forest` | 墨绿，自然沉稳 | 读书、知识 |
| `ocean` | 深海蓝，专业 | 财经、深度 |
| `sunset` | 暖橙，阅读舒适 | 情感、生活 |
| `noir` | 黑白极简 | 技术文档 |

#### 5 种代码高亮

| `solarized-light` | `vscode-dark` | `github` | `monokai` | `one-dark` |
|:---:|:---:|:---:|:---:|:---:|

#### 支持语法

标题 / 粗体 / 斜体 / 删除线 / 标记 / 下划线 / 上下标 / 代码块 / 行内代码 / 引用 / 列表 / 任务列表 / 表格 / 链接 / 图片 / 脚注 / 分割线 / GitHub 警告框

---

### 发布 — `scripts/publisher/`

> 需要 `WECHAT_APP_ID` + `WECHAT_APP_SECRET`，在[微信公众平台 → 开发 → 基本配置](https://mp.weixin.qq.com/) 获取。

```bash
python scripts/publisher/publish.py article.md                    # 本地发布
python scripts/publisher/publish.py article.md ocean monokai      # 指定主题
python scripts/publisher/publish_with_video.py article.md         # 含视频
python scripts/publisher/publish_remote.py article.md             # 远程 MCP
```

IP 白名单要求：
- 本地发布 → 本机 IP 加入白名单
- 远程 MCP → 服务器 IP 加入白名单

---

## 配置说明

### config.yaml

所有模块参数集中管理，编辑即生效：

```yaml
spider:
  parallel_downloads: 5       # 图片并行数
  image_timeout: 15           # 超时（秒）

search:
  max_results: 10             # 搜索结果数
  request_delay_ms: 800       # 请求间隔（防封）

publisher:
  theme: "lapis"              # 默认主题
  highlight: "solarized-light" # 默认代码高亮

typeset:
  local_fallback: true        # 本地排版降级
```

### .env

```
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
SOGOU_COOKIE=...
```

#### 获取 SOGOU_COOKIE

1. 浏览器打开 [weixin.sogou.com](https://weixin.sogou.com/)
2. F12 → Network → 刷新页面 → 点击任意请求
3. Request Headers → 复制 `Cookie` 完整值 → 粘贴到 `.env`

Cookie 有效期数天，过期后需重新获取。

### 优先级

```
CLI 参数 > 环境变量 > .env 文件 > config.yaml > 代码默认值
```

---

## 项目结构

```
wechat-mp-suite/
├── setup.py                        # 一键初始化向导
├── check.py                        # 环境检测工具
├── config.yaml                     # 统一配置
├── .env.example                    # 凭证模板
├── requirements.txt                # Python 依赖
├── CHANGELOG.md
├── MIGRATION.md                    # v1.0.1 → v1.0.2 迁移指南
├── lib/
│   └── config_loader.py            # 统一读取 config + .env
├── scripts/
│   ├── search/                     # 搜狗微信搜索
│   │   ├── index.py                # CLI 入口
│   │   ├── fetcher.py              # UA 池、重试、Cookie
│   │   └── parser.py               # HTML 解析
│   ├── spider/                     # 文章爬虫
│   │   ├── main.py                 # 主入口
│   │   ├── scraper.py              # 文章抓取
│   │   └── images.py               # 并行图片下载
│   ├── downloader/
│   │   └── download.py
│   ├── publisher/                  # 发布
│   │   ├── publish.py              # 本地
│   │   ├── publish_with_video.py   # 含视频
│   │   ├── publish_remote.py       # 远程 MCP
│   │   └── publish-remote.ps1      # Windows 远程脚本
│   └── typeset/                    # 排版引擎
│       ├── cli.py                  # CLI
│       ├── typeset.py              # 核心（700+ 行）
│       ├── themes.py               # 5 页面主题
│       ├── code_themes.py          # 5 代码主题
│       └── syntax_highlight.py     # 语法高亮
├── references/
│   └── SPEC.md                     # 排版 HTML 生成规范
└── tests/
    └── test_spider.py              # 15 个测试用例
```

---

## 测试

```bash
python -m pytest tests/test_spider.py -v
```

---

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| 爬虫 SSL 错误 | 网络环境受限 | `export HTTPS_PROXY=http://127.0.0.1:7890` |
| 搜索返回空 | 无 Cookie 或过期 | 重新获取 `SOGOU_COOKIE` |
| 排版样式不对 | 微信编辑器过滤 CSS | 用 `--theme lapis`（最兼容） |
| 发布 40001 | Token 失效 | 检查 `WECHAT_APP_SECRET` 是否正确 |

---

## 写作 / 洗稿 / 配图（AI 模块）

这三个模块通过对话触发，无需脚本：

| 功能 | 触发词示例 |
|------|-----------|
| 写作 | "帮我写一篇公众号文章" / "用刘润风格分析..." / "写篇财经夜报" |
| 洗稿 | "帮我洗稿这篇文章" / "改写成原创" / "去 AI 味" |
| 配图 | "生成封面图" / "这篇文章配什么图" |

详细 prompt 规范和写作风格说明见 `SKILL.md`。

---

## License

MIT
