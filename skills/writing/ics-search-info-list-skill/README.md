# 兴业证券智达平台智能搜索技能

## 概述

本技能用于在兴业证券智达平台上搜索各类信息，包括研报、活动、专题、研究员、项目、公告、文章、资讯和标的等。搜索结果包含所有不为空列表的完整数据，每次调用结尾输出免责声明。支持通过关键词进行精准搜索，返回结构化的搜索结果并保存到文件。

## 功能特性

| 功能 | 说明 |
|------|------|
| 研报搜索 | 获取研究报告列表 |
| 活动搜索 | 获取线上会议、调研活动等列表 |
| 专题搜索 | 获取行业专题、研究合集等列表 |
| 研究员搜索 | 获取研究员信息列表 |
| 项目搜索 | 获取投行业务项目列表 |
| 公告搜索 | 获取兴证期货公告列表 |
| 文章搜索 | 获取研究文章列表 |
| 资讯搜索 | 获取市场资讯列表 |
| 标的搜索 | 获取股票标的列表 |

## 环境要求

- **Python版本**: 3.8+
- **依赖包**: requests

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

在运行脚本前，需配置环境变量 `XYZD_APIKEY`：

```bash
# Windows
set XYZD_APIKEY=your_api_key_here

# Linux/Mac
export XYZD_APIKEY=your_api_key_here
```

或者在系统环境变量中永久配置。

## 使用方法

### 基本语法

```bash
python script/search.py <keyword> [requestNum]
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词 |
| requestNum | int | 否 | 20 | 返回数量，范围 1-50 |

### 使用示例

```bash
# 搜索"兴业证券"相关信息，默认返回20条
python script/search.py "兴业证券"

# 搜索"科技"相关信息，返回30条
python script/search.py "科技" 30
```

## 输出说明

### 终端输出

搜索结果会以结构化的 Markdown 格式在终端显示，包括各分类列表的数据条数统计和所有记录摘要。

### 文件输出

搜索结果会保存到 `output/search_results.json` 文件中，包含所有有值列表的完整数据。

## 项目结构

```
ics-search-info-list-skill/
├── script/
│   └── search.py                  # 主搜索脚本
├── output/
│   └── search_results.json        # 搜索结果文件
├── SKILL.md                       # 技能定义文件
├── README.md                      # 项目说明文档
└── requirements.txt               # Python依赖配置
```

## API接口说明

### 1. 获取用户信息接口

- **URL**: `https://ics.xyzq.cn/icsapp/ai/skill/account/get-user-info`
- **方法**: GET
- **参数**: apiKey, opStation, skillName

### 2. 搜索信息接口

- **URL**: `https://ics.xyzq.cn/icsapp/ai/skill/search/searchinfo`
- **方法**: GET
- **参数**: opStation, userId, keyword, requestNum

## 错误处理

- **API Key 未配置**: 提示"环境变量 XYZD_APIKEY 未设置"
- **技能未启用**: 显示平台返回的错误信息
- **搜索失败**: 显示平台返回的错误信息

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-06 | 初始版本 |

## 免责声明

以上内容通过技能（skill）自主调用数据生成，其准确性依赖底层模型的理解与处理能力，不保证信息完全无误，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。
