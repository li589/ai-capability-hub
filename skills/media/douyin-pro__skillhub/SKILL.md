---
name: douyin-video-skill
description: 抖音短视频双路径生产体系（单 Skill 版）。Path A[付费·高质量]：策略大脑→（可选：素材混剪/AI高光提取）→脚本优化→AI生图/素材准备→配音渲染（百炼/GPT-SoVITS/CosyVoice/VoxCPM2+剪映/Remotion/ffmpeg/数字人）。Path B[免费·动画风]：采集热点→脚本→edge-tts免费配音+HyperFrames开源渲染→MP4，零云费开箱快。触发词分层：①"抖音短视频/选题规划/合规闸门/运营策略" ②"口播脚本/AI生图/AI配音/视频渲染/Remotion渲染" ③"蹭热点/快速出片/免费做视频" ④"混剪/高光提取/素材粗剪/autoclip"
version: "5.2.2"
agent_created: false
---

# 抖音短视频生产 · 双路径 Skill

> **一条 Skill，两条路**：Path A [付费] 追求品质上限；Path B [免费] 追求零成本快出。选完就跑，不用配环境。

## ⚡ 一键安装（首次必做）

**Windows 用户（复制即跑）：**
```bash
# 1. 装 ffmpeg（没装的话）
winget install ffmpeg   # 或下载 https://www.gyan.dev/ffmpeg/builds/

# 2. 装 Node.js ≥22（HyperFrames 需要）
winget install OpenJS.NodeJS.LTS

# 3. 装 edge-tts
pip install edge-tts

# 4. 一键验证全部依赖
python scripts/install_path_b_deps.py --check
```

**Mac 用户：**
```bash
brew install ffmpeg node pip && pip3 install edge-tts && python3 scripts/install_path_b_deps.py --check
```

> 全绿 → 直接出片。有红 → 按提示装缺失项。**Path B 只需这 3 样东西，2 分钟搞定。**

---

## 两条路径怎么选

| | 🅰️ Path A 高质量 [付费] | 🅱️ Path B 免费直出 [免费·动画风] |
|---|---|---|
| **画面风格** | ✅ 真人混剪 / AI生图 / Remotion模板 / 数字人 | ⚠️ **文字动画风格**（非真人实拍，不适合真人出镜需求） |
| **音色** | ✅ 可克隆专属声音 | ⚠️ 微软预设音色（不可克隆） |
| **费用** | 需自备 TTS（百炼/CosyVoice 等）+ 渲染环境 | **完全免费**（edge-tts + HyperFrames 开源） |
| **联网** | 可完全离线运行 | edge-tts 需联网调用微软接口（偶尔等待或超时时自动降级到 CosyVoice） |
| **适合谁** | 品牌号、矩阵号、要真人质感、有实拍素材需混剪 | 蹭热点、模板化批量、快速试错 |
| **上手时间** | 10–30 分钟配环境 | **2 分钟装依赖即可跑** |
| **混剪支持** | ✅ 可选 混剪层（autoclip）提取高光 | ❌ 无，Path B 从热点/脚本直接生成 |

> 💡 **不知道选哪个？** 先用 Path B 免费出一条试试效果 → 满意了再投入 Path A 配环境。

> 🟢 **Path B 可移植提示**：本行链路（edge-tts + HyperFrames + ffmpeg + 本地脚本）是**纯开源组件**，理论上可改写进 Codex / Claude Code 等带 bash 的 agent 直接跑（平台专属入口除外）。详见下方「🧩 平台兼容性与适配范围」。

---

## 🎯 你说什么 → 我做什么（照着说就行）

