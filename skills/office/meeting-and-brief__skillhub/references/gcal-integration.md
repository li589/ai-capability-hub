# Google Calendar 集成（v1.3.0 起为**辅助**路线）

> ⚠ v1.3.0 起本路线降级为**辅助**——主路线改为企微 CalDAV（详见 `wecom-caldav-setup.md`）。
> 原因：用户实测企微同步到 gcal 的可靠性不足，且 gcal 同步并非企微原生功能。
> gcal 集成保留作"如有日程已在 gcal 里"的补漏路线，触发优先级低于 CalDAV。
>
> CalDAV 主路线见 `wecom-caldav-setup.md`；离线兜底见 `calendar_ics_parse.py`。
>
> 下文为 v1.2.0 原始集成规范，作为 work-brief 步骤 2.5.2 的辅助调用规范保留。

---

# Google Calendar 集成（v1.2 原 · v1.3 辅助）

> 用户把企微日历同步到 Google Calendar 后，plugin 直接通过 **Google Calendar MCP** 拉日程——零凭据、零本地配置、有服务端时间过滤 + 全文搜索。
> 这是 v1.2.0 起的主路线。离线/无 gcal 备选见 `shared/calendar_ics_parse.py`。

---

## §1 为什么从企微 API 切到 gcal

| 维度 | 企微 OA API（v1.1.x · 已废）| Google Calendar MCP（v1.2.x · 现行）|
|---|---|---|
| 凭据管理 | corpid + corpsecret + agentid 本地配 | 无（MCP 已默认连接）|
| 安全风险 | 长期凭据，泄露立刻丢全部日程 | 0（OAuth 已托管）|
| 日历来源限制 | **仅应用自建日历**——APP 手动建的拉不到 | 任何用户授权的日历都能拉 |
| 时间过滤 | 客户端做（接口不支持）| 服务端 `startTime/endTime` ISO 8601 |
| 客户关键字搜索 | 客户端 grep | 服务端 `fullText`（AND 多词搜） |
| 多日历支持 | 需配 calendar_ids | 任选 calendarId（默认 primary）|

---

## §2 调用规范

### §2.1 列日历（首次设置时用一次）

```
mcp__c27f45a9-cd38-4757-9292-7585f2017b3b__list_calendars()
```

输出 list，每个含 `id / summary / timeZone / description`。

**典型顾问的日历清单**（用户 user@example.com 实测）：

| 日历 ID | 用途 | 是否拉 |
|---|---|---|
| `{wecom_sync_id}@import.calendar.google.com` · "刘万超's Events" | 企微同步过来的主源 | ✅ 主用 |
| `{wecom_tasks_id}@import.calendar.google.com` · "刘万超's Tasks" | 企微任务同步 | △ 可选 |
| `user@example.com` · "工作时间表" | gcal 原生工作主日历 | ✅ 补充 |
| `zh-cn.china#holiday@group.v.calendar.google.com` · "中国节假日" | 假日 | ❌ 跳过 |

### §2.2 拉指定时段 + 客户相关的事件

```
mcp__c27f45a9-cd38-4757-9292-7585f2017b3b__list_events(
    calendarId="{wecom_sync_id}@import.calendar.google.com",
    startTime="2025-11-01T00:00:00+08:00",
    endTime="2025-12-01T00:00:00+08:00",
    fullText="甲方X",                    # 客户关键字搜索（标题/描述/地点/参与人）
    orderBy="startTime",
    pageSize=250
)
```

**关键字搜索语义**（来自工具描述）：
- 大小写不敏感
- 多个词按 AND 组合（如 `fullText="甲方X 平衡计分卡"` 要求两个词都出现）
- 不支持精确短语匹配（要那个用客户端 grep）

### §2.3 单事件结构（list_events 返回 items[] 每条）

```json
{
  "id": "abc123",
  "summary": "参加甲方X耗材2026-2028战略研讨会",
  "description": "...",
  "location": "客户总部会议室",
  "start": {"dateTime": "2025-11-18T14:00:00+08:00", "timeZone": "Asia/Shanghai"},
  "end":   {"dateTime": "2025-11-18T18:00:00+08:00", "timeZone": "Asia/Shanghai"},
  "attendees": [
    {"email": "contact@client-example.com", "displayName": "甲方代表", "responseStatus": "accepted"},
    ...
  ],
  "status": "confirmed",     // confirmed / tentative / cancelled
  "organizer": {"email": "...", "displayName": "..."}
}
```

