# select-stock

华泰证券金融标的条件选股 OpenClaw skill —— 让 LLM 用自然语言完成股票/ETF/基金等金融标的的条件筛选。

通过本 skill，LLM 可以理解用户的选股意图（"科技板块上周涨幅前10的股票"、"市盈率低于20且营收同比增长超过30%的股票"），并通过后端服务获取专业结果。所有响应统一结构，对模型友好且对人类可读。

## 安装

前提：Python 3.9 或以上（系统 Python 需已安装 `requests` 包）。

```bash
clawhub install select-stock
```

或克隆本仓库到 OpenClaw skills 目录后，通过 OpenClaw 自动识别。

## 配置

使用前需配置以下环境变量:

| 变量 | 必填 | 说明 |
|---|---|---|
| `SELECT_STOCK_SERVICE_URL` | 否 | 后端服务地址（默认 `https://ai.zhangle.com`） |
| `HT_APIKEY` | 是 | 认证密钥 |
| `SELECT_STOCK_TIMEOUT_MS` | 否 | 请求超时，单位秒（默认 300，因选股接口耗时较长） |

```bash
export HT_APIKEY="<your-api-key>"
```

## 工具

| 工具 | 说明 |
|---|---|
| `selectStock` | 根据自然语言筛选条件查询符合条件的金融标的 |

详细参数、返回字段见 [`SKILL.md`](SKILL.md)。

## 直接调用脚本

OpenClaw 内核会按 `SKILL.md` 中的"**执行**"指令调用本 skill。所有工具走统一入口：

```bash
python3 select_stock.py <toolName> [args]
```

开发者也可直接命令行调用：

```bash
# 条件选股
python3 select_stock.py selectStock --query "科技板块上周涨幅前10的股票"

# 查看参数说明
python3 select_stock.py selectStock --help
```

所有调用输出统一的 JSON 结构 `{ ok, data, error }`，详见 SKILL.md "响应结构"段。

## 设计原则

### 查询保真
第一次调用使用用户原始问句，不做改写。仅在无结果时，按 SKILL.md 中的查询改写规则进行语义补全后重试一次。

### 响应统一
成功时 `data.result` 已是结构化 Markdown，可直接展示，严禁修改格式。失败时 `error.category` 让模型立刻知道错误性质，决定是否重试。

### 后端承载业务逻辑
选股条件解析、数据聚合等业务逻辑由后端服务处理，skill 层仅做 HTTP 转发。

## 仓库结构

```
select-stock/
├── SKILL.md              # 给 OpenClaw 内核 + LLM 的契约文档
├── README.md             # 本文件
└── select_stock.py       # 配置、HTTP 客户端、工具函数、CLI 调度入口
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
