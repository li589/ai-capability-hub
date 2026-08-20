# 兴业证券智达平台研报摘要查询技能

## 简介

`ics-report-info-list-skill` 是用于查询兴业证券智达平台研报摘要信息的技能，支持关键词搜索和分页查询功能。

## 功能特性

- 🔍 关键词搜索研报摘要
- 📄 分页查询（支持"下一页"功能）
- 🔐 自动获取用户信息（userId）
- 📊 结果以 JSON 和 Markdown 格式保存
- ⚙️ 支持自定义查询数量（1-20条）

## 目录结构

```
ics-report-info-list-skill/
├── script/
│   └── report_info_list.py    # 主脚本文件
├── output/                    # 查询结果输出目录
│   ├── reportSearchInfos.json # JSON格式结果
│   └── report_result.md       # Markdown格式结果
├── SKILL.md                   # 技能定义文档
├── requirements.txt           # Python依赖列表
└── README.md                  # 项目说明文档
```

## 环境要求

- Python 3.6+
- 配置环境变量 `XYZD_APIKEY`

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

```bash
# Linux/Mac
export XYZD_APIKEY=your_api_key

# Windows PowerShell
$env:XYZD_APIKEY="your_api_key"
```

## 使用方法

```bash
# 查询关键词相关研报（默认20条）
python script/report_info_list.py "AI"

# 指定查询数量（1-20）
python script/report_info_list.py "AI" 10

# 查询下一页
python script/report_info_list.py "AI" 下一页

# 查询下一页并指定数量
python script/report_info_list.py "AI" 下一页 10
```

## 输出说明

### 输出文件

| 文件 | 格式 | 说明 |
|------|------|------|
| `output/reportSearchInfos.json` | JSON | 完整查询结果数据 |
| `output/report_result.md` | Markdown | 格式化的可读报告 |

### 输出示例

```markdown
## 1. 谷歌-A(GOOGL.O)AI 驱动核心业务增长，全栈能力显现

- **作者**: 兰测U13968
- **研究团队**: 汽车小组
- **报告类型**: 宏观经济研究 / 国际宏观经济点评
- **发布时间**: 2026-01-09 15:35:40
- **研报摘要**: ylm

---
```

## API 接口

| 接口 | URL | 方法 |
|------|-----|------|
| 用户信息 | `https://ics.xyzq.cn/icsapp/ai/skill/account/get-user-info` | GET |
| 研报查询 | `https://ics.xyzq.cn/icsapp/ai/skill/report/infoList` | GET |

## 安全规则

- ⚠️ 禁止在日志中打印 API Key
- ⚠️ keyword 禁止包含 SQL 注入字符
- ⚠️ 请求数量限制在 1-20 范围内

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.1 | 2026-06-17 | 优化结构，增强安全规则 |
| 1.0.0 | 2026-06-16 | 初始版本 |

## 免责声明

以上内容通过技能自主调用数据生成，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。