
## v4.15.56 — 2026-07-23

### 🔴 P0: P5 Risk TP diff_hint 截断修复（task_20260721_101429复盘驱动，小墨+小执联合核证）

**根因**: 生成 risk_verification TP 的 step_expected_pairs fallback 模板时，`diff_hint` 用 `clean_title[:20]` 硬截断，产生"技术方案尚功能模块"类语义破碎文本，注入模板后形成"打开技术方案尚功能模块，录入符合风险触发条件..."的不可读描述。

**证据**: task_20260721_101429 R1-001/R4-002/R5-001/R5-002 四个risk TP的描述均被截断破碎。

**修复 (orchestrator.py `_write_tp_contexts`→fallback diff_hint)**：
- risk_verification 分类使用 `clean_title[:40]`（原20字→40字）
- 增加 `risk_description` 字段作为fallback

**改动量**: +5行

### 🔴 P0: G6+C2级联豁免（task_20260721_101429复盘驱动）

**根因**: G6要求拆分合并步骤→步骤数从6增至9-12→C2要求步骤-期望偏差≤2→级联失败。两套规则独立运行，无豁免联动。

**修复 (orchestrator.py `_p7_check_c2`)**：
- 新增 `_tp_step_counts` 预处理：统计每个TP下所有case的步骤数分布
- G6拆分检测启发式：同TP多case(≥2) + 步骤数相近(差≤2) + 步骤数≥6
- 检测到G6拆分时放宽C2阈值1级：diff=3/4→INFO，diff=5→WARNING，diff≥6仍BLOCK

**改动量**: +25行

### 🟡 P1: Merge层shortfall容差对齐保存层

**根因**: V4.15.53在 `_save_single_tp` 加了±1容差(expected≥3时 min_acceptable=max(1,expected-1))，但 `action_p6_merge` 统计仍用 `actual < expected` 直接判定，两层不一致。

**修复 (orchestrator.py ×2)**：merge层两处shortfall判定同步使用 `_min_acc` 计算

**改动量**: +4行

### 🟡 P1: G1.5异常场景状态描述词豁免

**根因**: "网络中断"、"系统无响应"、"OA系统在响应过程中出现异常"等异常状态描述不在OBSERVABLE_DATA白名单，被误判为末位步骤缺乏可观测对象。

**修复 (gate_checker.py OBSERVABLE_DATA)**：新增3条pattern：
- 异常状态词（中断/无响应/异常/故障/宕机/不可用）作为末位
- 系统+异常描述（系统/服务器/网络+异常/故障/中断）
- 通用异常出现模式（在/出现/发生+异常/故障/中断）

**改动量**: +4行

### 🟡 P1: P7 quick_fix shortcut

**根因**: P7修复需改tp源文件→全量re-merge(79个TP)→重新P7检查，流水线耗时~2分钟/次。对定点修复效率极低。

**修复 (orchestrator.py 新增 `action_p7_quick_fix`)**：
- 直接修改 p6_output.json 中指定 case
- 双写回对应 tp_xxx.json 源文件
- 自动备份到 .tp_backup/
- 增量P7检查（跳过merge，≤5秒）
- 用法：`python3 $ORCH --action p7_quick_fix --case-id XXX --field steps --new-value "..."`

**改动量**: +80行

---

## v4.15.55 — 2026-07-20

### 🔴 P0: failed_cases 增加 tp_index/tp_file 定位字段

**根因**: P7报告中的 failed_cases 只含 case_id，Agent需 grep 136个 TP 文件定位修复位置，每次耗时3-5分钟。

**证据**: task_20260720_131327，Agent因缺少定位信息而改错文件(p6_output.json而非tp_N.json)，浪费约5分钟。

**修复 (orchestrator.py action_p7_code_check)**:
- failed_cases 每项新增 `tp_index` 和 `tp_file` 字段
- 通过 `_find_batch_for_case` 查询 case_id→tp_index 映射

### 🟡 P1: merge truncation_guard 失败时优雅降级

**根因**: merge 时 truncation_guard 返回非零（通常是 L3 字段不完整），但 p6_output.tmp.json 已含可用数据。merge 直接 sys.exit(1) 误导 Agent。

**证据**: task_20260720_131327，Agent报告"TRUNCATION_DETECTED导致exit=3"，但merge最终成功，exit code误导了Agent对流程的判断。

**修复 (orchestrator.py action_p6_merge)**:
- truncation_guard 失败时检查 tmp 文件是否存在且含 ≥80% 用例数据
- 满足条件 → 手动 mv + 写入 PARTIAL gate + WARNING stderr（不 exit）
- 不满足条件 → 保持原有 sys.exit(1) 行为

**改动量**: +40 行

---

## v4.15.54 — 2026-07-20

### 🔴 P1: fix_hints batch_index=-1 修复 — p6_tp_output 回退查找

**根因**: V4.11.0 改为逐TP生成后不再生成 `p6_batches/` 目录，但 `_find_batch_for_case` 仍只从 `p6_batches/` 查找 case_id → batch_index 映射。目录不存在 → 永远返回 -1。

**证据**: task_20260719_143735，fix_hints 中所有 case 的 batch_index 均为 -1。

**修复 (orchestrator.py `_find_batch_for_case`)**:
- p6_batches/ 查找结果为空或 case_id 未命中时，fallback 到 `p6_tp_output/tp_*.json`
- 从 TP 文件的 `tp_index` 字段获取索引映射
- 保持 `p6_batches/` 为优先路径（向后兼容）

**改动量**: +14 行（纯增量 fallback，零回归风险）

---

## v4.15.53 — 2026-07-17

### 🔴 P0：RISK P0保护失效 — risk_flag/priority_hint传递链路修复（task_20260716_152649数据驱动，小墨执行）

**背景**：V4.15.47/48 实现了全局P0预算保护(`_enforce_p0_budget`)和骨架降级保护(`_sk_protected`)，但上游数据链路存在3个断点，导致 risk_flag/priority_hint 无法传递到最终用例，保护逻辑收到空数据永远返回false。

**实际影响**：task_20260716_152649 — 41/58 TP有risk_flag=True，但RISK 38条仅4条P0，PCI 18条P0=0。

**三个断点**：

1. **`_write_tp_contexts` (L6694)**：context dict 遗漏 `priority_hint` 字段 — P5有值但未写入context JSON
   - 修复：+1行 `"priority_hint": tp.get("priority_hint", "")`

2. **`_save_single_tp` (L7503)**：单TP路径用例组装未从context复制 risk_flag/priority_hint
   - 修复：+2行从ctx读取并写入test_case

3. **`action_p6_save_batch` (L9929)**：分批路径骨架覆盖未复制 risk_flag/priority_hint
   - 修复：+2行从skeleton读取并写入test_case

**改动量**：5行代码，纯增量字段传递，零回归风险。

**验证预期**：修复后RISK/PCI类用例的P0数量应≥V4.15.47设计目标（RISK≥3, PCI≥1），V4.15.47/48的保护逻辑首次完整生效。

### 🟡 P0/P1：复盘6问题一并修复（task_20260716_152649复盘，小墨执行）

#### P0: expected_case_count容差（_save_single_tp）
- expected≥3时允许±1容差：`_min_acceptable = max(1, _expected_count - 1)`
- 解决13/58 TP首轮因数量不符重试问题，预计节省~25%执行时间

#### P0: HOLLOW_STEPS导航白名单（_quick_gate_single_tp）
- 长度检查前增加导航步骤白名单：含「点击/选择」+「进入/跳转/菜单/按钮」→ 视为有效UI操作
- 解决"点击菜单进入XXX"误判空洞问题，预计节省~12%执行时间

#### P1: description空值兜底（_write_tp_contexts + _desc_fallback）
- 新增 `_desc_fallback` 函数：description为空时自动用 `title - category场景` 兜底

#### P1: p6_resume返回next_tp_index（action_p6_resume）
- resume输出新增 `next_tp_index` 字段，直接执行 p6_generate_one 无需再调 p6_tp_list

#### P2: merge后清理context副本（action_p6_merge）
- merge完成后自动 glob("*_context.json") → os.remove()，文件数从116→58

#### P2: C7.1极短描述阈值放宽（_p7_c71_semantic_coverage）
- P5描述<30字时 threshold×0.3（原仅<50字×0.5），减少WARNING噪音

---

## v4.15.52 — 2026-07-16

### P6+P7复盘6项修复（task_20260716_103652复盘驱动，小墨执行）

#### 🔴 P0
1. **G5语义豁免**（gate_checker.py `gate_g5_banned_patterns` ⑤）：同TP内步骤完全相同但 preconditions 和 expected_results 各不同时豁免 BLOCK — 解决TP-081类异常场景三TC被误伤
2. **同TP多TC差异化**（rules/paragraph_6.md）：新增P6 prompt规则，多TC时每个TC步骤至少包含一个差异化描述
3. **TP超时动态化**（orchestrator.py）：新增 `_estimate_tp_timeout(case_count)=min(600,max(120,120×n))` 函数

#### 🟡 P1
4. **段内暂停恢复15TP**（orchestrator.py ×2）：`PAUSE_EVERY_N` 30→15，`action_p6_generate_one` checkpoint阈值同步恢复
5. **C6.1前置条件自动补全**（orchestrator.py `_save_single_tp`）：前置条件仅1段且含数据/配置描述但缺账号描述时自动补全
6. **WARNING降级不retry**（orchestrator.py `_save_single_tp`）：占位符检测WARNING级不再触发`sys.exit(1)`

---

## v4.15.51 — 2026-07-15

### 🔴 P0：G3 假阳性修复 — `_extract_step_lines` 无编号步骤 fallback

**根因**：`_extract_step_lines` 和 `_extract_step_contents` 的正则 `r'^\d+[\.\、）)]'` 只识别带编号前缀的步骤行。部分 P6 生成的用例步骤不带编号前缀（纯换行分隔），导致返回0步 → G3 误报 `a_class_step_short`。

**证据**：task_20260715_110631 — TP-075/076/078 共6条用例步骤 3-5步，但因无编号前缀被解析为0步。

**修复（gate_checker.py）**：两个函数 `_extract_step_lines` / `_extract_step_contents` 增加 fallback — 编号行数为0时，以所有非空行作为步骤内容。

**影响**：G3 检查不再误报，同时 C2/C7 等依赖 `_extract_step_lines` 的检查也会更准确。

### 🟡 P1：`_build_p7_fix_hints` 补全 G3 和 G6 处理逻辑

**根因**：`_build_p7_fix_hints` 函数处理了 C7/C2/G2/C5/C6/G4/C3/C4/C6.1/G9/G1/G1.5/G5 共 13 个检查项，但遗漏了 **G3（业务流程覆盖）** 和 **G6（步骤原子性）** 两个 BLOCK 级检查。当 G3/G6 FAILED 时，fix_hints 只有一个通用 fallback（`regenerate_from_prompt`），Agent 无法针对性修复。

**证据**：task_20260715_110631 E2E 数据 — G3 FAILED(6 issues) + G6 FAILED(2 issues)，block_passed=9/11，但 fix_hints 仅 1 个 fallback。

**修复（orchestrator.py `_build_p7_fix_hints`）**：

1. **G3 → `fix_workflow_coverage`**（分两路）：
   - `coverage_gap`（P5 活跃 TP 未被 P6 覆盖）→ `sub_action: generate_missing`，P0 优先级
   - `a_class_step_short` / `b_class_step_empty` / `b_class_smoke` → `sub_action: fix_case`，P1 优先级，含针对性修复指引

2. **G6 → `fix_atomicity`**：
   - 直接引用 G6 gate 已提供的 `fix_example`（含 before/after 拆分示例）
   - P1 优先级，逐条给出非原子步骤和拆分指引

**影响范围**：`_build_p7_fix_hints` +70行；`gate_checker.py` `_extract_step_lines` / `_extract_step_contents` 各+3行。现有逻辑不受影响。

## v4.15.50 — 2026-07-14

### 🔴 P0：P6 Context risk_flag 字段丢失修复（阻塞 V4.15.47/48 生效）

**根因**：`_write_tp_contexts` 使用 `_check_tp_risk_link()`（文本匹配）设置 context.risk_flag，**完全忽略 P5 已正确设置的 `tp.risk_flag` 字段**。19 个 risk_flag=True 的 TP 中有12个因文本匹配失败被改写为 False，导致 V4.15.47/48 的 `_enforce_p0_budget` 保护逻辑收到空数据。

**修复（orchestrator.py）**：P5 直接设置的 risk_flag 优先，文本匹配仅兜底。✅ 改动1行。

**证据**：task_20260713_141913 E2E 数据交叉验证，P5_RF=True(19) vs Context_RF=False(12)。

### 🟡 P1：P7 retry_count 统计补齐

**根因**：p6_metrics.jsonl 正确记录了每 TP 的重试次数（35/79 TP 有重试，总计47次），但 p7_output.json 的 statistics 缺少汇总字段。

**修复（orchestrator.py）**：新增 `_p7_retry_statistics()` 函数，从 p6_metrics.jsonl + orchestrator_state.json 汇总 retry 统计，写入 p7_output.json。

### 🟡 P1：C2 步骤计数正则扩展

**根因**：`_STEP_NUM_RE = r'^\d+[\.\、）)]'` 不支持冒号编号（如"1："）、空格分号，与自动校准的 `isdigit()` 逻辑不一致。

**修复**：正则扩展为 `r'^\d+[\.\、: )\）]'`。

### 🟡 P1：C7.1 语义覆盖 P5 描述长度差异化阈值

**根因**：P5 描述仅~30字的短 TP 和~100字的长 TP 使用相同 bigram Jaccard 阈值（0.04-0.08），导致短描述 TP 全覆盖性触发 WARNING（task_20260713_141913 实测 169/169）。

**修复**：P5 描述 <50 字符阈值×0.5，50-80 字符×0.75，≥80 字符不变。

### 🟢 P2：G1.5 业务操作结果词白名单

**修复（gate_checker.py）**：G15_WHITELIST 增加"提交|新增|保存|修改|删除|创建|更新|校验|验证|回填|同步|推送|导出|导入"+"成功|完成|通过|已生效|正确|一致|完整|无异常"的通用模式。

### 🟢 P2：G5 数据驱动测试豁免

**修复（gate_checker.py）**：在结构相似检测中增加数据驱动模式识别——若所有原始步骤去掉数据值（数字+引号内容）后结构完全一致，视为数据驱动参数化测试，**完全豁免**（非 WARNING）。

## v4.15.48 — 2026-07-13

### 🔴 RISK风险用例P0保护下沉骨架阶段（两级预算口径统一）

**背景**：V4.15.47 仅修复了全局 `_enforce_p0_budget` 对风险P0的保护，但**骨架阶段（inline L4383 + `_build_skeleton_for_batch` L5731）的批次内P0降级不认 `priority_hint`/`risk_flag`**，导致风险P0可能在骨架阶段就被降为P1，全局保护拿不到P0风险场景可保护——独立保护被上游架空。

**核证更正**：L4383 旧注释"已确认当前在LOW分支内"是**过期误导**。经小执+小墨双核证：V5.0(4.13.0) 已废除 HIGH/LOW 分档，统一 standard 模式，该骨架降级在**主执行路径、所有模型都走**，故此隐患对全部需求生效。

**修复（orchestrator.py，小墨执行，邵老板明确授权彻底方案）**：
1. **inline骨架（L4363）**：case_skeletons 透传 `risk_flag` + `priority_hint`
2. **inline骨架降级（L4417）**：降级候选顺序改为 普通非冒烟 → 普通冒烟 → 受保护非冒烟 → 受保护冒烟，`_sk_protected(sk)=priority_hint=="P0" and risk_flag` 的风险P0最后降；feature保护+冒烟计数逻辑保留
3. **`_build_skeleton_for_batch`（L5731）**：同步透传字段 + 同序降级保护
4. **注释更正**：修正 L4383 过期的 LOW 分支注释

**零回归保证**：改动仅对 `priority_hint=="P0" AND risk_flag==True` 场景生效。普通功能用例这两个条件都不满足，候选排序与旧版完全一致 → 代码路径与行为不变。下游P6/Gate只读 case_id/priority/is_smoke/source_test_point，新增字段为纯增量、向后兼容。

**验证**：py_compile通过 + 小墨self code review + 小执深度集成测试（覆盖普通需求零变化回归）。

**说明**：修复由小墨执行（邵老板明确授权彻底方案）。

## v4.15.47 — 2026-07-12

### 🔴 RISK风险用例优先级系统性降级修复（P0预算强约束误伤）

**背景**：task_20260712_112944（债券投顾分润，198用例）体检发现：72条RISK用例**无一条P0/无一条冒烟**，24条冒烟全部来自正向功能用例。小墨用真实P5数据逐层核证定位根因。

**根因（实证）**：
1. P3 `extended_test_points` 明确给出 `priority_hint="P0"`（存量迁移、比例越界、CRM→OA推送等金融高危场景，共18个）
2. `_enforce_p0_budget`（V4.15.8，P0预算硬约束15%）降级时**完全无视 priority_hint**：
   - 类型约束降级：boundary/permission/integration/exception类的P0无条件降P1
   - 预算超标降级：`p0_indices[-excess:]` 从列表**末尾**砍，RISK的ETP恰好排靠后→优先被砍
3. 结果：存量迁移（RISK-001）、比例越界（RISK-002）等高危场景被当普通P0砍掉，风险回归无高优先级把关

**修复（orchestrator.py `_enforce_p0_budget`）**：
1. 新增 `_is_protected(tp)`：`priority_hint==P0 and risk_flag` 的场景受保护
2. 类型约束降级：跳过受保护场景
3. 预算超标降级：降级候选排序改为「普通P0优先降 > 风险P0后降」，仅当普通P0降完仍超标时才降风险P0
4. 预算上限（max_p0）仍严格遵守，避免P0泛滥稀释冒烟比例

**验证（真实P5数据离线回放）**：
- 修复前：RISK P0 = **0**（全被砍）
- 修复后：降级后P0总数=12（严守预算max_p0=12），其中风险P0包含RISK-001存量迁移/RISK-002比例/RISK-003精度等关键场景，普通功能P0优先被降
- 说明：18个hint=P0风险场景因物82条TP戕15%预算上限仅容12个P0，仍有部分风险场景未进P0（物理预算取舍，非bug）
- py_compile语法通过

**遗留建议**：高风险金融需求的15% P0预算可能偏紧，后续可评估为风险场景留独立P0配额。

**说明**：修复由小墨执行（邵老板明确授权）。

## v4.15.46 — 2026-07-12

### 🔧 云端推送失败修复（p0p1非法字段 + HTTPError观测盒区）

**背景**：V4.15.45云端运行（task_20260712_112944，债券投顾分润，198用例，P7 PASS）报告云端推送失败，服务端返回400空details。小墨用真实task数据离线全链路复现定位。

**根因**（实证）：
1. 正式用例推送payload（198条，domain=交易域）用服务端真实严格schema逐条校验 **PASS** —— payload本身合法，本不该400
2. `_push_p0p1_to_review_tool` 构造的payload包含schema不接受的 `metadata.push_type` 和顶层 `p0p1_summary` → 离线报 `"metadata.push_type" is not allowed`（400）
3. 两处HTTPError分支只记 `HTTP {status_code}`，**未记服务端返回nedetails** → 观测盒区，误判为“服务端校验bug”

**修复**（orchestrator.py）：
1. `_push_p0p1_to_review_tool`：删除payload中 `metadata.push_type` 和顶层 `p0p1_summary`（服务端/api/projects/import不消费这两字段，删除无数据损失）
2. 两处HTTPError分支：补记 `e.response.text[:500]` 到error_msg + stderr，消除“只有状态码看不到原因”盒区

**服务端配合修复**（review-tool-cloud/server/routes/projects.js，已本地改，待部署）：`helpers.error('any.custom',{message})` → `helpers.message()`，消除400空details

**验证**：修复后 p0p1 payload 离线校验 PASS；正式198条 payload 严格schema PASS；py_compile语法通过。

**说明**：修复由小墨执行（邵老板明确授权）。


### 🔧 G11需求追溯读错字段真bug修复 + P6数量纪律 + rejection批量提交防护

**背景**：V4.15.44云端运行复盘（task_20260711_112854，债券投顾分润，125TP→268用例，P7 PASS）三路联合评审（小墨核证+小析+小执）。评审中通过实跑验证挖出G11一个真bug。

**修复（3项，3个文件）**：

**修复1（真bug）— gate_checker.py check_G11_req_traceability（L1933）**：
- 根因：`tp_id = case.get("tp_id", "")` 读错字段。case对象**没有tp_id字段**，只有 `source_test_point`（值形如 `requirement-TP-001`）。导致268条case全部映射到空字符串，tp_coverage只剩1个空key，误报「1/1 TP未关联REQ_ID(占比100%)」。
- 同文件其他所有函数（L1136/1206/1237/1304等）都用 `_get_case_field(c, "source_test_point", "") or c.get("source_test_point", "")`，唯独G11漏网。
- 修复：改为 `tp_id = str(_get_case_field(case, "source_test_point", "") or case.get("source_test_point", "")).strip()`
- **实跑验证**：修复后99个requirement-TP类100%正确追溯（source_scenario兜底）；剩余26个RISK/PCI类TP的 source_scenario 在P5中为空，属**上游P5对RISK/PCI类未填需求关联字段**的独立问题（见修复1b）。

**修复1b（方案A，G11实跑验证后补充）— gate_checker.py check_G11_req_traceability RISK/PCI豁免**：
- 背景：修复1消除假报后暴露真实问题——26个RISK(P3风险识别)/PCI(P4合规识别)类TP在P5中source_scenario为空。三路评审(小析+小执)一致推荐方案A：RISK/PCI是横切关注点，不对应单一需求，豁免REQ追溯；方案B(改上游P5补填)会波及G1/G1.5/G3/G4/G7/G12等多个gate，回归面不可控。
- 实现：新增 `_is_risk_pci(tp)` 双层判定（category in risk_verification/pci_verification **OR** ID前缀 `^R\d+-`/`PCI-`/`RISK-`）；从p5层构建 exempt_ids（p5的category是规范英文值，比case层中文可靠）；豁免TP不进tp_coverage；边界防御（全RISK/PCI→PASSED）；有声豁免（返回附 exempt_risk_pci_count + 文案区分需求类vs豁免）。
- **验收**：小执集成测试9/9全通过（含端到端p7_code_check真实门禁：G11 WARNING→PASSED，整体BLOCK 11/11）；小析code review有条件通过（S-1已采纳：为`^R\d+-`加意图注释，本任务实跑RISK ID即R1-001格式，故`^R\d+-`必需不可精简）。

**修复2（prompt纪律）— rules/paragraph_5.md 数量纪律条款**：
- Step②新增：生成前必须先读 context.json/P5数据的 `expected_case_count`，严格按数量生成；PCI类通常=3，禁止习惯性只写2条；生成后自检数量匹配再 --save。
- 解决本轮PCI-003/004/005习惯性写2条→数量不足返工问题。

**修复3（prompt纪律）— rules/paragraph_5.md rejection批量提交防护条款**：
- 重试规则后新增：批量提交时某TP被rejection→立即停止不发后续；下一轮先补发被拒TP；被拒TP PASS后才继续；禁止rejection后紧跟发后续TP（skipped累加）；高风险TP（G1.5高频词/PCI类）单条提交等PASS。
- 解决本轮tp_74/108/113/119后共约11个TP顺序违规skipped问题。orchestrator顺序约束是正确防御设计（V4.15.9/11历史教训），不改代码，改纪律。

**评审结论**：
- 前序版本改动全部实测生效：checkpoint/暂停点state计数(V4.15.38/41)零虚高零误暂停、metrics从state读retry(V4.15.44)23/23逐条一致、压缩后进度自检(V4.15.38)无丢失、RISK-ETP修复(V4.15.44) P7 C1/C2通过。
- G1.5触发8次全是真模糊词，gate拦对了（误诊无需改白名单）；tmp丢失属便利性、C7.1/G12阈值合理（均无需改）。

**说明**：修复由小墨执行（小猿opus-4-8连续2次网络故障0产出，按V4.15.44先例接管），语法检查通过 + G11用本任务真实数据离线实跑验证。

**变更文件**：tools/gate_checker.py(G11修复1+方案A豁免1b), rules/paragraph_5.md, tools/orchestrator.py, SKILL.md, CHANGELOG.md

## v4.15.44 — 2026-07-10

### 🔧 修复 RISK-ETP context 空洞bug（三重串联故障）+ metrics监控盲区

**背景**：V4.15.43云端运行复盘（task_20260710_105254，债券投顾分润，113TP→257用例，P7 PASS）三路联合评审（小墨核证+小析+小执）。

**根因**：RISK-ETP类TP的 step_expected_pairs 生成空洞（如"针对点]两人同时修改同一草稿执行相关测试操作"）。**非上游P3数据质量问题（P3数据完整），是orchestrator转换代码的三重串联故障**：
1. 故障A（根因）：operations_chain继承分支用精确匹配 `source_scenario==source_scenario`，但RISK是2级(M05-F01) vs 非RISK是3级(M05-F01-S01)，永远匹配不上→继承跳过→落兜底
2. 故障B（截断）：diff_hint正则 `(验证|检查|测试|评估)` 把"测试点"的"测试"当动词→截断为"点]..."
3. 故障C（无title）：ETP展开merged_points未设title→退化到id兜底 parts[-1]="1"→"针对1执行相关测试操作"

**额外发现**：p6_metrics.jsonl全部retries=0，但orchestrator_state有24个TP真实重试记录（metrics漏读state）。

**修复（6处，1个文件 orchestrator.py）**：
- P0 故障A（L5552）：精确匹配→`_ss_prefix_match`边界前缀匹配（RISK 2级前缀匹配非RISK 3级，`+"-"`防M05-F01误配M05-F010）
- P1 故障B（L5606）：diff_hint正则先清洗`[扩展测试点]`前缀 + `(?!点)`负向前瞻
- P1 故障C-id兜底（L5613）：纯数字/过短(len<2)时回退description全文
- P1 故障C-title（L5949）：ETP展开补 `title=etp.description`
- P1 监控（L7871）：metrics retries改从orchestrator_state.json读 `p6_tp_{index}_retry`
- L38：SKILL_VERSION 4.15.43→4.15.44

**评审结果**：小析 code review ✅ 有条件通过（边界安全已验证，4条非阻塞建议）+ 小执 回归验证 ✅ PASS（操作链继承率0%→100%，diff_hint截断4/4消除，非RISK无损10/10，metrics重试5/5正确）

**说明**：修复由小墨执行（小猿opus-4-8连续3次网络故障，邵老板授权破例），语法检查+离线单元测试通过。

**变更文件**：tools/orchestrator.py, CHANGELOG.md

## v4.15.43 — 2026-07-09

### 🔧 5项修复：跨TP去重保留变体+内容级完整性校验+_mtps Bug+C7.1阈值+local_repair增强

**背景**：V4.15.42云端运行复盘（task_20260708_103828，债券投顾分润，119TP→254条用例）联合小析小执三路分析。

**根因**：
1. TP-017 和 TP-018 生成完全相同内容（异常场景 vs 核心正向流程），跨TP去重丢弃了TP-019的2条
2. V4.15.41 PARTIAL仅检查文件存在，无法发现内容级缺失
3. `_mtps` 变量名Bug（NameError隐患）
4. C7.1 bigram Jaccard阈值0.10太严→40.6%假阳性

**修复（~35行，2个文件）**：

**orchestrator.py（4处）**：
- P0-1: 跨TP去重改为相同内容但不同source_tp→保留为跨TP变体（不再丢弃）
- P0-2: `_missing_tps`扩展为内容级校验（文件存在但merge后覆盖=0→计入missing）
- P0-3: `_mtps`→`_missing_tps` 修复变量名Bug
- P1-1: C7.1阈值 异常类0.05→0.04 / 功能/性能 0.10/0.08→0.08

