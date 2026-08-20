# 数据知识库（空骨架）

本目录为**空骨架**，不含任何客户库数据。

安装本技能后，首次使用需运行：
1. `scripts/setup_config.py --fill` 填写 MySQL 连接（只读账号）
2. `scripts/sync_schema.py --apply` 从客户库生成 schema / 枚举 / 白名单

生成后本目录将包含：schema.json（表结构）、allowed_tables.json（白名单）、
enum_dict.json（枚举字典）、asset_index.json（查询路由）、schema_pending.json（待确认字段）。
