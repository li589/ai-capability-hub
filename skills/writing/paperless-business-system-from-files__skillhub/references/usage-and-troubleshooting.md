# 使用、脚本示例与排错中心

> 想少记命令：优先使用 `python scripts/run_skill.py`。实际案例与能力证据标准见 `references/quickstart-and-evidence.md`。

本文件集中回答“怎么触发、脚本怎么单独运行、出错怎么修、哪些做法不要用”。在 ChatGPT/Codex 中，命令由执行技能的智能体运行；用户通常只需上传材料并说明目标。

## 目录

- 零命令使用入口
- 执行者与用户的分工
- 三条完整流程
- 脚本索引与独立示例
- 错误说明格式
- 错误码与恢复动作
- 安全重试规则
- 常见问题
- 反模式清单

## 零命令使用入口

用户可以直接说：

> 根据这些 Excel 和制度附件，生成一个可在 Windows 本地运行的中文业务系统 ZIP。

> 把这个已有系统和新报表合并升级，保留原数据库、账号权限和历史记录。

> 做成类似 V1.5.11 的完整局域网部署包，包含服务端和 Windows 填写客户端。

执行者不得要求用户先学习 Python、进入命令行或拼接参数。用户明确要求“告诉我如何在自己电脑运行”时，才把本文件中的命令转换成其操作系统可直接复制的步骤。

## 执行者与用户的分工

| 事项 | 默认负责人 |
| --- | --- |
| 读取附件、只读盘点、识别业务类型 | 执行者 |
| 运行初始化、诊断、验收、打包命令 | 执行者 |
| 从文件中核对字段、公式和流程证据 | 执行者 |
| 决定没有证据且会影响金额、工时、审批、权限或历史数据的规则 | 用户 |
| 在目标 Windows 电脑完成真实 EXE/断网/局域网验收 | 用户或用户授权的目标机操作者 |
| 解释限制、错误和恢复点 | 执行者 |

向用户汇报时先说结论，再列“已确认、待确认、阻断、下一步”。不要直接粘贴整段终端输出。

## 三条完整流程

以下命令用于执行者或本地维护人员。路径含空格或中文时始终加引号；输出目录放在输入目录之外。

### 流程一：普通本地系统

```bash
python scripts/bootstrap_generation.py "<材料目录或文件>" --output "<工作目录>"
python scripts/generate_business_system.py --spec "<工作目录>/system-spec.json" --output "<项目目录>"
python scripts/validate_local_bundle.py "<项目目录>" --strict
python scripts/finalize_delivery.py "<项目目录>" --output "<交付ZIP>"
```

`generate_business_system.py` 会自动物化能从证据稳定确定的业务结构与通用能力；审批、正式唯一键、字段级权限、统计口径等仍按证据门槛补充。骨架本身仍不是完成证据。

### 流程二：portable_full 局域网完整包

```bash
python scripts/bootstrap_generation.py "<材料>" --output "<工作目录>" --deployment-mode portable_full --network-mode lan
python scripts/generate_business_system.py --spec "<工作目录>/system-spec.json" --output "<项目目录>"
python scripts/validate_local_bundle.py "<项目目录>" --strict
python scripts/validate_portable_full.py "<项目目录>" --strict
python scripts/finalize_delivery.py "<项目目录>" --output "<交付ZIP>"
```

如果用户只要单机完整包，使用 `portable_full` 但不要加 `--network-mode lan`。

### 流程三：升级已有系统

1. 先对源码、数据库、迁移、账号权限、客户端、启停脚本和历史版本做只读盘点。
2. 用新附件补充 `system-spec.json`，记录旧→新字段映射和冲突。
3. 备份数据库后执行幂等迁移；不使用 `--force` 覆盖已有项目。
4. 核对升级前后行数、金额/数量合计、状态分布、孤儿记录和随机样本。
5. 运行对应验收与打包命令。

## 脚本索引与独立示例

