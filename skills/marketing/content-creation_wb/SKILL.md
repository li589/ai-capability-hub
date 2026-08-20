---
name: content-creation
description: 营销内容创作与分发。用户要写文案、写种草文、写公众号推文、发布公众号图文、生成小红书或朋友圈图文并保存入库时触发，按是否需要发布分三条链路。
displayName:
  zh: 内容创作与分发
  en: Marketing Content Creation and Publishing
displayDescription:
  zh: 创作营销文案、公众号图文、小红书和朋友圈内容；可按渠道生成素材并发布或保存入库。
  en: Create marketing copy, WeChat Official Account articles, Xiaohongshu notes,
    and Moments posts; generate channel-ready assets and publish or save them as
    needed.
disable-model-invocation: true
---

# 内容创作

## 功能说明

本 skill 统一承接三类营销内容创作诉求，按"是否需要发布/入库"做三级路由：

1. **纯文案创作（不发布）**：直接输出可用文案文本，不调用任何发布接口。
2. **公众号图文创作并发布**：校验公众号绑定、生成封面与配图、创作富文本正文，调用 `create_article` 落到公众号草稿箱。
3. **小红书 / 朋友圈图文创作并保存**：按商品生成图片、按渠道创作图文，调用 `smart-content save` 入库。

三条链路互相排他，**必须先判定链路再执行**，不得在纯文案链路里调用发布接口，也不得把公众号内容存进社交笔记库。

## 触发场景

- 写文案、写 copy、写种草文、写一段介绍、写产品描述、给我一个文案版本、写朋友圈文案、写品牌故事、帮我写一篇关于 XX 的文案。
- 写公众号文章并发布、创建并发布公众号推文、生成并发布公众号图文。
- 生成小红书图文并保存 / 入库 / 发布、生成朋友圈图文并入库、把刚才那篇小红书图文保存一下。
- 二次保存输入：只要出现"保存/入库/发布"意图词，且渠道词为"小红书"或"朋友圈"，同样进入链路 ③。

## 三级路由（先判链路，再执行）

**第一问：用户是否要求发布 / 保存 / 入库？**

| 判定 | 链路 | 核心动作 |
|---|---|---|
| ① 否 —— 只要文案、明确说"不用发布""草稿就行" | **纯文案创作** | 只输出文本，可选 `mall-goods get_goods_detail` 取素材 |
| ② 是，且渠道是**公众号** | **公众号图文发布** | `channel check-channel-bind` → 生图 → `mall-goods create_article` |
| ③ 是，且渠道是**小红书 / 朋友圈** | **社交图文保存** | 生图 → `smart-content save` |

边界锁死规则（互相点名，不得越界）：

- 用户只说"写文案/写推文草稿/给我几版文案/写种草文"且不涉及发布 → 走 ①，**禁止**调用 `create_article` 或 `smart-content save`。
- 用户要发布到**公众号** → 走 ②，**禁止**用 `smart-content save`。
- 用户要生成**小红书或朋友圈**图文并保存 → 走 ③，**禁止**用 `create_article`。
- 渠道词同时出现"小红书"和"朋友圈"，或渠道识别失败 → **必须追问确认渠道**，不得自行默认。
- 用户既没给主题也没给商品 ID（完全空请求）→ 终止，提示"请提供文案主题或商品 ID 后重试"。

## 调用方式

> **格式铁律**：`woscli <分类> <命令名> --参数名 参数值`。分类和命令名是位置参数，**都不加 `--` 前缀**；所有业务参数以独立 flag 逐一传入，**禁止打包成 JSON 字符串**（`--content` 这类本身就是 JSON 值的参数除外）。
>
> 若返回 `执行命令需要指定 command 参数`，判定为分类/命令名被误当成参数，**不要**添加 `--command`/`--cmd`/`--category`，按固定命令头重写重试一次。遇到报错或不清楚出入参时，先执行对应命令的 `--help`。

| 用途 | 命令 |
|---|---|
| 查询商品详情 | `woscli mall-goods get_goods_detail --goods_ids [1001,1002]` |
| 查询公众号是否绑定 | `woscli channel check-channel-bind` |
| 图生图（有原图） | `woscli image editImage --imageUrl "<原图URL>" --prompt "<描述>" --size 2048x2048 --count 1` |
| 文生图（无原图） | `woscli image generateImage --prompt "<描述>"` |
| 创建公众号文章 | `woscli mall-goods create_article --title "..." --cover_image_url "..." --content_info "<p>...</p>" --content_digest "..."` |
| 保存社交图文 | `woscli smart-content save --title "..." --content '<JSON>' --contentType 1 --source 1 --creator "system"` |

