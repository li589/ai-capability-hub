# 通用项目骨架契约

`assets/scaffold/universal-local-app/` 是工程底座，不是固定业务模板。

## 可直接复用

- 配置与 data 目录定位；
- SQLite 连接、WAL、外键；
- schema_migrations；
- 密码哈希、登录会话、基础 CSRF 防护；
- RBAC 与用户级权限覆盖；
- 审计日志；
- 健康检查；
- 备份/恢复；
- 安全启停与运行状态；
- Windows 启停/诊断/验收；
- EXE 构建入口；
- 基础模板、CSS、Excel I/O 公共函数。

## 必须由当前业务生成

2.6.0 起，以下“可由证据稳定推导”的部分优先交给 `generate_business_system.py` 自动物化；无法从证据确认的高风险规则仍保持待确认。

- 业务表和字段；
- 计算公式；
- 唯一键和防重复导入键；
- 审批状态机；
- 数据范围；
- 报表和看板；
- Excel 模板具体版式；
- 业务迁移；
- 业务测试。

## 生成顺序

推荐主链：

1. 形成 `system-spec`；
2. 运行 `generate_business_system.py`（内部先调用通用骨架）；
3. 自动生成业务表/迁移、CRUD、搜索分页、导入预览、Excel 导出、RBAC、审计和安全公式；
4. 对审批链、正式唯一键、字段级权限、统计口径等证据不足项继续人工确认/实现；
5. 添加业务回归测试；
6. 执行完整交付校验。

只有明确只需要工程底座时才单独运行 `create_project_scaffold.py`。

禁止把骨架中的示例页面当作“系统已完成”的证据。

## 平台安全模板层（2.5.1）

技能包上传包中，Windows BAT 和 PyInstaller spec 不以真实扩展名存放，而位于：

`assets/scaffold/universal-local-app/_platform_templates/`

`template-map.json` 定义安全模板文件到最终工程文件名的映射。`create_project_scaffold.py` 必须在复制骨架后完成还原并删除 `_platform_templates`，使最终工程直接获得 `start_windows.bat`、`stop_windows.bat`、诊断/验收 BAT 和 `app.spec`。模板还原失败属于阻断错误，不得继续交付半成品。


## ASCII 技能骨架文件名

技能包内部说明文件使用 `README_RUN.md`、`README_EXE_BUILD.md`、`README_SCAFFOLD.md`，避免 ZIP/上传链路造成中文文件名编码损坏。生成最终业务系统时，`create_project_scaffold.py` 必须还原为 `README_运行说明.md`、`README_EXE打包说明.md`、`README_工程骨架说明.md`。

## portable_full 骨架布局（2.5.1）

`create_project_scaffold.py` 读取 `system-spec.json`。当 `system.deployment_mode=portable_full` 或 `portable_full.enabled=true` 时：

- 通用 Web 工程写入 `01_服务端_完整程序/`；
- 根目录动态生成安全的一键启停包装；
- 自动生成 Windows 填写客户端、服务器地址设置/测试工具、参考资料区、电子模板区和版本区；
- macOS 客户端按 `portable_full.macos_client` 条件生成；
- 生成的客户端/包装文件属于本次业务系统输出，不属于技能 ZIP 固定成品。

业务代码仍必须写入 `01_服务端_完整程序/business/` 等实际服务端位置。


## 证据驱动运行时（2.6.0）

通用骨架内置 `business/runtime_generated.py`，但没有 `generated_schema.json` 时不会凭空创建业务对象。`generate_business_system.py` 根据 `system-spec.business_objects` 生成：

- `business/generated_schema.json`：运行时业务结构；
- `business/generated_migrations.py`：每个业务对象对应的 SQLite 表；
- 对象级权限：`view/create/edit/delete/import/export`；
- 服务器端安全公式计算，只执行可转换的白名单表达式；
- `AUTO_GENERATION_REPORT.md`、Python 源码清单和文件哈希。

候选唯一键只用于提示，不自动创建 `UNIQUE`；必须写入 `confirmed_unique_keys` 才会物化为正式约束。
