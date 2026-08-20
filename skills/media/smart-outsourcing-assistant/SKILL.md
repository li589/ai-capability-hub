---
name: smart-outsourcing-assistant
display_name: 鼎华eMES 产品委外助手-智能委外助手
display_name_en: Smart Outsourcing Assistant
description: "Smart outsourcing assistant: fetch outsourceable list & supplier performance, rank suppliers, dry-run preview, auto-create outsourcing orders, and handle returns via photo/voice recognition."
description_zh: 委外全流程智能助手：取可委外清单与供应商绩效，智能排序推荐供应商，dry-run 预览后自动生成委外单；回货拍照/语音识别按单回货，支持批量/单条回货。纯接口数据源。
description_en: "Smart outsourcing assistant: fetch outsourceable list & supplier performance, rank suppliers, dry-run preview, auto-create outsourcing orders, and handle returns via photo/voice recognition."
category: productivity
version: 1.0.0
author: Digihua
trigger:
  - 委外发货
  - 委外回货
  - 委外
  - 外协
  - 要委外
  - 委外建议
  - 推荐供应商
  - 品质要求高
  - 急单
  - 加急
  - 生成委外单
  - 供应商发货
  - 供应商回货
  - 发货
  - 回货
  - 拍照
  - 回货单
  - 准交率
  - 准时率
  - 良品率
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
---
# 委外发货回货助手（推荐供应商 → 自动生成委外单 → 拍照回货）

## 核心理念（完整业务闭环）

```
用户说"XX产品、XX工艺要委外"
  → ① 解析：产品/工艺/数量 + 需求类型（品质要求高 / 急单 / 未表态）
  → ② 查可委外工单 + 候选供应商绩效（良品率、准交率、在手委外单数）
  → ③ 按策略排序推荐供应商（品质高→良品率优先；急单→准交率优先；未表态→默认品质优先）
  → ④ 展示推荐列表与第一名；客户不选 → 自动选最符合的那一个
  → ⑤ 调用 OPENAPI 自动生成委外单，执行委外操作，生成委外单据
  → ⑥ 回货时：客户拍照上传回货单 → 识别委外单号/数量 → 核对 → 调用接口执行回货
```

**分工**：AI 负责「解析需求、看图识别回货单、组织确认与建议」；`recommend_supplier.py` 负责候选+绩效+排序推荐；`supplier_perf.py` / `outsource_list.py` 负责绩效与清单查询；**`outsource_tool.py` 负责查清单接口 + 匹配 + 调执行接口（标准 SSO/账密 Bearer Token 鉴权）**。

**数据来源（2026-08-17 用户确认）**：本技能**全部数据来自用户提供的 OPENAPI 接口**（可委外清单 getCanOutsourceList、待回货清单 getOutSourceList、供应商绩效 getOutSourceDash、执行 SendOutsource/sendOutsourceBack），**不读数据库、无报工相关接口**。

---

## ⚠️ 防重复执行铁律（最重要）

**`outsource_tool.py` 是"查询+匹配+执行"一体，去掉 `--dry-run` 就会真实执行（生成委外单/回货）。**

1. **匹配/展示阶段：必须加 `--dry-run`** —— 只输出匹配结果与执行计划，不调任何执行接口
2. **用户明确确认后：去掉 `--dry-run` 执行一次，绝不重复调用**
3. 不确定是否已执行 → 先 `--dry-run` 查状态，不要盲目重跑

```
# ❌ 禁止：为了"查询匹配"直接跑不带 --dry-run 的命令（这会真执行！）
# ✅ 正确：先预览
python outsource_tool.py --action send --product FCW-01 --process 钢材切割 --supplier FZHGYS --qty 10 --delivery-date 2026-08-20 --dry-run
# ✅ 正确：用户确认后，才去掉 --dry-run 执行一次
python outsource_tool.py --action send --product FCW-01 --process 钢材切割 --supplier FZHGYS --qty 10 --delivery-date 2026-08-20
```

---

## ⚠️ 安全红线（最高优先级）

1. 数据一律来自本技能配置的 OPENAPI 接口（`config.json apis`），**不读数据库**
2. 只调用委外相关接口（getCanOutsourceList / getOutSourceList / getOutSourceDash / SendOutsource / sendOutsourceBack / batchSendOutsourceBack），**不涉及任何其他业务接口**
3. 推荐只给**建议**：必须展示推荐列表与理由，用户可改选；**用户不选择时才自动选第一名**
4. 生成委外单/回货**必须**确认数量与供应商后才调接口；接口异常时明确告知错误原因，不猜测参数

