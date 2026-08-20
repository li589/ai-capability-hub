# 技能进化旁路 · 录入（Intake）

执行前须先 **`Read`** `prompts/evolution/guardrails.md`。

## 何时进入

用户显式提到例如：技能进化、政策雷达、审查政策更新、自进化、进化旁路、`/patent-evolve`、`/技能进化`。  
**禁止**因「写交底 / 读专利」自动进入本模式。

## 可选确认（信息不足时问 1–2 个）

```
1) 关注范围：审查工具(AI辅助) / 申请客体(AI·算法规则) / 全部（默认）？
2) 时间窗：近 12 个月（默认） / 近 6 个月 / 自定义起止？
```

可跳过；跳过则默认：**全部范围 + 近 12 个月**，以中国国知局为主。

## 输出约定

- 目录：`outputs/evolution/`（已被 gitignore；勿改到仓内 prompts）
- 文件：`EVOL-YYYYMMDD-HHMM.md`（本地时区；分钟两位）
- 可选：同 stem 的 `.status.md` 仅在用户勾选后写入采纳状态

## 下一步

1. **`Read`** `prompts/evolution/research.md` → 检索与抓取  
2. **`Read`** `prompts/evolution/emit_backlog.md` → 写清单  
3. 展示人审闸门文案（见 guardrails）；**等待确认**  
4. 仅当用户确认采纳后 → **`Read`** `apply_after_confirm.md`
