# API 调用示例

_同程程心 API 调用参考_

---

本技能**仅**通过 `scripts/` 下各 `*-query.js` 调用程心资源接口;须按 SKILL.md 将用户意图映射到对应脚本并传入结构化参数(及 `--channel` / `--surface`)。

## 📋 通用说明

### 基础调用格式

```bash
node scripts/<脚本名>.js [参数] --channel <渠道> --surface <界面>
```

### 通用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--channel <渠道>` | 通信渠道 | `webchat`、`wechat`、`app` |
| `--surface <界面>` | 交互界面 | `webchat`、`mobile`、`desktop`、`card` |

### 配置方式（优先级：环境变量 > config.json）

- **环境变量**: `CHENGXIN_API_KEY`
- **本地文件**: 创建 `config.json`（见 `config.example.json`）

---

## ✈️ 机票查询 (flight-query.js)

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 出发地 + 目的地 | `--departure "北京" --destination "上海"` | 按城市查询 |
| 航班号 | `--flight-number "CA1234"` | 精确查航班 |
| 出发地 + 特价 | `--departure "北京" --low-price` | 多地低价推荐 |
| 出发地 + 目的地 + 特价 | `--departure "上海" --destination "北京" --low-price` | 指定航线特价 |

### 调用示例

```bash
# 北京到上海，明天的机票
node scripts/flight-query.js \
  --departure "北京" \
  --destination "上海" \
  --extra "明天" \
  --channel webchat \
  --surface webchat

# 查询特定航班
node scripts/flight-query.js \
  --flight-number "CA1234" \
  --channel webchat \
  --surface webchat

# 上海到北京的特价机票
node scripts/flight-query.js \
  --departure "上海" \
  --destination "北京" \
  --low-price \
  --channel webchat \
  --surface webchat

# 从北京出发的特价推荐（未指定目的地）
node scripts/flight-query.js \
  --departure "北京" \
  --low-price \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "flightDataList": [
      {
        "desc": "北京 → 上海 2024-04-20",
        "flightList": [
          {
            "flightNo": "CA1234",
            "airlineName": "中国国航",
            "departureAirport": "首都国际机场T3",
            "arrivalAirport": "虹桥国际机场T2",
            "departureTime": "08:00",
            "arrivalTime": "10:20",
            "duration": "2小时20分",
            "price": 850,
            "discount": "5.2折",
            "cabinClass": "经济舱",
            "pcRedirectUrl": "https://...",
            "clawRedirectUrl": "https://..."
          }
        ],
        "pageDataList": [
          {
            "pcRedirectUrl": "https://..."
          }
        ]
      }
    ]
  }
}
```

---

## 🚂 火车票查询 (train-query.js)

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 出发地 + 目的地 | `--departure "北京" --destination "上海"` | 按城市查询 |
| 车次号 | `--train-number "G1234"` | 精确查车次 |
| 出发站 + 到达站 | `--departure-station "北京南站" --arrival-station "上海虹桥站"` | 精确站点查询 |

### 调用示例

```bash
# 北京到上海，明天的高铁
node scripts/train-query.js \
  --departure "北京" \
  --destination "上海" \
  --extra "明天 高铁" \
  --channel webchat \
  --surface webchat

# 查询特定车次
node scripts/train-query.js \
  --train-number "G1234" \
  --channel webchat \
  --surface webchat

# 站到站精确查询
node scripts/train-query.js \
  --departure-station "北京南站" \
  --arrival-station "上海虹桥站" \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "trainDataList": [
      {
        "desc": "北京 → 上海 2024-04-20",
        "trainList": [
          {
            "trainNo": "G1234",
            "trainType": "高铁",
            "departureStation": "北京南站",
            "arrivalStation": "上海虹桥站",
            "departureTime": "09:00",
            "arrivalTime": "13:28",
            "duration": "4小时28分",
            "seatTypes": [
              {
                "seatName": "二等座",
                "price": 553,
                "remainNum": 99
              },
              {
                "seatName": "一等座",
                "price": 933,
                "remainNum": 20
              }
            ],
            "pcRedirectUrl": "https://...",
            "clawRedirectUrl": "https://..."
          }
        ]
      }
    ]
  }
}
```

---

## 🚌 长途汽车查询 (bus-query.js)

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 出发地 + 目的地 | `--departure "北京" --destination "上海"` | 按城市查询 |
| 出发站 + 到达站 | `--departure-station "北京六里桥客运站" --arrival-station "上海长途汽车客运站"` | 精确站点查询 |

### 调用示例

