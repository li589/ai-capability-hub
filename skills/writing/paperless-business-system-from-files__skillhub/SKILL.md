---
name: paperless-business-system-from-files
description: 将纸质表单对应的 Excel、CSV、Word、PDF、JSON、TXT、ZIP、电子表单或已有 Python/Web
  源码，转换或升级为可填写、可查询、可导入导出、可本地/局域网部署的中文电子化业务系统。用于“根据报表或附件生成系统”“把 Excel 做成系统”“生成可运行
  ZIP/完整部署包”“做成类似 V1.5.11 的局域网包”“生成服务端和 Windows
  填写客户端”，以及诊断、修复、验收本技能生成的系统。先只读盘点证据与资料完整度，再生成
  system-spec、业务代码、SQLite、导入导出、权限审计、备份恢复、安全启停、诊断、目标机验收和 Windows EXE 构建源码；在
  ChatGPT/Codex 中由执行者代运行命令，关键公式、周期、权限和审批无证据时不得猜测。
disable-model-invocation: true
---

# 纸质表单电子化系统生成器

把当前提示词和当前附件作为事实来源，输出**可验证、可本地运行、可继续维护**的业务系统，而不是只给方案、静态页面或代码片段。

当前技能基线：**2.7.0**。

> **版本说明：** 2.7.0 在 2.6.0 的“业务理解 + 自动生成”基础上补齐**运行验收与安全升级闭环**。新增 `test` 命令，在隔离副本中真实启动系统并覆盖健康检查、登录、CRUD、严格类型校验、CSV 导入预览/确认、XLSX 导出、安全停止、SQLite 备份/恢复；`validate --strict` 不再把未测试项目判为通过。新增 `upgrade` 命令，对旧/新 `system-spec` 做差异分类并默认只自动处理新增对象/新增字段。业务关系推断升级为“字段语义 + 样本值重合 + 唯一性”，生成表单增加日期、布尔、枚举、数字控件与统一服务器端校验。候选关系、审批链、正式统计口径仍遵守“无证据不猜测”。

## 0. 30 秒快速入口

### 用户只做一件事

上传业务资料，然后直接说：

> **“把这些资料做成 Windows 本地中文业务系统，先分析资料；确认能做后自动生成、测试并给我完整 ZIP。”**

执行者负责其余步骤。不要让非技术用户自己拼参数。

### 技术人员只记一个入口

本技能新增统一路由器：

```bash
python scripts/run_skill.py analyze "<资料>" --output "<工作目录>"
python scripts/run_skill.py scaffold --spec "<工作目录>/system-spec.json" --output "<仅工程骨架目录>"
python scripts/run_skill.py generate --spec "<工作目录>/system-spec.json" --output "<完整业务项目目录>"
python scripts/run_skill.py test --project "<项目目录>"
python scripts/run_skill.py validate --project "<项目目录>" --strict
python scripts/run_skill.py upgrade --project "<旧项目目录>" --spec "<新system-spec.json>" --output "<升级副本目录>"
python scripts/run_skill.py diagnose --source "<资料>" --project "<项目目录>" --strict
python scripts/run_skill.py package --project "<项目目录>" --output "<交付ZIP>"
python scripts/run_skill.py self-test
```

它只是现有脚本的统一入口，不替换原脚本；原命令仍然有效。完整示例见 `references/quickstart-and-evidence.md`。

### 能力状态必须这样表述

技能输出中禁止把“设计支持”直接写成“已经可用”。统一使用以下五级证据：

1. **设计支持**：规则/脚手架中存在该能力；
2. **已生成**：本次项目已经生成对应文件或模块；
3. **静态验收通过**：结构、安全、哈希、配置等自动检查通过；
4. **运行验收通过**：本次已实际启动、操作并通过对应测试；
5. **目标机实测通过**：目标 Windows 电脑已实际验证，例如断网、EXE、局域网或客户端连接。