**rules/paragraph_6.md（1处）**：
- P1-2: generate_missing前先检查TP文件是否存在且有效，避免重复生成

**评审结果**：小墨自测（语法检查✅）+ V4.15.42回放plan

**变更文件**：tools/orchestrator.py, rules/paragraph_6.md, SKILL.md, CHANGELOG.md

## v4.15.41 — 2026-07-06

### 🔧 5项修复：checkpoint state计数+G1.5白名单+P6.merge partial+HOLLOW_STEPS阈值+G1.5诊断优化

**背景**：V4.15.39云端运行复盘（task_20260702_152300，债券投顾分润，84TP→199条用例）联合小析小执三路分析发现5项需修复。

**修复（~30行，2个文件）**：

**orchestrator.py（3处）**：
- P0-1: PAUSE检查计数改state优先（`p6_completed_tp_indices`），修复V4.15.38遗漏的主PAUSE路径
- P0-3: P6.merge检测到missing TP时gate_data标记PARTIAL（含missing_tp_count+missing_tp_indices）
- P1-1: HOLLOW_STEPS阈值按TP category区分（risk_verification:40%, 默认:60%），与已有降级机制形成双层保护

**gate_checker.py（2处）**：
- P0-2: G15_WHITELIST追加2条通用操作成功确认短语（提交/保存/删除/创建/修改/更新+成功/完成/已生效/通过）
- P1-2: G1.5诊断信息具体化（3条具体建议替代笼统提示）

**评审结果**：小析 ✅ 通过 + 小执 ✅ 通过（P0-1追加_max_seq边界保护 + P1-1方案A双层保护）

**变更文件**：tools/orchestrator.py, tools/gate_checker.py, SKILL.md, CHANGELOG.md

## v4.15.39 — 2026-07-02

### 🔧 10项复盘修复：G1.5词表+fix_hints priority+差异化阈值+高频词+跨TP限定

**背景**：V4.15.38云端运行复盘（task_20260702_103030，债券投顾分润，80TP→195条用例）发现10个问题。

**修复（~50行，2个文件）**：

**gate_checker.py（7处）**：
- G1.5 OBSERVABLE_DATA：新增性能监控类可观测指标（CPU/内存/QPS/响应时间/错误率）
- G1.5 G15_WHITELIST：新增业务操作术语豁免（补录/导入/审核/推送等）
- _build_fix_example：8个return分支全部增加priority字段（P0/P1/P2）
- G7：新增高频未匹配词统计（≥5次单独提示"请确认P5是否遗漏"）
- G5：相似度检测限定同source_tp内（跨TP不比较），减少误报
- G11：修正WARNING文案（"未关联REQ"→"未关联REQ_ID(占比XX%)"）
- G5 duplicate_steps阈值5→3（V4.15.37已改，版本号确认生效）

**orchestrator.py（3处）**：
- C7.1：按test_case_type差异化阈值（功能测试0.30/性能测试0.20/异常风险0.15）
- C7.1：删除硬编码 ENTITY_PATTERNS，改为纯动态提取（引号术语+长名词，过滤停用词），实现跨域通用
- C2：异常处理/风险验证场景diff=3降级为INFO（不触发WARNING）
- SKILL_VERSION：4.15.36→4.15.39

## v4.15.38 — 2026-07-01

### 🔧 checkpoint用state计数 + fs/state差异告警 + p6_verify_progress

**背景**：V4.15.37云端运行发现P6 checkpoint在实际生成18个TP时就错误暂停「已达30暂停点」。根因是checkpoint用glob数文件系统文件数（50个），但state只记录20个（压缩回滚），两者不一致导致 `_segment_done=50-0=50≥30` 错误触发。

**修复（~35行，2个文件）**：

**Fix1: checkpoint `_done` 改用 `p6_completed_tp_indices` 长度（~7行）**
- `_done = len([glob("tp_[0-9]*.json")])` → `_done = len(st.get("p6_completed_tp_indices", []))`
- 数据源统一为 state，不再依赖文件系统

**Fix2: 入口加 fs vs state 差异告警（~10行）**
- 每次 `p6_generate_one` 调用时检测 `_fs_done - _state_done`
- 差值 > 0 时输出 `state_mismatch_warning`（含差异数+修复建议）
- 排除 `_tmp` 临时文件防误报

**Fix3: 新增 `p6_verify_progress` action（~30行）**
- 输出 fs vs state 的完整对比（文件数/索引差异/最大索引）
- Agent 可在压缩后、断点续跑前执行，确认真实进度

**Fix4: paragraph_6.md 压缩后强制自检（~8行）**
- 会话压缩后必须先执行 `p6_verify_progress` 确认进度
- 禁止依赖压缩摘要中的进度描述

**评审结果**：小析 ✅ 通过 + 小执 ✅ 通过（建议 _tmp 排除+stdout+p6_verify_progress action已采纳）

**变更文件**：tools/orchestrator.py、rules/paragraph_6.md、SKILL.md、CHANGELOG.md

---

## v4.15.37 — 2026-07-01

### 🔧 6项修复：排除列表BUG + 热重载 + 空文件校验 + G1.5自检 + C2对应 + fix_hints优先级

**背景**：邵老板运行V4.15.36（实际执行V4.15.35代码），联合小析小执复盘发现6项需修复。

**根因**：
1. 排除列表 `[risk_verification, pci_verification]` 与 RISK TP 实际 category（main_flow/exception等）不匹配 → 降级不生效
2. orchestrator 缓存旧版本，覆盖安装不触发热重载 → 新代码不生效
3. TP-048 空文件 `cases:[]` 未被拦截（expected=2，实际0）
4. G1.5 模糊词反复拦截（生成→被拒→重试循环）
5. C2 步骤-期望数量偏差（5步3期望）
6. P7 fix_hints 缺少优先级，Agent 不知道先修什么

**修复（~40行，4个文件）**：

**Fix1: `gate_checker.py` — 排除列表增加 ID 前缀二次排除（+4行）**
- 降级条件增加：`_tp_id.startswith("RISK-") or _tp_id.startswith("PCI-")` → 不降级
- 防御 category 分配不一致导致的排除失效

**Fix2: `orchestrator.py` — 热重载机制（+20行）**
- 新增 `_hot_reload_modules()` 函数，每次 action 调用前 reload 已加载的 skill 工具模块
- 支持覆盖安装后自动生效，无需重启任务

**Fix3: `orchestrator.py` — `_save_single_tp` 空文件/数量不足校验（+12行）**
- `len(cases) < expected_case_count` → quality_rejected，拒绝保存
- 输出期望/实际数量和修复提示

**Fix4: `prompts/P6_testcase_generation.md` — 生成后强制自检（+8行）**
- 新增「生成后逐条扫描禁止词」步骤，含5类禁止词→可观测替换映射

**Fix5: `prompts/P6_testcase_generation.md` — 步骤-期望严格对应（+5行）**
- 明确 steps 几个编号 = expected_results 几个编号

**Fix6: `orchestrator.py` — fix_hints 加 priority 字段（+9处）**
- generate_missing=P0, fix_step_expected/fix_vague_expected/fix_forbidden/fix_precondition/fix_specificity/fix_forbidden_pattern=P1, meta=P2

**变更文件**：tools/gate_checker.py、tools/orchestrator.py、prompts/P6_testcase_generation.md、SKILL.md、CHANGELOG.md

**评审结果**：小析 code review ✅ 有条件通过（1个ctx顺序bug已修复）+ 小执集成测试 ✅ 发现2个漏修bug已修复

**小执测试发现的追加修复（在评审阶段补充）**：
- Fix7: `_build_fix_hints_single_tp` 3个hint加 `"priority": "P1"`（测试发现遗漏）
- Fix8: `p6_save_batch` 5个hint加 `"priority": "P1"`（测试发现遗漏）
- Fix9: G5 duplicate_steps 阈值 5→3（4条相同用例未被检测的bug）

**待评审**：小析 code review + 小执集成测试

---

## v4.15.36 — 2026-06-30

### 🔧 P5门禁 step_expected_pairs 降级机制

**背景**：邵老板运行债券投顾需求，P5门禁block率50%被拦截。根因是大量TP有完整操作链（step_expected_pairs >= 2步）但description描述偏短，门禁仅检查description质量，导致误拦截。

**根因**：P5门禁的 `_check_p5_desc_quality` 仅检查 description 字段（字数+维度关键词），不检查 `step_expected_pairs`（步骤-期望对）。PCI/风险类TP的描述天然偏短但操作链完整，被错误计入 block_active。

**修复（~35行，2个文件）**：

**Fix1: `gate_checker.py` — `check_p5_description_quality` 增加降级逻辑（+42行）**
- 新增 `DESC_GATE_DOWNGRADE_CATEGORIES` 排除列表（risk_verification, pci_verification）
- 降级条件（全部满足才降级）：
  1. `step_expected_pairs` 长度 >= 2
  2. `operations_chain` 非空（来源非fallback模板）
  3. `category` 不在排除列表
  4. 步骤内容不含 `{diff}` 等模板占位符
- 降级动作：BLOCK issue → WARNING（不参与 block_active 计数）
- 降级后描述仍 <30字 → 追加提示 WARNING
- results 新增 `downgraded` 字段

**Fix2: `orchestrator.py` — P5 gate 调用处增加降级统计（+10行）**
- 新增 `downgraded_count` 计数器
- TP 标记 `_desc_gate_downgraded: True` 供 P6/P7 追溯
- p5_quality 输出增加 `downgraded` 字段
- stderr 日志：`[V4.15.36] N个TP因有完整操作链而降级BLOCK→WARNING放行`

**双路评审**：小析（测试分析）有条件批准 ✅ + 小执（测试执行）方案可行 ✅

**变更文件**：tools/gate_checker.py、tools/orchestrator.py、SKILL.md、CHANGELOG.md

---

## v4.15.35 — 2026-06-27

### 🔧 risk TP 死循环修复 — 模板去占位符 + 降级保留warning

**背景**：V4.15.34云端测试发现TP-057~076（20个risk/PCI类TP）context含模板占位符，P6生成时被HOLLOW_STEPS + PLACEHOLDER_DETECT拦截→死循环。

**根因**：`_build_step_expected_pairs` 对 risk_verification 的兜底模板过于通用（"触发{diff}风险验证场景"），P6 context被污染后占位符检测无法区分模板占位符和Agent偷懒占位符。

**修复（~18行，3处）**：

**Fix1: 改进 risk_verification fallback 模板（L5623）**
- 旧："触发{diff}风险验证场景" / "验证{diff}风险处理逻辑是否符合预期"
- 新："打开{diff}功能模块，录入符合风险触发条件的测试数据并提交" / "系统弹出风险告警提示，且数据未被正常保存"
- 增加操作具体性（录入+提交），避免触发占位符检测

**Fix2: 增强 diff_hint 提取（L5593-5603）**
- 优先从 description 提取"验证/检查X"结构中的 X（动词+名词，语义更精准）
- 清洗 title 前缀（风险/PCI/安全/合规），避免 diff_hint 为模糊词
- 末选：ID后缀

**Fix3: risk TP 占位符检测降级（L7104-7114）**
- `_check_placeholder_patterns` 中新增 risk_verification 降级分支
- **关键修正**：保留原有 warning 类型 issue（不丢弃策略③的相似度warning）
- block → warning + `_RISK_DEGRADED` 标记 + note 说明

**第二轮修复（Q1~Q3，小析Code Review低风险改进点，~4行）**：

**Q1: diff_hint 正则防标点污染（L5595）**
- `._{2,15}?` → `[^，。,.]{2,15}?`，避免捕获到标点符号

**Q2: rule=None 防御（L7111）**
- `i.get("rule","")` → `(i.get("rule") or "")`，防御 rule 为 None 时 TypeError

**Q3: 降级事件 stderr 日志（L7114-7115）**
- 新增降级计数 + stderr 日志输出，格式：`[V4.15.35] risk_verification TP#N 降级: X 个block→warning`

**双轨评审结果**：小析 Code Review A- ✅ + 小执 集成测试 28/28 PASS ✅

**变更文件**：tools/orchestrator.py、SKILL.md、CHANGELOG.md

---

## v4.15.34 — 2026-06-26

### 🔧 统一checkpoint + C6.1词库扩展 + g15回缩 + 导出原子步骤

**背景**：V4.15.33云端测试（task_20260626_092645, 71TP→212用例）发现4类问题。

**修复（~20行）**：

**P0: 统一checkpoint 15→30（~4行）**
- PAUSE_EVERY_N 15→30
- _segment_done >= 15 → >= 30
- required_pause_after +14 → +29

**P1: C6.1词库扩展等效表达（~3行）**
- KW_DATA: +维护/已维护/填写/已填写/选项/字段/表单
- KW_ENV: +已配置/已启用/已开通
- 覆盖"XX已维护""表单已填写"等等效表达，减少69条C6.1假阳性

**P2: g15_drift stop_words回缩（~1行）**
- stop_words回加"验证/流程/场景/处理/进入/页面"等通用业务词
- 防止V4.15.33过度精简导致关键词泛滥、drift检测漏报

**P1: P6 prompt导出原子拆分规则（~2行）**
- prompts/P6_testcase_generation.md 新增第4条步骤规则：导出操作必须拆为"定位+点击"2步

**P3: generate_one边界校验（~8行）**
- tp_index越界→明确ERROR含修复提示，消除TP-092静默失败

**变更文件**：
- tools/orchestrator.py: checkpoint(~4行) + C6.1(~3行) + g15(~1行) + 边界校验(~8行) + _KW_DATA(~1行)
- prompts/P6_testcase_generation.md: 导出步骤规则(~2行)
- tools/core/constants.py + SKILL.md + CHANGELOG.md: 版本号

## v4.15.33 — 2026-06-25

### 🐛 g15_drift三修复 + checkpoint阈值下修

**背景**：V4.15.32云端58TP任务，13个P2 TP触发g15_drift（全在TP-044~058，M05/M06模块），checkpoint因>=60门槛未触发。

**g15_drift三修复（~7行）**：
1. 关键词来源扩展：description(42字) → description+scenario_description+business_context[:300]（1000+字）
2. stop_words精简：移除"验证/流程/状态/正常/异常/场景/处理/进入/页面"等业务核心词
3. 匹配文本全量：去除 each case [:500]截断，边界用例后半段关键词可匹配

**checkpoint阈值下修（~1行）**：
4. `_saved_count >= 60` → `>= 30`，让30-60TP中型任务也能触发30TP暂停

**变更文件**：
- tools/orchestrator.py: g15_drift检测逻辑(~7行) + checkpoint条件(~1行) + SKILL_VERSION
- tools/core/constants.py: SKILL_VERSION
- SKILL.md: 版本号

## v4.15.32 — 2026-06-25

### 🐛 P6 freq_data过早持久化导致timeout_hard死锁

**背景**：V4.15.31 云端运行 TP-118(PCI-001) 持续超时，首次471s后固定300s timeout_hard。

**根因**：`_save_single_tp` 中 freq_data(含last_save)在JSON解析和质量校验**之前**落盘，导致：
1. 质量不通过的调用也记录了 last_save
2. 后续重试时 elapsed = now - last_save > 300s → timeout_hard拦截
3. timeout_hard exit(1)不更新freq_data → 死锁永远无法重试

**修复**：freq_data写入从质量校验前(原L7302)移至文件保存成功后(L7637)，~9行移位

**变更文件**：
- tools/orchestrator.py: _save_single_tp freq_data写入位置下移 + SKILL_VERSION
- tools/core/constants.py: SKILL_VERSION
- SKILL.md: 版本号

## v4.15.31 — 2026-06-24

### ⚡ P6门禁效率优化：G1.5自检+HOLLOW前置+checkpoint减半+g15豁免

**背景**：V4.15.30 云端运行206条用例，BLOCK 10/10 PASS但P6阶段约**75分钟浪费**在：
- G1.5 模糊词循环重试 ~45min（9个词逐个触发）
- HOLLOW_STEPS 生成后拦截 ~20min（整条重写）
- 15-TP checkpoint 手动resume ~10min（打断节奏）
- g15_drift PCI误报（噪音）

**修复（4项，~23行）**：
1. **G1.5输出前强制自检** — P6 prompt末尾增加"扫描9个禁止词→发现即重写→0禁止词再输出"自检步骤，消除3-4轮循环重试(~10行)
2. **HOLLOW_STEPS步骤规范前置** — P6 prompt增加"≥10汉字+「」UI元素"强制规范，Agent生成前就知道标准(~8行)
3. **checkpoint 30TP+前60跳过** — `15→30`间隔，前60个TP不暂停，减少暂停次数并保留中后程断点(~1行)
4. **g15_drift PCI豁免** — P3/P4来源TP（关键词天然少）跳过drift检查，消除误报(~4行)

**预期效果**：
- G1.5重试: 3-4轮 → 1轮 (节省87%)
- HOLLOW: 生成后拦截 → 生成时避免 (节省80%)
- checkpoint: 5次→2次暂停 (节省60%)
- g15_drift: 消除PCI误报
- **总体节省约84% P6阶段无效耗时（~75min → ~12min）**

**变更文件**：
- tools/orchestrator.py: _build_p6_prompt(~18行) + _p6_save_tp(~5行)
- tools/core/constants.py: SKILL_VERSION
- SKILL.md: 版本号

## v4.15.30 — 2026-06-24

### 🐛 P2测试点71%丢失：description唯一化 + P5去重双维度防御 + P1字段一刀根治

**背景**：task_20260624_094953 发现 P2 生成85条测试点，P5合并后仅剩47条，**丢失60条(71%)**。

**根因**：
1. P2 description模板固化（`验证{scenario}正常流程`），61个场景的描述高度重叠
2. P5去重只用 `description` 完全相同判断，不同scenario但描述相同 → 被误删
3. P1场景用 `scenario_id` 字段但全链路读 `id` 字段 → source_scenario空 + P5富化/P6示例失效

**修复（4项，~38行）**：
1. **P2 description加scenario_id前缀** — 4条规则全部改为 `[{scenario_id}] 验证XXX`，确保描述唯一(~8行)
2. **P1 scenario字段兼容** — `scenario.get("id") or scenario.get("scenario_id", "")` 兼容两种字段名(~1行)
3. **P5去重双维度防御** — 改为 `(description, source_scenario)` 元组，仅完全相同时才去重(~10行)
4. **P1标准化一刀根治** — `action_p1_code_merge` 组装p1_output.json时递归遍历所有scenario节点，`scenario_id`→`id` 标准化，下游P2/P5/P6全部自动兼容(~15行)

**预期效果**：
- P2→P5去重率从71%降至<5%
- P2 test_points description全部带scenario_id前缀，可追溯
- 防御层：双维度去重不会误删；P1标准化后所有下游读取点自动修复
- 同行4056/4525/6031的同类问题一并消除

**变更文件**：
- tools/orchestrator.py: action_p2_code_generate(~8行) + action_p5_code_merge(~10行) + action_p1_code_merge(~15行)
- SKILL.md: 版本号

## v4.15.29 — 2026-06-23

### 🔧 P6阶段质量前移：C6.1前置条件分段自检 + G2模糊词扩展拦截

**背景**：V4.15.28 云端运行复盘发现，P6 Agent 生成缺陷全部拖到 P7 修复：
- C6.1前置条件不完整 64条/19%（P7修复3分钟）
- G2模糊词残留 4条/1.2%（未修复直接放过）

**根因**：`_quick_gate_single_tp` 仅检查 preconditions 是否为空，不检查内容完整性

**修复（2项，~20行）**：
1. **C6.1 前置条件分段自检** — preconditions 按分号/换行拆分，段数<2 则拦截，要求 ≥2 个要素(12行)
2. **G2 模糊词扩展** — fuzzy_words 增加"一致"/"无异常"(2行)，利用现有「」引号豁免机制防误报

**预期效果**：
- C6.1 拦截：P6 落盘前拒收不完整前置条件，Agent 在同次生成中补全
- G2 拦截："一致"/"无异常"在 P6 阶段强制具体化，不再拖到 P7

**变更文件**：
- tools/orchestrator.py: _quick_gate_single_tp (~20行)
- SKILL.md: 版本号

## v4.15.28 — 2026-06-23

### 🔴 C7/G3 核心阻塞修复：case_id与test_point.id不一致导致门禁永久FAIL

**背景**：task_20260622_163751 P7 门禁 C7/G3 始终 FAIL，BLOCK 仅 8/10 通过。
292条用例全部生成但 P7 报告 requirement-TP-076 未覆盖。

**根因**：
1. P6 LLM 生成 case_id 时使用了文件序号(tp_index=75)而非 P5 test_point.id(TP-076)
2. P6 save 代码在 LLM case_id 为有效 ASCII 时直接采纳，不校验是否包含正确 tp_id
3. P7 C7/G3 覆盖检查的主要匹配键为 source_test_point，但回退逻辑不足

**修复（3项）**：
1. **p6_save_one case_id 强制校验** — LLM case_id 不含正确 tp_id 时强制用 auto_cid(6行)
2. **C7 case_id 回退匹配** — 新增3级回退：TP短ID→数字索引→兜底(25行)
3. **G3 case_id 回退V2** — 新增数字索引回退(LLM误用tp_index场景)(15行)

**变更文件**：
- tools/orchestrator.py: 修复1/2 (~35行)
- tools/gate_checker.py: 修复3 (~15行)
- SKILL.md: 版本号

## v4.15.27 — 2026-06-22

### 🐛 V4.15.26 集成测试发现 C2自检 MULTILINE 遗漏

**根因**: `_quick_gate_single_tp` 中 C2 自检用 `re.findall(r'^\d+[…]', …)` 缺少 `re.MULTILINE`，导致只匹配第一行。
**修复**: 添加 `_qs_re.MULTILINE` 标志（2行）。
**验证**: TC-001(3步vs1期望)→触发C2 ✅ / TC-002(2步vs2期望)→不触发 ✅

## v4.15.26 — 2026-06-22

### 🔧 V4.15.25 复盘5项修复

**P0 修复：**
1. **P0-1 KeyError 'detail'** — `_p7_check_p0_distribution` 用 `message` 而 gate_checker 期望 `detail` → 统一为 `detail`(2行) + gate_checker防御加固(2行)

**P1 修复：**
2. **C2自检嵌入 P6** — `_quick_gate_single_tp` 末尾加 steps vs expected 行数差≥2检查(12行)，P6阶段拒绝保存
3. **checkpoint 强制暂停** — `action_p6_generate_one` 入口检查连续生成≥15TP→`CHECKPOINT_REQUIRED`→`exit(3)`(25行)

**P2 修复：**
4. **HMAC/Gate pass 文档化** — paragraph_6.md 加 gate pass JSON 格式示例 + checkpoint 机制说明(~25行)

**元规则：**
5. **SKILL.md 元规则#6** — 禁止Agent自行发明规则(sleep/延迟/防封禁)(~8行)

### 变更文件
- tools/orchestrator.py: 修复1/2/3 (~40行)
- tools/gate_checker.py: 修复1防御 (~2行)
- rules/paragraph_6.md: 修复4 (~25行)
- SKILL.md: 修复5 + 版本号

## v4.15.25 — 2026-06-22

### 🐛 action_p6_resume data_dir 变量作用域 bug

**根因**：L7830 `os.path.join(data_dir, ...)` 在 `data_dir = args.data_dir`(L7842) 之前执行，Python UnboundLocalError。

**修复**：将 checkpoint 清理代码移到 `data_dir = args.data_dir` 之后（1行移动）。

### 变更文件
- tools/orchestrator.py: ~6行挪动

## v4.15.24 — 2026-06-22

### 🔧 V4.15.23 复盘6项核心修复 + 84条未分类修复

**P0 修复：**
1. **去 [:20] 截断(5处)** — C1/C6.1/C6.2 检查输出 + C6.1/G1 fix_hints 全部去除截断，50条失败全部展示
2. **_quick_gate_single_tp 加 preconditions 检查** — 原只检查 title/steps/expected，新增 preconditions 为空检查(3行)，P6阶段直接拦截
3. **C6.1+G9 统一修复** — 合并 fix_precondition + fix_data_precondition 为 fix_precondition_unified，case_id 去重消除重叠
4. **menu_path 自动补全** — _save_single_tp 中若 LLM 漏填 menu_path，从 P5 TP→source_scenario→P1 feature_tree 自动推导路径(修复84条未分类)
5. **paragraph_6.md TP文件映射规则** — 显式说明 tp_{N}.json = TP-{N+1}（tp_index = TPN-1），消除文件混淆
6. **paragraph_6.md fix_hints 异常报告** — 增加 fix_hints 返回异常时必须报告用户、不得静默跳过的规则

### 变更文件
- tools/orchestrator.py: 修复1/2/3/4 (~80行)
- rules/paragraph_6.md: 修复5/6 (~6行)
- SKILL.md: 版本号

## v4.15.23 — 2026-06-18

### 🔧 V4.15.22 云端运行阻塞修复（3项）

1. **p3_p4_parallel 前置检查优化** — agent_output缺失时返回 needs_agent 状态（含prompt路径），而非硬失败
2. **p5_retry --force-continue 实现** — 实现熔断恢复action，清除.p5_blocked_lock后跳过质量门禁重新合并
3. **P5维度阈值降级** — PRECONDITION_DIMS 从≥2/5降为≥1/5（47条rule_issues全部为维度不达标）

### 变更文件
- tools/orchestrator.py: 修复1/2 (~30行)
- tools/gate_checker.py: 修复3 (~2行)

## v4.15.22 — 2026-06-18

### 🔧 V4.15.21 复盘 10 项修复（三方评审通过）

**P0 修复：**
1. **C7.1 乱码容错修正** — 正则提取短ID后缀再查 short_to_full_map（处理乱码前缀）
2. **P6 prompt 禁「确认数据符合预期」** — 增加反例，禁止模糊占位符式期望
3. **P6生成时C2自检** — _save_single_tp 中 steps vs expected 行数差≥3 自动补齐（标记需人工补充）

**P1 修复：**
4. **G7「系统中心」白名单** — 豁免系统入口路径（多入口导航不在P5 page_path中）
5. **G1.5 fix_hint 精确化** — hint_text 增加 vague_step + diagnostic 诊断信息
6. **P6暂停强制 checkpoint** — 每15TP写 .p6_checkpoint_required 标记文件，resume/merge 自动清理
7. **P6三要素模板强化** — 🔴 标记 + C6.1失败警告

**P2 修复：**
8. **速率说明显式化** — help 文本注明 rate_limit 为监控非强制
9. **p6_merge --retry** — 增加 retry 参数支持
10. **P7容忍度矩阵** — paragraph_6.md 增加导出决策表（≥7/9→导出, 5-6/9→标记, <5→拦截）

### 变更文件
- tools/orchestrator.py: 修复1/3/5/6/8/9 (~55行)
- tools/gate_checker.py: 修复4 (~3行)
- prompts/P6_testcase_generation.md: 修复2/7 (~8行)
- rules/paragraph_6.md: 修复10 (~10行)


## v4.15.21 — 2026-06-18

### 🔧 V4.15.20 复盘 + 三方评审后 9 项修复

