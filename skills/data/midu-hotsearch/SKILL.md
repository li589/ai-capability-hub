---
name: midu-hotsearch
version: 2.0.0
description: 调用蜜度热搜数据查询接口，支持按关键词、时间范围、榜单类型检索各平台热搜数据。当用户需要查询热搜、热点话题、舆论热度、榜单排行等场景时使用此 Skill。
license: MIT
metadata:
  openclaw:
    emoji: ""
    requires:
      bins:
        - python3
      env:
        - MIDU_APP_SECRET
    primaryEnv: MIDU_APP_SECRET
display_name: 蜜度热搜榜
display_name_en: Midu Hot Search
description_zh: 30+ 主流平台热搜数据查询，支持关键词、时间范围、榜单类型筛选，覆盖微博、抖音、百度、知乎、今日头条等。
description_en: Hot search data across 30+ platforms including Weibo, Douyin,
  Baidu, Zhihu, Toutiao, with flexible filtering.
visibility: public
disable-model-invocation: true
---

# 热搜数据检索 Skill

## 1. 技能概述

本 Skill 封装蜜度热搜数据查询 API，提供各平台热搜数据的检索能力。支持按关键词、时间范围和榜单类型进行灵活查询，覆盖微博、抖音、百度、知乎、今日头条、小红书、快手、网易、搜狐、腾讯新闻等 **30+ 主流平台**的热搜榜单。

**适用场景：**

- 用户需要查询某个关键词在各平台的热搜情况
- 用户需要了解某话题在不同时间段的舆论热度变化
- 用户需要按平台/榜单类型筛选热搜数据
- 舆情监测、热点追踪、话题分析等场景

**核心能力：**

- 支持关键词精确匹配搜索
- 支持日期范围查询（最长 60 天，最早回溯 24 个月）
- 支持 30+ 榜单类型按需筛选
- 返回话题名称、排名、链接、讨论量、搜索量等结构化数据

## 2. 脚本定义

- **主调用脚本**：`scripts/hot_search.py`，用于向热搜 API 发起 POST 请求并处理响应。
- **API 请求头参数**：

| 参数名 | 类型 | 必填 | 描述 |
|:-------|:-----|:-----|:-----|
| `Authorization` | String | 是 | 授权密钥，格式 `Bearer {apiKey}`，`apiKey` 由 `MIDU_APP_SECRET` 环境变量提供 |
| `X-Skill-Code` | String | 是 | 技能编码，固定值 `HOTSEARCH`，用于接口统计 |
| `X-User-Id` | String | 否* | 用户标识（官网 ID），**优先级高于**请求体 `gwUserId` |

> \* 请求头 `X-User-Id` 与请求体 `gwUserId` 至少提供一个有效用户标识，否则返回「用户标识为空」。

- **API 请求体参数**（脚本内部会自动将下述字段构建为 JSON Body 发送给接口）：

| 参数名 | 类型 | 必填 | 描述 |
|:-------|:-----|:-----|:-----|
| `gwUserId` | String | 否* | 用户标识备用字段；`X-User-Id` 请求头为空时使用 |
| `keyword` | String | 是 | 搜索关键词，最大 30 个字符 |
| `startTime` | String | 否 | 开始时间，格式 `yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm:ss` |
| `endTime` | String | 否 | 结束时间，格式 `yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm:ss` |
| `rankTypes` | Integer[] | 否 | 榜单类型编码列表；不传或空数组则查询全部榜单 |

- **脚本命令行参数**（通过 `--` 传入，脚本内部映射为对应的 API 字段）：

| 脚本参数 | 映射到 API 字段 | 类型 | 必填 | 描述 |
|:---------|:---------------|:-----|:-----|:-----|
| `--keyword` | 请求体 `keyword` | String | 是 | 搜索关键词 |
| `--user_id` | 请求头 `X-User-Id` + 请求体 `gwUserId` | String | 否 | 用户标识（官网 ID）；未传则从环境变量 `MIDU_USER_ID` 读取，仍未设置则使用默认值 `skill-hotsearch-agent` |
| `--start_time` | 请求体 `startTime` | String | 否 | 开始时间 |
| `--end_time` | 请求体 `endTime` | String | 否 | 结束时间 |
| `--rank_types` | 请求体 `rankTypes`（逗号分隔转 Integer 数组） | String | 否 | 榜单类型编码 |
| `--timeout` | - | Integer | 否 | 请求超时秒数，默认 `60` |
| `--pretty` | - | Boolean | 否 | 格式化输出 JSON |