只有达到对应证据等级，才能使用“已验证、断网可用、免 Python、局域网可用、解压即用”等表述。

## 0.1 用户操作说明：只上传“提示词 + 对应业务资料”

### 用户端只需要做 3 步

**第 1 步：上传业务提示词**

提示词可以是 TXT、DOCX、PDF，也可以直接在对话框输入。内容只需要说明“想做什么系统、给谁使用、希望解决什么问题”。不要求用户写技术参数。

示例：

> 请根据下面的业务资料，做一个中文 Windows 本地业务系统。保留原来的表单填写习惯，实现录入、查询、修改、统计、Excel 导入导出。请自动识别业务规则；能确认的直接生成，不能确认且会影响业务结果的地方再提醒我。最后完成测试并输出完整 ZIP。

**第 2 步：上传对应业务资料**

把与提示词对应的 Excel、CSV、Word、PDF、ZIP、JSON、TXT、已有源码或历史数据一起上传。可以一次上传多个文件，不需要先整理目录，也不需要给文件重命名。

**第 3 步：点击生成 / 直接发送“开始生成”**

用户不需要执行 Python、命令行、参数组合、脚本选择或手工拼接配置。执行者自动完成：

`提示词 + 业务资料 → 资料识别 → 业务建模 → system-spec → 系统生成 → 数据检查 → 测试验收 → ZIP交付`

### 用户不需要提供的内容

- 不需要写 Python 代码；
- 不需要知道 SQLite、Flask 等技术；
- 不需要填写脚本参数；
- 不需要选择应该运行哪个脚本；
- 不需要自己判断业务属于 energy / pointwork / operations 等类型；
- 不需要自己整理字段映射；
- 不需要自己打包 ZIP。

### 只有以下情况才向用户提问

如果附件已经能证明规则，直接采用附件事实；只有缺失内容会影响金额、工时、审批、权限、唯一键、历史数据或正式统计口径时，才向用户提出最少量确认问题。其他可由工程默认值解决的内容由执行者自动处理。

### 用户最终只应看到

1. **识别结果**：识别到了什么业务、哪些资料有效；
2. **处理结果**：哪些功能已经生成；
3. **验收结果**：哪些项目已经自动验证，哪些需要目标电脑实测；
4. **交付物**：完整 ZIP、使用说明、版本信息和必要的待确认事项。

不要把内部命令、Python traceback、JSON 中间文件或复杂参数表作为用户完成任务的前置条件。

## 0.1 执行约定：用户零命令、过程可恢复

- 在 ChatGPT/Codex 中触发时，由执行本技能的智能体读取附件、运行脚本、诊断、验收和打包；除非用户明确索要本地操作说明，不得把命令行步骤留给用户完成。
- 用户只需提供业务材料并说明想做什么。只在缺失规则会影响金额、工时、审批、权限、唯一键或历史数据时提问；能从附件验证的内容不重复询问。
- 每个阶段先报告“已确认、待确认、当前阻断、下一步”。中断后从最近通过的阶段继续，不覆盖已生成数据库或已确认规则。
- 命令失败时不得只转发异常文本。按“发生了什么 → 原因/位置 → 现在怎么处理 → 从哪里继续”四项向用户解释，并保留原错误码。
- 需要快速案例、能力证据等级、声明边界时读取 `references/quickstart-and-evidence.md`；需要命令示例、错误码、FAQ 或反模式时读取 `references/usage-and-troubleshooting.md`。

## 1. 适用与不适用

### 1.1 最短使用方式

非技术用户不需要先理解参数。直接提供业务资料并说明目标即可，例如：

- **普通本地系统：**“把这些 Excel 做成一个 Windows 本地业务系统，保留原表字段，能录入、查询、统计、导入导出，最后给我完整 ZIP。”
- **局域网系统：**“把这些表单做成局域网多人使用的系统，要求中文、断网可用，并给出完整部署包。”
- **已有系统升级：**“在不删除原数据库和历史数据的前提下，把这些新表单和规则合并进现有系统。”
- **只分析不生成：**“先分析这些资料，告诉我字段、业务规则、缺失资料和能不能做成系统。”

