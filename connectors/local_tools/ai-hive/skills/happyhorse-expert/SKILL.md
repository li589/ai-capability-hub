---
name: happyhorse-expert
display_name: Happyhorse 专家
display_name_en: Happyhorse Expert
description: "通过指导agent智能调度 Happyhorse 模型，针对\"图生视频、动态表现力、多图角色一致性\"等场景深度优化 prompt 工程，支持 T2V/I2V/R2V 三模态、首帧控制、多角色编排、音画同步与产品动态展示，输出具备角色一致性的高质量视频与流畅运镜。"
description_zh: "通过指导agent智能调度 Happyhorse 模型，针对\"图生视频、动态表现力、多图角色一致性\"等场景深度优化 prompt 工程，支持 T2V/I2V/R2V 三模态、首帧控制、多角色编排、音画同步与产品动态展示，输出具备角色一致性的高质量视频与流畅运镜。"
description_en: "Agent optimizes Happyhorse prompts for image-to-video, multi-character scenes, audio sync, smooth camera."
category: media
version: 1.1.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片与视频
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_video 与 get_generation_task
triggers:
- "Happyhorse"
- "happyhorse"
- "Happy Horse"
- "首帧控制"
- "产品动画"
- "角色融合"
- "多角色视频"
- "image to video"
- "product motion"
---

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `modelType`（可选，string）：资源类型枚举 `TEXT` / `IMAGE` / `VIDEO`（本 Skill 用 `VIDEO`）
- `cursor`（可选，string）：分页游标

### `upload_media_from_path`
- `path`（必填，string）：用户授权的本地文件绝对路径
- `kind`（可选，string）：资源类型 `video`

### `generate_video`
- `model`（必填，object）：来自 `list_models(modelType="VIDEO")` 的模型引用
- `prompt`（必填，string）：描述主体、动作、镜头、光线、风格与声音
- `durationSeconds`（可选，integer）：时长（公开值 3-15 秒取整，以 `list_models` 返回的该模型枚举为准）
- `count`（可选，integer）：候选数量（默认 1）
- `size`（可选，string）：像素尺寸（仅用支持的枚举值）
- `ratio`（可选，string）：画幅（仅用支持的枚举值）
- `referenceMediaIds`（可选，array）：参考媒体 mediaId 列表
- `firstFrameMediaId`（可选，string）：首帧 mediaId
- `lastFrameMediaId`（可选，string）：尾帧 mediaId

### `get_generation_task`
- `taskId`（必填，string）：`generate_video` 真实返回的 taskId



> 所有工具的真实返回值以服务端响应为准；本章节参数表是客户端约束说明。

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token


## 能力范围

本 Skill 专注 Happyhorse 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_video 工具完成视频生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 video 列出当前可用模型及价格快照，从中筛选 Happyhorse 对应的 publicModelId。
- upload_media_from_path：上传本地图片/视频并返回 mediaId，用于首帧控制、参考图与角色锚点。
- generate_video：使用选定模型与 prompt 创建视频任务。
- get_generation_task：使用 taskId 查询任务状态与结果。

## 适用场景

- 用户明确表达使用本 Skill 对应的模型能力或场景需求
- 用户提供素材（图片/视频）需要在该模型擅长的领域生成结果
- 用户希望跨场景复用同一模型能力保持风格一致
- 用户对生成结果的某项特性（文字渲染/真实质感/艺术风格/运镜/动态表现）有明确要求

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 涉及真实人脸的素材（部分模型平台会拦截）—— 改用卡通/虚拟人物描述
- 涉及未成年人、裸露、暴力、仇恨内容的素材
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览


## Happyhorse 擅长什么

Happyhorse 的核心优势是动态表现力与多图参考一致性，擅长从静态图片生成有运动感的视频，并保持多角色外貌不串。

