---
name: DNSPod DNS Management
description: 'DNSPod DNS record management via tccli CLI. Handles all DNS-related operations: domain list, record CRUD (A/AAAA/CNAME/MX/TXT/NS/SRV/CAA), smart resolution, batch operations, record line/TTL/weight/remark, domain health check, add domain resolution, modify DNS server. Triggers: DNS, DNSPod, 域名解析, 解析记录, 添加/修改/删除解析, 查看域名列表, 设置A记录/CNAME, 修改TTL, 批量操作DNS, 新域名接入, 修改DNS服务器, DNS服务器不正确, 域名健康巡检. Biases: uses tccli commands, queries before modifications, confirms before writes, prefers tccli --help over pretrained knowledge for latest parameters.'
metadata:
  {
    "openclaw": {
      "emoji": "🌐",
      "os": ["darwin", "linux"],
      "requires": {},
      "install": [
        {
          "id": "pip",
          "kind": "pip",
          "package": "tccli",
          "bins": ["tccli"],
          "label": "Install TCCLI"
        }
      ],
      "references": [
        {
          "id": "dnspod-record-management",
          "path": "references/dnspod-record-management.md",
          "label": "DNSPod 解析记录增删改查"
        },
        {
          "id": "dnspod-smart-resolution",
          "path": "references/dnspod-smart-resolution.md",
          "label": "DNSPod 智能解析配置"
        },
        {
          "id": "dnspod-domain-healthcheck",
          "path": "references/dnspod-domain-healthcheck.md",
          "label": "DNSPod 域名健康巡检"
        },
        {
          "id": "dnspod-add-domain-resolution",
          "path": "references/dnspod-add-domain-resolution.md",
          "label": "DNSPod 添加域名解析与修改DNS服务器"
        }
      ]
    }
  }
---

# DNSPod DNS 解析管理工具

你对腾讯云 API 参数、tccli 命令格式、产品限制数值的知识可能已过时。
**优先通过 `tccli --help` 和实际查询获取最新信息，而非依赖预训练知识。**

## 检索源

| 来源             | 如何检索                                             | 用于                                                |
|----------------|--------------------------------------------------|---------------------------------------------------|
| tccli 内置帮助     | `tccli dnspod <操作> --help`                       | 最新参数说明、必填/选填字段                                    | |
| 参考文档：解析记录增删改查  | `references/dnspod-record-management.md`         | 域名列表查询、解析记录的查询/添加/修改/删除、记录状态管理、可用线路查询、常见错误码       |
| 参考文档：智能解析配置    | `references/dnspod-smart-resolution.md`          | 基于线路的智能 DNS 解析（运营商分线路、境内外分流、访问限制）、线路类型说明、智能解析注意事项 |
| 参考文档：域名健康巡检    | `references/dnspod-domain-healthcheck.md`        | 域名状态检查（whois）、DNS 解析验证（dig）、HTTP 可用性检查（curl）、SSL 证书检查（openssl） |
| 参考文档：添加域名解析    | `references/dnspod-add-domain-resolution.md`     | 添加域名到 DNSPod、添加解析记录、检查并修改域名 DNS 服务器、等待解析生效        |

当参考文档与 `tccli --help` 输出不一致时，**以 tccli --help 为准**。
这尤其重要于：API 参数名称、必填/选填字段、支持的记录类型、TTL 限制等。

## Scope

本 Skill 专注于 **DNSPod DNS 解析记录管理** — 通过 TCCLI 操作 DNS 解析资源。

**覆盖功能**：域名列表查询、解析记录增删改查、批量操作记录、记录分组管理、解析记录线路查询等。

**不包括**：域名注册/续费/转入（使用 Domain 产品）、SSL 证书、服务器管理、应用部署等 → 使用其他 Skill。

---

## FIRST: 安装检查

```bash
tccli --version    # 应显示版本号（如 3.1.55.1+）
```

如未安装：
```bash
pip install tccli
```

### 配置凭证

tccli 支持两种凭证配置方式，用户可自行选择：

