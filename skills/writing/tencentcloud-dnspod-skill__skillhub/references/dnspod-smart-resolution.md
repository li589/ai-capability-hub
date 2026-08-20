# DNS 解析实现智能解析

你对腾讯云 DNSPod 智能解析相关 API 的参数可能已过时。
**执行前请先用 `tccli dnspod <操作> --help` 确认最新参数。**

> 利用「腾讯云解析 DNS（DNSPod）管理工具」Skill 实现基于线路的智能 DNS 解析。
>
> 📖 **参考文档**：https://cloud.tencent.com/document/product/302/44466

---

## 概述

智能解析是指 DNS 服务器根据访问者的来源（运营商、地域、境内/境外），自动返回不同的 IP 地址，从而实现就近接入、跨网加速或访问限制等目标。

**核心原理**：为同一主机记录（如 `www`）添加多条解析记录，每条记录指定不同的线路类型（如"电信"、"移动"、"境外"等），DNS 系统会自动识别访问者的 Local DNS IP 归属地，返回对应线路的 IP 地址。

**前提条件**：
- 拥有一个已在 DNSPod 管理的域名
- 准备好不同运营商或地域对应的服务器 IP 地址
- 必须设置一条**"默认"线路**记录作为兜底（当访问者不匹配任何特定线路时使用）

---

## 场景一：境内跨运营商/跨地区智能解析

### 任务描述

为域名配置智能解析，让不同运营商（电信/联通/移动等）的用户访问时，自动解析到对应运营商的服务器 IP，解决跨网访问速度慢的问题。

### 执行步骤

1. 使用 `tccli dnspod DescribeDomainList` 确认域名已在 DNSPod 管理
2. 使用 `tccli dnspod DescribeRecordList --Domain <domain>` 查看现有解析记录
3. 使用 `tccli dnspod DescribeRecordLineCategoryList --Domain <domain>` 查看域名支持的线路列表
4. 为同一主机记录添加多条 A 记录，每条使用不同的线路类型：

```bash
# 第一条：默认线路（必须设置，作为兜底）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.1.1.1

# 第二条：移动线路
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 移动 \
  --Value 2.2.2.2

# 第三条：电信线路
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 电信 \
  --Value 3.3.3.3

# 第四条：联通线路
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 联通 \
  --Value 4.4.4.4
```

5. 使用 `tccli dnspod DescribeRecordList --Domain <domain>` 验证记录已正确添加

### 实现效果

| 访问者运营商 | 解析结果 |
|------------|---------|
| 移动用户 | → `2.2.2.2`（移动线路） |
| 电信用户 | → `3.3.3.3`（电信线路） |
| 联通用户 | → `4.4.4.4`（联通线路） |
| 其他用户（如教育网等） | → `1.1.1.1`（默认线路兜底） |

---

## 场景二：全球范围境内外智能解析

### 任务描述

为域名配置智能解析，区分境内和境外用户，分别引导至不同的服务器，优化全球用户的访问体验。

### 执行步骤

1. 使用 `tccli dnspod DescribeDomainList` 确认域名已在 DNSPod 管理
2. 使用 `tccli dnspod DescribeRecordList --Domain <domain>` 查看现有解析记录
3. 为同一主机记录添加两条 A 记录：

```bash
# 第一条：默认线路（境内用户）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 2.2.2.2

# 第二条：境外线路（境外用户）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 境外 \
  --Value 1.1.1.1
```

4. 使用 `tccli dnspod DescribeRecordList --Domain <domain>` 验证记录已正确添加

### 实现效果

| 访问者来源 | 解析结果 |
|-----------|---------|
| 境内用户 | → `2.2.2.2`（默认线路，指向境内服务器） |
| 境外用户 | → `1.1.1.1`（境外线路，指向境外服务器） |

---

## 场景三：通过智能解析限制特定访问

### 任务描述

通过智能解析屏蔽特定运营商或地域的用户访问，例如屏蔽境外访问。

### 执行步骤