| 能力 | 说明 |
|---|---|
| 动态表现力 | 动作连贯流畅，力量感充足，大幅度动作稳定可用 |
| 多图参考一致性 | 多角色外貌保持不串、角色与场景自由组合、九宫格/分镜参考一致性强 |
| 长指令遵循 | 2500 字符后的指令仍稳定遵循，单条 Prompt 支持 6-8 个连续场景自动调度 |
| 视觉质感 | 自然柔和的皮肤纹理，面部特写表现力优秀，支持镜头语言术语（正反打、跟拍等） |
| 音频能力 | 台词语速语气自然变化，BGM 可控，音画同步精度高 |

## 模型规格

| 维度 | 规格 |
|---|---|
| 单次时长 | 3-15 秒（取整） |
| 分辨率 | 720p / 1080p |
| 宽高比 | 自由宽高比 |
| 模态 | T2V（文生视频）/ I2V（首帧生视频）/ R2V（参考图生视频） |

## OpenAPI 交叉验证：模型 ID（SDK models-reference.md，2026-08）

> 以下 `publicModelId` 来自 AI-HIVE OpenAPI `models-reference.md`（经 SDK 交叉验证）。
> 在 AI-HIVE Connector 中**运行时一切以 `list_models` 实际返回为准**；下表用于预校验，不臆造未返回字段。

| 任务类型 | publicModelId |
|---|---|
| 文生视频 T2V | `public_model_happyhorse_t2v` |
| 图生视频 I2V | `public_model_happyhorse_i2v` |
| 参考生视频 R2V | `public_model_happyhorse_r2v` |
| 视频编辑 | `public_model_happyhorse_video_edit` |

> 注：OpenAPI 另列有 `video_edit`（视频编辑）变体。本 Skill 的 prompt 指南聚焦 T2V/I2V/R2V；若 `list_models` 返回 video_edit 且用户需编辑已有视频，源视频放入 `referenceMediaIds` 并在 prompt 写清修改范围，或改用编辑能力更强的 Seedance 2.5（见 model-scenarios.md 选派逻辑）。

## 三种模态选择

| 用户意图 | 模态 | 参数 | 说明 |
|---|---|---|---|
| 从零构建完整场景 | T2V | 无 referenceMediaIds / 无首尾帧 | 从 prompt 生成 |
| 让静态画面动起来 | I2V | firstFrameMediaId | 从指定图片开始，生成自然延续运动 |
| 编排多角色舞台剧 | R2V | referenceMediaIds（多图）| 用图号引用角色，多角色交互 |
| 首帧 + 多角色 | I2V+R2V | firstFrameMediaId + referenceMediaIds | 首帧控制开头，参考图锚定角色 |

## T2V 文生视频 Prompt 指南

### 1. 风格锚定全局基调（开头第一句）

用一句话锁定视觉基调，让模型从第一帧就明确风格方向。

示例：真人写实+科幻UI，系统公告，电影级别运镜，电影级别分镜，突出场景真实感和情绪张力，8K UHD 全画幅原生超高清。

### 2. 景别+运镜前置（骨架）

景别决定画面的"呼吸感"，运镜决定"流动感"，必须在描述动作之前确定。

示例：中景，三人环顾寻找声源；全景，金色公告面板照亮的房间；特写手部，珠子还在微微发光。

### 3. 光影描述（质感关键）

不要只写"光线好"，要具体描述光源方向、色温、阴影关系。

示例：暖黄烛光在殿内缓缓流动，照亮了皇帝的面部轮廓和周围模糊的人影；阳光透过窗户，在古朴的木质家具上投下柔和的光影；明暗对比强烈，逆光剪影。

### 4. 长视频（大于 10 秒）使用时间戳分镜

示例：[00:00] 中景角色A走入画面环顾四周；[00:03] 特写角色A眼神变化瞳孔微缩；[00:06] 全景场景全貌展示远处角色B出现；[00:10] 近景两人对视气氛紧张。

### 5. 约束指令要具体

有效约束指向具体问题，不要泛泛而谈。

