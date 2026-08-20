# 抖音短视频生产专家团 (douyin-video-skill)

> 抖音短视频一站式生产体系：**一条 Skill，两条路**。
> **Path A（高质量·自配）**：大脑定方向 → 采集 → 脚本优化 → 图像采编 → AI 配音与多通道渲染出片，五模块串行。
> **Path B（免费端到端·开箱快）**：采集 → 脚本 → edge-tts 免费配音 + HyperFrames 开源渲染 → MP4，零云费。
> 全程内置 2026 年最新 AI 合规闸门。

## 一句话介绍

把"做一条抖音短视频"拆成可编排的流水线，由主理人（司远）统一调度策略、脚本、图像、渲染、适配五个模块，从选题一路走到成片。高质量路线可选付费配音/渲染通道，免费路线一条命令零云费出片。

## 类型

**单 Skill（内含 5 模块）**。原 Team 型专家包已折叠为单 Skill 形态：5 个角色（策远/润笔/绘影/渲工 + 主理人）对应 5 个模块（`skills/大脑`、`skills/抖音`、`skills/绘图`、`skills/video-render-engine` + 根主理人层），由根 `SKILL.md` 统一编排。

## 两条生产路径（核心差异）

| | Path A · 高质量自配 | Path B · 免费端到端 |
|---|---|---|
| 定位 | 品牌质感 / 专属人声 / 精修 | 快、免费、蹭热点、批量 |
| 链路 | 大脑 → 采集 → 抖音(脚本) → 绘图(配图) → 渲染出片 | 采集 → 抖音(脚本) → edge-tts + HyperFrames → MP4 |
| 配音 | 5 选 1（百炼 / GPT-SoVITS / VoxCPM2 / CosyVoice / **edge-tts 免费**） | **edge-tts（微软免费接口，无需 Key）** |
| 渲染 | 5 选 1（剪映 / Remotion（v5.2 新增可运行模板）/ ffmpeg / 数字人 / **HyperFrames 免费**） | **HyperFrames（Heygen 开源，本地渲染）** |
| 成本 | 视所选通道（部分付费） | **零云费**（仅本地算力） |
| 依赖 | 所选通道各自的运行时 | Node≥22 + FFmpeg + Chromium + 联网 |
| 适用 | 要质感、要数字人、要品牌级 | 要速度、要省钱、模板化批量 |

两条路共用同一套 `optimized_script` / `shot_plan` / `dubbing_method` / `render_channel` / `ai_label_config` 字段，可随时切换。

## 它能帮你做什么

- **从 0 到成片（Path A）**：给我赛道 / 产品 / 选题，自动走完"定位 → 选题 → 脚本 → 配图 → 配音 → 渲染 → 成片"。
- **免费快出（Path B）**：给我热点 / 文案，采集 + 脚本 + edge-tts + HyperFrames 直接出 MP4，**零云费**。
- **只优化脚本**：你有口播初稿，按 10 维模型提质、防同质化、配分镜与标题。
- **只出片**：脚本已定，选 AI 配音（5 选 1）× 渲染通道（5 选 1），输出成片。
- **数字人（Path A）**：想训练/克隆专属数字人，见 `skills/video-render-engine/references/digital-human-training.md`。
- **混剪实拍素材（可选）**：丢入多段实拍/录屏，`skills/混剪` 用 autoclip 自动高光提取，输出标准 `clip_segments.json` 后再写口播脚本，适合已有素材想快速出片（v5.2 新增）。
- **合规兜底**：内置六闸（标注 / 人设 / 红线 / 导流 / 质量 / 矩阵），出片前回放，任一不通过即拦截。
- **AI 直出视频（平台内置模型）**：除脚本驱动流水线外，还可用 WorkBuddy「多模态内容生成」入口直接调用 `HY-Video-1.5`（文生视频）/ `YT-Video-2.0`（图生视频）/ `YT-Video-HumanActor`（单图驱动人像）/ `YT-Video-FX`（图片特效视频）直出素材片段，再回灌混剪层衔接下游配音渲染。详见根 SKILL.md「🧩 AI 直出视频」章节。

## 五大模块

| 模块 | 路径 | 职责 |
|------|------|------|
| 根 · 主理人层 | — | 司远编排调度、合规闸门总控、汇编交付 |
| `skills/大脑` | Path A（Path B 可选） | 账号定位 / 选题 / 流量池战略 / 合规六闸 / 推荐通道 |
| `skills/采集` | Path B（Path A 可选） | 全网素材采集（零配置 WebSearch/WebFetch 或 feedgrab 深度模式） |
| `skills/抖音` | Path A + Path B | 脚本优化器（Dify 可选：对话直跑 / 导入 DSL；10 维优化 + shot_plan） |
| `skills/绘图` | Path A（Path B 可选） | 图像采编（9 模型切换的 AI 生图 + 素材摄入映射） |
| `skills/混剪` | 实拍素材流（可选） | AI 高光提取 / 自动粗剪（autoclip）→ 标准 clip_segments.json（v5.2 新增） |
| `skills/video-render-engine` | Path A + Path B | 配音（5 选 1）× 渲染通道（5 选 1）→ 成片 + 自检卡 |

