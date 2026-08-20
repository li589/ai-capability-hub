# 故障排除与避坑指南（TROUBLESHOOTING）

> 面向 cn-financial-scraper v5.0.0 用户。覆盖**安装、爬取、反爬、验证码、编码、并发、数据源**七大类高频坑。
> 每条错误都包含：症状 → 根因 → 解决 → 预防。

---

## 📑 目录

1. [安装与环境](#1-安装与环境)
2. [网络与代理](#2-网络与代理)
3. [反爬与验证码](#3-反爬与验证码)
4. [编码与解析](#4-编码与解析)
5. [性能与并发](#5-性能与并发)
6. [数据验证](#6-数据验证)
7. [MCP / Claude Code 集成](#7-mcp--claude-code-集成)
8. [v5.0 新增模块问题](#8-v50-新增模块问题)
9. [错误码速查表](#9-错误码速查表)
10. [如何提 Issue](#10-如何提-issue)

---

## 1. 安装与环境

### 1.1 `pip install` 慢 / 失败

**症状**：`pip install -r requirements.txt` 卡 10 分钟以上或 `ReadTimeoutError`。

**根因**：默认 PyPI 源在国外，国内网络易超时。

**解决**：
```bash
# 清华镜像（推荐）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 阿里镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 中科大镜像
pip install -i https://pypi.mirrors.ustc.edu.cn/simple -r requirements.txt

# 一键安装脚本（自动选最佳源）
python setup_env.py --recommended
```

**预防**：把 `pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple` 加入系统配置。

---

### 1.2 `playwright install` 失败

**症状**：`playwright install chromium` 长时间卡住或下载失败。

**根因**：Chromium 二进制下载源在海外。

**解决**：
```bash
# 设置 Playwright 镜像（中国官方镜像）
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium

# 或手动安装二进制
# 1. 下载 playwright-browslers-chromium
# 2. 放在 %LOCALAPPDATA%\ms-playwright\chromium-XXXX\
```

**预防**：在 CI 或重装机器时优先设置环境变量。

---

### 1.3 `ModuleNotFoundError: No module named 'playwright'`

**症状**：MCP 调用 `scrape_webpage` 时报模块未找到。

**根因**：Playwright 是**可选依赖**，按需安装。

**解决**：
```bash
# 方式 1：完整安装
pip install playwright && playwright install chromium

# 方式 2：跳过 Playwright，使用 `mode="static"`（默认）
# 这只走 HTTP 请求 + HTML 解析，对动态渲染页面会失败
```

**预防**：使用 `mode="realtime"` 之前先确认 Playwright 已安装。

---

### 1.4 不同 Python 解释器混乱

**症状**：有时 `import scripts` 失败，有时正常。

**根因**：系统有多个 Python（如 conda + 系统 Python）。

**解决**：
```bash
# 检查当前解释器
python -c "import sys; print(sys.executable, sys.version)"

# 强制使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

**预防**：项目根目录加 `.python-version`（用 pyenv）固定 Python 版本。

---

## 2. 网络与代理

### 2.1 `ConnectionRefusedError` / `Connection reset`

**症状**：爬某些网站立刻断开连接。

**根因**：
- 服务器主动拒绝（IP 被拉黑）
- 防火墙/NAT 会话超时

**解决**：
```python
from scripts.http_utils import set_proxy
set_proxy("http://127.0.0.1:7890")  # Clash / V2Ray 本地端口

# 或在 MCP 调用里指定
scrape_webpage(url="...", proxy="socks5://127.0.0.1:1080")
```

**预防**：
- 用同一个 IP 短时间请求不超过 50 次 / 分钟
- 间隔随机化（`time.sleep(random.uniform(1, 3))`）

---

### 2.2 `urllib3` SSL 错误 / `CERTIFICATE_VERIFY_FAILED`

**症状**：`[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`

**根因**：本地 CA 证书过期或代理中间人证书未安装。

**解决**：
```bash
# 临时方案（不推荐生产使用）
export CURL_CA_BUNDLE=""
# 或
python -c "import ssl; ssl._create_default_https_context = ssl._create_unverified_context"

# 正式方案：安装代理 CA 证书
# Windows：双击 .crt 文件 → 安装到"受信任的根证书颁发机构"
# Mac：sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain xxx.crt
```

---

### 2.3 反复 504 / 502 网关错误

**症状**：站点正常但爬虫频繁收到 5xx。

**根因**：源站用 CDN，对单一 IP 短时间请求有限速。

**解决**：
```python
# 自动重试（已内置）
scrape_webpage(url="...", retry=3, backoff_factor=0.5)

# 或显式
import time, random
for attempt in range(5):
    try:
        r = scrape_webpage(url=url)
        break
    except Exception:
        time.sleep(2 ** attempt + random.uniform(0, 1))
```

---

## 3. 反爬与验证码

### 3.1 IP 被封 → 一直 403

**症状**：同一 IP 爬几次后 `403 Forbidden`。

**根因**：网站把当前 IP 加入临时黑名单。

**解决**：
1. 立即暂停 5-10 分钟
2. 切换代理 IP（推荐住宅代理或自建 IP 池）
3. 降低频率（单次间隔 ≥3 秒）

**预防**：
```python
# 自动频率控制（默认开启）
scrape_webpage(url="...", rate_limit=0.5)  # 0.5 req/s
```

---

### 3.2 滑动验证码 / 点选验证码

**症状**：返回的 HTML 里只有「请完成验证」的脚本，没有实际数据。

**根因**：网站触发了高级验证（极验/网易易盾/腾讯防水墙）。

**解决**：
```python
# 方案 1：使用 Playwright 手打（仅调试用）
scrape_webpage(url="...", mode="realtime", manual_captcha=True)

# 方案 2：换 IP + 浏览器无痕
import asyncio
from playwright.async_api import async_playwright

async def bypass():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 让用户手动过验证码
        page = await browser.new_page()
        await page.goto(url)
        # 用户手动完成验证
        await page.wait_for_load_state("networkidle")
        html = await page.content()
        await browser.close()
        return html
```

**预防**：付费 / 验证码密集型站点请接入打码平台（成本约 0.5-2 分 / 次）。

---

### 3.3 返回空数据但状态码 200

**症状**：HTTP 200 OK，但 HTML 完全是空标签，正文靠 JS 渲染。

**根因**：SPA 应用，初始 HTML 无内容。

**解决**：
```python
# 切到实时渲染模式
result = scrape_webpage(url=url, mode="realtime")
# 内部用 Playwright + wait_for_selector
```

**预防**：先用浏览器打开目标 URL，View Source 查看是否为空；如是，启用 `mode="realtime"`。

---

### 3.4 User-Agent 失效 → 抓到的是「请升级浏览器」

**症状**：返回内容是 HTML banner「您的浏览器版本过低」，没有任何有用信息。

**根因**：UA 被反爬系统识别为爬虫。

**解决**：
```python
from scripts.http_utils import set_user_agent
set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...")
# 或随机 UA（默认开启）
from scripts.http_utils import enable_ua_rotation
enable_ua_rotation(True)
```

**预防**：把 `enable_ua_rotation=True` 写进配置（默认已开）。

---

## 4. 编码与解析

### 4.1 中文乱码 / `UnicodeDecodeError`

**症状**：解析 HTML 时部分字符变成 `??` 或 `�`。

**根因**：源站声明 ISO-8859-1 编码但实际是 UTF-8，或反之。

**解决**：
```python
from scripts.http_utils import decode_response
text = decode_response(response_bytes, default_encoding="utf-8")
# 自动尝试 utf-8 / gbk / gb18030 直到成功
```

**预防**：使用 `decode_response(response)` 代替 `response.text` 自动嗅探。

---

### 4.2 PDF 解析出乱码文字

**症状**：`parse_document("xxx.pdf")` 返回的文字顺序错乱或乱码。

**根因**：
- PDF 是扫描件（图片），需要 OCR
- PDF 用了非标准字体子集

**解决**：
```bash
# 安装 OCR 依赖
pip install pytesseract pdf2image

# 系统层安装（Windows）
# 1. 下载 tesseract：https://github.com/UB-Mannheim/tesseract/wiki
# 2. 加 PATH

# 调用时启用 OCR
result = parse_document("xxx.pdf", ocr=True, ocr_lang="chi_sim+eng")
```

**预防**：解析前调用 `parse_document("xxx.pdf", info_only=True)` 看是否含可提取文本。

---

### 4.3 日期解析失败

**症状**：`parse_date("2024-01-01")` 抛 `ValueError`。

**根因**：源站格式不标准（如 `2024/01/01` `2024年1月1日` `Jan 1, 2024`）。

**解决**：
```python
from scripts import parse_date
# 自动识别多种格式
d = parse_date("2024年1月1日")  # → datetime(2024, 1, 1)
d = parse_date("Jan 1, 2024")    # → datetime(2024, 1, 1)
```

如果仍未识别：
```python
# 自定义正则
import re
m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
if m:
    d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
```

---

## 5. 性能与并发

### 5.1 批量爬取卡死

**症状**：`batch_crawl_institutions(institutions=institutions)` 长时间无返回。

**根因**：默认并发数太高（> 20），触发目标站反爬。

**解决**：
```python
# 主动降并发
batch_crawl_institutions(
    institutions=institutions,
    max_workers=3,         # 建议 ≤ 5
    request_delay=2.0,     # 每请求间休眠（秒）
    timeout=30,            # 单请求超时
)
```

---

### 5.2 内存占用过高

**症状**：批量爬取 500+ 机构时内存 > 4 GB。

**根因**：所有结果累积在内存里。

**解决**：
```python
# 启用磁盘流式 + 断点续爬（默认开启）
batch_crawl_institutions(
    institutions=institutions,
    cache_dir="data/scrape_cache",  # 自动分批落盘
    resume=True,                     # 中断后可继续
)
```

---

### 5.3 单次请求超时（30s 仍不够）

**症状**：`Timeout` exception，metadata 显示 `read=30.0`。

**解决**：
```python
scrape_webpage(url=url, timeout=120)            # 单次 120s
batch_crawl_institutions(institutions, per_timeout=120)
```

**预防**：对内部 / 大文件 URL 用更长超时。

---

## 6. 数据验证

### 6.1 `data_validator.py` 报错「JSON 解析失败」

**症状**：
```
❌ institution_registry.json: JSON 解析失败: Expecting ',' delimiter (line 1234)
```

**根因**：之前爬取写入时进程被 kill，导致 JSON 截断。

**解决**：
```bash
# 1. 备份损坏文件
cp data/institution_registry.json data/institution_registry.json.bak

# 2. 手动修复或重建
python scripts/institution_updater.py --rebuild

# 3. 校验
python scripts/data_validator.py
```

**预防**：写入用 `tempfile + os.replace` 原子写入而非直接覆盖。

---

### 6.2 重复机构名导致查询冲突

**症状**：`query_institution("华夏")` 返回多个匹配但只想要第一个。

**解决**：
```python
# 返回 dict 而非 list
r = query_institution("华夏", unique=True)

# 或精确匹配
r = query_institution(name_exact="华夏基金")
```

---

### 6.3 列表「空」但 validator 显示 0 条

**症状**：`list_sentiment_targets()` 返回空。

**根因**：自定义目标列表保存在 `data/sentiment_custom_targets.json`，首次使用需初始化。

**解决**：
```bash
# 跑一次后会创建
python scripts/sentiment_crawler.py --list-targets
```

---

## 7. MCP / Claude Code 集成

### 7.1 Claude Code 中调用 `scrape_webpage` 无响应

**症状**：调用后挂在 loading 状态。

**根因**：
- Playwright 第一次启动会下载浏览器
- 大批量任务未启用流式输出

**解决**：
```bash
# 检查 MCP 服务器是否正常启动
python mcp_server.py --check

# 看日志（默认在 data/scheduler_logs/）
tail -f data/scheduler_logs/cn_fin_scraper_*.log

# 启用流式（实时回显进度）
scrape_webpage(url=url, stream=True)
```

---

### 7.2 MCP 工具名字找不到

**症状**：调用 `crawl_news` 报「Tool not found」。

**根因**：版本 ≤ v4.2 的工具名。

**解决**：
```bash
# 查看当前所有可用工具
python mcp_server.py --list-tools

# v4.3+ 重命名: crawl_news → crawl_financial_news
```

---

### 7.3 MCP 启动时报 `httpx` 版本冲突

**症状**：`ImportError: cannot import name 'AsyncClient' from 'httpx'`

**根因**：Claude Code 自带的 httpx 与本工具要求冲突。

**解决**：
```bash
# 升级到兼容版本
pip install httpx>=0.27

# 重启 MCP 服务器
```

---

## 8. v5.0 新增模块问题

### 8.1 akshare 返回空数据或报错

**症状**：`get_structured_data("shibor")` 返回 None，或报 `ModuleNotFoundError: No module named 'akshare'`

**根因**：akshare 是可选依赖，v5.0 结构化数据和数据源兜底都需要它

**解决**：
```bash
pip install akshare
# 验证
python -c "import akshare; print('akshare 版本:', akshare.__version__)"
```

**预防**：使用 `python setup_env.py --full` 安装全功能依赖

---

### 8.2 RSS 数据源返回空

**症状**：舆情爬取时 RSS 源返回 0 条结果

**根因**：
- RSS 源 URL 变更或失效
- 网络无法访问 RSS 端点

**解决**：
```python
# 检查 RSS 源是否可达
from scripts.sentiment_crawler import _rss_fetcher
result = _rss_fetcher.fetch("https://rsshub.app/cls/telegraph")
print(f"获取 {len(result)} 条")
```

**预防**：RSS 是零反爬的备用通道，主源正常时优先用主源

---

### 8.3 浏览器单例复用导致页面残留

**症状**：连续爬取多个网站时，第二个网站的页面内容混入第一个网站的数据

**根因**：进程级单例浏览器的标签页未清理

**解决**：
```python
# 显式释放浏览器实例
from scripts.browser_scraper import release_browser
release_browser()

# 或在每次爬取后清理
bs = BrowserScraper()
result = bs.extract(url)
bs.close()  # 显式关闭
```

**预防**：v5.0 的 `_get_browser_scraper` 单例会在新请求前自动清理旧标签页，一般不会出现此问题

---

### 8.4 软封禁检测误报

**症状**：正常页面被标记为"软封禁"并自动切换到浏览器兜底

**根因**：某些网站返回的 HTML 包含"验证"等关键词，但实际是正常内容

**解决**：
```python
# 跳过软封禁检测
result = scrape_webpage(url="...", skip_soft_block_check=True)
```

**预防**：软封禁检测默认开启，对大多数场景有效；如遇误报可关闭

---

### 8.5 结构化数据类型不存在

**症状**：`get_structured_data("xxx")` 返回 None，但不知道支持哪些类型

**解决**：
```python
from scripts import list_data_types
print(list_data_types())
# 返回: ['futures_spot', 'futures_daily', 'macro_gdp', 'macro_cpi', 'macro_ppi',
#         'macro_pmi', 'macro_forex', 'shibor', 'shibor_1w', 'hk_stock', 'us_stock', ...]
```

---

### 8.6 百度/搜狗搜索引擎被限流

**症状**：`quick_search("...", engines=["baidu_html"])` 返回空或报 429

**根因**：搜索引擎对频繁请求有限流

**解决**：
```python
# 降低搜索频率
quick_search("贵州茅台", engines=["baidu_html"], rate_limit=2.0)

# 或切换到 DDG（无限流但中文召回差）
quick_search("贵州茅台", engines=["ddg"])
```

**预防**：`MultiEngineSearch` 默认自动降级（百度→搜狗→DDG→SearXNG），一般无需手动处理

---

## 9. 错误码速查表

| 错误类型 | 含义 | 推荐动作 |
|---------|------|---------|
| `ConnectionRefusedError` | 端口关闭 / 防火墙 | 切换代理 |
| `urllib.error.URLError: timed out` | 网络超时 | 增加 `timeout=`，重试 |
| `urllib.error.HTTPError: 400` | URL 错误或参数缺失 | 检查 URL 格式 |
| `urllib.error.HTTPError: 401/403` | 鉴权 / IP 被封 | 换 IP 或登录 |
| `urllib.error.HTTPError: 404` | URL 已失效 | 更新机构 URL 库 |
| `urllib.error.HTTPError: 418` | 被反爬系统识别为爬虫 | 切换 UA + 降频 |
| `urllib.error.HTTPError: 429` | 请求过于频繁 | 降并发 + 加长间隔 |
| `urllib.error.HTTPError: 500/502/503` | 源站异常 | 稍后重试 |
| `urllib.error.HTTPError: 521/522/523` | CDN 故障 | 切换代理 |
| `ssl.SSLCertVerificationError` | 证书问题 | 安装代理 CA 或改 `verify=False` |
| `UnicodeDecodeError` | 编码错误 | 用 `decode_response()` 自动嗅探 |
| `playwright._impl._errors.TimeoutError` | 浏览器启动超时 | `playwright install chromium` |
| `ModuleNotFoundError` | 缺依赖 | `pip install -r requirements.txt` |

---

## 10. 如何提 Issue

如果上面的指南没解决您的问题：

1. **必填信息**：
   - `cn-financial-scraper --version` 输出
   - Python 版本：`python --version`
   - 完整错误堆栈（`python -X dev your_script.py 2>&1 | tee error.log`）
   - 重现命令（剥离敏感数据后）

2. **可选但重要**：
   - 系统信息（Windows 11 / macOS 14 / Ubuntu 22）
   - 网络环境（直连 / 代理 / VPN）
   - 目标 URL（脱敏后）

3. **提交渠道**：
   - GitHub Issues：附上上面所有信息
   - 微信群 / 知识星球：截图 + 简短描述

---

## 附：常见 python 环境就绪检查命令

```bash
# 一次性验证脚本（推荐加到 CI）
python -c "
import sys
checks = []
# 版本
checks.append(('Python >= 3.8', sys.version_info >= (3, 8)))
# 关键依赖
for mod in ('requests', 'urllib3', 'playwright', 'bs4', 'lxml'):
    try:
        __import__(mod); checks.append((f'{mod} 可导入', True))
    except ImportError:
        checks.append((f'{mod} 缺失', False))
# 输出
ok = sum(1 for _, v in checks if v)
print(f'环境检查: {ok}/{len(checks)} 通过')
for name, val in checks:
    print(f'  [{\"✓\" if val else \"✗\"}] {name}')
"
```

---

*最后更新：v5.0.0（2026-08-10）*
*反馈：见 README.md 中的支持渠道*
