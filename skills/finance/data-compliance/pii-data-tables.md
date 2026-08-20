# PII 离线数据表使用指引

> 最后核实日期：2026-06-04。表名、项目空间、URL、联系人均为快照，使用前请以下方权威来源为准；区域路由规则会随业务演进调整。

本文件沉淀 ICBU 隐私数据(PII)离线使用指引：快速决策流程、七大使用场景、表清单、区域路由规则、隐私字段清单。

权威来源（内网需 SSO）：
- 最新指引：https://alidocs.dingtalk.com/i/nodes/qnYMoO1rWxrkmoj2IzL5nx6MJ47Z3je9
- 表盘点：https://aliyuque.antfin.com/icbu-fund/xcz623/fg0ti786m32rnfyb?singleDoc

---

## 术语与合规定性（先读）

- 哈希脱敏不等于加密，也不等于匿名化。本文统一用「哈希脱敏 (SHA256)」指代 `PII_DESENSITIZATION(field,'sha256')` 的产出：它是不可逆哈希（无密钥、无法解密），不是可逆加密。为兼容历史叫法，下文有些地方仍写作"加密表"，但技术本质是哈希脱敏。
- 哈希脱敏数据在法律上仍然是个人信息（属假名化/去标识化，不是匿名化）。手机号、邮箱、姓名这类低熵字段即便做了 SHA256，仍可能被彩虹表、字典、枚举反推，所以：
  - "免内部评审"只是说内部取数流程更简便，不代表免除法律义务。
  - 把哈希脱敏数据用于跨境传输、对外/第三方提供、自动化决策时，仍要按个人信息对待，遵守 PIPL 第38条（跨境）、第23条（对外提供）、第24条（自动化决策）等要求。详见 [data-lifecycle.md](data-lifecycle.md)、[regulations.md](regulations.md)。
- 真正的匿名化要求处理后无法识别特定个人且不能复原，单纯哈希通常达不到。需要对外共享或公开时，请走合规评审并咨询法务，别默认"哈希了就安全"。

---

## 一、快速决策流程

拿到新需求后按三问决策：

```
Q1: 能用在线接口解决吗？
├─ 能 → 走在线链路（场景四/五），结束
└─ 不能 → 继续

Q2: 我需要看到明文吗？
├─ 不需要（只做匹配/关联/分析）
│    ├─ 精确匹配（撞库、JOIN 主键）
│    │    ├─ 标准 SHA256 哈希脱敏即可（即下文"加密表"，本质不可逆哈希，下同）→ 场景一
│    │    └─ 需要自定义预处理再哈希脱敏 → 场景二
│    └─ 模糊匹配（文本相似度）→ 场景六（SimHash）
└─ 需要明文（人工审核、监管报送、触达买卖家、明文验证、第三方核查）
     → 场景三（区域明文表，须走合规评审）

Q3: 我的用户在哪个区域？
├─ 只需要单区域数据（推荐）→ 用对应区域表（CN/SG/US/DE）
└─ 需要全量用户数据 → 只能用新加坡全量哈希脱敏表（即全量"加密表"，必须 SG 环境，无全量明文表）
```

> 取数不等于可以随便用。如果取明文是为了触达买卖家（营销/邀约/EDM/外呼/WhatsApp），"能取到联系方式"不等于"能发"——触达本身还要满足同意、退订、拒绝即停、频次等义务，见 [marketing-platform-compliance.md](marketing-platform-compliance.md)（营销红线与圈客规则），并先过滤退订名单（见本文「七、营销退订名单」）。

数据域怎么判断：

- 会员注册信息（姓名、邮箱、手机号等）→ 公域会员表
- 公司注册信息（公司名、法人、税号等）→ 公域公司表
- 其他（合同、认证、CRM、资金、物流、信用证）→ 私域表（场景七）

---

## 二、七大使用场景

### 场景一：精确匹配 / 撞库 / JOIN 主键

> 典型需求：黑名单匹配、团伙精确分析、用邮箱/手机号关联两张表、公司名与人名校验。