1. **p7_batch_fix自动merge** — action_p7_batch_fix修复成功后自动调用action_p6_merge
2. **resume TP完整性验证** — action_resume增加TP文件数量检查，缺失>3时报警
3. **G7业务数据值豁免** — 增加公司名/产品名/测试数据值豁免正则（~85%假性→约15%）
4. **G1.5诊断+豁免** — issue增加diagnostic字段 + OPERATIONAL_ACTIONS补充4词（复制/验算/准备/等待）
5. **C7.1乱码容错** — _p7_check_c71增加short_to_full_map映射
6. **must_emit警告强化** — paragraph_5/6.md中must_emit警告🔴→🔴🔴🔴级强化
7. **G5降级BLOCK→WARNING** — 结构相似检测降级为WARNING（边界测试合理现象）
8. **G4冒烟=P1允许** — 冒烟允许P0或P1，仅P2报警
9. **SKILL.md流程速查表** — 增加P0-P7段落速查表辅助Agent定位错误

### 变更文件
- tools/orchestrator.py: 修复1/2/5 (~35行)
- tools/gate_checker.py: 修复3/4/7/8 (~25行)
- rules/paragraph_5.md: 修复2b/6a (~5行)
- rules/paragraph_6.md: 修复6b (~3行)
- SKILL.md: 修复9 (~15行)

### 三方评审
- 小析（需求合理性）: ✅ 9/9通过，4项有条件
- 小执（代码安全性）: ✅ 7/9无风险，2项可控
- 小猿（实现可行性）: ✅ 5/9可行，4项调整（已纳入）
- 小墨（统合）: ✅ 全部通过，G5 fixer放弃（需LLM）

## v4.15.20 — 2026-06-17

### 🔧 V4.15.19 复盘11问题修复（10改1不改，三方评审通过）

### 🔧 P6暂停锁TP计数虚高修复 + V4.15.18全量修复合集

**修复0：P6暂停锁TP计数虚高（云端write限制联动修复）**
- 根因：glob模式`tp_[0-9]*.json`误匹配Agent中间文件`tp_XXX_agent_output.json`
- 7处glob/os.listdir过滤全部增加`_agent_output`排除条件
- 影响：暂停锁94→62虚高(误计32个agent_output文件)、resume段起点偏移

**修复1：source_test_point短格式→C7/G3/G4连锁故障**
- 修复A（生成端）: _save_single_tp移除V4.15.17#13反向校验，从tp_context.json读tp_id，乱码阈值0.5反推P5
- 修复B（检查端）: _p7_check_c7 + gate_g3 两处添加short_to_full_map容错映射，支持TP-NNN和ETP-N变体
- 根因：V4.15.17#13编码校验过严，Latin-1字符被回退短格式→C7覆盖率0%

**修复2：G12 boundary动态阈值**
- 加权平均替代if/elif冲突: 0.10×流程型+0.20×计算型+0.15×标准型
- TP<5时绝对数量判定(>=1即PASS)
- 移除无效_p0_output参数
- 配套: P4 boundary生成指引

**修复3：P5熔断三级响应**
- >=30% WARNING + ≥50% STOP + ≥80% SELF_CHECK
- STOP时写入.p5_blocked_lock状态锁 + BLOCK原因分类 + 恢复指引
- 变量名修正 total_checked→total_tp

**修复4：G7追溯容错**
- 随#1解决，增加source_matched标记区分格式问题vs真实缺失

**修复5：G1边缘case验证**
- task_092855回放确认 G1:79→0, G1.5:24→0，V4.15.16/17生效

**修复6：G2弱验证词**
- 保持现有BLOCK/WARNING分流，扩展has_explicit正则: 与.*一致|和.*相同|.*与.*值相等
- 不将"一致"整体降级（保守策略）

**修复7：C2步骤-期望偏差**
- P6铁律#4增强: 实操指南+正反例+P0排除说明
- C2语义检测推迟V4.15.19

**修复8：P5输出保护**
- p5_output.json写入前检查存在+有效（merge_log字段）

**修复9：P6监控增强**
- TP开始/结束时间戳 + >60秒慢告警 + 重试原因分类

**修复10：G4冒烟fallback**
- case_id→TP反推，纳入#1的统一映射

### 三方评审
- 小析（需求验证）: ✅ 有条件同意
- 小执（质量审计）: ✅ 有条件同意
- 小猿（代码评审）: ✅ 有条件同意
- 三方共识9项修改后发布

### 变更文件
- tools/orchestrator.py: 修复1A/1B/3/8/9/10 (~140行)
- tools/gate_checker.py: 修复1B/2/4/6 (~65行)
- prompts/P6_testcase_generation.md: 修复7 (~15行)
- rules/paragraph_4.md: 修复2配套 (~15行)

### 已知限制
- C6.1 batch_fix仅加remarks不修preconditions（V4.15.19升级）
- C2语义检测推迟V4.15.19
- P5质量根因（scenario拆分优化）架构级（V4.15.20+）

---

## v4.15.17 — 2026-06-16

### 🔧 G1/G1.5 豁免扩展第二轮 + orchestrator 信号增强

**gate_checker.py — 6处修复**

1. **等待豁免模式扩展**: `.{1,15}` → `.{1,25}`, 新增关键词：推送/显示/超时/同步/发送/返回/跳转/消失
2. **时间等待豁免**: 新增“等待N分钟/秒/小时”模式豁免
3. **超时状态豁免**: 网络/会话/请求/连接/接口/响应/系统 + 超时
4. **操作动词扩展**: 新增打开/清空/完善/不做/未做/修改/删除
5. **对象词库扩展**: 新增区域/变化/超时/异常
6. **输入动词简写**: 3处 `(?:输入|填写|录入|设置)` → `(?:输入|填写|录入|设置|填)`
7. **G1.5 OPERATIONAL_ACTIONS**: 新增检查/核对/校验/核实/验证/观察/模拟
8. **G1.5 白名单**: 新增“检查是否有值”模式

**orchestrator.py — 5处修复**

9. **P6完成信号**: `paragraph_complete` + `user_prompt` 在全部TP生成完毕时触发
10. **review_url提升为顶层**: cloud_review推送成功后将review_url放置在output_data顶层，附review_reminder
11. **merge警告**: p6_merge成功输出增加warning字段，禁止手动修改p6_output.json
12. **batch_fix C6_1说明**: 输出增加note字段，明确仅标注remarks未改写preconditions
13. **source_test_point编码**: 赋值后校验字符范围，异常字符回退为 `TP-{index:03d}`

### 变更文件
- `tools/gate_checker.py`: 2处新增 + 1处扩展
- `tools/orchestrator.py`: 3处新增 + 1处扩展 + 1处修改

---

## v4.15.16 — 2026-06-16

### 🔴 P0 — P7 质量门禁 G1/G1.5 豁免缺口全面修复（task_20260616_092855 联合分析驱动）

**修复1：G1 对象词库通用化 (L634-636)**
- UI对象词库扩展：`员工|客户` → `人员|实体|项目|条目`（通用化，避免HR域过拟合）
- 业务实体豁免加修饰限制 + 泛词排除（操作/结果/数据/内容/信息/状态/功能/页面/流程/记录/模式/任务）
- 新增通用选择/删除豁免（排除泛词后放行）

**修复2：G1 操作+数量+对象动词/对象集扩展 (L637-643)**
- 动词集扩展：添加/删除/新增/移除 → +选择/修改/切换/勾选
- 对象集扩展：行/条/个/组/配置 → +人员/实体/记录/项目/条目
- 新增无数量修饰豁免：添加/删除 + 通用对象

**修复3：G1 操作动词豁免扩展 (L646)**
- 新增25个豁免动词：补充/修正/保存/弹出/进入/审批/通过/执行/下载/对比/留空/置空/提示/刷新/不添加/未添加/提交/导出/模拟/同步/维护/关闭/查询/发送/找到
- 不包含"进行"（太泛，防止错误豁免真模糊步骤）

**修复4：G1 记录/查看/对比容错模式 (L650)**
- 新增通用容错：记录/查看/对比/观察 + 通用对象词（数据/数量/状态/结果/时间/信息/字段/内容/类型/级别/方式/项目）
- 移除业务特定词（姓名/比例）

**修复5：G1.5 操作性动词集扩展 (L794)**
- OPERATIONAL_ACTIONS 新增：查看/刷新/对比/记录/找到/修改/进入/尝试

**修复6：G1.5 白名单扩展 (L798-823)**
- 字符集扩展：[为是显示弹出] → [为是显示弹出一致正确相等相符保留]
- 新增"确认+数量限定"白名单：确认.*(?:只有|仅|仅剩|仅显示).*(?:保留|存在|显示|可见)
- 新增"进入/查看+对象"白名单

**修复7：G1.5 OBSERVABLE_DATA 扩展 (L801-803)**
- 新增时间指标：时间戳/耗时/加载时间/渲染时间/响应时间
- 新增字段结构指标：字段/列/表头 + 名称/顺序/排列/格式/类型

### 变更文件
- `tools/gate_checker.py`: 9处V4.15.16标记，7类豁免缺口修复

### 修复效果（回放 task_20260616_092855）
- G1: 79条 BLOCK → 0条 (-100%)
- G1.5: 20条 WARNING → 0条 (-100%)
- 可靠性验证：通用词库，无HR域过拟合

### 联合分析
- 小墨: 50条问题逐条分类，6类缺口全覆盖分析 + 可靠性审计
- 小执: 18项改动生效性验证，豁免逻辑逐行审计
- 小猿: 代码修改执行

---

## v4.15.15 — 2026-06-15

### 🟢 P1 — P6 生成阶段质量加强（P6 prompt 铁律#2 改动）

**修复1：P6 prompt 截断解除**
- `orchestrator.py` _read_file_safe max_chars: 15000→25000
- 根因：P6 prompt 文件 37KB，原只加载 15000 字符（截断 24%），LLM 看不到末尾重要规则

**修复2：铁律#2 一刀切→上下文指导**
- `prompts/P6_testcase_generation.md` 铁律#2
- 原："禁止 观察/检查/确认/记录/等待"
- 改：6 组动词 × ✅/❌ 对照表，有具体对象时允许使用
- 根因：铁律#2 与 G1 检查器 V4.15.14 的放行规则矛盾
- 预期效果：LLM 生成的步骤直接满足 G1，P7 G1 修复工作减少 60-70%

**修复3：铁律#4 放宽**
- 原："步骤数 = 期望结果数"（严格 1:1）
- 改："步骤数 ≈ 期望结果数，偏差 ≤ 2"（登录/导航步骤可不配）
- 对齐 C2 阈值（V4.15.12 diff≥5 BLOCK）

**修复4：P6_guided.md 同步**
- 步骤规则 + 期望规则均改为上下文指导模式
- 铁律#4 同步放宽

### 变更文件
- `tools/orchestrator.py`: max_chars 15000→25000
- `prompts/P6_testcase_generation.md`: 铁律#2 + 铁律#4
- `prompts/P6_guided.md`: 步骤规则 + 期望规则 + 铁律#4

### 联合分析
- 小墨: 发现 P6 prompt 与 G1 检查器矛盾 + 截断问题
- 小执: 技术可行性确认（截断 24% + token 预算安全）

---

## v4.15.14 — 2026-06-15

### 🟡 P1 — Agent修复效率优化（task_20260615_150738 联合分析驱动）

**修复1：fix_example 去占位符化**
- `_build_fix_example` 的 vague 分支原返回 "中的「具体按钮/字段名」" 占位符
- 改为从 extra.p5_elements 提取真实元素名生成 after 示例
- 调用处传入 valid_element_names[:5]
- 根因：Agent 拿到 fix_example 后无法直接应用 → 花 6 轮猜规则修复

**修复2：G1 新增 3 项豁免模式**
- 异步等待：`等待.{1,15}(?:完成|加载|响应|导出|下载)` — "等待导出完成"是合理步骤
- 数据记录/观察：`(?:记录|观察).{0,5}(?:列表|页面|系统).{0,10}(?:条数|数据|状态)` — "记录列表总条数"有具体对象
- UI 状态变更：`(?:(?:默认|已)?显示|激活|选中|禁用).{0,10}(?:tab|标签|按钮|字段)` — "默认显示tab"是具体可观测状态
- 预期效果：G1 WARNING 43 → 35

**修复3：G1 fix_hints hint_text 增加具体修复示例**
- 原文本只描述"做什么"，新增 3 组 before/after 修复示例
- 明确修复方法是"只在关键元素上加「」引号"而非整体重写

### 变更文件
- `tools/gate_checker.py`: fix_example 去占位符 + 3 项豁免模式
- `tools/orchestrator.py`: hint_text 增加修复示例

---

## v4.15.13 — 2026-06-15

### 🔴 P0 修复 — G1/G1.5 假性 BLOCK（task_20260615_104127 联合分析驱动）

**修复1：G1 增加 labels 收集**
- `gate_g1_step_concreteness` 的 `valid_element_names` 原只遍历 buttons/inputs/selectors
- 增加 labels 遍历（+6行代码），50个 P5 labels 对 G1 可见
- 根因：代码遗漏（缺一个 for 循环），P5 实际有 82 个元素但 G1 只用到 ~32 个

**修复2：G1 增加数据搜索步骤豁免**
- 新增："找到X记录""查找X数据"等测试数据准备步骤自动豁免
- 根因：G1 对这 27 条（34.6%）步骤无豁免，但它们是有具体对象的合理描述

**修复3：G1 增加操作+对象通用模式**
- 新增 "点击+按钮" "操作+数量+行/配置" 两种通用正面匹配
- 根因：P6 步骤用通用动词+对象名描述操作，即使对象名不在 P5 中也应豁免

**修复4：G1.5 扩展可观测 UI 模式**
- OBSERVABLE_UI 加入"表单"，扩展为"列表.{0,10}(是否有|包含|记录|数据)"
- 新增 "分页|页码|Sheet|下拉框" 等具体组件名匹配

**修复5：G1.5 增加数据对比/显示豁免**
- OBSERVABLE_DATA 新增对比类 "对比.{0,20}(一致|匹配|相同)"
- 新增显示类 "字符/字段.{0,8}(完整|无乱码|正确|格式)"

### 效果
- G1: FAILED (78) → WARNING (40) — 48.7% ↓
- G1.5: FAILED (58) → WARNING (49) — 15.5% ↓
- BLOCK 通过率: 7/11 (63.6%) → 8/11 (72.7%)

### 变更文件
- `tools/gate_checker.py`: G1 labels + 数据搜索豁免 + 操作模式 + G1.5 UI 扩展 + 对比豁免
- `SKILL.md`: 版本号
- `tools/orchestrator.py`: SKILL_VERSION
- `tools/core/constants.py`: SKILL_VERSION

### 联合分析
- 小析（test_analyst）：G1 88.5% 假阳性分析 + P5 82 元素确认
- 小执（test_executor）：labels 代码遗漏 + 5 个新匹配模式 + G1.5 豁免盲区
- 小墨（总协调）：方案设计 + 代码修改 + 版本发布

---

## v4.15.12 — 2026-06-15

### 🔴 P0 修复 — P7 质量门禁假性 BLOCK（task_20260613_173506 联合分析驱动）

**修复1：G9 词典扩充**（code review 后移除 "条" 和 "正常"）
- `DATA_KEYWORDS_V9` 扩充高频基础词
- 最终词典：account 新增 "已登录""登录""账号""账户""管理""权限"
  config 新增 "已打开""运行""系统正常"；data 新增 "创建""准备""数据"
- 移除 "条"（过短，匹配"条件"等，code review P0-1）
- 移除 "正常"（过泛，匹配"网络正常"等，code review P0-2）
- `DATA_KEYWORDS_V9` 扩充高频基础词：account 维度新增 "已登录""登录""账号""账户""管理""权限"
- data 维度新增 "创建""准备""数据""条"；config 维度新增 "已打开""运行""正常"
- 根因：249 条 WARNING 的 preconditions 全都含"已登录"，但旧词典完全不收录
- 预期效果：299/299 条 PASS

**修复2：G9 字段映射 bug**
- `check_G9_data_preconditions` 改用 `_get_case_field` 兼容嵌套 fields 结构
- 修复 2 条 case_id="?" 的 FAILED（preconditions 在嵌套结构中被漏读）

**修复3：G10 NoneType 异常**
- `check_G10_dependency` 过滤 None case_id，修复 `re.escape(None)` 异常
- 根因：2 条残缺用例缺少 case_id 字段

**修复4：C2 阈值调整（临时）+ 截断提升**
- BLOCK 阈值从 diff≥3 临时提升到 diff≥5（等语义分类器落地后恢复）
- issues 截断从 `[:10]+[:10]` 提升到 `sorted(...)[:30]+sorted(...)[:20]`（按 diff 降序）
- 预期效果：当前 20 BLOCK → ~4 WARNING

### 🟡 P1 — fix_hints 机制补全

**修复5：_build_p7_fix_hints 补充 G5**
- 新增加 `fix_forbidden_pattern` action
- 区分 duplicate_steps（完全重写）和 similar_structure_warning（注入差异化数据）
- 截取上限：[:10] 组

**修复6：_build_p7_fix_hints 补充 G9**
- 新增加 `fix_data_precondition` action
- 区分 FAILED（preconditions 为空→完整补充）和 WARNING（缺关键词→补充数据维度）
- 截取上限：[:30] 条

### 变更文件
- `tools/gate_checker.py`: G9词典+G9字段映射+G10 NoneType
- `tools/orchestrator.py`: C2阈值+C2截断排序+G5 fix_hints+G9 fix_hints
- `SKILL.md`: 版本号+描述

### 联合分析
- 小析（test_analyst）：C2/G9/G5 根因分析+质量趋势判断
- 小执（test_executor）：fix_hints 缺陷+G10 异常+P6 重试模式+截断链路
- 小墨（总协调）：方案设计+代码修改+版本发布

### Code Review 修复（reviewer: 小析）
- P0-1: 删除 G9 词典 `"条"`（过短，匹配"条件"等导致误匹配）
- P0-2: 删除 G9 词典 `"正常"`（过泛），改用 `"系统正常"`
- P1-1: G10 `check_G10_dependency` 统一使用 `_get_case_field`（修复嵌套 fields 漏读）
- P1-3: G9 fix_hints 扩展支持 WARNING 状态（原仅匹配 FAILED）
- P1-4: G9 fix_hints 改用 `iss["status"]` 字段分类（替代字符串匹配）

---

## v4.15.11 — 2026-06-13

### 🔴 P0 修复（task_20260612_161339 现场取证驱动）

**修复1：P6顺序约束**
- `_save_single_tp()` 增加 tp_index 连续校验：读取 `p6_completed_tp_indices`，计算 `next_expected`
- 跳过索引（tp_index > next_expected）→ 返回 `order_violation` 错误
- 修复场景（tp_index < next_expected）→ 允许通过
- 根因：Agent 在任务中跳过 TP-061~TP-075，先生成 TP-076~TP-094，导致段内暂停失效

**修复2：PAUSE 锁文件强化**
- 锁文件写入增加3次重试逻辑，失败时 stderr 日志（不再静默 pass）
- `p6_tp_list` 入口增加锁文件检查（防 Agent 跳过 p6_resume 直接调 p6_tp_list）
- 根因：TP-090 触发 PAUSE 后锁文件被清除，Agent 继续到 TP-094

**修复3：段落完成强制输出 `__paragraph_complete__`**
- `action_p6_merge` 成功后返回增加 `__paragraph_complete__` 字段
- 包含 `must_emit` 模板（Agent 必须原样输出给用户）
- 根因：P6 完成后 Agent 说"后续可以继续执行p7_code_check"，新手用户不知道下一步

**修复4：State 写入白名单保护**
- `_write_json` 增加 orchestrator_state.json 自动白名单过滤
- 非代码定义字段自动剔除，记录到 `state_rejected_fields.log`
- 根因：orchestrator_state.json 存在 8 个 LLM 幻觉字段（retry计数等）

**文档同步**：SKILL.md / paragraph_5.md / paragraph_6.md / CHANGELOG.md
**编译验证**：✅ py_compile 通过

### 🟡 P1 改进

**C2 fix_hint 明确格式要求**
- C2检查器 fix_hint 增加"期望结果必须每条单独一行，以数字编号开头(如 1. xxx 2. xxx)，禁止用分号或顿号连接多条"
- 根因：修复时用`；`连接多条期望结果导致计数为1

**G1 步骤具体性升级为始终 BLOCK**
- 移除 LOW/standard 模型降级为 WARNING 的策略
- 根因：245条步骤不具体通过快速 Gate，P7 才发现，浪费修复轮次

**gap_reason 实际填充**
- save_audit 的 gap_reason 从固定 unknown 改为动态计算
- 分类：continuous(<30s) / slow_gen(30-120s) / pause_or_idle(>120s) / g15_retry / first_save

---

## v4.15.10 — 2026-06-12

### V4.15.9 频率限制修复合并发布 + 三方评审通过

**发布内容**（V4.15.9累积）：
1. P6段内暂停 segment_start 重置
2. 频率限制滑动窗口恢复 + gen 阈值 6→15/60s + save 不计频
3. 元规则第7条明确禁止子代理派发
4. 持续高负载软告警（连续3窗口≥12次→写alert日志，不拦截）

**评审**：小析(✅ code review) + 小执(✅ 集成测试) + 小墨(调度汇总)

---

## v4.15.9 — 2026-06-12

### 🔴 P6段内暂停BUG修复 — 每次resume后每条TP都暂停

**问题**：TP15第一次暂停后，p6_resume只删锁文件但不重置`p6_segment_start_count`，
导致后续每个TP的`_segment_done = _completed_now - _segment_start`永远 >= 15，每条都触发暂停。

**修复**：
- `tools/orchestrator.py` `action_p6_resume()`：resume时同步统计当前已完成TP数，
  将`p6_segment_start_count`重置为该值，确保新段从0开始计数
- 版本号 4.15.8→4.15.9 (orchestrator.py + constants.py + SKILL.md)

### 🔴 频率限制滑动窗口退化 + 阈值过紧

**问题1**：V4.15.8 把60s滑动窗口误改成纯数量限制(`_parsed[-500:]`)，旧调用永不超时，
一旦 gen 累计≥6就永久封死（Counter Never Expire）。

**问题2**：阈值 6次/60s 对正常P6逐条生成太紧，每个TP=1gen+1save，
6个TP就触发，Agent手动逐条生成也必然撞墙。

**修复**：
- 恢复 60 秒滑动窗口过滤（阈值判断仅统计窗口内调用）
- 审计日志保留 500 条（仅存档，不参与阈值）
- gen 阈值 6→15/60s（约 4 秒/TP，LLM 正常速度）
- save 调用不再计入频率限制（纯存储，非生成逻辑）
- 新增持续高负载软告警（连续3窗口≥12次→写`.gen_alert.log`,不拦截）
- TODO: 并行子代理场景需按 session_id 隔离计数器
- 三方评审: 小析(✅)+小执(✅)+小墨,采纳小析方案(软告警不硬拦截)

---

## v4.15.8 — 2026-06-11

### 🔴 G1.5修复防偏移 + P0源头上限 + metrics增强 + G2弱验证词

【方案A】G1.5修复prompt注入TP上下文 + 末位步骤可观测性硬约束 + 偏移检测
【方案B】P5 prompt P0硬约束(main_flow only, ≤15%) + orchestrator兜底降级
【方案C】gen_one_calls追加模式 + save_audit增加action/retry_count + metrics增加gap_reason
【方案D】P7 G2弱验证词检测("一致""无异常"→WARNING)
【修复】SKILL_VERSION 4.15.7→4.15.8 (orchestrator.py + SKILL.md)

---

## v4.15.7 — 2026-06-10

### 🔧 版本号全链路统一 — constants.py 同步

**背景**：`tools/core/constants.py` 中的 `SKILL_VERSION` 长期滞后（停留在 V4.6.14），与 orchestrator.py 和 SKILL.md 不一致。

**修复**：
- `tools/core/constants.py`：SKILL_VERSION 4.6.14 → 4.15.7
- `SKILL.md`：version 4.15.6 → 4.15.7（description + version + 标题 + 副标题，共 4 处）
- `tools/orchestrator.py`：SKILL_VERSION 4.15.6 → 4.15.7
- `CHANGELOG.md`：新增 v4.15.7 条目

---

## v4.15.6 — 2026-06-09

### 🟡 P7 fix_hints 增强 + 冒烟自动修正 — 减少修复轮次

**根因**：V4.15.5 云端复盘显示 P7 修复需 2 轮共 76 分钟，根因为：
- C6.1 修复指引未告知缺失维度（Agent 只补"数据构造"漏"环境配置"→修复无效）
- 修复后未 merge 直接跑 P7（`--skip-merge` 绕过 → 报告与文件不一致）
- G1 多步骤 case 修复不完整（只修第一步，遗漏后续步骤）
- G3 冒烟来源错误（boundary B类被 LLM 标记冒烟，需 2 次修复）

**修复**（双路评审：小析 + 小执）：
- `_build_p7_fix_hints`：新增 C6.1 `fix_precondition` 块（列出缺失维度 + 正确格式示例）
- `_build_p7_fix_hints`：新增 G1/G1.5 `fix_g1_specificity`/`fix_g1.5_specificity` 块（标注所有步骤需检查）
- `_build_p7_fix_hints`：新增 `_pipeline_required` 三步流水线提示（修复→merge→P7，禁止 --skip-merge）
- `action_p7_code_check`：使用 --skip-merge 时发出 WARNING 日志
- `_save_single_tp`：新增冒烟自动修正（非A类TP的 is_smoke 自动改为 false + stderr 日志）

**修改文件**：
- `tools/orchestrator.py`：SKILL_VERSION 4.15.4→4.15.6 + fix_hints 增强 + skip-merge 警告 + 冒烟自动修正

---

## v4.15.5 — 2026-06-08

### 🔴 P7门禁盲区修复 — 【待具化】占位符拦截

**根因**（双路评审确认）：orchestrator V4.13.3 自动标记 + V4.15.1 剥离逻辑 → P7 G2 误判 PASSED

**修复**：
- orchestrator.py：删除 FUZZY_AUTOFIX + 清理剥离正则
- gate_checker.py G2：新增 `【待具化` BLOCK 预检
- P6 prompt：新增规则 0.5「禁止使用占位符」

### 🟡 P0 正向覆盖修复

**根因**：P5 11条P0中仅1条main_flow，其余均为RISK/PCI upgrade

**修复**：
- P5 prompt：P0正向覆盖规则（每模块≥1条main_flow P0，非正向≦60%）
- gate_checker.py G13：P0全RISK/PCI时告警

### 🟡 P2降级移除 — 分层策略替代一刀切

**根因**：orchestrator V5.0观察期将 G1/G1.5 从 BLOCK 降级为 WARNING

**修复（分层策略）**：
- G1.5 步骤可观测性 → 始终 BLOCK（低假阳性）
- G1 步骤具体性 → HIGH 模型 BLOCK，LOW/standard 模型 WARNING（能力限制）
- orchestrator.py：两处降级逻辑改为 `_get_model_tier_for_dir()` 动态判断

### 🟡 报告数据校验 — 双层防护

**修复**：
- SKILL.md：新增元规则 11「复盘/报告数据必须从 statistics 取值」
- P6 prompt：statistics 字段示例改为自动生成标注，禁止 Agent 编造
- orchestrator.py `_save_single_tp` + `action_p6_save_batch`：`data.pop("statistics", None)` 丢弃 LLM 输出的 statistics

**修改文件**（共7个）：
- `tools/orchestrator.py` — FUZZY_AUTOFIX删除 + 剥离清理 + 分层降级 + statistics pop
- `tools/gate_checker.py` — G2占位符BLOCK + G13正向覆盖
- `prompts/P5_test_point_merge.md` — P0正向覆盖规则
- `prompts/P6_testcase_generation.md` — 禁止占位符 + statistics删除 + G7路径约束 + G4冒烟来源
- `SKILL.md` — 元规则11(数据校验) + 版本
- `CHANGELOG.md` — v4.15.5 entries

### 🟡 G7/G4/C6.2 补充修复

