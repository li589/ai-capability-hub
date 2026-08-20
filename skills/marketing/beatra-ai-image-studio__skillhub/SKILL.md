---
name: "beatra-ai-image-studio"
description: "从文字描述、按顺序提供的一至四张参考图，或一张需要修改的原图出发，生成并完善图像。Beatra AI 图像工作室支持文生图、参考图创作和围绕指定部分进行的 AI 图片编辑，可用于产品图、广告创意、品牌视觉、海报、社交媒体配图、AI绘画、AI插画、概念图和照片背景修改。看到结果后，检查信息表达、主体是否符合要求、构图、风格、文字与发布场景，再选择最小有效的局部修改、重新构图或重新生成。"
---

# Beatra AI图像工作室

把一份清晰的视觉需求与最佳可用素材制作成经过检查的图像。此 Skill 适用于产品图、广告与品牌视觉、海报、社交媒体配图、插画、概念图、照片变体、背景修改，以及其他从文字、有序参考图或现有底图开始的图像工作。

## 范围与路线

每个逻辑结果只选择一条付费图片路线：

- 没有源图片时，调用 `beatra.images.generate` 进行文生图。
- 一至四张有序图片用于指导新构图时，调用 `beatra.images.transform`。这些输入会影响新图，但不承诺其中任何一张保持为底图。
- 必须以一张现有图片作为底图时，调用 `beatra.images.edit`。`images[0]` 是底图，之后的图片是可选的有序参考图。

只有结果交付并检查后，才把它用作后续聚焦编辑或构图的来源。不要静默地把编辑变成新构图，不要用纯文字生成替换用户提供的参考图，也不要承诺像素级完全保留。把人物面部、产品、Logo、文字、布局、配色及用户指定的其他细节作为必须保留项，再检查每张可访问的输出是否发生偏移。

## 输入与默认值

硬性输入是一段非空视觉方向。transform 还需要一至四张可访问且有序的参考图。edit 需要先有一张可访问的底图，之后最多可以使用三张参考图。只询问缺少的硬性输入，或会实质改变结果的选择。复用已知的发布场景、受众、主体、来源顺序、构图、风格、光线、色彩、排除项、必须保留项、数量和模型。

宿主 Agent 必须检查每份真实素材，并记录其 MIME 类型、字节大小、宽度、高度、宽高比、是否带 alpha 通道，以及是否为动画。上传只是传输，不是检查。对于宿主能够访问的本地文件，只能在检查后使用随包助手：

```text
python3 scripts/mcp_client.py upload ./product.png --mime-type image/png
```

保留返回的 artifact 引用。绝不要把本地路径传给远程工具。现有 artifact、HTTPS 或 data-URI 输入必须使用实时模型卡接受的传输方式，并且在付费执行前仍需要可信的媒体事实。

默认使用 `model: "auto"`、一张输出；generate 或 transform 默认使用 `output_relationship: "independent"`，并且不设置可选控制项。generate 和 transform 默认采用 2K 16:9 预设。edit 默认采用以第一张图片为基准的 2K 源素材画布。只有发布场景或用户意图需要，并且实时接口卡接受完整请求时，才设置不同画布、数量、关系、seed、palette、regions 或其他控制项。

## 黄金路径

1. 把工作分类为 generate、transform 或 edit。整理一份紧凑需求，覆盖一个信息目标、主体、构图、风格、光线、色彩、发布场景、排除项和必须保留项。保留 transform 输入顺序，并始终把 edit 底图放在第一位。
2. 上传前检查每张源图片并记录真实事实。阅读[视觉方向与素材准备](references/visual-direction.md)，了解画布选择、参考图角色和保留重点。
3. 在冻结任何付费 payload 前，针对选定能力调用 `beatra.models.list`：`text_to_image`、`image_to_image` 或 `image_edit`。检查实时提示词规则、素材格式和数量、字节与几何限制、alpha 和动画处理、可接受传输方式、排序语义、输出数量和关系、画布、控制项、条件规则，以及 `pricing.options` 中的每个价格选项。只有明确指定的模型完全接受该请求时才使用它；绝不要静默替换模型或丢弃控制项。
4. 展示路线、有序来源及其角色、视觉需求、必须保留项、数量、有效时的关系、画布、明确控制项、模型行为，以及实时暂估费用。将每个价格选项的维度与已准入请求逐一匹配；如果准入前无法唯一确定选项，就展示返回的价格区间，并按区间最高值取得批准。绝不要按源图片数量倍增价格。规划、评议和提示词准备免费。直接要求制作已经准备好的图片可以视为批准；来源顺序、底图选择、模型、画布、数量或付费范围仍未确定时，不构成批准。
5. 获得批准后，冻结所有参数并创建一个不透明且稳定的 `client_request_id`。只调用随包的 `scripts/mcp_client.py`：把 MCP 工具名放在 `call` 后，并通过标准输入传入 JSON 参数。例如：

   ```text
   printf '%s' '{"prompt":"Place the product from image 1 in the lighting and setting of image 2; keep its shape, color, and label recognizable.","images":[{"type":"artifact","artifact_id":"art_product"},{"type":"artifact","artifact_id":"art_style"}],"count":1,"client_request_id":"opaque-image-id"}' | python3 scripts/mcp_client.py call beatra.images.transform
   ```

   不要配置、调用或信任宿主 Beatra Connector，也不要使用 REST/OpenAPI 作为降级方案。选定的计费工具只提交一次。
