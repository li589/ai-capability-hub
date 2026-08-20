# 错误码与恢复手册

> **看不懂错误码？** 运行 `python scripts/diagnose_and_resume.py .`，会给出纯中文解释和操作步骤。

## 用户先做什么

在生成项目目录运行：

```text
python scripts/diagnose_and_resume.py .
```

输出只包含中文结论、构建进度、建议恢复点、下一步和数据保护说明。诊断只读，不删除数据库、构建状态或已完成导入批次。

如果错误发生在“还没开始生成”阶段，先执行 `python scripts/ensure_full_lan_energy_system.py --check-only` 排除内置基线损坏。

## 常见错误码速查表

### 文件问题

| 错误码 | 通俗解释 | 怎么办 |
|---|---|---|
| `ZIP_UNSAFE_PATH` | 压缩包里有危险路径（如 `../`） | 删除可疑文件后重新打包 |
| `ZIP_MEMBER_CORRUPT` | 压缩包里的文件损坏了 | 替换损坏的文件后重新打包 |
| `OFFICE_CORRUPT` | Excel 或 Word 文件损坏 | 重新导出或从原始来源重新获取 |
| `TEXT_ENCODING_UNSUPPORTED` | 文本文件编码不支持 | 用记事本另存为 UTF-8 编码 |
| `DELIMITED_EMPTY` | CSV/TSV 文件为空或没有表头 | 检查文件内容，确保有表头和数据 |
| `LAN_REFERENCE_MISSING` | 技能包缺少内置完整局域网基线 | 重新校验技能包并重新解压完整 ZIP，不要继续生成半成品 |
| `LAN_REFERENCE_CRC_FAILED` | 内置完整局域网基线损坏 | 重新获取完整技能包并核对 `FILES_SHA256.txt` |
| `LAN_REFERENCE_CORE_MISSING` | 基线缺少服务端/前端/启停/备份等核心文件 | 重新获取完整技能包，禁止用不完整模板继续生成 |
| `LAN_REFERENCE_STAGE_FAILED` | 基线临时展开失败 | 检查磁盘空间/权限后重试；失败前不继续写未验证内容 |

### 网络与依赖问题

| 错误码 | 通俗解释 | 怎么办 |
|---|---|---|
| `OFFLINE_FILE_TEMPORARY` | 离线依赖文件暂时不可读 | 关闭占用文件的软件，检查磁盘后重试 |
| `OFFLINE_DEPENDENCIES_UNAVAILABLE` | 离线模式下依赖不完整 | 在有网络的环境下运行 `prepare_offline_dependencies.py` |
| `DEPENDENCY_INSTALL_FAILED` | 依赖安装失败 | 查看下方详细输出，通常是网络或权限问题 |
| `PORT_IN_USE` | 端口被其他程序占用 | 设置环境变量 `PAPERLESS_PORT=8080` 换端口 |
| `FILE_LOCKED` | 文件被 Excel/WPS 占用 | 关闭占用文件后重试，最多自动重试 2 次 |

### 数据与业务问题

| 错误码 | 通俗解释 | 怎么办 |
|---|---|---|
| `MAPPING_CONFLICT` | 字段映射有冲突 | 检查映射配置，解决冲突后继续 |
| `BLUEPRINT_JSON_INVALID` | 业务蓝图格式错误 | 检查 JSON 格式，修复后重新生成 |
| `DATABASE_INTEGRITY_FAILED` | 数据库损坏 | 从最近备份恢复，故障副本已保留 |
| `TEST_FAILURE` | 测试未通过 | 查看测试报告，修复问题后重新测试 |
| `SECURITY_CHECK_REJECTED` | 安全检查未通过 | 查看安全报告，修复问题后再试 |

### 权限与安全

| 错误码 | 通俗解释 | 怎么办 |
|---|---|---|
| `PYTHON_ADMIN_INSTALL_DENIED` | 需要管理员权限安装 Python | 联系 IT 或使用已安装的 Python |
| `TEMPORARY_IO` | 临时文件读写失败 | 检查磁盘空间和权限，稍后重试 |

## 可自动重试

| 错误码 | 原因 | 自动处理 | 重试用尽后 |
|---|---|---|---|
| `FILE_LOCKED` | 文件被 Excel、WPS 或同步程序占用 | 重新检查后最多重试两次 | 关闭占用程序，从当前阶段继续 |
| `PORT_IN_USE` | 端口临时被占用 | 重新探测候选端口 | 设置 PAPERLESS_PORT |
| `TEMPORARY_IO` | 短暂读写异常 | 最多重试两次 | 检查磁盘空间、目录权限和同步状态 |
| `OFFLINE_FILE_TEMPORARY` | 离线依赖文件暂时不可读 | 关闭占用文件的软件并检查磁盘 | 使用完整离线包后继续 |

## 必须人工修复