参数细节：
- 公众号发布参数见 @references/article-publish-params.md
- 通用工具（`get_goods_detail` / `editImage` / `save`）见 @references/woscli-tools.md
- 小红书图文参数见 @references/xhs-note-params.md
- 朋友圈图文参数见 @references/moments-note-params.md
- 朋友圈 6 选 1 风格映射见 @references/style-mapping.md

**图片 prompt 固定禁止语**（每次调图片接口都必须原文追加在 prompt 末尾，不得省略或改写）：

```
不允许在图片上出现任何具体价格金额、满减数字、倒计时时长、折扣比例等捏造事实内容。
```

## 支持的操作

### 链路 ①：纯文案创作（不发布）

1. **解析参数**：`topic` 或 `goodsIdList`（二选一必填）、`copyType`、`writingStyle`、`wordCount`。后三项未指定时自动推断，**无需向用户确认**。

| 文案类型 | 默认字数 | 适用场景 |
|---|---|---|
| 公众号文案草稿 | 800–1500 字 | 完整推文初稿 |
| 小红书种草文 | 300–500 字 | 含 emoji，口语化 |
| 产品描述 | 150–300 字 | 详情页或简介 |
| 朋友圈文案 | 50–150 字 | 简短，适合配图发圈 |
| 品牌故事 | 500–800 字 | 叙事风，传递调性 |
| 活动推广文案 | 200–400 字 | 突出利益点，有号召 |

   未指定类型时：有商品 ID → 产品描述；只有主题 → 公众号文案草稿。
   风格推断：生活用品/家居/食品/美妆/服饰 → 小红书种草；旅行/自然/户外/季节 → 故事叙事风；节日/社交/日常 → 朋友圈轻松风；品牌/产品发布/企业介绍 → 品牌正式风；促销/活动/限时优惠 → 电商促销风；其他 → 小红书种草。

2. **取素材（仅商品模式）**：`woscli mall-goods get_goods_detail --goods_ids [...]`，使用 `title`/`description`/`tag`；`description` 为 null 时结合 `title`、`category_full_url`、`tag` 创作。
3. **创作**：需要标题的类型（公众号文案草稿、品牌故事、活动推广文案，或用户明确要求）生成悬念型/痛点型/反直觉型/利益相关型/强情绪型 5 类备选，选与风格最契合的一个；标题 ≤30 字、**禁止 emoji**。正文按"开篇钩子 → 主体 → 留余味结尾"展开。
4. **输出纯文本**，不做 HTML、不生成封面、不调用任何发布接口。多版本时按"版本一/版本二"分隔。

### 链路 ②：公众号图文创作并发布

1. **模式判断**：有商品 ID 列表 → 商品模式（还需 `goodsCountPerArticle`、`writingStyle`，缺失必须追问）；只有主题 → 通用模式（`writingStyle` 缺失时自动推断，不追问）。
2. **校验公众号绑定**：`woscli channel check-channel-bind`。`isBound === false` → 终止并返回 `CHANNEL_NOT_BOUND`；查询失败 → `CHANNEL_BIND_QUERY_FAILED`。
3. **选品并查详情（仅商品模式）**：**强制随机洗牌**——给每个商品 ID 生成 1–9999 独立随机权重，按权重升序得 `shuffledGoodsIdList`，取前 `min(goodsCountPerArticle, m)` 个查询；**禁止直接取列表前 N 个**。查回结果按选中顺序重排。返回数量不足时沿 `shuffledGoodsIdList` 往后补查**一次**，不循环。
4. **生成封面图**：商品模式用 `editImage` 基于重排后第一个商品的 `image_url` 做风格化；通用模式用 `generateImage` 从零生成。prompt 末尾必须追加固定禁止语。
5. **创作正文**：标题（5 类备选选一，≤30 字，无 emoji）→ 摘要（≤120 字）→ 配图（商品模式每个商品 1–2 张且**图文严格一一对应、不得跨商品混用**；通用模式至少 1 张、建议 2 张插入正文中）→ 富文本 HTML 正文。字数：商品模式 1 品约 2500 字、2 品约 3500 字、3 品及以上约 4500–5000 字；通用模式约 2000 字。
6. **发布**：`woscli mall-goods create_article --title "..." --cover_image_url "..." --content_info "..." --content_digest "..."`。

### 链路 ③：小红书 / 朋友圈图文创作并保存

1. **解析参数**：`channel`（`xhs`/`moments`，必填）、`goodsIdList`、`goodsCountPerNote`（xhs > 0；moments 1–5）、`writingStyle`。`target_age`/`target_sex` 仅 `xhs` 可选，`moments` 传了也忽略。
   - `moments` 风格 6 选 1：`日常生活型`/`情绪价值型`/`新品发布型`/`互动点赞评论型`/`换季推广型`/`促销折扣型`；未传默认 `日常生活型`（**不做品类兜底推断**），且必须明确告知用户选了哪个。