| 你说这话 / 有这个意图 | 我做什么 | 用哪条路 |
|---|---|---|
| 「做一条抖音短视频」「从选题到成片」 | 全流程端到端 | 问你要 A 还是 B |
| 「帮我采集最近 XX 热点」 | 全网素材采集报告 | Path B |
| 「帮我写个口播稿 / 优化这段文案」 | 脚本优化 + 标题方案 + 分镜 | A 或 B 都行 |
| 「帮我生成配图 / AI 生图」 | shot_plan → AI 生图（9 模型可选） | Path A |
| 「用 edge-tts 免费配音直接出 MP4」 | 脚本 → edge-tts 配音 → HyperFrames 渲染 | **Path B** |
| 「用 CosyVoice / 百炼配音出片」 | 脚本 → TTS 配音 → 渲染通道出片 | **Path A** |
| 「只做账号策略 / 选题方向」 | 大脑层策略分析 | A 或 B 可选 |
| 「合规检查一下这篇文案」 | 合规六闸检测 | A 或 B 都行 |
| 「蹭热点出条视频」 | 采集热点 → 脚本 → Path B 免费直出 | **Path B** |
| 「我要真人出镜效果」 | Path A（数字人或实拍素材混剪） | **Path A** |
| 「帮我批量出 5 条 XX 视频」 | 批量流水线自动循环 | Path B（或 A） |
| 「我有实拍素材，先帮我混剪/挑高光」 | 混剪层 AI 提取 clip_segments → 再进脚本 | **Path A（混剪流）** |
| 「用 Remotion 模板出片」 | 脚本 → 配音 → Remotion 渲染 | **Path A** |
| 「用文字/图片直接生成视频」「把这张图变动态」 | 平台内置 AI 视频模型（非本 skill A/B 流程） | 走「多模态内容生成」入口，结果可回灌混剪层 |
| 「我该用 Path A 还是 B？」 | 分析需求后推荐 + 理由 | — |

> 💡 **原则**：你说得越具体越好。不确定就说「帮我做一条关于 XX 的抖音短视频」，我会问你几个关键问题然后开干。

---

## 🚨 出问题了？30 秒自救（不用查文档）

### 第一步：判断问题类型

| 现象 | 最可能原因 | **立刻这样做** | 修完后呢？ |
|---|---|---|---|
| 一开始就说「缺少必填信息」 | 没给够具体要点 | 补 **3–5 条有立场的要点**（别只给一个笼统主题） | ✅ 自动继续 |
| 跑着超时报错 | 网络不通 / API Key 过期 | 检查网络 → 查 Key 过期没 → 余额够不够 | ✅ 重试即恢复 |
| 输出的不是 JSON / 结构乱了 | 温度太高或模型太弱 | 把 temperature 降到 **0.6–0.7**，换强模型 | ✅ 重试即恢复 |
| 质量分 score 不及格 | 要点太泛或模型不够好 | 已自动重跑 2 次；仍不行就**补具体要点**后手动重来 | ✅ 重来即可 |
| 分镜脚本不合格（太泛） | visual_prompt 没写具体画面 | 每槽写 **≥15 字 + 含具象名词**（如「办公桌上凉掉的咖啡杯」） | ✅ 自动重新校验 |
| 渲染报错（TTS/剪映） | 依赖没装好 | 跑 `python scripts/install_path_b_deps.py --check` 排查 | ✅ 装好后重跑 |
| 变量红显 / DSL 导入失败 | Dify 变量未绑定 | 在画布里重新拖拽变量绑定 | ✅ 绑定后重跑 |
| 合规检测拦截 | 文案含极限词/违规表述 | 按提示修改违规词 | ✅ 改后自动继续 |
| edge-tts 联网超时 | 微软服务偶尔不通 | **自动降级**：CosyVoice → GPT-SoVITS → 百炼（按顺序尝试） | ✅ 自动切换 |
| 批量出片其中一条失败 | 单条数据问题 | 该条自动跳过，**不影响其他条** | ✅ 查看失败条日志后单独重跑 |

### 第二步：安装 / 环境排错（依赖类问题）

| 报错 | 解决 |
|------|------|
| `pip install edge-tts` 超时 | 加 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| `node -v` < 22 | 去 nodejs.org 下 LTS 22+，或 `winget install OpenJS.NodeJS.LTS` |
| `ffmpeg: command not found` | Win: `winget install ffmpeg` / Mac: `brew install ffmpeg` |
| `npx hyperframes` 报错 | `npx hyperframes browser ensure`（首次下载 Chromium） |
| `python scripts/...` 找不到 | `cd` 到 skill 根目录（有 `scripts/` 的那层）再运行 |
| 依赖缺失（通用） | 跑 `python scripts/install_path_b_deps.py --check` → 缺啥装啥 |

### 第三步：卡住了？4 步排查

