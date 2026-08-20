---
name: equipment-repair-assistant
display_name: 设备智能报修助手
display_name_en: Equipment Repair Assistant
description: Worker reports a faulty machine in voice; AI matches the equipment, picks the fault reason and creates a repair order. Supports query, start/finish repair and repair-item reminders.
description_zh: 工人说设备+故障，AI 匹配设备、语音选择故障原因后自动生成维修单；支持查询维修单、开始维修、结束维修并按维修项目提醒填写。
description_en: Worker reports a faulty machine in voice; AI matches the equipment, picks the fault reason and creates a repair order. Supports query, start/finish repair and repair-item reminders.
category: productivity
version: 1.0.0
author: "Digihua"
trigger:
  - 报修
  - 维修
  - 设备报修
  - 故障
  - 设备坏了
  - 开始维修
  - 维修完成
  - 结束维修
  - 修一下
  - 修好了
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
---
# 设备智能报修助手（对话模式 · 报修+开始+结束三阶段）

## ⚠️ 执行原则（用户定稿 2026-08-07：精简确认流程）

**校验无问题 → 直接执行，不再让工人二次确认。** 只有出现歧义/异常才停下来问：

- ✅ **直接执行**：设备唯一匹配 + 原因唯一（序号或名称精确命中）+ 状态机校验通过 → 立即调接口，反馈结果
- ⏸ **停下来问**（仅这几种情况）：
  1. 设备匹配到多条候选 → 让工人选
  2. 原因名称模糊（多个命中）或工人说"其他" → 列候选让工人选/询问
  3. 状态机校验不通过（如对状态3执行结束）→ 提示当前状态和可执行动作，不执行
  4. 设备/维修单不存在 → 提示重输

**防重复执行铁律（仍有效）：**
- 一次报修/开始/结束请求，**只能执行一次**；如果 AI 不确定是否已执行，先查维修单（`list`）确认状态，不要盲目重跑。
- `--dry-run` 保留为兜底手段：仅当结果有重大不确定性（如候选人过多需先展示清单）时用，常规操作直接执行。
- 写接口（AIEqError/AIsendEqMainRecord）返回 `code=1 "状态错误"` 但**实际成功**（已实测），CLI 内部会回查确认，AI 不要据此判失败。

```
# ✅ 正常流程：校验通过 → 直接执行（不再预览确认）
python repair_tool.py --action create --eq "数控中心" --reason "主轴轴承磨损"
# ⏸ 仅多候选/歧义时：先 candidates/list 展示 → 工人选定后直接执行
python repair_tool.py --action candidates --eq "数控中心"
```

---

## 核心理念

工人对话说一句话 → AI 解析（设备/原因/动作）→ 调查询接口匹配 → 生成候选/预览 → 确认 → 执行。

**三个执行点：**
- `create`（报修）→ `AIEqError` 生成维修单，状态=3待维修
- `start`（开始维修）→ `AIsendEqMainRecord(mainOperate=1)`，仅对状态3
- `end`（结束维修）→ `AIsendEqMainRecord(mainOperate=2)`，仅对状态5，填 mainRecord 项目结果

**状态机（用户确认）：**
```
待维修(3) ──开始(mainOperate=1)──▶ 维修中(5) ──结束(mainOperate=2)──▶ 维修完成(4)
    只允许开始                         只允许结束
```
- 我们只管 **待维修(3)** 和 **维修中(5)** 的单；状态4/0/1/2 不操作。
- **开始只对状态3，结束只对状态5**，CLI 已内置校验（status_mismatch 会拒绝）。

---

## 完整链路

```
工人输入 → AI解析(设备?/原因?/动作?)
  → 动作识别：
     "报修/设备坏了/修一下" → 报修流程(candidates → create)
     "开始维修/开始修"      → start 流程
     "维修完成/结束维修/修好了" → end 流程
     "查维修单/维修单"      → list 流程
  → 设备匹配：调 AIgetEqStatusList（全量）→ 客户端模糊匹配 EQ_ID/EQ_NAME → 取最优
  → 校验（设备唯一/原因唯一/状态机通过）→ ✅ 直接执行 → 反馈
  → 有歧义（多候选/状态不符）→ 停下来问 → 选定后直接执行
```

---

## 工号会话记忆（可选）

