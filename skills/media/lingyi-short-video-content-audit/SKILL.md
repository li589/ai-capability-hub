---
name: lingyi-short-video-content-audit
display_name: 短视频内容审核（文案/画面/声音）
display_name_en: "Short-Video Compliance Audit (Text/Visual/Audio)"
description_zh: "【零一数科·出品】短视频内容审核（文案/画面/声音）（付费版）。视频发布前内容合规质检。支持口播文本或本地视频上传；文本层实质质检+画面声音人工复核清单+总判定。触发词：短视频内容审核、口播合规、发布前违禁词、广告法视频。"
description_en: "[Lingyi Tech] Pre-publish short-video compliance audit covering text-level violations, a visual/audio manual checklist, and an overall verdict."
category: content-creation
version: 0.1.0
author: 小风、CoderPig
---

# 短视频内容审核

> 版本：v0.1.0 · 作者：小风、CoderPig

对即将发布的视频做发布前合规排雷：**文本层实质质检 + 画面声音检查清单 + 特殊行业双关 + 总判定**。

| 环节 | 耗时 | 扣点 |
|------|------|------|
| **本地视频上传**（可选） | 视文件大小 | **不扣点**（上传换取后续分析用 id） |
| **短视频内容审核（仅口播文本）** | 约 1 分钟 | 约 20 点（按 token 实扣；**首次成功读取结果时结算**） |
| **短视频内容审核（有 video / video_id，走多模态）** | 约 5–10 分钟，片长更长会再往上 | 同上 |
| **Excel 空白模板**（本地） | 秒级 | 不扣点 |

⚠️ **对用户说话要说人话。** 不提 task_id、退出码、接口路径等技术细节。一句只做一件事。

⚠️ **边界**：本 skill **不在本地解析**视频画面；用户给本地视频时由脚本上传后由远端完成提取与质检。无视频时也可只传口播/字幕文本质检。

## 执行流程

1. 取 `LY_API_KEY`  
2. 收集输入（至少其一）：**口播/字幕**、**本地视频文件**、**已有 video_id**；再加平台/行业等可选字段  
3. **扣点确认（硬门禁）**：新任务创建前，必须先说明预估扣点并等用户明确确认；**未确认 / 未回应 / 改主意 → 禁止运行创建脚本**。仅 `--poll-task` 续轮询不重复确认。详见「扣点与确认」。  
4. 确认后跑脚本：若有本地视频 → 自动上传换 `video_id` → 创建质检任务；拆分轮询，禁止长同步阻塞  
5. 把 Markdown 报告渲染进对话，并告知本次实际扣点  
6. **额外**跑本地 Excel 空白模板脚本，把路径告诉用户  

### 本地视频上传（内部）

用户给本地视频路径时，脚本自动：上传文件 → 换取 `video_id` → 再创建质检任务（可同时带口播 text）。

上限 **100MB**；支持扩展名：mp4 / mov / m4v / avi / mkv / webm / flv / wmv。超限或格式不对直接参数错误退出，不发起上传。

### 异步与扣点（内部）

- 创建任务 → 轮询结果 → 完成则交付报告  
- **扣点时机**：任务完成后**第一次**成功读取结果时结算（只扣一次）  
- 脚本默认轮询间隔 **60s**；拆分模式下单次 `--poll-task` 只查一次  
- 有视频时远端要下载、压缩、多模态抽取再质检，**5–10 分钟仍是 running 属正常**，不要按「一两分钟」判断失败 

### 拆分轮询

1. 创建（示例：本地视频）：

```bash
python3 scripts/video_compliance.py --video "/path/to/video.mp4" --platforms douyin,xhs --only-create
```

或仅口播：

```bash
python3 scripts/video_compliance.py --text "<口播>" --platforms douyin,xhs --only-create
```

2. 对用户（有本地视频 / video_id）：「在看视频了，多模态大概五到十分钟，好了直接给你看。」仅口播文本：「在质检了，大概一分钟。」  
3. 循环 `--poll-task`：0 交付 / 13 继续 / 12 失败 / 9 上传失败可重试。有视频时至少等到 **10 分钟** 再考虑异常，中途 exit 13 立刻再 poll，不要提前放弃。 

### Excel 模板（本地、不扣点）

报告 Markdown 交付后，**必须再生成**可填 Excel 空白模板：

```bash
python3 scripts/gen_qc_xlsx.py --out ./短视频内容审核清单.xlsx
# 缺 openpyxl 时：
python3 scripts/gen_qc_xlsx.py --install-deps --out ./短视频内容审核清单.xlsx
```

stdout 含 `VIDEO_QC_XLSX_FILE=<绝对路径>`。对用户说：

> Excel 模板已生成：&lt;路径&gt;，打开即可填；对话里的质检报告 Markdown 与之一一对应。

## 鉴权

`config.json` → `LY_API_KEY`；缺失引导  
<https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy>

## 信息收集

