---
name: voice-work-reporting
display_name: 鼎华eMES 产品助手-语音智能报工助手
display_name_en: Voice Work Reporting
description: "MES voice work reporting: workers speak product + operation + quantity; AI matches the dispatch list and auto-completes start/report actions."
description_zh: MES 语音报工：工人说产品+工序+数量，AI 匹配派工清单后自动判断开工/报工，替代手工录入。
description_en: "MES voice work reporting: workers speak product + operation + quantity; AI matches the dispatch list and auto-completes start/report actions."
category: productivity
version: 1.0.0
author: Digihua
trigger:
  - 报工
  - 语音报工
  - 结束加工
  - 开工
  - 开始加工
  - mes报工
  - 我要报工
  - 切换工号
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
---
# 语音智能报工助手（对话模式 · 开工+报工双接口）

## ⚠️ 防重复执行铁律（最重要！）

**CLI 是"查询+匹配+执行"一体，只要带 `--qty` 就会真实执行、扣减数量。**

因此对话流程必须分两步：

1. **匹配/展示阶段：必须加 `--dry-run`** —— 只输出执行计划，不调任何接口、不扣数量。
2. **工人明确确认后：去掉 `--dry-run` 重新运行** —— 仅执行这一次，**绝不重复调用**。

```
# ❌ 禁止：为了"查询匹配"直接跑带 qty 的 CLI（这会真执行！）
# ✅ 正确：先预览
python report_tool.py --action start --product YZTEST --process 组装 --qty 2 --operator W00123 --dry-run
# ✅ 正确：工人说"确认"后，才去掉 --dry-run 执行一次
python report_tool.py --action start --product YZTEST --process 组装 --qty 2 --operator W00123
```

- 预览返回 `"dry_run": true`、`details[]` 中列出每笔 MO/工序/数量。
- 工人确认前**绝对禁止**运行不带 `--dry-run` 的命令。
- 一次报工/开工请求，**只能执行一次**；如果 AI 不确定是否已执行，先查 MOLIST（`--dry-run`）确认状态，不要盲目重跑。

---

## 核心理念

工人对话说一句话 → AI 解析 → 调查询接口匹配 → 自动判断开工还是报工 → 确认 → 执行。

**两个执行接口：**
- `AIStartPro`（开工）— 对应 LOT_STATUS=1（待加工）
- `AIEndPro`（报工/结束加工）— 对应 LOT_STATUS=2（加工中）

---

## 完整链路

```
工人输入 → AI解析(产品/工序/数量/设备?/操作类型?)
  → 识别操作类型：
      "开工/开始加工" → 筛状态1 → AIStartPro
      "报工/完工/结束加工" → 筛状态2 → AIEndPro
      未指定 → 两者都有→开工，仅加工中→报工
  → 调 AIGetMoLIST → MOLIST[]
  → AI 匹配：MA_ID/MATERIAL_NAME + OP_ID/OP_NAME
  → 匹配唯一 → 【--dry-run 预览计划给工人确认】；多条候选 → 让工人选
  → 工人确认 → 去掉 --dry-run 逐笔执行（只执行一次！）
  → 反馈结果
```

---

## 工号会话记忆

- 首次报工 → 问工号 → 记住
- 后续报工 → 自动带入
- "切换工号"/"换人"/"我是XXX" → 更新
- 对话结束 → 清除

---

## 对话流程（10 个场景）

### 场景0：首次报工（无工号）
工人："我要报工"
系统："请先告诉我你的工号。"
工人："W00123"
系统："工号已记录。请说报工信息，如：产品M02 铸造工序 100件"

### 场景1：完整输入 → 自动判断开工/报工
工人："产品M02 铸造工序 报工100件"
→ "报工"一词在具体语境中指操作，识别为直达命令→ 筛状态2
→ 调查询匹配 → 找到 MO=xxx, 状态=加工中
系统："匹配到：MO=xxx, 产品M02(螺丝), 工序铸造, 车间铸造
       状态：加工中 → 将执行【结束加工/报工】
       数量：100，工号：W00123
       确认吗？"
工人："确认" → 调 AIEndPro → 反馈结���

### 场景1A：说"开工"��� 直达开工
工人："产品YZTEST 组装工序 开工 1个"
→ 识别"开工"命令 → 只筛状态1
系统："匹配到：MO=xxx, 产品YZTEST, 工序组装
       状态：待加工 → 将执行【开始加工】
       数量：1，工号：{当前登录工号}
       确认吗？"

