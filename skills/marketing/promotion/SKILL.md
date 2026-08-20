---
name: promotion
description: 促销活动创建与权限校验。用户提到建活动、搞促销、限时折扣、满减满折、满减邮、满赠、一口价、拼团、N元N件、订单换购、秒杀时触发，按类型走接口直连或页面填表两条链路。
displayName:
  zh: 促销活动管理
  en: Promotion Campaign Management
displayDescription:
  zh: 校验活动权限并创建、查询、预览或修改促销活动，覆盖折扣、满减、满赠、拼团、秒杀等类型。
  en: Validate permissions and create, query, preview, or modify promotion campaigns, including discounts, threshold offers, gifts, group buying, and flash sales.
---

# 促销活动创建

## 功能说明

本 skill 负责识别用户要创建的促销活动类型、校验商户活动权限，并按活动类型分流到两条互斥的执行链路完成创建：

- **接口链路（直接写入）**：`限时折扣`、`满减满折`、`满减邮`、`满赠`、`N元N件` 五类，通过 `woscli activity query-supported-activity-types` 校验权限后，用 `delegate_to_sub_agent` 委派营销子任务直接调接口创建。
- **表单链路（页面填表）**：`一口价`、`拼团`、`订单换购`、`秒杀` 四类，以及用户明确要求"在页面上填表"的场景，通过 `woscli mall-goods query-supported-activity-types` 校验权限后跳转创建页并调用前端表单填充工具，最终由用户在前端手动保存。

两条链路不可混用：同一次创建任务只能走其中一条，不允许在接口链路失败后自动改走表单链路，也不允许在表单链路里调用 `delegate_to_sub_agent`。

## 触发场景

- 建活动、搞促销、做个折扣活动、创建促销活动。
- 明确点名活动类型：限时折扣、满减满折（满减/满折/满 X 减 Y）、满减邮（满额包邮/满减包邮）、满赠（买满送/满额赠）、一口价、拼团、N元N件（任选 N 件）、订单换购（订单加价购）、秒杀。
- 询问"当前支持哪些活动类型""我有没有创建 XX 活动的权限"。
- 要求跳转活动创建页、填写活动表单、修改尚未保存的活动表单。
- 查询、预览、修改上述五类接口活动。

**不触发**：`限量抢购`、`定金膨胀`、`阶梯价`、`特权价`、`企业内购`、`单品换购`、`必购码`、`单品赠品`、`X件X折`、`整单优惠`、`固定套装`、`搭配套装`、`买M付N`、`抽奖团`、`裂变内购` 等其余活动类型。这些名称只用于识别用户意图，命中时直接回复"当前暂不支持创建 <活动类型> 活动"，不查权限、不跳相似活动页。

## 链路优先级（最高优先级，先判链路再执行）

判定顺序自上而下，命中即停：

| 序号 | 判定条件 | 走哪条链路 |
|---|---|---|
| 1 | 用户明确要求"在页面上填表""帮我把创建页填好""跳到创建页" | 表单链路 |
| 2 | 活动类型 ∈ {一口价、拼团、订单换购、秒杀} | 表单链路 |
| 3 | 活动类型 ∈ {限时折扣、满减满折、满减邮、满赠、N元N件} 且用户要直接创建/新建/预览/查询/修改 | 接口链路 |
| 4 | 活动类型不在上述 9 类内 | 终止，回复不支持 |
| 5 | 活动类型未明确 | 先向用户确认具体活动类型，不自动选择 |

补充规则：

- `满减邮`、`满赠`、`满减满折`、`限时折扣`、`N元N件` 五类两条链路都能做；**默认优先走接口链路直接创建**，只有用户显式要求页面填表时才降级到表单链路。
- 泛化词（"做个活动""搞促销""做个换购活动""做个折扣活动"）不能覆盖明确活动类型。用户只说泛化词时，返回可识别的活动类型清单 + 当前商户支持清单让用户选一个。
- 活动类型识别必须**先精确名称匹配、再泛化触发词**。用户说"单品换购"就是 `单品换购`（不支持），不得因为含"换购"改写成 `订单换购`。
- 允许的归一别名：满减/满折/满 X 减 Y/满 X 打 Y 折 → 满减满折；满额包邮/满减包邮 → 满减邮；买满送/满额赠 → 满赠；N 元 N 件/任选 N 件 → N元N件；订单加价购 → 订单换购。别名只用于归一，不得跨类型改写。
- 上一轮用户已表达创建意图、本轮只回复了活动类型时，视为对活动类型的补充确认，立即继续后续步骤，不要再追问活动名称。

## 调用方式

### 权限查询（两条链路的 category 不同，不要混用）

```bash
# 接口链路
woscli activity query-supported-activity-types

# 表单链路
woscli mall-goods query-supported-activity-types
```

