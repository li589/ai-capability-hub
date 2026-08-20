# Path B 一键 Runbook · 采集→成片（免费端到端）

> 第二条路（Path B）：**零云费**，把"一个选题/一段文案"直接变成带 AI 配音 + 字幕的竖屏 MP4。
> 配音用微软免费接口 `edge-tts`，画面用开源 `HyperFrames`，合成用 `ffmpeg`。
> 与 Path A（高质量·自配）互补：Path B 不依赖任何付费 API / 云账号。

---

## 0. 它能做什么 / 不能做什么

| 能 | 不能 |
|----|------|
| 文字脚本 → 配音(中文多音色) + 动态幻灯片画面 + 烧字幕 → MP4 | 不是"数字人说话"那种口播（那是 Path A + 数字人通道） |
| 完全本地、零云费、无需 API Key | 画面是"文字+动画"风格，不是实拍/AI 生成真人 |
| 竖屏 1080x1920（抖音）/ 横屏可改 | 复杂特效、转场需手写 HTML，超出本 Runbook 基础范围 |

---

## 1. 安装依赖（一次性）

```bash
# ① pip 装配音; ② npm 装渲染; ③ 系统装 ffmpeg; ④ Chrome 由渲染时自动下载
python scripts/install_path_b_deps.py --auto
```

脚本会：装 `edge-tts`、全局装 `hyperframes`、尝试 `winget` 装 `ffmpeg`、下载 Chrome，最后跑 `hyperframes doctor` 自检。
若某步失败，脚本会给出手动安装指引（ffmpeg 需手动加 PATH）。

> 只检查不安装：`python scripts/install_path_b_deps.py --check`

---

## 2. 准备脚本

两种输入：

**A. 纯文本**（空行分段，每段=一个分镜。段首短行自动当标题）：

```text
三招让手机拍出电影感

第一招，找光源。逆光拍剪影，侧光出质感。
第二招，稳字当头。手抖就靠墙，或者上稳定器。
第三招，留白。画面别塞满，给主体呼吸的空间。
```

**B. JSON**（更可控，可指定每段音色）：

```json
[
  {"title": "三招拍出电影感", "body": "第一招，找光源。", "voice": "zh-CN-YunxiNeural"},
  {"title": "", "body": "第二招，稳字当头。", "voice": "zh-CN-YunxiNeural"}
]
```

可选音色（edge-tts）：`zh-CN-XiaoxiaoNeural`(女声·推荐)、`zh-CN-YunxiNeural`(男声)、`zh-CN-YunyangNeural`(新闻男声)。

---

## 3. 一条命令出片

```bash
python scripts/path_b_build.py \
  --input script.txt \
  --output final.mp4 \
  --voice zh-CN-XiaoxiaoNeural \
  --resolution 1080x1920
```

流程内部自动走完：分段 → 每段 edge-tts 配音+字幕 → 生成 HyperFrames 合成 HTML（时序对齐配音时长）→ `hyperframes render` 出静帧视频 → `ffmpeg` 拼音频+烧字幕 → **final.mp4**。

调试可用 `--skip-render`（只出音频+HTML 不渲染）或 `--keep`（保留中间文件）。

---

## 4. 直接手改模板（不写代码也能用）

不想跑脚本，想手工控制画面？直接用模板工程：

```bash
# 改 templates/hyperframes_path_b/index.html 里的分镜文字与时序
npx hyperframes render -c templates/hyperframes_path_b/index.html -o out.mp4
# 校验格式:  npx hyperframes lint templates/hyperframes_path_b
```

模板里每个 `<div class="clip">` 是一个分镜，`data-start`/`data-duration` 控制时序（秒），
`#root` 的 `data-duration` 是总时长（=各分镜之和）。动画在底部 `<script>` 用 GSAP 写。

---

## 5. 排错

| 现象 | 原因 / 解决 |
|------|------------|
| `edge-tts` 报 403 / 连不上 | 网络出口限制（连微软语音服务）。换能联网的环境；国内机器通常可用。 |
| `hyperframes render` 卡住/报错 | 多半没 Chrome：先 `npx hyperframes browser ensure`；确认 `hyperframes doctor` 全绿。 |
| `ffmpeg` 找不到 | 没装或没加 PATH：重跑 `install_path_b_deps.py --auto`，或手动装 ffmpeg 并加 PATH。 |
| 字幕烧不上去 | 确认 `subs.vtt` 生成、路径无中文空格；可去掉 `--vf` 先试纯合成音频。 |
| 视频无声 | 检查 `narration.mp3` 是否生成（edge-tts 那步是否成功）。 |

---

## 6. 与 Path A 怎么选

- **要快、要免费、要"文字→视频"口播风格** → Path B（本 Runbook）。
- **要数字人/实拍质感/品牌级精修/多通道渲染** → Path A（大脑→脚本→图像→`video-render-engine`）。
- 两者都从"采集"模块拿素材，从中游拿优化脚本，区别在下游渲染引擎。
