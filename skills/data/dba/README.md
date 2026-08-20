# DBA技能

通过自然语言直接操作 MySQL / PostgreSQL，推荐用 `/dba` 显式调用。

## 使用方法

```
/dba 连接本地数据库
/dba 查询最近7天的订单
/dba 看看用户表有哪些字段
/dba 把订单状态改为已完成
/dba 导出上个月的销售数据
```

## 能做什么

| 场景 | 示例 |
|------|------|
| 连接配置 | `/dba 连接本地`、`/dba 切换到生产环境` |
| 数据查询 | `/dba 查用户表前10条`、`/dba 订单号 O123 的详情` |
| 修改数据 | `/dba 把用户 1001 的状态改为已激活` |
| 查看结构 | `/dba 看看订单表有哪些字段`、`/dba 显示所有表` |
| 批量操作 | `/dba 批量更新订单状态` |
| 性能分析 | `/dba EXPLAIN 这个查询` |
| 导出DDL | `/dba 导出DDL到 sql/dbmate_scm` |
| 导出DML | `/dba 导出DML到 sql/dbmate_scm --tables sys_menu sys_config` |
| DDL对比 | `/dba 对比test和dev环境生成升级脚本`（生成CREATE+ALTER，不含DROP） |

## 首次使用

首次执行时会自动引导配置数据库连接信息，配置文件保存在 `~/.config/dba/config.json`，支持多环境切换。

```json
{"current": "local", "local": {"type": "mysql", "host": "localhost", "port": 3306, "user": "root", "password": "pwd", "database": "db"}}
```

支持多环境：
```
/dba 切换到 test 环境
/dba --env prod 查询今日订单
```