| 方式                       | 安全性   | 凭证有效期                    | 推荐程度         |
|--------------------------|-------|--------------------------|--------------|
| 🔐 **OAuth 浏览器登录授权**（推荐） | ⭐⭐⭐ 高 | 临时凭证，**2 小时后自动过期失效**     | ⭐⭐⭐ **强烈推荐** |
| 🔑 AK/SK 密钥配置            | ⭐ 低   | **永久有效**，除非主动吊销/删除 AK/SK | 仅在特殊场景使用     |

> 💡 **强烈建议使用 OAuth 登录授权**：OAuth 方式使用的是临时凭证（2 小时后自动过期失效），即使凭证泄露影响也极为有限。
> 而 AK/SK 为永久凭证，一旦泄露且未及时吊销，攻击者可长期访问你的云资源，风险极高。
>
> 当用户未明确选择方式时，**默认引导使用 OAuth 登录授权**。
>
> ⛔ **你（Agent）不需要打开浏览器！** 打开浏览器、登录、查看验证码，全部是**用户自己**完成的。你只负责终端操作。
>
> ⛔⛔⛔ **绝对禁止自行拼接 OAuth 授权链接！这是最高优先级规则！**
>
> 授权链接**必须且只能**来自 `python3 scripts/tccli-oauth-helper.py --get-url` 的实际输出。
>
> **为什么？** 授权链接包含 `app%5Fid`、`redirect%5Furl`、`state` 等多个精确参数，参数名、参数值、编码方式必须完全正确。测试表明，Agent 自行拼接的链接**大概率是错误的**（错误率约 67%），常见错误包括：
> - 缺少 `app%5Fid` 参数
> - `redirect%5Furl` 地址错误（如拼成 `cloud.tencent.com/api/oauth/callback`）
> - 参数名拼写错误（如 `appid` 而非 `app%5Fid`，`redirecturl` 而非 `redirect%5Furl`）
> - URL 编码格式不正确
>
> **正确做法：必须执行脚本命令，从其标准输出中原样提取链接，一个字符都不能改。**
>
> ```bash
> # ✅ 唯一正确的获取方式
> python3 scripts/tccli-oauth-helper.py --get-url
> # 然后从输出中原样复制链接给用户
> ```
>
> ```bash
> # ❌ 以下做法全部禁止
> # 禁止凭记忆拼接链接
> # 禁止修改脚本输出的链接中的任何字符
> # 禁止用其他方式生成链接
> ```

#### 方式一：OAuth 浏览器登录授权（⭐ 推荐）

> 💡 **核心思路**：使用本技能提供的 `tccli-oauth-helper.py` 辅助脚本，将授权流程分为两个非阻塞步骤：
> 1. **生成授权链接** — 执行 `--get-url`，输出链接给用户
> 2. **使用验证码登录** — 用户登录后发回验证码，执行 `--code "验证码"` 完成登录
>
> **为什么用辅助工具？** 原生的 `tccli auth login --browser no` 使用交互式 `input()` 等待用户输入验证码，在非交互式环境（如 Agent 子进程）中会因 EOF 而失败。辅助工具将验证码作为命令行参数传入，完美支持非交互式环境。

**第一步：检查当前凭证是否有效**
```bash
python3 scripts/tccli-oauth-helper.py --status
```

如果返回 `✅ 凭证有效`，说明凭证正常，可跳过授权。如果显示凭证不存在或已过期，执行以下授权流程。

也可以用 tccli 命令验证凭证是否可用：

```bash
tccli dnspod DescribeDomainList
```

> ⚠️ **注意**：不要使用 `tccli sts GetCallerIdentity` 验证凭证，该接口不支持 OAuth 临时凭证，会报 `InvalidParameter.AccessKeyNotSupport` 错误。

**第二步：生成授权链接**

执行辅助工具生成授权链接（此命令**不会阻塞**）：

```bash
python3 scripts/tccli-oauth-helper.py --get-url
```

输出示例：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 腾讯云 OAuth 授权登录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请在浏览器中打开以下链接完成登录：

https://cloud.tencent.com/open/authorize?scope=login&app%5Fid=100038427476&redirect%5Furl=...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
登录后，页面会显示一串 base64 编码的验证码。
请复制该验证码，然后运行以下命令完成登录：

  python3 tccli-oauth-helper.py --code "验证码"

