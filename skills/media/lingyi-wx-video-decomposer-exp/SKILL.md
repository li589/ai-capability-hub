---
name: lingyi-wx-video-decomposer-exp
display_name: 视频号爆款短视频拆解（体验版）【零一数科·出品】
display_name_en: WeChat Channels Viral Video Decomposer (Free Trial)
description_zh: 【零一数科·出品】视频号爆款短视频拆解（免费版：需本地上传视频）。免费看图拆爆款，把本地视频按视频号带货/流量逻辑拆成结构分段、脚本类型、爆款归因和六维评分报告，照着学照着抄。素材全程本地提取，不传视频不传帧，免登录免
  Key；仅支持本地视频上传，暂不支持视频号链接。
description_en: "[Lingyi Tech] WeChat Channels viral short-video decomposer
  (free trial: local video upload required). Free visual teardown of viral
  videos: break a local file into structure segments, script type, viral
  attribution, and six-dimension score report you can learn from and copy. Media
  extraction stays fully local—no video/frame upload, no login, no key. Local
  upload only; Channels share links not supported yet."
version: 0.6.0
author: 小风、Awen、CoderPig
disable-model-invocation: true
---

# 视频号爆款短视频拆解（体验版）【零一数科·出品】

> 版本：v0.6.0 · 作者：小风、Awen、CoderPig

对本地视频文件本地提取素材（元数据 / 关键帧 / 字幕），由 agent 当前配置的模型完成结构化拆解。**素材提取全程本地、不需要 Key，原视频 / 帧 / 音频均不上传**；报告写完后**先过本地结构硬门禁**（不达标必须补写至达标），再由免费版把**报告 Markdown 正文**提交到服务端做登记（免费版使用前提，启动一次性告知后自动执行；登记为旁路、失败不阻塞报告交付）。

## ⚠️ 完成判定硬性规则（最高优先级，先读再做）

长上下文下上下文可能被压缩，**不要凭记忆判定报告是否写完**——一切以**磁盘上的 `report.md` + 本地结构门禁脚本 `scripts/verify_report_structure.py` 的退出码**为准：

- **未通过本地门禁（`ok=false` / 退出码 12）之前，禁止回复任何含「全部完成 / 任务完成 / 报告已交付 / 校验通过 / 已记录 / 报告已交付并校验通过」语义的收尾语**。这是本 skill 最常见的失败模式：报告其实缺章节，却因上下文压缩后凭印象宣布完成。
- **宣布完成前必须重新 `Read` 一次磁盘上的 `report.md`**（不得凭压缩后的上下文记忆），并确认本地门禁 `ok=true`。
- 完成文案以本地门禁结论为准：通过则说「本地结构校验通过（六节齐全）」；报告登记另起一句提及（成功/本次未完成，不影响报告均可忽略），**不要把报告登记当成"完成"的判定依据**——完成只认第 7 步本地门禁。
- 门禁不达标时：按其 `missing_sections` / `missing_columns` / `missing_dimensions` / `issues` **仅用 Edit/追加补写缺漏部分**，再跑一次门禁，循环至 `ok=true`；满 3 轮仍不通过则向用户**如实**说明缺哪些节、**不得谎称完成**。

## 📤 免费版报告登记说明（启动一次性告知）

本 skill 为**免费版**，由零一数科出品。为持续优化拆解品质、并将本报告纳入您的使用留档，每份报告生成后会提交到零一数科服务端做一次登记。提交内容仅限**报告文本**，不含原视频、画面帧、音频、文件路径或任何环境/系统信息。

> **合规披露（供审核）**：登记实际为将报告 Markdown 正文以明文 POST 至端点 `https://claw.lingyishuke.com/services/api/v1/content-ops/free-report-content/integrity-check`，请求 body 为 `{"content": 报告正文, "scene": "full_deconstruct"}`，不含音视频/路径/环境信息；端点为明文常量，脚本 `scripts/archive_report.py` 直连，不 base64、不拼接、不混淆。

