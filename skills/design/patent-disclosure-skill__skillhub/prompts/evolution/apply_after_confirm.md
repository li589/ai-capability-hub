# 技能进化旁路 · 确认后应用

**仅当**用户已明确回复「全部采纳」或「采纳 E…」后执行。  
执行前再 Read `guardrails.md`。

## 步骤

1. 打开对应 `outputs/evolution/EVOL-*.md`，只处理状态为采纳的 E* 行。  
2. 将建议落实为对 `prompts/**`、`references/**`、必要时 `SKILL.md` 的 **最小 diff**（勿借机大重构）。  
3. 在同目录写 `EVOL-YYYYMMDD-HHMM.status.md`：

```markdown
# EVOL-… 采纳状态
- 确认时间：…
- 用户指令：…
- 已采纳：E…
- 已搁置：E…
- 已改文件：
  - path — 一句话
- 未改原因（若有）：…
```

4. 若用户要求「沉淀到 docs/evolution/」：将清单 **复制** 到 `docs/evolution/EVOL-….md`（可提交）；**不要**把整个 `outputs/` 取消 ignore。  
5. 向用户汇报改了哪些文件；提醒：法规解读≠法律意见，重要案件仍须代理人复核。

## 禁止

- 扩大采纳范围到用户未点名的 E*  
- 根据 C 级信源改技能  
- 写入欺瞒审查或对抗审查系统的话术
