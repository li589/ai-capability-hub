---
name: sql_query
version: 1.0.0
description: 当用户提出数据查询需求（如'查数'、'查一下订单量'、'有多少用户'、'帮我跑个SQL'等），使用数据源工具发现表结构，生成并执行只读 SQL 查询。
dependencies:
  tools:
    - datasourceTool
    - sqlQueryTool
install_source: official
install_method: download
skill_id: official_RuTj9IMT
enabled_at: 1787232830369
name_zh: SQL 查询
---

# SQL 查询技能

当用户提出与数据查询相关的问题时，按照以下工作流程操作。

## 工作流程

### 第一步：发现数据源
调用 `query_datasource(action='list_datasources')` 查看所有可用的外部数据源。
- 如果只有一个数据源，直接使用它
- 如果有多个数据源，根据用户问题推断最相关的数据源；不确定时询问用户

### 第二步：发现表结构
调用 `query_datasource(action='list_tables', datasourceId=<id>)` 查看数据源中的表列表。
- 根据表名和注释判断与用户问题相关的表
- 不要一次查看所有表的结构，只查看相关的 2-3 张表

### 第三步：查看列详情
调用 `query_datasource(action='describe_table', datasourceId=<id>, tableName='<表名>')` 查看列名、类型和注释。
- 记住列名和类型，生成 SQL 时必须使用正确的列名

### 第四步：生成 SQL
根据表结构和用户问题，生成 SELECT SQL。遵循以下规则：

**SQL 生成规则：**
1. **仅生成 SELECT 语句**，绝不生成 INSERT/UPDATE/DELETE/DROP 等写操作
2. 多表查询时，所有字段必须用表别名限定（如 `t1.name`）
3. 聚合查询使用 COUNT/SUM/AVG/MAX/MIN 等函数
4. 时间过滤使用数据库对应的日期函数
5. 字符串匹配使用 LIKE 并注意大小写
6. 结果默认按合理的顺序排序（如时间倒序）
7. 系统会自动注入 LIMIT 500，无需手动添加（除非用户指定了数量）

**不同数据库的注意事项：**
- MySQL：日期用 `DATE_FORMAT()`、`NOW()`，字符串连接用 `CONCAT()`
- PostgreSQL：日期用 `TO_CHAR()`、`NOW()`，字符串连接用 `||`
- ClickHouse：日期用 `toDate()`、`today()`，注意不支持部分标准 SQL 语法

### 第五步：执行查询
调用 `execute_sql(datasourceId=<id>, sql='<SQL>')` 执行查询。

### 第六步：解读结果
- 用自然语言总结查询结果的要点
- 如果结果为空，分析可能的原因（表名/列名/条件有误等）
- 如果需要，可以调整 SQL 重新查询
- 如果查询结果包含数值列，系统会自动生成 ECharts 图表，无需你手动生成图表代码
- **重要：不要使用 write_file 工具生成 HTML 图表文件，系统已内置图表渲染能力**

## 错误处理

如果 SQL 执行失败：
1. 仔细阅读错误信息
2. 常见原因：列名拼写错误、类型不匹配、语法错误
3. 根据错误修正 SQL 并重试一次
4. 如果仍然失败，向用户说明错误原因

## 安全须知

- 本工具仅支持只读查询（SELECT），写操作会被系统拒绝
- 查询结果默认限制为 500 行
- 查询超时为 30 秒
- 如果用户要求执行写操作，应礼貌拒绝并说明这是安全限制