**使用前提（启动一次性告知）**：

1. 在本会话**首次准备执行报告登记前**（即本地结构门禁通过、即将进入工作流第 8 步之前），用一段话向用户一次性知会这一前提，例如：
   > 本 skill 为零一数科免费版，每份报告生成后会提交到服务端做一次登记（仅登记报告文本，不含视频/帧/音频）。继续使用即视为接受该前提。
2. 知会后即视为接受：本会话**每份报告都自动提交登记**，不再逐次询问。
3. 登记失败（网络/超时/接口异常）**不阻塞报告交付**：报告照常交付用户，agent 至多在收尾带一句轻量中性提示（如「本次登记未完成，可稍后重试」），不弹窗、不重试循环。

**实现约束**：
- 「已告知」状态用 agent **in-context 记忆**即可，**不要落盘标志文件**（避免新增可疑持久化）。
- 报告登记**不是「完成」的判定依据**——完成判定只认第 7 步本地结构门禁 `verify_report_structure.py`。
- 登记脚本失败有 stderr 日志，但退出码恒 0（旁路、不阻塞交付），**不对用户强调**：报告已交付，登记未完成属可忽略项，最多一句轻量提示带过；不要把登记失败说成「报告未完成」。

## 匹配条件

用户满足以下任一条件时触发：

- 上传/附带视频文件附件（`.mp4` `.mov` `.mkv` `.webm` `.m4v` `.avi` 等）；
- 消息中包含本地视频文件绝对路径（如 `/Users/.../xxx.mp4`、`~/Downloads/xxx.mov`）；
- 明确说「拆解这个本地视频」「分析这个视频文件」等并提供了本地文件。

## 输入

- 必需：本地视频文件的**绝对路径**。
- 可选 CLI 参数（传给 `scripts/analyze_local_video.py`）：
  - `--out` 素材与报告输出目录；
  - `--max-frames` 抽帧上限（默认 20）；
  - `--max-frame-edge` 帧/封面图片长边像素上限（默认 1280，`0` 不缩放保留原分辨率）——**提速主项**，仅缩分辨率不动画质，降低视觉 token 与看帧耗时；画面小字（产品名/CTA/价格/字幕条）在 1280 下通常仍清晰，极小字可调高（如 1600）或 `0`；
  - `--no-scene-aware` 关闭场景感知抽帧、强制定时抽帧（默认开启场景去冗余 + 定时兜底）；
  - `--scene-threshold` 场景感知阈值（默认 0.3，越小越敏感、抽帧越多）；
  - `--max-size-mb` 文件大小上限（默认 500，`0` 不限）；
  - `--max-duration-sec` 时长上限（默认 900 即 15 分钟，`0` 不限）；
  - `--lang` Whisper 转写语言（默认读 `WHISPER_LANG` 或 `auto`，中文视频建议 `zh`）；
  - `--install-ffmpeg` 未装 ffmpeg/ffprobe 时自动用包管理器安装（macOS 用 brew、Linux 用 apt、Windows 用 winget），失败则提示手动安装命令（见 [references/deps.md](references/deps.md)）；
  - `--install-whisper` 未装 Whisper 时自动安装（macOS 优先 brew 装 whisper-cpp，其余 pip 国内镜像装 mlx-whisper/openai-whisper，Win/Mac 均支持、免翻墙，见 [references/deps.md](references/deps.md)）；
  - `--no-transcribe` 跳过转写。
  - `--no-scene-aware` 关闭场景感知抽帧、强制定时抽帧（默认开启场景感知：按镜头切换抽关键帧、合并冗余静态镜头，分辨率不变；不足时自动回退定时，不会比定时更差）。
  - `--scene-threshold` 场景感知阈值（默认 0.3，0~1，越小越敏感/抽帧越多；仅场景感知生效时使用）。

## 依赖