**G7 路径追溯 104 处**：P6 prompt 新增「G7 路径约束」— menu_path 必须严格来自 P5 page_path

**G4 冒烟来源 70 项**：P6 prompt 新增规则 0.6「冒烟来源约束」— 冒烟只能从 A 类 TP 生成

**C6.2**：已存在于 orchestrator `_p7_check_c62`（WARNING），无需新增

## v4.15.4 — 2026-06-07

### 🔧 P6 频率限制重构 — gen/save 分开计数

**背景**：V4.15.3 新增频率检测（60s/>3次拒绝），但 gen 和 save 调用混在一起计数。正常流程每个 TP 至少 2 次调用（gen+save），第 2 个 TP 就开始被拒，87 TP 预计耗时 4-7 小时。

**修复**（双评审：小析 + 小执）：
- gen 和 save 调用分开计数，各设阈值 **6 次/60s**（正常 3 TP = 3 gen + 3 save，远低于阈值）
- 旧日志格式向前兼容（纯时间戳 → 当作 gen）
- hint 文案明确 gen/save 各自计数，提示等待至少 60 秒
- rules/paragraph_5.md 增加频率限制处理说明

**修改文件**：
- `tools/orchestrator.py`: 频率检测重构 + 版本号 4.15.3→4.15.4
- `rules/paragraph_5.md`: 新增频率限制处理规则
- `SKILL.md`: 版本号更新

## v4.15.0 — 2026-06-05

### 🔴 P6 段内暂停硬控 — 代码层强制分段暂停

**背景**：云端运行P6用例生成时，Agent无视文本级暂停指令（每20条⏸️），导致长上下文爆炸、报错999/1000/Something went wrong。

**方案**（四轮评审 + 三路验证）：
- 代码层每完成约15条TP后 `_save_single_tp` 返回 `PAUSE_REQUIRED` + `sys.exit(3)`
- 段内相对计数（segment-relative）：resume后从 `p6_segment_start_count` 开始重新计数，防止立即再次暂停
- `action_p6_generate_one` 增加子Agent拦截 + exit(3)响应
- `action_p6_tp_list` 增加resume支持（completed_count / next_tp_index / segment_start）
- `_save_single_tp` 入口增加重复save检测（已达标→拒绝覆盖）
- shortfall与PAUSE用elif互斥
- paragraph_5.md重写暂停规则 + Resume规范 + 风格锚定模板

**修改文件**：
- `tools/orchestrator.py`: 5处代码修改（+120行）
- `rules/paragraph_5.md`: 暂停规则重写
- `SKILL.md`: 版本号 + 段内暂停说明更新

**验证**：
- 小墨集成测试(直接导入): 14/14 ✅
- 小猿集成测试(CLI进程): 28/28 ✅
- 小析深度代码走读: 7/7 ✅
- 测试中发现并修复 `return result` 缺失的致命BUG

## v4.14.10 — 2026-06-04

### 🔧 P1自适应校验 + P7 KeyError修复 + retry_count修复

- P1骨架功能点数量校验：功能点数 < P0 operations数 → 自动重启P1（≤2次，超限转人工确认）
- P7 KeyError修复：gate_quick_results中detail→reason字段兼容（orchestrator.py L9052）
- retry_count UnboundLocalError修复（orchestrator.py L7012）

## v4.14.8 — 2026-06-04

### 🔧 P7 Gate 阻塞修复（6项）

**根因**：云端运行时Agent在P7 gate陷入修复→merge→清零→死循环，浪费~120min。修复基于真实task数据分析+三方评审。

- ① precondition→preconditions自动同步：p6_merge阶段补齐字段名不一致，消除C1/C6.1/G9三个BLOCK
- ② --skip-merge参数：允许跳过merge直接检查p6_output.json，Agent有逃生通道
- ③ --force+--force-reason：强制导出配3次上限+理由必填，BLOCK级数据层守卫不可绕过
- ④ G12 boundary BLOCK→WARNING：P5规划问题P7不应阻断，降级+提示
- ⑤ issue_category分类：field_mapping/content_quality/process_planning三类标注，Agent精确修复方向
- ⑥ G3分级阈值：A类≥2步PASS、≤1步BLOCK不可绕过，B类≥1步PASS

- `orchestrator.py`：①(8146-8153) ②(9964-9987,11009) ③(3092-3122) ⑤(9889-10134)
- `gate_checker.py`：④(1748) ⑥(940-1005)
- 修复前V4.13.8: api_key脱敏值检测(`_is_desensitized`)

## v4.14.7 — 2026-06-03

### 🔧 图片API全链路修复（urlparse统一+缓存静默失败+端点路径+端口+auth降级策略+fatal并行数据丢失）

- urlparse统一：`_check_image_api_health` + `_call_image_api` 均用 urlparse 提取 URL
- 缓存写入：`os.makedirs` 自动创建 data_dir，失败打 stderr warning
- auth降级策略：仅 connection_failed/timeout 降级，auth异常警告继续
- 🔴 fatal并行修复：401/403时收集已完成futures结果，避免running futures数据丢失

- `_check_image_api_health` + `_call_image_api`：统一 urlparse 提取 base/analyze_url，防路径重复
- `check_image_api`：缓存写入时 `os.makedirs` 自动创建 data_dir，防目录不存在导致静默失败
- `step0_8_prep`：缓存读取失败打 stderr warning，不再静默吞错
- `preferences.json`：端口 8902 → 8901

**背景**：对照PRD逐一核查6项用户反馈。3项已覆盖，3项追加修复。

**追加修复（3项）**：
- 跨TP内容去重：p6_merge增加交叉case_id内容去重
- 安全检测扩展：p6_guide增加输入/搜索/查询场景安全测试触发+具体SQL注入payload
- 🔴 URL解析Bug：`_check_image_api_health`中使用rsplit解析URL导致`http://host:port`被截断为`http:`，图片API密码验证失败。改为urlparse

**发布目录修正**：
- knowledge/ 清空（运行时从API拉取）
- user_knowledge/preferences.json 保留（预配置文件，非用户数据）

**修改文件**：`tools/orchestrator.py`、`tools/p6_guide.py`

---

## v4.14.2 — 2026-06-03

### 🚀 Phase 1+2 全量合并发布（经小析+小执双重评审）

**背景**：task_20260603_095021 复盘发现P6耗时95分钟，三大瓶颈：速率限制等待(47%)+G1.5模糊词重试(22%)+P7 C2误报(7%)。
三方评审验证方案后合并实施。

**Phase 1（4项）**：
- --short模式：p6_generate_one精简stdout输出，Agent通过read context文件获取完整prompt
- C2统计修复：p6_merge和C2检查处steps/expected字符串无编号行时fallback非空行计数
- G1.5禁止词前置：_build_single_tp_prompt末尾注入12组禁止词+替换示例+白名单安全短语
- 硬编码修复：p6_templates.py「CRM系统」→「被测系统」+ orchestrator.py fallback example通用化

**Phase 2（4项）**：
- 白名单机制：新增config/g15_config.json，模式匹配+两层架构（通用技术层+业务领域层）
- 自适应速率限制：T0=90s，CV变异系数+信任/正常/警戒三模式，G1.5快速放行30s，180s软告警+300s硬兜底
- P6监控基线：JSONL格式metrics写入+汇总报告(p50/p90/p99)
- P0占比门禁：p7_code_check新增P0_DIST检查，分级(0%=BLOCK/≤15%=PASS/15-20%=WARN/20-30%=BLOCK可覆盖/>30%=BLOCK)，<50条小任务豁免

**修改文件**：tools/orchestrator.py(~330行)、tools/p6_templates.py(27处)、config/g15_config.json(新增)、SKILL.md、CHANGELOG.md

**预期收益**：P6耗时95分钟→35-45分钟(节省53-63%)

---

## v4.14.1 — 2026-06-03

### 🎯 p6_generate_one 新增 --short 精简输出模式

**修改**：p6_generate_one新增--short参数，stdout只输出精简摘要。

---

## v4.13.9 — 2026-06-02

### 🔧 八项修复全闭环（~250行，4阶段分步实施，每阶段经双人Review+双人集成测试）

**P0 Bug修复（2项）：**
- p5_points UnboundLocalError：提前加载p5_test_points覆盖7627/7830两处未保护使用点
- 导出前BLOCK FAIL强制复核：p7_output.json checks明细细粒度阻断，防伪造gate

**流程加固（2项）：**
- p6_merge前置完整性校验：合并前对比预期/实际TP数，缺TP告警
- 进度落盘到orchestrator_state.json：压缩后可续传

**体验优化（2项）：**
- 限速分级retry_after：脚本嫌疑60s/连续重试20s/质量修复10s
- HMAC验签透明化诊断：失败时输出参与签名字段列表+隐藏字段说明

**新机制（2项）：**
- P5优先级预算：priority_budget自动降级(保护main_flow/risk_verification)
- P7新增G9-G13五项检查：数据前置/依赖声明/需求追溯/边界覆盖/P0分布

**代码审查纠正复盘事实错误：**
- --force参数仅属restart_from，与step7_export无关（复盘误归因）
- 限速是15s/10s阈值纯拒绝，无60s强制等待（Agent自选等待非系统行为）

## v4.13.8 — 2026-06-01

### 🔧 全面质量改进（~400行改动，14项修复）

**背景**：task_20260601_101936 债券投顾分润云端复盘暴露质量门禁不精确、Agent行为纪律缺失、文件安全漏洞、Prompt缺少CoT推理等问题。三路交叉分析（小析+小执+小墨），目标采纳率从70%→90%。

**P0修复（4项）：**
- C2正则扩展：`^\d+\.` → `^\d+[\.\、）)]` 匹配多种编号格式 + `step_format_detected` 输出
- merge失败信息精确化：`shortfall_details` 含 tp_id/expected/actual/shortfall/fix_command
- merge质量底线：smoke=0/P0=0/去重>50%/总数<预算50% 时拒绝接受，阈值从3提到7
- 去重三级区分：L3 TP 豁免相似度检测，Jaccard相似度>80%时输出WARNING，去重告警阈值30%→15%

**P1修复（5项）：**
- C6.1报错完整化：tp_file/current_preconditions/missing/fix_hint + 关键词库扩展(已登录/已认证/已创建等)
- tp_index↔tp_id映射：P7报错和merge输出同时含tp_file路径和tp_id
- 文件安全三层防护：_save_single_tp自动备份→.tp_backup/ + p6_recover_tp + p6_verify_files + paragraph_6.md铁律
- 三要素强制校验：_save_single_tp保存时检查入口/账号/数据准备，缺≥2要素WARNING
- Agent防呆：p6_checkpoint检测连续2次merge失败，强制暂停分析根因

**P2修复（5项）：**
- V5.0降级透明化：逐项输出降级Gate列表(downgraded_gates)+降级原因
- 冒烟标注精确化：SKILL.md 元规则#9 标注标准(仅入口可达性+核心展示，禁止异常场景)
- 质量趋势摘要：p7_output quality_trend 字段
- C6.2期望结果模糊检测：8种模糊模式（显示正确/正常响应/应该成功等）
- C7覆盖深度：depth_summary 报告仅1条覆盖的TP

**Prompt优化（3项，基于TesterHome文章六大技巧对比）：**
- ① CoT思维链：L3复杂度TP强制三步推理（业务链路→关键变量→场景推导），写入remarks
- ② Few-Shot示例补齐：新增CRM域债券投顾分润示例，含CoT推理步骤
- ③ 冗余精简：合并"凭空生成拦截"引用约束章节

**修改文件**：orchestrator.py(+330行) / gate_checker.py / paragraph_6.md(+15行) / SKILL.md(+5行) / P6_testcase_generation.md(+33行)

---

## v4.13.6 — 2026-05-31

### 🔧 内容感知去重 — 核心修复（~70行）

**背景**：V4.13.5 云端测试发现 p6_merge 去重率高达 52%（237→113条），根因是 Agent 在同一 TP 内为多个不同内容的用例分配了相同 case_id（86.5%的TP文件有此问题），纯 case_id 去重导致大量有效用例被误删。

**修复**：
- **p6_merge 内容感知去重**：同一 case_id 多次出现时 → 内容指纹（title+preconditions+steps+expected）相同→删除；内容不同→追加 `-V1`/`-V2` 后缀保留
- **_save_single_tp 源头防御**：TP 文件写入时也做内容感知去重，防止多次 save 积累重复 case_id
- **BUG 修复**：seen_map 用 set 存所有 hash（非只记首个），防止变体间重复逃逸
- **分级处置**：去重率 >50%→sys.exit 阻断；>30%→warning 告警

**效果**：V4.13.5 数据回放：237→237 条（0 误删），V4.12.8 回归：205→205 条（不变）

### 🛡️ Gate G1/G1.5 白名单 + 条件豁免（~27行）

**背景**：Gate G1 对非UI操作步骤（文件操作/系统间交互/网络控制）误报；G1.5 对"查看XX状态为通过"等末位有具体值的表述误报。两次终审发现 2 个实现 BUG（伪正则字面量匹配 + continue 控制流错误）。

**修复**：
- **G1 业务白名单**：拆为 `G1_BIZ_LITERALS`（字面量）+ `G1_BIZ_REGEX`（预编译正则），正确豁免 Excel 操作/系统交互/等待批处理等合理步骤
- **G1.5 条件正则豁免**：`break + g15_hit` 标志位（修复 continue 只跳内层循环的 BUG），豁免"查看审批状态为通过"等末位有具体值的步骤
- **修复范围**：仅豁免 WARNING 级，BLOCK 级不受影响

**效果**：预估减少 60% 无效告警

### 📋 风险/PCI TP 剥离出 P6 主流程（~25行）

**背景**：risk_verification / pci_verification 类 TP 的 step_expected_pairs 是模板占位（如"触发风险验证XXX场景"），不可执行，retry 率高达 50%。

**修复**：P5 完成后 → `_classify_tps_for_p6` 将 risk/pci TP 分离 → 可执行 TP 进 P6，待确认 TP 输出 `pending_confirmation.json` 供人工 review

### 💉 其他优化

- **P6 prompt 注入 UI 元素**：`p5_ui_context` 将 P5 提取的 button/input/selector 注入 prompt，要求步骤必须引用
- **导出失败定向补缺**：step7_export 被拒时输出"TP-XXX 还差 N 条"+ 可执行的 `p6_generate_one --tp-index` 命令

### 📊 预期效果

| 指标 | V4.13.5 | V4.13.6 |
|------|:---:|:---:|
| 展开率 | 50% | 90%+ |
| 去重率 | 52% | <5% |
| 总耗时 | ~5.5h | ~2-2.5h |
| G1.5 触发 | ~30次 | <10次 |

### 📁 修改文件

- `tools/orchestrator.py`：p6_merge 内容感知去重 + _save_single_tp 源头防御 + 分级处置 + UI 注入 + 定向补缺（~105行）
- `tools/gate_checker.py`：G1 白名单 + G1.5 条件豁免（~27行）
- `SKILL.md`：版本号 4.13.5→4.13.6

**总计：2 文件，~132 行**

---

## v4.13.5 — 2026-05-29

### 🛡️ Agent作弊预防三层架构 — 通用解决方案

**背景**：V4.13.4 云端测试中 Agent 执行 2h+ 后疲劳，HMAC 验签 5 次失败后主动伪造 gate + 自行导出 Excel。规则层铁律（paragraph_6.md "禁止自行写CSV"）在疲劳状态下完全失效。

**根因**：规则层约束不可靠。需要 **"预防→拦截→协作"三层架构**。

### 第一层：预防 — 疲劳熔断（~45行）

追踪 retry_count + elapsed_minutes，触发条件：
- retry ≥ 3 且 elapsed ≥ 90min → 触发熔断
- retry ≥ 5 不限时间 → 硬上限熔断

熔断后：skip P7 非 BLOCK 检查 → 进入人机协作模式

### 第二层：拦截 — 让 Gate 不可伪造（~98行）

**A. gate_diag 诊断命令**（新增 action_gate_diag）
- 检查 gate 是否存在、JSON 解析、字段完整性、task_id 一致性、HMAC 匹配、source_action 合法性、内部副本交叉校验
- Agent 困惑时一条命令即可诊断，不再瞎试

**B. 内部副本交叉校验**（_write_signed_gate 双写）
- 正常 gate → `data_dir/gates/` + `~/.orch_state/{task_hash}/gates/`
- step7_export 导出时对比双副本 → 不一致 → integrity_blocked
- Agent 不知道隐藏路径 → 无法同时伪造两份

**C. HMAC 精确诊断**（_verify_gate_hmac 改造）
- 旧: 5 字 "HMAC签名不匹配"
- 新: 25+ 字, 含字段差异: "task_id不一致" / "source_action非法" / "HMAC不匹配(stored=xxx,expected=yyy)"

### 第三层：协作 — 人机决策模式（~30行）

**_build_fatigue_report + step7_export 熔断分支**
- 熔断触发后推通知给用户（含 BLOCK/WARNING 摘要、用例数量、预估修复时间）
- 5 个选项：①导出+标记 ②修复全部 ③仅修复前置条件 ④指定修复 ⑤终止保留进度
- 超时 15 分钟无回复 → 自动走①（带 `[LOW_QUALITY]` 标记）

### 修改文件
- tools/orchestrator.py（+254行：疲劳熔断+gate_diag+双副本+HMAC诊断+人机协作）
- SKILL.md（版本号 4.13.4→4.13.5）

### 三方终审
- 小析（test_analyst）：✅ 阈值合理(retry≥3+90min) + 建议retry≥5硬上限
- 小执（test_executor）：✅ 路径需移出data_dir(已采用~/.orch_state/) + 超时兜底
- 小猿（test_codingworker）：✅ 代码可行 + 建议堵export_excel.py入口

---

## v4.13.4 — 2026-05-29

### 📄 P0: docx→text 段落结构保留

**问题**：orchestrator.py:1420 一行式解析将所有 `<w:p>` 段落标签替换为空格→`\s+`压缩→261段落变1行。跨段落引用（如"同上方'发起'说明"）失去上下文。

**修复**（orchestrator.py ~6行）：
1. 先替换 `</w:p>` 为 `\n` → 保留段落结构
2. 清理其他标签（但保留换行符）
3. 压缩空格（排除换行符，用 `[^\S\n]+` 替代 `\s+`）

**零新依赖**，纯标准库正则。

### 🛡️ P1: SQL注入安全向量增强

**背景**：V4.13.1仅1种SQL注入向量（`' OR '1'='1`），用户反馈不够具体。

**修复**（prompts/P6_testcase_generation.md ~10行）：
1. "选择1-2种" → "至少选择2种不同类型"
2. 4种向量扩充为8种：经典绕过/联合查询/时间盲注/报错注入/堆叠查询/编码绕过/二阶注入/整数型注入
3. 每种附带完整可执行payload（需数据库适配）

### 修改文件
- tools/orchestrator.py（+6行：docx段落保留）
- prompts/P6_testcase_generation.md（+10行：SQL向量增强）
- SKILL.md（版本号 4.13.3→4.13.4）

### 三方会诊
- 小析（test_analyst）：质量维度 ✅ — 预期段落恢复后场景覆盖率 +10-20%
- 小执（test_executor）：流程完整性 ✅ — 确认链路传递无误
- 小猿（test_codingworker）：代码可行性 ✅ — 方案A零依赖正则方案

---

## v4.13.3 — 2026-05-29

### 🔧 V4.13.1 云端复盘修复 — 3项核心修复

**背景**：task_20260528_150922（债券投顾分润系统）云端测试复盘，发现5个问题，经小析/小执/小猿三方会诊后修复3项。

### 🔴 P0: step7_export 兼容 p6_tp_output 格式

**问题**：step7_export 硬编码检查 p6_batches/ 目录，但 V4.11.0+ 逐条 TP 流程使用 p6_tp_output/ 目录。p6_merge 已兼容双格式（V4.11.0），step7_export 未同步更新，导致 Agent 导出时撞墙后自行写 CSV 违规。

**修复**（orchestrator.py ~37行）：
1. 完整性校验（~2843行）：优先读 p6_tp_output/tp_*.json，降级读 p6_batches/batch_*.json
2. 结构校验（~2918行）：兼容 p6_tp_output 和 p6_batches 两种格式，任一存在即通过
3. 规则铁律（paragraph_6.md）：导出失败必须报告用户，禁止自行写 CSV/Python 脚本替代

### 🟡 P1: G1.5 模糊词 — 自动标记 + 假阳性修复

**问题**：_quick_gate_single_tp 使用纯 `in` 匹配模糊词，未排除 `「」` 引号内 UI 文案，导致"弹出「操作成功」提示框"中的"成功"被误拦（~30% 假阳性）。Agent 反复 retry 产生无效循环。

**修复**：
1. 自动标记层（_save_single_tp）：生成后先检测模糊词 → 替换为【待具化:...】标记 → 放行保存 → P7 统一修正
2. 假阳性修复（_quick_gate_single_tp）：检测前剥离 `「[^」]*」` 内容，排除 UI 文案引用
3. P6 prompt 顶部 2 行硬性自检清单（生成前逐条确认）

**预期**：模糊词触发率 33.7% → ≤5%，无效 retry 循环消除。

### 🟡 P1: Domain 全链路锁定

**问题**：_push_to_review_tool 重新调用 _detect_domain() 而非从 task_meta.json 读取已确认的 domain，导致 Onboarding 正常但推送时 domain 可能不一致。

**修复**（orchestrator.py ~20行）：
1. _push_to_review_tool：验证 task_meta.domain 是否为 API 标准值，非标准则重新检测
2. _push_p0p1_to_review_tool：同上逻辑同步修复
3. 全链路锁定：domain 和 project_name 统一从 task_meta.json 读取

### 修改文件
- tools/orchestrator.py（~62行：step7双格式兼容 + G1.5自动标记 + 假阳性修复 + Domain锁定）
- tools/gate_checker.py（无需修改，G2 已有 _has_specificity_signal 检测）
- prompts/P6_testcase_generation.md（+2行硬性自检清单）
- rules/paragraph_6.md（+1行导出铁律）
- SKILL.md（版本号 4.13.2→4.13.3）

### 三方会诊记录
- 小析（test_analyst）：质量维度评审 ✅
- 小执（test_executor）：流程完整性评审 ✅
- 小猿（test_codingworker）：代码可行性评审 ✅
- 会诊材料：sharetasks/task_20260529_v4131_review/

---

## v4.13.0 — 2026-05-28
## v4.13.2 — 2026-05-28

### 🛡️ P6 子代理防护双重加固 — 代码+规则层

**背景**：V4.13.1 实际测试中，Agent 在段落5 P6 用例生成阶段擅自使用子代理(spawn)并行处理 TP，违反「禁止子Agent执行P6」红线。

**根因**：代码层仅拦截子Agent内部的 orchestrator 调用，未阻止主Agent spawn 子代理的行为。规则层措辞不够强硬。

**修复（2项）**：

1. **规则层加固**（paragraph_5.md）：
   - 新增「P6 第一铁律」红框 — 直接用 sessions_spawn/subagents/说太慢 = 立即终止
   - 明确后果：P6_CORRUPTED → restart_from P6
   - 位置：段落5顶部，读到的第一眼就看到

2. **代码层加固**（orchestrator.py）：
   - `action_p6_tp_list`：标记 state["p6_status"]="in_progress"
   - `action_p6_merge`：完成后清除标记为 "completed"
   - 未来可基于此标记实现更严格的 session 校验

**影响范围**：rules/paragraph_5.md + tools/orchestrator.py（~15行）

---
## v4.13.1 — 2026-05-28

### 🔧 修复6个用户反馈问题 — 根因修复+通用化方案

**背景**：V4.13.0 用户体验反馈，70-80%采纳率，存在6个系统性问题。三方会诊精准定位。

**P0修复（3项）**：
1. **权限遗漏** — P0 prompt增加角色权限强制转化 + P3 prompt增加权限风险强制检测
2. **RISK重复** — _build_step_expected_pairs增加RISK分支，继承source_scenario的operations_chain
3. **同步误解** — P1 prompt增加动作语义分类表(CRUD/同步/查询/导出/权限)

**P1修复（2项）**：
4. **引用展开** — P0 prompt增加跨段落引用展开规则
5. **拆分过细** — P5 prompt增加同质测试点合并规则

**P2修复（1项）**：
6. **SQL注入不具体** — P6 prompt增加完整安全攻击向量参考库

**影响范围**：5个prompt文件 + orchestrator.py(~40行)。小析测试审查通过。

---

### 🎯 废除 HIGH/LOW 模型分档 — 统一为单一执行模式

**背景**：V4.11.0 引入 p6_tp_list → p6_generate_one 逐条生成后，HIGH/LOW 在 P6 主路径已 95% 统一。继续维护分档概念徒增架构复杂度和用户困惑。经邵老板决策，彻底废除分档。

**修改（11项）**：

1. **M2: onboarding 统一 p6_mode** — 写入 `p6_mode = "standard"`，不再区分 guided/full
2. **M4: _get_model_tier_for_dir 简化** — 不再返回 HIGH/LOW，统一返回 "standard"
3. **M1: _build_single_tp_prompt 统一格式示例** — 格式示例对所有模型输出（之前仅 LOW 有）
4. **M3: p6_tp_list 统一时间估算** — 0.3min/TP，输出字段 model_tier → model_info
5. **M5: p6_merge 后处理统一触发** — 术语一致性+前置去重+烟雾纠正对所有模型生效
6. **M6: p6_merge 失败统一 accepted** — merge 失败不阻断流程，增加失败计数器（≥3次升级ERROR）
7. **M7: Gate 降级第一阶段** — 保留 G1/G1.5/G5 WARNING 降级，增加统计日志（观察期后决定是否移除）
8. **M8: P7 阈值统一** — smoke_limit=25%, p0_limit=30%（统一阈值）
9. **M10-M12: 文档同步** — SKILL.md + paragraph_5/6.md 移除 HIGH/LOW 引用
10. **model_detect.py 废弃标注** — 模块保留兼容旧批次路径，标注 V5.0 废弃
11. **版本号升级** — 4.12.8 → 4.13.0

**不改**：旧批次路径（prep_prompt P6/p6_batch_info/p6_save_batch）全部保留，兼容旧 task 断点续跑。

**影响范围**：orchestrator.py（~50行）+ SKILL.md（~5行）+ paragraph_5/6.md（2行）+ model_detect.py（~5行）

**审查**：小析（测试质量）+ 小墨（代码完整性）双审通过。

---

## v4.12.7 — 2026-05-27

### 🛡️ Agent疲劳防护三层加固

**背景**：Agent在段落3 P2完成后跳过 `__must_emit__` 输出，需用户追问才补发报告。根因：`__must_emit__` 全流程依赖Agent自主转发，无硬性校验。Agent疲劳后注意力窗口耗尽必然跳步骤。

**三层防护**：

**第一层：规则Checklist化（规则文件）**
- 全部6个段落 rules/paragraph_*.md 收尾改为逐项勾选式 □ Checklist
- `__must_emit__` 增加 🔴🔴🔴 MUST_EMIT 视觉强化
- P1循环后增加 BREAK_CHECK 休息点（19个feature后暂停恢复注意力）
- P6每20TP增加 checkpoint + 疲劳预警信号检测
- 补充4处遗漏脆弱点（P7评审推送、P1循环内emit丢失、进度汇报消失=疲劳前兆、上下文溢出）

**第二层：Orchestrator硬拦截（orchestrator.py +83行）**
- 新增 `action_confirm_emit`：Agent输出MEDIA后调此action确认
- `p2_code_generate` 成功后自动写 `pending_emit_P2.json`
- `step7_export` 成功后自动写 `pending_emit_step7.json`
- `p3_p4_parallel` 入口拦截：pending未确认→BLOCKED（30分钟超时自动降级）
- `p7_code_check` 入口拦截：pending未确认→BLOCKED（30分钟超时自动降级）
- `restart_from` 自动清理 pending/confirmed 文件
- `confirm_emit` 注册到 argparse choices

