---
name: seedance-2-5-expert
display_name: Seedance 2.5 专家
display_name_en: Seedance 2.5 Expert
description: "通过指导agent智能调度 Seedance 2.5 模型，针对\"原生 30 秒长视频、最多 50 个全模态参考、专业级视频编辑与延长、首尾帧、关键帧/分镜、白模渲染、一键成片、无缝转场、多语言叙事\"等场景深度优化 prompt 工程，输出电影级、强角色一致性的高质量视频。"
description_zh: "通过指导agent智能调度 Seedance 2.5 模型，针对\"原生 30 秒长视频、最多 50 个全模态参考、专业级视频编辑与延长、首尾帧、关键帧/分镜、白模渲染、一键成片、无缝转场、多语言叙事\"等场景深度优化 prompt 工程，输出电影级、强角色一致性的高质量视频。"
description_en: "Agent optimizes Seedance 2.5 prompts for 30s long-form, up to 50 multimodal references, video editing, extension, first/last frame, keyframe, storyboard, white-model render, one-click, seamless transition, multilingual narrative."
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
- "Seedance 2.5"
- "seedance 2.5"
- "seedance2.5"
- "SD 2.5"
- "豆包视频"
- "视频编辑"
- "视频延长"
- "关键帧"
- "多宫格分镜"
- "白模渲染"
- "一键成片"
- "无缝转场"
- "30 秒视频"
- "长视频"
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
- `durationSeconds`（可选，integer）：时长 4-30（以 `list_models` 返回的该模型枚举为准）
- `count`（可选，integer）：候选数量（默认 1）
- `size`（可选，string）：像素尺寸（仅用支持的枚举值；API 通常为 480p / 720p）
- `ratio`（可选，string）：画幅（仅用支持的枚举值；编辑/延长/首尾帧类任务通常须设为 `adaptive`）
- `referenceMediaIds`（可选，array）：参考媒体 mediaId 列表（图片/视频/音频）
- `firstFrameMediaId`（可选，string）：首帧 mediaId
- `lastFrameMediaId`（可选，string）：尾帧 mediaId

### `get_generation_task`
- `taskId`（必填，string）：`generate_video` 真实返回的 taskId

> 所有工具的真实返回值以服务端响应为准；本章节参数表是客户端约束说明。部分高级参数（如 `output_format=mov`、`ratio=adaptive`）以 `list_models` 返回的该模型能力为准；若连接器暴露则使用，否则由模型按任务类型自动处理，不要臆造未暴露的参数。

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token

## 能力范围

本 Skill 专注 Seedance 2.5 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_video 工具完成视频生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 video 列出当前可用模型及价格快照，从中筛选 Seedance 2.5 对应的 publicModelId。
- upload_media_from_path：上传本地图片/视频/音频并返回 mediaId，用于首尾帧、参考图、参考视频与角色锚点。
- generate_video：使用选定模型与 prompt 创建视频任务。
- get_generation_task：使用 taskId 查询任务状态与结果。

## 适用场景

- 用户明确表达使用 Seedance 2.5 或需要长视频、强参考、可编辑的视频生成
- 用户提供素材（图片/视频/音频）需要在该模型擅长的领域生成结果
- 用户希望跨场景复用同一模型能力保持风格与角色一致
- 用户需要专业级视频编辑、延长、首尾帧过渡、关键帧/分镜、白模渲染、一键成片或无缝转场
- 用户对生成结果的某项特性（真实质感/艺术风格/运镜/动态表现/多语言叙事）有明确要求

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 涉及真实人脸的素材（平台会拦截）—— 改用卡通/虚拟人物描述
- 涉及未成年人、裸露、暴力、仇恨内容的素材
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览

## 触发原则

积极触发 —— 有疑虑时就用本 Skill。只要有视频生成意图且涉及长视频、强参考、编辑/延长/首尾帧/分镜/白模/多语言任一特征，都应考虑使用。信号包括：
- 显式：用户提到 Seedance 2.5、首尾帧、视频编辑、视频延长、关键帧、分镜、白模、一键成片、无缝转场
- 隐含：任何 AI 长视频任务、跨镜头角色一致性、多镜头序列、图生视频、视频续写、多语言叙事
- 概念：电影级 AI 制作、原生音频生成、多模态参考、工业级视频生产

