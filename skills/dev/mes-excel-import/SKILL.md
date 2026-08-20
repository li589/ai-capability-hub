---
name: mes-excel-import
display_name: 鼎华eMES 智能交付助手-excel导入
display_name_en: eMES Excel Data Import
description: "Import customer Excel data into eMES via OPENAPI: configure
  endpoint, parse Excel, confirm, import, and generate a report. Supports master
  data, check plans, inspection plans."
description_zh: 把客户 Excel 数据导入 eMES 系统（OPENAPI 数据维护接口）：配置地址→解析
  Excel→用户确认→导入→生成报告。支持基础资料、点检方案、检验方案等导入。
description_en: "Import customer Excel data into eMES via OPENAPI: configure
  endpoint, parse Excel, confirm, import, and generate a report. Supports master
  data, check plans, inspection plans."
category: data
version: 1.0.0
author: Digihua
trigger:
  - 导入
  - 数据导入
  - 基础资料导入
  - 交付
  - Excel
  - xlsx
  - xls
  - 新增接口
  - 配置服务器
  - 点检方案
  - 检验方案
  - 检验项目
  - 设备点检
  - 设备资料
  - 物料
  - 工单导入
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
disable-model-invocation: true
---

# 智能交付（eMES 数据导入）

> 将客户 Excel 数据导入 eMES 系统（OPENAPI 数据维护接口）。
> **触发规则**：用户直接提供 Excel/.xlsx/.xls 文件（无论是否附带"导入"指令）即触发解析与导入流程；说"导入、数据导入、新增接口、配置服务器"等关键词同样触发。

## 固定流程（5 步）

### 1. 首次使用配置（服务器 + 登录账号）
- ⚠️ **本技能不预制任何客户环境的 IP/端口/账号**（config.json 敏感字段为空，防止泄漏开发账号）。首次使用必须交互配置：
  ```bash
  "$PY" scripts/setup_config.py              # 交互式：问 IP/端口/登录账号/密码（密码不回显）→ 连通测试 → 保存
  "$PY" scripts/setup_config.py --check      # 验证配置是否完整可用
  "$PY" scripts/setup_config.py --get        # 查看当前配置（密码打码）
  ```
- 配置保存在本机 `config.json`（仅本机使用，**打包分发前已清空敏感字段**（config 不随包分发），新用户安装后运行 `scripts/setup_config.py` 交互填写）
- 每次 `run` 前会自动检测连接，失败会提示。

### 2. 解析 Excel
- 拿到客户 Excel 后，先解析结构：
  ```bash
  "$PY" scripts/deliver.py inspect <接口名> <excel路径>   # 接口字段 + 表头对照
  "$PY" scripts/auto_map.py <接口名> <excel路径>          # 术语词典自动映射
  ```
- **判断是否标准导入文档**（已存 `templates/` + `template_maps.json`）：
  - 是 → 走快速导入（跳过字段匹配）
  - 否 → 展示字段映射方案，**让用户确认**后再导入

### 2.5 合一表自动识别（单头+单身同表）
- **场景**：顾问为方便客户维护，常把单头字段和单身字段放在同一张表（head 字段只在每组**首行**填写，或每行都填；body 明细行跟在后面，一个 head 对应多行 body）。
- **自动识别**：`scripts/split_head_body.py` 按接口 spec 的 head/body 字段定义自动完成：
  1. 列定位：head 字段列 / body 字段列（支持中文表头 + col_map、英文字段名表头）
  2. 单头边界：head 字段"前向填充"后组合键变化 → 新单头（兼容仅首行填 / 每行都填两种模式）
  3. body 归属：head 为空的行自动归入最近单头
  ```bash
  "$PY" scripts/split_head_body.py <接口名> <rows.json> [col_map.json]   # 拆分预览
  # rows.json = parse_excel 输出的 rows 数组；输出 [{"head":{...},"body":[{...},...]}, ...]，
  # 与 nested 接口批量导入 payload 结构一致，可直接交给 batch_runner
  ```
- 验证：合一表拆分逻辑（英文字段表头/中文表头+col_map/每行都填 三场景）已通过实测

### 3. 用户确认
- 展示：Excel 表头 → 接口字段的映射、枚举转换（无→0、是→true、天→2 等）、跳过的列/数据（参考列、非标准日期、不等式区间）
- 用户确认或修正后执行

