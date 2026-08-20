# financial-analysis

华泰证券金融分析与资讯查询 OpenClaw skill —— 让 LLM 用自然语言完成金融资讯查询、市场分析、市场洞察等操作。

通过本 skill，LLM 可以理解用户的金融分析意图（"帮我分析一下比亚迪"、"整理最近的利好利空资讯"），并路由到对应后端服务获取专业结果。所有响应统一结构，对模型友好且对人类可读。

## 安装

前提：Python 3.9 或以上（系统 Python 需已安装 `requests` 包）。

```bash
clawhub install financial-analysis
```

或克隆本仓库到 OpenClaw skills 目录后，通过 OpenClaw 自动识别。

## 配置

使用前需配置以下环境变量:

| 变量 | 必填 | 说明                                 |
|---|---|------------------------------------|
| `FINANCIAL_ANALYSIS_SERVICE_URL` | 否 | 后端服务地址（默认 `https://ai.zhangle.com`） |
| `HT_APIKEY` | 是 | 认证密钥（可以共用）                         |

```bash
export HT_APIKEY="<your-api-key>"
```

## 工具一览

2 个工具，按问题类别路由：

| 工具 | 类别 | 说明 |
|---|---|---|
| `diagnosisStock` | 分析诊断 | 个股/基金/ETF 诊断（含实体识别 & SMA 回退） |
| `marketInsight` | 市场洞察 | 个股分析、大盘分析、板块分析、金融资讯等 |

详细参数、返回字段见 [`SKILL.md`](SKILL.md)。

## 直接调用脚本

OpenClaw 内核会按 `SKILL.md` 中的"**执行**"指令调用本 skill。所有工具走统一入口：

```bash
python3 financial_analysis.py <toolName> [args]
```

开发者也可直接命令行调用：

```bash
# 分析诊断
python3 financial_analysis.py diagnosisStock --query "帮我分析一下比亚迪"

# 市场洞察
python3 financial_analysis.py marketInsight --query "今天大盘为什么跌了？"

# 查看某个工具的参数说明
python3 financial_analysis.py marketInsight --help
```

所有调用输出统一的 JSON 结构 `{ ok, data, error }`，详见 SKILL.md "响应结构"段。

## 设计原则

### 问题路由
工具按问题类别路由：分析诊断走 `diagnosisStock`，其余走 `marketInsight`。模型按用户意图直接命中，不混淆。

### 响应统一
成功时 `data.answer` 已是结构化 Markdown，可直接展示。失败时 `error.category` 让模型立刻知道错误性质（校验/业务/网络），决定是否重试；`error.hint` 是可直接给用户的下一步建议。

### 查询保真
`queryIndicator` 不拆分、不改写、不补充用户的原始提问，避免信息丢失或歧义。

## 仓库结构

```
financial-analysis/
├── SKILL.md              # 给 OpenClaw 内核 + LLM 的契约文档
├── README.md             # 本文件
├── financial_analysis.py # 配置、HTTP 客户端、工具函数、CLI 调度入口
├── references/
│   └── CATEGORIES.md     # 问题分类详细说明与示例
└── pyproject.toml
```

## 安全建议

- 后端服务地址仅存于环境变量，不写进代码或日志
- skill 层不持久化任何用户数据
- 不提交 `.env` 文件到版本控制

## 维护

本项目由华泰证券维护。

**Authors**: Huatai Securities

## 许可证

MIT
