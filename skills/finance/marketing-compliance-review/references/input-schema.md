# 审查意见书 JSON 输入格式

`scripts/generate_review.js` 读取一个 JSON 文件，渲染为正式 .docx 审查意见书。
用法：`node generate_review.js <input.json> [output.docx]`

## 完整字段

```jsonc
{
  "meta": {                         // 封面基础信息
    "mode": "draft",               // draft（默认）/ archive（正式归档）
    "material": "送审材料名称",      // 必填，也用于推导默认输出文件名
    "type": "银行代销产品宣传海报",   // 送审类型
    "product": "关联产品名",
    "department": "送审部门",
    "submitter": "送审人",
    "date": "2026-07-28",         // 审查时间
    "conclusion": "❌ 不通过",       // ✅ 通过 / ⚠️ 有条件通过 / ❌ 不通过
    "riskLevel": "🔴 高风险",       // 🔴 高风险 / 🟡 中风险 / 🟢 低风险
    "docNo": "XIAOBAO-2026-0001",   // 意见书编号；草稿可缺省，归档必填
    "source": "图片OCR(腾讯云)"       // 可选：素材来源类型。取值："文字转录" / "图片OCR(腾讯云)" / "图片AI视觉" / "文档读取"。用于审查溯源。
  },
  "summary": {                      // 一、审查摘要
    "intro": "本次审查的…，存在 N 项合规问题，其中：",
    "high": "5 项（涉及…）",       // 🔴 高风险项描述
    "mid": "3 项（涉及…）",        // 🟡 中风险项描述
    "low": "无",                    // 🟢 低风险项描述
    "core": "核心问题为…"            // 核心风险一句话
  },
  "problems": [                    // 二、审查发现（每个问题一段）
    {
      "no": 1,
      "title": "标题“富利成长”暗示收益",
      "risk": "🔴 高风险",          // 决定该段标题/单元格配色
      "dimension": "合法合规",
      "excerpt": "「原文摘录段落」",
      "rule": "禁用词库 - 收益承诺类",
      "basis": [                      // 审查依据（法条），可多条
        "《银行保险机构消保管理办法》第 25 条：…",
        "《广告法》第 28 条：…"
      ],
      "suggestion": "具体可执行的修改方案"
    }
  ],
  "evaluation": [                 // 三、总体评估（维度评分表）
    { "dim": "合法合规", "score": "1/5", "note": "…" },
    { "dim": "真实准确", "score": "2/5", "note": "…" }
    // 维度：合法合规 / 真实准确 / 风险提示 / 信息完整 / 公平诚信 / 个人信息保护
  ],
  "evaluationSummary": "综合意见：…",   // 总体评估下方综合判断
  "remediation": [                // 四、整改要求
    { "no": 1, "item": "删除“富利成长”标题", "level": "🔴 高风险", "deadline": "即时", "owner": "（待分配）" }
    // level 取值：🔴 高风险 / 🟡 中风险 / 🟢 低风险
  ],
  "approvals": [                  // 五、审批记录（缺省自动给三栏模板）
    { "role": "审查人", "name": "AI 消保审查助手", "opinion": "见本意见书审查发现", "date": "2026-07-28" },
    { "role": "复核人", "name": "（待填）", "opinion": "（待填）", "date": "（待填）" },
    { "role": "审批人", "name": "（待填）", "opinion": "（待填）", "date": "（待填）" }
  ]
}
```

## 取值约定

- **risk / level**：必须为 `🔴 高风险` / `🟡 中风险` / `🟢 低风险`（脚本据此自动配色：红 CC0000 / 黄 E6A817 / 绿 2E7D32）。
- **mode**：`draft` 为审阅草稿，允许编号、送审人等信息暂缺；`archive` 为正式归档，脚本会强制校验 `docNo`、`date`、`department`、`submitter`、`conclusion`、`riskLevel`。
- **必填规则**：`meta.material` 必填；`problems` 必须为非空数组，且每项必须填写问题编号、标题、风险等级、审查维度、原文摘录、命中规则、审查依据和修改建议。
- **可选字段缺省**：`summary` 整段缺省则跳过；`approvals` 缺省自动生成"审查人 / 复核人 / 审批人"三栏。
- **conclusion 配色**：含"不通过"或 ❌ 自动标红，其余标黑。

## 最简可用输入

草稿模式只需填写 `meta.mode`、`meta.material` 和完整的 `problems` 即可生成；正式归档必须补齐上述归档字段。

机器可读的完整约束见 `references/input-schema.json`。