这里不用明文，是因为你只需要判断"A 和 B 是否相等"，两边用同样方式加密后密文相等就等于明文相等，效果一样。

单区域加密表（首选）：

| 类型 | 区域 | 加密表 | 项目空间 |
|------|------|---------|------------|
| 会员 | 中国 | `icbu_pii_cn.icbu_pii_privacy_computing_icbu_member_sha256_desensitized_cn_df` | 任意国内空间 |
| 会员 | 新加坡 | `icbu_pii_sg.icbu_pii_privacy_computing_icbu_member_sha256_desensitized_sg_df` | `global_insight_sg` |
| 会员 | 美国 | `icbu_pii_us.icbu_pii_privacy_computing_icbu_member_sha256_desensitized_us_df` | `icbu_gdpr_us_east` |
| 会员 | 德国 | `icbu_pii_de.icbu_pii_privacy_computing_icbu_member_sha256_desensitized_de_df` | `icbu_risk_de` |
| 公司 | 中国 | `icbu_pii_cn.icbu_pii_privacy_computing_icbu_company_sha256_desensitized_cn_df` | 任意国内空间 |
| 公司 | 新加坡 | `icbu_pii_sg.icbu_pii_privacy_computing_icbu_company_sha256_desensitized_sg_df` | `global_insight_sg` |
| 公司 | 美国 | `icbu_pii_us.icbu_pii_privacy_computing_icbu_company_sha256_desensitized_us_df` | `icbu_gdpr_us_east` |
| 公司 | 德国 | `icbu_pii_de.icbu_pii_privacy_computing_icbu_company_sha256_desensitized_de_df` | `icbu_risk_de` |

全量加密表（必须在新加坡环境使用）：

| 类型 | 全量加密表 | 项目空间 |
|------|---------------|------------|
| 会员 | `icbu_security_tech_sg.icbu_pii_privacy_computing_icbu_member_sha256_desensitized_df` | `global_insight_sg` |
| 公司 | `icbu_security_tech_sg.icbu_pii_privacy_computing_icbu_company_sha256_desensitized_df` | `global_insight_sg` |

操作步骤：

1. 申请加密函数

   | 申请项 | 内容 | 链接 |
   |---------|------|------|
   | 资源 | `pii_desensitization.py`（空间 `icbu_security_tech`） | https://guard.alibaba-inc.com/mark/mark.htm/#/resources/resourceApply |
   | 函数 | `PII_DESENSITIZATION` | https://guard.alibaba-inc.com/mark/mark.htm/#/function/apply |

2. 申请加密表权限：在 DataWorks 申请对应加密表的读权限。

3. 写 SQL：

   ```sql
   -- 列名以实际表 schema 为准；会员维度邮箱字段通常为 uic_email
   SELECT a.* FROM my_blacklist a
   JOIN icbu_pii_cn.icbu_pii_privacy_computing_icbu_member_sha256_desensitized_cn_df b
   ON icbu_security_tech:PII_DESENSITIZATION(a.email, 'sha256') = b.uic_email;
   ```

   函数语法：`icbu_security_tech:PII_DESENSITIZATION(字段, 'sha256')`
   注意：SHA256 区分大小写与完全字符，"ABC" 与 "abc"、"ABC " 与 "ABC" 不匹配。两侧字符难以逐字一致时，请用场景二做归一化预处理后再哈希。

### 场景二：自定义预处理后精确匹配

> 典型需求：匹配前需统一转小写、去空格、截取前 N 位等自定义逻辑；或有非标准 SHA256 加密方式要求。

和场景一的区别在于：先做业务自定义处理再加密，或者需要特定加密方式。

操作步骤：

1. 提交自定义加密方式配置申请（内网入口）。默认当天配置完成，完成后有钉钉工作通知。涉及自定义 UDF 函数需提供 jar/python 源文件，用于部署到隐私单元库。
2. 新建加密数据申请单（内网入口）。
   - 公司数据和会员数据不能放同一个申请单，需分开提交。
   - 私域数据需填写在线 PII 写入的 bizCode。