- **使用示例**：

```bash
# 查询当天全部榜单的"人工智能"热搜
python3 scripts/hot_search.py --keyword "人工智能" --pretty

# 查询指定日期范围的微博和抖音热搜（rankTypes = [1, 3]）
python3 scripts/hot_search.py --keyword "人工智能" --start_time "2025-03-01" --end_time "2025-03-15" --rank_types "1,3" --pretty

# 查询指定时间段+完整时间（rankTypes = [3, 7, 8]）
python3 scripts/hot_search.py --keyword "人工智能" --start_time "2025-03-01 08:00:00" --end_time "2025-03-01 20:00:00" --rank_types "3,7,8" --pretty
```

## 3. 工作流程

### Smart Workflow

1. **首次查询**：用户描述查询需求后，提取关键词、时间范围、平台偏好，构建脚本命令调用 API。
2. **结果呈现**：解析返回的 JSON 数据，按平台/榜单分组展示热搜话题、排名变化、讨论量等关键信息。
3. **深入分析**：用户可根据首次结果追问，例如缩小时间范围、更换平台、对比不同话题等，通过调整参数重新查询。

### Scripts

- `scripts/hot_search.py` - 发起热搜查询请求，处理参数校验和结果格式化。

### Key Features

- **多平台覆盖**：一次查询可覆盖 30+ 平台热搜榜单，支持按需筛选。
- **灵活时间查询**：支持当天查询、日期范围查询、精确时间查询三种模式。
- **自动时间补全**：未传时间参数时自动补全为当天 00:00:00 ~ 23:59:59。

### 常用榜单编码速查

| 编码 | 平台 | 编码 | 平台 |
|:-----|:-----|:-----|:-----|
| 1 | 抖音热点榜 | 3 | 微博热搜榜 |
| 5 | 今日头条 | 7 | 百度热搜风云榜 |
| 8 | 知乎 | 28 | 小红书 |
| 29 | 网易热搜榜 | 34 | 快手 |
| 53 | 腾讯新闻热点榜 | 78 | 搜狐热榜 |

> 完整榜单编码对照表见 `references/rank_types.md`。

### Usage Examples

```bash
# 查询"人员聚集"在微博和抖音的热搜情况
python3 scripts/hot_search.py --keyword "人员聚集" --rank_types "1,3" --pretty

# 查询最近 7 天"路面坍塌"的全部平台热搜
python3 scripts/hot_search.py --keyword "路面坍塌" --start_time "2025-03-10" --end_time "2025-03-17" --pretty

# 查询今天小红书热搜
python3 scripts/hot_search.py --keyword "人工智能" --rank_types "28" --pretty

# 查询今天全部平台热搜
python3 scripts/hot_search.py --keyword "人工智能" --pretty
```

## 4. 输出规范

### Output Examples

**成功响应：**

```json
{
  "code": "0000",
  "itemCount": 2,
  "data": [
    {
      "id": "10001",
      "topicName": "人工智能",
      "listType": 3,
      "rankName": "微博热搜榜",
      "topNumLast": 5,
      "topNumFirst": 8,
      "onRankTimes": 3,
      "searchCount": 520000,
      "discussSeveral": 38000,
      "discussTotal": 1200000,
      "totalCount": 10000,
      "url": "https://example.com/topic/1",
      "statTime": 1716000000000,
      "statTimeFormatted": "2024-05-17 16:00:00",
      "inTime": 1716000000000,
      "inTimeFormatted": "2024-05-17 16:00:00",
      "topicTag": "科技",
      "topicRegion": "全国",
      "city": "北京"
    },
    {
      "id": "10002",
      "topicName": "人工智能应用",
      "listType": 8,
      "rankName": "知乎",
      "topNumLast": 12,
      "url": "https://example.com/topic/2"
    }
  ],
  "query_info": {
    "keyword": "人工智能",
    "startTime": "2026-06-08 00:00:00",
    "endTime": "2026-06-08 23:59:59",
    "rankTypes": "all"
  }
}
```

