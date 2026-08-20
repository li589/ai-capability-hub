# Python 能源日报系统生成指南

## 推荐结构

```text
app.py
src/
  auth/ organization/ records/ workflows/ approvals/
  imports/ exports/ dashboards/ permissions/ database/ common/
config/business-system-blueprint.json
data/paperless_business.db
mapping/ tests/ templates/ static/ scripts/
standalone/   （仅用户明确要求桌面版时附加）
```

## 实现要求

1. 从能源业务蓝图生成迁移、实体仓储、服务、校验、页面和 API，不把用户未确认的单位、倍率、价格或目标硬编码为事实。
2. 认证使用安全密码哈希、随机临时管理员密码、首次改密、登录限速和安全 Cookie。
3. 后端对每次读写执行角色、动作和数据范围校验；越权返回 403。
4. 更新时比较 `version`，冲突返回 409 并保留用户输入。
5. 所有状态变化通过工作流或状态服务，记录前后状态、操作者、时间、理由和规则版本；审批层级按真实业务蓝图，不强制固定多人审批。
6. 导入先进入批次与暂存校验；使用文件指纹和业务主键幂等；错误逐行报告。
7. 导出附来源、过滤条件、生成时间、规则版本和审核/状态信息。
8. Waitress 正式运行，禁止 debug；启动前执行配置、数据库、依赖和端口自检。
9. 主 Web 系统必须有成对的一键启动/停止、SQLite 安全备份恢复和 EXE 构建源码。
10. 只有用户明确要求独立桌面版时，才运行 `scripts/ensure_energy_daily_standalone.py <项目目录> --overwrite`，并执行 `python standalone/energy_daily_report.py --self-test`。
11. 按 `intellectual-property-protection.md` 实例化版权、专有使用许可、第三方组件声明和机器可读权利元数据；清除全部占位符，并由 `FILES_SHA256.txt` 覆盖交付文件。
12. 没有真实业务文件时只允许生成明确标记的 prototype/demo，不得伪造真实历史、目标、价格和趋势。

## 完成判据

完整 Web/LAN 交付不能只是静态 HTML、空壳 CRUD、启动壳或只有 EXE 没有源码。至少实现一个真实能源日报主流程、真实或明确待确认的业务规则、权限隔离、审计、导入、导出、看板、备份恢复、成对启停和自动测试。

独立桌面版是按需附加能力；如果用户没有要求桌面版，缺少 `standalone/` 不应导致完整 Web/LAN 交付失败。
