# 无效检索 Goal Loop

## 目录

1. 适用范围与优先级
2. 初始化与持久化状态
3. 一次循环如何运行
4. 前沿、动作和证据增益
5. 续跑、暂停与中止
6. 控制器命令

## 1. 适用范围与优先级

本流程仅用于无效证据检索。目标是持续发现并核验最佳证据候选，而非在固定 Bool 次数或固定轮数后收尾。

无效检索以本文件和 `invalidity_search_workflow.md` 为准，优先于通用“8–10 次 Bool、2–3 轮、每轮等待用户校准”的查新规则。开始前仍须确认目标专利、权利要求、关键日、CN/world 范围和费用授权；费用检查点只暂停并保存状态，不构成检索完成。

不得把“找到候选”写成专利必然无效。Goal 的完成对象是可复核的证据池和检索饱和记录，不是法律结论。

## 2. 初始化与持久化状态

每件案例建立独立目录，并先运行 `scripts/invalidity_goal.py init`。控制器写入：

```text
<case>/
  goal_state.json           # 唯一当前状态
  goal_events.jsonl         # 不可逆事件日志
  rounds/R001/checkpoint.json
  actions/                  # 入队前的动作 JSON
  results/                  # 每个动作的结果 JSON
  raw/                      # 每次 API 原始响应
  pid_lists/                # Bool Top 50、语义全量 PID
  details/                  # 详情核验响应
```

`goal_state.json` 至少保存：目标、关键日、特征、特征覆盖矩阵（`feature_coverage`）、必经检索通道、动作前沿、候选 PID 来源、已完成循环数、两级零增益计数（`zero_gain_cycles` / `zero_decisive_cycles`）、积分消耗和状态。不得把金标、决定书、证据编号或答案 PID 写入该状态。

状态值：

- `active`：可继续认领动作；
- `paused`：用户或费用检查点暂停，可恢复；
- `complete`：仅在证据已准备或饱和门通过后封存；
- `blocked`：Key/权限/必要输入缺失等外部阻塞，记录原因后等待用户。

## 3. 一次循环如何运行

一次循环不是“又跑一轮相同检索”，而是一次可证伪的检索假设闭环：

1. 读取状态、未覆盖特征和未处理高优先级动作；
2. 从不同通道认领 1–3 个最高价值动作；语义请求仍必须串行、间隔至少 60 秒；
3. 执行 Bool、语义、详情、IPC、world、家族或引证动作，立即保存原始响应和 PID；
4. 做日期、自匹配、同族和可核验性过滤；对 Bool 保存 Top 50，对语义保存全量 PID；
5. 对高覆盖候选做详情核验，更新特征矩阵、Y-Base 残余矩阵及候选来源；
6. 记录本次增益，产生后续动作，写入 checkpoint；
7. 未满足饱和门时自动继续，不等待逐轮人工确认。

高优先级动作优先级如下：未核验的高覆盖候选 > 可形成 X/Y-Base 的路径 > 已确认 Y-Base 的残余特征 > 保留语义锚点的 Bool 扩展 > world/IPC/家族/引证桥接 > 普通术语扩展。

每个动作必须写清：`lane`、`action_type`、假设、父线索、查询、预期证据增益、优先级和是否为必经通道。控制器会拒绝精确重复的待执行或已执行动作。

## 4. 前沿、动作和证据增益

可用 `lane`：

| lane | 作用 |
|---|---|
| `qx` | 单篇高覆盖/X 候选 |
| `qy_base` | 最接近现有技术 |
| `qy_comp` | 已核验 Y-Base 的真实残余特征 |
| `semantic` | 直接候选和可复验 pivot |
| `world` | 英文、多语言、IPC/CPC 与 PID 前缀覆盖 |
| `family_citation` | 同族、引证、申请人、发明人线索 |
| `detail` | 日期、原文、特征、组合动机核验 |
| `source_gap` | 非专利来源缺口记录 |

每个结果写入以下收益，而非只写命中数：

- `new_candidates`：新的日期适格 PID；
- `new_high_coverage`：触发详情核验的高覆盖 PID；
- `new_decisive_evidence`：已有原文位置支撑的关键 PID；
- `new_pivots`、`new_ipcs`、`new_family_citation`：可生成不同路径的线索；
- `feature_coverage_delta`：人工填写的特征覆盖增量，**必须是数值（float，建议 0~1）**，不是对象/字典。填对象会让 `record` 抛 `TypeError: float() argument must be...`。经验刻度：零增益 `0`；补充性覆盖 `0.05~0.1`；跨领域功能等同证据 `0.1~0.15`；某特征首次被直接披露 `0.25~0.3`；
- `covered_features`：**结构化覆盖**——本动作经详情核验确证新覆盖的特征 ID 列表（如 `["F6"]`）。`checkpoint` 会据此计算 `real_coverage_delta`（新覆盖特征数 / 总特征数）并写入 `state.feature_coverage[F].covered_by`，饱和门第 4 条件由它强制；
- `feature_gaps`：本动作确证"该特征经检索仍无在先技术披露"的缺口记录，格式 `[{"feature_id":"F7","reason":"..."}]`。写入后 `state.feature_coverage[F].gap_recorded = true`，满足饱和门"已记录独立检索缺口"；
- `credits_charged` / `credits_remaining`：从 API 回包取的积分消耗与余额（可选），`record` 累加进 `state.cost`，`status`/`checkpoint` 报累计消耗。

