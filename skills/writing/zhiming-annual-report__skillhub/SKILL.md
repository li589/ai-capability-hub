---
name: zhiming-annual-report
description: 知命流年节奏报告（Pay Skill）。在用户提供出生年月日时、性别、阴阳历及目标公历年份后，生成该年 Markdown 流年解读：大运与流年关系、重点月份节奏、事业与情感倾向、可执行注意事项。结合规则引擎年度应事与调候/格局/盲派做功视角，理论含《穷通宝鉴》《子平真诠》《滴天髓》等及约1000例归纳知识。按次付费。用于年度规划与自我认知；非吉凶铁口、非决策承诺。
tags: [流年, 年度规划, 八字, 自我认知, 传统文化, 知命, 大运]
version: 1.0.2
pricing:
  model: per_call
  amount_fen: 10
---

# 知命 · 流年节奏报告（Pay Skill）

## 产品介绍（可对外展示）

**一句话**：按完整生辰与目标公历年份，生成该年事业、情感与节奏节点的结构化解读；算法应期 + 古籍理论视角，供年度规划与自我复盘参考。

**方法与优势（与站内引擎一致）**：

1. **生辰与历法严谨**：年月日时、性别、阴阳历必填；农历可标闰月；可选出生地修正。`target_year` 为要分析的**公历年**。
2. **先算法、后叙述**：规则引擎给出年度断局与应事线索，大模型引用展开，降低纯自由发挥跑偏。
3. **经典与案例**：注入 **《穷通宝鉴》《子平真诠》《滴天髓》** 等体系与约 **1000 例** 归纳知识；书房派定层次，盲派侧重做功与应期，互相印证。
4. **可标注依据**：关键结论可带来源标签，便于用户复核逻辑。
5. **分月节奏**：结合目标年流月干支等结构化信息，服务年度规划而非恐吓式断语。

**定位**：把「某一年」放进大运脉络里看**节奏与侧重点**。不承诺必发必破，不提供投机建议，不替代专业咨询。

**计费与交付**：按次付费（测试价 0.10 元/次，以配置为准）；交付 `content`；**不解锁**站内权益。

**免责声明**：内容由知命分析引擎生成，仅供文化参考与自我认知，不构成投资、职业、婚姻、健康或法律等重大决策的建议或保证。请以理性态度参考。

## 功能与交付

根据用户**完整生辰**与**目标公历年份**，生成 **Markdown 流年节奏报告**。

## 必填信息（向用户收集齐全后再请求）

| 信息 | 对应字段 | 说明 |
|---|---|---|
| 出生年、月、日 | `birth_year` `birth_month` `birth_day` | 整数 |
| 出生时 | `birth_hour` | **0–23** 整点（24 小时制，不是子丑寅卯） |
| 性别 | `gender` | `male`/`female` 或 `男`/`女`（乾造/坤造不同） |
| **阴阳历** | `is_lunar` 或 `calendar_type` | **必须明确**，见下文 |
| **流年年份** | `target_year` | 要分析的**公历年**（如 2026） |

可选：`birth_city`（出生城市，真太阳时修正）、`is_leap_month`（仅农历闰月）、`marital_status`。

**缺任一项必填 → 接口 400，不要猜测补全阴阳历或性别。**

## 阴阳历（极重要）

与站内排盘 API 一致：`is_lunar` + 可选 `is_leap_month`。

| 用户说法 | 传参 | `birth_year/month/day` 填什么 |
|---|---|---|
| 阳历 / 公历 | `is_lunar: false` 或 `calendar_type: "solar"` / `"公历"` / `"阳历"` | **公历**年月日 |
| 阴历 / 农历 | `is_lunar: true` 或 `calendar_type: "lunar"` / `"农历"` / `"阴历"` | **农历**年月日（服务端再转公历排盘） |
| 农历闰月 | 在农历基础上再加 `is_leap_month: true` | 农历月日 + 闰月标记 |

- **阳历与阴历是两套结果**：同一组数字在 `is_lunar` true/false 下八字不同，**禁止省略、禁止默认猜公历**。
- 用户只说「1990 年五月十五」未说阴阳历 → **先问清楚**再调用。
- `target_year` 始终是**公历年份**（分析哪一年运势），与出生用阴历无关。

## 付费前置检查

调用前确认 Agent 已安装 `weixinpay` 插件；未安装则提示不支持微信支付并终止。

## 工作流程

### 第一步：请求资源

`POST https://bz.dongcha.cyou/api/skillpay/annual-report`

**公历/阳历示例：**

```json
{
  "birth_year": 1990,
  "birth_month": 5,
  "birth_day": 15,
  "birth_hour": 10,
  "gender": "male",
  "is_lunar": false,
  "target_year": 2026,
  "birth_city": "北京",
  "marital_status": ""
}
```

**农历/阴历示例（含闰月时加 is_leap_month）：**

```json
{
  "birth_year": 1990,
  "birth_month": 4,
  "birth_day": 21,
  "birth_hour": 10,
  "gender": "female",
  "is_lunar": true,
  "is_leap_month": false,
  "target_year": 2026,
  "birth_city": "上海"
}
```

也可用：`"calendar_type": "农历"` 代替 `is_lunar: true`。

### 第二步：处理 402

HTTP **402** 时用 `weixinpay` 完成支付，保存：

- `WeixinPay-Required`（Header 或 Body）
- `X-Out-Trade-No` / `out_trade_no`

### 第三步：支付成功后必须重试

- **Body 与第一步完全一致**（含 `is_lunar`、`target_year` 等）
- Header：`X-Out-Trade-No`、`WeixinPay-Required`

成功：HTTP 200，`code=SUCCESS`，报告在 `content`。

### 第四步：异常

| code / 情况 | 处理 |
|---|---|
| 400 + detail | 缺字段/阴阳历未明，向用户补问后重发，**勿重复支付** |
| NOT_PAID | 未支付或校验中，稍后原样重试 |
| FULFILL_FAILED | 已支付生成失败，同一 `out_trade_no` 再试 |
| SUCCESS + already_fulfilled | 缓存报告 |

## 注意事项

1. 必须先确认 weixinpay 可用  
2. 支付后必须带 `X-Out-Trade-No` 重试  
3. 同一 `out_trade_no` 幂等履约一次  
4. 阴阳历、性别、时辰、`target_year` 均不可瞎编  
5. 本 Skill 付费不解锁网站会员/命盘  