```
① 跑 `python scripts/install_path_b_deps.py --check` → 缺什么装什么
② 看最后 20 行终端输出 → 复制给 AI 助手分析
③ 网络问题？→ 检查代理/VPN → edge-tts 不通就自动降级 Path A 配音
④ 完全不知道哪错了？→ 把完整报错发给 AI 助手
```

> 🔧 **需要深度排查？** → `skills/抖音/references/error-handling.md`（E001-E015 完整码表 + 大白话翻译 + 逐条修复步骤）

---

## 🚨 避坑清单（新手必读，5 分钟省 80% 坑）

> **记忆口诀：三点五分一七二，TTS 验时长别忘掉**

### 写脚本阶段（最容易翻车）

| ❌ 坑 | 后果 | ✅ 正确姿势 |
|---|---|---|
| 只给 1 条笼统主题（如"讲 AI"） | 脚本空洞、被质量门打回 | 给 **3–5 条有立场的具体要点** |
| video_duration 填 300s（5分钟） | LLM 装不下，截断烂尾 | **15–120 秒**，长内容拆系列 |
| temperature 设 1.0 | JSON 乱、声画错位 | **0.6–0.7** |
| 跳过 shot_plan 随便配图 | 完播率暴跌 | 必须 shot_plan 驱动每帧画面 |

### 配图阶段

| ❌ 坑 | 后果 | ✅ 正确姿势 |
|---|---|---|
| visual_prompt ≤14 字或无具象名词 | 分镜不合格被打回 | 每槽 **≥15 字 + 具体物体名** |
| source 留空不填 | 硬校验阻塞 | 必填 `ai_gen` 或 `asset_pool` |
| 用未授权人脸做数字人 | 合规红线直接毙 | 必须 **书面授权** |

### 渲染阶段

| ❌ 坑 | 后果 | ✅ 正确姿势 |
|---|---|---|
| TTS 后不验证实际时长 | ±10s 偏差，声画错位 | 以 **ffprobe 实际时长** 为准回写 beat |
| 同系列视频换 style_anchor | 风格跳来跳去不像一个号 | 同系列 **共享同一个** style_anchor |
| Path B 想要真人出镜效果 | HyperFrames 是文字动画，做不到 | 真人需求走 **Path A**（数字人/混剪） |
| 渲染报错就从头重来 | 浪费时间 | 先看报错→对应上方「30秒自救」→90%是依赖问题 |

### Dify 用户额外注意

| ❌ 坑 | 后果 | ✅ 正确姿势 |
|---|---|---|
| 导入 DSL 后变量红显不处理 | 运行时字段丢失 | 在画布里**重新拖拽绑定**每个变量 |
| 以为必须装 Dify 才能用 | 白忙活 | **对话直跑即可**，Dify 完全可选 |

---

## 五层模块（按需加载，不用全读）

| 层 | 复杂度 | 模块文件 | 职责 | 前提条件 |
|----|:------:|---------|------|---------|
| ① 大脑层 | 🟡 | `skills/大脑/SKILL.md` | 账号定位/选题/合规六闸/推荐通道 | 无，纯推理 |
| ② 采集 | 🟢 | `skills/采集/SKILL.md` | 全网素材采集（WebSearch/feedgrab） | 无（零配置模式） |
| ③ 脚本优化 | 🟡 | `skills/抖音/SKILL.md` | 产出 optimized_script / shot_plan / score | 给主题或初稿即可 |
| ④ 绘影图像 | 🟡 | `skills/绘图/SKILL.md` | shot_plan → 图片（9模型可切换） | WorkBuddy 生图工具可用 |
| ⑤ 渲染引擎 | 🔴 | `skills/video-render-engine/SKILL.md` | 配音×渲染 → 成片 | 至少装好一种 TTS + 一种渲染通道 |

**扩展层（可选，仅实拍素材场景）**：

| 层 | 复杂度 | 模块文件 | 职责 | 前提条件 |
|----|:------:|---------|------|---------|
| ②.5 混剪 | 🟡 | `skills/混剪/SKILL.md` | AI 高光提取 / 素材粗剪 → `clip_segments` | 原始实拍/直播回放素材 |