- 开始维修/结束维修可能需要记录操作人（AC_START_WORKER/AC_END_WORKER）。
- 首次操作 → 问工号 → 记住；后续自动带入；"换人/我是XXX" → 更新。

---

## 对话流程（场景）

### 场景A：报修生成维修单（核心）

```
工人："报修设备数控中心1号机，打码机故障"
系统：设备唯一匹配 + 原因"打码机故障"精确命中系统字典(DCCDID 449192954227339)
     → ✅ 直接调 create → "✅ 维修单已生成！设备 数控中心1号机，原因：打码机故障，状态：待维修。"
```

```
工人："报修设备数控中心1号机"（没给原因）
系统：调 candidates → 设备唯一，但原因未指定 → "设备 数控中心1号机(CNC)。请选择故障原因：
      1、故障111；2、机器嘀嘀嘀；3、打码机故障… 请说序号或原因名称。"
工人："3"
系统：原因唯一命中 → ✅ 直接调 create → 反馈结果
```

- 工人直接说原因名且唯一命中 → 跳过候选直接 create；候选太多时只播报前 5-8 条。
- **原因候选只用系统字典（COLLECTION_TYPE=8，带 DCCDID）**，通用原因库条目不在候选内（系统无对应 ID 无法建单）。

### 场景B：查询维修单

```
工人："查一下数控中心的维修单"
系统：调 list → "设备 数控中心1号机：1 张待维修单 WX-20260727003；数控中心2号机：2 张维修中单 WX-20260727001/002。"
```

### 场景C：开始维修

```
工人："开始维修数控中心1号机"
系统：调 list 匹配到唯一待维修单 WX-20260727003（状态3，校验通过）
     → ✅ 直接调 start → "✅ 已开始维修！单据 WX-20260727003，状态：维修中。"
```

- 若设备没有待维修单（状态3）→ 提示"没有可开始的维修单"，列出当前维修中单提示可结束。
- 若该设备有多张待维修单 → 列出来让工人选（唯一性校验失败才问）。

### 场景D：结束维修（按项目提醒填写）

```
工人："维修完成数控中心1号机，更换了轴承"
系统：调 list 匹配唯一维修中单 WX-20260727003（状态5，校验通过）
     → ✅ 直接调 end（--items "维修=更换了轴承"）→ "✅ 维修完成！单据 WX-20260727003，状态：维修完成。"
```

```
工人："维修完成数控中心1号机"（没给项目结果）
系统：调 list 匹配维修中单 → 校验通过，但维修项目结果未知 → 询问：
      "维修中单 WX-20260727003，请说维修项目及结果（如'更换传感器'）。"
工人："更换传感器，已完成"
系统：✅ 直接调 end（--items "更换传感器=已完成"）→ 反馈结果
```

- 结束维修的 `--items` 格式：`"项目1=结果1;项目2=结果2"`。
- 工人给了项目+结果 → 直接执行；只给了动作没给项目 → 简短追问一次；项目模板未配置时默认 1-2 项。

---

## 输入解析

### 设备识别

| 工人说的 | 匹配字段 |
|---------|---------|
| 设备编号 | `EQ_ID`（如 "XH1C1001"） |
| 设备名称 | `EQ_NAME`（如 "数控中心1号机"、"1号注塑机"） |

> 模糊匹配：输入包含在字段中或字段包含输入，都算命中；EQ_ID 精确 > EQ_NAME 精确 > 包含。多候选时让工人选。

### 动作识别

| 工人说的 | 动作 | 调接口 |
|---------|------|--------|
| 报修/设备坏了/修一下/故障 | **报修 create** | AIEqError |
| 开始维修/开始修/开工修 | **开始 start** | AIsendEqMainRecord(mainOperate=1) |
| 维修完成/结束维修/修好了/完工 | **结束 end** | AIsendEqMainRecord(mainOperate=2) |
| 查维修单/维修单/单据 | **查询 list** | AIgetEqMainList |

### 原因识别（create 用）

工人说的原因 → 匹配候选列表（序号/名称/同义词）→ 解析 DCCDID：