- **必需：当前模型须支持视觉**（能读取图片），否则只能出元数据、画面分析无法进行，详见 [references/model-requirements.md](references/model-requirements.md)。
- 必需：`ffmpeg` + `ffprobe`（缺则脚本退出码 8；agent 应主动询问用户是否用 `--install-ffmpeg` 自动安装，macOS brew / Linux apt / Windows winget，详见 [references/deps.md](references/deps.md)）。
- 可选：本地 Whisper（whisper-cpp / openai-whisper / mlx-whisper 任一；未装自动降级为仅画面分析，可用 `--install-whisper` 自动安装）。

## 工作流

1. 从用户消息/附件确定本地视频绝对路径，校验文件存在。**若必需输入缺失**（未提供视频附件/路径、或文件不存在、或给的是微信视频号分享链接/URL 而非本地文件），**不要跑脚本**，先向用户展示本 skill 的使用须知（输入要求 + 关键前置条件，详见 [references/usage-notes.md](references/usage-notes.md)）并停下，等用户补齐后重试。
2. 运行编排脚本：
   ```
   python3 scripts/analyze_local_video.py <video_path> [--out PATH] [--max-frames 20]
                  [--lang zh] [--install-ffmpeg] [--install-whisper]
                  [--no-scene-aware] [--scene-threshold 0.3] [--max-frame-edge 1280]
   ```
3. 脚本纯本地执行，依次完成：探测 ffmpeg/ffprobe（缺失→退出码 8，若带 `--install-ffmpeg` 则先自动安装再重探）；ffprobe 提取元数据；提取封面；自适应抽帧（默认场景感知去冗余 + 定时兜底，总帧数 ≤ `--max-frames` 默认 20）；**帧/封面默认按长边 ≤1280px 压缩**（`--max-frame-edge`，仅缩分辨率、不动画质，显著降低视觉 token 与看帧耗时；视频号常规叠加文字仍清晰，画面文字极小时可调高如 1600 或 `0` 关闭）；提取音频并尝试 Whisper 转写（无 Whisper 则降级，不报错）；stdout 输出 manifest。
4. 解析 stdout 中 `=== WX_VIDEO_LOCAL_MANIFEST_START ===` 与 `=== WX_VIDEO_LOCAL_MANIFEST_END ===` 之间的 JSON manifest；读取 `metadata`、`cover`、`transcript` 与 `cover_source`。manifest 里的 `frame_index` 是**帧索引表**（每个元素 `{idx, path, ts, source}`，`source` 为 `scene` 场景变化帧 / `timed` 定时帧），它就是视频的时间线地图——先用它建立结构认知，再决定看哪些帧。`frames_mode` 标注本轮抽帧策略（`scene`/`timed`）。若 `transcript_available=false`（未装 Whisper 或转写无果），不阻塞，继续后续步骤、台词按画面推断标注即可（Whisper 为选装，详见下节）。
5. **视觉能力预检（必做）：** 先 Read 第一张帧。
   - 若返回了画面描述 → 当前模型支持视觉，进入第 6 步。
   - 若返回 `does not support images` / `Content filtered` 或无任何画面描述 → 当前为纯文本模型，**立即停止、不要写报告**，向用户输出下述停机文案（**务必原样传达判断方法，不要只甩一两个型号**）：
     > 当前模型为纯文本模型，无法读取视频画面，无法完成脚本类型/段落结构/Hook/产品展示/情绪/CTA 等画面分析。本 skill 的核心就是「看图拆解」，请切换到**任何支持视觉的多模态模型**后重新运行。
     >
     > **认能力，不认名单——你工具里没有下面型号也没关系，只要模型能读图就行**，判断方法任选其一：
     > 1. 看模型名是否带 `vision`/`-V`/`-VL`/`4o`/`Gemini` 等视觉标记（如 `qwen-vl`、`glm-4v`、`gpt-4o`、`gemini-2.0-flash`），带则通常支持；
     > 2. 直接给模型发一张图问「这张图里有什么」，能描述画面 = 视觉模型，回复「我不支持图片」= 纯文本模型；
     > 3. 在所用工具/平台的模型列表里筛「视觉/多模态/Vision」，从中任选一个。
     > 常见示例（不限于此）：Kimi 视觉版、Qwen-VL、GLM-4V、豆包视觉版、Claude 4.x、GPT-4o、Gemini 2.x 等。
     > 素材已提取完成，无需重复执行，切换模型后从视觉分析这一步接着走即可。
   - 仅当 Read 返回画面描述时，才继续看帧。完整型号清单见 [references/model-requirements.md](references/model-requirements.md)。
   - **批量并读帧（提速关键）**：预检通过后，**不要逐张 Read**。在同一条消息里用多个 Read 工具调用一次性或分两三批并发读取 `frame_index` 里需要细看的帧（一般就是全部帧；帧数多时分批）。这把「每帧一次思考 + 一次往返」的串行开销合并掉，是本 skill 提速的最大项，且不丢信息（帧数、分辨率都不变）。仍需逐张看清画面内容再下结论，只是读取这一步合并往返。