执行者应根据目标自动选择路由，不要求用户自己拼接脚本参数。


使用本技能时，用户通常会提出以下目标之一：

- 根据 Excel/CSV/Word/PDF/ZIP 生成业务系统；
- 把现有表格流程改成本地或局域网系统；
- 根据已有源码和新附件继承升级系统；
- 生成完整可运行 ZIP、Windows 启停脚本或 EXE 构建源码；
- 生成 V1.5.11 级 `portable_full` 完整部署包（服务端 + Windows 填写客户端 + 局域网工具 + 版本资料 + 条件式 macOS 客户端）；
- 根据业务资料自动识别能源、点工/考勤、运营记录、生产、质量、设备、库存、审批或组合业务。

如果用户只要求分析报表、写方案、做单个文档或修改少量代码，不要强行生成完整系统。

### 快速路由

| 用户表达 | 默认动作 |
| --- | --- |
| “把这个 Excel/这些文件做成系统” | `local_or_lan`，核心断网可用，先自动识别业务类型 |
| “局域网多人使用” | 明确 `--network-mode lan`；不等于自动启用完整部署包装 |
| “完整部署包、类似 V1.5.11、服务端+填写客户端” | `portable_full`；只有用户同时要求多人访问时再启用 `lan` |
| “升级这个已有系统” | 优先继承源码、数据库、迁移、客户端和历史数据，不推倒重写 |
| “只分析/只给方案/只改一个文件” | 不进入完整系统生成流程 |

## 2. 事实优先级

业务事实按以下顺序处理：

1. 用户当前任务中的明确要求、修改和禁止项；
2. 正式制度、字段说明、表单模板、已有源码和数据库；
3. 可验证的工作簿/CSV/JSON 结构、公式、历史数据与文件间关系；
4. 本技能的 Profile、工程骨架和默认值。

第 4 项只能补工程能力，不能覆盖前 3 项。

会改变金额、工时、审批、权限、唯一键、历史数据或正式统计口径的冲突不得静默处理。把冲突写入 `BUSINESS_CONFLICTS.md`；可安全继续但尚未确认的内容写入 `ASSUMPTIONS.md` 或 `system-spec.json.open_questions`。

## 3. 第一步：运行时初始化，而不是把结果预置在技能包

正常任务由执行本技能的智能体先运行：

```bash
python scripts/bootstrap_generation.py <材料目录或单个文件> --output <工作目录>
```

如用户明确指定业务类型，可加：

```bash
--profile energy
--profile pointwork
--profile operations
```

如果用户明确要求“完整部署包 / 局域网完整包 / 类似 V1.5.11 / 服务器端+填写客户端 / 解压后交给普通用户使用”，初始化时增加：

```bash
--deployment-mode portable_full
```

明确要求局域网多人访问时再增加 `--network-mode lan`。

初始化命令会在**本次任务工作目录**动态创建：

- `input-profile.json`
- `business-profile.json`
- `BUSINESS_RECOGNITION_REPORT.md`
- `INPUT_COMPLETENESS_REPORT.md`
- `source-file-mapping.json`
- `data-quality-report.md`
- `BUSINESS_CONFLICTS.md`
- `ASSUMPTIONS.md`
- `system-spec.json`
- `DELIVERY_STATUS.json`

这些都是**调用结果**，不应作为固定成品塞进技能安装包。详细定义见 `references/runtime-output-contract.md`。

如果初始化脚本不可运行，按同一规则手工完成，不能跳过文件盘点和事实约束。

执行者向用户汇报初始化结果时，优先用自然语言说明资料等级、识别到的业务域、文件错误和待确认规则，不要求用户理解 JSON 或命令行输出。