2. **选品**：同链路 ② 的随机洗牌规则，按选中顺序重排结果，下架补足一次。
3. **按商品逐张生图**：每张图只用**同一个商品**的信息——`--imageUrl` 取当前商品 `image_url`，prompt 里的商品名、卖点、场景也只能来自同一商品。调用前做一致性自检，不一致必须停止重新构造。默认不在图里生成任何中文文案字。单张失败跳过继续，整篇全失败才返回 `IMAGE_GENERATE_FAILED`。
4. **创作图文**：`xhs` 生成标题 + 3–5 个标签 + 正文（≤800 字）；`moments` 不生成标题和标签，正文 100–400 字（可放宽到 600）。
5. **保存**：

```bash
# xhs
woscli smart-content save \
  --title "{标题}" \
  --content '{"title":"{标题}","image_url_list":["{图片URL列表}"],"content_info":"{正文}","content_tags":["{标签列表}"]}' \
  --contentType 1 --source 1 --creator "system"

# moments
woscli smart-content save \
  --content '{"image_url_list":["{图片URL列表}"],"content_info":"{正文}"}' \
  --contentType 2 --source 1 --creator "system"
```

## 输出格式

### 链路 ①（纯文案）

```
【标题】
（需要标题时输出）

【正文】
（文案正文）
```

无标题类型（朋友圈文案、产品描述、小红书种草文）直接输出正文。

### 链路 ②（公众号）

```
文章已保存至草稿箱！

标题：{文章标题}
文章ID：{article_id}
草稿位置：`admin_ref://feature_article_list`，进入页面后点击「草稿」即可查看
```

### 链路 ③（小红书 / 朋友圈）

**xhs**：
```
标题：{最终提交的完整标题}

正文：
{最终提交的完整正文}

标签：
#{标签1} #{标签2} ...

图片：
1. {图片URL1}
2. {图片URL2}
```

**moments**：
```
正文：
{最终提交的完整正文}

图片：
1. {图片URL1}
2. {图片URL2}
```

### 失败响应（链路 ②③ 通用）

```json
{ "success": false, "error": "错误描述", "error_code": "错误码" }
```

| 错误码 | 场景 |
|---|---|
| `MISSING_REQUIRED_PARAMS` | 缺少必填参数（无主题也无商品 ID / 渠道未确认） |
| `CHANNEL_BIND_QUERY_FAILED` | 公众号绑定状态查询失败 |
| `CHANNEL_NOT_BOUND` | 公众号未绑定 |
| `GOODS_QUERY_FAILED` | 商品详情查询失败 |
| `GOODS_NOT_FOUND` | 未查询到任何可用商品 |
| `IMAGE_GENERATE_FAILED` | 封面图/全部配图生成失败 |
| `ARTICLE_CREATE_FAILED` | 公众号文章创建失败 |
| `NOTE_SAVE_FAILED` | 社交图文保存失败 |

## 注意事项与边界

- **链路互斥**：纯文案链路不得调用 `create_article` 或 `smart-content save`；公众号链路不得用 `smart-content save`；社交图文链路不得用 `create_article`。
- **链路 ③ 的展示纪律**：保存成功后**直接向用户完整展示最终图文内容**（不摘要、不截断、不改写）；**不得**出现"已保存/保存成功/已入库/发布成功"等状态提示，**不得**展示内容 ID / noteId / contentId，**不得**告知去哪里查看或附加后台路径。用户问在哪看，就回答内容已在本次对话中完整展示，历史内容需回到对应会话查看。
- **内容真实性**：所有卖点、功效、材质描述必须来自 `get_goods_detail` 的真实字段；禁止捏造价格、活动、库存、时效。`category_full_url`/`classify_full_url` 只作背景知识，**禁止原文写进正文**。
- **图片 prompt** 每次都必须追加固定禁止语；图片来源只能是接口返回的真实 URL，不得编造。
- **写作禁区**：禁止开篇废话（"本文将为大家介绍…"）、禁止堆砌形容词、禁止每段同一句式收尾、禁止用 1./2./3. 清单代替叙述、禁止"我有个朋友/同事"式话术、禁止"说实话/老实说/你看/记得"等 AI 口头禅、结尾不做总结式教学。
- **文案美学**：中文句长 15–25 字为主，偶尔 5–8 字短句制造节奏；前 3 行决定读者是否继续；多用"我们"而非"你们"。
- 命令报错时先执行对应 `--help` 确认参数后重试一次，仍失败按对应错误码如实报告。
- 不硬编码任何 Token 或密钥；凭证由 woscli 本地会话提供。