### 场景1B：说"报工/完工"→ 直达报工
工人："产品YZTEST 组装工序 完工 5个"
→ 识别"完工"命令 → 只筛状态2
系统："匹配到：MO=xxx, 产品YZTEST, 工序组装
       状态：加工中 → 将执行【结束加工/报工】
       数量：5，工号：{当前登录工号}
       确认吗？"

### 场景1C：未指定操作 → 自动判断

### 场景2：带设备
工人："产品M02 铸造工序 设备M01 100件"
→ 调 AIGetMoLIST(eqName="M01") 过滤后再匹配

### 场景3：仅触发
工人："我要报工" → 系统引导输入

### 场景4：部分输入
工人："产品M02 报工100件" → 追问工序 → 补全后继续

### 场景5：候选不唯一
系统："找到2条匹配：1. 产品M02 工序铸造  2. 产品M02 工序冲压  选哪个？"
工人："1" → 确认 → 执行

### 场景6：无匹配
系统："未找到匹配'产品XYZ'的记录，请检查后重试。"

### 场景7：确认时修改
工人："不对，工序是冲压" → 重新匹配 → 重新确认

### 场景8：切换工号
工人："换人，我是W00456" → 更新工号

### 场景9：接口报错 → 直接展示
系统："❌ 执行失败：可加工数量不足！请检查后重试。"

---

## 数量拆分规则

当工人报工数量 > 匹配记录的单笔 QTY 时，按 OP_SEQ 升序依次拆分执行。**拆分过程无需工人确认，直接自动执行。**

```
如：工人报工 50，匹配到 3 笔（OP_SEQ=0010 QTY=20, OP_SEQ=0020 QTY=20, OP_SEQ=0030 QTY=20）
→ 第1笔 传 qty=20 → 剩余 30
→ 第2笔 传 qty=20 → 剩余 10
→ 第3笔 传 qty=10 → 剩余 0，完成
```

如工人的 qty <= 首笔 QTY，则只用首笔。

拆分过程中任意一笔失败 → 停止并展示错误，已成功的笔数不回滚。

---

## 确认规则

| 工人回复 | 动作 |
|---------|------|
| 确认/对/是的/没错/OK/好的 | 执行接口 |
| 取消/不对/错了/改 | 询问修改 |
| 给新值（如"工序是组装"） | 更新后重新匹配确认 |
| 序号（1/2/3） | 选择候选 |
| 切换工号/换人/我是XXX | 更新工号 |

---

## 输入解析

### 字段提取

| 字段 | 必填 | 关键词 |
|------|------|--------|
| 产品 | 是 | 产品/品号/品名/编号/物料/名称 |
| 工序 | 是 | 工序/工艺/步骤/工艺编号 |
| 数量 | 是 | 数字+件/个/pcs |
| 设备 | 否 | 设备/机器/机台 |
| 报废 | 否 | 报废/料废/不良（同义，都算报废数量） |

### 字段匹配映射

工人输入的内容，按以下规则匹配 MOLIST 字段：

| 工人说的 | 匹配 MOLIST 字段 | 说明 |
|---------|-----------------|------|
| 品号 / 产品编号 | `MA_ID` | 如 "YZTEST" → MA_ID |
| 品名 / 产品名称 | `MATERIAL_NAME` | 如 "测试产品" → MATERIAL_NAME |
| 工艺编号 / 工序编号 | `OP_ID` | 如 "YZ_OP_3" → OP_ID |
| 工艺名称 / 工序名称 | `OP_NAME` | 如 "组装" → OP_NAME |

> **匹配时模糊搜索**：输入内容包含在字段中，或字段包含输入内容，都算命中。

### 操作类型识别（直达命令）

| 工人说的 | 操作 | 查 MOLIST 的 LOT_STATUS |
|---------|------|------------------------|
| 开工 / 开始加工 / 进站 | **直接开工** | 只筛状态=1（待加工） |
| 报工 / 完工 / 结束加工 / 出站 | **直接报工** | 只筛状态=2（��工中） |

### 报废数量识别（同义词统一）

**"报废 / 料废 / 不良" 是同一语义**，工人说任何一个词都表示报废数量，解析后填入 `exceptionReason`（CLI `--scrap`）：

| 工人说的 | 解析结果 |
|---------|---------|
| "报工 12 个，报废 2 个" | qty=12, scrap=2 |
| "报工 12 个，料废 2 个" | qty=12, scrap=2 |
| "报工 12 个，不良 2 个" | qty=12, scrap=2 |
| "报工 12 个"（未提） | qty=12, scrap 不传（非必填） |