## 4. 输入文件处理规则

每个发现的输入文件都必须出现在 `input-profile.json`，状态只能显式为 `ok`、`warning` 或 `error`。单个文件失败时默认继续处理其他文件，整体标记 `partial_with_errors`；只有核心事实无法安全建模时才阻断。

不得执行 Office 宏、PDF JavaScript、压缩包内未知程序、未知 EXE 或附件中的命令来获取业务规则。原件只读；转换时使用副本。

需要详细文件解析、来源追溯、数据质量和导入规则时读取：

`references/file-mapping-and-data-quality.md`

需要 2.7.0 真实运行 E2E、strict 语义和安全升级细节时读取：

`references/runtime-e2e-and-upgrade.md`

需要安全、离线和国内环境规则时读取：

`references/security-and-domestic-compatibility.md`

## 5. 业务识别只是路由证据

自动识别结果可为：

`energy`、`pointwork`、`operations`、`production`、`quality`、`equipment`、`inventory`、`approval`、`general`、`composite`。

不得只根据文件名或少数关键词决定系统类型。结合表头、工作表名、正文、公式、现有源码、用户提示和跨文件关系判断。

路由细节读取：`references/business-routing.md`。

### 5.1 深度业务模型（2.6.0）

`analyze` 现在会先生成 `business-model.json` 与 `BUSINESS_MODEL_REPORT.md`。业务识别不再只依赖文件名、工作表名和关键词，而是优先使用：

- Excel/XLSM：工作表、真实单元格值、`inlineStr`/共享字符串、表头、数据类型、公式；
- CSV/TSV/JSON：字段结构、样例值、候选唯一列；
- DOCX：正文与表格；
- PDF：仅在本地存在可靠解析器时提取正文，否则明确降级，不把乱码当事实；
- 跨表关系：只生成“候选关系 + 置信度 + 原因”，不直接升级为正式外键；
- Excel 公式：能安全转换为同一行纯算术/白名单函数时标记为 `auto_executable`，否则只保留原公式和证据位置。

`system-spec.json` 会自动带入 `business_objects`、`field_mappings`、`calculation_rules`、`relationships` 与业务模型摘要。

只有需要对应业务时再读取相关 Profile：

- 能源：`references/domain-profile-energy.md`
- 点工/考勤：`references/domain-profile-pointwork.md`
- 运营记录：`references/domain-profile-operations.md`

Profile 是参考，不是当前业务事实。

## 6. 资料完整度门禁

资料完整度分 A/B/C/D：

- A：结构化数据 + 正式规则 + 现有源码/数据库证据较完整；
- B：有结构化数据，并有规则或源码证据；
- C：主要是报表/模板；可生成确定部分，关键规则保持待确认；
- D：缺少可验证结构化材料；只能生成通用原型/骨架，不得宣称已还原正式业务口径。

任何等级都不得无证据补齐考勤周期、金额/工时公式、目标方向、审核、权限或唯一键。

## 7. system-spec 是生成代码前的唯一业务规格入口

在写业务代码前先完善 `system-spec.json`。至少覆盖：

- 系统名称、业务域、部署模式；
- 业务对象、字段类型、唯一键、历史快照；
- 计算公式及证据来源；
- 角色、权限、数据范围、字段级权限；
- 状态机与审批链；
- 导入预览、防重和事务策略；
- 报表、看板、打印/导出；
- 审计、备份、恢复、迁移、升级；
- 目标机验收和未确认事项。

动态字段场景优先使用 schema snapshot；字段重命名/拆分时保留显式旧→新映射，默认非破坏式迁移。

### 7.1 自动生成完整业务模块（2.6.0）

当 `business_objects` 已有可追溯字段结构后，优先使用：

```bash
python scripts/run_skill.py generate --spec "<工作目录>/system-spec.json" --output "<项目目录>"
```

