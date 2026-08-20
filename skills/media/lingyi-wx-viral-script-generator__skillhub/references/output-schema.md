# 输出 Schema 契约（单一事实源）

agent 生成的 JSON 必须逐字段符合本契约；[scripts/render_script.py](../scripts/render_script.py) 据此校验。失败即退出码 2 + 中文报错。

## 顶层结构

```json
{
  "title": "脚本标题，≤15 字、无标点",
  "duration_sec": 138,
  "info": {
    "purpose": "带货",
    "industry": "厨房清洁",
    "audience": "家庭主妇",
    "topic": "农残清洗",
    "product": "洁娘子食用小苏打"
  },
  "campaign_types": ["short_video_seeding", "influencer_collaboration"],
  "script_type": "pain_point",
  "structure": {
    "hook": { },
    "body": { "segments": [ ] },
    "cta": { },
    "rhythm": { },
    "structure_summary": "痛点引入→痛点放大→给出解法→价值共鸣与转化引导",
    "rhythm_evidence": "信息切换频率30-45s，固定机位单人镜头",
    "product_conversion": null,
    "tags": ["生活好物", "科普/痛点型", "视频号", "食用小苏打", "厨房清洁", "健康生活"]
  }
}
```

## 字段细则

### 顶层

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `title` | str | 是 | 非空，≤15 字，不含标点 |
| `duration_sec` | int | 是 | >0；视频号建议 60–180 |
| `info` | obj | 是 | 见下 |
| `campaign_types` | list[str] | 是 | 非空，每项取下方枚举 |
| `script_type` | str | 是 | 取下方枚举 |
| `structure` | obj | 是 | 见下 |

### info

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `purpose` | str | 是 | 创作目的 |
| `industry` | str | 是 | 行业 |
| `audience` | str | 是 | 受众 |
| `topic` | str | 是 | 选题 |
| `product` | str | 否 | 产品名 + 卖点；缺失时省略此键，`product_conversion` 给 null |

### structure.hook

```json
"hook": {
  "index": 1,
  "section": "Hook段",
  "time_range": "0-43s",
  "start_time": "0",
  "end_time": "43",
  "function": "抓注意力",
  "type": "痛点提问",
  "visual": "画面描述（出镜、镜头、动作、字幕等可见画面）",
  "dialogue": "口播台词全文",
  "note": "设计意图"
}
```

- `index` 固定 **1**；`section` 固定 **"Hook段"**；`function` 固定 **"抓注意力"**。
- `start_time`/`end_time` 为整数字符串；`start_time` 必须为 `"0"`；`time_range` 形如 `"0-43s"`。
- `type`：钩子方式枚举见 [viral-patterns.md](viral-patterns.md)（利益/冲突/痛点提问/悬念/反差/共鸣/数据/反常识/场景建立/身份锚定）。
- `visual`（画面）与 `dialogue`（台词）**必须分别给出、不得合并**；`note` 非空（无内容填 `"-"`）。无口播段（如纯画面）`dialogue` 填 `"-"`。

### structure.body.segments

```json
"body": {
  "segments": [
    {
      "index": 2,
      "section": "中段段落1",
      "time_range": "43-90s",
      "start_time": "43",
      "end_time": "90",
      "function": "痛点放大",
      "type": "—",
      "visual": "画面描述",
      "dialogue": "口播台词全文",
      "info_density": "high",
      "visual_switch": "固定机位单人镜头",
      "note": "设计意图"
    }
  ]
}
```

- `segments` 至少 1 条；`index` 从 **2** 起升序连续（2,3,4…）。
- 段数上限：**教程/制作型 ≤7，其余 ≤5**。
- `section` 填实际段落功能名（如「产品出场」「效果展示」），**不要写「中段1/中段2」占位符**。
- `function`：该段功能归类（痛点放大/产品出场/效果展示/场景展开/制作过程…）。
- `type`：中段统一填 `"—"`（除非本身具备钩子性质）。
- `info_density` 枚举：`high` / `medium` / `low`。
- `visual_switch`：镜头/场景切换描述（如「固定机位单人镜头」「单人→手持产品展示」）。
- `visual`、`dialogue` 非空（无口播段 `dialogue` 填 `"-"`）；`note` 非空（无内容填 `"-"`）。

### structure.cta

```json
"cta": {
  "index": 99,
  "section": "CTA段",
  "time_range": "120-138s",
  "start_time": "120",
  "end_time": "138",
  "function": "转化引导",
  "type": "购买",
  "visual": "画面描述",
  "dialogue": "口播台词全文",
  "note": "自然度评价"
}
```

- `index` 固定 **99**；`section` 固定 **"CTA段"**；`function` 固定 **"转化引导"**。
- `type` 枚举：收藏/关注/购买/点击购物车/评论互动/转发/点赞。
- `visual`、`dialogue` 非空（无口播段 `dialogue` 填 `"-"`）；`end_time` 必须等于 `duration_sec`。

### structure.rhythm

```json
"rhythm": {
  "info_switch_interval": "30-45s",
  "emotion_curve": "担忧→惊恐质疑→找到解法→安心信赖",
  "energy_level": "medium"
}
```

- `info_switch_interval`：信息切换间隔区间（如 `"5-8s"`、`"30-45s"`）。
- `emotion_curve`：情绪走向，用 `→` 串联。
- `energy_level` 枚举：`low` / `medium` / `high`。

### structure 其余字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `structure_summary` | str | 是 | 按时序串联各段功能的一句话脉络 |
| `rhythm_evidence` | str | 是 | 节奏证据（切换频率/镜头方式） |
| `product_conversion` | obj\|null | 是 | 有产品给对象（SKU/价格/卖点/促销），无产品给 `null` |
| `tags` | list[str] | 是 | 非空，含行业、脚本类型、平台、品类关键词 |

## 枚举总表

- `campaign_types`（渲染时显示中文）：`short_video_seeding`(短视频种草)、`influencer_collaboration`(达人合作)、`live_stream_clip`(直播切片)、`brand_exposure`(品牌曝光)、`fan_growth`(涨粉)、`content_seeding`(内容种草)、`product_review`(产品测评)
- `script_type`：`pain_point`、`scene`、`drama`、`testimonial`、`unboxing`、`tutorial`
- `info_density`：`high`、`medium`、`low`
- `energy_level`：`low`、`medium`、`high`
- `cta.type`：`收藏`、`关注`、`购买`、`点击购物车`、`评论互动`、`转发`、`点赞`

## 时间轴自洽规则（脚本会校验）

1. `hook.start_time == 0`
2. `hook.end_time == segments[0].start_time`
3. `segments[i].end_time == segments[i+1].start_time`（i 从 0 起）
4. `segments[-1].end_time == cta.start_time`
5. `cta.end_time == duration_sec`

任一不满足 → 退出码 2，报错指明断点位置。