---

## 工具调用

```bash
PY="{{HOME}}/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SK="{{HOME}}/.workbuddy/skills/产品委外助手-智能委外助手/scripts"

# ① 委外推荐：产品(可加工艺) → 候选供应商按绩效排序 + 推荐第一名
"$PY" "$SK/recommend_supplier.py" --product M02                # 默认品质优先(良品率→准交率)
"$PY" "$SK/recommend_supplier.py" --product M02 --priority ontime   # 急单:准交率→良品率
"$PY" "$SK/recommend_supplier.py" --mo 5101-20260723043        # 按工单
"$PY" "$SK/recommend_supplier.py" --op FZH-CJ-01-01            # 按工艺
# ② 供应商委外全景汇总（发货前必查；默认数据库近90天，--api 用官方接口近一年）
"$PY" "$SK/supplier_perf.py" --perf [--supplier XX] [--days N]
"$PY" "$SK/supplier_perf.py" --perf --api          # 接口 getOutSourceDash(近一年绩效,无需参数)
# ③ 逾期明细
"$PY" "$SK/supplier_perf.py" --overdue
# ④ 待发货清单 / 在途待回货(含逾期) / 在手委外单汇总
"$PY" "$SK/outsource_list.py" --todo
"$PY" "$SK/outsource_list.py" --intransit [--overdue]
"$PY" "$SK/outsource_list.py" --hands
# ⑤ 指定委外单回货明细（回货核对用）
"$PY" "$SK/outsource_list.py" --detail OU-20260811001
# ⑥ 委外发货/回货执行 CLI（查询接口+匹配+执行接口；★匹配阶段必须 --dry-run）
"$PY" "$SK/outsource_tool.py" --action send --product FCW-01 --process 钢材切割 --qty 10 --delivery-date 2026-08-20 --dry-run   # 默认供应商提示
"$PY" "$SK/outsource_tool.py" --action send --product FCW-01 --process 钢材切割 --supplier FZHGYS --qty 10 --delivery-date 2026-08-20 --dry-run
"$PY" "$SK/outsource_tool.py" --action back --outsource-id OU-20260811001 --qty 10 --ok 9 --ng 1 --dry-run   # 填验收/验退
"$PY" "$SK/outsource_tool.py" --action back --qty 10 --dry-run                                               # 不填验收→全部验收;多条按委外日期早优先
```

---

## 🚀 首次使用配置检查（必须执行）

> 🔧 **账号安全**：`config.json` **不预制** IP/端口/登录账号（防止泄漏开发账号）。首次运行 `scripts/setup_config.py` 交互填写（密码不回显）；**打包分发前**运行 `scripts/clean_for_packaging.py` 清空敏感字段，新用户安装后再按实际环境填写。

```bash
"$PY" "$SK/supplier_perf.py" --perf
```
- 有数据 → 正常（绩效来自接口 getOutSourceDash，近一年）
- **接口检查**：`outsource_tool.py --action send --dry-run` 能返回可委外清单即接口+鉴权正常；若返回 401 → 检查 `auth`（SSO 应用配置）；若"接口未配置" → 检查 `config.json apis`
- 鉴权：标准 SSO/账密 Bearer Token（config.json auth），如报"第三方应用ID或密钥不正确"，需在平台 SSO 管理界面配置应用

---

## 处理流程（AI 行为规范）

### A. 委外推荐 + 自动生成委外单（核心流程，触发：XX产品/工艺要委外）

1. **解析需求四要素**：
   - 产品（编号/名称）、工艺（名称/编号）、数量（未说则用可委外数量）
   - 需求类型：**品质要求高** → `--priority quality`；**急单/加急** → `--priority ontime`；未表态 → 默认 `quality`（auto）
2. **查候选 + 绩效排序**：
   ```bash
   "$PY" "$SK/recommend_supplier.py" --product <MA_ID> [--op <OP_ID>] --priority <quality|ontime>
   ```
   展示：可委外工单清单 + 候选供应商排序表（良品率/准交率/在手委外单数）+ ★推荐第一名
3. **输出建议（固定句式，说明口径与理由）**：
   > 【委外建议 · 紧固件(FCW-01) 钢材切割，可委外 25】
   > 按良品率→准交率排序推荐：
   > 1. ★ **F供应商**：良品率 100%、准交率 100%、在手单 0 —— **最符合**
   > 2. 客户X供应商：良品率 91.67%、准交率 84.62%、在手单 0
   > 建议选择 **F供应商**。若需急单可切换准交率优先。
   > 是否按此生成委外单？（数量 25，要求回货日期 ___）