该命令会先生成通用工程底座，再自动物化：

- 每个业务对象对应的 SQLite 业务表与迁移；
- 新增、修改、删除、列表、查询、分页；
- Excel/CSV 导入，且必须先预览再确认写入；
- Excel 导出；
- 按业务对象生成 RBAC 权限并自动赋予管理员；
- 增删改导入导出的审计日志；
- 对 `auto_executable=true` 的安全公式在服务器端重新计算；
- `AUTO_GENERATION_REPORT.md` 与 `business/generated_schema.json`。

候选唯一键不会自动建立数据库 `UNIQUE`。只有在 `confirmed_unique_keys` 中明确确认的键才会生成正式唯一约束。审批、金额/工时正式口径、跨表强外键和字段级权限仍必须满足证据门槛。

### 7.2 运行级 E2E 与严格验收（2.7.0）

生成后优先执行：

```bash
python scripts/run_skill.py test --project "<项目目录>"
python scripts/run_skill.py validate --project "<项目目录>" --strict
```

`test` 永远在**隔离副本**中运行，不改写原项目业务数据库。通过后会更新 `TEST_REPORT.md` 与 `DELIVERY_STATUS.json.runtime_e2e_verified`。测试覆盖：启动与 `/health`、管理员登录、CRUD、数字/日期/布尔等严格类型校验、CSV 逐行导入校验、XLSX 导出、项目级安全停止、SQLite 备份/恢复与完整性检查。

2.7.0 起，`validate --strict` 如果发现 `tests_executed` 为空、`runtime_e2e_verified != true` 或 `TEST_REPORT` 仍为“未执行”，必须失败。**静态验收通过不再等同于系统可用。**

### 7.3 安全升级已有系统（2.7.0）

```bash
python scripts/run_skill.py upgrade --project "<旧项目目录>" --spec "<新system-spec.json>" --output "<升级副本目录>"
```

升级流程先生成 `UPGRADE_DIFF_REPORT.md` 与 `upgrade-diff.json`，将变化分成：

- `safe_additive`：新增对象、新增字段，可自动创建升级副本；
- `review_required`：标签、唯一约束、公式、权限/流程等变化，需要业务复核；
- `breaking`：删除对象、删除字段、字段改类型，默认阻断自动升级。

升级始终生成**新副本**并保留旧 `system-spec.before-upgrade.json`；不会直接修改原项目。SQLite 运行时会检查旧表结构并非破坏式补齐缺失的新字段。破坏性变化即使使用 `--allow-breaking` 也只是允许生成升级副本，不代表迁移风险已经自动消除，仍必须人工迁移演练与重新 E2E。

## 8. 从零生成与继承升级

### 有现有源码/数据库

优先继承升级。先识别数据库、迁移、权限、路由、导入导出、启停、测试和历史兼容，不得无理由推倒重写。

### 无现有源码

完善 `system-spec.json` 后运行：

```bash
python scripts/run_skill.py generate --spec <工作目录>/system-spec.json --output <项目目录>
```

`generate` 会自动物化有证据支撑的业务对象、字段、CRUD、搜索、导入导出、RBAC、审计和安全公式；审批、正式唯一键、复杂统计与无证据规则继续按待确认项处理。只有明确只要工程底座时才使用 `scaffold`。

公共工程模式见 `references/proven-system-patterns.md`；骨架边界见 `references/scaffold-contract.md`。

## 9. portable_full 完整部署包模式

当 `system-spec.json.system.deployment_mode = "portable_full"` 时，不得只交付扁平源码目录。必须按 `references/portable-full-contract.md` 生成 V1.5.11 级完整包装：

- `01_服务端_完整程序/`；
- `02_Windows填写客户端/`；
- 条件式 `03_macOS填写客户端/`；
- `04_业务原始资料参考/`、`05_电子档模板/`；
- `06_说明与版本记录/00_当前版本/`；
- 根目录一键启停；
- Windows 客户端服务器地址设置、连接测试；
- 局域网地址/端口辅助；
- 明确运行时策略与“免 Python/完全离线”声明证据。