## 用户常见说法 → 对应能力

| 用户说法 | 触发能力 | 连接器参数倾向 |
|---|---|---|
| 「生成一段 30 秒产品宣传长片」 | 文生视频（无锁定） | durationSeconds 取上限、ratio 自定义 |
| 「用这两张图做过渡」 | 首尾帧 | firstFrameMediaId + lastFrameMediaId，ratio=adaptive |
| 「把视频里背景换成雪山」 | 视频编辑 | referenceMediaIds 含源视频，prompt 含编辑关键词 |
| 「这段再延长 5 秒」 | 视频延长 | referenceMediaIds 含源视频 + extendDirection，建议 MOV |
| 「做一组分镜短片」 | 多宫格分镜 / 关键帧 | 参考图 + 时间戳分镜 |
| 「多个角色各自动作一致」 | 多主体角色引用 | 图N + 角色名逐一映射 |
| 「接着上一段继续拍」 | 分段尾帧接力 | 上段尾帧 → 下段首帧 |

## Seedance 2.5 模型规格

| 维度 | 规格 |
|---|---|
| 原生时长 | 最长 30 秒直出（API 通常 4-30 秒，以 list_models 枚举为准） |
| 输入模态 | 文本 + 最多 50 个全模态参考素材（图片最多 30 张 4K；视频最多 10 段、总时长 ≤30s；音频最多 10 段、总时长 ≤30s） |
| 输出 | MP4 / MOV（编辑、延长类建议 MOV 以保色亮度与声画一致）；API 常见 480p / 720p |
| 自由宽高比 | 支持 [0.4, 2.5] 之间任意宽高比（经输入素材控制） |
| 语言 | 原生支持 10 余种语言叙事 |
| 任务类型 | 参考生视频(R2V) / 首尾帧 / 视频编辑 / 视频延长 / 一键成片 / 无缝转场 / 组合能力 |

> 单次参考素材总上限 50 个；超出会被服务端拒绝。具体每张/每段的大小与格式限制以 `upload_media_from_path` 实际返回为准。

## OpenAPI 交叉验证：模型 ID 与参数（SDK models-reference.md，2026-08）

> 以下 `publicModelId` 与参数来自 AI-HIVE OpenAPI `models-reference.md`（经 SDK 交叉验证）。
> 在 AI-HIVE Connector 中**运行时一切以 `list_models` 实际返回为准**；下表用于预校验与 prompt 指引用，不臆造未返回字段。

### 已验证 publicModelId（Seedance 2.5）

| 任务类型 | publicModelId |
|---|---|
| 文生视频 T2V | `public_model_seedance_2_5_t2v` |
| 图生视频 I2V | `public_model_seedance_2_5_i2v` |
| 参考生视频 R2V | `public_model_seedance_2_5_r2v` |
| 视频编辑 | `public_model_seedance_2_5_video_edit` |
| 视频延长 | `public_model_seedance_2_5_video_extend` |

### 已验证参数（Seedance 2.5）

| 参数 | 取值 / 默认 | 说明 |
|---|---|---|
| `resolution` | 480p / 720p，默认 720p | 像素分辨率 |
| `duration` | -1（自动）或 4-30s，默认 -1 | 时长；-1 由模型自定 |
| `ratio` | adaptive / 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16，默认 adaptive | 编辑/延长/首尾帧锁定为 adaptive |
| `generateAudio` | 默认 true | 原生音频 |
| `outputFormat` | mp4 / mov，默认 mp4 | 编辑/延长建议 mov 保色亮度与声画一致 |
| `watermark` | 默认 false | 水印 |
| `extendDirection` | forward / backward | 仅视频延长；向前/向后延长 |