或发送给 AI 助手，让它帮你完成登录。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 State: xxxxxxxxxx (10分钟内有效)
```

**第三步：展示授权链接给用户**

将上一步生成的授权链接**原样**展示给用户（不要修改链接中的任何字符）：

```
请在您的浏览器中打开以下链接，完成腾讯云账号登录：

👉 <从脚本输出中原样复制的完整授权链接>

登录成功后，页面上会显示一个验证码（一串 base64 编码的字符串），请完整复制后发给我。
```

> ⚠️ **关于授权链接的注意事项**：
> - ✅ 链接中的 `%5F` 是正常的（`_` 的 URL 编码），**不要**将其还原为 `_`，这是为了防止 Markdown 渲染器破坏链接
> - ⛔ **严禁修改、重新拼接或"美化"脚本输出的链接**，必须原样传递给用户

> ⚠️ **关于验证码的正确认知**：
> - ✅ 验证码是浏览器登录成功后页面上显示的一串 **base64 编码字符串**（如 `eyJhY2Nlc3NUb2tlbi...`），通常很长
> - ✅ 这个 base64 字符串是 OAuth 授权码，辅助工具会用它去换取临时密钥
> - ❌ **不是** URL 中的参数（如 `state=xxx`）
> - ❌ **不是**短数字验证码
>
> ⛔ **你不需要打开浏览器** — 浏览器操作由用户完成，和你的运行环境无关。

**第四步：使用验证码完成登录**

用户在浏览器完成登录后，会将页面上显示的 base64 验证码发给你。

收到验证码后，执行以下命令完成登录（此命令**不会阻塞**）：

```bash
python3 scripts/tccli-oauth-helper.py --code "用户发来的完整base64验证码"
```

成功输出示例：
```
🔄 正在获取临时凭证...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ OAuth 登录成功!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 配置文件: default
📌 凭证路径: /root/.tccli/default.credential
📌 过期时间: 2026-03-21 16:43:20
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

现在可以使用 tccli 了，例如：
  tccli dnspod DescribeDomainList