### 报废原因解析（AIGetCollData）

报废时 `reasonId` 不写死，而是调 `AIGetCollData` 获取原因列表后按名称解析：

| 项目 | 内容 |
|------|------|
| 接口 | POST `{host}/open-api/bp/AIGetCollData`，body `{"COLLECTION_TYPE": 2}`（2=报废原因） |
| 返回 | `{"LIST": [{"DCCDID": 412036704721110, "COLLECTION_NAME": "报废1", "COLLECTION_CHOICE_NAME": "报废1-1", ...}]}` |
| reasonId 取值 | 命中条的 **DCCDID**（Long） |

**名称 → ID 匹配优先级：**
1. `COLLECTION_CHOICE_NAME` 精确匹配（如 "报废1-1"）
2. `COLLECTION_NAME`（原因组名）精确匹配（如 "报废"、"内废"）→ 取该组第一条
3. `COLLECTION_CHOICE_NAME` 包含匹配（互相包含）
4. `COLLECTION_NAME` 包含匹配 → 取该组第一条
5. 未匹配 / 工人未提原因 → **默认第一条**（LIST[0].DCCDID）

CLI 用 `--reason <名称>` 传入；不传则默认第一条。原因列表有 30s 文件缓存。

**实测样例（2026-08-03）：**
- "报废" → 报废/报废测试01 (443237662267127)
- "内废" → 内废/刀具问题和机床问题 (461910223286589)
- "外废" → 外废/气孔和裂痕 (461910223298874)
- "报废1-1" → 报废1/报废1-1 (412036704725209)

> ⚠️ **教训**：reasonId 填 0 会报 "原因不存在"，必须从 AIGetCollData 解析真实 DCCDID。

---

## API 接口规格

配置文件：`scripts/config.json`（host/账号/密码**不预制**；首次使用运行 `scripts/setup_config.py` 交互填写，打包分发前运行 `scripts/clean_for_packaging.py` 清空）

> 🔑 **鉴权**：OpenAPI 全部要求 Bearer Token（无 token 返回 401）。脚本自动走账密登录换取：
> 账密模式：`POST /account/v1/login`（密码前端算法加密）→ `result.token.accessToken`（1 小时）。备用 SSO 流程（`/sso/v1/code` + `/sso/v1/token`，env_type=sMES）已实现。
> `POST /sso/v1/code`（userNo+appId 按环境配置拿临时授权码）→ `POST /sso/v1/token`（appId+appSecret 按环境配置+code 换 accessToken，1 小时有效），请求头 `Authorization: Bearer {accessToken}`。
> userNo/appId/appSecret 在 config.json 的 auth.sso 配置（user_no 按环境配置，不预制）。若报"第三方应用ID或密钥不正确"，需客户在平台 SSO 管理界面配置应用后更新。

```json
{
  "server": { "host": "", "port": 20201 },  // host 首次使用 setup_config.py 填写
  "apis": {
    "queryMoList": "/open-api/bp/AIGetMoList",
    "startProduction": "/open-api/bp/AI_start_processing",
    "endProduction": "/open-api/bp/AI_end_processing",
    "queryReasonList": "/open-api/bp/AIGetCollData"
  }
}
```

### 1. AIGetMoLIST（查询派工清单）

POST，返回 `{"MOLIST": [...]}`。关键字段：

| 字段 | 类型 | 用途 |
|------|------|------|
| MA_ID | String | ★ 产品编号/品号，匹配用 |
| MATERIAL_NAME | String | ★ 产品名称/品名，匹配用 |
| OP_ID | String | ★ 工艺编号/工序编号，匹配用 |
| OP_NAME | String | ★ 工艺名称/工序名称，匹配用（可为空！） |
| OP_DESCRIPTION | String | OP_NAME 为空时参考 |
| LOT_STATUS | **int** | 1=待加工, 2=加工中 ★ |
| MO_ID / OP_SEQ / OP_ID | String | 传入执行接口 |
| WS_ID / WS_NAME | String | 传入接口 / 确认展示 |
| QTY | Decimal | 数量拆分基准 |
| EPSID | Long | 传执行接口 |
| WO_ID | String | workHours 参考 |
| EQ_ID | String | 设备，可选 |

> LOT_STATUS 是 int 不是 str。OP_NAME 可能为 ""。

### 2. AIStartPro（开工）