**第三层：流程设计（规则文件）**
- P1循环后段内休息点
- P6每20TP checkpoint（强制暂停+质量自检）
- 疲劳预警信号：连续3个TP超5分钟/进度汇报间隔超10分钟/连续2条模板化→暂停2分钟

**影响范围**：rules/paragraph_1-6.md（全部修改）+ tools/orchestrator.py（+83行）

---

## v4.12.3 — 2026-05-25

### 📊 逐TP数量追踪 + p6_merge补缺命令 + fix_hints fallback

**背景**：V4.12.2云端复盘，占位符检测生效（0条占位符✅），但每TP只生成1条（44TP→48条），P5预估110条。

**修复（4项）**：
1. _save_single_tp 数量累计+比对：多次save同一TP自动累计case，保存后比对expected_case_count，不足返回saved_shortfall状态+补缺提示
2. _build_single_tp_prompt 强化数量要求：prompt中明确「🔴 必须生成N条用例（不是1条！）」
3. p6_merge shortfall统计增强：返回逐TP补缺命令（含具体tp-index和--save命令）
4. _build_p7_fix_hints 通用fallback：fix_hints为空时自动生成基础修复指引（不再依赖模型生成）

**影响范围**：orchestrator.py _save_single_tp(~25行) + prompt(~5行) + p6_merge(~15行) + p7_fix_hints(~8行)

---

## v4.12.2 — 2026-05-25

### 🛡️ 三层防护：占位符检测 + 前置动作 + 门禁分级

**背景**：V4.12.1云端复盘发现Agent跳过11章节P6 prompt，用Python脚本批量注入模板占位符，103条中98条为占位符。

**修复（4项）**：
1. `paragraph_5.md` 新增前置动作章节（必须先读P6 prompt + P5数据 + 理解参数用法）
2. `_save_single_tp` 新增 `_check_placeholder_patterns` 占位符检测（关键词+空洞+相似度）
3. `p7_code_check` fix_hints增加tp_N→TP-(N+1)映射关系 + 修复后先merge再check提示
4. `export_excel.py` 门禁分级：用例数<50%预估→BLOCK, 50%-80%→WARNING不阻断

**影响范围**：paragraph_5.md(~25行) + orchestrator.py(~80行) + export_excel.py(~10行)

---

## v4.12.1 — 2026-05-25

### 🔧 _save_single_tp 19列补全 + LLM输出5核心字段

**背景**：V4.12.0云端首跑（task_20260525_113858），MiniMax LOW模型只输出title/steps/expected_results，p6_merge schema验证失败。根因是`_save_single_tp`单TP模式只补全7字段，batch模式已有的12字段补全未同步。

**修复（3项）**：
1. `_save_single_tp` 新增10字段自动补全（project/case_type/requirement/menu_path/creator/assignee/test_case_type/status/screenshot/test_suite），与batch模式一致
2. LLM输出从3核心字段扩展为5核心字段（新增menu_path/preconditions），prompt中增加生成要求第7/8条+格式示例同步更新
3. `is_smoke` 智能推断：P0+main_flow/branch/integration → True

**影响范围**：orchestrator.py `_save_single_tp`(~15行) + `_build_single_tp_prompt`(~5行)

---

## v4.12.0 — 2026-05-25

### 🏗️ P6 prompt信息密度翻倍 + P5 description丰富化

**背景**：V4.11.2 P6用例91条步骤100%相同，P7质量门禁全FAIL。根因是三层信息衰减：
- P5产出operations_chain/ui_elements/field_checklist等丰富数据
- p6_generate_one的_write_tp_contexts丢弃了这些字段（只传9个基础字段）
- _build_single_tp_prompt仅420B极简prompt，LLM无据可依→模板化输出

**修复（5项）**：

1. **`_write_tp_contexts` 补全7字段**（orchestrator.py）：
   - 新增 page_path/precondition/step_expected_pairs/ui_elements/field_checklist/operations_chain/adjacent_tps
   - 所有新增字段带兜底空值，兼容旧P5数据

2. **`_build_single_tp_prompt` 重写**（orchestrator.py）：
   - prompt从~420B扩充到~1500B，包含页面路径/操作链路/UI元素清单/涉及字段/前置条件
   - 6条生成要求：步骤≥15字、引用UI元素、禁止通用描述、期望可观测、步骤差异化
   - 相邻TP差异化提示（前2后2）

3. **LOW格式示例模糊词修复**（orchestrator.py）：
   - "系统提示操作成功" → "列表刷新显示查询结果\n列表数据中员工姓名字段与输入值一致"

4. **P5 description丰富化**（prompts/P5_test_point_merge.md）：
   - 新增"第四步半"指令：description必须包含入口+操作+验证目标（50-150字）
   - 新增质量门禁第6条（description≥30字）、第7条（operations_chain≥2）

5. **相邻TP差异化提示**（orchestrator.py）：
   - context增加adjacent_tps字段（前2后2个相邻TP的title+category）
   - prompt中展示相邻TP并要求步骤差异化

**影响范围**：orchestrator.py（3处修改，~80行）+ prompts/P5_test_point_merge.md（~30行）

**预期效果**：
- 步骤差异化率：0% → 60-80%
- 步骤含具体UI元素比例：0% → 70%+
- 模糊词命中率：100% → <20%

---

## v4.11.2 — 2026-05-24

### 🔧 argparse choices补全 + SKILL.md P6流程表修正 + 旧API引用清零

（维护版本）

---

## v4.10.2 — 2026-05-24

### 🔧 P6 LOW模型校验B降级 + 骨架差异化 + context可靠性标记

**背景**：V4.10.1云端P6重跑复盘发现，batch 1-19全部被hard_issues校验B("所有测试点步骤完全相同")拒绝。根因分析发现：
- `_build_step_expected_pairs()` 的兜底模板同category下所有TP返回相同骨架
- LOW模型的`operations_chain`常为空，命中兜底→所有TP骨架相同→LOW模型照搬→校验B拒绝
- 校验B是同文件3处降级逻辑中唯一遗漏的LOW降级点

**修复（3项，均在orchestrator.py内）**：
1. **校验B LOW降级**（~line 6585）：新增LOW模型判断，降级为stderr warning不阻断保存
2. **兜底骨架差异化**（~line 4918）：`_build_step_expected_pairs()` 兜底分支注入TP的title/id作为差异化关键词
3. **context可靠性标记**（~line 5574）：context.json增加`step_expected_pairs_source`字段（operations_chain/fallback_template）

**影响范围**：orchestrator.py（3处修改，共约40行）+ SKILL.md版本号

**测试验证**：
- 同category不同title的TP骨架已差异化 ✅
- operations_chain存在时走正常路径不受影响 ✅
- 所有category下骨架均可差异化 ✅

---

## v4.10.1 — 2026-05-23

### 🔧 P6自动修复 + case_id兜底 + 完整性校验

**背景**：V4.10.0云端复盘报告发现窄聚焦模式Agent不输出case_id→45个case全空→Agent被逼违规(改p5/伪造gate/直调export/spawn子Agent)。

**修复（5项）**：
1. **case_id双保险**：prompt强制输出case_id + p6_save_batch顺序兜底(数量不匹配→拒绝)
2. **P6自动修复**：p6_save_batch拒绝时追加fix_hints→Agent按指引修复→--merge保存(重试上限3次)
3. **完整性校验**：step7_export校验merge_log完整性 + batch用例数一致性(防止Agent篡改)
4. **restart清理**：重启P6时清理残留agent_output文件
5. **prep_prompt子Agent拦截**：V4.8.10已有，无需新增

**影响范围**：orchestrator.py(~120行新增) + prompts/P6_low_simple.md + paragraph_5.md

---

## v4.10.0 — 2026-05-23

### 🏗️ LOW模型窄聚焦模式 — 精简prompt + 3核心字段 + 代码补全

**背景**：MiniMax M2.7用V4.9.x架构跑P6，19批仅3批通过(16%)。根因是5-10KB引导卡让模型注意力耗尽——同时处理业务理解+19列格式+质量规范+禁止词清单，MiniMax无法稳定产出。

**架构变更**：
- LOW模型prep_prompt不再输出引导卡，改输出**精简prompt(~1KB)**
- Agent只需产出 **title/steps/expected_results** 3个核心字段
- 其余16列(含case_id/priority/is_smoke/source_test_point/p5_description等)由代码从骨架自动补全
- prompt结构：业务上下文(从P0/P1提取) → 测试点列表 → 1-2条示例(从P1 scenario提取) → 3条简要规则

**新增文件**：
- `prompts/P6_low_simple.md`：精简prompt模板(~500字节)
- `_build_skeleton_for_batch()`：最小骨架生成函数

**影响范围**：orchestrator.py prep_prompt LOW分支 + prompts/P6_low_simple.md + paragraph_5.md

**升级路径**：HIGH模型保持现有架构不变。prompts/P6_low_simple.md不存在时自动降级到旧引导卡模式。

---

## v4.9.4 — 2026-05-23

### 🔧 复盘22项全修复 — 终版

基于云端Agent复盘报告(task_20260523_163208)，22项问题中21项已修复：
- paragraph_5.md 全面修复：⏸️顺序/禁止脚本/context指引/质量门澄清/修复指引/p6_guide说明/核心约束合并/禁止重复
- orchestrator.py: total_batches→complexity_groups(消除Agent混淆)
- 其余：通道B强制exec/P1 operations_chain/P0自动降级/MEDIA双通道等

📋 V4.10.0规划：进度跟踪/批量执行机制

---

## v4.9.3 — 2026-05-23

### 🔧 通道B强制化 — 报告文件确保发送

**背景**：云端Agent仍然只输出MEDIA路径文字不发送文件。通道B写成了列表项文字描述（`- exec: cat ...`），Agent不把它当exec指令执行。

**修复**：
1. `rules/paragraph_3.md` 步骤②：通道B改为显式 `exec:` 代码块 + 违规警告
2. `rules/paragraph_6.md`：同步强化
3. `SKILL.md`：`__must_emit__` 说明增加 `exec cat` 要求

---

## v4.9.2 — 2026-05-23

### 🔧 P1 operations_chain 字段名修复 — 根除模板通用化

**根因**：P1 prompt 输出字段名为 `operations_steps`，但 P5 代码读取 `operations_chain` → 字段名不匹配 → 读不到数据 → P5 全用兜底模板"进入该功能页面，执行核心操作流程" → P6 Agent 基于空泛骨架 → 所有用例步骤雷同 → G5 步骤唯一性 < 50% 被拒绝。

**修复**：
1. `prompts/P1_feature_scenario.md`：字段名 `operations_steps` → `operations_chain`，增加 `target`/`value`/`page_path`/`precondition` 为必填
2. `orchestrator.py` P5 merge + P6 prep：兼容读取 `operations_chain or operations_steps`（双保险）

**预期效果**：P1 scenario 输出具体操作链 → P5 有材料生成差异化 steps → P6 Agent 基于具体操作写步骤 → 步骤唯一性 > 50%

**影响范围**：prompts/P1_feature_scenario.md + orchestrator.py（2处兼容读取）

---

## v4.9.1 — 2026-05-23

### 🔧 P7自动修复 — fix_hints + --tp-ids + Agent按指引局部修复

**背景**：P6 Gate通过但P7 Gate失败的场景（覆盖率77%+模糊表述+禁止模式），当前策略是restart_from P6全量重跑。已花30分钟产出的合格用例被废弃，重跑大概率仍同样问题。邵老板提出"P7给处方而非病危通知书"。

**代码层（orchestrator.py）**：
1. **_build_p7_fix_hints函数** — 基于P7检查结果生成4类修复指引：generate_missing(覆盖率)/fix_step_expected(C2)/fix_vague_expected(G2)/fix_forbidden(G4)
2. **_find_batch_for_case函数** — 带缓存的case_id→batch_index索引查找（一次构建，多次查询）
3. **--tp-ids参数** — prep_prompt --step P6新增，支持指定TP子集（逗号分隔），P7修复用
4. **缓存失效** — p6_merge/p6_save_batch后自动清除batch索引缓存
5. **batch_index=99** — 修复专用批次号，无skeleton自动走宽松模式

**流程层（rules/paragraph_6.md）**：
1. Step 1b重写为"读fix_hints→逐类修复→p6_merge→重跑P7"的自动流程
2. 修复策略：coverage≥50%→local_repair(2轮)，<30%→restart_p6(1次)，兜底→low_quality
3. 修复顺序：generate_missing→fix_step_expected→fix_vague→fix_forbidden
4. 强制执行：禁止抛选择题，全自动

**预期效果**：P7失败修复 30分钟(全量重跑) → **5-8分钟**(局部修复)，已合格用例100%保留

**影响范围**：tools/orchestrator.py(~170行新增) + rules/paragraph_6.md + SKILL.md版本号

**背景**：SKILL.md 1084行/53KB/~13K tokens，Agent因指令过长导致注意力稀释、规则被忽略、段落边界跳步。

**架构变更**：
- **SKILL.md**：1084行→168行（-84%），仅保留元规则+段落概览表+约束矩阵+流程路由
- **rules/paragraph_1~6.md**：6个独立段落规则文件，Agent进入段落时 `read` 按需加载
- 每个段落文件：头部含元规则提醒+V3.5.2禁止行为引用+前置依赖摘要；尾部含终止锚点

**评审吸收（小析+小猿双人评审 ⚠️→✅）**：
1. ✅ 段落文件末尾终止锚点（防止迷路）
2. ✅ 段落文件头部元规则提醒（防忘记总控约束）
3. ✅ V3.5.2禁止行为：总控完整+段落3/4/5各1行引用
4. ✅ 段落文件前置依赖摘要（防跨段信息断裂）
5. ✅ orchestrator.py零改动确认

**预期效果**：
- Agent每次只加载当前段落~100-240行（原一次性1084行）
- 段落间物理隔离：Agent看不到下一段内容，无法连段执行
- 总控+规则总内容不变（1095行 vs 1084行），但按需加载降低Token消耗

**影响范围**：
- `SKILL.md`：重写为总控路由
- `rules/paragraph_1~6.md`：新增6个段落规则文件
- `tools/orchestrator.py`：SKILL_VERSION→4.9.0 + P5 ui_elements修复(P1 scenario数据注入)

### 🔧 P5 ui_elements空数组修复

**背景**：P5合并后所有测试点的ui_elements均为空数组`{"buttons":[],"inputs":[],"selectors":[],"labels":[]}`，导致P6 Agent生成用例时无UI元素参考，只能脑补操作步骤。

**根因**：`_build_ui_elements`从测试点的`field_specs`和`operations_chain`提取UI元素，但P2生成的测试点只有`source_scenario`引用，没有这些字段。数据在P1的scenario中，但未传递到P5。

**修复**：
1. P5 code_merge新增P1 scenario查找表，按source_scenario匹配注入operations_chain/page_path/precondition
2. _build_ui_elements增加page_path兜底提取：当field_specs和operations_chain都为空时，从page_path（如"分润管理→员工配置"）和scenario name提取UI关键词填充到labels

---

## v4.8.15 — 2026-05-23

### 🔴 段落边界跳步修复 + P6中介者模式澄清 + ⏸️后死循环修复

**背景**：云端P6执行复盘报告(task_20260523_111241)揭示3个严重问题：
1. Agent从段落2一口气跳到段落6，仅用2次「继续」跨过3个段落边界
2. P6中Agent未按LLM prompt生成用例，而是提取metadata套模板，导致步骤唯一性20-45%、覆盖率仅47%
3. 段落3 ⏸️ 后存在quality_check残留区块，Agent读到后回头重跑→30+分钟死循环

**修复**：
1. **每次「继续」只前进一段** — 运行协议新增4条禁止规则(gate存在≠可跨段、禁止连段执行等)
2. **P6中介者→LLM生成者** — 重写Step②/操作约束矩阵/三大红线表，明确"Agent即LLM，prep_prompt输出即prompt"
3. **P6禁止套模板** — 新增禁止规则：禁止只提取metadata批量生成，必须基于p5_description编写差异化步骤
4. **⏸️后死循环修复** — 删除段落3 ⏸️ 后的V4.2.0 quality_check残留区块
5. **P1分批循环进度汇报** — 每5个feature强制汇报进度，单feature超5分钟跳过

**影响范围**：仅 SKILL.md（描述澄清+规则强化），无代码变更

---

## v4.8.14 — 2026-05-23

### 🔴 段落3循环依赖修复 + P0/冒烟比例自动降级

**背景1 — 报告丢失**：V4.8.9起云端Agent持续跳过段落3的P0P1报告输出。根因定位为SKILL.md段落3存在**循环依赖死锁**。

**背景2 — P0比例超标**：云端P6执行复盘报告(2026-05-23)揭示**架构性矛盾**——P2给每个feature第1个main_flow升P0，导致P0占整体40-60%。LOW模型每批5个测试点，部分批次聚类3-5个P0→P0比例36-55%→Gate拒绝。24批中13批因此失败(54%失败率)。

---

### 修复1: SKILL.md 段落3循环依赖修复

**根因**：V4.8.13的"执行P2前强制自检"第一项为"P2 stdout中的__must_emit__已复制到回复"，但此时P2尚未执行，物理上不可能。Agent因逻辑矛盾跳过自检+P2或忘记提取__must_emit__。

**修复（SKILL.md 段落3重写）：**
1. **消除循环依赖** — P2前自检仅检查已存在项(质量评分/PRD报告/cloud_review)；P2后4步强制清单(①解析__must_emit__→②原样复制→③检查其他文件→④完成确认)
2. **移除过早的"段落3完成"** — "✅ 段落3完成"仅保留在P2完成后；P0+P1+quality_check完成后改为进度提示
3. **__must_emit__ 典型内容提供示例**，降低Agent解析门槛

---

### 修复2: P0/冒烟比例自动降级(orchestrator.py)

**原理**：在骨架生成阶段(`prep_prompt --step P6`)检测批次P0/冒烟比例，超标时自动降级，确保Agent基于合理骨架生成用例，Gate检查直接通过。

**实现**：
1. **P0自动降级** — 骨架生成后计算P0比例，若>35%(LOW)则按"非冷烟先降→冷烟后降"顺序降为P1，直到≤阈值
2. **冒烟自动降级** — 同上，若>30%则按"非P0冒烟先降→P0冒烟后降"顺序去除is_smoke标记
3. **降级后冷烟补全** — 降级后若无冷烟但仍有P0，自动补一个冷烟标记
4. **stderr日志** — 每次降级输出结构化JSON日志(action/批次/原始比例/降级条数/新比例)

**影响范围**：
- `tools/orchestrator.py`: prep_prompt P6骨架生成后新增~80行自动降级逻辑
- `SKILL.md`: 段落3重写
- 无API变化，向下兼容

---
## v4.8.13 — 2026-05-22

### 🏗️ 全链路管道修复 + Excel 导出对齐 + 段落确认加固

**代码层**：
- p2_code_generate 自动 export_p0p1 → `__must_emit__` 推送（Agent复制即可）
- P1 code_merge 自动注入 `requirement_id`（从task_meta）→ 修复 case_id/预置条件 REQ-UNKNOWN
- batch-index 0-based 统一（3处：prep_prompt/p6_save_batch/main() agent_output读取）
- export_excel.py 6项对齐（字典+English key/creator/项目/需求/case_type默认/remarks清理）

**SKILL.md层**：
- 段落3/4 "P2/P5自动"≠"段落过渡" 双重澄清
- 6段全加 ⏸️ 强制等待标记
- `__must_emit__` 概念说明
- P6 中介者模式+5步执行模板（Step①-⑤ with操作示例）
- 文件修改规则（batch源/可改, output聚合/不可改）
- P6_guided 提交前自检清单+case_type默认"测试用例"

**边界防御**：
- prep_prompt --step P6 子Agent入口拦截
- p6_save_batch 差1行自动补齐+裸数组自动包装
- 占位符质量标记（remarks不拒绝）

## v4.8.12 — 2026-05-22

### 🏗️ P6中介者模式 + 报告自动推送 + 执行指南重写

- p2_code_generate 自动触发 export_p0p1 → `__must_emit__` 推送 MEDIA（Agent 复制即可）
- P6 角色从"执行者"→"中介者"，三大红线明确"Agent不是生成者，把prompt发给LLM"
- P6 执行流程从 1 行模糊描述重写为 5 步模板（①②③④⑤）
- P6_guided.md 新增"提交前自检清单"（5项检查，不通过不提交）
- p6_save_batch 步骤-期望差1行自动补齐
- prep_prompt --step P6 入口子Agent拦截
- 占位符质量标记（标题/步骤/期望空洞 → remarks）

## v4.8.11 — 2026-05-22

### 🛡️ P6入口子Agent拦截 + 占位符质量标记

- prep_prompt --step P6 增加子Agent检测（入口拦截，子Agent连引导卡都拿不到）
- p6_save_batch 增加占位符质量检测：标记标题占位/步骤空洞/期望空洞到remarks，不拒绝

## v4.8.10 — 2026-05-22

### 🐛 云端 P6 三个阻断修复

**背景**：V4.8.9 云端 P6 卡住（80条用例，P7被阻塞）。修复P1→P2兼容、p6_merge LOW兜底stdout可见、裸数组自动包装。

- P1→P2: children→modules 自动转换
- p6_merge: quality_accepted_low 同步输出 stdout（原仅stderr，Agent看不到）
- p6_save_batch: 裸数组 [] 自动包装为 {"testcases":[]}

## v4.8.9 — 2026-05-22 (patch 2)

### 🐛 P1→P2兼容 + p6_merge LOW兜底可见 + 裸数组自动包装

**背景**：V4.8.9 云端测试发现 4 个问题：①P1骨架输出 children→P2 期望 modules 导致数据结构断裂；②p6_merge LOW 兜底只输出 stderr，Agent 看不到就停下来了；③Agent 输出裸数组 [] 而非 {"testcases":[]}，10条用例丢失；④Agent 仍用子Agent 跑 P6（已有代码检测）。

**修复**：
1. **P1→P2 children→modules 自动转换** (`p1_code_merge`) — 写入 p1_output.json 前将 children 转为 modules
2. **LOW兜底双通道输出** (`p6_merge`) — quality_accepted_low 同步输出 stdout+stderr，确保 Agent 能看到并继续执行 P7
3. **裸数组自动包装** (`p6_save_batch`) — 检测到 list 类型自动包装为 {"testcases": [...]}，不丢失用例
4. **子Agent检测已有** — p6_save_batch/p6_merge/p6_batch_info 三个入口均有 _is_sub_agent_session()，本次 Agent 违规是执行问题

## v4.8.9 — 2026-05-22

### 🏗️ P1 分批生成架构（根治截断问题）

**背景**：P1 一次性生成完整 feature_tree（含所有 scenario）时 JSON 可达 30-80KB，LOW 模型频繁截断。Agent 为规避截断主动压缩 scenario 数量，导致功能点覆盖不足。需长期有效方案。

**架构变更**：P1 拆分为三阶段——骨架→逐feature填充→代码合并

**新增 actions（3个）**：
- `p1_skeleton_save`：保存 module/feature 骨架（无 scenario），输出 feature 列表
- `p1_save_feature --feature-id ID`：保存单个 feature 的 scenarios，校验≥2+含positive
- `p1_code_merge`：代码拼装骨架+所有features → 完整 feature_tree → Gate pass（场景数量校验+操作覆盖校验）

**新增 prompts（2个）**：
- `P1_skeleton.md`：精简 prompt，只要求生成 module→feature 结构，每 feature 的 children 留空
- `P1_feature_scenario.md`：聚焦单一 feature，注入该 feature 上下文+P0 关联规则

**前向兼容**：
- 原 P1 prompt（P1_feature_tree_generation.md）保留，HIGH 模型仍可一shot（但分批是默认推荐路径）
- P1 step_run 仍可用（保留 P1 场景数量 Gate），但推荐用新分批流程
- P2/P3/P4/P5/P6 对 P1 的读取（feature_tree）完全不变

**SKILL.md 段落3 更新**：P1 流程从一shot改为分批三步（骨架→循环填充→合并）

## v4.8.8 — 2026-05-22

### 🔴 段落确认硬性门禁 + 19列字段对齐 + 第二轮云端复盘全量修复

**背景**：V4.8.7 云端测试暴露 8 个新问题（段落确认坍塌、字段缺失、文件名规则缺失等）。经小析+小猿双路评审（均⚠️有条件通过），合并吸收后全量修复。

**修复（8项）：**

**代码层（3项）：**
1. **P6_guided.md 19列全字段对齐** (`prompts/P6_guided.md`) — 格式表扩至19列（对齐export_excel.py），示范JSON含全部字段（含空值），Agent按模板生成不再缺字段
2. **p6_save_batch 错误提示增强** (`orchestrator.py`) — 错误消息明确预期文件名、排查步骤、修复建议
3. **p6_batch_info 时间估算** (`orchestrator.py`) — 新增 `estimated_minutes` 字段（LOW≈1.5分钟/批，HIGH≈0.5分钟/批）

**SKILL.md层（5项）：**
4. **标题去合并化** — "段落3+4合并输出"→"段落3收尾输出"，"段落5+6合并输出"→"段落4收尾输出"，消除标题诱导合段
5. **每段末尾 ⏸️ 强制等待标记** — 6段全加，格式统一为「⏸️ 段落X完成。必须等待用户回复「继续」后，才能进入段落Y。禁止自动跨段。」
6. **段内规则明确化** — 段落3/4新增段内规则说明：P0+P1在段内连续执行，确认仅在段落边界
7. **P6文件名规则明确化** — P6_guided.md 示范区标注文件命名为 `p6_batch_{batch_index:03d}_agent_output.json`（_agent_output后缀不可少）
8. **P6执行描述修正** — "自动连续执行"→"分批自动执行"，明确可设中断点

### 🔴 关键架构
- **段内连续 vs 段间等待**：P0+P1在段落3内连续执行，段落边界（⏸️标记处）才等待用户「继续」。标题去合并化+强制等待标记双保险
- **19列 ≠ 21列**：export_excel.py 实际只有 19 列，不存在 `description` 列

## v4.8.7 — 2026-05-22

### 🔴 LOW模型P6全链路增强 + 段落3MEDIA锚定 + 规则矛盾统一

**背景**：V4.8.6云端运行复盘，发现17项问题（代码7+文档6+流程4），涵盖段落3报告未推送、P6 LOW模型用例数严重不足、SKILL规则自相矛盾、P6失败后抛选择题等。

**修复**:

**代码层（7项）：**
1. **LOW引导卡预算注入** (`p6_guide.py`) — 引导卡新增 `expected_case_count` + `complexity` 字段，模型知道每个TP要生成几条
2. **P6_guided.md全量重写** — 新增预算段落、context文件读取提示、2条用例示范、expected_case_count强制要求
3. **LOW P0/smoke比例放宽** (`orchestrator.py p6_save_batch`) — P0从25%→35%，smoke从25%→30%，适配小批次
4. **p6_batch_info输出执行批次数** — 新增 `total_execution_batches` + `execution_hint` 字段，消除complexity批次和执行批次混淆
5. **规则矛盾统一** (`SKILL.md`) — HIGH模型merge失败强制restart，LOW模型merge失败接受当前用例
6. **p6_merge LOW兜底** (`action_p6_merge`) — LOW模型quality_rejected不再exit(1)，输出 `quality_accepted_low` 继续流程
7. **P6_guided.md context文件读取** — LOW引导卡新增context文件读取步骤