继承现有 V1.5.11 类系统时，优先保留其完整部署结构、数据、迁移、客户端和运行生命周期，不得降级为简化源码包。

`portable_full` 额外验收：

```bash
python scripts/validate_portable_full.py <项目目录> --strict
```

只有实际带入并验证 EXE 或便携运行时，才能宣称“免 Python 解压即用”；只有依赖也可离线获得时，才能宣称“首次安装完全离线”。

## 10. 默认本地部署技术栈

> **能力边界先说明：** 默认生成目标是 Windows 10/11 上的 Python 本地 Web 系统。默认技术栈不是“只能生成 Python”的营销承诺，而是本技能当前脚手架和验收体系的实际实现边界。用户若要求非 Python、iOS 原生、Android 原生、纯前端静态站或其他技术栈，应先说明需要重新设计生成底座，不能直接声称当前技能已经支持。


除非用户指定其他技术栈，默认：

- Python 3.10+
- Flask + Jinja2
- SQLite
- 原生 JS/CSS
- openpyxl/XlsxWriter
- Waitress
- `zh-CN`
- 默认业务时区 `Asia/Shanghai`
- Windows 10/11 为第一目标
- 核心功能断网可用，不依赖 CDN、远程字体或在线许可证

单机默认监听 `127.0.0.1`；只有明确要求局域网共享时才监听内网地址。端口必须可配置。

## 11. 必须具备的工程能力

正常“生成系统”任务至少实现：

- 登录、改密、退出；
- 服务端 RBAC 与必要的数据范围/用户覆盖；
- 审计日志；
- SQLite WAL、事务、参数化 SQL、迁移；
- 真实 Excel/CSV 导入预览、校验、防重、导出；
- 备份、完整性检查、恢复前回滚副本；
- 健康检查；
- 项目专属安全启动/停止；
- 一键诊断；
- 目标电脑验收入口；
- Windows EXE 构建源码与 PyInstaller spec；
- 中文运行说明与已知限制。

审核链不得写死，可为无审核、单级、串行多级、并行多审核人或任意 N 人完成。只有附件有证据时才落定具体规则。

## 12. 启停与迁移硬规则

停止脚本必须只控制本项目实例，禁止：

- `taskkill /IM python.exe`
- `taskkill /F /IM pythonw.exe`
- `killall python`
- `pkill -f python`

推荐共享项目专属 PID/状态文件、端口和随机 shutdown token。

数据库升级前备份；迁移显式版本化、幂等、失败可回滚；禁止升级时静默重算已确认历史值。

## 13. 最终交付

除非用户明确只要方案/原型/单文件，正常“生成系统”任务默认交付完整 ZIP。

完整交付契约见：

`references/local-deployment-contract.md`

交付前按：

`references/acceptance-checklist.md`

执行验收。

至少运行：

```bash
python scripts/validate_local_bundle.py <项目目录> --strict
```

如果是 `portable_full`，还必须运行：

```bash
python scripts/validate_portable_full.py <项目目录> --strict
```

如果项目包含 `delivery-manifest.json`，再运行：

```bash
python scripts/validate_delivery.py <项目目录> --strict
```

最终打包优先运行：

```bash
python scripts/finalize_delivery.py <项目目录> --output <系统.zip>
```

只有验证成功后才能宣称“完整交付”。

## 14. 价值报告与验证表述

`VALUE_REPORT.md` 只有收到真实 `before_minutes`、`after_minutes`、`sample_count` 时才允许计算效率变化。不得用演示数据、经验值或模型估算冒充实测。

Windows EXE 未在 Windows 真机实际构建和运行时，只能表述为“已包含构建源码，未完成真机验证”。静态检查不能替代目标电脑验收。

