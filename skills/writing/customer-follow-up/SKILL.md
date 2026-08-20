---
name: customer-follow-up
description: 为导购生成客户跟进推荐话术（商品/活动/优惠券），静默执行只输出文案。触发词：客户跟进、跟进话术、导购话术、推荐商品给客户、生成推荐文案、换一版话术、重新生成。
displayName:
  zh: 客户跟进话术
  en: Customer Follow-up Messaging
displayDescription:
  zh: 为导购生成可直接发送的客户跟进话术，支持商品、活动和优惠券推荐及多轮改写。
  en: Generate ready-to-send customer follow-up messages for sales associates,
    including product, campaign, and coupon recommendations with iterative
    rewrites.
disable-model-invocation: true
---

# 客户跟进话术推荐

## 功能说明

调用 `woscli agent-guide sceneRecommendContent` 获取场景推荐数据，转化为可直接发送给客户的导购话术，覆盖商品、活动、优惠券三类推荐内容。

### 严格静默模式（最高优先级，优先于所有其他规则）

本 skill 为**静默执行模式**。构造参数、调用 woscli、规范化数据等全部中间步骤在后台完成，**最终只输出推荐文案本身**。

**绝对禁止**输出以下任何内容：

- 提及技能名称或加载过程（如「我将使用 customer-follow-up 技能…」）
- 描述执行步骤（如「现在我来构造请求参数…」「正在调用…」）
- 前置说明（如「根据返回结果…」「为您生成导购话术：」）
- 后置总结（如「以上是本次推荐」）
- 展示中间数据（原始 JSON、命令、规范化结果）
- 任何步骤编号、执行状态描述、emoji

**唯一允许的输出**：纯推荐文案，无任何前缀、后缀或包装文字。你的第一个字就是文案的第一个字，最后一个字就是文案的最后一个字。

**为什么**：输出直接发送给终端用户（导购员），而非开发者。过程描述会污染文案。你是「话术生成引擎」，不是「分析助手」。

## 触发场景

- 帮我给这个客户生成跟进话术
- 推荐点商品给这个客户
- 生成一条导购推荐文案
- 这版话术不行，换一版 / 再详细点 / 结合节气重写（→ 走重新生成）

## 调用方式

```bash
woscli agent-guide sceneRecommendContent --request '<JSON请求体>'
```

JSON 请求体必须用单引号包裹。

### 请求体字段

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `bosId` | number | 业务组织 ID | `4000172354837` |
| `vid` | number | 版本/门店 ID | `6000312123837` |
| `customerWid` | number | 客户微信 ID | `100542810` |
| `guiderWid` | number | 导购微信 ID | `1000589819` |
| `guiderId` | string | 导购工号 | `"11"` |
| `sceneInfo` | object | 场景配置信息 | 见下 |
| `recommendContent` | object | 推荐内容配置 | 见下 |

**sceneInfo**：

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `sceneCode` | string | 场景编码 | `"12321"` |
| `intelligentRec` | boolean | 是否开启智能推荐 | `false` |
| `recommendList` | string[] | 推荐模块列表 | `["recommendGoods","recommendCoupon"]` |

`recommendList` 可选值：`recommendGoods`（商品）、`recommendCoupon`（优惠券）、`recommendActivity`（活动）。该列表决定请求哪些类型的推荐，未列出的类型不会返回。

**recommendContent**：

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `index` | number | 推荐轮次索引，首次填 `1`，重新生成时递增 | `2` |
| `reGenerateType` | number | 重新生成类型：`1`=在原结果上优化，`2`=全新生成 | `1` |
| `reGenerateRequirement` | string | 重新生成的附加要求，首次调用可留空 | `"再写详细点，结合最近的节气"` |

### 完整示例

```bash
woscli agent-guide sceneRecommendContent --request '{"bosId":4000172354837,"vid":6000312123837,"customerWid":100542810,"guiderWid":1000589819,"guiderId":"11","sceneInfo":{"sceneCode":"12321","intelligentRec":false,"recommendList":["recommendGoods","recommendCoupon"]},"recommendContent":{"index":2,"reGenerateType":1,"reGenerateRequirement":"帮我把推荐文案再写详细点，最好结合最近的节气信息"}}'
```

参数缺失时**仅**在这种情况下才可向用户提问补充，补齐后立即回到静默模式。

## 支持的操作

### 内部执行流程（全程静默）

