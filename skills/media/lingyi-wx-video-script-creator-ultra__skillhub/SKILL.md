---
name: 视频号爆款文案生成（全能版）【零一数科·出品】
description: 【零一数科·出品】视频号爆款文案生成。一条链接二创脚本，丢进爆款视频号链接即以此骨架改写成你的视频脚本，或按方向/目的/商品原创多条视频脚本（含分段表、口播全文、六维质检评分）。付费版远端生成，约 98 点/次。
metadata:
  slug: lingyi-wx-video-script-creator-ultra
  version: v0.5.0
  author: 小风、CoderPig、Awen
  requires:
    bins:
      - python3
---

# 视频号爆款文案生成（全能版）【零一数科·出品】

> 版本：v0.6.0 · 作者：小风、CoderPig、Awen

通过远端付费 API 生成微信视频号爆款脚本，支持**创作**（按方向/目的/商品原创）与**二创**（以指定爆款视频为骨架改写）。二创源只支持**微信视频号分享链接**（不支持本地视频文件上传）。脚本 [scripts/generate_script.py](scripts/generate_script.py) 负责 config 拉取→创建任务→轮询→落接口响应 JSON，[scripts/render_report.py](scripts/render_report.py) 直接解析响应里的 `data.result.markdown` 字段原样输出为报告。接口契约见 [references/api.md](references/api.md)，取数路径见 [references/field-mapping.md](references/field-mapping.md)。

## 鉴权

Token 取「技能目录」（SKILL.md 所在目录）下 `config.json` 的 `LY_API_KEY` 字段，回退环境变量 `LY_API_KEY`。请求头 `Authorization: <api_key>`（裸 key，不带 `Bearer`）。`config.json` 形如：

```json
{ "LY_API_KEY": "你的密钥" }
```

运行前先确认 key：

1. **检查是否已有 key**：读 `config.json` 的 `LY_API_KEY` 是否非空；无则看环境变量 `LY_API_KEY`。任一有值即就绪。
2. **缺失则引导用户获取**：前往 <https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy> 取 API Key，把 key 直接发给你；收到后写入 `config.json` 的 `LY_API_KEY` 字段（保留其它内容）再继续。该文件已被 `.gitignore` 忽略。
3. **鉴权失败（退出码 8）**：key 失效或过期，重新获取并覆盖写 `config.json` 后重试，不反复用同一失效 key。
4. **SSL 错误**（`CERTIFICATE_VERIFY_FAILED` 等）：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用，有中间人风险）。

## 点数与计费提示

本 skill 调用的是远端付费 API，每个任务都会扣点。agent 必须在**创建任务前后**按下列三个时机向用户输出对应话术：

1. **执行前——扣点确认（必须先问，再创建）**：参数收齐、即将跑完整流程前，先告知用户预估扣点并请其确认，例如：

   > 本次「视频号爆款脚本生成」任务预估扣点约 **98 点**，实际扣点会根据任务复杂程度略有增减。是否继续执行？

   用户确认后再执行 `generate_script.py` 创建任务；用户未确认前**不要**发起创建。续传（`--task-id`，任务已创建过）不重复扣点，无需再确认。

2. **成功后——实际扣点回执 + 报告查看**：任务完成（退出码 0）后，从 stdout 标记块读取实际扣点并向用户回执，例如：

   > ✅ 任务已成功完成，本次实际扣点 **{N} 点**。

   - `{N}` 取自 `===POINTS_USED===` 标记块；若该块为空（后端未返回扣点字段），改说「实际扣点以账户侧扣点记录为准」，不要凭空编数字。
   - 紧接着告知用户如何查看报告：报告已落盘到 `===MD_PATH===` 标记块给出的路径，可直接打开该 Markdown 文件查看；同时在对话里附上报告正文（即 `===OVERVIEW_MD===` 内容）。

3. **失败后——网络原因 + 点数返还**：任务失败/超时（退出码 5/6/11 等，或脚本提示网络错误）时，统一安抚话术：

   > ❌ 本次任务因网络原因执行失败，已为您返还相应点数。请稍后检查网络后重试，或使用 `--task-id <script_task_id>` 续传同一任务（续传不重复扣点）。

   即便失败码（如 6 任务失败）非纯网络问题，对用户仍按上述话术说明点数已返还、引导续传/重试，不向用户透传后端原始错误码细节。

> 预估点数（98 点）仅为约定提示值；如需调整，改本节的「约 **98 点**」措辞即可。脚本本身不卡预估点数，一切以账户实际扣点为准。