**无数据响应：**

```json
{
  "code": "0000",
  "itemCount": 0,
  "data": [],
  "query_info": {
    "keyword": "不存在的关键词",
    "startTime": "2026-06-08 00:00:00",
    "endTime": "2026-06-08 23:59:59",
    "rankTypes": "all"
  }
}
```

**错误响应：**

```json
{
  "code": "1001",
  "message": "用户标识为空"
}
```

**外层字段说明：**

| 字段 | 说明 |
|:-----|:-----|
| `code` | 业务状态码，`0000` 表示成功，非 `0000` 为错误 |
| `message` | 提示信息（错误时返回） |
| `itemCount` | 返回的列表条数（等于 `data.length`），同时作为按条数计费字段 |
| `data` | 热搜记录列表 |
| `query_info` | 本次查询的参数摘要（脚本生成） |

**data 元素字段说明（StatRankList）：**

| 字段 | 说明 |
|:-----|:-----|
| `id` | 记录 ID |
| `topicName` | 话题名称 |
| `rankName` | 榜单名称（中文），由 `listType` 映射 |
| `listType` | 榜单类型编码 |
| `topNumLast` | 最新排名 |
| `topNumFirst` | 首次上榜排名 |
| `topNumHistory` | 历史最高排名 |
| `onRankTimes` | 上榜次数 |
| `searchCount` | 搜索量 |
| `discussSeveral` | 讨论数 |
| `discussTotal` | 讨论总量 |
| `totalCount` | 单条热搜的业务总量（**非**列表条数） |
| `url` | 话题链接 |
| `statTime` | 统计时间（毫秒时间戳） |
| `statTimeFormatted` | 统计时间（可读格式，脚本生成） |
| `inTime` | 入库时间（毫秒时间戳） |
| `inTimeFormatted` | 入库时间（可读格式，脚本生成） |
| `fetchingTimeFirst` | 首次抓取时间（毫秒时间戳） |
| `fetchingTimeLast` | 末次抓取时间（毫秒时间戳） |
| `fetchingTimeHistory` | 历史抓取时间（毫秒时间戳） |
| `wordCut` | 分词 |
| `topicTag` | 话题标签 |
| `topicRegion` | 话题地域 |
| `city` | 城市 |
| `author` | 作者 |
| `presenter` | 主持人/发布者 |
| `introduction` | 简介 |
| `industryTag` | 行业标签 |

> **字段区分：** 外层 `itemCount` = 本次返回的列表条数（同时也是按条数计费字段）；`data[i].totalCount` = 单条热搜记录的业务总量。

## 5. 注意事项

- **错误处理**：请求失败时优先检查网络连接、MIDU_APP_SECRET 是否正确、参数格式是否符合要求。API 返回明确错误信息时不要进行无意义的重试。
- **时间范围限制**：单次查询跨度不能超过 60 天，最早回溯 24 个月。超出范围会返回校验错误。
- **关键词限制**：关键词最长 30 个字符，超长会被服务端拒绝。
- **空结果处理**：查询无数据时 `itemCount` 为 0，`data` 返回空数组，属正常情况，不代表接口异常。
- **计费说明**：本 Skill 按条数计费，输出中 `itemCount` 字段为本次返回的列表条数，用于计费统计。
- **授权说明**：脚本通过 `MIDU_APP_SECRET` 环境变量获取授权密钥，放置于请求头 `Authorization: Bearer {apiKey}` 中。业务层通过请求头 `X-User-Id`（优先）或请求体 `gwUserId` 进行用户身份校验。如未设置 `MIDU_APP_SECRET`，请前往 [蜜度官网](https://ai.mdata.net/) 注册获取。