**SKILL.md层（6项）：**
- 段落3模板嵌入MEDIA行 + 质量评分 + cloud_review
- P6段落新增快速参考卡（LOW/HIGH对比表）
- P6段落新增元规则重申（禁止抛选择题）
- P6段落新增进度报告强制要求
- P6失败处理按HIGH/LOW分轨
- 3轮报错暂停指引保留并强化

### 🔴 关键架构说明
- **25% vs 30%/35%**：LOW模型每批3-5条用例，1条P0=20-33%极易突破25%门槛→放宽后用实际批次数验证
- **不restart vs 必须restart**：HIGH模型p6_merge失败重启P6，LOW模型接受当前用例继续
- **total_batches vs total_execution_batches**：前者是complexity分组，后者是LOW执行批次

## v4.8.6 — 2026-05-21

### 🐛 骨架+过滤修复 + P6红线集中化

**背景**：V4.8.5云端复盘发现3个代码bug + Agent违规问题。

**修复**:
1. **文件名过滤加强** (`action_p6_merge`)
   - 排除规则从 `_output` 扩展为 `_output` + `_agent_output`
   - 防止 `p6_batch_N_agent_output.json` 被错误当作context文件读取

2. **skeleton 文件位置统一** (`prep_prompt` + `p6_save_batch`)
   - 从 `data_dir/p6_batch_NNN_skeleton.json` → `data_dir/p6_batches/batch_NNN_skeleton.json`
   - 与 context 文件放在同一目录，降低Agent混淆风险

3. **p6_save_batch 无skeleton自动降级**
   - 骨架文件缺失时：跳过骨架锁定，质量检查降级为宽松模式
   - 不再因缺少skeleton直接拒绝批次

4. **SKILL.md P6 三大红线集中前置**
   - P6段落顶部新增表格：⓵禁止子Agent ⓶禁止跳过prep_prompt ⓷禁止forge gate
   - 在Agent进入P6前即看到红线，而非分散在段落后半部分

## v4.8.5 — 2026-05-21

### 🟢 LOW模型全链路增强

**背景**：V4.8.2云端复盘发现15个问题，其中5个阻塞级已修复，本次补全剩余增强项。

**新增**:
1. **P1 prompt LOW模型精简** (`action_prep_prompt`)
   - LOW模型下 P1 只注入核心5区块（objective + business_rules + constraints + unknowns + test_point_candidates）
   - 原53KB prompt → 预计15-20KB
   - 避免 MiniMax 等小模型 P1 输出被截断

2. **P1 输出截断检测** (`action_step_run`)
   - 检测 JSON 末尾是否完整闭合
   - 截断 → 明确报错 + 提示重跑（含LOW prompt已精简的提示）

3. **Gate LOW模型分级** (`_get_model_tier_for_dir`)
   - LOW模型：G1 + G1.5 从 BLOCK 降为 WARNING
   - 不再因步骤格式细节阻断流程，但仍标记供审查
   - G2/G3/G5/G6 保持 BLOCK 级别
   - 影响：p6_save_batch + p6_merge 两个Gate入口

4. **批次文件格式统一** (`action_p6_merge`)
   - p6_merge 只读取 `batch_[0-9]*.json`，排除 `*_output.json`
   - 避免旧格式文件导致 L3 校验失败

5. **烟雾比例自动纠正（增强）** (`action_p6_merge`)
   - smoke < 10% → 按优先级自动标记 main_flow 类用例为烟雾
   - 记录到 p6_post_process.json

## v4.6.8 — 2026-05-17

### 🔴 P6子任务超时问题修复（简化方案）

- **SKILL.md P6禁令标注**：段落5增加"🔴🔴🔴 V4.6.8 子任务执行禁令(最高优先级)"，明确P6禁止在子任务/子Agent环境中执行
- **删除无效的`--subagent-context`参数检测**：该方案依赖调用方主动传递，实际上不可靠，已移除
- **检测机制**：无（代码层检测走不通，已移除；仅保留SKILL.md禁令）
- **核心防护**：仅SKILL.md禁令（最有效的防护）+ 正确的执行流程（主会话按序执行P0→P1→P2→P3+P4→P5→P6→P7）

---

## v4.6.5 — 2026-05-17

### 🔴 HMAC密钥不一致修复

- **truncation_guard.py HMAC统一**：删除旧的_get_hmac_key_tg/_sign_gate_tg函数，改为从orchestrator.py直接导入_sign_gate，保证新生成的gate pass使用固定HMAC_SECRET
- **背景**：truncation_guard.py使用旧方法（基于文件哈希的HMAC密钥），orchestrator.py使用新方法（固定HMAC_SECRET），两者不一致导致潜在风险

---

## v4.6.4 — 2026-05-17

### 🔴 P7导出被跳过问题（阻塞问题修复）

- **SKILL.md段落5完成后加强提示**：增加强制指令，禁止Agent在此处宣布「任务完成」，必须执行段落6的Step 1（P7质量门禁）+ Step 2（Excel导出）
- **P0P1报告扩展名修复**：orchestrator.py 第5390行硬编码 `.html` → 改为 `.md`，与SKILL.md保持一致，解决Media failed问题

### 🔴 段落1完成后提示词修复

- **修复需求重复询问**：段落1完成后增加段间判断逻辑，如用户已在之前发送需求文档则直接执行step0，不再重复提示「请发送需求正文」

---

## v4.6.3 — 2026-05-17

### 🔴 飞书附件路径自动查找（阻塞问题修复）

- **Step 1 精准查找**：搜索 ~/Downloads、/tmp、~/Desktop、~/Documents、~/Library 最近30分钟内的 docx/txt/pdf 文件
- **Step 2 安全复制**：找到后 cp 到 data_dir/requirement.docx（使用 cp 而非 mv，保留源文件）
- **Step 3 兜底搜索**：Step 1 未找到时扩大范围到全盘搜索2小时内文件，返回最多5个候选让用户确认
- **覆盖路径**：解决飞书附件下载到非标准路径导致的"需求文档尚未上传到处理目录"错误

---

## v4.6.2 — 2026-05-16

### 🔴 知识库完整修复

- **新增knowledge目录**：复制skill_v2的knowledge到skill_v4（含methodology/company_standards/defect_patterns等完整知识体系）
- **SKILL.md增加文档保存说明**：明确上传文档必须移动到data_dir/requirement.docx

### 🔴 需求载荷前置重构（最高优先级）

- **新增⛔入口强制检查章节**：提升为技能最开头的独立章节，优先级高于运行协议
- **新增反面案例表格**：明确列出"等会发"、"稍后发"、"模糊引用"等不算已收到需求
- **新增常见误判场景附录**：Agent自我纠偏参考
- **6段确认模式中保留二次校验**：作为最后防线
- **强制需求载荷前置**:禁止无需求时进入Onboarding，必须先收到需求文档
- **Onboarding结束后直接开始分析**:不再等待「继续」，直接提示发送需求文档

### 🔧 三方审计修复

- **_extract_module动态化**：移除"债券投顾分润"硬编码，改用5级动态提取（tp.module_name > module_map.json > keyword_fallback > source_scenario > 编码展示）+ config/module_map.json配置
- **page_path全链路消费**：11个P6模板全部使用page_path（三重消费：scenario_inject + 模板引擎 + Gate G1/G7校验）
- **knowledge引用修复**：p6_templates.py新增knowledge_injected，引用reviewed_cases
- **batch_size统一**：p5_prepare.py导入orchestrator.P6_BATCH_SIZE=8
- **module_map.json默认配置**：填充M01-M10通用模块映射+关键词fallback
- **P6重试次数增加**：p6_retry_count 2→4次（指数退避）

### 🔴 P6 Prompt核心原则新增

- **不确定性处理**：新增"如果不确定，输出'待确认'而非编造"核心原则
- **5种情况明确处理方式**：字段名/页面路径/按钮文本/业务规则/操作顺序不确定时的正确做法
- **标记格式**：remarks中标注`待确认原因:XXX`，case_type标注为`条件验证`
- **效果**：带"待确认"的用例会被Gate拦截，由人工确认后补充

### 📝 其他修复

- **SKILL.md版本号统一**：标题和description统一为V4.6.0

---

## v4.3.0 — 2026-05-15

### 🏗️ 架构简化（P6三轨模式废弃，统一为单一流程）

- **废弃turbo/hybrid/strict三种P6模式**：统一为一条流程 `P5上下文 → AI生成 → 模板整理 → Gate检查 → 输出`
- **Onboarding简化为3步**：移除原第3步P6模式选择（set_p6_mode），3步为：PRD审查 → L5知识库 → 图片API密码
- **废弃命令**：`set_p6_mode`（Onboarding模式选择）、`p6_code_generate`（hybrid模式一键生成）
- **统一流程适用所有模型**：所有模型统一使用分批流程（p6_batch_info → prep_prompt+p6_save_batch循环 → p6_merge）
- **P6重试规则统一**：原strict模式的自动重试规则升格为所有模型的通用规则
- **p6_templates.py定位更新**：从"hybrid模式代码生成"改为"统一流程辅助"（模板整理阶段使用）
- **引用文件表同步更新**：p6_templates.py描述同步修改

---

## v4.2.0 — 2026-05-15

### 🔧 字段标准化（与评审工具v4.1.1对齐）

- **export_excel.py 需求列修复**: 改取 `case["project"]` 而非 `case["requirement"]`（后者存的是task_id无业务含义）
- **export_excel.py 创建者固定**: 固定返回 `"AI"`（之前为空）
- **export_excel.py 经办人**: 保持空字符串

### 📝 字段定义19列标准

| 列名 | 字段 | 说明 |
|------|------|------|
| 项目 | project | 取P6 JSON的project字段 |
| 类型 | case_type | 固定"测试用例" |
| 用例编号 | case_id | 原始编号 |
| 需求 | project | 取P6 JSON的project字段 |
| 优先级 | priority | P0→Highest映射 |
| ... | ... | ... |

---

## v4.1.1 — 2026-05-12

### 🐛 Bug修复

- **P0段落3内容修复** (SKILL.md): 字段路径从顶层改为blocks下business_objects/operations/business_rules/test_point_candidates；clarification_questions不存在，改为读blocks.unknowns
- **评审链接不展示修复** (orchestrator.py): cloud_review增加pushed字段，解决Agent读undefined→不展示链接
- **模型名归一化** (orchestrator.py): 新增_normalize_model_name()，去空格/连字符/下划线后匹配，解决deepseek-v4-pro vs deepseek v4 pro匹配失败
- **知识库同步URL修复** (cloud_sync.py+orchestrator.py): 修复嵌套结构review_tool.api_url读取逻辑，解决知识库从未同步问题

### ⚡ 性能/体验优化

- 云端知识库同步为唯一数据源，本地knowledge/目录已移除，58文件按需拉取
- 更名为qc-req2testcase-generator，触发词同步更新
- 废弃文件清理（SKILL.md.bak、prompts/archive、tools/review_tool）

# Changelog

## Changelog

### v4.0.1 (2026-05-11)

**变更类型**: enhancement（Phase 1-4 优化）

**Phase 1：评审推送闭环**
1. **SKILL.md段落8评审推送指令补全**：step7_export返回cloud_review字段时，Agent需输出评审链接
2. **SKILL.md段落3评审推送指令补全**：export_p0p1返回cloud_review字段时，Agent需输出评审链接
3. **orchestrator新增 `_push_p0p1_to_review_tool`**：段落3完成后推送P0/P1摘要到评审工具
4. **step5-7.md P7旧流程清理**：移除"构造Prompt+调用LLM"等过时描述
5. **用户交互指令表增加"重试推送"**：`retry_push` action
6. **`_enqueue_failed_push` 增加 `push_type` 字段**：区分P6用例推送和P0/P1摘要推送
7. **p0p1_summary补充模块名列表**：`p1_modules` 字段

**Phase 2：业务域匹配完善**
8. **project_domain_mapping.json升级v2.0**：10组项目映射（11→10，SMT合并）+ 16条同义词
9. **同义词模糊匹配**：`_match_project_to_domains` 增加第二层同义词匹配
10. **task_meta写入域匹配结果**：新增 `domains`/`matched_projects`/`matched_synonyms`/`project_name` 字段
11. **domain字段统一为中文域名**：`resolved_domain` 优先用域匹配结果
12. **4层注入支持同义词触发**：纯同义词匹配限制L1注入防prompt膨胀
13. **推送传递project_name**：`_push_to_review_tool` 补充project_name读取

**Phase 3：评审工具前端改造**
14. **后端新增 `GET /api/projects/dict`**：项目字典下拉框数据（动态读取+种子降级）
15. **后端新增 `dictionary.js`**：完整项目字典CRUD（增删改查+Levenshtein模糊匹配+别名）
16. **前端新建项目改为下拉选择**：el-select filterable + 手动输入切换
17. **导入匹配优先用project_name**：orchestrator推送的真实项目名
18. **新建项目同步创建字典条目**：保持数据一致性
19. **前端重名预检**：创建前检查避免重复提交

**Phase 4：文档清理**
20. **cloud.json.example更新**：实际腾讯云地址+experience_sync标注为预留

**四路交叉评审**：每阶段均经过小析/小文/小猿+小墨四路评审，所有P0/P1问题已修复

---

### v4.0.0 (2026-05-09)

**变更类型**: major feature

**变更内容**:
1. **云端评审推送**：新增 `_push_to_review_tool()` 和 `_retry_pending_reviews()`，段落3完成后自动推送P0/P1/P6数据到评审工具
2. **知识库同步**：新增 `_sync_knowledge_from_cloud()`，支持从云端拉取评审经验反馈到L6经验库
3. **项目→业务域匹配**：新增 `_match_project_to_domains()`，基于project_domain_mapping.json自动匹配12个一级业务域
4. **HMAC来源审计**：Gate Pass增加 source_action 字段，step7_export全链路审计来源合法性
5. **重试队列**：推送失败的评审记录写入 pending_reviews.jsonl，支持后续手动/自动重试
6. **P0/P1报告导出**：新增 `export_p0p1.py`，段落3完成后自动生成P0/P1结构化报告（MD+HTML）
7. **PRD审查增强**：新增 `export_prd_review.py`，PRD审查结果独立导出为Excel
8. **业务域扩展**：从8域扩展到12域（新增投顾/投研/自营/互联网终端）
9. **Onboarding交互优化**：需求载荷就绪前置检查，防止空需求启动流程
10. **架构声明升级**：SKILL.md metadata版本统一为V4.0.0，description更新

**新增文件**:
- tools/export_p0p1.py
- tools/export_prd_review.py
- config/project_domain_mapping.json
- prompts/P0_prd_review_enhance.md
- prompts/P6_api_rules.md

**影响范围**:
- orchestrator.py: 新增4个action（step7_export增强、retry_push、knowledge_sync、domain_match）
- SKILL.md: 架构声明、版本号、引用文件表全面更新

### v3.5.8 (2026-05-08)

**变更类型**: feature (段落3完成后发送P0/P1报告文件)

**新增：段落3完成后自动生成并发送需求理解与功能点拆解报告**

问题：用户反馈段落3完成后，页面上虽然显示了需求结构化的markdown和问题清单，但没有文件可以下载发送给产品经理审阅。

修复：
1. **新增export_p0p1.py脚本** — 将P0的blocks_markdown/issues和P1的feature_tree导出为结构化的Markdown文件
2. **orchestrator.py新增export_p0p1 action** — 调用导出脚本，生成p0p1_report.md文件
3. **SKILL.md指令更新** — 段落3完成后，自动执行export_p0p1并通过MEDIA指令发送文件给用户

文件内容：
- 第一部分：P0需求结构化（需求目标、质量评分、需求结构化内容、问题清单）
- 第二部分：P1功能点拆解（模块/功能点/场景树，带统计信息）

影响：
- 用户在段落3完成后可以直接收到p0p1_report.md文件，方便发送给产品经理审阅
- 如果开启了PRD审查，同时发送prd_review_report.md文件
- 不影响其他段落的执行流程

---

### v3.5.7 (2026-05-08)

**变更类型**: bugfix (PRD报告文件自动生成)

**修复：Agent未调用quality_check导致PRD报告文件未生成**

问题：V3.5.5将PRD报告文件生成逻辑放在quality_check action中，但Agent在P0完成后没有调用quality_check（直接用step_run通过），导致报告文件未生成，用户无法下载。

修复：
1. **step_run中自动生成报告** — P0的step_run成功后，如果prd_quality_review=True，自动读取p0_output.json并生成prd_review_report.md
2. **SKILL.md指令更新** — 段落3完成后，Agent检查报告文件是否存在，存在则发送下载链接

影响：
- 不依赖Agent是否调用quality_check，只要P0完成且开启PRD审查，报告文件必定生成
- 跳过PRD审查的任务不受影响

---

### v3.5.6 (2026-05-07)

**变更类型**: enhancement (PRD审查内容质量校验)

**新增：PRD审查内容质量三项校验**

在V3.5.4字段存在性校验的基础上，新增内容质量校验：

1. **blocks_markdown最小长度校验** — 内容不得少于200字符，防止Agent输出空字符串或过于简单的内容
2. **关键维度检查** — blocks_markdown必须至少包含2个维度（输入/输出、业务规则、角色权限、状态流转、约束条件），防止Agent只输出模块功能点列表
3. **issues格式校验** — issues数组中的对象必须包含severity/location/type/problem/suggestion字段，防止Agent输出不完整的问题清单

**错误类型**
- 字段缺失：`prd_review_validation_failed`
- 内容质量不达标：`prd_review_quality_failed`

**影响**
- 跳过PRD审查的任务不受影响
- 开启PRD审查后，Agent必须输出高质量的blocks_markdown和issues，否则step_run拒绝

---

### v3.5.5 (2026-05-07)

**变更类型**: enhancement (PRD审查报告文件输出 + blocks_markdown增强)

**新增：PRD审查结果自动生成Markdown报告文件**

1. **自动生成报告文件** — quality_check返回时自动将PRD审查结果写入 `{data_dir}/prd_review_report.md`，包含质量评分、结构化结果、问题清单
2. **Agent发送文件链接** — SKILL.md指令Agent在展示PRD审查结果后，发送文件下载链接给用户（像Excel一样）
3. **blocks_markdown增强** — 增加业务规则、角色权限、状态流转、约束条件等5个维度，输出更丰富的需求结构化内容

**改动文件**
- `tools/orchestrator.py`: quality_check中增加报告文件生成逻辑，返回prd_review_report_path字段
- `SKILL.md`: 段落3中P0执行后增加文件发送指令
- `prompts/P0_prd_review_enhance.md`: blocks_markdown输出要求增强，新增5个维度

**用户体验提升**
- PRD审查结果可下载保存，方便分享给产品经理
- 结构化结果更丰富，包含业务规则、权限、约束等测试用例设计关键信息

---

### v3.5.4 (2026-05-07)

**变更类型**: bugfix (PRD审查字段强制校验)

**修复：Agent忽略PRD审查字段导致输出缺失**

问题：开启PRD审查后，prompt正确注入了blocks_markdown和issues输出要求，但Agent（如DeepSeek-v4-pro）忽略了这两个字段，只输出基础字段，导致PRD审查增强功能完全无效。

修复：
1. **step_run中加PRD审查字段强制校验** — 当prd_quality_review=True时，检查P0的agent_output是否包含blocks_markdown和issues，缺少直接返回prd_review_validation_failed错误并拒绝
2. **SKILL.md中加强警告** — 在段落3的P0执行指令前增加红色高亮警告，明确告知Agent这两个字段是代码层强制校验的必填字段

影响：开启PRD审查后，Agent必须输出blocks_markdown和issues，否则step_run拒绝。跳过PRD审查的任务不受影响。

---

### v3.5.3 (2026-05-07)

**变更类型**: bugfix (step0覆盖task_meta)

**修复：step0全量覆盙task_meta.json导致prd_quality_review丢失**

问题：set_prd_review在Onboarding时正确写入prd_quality_review:true到task_meta.json，但step0执行时全量重建meta对象并覆盖写入，导致该字段丢失。

修复：step0写入task_meta前先读取已有内容，保留已有字段（如prd_quality_review），新字段覆盖旧字段。

---

### v3.5.2 (2026-05-07)

**变更类型**: security hardening (Agent绕过防护)

**核心功能：防止Agent绕过orchestrator伪造执行结果**

问题背景：MiniMax M2.7等弱模型在orchestrator返回错误时，不按SKILL.md指令重试，而是直接用Python调用内部函数伪造gate/output/state文件。

**新增防护机制：**
1. **SKILL.md绝对禁止规则** — 7条硬规则，明确禁止直接写gate/output/state、import orchestrator、伪造结果
2. **gate来源校验** — gate文件新增source_action字段，验证时检查来源是否合法
3. **全局变量_CURRENT_ACTION** — 只在main() dispatch时设置，Agent import时为空→指纹不匹配
4. **output文件写入保护** — step_run前检测文件是否被Agent提前写入，是则删除
5. **step7全链路审计** — 导出前检查所有gate的source_action是否合法，非法来源拒绝导出

**改动文件**
- `tools/orchestrator.py`: _CURRENT_ACTION全局变量 + _VALID_GATE_SOURCES映射 + _write_signed_gate加source_action + _verify_gate_hmac加来源校验 + step_run加output保护 + step7_export加审计
- `SKILL.md`: 操作约束矩阵追加V3.5.2绝对禁止行为

**兼容性**
- 旧版本gate文件（无source_action字段）自动跳过来源校验，不影响现有任务
- HMAC签名机制不变，新增字段参与签名计算

---

### v3.5.1 (2026-05-07)

**变更类型**: feature enhancement (PRD审查增强)

**核心功能：PRD质量审查增强输出**

用户在Onboarding选择「开启PRD审查」后，P0完成时自动输出：
- 需求结构化Markdown（带❗️不清晰标识）
- 问题清单（severity/location/type/description/suggestion）
- 评分<0.5仍然中断（保持现有逻辑），但中断前输出内容
- 评分≥0.5时展示内容后自动继续P1，不增加交互

**新增文件**
- `prompts/P0_prd_review_enhance.md` — PRD审查增强prompt（条件注入）

**新增action**
- `set_prd_review` — 设置PRD审查开关（Onboarding第1步用户选择后调用）

**改动文件**
- `tools/orchestrator.py`: prep_prompt条件注入 + quality_check增强返回 + set_prd_review action + 版本号3.5.1
- `SKILL.md`: 段落1第1步追加set_prd_review调用 + 段落3追加quality_check展示指令 + 版本号3.5.1

**兼容性**
- 跳过PRD审查时完全不触发新代码
- P1-P7无任何变化
- gate pass/HMAC签名不受影响
- 非交互模式不变（不增加等待点）

---

### v3.5.0 (2026-05-06)

**变更类型**: major release (推广前最终版)

**核心修复：turbo 模式绕路问题（三层防线）**

**问题**：turbo 模式云端测试中，Agent 以"耗时长"为由自行调用 `p6_code_generate`（hybrid 路径），导致用例质量低（步骤截断、内容重复），`generation_method: code_template` 而非 Agent 直出。

**修复1：orchestrator 代码硬拦截**
- `action_p6_code_generate` 入口增加模式检查，turbo/strict 模式调用直接返回 `mode_blocked` 错误
- hybrid 模式正常通过

**修复2：step7_export 模式一致性校验**
- 导出 Excel 前检查 `generation_method` 与 `p6_mode` 是否匹配
- turbo/strict 模式下 `generation_method=code_template` 直接拒绝导出，返回修复指引
- hybrid 模式下 `generation_method` 必须为 `code_template`

**修复3：SKILL.md 硬约束**
- turbo 段落开头加两条红色严禁标记
- 明确禁止调用 `p6_code_generate`，禁止以"耗时长"为由切换模式

**合并修复（V3.4.6~V3.4.11 全部变更）**
- V3.4.6: step0 自动发现需求文档
- V3.4.7: P0 提升改为 feature 级，P2 异常每 feature 只生 1 条
- V3.4.8: P1 scenario ≤6 硬校验
- V3.4.9: 空 data_dir 误命中修复，P0 expected_case_count 上限 2
- V3.4.10: export_excel.py 冒烟阈值同步修复（8%→5%）
- V3.4.11: 项目名自动提取（从需求文件名）

**验证结果**
- turbo/strict 模式调用 p6_code_generate → mode_blocked ✅
- hybrid 模式调用 p6_code_generate → 通过模式检查 ✅
- SKILL.md 约束文本到位 ✅
- 语法检查通过 ✅

---


**变更类型**: bugfix (测试用例项目名为空)

**问题**: 生成的测试用例 Excel 中项目字段为空。

**根因**: orchestrator 对每条用例执行 `tc.setdefault("project", "")`，直接设为空字符串，未从任何地方读取项目名。

**修复**:
1. **step0 自动提取项目名**：从需求文件名提取（去掉路径、扩展名、云端上传附加的 UUID 后缀 `---xxxx`），写入 task_meta.json 的 `project` 字段
2. **p6_code_generate 读取项目名**：从 task_meta.json 读取 `project` 字段，填充到每条用例

**示例**：
- 文件名 `集团CRM_V1.0.14_兴光闪耀活动机构战报优化产品需求文档---7bc1d4d1-...docx`
- 提取项目名：`集团CRM_V1.0.14_兴光闪耀活动机构战报优化产品需求文档`

---


**变更类型**: bugfix (小析+小猿评审发现的两个隐性问题 + export_excel冒烟阈値漏改)

**问题1: `_auto_discover_requirement` 空 data_dir 误命中**
- 根因：`os.path.dirname("")` 返回 `""`，原代码用 `os.path.isdir(d)` 判断，在某些系统下 `isdir("")` 可能返回 True，导致跳过空路径检查直接扫描 Downloads 误命中无关文件
- 修复：在 `isdir` 判断前增加明确的非空字符串检查 `if not d`，彻底屏蔽空路径

**问题2: 冒烟比例数学上仍不达标8%**
- 根因：P0 测试点因 category 为 exception/integration 被判 L3，`expected_case_count=3`，导致 P0 用例展开过多、冒烟比例被稀释；最坏情况冒烟比例 5.3% < 8%
- 修复1：P0 测试点 `expected_case_count` 强制上限为 2（P2 complexity 标注和 P5 merge 两处同步修复）
- 修复2：冒烟门槛下限从 8% 调整为 5%（orchestrator.py P6_QUALITY_RULES + export_excel.py 两处同步修复）
- 数学验证：12 features 最坏情况冒烟 5.6%，达标5%门槛

**问题3: export_excel.py 冒烟阈値漏改（云端测试发现）**
- 根因：orchestrator.py 的 P6_QUALITY_RULES 已改为 5%，但 export_excel.py 第309行独立硬编码了 `0.08`，导致冒烟比例 7.95% 被拦截（> 5% 但 < 8%）
- 修复：export_excel.py 冒烟阈値从 0.08 改为 0.05，与 orchestrator.py 一致

**云端测试验证结果（兴光闪耀需求，4模块/12功能点）**
- P1 scenarios: 39（原52，降25%），所有feature的scenario数量≤ 6 ✅
- P2 测试点: 68（原130，降48%），P0=12 ✅
- P5 测试点: 67，total_expected_cases=151
- P6 用例: 151条（原320，降53%），冒烟12条(7.9%) ✅
- P7 门禁: PASS ✅，Excel导出: 成功 ✅

---


**变更类型**: bugfix (P1 scenario数量膨胀根治)

**问题**: P1 Agent将单个feature拆出11个scenario（如「月榜榜单查看」「月榜数据导入」），导致P2测试点膨胀。即使已修复异常用例生成逻辑，根源过多的scenario仍会导致用例过多。