统一处理规则：

- 返回 `results` 非空时，提取 `results[].activityType` 作为商户可创建清单，与归一后的活动类型做**完全一致匹配**。
- 未匹配：终止，告知"当前商户没有创建 <活动类型> 的权限"，并返回当前支持清单。不得改用相似活动或同分组活动，不得跳转其他创建页。
- 命令失败：用相同顶层参数格式追加 `args: {"help": true}` 校验一次；仍失败则说明"当前无法确认商户活动权限"，不继续创建。
- 接口链路下，即使权限结果里出现 `一口价`、`拼团`、`订单换购`、`秒杀`，也必须忽略，不得视为接口链路支持。
- 纯只读任务（查询已有的五类接口活动）不要求创建权限，可直接委派。

### 接口链路：委派营销子任务

```json
{
  "name": "delegate_to_sub_agent",
  "arguments": {
    "description": "创建限时折扣",
    "task_prompt": "请处理促销活动任务。\n用户原始要求：<完整原话>\n执行模式：<正式创建/仅预览/查询/修改>\n活动类型：<规范名称>\n权限结果：<已通过及匹配名称，或纯只读无需创建权限>\n接口对齐：<准确 create command、关键 woscli 参数>\n固定模板：<模板内/超出模板及具体差异>\n已确认业务字段：\n- 活动名称：<已知值/允许生成>\n- 商品或适用范围：<已知值/允许自动选品>\n- 核心规则：<计算条件、门槛、折扣、金额、件数、赠品或地区及对应参数>\n- 活动时间：<已知值/允许默认>\n- 库存与限购：<已知值/允许默认/不适用>\n用户限制：<明确限制>\n请使用以上已确认信息直接完成，不要再次询问已知字段。只有当前 command 契约出现委派前无法预见的新必填业务字段时，才返回缺失项且不要执行写入。"
  }
}
```

### 表单链路：页面跳转 + 表单填充

```json
web_client_tool_call navigate_page tool_args: {"url": "<创建页别名>", "target": "push"}
```

`navigate_page` **不可并行调用**，且发起跳转的那一轮 assistant 消息内不得同时调用 `get_skill_reference`、`get_web_client_tool_schema` 或表单填充工具，必须等工具结果返回后的下一轮再继续。

表单填充工具**没有固定工具名**（`fill_form` 只是代称）：每次都从当前上下文 `web_client_tool_call` 的可用工具列表中挑选"填充/提交/应用活动表单"语义的真实工具，调用前必须先 `get_web_client_tool_schema(<工具名>)` 读取 `inputSchema`，再严格按 schema 组装参数。

```json
{
  "name": "<实际表单填充工具名>",
  "tool_args": {
    "<严格匹配 inputSchema 的参数>": "<value>"
  }
}
```

- schema 顶层直接是 `activityName` 等业务字段 → 字段放在 `tool_args` 顶层，不要额外包 `formData`。
- schema 顶层是 `formData` → 才把业务字段放进 `tool_args.formData`。
- 当前页面没有任何可用的表单填充工具时，才说明无法自动填表，不得硬编造工具名。

## 支持的操作

### A. 接口链路（限时折扣 / 满减满折 / 满减邮 / 满赠 / N元N件）

1. **识别活动类型并归一**，命中四类仅前端活动或范围外活动时直接终止，不查权限、不委派。
2. **权限校验**：`woscli activity query-supported-activity-types`，忽略结果中的一口价/拼团/订单换购/秒杀。
3. **业务字段收集**：用用户能理解的业务语言逐项确认下表字段；不让用户提供商品 ID、SKU ID、组织 ID、图片 URL、UUID 等内部字段。用户回答"按默认/你决定/自动选品"等同已确认，委派时标记"允许默认补齐"。默认时间为当前时区 15 分钟后开始、开始后 3 天结束；默认范围为全部组织、全部人群、线上订单。字段不齐时不得提前委派。