> 主理人（司远）只做编排和合规总控，不代写任何模块的专业产出。
> 💡 想用真正的多 agent 并发编排（而非单主机串行）？见下方「🤝 多 Agent 模式」。

---

## 字段怎么在各层之间传递

```
大脑层          采集/混剪              中游脚本           绘影          下游渲染
┌────────┐    ┌─────────────┐      ┌──────────────┐   ┌────────┐   ┌──────────────┐
│account │    │ clip_       │─────▶│ optimized_   │   │image_  │   │ dubbing_     │
│position│    │ segments    │      │ script       │──▶│map     │──▶│ method       │
│topic   │───▶│ (可选)      │      │ title_options│   │        │   │ render_      │
│compli- │    │             │      │ shot_plan [] │   │        │   │ channel      │
│ance    │    │             │      │ score        │   │        │   │ aspect_ratio │
└────────┘    └─────────────┘      └──────────────┘   └────────┘   └──────────────┘
   (可选)         (实拍素材可选)        (每次必经)       (可选)        (每次必经)
```

**4 条铁律**：
1. 每层必须把上一层**完整结构化字段**原文带入下一层，禁止凭记忆跳过
2. `dubbing_method` 枚举：**edge_tts(免费)** / baike / gptsovits / voxcpm2 / cosyvoice
3. `render_channel` 枚举：**hyperframes(免费)** / jianying / remotion / ffmpeg / digital_human
4. 合规闸门由大脑设计、下游执行，**任何层不得放宽**

### Handoff 字段速查

| 阶段 | 关键字段 |
|------|---------|
| 大脑→中游 | account_positioning / topic_direction / compliance_gate / render_channel(推荐) / dubbing_method(推荐) |
| 采集/混剪→中游 | clip_segments（实拍素材时传入脚本优化器） |
| 中游→绘影 | shot_plan（beat / visual_prompt / source / suggested_channel） |
| 绘影→下游 | image_map.json（beat_index → image_path） |
| 中游→下游 | optimized_script / dubbing_method(**edge_tts**免费/baike/gptsovits/cosyvoice) / render_channel(**hyperframes**免费/jianying/remotion/ffmpeg/digital_human) / aspect_ratio / clip_segments(如混剪过) |

> 枚举值必须合法，否则下游校验不通过。Path B = `edge_tts` + `hyperframes` = 免费直出。

---

## ✨ 独特价值（为什么不是又一个普通工具）

| 创新点 | 市面方案 | 本 Skill |
|--------|---------|---------|
| 双路径可切换 | 只有一条固定流程 | Path A / Path B **一键切换**，中间产物通用 |
| 零云费直出 | 按量计费/订阅制 | Path B **全链路零成本** |
| 合规内置 | 出完再审 | 合规六闸**嵌入每一层**，违规无法到达渲染 |
| 字段标准化 | 各模块各搞各的 | 统一 handoff JSON，换模块不换接口 |
| 质量门自动重跑 | 人工检查 | score<7 **自动重跑**最多 2 次 |
| 小白→专家渐进 | 要么太浅要么太深 | 复杂度标签 + 速查卡，按需深入 |

---

## 国内适配

- **Path A**：全链路国内部署——Dify+通义/DeepSeek、WorkBuddy内置生图、百炼/剪映/ffmpeg/CosyVoice。**GPT-SoVITS + ffmpeg 组合 = 完全离线**。
- **Path B**：WebSearch/WebFetch（国内可达）、edge-tts（微软免费，需联网）、HyperFrames（本地渲染）。**edge-tts 是唯一联网环节**，偶尔不通自动降级。

| 功能 | 离线？ | 外部依赖 |
|------|:------:|---------|
| 大脑层·策略推理 | ✅ 完全离线 | 无 |
| 脚本优化 | ✅ 完全离线 | 无 |
| AI 生图 | ✅ 完全离线 | 无 |
| GPT-SoVITS 配音 | ✅ 完全离线 | 无（本地GPU） |
| edge-tts 配音 | ❌ 需联网 | 微软TTS（国内直连稳定） |
| ffmpeg 合成 | ✅ 完全离线 | 无 |
| HyperFrames 渲染 | ✅ 完全离线 | 无（本地Chromium） |

## 质量承诺

