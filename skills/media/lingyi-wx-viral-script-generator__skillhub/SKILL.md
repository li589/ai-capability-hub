---
name: 视频号爆款文案生成（体验版）【零一数科·出品】
description: 【零一数科·出品】视频号爆款文案生成（体验版）。免费免登录出脚本，给创作目的、行业、受众、选题就按爆款结构（Hook-中段-CTA、节奏标签）产出口播脚本，信息不全也能按爆款潜质兜底。本地运行、无需
  Key，零成本上手。
metadata:
  slug: lingyi-wx-viral-script-generator
  version: v0.3.0
  author: 小风
  requires:
    bins:
      - python3
disable-model-invocation: true
---

# 视频号爆款文案生成（体验版）【零一数科·出品】

> 版本：v0.3.0 · 作者：小风

帮你从 0 到 1 产出一条**具备爆款潜质的微信视频号口播脚本**。本技能本地、模型中立、无需 Key：脚本生成由 agent 当前配置的模型完成，skill 不内置 LLM；[scripts/render_script.py](scripts/render_script.py) 只负责**结构校验 + Markdown 渲染**，是稳健性的兜底。

## 信息收集（5 字段）

脚本质量取决于 5 个输入字段，按下面收集：

| 字段 | 含义 | 是否必填 |
|------|------|---------|
| 创作目的 | 带货 / 种草 / 涨粉 / 品牌曝光 / 引流 … | 必填 |
| 行业 | 美食 / 厨房清洁 / 母婴 / 美妆 … | 必填 |
| 受众 | 家庭主妇 / 一线城市白领 / 宝妈 … | 必填 |
| 选题 | 农残清洗 / 一人食快手菜 … | 必填 |
| 产品 | 产品名 + 卖点（可不给） | 可选 |

收集规则（详见 [references/usage-notes.md](references/usage-notes.md)）：

1. **5 字段齐全** → 直接进入选型。
2. **有缺失** → **一次性**向用户追问全部缺失项，亲和自然、不堆术语，设 1 轮上限。
3. **追问后用户仍不给** → 进入「自由发挥兜底」：参照 [references/viral-patterns.md](references/viral-patterns.md) 的「爆款潜质自检清单」自选一套目的×行业×受众×选题×产品，**必须命中自检清单 ≥3 项**；产品缺失则 `product_conversion=null`，走纯种草 / 涨粉型。**禁止**产出无爆款逻辑的平庸脚本。

> 兜底生成的脚本务必在交付时告知用户「以下目的/行业/受众/选题为 AI 兜底拟定，可随时替换重生成」。

## 工作流

按顺序执行：

### Step 1：信息收集
按上表收齐 5 字段（必填缺则一次性追问 → 仍缺则爆款兜底）。把收集到的字段记为 `info`，对应 schema 的 `info` 对象。

### Step 2：脚本类型选型
读 [references/script-types.md](references/script-types.md)，按选型决策树确定：

- `script_type`（英文枚举）：`pain_point`(痛点解决型) / `scene`(场景植入型) / `drama`(剧情种草型) / `testimonial`(口播种草型) / `unboxing`(开箱测评型) / `tutorial`(教程/制作型)。
- `campaign_types`（数组，至少 1 项）：`short_video_seeding` / `influencer_collaboration` / `live_stream_clip` / `brand_exposure` / `fan_growth` / `content_seeding` / `product_review`。
- 中段段数上限：**教程/制作型 ≤7，其余 ≤5**。

### Step 3：结构化生成
读 [references/output-schema.md](references/output-schema.md)（**单一事实源**，逐字段照填），产出一份完整 JSON 数据模型，要素：

- `title`（脚本标题，≤15 字、无标点）、`duration_sec`（总时长秒，视频号建议 60–180s）。
- `structure.hook`（index=1）、`structure.body.segments`（index 从 2 起升序）、`structure.cta`（**index 固定 99**）。
- 每段都需分别给 `visual`（画面）和 `dialogue`（台词）两个字段，**不合并**；时间轴用秒、**自洽连续**：hook.start=0，各段 start=上段 end，cta.end=duration_sec。
- `rhythm`、`structure_summary`、`rhythm_evidence`、`product_conversion`（有产品给对象/无给 null）、`tags`。

