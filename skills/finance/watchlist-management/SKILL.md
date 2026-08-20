---
name: watchlist-management
description: "金融市场自选股管理工具，支持**添加股票到自选**、**查询自选股列表**两类操作。TRIGGER when: 用户明确要求将股票加入自选、或查询自己的自选股/特定分组自选股列表。DO NOT TRIGGER when: 除添加、查询自选之外的其他股票相关请求（如删除自选、调整分组、股票分析、交易、个股行情查询等）。"
example:
  - 将华泰证券加入自选列表
  - 将贵州茅台、紫金矿业加入白酒、有色分组
  - 我的自选股有哪些
  - 查看我自选股票
  - 帮我把比亚迪加到新能源分组，再看看这个分组有啥
user-invocable: true
metadata:
  openclaw:
    emoji: ⭐
    skillKey: watchlist-management
    author: Huatai Securities
    version: "3.0"
    requires:
      bins:
        - python3
install_source: official
install_method: download
skill_id: official_UH6WZoIc
enabled_at: 1787231181426
version: 1.0.0
name_zh: 华泰-金融自选股管理
---

# 自选股管理工具 Skill

支持两类核心操作：添加股票到自选股列表、查询自选股列表。

## 触发条件

当用户的问题明确表达「添加自选股」或「查询自选股列表」意图时，应该激活此Skill。

### 触发关键词
#### 【添加类】
- "将...加入自选"
- "把...加到自选股"
- "添加...到自选"
- "关注...股票"
- "自选股添加..."
- "收藏...股票"

#### 【查看类】
- "查看我的自选股"
- "我的自选股有哪些"
- "自选股列表"
- "看一下我收藏的股票"
- "看看自选里的股票"

### 不应触发的场景
- 从自选股中删除股票
- 调整自选股分组
- 股票技术面/基本面分析
- 股票交易操作（买入/卖出）
- 单只股票行情/价格查询
- 其他非添加/查询自选股的操作

---

## 通用约定

- 字段命名：**小驼峰**（`group`）
- 响应结构：`{ ok, data, error }`

## 响应结构

成功：
```json
{ "ok": true, "data": { "result": "...", ... }, "error": null }
```

失败：
```json
{
  "ok": false, "data": null,
  "error": {
    "code": 5000,
    "message": "面向用户的中文说明",
    "category": "network",
    "retriable": true,
    "hint": "下一步该怎么做"
  }
}
```

按 `error.category` 处理：

| category | 含义 | 处理 |
|---|---|---|
| `network` | 网络/超时/5xx | 临时问题，可稍后再试 |
| `business` | 业务限制（无数据、接口异常） | 不立即重试，告知用户 |

---

## 工具

### addWatchlist
添加自选股：将指定股票加入用户的自选股列表。

**参数**：
- `query`：用户加自选的请求文本（必填）
- `group`：自选股分组名称（可选，默认"默认组"）

**返回**：`data.result`（操作结果文本）、`data.stocks`（添加的股票信息）

**执行**：`python3 watchlist_management.py addWatchlist --query <query> [--group <group>]`

---

### getWatchlist
查询自选股：查询用户的自选股列表（前20条）。

**参数**：
- `query`：用户查自选的请求文本（必填）

**返回**：`data.result`（查询结果文本）、`data.answer`（自选股列表详情）

**执行**：`python3 watchlist_management.py getWatchlist --query <query>`

---

## 执行流程

### Step 0: 意图判断与拆分
首先识别用户请求的核心意图，分为两类：
1. 添加自选意图：用户明确要求将指定股票加入自选
2. 查看自选意图：用户明确要求查询自己的自选股列表

如果同时包含两类意图，拆分后分别执行对应流程。

### 分支1：添加自选流程

#### Step 1: 按自选分组拆分请求
从用户消息中提取加自选问题，按照用户提到的自选分组拆分，如果用户没有说明分组，默认自选分组是`默认组`。

**示例：**
- "紫金矿业最近行情怎么样？帮我加个自选" → query = "将紫金矿业加入自选", group = "默认组"
- "将华泰证券、贵州茅台分别加入证券和白酒分组" → 拆分2个请求：① query = "将华泰证券加入证券自选分组", group="证券"；② query = "将贵州茅台加入白酒自选分组", group="白酒"

#### Step 2: 调用添加自选股接口
```bash
python3 watchlist_management.py addWatchlist --query "<query>" [--group "<group>"]
```

### 分支2：查看自选流程

#### Step 1: 调用查询自选股接口
```bash
python3 watchlist_management.py getWatchlist --query "<query>"
```

### Step 3: 结果展示规范
1. **内容完整**：直接获取脚本返回内容反馈给用户，不得擅自总结或删减
2. **查看自选返回股票代码列表**：请注明超过20的部分被截断了

---

## 配置

环境变量：

| 变量 | 必填 | 说明 |
|---|---|---|
| `WATCHLIST_SERVICE_URL` | 否 | 后端服务地址（默认 `https://ai.zhangle.com`） |
| `HT_APIKEY` | 是 | 认证密钥 |
| `WATCHLIST_TIMEOUT_SECONDS` | 否 | 请求超时，单位秒（默认 30） |

### 如何获取 HT_APIKEY（首次使用必读）

1. **打开申请页面**：浏览器访问 https://ai.zhangle.com/nzl/skill-manage/skills.html ，登录后复制属于你的 API Key。
2. **检测是否已配置**：调用 skill 前如检测到环境变量 `HT_APIKEY` 缺失，或脚本返回业务错误（watchlist 在 Key 失效时常见的兜底是 `code=-2 category=business message="未知错误"`，遇到此类不明错误请优先怀疑 Key 状态），应主动引导用户去步骤 1 获取，然后回到对话里把 Key 发回。
3. **写入本地配置**：拿到 Key 后，按以下方式持久化（脚本会从 `~/.htsc-skills/config` 读取）：

```bash
mkdir -p ~/.htsc-skills
printf "HT_APIKEY=%s\n" "<这里替换为用户提供的Key>" > ~/.htsc-skills/config
chmod 600 ~/.htsc-skills/config

for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
  [ -f "$RC_FILE" ] || continue
  grep -v "^export HT_APIKEY=" "$RC_FILE" > /tmp/_rc_tmp && mv /tmp/_rc_tmp "$RC_FILE"
  echo "export HT_APIKEY=\"<这里替换为用户提供的Key>\"" >> "$RC_FILE"
done
```

4. **当前会话立即生效**：执行前 `export HT_APIKEY=<Key>`，或内联 `HT_APIKEY=<Key> python3 watchlist_management.py ...`。
5. **更换 Key**：重复步骤 3，新值覆盖旧的。
6. **安全**：不要把 Key 写进对外发送的代码 / 日志 / 截图。