- 每层必须把上一层**完整结构化字段**原文带入，禁止凭记忆跳过
- 合规闸门由大脑设计、下游执行，任何层不得放宽
- 不产出未过质量自检卡的成片

---

## 端到端实例（你说什么 → 我怎么做 → 出什么）

### Path B 免费直出（5 分钟）

> 你：「帮我蹭最近 AI 热点，用免费方式快速出一条抖音视频」

**我做**：① 采集 → AI热点报告 ② 脚本 → 口播稿+shot_plan+score=8.2 ③ 渲染 → edge-tts+HyperFrames → **final.mp4（1080×1920，带字幕）** ✅ 零云费 3-5min

### Path A 品牌向（有配音环境，10-15 分钟）

> 你：「帮我的知识付费账号做一条品牌向视频，用百炼克隆音色」

**我做**：① 大脑 → 定位+合规闸门 ② 脚本 → 优化稿+shot_plan+score=8.5 ③ 绘影 → 6张配图 ④ 渲染 → 百炼配音+剪映混剪 → **brand_final.mp4** ✅ 四层全跑

### Path A 实拍混剪流（有原始素材，15-20 分钟）

> 你：「我有一段 5 分钟直播回放，帮我挑高光剪成抖音带货视频」

**我做**：① 大脑 → 定位+合规闸门 ② 混剪 → autoclip 提取 clip_segments ③ 脚本 → 按高光写口播+shot_plan ④ 绘影/素材准备 → ⑤ 渲染 → CosyVoice 配音 + 剪映精修（或 Remotion 模板化） → **montage_final.mp4** ✅ 混剪层启用

### Path A Remotion 模板化出片（有脚本和图，10 分钟）

> 你：「给我做一条品牌一致的动态图文视频，用 Remotion 出片」

**我做**：① 大脑 → 定位+风格锚点 ② 脚本 → 口播稿+shot_plan ③ 绘影 → AI 生图 ④ 渲染 → edge_tts/百炼配音 + Remotion 模板渲染 → **remotion_final.mp4** ✅ 程序化动态图形

### 只要脚本（1-2 分钟）

> 你：「我有一段口播初稿，帮我优化」

**我做**：① 大脑可选(合规) ② 脚本 → 10维优化 → **optimized_script + title_options×5 + shot_plan + score** ✅ 只跑一层

---

## 🎓 高级功能（进阶按需深潜）

| 功能 | 前提条件 | 在哪学 | 难度 |
|------|---------|--------|:----:|
| 数字人出镜 | 授权肖像+运行时 | `skills/video-render-engine/SKILL.md §9.5` | 🔴 |
| 数字人训练/克隆 | GPU 或 SaaS + 训练素材 | `§9.8` + `skills/video-render-engine/references/digital-human-training.md` | 🔴 |
| 批量流水线(10+条) | 一种 TTS + ffmpeg | `§11` 批量代码 | 🟡 |
| Dify 工作流集成 | Dify 实例 | `skills/抖音/assets/dify-workflow-template.json` | 🟡 |
| 多语言视频 | 对应语种 TTS | CosyVoice §8.5 或 edge-tts 多音色 | 🟡 |
| 自定义 HyperFrames 模板 | HTML/CSS/GSAP | `templates/hyperframes_path_b/` + `§9.6` | 🟡 |
| 声音克隆 | 参考音频(10-30s) + 百炼账号 | `§8.2` 百炼章节 | 🟡 |
| Remotion 程序化模板 | Node.js + React | `§9.3` + `skills/video-render-engine/references/render-channels.md` | 🔴 |
| 实拍素材 AI 混剪 | autoclip + 原始视频 | `skills/混剪/SKILL.md` | 🟡 |

> **学习路径**：Path B 跑通基础(🟢) → Path A CosyVoice+剪映(🟢→🟡) → 按需深入 Remotion / 混剪 / 数字人(🔴)

---

## 🧩 AI 直出视频（平台内置模型 · 本 skill 之外的补充能力）

> 上面全部方法都是「脚本 → 配音 → 渲染/混剪」的**编排路线**。
> WorkBuddy 还内置 **4 个 AI 扩散视频模型**，给「文字 / 图片」就能**直接生成动态视频**，不走本 skill 的 A/B 流程——
> 通过平台「多模态内容生成」入口（或 AI 内容创作专家团的 video-generator 成员）调用。

