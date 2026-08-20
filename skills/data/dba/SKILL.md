---
name: dba
description: DBA工具。支持 MySQL 和 PostgreSQL，支持数据查询、增删改、事务控制、表结构查看、SQL 执行、JSON 输出。触发词：MySQL、PostgreSQL、数据库查询、SQL 执行、查表、数据增删改、查看表结构、EXPLAIN 分析、数据库连接
title: DBA
category: 开发
install_source: official
install_method: download
skill_id: 174d2991-0270-4cc0-b004-95f9c76857df
enabled_at: 1787232683847
version: 1.0.0
name_zh: DBA
---

# DBA

通过 `db_cli.py` 脚本直接执行 SQL，支持 **MySQL** 和 **PostgreSQL** 两种数据库。

## 智能预检查（重要）

**在执行 SQL 前，AI 必须遵循以下预检查流程：**

### 1. 不确定表名时 → 先查表列表

```bash
# MySQL 查看所有表
python3 <SKILL目录>/scripts/db_cli.py "SHOW TABLES;"

# PostgreSQL 查看所有表
python3 <SKILL目录>/scripts/db_cli.py "\dt"
```

### 2. 不确定字段名时 → 先查表结构

```bash
# MySQL 查看表结构
python3 <SKILL目录>/scripts/db_cli.py "DESCRIBE 表名;"

# MySQL 查看完整建表语句
python3 <SKILL目录>/scripts/db_cli.py "SHOW CREATE TABLE 表名;"

# PostgreSQL 查看表结构
python3 <SKILL目录>/scripts/db_cli.py "\d 表名"

# PostgreSQL 查看完整建表语句
python3 <SKILL目录>/scripts/db_cli.py "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '表名';"
```

### 3. 执行流程示例

```bash
# ❌ 错误：直接执行（可能字段名错误）
python3 <SKILL目录>/scripts/db_cli.py "SELECT * FROM wms_inbound_order WHERE order_no = 'IB123';"

# ✅ 正确：先查表结构
python3 <SKILL目录>/scripts/db_cli.py "DESCRIBE wms_inbound_order;"
# 发现字段名是 inbound_no，不是 order_no

# 再执行正确的 SQL
python3 <SKILL目录>/scripts/db_cli.py "SELECT * FROM wms_inbound_order WHERE inbound_no = 'IB123';"
```

**触发场景**：
- 第一次操作某张表
- SQL 执行失败（表不存在/字段不存在）
- 不确定字段名或表名
- 用户说“查XX数据”但未指定表

## 快速使用

**脚本路径**：`<SKILL目录>/scripts/db_cli.py`

```bash
# 查询数据
python3 <SKILL目录>/scripts/db_cli.py "SELECT * FROM users LIMIT 10;"

# 插入/更新/删除
python3 <SKILL目录>/scripts/db_cli.py "INSERT INTO users (name) VALUES ('张三');"
python3 <SKILL目录>/scripts/db_cli.py "UPDATE users SET status = 'active' WHERE id = 1;"
python3 <SKILL目录>/scripts/db_cli.py "DELETE FROM users WHERE id = 1;"

# 事务操作（多条 SQL，全部成功才提交）
python3 <SKILL目录>/scripts/db_cli.py -t \
  "INSERT INTO users (name) VALUES ('张三');" \
  "UPDATE accounts SET balance = balance - 100 WHERE id = 1;"

# 事务操作（单条 SQL 也可以用 -t）
python3 <SKILL目录>/scripts/db_cli.py -t "UPDATE users SET status = 'active' WHERE id = 1;"

# JSON 格式输出
python3 <SKILL目录>/scripts/db_cli.py -j "SELECT * FROM users;"
```

> **注意**：`<SKILL目录>` 会被自动替换为当前技能的实际路径