| 脚本 | 何时使用 | 主要结果 |
| --- | --- | --- |
| `profile_inputs.py` | 只读盘点所有输入和文件级问题 | `input-profile.json` |
| `extract_business_model.py` | 深度提取对象、字段、公式、候选关系和证据 | `business-model.json`、业务模型报告 |
| `detect_business_profile.py` | 结合深度模型解释业务类型候选 | `business-profile.json`、识别报告 |
| `assess_input_completeness.py` | 评估 A/B/C/D 资料完整度 | 完整度报告和 JSON |
| `bootstrap_generation.py` | 一次完成初始化三项分析并生成规格入口 | 初始化工作区 |
| `create_project_scaffold.py` | 只需要工程底座时使用 | 本地或 `portable_full` 工程骨架 |
| `generate_business_system.py` | 根据 system-spec 自动生成业务系统 | 骨架 + 业务迁移 + CRUD/查询/导入导出/RBAC/审计/安全公式 |
| `diagnose.py` | 汇总技能、材料和项目阻断项 | 中文诊断与可选 JSON 报告 |
| `validate_local_bundle.py` | 检查本地交付结构与安全启停 | 本地部署验收结果 |
| `validate_portable_full.py` | 检查完整部署包装 | `portable_full` 验收结果 |
| `validate_delivery.py` | 检查 `delivery-manifest.json`、哈希与安全项 | 交付清单验收结果 |
| `generate_value_report.py` | 有真实前后耗时后生成价值报告 | `VALUE_REPORT.md` |
| `finalize_delivery.py` | 测试和验收通过后最终打包 | 二次解包验证后的 ZIP |
| `check_version.py` | 发布或诊断时核对技能基线 | 版本一致性结果 |

`portable_full_support.py` 是 `create_project_scaffold.py` 的内部模块，不单独运行。

### 只盘点材料

```bash
python scripts/profile_inputs.py "<材料>" --output "<工作目录>/input-profile.json" --strict
```

移除 `--strict` 时，个别文件失败仍会生成部分成功报告；`--strict` 用于需要把任一文件错误作为非零返回的验收场景。

### 只提取深度业务模型

```bash
python scripts/extract_business_model.py "<材料>" --output "<工作目录>/business-model.json" --report "<工作目录>/BUSINESS_MODEL_REPORT.md"
```

该结果是 `system-spec.business_objects` 的主要结构来源。候选唯一键与候选关系不会自动当成正式约束。

### 只识别业务类型

```bash
python scripts/detect_business_profile.py "<材料>" --output "<工作目录>/business-profile.json" --report "<工作目录>/BUSINESS_RECOGNITION_REPORT.md"
```

识别结果只负责路由，不能覆盖用户要求或附件中的业务事实。

### 只评估资料完整度

```bash
python scripts/assess_input_completeness.py "<材料>" --profile production --output "<工作目录>/INPUT_COMPLETENESS_REPORT.md" --json-output "<工作目录>/input-completeness.json"
```

`--profile` 可使用技能支持的业务类型；不确定时优先运行 `bootstrap_generation.py` 自动识别。

### 初始化时明确业务和系统名

```bash
python scripts/bootstrap_generation.py "<材料>" --output "<工作目录>" --profile quality --system-name "质量检验系统"
```

### 自动生成业务系统

```bash
python scripts/generate_business_system.py --spec "<工作目录>/system-spec.json" --output "<项目目录>"
```

它会自动生成 SQLite 业务表、CRUD、搜索分页、导入预览、Excel 导出、对象级 RBAC、审计和可安全执行公式，并生成 `AUTO_GENERATION_REPORT.md`。

### 只生成骨架

```bash
python scripts/create_project_scaffold.py --spec "<工作目录>/system-spec.json" --output "<项目目录>"
```

只有明确只需要工程底座时才用。输出目录已存在时先核对内容和备份；只有确认可覆盖时才加 `--force`。

### 一键诊断

```bash
python scripts/diagnose.py --source "<材料>" --project "<项目目录>" --strict --json-report "<工作目录>/diagnose.json"
```