### 4. 导入数据
```bash
# 标准模板快速导入
"$PY" scripts/template_import.py --list                  # 看可用模板
"$PY" scripts/template_import.py 检验方案                # 按模板导入（逐条，重复自动跳过）

# 智能映射导入
"$PY" scripts/deliver.py run <接口名> "<excel路径>" --map '{映射JSON}' [--dry-run]
```
- 大数据量自动分批（500 条/批）；嵌套接口 head 自动合并、前向填充
- 建议 `--dry-run` 先校验，再正式导入
- 重复数据场景（接口批量含重复会整批回滚）→ 逐条导入

### 5. 结果报告
- 报告输出到 `reports/{接口名}_{时间戳}.xlsx`（成功绿/失败红 + 接口返回原因）
- 汇总：新增 X / 已存在 Y / 失败 Z

### 6. 导入进度跟踪与检核（方法论 3.7 / 4.1）
- 全接口导入完成后，运行进度跟踪脚本，输出《基础资料整理跟进表》：
  ```bash
  "$PY" scripts/track_progress.py --client "<客户名>" \
    --plan "eq_data:120,material_data:300,mo_data:80"   # 计划条数，按实际填写
  ```
- 自动按标准导入顺序（工厂→车间→工艺→设备→物料→工单→工艺路线→订单→领料→仓库→检验→点检→模具）汇总各接口最新报告，输出 xlsx：
  - **Sheet1 基础资料整理跟进表**：每接口 计划/成功/失败/格式错误/状态（✅完成 ⚠️部分 ❌失败/未导入）/完成率
  - **Sheet2 期初工单导入进度**（4.1）：从 mo_data 报告提取工单导入结果明细
  - **Sheet3 失败明细**：全接口失败行 + 原因，用于检核与二次导入
- 输出路径：`reports/{客户}_基础资料整理跟进表.xlsx`；可用 `--report-dir` 指定其他目录、`--out` 指定输出位置
- 检核用途：给客户/项目例会展示基础资料完善度，识别未导入接口与失败原因

## 新增接口流程（用户提供传参）

1. 用户提供新接口名（如 mold_data、emcheck_data）与**传参模板**
2. 探测接口：`POST /open-api/bp/{接口名}` 发空 body，从校验错误信息判断结构（平铺/嵌套、OperationType 是否必填、head/body 必填）
3. 按传参模板建 `api_specs/{名称}.json`（字段/类型/必填/枚举/默认值；无前缀 ID 与审计字段标 auto_generate 不传）
4. 注册 `config.json` 的 apis
5. dry-run 验证组装 → 真实调用测试（小数据）→ 更新 SKILL.md 状态表
6. 接口报错先检查是否为 BP 公式问题（报错含 `addPrb`/`编译失败` 多为接口侧配置，反馈客户修复）

## Token 鉴权（账密登录模式，默认开启）

- `config.json` 的 `auth`：`enabled` 开关、`mode` 支持两种换取 token 方式：
  - **`mode: "account"`（默认）**：`POST /account/v1/login`，body `{userName, password(前端算法加密), language, platform}` → `result.token.accessToken`（1 小时有效）。密码加密算法为前端 c436 模块：XOR(key, pwd) → btoa → reverse → btoa → reverse（key 常量已内置脚本）
  - **`mode: "sso"`（可选）**：① `POST /sso/v1/code`，body `{userNo, appId}` → 临时授权码；② `POST /sso/v1/token`，body `{appId, appSecret, code, language, envType, mode}` → accessToken
- **账号与密钥不预制**：`auth.account.user_name/password`、`auth.sso.app_id/app_secret/user_no` 默认空，由使用者通过 `scripts/setup_config.py` 交互填写（SSO 参数可选，账密模式无需 SSO）。**禁止把个人/开发账号写死在技能里分发**
- 每次调用自动检查 token，无/过期自动登录换取；401 时强制刷新重试一次
- 3.X 版本 SSO 路径不同：`/cms/api/inbound/v1/code` + `/cms/api/inbound/v1/token`
- 启用方式：`setup_config.py` 交互填写账号密码（或编辑 config.json 的 auth.account 并设 enabled=true）；若用 SSO 文档流程则改 mode="sso" 并填 auth.sso 配置

## 枚举知识库

- 完整 94 个系统枚举：`data/enum_knowledge.json`；接口相关摘要：`data/enum_knowledge.md`
- 常用：PQC_FREQUENCY 0无/1班别/2天；INSPECTION_TYPE 2数值/3开关；CHECKLIST_TYPE 1设备/2模具；CHECK_FREQUENCY 0无~7年；CHECK_TYPE 1标准/2区间/3开关；MATERIAL_TYPE 1产品/2物料；WAREHOUSE_TYPE 1成品/2报废；OP_TYPE 0无/1包装/2工位组装；DISPATCH_MOLD 1人员/2派工/3设备报工；MO_TYPE 1工单/2订单/3委外单