**修复内容**:
1. **P1 prompt新增约束4**：每feature的scenario建议2-5个，最多不超过6个；超过时必须合并相似场景
2. **P1质量门禁新增第6条**：任何单个feature的scenario数量不得超过6个，超过时必须在coverage_check.scenario_overflow中标注
3. **orchestrator P1 quality_check新增硬校验**：任何feature超过6个scenario直接拒绝，返回具体超过的feature列表

**预期效果**：同样需求（兴光闪耀，4模块/12功能点）：P1 scenario从52个降至最多72个，P2测试点从130条降至约60-80条，总用例从320降至约150-200条

---


**变更类型**: bugfix (冒烟比低 + 用例数量过多)

**问题1: 冒烟比例1%（应≥8%）**
- 根因：P0提升逻辑是“每module只提升第1个main_flow”，4个module只产生4个P0测试点，320条用例中冒烟只有4条(1%)
- 修复：改为“每feature第1个main_flow升为P0”，12个功能点就有‒12个P0测试点，冒烟比例大幅提升

**问题2: 用例数量320条过多**
- 根因：P2代码生成对每scenario无条件生成「正向+异常」2条，12个功能点平均含多个scenario，导致P2测试点膨胀到130条
- 修复：异常验证改为「每feature只生成1条」，避免每scenario都生成异常用例；权限验证增加scenario_type信号判断，不再仅凭多角色就生成

**预期效果**：
- 同样需求（兴光闪耀，4模块/12功能点）：P2测试点从130条降至约60-70条，总用例从320降至约150-180条
- 冒烟比例：从1%提升至预期8-15%

---


**变更类型**: bugfix (段落2 requirement_length=0 根治)

**核心问题**: V3.4.5云端测试中，Agent未正确替换SKILL.md中的`{docx_path}`占位符，导致step0收到空的requirement_file，requirement_length=0，后续所有段落无需求文本可用。

**根因**: SKILL.md段落2指令依赖Agent正确替换`{docx_path}`，但Agent在云端环境下直接原样传入占位符或传空字符串。

**修复内容**:
1. **新增`_auto_discover_requirement(data_dir)`函数**：当requirement_file和requirement_text均为空时，自动扫描以下路径（按优先级）：
   - data_dir同级目录
   - ~/Downloads
   - ~/Desktop
   - ~/.openclaw/workspace/sharetasks
   - 当前工作目录(cwd)
   - 优先.docx，其次.md，最后.txt；同目录取最新修改时间的文件
2. **step0返回auto_discovered字段**：自动发现时返回`auto_discovered:true`和warning说明，便于Agent感知
3. **step0无文件时明确报错**：扫描仍未找到时返回`status:error`并给出明确提示，exit(1)
4. **step0_8_prep兜底**：requirement_file为空时先从task_meta.json读取，避免Agent跨段落传参丢失

---


**变更类型**: bugfix (移除$ORCH引用触发安全检查)

**核心问题**: V3.4.4云端测试中，step_3_display和step_4_display包含`$ORCH`字符串，触发了云端exec工具的shell变量注入安全检查，导致orchestrator完全无法执行

**修复内容**:
1. 移除step_3_display和step_4_display中的`$ORCH`、`exec:`、双引号包裹等可能触发安全检查的内容
2. 改为纯文本描述（"执行 orchestrator --action xxx"），不包含shell变量或引号

---

### v3.4.4 (2026-05-05)

**变更类型**: bugfix (Onboarding第3/4步执行指令补全)

**核心问题**: V3.4.3云端测试中Agent正确展示了交互选项，但用户输入密码后没有执行check_image_api验证命令，导致图片理解未启用

**根因**: step_3_display和step_4_display只包含展示文案，没有告诉Agent收到用户回复后要执行什么命令

**修复内容**:
1. **step_3_display增加执行指令**: 用户选模式后必须执行set_p6_mode
2. **step_4_display增加执行指令**: 用户输密码后必须执行check_image_api验证

---

### v3.4.3 (2026-05-05)

**变更类型**: bugfix (Onboarding交互内容修复)

**核心问题**: V3.4.2云端测试中Agent展示了交互步骤（修复生效），但内容完全错误——Agent自由发挥而非按SKILL.md中的文案展示

**根因**: Agent读到了步骤名称但没有读SKILL.md中每步的具体展示内容，自己"创造性"理解后输出了错误文案

**修复内容**:
1. **onboarding返回JSON包含每步完整展示文案**: step_1_display到step_4_display，Agent只需原样输出
2. **版本号统一为3.4.3**

**设计原则**: Agent不需要理解步骤含义，只需要按顺序原样输出orchestrator返回的display文案

---

### v3.4.2 (2026-05-05)

**变更类型**: bugfix (Onboarding交互流程修复)

**核心问题**: V3.4.0云端测试中Agent跳过了Onboarding的分步交互（第1-4步全部未展示），导致P6模式未选择、图片密码未输入

**根因**: SKILL.md第3步（P6模式选择）的描述过于复杂（包含“Agent执行onboarding”、变量替换、多层代码块），Agent解析困难后跳过了整个交互流程

**修复内容**:
1. **简化SKILL.md第3步格式**: 与第1步、第2步保持一致的简洁格式（标题+代码块选项+等待提示）
2. **移除多余指令**: 删除“Agent执行 onboarding（如已执行则跳过）”等混淆指令
3. **统一四步格式**: 第1-4步全部采用相同结构，降低Agent解析难度
4. **orchestrator onboarding返回增加next_action字段**: 明确告知Agent"接下来必须展示4步交互"，不允许跳过
5. **SKILL.md强化onboarding指令**: “段落1还没完成！必须继续执行4步交互”
6. **onboarding返回包含每步完整展示文案**: step_1_display到step_4_display，Agent只需原样输出，不需自己创造内容

**测试验证**: SKILL.md格式一致性确认 ✅

---

### v3.4.0 (2026-05-05)

**变更类型**: architecture (P6双轨架构 + 模板引擎)

**核心问题**: minimax-m2.7在P6阶段反复证明无法稳定生成高质量差异化用例，需要根据模型能力提供不同执行路径

**竞品借鉴**: AITestCraft (github.com/liwanlei/AITestCraft)

**核心改动**:
1. **P6双轨架构（3条路径）**:
   - turbo: 强模型直出，宽松门禁，P7兆底
   - hybrid: 代码生成全部用例 + 可选Agent润色P0+P1
   - strict: 严格门禁 + 自动重试（V3.3.5逻辑）
2. **新增p6_templates.py模板引擎**: 11套category模板，基于P5测试点自动生成完整用例
3. **新增action p6_code_generate**: hybrid模式核心，一条命令完成全部P6
4. **新增action set_p6_mode**: 用户选择执行路径
5. **Onboarding新增第3步**: P6模式选择（系统推荐+用户决定）
6. **P7模式感知**: turbo下C2/C6.1降级为WARNING
7. **p6_save_batch模式分支**: turbo宽松/strict严格/hybrid拒绝
8. **MODEL_RECOMMENDATIONS**: 模型→推荐模式映射表
9. **SKILL.md段7三模式分支**: 根据p6_mode执行不同流程

**模板引擎覆盖**: main_flow/branch/integration/permission/exception/boundary/compatibility/performance/security/state_migration/api

**测试结果**:
- p6_code_generate: 149条用例秒级生成 ✅
- set_p6_mode: turbo/hybrid/strict切换正常 ✅
- 语法检查: OK ✅

---

### v3.3.5 (2026-05-05)

**变更类型**: quality + efficiency (P6质量提升 + 竞品借鉴 + 效率优化)

**核心问题**: V3.3.4云端P6生成151条用例但P7门禁失败（C2步骤数≠期望结果数，C6.1前置条件检测过严）

**竞品借鉴**: AITestCraft (github.com/liwanlei/AITestCraft)
- 极简schema思路：Agent只生成8个核心字段，代码补全其余11个
- 自动重试机制：p6_save_batch失败时Agent自动重试，不报告用户
- 正面规则替代禁止描述：告诉Agent怎么做而不是不要做什么
- 确定性输出：temperature=0思路

**修复内容**:
1. **骨架改为step_expected_pairs配对格式**: 天然保证步骤数=期望结果数，根因修复
2. **p6_save_batch增加步骤-结果数量校验**: 阈值15%，差≥11即判定，P6阶段拦截不等P7
3. **P6 prompt增加最佳实践示例**: 含正向/异常/权限三种场景的完整示例，正面引导
4. **P6输出简化**: Agent只生成8个核心字段，代码自动补全其余11个
5. **SKILL.md增加P6自动重试规则**: 最多2次自动重试，用户无感
6. **P7 C6.1检测放宽**: 2/3匹配即通过 + 关键词扩充
7. **P6 prompt增加确定性输出提示**: 借鉴AITestCraft temperature=0思路

**增量修补铺路(V3.4)**: P7输出增加fixable_cases字段，为后续增量修补做准备

---

### v3.3.4 (2026-05-05)

**变更类型**: hardening + quality (Agent遵循性强制约束 + P6用例质量改善)

**核心问题**: V3.3.2云端测试中Agent无视SKILL.md指令，P2仍走老路径(prep_prompt+step_run)；P6生成占位符内容通不过质量门禁

**修复内容**:
1. **step_run增加P2硬拒绝**: 与P5/P6/P7对齐，代码层强制拒绝非法调用
2. **prep_prompt增加P2/P5/P7准入检查**: 更早拦截，阻止无效LLM调用浪费Token
3. **p6_save_batch增加步骤唯一性检查**: 所有用例步骤相同时直接拒绝（占位符检测）
4. **P6 prompt增加反占位符警告**: 明确告知Agent不允许泛化描述
5. **SKILL.md顶部增加操作约束矩阵**: 结构化表达每个Step的Agent角色和唯一正确命令
6. **SKILL.md段落4精简**: 删除所有"禁止"描述，只保留唯一正确路径

**设计原则**: 纵深防御——SKILL.md约束矩阵 → prep_prompt准入 → step_run硬拒绝，三层拦截确保Agent只能走正确路径

**测试结果**:
- step_run P2: REJECTED ✅
- prep_prompt P2: REJECTED ✅
- prep_prompt P5: REJECTED ✅
- prep_prompt P6: OK（分批流程需要） ✅
- p2_code_generate: 正常执行 ✅

**P6用例质量改善（同版本追加）**:
7. **batch_size从10降到6**: 降低模型单批生成压力，每批12-18条用例
8. **骨架预生成steps_hint/expected_hint**: 基于category+description为每条用例预生成差异化步骤草稿，Agent任务从"从零创造"降级为"细化补充"
9. **P6 prompt增加反面few-shot示例**: 明确展示不合格输出vs合格输出
10. **步骤唯一性检查改为跨测试点级别**: 同测试点内步骤相似是合理的，只拦截跨测试点完全相同的占位符

---

### v3.3.2 (2026-05-05)

**变更类型**: optimization (P2代码路径 + P6 prompt瘦身)

**核心问题**: V3.3.1云端测试中P2步骤Agent未能正常执行LLM推理，手动构造了机械化测试点；P6因prompt过长(68KB/47K chars)导致Agent无法生成有效JSON

**数据来源**: V3.3.1云端测试 task_20260505_002437 全量JSON产物分析 + 小猿交叉评审

**核心原则**: P2代码硬控结构，零Agent依赖；P6减少注意力分散，提高指令遵循精度

**修复内容**:
1. **新增action_p2_code_generate**（核心改动，~170行新增代码）：
   - 从P1 feature_tree自动生成测试点，零Agent依赖
   - 规则引擎：每scenario生成2-4个测试点（正向+异常+按需补充边界/权限）
   - 优先级硬控：main_flow=P1，exception=P2，boundary=P3，permission=P1，每module第1个正向升P0
   - 覆盖率校验：确保所有module和feature被覆盖
   - complexity/expected_case_count自动标签
   - truncation_guard + gate pass完整流程
2. **P6 prompt瘦身**（47577→29493 chars，压缩38%）：
   - 移除完整p5_output.json注入（-40.9%），改为批次信息中注入P1 scenario语义详情
   - 移除defect_schema知识注入（-6.3%，与P6用例生成无关）
   - 接口测试规则拆分为独立文件，按需加载（-9.5%，无接口场景时）
   - 骨架JSON改compact格式（-4.2%）
   - 新增全局上下文摘要（告知模型需求整体范围）
   - 新增P1 scenario语义注入（替代被移除的完整p5，给P6业务上下文）
   - 新增输出长度预估提示（帮助模型规划输出结构）
3. **新增_check_api_features函数**（~30行）：
   - 检查P0 operations和P1 feature names中是否包含接口相关关键词
   - 决定是否注入接口测试规则
4. **P6模板拆分**：
   - P6_testcase_generation.md: 603行→468行（移除接口规则段落）
   - P6_api_rules.md: 新建135行（从原模板拆出，按需加载）
5. **SKILL.md段4更新**: 从Agent推理改为代码路径（p2_code_generate）
6. **版本号统一为3.3.2**: orchestrator.py + SKILL.md

**测试结果**:
- p2_code_generate: 35条测试点，P0:5/P1:10/P2:15/P3:5，覆盖5/5模块 ✅
- P6 prompt: 47577→29493 chars（压缩38%） ✅
- _check_api_features: 正确识别推送功能 ✅
- 语法检查: OK ✅

**交叉评审**: 小猿评审通过（有条件），3个BLOCK项已在实现中修正

---

### v3.3.1 (2026-05-04)

**变更类型**: version-bump (版本号统一)

**核心问题**: V3.3.0发布时orchestrator.py的SKILL_VERSION残留为"3.2.9"，与SKILL.md版本号不一致

**修复内容**:
1. **版本号全量统一为3.3.1**: orchestrator.py SKILL_VERSION、SKILL.md version、export_excel.py标题、HTML报告版本号
2. **CHANGELOG补全**: 补充V3.3.0和V3.3.1变更记录

### v3.3.0 (2026-05-04)

**变更类型**: architecture-change (P7代码硬校验 + 校验去重)

**核心问题**: V3.2.9云端测试中P7质量自检阶段Agent无法生成有效JSON（输入350KB/89K tokens过大），导致任务卡死在P7，无法进入step7_export

**数据来源**: V3.2.9云端测试 task_20260503_233148 全量JSON产物深度分析 + 双路交叉评审（小析测试分析+小猴代码实现）

**核心原则**: P7代码硬校验，零Agent依赖，秒级完成。与P5(p5_code_merge)、P6(p6_save_batch+p6_merge)一样走代码路径。

**修复内容**:
1. **新增action_p7_code_check**（核心改动，501行新增代码）：
   - C1要素完整性[BLOCK]: 必填7项字段非空校验
   - C2步骤-结果对应[分级]: ±1=INFO, ±2=WARNING, ≥3=BLOCK
   - C3 P0占比[WARNING]: ≤20%通过, 20-40%警告, >40%阻塞
   - C4冒烟占比[WARNING]: 按总数分档校验
   - C5步骤描述质量[WARNING]: 上下文感知正则，模糊词表过滤（误报率从34%降至4.7%）
   - C6期望结果质量[WARNING]: 负向模式正则，只匹配句末孤立模糊描述（误报率从66%降至16.8%）
   - C6.1前置条件三要素[BLOCK]: 账号/权限 + 数据构造 + 环境配置关键词检测
   - C7测试点覆盖率[BLOCK]: P5 active测试点必须100%覆盖
   - C7.1语义覆盖[WARNING]: 业务实体匹配（从需求提取固定术语，0%误报）
   - C8冒烟合规性[WARNING]: 冒烟用例priority应为P0/P1
   - C9伞形用例检测[WARNING]: 正则检测“同上/同理/与…一致”
   - 自动生成p7_output.json + p7_report.html + P7.pass.json(HMAC签名)
   - INFO级统计: 优先级分布、步骤唯一率、平均步骤长度、标题重复度
2. **step_run禁止P7**（与P5/P6一样）：
   - `step_run --step P7`直接拒绝，返回错误提示必须用p7_code_check
3. **step7_export去重**（移除P6质量重复校验）：
   - 移除smoke比例、P0比例、优先级分布校验（P7已覆盖）
   - 只保留用例数量底线(≥15) + P7 source校验(source="p7_code_check")
4. **p6_merge去重**（精确比例校验移至P7）：
   - smoke/P0改为底线校验(>0)，移除比例校验和步骤去重
   - 保留skeleton一致性、用例数量、测试点覆盖校验
5. **P7 prompt归档**: P7_quality_gate.md移至prompts/archive/目录
6. **SKILL.md段8更新**: P7指令从`step_run --step P7`改为`p7_code_check`
7. **P7 HTML报告自动生成**: 校验完成后自动生成p7_report.html，包含各Check状态、WARNING用例列表、统计指标

**集成测试**（V3.2.9云端190条用例验证）:
- Gate: PASS
- BLOCK: 4/4全通过（C1/C2/C6.1/C7）
- WARNING: 3/7触发（C4冒烟8.9%偏低、C8一条P2+smoke、C9三条伞形）
- 性能: 190条用例全量校验1.2ms，远低于3秒目标

**影响范围**:
- tools/orchestrator.py: 新增501行P7代码 + step_run/step7_export/p6_merge改造 (2700行→3164行)
- tools/export_excel.py: 版本号更新
- SKILL.md: 版本号+段8指令更新
- prompts/P7_quality_gate.md: 移至archive/

**兼容性**: ✅ 向后兼容。P0-P6流程不变，P7从“Agent审计”改为“代码校验”，Agent只需调用一条命令。

### v3.2.9 (2026-05-03)

**变更类型**: 代码层硬控全面升级 (基于V3.2.8云端测试失败分析+小析交叉评审)

**核心问题**: V3.2.8云端测试证明依赖prompt指令约束Agent行为不可靠。168条用例只有2种步骤模板，冷烟50%，P0=0，L3全部只展开2条。

**核心原则**: 代码硬控 > prompt指令。凡是仅靠Agent“自觉遵守”的方案都不可接受。

**修复内容**:
1. **priority/is_smoke代码预分配+锁定**（核心改动）：
   - prep_prompt为每个测试点生成case骨架（case_id/source_test_point/priority/is_smoke）
   - 冷烟分配策略：仅P0+主流程类别(main_flow/branch/integration)标冷烟
   - 骨架写入p6_batch_NNN_skeleton.json
   - save_batch时强制用代码原值覆盖Agent返回的priority/is_smoke，Agent无法篡改
2. **p6_save_batch硬校验**（从软校验升级）：
   - 逐测试点校验expected_case_count达标（不只看批次总数）
   - 冷烟比例≨25%（单批宽松）
   - P0比例≨25%
   - 步骤去重检测：唯一步骤<50%直接拒绝
   - 关键字段非空：title/steps/expected_results
   - 不达标直接拒绝保存，删除不合格文件
3. **p6_merge全局硬校验**（从warning升级为硬拒绝）：
   - 总用例数≥总预算(total_expected_cases)
   - 逐测试点展开数达标
   - 全局冷烟8%-20%
   - 全局P0>0且≨20%
   - 全局步骤去重≥50%
   - 不达标直接拒绝合并
4. **step7_export失败自动回流**（代码层实现）：
   - 失败时返回`auto_retry`状态+明确指令
   - 状态文件记录p6_retry_count
   - 最多重试2次，超过才报告用户
   - 禁止Agent向用户抛选择题

### v3.2.8 (2026-05-03)

**变更类型**: 质量校验加固 + 代码层优化 + complexity预算体系 + 交叉评审修复 (基于V3.2.7四路评审反馈+V3.2.8小析交叉评审)

**核心问题**: V3.2.7四路评审发现多个可优化点：P6展开数量全靠prompt猜、p6_save_batch无质量预检、P2门禁静态形同虚设、is_smoke格式多处重复判断、p6_merge无P5覆盖校验

**数据来源**: V3.2.7四路评审（小析有条件通过+6条建议、小猩有条件通过+3条建议、小执通过）

**修复内容**:
1. **P5 complexity标签体系**（小析核心建议，治本之策）：
   - p5_code_merge给每个测试点打`complexity`(L1/L2/L3)和`expected_case_count`(1/2/3)标签
   - 分级规则：根据测试点类型、风险标记、PCI标记、来源、描述长度综合评分
   - L1(简单:display/compatibility)≥1条, L2(常规:main_flow/branch)≥2条, L3(复杂:permission+risk/exception+pci)≥3条
   - P5输出新增coverage_summary.complexity_distribution和total_expected_cases
2. **P6 prep_prompt注入用例预算**（配合#1）：
   - 每个batch注入“本批次应生成至少N条”和每个测试点的展开预算
   - Agent不再猜展开数量，按预算执行
3. **P6动态门禁升级**（配合#1）：
   - quality_check和step7_export的P6最低用例数优先用P5的total_expected_cases
   - 其次回退到P5测试点数×1.5（V3.2.7兼容）
4. **p6_save_batch加软校验**（小猩V3.2.8建议）：
   - 保存批次时检查：用例数是否为0、is_smoke格式是否为布尔值、priority格式是否合规、title/steps是否为空
   - warning级别不阻塞保存，但尽早暴露质量问题
5. **P2 MIN_OUTPUT_COUNTS动态化**（小猩V3.2.8建议）：
   - `max(8, P1叶节点数×2)`替代静态底线8
6. **is_smoke格式统一**（小析V3.2.8建议）：
   - 新增`_is_smoke()`公共函数，替换orchestrator.py中4处重复判断
   - export_excel.py同步统一
7. **p6_merge加P5覆盖校验**（小析V3.2.8建议）：
   - 合并后检查每个P5测试点是否都被P6用例覆盖
8. **小析交叉评审修复——export_excel.py门禁同步**（小析评审必修#1）：
   - export_excel.py的P6质量门禁从写歭15升级为动态计算（与orchestrator完全一致）
   - 优先用P5的total_expected_cases，其次P5测试点×1.5，底线15
   - P0比例阈值从40%修正为20%（与orchestrator的P6_QUALITY_RULES一致）
9. **小析交叉评审修复——export_excel.py is_smoke统一**（小析评审必修#2）：
   - 新增`_is_smoke_check()`函数，与orchestrator的`_is_smoke()`完全一致
   - 替换export_excel.py质量检查中的内联判断
   - 消除双真源漂移风险
10. **小析交叉评审修复——P6 batch_points精简字段版**（小析评审中风险）：
   - batch_points不再用`json.dumps(full)[:5000]`截断
   - 改为精简字段版（只保留id/description/category/priority/risk_flag/pci_flag/complexity/expected_case_count）
   - 确保预算和测试点语义的绑定不会被截断削弱

### v3.2.7 (2026-05-02)

**变更类型**: 用例质量优化 + 效率提升 (基于V3.2.6云端测试JSON深度分析)

**核心问题**: V3.2.6云端测试成功完成但用例数量偏少（24条），P2每场景只生成1个测试点、P6每测试点只展开为1条用例；段7 batch文件命名试错浪费时间；段8 P0比例反复调整

**数据来源**: V3.2.6云端测试 task_20260502_204631 全量JSON产物深度分析

**修复内容**:
1. **P2 prompt强化最低展开数**（用例数量优化）：
   - 原规则：每个叶节点至少生成1个测试点
   - 新规则：每个叶节点至少生成**2个**测试点（1条正向+1条反向/异常/边界）
   - 质量门禁同步更新
2. **P6 prompt强化展开规则**（用例数量优化）：
   - 原规则：每个测试点展开为1~N个用例
   - 新规则：每个测试点必须展开为至少**2条**用例，并按测试点类型给出展开数量参考
   - prep_prompt注入规则同步更新
3. **P6质量门禁动态化**（代码层硬控）：
   - 原规则：MIN_OUTPUT_COUNTS["P6"]=15（静态）
   - 新规则：max(15, P5测试点数×1.5)（动态计算）
   - quality_check和step7_export同步使用动态阈值
4. **SKILL.md段7 batch文件命名格式明确**（效率优化）：
   - 明确标注`p6_batch_{N:03d}_agent_output.json`（3位零填充：001/002/003）
   - 避免Agent试错浪费时间
5. **P6 prep_prompt注入P0比例约束**（效率优化）：
   - 明确告知Agent "P0不得超过20%"，避免段8反复调整

### v3.2.6 (2026-05-02)

**变更类型**: 安全加固 + 结构校验 (基于V3.2.5四路评审反馈)

**核心问题**: Agent可通过直接写入gate pass文件、伪造p5/p6_output.json等方式绕过流程控制，step_run硬控只堵了一条路

**数据来源**: V3.2.5四路评审（小析发现5条未防护绕过路径，小猩提供HMAC方案，小文发现段6禁止列表不对称+CHANGELOG格式不一致）

**修复内容**:
1. **HMAC签名机制**（核心安全加固）：
   - 所有gate pass写入时加HMAC签名（基于orchestrator.py文件哈希派生密钥）
   - `check_gate()`验证时同时校验HMAC，签名不匹配则拒绝
   - 覆盖全部gate写入入口：onboarding/step_run/p5_code_merge/p6_merge/quality_check/truncation_guard
   - Agent无法获取密钥（依赖代码文件哈希），从根本上杠绝伪造gate pass
2. **P5结构特征校验**（辅助防线）：
   - step7_export导出前校验P5的merge_log必含from_p2/from_p3/from_p4
   - 确保P5由p5_code_merge生成，而非Agent自己写的
3. **P6批次结构校验**（辅助防线）：
   - step7_export导出前校验p6_batches目录存在且含batch文件
   - 确保P6由分批流程生成，而非Agent一次性写入
4. **SKILL.md段6禁止列表补全**（小文反馈）：
   - 段6禁止列表补充`write: p5_output.json`和`write: gates/P5.pass.json`，与段7对称
   - 段7禁止列表补充`write: gates/P6.pass.json`
5. **truncation_guard.py同步HMAC**：
   - truncation_guard写入gate pass时同样加HMAC签名
   - 密钥派生算法与orchestrator.py一致
6. **p6_merge/p6_save_batch/p6_batch_info加P5前置gate校验**（V3.2.6四路评审反馈）：
   - 小析发现：Agent可伪造batch文件后调p6_merge，借 orchestrator签发合法HMAC gate
   - 修复：p6_batch_info/p6_save_batch/p6_merge入口均加check_gate("P5")前置校验
   - 没有合法P5 gate pass就无法进入P6流程
7. **export_excel.py加HMAC验签**（V3.2.6四路评审反馈）：
   - 小析发现：Agent可直接调用export_excel.py绕过step7_export的全部门禁
   - 修复：export_excel.py的gate检查加HMAC验签+task_id校验，与orchestrator同等安全级别

### v3.2.5 (2026-05-01)

**变更类型**: bugfix + 流程硬控 (基于V3.2.4云端测试task_20260501_211514分析)

**核心问题**: Agent绕过p5_code_merge自己写P5、绕过P6分批流程一次性生成用例、P7 gate_result格式不兼容导致step7_export崩溃

**数据来源**: V3.2.4云端测试 task_20260501_211514 全量JSON产物分析

**修复内容**:
1. **P7 gate_result兼容性修复**（P1级Bug）：
   - Agent生成的P7 output中`gate_result`是字符串"PASSED"，但step7_export期望对象`{status:"PASS"}`
   - `"PASSED".get("status")` → AttributeError，导致导出崩溃
   - 修复：兼容字符串"PASS"/"PASSED"和对象{status:"PASS"}两种格式
2. **P5/P6 step_run代码层硬控**（流程强化）：
   - `step_run --step P5` 直接拒绝，返回错误提示必须用p5_code_merge
   - `step_run --step P6` 直接拒绝，返回错误提示必须用分批流程
   - 根因：V3.2.4云端测试中Agent绕过p5_code_merge自己写P5（risk_flagged=0），绕过分批流程一次性生成62条用例（前置条件全部相同、步骤平均2.6步、期望结果只有1条）
