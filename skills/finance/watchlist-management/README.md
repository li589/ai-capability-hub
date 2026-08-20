# watchlist-management

华泰证券自选股管理 OpenClaw skill —— 让 LLM 用自然语言完成添加自选股、查询自选股列表等操作。

通过本 skill，LLM 可以理解用户的自选股管理意图（"将华泰证券加入自选"、"我的自选股有哪些"），并通过后端服务获取专业结果。所有响应统一结构，对模型友好且对人类可读。

## 安装

前提：Python 3.9 或以上（系统 Python 需已安装 `requests` 包）。

```bash
clawhub install watchlist-management
```

或克隆本仓库到 OpenClaw skills 目录后，通过 OpenClaw 自动识别。

## 配置

使用前需配置以下环境变量:

| 变量 | 必填 | 说明 |
|---|---|---|
| `WATCHLIST_SERVICE_URL` | 否 | 后端服务地址（默认 `https://ai.zhangle.com`） |
| `HT_APIKEY` | 是 | 认证密钥 |
| `WATCHLIST_TIMEOUT_SECONDS` | 否 | 请求超时，单位秒（默认 30） |

```bash
export HT_APIKEY="<your-api-key>"
```

## 工具

| 工具 | 说明 |
|---|---|
| `addWatchlist` | 将指定股票加入用户的自选股列表 |
| `getWatchlist` | 查询用户的自选股列表（前20条） |

详细参数、返回字段见 [`SKILL.md`](SKILL.md)。

## 直接调用脚本

OpenClaw 内核会按 `SKILL.md` 中的"**执行**"指令调用本 skill。所有工具走统一入口：

```bash
python3 watchlist_management.py <toolName> [args]
```

开发者也可直接命令行调用：

```bash
# 添加自选股
python3 watchlist_management.py addWatchlist --query "将华泰证券加入自选" --group "默认组"

# 查询自选股
python3 watchlist_management.py getWatchlist --query "查看我的自选股"

# 查看参数说明
python3 watchlist_management.py addWatchlist --help
python3 watchlist_management.py getWatchlist --help
```

所有调用输出统一的 JSON 结构 `{ ok, data, error }`，详见 SKILL.md "响应结构"段。

## 设计原则

### 意图拆分
用户请求可能同时包含"添加"和"查看"两类意图，应拆分后分别调用对应工具。

### 分组感知
添加自选股时按用户指定的分组拆分请求，未指定分组时默认为"默认组"。

### 响应统一
成功时 `data.result` 提供操作结果文本，`data.answer` / `data.stocks` 提供结构化详情。失败时 `error.category` 让模型立刻知道错误性质，决定是否重试。

### 后端承载业务逻辑
股票识别、自选股管理等业务逻辑由后端服务处理，skill 层仅做 HTTP 转发。

## 仓库结构

```
watchlist-management/
├── SKILL.md                    # 给 OpenClaw 内核 + LLM 的契约文档
├── README.md                   # 本文件
└── watchlist_management.py     # 配置、HTTP 客户端、工具函数、CLI 调度入口
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
