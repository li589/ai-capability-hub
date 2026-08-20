---
name: weather-forecast
description: "Use when users ask about weather, weather forecast, temperature, today's weather, tomorrow's weather, this week's weather, or city weather conditions in China. Supports real-time weather, 7-day 3-hour interval forecasts, 15-day forecasts, and 40-day long-term forecasts. Trigger phrases include: 'weather', 'forecast', 'temperature', 'will it rain', 'hourly weather', 'next N days', 'next month'."
install_source: official
install_method: download
skill_id: official_SPhWV7D0
enabled_at: 1787232677951
version: 1.0.0
name_zh: 天气预报中国气象网
---

# 天气预报技能

查询中国城市的实时天气和未来天气预报。支持实时天气、逐3小时预报、7天预报、15天预报和40天长期预报。

## 触发场景

- "北京天气怎么样" / "查一下上海天气"
- "今天/明天/后天天气如何"
- "未来一周/一个月天气怎么样"
- "会下雨吗" / "需要带伞吗"
- "今天每个小时天气" / "逐小时预报"
- "深圳气温多少度"
- "杭州/成都/广州天气预报"
- "下个月天气如何"

## 数据来源

使用中国天气网 (weather.com.cn) 的数据：

| 数据类型 | URL | 说明 |
|---------|-----|------|
| 实时天气 | `https://www.weather.com.cn/data/sk/{城市代码}.html` | 当前温度、风向、湿度 |
| 7天预报 | `https://www.weather.com.cn/weather/{城市代码}.shtml` | 含逐3小时预报 |
| 15天预报 | `https://www.weather.com.cn/weather15d/{城市代码}.shtml` | 较详细的15天预报 |
| **40天预报** | `https://d1.weather.com.cn/calendar_new/{年份}/{城市代码}_{年份月份}.html` | 长期预报 |
| 城市代码 | `https://j.i8tq.com/weather2020/search/city.js` | 城市代码查询 |

## 常用城市代码

| 城市 | 代码 | 城市 | 代码 |
|------|------|------|------|
| 北京 | 101010100 | 武汉 | 101200101 |
| 上海 | 101020100 | 西安 | 101110101 |
| 广州 | 101280101 | 杭州 | 101210101 |
| 深圳 | 101280601 | 南京 | 101190101 |
| 成都 | 101270101 | 重庆 | 101040100 |

## 工作流程

### 步骤 1: 确定城市代码

**优先使用已知城市代码**（见上表）。如果城市不在列表中，从远程获取：

```python
import urllib.request, json, re

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://j.i8tq.com/weather2020/search/city.js', headers=headers)
resp = urllib.request.urlopen(req)
text = resp.read().decode('utf-8')

# 解析 city_data
match = re.search(r'var city_data\s*=\s*(\{.*\});', text, re.DOTALL)
city_data = json.loads(match.group(1))

# 搜索城市
def find_city(city_data, name):
    for province, cities in city_data.items():
        for city, districts in cities.items():
            for district, info in districts.items():
                if name in info.get('NAMECN', ''):
                    return info.get('AREAID')
    return None

city_id = find_city(city_data, '北京')  # 返回 '101010100'
```

### 步骤 2: 获取天气数据

根据查询类型选择合适的API：

#### 2.1 实时天气（快速查询）

```python
import urllib.request, json

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://www.weather.com.cn/data/sk/101010100.html'
req = urllib.request.Request(url, headers=headers)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode('utf-8'))

info = data['weatherinfo']
print(f"{info['city']}: {info['temp']}°C, {info['WD']} {info['WS']}, 湿度{info['SD']}")
```

#### 2.2 40天预报（长期预报，推荐）

```python
import urllib.request, json, re, time

headers = {
    'Referer': 'https://www.weather.com.cn/',
    'User-Agent': 'Mozilla/5.0'
}

def get_40day_forecast(city_id, year_month):
    """获取指定月份的40天预报数据"""
    url = f'https://d1.weather.com.cn/calendar_new/{year_month[:4]}/{city_id}_{year_month}.html?_={int(time.time()*1000)}'
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    text = resp.read().decode('utf-8')
    # 去掉 JSONP 前缀
    text = re.sub(r'^var fc40\s*=\s*', '', text)
    return json.loads(text)

# 示例：获取2026年6月数据
data = get_40day_forecast('101010100', '202606')

# 过滤有效预报数据（排除历史数据）
valid = [d for d in data if d.get('cla') not in ('history', 'obs')]

# 按日期去重（同一日期可能有多条数据，优先保留有w1的）
seen = {}
for d in valid:
    date = d.get('date', '')
    if date not in seen:
        seen[date] = d
    elif not seen[date].get('w1') and d.get('w1'):
        seen[date] = d

# 查找特定日期
target_date = '20260627'
if target_date in seen:
    day = seen[target_date]
    print(f"{day['date']} 周{day['wk']}: {day.get('w1','--')} {day.get('min','--')}~{day.get('max','--')}°C")
```

