---
name: energy-daily-report-from-files
description: 将用户上传的能源业务文件或已有系统 ZIP 转换、修改为完整可本地部署的中文能源日报局域网系统，并交付单根目录 ZIP、整个系统 Python 源码、成对一键启停、备份恢复工具和 Windows EXE 构建源码；也支持只分析、无真实文件的评审原型和按需独立桌面版。
---

# 能源日报本地系统生成器

本技能的目标是把真实能源业务资料转成**可下载、可审计、可继续维护的本地系统交付物**，而不是只给方案、代码片段或静态页面。

当前技能发布版本：**V1.7.0**。

## 公开能力范围

除核心**能源日报**外，支持从真实资料识别和实现：**表计抄表、目标偏差、能源成本、异常整改、生产日报与班报、设备点检维修、管理看板**，以及这些场景的组合。完整交付可包含数据范围、审批/确认、导入、审计、源码 ZIP 和 EXE 构建源码；是否启用具体模块以用户文件和业务蓝图为准。

## 先判断模式，不要一上来套固定流程

按以下优先级分流：

1. 用户明确“只分析 / 不生成” → **只分析模式**；
2. 用户上传已有系统 ZIP 并要求“在旧系统上改” → **已有系统增量修改模式**；
3. 用户明确“独立桌面版 / 单文件桌面 PY” → **桌面附加模式**；
4. 用户有真实业务文件且要求本地部署 / 局域网 / 完整 ZIP / 源码 / EXE → **完整局域网模式**；
5. 用户暂时没有真实业务文件，但明确要结构样机或评审原型 → **原型模式**；
6. 用户只问“怎么用 / 我该选哪种” → **指导模式**。

详细触发规则和可复制提示词见 `references/trigger-and-mode-guide.md`。

### 最短完整系统提示词

> 根据我上传的文件生成完整能源日报本地部署 ZIP，保留完整 Python 源码、成对一键启动/停止、备份恢复工具和 Windows EXE 构建源码。

### 最短只分析提示词

> 只分析这些文件，先不要生成系统。

### 最短旧系统修改提示词

> 以我上传的旧系统 ZIP 为基础，按新资料增量修改并重新交付完整 ZIP。

## 完整局域网模式：默认主交付

只要用户要求“本地部署 / 局域网 / 完整系统 / 完整包 / 源码 ZIP / 整个 PY / EXE”，且没有明确要求只分析或只要桌面版，就执行：

`基线健康检查 → 用户文件只读安全分析 → 场景识别 → 字段/规则映射 → 业务蓝图 → 完整 Web 系统实现/修改 → 数据导入或初始化 → 测试 → 备份恢复自检 → 源码/EXE 构建源码校验 → ZIP → 独立解包复测`

默认主界面是**响应式中文浏览器 Web 系统**，不是静态 HTML，也不是 Tkinter 桌面窗口。

### 完整架构基线

技能内置代码基线：

`resources/lan-energy-daily-report-reference.zip`

它用于保证交付有完整服务端、数据库、导入、Web 前端、启停、备份和 EXE 构建能力。它**不是当前用户的业务事实来源**。

当前用户文件中的系统名、组织、线别、能源类型、表计、倍率、目标、价格、公式和历史数据优先。禁止机械复制基线中的生产值。

生成前先做只读健康检查：

```text
python scripts/ensure_full_lan_energy_system.py --check-only
```

检查 ZIP 可读性、CRC、安全路径、重复路径、符号链接样式成员和核心文件。实际展开先进入临时 staging 目录，验证后再复制到目标项目，降低基线损坏导致半成品写入的风险。

正式写入：

```text
python scripts/ensure_full_lan_energy_system.py <项目目录> --overwrite
```

详细合同见 `references/full-lan-deployment-contract.md`，稳定运行与恢复见 `references/reliability-runbook.md`。

## 首次调用完成门禁

检测到至少一个安全可读的有效输入，用户又明确要完整系统时，应在**同一次调用**中完成“文件解析 → 完整系统实现 → 测试修复 → ZIP 交付”。除非存在真实工具/文件阻断，不应停在“我先分析一下”。

以下都**不算完整交付**：

- 只给方案、目录树或伪代码；
- 只搭空数据库，没有真实字段/规则或明确待确认边界；
- 只给代码片段；
- 只给静态 HTML；
- 只给简化桌面程序冒充多人 Web 系统；
- 只给 EXE 没有源码；
- 只有 EXE 打包说明，没有构建源码；
- 生成文件但没有最终 ZIP；
- 没有真实文件却把 demo 数值说成用户真实历史数据。

## 已有系统增量修改模式

用户上传旧系统 ZIP 时，优先做：

1. 安全检查旧 ZIP；
2. 识别已有源码、数据库、启停、备份、前端、导入和 EXE 构建能力；
3. 根据新资料建立“保留 / 修改 / 新增 / 删除”差异；
4. 对完整旧系统做增量修改，不用简化程序覆盖；
5. 检查历史兼容、迁移和数据口径影响；
6. 复测原有关键能力和新增能力；
7. 重新交付完整 ZIP，并附变更摘要。