```json
// 请求
{"moId":"", "opSeq":"", "opId":"", "qty":1.0, "wsId":"", "eqId":"", "epsId":123}

// 成功 → {"res":{"executeResult":true,"amrpId":...,"pmopId":0}}
// 失败 → {"code":1,"message":"错误原因","result":null}
```

### 3. AIEndPro（报工）

```json
// 请求
{
  "moId":"", "opSeq":"", "opId":"", "qty":1.0,
  "exceptionReason":[{"exceptionType":"2","exceptionQty":0.0,"reasonId":0,"sn":""}],
  "dataCollection":[], "useList":[],
  "workHours":[{"userId":"WO_ID(派工人员账号)","reportQty":1.0,"humanTime":0,"machineTime":0}],
  "humanTime":0, "machineTime":0,
  "eqId":"", "nextOpSeq":"<从MOLIST查下一道工序的OP_SEQ>", "nextOpId":"<下一道OP_ID>", "nextWsId":"<下一道WS_ID>",
  "wsId":"", "epsId":123
}

// 成功 → {"res":{"executeResult":true,"amrpId":...,"pmopId":...}}
// 失败 → {"code":1,"message":"错误原因","result":null}
```

> **workHours 必填！** userId = MOLIST 中的 **WO_ID**（派工人员账号），reportQty = 报工数量。
> **humanTime / machineTime** 传 0，后端自行处理。
> **nextOpSeq / nextOpId / nextWsId**：从 MOLIST 中查找同 MO_ID 下的下一道工序（OP_SEQ 更大且最小），查到就填，查不到传空字符串。
> **报废数量填报（exceptionReason）**：有报废时填入 `[{"exceptionType":"2","exceptionQty":<报废数>,"reasonId":<解析后ID>,"sn":""}]`；无报废时传 `[]`。exceptionType 固定 "2"，reasonId 由 AIGetCollData 按名称解析（见"报废原因解析"章节），sn 传空。CLI 用 `--scrap <数量> --reason <名称>` 传入（--reason 可不传，默认第一条）。

---

## AI 匹配算法

```
1. 识别操作类型：有"开工/开始加工"→筛状态1 / 有"报工/完工/结束加工"→筛状态2 / 未指定→全量
2. 从 MOLIST 筛选：
   - MA_ID 或 MATERIAL_NAME 包含产品关键词
   - OP_ID 或 OP_NAME 包含工序关键词
   - 按操作类型筛选 LOT_STATUS
3. 排序：精确匹配 > 包含匹配 > 字段非空优先
4. 1条→确认 / 2-5条→列候选 / 0条→重输
```

---

## 执行流程（确认后）

```
1. 匹配记录按 LOT_STATUS 分组
2. 决定操作：有状态1→开工 / 仅有状态2→报工
3. 按 QTY 判断是否需要多笔拆分
4. 逐笔调用 AIStartPro 或 AIEndPro
   - AIEndPro 时：从 MOLIST 查同 MO_ID 下 OP_SEQ 更大的最小一笔 → 填 nextOpSeq/nextOpId/nextWsId
   - 查不到 → nextOpSeq/nextOpId/nextWsId 传空字符串 ""
5. 检查返回：有 "res" 键 → 成功 / 有 "code" 键 → 失败，展示 message
6. 全部成功 → "✅ 完成" / 中间失败 → "❌ 第N笔失败: [原因]"
```

> **数量拆分无需工人确认，直接执行。** 确认总量后自动拆分。

---

## ⚠️ 性能优化：用 CLI 工具，禁止每次重写脚本

实测端到端（查询+匹配+调接口）仅需 **700ms 左右**，`report_tool.py` 已固化所有逻辑。
54s 主要来自"AI 每轮重写 Python 脚本 + 生成回复"。改用 CLI 后大幅提速。

### 调用方式（Bash 工具直接执行，不要再 Write 新脚本）

```bash
# 相对本 skill 目录：scripts/report_tool.py
python "scripts/report_tool.py" \
  --action report|start \
  --product <产品关键词> --process <工序关键词> \
  --qty <数量> --operator <工号> \
  [--scrap <报废数> --reason <原因名>]  # 报废填报
  [--exact-process]   # 严格匹配工序名（"组装"不匹配"组装2"）
  [--no-cache]        # 强制重新查询 MOLIST
  [--dry-run]         # ★ 只预览执行计划，不调接口！匹配/确认阶段必须加
```