> 详细参数说明见下方 [参数说明](#db_cli-参数说明)

## 核心操作

### 查询数据

```bash
python3 <SKILL目录>/scripts/db_cli.py "SELECT * FROM users WHERE id = 1;"
python3 <SKILL目录>/scripts/db_cli.py "SELECT COUNT(*) as total FROM orders;"
```

### 插入/更新/删除

```bash
python3 <SKILL目录>/scripts/db_cli.py "INSERT INTO users (name, email) VALUES ('张三', 'zhangsan@example.com');"
python3 <SKILL目录>/scripts/db_cli.py "UPDATE users SET status = 'active' WHERE id = 1;"
python3 <SKILL目录>/scripts/db_cli.py "DELETE FROM users WHERE id = 1;"
```

### 事务操作

```bash
# 多条 SQL 在同一事务中执行，任一失败则全部回滚
python3 <SKILL目录>/scripts/db_cli.py -t \
  "INSERT INTO users (name) VALUES ('张三');" \
  "UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;" \
  "UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;"
```

### 查看表结构

```bash
python3 <SKILL目录>/scripts/db_cli.py "DESCRIBE users;"
python3 <SKILL目录>/scripts/db_cli.py "SHOW CREATE TABLE users;"
```

## 首次使用配置

首次执行 SQL 时，如果检测到配置不存在，会自动启动交互式配置向导。

也可以手动运行配置命令：

```bash
python3 <SKILL目录>/scripts/db_cli.py --init
```

配置文件位置：`~/.config/dba/config.json`（可通过 `AGENT_MYSQL_CONFIG` 环境变量覆盖）

### MySQL 配置示例

```json
{
  "current": "local",
  "local": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "pwd",
    "database": "db"
  }
}
```

### PostgreSQL 配置示例

```json
{
  "current": "local",
  "local": {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "pwd",
    "database": "db"
  }
}
```

### 多环境配置

支持同时配置多个环境，通过 `--env` 切换：

```json
{
  "current": "local",
  "local": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "local_pwd",
    "database": "dev_db"
  },
  "prod": {
    "type": "mysql",
    "host": "prod-db.example.com",
    "port": 3306,
    "user": "app_user",
    "password": "prod_pwd",
    "database": "prod_db"
  }
}
```

切换环境：

```bash
python3 <SKILL目录>/scripts/db_cli.py --env prod "SELECT * FROM users LIMIT 10;"
```

## 自动错误处理

脚本会自动处理以下问题，无需手动操作：

| 问题 | 自动处理 |
|------|----------|
| `pymysql` 未安装 (MySQL) | 自动安装依赖 |
| `psycopg2-binary` 未安装 (PostgreSQL) | 自动安装依赖 |
| 配置文件不存在 | 自动启动配置向导 |
| 数据库连接失败 | 显示详细错误信息 |
| SQL 语法错误 | 回滚事务并提示 |

**常见 MySQL 错误**：
- `OperationalError (1045)` - 密码错误，检查用户名/密码
- `OperationalError (1049)` - 数据库不存在，检查数据库名
- `OperationalError (2003)` - 连接失败，检查 MySQL 服务
- `ProgrammingError (1146)` - 表不存在，检查表名

**常见 PostgreSQL 错误**：
- `OperationalError: FATAL: password authentication failed` - 密码错误
- `OperationalError: FATAL: database does not exist` - 数据库不存在
- `OperationalError: could not connect to server` - 连接失败
- `UndefinedTable: relation does not exist` - 表不存在

**重要：Unknown database 错误处理**

当执行 SQL 时提示 `Unknown database 'xxx'` 错误，**不要盲目尝试其他 SQL**，应该：

1. **重新理解用户意图**：确认用户想查询的是哪个数据库
2. **读取配置文件确认**：检查 `~/.config/dba/config.json` 查看已配置的数据库
3. **与用户确认**：如果配置的数据库与用户意图不匹配，询问用户是否需要：
   - 切换到已配置的其他环境（使用 `--env` 参数）
   - 添加新的数据库配置（使用 `--init` 参数）

```bash
# ❌ 错误做法：盲目执行 SQL 尝试
python3 <SKILL目录>/scripts/db_cli.py "SELECT * FROM users;"
# 报错: Unknown database 'old_db'
python3 <SKILL目录>/scripts/db_cli.py "SHOW DATABASES;"  # 仍然连接不上

# ✅ 正确做法：先检查配置
cat ~/.config/dba/config.json
# 查看已配置的数据库，确认当前环境的 database 字段
# 然后与用户确认是否使用正确的数据库
```

## db_cli.py 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `sql` | 要执行的 SQL 语句（支持多条） | `"SELECT * FROM users;"` |
| `--file, -f` | SQL 文件路径 | `--file query.sql` |
| `--env, -e` | 数据库环境 | `--env dev` |
| `--config, -c` | 配置文件路径 | `--config /path/to/config.json` |
| `--max-rows, -m` | 最大返回行数 | `-m 100` |
| `--json, -j` | JSON 格式输出 | `-j` |
| `--transaction, -t` | **事务模式**（单条或多条SQL在同一事务中执行） | `-t "UPDATE..."` |
| `--init` | **初始化配置**（交互式配置数据库） | `--init` |
| `--export-ddl` | **导出DDL**（导出所有表结构到指定目录） | `--export-ddl sql/dbmate_xxx` |
| `--export-dml` | **导出DML**（导出指定表数据到指定目录） | `--export-dml sql/dbmate_xxx --tables sys_menu sys_config` |
| `--tables` | 导出DML时指定表名列表 | `--tables table1 table2` |
| `--exclude-tables` | 导出DDL时排除的表（默认排除schema_migrations） | `--exclude-tables schema_migrations dbmate_xxx` |
| `--output-file, -o` | 指定输出文件名（可选） | `-o init.sql` |
| `--diff-ddl` | **对比DDL差异**（对比两个环境生成升级脚本） | `--diff-ddl dev` |
| `--output-dir, -d` | diff-ddl输出目录（默认: sql/dbmate_xxx） | `-d sql/dbmate_scm` |

**使用示例**：

```bash
# 单条查询
python3 <SKILL目录>/scripts/db_cli.py "SELECT * FROM users LIMIT 10;"

# 多条 SQL（逐条执行，各自独立提交）
python3 <SKILL目录>/scripts/db_cli.py "INSERT INTO..." "UPDATE..."

# 事务模式（单条或多条SQL，全部成功才提交，任一失败则回滚）
python3 <SKILL目录>/scripts/db_cli.py -t "UPDATE users SET status = 'active' WHERE id = 1;"

python3 <SKILL目录>/scripts/db_cli.py -t \
  "INSERT INTO users (name) VALUES ('张三');" \
  "UPDATE accounts SET balance = balance - 100 WHERE id = 1;"

# JSON 输出（方便程序处理）
python3 <SKILL目录>/scripts/db_cli.py -j "SELECT * FROM users;"

# DDL差异对比（生成升级脚本）
python3 <SKILL目录>/scripts/db_cli.py --env test --diff-ddl dev --output-dir sql/dbmate_scm
python3 <SKILL目录>/scripts/db_cli.py --env test --diff-ddl dev -o 20260515163211_DDL_v2.sql
```

## 数据库管理

### MySQL

```bash
# 查看所有数据库
python3 <SKILL目录>/scripts/db_cli.py "SHOW DATABASES;"

# 查看当前数据库的表
python3 <SKILL目录>/scripts/db_cli.py "SHOW TABLES;"

# 创建数据库
python3 <SKILL目录>/scripts/db_cli.py "CREATE DATABASE IF NOT EXISTS mydb CHARACTER SET utf8mb4;"
```

### PostgreSQL

```bash
# 查看所有数据库
python3 <SKILL目录>/scripts/db_cli.py "SELECT datname FROM pg_database;"

# 查看当前数据库的表
python3 <SKILL目录>/scripts/db_cli.py "\dt"

# 创建数据库
python3 <SKILL目录>/scripts/db_cli.py "CREATE DATABASE mydb;"
```

## 数据库导出（新增）

支持从 MySQL 数据库导出 DDL（表结构）和 DML（表数据），用于数据库迁移或备份。

### 导出DDL（表结构）

```bash
# 导出所有表DDL到指定目录
python3 <SKILL目录>/scripts/db_cli.py --export-ddl sql/dbmate_scm_dev

# 导出DDL并排除特定表
python3 <SKILL目录>/scripts/db_cli.py --export-ddl sql/dbmate_scm_dev \
  --exclude-tables schema_migrations dbmate_scm

# 导出DDL并指定输出文件名
python3 <SKILL目录>/scripts/db_cli.py --export-ddl sql/dbmate_scm_dev \
  --output-file 20260512120000_DDL_init.sql

# 在dev环境中导出DDL
python3 <SKILL目录>/scripts/db_cli.py --env dev --export-ddl sql/dbmate_scm_dev
```

### 导出DML（表数据）

```bash
# 导出指定表的数据
python3 <SKILL目录>/scripts/db_cli.py --export-dml sql/dbmate_scm_dev \
  --tables sys_menu sys_permission sys_config

# 导出单个表的数据
python3 <SKILL目录>/scripts/db_cli.py --export-dml sql/dbmate_scm_dev \
  --tables sys_config

# 导出数据并指定输出文件名
python3 <SKILL目录>/scripts/db_cli.py --export-dml sql/dbmate_scm_dev \
  --tables sys_menu sys_config \
  --output-file 20260512120000_DML_init.sql
```

### 使用场景

1. **数据库迁移**：从本地数据库导出DDL+DML，在测试/生产环境执行
2. **数据库备份**：定期导出DDL作为数据库结构备份
3. **生成迁移脚本**：导出后添加 `-- migrate:up/down` 标记，用于dbmate迁移

### 注意事项

- 导出功能目前仅支持 **MySQL** 数据库
- DDL导出默认排除 `schema_migrations` 表
- DML导出时，空表会被自动跳过
- 导出的文件不包含 dbmate 的 migrate 标记，需要手动添加

### 典型工作流程

```bash
# 1. 导出DDL
cd /path/to/project
python3 ~/.qoder/skills/dba/scripts/db_cli.py --export-ddl sql/dbmate_scm_dev \
  --exclude-tables schema_migrations

# 2. 导出DML（仅系统配置表）
python3 ~/.qoder/skills/dba/scripts/db_cli.py --export-dml sql/dbmate_scm_dev \
  --tables sys_menu sys_permission sys_config

# 3. 手动添加 migrate 标记到 SQL 文件
# 在文件开头添加: -- migrate:up
# 在文件结尾添加: -- migrate:down

# 4. 使用 dbmate 执行迁移
bash <dbmate技能目录>/scripts/migrate.sh --config=dev --module=dbmate_scm_dev
```

## DDL差异对比

对比两个数据库环境的表结构差异，自动生成升级脚本（CREATE TABLE + ALTER TABLE）。

### 使用场景

1. **环境同步**：对比test和dev环境，生成dev的升级脚本
2. **数据库迁移**：对比本地和生产环境，生成迁移SQL
3. **结构审计**：快速查看两个环境的表结构差异

### 使用示例

```bash
# 对比test和dev环境，生成升级脚本
cd /path/to/project
python3 ~/.qoder/skills/dba/scripts/db_cli.py --env test --diff-ddl dev \
  --output-dir sql/dbmate_scm

# 指定输出文件名
python3 ~/.qoder/skills/dba/scripts/db_cli.py --env test --diff-ddl dev \
  -o 20260515163211_DDL_v2.sql
```

### 输出内容

生成的SQL文件包含：
- **migrate:up**：新增表（CREATE TABLE）+ 修改表（ALTER TABLE）
- **migrate:down**：预留注释，手动编写回滚SQL

> **注意**：不会生成DROP TABLE语句，确保升级安全

## 安全建议

1. **禁止**在代码中硬编码密码，使用配置文件或环境变量
2. **使用**参数化查询防止 SQL 注入（拼接 SQL 时注意转义）
3. 生产环境**建议**使用只读账号执行查询
4. 修改操作建议使用事务，确保数据一致性

## 执行规则（AI 必读）

### 强制预检查

**在执行任何 SQL 前，必须遵循：**

1. **第一次操作表** → 先 `DESCRIBE 表名;` 确认字段名
2. **不确定表名** → 先 `SHOW TABLES;` 查找表
3. **SQL 报错** → 根据错误信息调整，不要盲目重试

### SELECT 字段选择原则

**查询数据时，优先使用 `SELECT *`，避免指定字段名。**

- ✅ **正确**：`SELECT * FROM users LIMIT 10;`
- ❌ **避免**：`SELECT id, name, status FROM users LIMIT 10;`（字段名可能不存在或拼写错误）

**为什么优先用 `SELECT *`？**
- 执行前无法 100% 确认字段名，硬编码字段极易出现 `Unknown column` 错误
- `SELECT *` 可以直观看到表中所有字段及数据样例
- 只有在确认字段名完全正确后，才考虑使用指定字段（如数据量极大、字段极多的场景）

> 💡 **执行流程建议**：先用 `SELECT *` 查看数据 → 确认字段名 → 如需优化再改用指定字段

### 常见错误处理

| 错误信息 | 原因 | 解决方法 |
|---------|------|----------|
| `Unknown column 'xxx'` (MySQL) | 字段名错误 | `DESCRIBE 表名;` 查看正确字段名 |
| `Table 'xxx' doesn't exist` (MySQL) | 表名错误 | `SHOW TABLES;` 查找正确的表名 |
| `relation "xxx" does not exist` (PostgreSQL) | 表名错误 | `\dt` 查找正确的表名 |
| `column "xxx" does not exist` (PostgreSQL) | 字段名错误 | `\d 表名` 查看正确字段名 |

### 执行前自检清单

- [ ] 表名是否正确？（不确定的话 `SHOW TABLES;`）
- [ ] 字段名是否正确？（不确定的话 `DESCRIBE 表名;`）
- [ ] WHERE 条件字段是否存在？
- [ ] UPDATE/DELETE 是否有 WHERE 条件？（防止全表更新/删除）

**记住**：花 5 秒钟预检查，胜过花 5 分钟调试错误！