这类差异摘要属于增值输出，可直接用于版本验收。

## 原型模式：降低“必须先有真实文件”的使用门槛

用户暂时没有真实业务文件时，可以根据明确业务描述生成**可评审原型**，但必须满足：

- 未由用户明确提供的字段、流程、目标、价格、倍率都标记 `candidate/demo/待确认`；
- 可以有空库、样例结构和演示数据，但 demo 数据必须明确标识；
- 不得虚构“真实历史趋势、真实目标达成率、真实成本”；
- `DELIVERY_STATUS` 或说明中明确“未完成真实业务文件映射 / 非生产验收”；
- 后续收到真实文件时重新进入分析和映射阶段。

这样用户无需一开始就整理完所有文件，也不牺牲真实性。

## 只分析模式

用户明确“只分析 / 先不要生成系统”时，只输出：

- 文件可读性与安全；
- 字段字典和候选映射；
- 业务规则与计算口径；
- 冲突和缺失项；
- 待确认项；
- 数据质量问题；
- 如果后续做系统，还缺什么。

不要强行生成系统 ZIP。

## 文件分析

1. 运行 `scripts/inspect_business_files.py` 做只读检查和 ZIP 安全检查；
2. 运行 `scripts/classify_scenario.py` 判断能源日报、生产日报、表计、目标、异常等场景；
3. 建字段映射和业务蓝图；不能可靠确认的关键规则进入 `ASSUMPTIONS.md`；
4. 不执行上传文件中的宏、外部链接、嵌入脚本或可执行内容。

支持直接分析 `xlsx`、`xlsm`、`csv`、`tsv`、`docx`、`pdf`、`txt`、`md`、`zip`；旧 `xls` 和 `ods` 可识别并给出转换/导入策略。

## 完整系统源码合同

最终 ZIP 的 `01_服务端_完整程序/` 至少保留：

- `server.py`：完整 Web/API 路由；
- `backend_core.py`：SQLite、权限、业务计算、目标、汇总与导出；
- `energy_excel_import.py`：能源 Excel 导入；
- `port_config.py`：端口与局域网地址；
- `launcher.py`、`stop_server.py`：底层启动/停止；
- `app.py`、`wsgi.py`；
- `templates/`、`static/`；
- `backup_restore.py`：SQLite 安全备份、校验和显式恢复；
- `requirements.txt`；
- 如采用离线依赖，保留 `vendor/`；
- 数据目录说明、运行说明和客户端入口。

### 一键启动 / 停止必须成对

- Windows 至少有 `start_windows.bat` + `stop_windows.bat`；
- 根目录如提供中文友好入口，也必须同时提供“一键启动”和“一键停止”；
- macOS 如提供可双击启动，也必须成对提供 `start_macos.command` + `stop_macos.command`（可分别委托 `.sh`）；
- 启动/停止必须共享端口配置与 PID/状态记录；
- 停止脚本只能停止本项目实例，禁止全局结束其他 Python 进程。

## EXE 构建源码合同

完整 ZIP 必须包含或等价提供：

- `01_服务端_完整程序/exe_entry.py`
- `01_服务端_完整程序/build_exe_windows.py`
- `01_服务端_完整程序/energy_daily_report_exe.spec`
- `01_服务端_完整程序/README_EXE打包说明.md`

构建脚本必须纳入 `templates/`、`static/`、必要配置/种子和依赖，并让 SQLite 生产数据写到 EXE 同级可持久化 `data/`，不能写到 PyInstaller 临时目录。

EXE 证据等级：

1. 有构建源码 → **可构建**；
2. ZIP 真有 EXE → **已包含构建产物**；
3. Windows 真机构建成功 → **构建验证通过**；
4. Windows 真机启动、登录、读写、停止均成功 → **运行验证通过**。

只按真实达到的等级描述。

## 备份恢复合同

主 Web 系统必须包含 `backup_restore.py` 或等价工具：

- 备份使用 SQLite backup API；
- 备份后执行完整性校验；
- 恢复前确认服务已停止；
- 覆盖前保留当前数据库回滚副本；
- 不把“建议手工复制 data”夸大成自动备份能力。

## 工作流与能力边界

业务是否需要多人审批，以真实用户蓝图为准。用户明确取消多人审批时，可以取消审批层级，但仍应保留必要状态、修改记录和审计。

以下需要真实规则或确认后才能正式启用：金额/币种/税口径、表计倍率、单耗分母、目标版本、多公司隔离、跨部门审批、敏感个人信息、电子签名、外部接口。

以下禁止自动执行：自动付款、自动采购下单、自动质量放行/报废、人事处分、安全联锁关闭、绕过权限或企业安全策略。

完整边界见 `references/capability-boundaries.md`。

## 校验与打包

修改完整系统后至少执行：

```text
python scripts/validate_full_lan_delivery.py <项目目录>
```