```bash
# 北京到上海，明天的长途汽车
node scripts/bus-query.js \
  --departure "北京" \
  --destination "上海" \
  --extra "明天" \
  --channel webchat \
  --surface webchat

# 站到站精确查询
node scripts/bus-query.js \
  --departure-station "北京六里桥客运站" \
  --arrival-station "上海长途汽车客运站" \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "busDataList": [
      {
        "desc": "北京 → 上海 2024-04-20",
        "busList": [
          {
            "busNo": "K1234",
            "departureStation": "北京六里桥客运站",
            "arrivalStation": "上海长途汽车客运站",
            "departureTime": "08:30",
            "arrivalTime": "20:00",
            "duration": "11小时30分",
            "price": 350,
            "seatType": "大型高三",
            "pcRedirectUrl": "https://...",
            "clawRedirectUrl": "https://..."
          }
        ]
      }
    ]
  }
}
```

---

## 🏨 酒店查询 (hotel-query.js)

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 目的地城市 | `--destination "上海"` | 按城市查询 |
| 目的地 + 位置偏好 | `--destination "上海" --extra "外滩附近"` | 指定区域 |
| 目的地 + 入住日期 | `--destination "上海" --extra "明天入住"` | 指定日期 |

### 调用示例

```bash
# 上海酒店，明天入住
node scripts/hotel-query.js \
  --destination "上海" \
  --extra "明天入住" \
  --channel webchat \
  --surface webchat

# 上海外滩附近的酒店
node scripts/hotel-query.js \
  --destination "上海" \
  --extra "外滩附近" \
  --channel webchat \
  --surface webchat

# 简单查询（仅目的地）
node scripts/hotel-query.js \
  --destination "上海" \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "hotelDataList": [
      {
        "desc": "上海酒店推荐",
        "hotelList": [
          {
            "hotelName": "上海外滩华尔道夫酒店",
            "address": "上海市黄浦区中山东一路2号",
            "star": "五星级",
            "score": 4.8,
            "price": 1280,
            "originalPrice": 1580,
            "discount": "8.1折",
            "tags": ["外滩", "江景", "豪华"],
            "pcRedirectUrl": "https://...",
            "clawRedirectUrl": "https://..."
          }
        ]
      }
    ]
  }
}
```

---

## 🏞️ 景点查询 (scenery-query.js)

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 目的地城市 | `--destination "杭州"` | 按城市查询 |
| 目的地 + 特色 | `--destination "杭州" --extra "适合亲子"` | 指定特色 |
| 目的地 + 类型 | `--destination "苏州" --extra "园林 5A 景区"` | 指定类型 |

### 调用示例

```bash
# 杭州景点，适合亲子
node scripts/scenery-query.js \
  --destination "杭州" \
  --extra "适合亲子" \
  --channel webchat \
  --surface webchat

# 苏州园林景点
node scripts/scenery-query.js \
  --destination "苏州" \
  --extra "园林" \
  --channel webchat \
  --surface webchat

# 简单查询（仅目的地）
node scripts/scenery-query.js \
  --destination "杭州" \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "sceneryDataList": [
      {
        "desc": "杭州景区推荐",
        "sceneryList": [
          {
            "name": "西湖风景名胜区",
            "cityName": "杭州",
            "star": "5A 景区",
            "score": 4.9,
            "price": 0,
            "describe": "世界文化遗产，杭州标志性景点",
            "pcRedirectUrl": "https://...",
            "clawRedirectUrl": "https://..."
          }
        ]
      }
    ]
  }
}
```

---

## 🧳 旅行度假查询 (travel-query.js)

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 目的地 | `--destination "三亚"` | 按城市/地区查询 |
| 出发地 + 目的地 | `--departure "苏州" --destination "杭州"` | 含往返交通规划 |
| 出发地 + 目的地 + 天数 | `--departure "苏州" --destination "杭州" --extra "3天2晚"` | 含行程规划 ⭐ |
| 目的地 + 天数 + 类型 | `--destination "云南" --extra "6天5晚 自由行"` | 指定行程 |

### 调用示例