**数据字段说明**：

| 字段 | 说明 | 示例 |
|------|------|------|
| date | 日期 (YYYYMMDD) | "20260627" |
| wk | 星期 | "六" |
| w1 | 天气现象（白天） | "多云" |
| w2 | 天气现象（夜间） | "晴" |
| c1 | 天气图标代码（白天） | "1" |
| c2 | 天气图标代码（夜间） | "0" |
| max/min | 最高/最低温度 | "34"/"24" |
| hmax/hmin | 历史均值温度 | "32"/"22" |
| hgl | 降水概率 | "33%" |
| rain1 | 降水量(mm) | "0.0" |
| wd1/ws1 | 风向/风力 | "东南风"/"3级" |
| cla | 数据类型 | 见下方说明 |

**cla字段含义**：

| cla值 | 说明 | 数据完整性 |
|-------|------|-----------|
| `d15 pre` | 15天预报（今天~3天内） | ✅ 完整（含w1/w2/c1/c2/wd1/ws1） |
| `d15` | 15天预报（当天） | ✅ 完整 |
| `d15 next` | 15天预报（跨月前几天） | ✅ 完整 |
| `d40` | 40天预报 | ⚠️ 无w1/w2，但有hgl/rain1 |
| `d40 next` | 40天预报（跨月） | ⚠️ 无w1/w2，但有hgl/rain1 |
| `history` | 历史均值 | ❌ 过滤掉 |
| `obs` | 已观测数据 | ❌ 过滤掉 |

**重要**：
- 16天后（`d40`/`d40 next`）没有天气现象文字（`w1`为空），但**有降水概率（`hgl`）和降水量（`rain1`）**
- 网页版根据 `hgl` 值显示雨图标：`hgl > 50%` 显示大雨，`30-50%` 显示中雨，`< 30%` 显示小雨或无雨
- 展示时可根据 `hgl` 推断降水可能性，如 `hgl > 50%` 提示"可能有雨"

#### 2.3 逐3小时预报（7天详细预报）

```python
import urllib.request, json, re

headers = {
    'Referer': 'https://www.weather.com.cn/',
    'User-Agent': 'Mozilla/5.0'
}

def get_hourly_forecast(city_id):
    """获取7天逐3小时预报"""
    url = f'https://www.weather.com.cn/weather/{city_id}.shtml'
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    html = resp.read().decode('utf-8')
    
    # 精确提取 hour3data JSON（通过括号匹配）
    start = html.index('var hour3data')
    brace_start = html.index('{', start)
    depth = 0
    end = brace_start
    for i in range(brace_start, len(html)):
        if html[i] == '{': depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    return json.loads(html[brace_start:end])

data = get_hourly_forecast('101010100')
# data['7d'] 是7天数据，每天8个时间点
# data['7d'][0] = 今天, data['7d'][1] = 明天, ...

# 解析单条数据
# 格式: "27日11时,d01,多云,31℃,东南风,<3级,2"
#       日期时间,天气代码,天气现象,温度,风向,风力,降水概率

for item in data['7d'][0]:  # 今天
    parts = item.split(',')
    print(f"{parts[0]} {parts[2]} {parts[3]} {parts[4]} {parts[5]}")
```

### 步骤 3: 解析和展示数据

#### 3.1 单日天气展示

```
📅 2026年6月27日 周六
🌤️ 多云转晴
🌡️ 温度: 24°C ~ 34°C
💨 风向: 东南风
💧 降水概率: 33%
```

#### 3.2 多日预报表格

```
======================================================================
  北京天气预报 | 2026年6月27日 ~ 7月10日
======================================================================
日期          星期  天气          温度         降水概率
----------------------------------------------------------------------
6月27日       周六  多云          24~34°C     33%
6月28日       周日  晴            24~35°C     50%
...
======================================================================
  说明: 16天后为长期预报，仅有温度范围
======================================================================
```

#### 3.3 逐3小时预报展示

```
杭州今天逐小时天气:
08时  多云  26°C  东南风 <3级
11时  多云  29°C  东南风 <3级
14时  晴    32°C  南风   <3级
17时  晴    31°C  南风   <3级
20时  晴    28°C  南风   <3级
23时  晴    26°C  西南风 <3级
```

### 步骤 4: 处理用户查询

根据查询类型选择数据源：