## 信息收集

生成前与用户确认以下信息（缺项给默认建议，必填缺失则一次性问清）。**枚举字段一律用中文向用户展示，内部再映射回英文 value 传后端**（中文 label 会被 400 拒绝）。

### 两步收集流程（推荐）

1. **先拉可选项（用中文问用户）**：

```bash
python3 scripts/generate_script.py --show-options
```

只拉 config 并输出 `===CONFIG_OPTIONS===` 标记块（含每个枚举字段的 `label`(中文) + `value`(英文)），不创建任务。agent 读到后，**用中文 label 向用户弹窗询问**（如「这次二创的创作方向是什么？达人带货 / IP账号 / 品牌账号」）。

2. **拿到用户选择后，映射回英文 value 跑完整流程**：把用户选的中文对应回英文 value，传给 `--mode/--direction/--industry/--purpose/--platform/--script-type/--depth` 等参数。

| 字段 | 必填 | 说明（中文为主） |
|------|------|------|
| `mode` | 是 | 创作模式：创作(`creation`) / 二创(`recreation`) |
| `direction` | 是 | 创作方向：达人带货 / IP账号 / 品牌账号 等（以 config 可选值为准） |
| `industry` / `industries` | 至少一个 | 行业（config 给候选） |
| `purpose` / `campaign_types` | 至少一个 | 营销目的：直播带货 / 品牌 等（以 config 可选值为准） |
| `platform` | 是 | 发布平台，默认 视频号(`channels`) |
| `product` | 条件必填 | 创作且方向=达人带货时必填且非空对象（name/price/selling_points/target_users） |
| `source_video` | 条件必填 | 二创时必填，微信视频号分享链接 `share_url`（用 `--share-url` 传入） |
| `account_brief` | 否 | 账号/人设/品牌/栏目等补充信息 |
| `script_type` | 否 | 脚本类型（不传由后端自动匹配） |
| `count` | 否 | 生成条数 1–3，默认 1 |
| `target_duration_sec` | 否 | 目标时长 1–1800 秒 |
| `depth` | 否 | 创作深度：快速(`fast` 默认) / 深度(`deep`，单价更高需向用户确认) |
| `additional_requirements` | 否 | 额外要求：口吻、禁忌词、必含信息 |

**关键**：
- **向用户展示一律用中文 label**（来自 config 的 `options[].label`），**传给脚本/后端一律用英文 value**——传中文 label 会被 400 拒绝。脚本校验失败时也以「中文 label（英文 value）」对照提示合法值。
- **二创只支持微信视频号分享链接**：不支持本地视频文件上传；用户给分享链接用 `--share-url` 原样传给后端，不要索要或猜测 video_id。

## 运行方式

```bash
python3 scripts/generate_script.py \
  --mode creation --direction influencer_commerce --platform channels \
  --industry food --purpose live_commerce \
  --product '{"name":"土豆馍","selling_points":["五步古法","无添加"],"target_users":"中老年及主妇"}' \
  --count 1 --depth fast \
  --response-out /tmp/wxscript_response.json --md-out ./report.md
```

二创（微信视频号分享链接）：

```bash
python3 scripts/generate_script.py \
  --mode recreation --direction influencer_commerce --platform channels \
  --industry food --purpose live_commerce \
  --share-url "https://weixin.qq.com/sph/..." \
  --count 1 --response-out /tmp/wxscript_response.json --md-out ./report.md
```

续传已超时任务（跳过创建、不重新计费，直接轮询）：

```bash
python3 scripts/generate_script.py --task-id "<script_task_id>" \
  --response-out /tmp/wxscript_response.json --md-out ./report.md
```

可选参数：`--script-type`、`--account-brief '<json>'`、`--source-video '<json>'|--share-url <url>`、`--target-duration-sec`、`--additional-requirements`、`--skip-config`（跳过枚举预校验）、`--insecure`、`--poll-interval`、`--poll-timeout`。

## 执行流程