推荐：禁止出现字幕、禁止出现背景音乐、画面无穿帮漂移、光影统一、口型同步台词、全程画面内无任何水印或 logo。

不推荐：生成高质量的视频。

### 6. Prompt 长度与视频时长成正比

建议按每增加 1 秒约增加 30-50 字的节奏扩展 Prompt 内容，增量主要放在动作描述和分镜细化上。

## I2V 首帧生视频 Prompt 指南

### 核心原则：简短即正义

首帧图片已承载大量信息（人物外貌、服装、场景环境），Prompt 聚焦于"变化"和"动态"，不重复描述静态信息。

短 Prompt 示例（适合 5-6 秒）：角色沉思内心了然；妹妹将我迷晕在房间里她自己上了花轿；轿子向着庭院外走去走出将军府。

### 需要精细控制时采用分层结构

分层：基础参数约束（禁止字幕禁止BGM）+ 场景时间（白天）+ 景别运镜（手部特写快速上移至脸部小幅慢推）+ 画面（角色站在玄关手持手机瞳孔一缩脸色瞬间发白）+ 音效（清脆手机提示音微弱震动轻响急促吸气声）。

### 光影描述避免"光影跳变"

虽然图片已定义基础光影，但 Prompt 中的光影描述能指导模型在动态过程中维持和演变光影效果。

## R2V 参考图生视频 Prompt 指南

### 1. 开篇建立"图号-角色"映射

写法A（角色名+图号）：夏风禾是图1，父亲是图2，后妈是图3，场景是图4。

写法B（直接在分镜中引用，推荐）：[00:00] 近景图2对着图3质问。

### 2. 时间戳分镜编排多角色交互

示例：[00:00] 近景图2正要开口说话；[00:02] 近景图3大步踏出一步扑通跪在大殿正中；[00:04] 近景图3抬起头目光坚定。

### 3. 音效和台词标注

台词标注格式：图号台词情绪具体台词内容。

示例：图1台词震惊妈你疯了；图2台词激动我是疯了只有疯子才会给你们当牛做马三十年；BGM/音效围裙被丢到地上的声音。

### 4. 场景参考图的使用

将场景图作为独立参考图在开头声明，分镜中只引用角色图。示例：场景是图4，[00:00] 中景图1内图2对着图3质问。

## 景别选择速查

| 景别 | T2V | I2V | R2V | 适用场景 |
|---|---|---|---|---|
| 特写 | 强推 | 一般 | 强推 | 面部表情、手部动作、物品细节 |
| 近景 | 一般 | 强推 | 强推 | 对话场景、情绪表达 |
| 中景 | 强推 | 一般 | 一般 | 日常互动、动作展示 |
| 全景 | 一般 | 一般 | 一般 | 场景建立、环境展示 |
| 远景 | 一般 | 不适用 | 不适用 | 开场/收束、大场景 |

## 常见误区与修正

误区一：I2V 中重复描述图片已有信息。修正：Prompt 应聚焦于"变化"和"动态"，不重复静态信息。

误区二：T2V 短视频使用分镜结构。修正：4-6 秒视频不需要时间戳分镜，一段连贯叙事更适合短时长，分镜建议 8 秒以上再使用。

误区三：R2V 缺少图号映射表。修正：务必在开头建立图号-角色映射，不能直接写"图2对着图3质问"。

误区四：约束指令过于笼统。修正：有效约束应指向具体问题，如"画面无穿帮漂移"、"口型同步台词"、"全程无字幕"。

## Prompt 骨架（通用模板）

逐场景组装时，按以下字段结构化；缺省字段留空，不强行填充：