| 模型 | 调用标识 | 输入 → 输出 | 适合场景 |
|------|---------|------------|---------|
| HY-Video-1.5 | `hy-video-1.5` | 文字 → 5–10s 视频（也支持图生视频） | 一句话出片、场景切换、多角色交互 |
| YT-Video-2.0 | `yt-video-2.0` | 图片 → 动态连贯视频 | 产品/广告/影视质感画面 |
| YT-Video-HumanActor | `yt-video-humanactor` | 单张人物照片 → 说话/表情视频 | 单图驱动人像，免授权肖像运行时 |
| YT-Video-FX | `yt-video-fx` | 图片 + 特效模板 → 动态特效 | 飘雪/拥抱/变身/万物归尘等模板 |

**和本 skill 的关系：互补，不是替代。**
- 本 skill = 工业化流水线（口播、矩阵号、真人质感、实拍混剪）。
- 这 4 个 = 扩散式直接生成动态画面（创意片段、素材生成、单图人像）。

**怎么接入你的工作流（推荐组合）：**
1. 用 `HY-Video-1.5` / `YT-Video-2.0` 生成几段素材片段（MP4）；
2. 把它们当作**实拍素材**喂进本 skill 的「②.5 混剪层」（autoclip）→ 提取 `clip_segments`；
3. 再走中游脚本 + 下游配音渲染，汇入成片。
→ 等于给 Path A 混剪流补上「AI 生成素材」入口，不必自己拍/找素材。

> ⚠️ 这 4 个模型**不在本 skill 目录内**，由平台统一提供，无需安装任何依赖。🔴 **仅 WorkBuddy 平台可用**——依赖平台内置运行时与「多模态内容生成」入口，无法在其它 agent 上复现。
> 触发方式：直接说「用文字/图片生成视频」「把这张图变成动态视频」即可唤起「多模态内容生成」。

---

## 🧩 平台兼容性与适配范围（重要 · 仅 WorkBuddy vs 可移植）

> 本 skill **在 WorkBuddy 上开箱即用**。但内部各能力的"可移植到 Codex / Claude Code / 其它带 bash 的 agent"程度不同——下面逐能力标注，方便你判断能搬哪些、哪些搬不了。

| 能力 | 适配范围 | 说明 |
|------|---------|------|
| 🧩 AI 直出视频（HY-Video / YT-Video 4 模型） | 🔴 **仅 WorkBuddy** | 模型由平台内置，外部无等价实现；必须经「多模态内容生成」入口调用 |
| Path A 付费通道（百炼 / 剪映 / GPT-SoVITS / CosyVoice / 数字人） | 🔴 **仅 WorkBuddy** + 需各自账号密钥 | 依赖平台托管或外部付费服务 |
| 「多模态内容生成」入口 / 零配置 WebSearch·WebFetch / 受管 Python·Node 运行时 | 🔴 **仅 WorkBuddy** | 平台内置工具与运行时 |
| Path B 免费链路（edge-tts + HyperFrames + ffmpeg + 本地脚本） | 🟢 **可移植** | 纯开源组件（Python/Node/ffmpeg），改写成 AGENTS.md / Claude Code skill 格式 + 备好环境即可在别处跑 |
| 合规六闸 / 脚本 10 维优化 / 分镜 shot_plan（纯逻辑层） | 🟢 **可移植（作为方法论）** | 本质是 markdown SOP 与提示词，任何 agent 可读可执行 |
| autoclip 混剪层（实拍素材高光提取） | 🟡 **部分可移植** | 依赖开源 autoclip CLI + ffmpeg，逻辑可搬；与本 skill 字段衔接需适配 |

**一句话结论**：当「可运行的 skill」只认 WorkBuddy；当「编排思路 / 免费渲染脚本」可在其它 agent 复用——最现实做法是拆出 **Path B 免费链路**独立版（摘掉平台专属入口即可）。

---

## 🤝 多 Agent 模式（可选 · 把 6 个子模块交给会 spawn agent 的宿主并发编排）