> 模式约束：I2V 需 `firstFrameUrl`；编辑与延长锁定 `ratio=adaptive`，编辑锁定 `duration=-1`。

**可复现性（可选）**：若 `list_models` 返回该模型支持 `seed` 参数，可固定种子复现结果（调试或抽卡对齐时使用）；不固定则由模型随机生成。参考社区 Seedance CLI 支持 `-1` 到 `2147483647` 的种子范围。

### 价格参考（¥/秒，以服务端 `pricingSnapshot` 为准）

| 分辨率 | 无参考 | 有参考 |
|---|---|---|
| 480p | 0.672 | 0.4032 |
| 720p | 1.512 | 0.9072 |

## 任务分类：有锁定 vs 无锁定

Seedance 2.5 根据传入素材是否锁定输出属性，把任务分为两类（Seedance 2.0 无此区分）：

### 有锁定：编辑 / 首尾帧 / 延长

这类任务会根据输入素材自动锁定部分生成参数，通常不支持自定义宽高比：

| 任务类型 | 锁定说明 | 连接器参数提示 |
|---|---|---|
| 视频编辑 | 锁定宽高比（严格对齐待编辑视频），`ratio` 建议 `adaptive`；时长由模型基本对齐输入 | `referenceMediaIds` 含源视频；prompt 含编辑关键词（编辑/增加/删除/修改/替换） |
| 首帧/首尾帧 | 锁定宽高比（严格对齐首帧图）；时长可自定义 | `firstFrameMediaId`（+`lastFrameMediaId`）；建议首尾帧画幅一致 |
| 视频延长 | 锁定宽高比（严格对齐待延长视频），`ratio` 建议 `adaptive`；时长可自定义 | `referenceMediaIds` 含源视频；prompt 含延长关键词（向前/向后延长/续写）；建议 MOV |

### 无锁定：参考任务 / 多宫格分镜 / 关键帧

参考类任务（含多宫格分镜、关键帧）不锁定输出宽高比与时长，用户可自定义：

- 多宫格分镜：生成画面不严格对齐分镜图细节，分镜图主要提供剧情参考；推荐简约线稿分镜，prompt 补齐动作/运镜/风格。
- 关键帧：多张独立分镜图作为关键帧输入，生成画面相对严格对齐输入图；时长可自定义。

## 模式 → 连接器参数矩阵（避免非法媒体组合）

> 借鉴 SDK 示例技能的 `validate_mode_inputs()`。映射到 `generate_video` 的三个媒体入参：`referenceMediaIds` / `firstFrameMediaId` / `lastFrameMediaId`。
> 提交前按下表自检，**不要把所有媒体字段同时填上**；非法组合会被服务端拒绝（400）。

| 模式 | `firstFrameMediaId` | `lastFrameMediaId` | `referenceMediaIds` | 参数锁定 |
|---|---|---|---|---|
| 文生视频 T2V | ✗ 禁止 | ✗ 禁止 | ✗ 禁止（仅 prompt） | ratio/duration 可配 |
| 图生视频 I2V（首尾帧） | ✅ 必填 | 可选 | ✗ 禁止 | ratio=adaptive |
| 参考生视频 R2V | ✗ 禁止 | ✗ 禁止 | ✅ 必填（≥1 图/视频/音频） | ratio/duration 可配 |
| 视频编辑 edit | ✗ 禁止 | ✗ 禁止 | ✅ 必填（**首个视频=待编辑**，4-30s；后续为参考） | ratio=adaptive、duration=-1 |
| 视频延长 extend | ✗ 禁止 | ✗ 禁止 | ✅ 必填（首个视频=待延长） | ratio=adaptive；extendDirection=forward/backward |

> 关键规则：首尾帧字段只用于 I2V；参考/编辑/延长只走 `referenceMediaIds`；T2V 不带任何媒体。编辑/延长的源视频放在 `referenceMediaIds` 首位。

## Seedance 2.5 全模态能力清单

> 支持文本、图片、视频、音频的灵活组合。下表为典型能力。

