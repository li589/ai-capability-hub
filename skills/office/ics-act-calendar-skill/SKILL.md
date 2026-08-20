---
name: "ics-act-calendar-skill"
description: "查询兴业证券智达平台的活动日历信息，支持指定日期范围获取活动列表及详情。"
display_name: "兴业证券智达平台活动日历查询"
title: "兴业证券智达平台活动日历查询技能"
version: "1.0.1"
author: "兴业证券智达团队"
tags: ["活动日历", "查询活动", "活动查询", "活动"]
---

# 兴业证券智达平台活动日历查询技能

## 功能描述

查询兴业证券智达平台的活动日历信息，支持指定日期范围获取活动列表及详情。

## 触发条件

### 关键词触发
- 用户询问包含"活动日历"、"查询活动"、"活动查询"、"活动安排"等关键词

### 自然语言触发示例
- "查询今天的活动日历"
- "明天有什么活动？"
- "查看本周的活动安排"
- "帮我查一下活动"

### 显式日期触发
- 用户提供明确日期范围进行活动查询

## 参数说明

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| startDate | string | 是 | 开始日期，支持绝对日期(YYYY-MM-DD)和相对日期(今天、明天、昨天等) | 无 |
| endDate | string | 是 | 结束日期，支持绝对日期和相对日期 | 无 |

## 日期约束

- endDate ≥ startDate
- 日期跨度 < 5天

## 缺失输入处理

| 场景 | 处理策略 |
|------|----------|
| 仅提供 startDate | 默认 endDate = startDate（查询单日） |
| 仅提供 endDate | 默认 startDate = endDate（查询单日） |
| 未提供任何日期 | 提示用户补充日期范围 |
| 日期格式错误 | 返回错误提示并列出支持的格式 |

## 使用示例

```bash
# 查询今天的活动
python script/activity_calendar.py "今天" "今天"

# 查询指定日期范围
python script/activity_calendar.py "2024-01-01" "2024-01-03"

# 使用相对日期
python script/activity_calendar.py "前天" "3天后"
```

## 输出格式

### JSON 输出结构
```json
{
  "status": "success",
  "message": "查询成功",
  "data": [
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
}
```

### Markdown 输出模板
```markdown
## 活动日历查询结果 ({startDate} 至 {endDate})

查询期间共 **{totalCount}** 场活动

### {date}
活动数量：**{count}** 场

**1. {title}**
   - 活动类型：{activityTypeName}
   - 活动状态：{activityStatus}
   - 一级行业：{primaryIndustry}
   - 二级行业：{secondaryIndustry}
   - 活动城市：{activeAddress}
   - 开始时间：{startTime}
   - 结束时间：{endTime}
```

### 字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 活动标题 |
| activityTypeName | string | 活动类型名称 |
| activityStatus | string | 活动状态（未开始/进行中/已结束） |
| primaryIndustry | string | 一级行业 |
| secondaryIndustry | string | 二级行业 |
| activeAddress | string | 活动城市 |
| startTime | string | 开始时间 |
| endTime | string | 结束时间 |

## 环境配置

需配置环境变量 `XYZD_APIKEY`。

## 执行规则

### 1. 脚本修改限制
- **禁止**大模型重新生成或修改 `script/activity_calendar.py` 脚本
- 技能执行应直接调用现有脚本，不得修改代码逻辑

### 2. userId 必填约束
- `https://ics.xyzq.cn/icsapp/ai/skill/activity/calendar/single` 接口的 `userId` 参数**必须**非空
- userId 由 `get-user-info` 接口获取，获取失败时禁止继续执行查询

### 3. 错误立即返回
- 当 `https://ics.xyzq.cn/icsapp/ai/skill/account/get-user-info` 接口报错时，立即返回错误信息
- 禁止在用户信息获取失败后执行任何后续操作

### 4. 异常处理
- API 调用超时（30秒）：返回超时错误
- 网络错误：返回网络异常提示
- 数据格式异常：返回数据解析错误

## 安装约束

### 重名技能处理
- **约束规则**：安装此技能时，如果目标位置已存在同名技能（`ics-act-calendar-skill`），必须先卸载旧技能，再进行安装
- **禁止操作**：禁止直接覆盖安装，避免文件冲突和残留问题

## 免责声明

以上内容通过技能（skill）自主调用数据生成，其准确性依赖底层模型的理解与处理能力，不保证信息完全无误，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。