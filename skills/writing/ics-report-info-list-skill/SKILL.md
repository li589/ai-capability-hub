---
name: "ics-report-info-list-skill"
description: "查询兴业证券智达平台研报摘要，支持关键词搜索和分页查询。"
display_name: "兴业证券智达平台研报摘要查询"
title: "兴业证券智达平台研报摘要查询技能"
version: "1.0.1"
author: "兴业证券智达团队"
tags: ["研报", "研报摘要", "研报查询", "研究报告"]
last_updated: "2026-06-17"
---

# 兴业证券智达平台研报摘要查询技能

## 功能描述

查询兴业证券智达平台的研报摘要信息，支持关键词搜索和分页查询功能。

## 触发条件

### 关键词触发
- 用户输入包含以下关键词：研报、研究报告、研报摘要、查询研报

### 自然语言示例
- "查询AI相关的研报"
- "帮我找一下测试相关的研究报告"
- "查看下一页研报"
- "研报摘要"

### 分页触发
- 用户输入"下一页"关键词进行分页查询

## 参数说明

| 参数 | 类型 | 必填 | 范围 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| keyword | string | 是 | 1-100字符 | 无 | 搜索关键词，用于匹配研报标题、摘要 |
| requestNum | int | 否 | 1-20 | 20 | 查询数量 |
| positionStr | string | 否 | - | 无 | 分页标识，用于下一页查询 |

## 分页机制

- **首次查询**：无需 positionStr，系统自动获取第一页数据
- **下一页查询**：用户输入"下一页"关键词，系统自动读取上次保存的 positionStr
- **每页上限**：最多返回20条数据

## 使用示例

```bash
# 查询关键词相关研报（默认20条）
python script/report_info_list.py "AI"

# 指定查询数量
python script/report_info_list.py "AI" 10

# 查询下一页
python script/report_info_list.py "AI" 下一页

# 查询下一页并指定数量
python script/report_info_list.py "AI" 下一页 10
```

## 输出格式

### JSON 输出结构
```json
{
  "reportInfoVOList": [
    {
      "title": "研报标题",
      "author": "作者",
      "researchTeam": "研究团队",
      "reportSummary": "研报摘要",
      "prnRptTypeName": "父报告类型名称",
      "subRptTypeName": "子报告类型名称",
      "releaseTime": "2024-01-01 10:00:00"
    }
  ],
  "positionStr": "分页标识"
}
```

### Markdown 输出模板
```markdown
## 1. {title}

- **作者**: {author}
- **研究团队**: {researchTeam}
- **报告类型**: {prnRptTypeName} / {subRptTypeName}
- **发布时间**: {releaseTime}
- **研报摘要**: {reportSummary}

---
```

### 字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 研报标题 |
| author | string | 作者 |
| researchTeam | string | 研究团队 |
| reportSummary | string | 研报摘要 |
| prnRptTypeName | string | 父报告类型名称 |
| subRptTypeName | string | 子报告类型名称 |
| releaseTime | string | 发布时间（yyyy-MM-dd HH:mm:ss格式） |

## 安全规则

### API Key 保护
- 禁止在日志、输出或错误信息中打印 API Key

### 输入验证
- keyword 禁止包含 SQL 注入字符（如 `'`, `"`, `;`, `--`）
- keyword 长度限制为 1-100 字符
- requestNum 强制限制在 1-20 范围内

### 数据隐私
- 查询结果仅用于展示，不进行二次存储
- 用户信息（userId）仅用于接口调用，不泄露给第三方

## 环境配置

需配置环境变量 `XYZD_APIKEY`：

```bash
# Linux/Mac
export XYZD_APIKEY=your_api_key

# Windows PowerShell
$env:XYZD_APIKEY="your_api_key"
```

## 执行规则

### 脚本约束
- **禁止**大模型重新生成或修改 `script/report_info_list.py` 脚本
- 技能执行应直接调用现有脚本，不得修改代码逻辑

### 必填参数校验
- `userId` 参数**必须**非空，由 `get-user-info` 接口获取
- `keyword` 参数**必须**非空，未提供时提示用户补充

### 错误处理
- **用户信息接口失败**：立即返回错误信息，禁止继续执行
- **研报查询接口失败**：立即返回错误信息
- **网络超时**（30秒）：返回超时错误提示
- **数据格式异常**：返回解析错误提示

## 安装约束

### 重名技能处理
- **约束规则**：安装此技能时，如果目标位置已存在同名技能，必须先卸载旧技能再安装
- **禁止操作**：禁止直接覆盖安装，避免文件冲突和残留问题

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.1 | 2026-06-17 | 优化结构，增强安全规则，添加版本历史 |
| 1.0.0 | 2026-06-16 | 初始版本 |

## 免责声明

以上内容通过技能自主调用数据生成，其准确性依赖底层模型的理解与处理能力，不保证信息完全无误，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。