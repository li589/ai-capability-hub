# 企微 CalDAV 集成配置指南（v1.3.0 主路线）

> work-brief 通过标准 CalDAV 协议直连企微日历，实时拉时段内与客户相关的日程合并到简报。
> 这是 v1.3.0 起的**主路线**——比企微 OA API 简单 + 比 ICS 实时 + 比 gcal 不依赖第三方同步。

---

## §1 为什么选 CalDAV

| 维度 | CalDAV | OA API（v1.1.x · 已废）| ICS 离线 | gcal MCP |
|---|---|---|---|---|
| 标准协议 | ✅ RFC 4791 | 否（企微专有）| ✅ RFC 5545 | 否（专有）|
| 凭据性质 | **固定应用密码** | 长期 corpsecret | 无 | OAuth 已托管 |
| 凭据泄露后影响 | 撤销即止损 | 严重 | 0 | 撤销即止损 |
| 实时性 | ✅ 实时 | ✅ 实时 | 离线快照 | ✅ 实时 |
| 日历来源 | **个人所有日历** | 仅应用自建日历 | 你导的那份 | 看 gcal 同步可靠性 |
| 配置复杂度 | 低（4 行 yaml）| 高（建应用 + 拿凭据 + 创日历）| 极低 | 0 |

---

## §2 凭据获取（一次性 · 固定密码不过期）

### §2.1 在企微 APP 拿用户名 + 密码

1. 企微 APP → **日历**
2. 右上角 / 设置图标 → **同步到其他日历**
3. 看到三个字段：**账户**（username）/ **密码**（password）/ **服务器**（`caldav.wecom.work`）
4. 把账户和密码记下来（密码是**固定的**，不会过期）

### §2.2 PC 桌面端等效路径

企微桌面客户端 → 日历 → 设置 → 同步到其他日历 → 看到同样三个字段。

---

## §3 本地配置

### §3.1 配置路径

```
~/.consult/wecom-caldav.yaml
```

- Windows: `C:\Users\{你}\.consult\wecom-caldav.yaml`
- macOS/Linux: `~/.consult/wecom-caldav.yaml`

### §3.2 配置模板

```yaml
# ⚠ 含敏感密码 · .gitignore · chmod 600

username: "your-wecom-account"                # 企微 APP 拿到的账户
password: "your-caldav-password"               # 企微 APP 拿到的密码
server: "https://caldav.wecom.work"           # 固定服务器地址

# 可选：只读特定日历名（精确匹配 summary，留空读所有）
calendar_filter: []
#  - "我的日程"
#  - "客户工作"
```

### §3.3 文件权限

```bash
# macOS / Linux
mkdir -p ~/.consult
chmod 700 ~/.consult
chmod 600 ~/.consult/wecom-caldav.yaml

# Windows
# 右键 → 属性 → 安全 → 仅勾自己读写
```

### §3.4 .gitignore 必加

```gitignore
# CalDAV 凭据 · 不可入库
.consult/
**/wecom-caldav*
```

---

## §4 Python 依赖

```bash
pip install caldav
```

`caldav` 是 PyPI 上的标准 Python CalDAV 客户端库，活跃维护。
plugin 内 `shared/wecom_caldav.py` 依赖它——未装时脚本会友好报错并提示装。

---

## §5 验证配置

```bash
# 在 skill 目录跑
cd <skill>/meeting-and-brief

# 拉 11 月某客户的日程
python3 shared/wecom_caldav.py \
  --start 2025-11-01 --end 2025-11-30 \
  --client 甲方X --format brief-log
```

预期：每条"{月}月{日}日，{动词}{标题}；"+ 末尾打"共 N 条日程匹配"。

---

## §6 与 work-brief 的集成

启用后，`/new-brief` 会在 **步骤 2.5** 自动调 `shared/wecom_caldav.py`：

```
扫描切片 → 主题聚类 →
        ↓
   📅 CalDAV 拉时段日程（按客户关键字过滤）→
        ↓
合并到主题块日志条目（标 [来源:CalDAV] tag）→
        ↓
填充其余字段 → 二次校对 → 强制人审 → 出 docx
```

**冲突处理**：同日同主题的日程与切片日志重复时——
- 优先取**切片日志**（含决议/行动项，更准确）
- CalDAV 条目仅补充切片中未记录的日程（标 `[来源:CalDAV]`）

---

## §7 安全规则（不可豁免）

| 规则 | 说明 |
|---|---|
| 🔒 **不进 git** | `~/.consult/wecom-caldav.yaml` 加 `.gitignore` |
| 🔒 **不进 skill 包** | 凭据仅放本机 `~/.consult/`，绝不写进 skill 任何文件 |
| 🔒 **不发邮件/微信** | 凭据不发邮件、不微信、不复制粘贴到聊天 |
| 🔒 **泄露立即撤销** | 怀疑泄露 → 企微 APP → 日历 → 同步设置 → **关闭同步** 或 **重新生成密码** |
| 🔒 **文件权限 600** | macOS/Linux：`chmod 600 ~/.consult/wecom-caldav.yaml` |

**CalDAV 密码比 corpsecret 安全在哪**：
- 仅日历读取权限（不能读邮件/通讯录/发消息）
- 在企微后台**1 个动作可撤销**（关闭同步）
- 不像 corpsecret 那样需要重置所有依赖 secret 的应用

---

## §8 常见错误码

| 现象 | 处理 |
|---|---|
| `RuntimeError: CalDAV 连接/认证失败` | 1) 检查 server 是否 `caldav.wecom.work`；2) 检查 password 是否准确（复制时少字符）；3) 在企微 APP 重新生成密码 |
| `ImportError: 未装 caldav 库` | `pip install caldav` |
| 连接超时 | 检查网络；公司防火墙是否屏蔽了 caldav.wecom.work |
| 401 Unauthorized | password 错或被撤销，重新到企微 APP 拿 |
| 拉到 0 条日程 | 1) 检查时间窗对不对；2) 检查关键字是否太严；3) 用 `--format json` 看裸数据 |

---

## §9 关闭 CalDAV 集成

不创建 `~/.consult/wecom-caldav.yaml` → work-brief 检测到无凭据自动跳过 CalDAV 步骤，照常用切片数据 + 可选 gcal MCP / ics 备选。

不会因缺 CalDAV 而报错。

---

## §10 与其他路线的关系

| 路线 | 用途 | 文档 |
|---|---|---|
| **CalDAV（本文档 · 主）** | 实时拉企微日程 | 本文档 |
| ICS 离线（兜底）| 偶尔企微 APP 导出 ics 后解析 | `calendar_ics_parse.py` |
| gcal MCP（辅助）| 如有日程在 gcal 里 | `gcal-integration.md` |

work-brief 步骤 2.5 优先 CalDAV；CalDAV 不可用时 fallback 到 gcal MCP；都不可用时退化为纯切片数据。
