# 04 — 自动化与工作流配置指南

> **版本**：v1.0 (2026-06-01)
> **目标**：把重复操作沉淀为自动化任务
> **适用**：使用 `automation_update` 工具创建/管理自动化任务

---
## 问题诊断决策树

```
自动化不执行？
    │
    ▼
[1] 检查状态
    ├── status 是 "PAUSED"？ → 改成 "ACTIVE"
    └── status 是 "ACTIVE" → 继续排查 ▶

[2] 检查时间
    ├── rrule 写对了吗？→ 用在线 RRULE 验证器检查
    ├── BYHOUR 是 UTC 还是本地时间？→ 确认时区
    ├── validFrom/validUntil 过了有效期？
    └── 刚创建需要等几分钟 → 调度器有轮询间隔

[3] 检查执行记录
    ├── automation_runs 表有记录吗？
    ├── 有记录但输出不对 → 改 prompt
    └── 无记录 → 检查 cwds（工作目录）是否存在

[4] 检查模型配置
    ├── modelId 指定的模型还可用吗？
    └── 没有指定 → 使用默认模型
```

---
## 4.1 自动化类型速查

| 类型 | scheduleType | 适用场景 | 示例 |
|------|-------------|---------|------|
| 循环执行 | `"recurring"` | 每日/每周/每月定时任务 | 每日邮件摘要、每周报告 |
| 一次性 | `"once"` | 单次延迟执行 | 明天下午3点提醒开会 |

---
## 4.2 自动化配置结构

```json
{
  "name": "任务名称",
  "prompt": "要执行的任务描述（保持自给自足，不依赖交互）",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=DAILY;BYHOUR=9;BYMINUTE=0",
  "cwds": "工作目录（逗号分隔多个）",
  "status": "ACTIVE",
  "modelId": "使用的模型ID（可选，不填用默认）",
  "modelIsThinking": false,
  "validFrom": "2026-03-18",
  "validUntil": "2026-03-22"
}
```

**⚠️ 创建前检查清单：**
```
□ prompt 是否自给自足？（不依赖与用户交互）
□ rrule 时间是否正确？（注意时区）
□ cwds（工作目录）是否存在？
□ status 是否设为 "ACTIVE"？
□ 如是一次性任务，用 scheduleType="once" + scheduledAt
□ 如是循环任务，用 scheduleType="recurring" + rrule
```

---
## 4.3 RRULE 语法速查

### 4.3.1 基础规则

| 规则 | 说明 | 示例 |
|------|------|------|
| `FREQ=DAILY` | 每天 | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` |
| `FREQ=HOURLY` | 每小时 | `FREQ=HOURLY;BYMINUTE=0` |
| `FREQ=WEEKLY` | 每周 | `FREQ=WEEKLY;BYDAY=MO` |
| `FREQ=MONTHLY` | 每月 | `FREQ=MONTHLY;BYMONTHDAY=1` |
| `FREQ=YEARLY` | 每年 | `FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1` |

### 4.3.2 BYDAY 星期对照

| 缩写 | 全称 |
|------|------|
| MO | 周一 Monday |
| TU | 周二 Tuesday |
| WE | 周三 Wednesday |
| TH | 周四 Thursday |
| FR | 周五 Friday |
| SA | 周六 Saturday |
| SU | 周日 Sunday |

### 4.3.3 常用组合模板

```json
// 每天9:30执行
{"scheduleType": "recurring", "rrule": "FREQ=DAILY;BYHOUR=9;BYMINUTE=30"}