| 活动类型 | 需要明确的业务字段 | 对齐的 create command 与关键参数 |
|---|---|---|
| 限时折扣 | 活动名称；一个活动商品；折扣；活动库存；开始/结束时间 | `discount-create`：`title`；`discount-goods[].goodsId`、`discount-goods[].skuList[].skuId/discount/changeCanSaleNum`；固定 `discountType=1001`、`limit-type=0`；`start-date/end-date` |
| 满减满折 | 活动名称；一个适用商品；满减门槛；减免金额；开始/结束时间 | `fulldiscount-create`：`title`；固定 `select-goods-type=102` + `select-goods-ids`；`rule-biz-vo` 固定 `conditionType=102/calculateType=1/resultType=1001`，映射 `conditionValue/resultValue/maxAmount`；`start-date/end-date` |
| 满减邮 | 活动名称；一个适用商品；包邮门槛；开始/结束时间 | `freefreight-create`：`title`；固定 `select-goods-type=102` + `select-goods-ids`；固定 `postage-setting-factor=102`；门槛映射 `free-freight-rule-level-vos[].postageCondition`，其余固定 `postageType=2001/postageReduceAmt=0/limitDistrictType=0/areaJson=[]`；`start-date/end-date` |
| 满赠 | 活动名称；一个适用商品；一个不同的赠品；满赠门槛；赠送数量；每人参与次数；开始/结束时间 | `gift-create`：`title`；固定 `select-goods-type=102` + `select-goods-ids`；固定 `full-gift-factor=102/full-gift-type=1`；`gift-market-rule-level-vos[].fullGiftCondition`、`.giftMarketGoodsVOS[].goodsId/skuId/skuIds/singleLimit`、`.fullGiftLimit`；`limit-num`；`start-date/end-date` |
| N元N件 | 活动名称；一个适用商品；任选件数；套餐总价；每人参与次数；开始/结束时间 | `nynj-create`：`title`；固定 `select-goods-type=102` + `select-goods-ids`；`rule-biz-vo` 固定 `conditionType=103/calculateType=2/resultType=1003`，映射 `conditionValue/resultValue`；`limit-num`；`start-date/end-date` |

4. **委派**：字段齐备后只调用**一次** `delegate_to_sub_agent`，`task_prompt` 必须包含用户原话、执行模式、规范活动类型、权限结果、已确认业务字段、对应 create command 与参数映射、用户限制与是否超出固定模板、以及"不得再次询问已知字段"。
5. **返回处理**：子任务成功则直接转述结果，不再查详情、不重复执行、不追加确认；返回"需要补充"则用业务语言询问缺失项，回答后携带全部上下文重新委派；超时/中断/写入状态未知则报告卡点，不更换批次号、不重试可能重复写入的操作。

> 用户主动提出限购、非八折、满件、满折、循环、多层、指定地区、减部分运费等表外变体时，用业务语言确认该变体的值，并在委派时标记"超出固定模板，先按当前 command help 判断能否执行"。

### B. 表单链路（一口价 / 拼团 / 订单换购 / 秒杀，或用户要求页面填表）

1. **识别活动类型**，确认在 9 类支持范围内。
2. **权限校验**：`woscli mall-goods query-supported-activity-types`。
3. **跳转创建页**：先比对当前页面 URL 是否已是目标创建页。

| 活动类型 | 表单说明 | 创建页别名 |
|---|---|---|
| 限时折扣 | @references/discount.md | `admin_ref://discount_create` |
| 满减邮 | @references/freepostage.md | `admin_ref://freepostage_create` |
| 满减满折 | @references/fulldiscount.md | `admin_ref://fulldiscount_create` |
| 满赠 | @references/fullgift.md | `admin_ref://fullgift_create` |
| 一口价 | @references/fixedprice.md | `admin_ref://fixedprice_create` |
| 拼团 | @references/groupon.md | `admin_ref://groupon_create` |
| N元N件 | @references/multioneprice.md | `admin_ref://multioneprice_create` |
| 订单换购 | @references/ordermarkup.md | `admin_ref://ordermarkup_create` |
| 秒杀 | @references/seckill.md | `admin_ref://seckill_create` |

   - 已在目标创建页且最近一次工具结果含"保存成功/发布成功/创建成功/提交成功" → 上一活动已完成，直接进入第 4 步重新生成并回填新活动。
   - 已在目标创建页、无完成信号但表单有非空数据 → 提醒"当前页面已有未保存的活动表单，请先在前端保存后再继续创建新活动"，终止本次创建。
   - 已在目标创建页且表单为空/初始态 → 直接进入第 4 步。
   - 不在目标页 → 调 `navigate_page` 跳转；跳转成功后**继续执行**，不要输出"页面已跳转，接下来需要做什么"之类的确认话术。
4. **生成表单草稿**：跳转结果返回后，读取该活动类型对应的表单说明 + @references/initial-fill-fields.md，**只生成 initial-fill-fields 中该活动小节列出的字段**。