| 查询类型 | 数据源 | 说明 |
|---------|--------|------|
| 今天天气 | 实时天气 + 7天预报 | 优先使用实时天气 |
| 明天/后天 | 7天逐3小时预报 | 包含详细天气现象 |
| 未来一周 | 7天预报 | 每天一条汇总 |
| 未来15天 | 40天预报（当月API） | 有完整天气现象 |
| 未来30天 | 40天预报（当月+下月API合并，自动计算月份） | 前15天有天气现象，16天后只有温度 |
| 未来40天 | 40天预报（当月+下月+下下月API合并，自动计算月份） | 前15天有天气现象，16天后只有温度 |
| 逐小时天气 | 7天逐3小时预报 | 每3小时一条 |

**跨月查询处理（完整方案）**：

```python
from datetime import datetime, timedelta

def get_40day_forecast(city_id, year_month):
    """获取指定月份的40天预报数据"""
    import urllib.request, json, re, time
    headers = {
        'Referer': 'https://www.weather.com.cn/',
        'User-Agent': 'Mozilla/5.0'
    }
    url = f'https://d1.weather.com.cn/calendar_new/{year_month[:4]}/{city_id}_{year_month}.html?_={int(time.time()*1000)}'
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    text = resp.read().decode('utf-8')
    text = re.sub(r'^var fc40\s*=\s*', '', text)
    return json.loads(text)

def get_forecast_data(city_id, start_date, end_date):
    """
    获取指定日期范围的预报数据。
    
    关键逻辑：
    - 计算需要请求的月份（可能跨2-3个月）
    - 合并所有月份的数据
    - 过滤历史数据（cla=history/obs）
    - 按日期去重：同一日期有多条时，优先保留有天气现象(w1)的
    - 筛选目标日期范围
    
    注意：40天预报API返回的数据范围有限：
    - 当月API：当月剩余天数 + 下月初约4-5天（共约35天）
    - 下月API：上月末3天 + 下月全部 + 再下月初约2天
    - 最远可覆盖约40天，超出范围的数据不存在
    """
    # 计算需要的月份
    months = set()
    current = datetime.strptime(start_date, '%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d')
    
    while current <= end:
        months.add(current.strftime('%Y%m'))
        # 移到下个月
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    # 获取所有月份数据并合并
    all_data = []
    for month in sorted(months):
        data = get_40day_forecast(city_id, month)
        all_data.extend(data)
    
    # 过滤和去重
    valid = [d for d in all_data if d.get('cla') not in ('history', 'obs')]
    seen = {}
    for d in valid:
        date = d.get('date', '')
        if date not in seen:
            seen[date] = d
        elif not seen[date].get('w1') and d.get('w1'):
            seen[date] = d
    
    # 筛选日期范围
    result = []
    for date_str in sorted(seen.keys()):
        if start_date <= date_str <= end_date:
            result.append(seen[date_str])
    
    return result


def get_forecast_months(start_date, days):
    """
    计算指定天数范围内需要获取的月份。
    
    例如：5月31日开始，40天后是7月10日，需要5月、6月、7月共3个月。
    """
    start = datetime.strptime(start_date, '%Y%m%d')
    end = start + timedelta(days=days)
    months = set()
    current = start
    while current <= end:
        months.add(current.strftime('%Y%m'))
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    return sorted(months)


def get_30day_forecast(city_id):
    """
    获取从今天开始的30天预报。
    
    自动计算需要请求的月份（当月+下月，可能需要3个月），合并数据。
    返回去重后的日期->数据字典。
    """
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    
    # 计算需要的月份（30天可能跨2-3个月）
    months_needed = get_forecast_months(today_str, 30)
    
    all_data = []
    for month in months_needed:
        data = get_40day_forecast(city_id, month)
        all_data.extend(data)
    
    valid = [d for d in all_data if d.get('cla') not in ('history', 'obs')]
    seen = {}
    for d in valid:
        date = d.get('date', '')
        if date not in seen:
            seen[date] = d
        elif not seen[date].get('w1') and d.get('w1'):
            seen[date] = d
    
    return seen


def get_40day_forecast_complete(city_id):
    """
    获取从今天开始的40天完整预报。
    
    自动计算需要请求的月份（当月+下月+下下月），合并数据。
    返回去重后的日期->数据字典。
    
    注意：API返回的数据范围有限，最远约40天。
    16天后（d40类型）只有温度范围，没有天气现象(w1)。
    """
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    
    # 计算需要的月份（40天可能跨3个月）
    months_needed = get_forecast_months(today_str, 40)
    
    all_data = []
    for month in months_needed:
        data = get_40day_forecast(city_id, month)
        all_data.extend(data)
    
    valid = [d for d in all_data if d.get('cla') not in ('history', 'obs')]
    seen = {}
    for d in valid:
        date = d.get('date', '')
        if date not in seen:
            seen[date] = d
        elif not seen[date].get('w1') and d.get('w1'):
            seen[date] = d
    
    return seen


def infer_weather_from_hgl(hgl):
    """根据降水概率推断天气状况（用于d40数据，没有w1字段时）"""
    try:
        val = int(hgl.replace('%', ''))
        if val >= 70:
            return '🌧️大雨'
        elif val >= 50:
            return '🌦️中雨'
        elif val >= 30:
            return '🌦️小雨'
        elif val >= 10:
            return '☁️阴'
        else:
            return '☀️晴'
    except (ValueError, AttributeError):
        return '—'


def display_forecast(city_name, city_id, days=30):
    """获取并展示N天天气预报（通用函数，支持30天或40天）"""
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if days == 40:
        seen = get_40day_forecast_complete(city_id)
    else:
        seen = get_30day_forecast(city_id)
    
    dates = sorted(seen.keys())
    
    # 只取前N天
    display_dates = dates[:days]
    
    print(f"{'=' * 72}")
    print(f"  {city_name}{days}天天气预报")
    print(f"  {display_dates[0][:4]}年{int(display_dates[0][4:6])}月{int(display_dates[0][6:8])}日 ~ "
          f"{display_dates[-1][:4]}年{int(display_dates[-1][4:6])}月{int(display_dates[-1][6:8])}日")
    print(f"{'=' * 72}")
    print(f"{'日期':<12} {'星期':<6} {'天气':<14} {'温度':<12} {'降水概率':<10}")
    print(f"{'-' * 72}")
    
    for date_str in display_dates:
        d = seen[date_str]
        month = date_str[4:6]
        day = date_str[6:8]
        wk = d.get('wk', '')
        w1 = d.get('w1', '')
        w2 = d.get('w2', '')
        max_t = d.get('max', '--')
        min_t = d.get('min', '--')
        hgl = d.get('hgl', '--')
        cla = d.get('cla', '')
        
        # 有w1时使用文字描述，没有时根据降水概率推断
        if w1:
            weather = w1
            if w2:
                weather += f'转{w2}'
        else:
            # d40数据没有w1，根据hgl降水概率推断天气
            weather = infer_weather_from_hgl(hgl)
        
        print(f"{int(month)}月{int(day):02d}日  周{wk}   {weather:<12} {min_t}~{max_t}°C  {hgl}")
    
    print(f"{'=' * 72}")
    print(f"  说明：")
    print(f"  - 前15天有完整天气现象描述")
    print(f"  - 16天后为长期预报，根据降水概率推断天气状况")
    print(f"  - 数据来源：中国天气网 (weather.com.cn)")
    print(f"{'=' * 72}")


def display_30day_forecast(city_name, city_id):
    """获取并展示30天天气预报"""
    display_forecast(city_name, city_id, days=30)


def display_40day_forecast(city_name, city_id):
    """获取并展示40天天气预报"""
    display_forecast(city_name, city_id, days=40)
```