## 15. 异常恢复与有限重试

任何脚本返回非零状态时：

1. 保留错误码和最小定位，不用大段堆栈代替解释；
2. 读取 `references/usage-and-troubleshooting.md`，给出用户可执行的修复动作和恢复点；
3. 原因不明确时运行 `python scripts/diagnose.py --source <材料> --project <项目> --strict`，只提供实际存在的参数；
4. 只有只读或幂等步骤、原因明确且修复已完成时，才自动重试一次；写库、迁移、恢复、覆盖和打包失败不得盲目循环；
5. 可选联网步骤超时时，不阻断离线核心生成。记录未完成项；只有用户已授权且调用幂等时才重试一次。

不得把“重新运行全部流程”作为默认修复。优先从诊断报告中的 `recommended_resume_point` 或最近通过阶段继续。

## 16. 用户可用最短触发语

用户不需要复制长工程规范。以下短句应进入完整生成流程：

> 根据这份报表和附件生成对应的完整本地部署业务系统 ZIP。

如果用户说“做成和这个 V1.5.11 一样的完整局域网部署包”，自动进入 `portable_full`，不得要求用户再写工程细节。

如果用户只说“把这个 Excel 做成系统”“根据这些文件做个本地系统”，也按同样流程执行；重要规则证据不足时显式保留待确认项，而不是降低为静态原型。

## 17. 参考文件路由

| 当前需要 | 读取 |
| --- | --- |
| 第一次使用、脚本单独用法、错误码、FAQ、常见错误 | `references/usage-and-troubleshooting.md` |
| 全量输入追溯、格式解析、数据质量 | `references/file-mapping-and-data-quality.md` |
| 业务类型识别与组合域 | `references/business-routing.md` |
| 能源、点工、运营记录的领域边界 | 对应 `references/domain-profile-*.md`，只加载命中的业务域 |
| 通用工程模式与骨架边界 | `references/proven-system-patterns.md`、`references/scaffold-contract.md` |
| 本地/局域网交付 | `references/local-deployment-contract.md` |
| `portable_full` | `references/portable-full-contract.md` |
| 安全、离线和国内兼容 | `references/security-and-domestic-compatibility.md` |
| 最终验收 | `references/acceptance-checklist.md` |
## 18. 能力声明与验证门禁

技能对外描述必须区分“设计支持”“脚本检查通过”和“目标机实测通过”，禁止把设计目标写成已经验证的事实。

### 14.1 三档声明

| 声明 | 允许条件 | 对用户的表述 |
|---|---|---|
| 设计支持 | SKILL/脚本/模板已经覆盖该能力 | “支持生成/包含相关能力” |
| 本地验收通过 | 对应自动验收脚本通过 | “已通过本地验收” |
| 目标机实测通过 | 在目标 Windows 机器实际启动、操作、断网/局域网验证 | “已在目标机实测通过” |

尤其是“免 Python”“完全离线”“局域网多人”“EXE 解压即用”“不会数据丢失”等强声明，必须有对应证据后才能使用。

### 14.2 交付前最低证据

最终 ZIP 至少应能追溯：输入资料盘点、业务规格、测试结果、验收结果、交付状态和文件清单。缺少实际测试时，在 `TEST_REPORT.md` 或交付说明中明确标记“未实测”，不要用“已验证”“保证”等词替代。

### 14.3 用户可见的失败信息

错误信息必须同时回答：**哪里出错、为什么、用户/执行者现在做什么、修复后从哪里继续**。优先使用 `PBxxx` 错误码和 `cause/action/resume_point`，不要把 Python traceback 直接作为主要说明。

## 19. 最小可复现示例

完整示例与常见问题集中放在 `references/usage-and-troubleshooting.md`。每次需要示例时优先引用其中的“示例 A/B/C”。示例只用于说明调用方式，不得当作业务规则或验收结果。