| 字段 | 含义 | 示例 |
|---|---|---|
| 用途 | 视频用在哪（产品讲解 / 宣传片 / 分镜） | 产品宣传短片 |
| 主体 | 核心对象 / 人物 | 产品 + 模特 |
| 镜头脚本 | 分镜与时长（0-4s / 4-8s …） | 0-4s 推进特写 |
| 运镜 | 相机运动 | 环绕 / 横移 |
| 视觉风格 | 电影级 / 动画 / 实拍 | 电影级调色 |
| 光线色彩 | 光向与色调 | 暖光、霓虹 |
| 音频 | 原生音 / 配乐 / BGM | Synthwave 124BPM |
| 保留项 | 图生视频须保留要素 | 人物不变形 |
| 输出规格 | 时长 / 画幅 / 分辨率 | 12s / 9:16 / 480P |

组装顺序：用途 → 主体 → 镜头脚本 → 运镜 → 视觉风格 → 光线色彩 → 音频 → 保留项 → 输出规格。仅保留有值的字段。

## 调用流程

1. get_user_info 检查余额。
2. list_models(modelType=VIDEO) 获取 Happyhorse 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 分析用户需求选择模态：T2V（文生）/ I2V（首帧）/ R2V（多图角色）。
4. 如需参考图，upload_media_from_path 逐张上传得到 mediaId。
5. 按模态组装 prompt（参见上方对应模态指南）。
6. generate_video 提交任务，get_generation_task 跟踪到 completed。

## 输入检查

- 明确模态（T2V / I2V / R2V）。
- 参考图仅使用用户主动选择的文件。
- 时长仅使用服务端支持的枚举值（3-15 秒取整）。
- 画幅使用服务端支持的枚举值。
- I2V 时 Prompt 聚焦变化与动态，不重复静态信息。
- R2V 时必须在开头建立图号-角色映射。

## 生成后建议

- 尝试不同模态（I2V 不理想可改 T2V 或 R2V）。
- 调整景别（特写/近景/中景/全景/远景）。
- 增减参考图数量。
- 调整时长（短视频用连贯叙事，长视频用时间戳分镜）。
- 添加或修改约束指令。

## 事实与合规边界

1. 只使用 list_models 真实返回的 publicModelId 与 pricingSnapshot。
2. 不虚构商品信息、不制造虚假代言。
3. 不擅自改变参考图中人物的外观或身份特征。
4. 涉及真人时须确认用户拥有合法授权，不制造公众人物虚假内容。
5. 对未成年人、裸露、暴力内容采取保守判断。
6. Token 只在 AI-HIVE Connector 凭证设置中填写。

## 费用授权

- generate_video 调用即按服务端计费扣费。
- 失败、被拒绝或余额不足时不重试扣费。
- 用户修改模型、prompt、时长、画幅或参考素材后必须重新调用。

## 状态与错误处理

### 余额不足 / 任务被拒（INSUFFICIENT_BALANCE / REJECTED）

**AI-HIVE 官网**：https://ai-hive.iclip.cn

**充值路径**（账户已存在）：
1. 访问 https://ai-hive.iclip.cn → 登录 AI-HIVE 账户
2. 进入「账户中心」/「钱包」/「充值」页面
3. 选择充值套餐或自定义金额 → 完成支付
4. 充值成功后回到 WorkBuddy，无需重新连接 Connector，直接重试任务

**注册路径**（首次用户）：
1. 访问 https://ai-hive.iclip.cn → 点「注册」按钮
2. 用手机号/邮箱完成注册
3. 注册后默认赠送体验额度（具体额度以页面展示为准）
4. 登录 → 回到 WorkBuddy 重新连接 AI-HIVE Connector 即可

**价格透明**：
- 每次调用前可调 `get_user_info` 查看当前余额
- 调用后实际扣费以服务端 `pricingSnapshot` 为准
- 任务被拒时若因余额不足，会返回 `INSUFFICIENT_BALANCE`
- 详细价格参考：https://ai-hive.iclip.cn/pricing

**常见扣费场景参考**（具体以服务端为准）：
- 文本生成：按 token 数计费
- 图片生成：按张数 + 分辨率计费
- 视频生成：按秒数 + 分辨率计费