```

**第五步：验证授权结果**

登录成功后，执行以下命令验证：

```bash
tccli dnspod DescribeDomainList
```

返回域名列表即表示授权成功。

> ⚠️ **注意**：不要使用 `tccli sts GetCallerIdentity` 验证，该接口不支持 OAuth 凭证。

#### 辅助工具命令参考

| 命令 | 说明 |
|------|------|
| `python3 scripts/tccli-oauth-helper.py --get-url` | 生成 OAuth 授权链接 |
| `python3 scripts/tccli-oauth-helper.py --code "验证码"` | 使用验证码完成登录 |
| `python3 scripts/tccli-oauth-helper.py --status` | 检查当前凭证状态 |
| `python3 scripts/tccli-oauth-helper.py --status --profile myprofile` | 检查指定配置文件的凭证状态 |
| `tccli auth logout` | 退出登录，清除本地凭证 |

授权成功后凭证会保存在 `~/.tccli/default.credential`，后续命令无需重复登录。tccli 会自动刷新 OAuth 凭证，无需手动维护。

#### 退出登录

当用户需要退出当前登录、切换账号或清除本地凭证时，可使用以下命令：

```bash
tccli auth logout
```

该命令会清除本地保存的凭证信息（包括 OAuth 临时凭证和 AK/SK 配置）。

> 💡 **退出后**：需要重新执行 OAuth 登录授权或配置 AK/SK 才能继续使用 tccli。

#### 方式二：AK/SK 密钥配置

> ⚠️ **安全提示**：AK/SK 为**永久凭证**，除非你主动在腾讯云控制台吊销或删除，否则将一直有效。一旦泄露，攻击者可持续访问你的云资源。建议优先使用上方的 OAuth 登录授权方式。

如果用户选择使用 AK/SK 方式，或**主动**提供了 SecretId 和 SecretKey，可通过 tccli 命令配置：

```bash
tccli configure set secretId <用户提供的SecretId>
tccli configure set secretKey <用户提供的SecretKey>
```

配置完成后可通过以下命令验证：

```bash
tccli dnspod DescribeDomainList
```

> 💡 **提示**：当用户未明确选择凭证方式时，不要主动索要 AK/SK，应优先引导使用 OAuth 登录授权。

---

## 速查表

| 任务 | 命令 |
|------|------|
| 查看域名列表 | `tccli dnspod DescribeDomainList` |
| 添加域名 | `tccli dnspod CreateDomain --Domain <domain>` |
| 查看解析记录 | `tccli dnspod DescribeRecordList --Domain <domain>` |
| 添加解析记录 | `tccli dnspod CreateRecord --Domain <domain> --SubDomain <sub> --RecordType <type> --RecordLine 默认 --Value <value>` |
| 修改解析记录 | `tccli dnspod ModifyRecord --Domain <domain> --RecordId <id> --SubDomain <sub> --RecordType <type> --RecordLine 默认 --Value <value>` |
| 删除解析记录 | `tccli dnspod DeleteRecord --Domain <domain> --RecordId <id>` |
| 查看记录线路 | `tccli dnspod DescribeRecordLineCategoryList --Domain <domain>` |
| 设置记录状态 | `tccli dnspod ModifyRecordStatus --Domain <domain> --RecordId <id> --Status <enable/disable>` |
| 设置记录备注 | `tccli dnspod ModifyRecordRemark --Domain <domain> --RecordId <id> --Remark <remark>` |
| 批量添加记录 | `tccli dnspod CreateRecordBatch --help`（先查参数） |
| 批量修改记录 | `tccli dnspod ModifyRecordBatch --help`（先查参数） |
| 查看域名信息 | `tccli dnspod DescribeDomain --Domain <domain>` |
| 查看操作参数 | `tccli dnspod <操作> --help` |
| 查看所有 DNSPod 操作 | `tccli dnspod --help` |
| 退出登录 | `tccli auth logout` |

---

## 常用记录类型

| 记录类型 | 用途 | Value 示例 |
|---------|------|-----------|
| A | 将域名指向 IPv4 地址 | `1.2.3.4` |
| AAAA | 将域名指向 IPv6 地址 | `2001:db8::1` |
| CNAME | 将域名指向另一个域名 | `cdn.example.com` |
| MX | 指定邮件服务器 | `mail.example.com`（需设置 MX 优先级） |
| TXT | 文本记录，常用于域名验证、SPF | `v=spf1 include:example.com ~all` |
| NS | 指定子域名的 DNS 服务器 | `ns1.example.com` |
| SRV | 指定服务的服务器地址和端口 | `0 5 5060 sip.example.com` |
| CAA | 指定可为域名签发证书的 CA | `0 issue "letsencrypt.org"` |

---

## 场景决策

用户想做什么？
```
├─ 添加域名解析 / 新域名接入 / 快速添加解析 → 读取 references/dnspod-add-domain-resolution.md
├─ 修改域名 DNS 服务器 / 未使用云解析 DNS 地址 → 读取 references/dnspod-add-domain-resolution.md（步骤 3）
├─ 查看域名列表 → tccli dnspod DescribeDomainList
├─ 查看某域名的解析记录 → tccli dnspod DescribeRecordList --Domain <domain>
├─ 添加解析记录（A/CNAME/MX/TXT 等） → tccli dnspod CreateRecord
├─ 修改已有解析记录 → 先查 RecordId，再 tccli dnspod ModifyRecord
├─ 删除解析记录 → 先查 RecordId，确认后 tccli dnspod DeleteRecord
├─ 启用/暂停解析记录 → tccli dnspod ModifyRecordStatus
├─ 批量操作记录 → tccli dnspod CreateRecordBatch / ModifyRecordBatch
├─ 查看可用线路 → tccli dnspod DescribeRecordLineCategoryList --Domain <domain>
├─ 配置智能解析/分线路解析/按运营商解析 → 读取 references/dnspod-smart-resolution.md
├─ 退出登录/切换账号 → tccli auth logout
└─ 其他 DNSPod 操作 → tccli dnspod --help 探索
```

---

## 端到端示例

### 示例一：查询域名的所有解析记录

```bash
# 1. 查看账号下的域名列表
tccli dnspod DescribeDomainList

# 2. 查看指定域名的所有解析记录
tccli dnspod DescribeRecordList --Domain example.com
```

### 示例二：添加一条 A 记录

```bash
# 1. 先查看当前记录，避免重复
tccli dnspod DescribeRecordList --Domain example.com \
  --Subdomain www

