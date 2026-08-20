# 外资研报查询 · 接口参考

MCP 命名空间：`user-comein-brm`

---

## 1. research_query（条件检索 / 分页）

查外资时 **必须** `type: "oversea"`。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | 固定 `"oversea"` |
| `startTime` | 否 | `yyyy-MM-dd HH:mm:ss` 或 `yyyy-MM-dd`；不传默认近 30 天 |
| `endTime` | 否 | 同上；不传默认当前时间 |
| `page` | 否 | 默认 1 |
| `pageSize` | 否 | 默认 20，**最大 100**；全量翻页用 100 |
| `keywords` | 否 | 关键词模糊匹配（如 Cloudflare、HBM、memory） |
| `stockCode` | 否 | 股票代码/ticker；可配 market |
| `market` | 否 | `sz` / `sh` / `bj` / `hk` / `us` |
| `industryName` | 否 | 申万一级行业名，**不带「行业」后缀** |
| `region` | 否 | **仅 oversea 生效**：研报标的所属地区（非机构所在地） |
| `divergenceLevel` | 否 | `low` / `medium` / `high`，默认 `low` |
| `groupIds` | 否 | 自选分组；`-1` 为全部 |
| `featuredTagNames` | 否 | 特色标签 |

### 发布机构限制

`research_query` 当前没有发布机构参数。需要按高盛、摩根大通、摩根士丹利等机构生成日报时，必须先拉取指定日期的全量外资研报，再依据返回的机构字段或标题前缀归一分组。

- `region` 是研报研究对象所在地区，不能用于筛选发布机构。
- `keywords` 是内容关键词，不能保证完整召回某家机构的全部研报。
- 机构日报的完整流程见 [institution-report.md](institution-report.md)。

### region 枚举

| 值 | 含义 |
|----|------|
| `cn_mainland` | 中国大陆（A 股/中国宏观等） |
| `cn_hongkong` | 中国香港 |
| `cn_taiwan` | 中国台湾 |
| `europe` | 欧洲 |
| `southeast_asia` | 东南亚 |
| `north_america` | 北美 |
| `latin_america` | 拉美 |
| `japan` | 日本 |
| `korea` | 韩国 |
| `india` | 印度 |
| `australia` | 澳洲 |
| `other` | 其他 |

例：高盛写 A 股 → `region=cn_mainland`（不是 north_america）。

### 调用示例

```json
// 个股
{ "type": "oversea", "stockCode": "NET", "market": "us", "startTime": "2026-05-10", "endTime": "2026-08-10", "page": 1, "pageSize": 100 }

// 关键词 + 地区
{ "type": "oversea", "keywords": "HBM", "region": "korea", "startTime": "2026-08-01", "endTime": "2026-08-10", "page": 1, "pageSize": 100 }

// 单日全量（全市场日报基准）
{ "type": "oversea", "startTime": "2026-08-09 00:00:00", "endTime": "2026-08-09 23:59:59", "page": 1, "pageSize": 100 }
```

### 分页终止

满足任一即停：返回空 / 本页条数 < pageSize / 达 max_pages（建议 100）。

---

## 2. searchForeignReports（语义检索）

向量库检索，适合主题与观点，不保证某一天「全量无遗漏」。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `query` | 是 | **英文**自然语言；写明行业/公司/事件 |
| `filterImage` | 是 | 默认 `true`（过滤图片类）；用户明确要图表时才 `false` |
| `start_time` | 否 | `YYYY-MM-DD` |
| `topK` | 否 | 1–50；不传用服务端默认 |

### query 写法

| 好 | 差 |
|----|----|
| `Impact of US Fed rate path on emerging market equities` | `外资怎么看美联储` |
| `Cloudflare NET edge AI inference and developer platform outlook` | `有没有 Cloudflare 研报` |
| `China AI foundation model monetization vs price war` | `中国 AI` |

### start_time 默认窗口（用户未指定时）

| 场景关键词 | 窗口 |
|------------|------|
| 还能买吗 / 目标价 / 最新观点 | 当前 − 3 个月 |
| 大跌 / 异动 / 点评 / 为何 | 当前 − 1 个月 |
| 年报 / 业绩 / 占比 / Top | 当前 − 1 年 |
| 壁垒 / 复盘 / 技术路线 | 当前 − 3 年 |
| 今天 / 本周 / 本月 | 锚定到具体 `YYYY-MM-DD` |

### 调用示例

```json
{
  "query": "Cloudflare NET edge AI leadership CDN AppSec Zero Trust outlook",
  "filterImage": true,
  "start_time": "2026-05-10",
  "topK": 15
}
```

---

## 3. 组合策略

| 目标 | 建议链路 |
|------|----------|
| 某公司近期专篇 | `research_query` stockCode 完整分页 + 公司名补漏 → 研报表 + 时间变化 + 不同视角 |
| 主题摸底再落到个股 | `searchForeignReports` → 抽出 ticker → `research_query` |
| 单日全市场扫描 | 仅 `research_query` 单日翻页（勿用语义冒充全量） |
| 地区主题 | `research_query` region ± keywords；语义补观点 |

---

## 4. 实测备忘

- `keywords=Cloudflare` 与 `stockCode=NET, market=us` 均可返回专篇（如近窗约 30+ 条量级，视库内数据而定）
- `searchForeignReports` 对 Cloudflare 可返回含评级/论点的 FOREIGN_REPORT 切片
- 公司研报模式未指定时间时显式查询近 3 个月，不依赖接口默认近 30 天；完整规范见 [company-query.md](company-query.md)
- 日报默认保存到当前工作空间根目录；指定路径不可写时需检测并重新询问，不要写到技能目录