新线索必须生成后续动作；没有新线索的动作也必须记录其失败原因，避免下一轮重复。Y-Comp 只能在完成 Y-Base 详情和残余矩阵后入队。语义直接候选可直接进入 `detail`，不必先被 Bool 复现；语义 pivot 回写 Bool 时，Top 50 必须保留至少一个高覆盖锚点，否则该动作无效并回退。

动作 JSON 可选填 `features`（特征 ID 列表），标注该动作攻击的特征；`suggest-diversity` 子命令据此判断哪些特征已尝试过哪些 Bool 通道。`record` 检测到封顶（`truncated=true` 或 `total>=10000`）时，会在输出中附带 `narrowing_suggestions`（收窄建议骨架），由 agent 决定是否入队，不自动扩张前沿。

## 5. 续跑、暂停与中止

出现 API 401/402/403 时立即 `pause`，保留全部已完成动作并等待用户，不得替换为其他检索引擎。429、超时或取消只标记该动作失败；以不同入口或更窄表达重试，并保留已接收结果。

每完成一组动作运行 `checkpoint`。它会计算本循环新增候选、决定性证据、pivot、分类、家族/引证和特征覆盖，并维护**两级零增益计数**：

- `zero_gain_cycles`：任一正增益（含新候选、pivot 等）即归零——宽松口径，防止噪声无限续命但仍记录；
- `zero_decisive_cycles`：仅 `new_high_coverage` / `new_decisive_evidence` / `real_coverage_delta > 0` 才归零——严格口径，是饱和门的真正判据。

只有同时满足以下条件，才可用 `complete --reason saturated`：

1. QX、QY-Base、world、语义 A 和详情等必经通道均已执行；
2. 所有高优先级候选和前沿已处理，或明确记录不处理原因；
3. 连续至少 3 个完整 checkpoint 没有新的决定性证据/高覆盖候选/真实特征覆盖增益（`zero_decisive_cycles >= 3`）；
4. **每个必要特征都有已核验证据（`feature_coverage[F].covered_by` 非空）或已记录独立检索缺口（`feature_coverage[F].gap_recorded = true`）**——即 `all_features_covered_or_gapped`，饱和门第 4 条件由代码强制，不靠人工记忆；
5. 非专利来源缺口已标记。

若新候选、pivot、分类或家族线索出现，必须重新打开相关通道并将零增益计数归零。`evidence_ready` 表示已形成经详情核验的强候选路线，但仍不能替代法律结论。

**`evidence_ready` 完成前置校验**：运行 `complete --reason evidence_ready` 时，控制器先打印一份 `completion_audit`（必经通道是否全执行、特征是否全部 covered_or_gapped、decisive/high 候选数、门当前 recommendation）。若门的 recommendation 不是 `saturation_review`（即 agent 在覆盖门的判断），**必须附带 `--note` 说明覆盖理由**，否则拒绝执行；事件日志记 `override_gate=true` 留审计痕。不硬阻——保留人工裁量，但审计不可绕过。

**饱和门与多样性续作的解耦**：当 `zero_decisive_cycles >= 3` 但仍有特征未覆盖（`all_features_covered_or_gapped = false`）时，recommendation 走 `plan_new_diverse_actions` 而非 `saturation_review`——即"还有特征没证据，必须继续找"。这保护了多样性续作机制不被过早饱和。

## 6. 控制器命令

```bash
# 1. 初始化：features.json 为权利要求特征数组
python3 <skill-dir>/scripts/invalidity_goal.py init <case-dir> \
  --case-id INVDEV-XX --target-patent <目标号> --critical-date YYYYMMDD \
  --features <case-dir>/features.json

# 2. 将 JSON 动作加入前沿；再认领最高优先级动作
python3 <skill-dir>/scripts/invalidity_goal.py enqueue <case-dir> action.json
python3 <skill-dir>/scripts/invalidity_goal.py next <case-dir> --limit 3 --claim

# 3. API 调用结束后，写入结果和自动生成的 followups
python3 <skill-dir>/scripts/invalidity_goal.py record <case-dir> A0001 result.json
python3 <skill-dir>/scripts/invalidity_goal.py checkpoint <case-dir> --note "本轮诊断"

# 4. 查看、暂停、恢复和封存
python3 <skill-dir>/scripts/invalidity_goal.py status <case-dir>
python3 <skill-dir>/scripts/invalidity_goal.py pause <case-dir> --note "等待费用授权"
python3 <skill-dir>/scripts/invalidity_goal.py resume <case-dir>
python3 <skill-dir>/scripts/invalidity_goal.py complete <case-dir> --reason saturated

# 5. 多样性建议：对未覆盖特征（经 ≥2 个 Bool 通道仍零决定性证据）建议语义 B/C 骨架
python3 <skill-dir>/scripts/invalidity_goal.py suggest-diversity <case-dir> [--threshold 2]

# 6. 导出 evidence.json 骨架：从 goal_state 自动生成 searches/details/gate stub，
#    gate.status / limitations / conclusion 需人工填写，再交 report_guard 校验
python3 <skill-dir>/scripts/invalidity_goal.py export <case-dir> [--output <path>]
```

`result.json` 只引用已保存的原始响应和 PID 文件；它不得含答案信息。运行 `self-test` 验证控制器本身：

```bash
python3 <skill-dir>/scripts/invalidity_goal.py self-test
```
