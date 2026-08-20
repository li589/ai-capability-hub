# 添加域名解析

本文档指导如何通过 tccli 完成域名解析的添加，以及当 DNS 服务器地址不正确时如何修改。

> 📖 参考文档：
> - [快速添加域名解析](https://cloud.tencent.com/document/product/302/3446)
> - [修改域名 DNS 服务器](https://cloud.tencent.com/document/product/302/5518)

---

## 场景概览

```
用户想添加域名解析
├─ 步骤 1：添加域名到 DNSPod（非腾讯云注册的域名需要此步骤）
├─ 步骤 2：添加解析记录（A / CNAME / MX 等）
├─ 步骤 3：查询 DNS 服务器状态并判断（⚠️ 必须先查再决定）
│   ├─ EffectiveDNS 与 DnspodNsList 一致 → ✅ 已正确，跳过修改，直接到步骤 4
│   └─ EffectiveDNS 与 DnspodNsList 不一致 → ❌ 需要修改域名 DNS 服务器
└─ 步骤 4：等待解析生效（全球生效需 0 - 48 小时）
```

---

## 步骤 1：添加域名到 DNSPod

### 适用场景
- 域名**不是**在腾讯云注册的（第三方注册商如阿里云、GoDaddy 等）
- 域名尚未出现在 DNSPod 解析列表中

> 💡 如果域名已在腾讯云注册，系统会自动将其添加到 DNS 解析列表，可跳过此步。

### 操作步骤

**先检查域名是否已在列表中**：

```bash
tccli dnspod DescribeDomainList
```

如果目标域名不在返回列表中，执行添加：

```bash
tccli dnspod CreateDomain --Domain <域名>
```

> ⚠️ 使用前先确认参数：
> ```bash
> tccli dnspod CreateDomain --help
> ```

添加成功后，再次确认域名已在列表中：

```bash
tccli dnspod DescribeDomainList
```

---

## 步骤 2：添加解析记录

域名添加成功后，需要添加具体的解析记录。

### 网站解析（最常见）

通常需要添加 `www` 和 `@` 两条 A 记录，使 `www.example.com` 和 `example.com` 都能访问：

```bash
# 添加 www 记录（www.example.com → IP）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value <网站服务器IP>

# 添加 @ 记录（example.com → IP）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain @ \
  --RecordType A \
  --RecordLine 默认 \
  --Value <网站服务器IP>
```

### 其他常见解析类型

| 解析类型 | 用途 | 示例 |
|---------|------|------|
| A | 将域名指向 IPv4 地址 | `--RecordType A --Value 1.2.3.4` |
| AAAA | 将域名指向 IPv6 地址 | `--RecordType AAAA --Value 2001:db8::1` |
| CNAME | 将域名指向另一个域名 | `--RecordType CNAME --Value cdn.example.com` |
| MX | 邮箱解析，指向邮件服务器 | `--RecordType MX --Value mail.example.com --MX 10` |
| TXT | 文本记录，常用于验证 | `--RecordType TXT --Value "v=spf1 ..."` |
| NS | 指定子域名的 DNS 服务器 | `--RecordType NS --Value ns1.example.com` |
| SRV | 服务定位记录 | `--RecordType SRV --Value "..."` |

### 邮箱解析

如果需要配置企业邮箱，需要添加 MX 记录。不同邮箱厂商的配置值不同，请参考对应邮箱厂商的文档获取 MX 记录值。

```bash
# 示例：添加 MX 记录
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain @ \
  --RecordType MX \
  --RecordLine 默认 \
  --Value <邮件服务器地址> \
  --MX <优先级数值>
```

### 添加记录后验证

```bash
# 查看已添加的解析记录
tccli dnspod DescribeRecordList --Domain <域名>
```

---

## 步骤 3：检查 DNS 服务器状态（⚠️ 必须先查再决定）

解析记录添加完成后，必须确保域名的 DNS 服务器地址指向腾讯云 DNS，否则解析不会生效。

> ⛔⛔⛔ **最高优先级规则：禁止重复修改 DNS 服务器**
>
> 修改域名 DNS 服务器的全球生效时间为 **0 - 48 小时**，期间部分地区可能无法解析。
> **如果域名的 DNS 服务器已经指向腾讯云 DNS，重复修改会导致不必要的生效等待，甚至引发解析中断。**
>
> **你必须严格按照以下流程操作：先查询 → 再判断 → 仅在确认不一致时才修改。**

### 第一步：查询 DNS 状态（必须执行）

```bash
tccli dnspod DescribeDomain --Domain <域名>
```

在返回结果中检查以下关键字段：
- `DnspodNsList`：腾讯云分配的 DNS 服务器地址（**应该使用的地址**）
- `EffectiveDNS`：域名当前实际使用的 DNS 服务器地址

### 第二步：判断是否需要修改（必须判断）

```
查询结果判断：
├─ EffectiveDNS 包含 DnspodNsList 中的地址（如都含 *.dnspod.net 或 *.tencentcns.com）
│   → ✅ DNS 服务器已正确，**无需任何修改，直接跳到步骤 4 等待生效**
│   → ⛔ 不要输出任何关于"修改DNS服务器"或"下一步"的提示
│
└─ EffectiveDNS 与 DnspodNsList 不一致（如指向其他注册商的 NS）
    → ❌ DNS 服务器不正确，需要修改（继续执行下方"第三步"）
    → 仅此情况下才在操作摘要中提示用户修改 DNS 服务器
```

**判断示例**：

| EffectiveDNS | DnspodNsList | 是否需要修改 |
|-------------|-------------|------------|
| `["f1g1ns1.dnspod.net","f1g1ns2.dnspod.net"]` | `["f1g1ns1.dnspod.net","f1g1ns2.dnspod.net"]` | ❌ **不需要**，已一致 |
| `["dns1.tencentcns.com","dns2.tencentcns.com"]` | `["dns1.tencentcns.com","dns2.tencentcns.com"]` | ❌ **不需要**，已一致 |
| `["ns1.alidns.com","ns2.alidns.com"]` | `["f1g1ns1.dnspod.net","f1g1ns2.dnspod.net"]` | ✅ **需要修改** |
| `["ns1.godaddy.com","ns2.godaddy.com"]` | `["f1g1ns1.dnspod.net","f1g1ns2.dnspod.net"]` | ✅ **需要修改** |

> 💡 **关键**：只要 `EffectiveDNS` 中的地址已经包含在 `DnspodNsList` 中，就说明 DNS 服务器已正确指向腾讯云，**绝对不要再执行修改操作，也不要在输出中提示用户去修改**。

### 操作完成后的输出规范（⚠️ 必须遵守）

根据第二步的判断结果，操作摘要中 DNS 服务器相关内容**必须区分呈现**：

**✅ DNS 已正确（EffectiveDNS 与 DnspodNsList 一致）时的输出**：

```
✅ 已完成！以下是操作摘要：

| 操作 | 结果 |
|------|------|
| 添加域名 | example.com (DomainId: xxx) |
| 添加解析记录 | @ → 1.2.3.4 (A 记录, RecordId: xxx) |
| DNS 服务器 | ✅ 已正确指向腾讯云 DNS (xxx.dnspod.net) |

域名解析配置已全部完成，无需额外操作。
```

> ⛔ 此情况下**绝对不要**输出：
> - "下一步"、"你需要修改DNS服务器" 等引导修改的提示
> - "等待 DNS 生效"、"可能需要等待"、"约几分钟到几小时" 等暗示 DNS 未就绪的描述
>
> DNS 服务器已正确 = 不需要修改 = 不存在修改后的生效等待。直接告知"已全部完成"即可。

**❌ DNS 不正确（EffectiveDNS 与 DnspodNsList 不一致）时的输出**：

```
✅ 已完成！以下是操作摘要：

| 操作 | 结果 |
|------|------|
| 添加域名 | example.com (DomainId: xxx) |
| 添加解析记录 | @ → 1.2.3.4 (A 记录, RecordId: xxx) |
| DNS 服务器 | ⚠️ 需要修改 (当前: ns1.alidns.com, 应改为: xxx.dnspod.net) |

⚠ 下一步：你需要在域名注册商处将 DNS 服务器修改为以上地址，解析才会生效。通常需要 0-48 小时全球生效。
```

> 仅在此情况下才输出"下一步"修改提示。

### 第三步：修改 DNS 服务器（仅在第二步判断为"需要修改"时执行）

> ⚠️ **再次确认**：执行修改前，请回顾第二步的判断结果。如果 DNS 已指向腾讯云，**立即停止，不要修改**。

修改 DNS 服务器需要在**域名注册商处**操作，根据域名注册位置分为两种情况：

#### 情况一：域名在腾讯云注册

可以通过 tccli 使用域名注册接口修改：

```bash
# 先查看帮助确认参数
tccli domain ModifyDomainDNSBatch --help
```

也可以引导用户在腾讯云域名注册控制台操作：

1. 登录 [腾讯云域名注册控制台](https://console.cloud.tencent.com/domain)
2. 选择域名 → 更多 → 修改 DNS 服务器
3. 选择"使用 DNSPod"，系统会自动匹配正确的 DNS 地址
4. 提交修改

#### 情况二：域名在其他注册商注册（如阿里云、GoDaddy 等）

需要引导用户到对应注册商的管理页面修改 DNS 服务器：

1. 先通过 tccli 获取正确的 DNS 服务器地址（如果前面已查询可直接使用）：
   ```bash
   tccli dnspod DescribeDomain --Domain <域名>
   ```
   从返回结果的 `DnspodNsList` 字段获取 DNS 地址。

2. 告知用户需要修改的 DNS 地址，并引导操作：
   ```
   您的域名需要将 DNS 服务器修改为以下地址：
   - <DnspodNsList 中的地址1>
   - <DnspodNsList 中的地址2>

   请登录您的域名注册商控制台，找到 DNS 服务器修改设置，
   将 DNS 服务器替换为上述地址。
   ```

> ⚠️ **重要提示**：
> - 不同解析套餐（免费版 / 专业版 / 企业版等）对应的 DNS 服务器地址不同
> - 修改 DNS 服务器后，全球生效通常需要 **0 - 48 小时**
> - 修改期间，部分地区可能暂时无法解析
> - **因此，仅在 DNS 确实不正确时才修改，避免不必要的生效等待**

---

## 步骤 4：等待解析生效

完成以上步骤后，需要等待解析在全球范围内生效。

### 生效时间

- **修改解析记录**：修改后实时同步到 DNS 服务器，但受各地 DNS 缓存 TTL 影响
- **修改 DNS 服务器**：全球 DNS 刷新通常需要 **0 - 48 小时**

### 验证解析是否生效

可以使用以下方式验证：

```bash
# Linux/macOS
dig <域名>
nslookup <域名>

# Windows
nslookup <域名>
```

如果返回的 IP 地址与设置的记录值一致，说明解析已生效。

---

## 完整端到端示例

以下是一个完整的添加域名解析流程示例：

```bash
# 1. 检查域名是否已在 DNSPod 列表中
tccli dnspod DescribeDomainList

# 2. 添加域名（如果不在列表中）
tccli dnspod CreateDomain --Domain example.com

# 3. 添加网站解析记录
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.2.3.4

tccli dnspod CreateRecord --Domain example.com \
  --SubDomain @ \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.2.3.4

# 4. 验证解析记录已添加
tccli dnspod DescribeRecordList --Domain example.com

# 5. 查询 DNS 服务器状态（⚠️ 必须执行此步骤）
tccli dnspod DescribeDomain --Domain example.com
# 对比返回结果中的 DnspodNsList 和 EffectiveDNS：
#
#   ✅ 如果一致（如都是 *.dnspod.net）：
#      → DNS 已正确，无需修改，直接等待生效
#      → 操作摘要中不要输出"下一步"修改提示，只需告知"DNS 服务器已正确"
#
#   ❌ 如果不一致：
#      → 需要到域名注册商处修改 DNS 服务器（见步骤 3 详细说明）
#      → 仅此时才在操作摘要中输出"下一步"修改 DNS 服务器的提示

# 6. 等待生效后验证
nslookup example.com
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 添加域名失败？ | 检查域名格式是否正确，是否已被其他账号添加 |
| 添加记录后解析不生效？ | 检查 DNS 服务器是否已修改为腾讯云 DNS 地址 |
| DNS 服务器修改后仍不生效？ | 全球 DNS 刷新需要 0-48 小时，请耐心等待 |
| 如何查看正确的 DNS 地址？ | `tccli dnspod DescribeDomain --Domain <域名>` 查看 `DnspodNsList` 字段 |
| 域名不是腾讯云注册的怎么办？ | 需要到域名注册商控制台修改 DNS 服务器 |
| 不同套餐 DNS 地址不同？ | 参考 [各套餐 DNS 服务器地址说明](https://cloud.tencent.com/document/product/302/79833) |
