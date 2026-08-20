---
name: "beatra-ai-voice-studio"
description: "用 Beatra AI语音工作室统筹AI配音、文字转语音和AI语音生成：从当前声音库选择合适音色，把文稿制作成可直接剪辑的语音合成音频，或通过声音克隆创建并复用品牌专属声音。适合文稿转语音、短视频配音、有声书旁白、课程配音、多语言配音和粤语配音，也可作为AI语音生成器与品牌声音工作台；制作前查看当前费用，长篇内容按章节、多语言内容按语言清晰交付。"
---

# Beatra AI语音工作室

选择能完成用户已确认文稿的最小语音工作流：制作单条配音、按顺序制作长篇内容、制作已
备好文稿的多语言版本，或创建一个获授权且可复用的音色。如果请求混合了这些结果，或者
制作会跨越多个会话，就继续由本工作室协调。

## 范围与路线

复用对话中已有的每项决定。已有更聚焦的 Skill 时，把独立且目标明确的请求交给它：

| 用户目标 | 最佳路线 |
| --- | --- |
| 一条短视频、广告、社交或推广口播 | `short-form-voiceover-audio` |
| 有声书或其他按顺序制作的长篇旁白 | `ai-audiobook-narration` |
| 已提供并确认目标语言文稿的多语言配音 | `ai-multilingual-dubbing` |
| 创建一个获授权且可复用的音色 | `voice-cloning-studio` |
| 混合任务、持续语音制作，或组合上述多条路线的请求 | 继续在这里处理，并维护一份制作台账 |

本工作室根据用户提供或确认的文本制作语音。它不制作完整视频，不为说话者做口型同步，
不发布媒体，不转录录音，也不编辑现有波形。保留其中可完成的语音子任务，并将相邻结果
交给对应的专门工作流。

在聚焦 Skill 与混合工作室项目之间选择时，阅读[意图与路线](references/intent-and-routing.md)。

## 输入与默认值

语音合成的硬性输入为：

- 用户提供的最终文本，或允许先整理成适合朗读的版本并展示给用户确认；
- 一个当前且准确的 `voice_id`；无论它来自用户、当前对话还是新的推荐，都要通过
  `beatra.voices.list` 再次查询；
- 仅在用户指定时使用目标语言；否则省略 `language`，不要只为询问它而打断流程。

声音克隆还需要一份样本、一个显示名称，以及用户以简单明确的话确认这是本人声音，或
说话者已明确授权克隆。上传本地样本前必须先确认授权。

当交付目标不要求其他选择时，使用克制的默认值：`model: "auto"`、`format: "mp3"`、
`speed: 1.0`、`volume: 1.0`、`pitch: 0`，不设置 `emotion`，也不设置
`sample_rate`。为朗读整理数字、名称、缩写、单位和停顿；任何实质性改写都必须在付费
制作前展示给用户。

## 标准路径

1. 确定一条路线或一组有顺序的路线。混合任务中，要在台账里区分克隆、语言、章节和
   修改步骤。
2. 首次使用或包版本变化后，尽力执行一次不计费的安装注册。注册失败绝不能阻断用户的
   语音工作。
3. 即使之前已提供声音 ID，也要调用 `beatra.voices.list`。精确匹配不透明 ID，并保存其
   当前 `status`、`language`、`languages_supported` 和 `compatible_models`。
   如果找不到该声音或状态不是 `ready`，不要提交；改选另一个当前已就绪声音，或停止。
   仍需选声时，只推荐当前已就绪的候选。只有返回的声音确实带有 `preview_url` 时，才能
   将其作为可选的免费辅助；绝不要为试听合成付费音频。
4. 固定这个准确且当前的 `voice_id` 及已保存的兼容性事实。在比较模型、验证用户要求的
   语言或估算费用前，调用 `beatra.models.list` 查询 `text_to_speech`。
5. 准备一张精确的制作卡：已确认文本或试制文本、声音 ID、用户提供时的语言、控制项、
   加权字符数、当前模型选择、费用估算、付费调用次数、交付顺序和复核目标。
