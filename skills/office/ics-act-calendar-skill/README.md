# 兴业证券智达平台活动日历查询技能

本技能用于在兴业证券智达平台上查询活动日历信息，支持通过指定日期范围获取活动列表及详细信息。

## 功能特性

- **活动日历查询**：获取指定日期范围内的活动列表
- **相对日期解析**：支持今天、明天、昨天、N天前、N天后等相对日期表达式
- **活动状态映射**：1=未开始、2=进行中、3=已结束
- **结果持久化**：查询结果保存到本地 JSON 文件
- **结构化输出**：以 Markdown 格式展示查询结果

## 环境要求

- Python 3.8+
- requests >= 2.31.0

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

### 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| XYZD_APIKEY | 是 | 智达平台 API Key |

**配置方式：**

```bash
# Windows
set XYZD_APIKEY=your_api_key_here

# Linux/Mac
export XYZD_APIKEY=your_api_key_here
```

## 使用方法

```bash
python script/activity_calendar.py <startDate> <endDate>
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startDate | string | 是 | 查询开始日期 |
| endDate | string | 是 | 查询结束日期 |

### 日期格式支持

**绝对日期**：
- YYYY-MM-DD（如：2024-01-01）
- YYYYMMDD（如：20240101）

**相对日期**：
- 今天、今日、明天、明日、昨天、昨日、前天、前日、大前天、大前日
- N天前（如：3天前）
- N天后（如：5天后）
- 本周、下周、本月、下月

### 日期约束

- endDate 必须大于或等于 startDate
- 日期跨度必须小于5天

### 使用示例

```bash
# 查询今天的活动
python script/activity_calendar.py "今天" "今天"

# 查询指定日期范围
python script/activity_calendar.py "2024-01-01" "2024-01-03"

# 使用相对日期
python script/activity_calendar.py "前天" "3天后"
python script/activity_calendar.py "本周" "下周"
```

## 输出说明

### 终端输出

```markdown
## 活动日历查询结果 (2024-01-01 至 2024-01-03)

查询期间共 **5** 场活动

### 2024-01-01 (周一)
活动数量：**2** 场

**1. 活动标题**
   - 活动类型：线上会议
   - 活动状态：进行中
   - 一级行业：金融
   - 二级行业：证券
   - 活动城市：上海
   - 开始时间：2024-01-01 09:00:00
   - 结束时间：2024-01-01 17:00:00
```

### 文件输出

查询结果保存到 `output/calendar_results.json`：

```json
[
  {
    "date": "20240101",
    "activityCount": 2,
    "activityList": [
      {
        "title": "活动标题",
        "activityTypeName": "线上会议",
        "activityStatus": "进行中",
        "primaryIndustry": "金融",
        "secondaryIndustry": "证券",
        "activeAddress": "上海",
        "startTime": "2024-01-01 09:00:00",
        "endTime": "2024-01-01 17:00:00"
      }
    ]
  }
]
```

## 错误处理

| 错误类型 | 错误信息 | 处理方式 |
|----------|----------|----------|
| API Key 未配置 | 环境变量 XYZD_APIKEY 未设置 | 配置环境变量 |
| 日期格式错误 | 无法解析日期 | 检查日期格式 |
| 日期范围错误 | 日期验证失败 | 调整日期范围 |
| API调用失败 | 平台返回的错误信息 | 检查网络和API Key |

## 项目结构

```
ics-act-calendar-skill/
├── script/
│   └── activity_calendar.py    # 主查询脚本
├── output/
│   └── calendar_results.json   # 查询结果文件
├── SKILL.md                    # 技能定义文件
├── README.md                   # 项目说明文档
└── requirements.txt            # Python依赖配置
```

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-06-17 | 初始版本，支持活动日历查询 |

## 免责声明

以上内容通过技能（skill）自主调用数据生成，其准确性依赖底层模型的理解与处理能力，不保证信息完全无误，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。