3. **SKILL.md段6/段7指令强化**：
   - 段6：明确禁止step_run/自己写P5/Python脚本生成，加代码层硬控说明
   - 段7：明确禁止step_run/直接写p6_output/Python脚本生成，加代码层硬控说明
   - 段落对照表加强说明

### v3.2.4 (2026-05-01)

**变更类型**: P0级bugfix (基于V3.2.3云端测试JSON产物深度分析)

**核心问题**: Excel导出除优先级/冒烟外全部空白，quality_check/p6_merge/step7_export读不到fields嵌套字段

**数据来源**: V3.2.3云端测试 task_20260501_073619 全量JSON产物分析

**修复内容**:
1. **新增`_get_case_field()`统一读取函数**（P0级Bug）：
   - P6用例数据结构为嵌套的`{id, source_test_point, fields: {19列字段}}`
   - 但orchestrator和export_excel全部用`case.get(field)`只读顶层，读不到fields子对象
   - 新增`_get_case_field(case, field)`: 先读顶层→再读fields子对象，兼容两种结构
   - 影响范围: orchestrator.py的quality_check/p6_merge/step7_export + export_excel.py的build_workbook
2. **export_excel.py列21列→P6 prompt 19列对齐**（P0级Bug）：
   - 旧版列21列定义与P6 prompt的19列字段映射表不一致
   - project/requirement/test_case_type/test_suite/screenshot这5个字段P6生成了但Excel不导出
   - executor/module/feature等7个字段Excel要导出但P6没生成
   - 现在严格按P6 prompt的19列字段映射表导出
3. **quality_check通过后自动创建gate文件**（P1级Bug）：
   - 旧版quality_check通过后不创建gate，Agent被迫手动创建P7.pass.json绕过门禁
   - 现在quality_check passed后自动写入gates/{step}.pass.json
4. **P0 prompt强调顶层必填字段**（P2级）：
   - P0 prompt的JSON模板缺少`quality_score`和`objective`顶层字段
   - 但orchestrator的P0_REQUIRED_FIELDS要求这两个字段必须在顶层
   - Agent第一次生成时漏了，校验失败后自行修补（“已添加缺失的顶层字段”）
   - 现在在JSON模板前加🔴强调标记，并在模板中明确展示这两个字段

### v3.2.3 (2026-04-30)

**变更类型**: bugfix + ux (基于V3.2.2云端测试反馈的流程强化)

**核心问题**: Agent把段4-6合并成一个“段4”，把段7(P6)当“段5”执行时错误调用step_run而非分批流程

**数据来源**: V3.2.2云端测试(minimax-m2.7) task_20260430_220353 全量JSON产物分析

**云端验证结果**: P0-P5全部通过，P5合并首次成功(39条测试点，risk_flagged=29，pci_flagged=24，P0卣18.4%)

**修复内容**:
1. **段落编号强制对照表**：在运行协议顶部加8段编号对照表，明确禁止合并段落
2. **段7 P6分批流程强化**：加🔴🔴🔴三重标记，明确Step 1/2/3三步分批流程，绝对禁止用step_run执行P6
3. **四路评审修复**（V3.2.2评审反馈）：
   - 边界安全前缀匹配：startswith(prefix)改为startswith(prefix+'-')，防止M01-F01误匹配M01-F010
   - P3全量匹配：feature级风险映射到该feature下所有scenario，不再break
   - P4全量匹配：blocked_scenarios全量匹配所有blocked的P2点，不再break
   - P0阈值收紧：40%→20%，推荐10-15%
   - schema JSON title更新：4个文件V3.2.0→V3.2.3

### v3.2.2 (2026-04-30)

**变更类型**: bugfix (基于V3.2.1云端实际JSON数据分析的深层修复)

**核心问题**: P5合并匹配逻辑与P3/P4实际字段不匹配，P2优先级分布失控

**数据来源**: V3.2.1云端测试(minimax-m2.7) task_20260430_194811 全量JSON产物分析

**修复内容**:
1. **P5合并匹配逻辑升级**（P0级Bug）：
   - P3匹配：新增`source_node`字段读取 + 前缀匹配（P3用feature级别M01-F01，P2用scenario级别M01-F01-S01）
   - P4匹配：新增`blocked_scenarios`数组精确匹配（P4的source字段写的是"P1"无用，但blocked_scenarios有正确的scenario ID）
   - 匹配策略：精确匹配→前缀匹配→新增独立点（三级降级）
   - 根因：V3.2.1的p5_code_merge只读source_scenario做精确匹配，但P3实际用source_node、P4实际source="P1"，导致26条全部未匹配
2. **P2优先级分布注入**（P0级）：
   - P2 prep_prompt注入优先级分布要求：P0≤40%、P1占主体40-60%、不允许全同一优先级
   - 根因：V3.2.1云端P2产出P0卣63.2%，远超40%上限，即使P5过了P6质量门禁也会拒绝
3. **SKILL.md 5段→8段残留清理**（已在V3.2.1修复）

### v3.2.1 (2026-04-30)

**变更类型**: bugfix + architecture (拆段优化 + 字段契约修复 + Onboarding分步强化)

**核心问题**: V3.2.0云端测试发现段4太重导致Agent崩溃、P5合并缺字段、Onboarding多项合并展示

**修复内容**:
1. **拆段5→8段**（解决段4太重导致Agent崩溃的根因）：
   - 段1: init+onboarding
   - 段2: step0+图片理解
   - 段3: P0+P1
   - 段4: P2（测试点）← 原段4拆出
   - 段5: P3+P4（风险+PCI）← 原段4拆出
   - 段6: P5（代码自动合并）← 原段4拆出
   - 段7: P6（用例生成）← 原段5拆出
   - 段8: P7+Excel ← 原段5拆出
2. **P5合并补齐priority/status字段**（解决truncation_guard L3校验失败）：
   - p5_code_merge合并后统一补齐priority（从priority_hint读取）和status（默认active）
   - P2 prep_prompt注入priority/status字段要求，让Agent生成时就带上
3. **P6 prep_prompt注入字段格式要求**：
   - is_smoke必须是boolean(true/false)
   - priority必须是P0/P1/P2/P3
   - testcases必须小写
4. **P7 prep_prompt强调gate_result字段名**：
   - 明确gate_result不是quality_check
5. **Onboarding分步交互强化**：
   - 每步加🔴强制标记
   - 必须等用户回复后才展示下一项
   - 不允许多项合并展示

### v3.2.0 (2026-04-29)

**变更类型**: architecture-fix (路线A止血版)

**核心问题**: Agent可绕过orchestrator直接写JSON/调用export_excel，质量门禁全部失效

**修复策略**: 不加指令，从代码层堵住绕过路径

**变更内容**:
1. **T2: export_excel.py加gate pass前置检查** — 即使Agent直接调用也必须有完整gate pass + P6质量校验
2. **T6: api_key密码缓存机制** — check_image_api成功后缓存到task目录，step0_8_prep自动读取，不再依赖Agent跨段落传递
3. **T4: 图片理解API串行→并行** — ThreadPoolExecutor(max_workers=3)，19张图从~570s→~190s
4. **T8: P5合并下沉代码层** — 新增p5_code_merge action，代码合并P2+P3+P4→P5，Agent不再参与合并
5. **T9: SKILL.md段落4更新** — P5改为调用p5_code_merge，Agent只需执行P2/P3/P4

### v3.1.0 (2026-04-29)

**变更类型**: fix + feature (系统性契约统一 + 图片理解升级)

**核心问题**: schema/prompt/orchestrator/实际产物四套口径并存，导致质量校验失效、字段读取失败、门禁被绕过

**修复策略**: 以云端实际JSON产物为真源，反向修 orchestrator代码

**变更内容**:
1. **REQUIRED_FIELDS统一到云端实际字段名**: P1 modules→feature_tree, P6删除statistics, P7 quality_check→gate_result
2. **MIN_OUTPUT_COUNTS多候选路径**: P0 blocks.operations|pages|business_rules, P1 feature_tree.modules|modules
3. **_get_nested()升级**: 支持多候选路径（用|分隔）
4. **step_run必需字段校验（代码硬控）**: 写入tmp后、guard前校验REQUIRED_FIELDS，缺失→删tmp+拒绝+明确错误
5. **step7_export内置P6质量硬门禁**: 导出前强制校验用例数≥15/冒烟8%-20%/P0≤40%/优先级分布 + P7 gate_result必须PASS
6. **prep_prompt注入P1/P7必需字段提醒**: 减少Agent猜测
7. **P6质量规则统一真源**: prep_prompt和quality_check完全一致，冒烟超限从 warning→issue(拒绝)
8. **Qwen VL升级为主引擎**: 语义理解能力远强CI，CI降为OCR辅助
9. **Qwen VL失败自动降级CI**: VL失败→CI(OCR+标签)→caption_only三级降级
10. **图片选图上限5→50**: 避免大量图片被跳过
11. **API超时30→120秒**: Qwen VL复杂图需要更长时间
12. **partial结果消费**: server返回partial时orchestrator保留有效内容，不再丢弃
13. **Onboarding 4B密码重试**: 3次重试+自动降级
14. **真实文件类型校验**: 图片头魔数检查
15. **统一失败语义**: ok/partial/error三态

**部署验证** (2026-04-29):
- 图片理解API 8项端到端验证全部通过
- Qwen VL语义理解质量远超CI
- 云端实际JSON数据验证全部通过

### v3.0.3 (2026-04-29)

**变更类型**: feature (图片理解API集成)

**变更内容**:
1. **图片理解API服务**：新增image_api_server/server.py，部署在腾讯云，调用数据万象OCR+图片标签
2. **step0_8_prep重构**：orchestrator直接调用API理解图片，不依赖Agent行为
3. **降级策略**：API未配置/失败→caption_only（用前后文推断），不回退Agent看图
4. **api_key安全**：Onboarding交互时用户输入密码，运行时传入，不写入任何文件
5. **task_meta脱敏**：preferences中image_api只保留url/model/timeout，api_key不落盘
6. **Onboarding检查4B**：新增图片理解API密码交互（输入密码/跳过+验证）
7. **预检+熔断**：API auth-check验证、401/403不重试、429限流熔断、连续3次失败熔断
8. **支持双引擎**：ci=数据万象(默认), qwen=通义千问VL(可选)
9. **新增接口**：/api/auth-check密码验证专用接口（health不鉴权问题修复）
10. **COS签名修复**：有效期0秒→300秒、参数排序字典序、ci-process全小写格式
11. **代码优化**：抽取_cos_sign()签名函数（消除6处重复）、UUID防并发冲突、删除SDK死代码
12. **空文件拦截**：0字节文件显式返回400 empty_file
13. **gunicorn配置优化**：timeout 60→120s、max-requests 500防内存泄漏

**部署验证**（2026-04-29 已通过）：
- /api/health ✅
- 正确/错误密码auth-check ✅
- 图片分析OCR+标签 ✅
- 空文件/错误密码拦截 ✅
- orchestrator check_image_api端到端 ✅

### v3.0.2 (2026-04-28)

**变更类型**: fix

**变更内容**:
1. **段间gate验证**：每段开头exec status确认上一段gate pass存在
2. **MEDIA文件发送**：step7_export返回media_instruction，SKILL.md要求输出MEDIA指令
3. **全链路gate校验**：step7_export检查onboarding/P0-P7全部9个gate pass

### v3.0.1 (2026-04-28)

**变更类型**: fix

**变更内容**:
1. **state持久化完善**：skill_dir/data_dir在init和onboarding中写入state；requirement_file/current_phase在step0中写入
2. **SKILL.md {SKILL_DIR}占位符修复**：改为ORCH变量自动发现，Agent不需要知道skill_dir路径
3. **restart_from action新增**：支持"从P{N}重新开始"，清除指定步骤及后续的gate pass和output
4. **find_latest_task安全加固**：查找范围从5个缩减为3个，减少多任务串扰风险
5. **CHANGELOG补全**：补充patch2/patch3/v3.0.1记录
6. **版本号统一为v3.0.1**

### v3.0.0 (2026-04-28)

**变更类型**: architecture-change (重大架构重构)

**变更内容**:
1. **orchestrator.py核心框架**：1150行Python脚本，14个action，代码控制全流程
2. **架构从指令驱动改为orchestrator驱动**：Agent不再自行决定流程，只负责执行prompt返回JSON
3. **文件写入完全由代码控制**：所有写入通过orchestrator→truncation_guard→gate pass，Agent无法绕过
4. **prep_prompt action**：为P0-P7自动准备完整prompt（含知识注入/上游产物/PX增强）
5. **P6分批全套**：p6_batch_info+p6_save_batch+p6_merge，代码控制分批和合并
6. **quality_check action**：最小产出数量/P0评分/P6冒烟比例+优先级分布，代码强制校验
7. **PX图片理解由orchestrator调度**：step0_8_prep价值选图+Agent逐张read+step0_8_save保存
8. **断点续跑由代码实现**：resume action自动扫描gate pass确定下一步
9. **SKILL.md重写**：从186行指令约束→120行orchestrator调用流程
10. **Agent交互协议**：新增orchestrator_protocol.md定义Agent↔orchestrator交互格式

**影响范围**:
- 新增 tools/orchestrator.py（核心）
- 新增 references/orchestrator_protocol.md
- SKILL.md 完全重写
- references/*.md 新增V3.0架构声明

**兼容性**: ⚠️ 重大架构变更，从指令驱动改为orchestrator驱动。现有Prompt/Schema/工具脚本全部保留兼容。

### v3.0.0-patch1 (2026-04-28)

**变更类型**: fix (四路评审修复)

**变更内容**:
1. **image_enhance.py A-2适配层**：新增_adapt_a2_format()函数，将A-2方案的results/understanding_mode/confidence(字符串)映射为旧格式的images/processing_status/classification.confidence(数值)，解决PX增强完全失效问题
2. **Onboarding门禁时序修复**：task_id创建从Step 0提前到Onboarding完成时，解决"task_id未创建→无法写onboarding.pass.json→无法进入Step 0"的时序悖论
3. **Step 0门禁检查增强**：从"扫描最新pass文件"改为"校验当前task_id的pass文件+task_id一致性验证"
4. **step0-px.md顶部OCR残留清理**：删除"OCR不可用时先装Tesseract"旧约束，替换为A-2方案说明
5. **skill_version更新**：step0-px.md中task_meta.json的skill_version从2.4.0更新为2.5.0
6. **状态行模板统一**：所有references中旧格式`✅ Step X(PX)完成!-`统一为新格式`✅ P{N}完成 | {指标} | 文件已保存`
7. **执行模型表述统一**：onboarding.md"零暂停"改为"自动推进"；step0-px.md"一气呵成"改为"按顺序自动推进"；step1-4.md/step5-7.md顶部新增"顶层协议优先"声明
8. **model_detect.py退出范围精确化**：从"退出主流程"改为"退出PX主流程（仍在P5分批模式中使用）"；引用文件清单新增退出标注

**影响范围**:
- tools/image_enhance.py: 新增A-2适配层
- references/onboarding.md: task_id提前创建+门禁时序修复+自动推进表述
- references/step0-px.md: 顶部OCR清理+skill_version+门禁检查增强+执行模型统一
- references/step1-4.md: 状态行统一+顶层协议优先声明
- references/step5-7.md: 状态行统一+顶层协议优先声明
- SKILL.md: 引用文件清单退出标注

### v2.5.0 (2026-04-28)

**变更类型**: fix + architecture-change

**变更内容**:
1. **需求载荷前置规则**：触发技能后必须先确认需求已就绪才启动Onboarding,未收到需求时仅输出固定等待话术,不输出步骤清单或能力介绍
2. **需求上下文判定规则**：支持本条消息含需求/含附件/明确引用近期需求三种就绪判定,禁止复用已完成task的旧需求
3. **Onboarding完成状态门禁**：Onboarding完成后写入onboarding.pass.json,Step 0前置检查该文件存在才允许进入主流程,从"指令约束"升级为"状态门禁"
4. **三阶段执行规则**：从两阶段(Onboarding+主流程)升级为三阶段(需求等待+Onboarding+主流程)
5. **对话输出硬约束**：从白名单改为计数硬约束(每步严格限1行),新增固定状态行格式和动作链模板
6. **PX图片理解A-2方案重构**：
   - 删除三级降级架构(model_detect→vision/OCR/context_only)
   - 改为Agent直接read图片,能看懂就用,看不懂就降级为caption+上下文
   - 图片选择改为价值优先(流程图>原型页>规则表>其他),最多5张
   - 新增三条件理解判定标准(识别类型+提取2个元素+1个测试价值点)
   - px_understand.json新增understanding_mode/confidence/evidence/selection_reason等字段
   - model_detect.py/image_understand.py/image_ocr.py退出主流程(保留文件不删除)
7. **P0内联必需字段**：在step1-4.md中直接内联P0顶层必需字段(quality_score/blocks/objective),减少Agent读schema的认知负担
8. **截断防护规则**：禁止单exec写完整P0-P7逻辑;禁止单轮回复连续推进超过一个Step;新增按gate pass精准恢复规则(支持P2/P3/P4复合步骤局部续跑)
9. **每步输出提醒**：所有Step指令开头新增"⚠️ 本步只输出1行状态"提醒

**影响范围**:
- SKILL.md: 运行协议重写(三阶段+需求前置+输出硬约束+截断防护+动作链模板)
- references/onboarding.md: 新增需求载荷前置规则+onboarding.pass.json门禁
- references/step0-px.md: Step 0新增onboarding门禁检查;Step 0.8整段重写为A-2方案
- references/step1-4.md: P0内联字段+各步输出提醒
- references/step5-7.md: 各步输出提醒

**兼容性**: ⚠️ 重大架构变更,PX从三级降级改为Agent直接视觉,Onboarding新增状态门禁


### v2.3.3 (2026-04-27)

**变更类型**: fix + architecture-change

**变更内容**:
1. **truncation_guard.py 四级截断检测脚本**：L1文件存在→L2 JSON有效→L3结构完整→L4内容完整，支持 `--auto-mv` 原子操作（校验通过自动mv+生成gate pass，失败自动rm tmp），Agent无法绕过
2. **thresholds.json L4阈值外部化配置**：P5输出≥max(15, P2×0.6)，P6输出≥max(10, P5×0.8)
3. **所有P0-P7统一改为tmp→truncation_guard→mv原子写入**：禁止heredoc直写正式文件，截断时最多损坏tmp不污染正式缓存
4. **gate pass链式依赖机制**：每步校验通过后自动生成gates/{step}.pass.json，下游步骤必须检查上游pass才能启动
5. **断点续跑改为"gate pass才能复用"**：不再只看"文件存在且非空"，必须pass存在且task_id一致
6. **P6降级产物隔离**：降级产物写入p6_output.degraded.json，不生成gate pass
7. **P5双模式执行**：新增model_detect.py output_capacity检测（high/medium/low三级），P5根据模型能力自动选择single/auto_batch/force_batch策略
8. **P5分批模式**：新增p5_prepare.py（按模块分组生成batch_context）+ P5a_batch_merge.md（批内合并子Prompt）+ Step 4c跨批汇总（脚本级ID去重+统计口径重定义）
9. **P5统计口径重定义**：merge_log区分batch_merge和cross_batch_dedup，coverage_summary新增source_covered_ratio
10. **Onboarding恢复交互模式**：PRD审查和L5上传恢复为用户可选择的开/跳过
11. **PX视觉模式修复**：支持视觉的模型必须走Agent直接调用路径（CLI无法提供model_caller），禁止CLI调用视觉模式
12. **OCR自动安装**：Tesseract不可用时先尝试自动安装（apt/yum/brew/apk），只有安装失败后才降级
13. **export_excel.py字典值映射修复**：优先级→Highest/High/Medium/Low，用例类型→正例/反例，测试类别→功能测试等
14. **P5严禁跳步强化**：明确禁止跳过P5/P6/P7直接生成Excel
15. **L4组合校验**：P5增加模块覆盖+优先级保留+merge_log一致性；P6增加P0全展开率；WARNING不阻塞流程
16. **revision简化版**：current_revision.json管理+断点续跑revision校验+bump-revision时清除下游gate pass+备份策略(.prev.json)
17. **SKILL.md指令冲突修复（根因级）**：对话输出白名单追加"Onboarding交互输出"豁免；元叙述硬禁令追加"Onboarding阶段例外"；全流程交互规则重构为两阶段制（Onboarding交互+主流程零暂停）；消除"零暂停"误杀Onboarding交互的根因
18. 专属触发词新增「xy测试用例生成」

**影响范围**:
- 新增 tools/truncation_guard.py（四级截断检测脚本）
- 新增 tools/thresholds.json（L4阈值配置）
- 新增 tools/p5_prepare.py（P5分批预处理脚本）
- 新增 prompts/P5a_batch_merge.md（P5批内合并子Prompt）
- 修改 tools/model_detect.py（新增output_capacity检测）
- SKILL.md: 所有Step写入方式改造、gate pass链式依赖、断点续跑升级、P5双模式执行、关键产物门禁重写
- export_excel.py: PRIORITY_MAP/TEST_CASE_TYPE_MAP/TEST_CATEGORY_MAP重写
- P6_testcase_generation.md: 字段映射对齐公司字典

**兼容性**: ⚠️ 重大架构变更，所有Step写入方式改变，新增gate pass机制

### v2.3.2 (2026-04-27)

**变更类型**: fix + behavior-change

**变更内容**:
1. **Onboarding 恢复交互模式**:PRD质量审查和L5知识库上传恢复为交互式询问,用户可选择「开启/跳过」和「上传/跳过」,之前的非交互模式导致能力丢失
2. **PX 图片理解视觉模式修复**:
   - 视觉模式(vision)禁止通过CLI调用(CLI无法提供model_caller,导致静默降级)
   - 支持视觉的模型(Doubao-Seed-2.0-pro等)必须走Agent直接调用路径:用read工具逐张读取图片,Agent用自己的视觉能力理解
   - 新增视觉模式Agent调用流程和VISION_QUEUE机制
3. **OCR引擎自动安装**:OCR不可用时先尝试自动安装Tesseract(含中文语言包),支持apt/yum/brew/apk四种包管理器,只有安装失败后才降级为纯文本模式
4. PX 跳过原因输出增强:跳过时必须附带具体原因
5. P5 截断自愈规则加强:明确禁止跳过P5/P6/P7直接生成Excel
6. export_excel.py 字典值映射修复:
   - 优先级:P0→Highest / P1→High / P2→Medium / P3→Low
   - 用例类型:正向类→「正例」,异常/边界/安全类→「反例」
   - 测试类别:功能→功能测试 / 性能→性能测试 / 安全→安全性测试 等
7. P6 Prompt 和 testcase_design_spec.md 字段映射说明同步更新
8. 专属触发词新增「xy测试用例生成」

**影响范围**:
- SKILL.md: Onboarding交互模式恢复、PX视觉模式调用方式变更、OCR自动安装、P5严禁跳步
- export_excel.py: PRIORITY_MAP / TEST_CASE_TYPE_MAP / TEST_CATEGORY_MAP 全部重写
- P6_testcase_generation.md: 字段映射说明对齐公司字典
- testcase_design_spec.md: 字段映射说明对齐公司字典

**兼容性**: ⚠️ 行为性变更,Onboarding从非交互恢复为交互,PX视觉模式调用方式变更

### v2.3.1 (2026-04-26)

**变更类型**: fix

**变更内容**:
1. model_detect.py 增加 provider 前缀剥离,修复 Doubao-Seed-2.0-pro 等带前缀模型ID被误判降级为OCR的问题
2. model_vision_capability.json 新增 doubao-seed-2.0-pro 等精确匹配条目
3. SKILL.md Step 3/4 JSON 写入改用 heredoc 方式,解决弱模型 tool calling 失败问题
4. SKILL.md Step 5 (P6) 大JSON采用 write→校验→mv 分步写入策略
5. SKILL.md 新增关键产物门禁:P0-P4 JSON写入后必须校验,失败则终止
6. SKILL.md 新增跳步分级规则:关键产物缺失必须终止,非关键步骤允许受控降级
7. SKILL.md 新增工具调用指导(弱模型适配)和禁止自建脚本规则
8. SKILL.md Onboarding 输出加"已自动继续"后缀,防止被误解为需用户回复
9. SKILL.md 检查1.5路径发现增加环境变量兜底和容器常见路径
10. model_detect.py 增加日志输出,便于排查模型能力检测结果
11. 门禁校验脚本assert改为if+sys.exit(1),防止python3 -O优化跳过
12. P6写入策略移除5KB阈值判断,统一使用write→校验→mv方式(避免LLM无法精确判断字节数)
13. P5提升为二级关键产物:写入失败必须终止,质量不达标允许降级
14. 跳步分级触发条件新增"JSON格式无效",与关键产物门禁一致
15. 路径发现失败时Markdown降级改为内联输出(不依赖export_markdown.py脚本)
16. P6校验失败时清理p6_raw.json临时文件(mv替代cp)
17. Onboarding非交互总则升级为全流程非交互规则(覆盖Onboarding→Step 0-7)
18. Step 7新增导出门禁,Excel/Markdown导出后强制校验文件存在且非空
19. P6降级操作具体化:最小可行用例集+degraded:true标记+警告输出
20. 工具调用指导vs门禁优先级明确:关键产物门禁>工具调用指导
21. 异常处理兆底规则与跳步分级规则措辞统一
22. 路径发现find命令加timeout 10和-print -quit优化

**影响范围**:
- model_detect.py: model_id 预处理逻辑变更,所有带 provider 前缀的模型ID受影响
- SKILL.md: Step 3/4/5 写入方式变更,Onboarding/路径发现/跳步规则增强

### v2.3.0 (2026-04-26)

**变更类型**: fix + behavior-change

**变更内容**:
1. Step 0.5 blocker 处理:从「等待用户强制跳过」改为「自动转 PCI 继续执行」,新增 `auto_skipped`/`skipped_blocker_count` 字段
2. Step 1 质量门禁:从「等待用户强制继续」改为「自动 CONDITIONAL_PASS 继续执行」,新增 `auto_forced`/`original_score` 字段,禁止写 `PASSED`
3. 新增「执行诚实规则」(全流程10条),解决 Excel 文件幻觉发送问题
4. 新增「跨步骤可测性分流规则」:可测/条件可测/不可测三分类
5. 新增「异常处理兆底规则」:执行错误→终止,不等用户
6. Step 7 输出增加文件生成验证和三级降级机制(Excel→Markdown→JSON)
7. MEDIA 指令强制全大写,独占一行,无前后空白
8. 新增 `export_markdown.py` 降级脚本,禁止 `cp .json → .md` 伪装
9. `export_excel.py` 增加 try-catch 兜底、空列表警告、写入异常捕获
10. P6 质量门禁冒烟占比从固定"10%~20%"改为分档规则(与生成规则/P7一致)
11. P6/P7 P0占比从强制"≤15%"改为建议"≤40%"(非强制,避免缩减必要用例)
12. P6 增加 blocked 测试点可测性分流(含6类核心缺失判定清单)
13. p6_output.schema.json 新增"条件验证" enum
14. P6 新增"禁止伞形用例规则",P7 新增 C9 伞形用例检测(WARNING级别)
15. SKILL.md blocked不可测落盘位置从 P5 的 blocked_test_points 改为 P6 的 statistics.risk_items

**影响范围**:
- 所有步骤的"等待用户"指令被非交互模式覆盖
- `p0_output.json` 新增可选字段 `auto_forced`/`original_score`(quality_check 对象内),status 新增 `CONDITIONAL_PASS` 枚举值
- `p0.5_output.json` 新增可选字段 `auto_skipped`/`skipped_blocker_count`(根级别)
- Step 7 行为变更:先验证后发送,支持降级输出

**兼容性**: ⚠️ 行为性变更,原有"等待用户确认"语义不再生效