- **序号（"1"、"3"）**：AI 先调 `candidates` 拿候选列表（含每项 DCCDID），工人说序号 → 取对应项的 DCCDID → 用 `--reason-id` 直接传入（最可靠，避免名称二义性）
- 名称精确/包含 → `--reason` 传名称，CLI 内 resolve_reason_id 解析（同报废原因规则）
- 同义词（"液压漏油"≈"密封泄漏"）→ fault_reasons.json 的 aliases 映射（AI 层处理）
- 未匹配 / 未提供 → 默认第一条（需在预览中明确展示让工人确认）

---

## API 接口规格（实测 2026-08-07）

配置文件：`scripts/config.json`（host/port 不预制，首次使用运行 `scripts/setup_config.py` 交互填写）

> 🔑 **鉴权**：当前客户环境 = MES 运行时（sMES）。OpenAPI 全部要求 Bearer Token（无 token 返回 401）。脚本自动走账密登录换取：
> 账密模式：`POST /account/v1/login`（密码前端算法加密）→ `result.token.accessToken`（1 小时）。备用 SSO 流程（`/sso/v1/code` + `/sso/v1/token`，env_type=sMES）已实现。
> `POST /sso/v1/code`（userNo+appId 按环境配置拿临时授权码）→ `POST /sso/v1/token`（appId+appSecret 按环境配置+code 换 accessToken，1 小时有效），请求头 `Authorization: Bearer {accessToken}`。
> userNo/appId/appSecret 在 config.json 的 auth.sso 配置（user_no 按环境配置，不预制）。若报"第三方应用ID或密钥不正确"，需客户在平台 SSO 管理界面配置应用后更新。

### 1. AIgetEqStatusList（设备清单）

POST `{}` → `{"eqList": [{"EQ_NAME","EQ_ID","EQ_STATUS","BUTTON"}]}`

> ⚠️ **不做服务端过滤**：传 eqId/eqName 也返回全量 60+ 台，匹配必须在客户端做。
> EQ_STATUS：1闲置、2加工、6故障（可优先展示故障设备）。

### 2. AIGetCollData（故障原因字典）

POST `{"COLLECTION_TYPE": 8}` → `{"LIST": [{"DCDID","DATA_TYPE","COLLECTION_TYPE","DCCDID","COLLECTION_ID","COLLECTION_NAME","COLLECTION_CHOICE_NAME"}]}`

> ⚠️ **键名必须大写** `COLLECTION_TYPE`（小写报"属性 [COLLECTION_TYPE] 必填"）。reasonId 取 **DCCDID**（Long），不能填 0。

### 3. AIGetOee（历史稼动/故障）

POST `{"EQ_ID": "X"}` → `{"list": [{"EQ_ID","EQ_STATUS","START_TIME","END_TIME","COLLECTION_CHOICE_NAME?"}]}`

> EQ_STATUS=6 记录带故障原因名；END_TIME=1900-01-01 表示故障未恢复。用于历史故障候选。

### 4. AIEqError（报修生成维修单）

POST `{"eqId": String, "reasonId": String}` → 生成维修单（状态=3待维修）

### 5. AIgetEqMainList（查询设备维修单）

POST `{"EQ_ID": "X"}` → `{"eqMainList": [{"ID","EQ_ID","EQ_MAINTENANCE_ID","EQ_MAINTENANCE_DATE","EQ_MAINTENANCE_STATUS","EQ_MAINTENANCE_TYPE","EXPECTED_START_DATE","EXPECTED_END_DATE",...}]}`

> 返回状态3（待维修）+ 状态5（维修中），状态4（维修完成）不返回（已完成无需操作）。单据号字段 = `EQ_MAINTENANCE_ID`。

### 6. AIsendEqMainRecord（开始/结束维修）

```json
{
  "mainOperate": 1,        // 1=开始(对状态3)  2=结束(对状态5)
  "eqMainId": "WX-20260727003",
  "mainRecord": [{"EQ_MAINTENANCE_ITEM": "维修", "EQ_MAINTENANCE_RECORD": "1"}],
  "picture": ""
}
```

> mainRecord 仅结束(2)时必填，开始(1)时传 []。落库：mainRecord→eq_maintenance_record_detail，主记录→eq_maintenance_record(AC_START/END_DATE/WORKER, PICTURE)。

---

## 状态机与安全规则