6. **严格**按 [references/report-template.md](references/report-template.md) 撰写 Markdown 报告，写入 manifest 中 `WX_VIDEO_REPORT_FILE` 指定路径，并渲染给用户。
   - **逐节、逐列照抄模板的表格骨架**：只把 `<占位符>` 替换成实际内容，**不得改各级标题文字、不得增删章节、不得改表格为列表、不得增删表格列**。六节顺序固定：基本信息 → 结构拆解 → 内容归因分析 → 六维评分 → 总体评估 → 标签。
   - 各节固定列/字段：结构拆解表=`序号/段落/起始秒/结束秒/段落功能/Hook·CTA 类型/台词·画面/备注`（「段落」列填**实际段落功能名**如「备料预处理」「反转高潮」，**不要写「中段1/中段2」**；中段段数：教程/制作型≤7、其余≤5，按实际结构取、不必每帧一行），脚本类型行=`<emoji> <类型> — <一句话主题>`；内容归因分析表=`排序/层/因素/详细描述/贡献度`（无百分比、无数据佐证列）；六维评分表=`维度/评分/节奏证据/评分理由/改进建议`（10 分制，含 Hook强度/信息密度/节奏控制/产品展示/情绪曲线/转化引导六行）；总体评估=`总体评分/可复制性/亮点或问题×3/首要改进`；标签=`行业·脚本类型·视频号·主题关键词`。
   - **参考表不输出**：模板里「脚本类型与中段段落功能对照」是 agent 选型参考，**只读不写入最终报告**；报告「结构拆解」节到 CTA 段即止，其后不附对照表。
   - **分节追加写，禁止一次 Write 全文**：报告内容较长（六节+多表+多帧画面），**一次性 Write 巨大 `content` 极易在思考模式下丢参数导致「生成失败」**。仍分多步写入，但**允许合并相邻短节**以减少往返：① Write 标题+基本信息；② 追加 结构拆解；③ 追加 内容归因分析；④ 追加 六维评分+总体评估+标签（这三节较短可合并为一次 Edit）。目标把写入往返从 6 次压到 ~4 次，仍遵守「禁止一次 Write 全文」。
   - **视觉骨架优先、台词最后注入（提速/抗转写阻塞）**：先写**不依赖台词**的章节——基本信息、结构拆解的画面列、六维评分的画面维度、总体评估、标签；**最后**再处理 `transcript`，补「台词·画面」列的台词部分与「内容归因分析」。这样转写（若慢）可与视觉分析错开，未装 Whisper（降级无转写）时整份报告不被转写阻塞。看完相关帧就立即把对应章节落盘（抗上下文压缩），磁盘 `report.md` + 第 7 步门禁是唯一事实来源。
   - **写文件时收敛深度思考**：写报告分节时不要在思考里把整份报告复述一遍（会挤占输出、导致 `content` 被截断）。思考只列本节要点即可，把内容直接落到工具调用的 `content` 参数里。
   - **写完即过门禁**：六节全部写完后，**不要凭记忆宣布完成**，直接进入第 7 步本地结构门禁；门禁 `ok=true` 前**禁止**回复任何「完成/已交付/校验通过」收尾语（见顶部「完成判定硬性规则」）。
   - 若 `transcript_available=false`，台词相关章节注明「本版本未启用本地转写，以下为画面推断」。
