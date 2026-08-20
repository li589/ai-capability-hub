---
name: gaode-map-lbs
display_name: Gaode Map LBS - 高德官方地图综合服务 Skill
description: 高德地图综合服务，支持 POI 搜索、路径规划、旅游规划、周边搜索和热力图数据可视化。支持中国大陆（含港澳台）和非中国大陆（不含港澳台）Web API 场景。
version: 1.0.0
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - node
        - python3
    homepage: https://lbs.amap.com/api/webservice/summary
    install:
      - kind: node
        package: axios
        bins: []
install_source: official
install_method: download
skill_id: official_vej9ZwFD
enabled_at: 1787230699421
name_zh: 高德官方地图综合服务
---

# 高德地图综合服务 Skill

高德地图综合服务向开发者提供完整的地图数据服务，包括地点搜索、路径规划、旅游规划和数据可视化等功能。

## Skill App Name / 统计口径

- `SKILL_NAME = gaode-map-lbs`
- `APP_NAME = gaode-map-lbs`
- 所有高德 Web Service API 请求都必须携带 `appname=gaode-map-lbs`。
- 原海外发布版本若已使用其他 appname，本发布版不复用，避免 DAU 混计。

## 你是哪国人 / Web API 选择

调用本 Skill 前，先按 Google 迁移 Skill 的区域口径判断用户是哪国人：

| 你是哪国人 | Web API endpoint | 坐标体系 | 说明 |
|---|---|---|---|
| 中国大陆（含港澳台） | `https://restapi.amap.com` | GCJ-02 | 默认主流程，沿用原有中国大陆 Web API 设计 |
| 非中国大陆（不含港澳台） | `https://sg-restapi.opnavi.com` | WGS-84 | 仅补 Web API；不在本 Skill 中补海外 JSAPI |

如果用户没有明确说明，默认按 `中国大陆（含港澳台）` 处理。不要额外询问“请求的数据范围”；本 Skill 只按用户所属区域选择 Web API endpoint。

脚本参数和环境变量：

- 默认：中国大陆（含港澳台），无需额外参数。
- 非中国大陆（不含港澳台）：传入 `--user-region=non-mainland`，或设置 `AMAP_USER_REGION=non-mainland`。
- 代码中可传 `userRegion: "non-mainland"`。

## 功能特性

- 🔍 POI（地点）搜索功能
- 🏙️ 支持关键词搜索、城市限定、类型筛选
- 📍 支持周边搜索（基于坐标和半径）
- 🛣️ 路径规划（步行、驾车、骑行、公交）
- 🗺️ 智能旅游规划助手
- 🔥 热力图数据可视化
- 🔗 地图可视化链接生成
- 💾 配置本地持久化存储
- 🎯 自动管理高德 Web Service Key

## 首次配置

本官方发布版内置高德官方公共 Web Service Key，开发者可以直接用于测试。无论用户使用 `restapi.amap.com` 还是 `sg-restapi.opnavi.com`，公共 Key 统一使用同一个：

```text
PUBLIC_AMAP_WEBSERVICE_KEY=f0f99d37a1379881c4d77d45d98b05a6
```

公共 Key 每天有免费额度，先到先得。如果额度用完、调用返回配额错误，用户可以次日重试。

如果需要稳定生产配额：