**其他被拒原因**：
- 账户被风控：联系 AI-HIVE 客服（https://ai-hive.iclip.cn → 登录 → 设置 → 联系客服）
- 模型临时不可用：稍后重试或换模型
- 内容违规审核：调整 prompt 后重试（避免敏感内容）

- pending / processing：返回工具真实状态或进度，无进度数字时不自行估算。
- completed：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。
- failed：保留可安全展示的 errorCode / errorCategory / retryable。
- 超时或网络不明：拿到 taskId 时只查询原任务，不重复创建。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

### 常见错误指引

| 错误类型 | 可能原因 | 处理建议 |
|---|---|---|
| 上传失败 413 | 文件超过服务端大小限制 | 压缩视频或拆分素材（单文件上限以 `upload_media_from_path` 实际返回为准，见 references/material-prep.md） |
| 上传失败 415 | 文件格式不支持 | 转 mp4/mov 视频，mp3/wav 音频，jpeg/png/webp 图片 |
| 生成失败（realistic human faces） | 上传内容含真实人脸 | 改用卡通/虚拟人物，或换 Seedance 工具 |
| 生成失败（参数不支持） | durationSeconds/ratio 超出枚举 | 调用 list_models 查询该模型支持的枚举值 |
| 余额不足 | INSUFFICIENT_BALANCE | 引导用户充值后重试 |
| 任务超时 | 服务端压力 | 等几分钟后用 taskId 重查询，不重复创建 |

## 调用示例

### 示例 1：文生视频（T2V）

**用户表达**：生成一段 8 秒的产品展示视频，金色背景，镜头环绕产品。

**AI 行为**：
1. 调用 `get_user_info` 检查余额
2. 调用 `list_models(modelType="VIDEO")` 筛选 Happyhorse 对应的 publicModelId 与 pricingSnapshot
3. 无需参考素材，直接组装 prompt：风格锚定（开头第一句）+ 景别运镜前置（中景环绕）+ 光影描述（暖金侧光）
4. 调用 `generate_video`：`durationSeconds=8`，无 referenceMediaIds / 无首尾帧
5. 调用 `get_generation_task(taskId)` 跟踪到 completed
6. 输出视频 URL + 参数摘要 + 后续建议

### 示例 2：首帧生视频（I2V）

**用户表达**：用这张产品图当首帧，让它动起来，镜头缓慢推进。

**AI 行为**：`upload_media_from_path` 上传首帧图 → `list_models(modelType="VIDEO")` 选定 Happyhorse → `generate_video`（`firstFrameMediaId=图`，prompt 只写「变化与动态」如「镜头缓慢推进、产品自然旋转」，不重复图中静态信息）→ `get_generation_task` 跟踪。

### 示例 3：多角色参考（R2V）

**用户表达**：图1是主角、图2是对手，生成一段 10 秒两人对峙的短剧。

**AI 行为**：上传图1、图2 → `generate_video`（`referenceMediaIds=[图1,图2]`、`durationSeconds=10`，prompt 开头建立「图1是主角、图2是对手」映射 + 时间戳分镜 [00:00]…[00:05]… + 台词标注）→ 跟踪结果。

### English Example

User: "Generate an 8-second product showcase video on a gold background with the camera orbiting the product."

AI flow: run `get_user_info` for balance, call `list_models(modelType="VIDEO")` to fetch the Happyhorse `publicModelId` and `pricingSnapshot`, assemble a prompt (style anchor first, shot+camera up front, lighting described), call `generate_video` with `durationSeconds=8` and no reference media, track with `get_generation_task(taskId)` until `completed`, return video URL + parameter summary. Never ask the user to paste a Token into chat.


## 输出模板

### 成功：taskId + 模型与参数 + 视频 URL 列表 + 下一步建议
### 失败：错误码 + 错误分类 + 原因摘要 + 下一步建议
### 部分失败：成功视频完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