只有材料时使用 `--source`，只有项目时使用 `--project`；不要传不存在的占位路径。

### 验收交付清单

```bash
python scripts/validate_delivery.py "<项目目录>" --strict --json-report "<工作目录>/delivery-validation.json"
```

### 生成价值报告

```bash
python scripts/generate_value_report.py --spec "<项目目录>/system-spec.json" --status "<项目目录>/DELIVERY_STATUS.json" --metrics "<真实测量数据.json>" --output "<项目目录>/VALUE_REPORT.md"
```

没有真实 `before_minutes`、`after_minutes` 和 `sample_count` 时，报告必须标记待测，不得估算效率提升。

## 错误说明格式

每次失败都用以下四项，不要求用户猜错误码含义：

```text
状态：未完成“输入文件盘点”。
原因/位置：[PB001] 路径 D:\业务资料 不存在。
现在怎么处理：确认盘符和文件夹名称；路径含空格时加双引号。
恢复点：修正路径后只重新运行“输入文件盘点”，无需重做已通过步骤。
```

脚本已提供更细的 `cause`、`impact`、`action`、`resume_point` 时，优先使用这些字段，不改写成含糊的“执行失败”。

## 错误码与恢复动作

| 错误码 | 常见原因 | 立即动作 | 恢复点 |
| --- | --- | --- | --- |
| `PB001` | 输入/项目路径不存在、参数值错误、输出位于输入目录内 | 核对实际路径与参数；把输出改到输入目录之外 | 输入清单或当前命令 |
| `PB002` | 格式不在支持清单 | 另存为标准 XLSX/CSV/DOCX/PDF/JSON/TXT，或明确排除 | 输入清单 |
| `PB003` | 文件损坏、加密、编码异常、Office/ZIP 结构异常或不安全路径 | 用 WPS/Office 另存副本、修复编码、移除越界成员；保留原件 | 文件解析 |
| `PB101` | 目标 Windows 启动时未找到 Python、EXE 或便携运行时 | 按交付声明补齐对应运行时；不要声称免 Python | 安装验证 |
| `PB201` | Python/离线依赖不满足，或严格验收发现外部依赖 | 使用匹配运行时和本地依赖；记录未满足的离线条件 | 安装验证 |
| `PB301` | 密钥、危险路径、弱密码哈希或其他安全阻断 | 移除/轮换凭证并修复配置，再重跑安全验收 | 安全验收 |
| `PB401` | 测试、通用交付验收、打包或步骤超时失败 | 修复输出中的首个阻断项；必要时运行 `diagnose.py` | 对应测试/验收步骤 |
| `PB451` | `portable_full` 规格或目录、客户端、运行时证据不完整 | 对照 `portable-full-contract.md` 补齐后仅重跑专项验收 | portable_full 验收 |
| `PB501` | 技能基线版本来源不一致 | 同步技能说明与脚手架版本，再运行 `check_version.py` | 发布检查 |
| `PB601`–`PB604` | 规格不存在/无法解析、输出目录冲突、模板还原失败 | 检查 `system-spec.json`、目标目录和骨架模板；不要交付半成品 | 工程骨架生成 |
| `PB701`–`PB703` | 自动生成阶段规格不存在/无法解析/没有可生成业务对象 | 先运行 `analyze` 生成深度业务模型，或补充 `system-spec.business_objects` | 自动生成 |
| `PB999` | 未分类异常 | 保留最小脱敏样例并运行诊断；不要循环重试 | 最近通过步骤 |

## 安全重试规则

只在同时满足以下条件时自动重试一次：

- 当前步骤只读或幂等；
- 原因已经定位并完成修复；
- 重试不会覆盖数据库、迁移、备份、用户项目或已生成 ZIP；
- 输入和目标路径已经重新核对。

以下情况不要自动重试：写库/迁移/恢复、`--force` 覆盖、未知异常、磁盘空间不足、权限拒绝、安全检查失败。先停止并给出恢复动作。

核心流程默认不联网。可选联网步骤超时后，先继续离线核心并记录限制；只有用户已授权、调用幂等且没有产生部分写入时才重试一次。