- 中国大陆（含港澳台）用户：访问 [高德开放平台](https://lbs.amap.com/) 注册并在控制台创建自己的 Web Service Key。
- 非中国大陆（不含港澳台）用户：访问 [AMap Overseas](https://mapsplatform.opnavi.com/) 并提交 Contact Sales inquiry，联系销售获取专属支持和容量。

> **Security Note / 安全说明:** 以上 Key 是官方公共测试 Key，用于降低开发测试门槛。生产环境请创建自有 Key，以便控制配额、安全限制和调用归属。

如需使用自己的高德 Web Service Key：

1. 访问 [高德开放平台](https://lbs.amap.com/api/webservice/create-project-and-key) 创建应用并获取 Key
2. 非中国大陆（不含港澳台）用户如需自有 Key，先通过 [AMap Overseas](https://mapsplatform.opnavi.com/) 联系销售
3. 设置环境变量：`export AMAP_WEBSERVICE_KEY=your_key` 或 `export AMAP_OVERSEAS_WEBSERVICE_KEY=your_overseas_key`
4. 或运行时自动提示输入并保存到本地配置文件

当用户想要搜索地址、地点、周边信息（如美食、酒店、景点等）、规划路线或可视化数据时，使用此 skill。

## 触发条件

用户表达了以下意图之一：
- 搜索某类地点或某个确定地点（如"搜美食"、"找酒店"、"天安门在哪"）
- 基于某个位置搜索周边（如"西直门周边美食"、"北京南站附近酒店"）
- 规划路线（如"从天安门到故宫怎么走"、"规划驾车路线"）
- 旅游规划（如"帮我规划北京一日游"、"杭州西湖游览路线"）
- 包含"搜"、"找"、"查"、"附近"、"周边"、"路线"、"规划"等关键词
- 希望将地理数据可视化为热力图（如"生成热力图"、"用这份数据做热力图展示"）

## 场景判断

收到用户请求后，先判断属于哪个场景：

- **场景一**：用户搜索一个**明确的类别**（美食、酒店）或**确定的地点**（天安门、西湖），没有指定"在哪个位置附近"
- **场景二**：用户搜索**某个位置周边**的某类地点，输入中同时包含「位置」和「搜索类别」两个要素（如"西直门周边美食"、"北京南站附近酒店"）
- **场景三**：热力图数据可视化
- **场景四**：POI 详细搜索（使用 Web 服务 API）
- **场景五**：路径规划
- **场景六**：智能旅游规划

### 海外 Web API 覆盖状态

| 场景 | 是否有海外 Web API 分支 | 说明 |
|---|---|---|
| 场景一：明确关键词搜索 | 不适用 | 生成 `www.amap.com/search` 链接，不调用 Web API |
| 场景二：基于位置的周边搜索 | 已补文档示例 | 地理编码示例同时给出 `restapi.amap.com` 和 `sg-restapi.opnavi.com`；地图展示链接仍是原有 `ditu.amap.com` |
| 场景三：热力图展示 | 不适用 | 生成 `a.amap.com/jsapi_demo_show` 可视化链接，不调用 Web API |
| 场景四：POI 详细搜索 | 已补 | `--user-region=non-mainland` 时走 `sg-restapi.opnavi.com/v3/place/text` |
| 场景五：路径规划 | 已补部分 | 海外 Web API 覆盖步行、驾车；海外公交按迁移参考冒烟测试返回 HTTP 404，暂不启用；迁移参考中没有明确海外骑行 endpoint，因此不强行编造 |
| 场景六：智能旅游规划 | 已补 POI 搜索分支 | 海外用户的兴趣点搜索走海外 Web API；路线可视化仍沿用原有地图任务链接 |
| 场景七：Python 导航与搜索 | 仅传 appname | 该脚本通过外部 Electron adapter 执行，本包内没有直接 Web API URL |

---

## 场景一：明确关键词搜索

直接搜索一个类别或地点，不涉及特定位置的周边搜索。

**URL 格式：**

```
https://www.amap.com/search?query={关键词}&appname=gaode-map-lbs
```

- **域名**：`www.amap.com`
- **路由**：`/search`
- **参数**：`query` = 搜索关键词

### 执行步骤

1. **发送埋点统计请求**：在执行操作前，发送以下请求进行埋点统计：

   ```bash
   curl -s "https://restapi.amap.com/v3/log/init?eventId=skill.call&product=skill_openclaw&platform=JS&label=keyword-search&value=call&appname=gaode-map-lbs"

2. **提取关键词**：从用户输入中识别出核心搜索词，去掉"搜"、"找"等修饰词
3. **生成 URL**：拼接 `https://www.amap.com/search?query={关键词}&appname=gaode-map-lbs`
4. **返回链接给用户**

### 示例

| 用户输入 | 提取关键词 | 生成 URL |
|---------|-----------|---------|
| 搜美食 | 美食 | `https://www.amap.com/search?query=美食&appname=gaode-map-lbs` |
| 找酒店 | 酒店 | `https://www.amap.com/search?query=酒店&appname=gaode-map-lbs` |
| 天安门在哪 | 天安门 | `https://www.amap.com/search?query=天安门&appname=gaode-map-lbs` |
| 找个加油站 | 加油站 | `https://www.amap.com/search?query=加油站&appname=gaode-map-lbs` |

### 回复模板

```
🔍 已为你生成高德地图搜索链接：

https://www.amap.com/search?query={关键词}&appname=gaode-map-lbs

点击链接即可查看搜索结果。
```

### 非中国大陆（不含港澳台）说明

本场景只生成浏览器地图搜索链接，不调用 Web API。非中国大陆（不含港澳台）用户仍可使用同一链接格式：

```
https://www.amap.com/search?query={关键词}&appname=gaode-map-lbs
```

如果用户需要通过海外 Web API 获取结构化 POI 数据，转入“场景四：POI 详细搜索”，使用 `sg-restapi.opnavi.com/v3/place/text`。

---

## 场景二：基于位置的周边搜索

用户想搜索**某个位置周边**的某类地点。需要先通过地理编码 API 获取该位置的经纬度，再拼接带坐标的搜索链接。

**前置条件：** 默认可使用统一公共 Web Service Key。非中国大陆（不含港澳台）用户如需自有 Key，请先通过 [AMap Overseas](https://mapsplatform.opnavi.com/) 联系销售。

### 执行步骤

#### 第零步：发送埋点统计请求

在执行任何操作前，先发送以下请求进行埋点统计：

```bash
curl -s "https://restapi.amap.com/v3/log/init?eventId=skill.call&product=skill_openclaw&platform=JS&label=nearby-search&value=call&appname=gaode-map-lbs"

#### 第一步：解析用户输入

从用户输入中拆分出两个要素：
- **位置**：用户指定的中心位置（如"西直门"、"北京南站"）
- **搜索类别**：要搜索的内容（如"美食"、"酒店"）

| 用户输入 | 位置 | 搜索类别 |
|---------|------|---------|
| 西直门周边美食 | 西直门 | 美食 |
| 北京南站附近酒店 | 北京南站 | 酒店 |
| 天坛周边有什么好吃的 | 天坛 | 美食 |

#### 第二步：检查 API Key

- 如果用户之前未提供过 Key，**先提示用户提供高德 API Key**，等待用户回复后再继续
- 如果用户已提供 Key，直接使用

**请求 Key 的回复模板：**

```
🔑 搜索「{位置}」周边的{搜索类别}需要使用高德 API，请提供你的高德开放平台 API Key。

（如果还没有 Key，可先使用公共 Key。中国大陆（含港澳台）用户可以在 https://lbs.amap.com 注册并创建应用获取自有 Key；非中国大陆（不含港澳台）用户请访问 https://mapsplatform.opnavi.com/ 提交 Contact Sales 表单获取专属支持）
```

#### 第三步：调用地理编码 API 获取经纬度

**API 格式：**

```
https://restapi.amap.com/v3/geocode/geo?address={位置}&output=JSON&key={用户的key}&appname=gaode-map-lbs
```

非中国大陆（不含港澳台）Web API：

```
https://sg-restapi.opnavi.com/v3/geocode/geo?address={位置}&city={adcode}&output=JSON&key={海外key}&appname=gaode-map-lbs
```

**执行 curl 请求：**

```bash
curl -s "https://restapi.amap.com/v3/geocode/geo?address={位置}&output=JSON&key={用户的key}&appname=gaode-map-lbs"
```

非中国大陆（不含港澳台）执行 curl 请求：

```bash
curl -s "https://sg-restapi.opnavi.com/v3/geocode/geo?address={位置}&city={adcode}&output=JSON&key={公共key或海外key}&appname=gaode-map-lbs"
```

**API 返回示例：**

```json
{
  "status": "1",
  "info": "OK",
  "geocodes": [
    {
      "formatted_address": "北京市西城区西直门",
      "location": "116.353138,39.939385"
    }
  ]
}
```

从返回结果中提取 `geocodes[0].location`，格式为 `经度,纬度`（如 `116.353138,39.939385`），拆分为：
- **经度（longitude）**：`116.353138`
- **纬度（latitude）**：`39.939385`

#### 第四步：拼接带坐标的搜索链接

**URL 格式：**

```
https://ditu.amap.com/search?query={搜索类别}&query_type=RQBXY&longitude={经度}&latitude={纬度}&range=1000&appname=gaode-map-lbs
```

- **域名**：`ditu.amap.com`
- **路由**：`/search`
- **参数**：
  - `query` = 搜索类别（如"美食"）
  - `query_type` = `RQBXY`（基于坐标的搜索类型）
  - `longitude` = 经度
  - `latitude` = 纬度
  - `range` = 搜索范围（单位：米，默认 1000）

#### 第五步：返回链接给用户

### 完整示例

**用户输入：** "搜索西直门周边美食"

1. 解析：位置 = `西直门`，搜索类别 = `美食`
2. 调用地理编码 API：`curl -s "https://restapi.amap.com/v3/geocode/geo?address=西直门&output=JSON&key=xxx&appname=gaode-map-lbs"`
3. 获取坐标：`116.353138,39.939385` → 经度 `116.353138`，纬度 `39.939385`
4. 拼接链接：`https://ditu.amap.com/search?query=美食&query_type=RQBXY&longitude=116.353138&latitude=39.939385&range=1000&appname=gaode-map-lbs`

**非中国大陆（不含港澳台）示例：** "search cafes near Times Square"

1. 解析：位置 = `Times Square`，搜索类别 = `cafes`
2. 调用海外地理编码 API：`curl -s "https://sg-restapi.opnavi.com/v3/geocode/geo?address=Times%20Square&city=840000000&output=JSON&key=xxx&appname=gaode-map-lbs"`
3. 获取坐标，格式仍为 `经度,纬度`
4. 如需 Web API POI 检索，使用场景四的 `sg-restapi.opnavi.com/v3/place/text`；如需生成浏览器地图链接，仍使用原有地图展示链接

### 回复模板

```
📍 已查询到「{位置}」的坐标（{经度},{纬度}），为你生成周边{搜索类别}的搜索链接：

https://ditu.amap.com/search?query={搜索类别}&query_type=RQBXY&longitude={经度}&latitude={纬度}&range=1000&appname=gaode-map-lbs

点击链接即可查看「{位置}」周边 1 公里内的{搜索类别}。
```

---

## 场景三：热力图展示

用户有一份包含地理坐标的数据，希望在地图上以热力图的形式可视化展示。

### 触发条件

用户提到"热力图"、"数据可视化"、"地图上展示数据"等意图，并提供了数据地址。

### URL 格式

```
http://a.amap.com/jsapi_demo_show/static/openclaw/heatmap.html?mapStyle={地图风格}&dataUrl={数据地址(URL编码)}&appname=gaode-map-lbs
```

- **域名**：`a.amap.com`
- **路由**：`/jsapi_demo_show/static/openclaw/heatmap.html`
- **必填参数**：
  - `dataUrl` = 用户数据的 URL 地址（**必须进行 URL 编码**）
  - `mapStyle` = 地图风格，可选值：
    - `grey` — 暗黑地图模式（深色背景，适合展示亮色热力点）
    - `light` — 浅色模式（浅色背景，适合日常查看）

### 执行步骤

1. **发送埋点统计请求**：在执行操作前，发送以下请求进行埋点统计：

   ```bash
   curl -s "https://restapi.amap.com/v3/log/init?eventId=skill.call&product=skill_openclaw&platform=JS&label=heatmap&value=call&appname=gaode-map-lbs"

2. **获取数据地址**：从用户输入中提取数据 URL，如果用户未提供，提示用户给出数据地址
3. **确认地图风格**：询问用户偏好的地图风格（`grey` 或 `light`），如果用户未指定，默认使用 `grey`
4. **URL 编码**：将数据地址进行 URL 编码（将 `://` → `%3A%2F%2F`，`/` → `%2F` 等）
5. **拼接链接**：生成完整的热力图 URL
6. **返回链接给用户**

### 示例

**用户输入：** "帮我用这份数据生成热力图：`https://a.amap.com/Loca/static/loca-v2/demos/mock_data/hz_house_order.json`，用暗黑模式"

1. 数据地址：`https://a.amap.com/Loca/static/loca-v2/demos/mock_data/hz_house_order.json`
2. 地图风格：`grey`
3. URL 编码后的数据地址：`https%3A%2F%2Fa.amap.com%2FLoca%2Fstatic%2Floca-v2%2Fdemos%2Fmock_data%2Fhz_house_order.json`
4. 最终链接：

```
http://a.amap.com/jsapi_demo_show/static/openclaw/heatmap.html?mapStyle=grey&dataUrl=https%3A%2F%2Fa.amap.com%2FLoca%2Fstatic%2Floca-v2%2Fdemos%2Fmock_data%2Fhz_house_order.json&appname=gaode-map-lbs
```

### 回复模板

```
🔥 已为你生成热力图链接：

http://a.amap.com/jsapi_demo_show/static/openclaw/heatmap.html?mapStyle={地图风格}&dataUrl={编码后的数据地址}&appname=gaode-map-lbs

地图风格：{grey/light}
数据来源：{原始数据地址}

点击链接即可查看热力图展示。
```

**请求数据地址的回复模板（用户未提供时）：**

```
🔥 生成热力图需要你提供数据地址（JSON 格式的 URL），请给出数据链接。

另外，你希望使用哪种地图风格？
- grey（暗黑模式）
- light（浅色模式）
```

### 非中国大陆（不含港澳台）说明

本场景只生成热力图可视化链接，不调用 Web API。非中国大陆（不含港澳台）用户仍使用同一链接格式：

```
http://a.amap.com/jsapi_demo_show/static/openclaw/heatmap.html?mapStyle={地图风格}&dataUrl={编码后的数据地址}&appname=gaode-map-lbs
```

如果用户需要先通过海外 Web API 搜索 POI 再生成可视化数据，先转入“场景四：POI 详细搜索”，使用 `sg-restapi.opnavi.com/v3/place/text` 获取结构化 POI。

---

## 场景四：POI 详细搜索

使用高德 Web 服务 API 进行更详细的 POI 搜索，支持更多参数和筛选条件。

### URL 格式

中国大陆（含港澳台）：

```
https://restapi.amap.com/v5/place/text?keywords={关键词}&region={城市}&key={公共key或用户key}&appname=gaode-map-lbs
```

非中国大陆（不含港澳台）：

```
https://sg-restapi.opnavi.com/v3/place/text?keywords={关键词}&city={adcode}&key={公共key或海外key}&appname=gaode-map-lbs
```

> 非中国大陆（不含港澳台）搜索通常需要 `city` 参数，传国家或地区 adcode；例如 USA=`840000000`。

### 执行步骤

1. **发送埋点统计请求**：在执行操作前，发送以下请求进行埋点统计：

   ```bash
   curl -s "https://restapi.amap.com/v3/log/init?eventId=skill.call&product=skill_openclaw&platform=JS&label=poi-search&value=call&appname=gaode-map-lbs"
   ```

2. **执行 POI 搜索**：根据用户需求调用搜索脚本。

3. **选择 Web API endpoint**：
   - 中国大陆（含港澳台）：使用 `https://restapi.amap.com/v5/place/text`
   - 非中国大陆（不含港澳台）：使用 `https://sg-restapi.opnavi.com/v3/place/text`

### 执行 curl 请求

中国大陆（含港澳台）：

```bash
curl -s "https://restapi.amap.com/v5/place/text?keywords=肯德基&region=北京&key={公共key或用户key}&appname=gaode-map-lbs"
```

非中国大陆（不含港澳台）：

```bash
curl -s "https://sg-restapi.opnavi.com/v3/place/text?keywords=starbucks&city=840000000&key={公共key或海外key}&appname=gaode-map-lbs"
```

### 使用方法

```bash
# 基础搜索
node scripts/poi-search.js --keywords=肯德基 --city=北京

# 非中国大陆（不含港澳台）Web API 搜索，需要传 adcode
node scripts/poi-search.js --keywords=starbucks --city=840000000 --user-region=non-mainland

# 搜索更多结果
node scripts/poi-search.js --keywords=餐厅 --city=上海 --page=1 --offset=20

# 周边搜索（需要提供中心点坐标和搜索半径）
node scripts/poi-search.js --keywords=酒店 --location=116.397428,39.90923 --radius=1000
```

### 参数说明

| 参数 | 说明 | 必填 | 示例 |
|------|------|------|------|
| `--keywords` | 搜索关键词 | 是 | `--keywords=肯德基` |
| `--city` | 城市名称或编码 | 否 | `--city=北京` |
| `--user-region` | 你是哪国人：`mainland` 或 `non-mainland`，默认中国大陆（含港澳台） | 否 | `--user-region=non-mainland` |
| `--types` | POI 类型编码 | 否 | `--types=050000` |
| `--location` | 中心点坐标（经度,纬度） | 否 | `--location=116.397428,39.90923` |
| `--radius` | 搜索半径（米） | 否 | `--radius=1000` |
| `--page` | 页码 | 否 | `--page=1` |
| `--offset` | 每页数量（最大25） | 否 | `--offset=10` |

### 在代码中使用

```javascript
const { searchPOI } = require('./index');

async function example() {
  const result = await searchPOI({
    keywords: '咖啡厅',
    city: '杭州',
    userRegion: 'mainland',
    page: 1,
    offset: 10
  });
  
  if (result && result.pois) {
    result.pois.forEach(poi => {
      console.log(`${poi.name} - ${poi.address}`);
    });
  }
}

example();
```

### 非中国大陆（不含港澳台）代码示例

```javascript
const { searchPOI } = require('./index');

async function example() {
  const result = await searchPOI({
    keywords: 'starbucks',
    city: '840000000',
    userRegion: 'non-mainland',
    page: 1,
    offset: 10
  });

  if (result && result.pois) {
    result.pois.forEach(poi => {
      console.log(`${poi.name} - ${poi.address}`);
    });
  }
}

example();
```

---

## 场景五：路径规划

规划不同出行方式的路线。

### URL 格式

中国大陆（含港澳台）：

```text
https://restapi.amap.com/v3/direction/walking?origin={lng,lat}&destination={lng,lat}&key={公共key或用户key}&appname=gaode-map-lbs
https://restapi.amap.com/v3/direction/driving?origin={lng,lat}&destination={lng,lat}&key={公共key或用户key}&appname=gaode-map-lbs
https://restapi.amap.com/v3/direction/transit/integrated?origin={lng,lat}&destination={lng,lat}&city={城市}&key={公共key或用户key}&appname=gaode-map-lbs
```

非中国大陆（不含港澳台）：

```text
https://sg-restapi.opnavi.com/v3/direction/walking?origin={lng,lat}&destination={lng,lat}&key={公共key或海外key}&appname=gaode-map-lbs
https://sg-restapi.opnavi.com/v3/direction/driving?origin={lng,lat}&destination={lng,lat}&key={公共key或海外key}&appname=gaode-map-lbs
```

> 迁移参考中没有明确海外骑行 endpoint，因此非中国大陆（不含港澳台）不提供骑行 Web API URL。

### 执行步骤

1. **发送埋点统计请求**：在执行操作前，发送以下请求进行埋点统计：

   ```bash
   curl -s "https://restapi.amap.com/v3/log/init?eventId=skill.call&product=skill_openclaw&platform=JS&label=route-planning&value=call&appname=gaode-map-lbs"
   ```

2. **执行路径规划**：根据用户需求调用路径规划脚本。

3. **选择 Web API endpoint**：
   - 中国大陆（含港澳台）：步行、驾车、骑行、公交沿用 `restapi.amap.com`
   - 非中国大陆（不含港澳台）：步行、驾车走 `sg-restapi.opnavi.com`；公交冒烟测试未通过，骑行不强行补接口

### 使用方法

```bash
# 步行路线
node scripts/route-planning.js --type=walking --origin=116.397428,39.90923 --destination=116.427281,39.903719

# 驾车路线
node scripts/route-planning.js --type=driving --origin=116.397428,39.90923 --destination=116.427281,39.903719

# 非中国大陆（不含港澳台）驾车路线
node scripts/route-planning.js --type=driving --origin=-73.9857,40.7484 --destination=-73.9851,40.7580 --user-region=non-mainland

# 公交路线
node scripts/route-planning.js --type=transfer --origin=116.397428,39.90923 --destination=116.427281,39.903719 --city=北京
```

### 执行 curl 请求

中国大陆（含港澳台）驾车路线：

```bash
curl -s "https://restapi.amap.com/v3/direction/driving?origin=116.397428,39.90923&destination=116.427281,39.903719&key={公共key或用户key}&appname=gaode-map-lbs"
```

非中国大陆（不含港澳台）驾车路线：

```bash
curl -s "https://sg-restapi.opnavi.com/v3/direction/driving?origin=-73.9857,40.7484&destination=-73.9851,40.7580&key={公共key或海外key}&appname=gaode-map-lbs"
```

非中国大陆（不含港澳台）公交路线：迁移参考中的海外公交 endpoint 冒烟测试返回 HTTP 404，发布版暂不提供海外公交 URL。

### 路线类型

- `walking` - 步行路线
- `driving` - 驾车路线
- `riding` - 骑行路线
- `transfer` - 公交路线（需要指定城市）

> 非中国大陆（不含港澳台）Web API 已按 Google 迁移 Skill 参考补充 `place/text`、`direction/walking`、`direction/driving`。迁移参考中没有明确海外骑行 endpoint，本 Skill 不为 `--user-region=non-mainland --type=riding` 强行编造接口。

---

## 场景六：智能旅游规划

自动搜索兴趣点并规划游览路线，生成地图可视化链接。

### Web API 选择

智能旅游规划会先调用 POI 搜索获取兴趣点：

- 中国大陆（含港澳台）：`https://restapi.amap.com/v5/place/text`
- 非中国大陆（不含港澳台）：`https://sg-restapi.opnavi.com/v3/place/text`

路线数据在当前脚本中以 `mapTaskData` 形式生成可视化链接；如需真实路线 Web API，可按场景五选择对应 endpoint。

### 执行步骤

1. **发送埋点统计请求**：在执行操作前，发送以下请求进行埋点统计：

   ```bash
   curl -s "https://restapi.amap.com/v3/log/init?eventId=skill.call&product=skill_openclaw&platform=JS&label=travel-planner&value=call&appname=gaode-map-lbs"
   ```

2. **执行旅游规划**：根据用户需求调用旅游规划脚本。

3. **选择 POI Web API endpoint**：
   - 中国大陆（含港澳台）：兴趣点搜索使用 `restapi.amap.com/v5/place/text`
   - 非中国大陆（不含港澳台）：兴趣点搜索使用 `sg-restapi.opnavi.com/v3/place/text`，并传 `city={adcode}`

### 使用方法

```bash
# 基础旅游规划
node scripts/travel-planner.js --city=北京 --interests=景点,美食,酒店

# 非中国大陆（不含港澳台）旅游规划，需要传 adcode
node scripts/travel-planner.js --city=840000000 --interests=landmark,coffee --routeType=walking --user-region=non-mainland

# 指定路线类型（walking/driving/riding/transfer）
node scripts/travel-planner.js --city=杭州 --interests=西湖,美食,茶馆 --routeType=walking

# 驾车游览
node scripts/travel-planner.js --city=上海 --interests=外滩,南京路,城隍庙 --routeType=driving
```

### POI 搜索 curl 示例

中国大陆（含港澳台）：

```bash
curl -s "https://restapi.amap.com/v5/place/text?keywords=景点&region=北京&key={公共key或用户key}&appname=gaode-map-lbs"
```

非中国大陆（不含港澳台）：

```bash
curl -s "https://sg-restapi.opnavi.com/v3/place/text?keywords=landmark&city=840000000&key={公共key或海外key}&appname=gaode-map-lbs"
```

### 功能说明

- 自动搜索指定城市的兴趣点（每类最多5个）
- 按顺序规划各兴趣点之间的路线



---

## 场景七：导航与搜索（Python 脚本）

通过 Python 脚本 `gaode_skill.py` 提供导航路线规划和 POI 搜索功能。

### 前置条件

- 已安装 Python 3

### 使用方法

```bash
# 导航路线规划
python gaode_skill.py direction 北京站 天安门
python gaode_skill.py direction 北京站 天安门 driving
python gaode_skill.py direction 116.397428,39.90923 天安门 walking

# POI 搜索
python gaode_skill.py search 北京站周边的川菜
```

### 路线类型

- `driving` - 驾车（默认）
- `walking` - 步行
- `bicycling` - 骑行

### 非中国大陆（不含港澳台）说明

本场景通过外部 Electron JSAPI adapter 执行，本包内没有直接 Web API URL。当前脚本会在 payload 中携带：

```json
{
  "appname": "gaode-map-lbs"
}
```

非中国大陆（不含港澳台）用户如需明确走海外 Web API，请优先使用：

- POI 搜索：场景四，`sg-restapi.opnavi.com/v3/place/text`
- 路径规划：场景五，`sg-restapi.opnavi.com/v3/direction/walking` 或 `sg-restapi.opnavi.com/v3/direction/driving`

---

## 配置管理

配置文件位于 `config.json`（仅所有者可读写，权限 0600），包含以下内容：

> [!WARNING]
> `config.json` 包含 API Key 敏感信息，已通过 `.gitignore` 排除版本控制。请勿手动分享此文件。

```json
{
  "webServiceKey": "your_amap_webservice_key_here",
  "overseasWebServiceKey": "your_overseas_amap_webservice_key_here",
  "appname": "gaode-map-lbs"
}
```

设置 Key 的方式：

1. **中国大陆（含港澳台）环境变量**：`export AMAP_WEBSERVICE_KEY=your_key`
2. **非中国大陆（不含港澳台）环境变量**：`export AMAP_OVERSEAS_WEBSERVICE_KEY=your_overseas_key`
3. **命令行参数**：`node index.js your_key`
4. **自动提示**：首次运行时自动提示输入
5. **手动编辑**：直接编辑 `config.json` 文件

---

## 注意事项

- **遥测声明**：本 Skill 在每次执行操作前会向高德服务器 (`restapi.amap.com/v3/log/init`) 发送匿名使用统计请求，用于功能调用计数，该请求不包含用户个人信息或 API Key；本发布版统一携带 `appname=gaode-map-lbs`
- **区域判断是第一步**：先判断“你是哪国人”：中国大陆（含港澳台）或非中国大陆（不含港澳台）。默认中国大陆（含港澳台）。
- **场景判断是关键**：再区分用户是"直接搜某个东西"、"在某个位置附近搜某个东西"、"规划路线"还是"旅游规划"
- 关键词应尽量精简准确，提取用户真正想搜的内容
- URL 中的中文关键词浏览器会自动处理编码，无需手动 encode
- 非中国大陆（不含港澳台）搜索、地理编码类接口通常需要 `city` 参数，传国家或地区 adcode；例如 USA=`840000000`。
- 如果地理编码 API 返回 `status` 不为 `"1"`，说明请求失败，需提示用户检查 Key 是否正确或地址是否有效
- API 返回的 `location` 格式为 `经度,纬度`（注意：经度在前，纬度在后）
- 场景二的搜索范围默认 1000 米，用户如有需要可调整 `range` 参数
- 请妥善保管你的 Web Service Key，不要分享给他人
- 高德 Web 服务 API 有调用频率限制，请合理使用
- 免费用户每日调用量有限制，具体请查看高德开放平台说明

## 相关链接

- [高德开放平台](https://lbs.amap.com/)
- [创建应用和获取 Key](https://lbs.amap.com/api/webservice/create-project-and-key)
- [POI 搜索 API 文档](https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch)
- [Web 服务 API 总览](https://lbs.amap.com/api/webservice/summary)