# 2. 添加 A 记录：www.example.com → 1.2.3.4
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.2.3.4
```

### 示例三：修改一条解析记录

```bash
# 1. 先查询获取 RecordId
tccli dnspod DescribeRecordList --Domain example.com \
  --Subdomain www

# 2. 修改记录（假设 RecordId 为 123456）
tccli dnspod ModifyRecord \
  --Domain example.com \
  --RecordId 123456 \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 5.6.7.8
```

### 示例四：删除一条解析记录

```bash
# 1. 先查询确认要删除的记录
tccli dnspod DescribeRecordList --Domain example.com \
  --Subdomain test

# 2. 确认后删除（假设 RecordId 为 789012）
tccli dnspod DeleteRecord \
  --Domain example.com \
  --RecordId 789012
```

---

## 写操作和高危操作

### 操作分级

| 风险等级 | 操作类型 | 确认要求 |
|---------|---------|---------|
| ❌ 高危 | 修改解析记录、删除解析记录、批量修改记录、批量删除记录 | **二次确认**，明确写出影响范围 |
| ⚠️ 中危 | 添加解析记录、启用/暂停记录 | 单次确认 |
| ✅ 低危 | 查询域名列表、查看解析记录、查看线路 | 无需确认，直接执行 |

### 确认流程

1. 清楚说明将要执行的操作
2. 说明影响范围和后果（如：删除记录可能导致域名无法解析）
3. 等待用户明确输入"确认"或"是"
4. 收到确认后才执行

直接执行高危操作可能导致 **域名解析中断**、**服务不可访问**。

### 示例

**修改记录示例：**
```
用户：把 www.example.com 的 A 记录改成 5.6.7.8
Agent：
⚠️ 警告：即将修改以下解析记录
- 域名：example.com
- 主机记录：www
- 记录类型：A
- 当前记录值：1.2.3.4
- 修改后记录值：5.6.7.8
- RecordId：123456

此操作将变更 www.example.com 的解析指向，可能影响正在访问该域名的用户。
请输入"确认"继续，或"取消"放弃。
```

**删除记录示例：**
```
用户：删除 www.example.com 的 A 记录
Agent：
⚠️ 警告：即将删除以下解析记录
- 域名：example.com
- 主机记录：www
- 记录类型：A
- 记录值：1.2.3.4
- RecordId：123456

此操作将导致 www.example.com **无法通过该 A 记录解析**，可能影响网站访问。
请输入"确认"继续，或"取消"放弃。
```

---

## 反模式与常见错误

### 自行拼接 OAuth 授权链接（⛔ 严重错误）

授权链接包含 `app%5Fid`、`redirect%5Furl`、`state` 等关键参数，**必须由辅助脚本动态生成**。Agent 自行拼接的链接几乎必定出错。

**Check**: 授权链接**只能**从 `python3 scripts/tccli-oauth-helper.py --get-url` 的输出中原样获取，一个字符都不能改。

### 使用占位符假装执行成功

**Check**: 用户未提供 Domain/RecordId 等关键参数时，不使用占位符执行命令。

```bash
# ✅ 正确：向用户索取缺失参数
# "请提供要操作的域名，可通过 tccli dnspod DescribeDomainList 查询"
```

```bash
# ❌ 错误：用占位符直接执行
tccli dnspod DeleteRecord --Domain <domain> --RecordId <id>
# 这会导致 API 报错
```

### 跳过 --help 直接猜参数

**Check**: 对不确定的参数，先用 `--help` 确认。

```bash
# ✅ 正确：先查参数再执行
tccli dnspod CreateRecord --help
```

```bash
# ❌ 错误：凭记忆拼参数——可能参数名已变更或格式不对
tccli dnspod CreateRecord --Domain example.com --Type A --Host www --IP 1.2.3.4
# 参数名不对：应该是 RecordType、SubDomain、Value
```

### 不区分查询和写操作

**Check**: 能先 `Describe` 的，不直接 `Create` / `Modify` / `Delete`。

```bash
# ✅ 正确：先查再改
tccli dnspod DescribeRecordList --Domain example.com
# 确认记录后再执行修改/删除操作
```

```bash
# ❌ 错误：直接删除，不先查看当前记录
tccli dnspod DeleteRecord --Domain example.com --RecordId 123456
# 可能删错记录，导致 **域名解析中断**
```

### DNS 已正确时重复修改 DNS 服务器（⛔ 严重错误）

**Check**: 修改域名 DNS 服务器前，**必须**先查询 `DescribeDomain` 对比 `EffectiveDNS` 和 `DnspodNsList`，仅在不一致时才修改。

修改 DNS 服务器的全球生效时间为 0 - 48 小时。如果 DNS 已正确指向腾讯云，重复修改会导致不必要的生效等待，甚至引发解析中断。

```bash
# ✅ 正确：先查询 DNS 状态，对比后再决定
tccli dnspod DescribeDomain --Domain example.com
# 对比 EffectiveDNS 和 DnspodNsList
# → 一致：无需修改，直接跳过
# → 不一致：执行修改
```

```bash
# ❌ 错误：不查询直接引导用户修改 DNS 服务器
# "请到域名注册商处将 DNS 服务器修改为 f1g1ns1.dnspod.net"
# DNS 可能已经是正确的，重复修改会触发 0-48 小时的全球刷新等待
```

### 修改记录时遗漏必填参数

**Check**: `ModifyRecord` 需要同时提供 `RecordType`、`RecordLine`、`Value` 等参数，即使只想改其中一个值。

```bash
# ✅ 正确：提供所有必填参数
tccli dnspod ModifyRecord \
  --Domain example.com \
  --RecordId 123456 \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 5.6.7.8