| 任务类型 | 支持的能力 | 能力细化 |
|---|---|---|
| 参考生视频 | 主体参考 / 运动参考 / 白模参考 / 风格参考 / 音频参考 / 宫格分镜参考 / 关键帧参考 | 主体图/音视频/图+音色；动作/表情/运镜/特效运动；粗/细粒度白模渲染；风格图/视频；音乐/台词/音色；多宫格分镜；单/多图关键帧、首尾帧 |
| 首尾帧生视频 | 首帧 / 首尾帧 | 严格通过 `firstFrameMediaId` / `lastFrameMediaId` 控制 |
| 编辑视频 | 视频指令编辑 / 视频参考图编辑 / 视频音频编辑 | 增/改/删主体、服饰、运镜、特效、背景、字幕、水印；支持时间戳指定生效时段；人声/音乐/音效增删改 |
| 视频延长 | 向前/向后延长 | 可要求画面/音频无缝衔接；建议 MOV |
| 其他 | 一键成片 / 视频无缝转场 / 组合能力 | 多图/视频生成短片；两段视频补全间隙转场；上述能力自由组合 |

## 素材输入建议

| 场景 | 输入建议 |
|---|---|
| 输入素材总上限 | 图片最多 30 张 4K；视频最多 10 段（总时长 ≤30s）；音频最多 10 段（总时长 ≤30s）；合计 ≤50 |
| 主体音视频（建议几个主体） | 1-5 主体效果较好；6-10 可尝试但稳定性下降、可能需抽卡 |
| 主体音视频（建议时长） | 5-10s 效果较好；更长稳定性下降 |
| 主体图（建议几个主体） | 1-8 主体效果较好；9-12 可尝试但稳定性下降 |
| 多视角主体图 | 1-5 主体「单视图」「多视图」均可；超 5 主体建议拆分为多张不同视图分别输入 |
| 宫格图分镜 | 更适用于 15 个以下分镜；推荐火柴人/线稿，不在分镜图上写过多文字 |
| 白模参考 | 简单建模（粗粒度）参考效果较好，建议仅用简单几何体拼接 |
| 视频编辑 | 20s 以内效果较好；更长稳定性下降 |
| 视频参考图编辑 | 1-5 张参考图较好；6-8 可尝试但稳定性下降 |
| 视频延长 | 为最佳声画衔接，输入与输出均采用 MOV |

## 超长视频：分段 + 尾帧接力

Seedance 2.5 原生最长 30 秒（H3 仅 15 秒）。要生成超过该上限的连贯长片，用「分段生成 + 尾帧接力」：

1. 生成第一段，时长取模型上限内（2.5 用 30s / H3 用 15s）。
2. 获取尾帧：若 `get_generation_task` 返回 `lastFrameUrl` / 尾帧图，直接用作下一段首帧；否则由 agent 从成片截取最后一帧并 `upload_media_from_path` 上传，拿到 `mediaId`。
3. 以该尾帧作为下一段的 `firstFrameMediaId`，prompt 写明「紧接上一段结尾，运镜 / 主体 / 服装连续不跳变」，继续生成。
4. 重复直到完片；每段保持相同角色锚点与画幅，保证一致性。

> 借鉴自社区 Seedance CLI 的 `returnLastFrame` + 多段连续生成模式；在 AI-HIVE Connector 中一切以 `get_generation_task` 实际返回为准，不臆造尾帧字段。

## 角色引用系统（核心语法）

Seedance 2.5 把参考图/视频/音频当作角色而非单纯视觉锚点。上传后按上传顺序编号（图1、图2…/视频1/音频1），在 prompt 中声明每张素材的用途：

- 图1 作为首帧 / 图2 作为尾帧
- 图1 的角色作为主体（身份锚定）
- 场景参考图3
- 参考视频1 的运镜
- 穿着图2 中的服装
- BGM 参考音频1

多主体逐一列清映射关系，人数多时用清单罗列（如「img1-2 是人物1，对应音频1；img3-4 是人物2，对应音频2」），避免角色混淆或重复。

## Prompt 公式（导演思维）