| 活动类型 | 顶层必填字段 |
|---|---|
| 限时折扣 | `activityName`, `activityTime`, `limitPurchaseSetting`, `orderAutoClosedTime` |
| 满减邮 | `activityName`, `activityTime`, `postageSetting`, `activityDesc` |
| 满减满折 | `activityName`, `activityTime`, `fullDiscountRule` |
| 满赠 | `activityName`, `activityTime`, `fullGiftMethod`, `limitPurchaseSetting` |
| 一口价 | `activityName`, `activityTime`, `orderAutoClosedTime` |
| 拼团 | `title`, `startDate`, `endDate`, `durationTime` |
| N元N件 | `activityName`, `activityTime`, `multiOnePriceRule`, `limitPurchaseSetting` |
| 订单换购 | `activityName`, `activityTime`, `exchangePurchaseSetting`, `exchangeCountEveryOrder`, `limitPurchaseSetting` |
| 秒杀 | `activityName`, `activityTime`, `secKillPurchaseLimit`, `orderAutoClosedTime` |

   取值优先级：用户明确指定 > 本地待填表单/页面上下文 > 可稳定推断的信息 > 基于当前日期和临近节日/经营节点的合理策划。**不要因为缺少活动参数而追问**。
5. **调用表单填充工具**推送草稿到页面，并在**同一条**消息里给出简短正文（如"已为您填写活动表单，请检查后在前端保存/发布。"）。
6. **未保存态修改**：用户继续要求改字段时，基于最新草稿更新对应字段，重新读 schema 后再次调用填充工具推送，不要只用文字回复、不要让用户手改页面。
7. **结果判定**：活动是否真正创建以后续前端工具结果为准。出现"保存成功/发布成功/创建成功/提交成功"才回复已完成；出现"取消/关闭/放弃保存/返回列表/未保存/未提交"则回复活动未保存、任务未完成。

## 输出格式

- **接口链路成功**：转述子任务返回的创建结果（活动类型、活动名称、关键规则、活动时间），一句话说明已创建成功。
- **接口链路需要补充**：用业务语言列出待补字段清单，不暴露内部参数名。
- **表单链路中间态**（只填了表单、还没保存）：
  > 表单已填入当前页面，请检查后在前端保存/发布。

  多活动连续创建时：
  > 当前活动表单已填入当前页面，请检查后在前端保存/发布；保存/发布成功后我再继续下一个活动。

  中间态**不得**输出完整已填表单内容（Markdown 表格、JSON、字段列表都不行），也不得声称活动已提交/保存/发布/创建。仅针对用户关注的变更点或无法满足的要求做针对性说明。
- **表单链路结果态**：保存/发布成功后简短说明活动已保存成功；取消/未保存则说明活动未保存、任务未完成。两种情况都**不输出任何已填充的字段值**。
- **权限不足 / 不支持**：明确告知原因，并返回当前商户支持的活动类型清单。

## 注意事项与边界

- **两条链路互斥**：接口链路只用 `woscli activity ...` + `delegate_to_sub_agent`；表单链路只用 `woscli mall-goods ...` + `web_client_tool_call`。一次创建任务内不得跨链路混用工具。
- **接口链路硬边界**：`一口价`、`拼团`、`订单换购`、`秒杀` 无论权限查询是否返回支持，一律按接口链路不支持处理，不收集字段、不委派、不改用相似活动。
- **表单链路硬边界**：只做到"填表"，提交/落库由前端页面完成；仅调用填充工具且无保存结果时，绝不声称活动已创建成功。
- 已保存/已发布的活动不再走"未保存修改"流程；用户要改需走前端已提交活动的编辑能力，本 skill 不通过接口修改已提交活动。
- 活动名称禁止只用"活动类型+活动"这类单一模板（如"秒杀活动"）。必须体现至少两个信息维度（节日/时令/品类/人群/利益点 + 活动类型），控制在表单最大长度内（多数活动 30 字）。
- 时间字段：多数活动 `activityTime.start/end` 用 `YYYY-MM-DD HH:mm:ss` 字符串；**拼团** `startDate/endDate` 用毫秒时间戳，必须先生成标准时间字符串再调用 `string_to_timestamp(time_string="...", fmt="%Y-%m-%d %H:%M:%S", timezone_offset=8, output_millis=True)` 取返回值，禁止心算或直接填字符串。
- 开始时间必须晚于当前时间（未指定时取当前时间后 5–15 分钟并对齐整 5 分钟），结束时间必须晚于开始时间。用户指定的过去时间若语义是"立即/今天"则自动修正；若是明确的历史绝对日期，必须追问确认。
- 门槛、优惠力度、库存、成团人数、限购等影响商家权益的参数，用户未提供时按偏保守、可回退的默认策划生成，避免过高优惠或过大库存承诺。
- 面向用户回复只使用业务语言，禁止暴露 `activityName`、`activityTime.start`、`exchangePurchaseSetting` 等内部字段名、字段路径、schema 结构或枚举值。
- `references/initial-fill-fields.md` 只定义首次创建默认自动填充的字段，**不是**可修改字段清单；回答"能改哪些字段"时以当前页面表单工具的 `inputSchema` 为准，schema 中只有唯一值/固定值/只读的字段不算可修改字段。
- 读取表单说明是内部步骤，除非用户明确索要字段定义，不要向用户输出字段清单。