## 常见问题

### 1. 我完全不懂命令行，也能用吗？

能。在 ChatGPT/Codex 中只需上传材料并描述目标，执行者负责运行脚本。命令示例是给执行者和需要自行维护的技术人员使用的。

### 2. 会修改原始 Excel、Word 或数据库吗？

输入材料默认只读，转换使用副本。已有数据库升级前必须备份，迁移失败要能回滚。

### 3. WPS 文件能用吗？

标准 XLSX、DOCX、CSV、PDF 可以处理。WPS 专有或旧式格式先另存为标准格式，关键行数、金额、日期和公式结果要复核。

### 4. 文件有密码或 PDF 是扫描件怎么办？

不破解密码。请提供已解密副本。扫描件 OCR 结果只作为候选，关键编号、金额、数量和审批结论必须人工复核。

### 5. 能保证完全离线、免 Python、解压即用吗？

只有包内包含匹配的 EXE 或便携运行时、全部依赖，并在目标 Windows 真机断网验证后才能这样表述。只有源码和 `requirements.txt` 时不能作该承诺。

### 6. 为什么有些规则会被列为待确认？

因为金额、工时、审批、权限、唯一键和历史口径不能靠经验猜。缺少可靠证据时，保留待确认比生成错误规则更安全。

### 7. 局域网模式会自动开放防火墙吗？

不会静默修改。开放端口必须由用户主动确认，并只针对本项目当前端口。

### 8. 端口冲突、启动闪退或数据库异常怎么办？

优先运行项目内的一键诊断；技能开发阶段使用 `scripts/diagnose.py`。按首个阻断项修复，从报告给出的恢复点继续。

### 9. 验收脚本通过是否等于第三方安全认证？

不等于。它只证明脚本覆盖范围内的本地静态检查和测试结果。第三方结论必须有对应版本、范围、日期和报告。

### 10. 什么时候才能打最终 ZIP？

真实测试已经执行、`DELIVERY_STATUS.json` 与 `TEST_REPORT.md` 一致、对应严格验收通过后，才运行 `finalize_delivery.py`。

## 反模式清单

- 不要把命令行操作转交给未要求自行部署的用户。
- 不要把输出目录放在输入目录内部，避免生成文件被误当成业务证据。
- 不要把骨架页面、静态 HTML 或截图当成业务系统完成证据。
- 不要凭文件名或单个关键词确定业务类型。
- 不要无证据补齐公式、考勤周期、审批链、权限或主键。
- 不要默认启用局域网、自动开放防火墙或写死 `192.168.*` 地址。
- 不要用 `--force`、全局 `taskkill` 或反复重跑掩盖错误。
- 不要把“含 EXE 构建源码”表述为“已提供并验证 EXE”。
- 不要把“核心代码不联网”表述为“首次安装完全离线”。
- 不要在失败后从头覆盖项目；从最近通过步骤或 `recommended_resume_point` 继续。

## 示例 A：把 Excel 做成本地系统

**用户说：**

> “把 `点工记录.xlsx` 做成 Windows 本地系统。保留原来的填写习惯，支持录入、查询、修改、统计、Excel 导入导出，完成后给我完整 ZIP。”

**执行路径：**

1. 运行初始化并识别业务类型；
2. 检查字段、公式、人员/工时规则是否有证据；
3. 生成 `system-spec.json`；
4. 生成业务系统并实现导入、查询、统计、权限、备份等能力；
5. 运行诊断、严格验收和打包；
6. 向用户报告“已确认/待确认/未实测”的区别。

**不要做：** 没有工时规则证据时自行猜一个工时公式。

## 示例 B：资料不完整时怎么处理

**用户说：**

> “这些表先帮我做成系统，工时计算规则我暂时没有。”

如果工时规则会影响正式结果，可以先完成字段和页面等确定部分，但把工时规则写入 `open_questions` / `ASSUMPTIONS.md`，不得把猜测公式写入正式业务规则。必要时只询问影响结果的最少问题。

