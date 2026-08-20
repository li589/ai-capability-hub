# Changelog

All notable changes to wechat-mp-suite are documented here.

---

## [1.0.2] - 2026-07-06

### Changed
- **统一 Python 技术栈**：全部模块从 Node.js 迁移至纯 Python，移除所有 JS 依赖
  - `scripts/search/`：fetcher.js + parser.js + index.js → fetcher.py + parser.py + index.py
  - `scripts/downloader/`：download.js (Puppeteer) → download.py (requests + bs4)
  - `scripts/publisher/`：publish.js + publish_with_video.js → publish.py + publish_with_video.py
  - `scripts/typeset/`：整个排版模块（wechat-html.js + lib/ 等）→ typeset.py + cli.py + themes.py + code_themes.py + syntax_highlight.py
- **Dockerfile 精简**：从 `nikolaik/python-nodejs` 双镜像改为 `python:3.12-slim`，镜像体积减少约 60%
- **统一配置**：新增 `config.yaml` 集中管理所有模块参数
- **凭证安全**：新增 `.env.example`，所有 API 密钥统一通过 `.env` 管理

### Added
- **本地排版引擎**：纯 Python 实现 Markdown→微信 HTML 转换器，5 种主题（lapis/forest/ocean/sunset/noir）+ 5 种代码高亮主题，零外部依赖
- **并行图片下载**：`images.py` 使用 ThreadPoolExecutor 多线程下载，速度提升 3-5 倍
- **图片重试机制**：3 次自动重试 + 指数退避
- **Windows 支持**：`publish-remote.ps1` PowerShell 发布脚本
- **Docker 部署**：新增 `Dockerfile` + `requirements.txt`
- **测试体系**：`tests/` 目录，15+ 测试用例
- **配置加载器**：`lib/config_loader.py`，统一读取 config.yaml + .env

### Removed
- 所有 Node.js 依赖（cheerio, puppeteer, undici, wenyan-cli 等）
- `node_modules/` 目录（不再需要）

---

## [1.0.1] - 2026-04-07

### Added
- **模块二（下载器）**：新增 `scripts/downloader/download.js`，基于 Puppeteer，支持懒加载图片、视频链接嗅探、完整 DOM 渲染，适合需要完整文章内容的场景
- **远程 MCP 发布**：新增 `scripts/publisher/publish-remote.sh`，通过远程 wenyan-mcp 服务中转发布，解决家庭宽带 IP 白名单问题
- **含视频文章发布**：新增 `scripts/publisher/publish_with_video.js`，支持上传视频封面并发布图文+视频组合内容
- **财经夜报写作风格**：模块三新增财经老韭菜视角写作风格

### Changed
- 模块一览从「七大模块」扩展为「八大模块」，补全下载器模块说明
- SKILL.md 结构优化，新增 Quick Start 触发词示例表
- 排版模块新增外部服务依赖声明
- 所有工作流示例路径统一为 `{baseDir}` 占位符

### Fixed
- 修正工作流示例中使用相对路径的问题

---

## [1.0.0] - 2026-04-06

### Added
- 初始版本，包含七大模块：搜索、爬虫、写作（刘润/爆款/真人）、洗稿、AI配图、排版、发布
- `scripts/search/search_wechat.js`：搜狗微信搜索，支持批量抓取正文
- `scripts/spider/`：Python 实现，轻量级文章爬取
- `scripts/typeset/`：Markdown → 微信富文本排版，双版本预览
- `scripts/publisher/publish.js`：本地 wenyan-cli 发布