3. 审批通过后 T+1 自动创建对应加密表/视图（`icbu_security_tech` 空间）。
4. 申请新表权限后使用，SQL 写法参考场景一。

### 场景三：需要使用明文数据

> 典型需求：向监管报送商家实名信息、人工审核买卖家是否同人、触达买卖家（寄信/颁证/leads）、必须基于完整原始明文验证邮箱/号码有效性、配合政府协查。

> 再确认一次：你确定需要明文吗？只是做匹配的话请回看场景一，明文表的审核严格得多。

操作步骤：

1. 提交合规评审 → https://yida.alibaba-inc.com/s/PII_apply#/
   - 说清应用场景（如"向 XX 监管机构报送商家实名信息"）。
   - 列明每个字段用途。
   - 只申请最小必要字段。
2. 评审通过，拿到评审链接。
3. 申请区域明文表权限，申请中贴上评审链接。

区域明文表：

| 区域 | 会员明文表 | 公司明文表 | 项目空间 |
|------|---------------|---------------|------------|
| 中国 | `icbu_pii_cn.icbu_pii_privacy_computing_icbu_member_original_cn_df` | `icbu_pii_cn.icbu_pii_privacy_computing_icbu_company_original_cn_df` | 任意国内项目空间 |
| 新加坡 | `icbu_pii_sg.icbu_pii_privacy_computing_icbu_member_original_sg_df` | `icbu_pii_sg.icbu_pii_privacy_computing_icbu_company_original_sg_df` | `global_insight_sg` |
| 美国 | `icbu_pii_us.icbu_pii_privacy_computing_icbu_member_original_us_df` | `icbu_pii_us.icbu_pii_privacy_computing_icbu_company_original_us_df` | `icbu_gdpr_us_east` |
| 德国 | `icbu_pii_de.icbu_pii_privacy_computing_icbu_member_original_de_df` | `icbu_pii_de.icbu_pii_privacy_computing_icbu_company_original_de_df` | `icbu_risk_de` |

重要限制：
- 明文表只能在对应区域项目空间使用，不允许跨区域。
- 国内 ODPS 环境只能用中国区域明文表。
- 明文数据没有全量表，不存在跨区域整合全部用户明文的方式。

### 场景四：在线业务系统调用 PII（优先方式）

> 典型需求：生意参谋/数据管家展示用户姓名、CRM 销售系统查询买家联系方式、EDM 营销邮件、智能外呼 IVR、网站主页公司名搜索。

操作步骤：

1. 申请 bizCode → https://yuque.antfin.com/twm0yn/project/xzrcnm （秉持最小使用原则，按场景申请）。
2. 对接 PII 在线读写接口（参考最新指引中 PII 数据服务-接口使用指南）。
3. 权限上线：审批通过后仅在预发生效 → 预发验证通过 → 手动同步至线上 → 走线上变更审批流。

### 场景五：FBI 报表展示

> 典型需求：在 FBI 报表中展示买卖家姓名、邮箱、手机号等。

原理是 FBI 插件用 aliId 或 companyId 在线调用 PII 实时接口取数展示，每次报表加载时触发查询，数据只展示不存储。

操作步骤：

1. 申请 bizCode（每个使用场景需独立 bizCode）。
2. 在 FBI 报表配置 PII 展示插件。
3. 查询已有 bizCode → https://fbi.alibaba-inc.com/dashboard/view/page.htm?id=1544815

### 场景六：文本相似度 / 模糊匹配

> 典型需求：团伙模糊分析、通过关联介质文本相似度做模糊关联。

加密表只能做精确相等判断，做不了模糊匹配，所以模糊匹配走 SimHash 方案。

操作要点：
- 离线所在空间：`b_risk`
- 函数：`CalSimHash`
- 参数：第一个参数文本内容，第二个参数配置项
- 详见：https://aliyuque.antfin.com/gkxz50/igqkce/qayqggak6h35nvuo