```

```bash
# ❌ 错误：只提供要修改的字段
tccli dnspod ModifyRecord --Domain example.com --RecordId 123456 --Value 5.6.7.8
# 缺少 RecordType、RecordLine 等必填参数，会报错
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 如何查看所有 DNSPod 支持的操作？ | `tccli dnspod --help` |
| 命令执行失败？ | 检查凭证有效性、用 `--help` 确认参数 |
| 如何退出登录/切换账号？ | `tccli auth logout`，然后重新登录 |
| 如何查看某条记录的 RecordId？ | `tccli dnspod DescribeRecordList --Domain <domain>` 返回结果中包含 RecordId |
| 如何按子域名过滤记录？ | `tccli dnspod DescribeRecordList --Domain <domain> --Subdomain <sub>` |
| 如何查看可用的记录线路？ | `tccli dnspod DescribeRecordLineCategoryList --Domain <domain>` |
| 记录添加后多久生效？ | 取决于 TTL 设置和各地 DNS 缓存刷新，通常几分钟到 72 小时不等 |
| 如何批量操作？ | 使用 `CreateRecordBatch` / `ModifyRecordBatch`，先用 `--help` 查看参数格式 |

---

## 关键词

Search: `DescribeDomainList`, `DescribeRecordList`, `CreateRecord`, `ModifyRecord`,
`DeleteRecord`, `ModifyRecordStatus`, `ModifyRecordRemark`, `CreateRecordBatch`,
`ModifyRecordBatch`, `DescribeRecordLineCategoryList`, `DescribeDomain`,
`CreateDomain`, `ModifyDomainDNSBatch`,
`tccli`, `DNSPod`, `DNS`, `解析记录`, `A记录`, `CNAME`, `MX`, `TXT`,
`NS`, `AAAA`, `SRV`, `CAA`, `TTL`, `域名解析`, `记录线路`,
`添加域名解析`, `快速添加域名解析`, `新域名接入`,
`修改DNS服务器`, `DNS服务器`, `未使用云解析DNS地址`,
`退出登录`, `logout`, `切换账号`, `清除凭证`

---

## Reference 文件

- [解析记录增删改查](references/dnspod-record-management.md) — 域名列表查询、解析记录的查询/添加/修改/删除、记录状态管理
- [智能解析配置](references/dnspod-smart-resolution.md) — 按运营商/地域/境内外分线路智能解析配置
- [域名健康巡检](references/dnspod-domain-healthcheck.md) — 域名状态检查、DNS 解析验证、HTTP 可用性检查、SSL 证书检查
- [添加域名解析](references/dnspod-add-domain-resolution.md) — 添加域名、添加解析记录、修改域名 DNS 服务器

---

**版本**：v1.0.0
**最后更新**：2026-04-08
