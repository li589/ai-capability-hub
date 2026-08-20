# DNSPod 域名健康巡检

本文档描述如何通过 tccli 结合系统命令（whois、dig、curl、openssl）对域名进行全方位健康巡检。

> 💡 **适用场景**：定时巡检域名状态、DNS 解析、网站可用性、SSL 证书有效期，及时发现异常。
> 本文档专注于巡检命令和判断逻辑，不涉及 Webhook 推送。

---

## 概述

域名健康巡检包含 4 个维度：

| 巡检项 | 检查工具 | 检查内容 | 异常影响 |
|--------|---------|---------|---------|
| ① 域名状态 | `whois` + `tccli` | 域名是否被 Hold（冻结） | 域名完全无法解析 |
| ② DNS 解析 | `dig` / `nslookup` + `tccli` | A 记录是否正确返回 | 网站无法访问 |
| ③ HTTP 可用性 | `curl` | HTTP 状态码是否正常 | 网站服务异常 |
| ④ SSL 证书 | `openssl` | 证书是否过期或即将过期 | 浏览器安全警告、HTTPS 不可用 |

---

## 一、域名状态检查

### 1.1 通过 tccli 查询域名信息

```bash
tccli dnspod DescribeDomain --Domain example.com
```

关注返回字段：
- `DomainInfo.Status` — 域名状态（`ENABLE` 正常 / `PAUSE` 暂停）
- `DomainInfo.DNSStatus` — DNS 设置状态（NS 记录是否正确指向 DNSPod）

### 1.2 通过 whois 检查域名注册状态

```bash
whois example.com | grep -i "status"
```

**正常状态**（至少包含以下之一）：
- `clientTransferProhibited` — 禁止转移（正常保护状态）
- `ok` — 正常

**异常状态**（需要立即关注）：

| 状态 | 含义 | 紧急程度 |
|------|------|---------|
| `clientHold` | **注册商暂停解析** — 通常因未实名认证、违规等 | 🔴 紧急 |
| `serverHold` | **注册局暂停解析** — 通常因司法冻结、争议等 | 🔴 紧急 |
| `pendingDelete` | 域名即将被删除 | 🔴 紧急 |
| `redemptionPeriod` | 域名赎回期 | 🟡 警告 |

### 1.3 检查域名过期时间

```bash
whois example.com | grep -i "expir"
```

输出示例：
```
Registry Expiry Date: 2027-03-15T08:00:00Z
```

**判断逻辑**：
- 过期时间 ≤ 30 天 → 🔴 **紧急**：域名即将过期，需立即续费
- 过期时间 ≤ 90 天 → 🟡 **警告**：建议尽快续费
- 过期时间 > 90 天 → ✅ **正常**

---

## 二、DNS 解析检查

### 2.1 通过 tccli 查询 DNSPod 配置的记录

```bash
tccli dnspod DescribeRecordList --Domain example.com --Subdomain www --RecordType A
```

此命令查询的是 **DNSPod 服务端配置的记录**，即"应该解析到什么"。

### 2.2 通过 dig 验证实际解析结果

```bash
dig example.com A +short
```

或指定子域名：

```bash
dig www.example.com A +short
```

此命令查询的是 **实际 DNS 解析返回的结果**，即"真正解析到了什么"。

### 2.3 对比验证

**判断逻辑**：
1. 先用 tccli 获取 DNSPod 上配置的预期 IP
2. 再用 dig 获取实际解析的 IP
3. 对比两者是否一致

```bash
# 获取预期值（DNSPod 配置）
tccli dnspod DescribeRecordList --Domain example.com --Subdomain www --RecordType A

# 获取实际值（DNS 解析结果）
dig www.example.com A +short
```

| 情况 | 含义 | 处理 |
|------|------|------|
| 预期 IP = 实际 IP | ✅ 解析正常 | 无需处理 |
| 预期 IP ≠ 实际 IP | ⚠️ 解析不一致 | 可能是 DNS 缓存未刷新、NS 未正确指向 DNSPod、或被劫持 |
| dig 无返回 | 🔴 解析失败 | 检查域名状态、NS 记录、DNSPod 记录配置 |