1. 从上下文提取参数，构造 JSON 请求体。
2. 调用 `woscli agent-guide sceneRecommendContent`，不展示命令与返回。
3. 通过 function_call 协议调用 `guide_recomment_content_callback` 对推荐数据做规范化，无任何用户可见输出。
4. 生成最终文案——这是**唯一**允许产生输出的步骤。

生成前先检查 `recommendContent.reGenerateRequirement`：不为空则结合该要求调整文案内容与风格；为空或 null 则按模板正常生成。

### 分类判断

| 条件 | 动作 |
|---|---|
| `goodsId` 不为 null | 生成商品推荐文案 |
| `activityId` 不为 null | 生成活动推荐文案 |
| `couponId` 不为 null | 生成优惠券推荐文案 |

三类文案各自独立，有则生成、无则跳过；多个同时存在时按 商品 → 活动 → 优惠券 顺序自然衔接。

### 重新生成

用户要求「换一版」「再详细点」「按某要求重写」时，递增 `index`，设置 `reGenerateType`（`1` 优化 / `2` 全新），把用户要求原样填入 `reGenerateRequirement` 后重新调用，输出仍然只有文案。

## 输出格式

### 商品推荐

可用字段：`goodsName`、`goodsMinPrice`、`goodsMaxPrice`。突出商品名，价格相同时只说一个数，强调卖点营造紧迫感。

```
为您推荐：【{goodsName}】
售价：{价格} 元

库存有限，手慢无！
```

### 活动推荐

可用字段：`activityName`、`activityTag`、`activityMinPrice`、`activityMaxPrice`、`validDateDesc`。

```
限时活动：【{activityName}】
活动标签：{activityTag}
活动价：{activityMinPrice}-{activityMaxPrice} 元
{validDateDesc 不为 null 时输出 validDateDesc + "，错过再等一年！"}

赶紧行动，名额有限！
```

### 优惠券推荐

可用字段：`couponName`、`couponTag`。强调「领取即用」降低使用门槛。

```
专属优惠券：【{couponName}】
{couponTag 不为 null 时输出 "标签：" + couponTag}

领券下单立减，数量有限，先到先得！
```

### 完整示例（应输出的全部内容）

商品 + 活动 + 优惠券全部存在：

```
为您推荐：【夏季新款连衣裙】
售价：299-599 元
库存有限，手慢无！

限时活动：【618年中大促】
活动标签：满减
活动价：199-499 元
仅剩3天，错过再等一年！

专属优惠券：【满300减50】
领券下单立减，数量有限，先到先得！
```

全部为 null 时，只输出一句：

```
当前暂无推荐内容，请稍后再试
```

## 注意事项/边界

### 硬性输出约束

1. **禁止 emoji**：不使用任何表情符号，包括 🔥🎉🎫⏰💡 等。
2. **禁止输出图片链接**：`goodsImgPicUrl` 仅供内部判断，绝不出现在文案中。
3. **总字数不超过 500 字**（含标点、换行符），生成后自查，超出则精简。
4. **禁止任何前缀文字**：无开场白、无分析过程、无步骤说明。
5. **禁止任何后缀文字**：无总结、无提示、无附加说明。
6. **null 字段直接跳过**：不输出「null」字样或空白占位符。
7. **不虚构数据**：数据为 null 的模块直接跳过，不生成对应文案。

### 异常处理

| 场景 | 处理方式 |
|---|---|
| `goodsId`、`activityId`、`couponId` 均为 null | 只输出「当前暂无推荐内容，请稍后再试」 |
| 仅有商品信息 | 只生成商品文案，不硬凑活动和优惠券 |
| 仅有活动信息 | 只生成活动文案，不虚构商品数据 |
| 仅有优惠券信息 | 只生成优惠券文案 |
| 价格信息缺失 | 用「优惠价」代替具体价格 |
| `goodsMinPrice == goodsMaxPrice` | 只说一个价格，禁止输出「259-259元」 |
| `validDateDesc` 为 null | 跳过活动截止时间描述 |
| `couponTag` 为 null | 跳过标签行 |
| woscli 返回 `error` 不为 null | 输出「系统繁忙，请稍后重试」，不展示原始错误 JSON |

### 禁用表述

- 「随便看看」「您决定就好」
- 无价格锚点的模糊表述
- 过期优惠信息
- 输出「null」字样或空白占位符
- 在对应数据为 null 时虚构活动/优惠券描述