4. **确认或自动选择**：
   - 用户指定 → 按用户选择
   - 用户未表态/回复"按推荐" → **自动选第一名**
   - 补充说明：品质高场景讲良品率，急单场景讲准交率；可追问"急单的话推荐谁"重新排序
5. **调用接口生成委外单**（`outsource_tool.py --action send`，查询+执行两接口）：
   - 先 **--dry-run 预览**执行计划（匹配到的 MO/工序/数量/供应商），展示给用户
   - **多条匹配时按工序（OP_SEQ）排列，从第一条开始往下匹配；数量超过则排序后继续下一笔执行发货**
   - **默认供应商/默认时间**：发货单带默认供应商与回货日期——若客户选择的数据存在默认数据，**可以不重新选择供应商**：告知客户"该工艺默认供应商为 XX、默认回货日期 XX，是否沿用？"；沿用 → 按原供应商传参；重新选择 → 提供供应商绩效（`recommend_supplier.py`）供选择
   - 用户确认后去掉 --dry-run **执行一次**（不重复调用）
   - 回执展示：生成的委外单号、结果；可用 `--intransit` 复核在途
6. **接口异常时**：展示错误原因（如"请选择数据后进行操作"=无匹配数据可发；鉴权失败=检查 SSO 应用配置），提示用户修正后重试

### B. 委外回货（触发：回货/拍照/回货单）

1. **客户拍照上传回货单（或语音输入）**：AI 看图识别 → 提取**委外单号、产品/工艺、回货数量、验收合格/验退数量**（识别不出时请客户口述补充）
2. **核对**：
   ```bash
   "$PY" "$SK/outsource_list.py" --intransit        # 在途单核对
   "$PY" "$SK/outsource_list.py" --detail <单号>     # 已有回货记录
   ```
   确认该单在手、可回货数量充足
3. **确认后执行**（`outsource_tool.py --action back`，查询+执行接口）：
   - **多条匹配时按委外日期早的优先**（自动排序，从最早的开始执行）
   - **不传 --qty = 全部回货**：查询出的**所有产品/单据全部执行回货**（每笔发满待回货量）
   - 可填回货数量、验收合格（--ok）、验退（--ng）；**不填验收/验退 → 全部验收**（合格=回货量，验退=0）
   - 验退分配：**验退尽量放第一笔**（不足顺延后续笔），其余笔全部验收；每笔 验收+验退 = 该笔回货量，**不得超过当条剩余待回货数量**
   - **回货接口自动选择**：多条 → 批量 `batchSendOutsourceBack`（BACKLIST 数组）；单条 → `sendOutsourceBack`（OUTSOURCE_LIST）
   - 先 **--dry-run** 预览（匹配单/数量/验收/验退/将用接口），用户确认后去掉 --dry-run 执行一次
   - 回货数量、验收合格、验退（合格+验退=回货）
4. **回执**：展示接口返回；`--detail` 复核

### C. 供应商绩效独立查询（触发：准交率/良品率/供应商绩效/评估）

```bash
"$PY" "$SK/supplier_perf.py" --perf [--supplier XX]   # 全景(在手单+良品率+准交率),接口近一年
"$PY" "$SK/supplier_perf.py" --quality / --ontime     # 按良品率/准交率排序
"$PY" "$SK/supplier_perf.py" --overdue                # 逾期单数(接口无明细)
"$PY" "$SK/outsource_list.py" --hands                 # 在手委外单汇总(数据库清单)
```

### D. 清单/逾期（触发：待发货/在途/待回货/逾期）

```bash
"$PY" "$SK/outsource_list.py" --todo          # 待发货(可委外工单)
"$PY" "$SK/outsource_list.py" --intransit --overdue   # 在途且逾期
```

---

## 📐 统计口径（必须向用户说明，勿省略）

| 指标 | 口径 |
|------|------|
| **良品率** | 验收合格 /（验收合格+验退）×100%，按委外回货验收统计（近90天） |
| **准交率**（=准时率） | 已完成委外单（全部回货）中，最后一批回货日期≤要求回货日期的单数占比；按单聚合，当天内回货算准时 |
| **在手委外单数** | 委外中状态（未回货完成）的单数，按单号去重 |
| 委外单状态 | 1=委外中 2=部分回货 3=全部回货 |
| 无历史绩效 | 良品率/准交率为空（NULL），排最后，建议谨慎选择 |

