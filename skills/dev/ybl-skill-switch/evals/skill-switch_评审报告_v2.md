# ybl-skill-switch 评审报告 v2（独立评审）

**评审人**：工程工作流教练（本窗口）
**评审对象**：`~/.workbuddy/skills/ybl-skill-switch/`
**基线**：v1（工序达 Rex，APPROVE WITH CHANGES）6 条已闭环；本评审独立重验 + 找新问题
**评审日期**：2026-07-22

---

## Review Summary

**Verdict: REQUEST CHANGES**

**Overview:** 这是一个设计清晰、触发契约规范、示例已对齐真实测试的 Skill 开关管理器。但 v1 闭环后引入了一个**致命正确性问题**：当前 30/41（73%）的已安装 Skill 根本没有 `disable` 字段，而启用/禁用流程的 Edit 步骤写死了"改字段值"，对无字段 Skill 会直接操作失败。这与其核心目标（禁用任意已安装 Skill）直接矛盾，必须修。

---

## Critical Issues（合并前必须修）

### [C1] 禁用流程对"无 disable 字段"的 Skill 会直接失败
- **位置**：`SKILL.md:31`（禁用流程 step 3）
- **描述**：流程写死「用 Edit 工具将目标 SKILL.md 的 `disable: false` 改为 `disable: true`」。但实测 `~/.workbuddy/skills/` 下 **41 个 Skill 中有 30 个（73%）根本没有 `disable` 字段**（含 humanizer、全部 ybl-* 系列、wechat-*、skill-creator 等）。
- **后果**：禁用一个"当前启用且无字段"的 Skill（如 humanizer、ybl-editor）时，Edit 的 old_string `disable: false` 在文件里不存在 → **工具报错，禁用操作失败**。等于这个管理器无法禁用绝大多数已安装 Skill。
- **修复**：
  ```
  禁用流程 step 3 改为：
  1) 读目标 frontmatter，判断是否存在 `disable:` 字段
  2) 若字段存在：
       - 当前 true → 改为 false（已是禁用，提示无需操作）
       - 当前 false → 改为 true（执行禁用）
  3) 若字段不存在（默认启用）：
       - 在 frontmatter 插入 `disable: true`
         （锚定 `version: x.y.z` 行后，或 `---` 结束符前，用 Edit 插入一行）
  ```

### [C2] Gotchas G1 与可执行流程自相矛盾（空头支票）
- **位置**：`SKILL.md:65`（G1 注释）vs `SKILL.md:24,31`（流程 Edit 步骤）
- **描述**：G1 写明「没有 disable 字段 = 默认启用，视为 `disable: false`」——认知正确。但 line 24/31 的 Edit 步骤**只实现了"字段存在"分支**，既无分支处理无字段，也没落地 G1 的意图。G1 成了没有被流程支持的装饰性说明。
- **修复**：C1 修好后，G1 自然成立；否则删掉 G1 以免误导。

---

## Important Issues（合并前应修）

### [I1] 启用流程对"已启用且无字段"Skill 会误导报错
- **位置**：`SKILL.md:24`
- **描述**：用户说「打开 humanizer」，扫描发现无字段（已启用），step 3 却去把 `disable: true` 改 `false` → Edit 失败。正确行为应是识别为已启用 → 反馈「已启用，无需操作」。与 C1 同源，随 C1 一起修。

### [I2] 白名单管理流程不可触发（死代码）
- **位置**：`SKILL.md:34-39`（白名单管理流程）+ `SKILL.md:4`（description 触发词）
- **描述**：body 写了「把 XX 加入/移出白名单」的完整流程，但 description 触发词里**没有**"白名单"字样。用户说这句话时，ybl-skill-switch 大概率不触发 → 这段流程成死代码。
- **修复**：在 description 补「管理白名单」触发词，或 body 注明"此流程需配合主触发词/手动调用"。

### [I3] 白名单"列表"实际不存在
- **位置**：`SKILL.md:38`（"在本 SKILL.md 的白名单列表中增删条目"）vs `SKILL.md:45-46`（仅硬编码单一项）
- **描述**：body 只有 `- ybl-skill-switch（自身）` 一项，没有可供"增删"的列表结构。要加 XX 得 Edit 插入 `- XX` 行，可行但非字面"列表增删"，易混淆。
- **修复**：明确写为"在白名单区块追加/删除一行 `- <skill名>`"，或直接说明白名单存于 SKILL.md 本节。

---

## Suggestions（建议改进）

### [S1] few-shots 未覆盖 73% 主流场景
- **位置**：`references/few-shots.md`
- **描述**：三例全是"字段存在"情况（market-researcher / github 均有 `disable: true`）。应补一个"无字段"示例：如「打开 humanizer」→ 报告已启用无需操作；或「关闭 ybl-editor」→ 需新增 `disable: true` 字段。这正是真实失败模式。

### [S2] 端到端未经本 Skill 自身验证
- **描述**：我们之前手动做的启用/禁用（market-researcher、github），是我在对话里**直接调 Edit** 完成的，**没有走"触发 ybl-skill-switch → 扫描 → 列候选 → 确认 → Edit"这条完整链路**。Skill 自身执行路径未实证。C1 修复后建议实跑一次「关闭某个无字段 Skill」做验收。

### [S3] 简洁性可再收
- **位置**：全文件（69 行）
- **描述**：用户要求"简洁"。白名单管理（用得少）占 6 行 + 流程 6 行。核心正确性修好后，可考虑把低频的"白名单管理"精简为单行指引外移，但优先级低于 C/I 类。

---

## What's Done Well

- ✅ **触发契约集中且规范**：`description` 只放触发词 + 正负触发，机制细节放 body（SKILL.md:4,12），分工干净
- ✅ **Gotchas G2/G3/G4 正确**：自保护（不禁用自身）、需用户确认、不碰 plugins/，三条都站得住
- ✅ **few-shots 已对齐真实测试**（上轮修正成果）：三例均对应本窗口实测，非编造
- ✅ **allowed-tools 显式收敛**：`Read, Edit, Glob, Grep`，权限面收得紧
- ✅ **evals 三件套齐全**：test-cases.yaml / eval-report.md / regression-log.md
- ✅ **无 index.yaml 陈旧引用**：早期设计提过，当前已改实时扫描，无残留

---

## Verification Story

- **测试 reviewed**：`evals/test-cases.yaml` 12 用例；`eval-report.md` 八维 4.85
- **评测覆盖盲区**：TC01/TC02 均描述"字段存在"场景（market-researcher/github），**无"无字段"用例** → 评测未覆盖 73% 主流失败模式（与 C1 同源）
- **真实端到端执行**：❌ 未验证（见 S2）
- **构建/安全**：N/A（纯提示词 Skill，无代码）

---

## 修复优先级

```
P0  C1  禁用流程支持"无字段"Skill（插入 disable: true）   ← 不修则管理器废掉 73% 功能
P0  C2  G1 与流程对齐（随 C1 自然解决）
P1  I1  启用流程识别"已启用无字段"→ 反馈无需操作
P1  I2  白名单管理补触发词（否则死代码）
P1  I3  白名单"列表"措辞明确化
P2  S1  few-shots 补无字段示例
P2  S2  修复后实跑端到端验收
P2  S3  简洁性再收（可选）
```