1. **取 API Key**：读 `config.json` / 环境变量；缺失→退出码 2，引导获取。
2. **扣点确认（创建前必备）**：参数收齐后、跑 `generate_script.py` 创建任务前，按「点数与计费提示」第 1 步告知用户预估扣点约 98 点并请其确认；用户确认后再继续。续传（`--task-id`）跳过此步。
3. **（无 `--task-id`）组装并创建**：GET config 拉可选值 → 校验枚举入参∈options.value、必填规则、product 非空、源视频、范围 → 组装 body（自动注入 `origin=workbuddy`、`origin_method=skill`）→ POST 创建，取 `script_task_id`。
4. **轮询**：按 `--poll-interval` 轮询，看 `data.status`（completed/success/succeeded/done=完成；failed/error/cancelled=失败；pending/queued/running/processing=执行中）。进度写 stderr。每次轮询把最新响应落 `--response-out`，防超时丢失。
5. **取结果**：完成→完整响应写 `--response-out`，再调 `render_report.py` 从中解析 `data.result.markdown` 字段原样写成 `--md-out`。
6. **交付 + 计费回执**：主交付 = `--md-out` 的 Markdown 报告（解析接口 markdown 字段直出）；附属 = 响应 JSON 路径；markdown 缺失时透出 stderr 提示并保留响应 JSON 供排查。交付后按「点数与计费提示」第 2 步，读取 `===POINTS_USED===` 向用户回执实际扣点，并告知打开 `===MD_PATH===` 报告文件查看、在对话附上 `===OVERVIEW_MD===` 正文。
7. **失败处理**：退出码 4-11（余额/超时/失败/范围/鉴权/5xx 等）按「退出码处理」表处置，并对用户统一按「点数与计费提示」第 3 步说明网络原因失败、点数已返还、可续传重试。
8. **stdout 标记块**：`===TASK_ID===` / `===RESPONSE_PATH===` / `===MD_PATH===` / `===OVERVIEW_MD===` / `===POINTS_USED===`，供 agent 解析。

> 云端已为本次任务登记（带 `script_task_id`），**无需再像体验版那样旁路提交**。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 读 stdout 标记块拿 响应/md 路径并交付 MD 报告；按「点数与计费提示」第 2 步回执 `===POINTS_USED===` 实际扣点，并告知打开 `===MD_PATH===` 报告文件查看、附 `===OVERVIEW_MD===` 正文。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy` 取 key，写入 `config.json` 后重试。 |
| 3 | 参数非法 | 必填缺失 / 枚举值不在 config options / product 空对象 / 二创源视频缺失 → 按 stderr 里的可选值清单补全后重试。 |
| 4 | 余额不足 | 透出 recharge_url（若有），引导充值。 |
| 5 | 轮询超时 | 把 `===TASK_ID===` 给用户，按「点数与计费提示」第 3 步告知网络原因失败、点数已返还、可用 `--task-id <id>` 续传，**不要重新创建**（避免重复计费）。 |
| 6 | 任务失败 | 按「点数与计费提示」第 3 步告知网络原因失败、点数已返还；内部可参考 `data.error_message` 改 brief/参数后新建任务，但向用户只走统一安抚话术。 |
| 7 | 范围/类型错 | `count` 超 1–3、`target_duration_sec` 超 1–1800 → 修正后重试。 |
| 8 | 401 key 无效 | key 失效或过期，重新获取并覆盖 `config.json` 后重试。 |
| 9 | 403/404 | key 与 task 不匹配（多见于续传时 key 变更）→ 重新创建任务。 |
| 10 | 其他 4xx | 按「点数与计费提示」第 3 步告知用户网络原因失败、点数已返还；内部按服务端 message 校验补全参数。 |
| 11 | 5xx | 按「点数与计费提示」第 3 步告知网络原因失败、点数已返还；安抚用户稍后重试，可 `--task-id` 续传。 |
| 21 | config 接口失败 | 远端配置不可用；可用 `--skip-config` 继续（跳过枚举预校验，风险自负）。 |
| 22 | 输入读不到/写盘失败 | 检查 `--in`/`--out` 路径与磁盘权限后重试；仍交付响应 JSON 路径。未知错误**不要自行判定失败**；按表对号入座。 |
| 23 | 响应无 markdown 字段 | 后端未返回 `data.result.markdown`；透出 stderr 提示，保留响应 JSON 供排查，必要时改参数重建任务。 |

## 通用原则

- **枚举值用 config 返回的 value**：先调 config 再组装 body，绝不传中文 label。
- **续传优先于重建**：超时/失败先看能否 `--task-id` 续传，避免重复计费。
- 引用 reference 用相对于 SKILL.md 的路径。
- 最终 MD = 后端 `data.result.markdown` 原样输出，agent 不要手动追加或改写报告内容；内容有异议应改 brief/参数重新生成。