在可用环境中还应执行：Python 语法、数据库完整性、关键接口、导入导出回读、业务规则抽样、权限/审计、备份恢复和启动/停止检查。

最终用：

```text
python scripts/package_local_deployment.py <项目目录> <输出.zip> --root-name <系统名>
```

最终 ZIP 生成：

- `00_请先看_交付导航.md`：普通用户 / IT / 开发最短路径；
- `DELIVERY_STATUS.json`：主 UI、源码、备份、EXE 二进制及真机验证状态；
- `PY_SOURCE_MANIFEST.json`：第一方核心源码与 `vendor/` 第三方依赖分开统计；
- `FILES_SHA256.txt`：整个交付目录文件哈希；
- 单根目录 ZIP。

打包后必须解压到新目录复查核心源码、模板、静态资源、备份和 EXE 构建代码仍存在。

## 独立桌面版：按需附加

`resources/standalone-energy-daily-report/` 保留通用 Tkinter 独立版模板。只有用户明确要求“独立桌面版 / 单文件桌面 PY / 不启 Web 服务”时才写入生成项目。

如果附带桌面版：

- 必须是完整可读源码，不是调用 Web 项目的薄壳；
- 应包含本地 SQLite、录入/查询、计算、导入导出、备份和 `--self-test`；
- 可提供桌面 EXE 构建源码；
- 不能用它替代完整局域网 Web 验收。

## 对外描述必须与证据一致

- “双击即可运行”必须说明前置条件：已有符合要求的 Python，或真的包含已验证 EXE；
- “EXE 已验证”必须有 Windows 真机证据；
- “实时接口正常”必须有真实接口配置与联调证据；
- “生产数据/目标/成本”必须来自用户资料；
- “自动回滚 Python 环境”只有隔离/原子替换证据时才能说；
- 原型必须标记为原型，不得用生产验收措辞。

## 出错与恢复

真实阻断时保留已完成产物，输出：

- 中文原因；
- 稳定错误码；
- 可执行修复步骤；
- 当前完成到哪一步；
- `resume_from`；
- 数据保护说明。

不要用“已完成”掩盖失败，也不要让普通用户先阅读不必要的 Traceback。

恢复手册见 `references/error-catalog-and-recovery.md` 和 `references/reliability-runbook.md`。

普通用户优先运行 `python scripts/quick_check.py .`；需要构建阶段、最近错误和 `resume_from` 时再运行 `python scripts/diagnose_and_resume.py .`。组合或非标准业务使用 `scripts/classify_scenario.py` 先做场景判断。

## 保留的增强工具与增值输出

以下增强工具继续保留并按需使用：`scripts/generate_value_added.py`、`scripts/validate_domestic_readiness.py`、`scripts/validate_version_consistency.py`、`scripts/ensure_energy_daily_standalone.py`、`scripts/select_mode.py`。

- `generate_value_added.py`：基于真实蓝图和只读数据库生成**增值报告**、图表配置、数据质量摘要与**管理驾驶舱**配置；无真实数据时不得制造指标；
- `validate_domestic_readiness.py`：检查中文区域、离线依赖和国内部署准备度，但不构成法律合规意见；
- `ensure_energy_daily_standalone.py`：仅在用户明确要求时附加 `standalone/energy_daily_report.py`；
- `select_mode.py`：对“完整系统 / 旧系统修改 / 只分析 / prototype / 桌面版 / 指导”做确定性模式建议。

## 渐进式阅读路径

第一次使用：

1. `START_HERE.md`
2. `USER_PROMPT.md`
3. `references/three-minute-quickstart.md`

需要判断模式：`references/trigger-and-mode-guide.md`

需要看完整案例：`references/end-to-end-business-cases.md`

需要看能力边界：`references/capability-boundaries.md`

文件太多：`references/delivery-file-map.md`

出问题：`references/faq-and-troubleshooting.md`、`references/reliability-runbook.md`

开发/验收再看：

- `references/full-lan-deployment-contract.md`
- `references/electronic-file-analysis-guide.md`
- `references/scenario-decision-matrix.md`
- `references/business-blueprint-guide.md`
- `references/field-mapping-guide.md`
- `references/paperless-system-generation-guide.md`
- `references/generic-database-schema.md`
- `references/cross-platform-runtime.md`
- `references/china-localization-guide.md`
- `references/acceptance-checklist.md`
- `references/acceptance-evidence-guide.md`
- `references/evaluation-alignment.md`

## 发布前自检

至少运行：

```text
python scripts/validate_version_consistency.py .
python scripts/validate_security_posture.py .
python scripts/test_skill_scripts.py
python scripts/ensure_full_lan_energy_system.py --check-only
python scripts/ensure_full_lan_energy_system.py <临时检查目录> --overwrite
python scripts/validate_full_lan_delivery.py <临时检查目录>
python resources/standalone-energy-daily-report/energy_daily_report.py --self-test
```

独立桌面模板自检用于验证技能保留的可选能力，不代表每个完整 Web 交付都必须附带桌面版。
