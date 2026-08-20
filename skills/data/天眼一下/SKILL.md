---
name: 天眼一下
description: 使用本地 `tyc` 命令查询天眼查企业数据。适用于企业主体核验、合作方/客户/供应商风险评估、股东和实控人分析、受益所有人、关联关系路径、司法诉讼、执行失信、行政处罚、经营真实性、招投标、资质许可、知识产权、董监高、历史沿革、行业企业发现，以及生成简短商查摘要。查询前使用 `tyc login` 完成 OAuth 鉴权。
---

# 天眼一下

使用 `tyc` 在命令行查询天眼查数据。先锚定主体，再按用户问题调用必要维度，最后给出结论、证据和未覆盖点。

## 安装与鉴权

安装：

```bash
npm install -g tyc-cli
```

使用 OAuth 登录：

```bash
tyc login
```

浏览器无法自动打开时，使用：

```bash
tyc login --no-open
```

只有在用户要求非默认服务地址时，才使用：

```bash
tyc login --url <url>
```

首次查询前确认 CLI 可用：

```bash
tyc --version
tyc company companies "百度" --pageNum 1 --pageSize 3 --md
```

如果查询提示未登录、凭证缺失或凭证过期，重新执行 `tyc login`。

## 命令规则

- 使用 `tyc` 命令，不使用 `tyc-cli` 命令。
- 不确定参数时，先运行 `tyc <category> --help` 或 `tyc <category> <method> --help`。
- 分析时优先使用默认 JSON 输出；需要给用户展示候选表或简短结果时使用 `--md`。
- 列表查询默认加 `--pageNum 1 --pageSize 10`，除非用户要求更多。
- 大结果使用 `--head`、`--threshold` 或 `--output-file` 控制输出，不把长原始数据直接塞进最终答复。
- 空结果只表示当前命令未返回数据；不要写成“绝对没有风险”。

## 查询流程

1. 从用户问题提取主体、意图、深度和决策场景。
2. 除非用户给出完整企业名或 18 位统一社会信用代码，否则先锚定主体。
3. 先调用一到两个总览命令。
4. 只下钻回答问题必需的维度。
5. 重要判断尽量用两个以上维度交叉验证。
6. 输出时先给结论，再给证据、限制和下一步建议。

## 主体锚定

简称、品牌、曾用名、模糊名称或不确定主体，先用企业搜索：

```bash
tyc company companies "<query>" --pageNum 1 --pageSize 5 --md
```

优先选择经营状态正常、名称匹配语境，并且法定代表人、地区、行业或 USCC 与用户线索一致的候选。

只有一个明确候选时，可继续使用官方名称或 USCC 查询。多个候选都可能匹配时，先让用户确认：

```markdown
你说的「<query>」匹配到多家企业，请确认是哪一家：

| # | 企业名称 | USCC | 状态 | 法定代表人 | 注册地 |
|---|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... |

回复编号继续，或回复“都不是”重新输入。
```

多主体关系问题必须分别锚定每个主体，再判断关系。

## 常用命令

