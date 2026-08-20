# DNSPod 解析记录增删改查

本文档描述通过 tccli 对 DNSPod 解析记录进行增删改查的标准操作流程。

---

## 前置条件

- tccli 已安装并配置凭证（OAuth 或 AK/SK）
- 用户账号下已有托管在 DNSPod 的域名

---

## 一、查询域名列表

获取当前账号下所有托管域名：

```bash
tccli dnspod DescribeDomainList
```

返回字段说明：
- `DomainList[].Name` — 域名
- `DomainList[].DomainId` — 域名 ID
- `DomainList[].Status` — 域名状态（ENABLE / PAUSE）
- `DomainList[].RecordCount` — 解析记录数量
- `DomainList[].GradeTitle` — 套餐等级

如需按关键词搜索域名：

```bash
tccli dnspod DescribeDomainList --Keyword "example"
```

---

## 二、查询解析记录

### 查看某域名的所有记录

```bash
tccli dnspod DescribeRecordList --Domain example.com
```

返回字段说明：
- `RecordList[].RecordId` — 记录 ID（修改/删除时需要）
- `RecordList[].Name` — 主机记录（子域名，如 www、@、mail）
- `RecordList[].Type` — 记录类型（A、CNAME、MX、TXT 等）
- `RecordList[].Value` — 记录值
- `RecordList[].Line` — 线路（默认、电信、联通等）
- `RecordList[].TTL` — TTL 值
- `RecordList[].Status` — 状态（ENABLE / DISABLE）
- `RecordList[].Weight` — 权重（负载均衡时使用）
- `RecordList[].MX` — MX 优先级（仅 MX 记录）
- `RecordList[].Remark` — 备注

### 按子域名过滤

```bash
tccli dnspod DescribeRecordList --Domain example.com --Subdomain www
```

### 按记录类型过滤

```bash
tccli dnspod DescribeRecordList --Domain example.com --RecordType A
```

### 分页查询

当记录数量较多时，使用分页参数：

```bash
tccli dnspod DescribeRecordList --Domain example.com --Offset 0 --Limit 100
```

### 按关键词搜索

```bash
tccli dnspod DescribeRecordList --Domain example.com --Keyword "mail"
```

---

## 三、添加解析记录

### 基本语法

```bash
tccli dnspod CreateRecord \
  --Domain <域名> \
  --SubDomain <主机记录> \
  --RecordType <记录类型> \
  --RecordLine <线路> \
  --Value <记录值>
```

### 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--Domain` | 域名 | `example.com` |
| `--SubDomain` | 主机记录（子域名） | `www`、`@`、`mail`、`*` |
| `--RecordType` | 记录类型 | `A`、`CNAME`、`MX`、`TXT`、`AAAA`、`NS`、`SRV`、`CAA` |
| `--RecordLine` | 记录线路 | `默认`、`电信`、`联通`、`移动`、`海外` |
| `--Value` | 记录值 | IP 地址、域名、文本等 |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--TTL` | TTL 值（秒） | 600 |
| `--MX` | MX 优先级（仅 MX 记录） | 无 |
| `--Weight` | 权重（0-100） | 无 |
| `--Status` | 记录状态 | `ENABLE` |
| `--Remark` | 备注 | 无 |

### 示例

#### 添加 A 记录

```bash
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.2.3.4
```

#### 添加 CNAME 记录

```bash
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain cdn \
  --RecordType CNAME \
  --RecordLine 默认 \
  --Value cdn.provider.com
```

#### 添加 MX 记录

```bash
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain @ \
  --RecordType MX \
  --RecordLine 默认 \
  --Value mail.example.com \
  --MX 10
```

#### 添加 TXT 记录（域名验证）

```bash
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain @ \
  --RecordType TXT \
  --RecordLine 默认 \
  --Value "v=spf1 include:spf.mail.example.com ~all"
```

#### 添加 AAAA 记录（IPv6）

```bash
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain www \
  --RecordType AAAA \
  --RecordLine 默认 \
  --Value 2001:db8::1
```

#### 添加泛解析记录

```bash
tccli dnspod CreateRecord \
  --Domain example.com \
  --SubDomain "*" \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.2.3.4
