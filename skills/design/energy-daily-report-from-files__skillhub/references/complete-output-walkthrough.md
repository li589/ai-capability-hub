# 完整输出效果示例

本页展示“能源日报 + 表计 + 异常整改”完成后用户实际会看到什么。所有名称和数值只用于说明交付形态，真实项目必须来自用户输入或明确标记为 demo。

## 1. 登录与首次使用

```text
系统名称：华东工厂能源日报管理平台
登录提示：首次登录必须修改临时密码
今日待办：待提交日报 2、待处理异常 4
数据范围：华东工厂 / 动力车间
```

角色和数据范围由真实业务蓝图决定。用户明确不需要多人审批时，不应为了固定模板强加“管理员审批/退回”。

## 2. 首页管理看板

```text
今日用电          今日用水          能源成本          未关闭异常
128,480 kWh       3,260 t           86,420 元         4 项

趋势：最近 30 天消耗、单耗、成本和目标偏差
数据状态：截至 2026-08-06 08:00；接口未配置，数据来自已确认导入批次
```

看板和导出必须调用同一后端口径；零分母显示“—”，不能输出虚假的 0% 或 100%。

## 3. 能源日报主流程

流程按真实用户要求配置。例如：

```text
草稿 → 已提交 → 已确认
```

或在确实需要审批时：

```text
草稿 → 已提交 → 能源主管审核 → 已审核
                    └→ 退回修改
```

系统记录操作者、时间、版本和修改前后值；不能只在前端改状态。

## 4. 独立 PY 能源日报（按需附加）

只有用户明确要求独立桌面版时，最终 ZIP 才附带 `standalone/energy_daily_report.py`、运行说明、自检和桌面 EXE 构建源码。它必须是完整本地程序，但不能替代默认 Web/LAN 主系统。

## 5. 历史导入与错误处理

```text
批次：IMPORT-20260806-01
来源：7月能源日报与表计.xlsx
文件 SHA-256：...
读取：2,148 行
成功：2,136 行
拒绝：12 行
重复跳过：38 行
待确认：3 项
```

逐行错误报告包含工作表、行号、原值、字段、错误码、中文原因和解决方法。修正后按幂等策略重导，不重复写入成功行。

## 6. 跨模块闭环

```text
日报 ED-20260806-003
  └─ 能耗异常 EA-20260806-007
       ├─ 能源类型：电
       ├─ 实际单耗：来自真实计算
       ├─ 目标单耗：来自已确认目标版本
       ├─ 责任部门：动力车间
       └─ 可关联设备点检/整改任务
```

异常关闭前应有原因、措施和验证证据；维修完成不自动等于能耗异常关闭。

## 7. 导出与追溯

导出文件包含系统名称、组织范围、筛选条件、生成时间、规则版本、状态和数据来源。文本字段做公式注入防护，并通过程序回读验证。

## 8. 备份恢复

完整 Web 系统包含 `backup_restore.py`：

- 备份使用 SQLite backup API；
- 备份后执行完整性校验；
- 恢复前要求停服确认；
- 覆盖前保留当前数据库回滚副本。

## 9. 构建恢复

```text
[需处理] 项目需要修复后继续
- 构建进度：71%（5/7 阶段）
- 建议恢复点：TESTED
- 下一步：运行完整自动测试并生成真实验收证据
- 数据保护：诊断只读；保留已完成产物和导入批次
- [TEST_FAILURE] 必需验收用例失败
```

普通用户先运行 `python scripts/quick_check.py .`，需要恢复点时运行 `python scripts/diagnose_and_resume.py .`。

## 10. 最终 ZIP 导航

```text
系统根目录/
├─ 00_请先看_交付导航.md
├─ DELIVERY_STATUS.json
├─ 一键启动_Windows.bat
├─ 一键停止_Windows.bat
├─ 01_服务端_完整程序/
│  ├─ server.py / backend_core.py
│  ├─ energy_excel_import.py
│  ├─ backup_restore.py
│  ├─ launcher.py / stop_server.py
│  ├─ exe_entry.py / build_exe_windows.py / *.spec
│  ├─ templates/ / static/
│  └─ data/
├─ 02_Windows填写客户端/
├─ 03_macOS填写客户端/
├─ PY_SOURCE_MANIFEST.json
└─ FILES_SHA256.txt
```

如果用户明确要求独立桌面版，才额外出现：

```text
standalone/
├─ energy_daily_report.py
├─ README_STANDALONE.md
├─ requirements_standalone.txt
├─ build_exe_windows.py
└─ standalone-manifest.json
```

## 11. EXE 状态示例

```text
exe_build_source_included: true
built_exe_included: false
windows_exe_runtime_verified: false
```

这表示“已提供 EXE 构建源码”，不表示“已有 EXE”，更不表示“Windows 真机运行验证通过”。

## 12. 无真实文件的原型状态示例

```text
mode: prototype_from_description
business_file_mapping: not_run
sample_data: demo_only
production_acceptance: not_run
```

原型可以帮助评审流程和界面，但不能展示为真实历史趋势或生产验收结果。

## 13. 最终交付摘要

```text
系统：华东工厂能源日报管理平台
模式：完整 Web/LAN
场景：能源日报 + 表计管理 + 能耗异常整改
有效输入：4 个；导入成功 2,136 条；拒绝 12 条；待确认 3 项
接口：未配置（未伪装实时数据）
EXE：构建源码已提供；二进制和真机验证按实际记录
恢复：PACKAGED，独立解包复测通过
交付：energy-daily-report-system.zip
SHA-256：<真实计算值>
```