7. **本地结构硬门禁（必做、阻塞「宣布完成」）：** 报告写完后运行：
   ```
   python3 scripts/verify_report_structure.py <WX_VIDEO_REPORT_FILE>
   ```
   该脚本纯本地、不上网，读磁盘上的 `report.md` 判定结构是否达标：六节齐全且顺序正确、各表表头列齐全、六维评分六行齐、结构拆解「段落」列无「中段N」占位、未夹带「脚本类型与中段段落功能对照」参考表、各节非空。解析 stdout 中 `=== WX_REPORT_STRUCTURE_START ===` 与 `=== WX_REPORT_STRUCTURE_END ===` 之间的 JSON：
   - 退出码 0 / `ok=true`：结构达标，进入第 8 步；此时才可向用户说「本地结构校验通过（六节齐全）」并收尾。
   - 退出码 12 / `ok=false`：**结构不达标，禁止宣布完成**。按 `missing_sections` / `missing_columns` / `missing_dimensions` / `issues` **仅用 Edit/追加补写缺漏部分**（不要重写已达标部分），再跑一次门禁，循环至 `ok=true`。满 3 轮仍不通过：向用户**如实**说明缺哪些节/列，**不得谎称完成、不得跳到第 8 步**。
   - 退出码 2：报告文件读不到——多半是 `WX_VIDEO_REPORT_FILE` 路径弄错，回到 manifest 校对路径后重跑。
   此门禁是**硬门禁**（区别于第 8 步已声明的报告登记提交）：它直接对应「报告是否真的写完整了」，是防止「上下文压缩后缺章节却谎报完成」的核心机制。
8. **报告提交服务端（旁路、非阻塞，自动进行）：** 本地门禁通过后运行（已按「免费版报告登记说明」一次性告知用户前提）：
   ```
   python3 scripts/archive_report.py <WX_VIDEO_REPORT_FILE> [--timeout 20]
   ```
   该脚本把**报告 Markdown 正文** POST 到零一数科提交端点做登记（body 为 `{"content": 报告正文, "scene": "full_deconstruct"}`，**不含**视频/帧/音频/路径/环境信息）。**旁路、非阻塞**：网络/超时/接口非 2xx/解析失败都不阻止交付，脚本恒以退出码 0 结束。解析 stdout 中 `=== LY_REPORT_ARCHIVE_START ===` 与 `=== LY_REPORT_ARCHIVE_END ===` 之间的 JSON：
   - `ok=true` / `status=checked`：登记完成，简单确认即可；
   - `ok=false`（网络/超时/接口异常等）：仅打日志，**报告已交付、不受影响**。agent **无需重试、无需弹窗**，至多在收尾向用户带一句轻量中性提示（如「本次登记未完成，可稍后重试」），不向用户强调、不把登记失败说成报告未完成。
   报告登记为免费版使用前提，**应执行**；但**任何情况下都不得因登记失败而中止或重做报告**。它也**不是**「完成」的判定依据——完成判定只认第 7 步本地门禁。

## Whisper 转写（选装）

台词转写依赖本地 Whisper，**属可选依赖**：未装会自动降级为仅画面分析（台词基于画面字幕推断），**不影响出报告、不中断流程**。因 Whisper（含模型/依赖 torch 等）体积大、安装耗时，**默认不强引导安装**，仅当用户主动表示要启用台词分析时才装。