### 2.4 检查 NS 记录是否正确

```bash
dig example.com NS +short
```

正常情况应返回 DNSPod 的 NS 服务器（如 `*.dnspod.net`）。如果 NS 不是 DNSPod 的，说明域名的 DNS 服务器未正确指向 DNSPod，DNSPod 上的记录配置不会生效。

### 2.5 指定 DNS 服务器查询（排除缓存干扰）

```bash
# 直接查询 DNSPod 的 NS 服务器，绕过本地缓存
dig www.example.com A @ns1.dnspod.net +short
```

---

## 三、HTTP 可用性检查

### 3.1 检查 HTTP 状态码

```bash
curl -I -s -o /dev/null -w "%{http_code}" https://example.com
```

参数说明：
- `-I` — 只获取 HTTP 头
- `-s` — 静默模式
- `-o /dev/null` — 丢弃响应体
- `-w "%{http_code}"` — 只输出状态码

### 3.2 带超时的检查

```bash
curl -I -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 https://example.com
```

### 3.3 同时检查 HTTP 和 HTTPS

```bash
# 检查 HTTP
curl -I -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://example.com

# 检查 HTTPS
curl -I -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://example.com
```

### 3.4 状态码判断

| 状态码 | 含义 | 判断 |
|--------|------|------|
| `200` | 正常 | ✅ 正常 |
| `301` / `302` | 重定向 | ✅ 正常（如 HTTP→HTTPS 跳转） |
| `403` | 禁止访问 | ⚠️ 警告：可能是配置问题 |
| `404` | 页面不存在 | ⚠️ 警告：首页 404 说明站点配置异常 |
| `500` / `502` / `503` | 服务器错误 | 🔴 异常：服务端故障 |
| `000` 或超时 | 无法连接 | 🔴 异常：服务不可达 |

### 3.5 获取更详细的信息

```bash
curl -I -s --connect-timeout 10 https://example.com
```

可以查看完整的响应头，包括 Server、Content-Type、重定向目标等。

---

## 四、SSL 证书检查

### 4.1 查看证书有效期

