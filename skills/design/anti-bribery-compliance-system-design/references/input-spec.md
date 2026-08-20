# 输入字段定义

> 版本：2.0.0 | 配套技能：anti-bribery-compliance-system-gen

---

## 1. 必填字段

### 1.1 company_type（企业类型）

| 属性 | 值 |
|------|-----|
| 类型 | string |
| 必填 | 是 |
| 可选值 | manufacturer / trader / energy / pharmaceutical / construction / financial / technology / service / other |
| 说明 | 企业类型决定反贿赂合规重点——制药企业对医疗保健专业人士互动（HCP/HCO）管控要求高；能源/基建企业对政府合同贿赂风险高；金融企业对中间人/代理人管控要求高 |

**输入规则**：
- 制造企业(manufacturer)：关注海外代理商/分销商贿赂风险+政府招标合规
- 贸易商(trader)：关注中间人/代理商/佣金支付的FCPA风险
- 能源企业(energy)：关注资源国政府官员贿赂风险+政治捐赠管控
- 制药企业(pharmaceutical)：关注HCP/HCO互动+学术赞助合规+加速费管控
- 建筑/基建(construction)：关注政府合同招标贿赂风险+分包商合规
- 金融企业(financial)：关注代理人/中介机构合规+海外投资反腐败尽调
- 科技企业(technology)：关注海外销售代理+技术许可过程中的贿赂风险
- 服务企业(service)：关注咨询费/服务费合理性审查
- 其他(other)：按通用反贿赂合规框架

### 1.2 business_model（业务模式描述）

| 属性 | 值 |
|------|-----|
| 类型 | text |
| 必填 | 是 |
| 长度限制 | ≤3000字符 |
| 说明 | 业务模式描述决定第三方管理、代理商、分销商等风险维度——建议包含销售模式（直销/代理/分销）、政府客户占比、使用第三方中介情况 |

**输入规则**：
- 应包含：销售渠道（直销/代理/分销）+ 主要客户类型（政府/国企/私企）+ 第三方使用情况（代理商/咨询顾问/中介机构）
- 如涉及政府客户，须标注政府业务占比
- 如使用代理商/中介，须描述佣金结构和审批流程

### 1.3 operating_regions（运营地域清单）

| 属性 | 值 |
|------|-----|
| 类型 | string[] |
| 必填 | 是 |
| 格式 | 国家/地区代码或名称列表 |
| 说明 | 运营地域决定适用法规范围——FCPA域外效力（发行人+国内企业+在美国境内行为的外国主体）、UKBA域外效力（与英国有"密切联系"的商业组织）、东道国反贿赂法适用 |

**输入规则**：
- 使用国家代码（如CN/SG/MY/SA/AE/NG）或国家名称
- 标注汇率管制的国家（涉及现金支付管控）
- 标注反腐透明度指数（TI CPI）较低的国家（高风险地区，需加强管控）
- 注意：运营地域决定了UKBA §7是否适用（与英国有密切联系的企业）

### 1.4 company_size（企业规模）

| 属性 | 值 |
|------|-----|
| 类型 | string |
| 必填 | 是 |
| 可选值 | large / medium / small |
| 影响 | 生成范围自动推荐（large→full / medium→standard / small→compact）+ 组织架构复杂度 + SOP数量 |

---

## 2. 选填字段

### 2.1 industry_sector（行业领域）

| 属性 | 值 |
|------|-----|
| 类型 | string |
| 必填 | 否 |
| 可选值 | pharmaceutical / energy / infrastructure / defense / financial / technology / manufacturing / trade / service / other |
| 影响 | 贿赂风险等级评估（制药/能源/基建/国防→高风险行业）+ 特定SOP侧重点 |

### 2.2 existing_host_country_law（已有东道国反贿赂法规汇编）

| 属性 | 值 |
|------|-----|
| 类型 | text |
| 必填 | 否 |
| 来源 | host-country-legal-compilation 技能输出 |
| 说明 | 已有东道国反贿赂法规汇编——本技能引用而非重复检索，在合规手册和SOP法律依据中标注引用来源 |