把 Seedance 2.5 当作视觉内容生产者，用导演思维书写结构化 Prompt：

**1. 素材指代**：明确每个图/视频/音频的编号（按上传顺序）与用途（谁是形象、音色、动作、场景）。

**2. 一句话概述**：主体 + 地点 + 事件 + 题材/风格 + 特殊运镜。

**3. 具体情节描述**：用时间戳（整数秒）或「镜头 N」切分，逐段描述画面内容、运镜、动作、台词、音效，尽量用正向描述。支持负向控制：如「不要字幕」「无 bgm，只生成环境音」。

**4. 结尾**：补充贯穿始终的画面细节，如机位/运镜、环境/场景、声音、氛围。

大于 8 秒视频按时间片分段示例：
`0-3秒女孩推门走进咖啡馆镜头向前推；3-6秒她坐下点单镜头平移到吧台；6-10秒咖啡上桌特写镜头固定。`

### 时间戳写法

- 整数秒时间区间（注意连续，避免 `0-3秒...5-6秒` 这种跳变）：`0-3秒……3-7秒……7-15秒` 或 `[1s-4s]…[4s-8s]`
- 时间点：`第5s快速向左横移转场`
- 相对时间：`张三呆滞站立，3秒后周围人纷纷摇头`
- 不建议用时间戳控制频率（如「一秒摇头3次」）

### 进阶：镜头语言

- 通识可直接写：景别（大全景/全景/中景/近景/特写）、运镜（推/拉/摇/移/跟/环绕/俯冲/后拉/上摇/手持晃动）、机位（低角度/俯视/第一人称）
- 热门运镜可直接写：一镜到底、希区柯克变焦、航拍、FPV、子弹时间、手持、回弹变速
- 小众专业名词转为「名词+描述性解释」
- 转场写清触发点与方式、时间

### 进阶：动作/表情

- 动作：优先概括性描述（「连续高抬腿和空翻」），只在记忆点写具体细节
- 表情：写描述性语句（「脸上带着满足的笑容，大口吃饭」），减少成语

### 进阶：白模参考/渲染

- 写明希望参考白模视频的什么元素（运镜/动作/光影）
- 叠加参考图时，写明参考图与白模的对应关系
- 建议在 Prompt 中详细描述希望生成的视频内容，文本需与白模吻合

### 进阶：多宫格分镜/关键帧

- 多宫格分镜：≤15 分镜；推荐线稿；prompt 避免前后矛盾；宫格图不严格对齐，需严格对齐时用多关键帧
- 关键帧：第一句写「以图片1至图片N的顺序作为关键帧」，按序传入

## 与 Seedance 2.0 的差异

1. 响应时间戳：2.0 只响应镜头序号，2.5 响应整数秒时间戳。
2. 多视图：2.0 不建议多视图主体参考，2.5 支持。
3. 自由宽高比：2.0 仅 6 档固定，2.5 支持 [0.4, 2.5] 任意宽高比。
4. V2V 画质：2.5 支持 MOV，编辑/延长中更好保持颜色亮度与声画一致。

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
2. list_models(modelType=VIDEO) 获取 Seedance 2.5 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 分析用户需求：文生 / 图生 / 首尾帧 / 多图角色 / 编辑 / 延长 / 分镜 / 白模 / 一键成片 / 转场。
4. 如需参考素材，upload_media_from_path 逐张上传得到 mediaId（注意 50 个总上限）。
5. 组装 prompt：素材指代、一句话概述、时序情节、结尾细节；按任务类型选用对应模式与关键词。
6. generate_video 提交任务，get_generation_task 跟踪到 completed。

## 输入检查