| 维修单状态 | 含义 | 可执行 |
|-----------|------|--------|
| 3 待维修 | 已报修未开始 | 开始(mainOperate=1) |
| 5 维修中 | 已开始未完成 | 结束(mainOperate=2) |
| 4 维修完成 | 已结束 | 无（不再操作） |
| 0/1/2 | 计划中/保养中/保养完成 | 本功能不操作（保养流程不走报修） |

- CLI 内置校验：start 只认状态3，end 只认状态5，违反会返回 `status_mismatch` 拒绝。
- 常规操作校验通过即直接执行（不预览确认）；`--dry-run` 仅在有歧义需先展示清单时使用。

---

## CLI 用法（scripts/repair_tool.py，禁止每次重写脚本）

```bash
# 相对本 skill 目录：scripts/repair_tool.py
python repair_tool.py --action candidates --eq <设备关键词> [--no-cache]      # 报修候选
python repair_tool.py --action create --eq <设备关键词> --reason <原因名/序号> [--dry-run]
python repair_tool.py --action list --eq <设备关键词> [--no-cache]
python repair_tool.py --action start --eq <设备关键词> [--repair <单据号>] [--dry-run]
python repair_tool.py --action end --eq <设备关键词> --items "项目=结果;项目2=结果2" [--dry-run]
```

| 参数 | 说明 |
|------|------|
| `--action` | candidates \| create \| list \| start \| end |
| `--eq` | 设备编号或名称关键词（匹配 EQ_ID/EQ_NAME） |
| `--reason` | 故障原因名称（create 用，解析 DCCDID；不传默认第一条） |
| `--reason-id` | 故障原因 DCCDID（create 用，AI 从 candidates 序号取到直接传，优先于 --reason） |
| `--repair` | 维修单号（start/end 用，不传自动取状态匹配的单） |
| `--items` | 结束维修项目结果 `"项目=结果;项目2=结果2"` |
| `--dry-run` | 只查询+预览，不调用写接口（建单/改状态）。**仅多候选/歧义展示时用，常规操作直接执行不用它** |
| `--no-cache` | 强制刷新设备清单/原因字典缓存（默认30s TTL） |

**CLI 内置能力：**

| 能力 | 说明 |
|------|------|
| 设备匹配 | AIgetEqStatusList 全量 + 客户端模糊匹配，EQ_ID 精确>EQ_NAME 精确>包含，多候选提示 |
| 设备类型判定 | 设备名含"注塑"→注塑机；含"数控/CNC/车床/铣床"→CNC；否则通用（供原因库选型） |
| 三源候选 | 历史故障(AIGetOee) + 通用原因库(fault_reasons.json 按类型) + 系统字典(COLLECTION_TYPE=8)，去重合并 |
| 原因解析 | 名称/序号 → DCCDID，同义词映射（fault_reasons.json aliases），默认第一条 |
| 状态机校验 | start 只认状态3，end 只认状态5，违反拒绝 |
| 缓存 | 设备清单/原因字典 30s TTL 文件缓存 |

**返回解析：**
- `ok=true` → 成功（dry_run 时表示预览）
- `reason=no_eq` → 设备无匹配，提示重输
- `reason=no_actionable` / `status_mismatch` → 没有可操作单据 / 状态不符
- `details[]` / `will_send` → 预览的执行计划

---

## 反馈模板

**报修成功：**
"✅ 维修单已生成！设备 数控中心1号机，原因：主轴轴承磨损，状态：待维修。"

**开始成功：**
"✅ 已开始维修！单据 WX-20260727003，状态：维修中。"

**结束成功：**
"✅ 维修完成！单据 WX-20260727003，状态：维修完成。维修项目：维修=已更换轴承，润滑=正常。"

**失败：**
"❌ 执行失败：[message]。请检查后重试。"

**状态不符：**
"⚠️ 该单据状态不允许此操作（开始只对待维修单，结束只对维修中单）。"

---

## 相关文件（skill 目录内）

- 执行工具（参数化 CLI）：`scripts/repair_tool.py`
- 配置：`scripts/config.json`（6 接口 + mainOperate + 状态枚举）
- 通用原因库：`scripts/fault_reasons.json`（CNC/注塑机/通用 3 类 90+ 条 + 同义词）
- 方案文档：用户工作区（非 skill 必需）
- 原因库整理：用户工作区（非 skill 必需）
