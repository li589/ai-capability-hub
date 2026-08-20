---
name: cyber-threat-intel-daily-shared
description: >
  网络安全威胁情报日报生成工具（可分享版）。支持首次使用配置向导、自定义 RSS 情报源管理，
  从 13+ RSS 安全媒体源（中英文）和 0.zone 勒索情报平台采集当日数据，
  由 AI 以情报分析专家视角撰写结构化威胁情报日报，通过邮件发送（支持 AgentMail 和 SMTP）。
agent_created: false
version: "2.0"
---

# 网络安全威胁情报日报（可分享版）

## 功能特点

- ✅ **首次使用向导**：引导用户配置邮箱，支持 AgentMail 和 SMTP 两种方式
- ✅ **自定义 RSS 源**：可新增、禁用、删除情报数据源，无需修改代码
- ✅ **零硬编码**：所有个人信息（邮箱、密码、API Key）存储在配置文件中
- ✅ **13+ 内置 RSS 源**：覆盖中英文主流安全媒体
- ✅ **0.zone 勒索情报**：每日勒索组织动态追踪
- ✅ **HTML 邮件报告**：完整排版，含 CVE 高亮、威胁等级徽章、目录导航

---

## 首次使用：配置邮箱

**⚠️ 在运行日报之前，必须先完成一次配置。**

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py
```

配置向导将引导你：
1. 选择发送方式（AgentMail 推荐 / SMTP）
2. 填写邮箱凭据
3. 设置收件人邮箱

配置将保存在 `~/.workbuddy/skills/cyber-threat-intel-daily-shared/config.json`，后续无需重复配置。

### 两种发送方式说明

| 方式 | 适用场景 | 注册说明 |
|------|---------|---------|
| **AgentMail**（推荐） | 专为 AI Agent 设计，轻量简单 | 注册地址：https://agentmail.to |
| **SMTP** | 已有 Gmail / 企业邮箱 | 填写 SMTP 服务器、账号密码即可 |

---

## 管理 RSS 情报源

通过配置向导管理数据源：

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py
```

菜单选项：
- **1** → 查看所有 RSS 源（内置 + 自定义）
- **2** → 新增自定义 RSS 源
- **3** → 删除/禁用数据源

也可以告诉 AI：
> "帮我添加 BleepingComputer 的 RSS 源：https://www.bleepingcomputer.com/feed/"

---

## 执行流程（SOP）

### Phase 0：配置检查

在执行任何步骤前，检查是否已完成配置：

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py
```

若配置未完成，**暂停流程**，提示用户：

```
⚠️ 首次使用：请先完成邮箱配置

请运行以下命令完成配置：
    python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py

支持 AgentMail（推荐）或 SMTP 两种发送方式。
配置完成后，重新发起日报生成请求即可。
```

### Phase 1：确定目标日期

- 默认使用**今天**的日期
- 如用户指定日期（如"昨天的"、"5月16日的"），转换为 `YYYYMMDD` 格式
- 将日期存为变量 `DATE_STR`，如 `20260508`

### Phase 2：运行情报采集脚本

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/fetch_intel.py \
  --date {DATE_STR} \
  --output /tmp/intel_raw_{DATE_STR}.json
```

**注意**：
- 脚本自动加载用户自定义 RSS 源
- 运行时间约 30-90 秒
- 部分 RSS 源因网络限制可能返回 0 条，属正常现象

### Phase 3：生成结构化上下文文档

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/generate_report.py \
  /tmp/intel_raw_{DATE_STR}.json \
  --output /tmp/intel_context_{DATE_STR}.md
```

### Phase 4：读取上下文文档

读取 `/tmp/intel_context_{DATE_STR}.md`，内容将作为情报分析基础。

### Phase 5：AI 生成威胁情报日报

基于采集数据，以**情报分析专家**视角撰写日报。

**必须读取参考文档**（首次执行时）：
- `~/.workbuddy/skills/cyber-threat-intel-daily-shared/references/report_template.md`
- `~/.workbuddy/skills/cyber-threat-intel-daily-shared/references/data_sources.md`

**报告结构**（按 report_template.md 规范）：
1. 报告头部（日期、TLP 标记）
2. 执行摘要（3-5 句）
3. 威胁态势评级
4. 高优先级威胁预警（2-5 条）
5. 漏洞与补丁情报（CVE 表格）
6. 勒索软件与 APT 活动
7. 数据泄露与隐私安全
8. 供应链与软件安全
9. 政策监管与执法动态
10. 其他值得关注的情报
11. 防御建议摘要（立即/近期/持续）
12. 情报来源统计

**写作原则**：
- 区分"已确认"与"报告称/疑似"，保持客观
- 每个重大威胁必须有可操作的防御建议
- 英文资讯自动翻译/摘要为中文
- 如某类别无情报，标注"今日暂无相关情报"

### Phase 6：保存报告（Markdown + HTML）

**6a. 保存 Markdown 报告**

将 AI 生成的报告保存为：
```
网络安全威胁情报日报_{DATE_STR}.md
```

**6b. 转换为 HTML**

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/md_to_html.py \
  "网络安全威胁情报日报_{DATE_STR}.md" \
  --output "网络安全威胁情报日报_{DATE_STR}.html"
```

### Phase 7：发送邮件

```bash
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/send_report.py \
  --date {DATE_STR} \
  --context /tmp/intel_context_{DATE_STR}.md \
  --html-report "网络安全威胁情报日报_{DATE_STR}.html"
```

脚本自动从 config.json 读取邮件配置和收件人，无需手动指定。

---

## 管理命令速查

```bash
# ① 首次配置 / 修改配置
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py

# ② 新增 RSS 源（交互式）
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py
# → 选 2. 新增自定义 RSS 源

# ③ 查看当前 RSS 源列表
python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py
# → 选 1. 查看 RSS 数据源列表

# ④ 全流程一键生成（当日）
DATE=$(date +%Y%m%d)
SKILL=~/.workbuddy/skills/cyber-threat-intel-daily-shared
python3 $SKILL/scripts/fetch_intel.py --date $DATE --output /tmp/intel_raw_$DATE.json && \
python3 $SKILL/scripts/generate_report.py /tmp/intel_raw_$DATE.json --output /tmp/intel_context_$DATE.md
```

---

## 配置文件说明

配置保存在：`~/.workbuddy/skills/cyber-threat-intel-daily-shared/config.json`

```json
{
  "email_method": "agentmail",
  "agentmail": {
    "api_key": "your-api-key",
    "inbox_id": "you@agentmail.to"
  },
  "smtp": {},
  "recipient_email": "team@yourcompany.com",
  "custom_rss_sources": {
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "SecurityWeek": "https://www.securityweek.com/feed/"
  },
  "disabled_rss_sources": ["Threatpost"]
}
```

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 配置文件不存在 | 提示用户运行 setup_config.py |
| 某 RSS 源返回 0 条 | 继续执行，报告中标注"数据获取受限" |
| 0.zone 访问失败 | 勒索情报部分标注"受网络限制，数据不可用" |
| SMTP 认证失败 | 检查账号密码/授权码是否正确 |
| AgentMail 发送失败 | 检查 API Key 和 Inbox ID 是否有效 |

---

## 依赖说明

- **Python 3.8+**（使用标准库，大部分功能无需额外安装）
- `agentmail` Python 包（仅 AgentMail 方式需要）：`pip3 install agentmail`
- 网络访问（部分 RSS 源和 0.zone 需要稳定的网络）