- 明确生成模式（文生 / 图生 / 首尾帧 / 多图角色 / 编辑 / 延长 / 分镜 / 白模 / 一键成片 / 转场）。
- 参考素材仅使用用户主动选择的文件，且总数 ≤50。
- 时长仅使用服务端支持的枚举值（通常 4-30 秒）。
- 画幅仅使用服务端支持的枚举值；编辑/延长/首尾帧类任务优先 `adaptive`。
- 多图角色引用时，必须用图N + 角色名明确每张图用途。
- 编辑/延长任务通过 prompt 关键词触发，并将源视频放入 `referenceMediaIds`。
- 首尾帧通过 `firstFrameMediaId` / `lastFrameMediaId` 控制。
- 编辑/延长建议输出 MOV 以保声画一致。

## 生成后建议

- 尝试不同模态（文生不理想可改图生、首尾帧或参考）。
- 调整运镜（推/拉/摇/移/跟/升/降/固定）。
- 增减参考图数量或改用线稿分镜/关键帧。
- 调整时长（短视频连贯叙事，长视频用时间戳分镜）。
- 编辑/延长不满意可换 MOV 或调整源素材。

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
- completed：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。注意 COMPLETED 状态不保证有视频 URL，必须检查返回体。
- failed：保留可安全展示的 errorCode / errorCategory / retryable。
- 超时或网络不明：拿到 taskId 时只查询原任务，不重复创建。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

### 常见错误指引

| 错误类型 | 可能原因 | 处理建议 |
|---|---|---|
| 上传失败 413 | 文件超过大小限制 | 压缩视频或拆分素材 |
| 上传失败 415 | 文件格式不支持 | 转 mp4/mov 视频，mp3/wav 音频，jpeg/png/webp 图片 |
| 生成失败（realistic human faces） | 上传内容含真实人脸 | 改用卡通/虚拟人物 |
| 生成失败（参数不支持） | durationSeconds/ratio 超出枚举 | 调用 list_models 查询该模型支持的枚举值 |
| 参考素材超限 | 超过 50 个或单类超上限 | 精简素材至 50 以内，遵循素材输入建议 |
| 余额不足 | INSUFFICIENT_BALANCE | 引导用户充值后重试 |
| 任务超时 | 服务端压力 | 等几分钟后用 taskId 重查询，不重复创建 |

## 调用示例

### 示例 1：参考生视频（多主体）

**用户表达**：用角色图1-2 和场景图3，生成一个 10 秒电影级短片，角色在雪夜房间对话。

**AI 行为**：
1. get_user_info 检查余额
2. list_models(modelType=VIDEO) 筛选 Seedance 2.5 的 publicModelId
3. upload_media_from_path 上传图1-3 得到 mediaId
4. 组装 prompt：素材指代（图1-2=人物，图3=场景）+ 时序分镜（0-5s…5-10s…）+ 运镜/光影/音频
5. generate_video（referenceMediaIds=[图1,图2,图3]）提交
6. get_generation_task 跟踪到 completed，返回视频 URL + 参数摘要

### 示例 2：视频编辑

**用户表达**：把视频1里男人的台词改成「你不要过来啊」，口音改东北口音。

**AI 行为**：upload 视频1 → generate_video（referenceMediaIds=[视频1]，prompt 含「仅编辑视频1中男人的台词…」），get_generation_task 跟踪。

### 示例 3：首尾帧

**用户表达**：用这张首帧图和这张尾帧图，生成 6 秒过渡视频。

**AI 行为**：upload 两张图 → generate_video（firstFrameMediaId=图1, lastFrameMediaId=图2, durationSeconds=6），跟踪结果。

### English Example

User: "Generate a 10-second cinematic clip from character images 1-2 and scene image 3, with the characters talking in a snowy night room."

AI flow: get_user_info for balance, list_models(modelType=VIDEO) to fetch Seedance 2.5 publicModelId, upload images 1-3 via upload_media_from_path, assemble a structured prompt (asset mapping + timestamped storyboard + camera/light/audio), call generate_video with referenceMediaIds, track with get_generation_task until completed, return video URL + parameter summary. Never ask the user to paste a Token into chat.

## 输出模板

### 成功：taskId + 模型与参数 + 视频 URL 列表 + 下一步建议
### 失败：错误码 + 错误分类 + 原因摘要 + 下一步建议
### 部分失败：成功视频完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