### 场景七：私域数据使用

> 典型需求：使用合同、认证、CRM、资金、物流、信用证等业务域的隐私数据（除会员/公司注册信息外的所有隐私数据）。

和公域基本一致：分明文/加密两种，按区域部署，全量数据只有加密版本且在新加坡。不同的地方：

- 申请时必须填写对应在线 PII 写入 bizCode，只能申请该 bizCode 有写权限的隐私字段。
- 私域数据相对分散，目前只梳理了部分私域表（见本文「三、私域数据表清单」）。
- 找不到所需私域数据表 → 联系 PII 离线数据 owner（当前 @平悦）咨询。

使用方式：
- 精确匹配 → 私域 SHA256 哈希脱敏表（如 `icbu_security_tech.icbu_pii_privacy_computing_trade_contract_sha256_desensitized_df`）。
- 需明文 → 走合规评审后申请对应私域明文表。

> 项目空间归属：`icbu_security_tech`（无区域后缀）与场景二自定义生成的表，可用项目空间随表配置而定，不要默认等同于公域区域表的空间映射。申请权限前先用 DataWorks 查看该表的归属项目与可访问空间，或联系 PII 离线数据 owner（当前 @平悦）确认，避免跨区域误用。

查询自己的 bizCode → https://fbi.alibaba-inc.com/dashboard/view/page.htm?id=1544815

---

## 三、私域数据表清单

找不到所需私域表请联系 PII 离线数据 owner（当前 @平悦）。

| 业务域 | 表名 | 数据类型 |
|---------|------|------------|
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_address_info` | 明文 |
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_s_auth` | 明文 |
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_auth_data_field` | 明文 |
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_auth_request` | 明文 |
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_company_info` | 明文 |
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_person_info` | 明文 |
| 认证 | `icbu_security_tech.icbu_pii_private_seller_auth_all_data` | 明文 |
| 合同 | `icbu_security_tech.icbu_pii_privacy_computing_trade_contract_plaintext_desensitized_df` | 明文 |
| 合同（美国） | `icbu_pii_us.icbu_pii_privacy_computing_trade_contract_plaintext_desensitized_us_df` | 美国明文 |
| 合同 | `icbu_security_tech.icbu_pii_privacy_computing_trade_contract_sha256_desensitized_df` | SHA256 加密 |
| 资金 | `icbu_security_tech.icbu_pii_privacy_computing_fund_refund_account_plaintext_desensitized_df` | 明文 |
| 物流订单 | `icbu_security_tech.icbu_pii_privacy_computing_logistics_order_pii_desensitized_df` | 明文 |
| CRM 售中 | `icbu_security_tech.icbu_pii_privacy_computing_seller_crm_order_indianocean_plaintext_desensitized_df` | 明文 |
| CRM 售前 | `icbu_security_tech.icbu_pii_privacy_computing_crm_aurora_contact_info_plaintext_desensitized_df` | 明文 |
| CRM 售前 | `icbu_security_tech.icbu_pii_privacy_computing_seller_crm_customer_create_plaintext_desensitized_df` | 明文 |
| 信用证 | `icbu_security_tech.icbu_pii_privacy_computing_fin_lc_core_privacy_plaintext_desensitized_df` | 明文 |
| 信用证 | `icbu_security_tech.icbu_pii_privacy_computing_fin_lc_b2e_privacy_plaintext_desensitized_df` | 明文 |
| 信用证 | `icbu_security_tech.icbu_pii_privacy_computing_fin_lc_privacy_plaintext_desensitized_df` | 明文 |

---

## 四、区域路由规则：用户数据在哪？

隐私数据按用户注册国家/地区路由到不同存储区域。

| 路由区域 | 覆盖的国家/地区 |
|------------|----------------------|
| **CN（中国）** | 中国大陆 |
| **SG（新加坡）** | 东南亚、中国香港、中国台湾、俄罗斯、印度、日本、韩国，以及所有未明确归属的国家（兜底） |
| **US（美国）** | 五眼联盟：美国、澳大利亚、加拿大、新西兰、英国 |
| **DE（德国）** | 所有欧洲国家/地区（芬兰、瑞典、法国、德国、意大利、西班牙、荷兰、波兰等） |