## 术语词典

- `term_dict.json`（297+ 条客户表头→字段）：品号→MA_ID、机台→EQ_ID、过程检验规则编号→PQC_RANGE_ID、交期→DAMAND_DATETIME 等
- 客户新叫法 → 维护术语字典（term_dict.json）后执行重建

## 接口清单（18 个，全部为 /open-api/bp/{接口} 路径，Bearer Token 鉴权）

| 旧接口名 | 新接口名（/open-api/bp/） | 说明 |
|---|---|---|
| factory_data | erp_fb | 工厂 |
| workstation_data | erp_ws | 车间 |
| eq_data | erp_eq | 设备 |
| material_data | erp_mb | 物料 |
| warehouse_data | erp_wb | 仓库 |
| me_op_data | erp_ob | 工艺 |
| process_route_data | erp_prb | 工艺路线（head/body 嵌套） |
| process_route_detail_data | erp_mrd | 领料（head/body 嵌套） |
| pqc_data | erp_ipd | 检验（head/body 嵌套） |
| emcheck_data | erp_emcheck | 点检方案（head/body 嵌套） |
| mold_data | erp_mold | 模具 |
| order_data | erp_sod | 订单（head/body 嵌套） |
| mo_data | erpInsertMoid | 工单 |
| customer_data | erp_customer | 客户（平铺，2026-08-18 注册） |
| qc_item_data | erp_qcitem | 检验项目主数据（平铺，2026-08-18 注册） |
| collection_data | erp_collect | 生产收集数据（head/body 嵌套，2026-08-18 注册） |
| bom_data | erp_bom | 产品BOM（平铺；⚠️无 OperationType + upsert 语义，2026-08-18 注册） |
| wage_data | erp_wage | 工价方案（平铺；ID/审计字段 auto_generate 不传，2026-08-18 注册） |

> 字段经新旧文档比对：前 13 个接口字段定义完全一致，仅路径与接口名变更。
> 其他新文档接口：AIGetCollData/AIGetMoList/AI_start_processing/AI_end_processing（AI 报工）、AIEqError/AIgetEqMainList/AIgetEqStatusList/AIGetOee/sendEqMainRecord（设备报修）、AC_MO_REPORT_PROCESS（工单报工记录表查询，Table 类型）——由对应产品助手 skill 使用。
> **员工/用户数据无 OPENAPI 接口**：通过 eMES 平台"用户管理"等功能导入，不走 /open-api/bp/ 通道（2026-08-18 确认）。

## 已知接口侧问题（反馈客户）

1. 重复插入报错信息公式 bug（addPrb 编译失败，本应提示"已存在"）→ 批量含重复会整批回滚，用逐条导入规避（⚠️ 仅限普通接口；**erp_bom 例外**：upsert 语义，重复数据自动更新不报错）
2. 接口文档会演进（工艺 SYS_OUT_SN、订单 body 都更新过）→ 导入前以客户环境实际接口文档为准核对
3. **erp_bom 特殊**：① 请求体**不含 OperationType**（spec payload.OperationType=null 显式禁用，batch_runner 不会追加）；② 数据**存在即更新、不存在即新增**（upsert），重复导入安全

## 目录结构

```
智能交付助手-excel导入/
├── SKILL.md                 # 本文件（对话版）
├── config.json              # 服务器地址 + 接口路径 + auth
├── api_specs/               # 接口字段定义（18 个）
├── templates/               # 标准模板（检验方案单头/单身）
├── template_maps.json       # 标准模板配置
├── (接口文档以客户环境实际为准，不随包分发)
├── data/                    # 枚举知识库 + 待导入数据
├── reports/                 # 导入报告
└── scripts/
    ├── deliver.py           # 主入口（inspect/run/config）
    ├── setup_config.py      # 首次使用配置（IP/端口/账号/密码，交互式）
    ├── auto_map.py          # 智能映射
    ├── template_import.py   # 标准模板快速导入
    ├── parse_excel.py       # Excel 解析
    ├── build_payload.py     # 参数组装（平铺+嵌套）
    ├── call_api.py          # 接口调用（超时/重试/Token）
    ├── batch_runner.py      # 分批调度 + 报告
    ├── split_head_body.py   # 合一表自动拆分（单头边界 + body 归属）
    ├── track_progress.py    # 导入进度跟踪/检核（跟进表 + 工单进度）
    └── gen_docs.py / gen_specs.py  # 知识维护
```