| 意图 | 命令 |
|---|---|
| 主体画像 | `tyc company registration-info "<company>"`; `tyc company profile "<company>"`; `tyc company scale "<company>"`; `tyc company contact-info "<company>" --pageNum 1 --pageSize 10` |
| 合作风险 | `tyc risk overview "<company>"`; `tyc risk business-exception "<company>" --pageNum 1 --pageSize 10`; `tyc risk administrative-penalty "<company>" --pageNum 1 --pageSize 10`; `tyc risk judgment-debtor-info "<company>" --pageNum 1 --pageSize 10`; `tyc risk dishonest-info "<company>" --pageNum 1 --pageSize 10` |
| 司法与执行 | `tyc risk judicial-case "<company>" --pageNum 1 --pageSize 10`; `tyc risk judicial-documents "<company>" --pageNum 1 --pageSize 10`; `tyc risk case-filing-info "<company>" --pageNum 1 --pageSize 10`; `tyc risk high-consumption-restriction "<company>" --pageNum 1 --pageSize 10` |
| 行政与合规 | `tyc risk administrative-penalty "<company>" --pageNum 1 --pageSize 10`; `tyc risk serious-violation "<company>" --pageNum 1 --pageSize 10`; `tyc risk environmental-penalty "<company>" --pageNum 1 --pageSize 10`; `tyc risk tax-violation "<company>" --pageNum 1 --pageSize 10`; `tyc risk tax-arrears-notice "<company>" --pageNum 1 --pageSize 10` |
| 股东与实控 | `tyc company shareholder-info "<company>" --pageNum 1 --pageSize 10`; `tyc company actual-controller "<company>"`; `tyc company beneficial-owners "<company>" --pageNum 1 --pageSize 10`; `tyc company equity-tree "<company>"`; `tyc company equity-ratio "<company>"` |
| 关联关系 | `tyc company relation-path "<companyA>" --searchKey2 "<companyB>"`; `tyc company relation-graph "<company>"`; `tyc company group-info "<company>"` |
| 经营真实性 | `tyc operation bidding-info "<company>" --pageNum 1 --pageSize 10`; `tyc operation qualifications "<company>" --pageNum 1 --pageSize 10`; `tyc operation administrative-license "<company>" --pageNum 1 --pageSize 10`; `tyc operation recruitment-info "<company>" --pageNum 1 --pageSize 10`; `tyc operation products-info "<company>" --pageNum 1 --pageSize 10`; `tyc operation suppliers-and-customers "<company>" --pageNum 1 --pageSize 10` |
| 知识产权与品牌 | `tyc intellectual_property ipr-score "<company>"`; `tyc intellectual_property patent-info "<company>" --pageNum 1 --pageSize 10`; `tyc intellectual_property trademark-info "<company>" --pageNum 1 --pageSize 10`; `tyc intellectual_property software-copyright-info "<company>" --pageNum 1 --pageSize 10` |
| 董监高和人员 | `tyc company key-personnel "<company>" --pageNum 1 --pageSize 10`; `tyc executive person-profile "<company>" --humanName "<name>"`; `tyc executive person-risk-overview "<company>" --humanName "<name>"`; `tyc executive personnel-positions "<company>" --humanName "<name>"`; `tyc executive personnel-related-companies "<company>" --humanName "<name>"` |
| 历史沿革 | `tyc history historical-overview "<company>"`; `tyc history historical-registration "<company>"`; `tyc history historical-shareholders "<company>" --pageNum 1 --pageSize 10`; `tyc history historical-investments "<company>" --pageNum 1 --pageSize 10`; `tyc company change-records "<company>" --pageNum 1 --pageSize 10`; `tyc company history-names "<company>"` |
| 企业发现 | `tyc company companies-by-industry-region "<keyword>" --industry "<code>" --region "<code>" --pageNum 1 --pageSize 10`; `tyc company companies-by-tag "<tag>" --pageNum 1 --pageSize 10`; `tyc company companies-by-ranking "<company>" --pageNum 1 --pageSize 10`; `tyc company park-companies "<park>" --pageNum 1 --pageSize 10` |
| 关键词搜索 | `tyc operation bids "<keyword>" --pageNum 1 --pageSize 10`; `tyc intellectual_property patents "<keyword>" --pageNum 1 --pageSize 10`; `tyc intellectual_property trademarks "<keyword>" --pageNum 1 --pageSize 10` |
| 上市与财务 | `tyc company financial-summary "<company>"`; `tyc company financial-data "<company>"`; `tyc company listing-info "<company>"`; `tyc company income-statement "<company>"`; `tyc company balance-sheet "<company>"`; `tyc company cash-flow-statement "<company>"`; `tyc company stock-shareholders "<company>" --pageNum 1 --pageSize 10` |

## 意图捷径

- 用户只说“查一下这家公司”时，默认查主体画像、风险总览、经营真实性和实控摘要。
- 用户问“能不能合作/供应商准入/客户风险”时，优先查登记状态、风险总览、行政处罚、执行失信、经营异常、经营信号和资质。
- 用户问“背后是谁/实际控制人/受益人”时，优先查股东、实际控制人、受益所有人、股权树和集团信息。
- 用户问“两家公司有没有关系”时，先锚定双方，再查关联路径和关键中间节点。
- 用户问“真实经营吗”时，结合登记信息、规模、招投标、资质、许可、产品、招聘、客户供应商和必要的舆情信息。
- 用户问“商标/专利/技术实力”时，结合创新力评分、专利、商标和软著明细。
- 用户问“高管/法人背景”时，先查主要人员，再带 `--humanName` 查询人员画像和人员风险。

## 判断规则

- 区分“查到风险记录”“已查询但未返回记录”“未查询该维度”。
- 不替用户做法律、投资、授信或采购最终决策；给数据驱动建议，并列出需要人工复核的材料。
- 重大风险结论必须标注证据来自哪些 `tyc` 命令。
- 优先使用具体记录和近期记录，不只看总数。总览和明细冲突时，直接说明冲突。
- 集团、实控和关联关系判断以路径、持股、任职、集团信息为依据，不以名称相似为依据。

## 输出格式

默认使用简体中文，结论先行。

```markdown
# 商查摘要：<company>

## 结论
<1-3 句话直接回答用户问题>

## 关键信号
| 维度 | 发现 | 判断 |
|---|---|---|
| 主体 | ... | 通过/关注/异常 |
| 风险 | ... | 低/中/高 |
| 经营 | ... | 强/一般/弱 |
| 股权/关系 | ... | 清晰/需复核 |

## 建议
- <下一步动作>
- <需要人工复核的点>

## 数据来源
`tyc ...`，`tyc ...`
```