| 错误码 | 通俗解释 | 怎么处理 | 恢复点 |
|---|---|---|---|
| `CORRUPT_INPUT` | 输入文件已损坏无法读取 | 从原始来源重新获取完整文件 | ANALYZED |
| `ENCRYPTED_FILE` | PDF 或 Office 文件加密了 | 提供未加密的副本（不要求用户告知密码） | ANALYZED |
| `ZIP_UNSAFE_PATH` | 压缩包里有 `..` 或绝对路径 | 删除危险成员后重新打包 | ANALYZED |
| `ZIP_CRC_FAILED` | 压缩包 CRC 校验失败 | 重新压缩或重新下载源文件 | ANALYZED |
| `ZIP_MEMBER_CORRUPT` | 压缩包内某个文件损坏 | 替换损坏文件后重新压缩 | ANALYZED |
| `ZIP_RATIO_UNSAFE` | 检测到压缩炸弹（超高压缩比） | 重新用正常压缩比打包文件 | ANALYZED |
| `OFFICE_CORRUPT` | Excel 或 Word 文件内部损坏 | 用 Excel/WPS 重新打开后另存为新文件 | ANALYZED |
| `OFFICE_CRC_FAILED` | Office 文件内部成员 CRC 校验失败 | 重新导出电子档 | ANALYZED |
| `OFFICE_STRUCTURE_INVALID` | Office 文件缺少关键结构 | 确认扩展名与实际格式一致 | ANALYZED |
| `EXCEL_NO_SHEETS` | 工作簿没有可识别的工作表 | 重新导出包含数据的工作簿 | ANALYZED |
| `DOCX_EMPTY` | Word 文档没有可识别的正文 | 提供包含文字或表格的文档 | ANALYZED |
| `PDF_STRUCTURE_INVALID` | PDF 文件头或结束标记无效 | 重新导出为有效 PDF | ANALYZED |
| `PDF_ENCRYPTED` | PDF 文件已加密 | 提供可读取的未加密副本 | ANALYZED |
| `INPUT_EMPTY` | 输入文件为空（0 字节） | 提供有内容的文件 | ANALYZED |
| `INPUT_TOO_LARGE` | 单个文件超过 100MB 安全上限 | 拆分文件后分批处理 | ANALYZED |
| `UNSUPPORTED_EXTENSION` | 文件格式不被支持 | 转换为 xlsx/csv/tsv/docx/pdf/txt/md 或 zip | ANALYZED |
| `TEXT_ENCODING_UNSUPPORTED` | 文本编码无法识别 | 用记事本打开后另存为 UTF-8 编码 | ANALYZED |
| `MAPPING_CONFLICT` | 关键字段映射冲突 | 修正字段映射配置后重新导入 | MAPPED |
| `BLUEPRINT_JSON_INVALID` | 业务蓝图 JSON 格式有误 | 检查并修复 JSON 语法后重新生成 | MAPPED |
| `DATABASE_INTEGRITY_FAILED` | 数据库完整性检查失败 | 立即停止写入，从最近备份恢复 | 从最近备份恢复 |
| `TEST_FAILURE` | 自动化测试未通过 | 查看测试报告，修复问题后重新测试 | TESTED |
| `SECURITY_CHECK_REJECTED` | 安全检查未通过，有安全风险 | 按安全报告逐项修复后重新检查 | 按报告修复 |
| `PYTHON_ADMIN_INSTALL_DENIED` | 安装 Python 需要管理员权限 | 联系 IT 管理员或使用已安装的 Python 3.10+ | — |
| `OFFLINE_MANIFEST_VERIFY_FAILED` | 离线依赖包清单与预期不符 | 重新运行 prepare_offline_dependencies.py | — |
| `VALUE_ADDED_WRITE_FAILED` | 增值报告无法写入磁盘 | 检查磁盘空间和目录写入权限 | — |

## 边界情况

- 输入在分析后发生变化：创建新输出目录，从 ANALYZED 重新开始，不复用旧映射。
- 业务蓝图发生变化：创建新蓝图或规则版本，只重新执行受影响阶段，不静默重算历史。
- 导入中断：按文件指纹、业务主键和批次幂等续跑，已成功行不得重复写入。
- 数据库锁持续存在：停止自动重试，提示占用进程和日志位置，不强制终止其他程序。
- 磁盘空间不足：停止写入，不删除旧备份；用户清理空间后从失败阶段继续。
- 用户拒绝管理员授权：不修改数据库，输出 PYTHON_ADMIN_INSTALL_DENIED 和管理员协助步骤。
- 权利文件或哈希被移除：交付校验失败，重新实例化权利文件并生成完整哈希清单。

## 构建恢复与续跑

构建固定为七阶段：`ANALYZED → MAPPED → SCAFFOLDED → IMPLEMENTED → IMPORTED → TESTED → PACKAGED`。

`.build-state.json` 记录输入指纹、业务蓝图 SHA-256、技能版本、规则版本、阶段状态、产物哈希和最近错误。输入或蓝图变化时回到 ANALYZED，不能复用旧导入结果。

自动重试仅允许 `FILE_LOCKED`、`PORT_IN_USE`、`TEMPORARY_IO`、`OFFLINE_FILE_TEMPORARY`，最多两次。损坏文件、映射冲突、蓝图错误、数据库完整性、安全拒绝和测试失败不盲目重试。

每个完成阶段必须记录存在的项目内相对路径；拒绝绝对路径、盘符和 `..`。导入使用批次和业务主键幂等，续跑不能重复提交已完成批次。

### 一键诊断

运行 `python scripts/diagnose_and_resume.py <项目目录>`，以只读方式联合检查启动条件和构建状态，输出：

- 已完成阶段数与百分比
- `resume_from` 和下一步中文动作
- 最近错误的稳定错误码、原因和是否可自动重试
- 已完成且必须保护的产物路径
- 端口、依赖、蓝图和数据库检查结果
- "不删除数据库、不清除构建状态、不重复导入"的数据保护说明

诊断脚本不能自动修复业务主键、金额、权限、审批、数据库损坏或安全拒绝等需要判断的问题。