1. 使用 `tccli dnspod DescribeDomainList` 确认域名已在 DNSPod 管理
2. 使用 `tccli dnspod DescribeRecordList --Domain <domain>` 查看现有解析记录
3. 为同一主机记录添加两条 A 记录：

```bash
# 第一条：默认线路（正常访问）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 2.2.2.2

# 第二条：境外线路（指向不可达地址，实现屏蔽）
tccli dnspod CreateRecord --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 境外 \
  --Value 127.0.0.1
```

4. 使用 `tccli dnspod DescribeRecordList --Domain <domain>` 验证记录已正确添加

### 实现效果

| 访问者来源 | 解析结果 |
|-----------|---------|
| 境内用户 | → `2.2.2.2`（正常访问） |
| 境外用户 | → `127.0.0.1`（无法访问，被屏蔽） |

> ⚠️ **注意**：此方法是在 DNS 层面进行屏蔽，并非绝对安全。境外用户如果直接使用 IP 访问或配置了其他 DNS 服务器，仍可能绕过此限制。如需更严格的访问控制，建议配合安全组或 Web 应用防火墙（WAF）使用。

---

## 常用线路类型

| 线路名称 | 说明 |
|---------|------|
| `默认` | 兜底线路，**必须设置**，匹配所有未命中特定线路的访问者 |
| `电信` | 中国电信用户 |
| `联通` | 中国联通用户 |
| `移动` | 中国移动用户 |
| `铁通` | 中国铁通用户 |
| `教育网` | 教育网用户 |
| `境外` | 境外访问者 |
| `百度` | 百度爬虫 |
| `谷歌` | 谷歌爬虫 |
| `搜搜` | 搜搜爬虫 |
| `有道` | 有道爬虫 |
| `必应` | 必应爬虫 |
| `搜狗` | 搜狗爬虫 |
| `奇虎` | 奇虎爬虫 |

> 💡 **提示**：不同套餐版本支持的线路细分程度不同。免费版支持基础线路（运营商级别），付费版支持更细粒度的线路（如省份级别）。可通过 `tccli dnspod DescribeRecordLineCategoryList --Domain <domain>` 查看当前域名支持的完整线路列表。

> ⚠️ **关键规则**：`RecordLine` 参数必须使用**中文**线路名称（如"默认"、"电信"、"境外"），**不能**使用英文（如 "default"、"telecom"、"overseas"），否则 API 会报错。

---

## API 速查

| 功能 | 接口 | 说明 |
|------|------|------|
| 查询域名列表 | `DescribeDomainList` | 获取账户下所有域名 |
| 查询解析记录 | `DescribeRecordList` | 获取指定域名的所有解析记录 |
| 查询支持线路 | `DescribeRecordLineCategoryList` | 获取域名支持的线路类型列表 |
| 添加解析记录 | `CreateRecord` | 添加一条新的解析记录 |
| 修改解析记录 | `ModifyRecord` | 修改已有的解析记录 |
| 删除解析记录 | `DeleteRecord` | 删除一条解析记录 |
| 查询单条记录 | `DescribeRecord` | 获取单条记录的详细信息 |
| 批量添加记录 | `CreateRecordBatch` | 批量添加多条解析记录 |

---

## 注意事项

1. **必须设置默认线路**：智能解析配置中，"默认"线路记录是必须的，作为兜底策略。如果没有默认线路，未匹配到特定线路的用户将无法解析。
2. **TTL 生效时间**：修改解析记录后，虽然 DNS 服务器会实时同步，但由于各地 DNS 缓存的存在，全球完全生效需要等待 TTL 过期（默认 600 秒 = 10 分钟）。
3. **套餐限制**：免费版支持基础线路（运营商级别），如需省份级别的细粒度线路，需要升级到付费套餐。
4. **记录冲突**：同一主机记录下，相同线路类型只能有一条同类型记录。例如，不能为 `www` 的"电信"线路添加两条 A 记录。
5. **先查后改**：执行修改或删除操作前，务必先用 `DescribeRecordList` 查看现有记录，确认要操作的记录信息。