## 快速开始

### Path A · 端到端高质量生产
> 我要做一条抖音短视频，从选题到成片帮我走完五模块流水线

主理人自动走 大脑 → 采集 → 抖音(脚本) → 绘图(配图) → 渲染出片。

### Path B · 免费端到端（新手先看这里）
> 帮我采集最近 XX 热点，写脚本并用 edge-tts + HyperFrames 直接出一条 MP4

- **新手指南（5 分钟出第一条）**：`references/path_b_beginner.md`
- **完整手册（含排错）**：`references/path_b_runbook.md`
- 现成资产：`templates/hyperframes_path_b/`（模板）、`scripts/path_b_build.py`（串联）、`scripts/install_path_b_deps.py`（装依赖）

最简用法：
```bash
python scripts/install_path_b_deps.py --auto     # 一次性装依赖
python scripts/path_b_build.py --input 脚本.txt --output final.mp4
```

### 只优化脚本 / 只出片
> 我有口播初稿，用中游优化器提质        （跳过大脑层）
> 脚本已定，用下游渲染引擎出片          （跳过前两阶段）

## 合规闸门（关键差异点）

在大脑层内置六闸：`标注 / 人设 / 红线 / 导流 / 质量 / 矩阵`。渲工出片前回放六闸，任一不通过即停渲。规则基准：2026.7.21 抖音安全与信任大会 + 2026.6.15 AI 合规池 + 2026.7.8 佣金新规 + 《人工智能生成合成内容标识办法》(2025.9.1 起施行，数字人须加显式+隐式 AI 标识)。

## 目录结构

```
douyin-video-skill/
├── SKILL.md                         # 根 · 主理人层（双路径编排 / 模块路由 / SOP / handoff）
├── settings.json                    # 版本号 (5.2.2)
├── README.md
├── skills/
│   ├── 大脑/SKILL.md                # 上游策略引擎 (v5.x)
│   ├── 采集/SKILL.md                # 外部内容采集 (⭐v5.1 新增)
│   ├── 抖音/SKILL.md                # 中游脚本优化 (Dify 可选)
│   ├── 绘图/SKILL.md                # 绘影图像层
│   ├── 混剪/SKILL.md                # ⭐v5.2 新增：实拍素材混剪 (autoclip 高光提取)
│   └── video-render-engine/
│       ├── SKILL.md                # 下游渲染引擎 (5 配音 × 5 通道)
│       └── references/
│           ├── digital-human-training.md   # 数字人训练方法 (Path A 参考)
│           ├── dubbing-methods.md
│           └── render-channels.md
├── references/
│   ├── brain-layer.md
│   ├── quickstart.md
│   ├── skillhub-listing.md
│   ├── path_b_runbook.md            # Path B 完整手册
│   └── path_b_beginner.md          # Path B 新手指南
├── templates/
│   ├── hyperframes_path_b/          # Path B 现成合成模板 (已 lint 0 错)
│   │   ├── index.html
│   │   ├── hyperframes.json
│   │   └── meta.json
│   └── remotion/                    # ⭐v5.2 新增：Remotion 可运行渲染工程
│       ├── package.json
│       ├── tsconfig.json
│       ├── remotion.config.ts
│       ├── src/                     # Video.tsx / index.tsx / types.ts
│       ├── public/style.css
│       └── README.md
├── scripts/
│   ├── path_b_build.py              # Path B 全链路串联
│   ├── install_path_b_deps.py       # Path B 依赖安装 + 自检
│   ├── render_remotion.py           # ⭐v5.2 新增：编排 Remotion 出片
│   └── run_autoclip.py              # ⭐v5.2 新增：包装 autoclip 混剪
└── avatars/                         # 团队头像 (SkillHub 上传时若提示二进制可忽略)
```

## 安装与注册

这是**单 Skill**，安装 = 把 `douyin-video-skill/` 整个目录放到 WorkBuddy 的 skills 目录：

```
# Windows 示例
C:\Users\<你>\.workbuddy\skills\douyin-video-skill\
# macOS / Linux
~/.workbuddy/skills/douyin-video-skill/
```

重启 WorkBuddy 后，用自然语言触发即可（如"帮我做条抖音短视频"）。发布到 SkillHub 的说明见 `references/skillhub-listing.md`。

## 依赖说明（Path B 用户必读）

Path B 免费但不"零安装"——需本地准备：
- **Node.js ≥ 22**（HyperFrames 要求）
- **FFmpeg + FFprobe**（合成与字幕）
- **Chromium**（HyperFrames 首次渲染自动下载，或 `npx hyperframes browser ensure`）
- **Python ≥ 3.10** + `edge-tts`（配音，微软免费接口，需联网调用）