6. 取得这张制作卡的批准，为每个逻辑付费请求创建一个新的本地不透明
   `client_request_id`，每个请求只提交一次，并且只轮询它返回的任务。
7. 按台账顺序交付真实产物和事实。文本、声音、模型、语言或控制项发生变化，就是一项
   新的付费工作，需要新的制作卡、批准和请求标识。

每次 Beatra 操作都必须使用随包 `scripts/mcp_client.py`：

```text
python3 scripts/mcp_client.py call <tool-name>
```

通过标准输入传入一个 JSON 对象。上传本地样本时使用
`python3 scripts/mcp_client.py upload <path> --mime-type <exact MIME>`。不要配置或调用宿主
Beatra Connector。不得使用 REST/OpenAPI 作为降级或回退方案，也不要仿造上传协议。

## 声音、语言与费用事实

使用用户提供的语言前，先验证它是 BCP-47 标签。将主标签转为小写，把文档规定的别名
`nb` 映射为 `no`、`tl` 映射为 `fil`，并对目录中的值做相同标准化；例如，
`yue-HK` 会变成 `yue`。只有 `voice.language` 或 `voice.languages_supported` 中的
一个条目具有相同的标准化主标签时，当前声音才支持该目标语言。

对于 `model: "auto"`，实时可选模型集合按下式得出：

```text
models.list.auto.candidate_order ∩ selected_voice.compatible_models
```

保留候选顺序，并且只留下实时可用的信息卡。另行从这个准确且当前的声音所列出的所有
`compatible_models` 实时信息卡构建显式模型池；位于 `candidate_order` 之外的兼容信息卡
只能显式选择，绝不能进入自动集合。用户提供语言时，针对每个自动候选的
`constraints.supported_languages` 检查其标准化主标签。只有所有候选都支持时才保留
`auto`。如果自动集合为空或有任何候选不支持，就从显式模型池中提出一个兼容该语言的
信息卡并取得批准。用户未提供语言时，保留非空自动集合；若为空，则从显式模型池提出一个
信息卡。如果没有适用的显式信息卡，就提供另一个当前声音、在相关情况下由用户选择一个
受支持语言，或者不提交。语言不能作为隐藏的自动选择输入。

语音费用根据每张适用实时信息卡的 `estimate_formula`、`unit_price_credits`、`scale` 和
`billing_basis: "beatra_weighted_characters"` 估算。每个汉字计 2，其他每个字符计 1。
当固定的显式模型或所有可能的自动模型得到相同结果时，给出一个精确估算；否则给出实时
区间。绝不要虚构自动解析的模型，也不要使用记忆中的价格。

关于精确的模型、语言、价格、请求和输出处理，阅读[选声与交付](references/voice-casting-and-delivery.md)。

## 试制与付费确认

规划、文稿准备、声音列表、试听链接、模型列表和费用估算都不计费。
`beatra.speech.synthesize` 与 `beatra.voices.clone` 会计费。

- 一份已确认的单条文稿使用一张已确认的合成制作卡。
- 长篇任务先使用一段由用户提供并确认的试制内容，再另行确认剩余部分。
- 多语言任务为每条不同的声音/语言/模型路线使用一段由用户提供并确认的试制内容，再另行
  确认剩余部分。
- 克隆是一次付费操作。任何有声验证都是一次单独的合成操作，需要自己的已确认文本、
  制作卡、批准和请求标识。

当用户当前明确要求“生成”或“制作”，并且该指令完整覆盖已经固定的制作卡时，就视为批准。
此时不要重复确认。只询价、比较、准备、笼统允许“帮我处理”，以及尚未固定的批次或变体
集合，都不构成批准。只有用户提出时才请求取消；发生冲突或远程停止未得到确认时，应继续
轮询同一任务。

