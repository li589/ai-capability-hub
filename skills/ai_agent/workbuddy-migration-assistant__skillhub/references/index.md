# references 索引

按需加载的模块化参考。SKILL.md 只做入口分派与关键约束，以下文件在对应阶段才读取。

| 文件 | 何时加载 | 内容 |
|------|----------|------|
| `asset_inventory.md` | 资产扫描/导出时 | 迁移资产白名单、DB 表合并策略（`<!-- machine:KEY -->` 数据驱动） |
| `workspace_excludes.md` | 产物包打包时 | 产物包默认排除规则（node_modules/.git/dist 等） |
| `commands.md` | 构造 export/import/info 命令时 | 三命令全部参数与说明 |
| `flows.md` | 导出/导入/检视执行时 | 导出流程、导入流程、Agent 调用分派与步骤 0 资产扫描 |
| `conflict-pathmap.md` | 跨机器路径重写、冲突处理时 | 冲突处理规则、冲突报告格式、路径映射逻辑、产物包 MANIFEST 格式 |
| `known-issues.md` | 排查故障、准备回滚时 | 已知问题、回滚步骤、FAQ、版本演进说明 |

## 读取规则

- **SKILL.md**（L1）：始终加载，入口分派 + 关键约束 + 资产全景
- **index.md**（L2）：需要细节时按上表定位
- **各 references 文件**（L3）：命中对应阶段才加载