### 2.3 existing_risk_assessment（已有风险初评结果）

| 属性 | 值 |
|------|-----|
| 类型 | text |
| 必填 | 否 |
| 来源 | trade-compliance-risk-assessment 技能输出 |
| 说明 | 已有贿赂风险初评结果——决定合规手册风险侧重点和SOP管控严格程度 |

### 2.4 current_compliance_status（当前合规现状）

| 属性 | 值 |
|------|-----|
| 类型 | string |
| 必填 | 否 |
| 可选值 | none / partial / needs_update |
| 影响 | 生成策略——全新生成 vs 补充完善 vs 更新替换 |

### 2.5 generation_scope（生成范围）

| 属性 | 值 |
|------|-----|
| 类型 | string |
| 必填 | 否 |
| 可选值 | full / standard / compact |
| 说明 | 手动指定生成范围——留空则按company_size自动推荐（Phase 0交互门控确认） |

### 2.6 specific_concerns（特别关注事项）

| 属性 | 值 |
|------|-----|
| 类型 | text |
| 必填 | 否 |
| 说明 | 用户特别关注的合规风险点（如近期DOJ执法趋势/FCPA新政策/特定国家反贿赂法规更新/已知贿赂事件/行业特有合规要求） |

---

## 3. 输入模式

### Mode A：完整输入

用户提供全部必填+选填字段（含generation_scope），跳过IG-A门控直接进入制度生成。

### Mode B：最小输入

用户仅提供 company_type + business_model + operating_regions + company_size，其余字段由技能根据企业画像自动推断，IG-A展示推荐模式等待确认。

### Mode C：自然语言输入

用户用自然语言描述需求（如"我们是做制药的公司，通过代理商在东南亚和中东销售，需要一套反商业贿赂合规制度"），自动提取参数，IG-A展示推荐模式等待确认。

---

## 4. 输入验证规则

| 规则ID | 检查项 | 失败动作 |
|--------|--------|---------|
| V1 | company_type 非空且为合法枚举值 | 🔴阻断 |
| V2 | business_model 非空 | 🔴阻断 |
| V3 | operating_regions 非空且≥1个地域 | 🔴阻断 |
| V4 | company_size 非空且为合法枚举值（large/medium/small） | 🔴阻断 |
| V5 | generation_scope（如提供）为合法枚举值（full/standard/compact） | 🟡回退到推荐模式 |
| V6 | operating_regions中的国家可识别（用于法规适用分析） | 🟡确认（无法识别时标注"[需手动确认东道国法适用]"） |
| V7 | business_model是否包含政府客户描述（影响政治捐赠SOP的必要性判断） | 🟢提示 |

---

## 5. 生成范围自动推荐规则

| company_size | 推荐模式 | 推荐理由 |
|-------------|---------|---------|
| large | full | 大型企业（500+员工/多国运营）受FCPA/UKBA域外效力覆盖，须满足DOJ/SFO"充分合规程序"标准，需全套制度覆盖 |
| medium | standard | 中型企业（50-500员工）核心风险需覆盖但合规成本可控，5套核心SOP覆盖主要贿赂风险点 |
| small | compact | 小型企业（<50员工）合规成本优先，3套核心SOP（第三方尽调/礼品招待/利益冲突）已覆盖最高频贿赂场景 |

### 推荐结果呈现（IG-A交互门控）

```
## 生成范围推荐

根据企业规模（{company_size}），推荐生成范围：**{recommended_scope}** 模式

| 选项 | 模式 | 产物范围 | 文件数 |
|------|------|---------|--------|
| A | full（完整版） | 合规手册+8套SOP+8份表格+角色矩阵+违规流程，每类文件独立输出（DOCX+XLSX） | 19个 |
| B | standard（标准版） | 合规手册+5套SOP+5份表格+角色矩阵，违规流程内联合规手册 | 12个 |
| C | compact（精简版） | 合规手册（精简版，含核心SOP+表格内联） | 1个 |

请选择（输入A/B/C），或直接回复"确认"使用推荐模式。
```