简单记：欧洲存德国，东南亚存新加坡，五眼存美国，中国大陆存中国，不确定的归到新加坡兜底。

**常见国家路由对照**：

| 国家 | 代码 | 区域 | 国家 | 代码 | 区域 |
|------|------|------|------|------|------|
| 中国大陆 | CN | CN | 美国 | US | US |
| 中国香港 | HK | SG | 英国 | GB/UK | US |
| 中国台湾 | TW | SG | 澳大利亚 | AU | US |
| 印度 | IN | SG | 加拿大 | CA | US |
| 日本 | JP | SG | 新西兰 | NZ | US |
| 韩国 | KR | SG | 法国 | FR | DE |
| 俄罗斯 | RU | SG | 德国 | DE | DE |
| 新加坡 | SG | SG | 意大利 | IT | DE |
| 泰国 | TH | SG | 西班牙 | ES | DE |

---

## 五、隐私字段清单：哪些字段是隐私字段？

### 会员维度（`uic_` 前缀）

| 字段代码 | 含义 | 字段代码 | 含义 |
|------------|------|------------|------|
| `uic_email` | 注册邮箱 | `uic_mobile_no` | 手机号 |
| `uic_first_name` | 名 | `uic_last_name` | 姓 |
| `uic_login_id` | 登陆帐号 | `uic_login_mobile` | 登陆手机号 |
| `uic_alt_email` | 备用邮箱 | `uic_phone_number` | 电话号码 |
| `uic_address` | 街道地址 | `uic_city` | 城市 |
| `uic_province` | 省 | `uic_country` | 国家 |
| `uic_zip` | 邮编 | `uic_gender` | 性别 |
| `uic_job_title` | 头衔 | `uic_department` | 部门 |
| `uic_fax_number` | 传真号 | `uic_company_tmp_name` | 临时公司名 |

### 公司维度

| 字段代码 | 含义 | 字段代码 | 含义 |
|------------|------|------------|------|
| `company_name` | 公司名称 | `company_email` | 公司邮箱 |
| `principal` | 法人 | `tax_no` | 税号 |
| `website` | 网址 | `company_detail_1` | 公司详情 |
| `reg_address` | 注册地-街道 | `reg_city` / `reg_country` | 注册地-城市/国家 |
| `operational_address` | 经营地-街道 | `operational_city` / `operational_country` | 经营地-城市/国家 |

### 其他通用字段

| 字段代码 | 含义 | 字段代码 | 含义 |
|------------|------|------------|------|
| `email` | 联系邮箱 | `mobile_number` | 手机号 |
| `first_name` / `last_name` | 姓名 | `full_name` | 全名 |
| `id_number` | 身份证号 | `passport` | 护照号 |
| `bank_account_number` | 银行账号 | `account_holder_name` | 开户人 |
| `ip` | IP 地址 | `longitude` / `latitude` | 经纬度 |

---

## 六、申请与评审流程

> 关键顺序：用隐私敏感数据必须先提合规评审、拿到评审链接，再申请离线表权限并贴上评审链接。顺序反了会被直接退回。

详细流程与申请表填写要点见 [review-process.md](review-process.md)。

---

## 七、营销退订名单（非获客源表）

做营销触达前需先过滤退订/黑名单，这类名单表（统一维表 `icbu_security_tech.icbu_risk_marketing_blacklist_df` 及上游来源表、在线 DNC 过滤服务）属合规过滤用途，**不是营销获客的 PII 源表**。表清单、字段与接入方式见 [marketing-platform-compliance.md](marketing-platform-compliance.md)「五、营销退订名单（黑名单）接入」；营销合规要求（圈客/疲劳度/披露）见同文件「四、ICBU 内部直销营销操作规范」。