6. 立即记录返回的任务 ID，并使用 `beatra.tasks.get` 轮询该任务，直到 `succeeded`、`failed` 或 `canceled`。`queued` 和 `running` 是进度状态。交付每张返回图片的 URL 和 artifact ID，以及返回时提供的真实宽度、高度、格式、MIME 类型和字节大小。报告终态模型、用量、成功图片数量和 `billing.net_charged_credits`；不要用估算替代这些事实。
7. 检查每张可访问的输出是否符合需求中的信息表达、主体与必须保留项、构图、风格、光线、色彩、文字与 Logo 呈现、真实尺寸和发布场景。说明哪些内容能够检查、哪些不能。然后最多推荐一个聚焦编辑、新构图或重新生成，并等待该工作单独获得付费批准。

## 控制项与付费变更

设置任何控制项前，使用精确的实时模型卡并阅读[图片 payload 与准入](references/image-recipes.md)。数量必须是从一到四的严格整数，不能拆成隐藏请求。`output_relationship` 只属于 generate 和 transform；`reasoning` 只属于 generate。edit region 是有限范围的指令，并不保证其他每个像素都完全不变。

提示词、来源、来源顺序、底图、数量、关系、画布、模型、seed、palette、region 或其他控制项发生任何变化，都属于新的逻辑付费工作，需要新请求 ID 和批准。只有在明确给出最大付费阶段数和输出数量时，有限的多阶段计划才能一次获批；每个阶段仍须使用自己的稳定 ID、按顺序运行，并在依赖阶段执行前先检查结果。如果中间结果的偏移会改变下一个 payload，应停下并重新规划，而不是按旧批准继续花费。

图片按照成功持久保存的图片张数，以整数积分计费。多输出任务部分成功时，只对成功图片收费。实时估算是临时值；终态 `billing.net_charged_credits` 才是最终值。

## 恢复与取消

维护一份私有台账，记录路线、归一化的冻结参数、稳定请求 ID、批准、创建时间、创建响应、任务 ID 和终态结果。

- 如果创建响应丢失，但稳定 ID 和冻结参数仍在，只能使用相同 ID 重试完全一致的 payload。
- 如果任务 ID 丢失但台账仍在，针对相应能力调用 `beatra.tasks.list`，再用 `beatra.tasks.get` 检查可能的候选任务，并匹配能力、归一化输入和时间。匹配结果含糊时不要提交。
- 如果稳定请求 ID 也丢失，绝不要编造一个 ID 并重放付费请求。应从近期任务中恢复原任务；如果无法安全识别，就停下。

只有用户要求取消时才调用 `beatra.tasks.cancel`。只调用一次，然后使用 `beatra.tasks.get` 验证终态结果。如果取消未获确认，继续轮询同一任务；取消不授权替代工作。

## 按任务查阅参考资料

- 阅读[意图与路线](references/intent-and-routing.md)，以在文生图、有序参考图构图和底图编辑之间选择，或规划有限阶段序列。
- 阅读[视觉方向与素材准备](references/visual-direction.md)，以整理需求、排列参考图、检查素材事实、选择画布并定义必须保留项。
- 阅读[图片 payload 与准入](references/image-recipes.md)，了解精确的实时模型卡检查、有效控制项、随包客户端调用、价格和恢复。
- 阅读[检查与迭代](references/review-and-iteration.md)，以交付真实 artifact、检查每个结果、保留可用参考图并选择最小后续工作。
- 仅在授权或共享凭据需要处理时阅读[安装与身份验证](references/installation-and-auth.md)，并阅读[安装注册](references/installation-registration.md)了解不计费的尽力而为包注册步骤。
- 阅读[任务与结果](references/tasks-and-results.md)，了解共享终态任务语义；阅读[账单、错误与恢复](references/billing-errors-and-recovery.md)，了解返回的结算或错误详情。
- 当随包客户端无法连接时阅读[随包 MCP Client 连接诊断](references/mcp-connection.md)。不要配置宿主 Connector。
- 阅读[自动更新与安全](references/automatic-updates-and-safety.md)，了解更新保证与控制项。
- 仅在用户要求删除此包或共享凭据时阅读[卸载与断开连接](references/uninstall-and-disconnect.md)。

## 运行时与安全自动更新

每次 Beatra 操作都只能使用或调用随包的 `scripts/mcp_client.py`。在执行普通命令前，它会静默检查更新，每个安装最多每 24 小时检查一次。静默检查默认启用，发现更高版本时不另行确认便会自动安装。

更新器只接受针对此包、渠道和语言环境内置的固定官方发现地址与不可变 Beatra CDN 路径。替换前，它会校验压缩包、清单和每个文件的大小与校验和。它只替换本包文件，并拒绝重定向、降级、错误的包、渠道、语言环境或版本数据、意外 URL、不安全归档和目标目录之外的文件。

更新检查、下载、验证、替换、回滚或恢复失败时保持开放：当前安装仍可使用，用户原本请求的命令继续执行。更新失败绝不授权重试付费图片请求。自动更新设置持续生效，并会在此安装的后续命令之间持久保存：

```text
python3 scripts/mcp_client.py update --auto off
python3 scripts/mcp_client.py update --auto on
python3 scripts/mcp_client.py update --check
```

`--auto off` 会关闭静默检查，`--auto on` 会重新启用，`--check` 只报告官方可用版本而不替换文件。