## 示例 C：用户要求跨平台

**用户说：**

> “能不能直接生成 iPhone 原生 APP？”

当前技能默认底座是 Python + Flask/Jinja2 + SQLite，第一目标为 Windows 10/11。本技能不能直接把该需求描述成“已支持 iPhone 原生 APP”。应先说明这是超出当前脚手架边界的技术栈需求，并根据用户是否愿意调整目标决定后续方案。

## 示例 D：用户要求完全离线、免 Python

只有当交付包实际带入匹配 EXE 或便携运行时、依赖完整，并完成目标 Windows 机器断网验证时，才能说“免 Python/完全离线”。仅有 Python 源码、`requirements.txt` 或开发机测试通过，不足以作该声明。

## 问题定位速查

| 我遇到的问题 | 先看哪里 | 推荐动作 |
|---|---|---|
| 不知道该怎么说才能触发 | 本文件“零命令使用入口” | 直接上传资料 + 说“做成系统” |
| 不知道生成哪种模式 | `SKILL.md` 第 1 节“快速路由” | 明确本地 / 局域网 / `portable_full` |
| 不知道为什么某条规则没生成 | `BUSINESS_RECOGNITION_REPORT.md`、`ASSUMPTIONS.md` | 查证据和待确认项 |
| 系统生成失败 | `diagnose.py` + `PBxxx` | 修复首个阻断项，从恢复点继续 |
| 说“完全离线”被阻止 | `PB101/PB201`、`portable-full-contract.md` | 补齐运行时和离线依赖并实测 |
| 说“EXE 即用”被阻止 | `PB101` | 检查 EXE/便携运行时证据 |
| 局域网无法访问 | `PB451` 或项目诊断 | 检查绑定地址、端口和主动确认的防火墙规则 |
| 最终 ZIP 不允许生成 | `TEST_REPORT.md`、`DELIVERY_STATUS.json` | 先完成真实测试和严格验收 |

## 文档阅读顺序（非技术用户）

不需要通读所有文档。按任务选择：

1. **第一次使用：** 先看本文件“零命令使用入口” + “三条完整流程”；
2. **遇到资料问题：** 看 `file-mapping-and-data-quality.md`；
3. **遇到规则不确定：** 看 `business-routing.md`、对应 Profile 和 `system-spec` 规则；
4. **遇到部署问题：** 看 `local-deployment-contract.md`；
5. **要求完整部署包：** 看 `portable-full-contract.md`；
6. **遇到报错：** 先按 `PBxxx` 表定位，再看“错误说明格式”和“安全重试规则”。

## 反模式补充

- **把“脚本通过”写成“目标机已实测”：** 禁止。两者必须分开。
- **把“设计支持”写成“100%保证”：** 禁止。尤其是跨平台、免 Python、完全离线和数据不丢失。
- **没有业务证据却补公式：** 禁止。应进入待确认项。
- **为了提高一次生成成功率而跳过资料完整度门禁：** 禁止。
- **遇到错误反复全流程重跑：** 禁止。优先从最近恢复点继续。
- **为了让文档更完整而让用户先阅读全部 references：** 不推荐。按任务按需读取。

## 2.7.0：真实运行测试与升级

### 真实运行 E2E

```bash
python scripts/run_skill.py test --project <项目目录>
```

- `PB802`：当前 Python 没有 Flask/openpyxl。先按项目 `requirements.txt` 准备环境，或 `--python <虚拟环境Python>`。
- 测试总是在隔离副本执行，不应改写原项目业务数据库。
- 测试通过后再运行 `validate --strict`。

### 安全升级

```bash
python scripts/run_skill.py upgrade --project <旧项目> --spec <新规格> --output <升级副本>
```

- `PB904`：存在删除字段/对象或字段类型变化，默认阻断；先查看 `UPGRADE_DIFF_REPORT.md`。
- 仅想看差异：加 `--plan-only`。
- 升级完成后必须重新执行 E2E，旧测试证据不自动继承。