---

## §3 客户级配置（每个客户一次）

简报合成器（work-brief）在客户 README 中读取 gcal 配置：

```yaml
# memory/projects/clients/{客户}/README.md §1.2 段
gcal:
  primary_calendar_id: "ptr1b9mftml2ad0pvttco6m5snveljcd@import.calendar.google.com"
  # 客户匹配关键字（用作 list_events 的 fullText 参数）
  match_keywords:
    - "甲方X"
    - "甲方X简称"
    - "MCU"        # 客户业务相关词，扩大命中范围
    - "SOC"
  # 可选：多日历并查
  secondary_calendar_ids:
    - "user@example.com"
```

如果客户 README 中没配 `gcal:` 段 → work-brief 跳过 gcal 集成步骤，照常用切片数据。

---

## §4 集成到 work-brief 的步骤 2.5

work-brief 在主题聚类完成后（步骤 2 结束）执行：

```
1. 读客户 README §1.2 的 gcal 配置
2. 对每个 match_keywords 调一次 list_events（OR 关系合并结果）
3. 去重（按 event.id）
4. 过滤 status=cancelled
5. 转换为简报日志条目格式：
   "{月}月{日}日，{动词}{summary}；"
   - 动词推测：summary 首词命中 "汇报/沟通/讨论/评审/研讨/走访/参观/梳理/答疑/汇总/修订/参加" 之一 → 用它；否则默认"参加"
6. 与切片日志条目去重——同日同主题的事件，切片优先（切片含决议/行动项，gcal 只有题目）
7. 切片中没记录的 gcal 事件 → 标 [来源:gcal] tag 补到对应主题块
```

---

## §5 与切片合并的去重规则

| 切片日志条 | gcal 事件 | 处理 |
|---|---|---|
| "11月18日，参加甲方X耗材战略研讨会" | "11月18日，参加甲方X耗材2026-2028战略研讨会" | 切片优先（更准确）|
| "11月18日，参加甲方X耗材战略研讨会" | "11月18日，13:00 走访甲方X工厂"（同日不同事件）| 都保留 |
| 无 | "11月22日，沟通甲方X平衡计分卡"（切片中没记录）| gcal 补到主题块 + 标 `[来源:gcal]` |

**判定相同事件的规则**：同日 + 标题主关键字（取前 4-6 字）相似。

---

## §6 时区注意

- gcal MCP 默认按用户日历的时区返回
- 你的 calendar 实测时区：企微同步日历是 UTC（需转 Asia/Shanghai），原生 gcal 是 Asia/Shanghai
- 简报里的时间显示一律按 Asia/Shanghai
- 调 list_events 时 `startTime/endTime` 用 ISO 8601 带 +08:00 后缀，避免歧义

---

## §7 错误处理

| 场景 | 处理 |
|---|---|
| gcal MCP 未连接 | 提示用户在 Cowork 设置里连接 gcal；fallback 走 calendar_ics_parse.py |
| 客户 README 无 `gcal:` 字段 | 跳过 gcal 步骤，照常用切片 |
| list_events 返回空 | 不报错，简报里就少"gcal 补充"段 |
| 单次返回 >250 个事件 | 用 pageToken 翻页（list_events 单页上限 250）|
| 网络超时 | 重试一次；仍失败则 fallback 走 ics 或纯切片 |

---

## §8 离线/无 gcal 时的备选路线

如果你不用 Google Calendar：
1. 在企微 APP（或任何日历应用）导出 .ics
2. 调 `shared/calendar_ics_parse.py` 解析
3. 输出结构与 gcal MCP 完全一致

```bash
python3 shared/calendar_ics_parse.py \
  --ics ~/Downloads/calendar.ics \
  --start 2025-11-01 --end 2025-11-30 \
  --client 甲方X --format brief-log
```

---

## §9 v1.2.0 安全性收益

| 风险点 | v1.1.x（企微 API）| v1.2.x（gcal MCP）|
|---|---|---|
| corpsecret 泄露风险 | 高（长期凭据，文本配置）| **0**（OAuth 在 Cowork 侧托管）|
| 多人协作时的密钥分发 | 难（每人配一份）| **0**（每人各自 OAuth 即可）|
| 审计追踪 | 弱 | **强**（gcal 审计日志） |
| 撤销访问 | 重置 secret + 通知所有人 | **撤销 OAuth 单一动作** |