| 参数 | 说明 |
|------|------|
| `--action report` | 报工/完工/结束加工（筛 LOT_STATUS=2） |
| `--action start` | 开工/开始加工（筛 LOT_STATUS=1） |
| `--product` | 产品关键词，匹配 MA_ID 或 MATERIAL_NAME |
| `--process` | 工序关键词，匹配 OP_NAME 或 OP_ID |
| `--qty` | 报工数量（小数） |
| `--scrap` | 报废数量（仅报工有效；>0 时填 exceptionReason: type="2", reasonId=0, sn=""） |
| `--operator` | 工号（填入 workHours.userId） |
| `--dry-run` | **只查询匹配+输出计划，不调用执行接口（不扣数量）**。工人确认前必须加此参数 |

### CLI 内部已封装

1. 读 `config.json` 取 BASE URL
2. 查 MOLIST（30s 文件缓存，执行成功后自动失效刷新）
3. 按 product/process/action 匹配 + OP_SEQ 升序
4. qty > 可用量自动多笔拆分（无需确认）
5. 逐笔调 AIStartPro / AIEndPro
6. 输出 JSON：`reported`/`unreported`/`batches`/`details`

### 返回解析

- `ok=true` → 全部成功
- `ok=false` 且 `reason=no_match` → 无匹配，提示重新输入
- `details[].ok=false` → 某笔失败，展示 `error`
- `unreported > 0` → 数量不足，提示剩余未报数量

---

## 反馈模板

**开工成功：**
"✅ 开工成功！MO=xxx, 产品M02(螺丝), 工序铸造, 数量100, 车间铸造"

**报工成功：**
"✅ 报工成功！MO=xxx, 产品M02(螺丝), 工序铸造, 数量100, 车间铸造"

**失败：**
"❌ 执行失败：[message]。请检查后重试。"

**多笔拆分成功：**
"✅ 全部完成！共执行 3 笔，合计数量 50：MO=xxx(20) → MO=yyy(20) → MO=zzz(10)"

**部分失败：**
"⚠️ 第 2 笔失败：[message]，第 1 笔已成功(数量20)。"

---

## 相关文件（skill 目录内，相对路径）

- 执行工具（参数化 CLI）：`scripts/report_tool.py`
- 配置：`scripts/config.json`
- 分析：用户工作区（非 skill 必需）
- 接口测试：用户工作区（非 skill 必需）

### 执行工具 report_tool.py 说明

**统一用法（禁止每次重写脚本，直接调 CLI）：**

```bash
python report_tool.py --action report --product 产品 --process 工序 --qty 数量 --operator 工号 [--scrap 报废数 --reason 原因名] [--no-cache]
python report_tool.py --action start  --product 产品 --process 工序 --qty 数量 --operator 工号 [--no-cache]
```

> `--scrap <报废数>`：填 exceptionReason.exceptionQty（仅报工有效，>0 才填）。
> `--reason <原因名>`：报废原因名称，调 AIGetCollData 按名称解析出 reasonId（DCCDID）；不传或查不到 → 默认第一条。

**内置能力：**

| 能力 | 说明 |
|------|------|
| 匹配 | MA_ID/MATERIAL_NAME 匹配产品，OP_ID/OP_NAME 匹配工序（含 OP_NAME 为空时参考 OP_DESCRIPTION） |
| 状态判断 | `--action report` 只筛加工中(状态2)；`--action start` 只筛待加工(状态1) |
| 数量拆分 | qty > 单笔可用 → 按 OP_SEQ 升序自动拆多笔，无需工人确认 |
| **多笔并发** | `execute()` 用 ThreadPoolExecutor 并发调接口（max_workers=min(笔数,8)），单笔走同步分支零开销；结果按原始 OP_SEQ 顺序回填 |
| 报废原因解析 | 调 AIGetCollData 拿原因列表（30s 缓存），`resolve_reason_id` 按 名称→DCCDID 解析，默认第一条 |
| MOLIST 缓存 | 30s TTL 文件缓存，查询 170ms→2ms；执行（开工/报工）成功后自动失效刷新，避免状态过期 |
| 配置 | 读 `config.json`，改 IP/端口无需改代码 |

**性能基线（实测）：**
- 查询接口 AIGetMoLIST：~170ms（缓存命中后 2ms）
- CLI 端到端（查询+匹配+调接口+回参）：~724ms
- 多笔拆分并发：4 笔 mock 验证 303ms（串行需 1200ms）
- 历史 54s 慢响应主因是"每轮重写脚本"的 AI 开销，改用 CLI 后已消除