| 用户提供 | 说明 |
|----------|------|
| **口播/字幕** | 与本地视频 / video_id 至少其一；**仅文本**时建议 ≥20 字 |
| **本地视频** | 拖入文件或给路径；脚本上传换 `video_id`（≤100MB） |
| **video_id** | 已有则直接用，**跳过上传**；可与 text 同给 |
| **平台** | 抖音/视频号/小红书/B站/快手，可多选；默认全平台 |
| **行业** | 可选，医美/金融/教培等影响专项检查 |
| **资质** | 可选 |
| **标题封面 / 是否带货** | 可选 |

平台映射：抖音→`douyin`，视频号→`channels`，小红书→`xhs`，B站→`bilibili`，快手→`kuaishou`。

> 报告骨架与样例见 `references/template.md`、`references/sample.md`。

## 扣点与确认

本技能每次「新发起」质检任务会消耗点数；整条链路的扣点感知由你（assistant）贯穿，**不能跳过确认直接开跑**。

- **执行前确认（仅新任务）**：输入齐、API Key 就绪后，**先停下来**用下面话术请用户确认，再运行 `video_compliance.py`（含 `--only-create`；含本地上传）：

  > 本次短视频内容审核预计扣点约 20 点，实际按 token 用量实扣。是否继续？

  等用户明确说「继续 / 可以 / 确认」等同意表述后再跑脚本。  
  用户未确认、未回应、或要求先改口播/换视频时，**不要运行脚本**。

- **上传本身不单独扣点**；确认话术仍按「质检约 20 点」说明即可。

- **仅轮询不重复确认**：已创建过任务、只跑 `--poll-task` 时，**不要再问一遍扣点**。

- **失败重试**：用户同意「再试一次」后，才可跑 `--retry-task` 或重新创建；重新创建新任务须再走一次扣点确认。

- **执行成功后回告实际扣点**：见「输出交付」，用 `VIDEO_QC_POINTS_USED` 告诉用户「本次实际扣除 {N} 点」；为空时说「约 20 点（实际以账户明细为准）」。

- **执行失败后告知点数处理**：任务已发起但未成功产出报告时，告知「因异常本次未完成，相应点数已退回/未扣除（以账户为准）」，并询问是否重试。上传阶段失败（退出码 9）任务未创建，**不扣点**。

- **Excel 模板**：本地生成，**不扣点**，无需为此单独确认。

## 运行方式

```bash
# 本地视频：上传 → 创建质检
python3 scripts/video_compliance.py \
  --video "/path/to/video.mp4" \
  --platforms douyin,channels \
  --industry 美妆 \
  --is-commerce \
  --only-create

# 口播文本
python3 scripts/video_compliance.py \
  --text "<口播或文件>" \
  --platforms douyin,xhs \
  --only-create

# 已有 video_id（可与 text 同给）
python3 scripts/video_compliance.py --video-id <video_id> --platforms channels --only-create

python3 scripts/video_compliance.py --poll-task <task_id> --out ./短视频内容审核报告.md
python3 scripts/video_compliance.py --retry-task <task_id> --out ./短视频内容审核报告.md

# 交付报告后生成本地 Excel
python3 scripts/gen_qc_xlsx.py --out ./短视频内容审核清单.xlsx
```

## 输出交付

```
VIDEO_QC_VIDEO_ID=<上传或传入的 video_id，可有可无>
VIDEO_QC_POINTS_USED=<实扣，来自 data.total_points>
VIDEO_QC_PLAN_POINTS=20
VIDEO_QC_REPORT_FILE=<路径>
VIDEO_QC_TASK_ID=<id>
=== VIDEO_QC_REPORT_START ===
<Markdown>
=== VIDEO_QC_REPORT_END ===
```

**必须把报告 Markdown 完整渲染到对话。**

交付时按顺序：

1. **渲染报告**：START/END 之间的 Markdown 完整给用户。  
2. **告知实际扣点**：`VIDEO_QC_POINTS_USED` 非空 →「本次任务实际扣除 {N} 点」；为空 →「本次约 20 点（实际以账户明细为准）」。  
3. **Excel 模板路径** + 提醒画面项人工复核。

收尾示例：  
> 质检报告如上 ✅ 本次实际扣除 {N} 点。画面相关项请按清单人工再看一眼。Excel 模板：&lt;路径&gt;。

## 退出码

| 码 | 对用户 |
|----|--------|
| 0 | 渲染报告 |
| 2/8 | 取/换 API Key |
| 3 | 补参数 / 换合法视频（格式、大小） |
| 4 | 充值 |
| 9 | 视频上传失败，可稍后重试（**未扣点**） |
| 12 | 出了点问题，点数已退回，要不要再试？ |
| 13 | 还在质检 → 继续 poll |

`gen_qc_xlsx.py` 缺 openpyxl 时退出码 2：引导 `pip3 install openpyxl` 或 `--install-deps`。

## 原则

- **新任务必须先扣点确认再跑脚本**；未确认不得创建任务  
- 本地视频：脚本内上传后质检；报告以脚本返回为准，**禁止改写**  
- 异步创建 → 轮询 → 可选重试；禁止一次长阻塞  
- Excel **本地**生成、不联网、不扣点  