// 工作日（周一到周五）每天9:00
{"scheduleType": "recurring", "rrule": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9;BYMINUTE=0"}

// 每周一、三、五9:00执行
{"scheduleType": "recurring", "rrule": "FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=9;BYMINUTE=0"}

// 每月1号8:00执行
{"scheduleType": "recurring", "rrule": "FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=8;BYMINUTE=0"}

// 每小时执行一次
{"scheduleType": "recurring", "rrule": "FREQ=HOURLY;BYMINUTE=0"}

// 工作日（周一到周五）每小时执行
{"scheduleType": "recurring", "rrule": "FREQ=HOURLY;BYDAY=MO,TU,WE,TH,FR"}

// 有效期：3月18日到3月22日
{"validFrom": "2026-03-18", "validUntil": "2026-03-22"}

// 每季度第一天 9:00（1月1日、4月1日、7月1日、10月1日）
{"scheduleType": "recurring", "rrule": "FREQ=MONTHLY;BYMONTH=1,4,7,10;BYMONTHDAY=1;BYHOUR=9;BYMINUTE=0"}
```

### 4.3.4 RRULE 常见错误

| 错误写法 | 正确写法 | 说明 |
|---------|---------|------|
| `BYDAY=Monday` | `BYDAY=MO` | 必须用双字母缩写 |
| `BYHOUR=9:30` | `BYHOUR=9;BYMINUTE=30` | 时间分两个字段 |
| `FREQ=WEEKLY;BYDAY=MO-FR` | `FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR` | WEEKLY不能BYDAY=多天范围，用DAILY |
| `BYMONTH=Jan` | `BYMONTH=1` | 月份用数字 |

---
## 4.4 拿来即用自动化模板

> 以下 6 个模板可直接复制使用，只需修改 prompt 中的具体参数（如邮箱、关键词、时间），不需要理解 RRULE 语法。

### 模板 1：每日晨报（信息聚合）

```json
{
  "name": "每日晨报",
  "prompt": "聚合以下内容生成今日晨报：\n1. 天气：查询当前城市今日天气（温度/空气质量/是否适合外出）\n2. 日程：查看今日日历事件\n3. 邮件：检查最近12小时未读邮件，标出需要回复的\n4. 待办：列出今日到期的待办事项\n输出格式：\n## 今日晨报（{日期}）\n### 🌤️ 天气\n### 📅 日程\n### 📧 邮件（X 封未读）\n### ✅ 待办\n按优先级排列，需要决策的标⚠️",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=DAILY;BYHOUR=7;BYMINUTE=30",
  "status": "ACTIVE"
}
```

### 模板 2：定时提醒（单次/周期）

```json
{
  "name": "每周五提交周报提醒",
  "prompt": "提醒用户：现在是周五下午4点，请在下班前提交本周周报。周报模板：\n1. 本周完成\n2. 下周计划\n3. 需要支持\n4. 风险项",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=WEEKLY;BYDAY=FR;BYHOUR=16;BYMINUTE=0",
  "status": "ACTIVE"
}
```

### 模板 3：周期巡检（健康检查）

```json
{
  "name": "WorkBuddy 环境巡检",
  "prompt": "运行环境诊断：\n1. 检查代理状态（curl http://127.0.0.1:51103/health）\n2. 检查各连接器连接状态\n3. 检查最近错误日志\n如有异常，输出异常项和建议修复操作；如无异常，输出'环境正常'。",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=DAILY;BYHOUR=9;BYMINUTE=0",
  "status": "ACTIVE"
}
```

### 模板 4：文件监控（变更检测）

```json
{
  "name": "工作区文件变更监控",
  "prompt": "检查工作目录中最近24小时内被修改的文件：\n1. 列出被修改的文件路径和修改时间\n2. 标记出 >1MB 的大文件变更\n3. 标记出配置文件（.json/.yaml/.toml）变更\n输出格式：Markdown 表格，按修改时间倒序",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=DAILY;BYHOUR=18;BYMINUTE=0",
  "cwds": "D:/workstore",
  "status": "ACTIVE"
}
```

### 模板 5：数据同步（定时拉取）

```json
{
  "name": "股票每日收盘数据",
  "prompt": "使用 westock-data 查询以下股票今日收盘数据：\n- 持仓股票列表（需用户指定）\n输出内容：股票代码/名称/收盘价/涨跌幅/成交量\n格式：Markdown 表格\n如有涨跌幅超过 ±5% 的标⚠️",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=16;BYMINUTE=0",
  "status": "ACTIVE"
}
```

### 模板 6：定时汇报（周期总结）

```json
{
  "name": "每周工作总结",
  "prompt": "生成本周工作总结：\n1. 本周完成的任务（从对话历史和文件变更推断）\n2. 本周创建/修改的文件统计\n3. 时间分配分析\n4. 下周建议关注的重点\n输出格式：\n## 周报（{起始日期} ~ {结束日期}）\n### 📋 完成任务\n### 📁 文件变更\n### ⏱️ 时间分析\n### 🎯 下周建议",
  "mode": "create",
  "scheduleType": "recurring",
  "rrule": "FREQ=WEEKLY;BYDAY=FR;BYHOUR=17;BYMINUTE=0",
  "status": "ACTIVE"
}
```

---

## 4.4b 模板使用说明

```
使用方法：
1. 选择最接近你需求的模板
2. 复制整个 JSON
3. 修改 prompt 中的具体内容（名称/关键词/时间等）
4. 修改 rrule 中的触发时间（BYHOUR/BYMINUTE/BYDAY）
5. 发给 AI 说"用这个配置创建自动化"

注意：
- cwds（工作目录）字段按需添加，不填默认当前目录
- 时间使用系统本地时间
- 模板中的 prompt 仅供参考，可按需调整
```

---
## 4.5 Prompt 编写规范

### 必须包含的四大要素

```
1. 明确的任务目标：
   "查看邮箱最近24小时的邮件"
   （而不是"处理邮件"）

2. 使用的工具/技能：
   "使用邮箱连接器"
   （让AI知道用什么工具）

3. 输出格式要求：
   "生成Markdown表格，包含发件人、主题、时间、重要性"
   （不给格式就会随意输出）

4. 边界约束：
   "只统计最近24小时，超过24小时的不计入"
   "如果某类数据为空，输出'无'而不是省略该部分"
```

### 编写检查清单

```
□ 任务是自给自足的吗？（不依赖用户交互）
□ 输出格式是否明确？（Markdown/表格/JSON/纯文本？）
□ 时间范围/数据范围是否指定？（避免返回过多数据）
□ 失败场景是否考虑？（如果工具不可用怎么做？）
□ 输出量是否受控？（避免每次输出几十页数据）
```

---
## 4.6 自动化管理命令

```json
// 查看所有自动化
{"mode": "list"}

// 查看单个自动化详情
{"mode": "view", "id": "automation-id"}

// 创建自动化
{"mode": "create", "name": "任务名", "prompt": "任务描述", ...}

// 更新自动化（只传需要修改的字段）
{"mode": "update", "id": "automation-id", "status": "PAUSED"}

// 暂停/恢复
{"mode": "update", "id": "automation-id", "status": "PAUSED"}   // 暂停
{"mode": "update", "id": "automation-id", "status": "ACTIVE"}   // 恢复

// 删除自动化
{"mode": "delete", "id": "automation-id"}
```

**⚠️ 删除注意事项**：
- 必须使用 `automation_update` 工具的 `delete` 模式
- **严禁**使用 `rm`、`sqlite3` 或文件系统操作删除
- 删除是软删除，数据保留但隐藏，可由支持工具恢复

---
## 4.7 自动化故障排查

### 4.7.1 任务不执行

```
排查顺序：
1. status = "PAUSED"？→ 改成 "ACTIVE"
2. 刚创建不到5分钟？→ 调度器有轮询间隔，再等一会
3. validFrom 是未来时间？→ 等到那个时间才触发
4. validUntil 是过去时间？→ 已过期，修改有效期
5. cwds（工作目录）不存在？→ 检查目录是否正确
6. modelId 指定的模型不可用？→ 去掉 modelId 用默认模型
```

### 4.7.2 任务执行了但结果不对

```
排查顺序：
1. prompt 不够具体？→ 补全"工具+格式+约束"
2. 输出被截断？→ 精简 prompt，减少输出量
3. 时间范围理解错误？→ 明确写清楚"最近24小时"而非"今天"
4. 依赖的skill/连接器不可用？→ 检查prompt中引用的工具
```

### 4.7.3 时区问题

```
RRULE 中 BYHOUR 通常使用系统本地时间
如需确认：创建一个简单的测试自动化（如5分钟后执行），观察是否按时触发
```

---
## 4.8 推荐自动化配置

| 名称 | 频率 | 用途 | 优先级 |
|------|------|------|-------|
| 工作日晨间规划 | 工作日7:30 | 查看今日待办，生成优先级排序 | ⭐⭐⭐ |
| 每日邮件摘要 | 每天9:00 | 汇总过去24小时邮件 | ⭐⭐⭐ |
| AI行业日报 | 每天8:30 | 汇总AI领域最新动态 | ⭐⭐ |
| 周末工作复盘 | 每周五18:00 | 回顾一周工作，分析效率 | ⭐⭐ |
| 投资日历提醒 | 每周日20:00 | 预告下周重要财经事件 | ⭐ |

---
## 4.9 扩展阅读

- `05-quick-cards.md` 卡片3：自动化配置的即查即用步骤
- `troubleshooting.md` — 自动化任务的跨领域诊断决策树
- 官方文档：https://www.codebuddy.cn/docs/workbuddy/Overview

---
## 4.10 踩坑经验

- 自动化 prompt 必须自给自足，不能依赖用户交互（没有人在线回答）
- rrule 的 BYHOUR 是系统本地时间，测试时注意时区
- 删除自动化只能用 automation_update delete 模式，绝不能用 rm/sqlite3
- 刚创建的自动化可能5分钟内不触发，调度器有轮询间隔
- cwds 必须是有效存在的目录，否则任务会失败
- 一次性任务用 scheduleType="once"，不要用 recurring+validUntil