> 上方「五层模块（按需加载）」默认是**单主机串行**：一个宿主 agent 拿着本 SKILL.md，按「大脑 → 脚本 → 绘图 → 渲染」顺序逐层读、把结构化 JSON 字段往下传（见上方字段传递图）。
> 如果你想真正**多 agent 并发**（几个角色同时干、再汇总），可以把本 skill 的 6 个子模块交给一个**能 spawn 子 agent 的宿主**（例如 WorkBuddy 的「AI 内容创作专家团 · 司远」）来编排——这也正好是调用上方「🧩 AI 直出视频」4 个平台视频模型的入口（本 skill 自己到不了）。

### 子模块 → 专家团成员 映射

| 本 skill 子模块（agent） | 专家团对应成员 | 职责衔接 |
|------|---------|------|
| 大脑 `douyin-brain-strategy` | `creative-strategist` | 账号定位 / 选题 / 合规六闸 |
| 脚本 `douyin-script-optimizer` | `copywriter` | 口播稿 + `shot_plan` + 质量门（`score`） |
| 绘图 `douyin-image-generator` | `image-creator` | 9 模型生图 / 素材摄入 |
| 渲染 `video-render-engine` + 混剪 `douyin-montage` | `video-generator` + `video-editor` | 配音渲染 / 平台视频模型 / 剪辑混剪 |
| 采集 `content-collector` | 宿主 WebSearch 或 `content-adapter` | 热点 / 素材采集 |

> ⚠️ **两个「司远」别混**：本 skill 第 176 行的「主理人（司远）」只是文档里的**角色比喻**（指跑这份 skill 的人）；真正的多 agent 宿主是另一套「AI 内容创作专家团 · 司远」专家，两者独立、不要对号入座。

### 并发要点（多 agent 模式）

- **可并行**：绘影生图 与 平台视频模型生成素材片段 互不依赖，可同时派 `image-creator` 和 `video-generator`；
- **必须串行**：脚本层（`copywriter`）先出 `optimized_script` + `shot_plan`，绘影和渲染才能接字段；
- **合规闸门**：大脑设计的合规规则在每一层（尤其 `copywriter` 产出前）都要回放，任一不过即拦截；
- **汇总成片**：宿主把各 agent 产物（文案 / 图 / 视频片段）交给 `video-editor` 拼接，或回灌本 skill 的「②.5 混剪层」。

### 适配范围再提醒

- 多 agent 模式下，**平台 4 视频模型（HY/YT）变得可达**——补齐了本 skill 本地链路缺的「AI 生成素材」短板（接入法见「🧩 AI 直出视频」）；
- 但 Path A 付费通道、平台运行时仍 🔴 **仅 WorkBuddy**；Path B 本地链路仍 🟢 **可移植**。

---

## 文件索引与阅读路径

| 你的目标 | 读这些（按顺序） | 预计时间 |
|---------|-----------------|---------|
| **第一次用，想快速出片** | 本文件「⚡一键安装」→ `references/path_b_beginner.md` → `scripts/path_b_build.py --help` | 10 min |
| **只想写/优化脚本** | 本文件 → `skills/抖音/SKILL.md` 前5节 | 15 min |
| **只想配音+渲染** | `skills/video-render-engine/SKILL.md`（有📑顶部导航） | 20 min |
| **想用 Remotion 模板化出片** | `skills/video-render-engine/SKILL.md §9.3` → `templates/remotion/` | 25 min |
| **有实拍素材要混剪** | `skills/混剪/SKILL.md` → `skills/抖音/SKILL.md` | 20 min |
| **想了解完整 Path A** | 本文件路径介绍 → 逐层 Read 各模块前3节 | 40 min |
| **遇到问题排错** | 本文件「🚨30秒自救」→ `skills/抖音/references/error-handling.md` | 按需 |
| **高级功能** | 上方「🎓高级功能」表 → 对应深潜文档 | 因功能异 |

### 核心文件清单

