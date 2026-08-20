-- ============================================================
-- MES 智能问数 · MySQL 只读账号建立脚本
-- 适用：MySQL 5.7 / 8.0（MariaDB 亦可）
-- 执行方式：以 root 或具备 CREATE USER / GRANT 权限的账号登录后执行本脚本
-- 执行前必改 3 处：① 密码  ② 数据库名 your_mes_db  ③ 主机网段 10.0.%
-- ============================================================

-- 0. 确认当前身份（应显示 root@localhost 或管理账号）
SELECT CURRENT_USER();

-- ------------------------------------------------------------
-- 1. 创建只读账号 mes_query
--    ⚠️ 若提示已存在，先执行文末【附录 A】的 DROP 语句再重跑本脚本
--    ⚠️ MySQL 8.0 + 旧驱动(pymysql<1.0/MySQLdb)：改用下面的兼容写法：
--       CREATE USER 'mes_query'@'10.0.%' IDENTIFIED WITH mysql_native_password BY '你的强密码';
-- ------------------------------------------------------------
CREATE USER 'mes_query'@'10.0.%' IDENTIFIED BY '你的强密码';

-- ------------------------------------------------------------
-- 2. 授权：只读你的 MES 业务库（把 your_mes_db 换成实际库名）
--    只授 SELECT，INSERT/UPDATE/DELETE/DDL 天然全部禁止
-- ------------------------------------------------------------
GRANT SELECT ON your_mes_db.* TO 'mes_query'@'10.0.%';

-- ------------------------------------------------------------
-- 3. 资源限制（可选，建议保留）：
--    最多 5 个并发连接；每小时最多 3600 次查询（防拖垮生产库）
-- ------------------------------------------------------------
ALTER USER 'mes_query'@'10.0.%' WITH MAX_USER_CONNECTIONS 5;
ALTER USER 'mes_query'@'10.0.%' WITH MAX_QUERIES_PER_HOUR 3600;

-- 4. 刷新权限
FLUSH PRIVILEGES;

-- 5. 验证：输出应只有 SELECT 相关授权，不应出现 GRANT OPTION / FILE / PROCESS
SHOW GRANTS FOR 'mes_query'@'10.0.%';

-- ============================================================
-- 附录 A：账号已存在时重建
-- ============================================================
-- DROP USER IF EXISTS 'mes_query'@'10.0.%';

-- ============================================================
-- 附录 B：按表精确授权（最严格，推荐生产环境使用）
-- 覆盖智能问数 16 个 intent 的核心底层表；其余表按需追加
-- 用附录 B 时，可把第 2 步的 GRANT ... ON your_mes_db.* 注释掉
-- ============================================================
-- GRANT SELECT ON your_mes_db.ac_mo_report_process TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.ac_station_report_process TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.ac_report_data_detail TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.ac_lot_status TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.pl_mo_data TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.pl_mo_status TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.eq_status TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.eq_basis TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.eq_check_record TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.eq_check_record_detail TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.eq_maintenance_record TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.in_except_reason_record TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.in_pqc_record_process TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.in_pqc_task_data TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.dispatch_record TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.me_op_basis TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.me_workstation_basis TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.ma_basis TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.ac_station_sn_process TO 'mes_query'@'10.0.%';
-- GRANT SELECT ON your_mes_db.en_calendar_basis TO 'mes_query'@'10.0.%';
-- FLUSH PRIVILEGES;
-- SHOW GRANTS FOR 'mes_query'@'10.0.%';

-- ============================================================
-- 附录 C：只读验证（用 mes_query 账号另开一个连接执行，预期全部报权限错误）
-- ============================================================
-- UPDATE your_mes_db.pl_mo_data SET QTY = QTY;        -- 应报: UPDATE command denied
-- DELETE FROM your_mes_db.pl_mo_data WHERE 1=0;       -- 应报: DELETE command denied
-- DROP TABLE your_mes_db.pl_mo_data;                  -- 应报: DROP command denied
