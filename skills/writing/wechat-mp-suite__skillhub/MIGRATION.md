# v1.0.1 → v1.0.2 迁移指南

> **一句话说清楚**：我们用 Python 重写了全部脚本，你不再需要 Node.js。

---

## 三分钟迁移清单

| 步骤 | 操作 | 说明 |
|:----:|------|------|
| 1 | `pip install -r requirements.txt` | 安装 5 个 Python 依赖包 |
| 2 | `cp .env.example .env` | 旧版 `wechat.env` 改名为 `.env`，格式不变 |
| 3 | 删掉 `node_modules/` | 不再需要，可放心删除 |
| 4 | 卸载 `wenyan` CLI（可选） | `npm uninstall -g @wenyan-md/cli` |
| 5 | 更新你的 alias / 快捷命令 | 所有 `node xxx.js` → `python3 xxx.py` |

---

## 命令对照表

### 搜索

| v1.0.1 (Node.js) | v1.0.2 (Python) |
|---|---|
| `node scripts/search/search_wechat.js "关键词"` | `python scripts/search/index.py "关键词"` |
| `node scripts/search/... "关键词" -n 5 -c` | `python scripts/search/index.py "关键词" -n 5 -c` |

参数名完全兼容（`-n` / `-c` / `-r` / `-o`），无需改习惯。

### 爬虫

| v1.0.1 | v1.0.2 |
|---|---|
| `python3 scripts/spider/main.py URL` | **不变** |

爬虫模块本来就是 Python，无需调整。

### 下载

| v1.0.1 (Node.js) | v1.0.2 (Python) |
|---|---|
| `node scripts/downloader/download.js URL` | `python scripts/downloader/download.py URL` |

### 排版

| v1.0.1 (Node.js) | v1.0.2 (Python) |
|---|---|
| `node scripts/typeset/wechat-dual-copy.js article.md` | `python scripts/typeset/cli.py article.md --theme lapis` |
| `node scripts/typeset/html-to-wechat-copy.js file.html` | **不再需要**，`cli.py` 统一处理 Markdown → HTML |

重大变化：排版引擎从外部服务依赖改为纯本地 Python 引擎，**零网络依赖，离线可用**。

### 发布

| v1.0.1 | v1.0.2 |
|---|---|
| `node scripts/publisher/publish.js article.md` | `python scripts/publisher/publish.py article.md` |
| `wenyan publish -f article.md -t lapis` | `python scripts/publisher/publish.py article.md lapis monokai` |
| `bash scripts/publisher/publish-remote.sh article.md` | `python scripts/publisher/publish_remote.py article.md` |

`wenyan` CLI 已废弃，本地发布改为纯 Python 直接调微信 API。

---

## 凭证文件迁移

| v1.0.1 | v1.0.2 |
|---|---|
| `scripts/publisher/wechat.env` | 项目根目录 `.env` |
| 格式：`export WECHAT_APP_ID="wx..."` | 格式：`WECHAT_APP_ID=wx...` |

迁移操作：

```bash
# 旧版格式 (wechat.env)
export WECHAT_APP_ID="wx1234567890"
export WECHAT_APP_SECRET="abc123def456"

# 新版格式 (.env) —— 去掉 export 和引号即可
WECHAT_APP_ID=wx1234567890
WECHAT_APP_SECRET=abc123def456
```

---

## 不再需要的环境

| 旧依赖 | 处理方式 |
|---|---|
| Node.js (≥18) | **不再需要**（除非你有其他项目用到） |
| npm 全局包 `cheerio` | 卸载 |
| npm 全局包 `@wenyan-md/cli` | 卸载 |
| Google Chrome（下载模块） | 不再需要，改为纯 HTTP 请求 |
| `curl` / `jq` | 不再需要 |
| `puppeteer` | 不再需要 |
| 排版外部服务 `edit.shiker.tech` | 不再需要，本地引擎替代 |

---

## 新增特性一览

| 特性 | v1.0.1 | v1.0.2 |
|---|---|---|
| 排版引擎 | 依赖外部服务 | 纯本地 Python，离线可用 |
| 排版主题 | 外部服务提供 | 5 种内置主题 + 5 种代码高亮 |
| 图片下载 | 单线程 | 多线程（3-5x 加速）+ 自动重试 |
| 统一配置 | 无 | `config.yaml` 集中管理 |
| Docker 镜像 | `nikolaik/python-nodejs` (~500MB) | `python:3.12-slim` (~120MB) |
| Windows 支持 | ❌ | ✅（含 `.ps1` 脚本） |
| 测试覆盖 | 无 | 15 个测试用例 |
| 搜索模块 | `-r` 解析真实 URL | `-r` 解析真实 URL + `--cookie` 直接传入 Cookie |

---

## 验证迁移是否成功

```bash
python -c "import requests, bs4, yaml, dotenv; print('all good')"
```

输出 `all good` 即表示依赖安装成功。

---

## 有问题？

参考 [README.md](./README.md) 的"常见问题"章节，或查看 `references/` 目录下的详细文档。