## 错误处理

1. **API返回空数据**：检查城市代码是否正确，尝试使用备选数据源
2. **请求被拒绝**：确保带上 `Referer` 和 `User-Agent` 请求头
3. **JSON解析失败**：检查是否正确去掉了 `var fc40 = ` 前缀
4. **数据缺失**：16天后的长期预报没有天气现象，使用"—"表示
5. **日期超出范围**：40天预报API有数据范围限制
   - 当月API：覆盖当月剩余 + 下月初约4-5天
   - 下月API：覆盖上月末3天 + 下月全部 + 再下月初约2天
   - 最远约40天，超出范围返回 `history` 类型数据（应过滤）
   - 如果查询的日期没有数据，提示用户"该日期暂无预报数据"

## 注意事项

1. **城市匹配**：支持模糊匹配，如"北京"、"北京市"、"海淀"都能匹配到北京
2. **默认城市**：如果用户没有指定城市，询问用户
3. **数据更新**：天气数据每小时更新，无需频繁请求
4. **长期预报限制**：40天预报中16天后只有温度范围，天气现象为"—"
5. **降水提示**：当 `rain1 > 0` 或 `hgl > 50%` 时，提醒用户可能下雨
6. **温度单位**：统一使用 `°C`
7. **30天预报**：从今天算起30天，需要合并当月和下月API数据。如果用户指定具体日期范围（如"6月27日到7月10日"），使用 `get_forecast_data()` 函数按日期范围查询
8. **数据范围限制**：如果查询的日期超出API覆盖范围（约40天），会返回空结果。此时应提示用户该日期暂无预报数据，并建议临近时再查