任何有顺序的批次开始前，阅读[长篇与多语言制作](references/long-form-and-multilingual.md)；
上传样本或提交克隆前，阅读[声音克隆与复核](references/voice-cloning-and-review.md)。

## 执行、恢复与交付

提交前，在本地保存路线、精确 JSON、制作卡批准、`client_request_id`，随后保存
`task_id`。请求标识是本地恢复键；`tasks.list` 和 `tasks.get` 不会按它筛选，也不会返回它。

如果响应或任务 ID 丢失，就以相关 capability 调用 `beatra.tasks.list`，并跟随覆盖该时间
窗口所需的每个 `next_cursor`。使用返回的任务事实，通过 `beatra.tasks.get` 核验可能的
候选。只要匹配的任务可能仍在排队或运行，就不要提交。只有在任务是否已创建仍确实无法
确定时，才能为逐字段完全一致的重放复用同一请求标识；任何字段变化都需要新的批准和新
标识。缓慢、失败、取消、授权或更新结果都不会自动授权替代制作。

语音合成成功后，只报告返回的事实：`type`、`model`、`voice_id`、`audio.url`、
`audio.artifact_id`、`audio.duration_seconds`、`audio.mime_type`、`audio.size_bytes`、
可选的 `audio.sample_rate`、`characters`、可选的 `subtitles`、任务状态、解析后的模型，
以及返回时的计费信息。声音克隆成功后，完整保留四字段输出：`type`、`voice_id`、
`status` 和 `display_name`。绝不要声称已经试听、完成同步、发布、确保准确性或持久性、
完成删除或退款，除非返回结果确实能够证明。

按已批准的路线、语言和片段顺序交付长篇及多语言结果。已接受的音频保持不变。修正时，
只重新合成明确获准修改的片段。

## 按任务查阅资料

- 需要判断工作室矩阵、最低输入、免费规划和付费试制边界时，阅读[意图与路线](references/intent-and-routing.md)。
- 需要确认声音身份、实时模型/语言检查、价格计算、合成 JSON 与结果复核时，阅读
  [选声与交付](references/voice-casting-and-delivery.md)。
- 需要处理路线台账、试制覆盖、按顺序制作的批次与中断恢复时，阅读
  [长篇与多语言制作](references/long-form-and-multilingual.md)。
- 需要处理授权、样本传输、克隆 JSON、精确输出和可选验证时，阅读
  [声音克隆与复核](references/voice-cloning-and-review.md)。
- 仅在核验随包客户端或排查传输问题时，阅读[随包 MCP Client 连接诊断](references/mcp-connection.md)。
- 仅在相应操作分支生效时，阅读[安装与授权](references/installation-and-auth.md)、
  [安装注册](references/installation-registration.md)、[任务与结果](references/tasks-and-results.md)、
  [计费、错误与恢复](references/billing-errors-and-recovery.md)和
  [卸载与断开连接](references/uninstall-and-disconnect.md)。

## 运行与安全自动更新

执行普通 Beatra 命令前，随包客户端会为当前安装固定的官方渠道与语言区域静默检查是否有
更高版本，每 24 小时最多一次。发现更高版本时，它会在不另行确认的情况下自动安装。它只
接受固定的官方发现地址和不可变 Beatra CDN 来源，并按身份、大小和 SHA-256 校验发现数据、
压缩包、清单和每个文件；只替换本包拥有的文件。替换过程采用锁定、暂存、备份、恢复与
回滚，并在最后替换更新器本身。

它会拒绝重定向、降级、不同的包，以及不同渠道或语言区域的内容。

如果更新、校验、下载、回滚或恢复的任何步骤失败，当前安装仍可使用，用户原本请求的命令
也会继续执行。更新失败绝不授权付费重试。以下设置对当前安装持续生效：

```text
python3 scripts/mcp_client.py update --auto off
python3 scripts/mcp_client.py update --auto on
python3 scripts/mcp_client.py update --check
```

完整更新契约和立即执行已验证更新的命令参见
[自动更新与安全](references/automatic-updates-and-safety.md)。
