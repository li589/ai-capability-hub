# 情报数据源说明

## 内置 RSS 数据源（13 个，默认全部启用）

| 标识符 | 名称 | URL | 语言 | 类型 |
|-------|------|-----|------|------|
| 安全圈 | 安全圈（微信公众号） | https://wechat2rss.xlab.app/feed/d568d6fca93d750898111f09cc3c551e7a62f7ab.xml | 中文 | 行业资讯聚合 |
| 看雪论坛 | 看雪论坛 | https://wechat2rss.xlab.app/feed/0e026637254d450ae84c59f87d4e4fb4616651ca.xml | 中文 | 逆向/漏洞技术 |
| FreeBuf | FreeBuf | https://www.freebuf.com/feed | 中文 | 综合安全媒体 |
| 嗅学安全 | 嗅学安全（微信公众号） | https://wechat2rss.xlab.app/feed/b15a925f83a4b108b957f8dd0e8030b6caa7da5e.xml | 中文 | 威胁分析 |
| Krebs on Security | Krebs on Security | https://krebsonsecurity.com/feed/ | 英文 | 知名安全博客/调查 |
| Threatpost | Threatpost | https://threatpost.com/feed/ | 英文 | 安全新闻 |
| Dark Reading | Dark Reading | https://www.darkreading.com/rss_simple.asp | 英文 | 企业安全媒体 |
| Schneier on Security | Schneier on Security | https://www.schneier.com/feed/atom/ | 英文 | 安全专家博客 |
| CISA | CISA 网络安全公告 | https://www.cisa.gov/news-events/cybersecurity-advisories/rss | 英文 | 美国官方机构 |
| Ars Technica Security | Ars Technica 安全版块 | https://arstechnica.com/security/feed/ | 英文 | 科技媒体安全栏目 |
| The Register | The Register 安全 | https://www.theregister.com/security/headlines.atom | 英文 | 科技新闻 |
| Wired Security | Wired 安全 | https://www.wired.com/feed/category/security/latest/rss | 英文 | 主流科技媒体 |
| Microsoft Security | 微软安全博客 | https://www.microsoft.com/en-us/security/blog/feed/ | 英文 | 厂商官方博客 |

## 自定义 RSS 源管理

用户可通过配置向导新增、禁用、删除 RSS 数据源，无需修改脚本代码。

### 新增自定义源

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py
# 选择菜单 → 2. 新增自定义 RSS 源
```

也可通过告知 AI 的方式新增，例如：
> "帮我添加 SecurityWeek 的 RSS 源：https://www.securityweek.com/feed/"

### 推荐的额外 RSS 源

| 名称 | URL | 特点 |
|------|-----|------|
| SecurityWeek | https://www.securityweek.com/feed/ | 企业安全新闻 |
| BleepingComputer | https://www.bleepingcomputer.com/feed/ | 病毒/勒索/泄露 |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews | 高频更新 |
| Recorded Future | https://www.recordedfuture.com/feed | APT/情报分析 |
| Securelist (Kaspersky) | https://securelist.com/feed/ | APT/恶意软件 |
| Unit 42 (Palo Alto) | https://unit42.paloaltonetworks.com/feed/ | 威胁研究 |
| 安全客 | https://api.anquanke.com/data/v1/rss | 中文综合 |
| 奇安信威胁情报 | https://ti.qianxin.com/blog/feed | 中文 APT/分析 |

## 专项情报源

### 0.zone 勒索情报

- **URL 格式**: `https://0.zone/article/{YYYYMMDD}`
- **更新频率**: 按天更新
- **内容**: 全球勒索软件受害者追踪、被盗数据公告、勒索组织动态
- **注意**: 部分内容可能受地区访问限制，爬取失败时应在报告中注明

## 爬取注意事项

1. **微信 RSS 源（wechat2rss.xlab.app）**：为第三方转换服务，可能存在延迟或失效风险
2. **CISA RSS**：内容权威但更新频率较低，适合关注官方漏洞预警
3. **Wired / The Register**：可能存在 Cloudflare 防护，偶发 403/429 错误属正常现象
4. **0.zone**：为动态渲染页面，依赖正则提取，如页面结构变化需更新解析逻辑
5. **日期过滤**：RSS 文章按发布时间过滤，允许 ±1 天误差（时区差异）

## 中文来源权重

中文安全媒体更关注国内威胁动态，在报告中应重点突出：
- 涉及国内企业、系统、政策的情报
- 国内已公开披露的漏洞和攻击事件
- 国内安全厂商的威胁分析报告