```bash
# 经典场景：从某地出发到某地玩几天（推荐）
node scripts/travel-query.js \
  --departure "苏州" \
  --destination "杭州" \
  --extra "3天2晚" \
  --channel webchat \
  --surface webchat

# 仅目的地查询
node scripts/travel-query.js \
  --destination "三亚" \
  --channel webchat \
  --surface webchat

# 带假期条件
node scripts/travel-query.js \
  --destination "三亚" \
  --extra "五一假期" \
  --channel webchat \
  --surface webchat

# 指定天数和类型
node scripts/travel-query.js \
  --destination "云南" \
  --extra "6天5晚 自由行" \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "trainDataList": [
      {
        "desc": "苏州 → 杭州 推荐火车",
        "trainList": [
          { "trainNo": "G7589", "departureTime": "09:00", "arrivalTime": "09:45" }
        ]
      }
    ],
    "hotelDataList": [
      {
        "hotelList": [
          { "hotelName": "杭州西湖大酒店", "price": 580 }
        ]
      }
    ],
    "sceneryDataList": [
      {
        "sceneryList": [
          { "name": "西湖", "price": 0 }
        ]
      }
    ],
    "tripDataList": [
      {
        "desc": "杭州3日游产品",
        "tripList": [
          {
            "tripName": "杭州西湖3日自由行",
            "price": 1280,
            "days": 3,
            "type": "自由行",
            "pcRedirectUrl": "https://..."
          }
        ]
      }
    ],
    "tripPlanDataList": [
      {
        "planTitle": "杭州3日游行程规划",
        "days": [
          {
            "day": 1,
            "title": "西湖经典游",
            "activityList": [
              {
                "name": "千岛湖景区",
                "introduction": "徜徉在星罗密布的岛屿中",
                "price": "45.5",
                "star": "5A级景区",
                "score": "4.6",
                "commentNum": "13615",
                "openTime": "08:00-15:00",
                "playTime": "半天-1天",
                "theme": "海滨岛屿",
                "pcRedirectUrl": "https://...",
                "redirectUrl": "https://..."
              }
            ]
          }
        ]
      }
    ],
    "ugcDataList": [
      {
        "ugcList": [
          {
            "name": "杭州三日游攻略",
            "nickName": "旅行达人",
            "redirectUrl": "https://..."
          }
        ]
      }
    ]
  }
}
```

---

## 🚗 智能交通查询 (traffic-query.js)

> 🚨 **使用场景**: 用户**未明确指定交通方式**时使用！

### 参数组合

| 组合 | 参数示例 | 说明 |
|------|---------|------|
| 出发地 + 目的地 | `--departure "北京" --destination "上海"` | 按城市查询 |

### 调用示例

```bash
# 北京到上海，智能推荐交通方式
node scripts/traffic-query.js \
  --departure "北京" \
  --destination "上海" \
  --channel webchat \
  --surface webchat

# 明天出发
node scripts/traffic-query.js \
  --departure "北京" \
  --destination "上海" \
  --extra "明天" \
  --channel webchat \
  --surface webchat

# 包含自驾偏好
node scripts/traffic-query.js \
  --departure "苏州" \
  --destination "南京" \
  --extra "自驾" \
  --channel webchat \
  --surface webchat
```

### 响应数据结构

```json
{
  "code": "0",
  "data": {
    "trainDataList": [
      {
        "desc": "北京 → 上海 火车推荐",
        "trainList": [
          { "trainNo": "G123", "departureTime": "09:00", "price": 553 }
        ]
      }
    ],
    "flightDataList": [
      {
        "desc": "北京 → 上海 航班推荐",
        "flightList": [
          { "flightNo": "CA1234", "departureTime": "08:00", "price": 850 }
        ],
      }
    ],
    "busDataList": [
      {
        "desc": "北京 → 上海 汽车推荐",
        "busList": [
          { "busNo": "K1234", "departureTime": "08:30", "price": 350 }
        ]
      }
    ]
  }
}
```

---

## 📤 响应结构说明

### 成功响应

```json
{
  "code": "0",
  "data": {
    "xxxDataList": [
      {
        "desc": "描述信息",
        "xxxList": [
          {
            "具体资源对象": "..."
          }
        ]
      }
    ]
  }
}
```

**说明**:
- `code`: `"0"` 表示成功
- `data`: 业务数据对象（单层 data，不是双层）
- `xxxDataList`: 各类资源列表（如 `flightDataList`、`trainDataList` 等）
- `xxxList`: 具体资源列表（如 `flightList`、`trainList` 等）
- `desc`: 描述信息（可选）

### 无结果

```json
{
  "code": "1",
  "message": "无结果"
}
```

### 错误响应

```json
{
  "code": "3",
  "message": "鉴权失败"
}
```

---

## ⚠️ 错误码处理

| Code | 含义 | 处理方式 |
|------|------|---------|
| `0` | 成功 | 正常解析并输出结果 |
| `1` | 无结果 | 告知用户未找到相关资源，建议调整搜索词 |
| `3` | 鉴权失败 | 检查 API Key 是否配置正确 |

详细错误处理指南见 `references/error-handling.md`

---

_同程旅行 · 让旅行更简单，更快乐_