- `scripts/install_path_b_deps.py` — Path B 依赖安装 + 环境自检（**首次必跑**）
- `scripts/path_b_build.py` — Path B 全链路串联脚本
- `templates/hyperframes_path_b/` — Path B 现成合成模板（lint 0 错误）
- `skills/大脑/SKILL.md` — 策略引擎 **[🟡]** 账号定位/选题/合规六闸
- `skills/采集/SKILL.md` — 内容采集 **[🟢]** 零配置热点采集
- `skills/混剪/SKILL.md` — 素材混剪 **[🟡]** AI 高光提取 / autoclip 粗剪
- `skills/抖音/SKILL.md` — 脚本优化器 **[🟡]** 口播稿+分镜+质量门
- `skills/绘图/SKILL.md` — 绘影图像层 **[🟡]** 9 模型 AI 生图
- `skills/video-render-engine/SKILL.md` — 渲染引擎 **[🔴]** 配音×渲染 → 成片
- `skills/抖音/references/error-handling.md` — 完整错误码 E001-E015 + 大白话翻译 + 高级排错
- `skills/抖音/assets/` — Dify 工作流骨架 + 质量门运行器
- `references/path_b_beginner.md` — Path B 新手指南（5分钟白话版）
- `references/path_b_runbook.md` — Path B 一站式手册（含排错）
- `skills/video-render-engine/references/dubbing-methods.md` — 5 种配音方案详解
- `skills/video-render-engine/references/render-channels.md` — 5 种渲染通道详解
- `avatars/` — 团队头像（上传 SkillHub 时可跳过）

---

> **v5.1.8（T.C.E 六轮评审 · 双向融合最终版）**：
> 融合 v5.1.7（内容最全）与 v5.1.8（评审精简重构）两版优点——
> **吸收 5.1.8 的结构改进**：①「⚡ 一键安装」提到文件最前（Win/Mac 复制即跑）；② 每条路径加 **[付费]/[免费]** 标签 + **⚠️ 画面风格限制**最醒目标注；③「🎯 意图路由表」覆盖 12 种常见话术一站式；④「🚨 30 秒自救」10 种现象 + 安装排错表 + 4 步排查树全覆盖；⑤「🚨 避坑清单」4 场景 16 条 + 记忆口诀；⑥ edge-tts 联网依赖 + 自动降级在路径处醒目提示；⑦ **修正全部错误路径引用**（`error-handling.md` / `digital-human-training.md` / `render-channels.md` 指向正确子模块路径）。
> **保留 5.1.7 的实质内容**：独特价值表、国内适配矩阵、质量承诺、端到端实例、高级功能表、文件阅读路径、核心文件清单、Handoff 字段速查。
> **v5.2.0（平台 AI 视频模型接入 + 版本校正）**：① 新增「🧩 AI 直出视频（平台内置模型）」一节，补齐 WorkBuddy 内置 4 个 AI 视频大模型（HY-Video-1.5 / YT-Video-2.0 / YT-Video-HumanActor / YT-Video-FX），说明其与本 skill 编排路线的互补关系及「生成素材 → 回灌混剪层」的接入方式；② 意图路由表新增「文字/图片直接生成视频」话术去向；③ 修正 changelog 版本号漂移（frontmatter 已升 5.2.0，此处此前仍停留在 5.1.8）。
> **v5.2.1（平台兼容性与适配范围标注）**：① 新增「🧩 平台兼容性与适配范围」专节，按 🔴 仅 WorkBuddy / 🟢 可移植 / 🟡 部分可移植 逐能力标注可移植性；② 在「AI 直出视频」章节与 Path B 选择处加行内 🔴/🟢 标记；③ 同步 video-render-engine 子模块版本至 5.2.1。
> **v5.2.2（多 Agent 模式章节）**：① 新增「🤝 多 Agent 模式」专节，说明本 skill 默认单主机串行、如何把 6 个子模块交给能 spawn 子 agent 的宿主（如 AI 内容创作专家团）并发编排；② 给子模块→专家团成员映射、并发要点（可并行/必须串行）、与「🧩 AI 直出视频」衔接；③ 澄清文档内「主理人（司远）」比喻与真实多 agent 宿主的区别。
> **历史版本**：v5.1.0（双路径初版）→ v5.1.2（Path B 资产补全）→ v5.1.7（Round 5 结构性精简 627→345 行）→ v5.1.8（T.C.E 六轮评审双向融合最终版）→ v5.2.0（AI 直出视频章节 + 版本校正）→ v5.2.1（平台兼容性标注 + 子模块版本对齐）→ v5.2.2（多 Agent 模式章节）。