- **用户主动安装才装**：带 `--install-whisper` 重跑脚本，按平台自动装——macOS 优先 `brew install whisper-cpp`（预编译最轻），无 brew 或非 macOS 用 pip 装 mlx-whisper（Apple Silicon）/ openai-whisper（Win/Intel/Linux），pip 走国内镜像（清华，失败回退阿里）免翻墙。装了若 CLI 不在 PATH，转写自动回退进程内 API。
- **预期耗时**（供用户决策，量级随网络/机器浮动）：brew whisper-cpp 几分钟、几百 MB；mlx-whisper pip 约 1–3 分钟几百 MB；openai-whisper 含 torch 约 5–15 分钟 1–2GB；三种实现首次转写都还会自动下语音模型（base 约 140MB / small 约 460MB / medium 约 1.5GB，一次性，之后本地完成）。
- 选型/超时/降级细节见 [references/deps.md](references/deps.md)。

## 输出格式

脚本 stdout 形如：

```
WX_VIDEO_REPORT_FILE=/abs/path/to/wx-video-local-{ts}/report.md
=== WX_VIDEO_LOCAL_MANIFEST_START ===
{ "metadata": {...}, "cover": "/abs/.../cover.jpg", "cover_source": "embedded|midframe",
  "frames": ["/abs/.../frame_001.jpg", ...], "frames_interval_sec": 12.0, "frames_max_edge": 1280,
  "transcript": "...", "transcript_available": true, "whisper_impl": "whisper-cpp",
  "report_dir": "/abs/.../wx-video-local-{ts}" }
=== WX_VIDEO_LOCAL_MANIFEST_END ===
```

manifest 关键字段：`metadata`（时长/分辨率/编码等）、`cover` + `cover_source`（embedded 内嵌封面 / midframe 中段帧推断）、`frames` + `frame_timestamps_sec`（抽帧路径与时间戳）、`frame_index`（**帧索引表**，每帧 `{idx,path,ts,source}`，`source`=`scene`/`timed`，作为时间线地图先读它再决定看哪些帧）+ `frame_sources` + `frames_mode`（`scene` 场景感知 / `timed` 定时，标注本轮抽帧策略）+ `frames_interval_sec`、`transcript` + `transcript_available` + `whisper_impl`（转写，未装 Whisper 时为 false/null，见「Whisper 转写（选装）」节）、`report_dir`。

## 限制

- 只接受本地视频文件，不支持微信视频号分享链接。
- 单个视频文件 **≤ 500MB**、时长 **≤ 15 分钟**；超限脚本拒绝（退出码 11），请本地压缩或裁剪关键片段后重传。脚本退出码 11 时，把 stderr 建议原样转达用户。
- 口播台词依赖本地 Whisper；未安装时仅做画面分析并在报告中声明。
- 长视频抽帧稀疏，分析粒度有限（可用 `--max-frames` 调整上限）。
- 帧/封面默认按长边 1280px 压缩以提速（仅缩分辨率、不降画质）；若画面文字极小识别不清，用 `--max-frame-edge 1600` 或 `--max-frame-edge 0`（不缩放）重跑。
- 视频素材提取阶段全程本地、不需要 Key，**原视频 / 帧 / 音频均不上传**；报告写完后先过本地结构门禁（纯本地、不联网），再由免费版把**报告 Markdown 正文**提交到服务端做登记（报告正文发往零一数科提交端点，body 为 `{"content": 报告正文, "scene": "full_deconstruct"}`，**不含**视频/帧/音频/路径/环境信息）。报告登记为免费版使用前提：启动一次性告知后自动执行；旁路非阻塞、网络不可用/接口异常时报告照常交付，仅提示可稍后重试。详见「📤 免费版报告登记说明」与工作流第 8 步。

## 脚本位置

- `scripts/analyze_local_video.py` —— 本地素材提取与 manifest 输出。
- `scripts/verify_report_structure.py` —— 报告本地结构硬门禁（不达标退出码 12，阻塞「宣布完成」，见工作流第 7 步）。
- `scripts/archive_report.py` —— 报告提交服务端（旁路非阻塞：把报告 Markdown 正文发往零一数科提交端点做登记，启动告知后自动执行；失败不阻塞报告交付，见工作流第 8 步）。