```bash
echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

输出示例：
```
notBefore=Jan 15 00:00:00 2026 GMT
notAfter=Apr 15 23:59:59 2026 GMT
```

### 4.2 查看证书剩余天数

```bash
echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2
```

然后可以计算剩余天数：

```bash
expiry_date=$(echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry_date" +%s 2>/dev/null)
current_epoch=$(date +%s)
days_left=$(( (expiry_epoch - current_epoch) / 86400 ))
echo "证书剩余 ${days_left} 天"
```

> 💡 **注意**：macOS 和 Linux 的 `date` 命令语法不同，上面的命令兼容了两种系统。

### 4.3 查看证书详细信息

```bash
echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

输出示例：
```
subject=CN = example.com
issuer=C = US, O = Let's Encrypt, CN = R3
notBefore=Jan 15 00:00:00 2026 GMT
notAfter=Apr 15 23:59:59 2026 GMT
```

### 4.4 证书有效期判断

| 剩余天数 | 判断 | 处理 |
|---------|------|------|
| ≤ 0 天 | 🔴 **已过期** | 立即更换证书 |
| ≤ 7 天 | 🔴 **即将过期** | 紧急更换证书 |
| ≤ 30 天 | 🟡 **警告** | 尽快续期或更换证书 |
| > 30 天 | ✅ **正常** | 无需处理 |

### 4.5 检查子域名的证书

```bash
echo | openssl s_client -servername www.example.com -connect www.example.com:443 2>/dev/null | openssl x509 -noout -dates
```

> ⚠️ **注意**：`-servername` 参数用于 SNI（Server Name Indication），确保获取到正确域名的证书。如果省略此参数，可能获取到服务器默认证书而非目标域名的证书。

---

## 五、完整巡检流程

### 对单个域名执行完整巡检

按以下顺序依次执行 4 项检查：

```
巡检流程：
├─ 1. 域名状态检查
│   ├─ tccli dnspod DescribeDomain --Domain <domain>
│   ├─ whois <domain> | grep -i "status"
│   └─ whois <domain> | grep -i "expir"
│
├─ 2. DNS 解析检查
│   ├─ tccli dnspod DescribeRecordList --Domain <domain>
│   ├─ dig <domain> A +short
│   └─ dig <domain> NS +short
│
├─ 3. HTTP 可用性检查
│   ├─ curl -I -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://<domain>
│   └─ curl -I -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://<domain>
│
└─ 4. SSL 证书检查
    └─ echo | openssl s_client -servername <domain> -connect <domain>:443 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

### 对多个域名批量巡检

先获取域名列表，然后逐个执行巡检：

```bash
# 第一步：获取所有域名
tccli dnspod DescribeDomainList
```

然后对返回的每个域名依次执行上述完整巡检流程。

### 巡检报告输出格式

巡检完成后，按以下格式汇总输出：

```
📊 域名健康巡检报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 巡检时间：2026-04-08 09:00:00
🌐 巡检域名：example.com

1️⃣ 域名状态
   ├─ DNSPod 状态：✅ ENABLE
   ├─ Whois 状态：✅ clientTransferProhibited（正常）
   └─ 过期时间：✅ 2027-03-15（剩余 341 天）

2️⃣ DNS 解析
   ├─ DNSPod 配置：www → A → 1.2.3.4
   ├─ 实际解析：✅ 1.2.3.4（一致）
   └─ NS 记录：✅ ns1.dnspod.net / ns2.dnspod.net

3️⃣ HTTP 可用性
   ├─ HTTP：✅ 301（重定向到 HTTPS，正常）
   └─ HTTPS：✅ 200（正常）

4️⃣ SSL 证书
   ├─ 颁发者：Let's Encrypt R3
   ├─ 有效期：2026-01-15 ~ 2026-04-15
   └─ 剩余天数：✅ 7 天（⚠️ 即将过期，建议尽快续期）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 汇总：✅ 正常 3 项 | ⚠️ 警告 1 项 | 🔴 异常 0 项
```

---

## 六、常见巡检异常及处理

| 异常 | 可能原因 | 处理建议 |
|------|---------|---------|
| whois 显示 `clientHold` | 域名未实名认证或被注册商暂停 | 联系域名注册商处理 |
| whois 显示 `serverHold` | 域名被注册局冻结（司法、争议等） | 联系注册局或法务处理 |
| 域名即将过期（≤30天） | 未及时续费 | 立即续费域名 |
| dig 无返回 | NS 未指向 DNSPod / 域名被 Hold | 检查域名状态和 NS 配置 |
| dig 结果与 DNSPod 配置不一致 | DNS 缓存 / NS 未切换 / DNS 劫持 | 等待 TTL 过期或检查 NS 记录 |
| curl 返回 000 或超时 | 服务器宕机 / 防火墙拦截 / IP 不可达 | 检查服务器和安全组配置 |
| curl 返回 502/503 | 后端服务异常 | 检查 Web 服务和应用状态 |
| SSL 证书已过期 | 未及时续期 | 立即更换或续期证书 |
| SSL 证书即将过期（≤7天） | 续期流程未完成 | 紧急处理证书续期 |

---

## 七、工具依赖

本巡检功能依赖以下系统命令，执行前请确认已安装：

| 工具 | 用途 | 检查安装 |
|------|------|---------|
| `tccli` | 查询 DNSPod 配置 | `tccli --version` |
| `whois` | 查询域名注册状态 | `whois --version` 或 `which whois` |
| `dig` | DNS 解析验证 | `dig -v` 或 `which dig` |
| `curl` | HTTP 可用性检查 | `curl --version` |
| `openssl` | SSL 证书检查 | `openssl version` |

> 💡 **提示**：
> - macOS 系统通常已预装以上所有工具
> - Linux 系统如缺少 `whois`，可通过 `apt install whois`（Debian/Ubuntu）或 `yum install whois`（CentOS）安装
> - Linux 系统如缺少 `dig`，可通过 `apt install dnsutils`（Debian/Ubuntu）或 `yum install bind-utils`（CentOS）安装