```

---

## 四、修改解析记录

> ⚠️ **高危操作**：修改记录会变更域名解析指向，可能影响正在访问该域名的用户。执行前必须二次确认。

### 基本语法

```bash
tccli dnspod ModifyRecord \
  --Domain <域名> \
  --RecordId <记录ID> \
  --SubDomain <主机记录> \
  --RecordType <记录类型> \
  --RecordLine <线路> \
  --Value <新记录值>
```

### 必填参数

| 参数 | 说明 |
|------|------|
| `--Domain` | 域名 |
| `--RecordId` | 记录 ID（通过 DescribeRecordList 获取） |
| `--SubDomain` | 主机记录 |
| `--RecordType` | 记录类型 |
| `--RecordLine` | 记录线路 |
| `--Value` | 新的记录值 |

> ⚠️ **注意**：即使只想修改 Value，也必须同时提供 `RecordType`、`RecordLine`、`SubDomain` 等必填参数，否则 API 会报错。建议先查询当前记录，获取完整信息后再修改。

### 标准操作流程

```bash
# 第一步：查询当前记录，获取 RecordId 和其他字段
tccli dnspod DescribeRecordList --Domain example.com --Subdomain www

# 第二步：确认修改内容后执行（假设 RecordId 为 123456）
tccli dnspod ModifyRecord \
  --Domain example.com \
  --RecordId 123456 \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 5.6.7.8
```

### 修改 TTL

```bash
tccli dnspod ModifyRecord \
  --Domain example.com \
  --RecordId 123456 \
  --SubDomain www \
  --RecordType A \
  --RecordLine 默认 \
  --Value 1.2.3.4 \
  --TTL 300
```

---

## 五、删除解析记录

> ⚠️ **高危操作**：删除记录将导致对应域名无法解析，可能影响网站访问。执行前必须二次确认。

### 基本语法

```bash
tccli dnspod DeleteRecord --Domain <域名> --RecordId <记录ID>
```

### 标准操作流程

```bash
# 第一步：查询确认要删除的记录
tccli dnspod DescribeRecordList --Domain example.com --Subdomain test

# 第二步：确认后删除
tccli dnspod DeleteRecord --Domain example.com --RecordId 789012
```

---

## 六、修改记录状态（启用/暂停）

暂停记录不会删除记录，但会使其暂时不生效：

```bash
# 暂停记录
tccli dnspod ModifyRecordStatus \
  --Domain example.com \
  --RecordId 123456 \
  --Status DISABLE

# 启用记录
tccli dnspod ModifyRecordStatus \
  --Domain example.com \
  --RecordId 123456 \
  --Status ENABLE
```

---

## 七、修改记录备注

```bash
tccli dnspod ModifyRecordRemark \
  --Domain example.com \
  --RecordId 123456 \
  --Remark "生产环境主站"
```

---

## 八、查看可用线路

不同套餐等级支持的线路不同，查询当前域名可用的线路列表：

```bash
tccli dnspod DescribeRecordLineCategoryList --Domain example.com
```

常见线路值：
- `默认` — 所有未匹配到特定线路的请求
- `电信` / `联通` / `移动` — 运营商线路
- `海外` — 海外访问
- `百度` / `谷歌` / `搜搜` — 搜索引擎线路（部分套餐支持）

---

## 常见错误

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `InvalidParameter.DomainInvalid` | 域名不存在或未托管 | 检查域名是否在账号下 |
| `InvalidParameter.RecordIdInvalid` | RecordId 不存在 | 重新查询获取正确的 RecordId |
| `InvalidParameter.RecordLineInvalid` | 线路不支持 | 用 DescribeRecordLineCategoryList 查询可用线路 |
| `InvalidParameter.RecordTypeInvalid` | 记录类型不支持 | 检查记录类型拼写 |
| `InvalidParameter.RecordValueInvalid` | 记录值格式错误 | 检查 Value 格式（如 A 记录必须是 IP） |
| `LimitExceeded.RecordCountLimit` | 记录数量超限 | 升级套餐或删除不需要的记录 |
| `InvalidParameter.RecordConflict` | 记录冲突 | CNAME 记录不能与其他类型共存 |