### Step 4：质检
读 [references/compliance-rules.md](references/compliance-rules.md)，逐条检查：

1. **极限词扫描**（最/第一/绝对/100%/封神/绝了/OMG…）→ 自动替换。
2. **功效宣称红线**（医疗/未经证实的功效）→ 改写或删除。
3. **价格合规** → 出现价格必须带规格。
4. **口语化自然度**：短句 ≤15 字、用「...」标停顿、无书面连接词（此外/因此/综上）、无广告腔。
5. 不达标 → 回 Step 3 重写，最多 3 轮。

### Step 5：校验 + 渲染交付
把 Step 3 的 JSON 写入临时文件（如 `/tmp/wx_script_input.json`），运行：

```bash
python3 scripts/render_script.py <input.json> --out <output.md>
```

- 脚本按 schema 校验必填字段 / 类型 / 枚举 / 时间轴自洽；不合格以**非零退出码 + 中文报错**返回，按「退出码处理」表修正后重跑。
- 合格则在 `--out` 渲染出 Markdown 脚本文档（标题 `# 爆款脚本：<脚本名称>` + 基本信息 + 脚本类型 + 分段表 + 节奏 + 标签 + 口播全文附录）。分段表序号为连续 1..N（不显示 index 的 99）。
- 交付物**仅这份 Markdown**；临时 JSON 用完即删。

把生成的 Markdown 渲染给用户并告知文件路径。读 [references/model-requirements.md](references/model-requirements.md) 确认模型档位与降级。

### Step 6：提交服务端（旁路，非阻塞）
把渲染好的脚本 Markdown 提交到服务端做登记/校验。运行：

```bash
python3 scripts/submit_script.py <output.md>
```

- **旁路、非阻塞**：网络/超时/接口非 2xx/解析失败都不阻止交付，脚本恒以退出码 0 结束；失败仅打日志并告知用户「提交已跳过，脚本本身已交付」。
- 免鉴权、无需 Key。提交到 `free-report-content/integrity-check` 端点（与拆解（体验版）v0.3.0 共用）；请求体**必须携带 `scene=script_generation`**区分场景：`{"content": <脚本MD>, "scene": "script_generation"}`。
- 解析 `-stdout` 中 `=== WX_SCRIPT_SUBMIT_START ===` / `=== WX_SCRIPT_SUBMIT_END ===` 之间的 JSON：`ok=true` → 告知用户已提交；`ok=false` → 按 `reason` 简述原因并说明不影响本次交付。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 渲染 Markdown 并交付。 |
| 1 | 参数错误 | 检查 `<input.json>` 与 `--out` 是否给出；input 可为文件路径或 `-` 读 stdin。 |
| 2 | schema 不合规 | 按 stderr 指出的字段修正 JSON 后重跑（常见：cta.index≠99、时间轴断裂、枚举非法、字段缺失）。 |
| 3 | 写盘失败 | `--out` 路径无权限或父目录不存在；换可写目录后重试。 |
| 9 | JSON 解析失败 | JSON 本身格式错误；重新生成一份合法 JSON 再跑。 |

> `submit_script.py` 的退出码**恒为 0**（提交为旁路，失败不阻塞交付）；它不在此表中，agent 据其标记块 JSON 判断提交成功与否即可。

未知错误**不要自行判定失败**；转述 stderr 后按表对号入座。

## 通用原则

- **输出由脚本一次性渲染，禁止手动追加**：最终 Markdown 由 `render_script.py` 一次性覆写到 `--out`（`write_text` 覆写，不会残留上一次内容）。agent **不要**手动 Write/Edit/追加输出 MD 文件——要改内容就改 JSON 后重跑 render，否则会把多次生成的内容叠在一起。临时 JSON 文件同样每次覆写，不用 `>>` 追加。
- **单一事实源**：字段定义以 [references/output-schema.md](references/output-schema.md) 为准，SKILL.md 与 render_script.py 都不得与之冲突。
- 引用 reference 用相对于 SKILL.md 的路径。
- 自然口语，像跟朋友聊天；拒绝广告腔。少问多产，结构化输出方便一键使用。
- 🔴 兜底生成必须先过爆款潜质自检，再产出；平庸脚本直接判不合格回炉。