一条命令装齐：`python scripts/install_path_b_deps.py --auto`。

## 常见问题（FAQ）

**Q1：需要先装 Dify / 剪映 / 配音模型吗？**
A：纯"选题 + 脚本"阶段零外部依赖（中游支持对话直跑，Dify 可选）。Path B 出片依赖本地 Node≥22 + FFmpeg + edge-tts + Chromium；Path A 的付费通道（百炼/剪映等）才需要对应账号/软件。

**Q2：Path B 真的免费吗？**
A：零云费、无订阅、无按量计费——配音用微软免费 edge-tts 接口，画面用开源 HyperFrames 本地渲染。代价是本地得装好上述依赖，且 edge-tts 音色是微软预设（不可克隆专属声线）。

**Q3：某一层返回不完整 / 卡住怎么办？**
A：主理人会通报阶段状态。若某模块产出缺字段，主理人回退补派，不跳过阶段；仍异常可手动指定阶段重跑。

**Q4：会违规吗？**
A：内置六闸在出片前拦截红线（稀缺逼单、虚假价格、售后造假、虚假权威极限词、私域导流零容忍、AI 漏标等）。数字人视频须加显式+隐式 AI 标识。但 AI 不替代平台终审，发布前仍建议人工过一遍。

**Q5：支持横屏 / 竖屏吗？**
A：支持。中游产出 `aspect_ratio`（9:16 / 1:1 / 16:9），下游按之出片；Path B 默认竖屏 1080×1920，可在脚本/参数里改。

## 版本与更新

- **v5.2.0**（2026-07-27）：**功能扩展（内容同步本次更新）**——① 新增 `skills/混剪` 模块：用 autoclip 对实拍素材做 AI 高光提取 / 自动粗剪，输出标准 `clip_segments.json` 衔接脚本层；② 新增 Remotion 可运行渲染通道：`templates/remotion/` 完整工程（React + TS，支持 9:16 / 1:1 / 16:9、按 shot_plan 切镜、字幕、AI 标识）+ `scripts/render_remotion.py` 一键编排出片；③ `scripts/run_autoclip.py` 包装 autoclip CLI 归一化输出；④ 根 SKILL.md 新增「🧩 AI 直出视频（平台内置模型）」章节，列举 `HY-Video-1.5` / `YT-Video-2.0` / `YT-Video-HumanActor` / `YT-Video-FX` 四个平台 AI 视频模型及其与混剪层的衔接法，意图路由表同步增补。根 SKILL.md 的路由表、字段传递图、端到端示例已同步。
- **v5.2.1**（2026-07-28）：**平台适配范围标注**——新增「🧩 平台兼容性与适配范围」专节，逐能力标注 🔴 仅 WorkBuddy / 🟢 可移植 / 🟡 部分可移植（AI 直出视频与 Path A 付费通道绑定平台；Path B 免费链路与纯逻辑层可搬到 Codex / Claude Code 等带 bash 的 agent）；并在 AI 直出视频章节、Path B 选择处加行内标记。版本号同步升至 5.2.1。
- **v5.2.2**（2026-07-28）：**多 Agent 模式章节**——新增「🤝 多 Agent 模式」专节，说明本 skill 默认单主机串行、如何把 6 个子模块交给能 spawn 子 agent 的宿主（如 AI 内容创作专家团）并发编排；给出子模块→专家团成员映射、并发要点（可并行/必须串行）及与「🧩 AI 直出视频」的衔接；澄清文档内「主理人（司远）」比喻与真实多 agent 宿主的区别。版本号同步升至 5.2.2。
- **v5.1.8**（2026-07-25）：**T.C.E 六轮评审综合重构**——①「⚡ 一键安装」提到文件最前面（Win/Mac 命令复制即跑）；② 每条路径加 **[付费]** / **[免费]** 标签 + **⚠️ 画面风格限制**最醒目标注（Path B 动画风非真人实拍）；③「🎯 意图路由表」10 种常见话术一站式；④「🚨 30 秒自救卡」10 种现象全覆盖（不用查文档解决 95% 问题）；⑤「🚨 避坑清单」独立大节（4 场景 16 条 + 记忆口诀）；⑥ edge-tts 联网依赖 + 自动降级策略醒目提示；⑦ 已知限制对比表紧贴路径选择；⑧ 结构精简去重 50%+；⑨ error-handling 新增「小白话速懂」表（11 码全覆盖 + 修完后下一步）。
- **v5.1.2**（2026-07-22）：Path B 可用性补全——模板工程/串联脚本/安装脚本/手册/新手指南；订正 HyperFrames 合成格式。

## 头像说明

头像在 `avatars/` 目录下（团队风，512×512）。SkillHub 网页端上传单 Skill 时若提示二进制跳过、显示默认头像，属非致命，可忽略；本地加载不影响功能。