**排序策略**：
- **品质要求高**：良品率最高 → 准交率次之 → 在手单数少者优先
- **急单/加急**：准交率最高 → 良品率次之 → 在手单数少者优先
- **未表态**：按品质优先；客户不选择 → 自动选第一名

---

## 已知边界（如实告知用户）

- **接口已配置（2026-08-17 用户提供并实测连通）**：
  - 查询：`/open-api/bp/getCanOutsourceList`（可委外清单）/ `/open-api/bp/getOutSourceList`（待回货清单）/ `/open-api/bp/getOutSourceDash`（供应商近一年绩效，无需参数，返回 list）
  - 执行：`/open-api/bp/SendOutsource`（发货）/ `/open-api/bp/sendOutsourceBack`（回货）/ `/open-api/bp/batchSendOutsourceBack`（批量回货）
  - 响应容器：`canOutList` / `list` / 兼容 LIST/MOLIST/OUTSOURCE_LIST/data 等；空数据会被后端校验拦截（"请选择数据后进行操作""操作数量不可为0"），不会产生脏单据
- **绩效数据源（2026-08-17 用户确认）**：供应商绩效（良品率/准交率/在手单/逾期）**一律走接口 `getOutSourceDash`（近一年），不读数据库**；`recommend_supplier.py` 与 `supplier_perf.py` 已全面接口化（接口失败即报错，不回退数据库）
- **鉴权**：标准 SSO 两段式（/sso/v1/code + /sso/v1/token）与账密登录（/account/v1/login）双模式，Bearer Token 自动缓存 1 小时、401 自动刷新；若报"第三方应用ID或密钥不正确"，需在平台 SSO 管理界面配置应用
- **数据实体分离（2026-08-17 用户要求）**：可委外清单与待回货清单是**两个独立数据实体**，处理逻辑完全分开、不共用容器——
  - 实体A 可委外清单：`getCanOutsourceList` → 容器 `canOutList`（`fetch_can_outsource`）
  - 实体B 待回货清单：`getOutSourceList` → 容器 `MOLIST`（`fetch_back_list`）
  - 绩效：`getOutSourceDash` → 容器 `list`（`fetch_supplier_perf`）
- 匹配规则：产品/工艺/供应商支持编号或中文名（编号传查询接口精确过滤，中文名本地模糊匹配）；同实体编号+名称任中其一即命中
- 候选供应商：优先工艺预设供应商；工艺无预设时扩到全部有委外记录的供应商
- 待发货清单为简化版（复用 GET_OUTSOURCE_LIST 非派工模式逻辑），强制派工模式口径可扩展
- 绩效接口固定近一年；清单类查询（outsource_list.py）非绩效口径，仍走数据库

---

## 示例对话

**用户**：紧固件FCW-01的钢材切割要委外
**AI**：查可委外（3张工单）→ 候选供应商按良品率排序：★F供应商（良品率100%、准交率100%）→ 建议选 F供应商，是否生成委外单？→ 用户"按推荐" → `outsource_tool.py --action send ... --dry-run` 预览 → 确认后执行 SendOutsource → 回执委外单号

**用户**：这批货很急，哪个供应商快
**AI**：切换准交率优先：★F供应商（准交率100%）→ 建议 F供应商 → 确认后生成委外单

**用户**：品质要求高，不能有不良
**AI**：良品率优先：★F供应商 良品率100% → 确认后生成委外单

**用户**：［上传回货单照片］
**AI**：识别到委外单 OU-20260811001、回货 10、验收合格 9、验退 1 → 核对在途 → 确认后调接口回货 → 回执

---

## 相关文件

- `config.json`：server(host/port) + apis(查询/执行接口路径) + auth(鉴权)
- `scripts/recommend_supplier.py`：**委外推荐核心**——候选工单 + 供应商绩效排序 + 推荐第一名（quality/ontime 双策略）
- `scripts/outsource_tool.py`：**执行 CLI**——查询清单接口 + 匹配 + dry-run 预览 + 调执行接口（发货/回货）
- `scripts/api_common.py`：OpenAPI 共享模块（SSO/账密鉴权、Bearer Token、401 刷新）
- `scripts/supplier_perf.py`：供应商全景绩效（在手单+良品率+准交率）/逾期明细
- `scripts/outsource_list.py`：待发货 / 在途待回货 / 在手单汇总 / 单号回货明细
- `docs/supplier_perf_sql.md`：SQL 整理文档（口径 + 全部 SQL + 验证结果）
