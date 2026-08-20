#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 执行器 - 支持 MySQL 和 PostgreSQL
自动处理依赖安装和配置初始化，无需手动操作

用法:
  python3 db_cli.py "SELECT * FROM users LIMIT 10;"
  python3 db_cli.py --file query.sql
  python3 db_cli.py --env dev "SELECT COUNT(*) FROM orders;"
  python3 db_cli.py --init  # 交互式配置数据库连接
"""

import json
import os
import sys
import argparse
import re
import subprocess

# 全局数据库驱动变量
pymysql = None
psycopg2 = None
psycopg2_extras = None

# ============================================
# 依赖管理
# ============================================

def ensure_mysql_driver():
    """确保 pymysql 已安装,未安装则自动安装"""
    global pymysql
    try:
        import pymysql as pm
        pymysql = pm
        return pymysql
    except ImportError:
        print("⚠ 检测到 pymysql 未安装,正在自动安装...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "pymysql",
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ pymysql 安装成功\n")
            import pymysql as pm
            pymysql = pm
            return pymysql
        except Exception as e:
            print(f"✗ 自动安装失败: {e}")
            print("\n请手动安装: pip install pymysql")
            sys.exit(1)

def ensure_pgsql_driver():
    """确保 psycopg2-binary 已安装,未安装则自动安装"""
    global psycopg2, psycopg2_extras
    try:
        import psycopg2 as ps
        import psycopg2.extras as pse
        psycopg2 = ps
        psycopg2_extras = pse
        return psycopg2
    except ImportError:
        print("⚠ 检测到 psycopg2-binary 未安装,正在自动安装...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "psycopg2-binary",
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ psycopg2-binary 安装成功\n")
            import psycopg2 as ps
            import psycopg2.extras as pse
            psycopg2 = ps
            psycopg2_extras = pse
            return psycopg2
        except Exception as e:
            print(f"✗ 自动安装失败: {e}")
            print("\n请手动安装: pip install psycopg2-binary")
            sys.exit(1)

def ensure_driver(db_type):
    """根据数据库类型确保对应的驱动已安装"""
    if db_type == 'mysql':
        return ensure_mysql_driver()
    elif db_type == 'postgresql':
        return ensure_pgsql_driver()
    else:
        print(f"✗ 不支持的数据库类型: {db_type}")
        print("支持的数据库类型: mysql, postgresql")
        sys.exit(1)

def load_config(config_file=None, env_name=None):
    """加载数据库配置,配置不存在时引导创建"""
    if config_file:
        config_path = os.path.expanduser(config_file)
    else:
        config_path = os.getenv('AGENT_MYSQL_CONFIG', 
                               os.path.expanduser('~/.config/dba/config.json'))
    
    if not os.path.exists(config_path):
        print(f"⚠ 配置文件不存在: {config_path}")
        print("\n📝 首次使用需要配置数据库连接信息\n")
        create_config(config_path)
        # 重新加载配置
        return load_config(config_path, env_name)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    env = env_name or config_data.get('current', 'local')
    
    if env not in config_data:
        print(f"错误: 环境 '{env}' 不存在")
        print(f"可用环境: {', '.join([k for k in config_data.keys() if k != 'current'])}")
        sys.exit(1)
    
    config = config_data[env].copy()
    db_type = config.pop('type', 'mysql')  # 移除 type 字段，避免传给数据库驱动
    
    # 根据数据库类型设置不同的连接参数
    if db_type == 'mysql':
        config['charset'] = 'utf8mb4'
        pymysql = ensure_driver(db_type)
        config['cursorclass'] = pymysql.cursors.DictCursor
    elif db_type == 'postgresql':
        ensure_driver(db_type)
        # PostgreSQL 不需要 cursorclass,会在连接时指定
    
    return config, env, db_type

def execute_transaction(sql_statements, config, max_rows=1000, db_type='mysql'):
    """执行事务(多条 SQL)"""
    connection = None
    try:
        # 检测是否包含 DDL 语句
        has_ddl = False
        ddl_statements = []
        for sql in sql_statements:
            sql_upper = sql.strip().upper()
            if sql_upper.startswith(('ALTER ', 'CREATE ', 'DROP ', 'TRUNCATE ', 'RENAME ', 'INDEX ', 'GRANT ', 'REVOKE ')):
                has_ddl = True
                ddl_statements.append(sql)
        
        # 如果包含 DDL 且是 MySQL，给出警告
        if has_ddl and db_type == 'mysql':
            print(f"\n⚠ 警告: 检测到 DDL 语句(共 {len(ddl_statements)} 条)")
            print("  MySQL 的 DDL 语句不支持事务回滚，会立即生效！")
            print("  如后续语句失败，已执行的 DDL 无法回滚。\n")
        
        if db_type == 'mysql':
            connection = pymysql.connect(**config)
        elif db_type == 'postgresql':
            # PostgreSQL 连接
            pg_config = {
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 5432),
                'user': config.get('user', 'postgres'),
                'password': config.get('password', ''),
                'dbname': config.get('database', config.get('dbname', ''))
            }
            connection = psycopg2.connect(**pg_config)
        
        # 开启事务
        # MySQL 默认自动开启事务,PostgreSQL 需要显式开始
        if db_type == 'postgresql':
            connection.autocommit = False
        
        results = []
        for i, sql in enumerate(sql_statements, 1):
            sql = sql.strip()
            if not sql:
                continue
            
            print(f"\n[{i}/{len(sql_statements)}] 执行: {sql[:80]}{'...' if len(sql) > 80 else ''}")
            
            if db_type == 'mysql':
                with connection.cursor() as cursor:
                    is_select = sql.upper().startswith('SELECT')
                    is_metadata = sql.upper().startswith(('SHOW', 'DESC', 'DESCRIBE', 'EXPLAIN'))
                    
                    try:
                        cursor.execute(sql)
                        
                        if is_select:
                            query_results = cursor.fetchmany(max_rows)
                            results.append({
                                'status': 'success',
                                'type': 'query',
                                'sql': sql,
                                'rows': len(query_results),
                                'data': query_results
                            })
                            print(f"  ✓ 查询成功 ({len(query_results)} 条)")
                        elif is_metadata:
                            query_results = cursor.fetchmany(50)
                            results.append({
                                'status': 'success',
                                'type': 'query',
                                'sql': sql,
                                'rows': len(query_results),
                                'data': query_results
                            })
                            print(f"  ✓ 查询成功 ({len(query_results)} 条)")
                        else:
                            rows_affected = cursor.rowcount
                            last_id = cursor.lastrowid
                            results.append({
                                'status': 'success',
                                'type': 'modify',
                                'sql': sql,
                                'rows_affected': rows_affected,
                                'last_insert_id': last_id if last_id else None
                            })
                            print(f"  ✓ 执行成功 (影响 {rows_affected} 行)")
                            
                    except Exception as e:
                        print(f"  ✗ 执行失败: {e}")
                        raise
            elif db_type == 'postgresql':
                # PostgreSQL 使用 DictCursor
                with connection.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cursor:
                    is_select = sql.upper().startswith('SELECT')
                    is_metadata = sql.upper().startswith(('SHOW', 'DESC', 'DESCRIBE', 'EXPLAIN', '\\d'))
                    
                    try:
                        cursor.execute(sql)
                        
                        if is_select:
                            query_results = cursor.fetchmany(max_rows)
                            # 将 DictRow 转换为普通字典
                            query_results = [dict(row) for row in query_results]
                            results.append({
                                'status': 'success',
                                'type': 'query',
                                'sql': sql,
                                'rows': len(query_results),
                                'data': query_results
                            })
                            print(f"  ✓ 查询成功 ({len(query_results)} 条)")
                        elif is_metadata:
                            query_results = cursor.fetchmany(50)
                            # 将 DictRow 转换为普通字典
                            query_results = [dict(row) for row in query_results]
                            results.append({
                                'status': 'success',
                                'type': 'query',
                                'sql': sql,
                                'rows': len(query_results),
                                'data': query_results
                            })
                            print(f"  ✓ 查询成功 ({len(query_results)} 条)")
                        else:
                            rows_affected = cursor.rowcount
                            # PostgreSQL 获取最后插入 ID
                            last_id = None
                            if sql.upper().startswith('INSERT'):
                                cursor.execute("SELECT LASTVAL()")
                                last_id_result = cursor.fetchone()
                                last_id = last_id_result[0] if last_id_result else None
                            
                            results.append({
                                'status': 'success',
                                'type': 'modify',
                                'sql': sql,
                                'rows_affected': rows_affected,
                                'last_insert_id': last_id
                            })
                            print(f"  ✓ 执行成功 (影响 {rows_affected} 行)")
                            
                    except Exception as e:
                        print(f"  ✗ 执行失败: {e}")
                        raise
        
        # 所有语句执行成功,提交事务
        # 注意: MySQL 的 DDL 语句已自动提交，此处 commit 对其他语句生效
        connection.commit()
        if has_ddl and db_type == 'mysql':
            print(f"\n✓ 所有语句执行完成")
            print("  注意: DDL 语句已自动提交，无法回滚")
        else:
            print(f"\n✓ 事务提交成功")
        
        return {
            'status': 'success',
            'type': 'transaction',
            'committed': True,
            'statements': len(results),
            'results': results,
            'has_ddl': has_ddl
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
            print(f"\n✗ 事务已回滚: {e}")
        
        return {
            'status': 'error',
            'type': 'transaction',
            'committed': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
    finally:
        if connection:
            connection.close()

def execute_sql(sql, config, max_rows=1000, db_type='mysql'):
    """执行 SQL 并返回结果"""
    connection = None
    try:
        if db_type == 'mysql':
            connection = pymysql.connect(**config)
        elif db_type == 'postgresql':
            # PostgreSQL 连接
            pg_config = {
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 5432),
                'user': config.get('user', 'postgres'),
                'password': config.get('password', ''),
                'dbname': config.get('database', config.get('dbname', ''))
            }
            connection = psycopg2.connect(**pg_config)
        
        if db_type == 'mysql':
            with connection.cursor() as cursor:
                # 判断是否为 SELECT 查询
                is_select = sql.strip().upper().startswith('SELECT')
                is_metadata = sql.strip().upper().startswith(('SHOW', 'DESC', 'DESCRIBE', 'EXPLAIN'))
                
                # 执行 SQL
                cursor.execute(sql)
                
                if is_select:
                    # SELECT 查询类语句
                    results = cursor.fetchmany(max_rows)
                    
                    output = {
                        'status': 'success',
                        'type': 'query',
                        'rows': len(results),
                        'data': results
                    }
                    
                    # 打印结果
                    if results:
                        print(f"\n查询结果 ({len(results)} 条记录):\n")
                        
                        # 表格化输出
                        headers = list(results[0].keys())
                        
                        # 计算列宽
                        col_widths = {}
                        for header in headers:
                            col_widths[header] = len(str(header))
                            for row in results[:10]:  # 只检查前10行
                                col_widths[header] = max(col_widths[header], len(str(row.get(header, ''))))
                            col_widths[header] = min(col_widths[header], 50)  # 最夔50字符
                        
                        # 打印表头
                        header_line = ' | '.join([str(h).ljust(col_widths[h]) for h in headers])
                        print(header_line)
                        print('-' * len(header_line))
                        
                        # 打印数据(最多10行)
                        for i, row in enumerate(results[:10]):
                            values = [str(row.get(h, '')).ljust(col_widths[h]) for h in headers]
                            print(' | '.join(values))
                        
                        if len(results) > 10:
                            print(f"\n... 还有 {len(results) - 10} 条记录(仅显示前10条)")
                    else:
                        print("\n查询结果为空")
                    
                    return output
                elif is_metadata:
                    # SHOW/DESC/DESCRIBE/EXPLAIN 元数据查询
                    results = cursor.fetchmany(50)
                    
                    output = {
                        'status': 'success',
                        'type': 'query',
                        'rows': len(results),
                        'data': results
                    }
                    
                    # 打印结果
                    if results:
                        print(f"\n查询结果 ({len(results)} 条记录):\n")
                        
                        # 表格化输出
                        headers = list(results[0].keys())
                        
                        # 计算列宽
                        col_widths = {}
                        for header in headers:
                            col_widths[header] = len(str(header))
                            for row in results[:10]:  # 只检查前10行
                                col_widths[header] = max(col_widths[header], len(str(row.get(header, ''))))
                            col_widths[header] = min(col_widths[header], 50)  # 最多50字符
                        
                        # 打印表头
                        header_line = ' | '.join([str(h).ljust(col_widths[h]) for h in headers])
                        print(header_line)
                        print('-' * len(header_line))
                        
                        # 打印数据(最多50行)
                        for i, row in enumerate(results[:50]):
                            values = [str(row.get(h, '')).ljust(col_widths[h]) for h in headers]
                            print(' | '.join(values))
                        
                        if len(results) > 50:
                            print(f"\n... 还有 {len(results) - 50} 条记录(仅显示前50条)")
                    else:
                        print("\n查询结果为空")
                    
                    return output
                else:
                    # 非查询类语句(INSERT/UPDATE/DELETE)
                    connection.commit()
                    rows_affected = cursor.rowcount
                    last_id = cursor.lastrowid
                    
                    output = {
                        'status': 'success',
                        'type': 'modify',
                        'rows_affected': rows_affected
                    }
                    
                    if last_id:
                        output['last_insert_id'] = last_id
                    
                    print(f"\n执行成功!")
                    print(f"影响行数: {rows_affected}")
                    if last_id:
                        print(f"自增ID: {last_id}")
                    
                    return output
        
        elif db_type == 'postgresql':
            with connection.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cursor:
                # 判断是否为 SELECT 查询
                is_select = sql.strip().upper().startswith('SELECT')
                is_metadata = sql.strip().upper().startswith(('SHOW', 'DESC', 'DESCRIBE', 'EXPLAIN', '\\d'))
                
                # 执行 SQL
                cursor.execute(sql)
                
                if is_select:
                    # SELECT 查询类语句
                    results = cursor.fetchmany(max_rows)
                    # 将 DictRow 转换为普通字典
                    results = [dict(row) for row in results]
                    
                    output = {
                        'status': 'success',
                        'type': 'query',
                        'rows': len(results),
                        'data': results
                    }
                    
                    # 打印结果
                    if results:
                        print(f"\n查询结果 ({len(results)} 条记录):\n")
                        
                        # 表格化输出
                        headers = list(results[0].keys())
                        
                        # 计算列宽
                        col_widths = {}
                        for header in headers:
                            col_widths[header] = len(str(header))
                            for row in results[:10]:  # 只检查前10行
                                col_widths[header] = max(col_widths[header], len(str(row.get(header, ''))))
                            col_widths[header] = min(col_widths[header], 50)  # 最夔50字符
                        
                        # 打印表头
                        header_line = ' | '.join([str(h).ljust(col_widths[h]) for h in headers])
                        print(header_line)
                        print('-' * len(header_line))
                        
                        # 打印数据(最多10行)
                        for i, row in enumerate(results[:10]):
                            values = [str(row.get(h, '')).ljust(col_widths[h]) for h in headers]
                            print(' | '.join(values))
                        
                        if len(results) > 10:
                            print(f"\n... 还有 {len(results) - 10} 条记录(仅显示前10条)")
                    else:
                        print("\n查询结果为空")
                    
                    connection.commit()
                    return output
                elif is_metadata:
                    # SHOW/DESC/DESCRIBE/EXPLAIN 元数据查询
                    results = cursor.fetchmany(50)
                    # 将 DictRow 转换为普通字典
                    results = [dict(row) for row in results]
                    
                    output = {
                        'status': 'success',
                        'type': 'query',
                        'rows': len(results),
                        'data': results
                    }
                    
                    # 打印结果
                    if results:
                        print(f"\n查询结果 ({len(results)} 条记录):\n")
                        
                        # 表格化输出
                        headers = list(results[0].keys())
                        
                        # 计算列宽
                        col_widths = {}
                        for header in headers:
                            col_widths[header] = len(str(header))
                            for row in results[:10]:  # 只检查前10行
                                col_widths[header] = max(col_widths[header], len(str(row.get(header, ''))))
                            col_widths[header] = min(col_widths[header], 50)  # 最多50字符
                        
                        # 打印表头
                        header_line = ' | '.join([str(h).ljust(col_widths[h]) for h in headers])
                        print(header_line)
                        print('-' * len(header_line))
                        
                        # 打印数据(最多50行)
                        for i, row in enumerate(results[:50]):
                            values = [str(row.get(h, '')).ljust(col_widths[h]) for h in headers]
                            print(' | '.join(values))
                        
                        if len(results) > 50:
                            print(f"\n... 还有 {len(results) - 50} 条记录(仅显示前50条)")
                    else:
                        print("\n查询结果为空")
                    
                    connection.commit()
                    return output
                else:
                    # 非查询类语句(INSERT/UPDATE/DELETE)
                    connection.commit()
                    rows_affected = cursor.rowcount
                    
                    # PostgreSQL 获取最后插入 ID
                    last_id = None
                    if sql.strip().upper().startswith('INSERT'):
                        cursor.execute("SELECT LASTVAL()")
                        last_id_result = cursor.fetchone()
                        last_id = last_id_result[0] if last_id_result else None
                    
                    output = {
                        'status': 'success',
                        'type': 'modify',
                        'rows_affected': rows_affected
                    }
                    
                    if last_id:
                        output['last_insert_id'] = last_id
                    
                    print(f"\n执行成功!")
                    print(f"影响行数: {rows_affected}")
                    if last_id:
                        print(f"自增ID: {last_id}")
                    
                    return output
                
    except Exception as e:
        if connection:
            connection.rollback()
        
        error_output = {
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }
        
        print(f"\n执行失败!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        
        return error_output
    finally:
        if connection:
            connection.close()

def execute_sql_file(file_path, config, max_rows=1000, db_type='mysql'):
    """执行 SQL 文件"""
    if not os.path.exists(file_path):
        print(f"错误: SQL 文件不存在: {file_path}")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除注释
    content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # 分割 SQL 语句
    statements = [s.strip() for s in content.split(';') if s.strip()]
    
    print(f"执行 SQL 文件: {file_path}")
    print(f"共 {len(statements)} 条语句\n")
    
    results = []
    for i, sql in enumerate(statements, 1):
        print(f"\n[{i}/{len(statements)}] 执行:")
        # 打印 SQL(截断显示)
        sql_preview = sql[:100] + '...' if len(sql) > 100 else sql
        print(f"  {sql_preview}\n")
        
        result = execute_sql(sql, config, max_rows, db_type)
        results.append(result)
    
    # 总结
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n{'='*60}")
    print(f"执行完成: {success_count}/{len(statements)} 成功")
    print(f"{'='*60}")
    
    return results

def create_config(config_path):
    """引导创建配置文件（支持追加新环境或更新现有配置）"""
    # 确保目录存在
    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)
    
    # 检查配置文件是否已存在
    config_exists = os.path.exists(config_path)
    existing_config = {}
    
    if config_exists:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
            print(f"✓ 检测到现有配置文件: {config_path}")
            print(f"  当前环境: {existing_config.get('current', '未设置')}")
            envs = [k for k in existing_config.keys() if k != 'current']
            print(f"  已有环境: {', '.join(envs) if envs else '无'}")
            print()
        except Exception as e:
            print(f"⚠ 读取现有配置失败: {e}")
            print("将创建新的配置文件\n")
            existing_config = {}
    else:
        print("⚠ 配置文件不存在，将创建新配置\n")
    
    print("="*50)
    print("数据库配置向导")
    print("="*50)
    print("\n请选择数据库类型:")
    print("1. MySQL")
    print("2. PostgreSQL")
    
    db_choice = input("\n请选择 [1]: ").strip() or "1"
    if db_choice == "2":
        db_type = 'postgresql'
        print("\n已选择: PostgreSQL")
    else:
        db_type = 'mysql'
        print("\n已选择: MySQL")
    
    print("\n请输入数据库连接信息(直接回车使用默认值):\n")
    
    env_name = input("环境名称 [local]: ").strip() or "local"
    
    # 检查环境是否已存在，如果存在则自动要求重新输入
    if env_name in existing_config:
        print(f"\n⚠ 环境 '{env_name}' 已存在!")
        print(f"现有配置:")
        old_config = existing_config[env_name]
        print(f"  类型: {old_config.get('type', 'unknown')}")
        print(f"  主机: {old_config.get('host', 'N/A')}:{old_config.get('port', 'N/A')}")
        print(f"  数据库: {old_config.get('database', 'N/A')}")
        print("\n请输入新的环境名称:\n")
        
        # 循环直到输入不重复的环境名称
        while True:
            env_name = input("环境名称: ").strip()
            if not env_name:
                print("✗ 环境名称不能为空")
                continue
            if env_name in existing_config:
                print(f"⚠ 环境 '{env_name}' 已存在，请选择其他名称")
                continue
            break
    
    if db_type == 'mysql':
        host = input("\n主机地址 [localhost]: ").strip() or "localhost"
        port = input("端口号 [3306]: ").strip() or "3306"
        user = input("用户名 [root]: ").strip() or "root"
    elif db_type == 'postgresql':
        host = input("\n主机地址 [localhost]: ").strip() or "localhost"
        port = input("端口号 [5432]: ").strip() or "5432"
        user = input("用户名 [postgres]: ").strip() or "postgres"
    
    password = input("密码: ").strip()
    database = input("数据库名: ").strip()
    
    if not database:
        print("✗ 数据库名不能为空")
        sys.exit(1)
    
    # 构建新环境配置
    new_env_config = {
        "type": db_type,
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database
    }
    
    # 合并配置
    if config_exists:
        # 保留现有配置，添加或更新环境
        existing_config[env_name] = new_env_config
        # 如果是第一个环境，设置为当前环境
        if 'current' not in existing_config:
            existing_config['current'] = env_name
        config_data = existing_config
        print(f"\n✓ 环境 '{env_name}' 已{'更新' if env_name in [k for k in existing_config.keys() if k != 'current'] else '添加'}")
    else:
        # 新建配置文件
        config_data = {
            "current": env_name,
            env_name: new_env_config
        }
    
    # 写入配置
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 配置文件已保存: {config_path}")
        print("\n当前所有配置:")
        # 不显示密码
        display_config = {}
        for key, value in config_data.items():
            if key == 'current':
                display_config[key] = value
            else:
                display_env = value.copy()
                if 'password' in display_env:
                    display_env['password'] = '***' if display_env['password'] else '(空)'
                display_config[key] = display_env
        print(json.dumps(display_config, indent=2, ensure_ascii=False))
        print("\n正在测试数据库连接...")
        
        # 测试连接
        ensure_driver(db_type)
        config = config_data[env_name].copy()
        config.pop('type', None)  # 移除 type 字段，避免传给数据库驱动
        
        try:
            if db_type == 'mysql':
                config['charset'] = 'utf8mb4'
                connection = pymysql.connect(**config)
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute("SELECT VERSION() as version;")
                    version = cursor.fetchone()
                    print(f"✓ 数据库连接成功 (MySQL {version['version']})")
                connection.close()
            elif db_type == 'postgresql':
                pg_config = {
                    'host': config.get('host', 'localhost'),
                    'port': config.get('port', 5432),
                    'user': config.get('user', 'postgres'),
                    'password': config.get('password', ''),
                    'dbname': config.get('database', '')
                }
                connection = psycopg2.connect(**pg_config)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    print(f"✓ 数据库连接成功 (PostgreSQL {version[0]})")
                connection.close()
        except Exception as e:
            print(f"⚠ 连接测试失败: {e}")
            print("请检查配置是否正确,或重新运行 --init 修改配置")
        
    except Exception as e:
        print(f" 创建配置文件失败: {e}")
        sys.exit(1)


# ============================================
# 导出功能
# ============================================

def export_ddl_to_file(output_dir, output_file=None, exclude_tables=None, env_name=None):
    """
    导出当前数据库的所有表DDL到指定目录
    
    Args:
        output_dir: 输出目录
        output_file: 输出文件名(可选,默认自动生成带时间戳的文件名)
        exclude_tables: 排除的表名列表
        env_name: 数据库环境名称(可选)
    """
    from datetime import datetime
    
    config, env, db_type = load_config(None, env_name)
    
    if db_type != 'mysql':
        print(" 导出DDL功能目前仅支持MySQL数据库")
        sys.exit(1)
    
    ensure_mysql_driver()
    
    # 连接数据库
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        sys.exit(1)
    
    try:
        # 获取所有表名
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.TABLES 
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
        
        # 过滤排除的表
        if exclude_tables:
            tables = [t for t in tables if t not in exclude_tables]
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_file = f"{timestamp}_DDL_export.sql"
        
        output_path = os.path.join(output_dir, output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在导出 {len(tables)} 个表的DDL...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"-- DDL Export from {config['database']}\n")
            f.write(f"-- Exported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, table in enumerate(tables, 1):
                print(f"  [{i}/{len(tables)}] 导出 {table}...")
                with connection.cursor() as cursor:
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    result = cursor.fetchone()
                    if result:
                        create_sql = result[1]
                        # 移除字段级别的字符集声明，保持输出简洁
                        create_sql = strip_column_charset(create_sql)
                        f.write(f"-- {table}\n{create_sql};\n\n")
        
        print(f"\n✓ DDL导出成功: {output_path}")
        print(f"  共导出 {len(tables)} 个表")
        
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        connection.close()


def export_dml_to_file(output_dir, tables, output_file=None, env_name=None):
    """
    导出指定表的数据DML到指定目录
    
    Args:
        output_dir: 输出目录
        tables: 要导出的表名列表
        output_file: 输出文件名(可选,默认自动生成带时间戳的文件名)
        env_name: 数据库环境名称(可选)
    """
    from datetime import datetime
    
    config, env, db_type = load_config(None, env_name)
    
    if db_type != 'mysql':
        print(" 导出DML功能目前仅支持MySQL数据库")
        sys.exit(1)
    
    ensure_mysql_driver()
    
    # 连接数据库
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        sys.exit(1)
    
    try:
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_file = f"{timestamp}_DML_export.sql"
        
        output_path = os.path.join(output_dir, output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在导出 {len(tables)} 个表的数据...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"-- DML Export from {config['database']}\n")
            f.write(f"-- Exported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for table in tables:
                print(f"  导出 {table}...")
                
                # 获取表数据
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM `{table}`")
                    rows = cursor.fetchall()
                    
                    if not rows:
                        print(f"     {table} 没有数据,跳过")
                        continue
                    
                    # 获取字段名
                    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                    columns = [col[0] for col in cursor.fetchall()]
                    
                    field_names = ', '.join([f'`{col}`' for col in columns])
                    
                    # 生成INSERT语句
                    sql_lines = []
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                val_str = str(val).replace("'", "''")
                                values.append(f"'{val_str}'")
                        values_str = ', '.join(values)
                        sql_lines.append(f"  ({values_str})")
                    
                    insert_sql = f"INSERT INTO `{table}` ({field_names}) VALUES\n" + ',\n'.join(sql_lines) + ";\n\n"
                    f.write(f"-- {table}\n{insert_sql}")
        
        print(f"\n✓ DML导出成功: {output_path}")
        
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        connection.close()


def diff_ddl(source_env, target_env, output_dir, output_file=None):
    """
    对比两个环境的DDL差异，生成升级脚本
    
    Args:
        source_env: 源环境名（当前环境）
        target_env: 目标环境名（要升级到的环境）
        output_dir: 输出目录
        output_file: 输出文件名(可选)
    """
    from datetime import datetime
    
    print(f"\n{'='*60}")
    print(f"DDL差异对比: {source_env} -> {target_env}")
    print(f"{'='*60}\n")
    
    # 1. 导出源环境DDL
    print("[1/4] 导出源环境DDL...")
    source_ddl = export_ddl_to_memory(source_env)
    
    # 2. 导出目标环境DDL
    print("[2/4] 导出目标环境DDL...")
    target_ddl = export_ddl_to_memory(target_env)
    
    # 3. 对比差异
    print("[3/4] 对比差异...")
    diff_result = compare_ddl(source_ddl, target_ddl, source_env, target_env)
    
    # 4. 检查是否有实际差异
    added_count = len(diff_result['added_tables'])
    removed_count = len(diff_result['removed_tables'])
    modified_count = len(diff_result['modified_tables'])
    
    if not added_count and not removed_count and not modified_count:
        print(f"\n{'='*60}")
        print(f"✅ 两个环境的表结构完全一致，无需生成升级脚本")
        print(f"{'='*60}\n")
        return
    
    # 5. 生成升级脚本
    print("[4/4] 生成升级脚本...")
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        output_file = f"{timestamp}.sql"
    
    output_path = generate_upgrade_script(diff_result, output_dir, output_file, source_env, target_env)
    
    print(f"\n{'='*60}")
    print(f"✓ 升级脚本已生成: {output_path}")
    print(f"{'='*60}\n")


def export_ddl_to_memory(env_name):
    """
    导出环境DDL到内存（字典格式）
    
    Returns:
        dict: {table_name: create_sql}
    """
    config, env, db_type = load_config(None, env_name)
    
    if db_type != 'mysql':
        print(f"✗ 对比功能目前仅支持MySQL数据库")
        sys.exit(1)
    
    ensure_mysql_driver()
    
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
    except Exception as e:
        print(f"✗ 数据库连接失败 ({env_name}): {e}")
        sys.exit(1)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.TABLES 
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
        
        # 过滤排除的表
        IGNORED_PREFIXES = ('dbmate_', 'schema_migrations')
        tables = [t for t in tables if not any(t.startswith(p) for p in IGNORED_PREFIXES)]
        
        ddl_dict = {}
        for table in tables:
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                result = cursor.fetchone()
                if result:
                    ddl_dict[table] = strip_column_charset(result[1])
        
        print(f"  ✓ {env_name}: {len(ddl_dict)} 个表")
        return ddl_dict
        
    except Exception as e:
        print(f"✗ 导出失败 ({env_name}): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        connection.close()


def strip_column_charset(create_sql):
    """
    移除CREATE TABLE语句中字段级别的CHARACTER SET和COLLATE声明
    
    保留表级别的CHARSET和COLLATE设置，仅移除每个字段定义中的：
    - CHARACTER SET utf8mb4
    - COLLATE utf8mb4_unicode_ci (或其他collation)
    
    示例:
    输入: `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
    输出: `name` varchar(100) DEFAULT NULL
    """
    lines = create_sql.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        # 只处理字段定义行（以反引号开头的行）
        if stripped.startswith('`'):
            # 移除字段级别的 CHARACTER SET xxx
            line = re.sub(r'\s+CHARACTER SET\s+\w+', '', line)
            # 移除字段级别的 COLLATE xxx
            line = re.sub(r'\s+COLLATE\s+\w+', '', line)
        result.append(line)
    return '\n'.join(result)


def normalize_create_table(create_sql):
    """
    标准化CREATE TABLE语句，消除格式差异
    
    处理：
    1. 移除字段顺序差异（SHOW CREATE TABLE的字段顺序可能不同）
    2. 移除索引顺序差异
    3. 统一字符集写法（CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci vs COLLATE utf8mb4_unicode_ci）
    4. 移除多余空格和换行
    """
    # 统一换行符和空格
    sql = create_sql.strip()
    sql = re.sub(r'\s+', ' ', sql)
    
    # 统一字符集写法：如果有COLLATE但没有CHARACTER SET，补充CHARACTER SET
    # 匹配: varchar(50) COLLATE utf8mb4_unicode_ci
    # 替换为: varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    sql = re.sub(
        r'(varchar\(\d+\))\s+(COLLATE\s+utf8mb4_unicode_ci)',
        r'\1 CHARACTER SET utf8mb4 \2',
        sql
    )
    
    # 统一字符集写法：移除多余的 CHARACTER SET（如果已有COLLATE）
    # 匹配: varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    # 保持原样（标准化后一致）
    
    return sql


def compare_ddl(source_ddl, target_ddl, source_env, target_env):
    """
    对比两个环境的DDL差异
    
    Returns:
        dict: {
            'added_tables': [table_names],  # 目标环境新增的表
            'removed_tables': [table_names],  # 目标环境删除的表
            'modified_tables': {table_name: {'source': sql, 'target': sql}},  # 修改的表
            'alter_statements': {table_name: [sql]},  # 生成的ALTER语句
        }
    """
    source_tables = set(source_ddl.keys())
    target_tables = set(target_ddl.keys())
    
    added_tables = sorted(target_tables - source_tables)
    removed_tables = sorted(source_tables - target_tables)
    common_tables = source_tables & target_tables
    
    modified_tables = {}
    alter_statements = {}
    
    for table in sorted(common_tables):
        # 标准化后再对比，避免格式差异导致的误判
        source_normalized = normalize_create_table(source_ddl[table])
        target_normalized = normalize_create_table(target_ddl[table])
        
        if source_normalized != target_normalized:
            # 生成ALTER语句
            alter_sqls = generate_alter_statements(source_ddl[table], target_ddl[table], table)
            if alter_sqls:
                modified_tables[table] = {
                    'source': source_ddl[table],
                    'target': target_ddl[table]
                }
                alter_statements[table] = alter_sqls
    
    print(f"  新增表: {len(added_tables)} 个")
    if added_tables:
        for t in added_tables:
            print(f"    + {t}")
    
    print(f"  删除表: {len(removed_tables)} 个")
    if removed_tables:
        for t in removed_tables:
            print(f"    - {t}")
    
    print(f"  修改表: {len(modified_tables)} 个")
    print(f"  生成ALTER语句: {len(alter_statements)} 个表")
    
    return {
        'added_tables': added_tables,
        'removed_tables': removed_tables,
        'modified_tables': modified_tables,
        'target_ddl': target_ddl,
        'alter_statements': alter_statements
    }


def parse_create_table(create_sql):
    """
    解析CREATE TABLE语句，提取表结构信息
    
    Returns:
        dict: {
            'columns': {col_name: col_def},
            'indexes': [index_def],
            'primary_key': pk_def,
            'table_options': options
        }
    """
    result = {
        'columns': {},
        'indexes': [],
        'primary_key': None,
        'table_options': ''
    }
    
    # 提取表名后的所有内容（注意：MySQL SHOW CREATE TABLE返回的DDL可能没有分号）
    match = re.search(r'CREATE TABLE.*?\((.*)\)\s*(ENGINE.*?)\s*;?\s*$', create_sql, re.DOTALL)
    if not match:
        return result
    
    body = match.group(1)
    result['table_options'] = match.group(2)
    
    # 分割定义项（需要处理括号内的逗号和字符串内的逗号）
    items = []
    current = ''
    paren_depth = 0
    in_string = False
    string_char = None
    
    i = 0
    while i < len(body):
        char = body[i]
        
        # 处理字符串（单引号包裹）
        if char == "'" and (i == 0 or body[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = "'"
            elif string_char == "'":
                in_string = False
                string_char = None
            current += char
        # 处理括号深度（只在字符串外）
        elif not in_string:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0:
                items.append(current.strip())
                current = ''
            else:
                current += char
        else:
            current += char
        
        i += 1
    
    if current.strip():
        items.append(current.strip())
    
    # 分类处理
    for item in items:
        item_upper = item.upper().strip()
        
        if item_upper.startswith('PRIMARY KEY'):
            result['primary_key'] = item
        elif item_upper.startswith('KEY ') or item_upper.startswith('UNIQUE KEY') or item_upper.startswith('INDEX '):
            result['indexes'].append(item)
        elif item_upper.startswith('CONSTRAINT'):
            result['indexes'].append(item)
        else:
            # 字段定义
            col_match = re.match(r'`?(\w+)`?\s+(.*)', item, re.DOTALL)
            if col_match:
                col_name = col_match.group(1)
                result['columns'][col_name] = item
    
    return result


def generate_alter_statements(source_sql, target_sql, table_name):
    """
    生成ALTER TABLE语句
    
    Returns:
        list: ALTER语句列表（按安全顺序：删除索引 → 删除列 → 修改列 → 添加列 → 添加索引 → 主键 → 表选项）
    """
    source_struct = parse_create_table(source_sql)
    target_struct = parse_create_table(target_sql)
    
    alter_sqls = []
    
    # 1. 先删除索引（避免后续操作冲突）
    source_indexes = set(source_struct['indexes'])
    target_indexes = set(target_struct['indexes'])
    for idx in sorted(source_indexes - target_indexes):
        # 提取索引名
        idx_match = re.search(r'(?:KEY|INDEX)\s+`(\w+)`', idx)
        if idx_match:
            idx_name = idx_match.group(1)
            alter_sqls.append(f"ALTER TABLE `{table_name}` DROP INDEX `{idx_name}`;")
    
    # 2. 删除字段
    source_cols = set(source_struct['columns'].keys())
    target_cols = set(target_struct['columns'].keys())
    for col in sorted(source_cols - target_cols):
        alter_sqls.append(f"ALTER TABLE `{table_name}` DROP COLUMN `{col}`;")
    
    # 3. 修改字段（对比字段定义）
    for col in sorted(source_cols & target_cols):
        # 标准化后对比，避免字符集写法差异导致的误判
        source_col_normalized = normalize_create_table(source_struct['columns'][col])
        target_col_normalized = normalize_create_table(target_struct['columns'][col])
        
        if source_col_normalized != target_col_normalized:
            col_def = target_struct['columns'][col]
            alter_sqls.append(f"ALTER TABLE `{table_name}` MODIFY COLUMN {col_def};")
    
    # 4. 新增字段
    for col in sorted(target_cols - source_cols):
        col_def = target_struct['columns'][col]
        alter_sqls.append(f"ALTER TABLE `{table_name}` ADD COLUMN {col_def};")
    
    # 5. 添加索引
    for idx in sorted(target_indexes - source_indexes):
        alter_sqls.append(f"ALTER TABLE `{table_name}` ADD {idx};")
    
    # 6. 对比主键
    if source_struct['primary_key'] != target_struct['primary_key']:
        if source_struct['primary_key']:
            alter_sqls.append(f"ALTER TABLE `{table_name}` DROP PRIMARY KEY;")
        if target_struct['primary_key']:
            alter_sqls.append(f"ALTER TABLE `{table_name}` ADD {target_struct['primary_key']};")
    
    # 7. 对比表选项（ENGINE, CHARSET等）
    if source_struct['table_options'] != target_struct['table_options']:
        # 提取关键选项
        source_opts = extract_table_options(source_struct['table_options'])
        target_opts = extract_table_options(target_struct['table_options'])
        
        changes = []
        for opt_name, opt_value in target_opts.items():
            if source_opts.get(opt_name) != opt_value:
                changes.append(f"{opt_name} = {opt_value}")
        
        if changes:
            alter_sqls.append(f"ALTER TABLE `{table_name}` {' '.join(changes)};")
    
    return alter_sqls


def extract_table_options(options_str):
    """
    提取表选项
    
    Returns:
        dict: {option_name: option_value}
    """
    opts = {}
    
    # ENGINE
    match = re.search(r'ENGINE=(\w+)', options_str)
    if match:
        opts['ENGINE'] = match.group(1)
    
    # DEFAULT CHARSET
    match = re.search(r'DEFAULT CHARSET=(\w+)', options_str)
    if match:
        opts['DEFAULT CHARSET'] = match.group(1)
    
    # COLLATE - 跳过（环境间默认排序规则差异，非结构变更）
    # AUTO_INCREMENT - 跳过（自增值随数据变化，非结构变更）
    
    # COMMENT
    match = re.search(r"COMMENT='([^']*)'", options_str)
    if match:
        opts['COMMENT'] = f"'{match.group(1)}'"
    
    return opts


def generate_upgrade_script(diff_result, output_dir, output_file, source_env, target_env):
    """
    生成升级脚本
    
    Args:
        diff_result: 差异结果
        output_dir: 输出目录
        output_file: 输出文件名
        source_env: 源环境
        target_env: 目标环境
    
    Returns:
        str: 输出文件路径
    """
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 文件头
        f.write(f"-- DDL Upgrade Script: {source_env} -> {target_env}\n")
        f.write(f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Source: {source_env}环境\n")
        f.write(f"-- Target: {target_env}环境\n")
        f.write(f"--\n")
        
        # 统计信息
        added_count = len(diff_result['added_tables'])
        removed_count = len(diff_result['removed_tables'])
        modified_count = len(diff_result['modified_tables'])
        
        f.write(f"-- 差异统计:\n")
        f.write(f"--   新增表: {added_count} 个\n")
        f.write(f"--   删除表: {removed_count} 个\n")
        f.write(f"--   修改表: {modified_count} 个\n")
        f.write(f"\n")
        
        # migrate:up
        f.write("-- migrate:up\n\n")
        
        # 1. 新增表
        if diff_result['added_tables']:
            f.write("-- ============================================\n")
            f.write("-- 1. 新增表\n")
            f.write("-- ============================================\n\n")
            for table in diff_result['added_tables']:
                create_sql = diff_result['target_ddl'][table]
                f.write(f"-- {table}\n{create_sql};\n\n")
        
        # 2. 修改表（生成ALTER语句）
        if diff_result['alter_statements']:
            section_num = 2 if diff_result['added_tables'] else 1
            f.write("-- ============================================\n")
            f.write(f"-- {section_num}. 修改表（自动生成的ALTER语句）\n")
            f.write("-- ============================================\n")
            f.write("-- 注意：以下语句如果执行失败（如索引/列已不存在），可手动跳过\n\n")
            
            for table, alter_sqls in diff_result['alter_statements'].items():
                f.write(f"-- 表: {table}\n")
                for sql in alter_sqls:
                    f.write(f"{sql}\n")
                f.write("\n")
        
        if not added_count and not removed_count and not modified_count:
            f.write("-- ✅ 两个环境的表结构完全一致，无需升级\n\n")
        
        # migrate:down
        f.write("-- migrate:down\n")
        f.write("-- 请在此处手动编写回滚SQL\n")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description='SQL 执行器 (支持 MySQL 和 PostgreSQL)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "SELECT * FROM users LIMIT 10;"
  %(prog)s --env dev "SELECT COUNT(*) FROM orders;"
  %(prog)s --file query.sql
  %(prog)s --config /path/to/config.json "SELECT 1;"
  %(prog)s --transaction "INSERT INTO ..." "UPDATE ..." "DELETE ..."
  %(prog)s --init  # 交互式配置数据库连接
        """
    )
    
    parser.add_argument('sql', nargs='*', help='要执行的 SQL 语句(支持多条)')
    parser.add_argument('--file', '-f', help='SQL 文件路径')
    parser.add_argument('--env', '-e', help='数据库环境名称')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--max-rows', '-m', type=int, default=1000, 
                       help='最大返回行数(默认: 1000)')
    parser.add_argument('--json', '-j', action='store_true', 
                       help='以 JSON 格式输出结果')
    parser.add_argument('--transaction', '-t', action='store_true',
                       help='启用事务模式(多条 SQL 在同一事务中执行)')
    parser.add_argument('--init', action='store_true',
                       help='交互式配置数据库连接')
    parser.add_argument('--export-ddl', metavar='DIR',
                       help='导出DDL到指定目录')
    parser.add_argument('--export-dml', metavar='DIR',
                       help='导出DML到指定目录(需要配合--tables参数)')
    parser.add_argument('--tables', nargs='+',
                       help='要导出DML的表名列表')
    parser.add_argument('--exclude-tables', nargs='+', default=['schema_migrations'],
                       help='导出DDL时排除的表名(默认排除schema_migrations)')
    parser.add_argument('--output-file', '-o',
                       help='输出文件名(可选)')
    parser.add_argument('--diff-ddl', metavar='ENV',
                       help='对比当前环境与目标环境的DDL差异，生成升级脚本(指定目标环境名)')
    parser.add_argument('--output-dir', '-d',
                       help='diff-ddl输出目录(默认: sql/dbmate_scm)')
    
    args = parser.parse_args()
    
    # 仅初始化配置
    if args.init:
        config_path = os.path.expanduser(args.config if args.config else '~/.config/dba/config.json')
        create_config(config_path)
        return
    
    # 导出DDL
    if args.export_ddl:
        output_dir = os.path.expanduser(args.export_ddl)
        exclude_tables = args.exclude_tables if args.exclude_tables else []
        # 使用 --env 参数指定的环境，如果未指定则使用默认环境
        export_ddl_to_file(output_dir, args.output_file, exclude_tables, args.env)
        return
    
    # 导出DML
    if args.export_dml:
        if not args.tables:
            print(" 导出DML需要指定--tables参数")
            sys.exit(1)
        output_dir = os.path.expanduser(args.export_dml)
        # 使用 --env 参数指定的环境，如果未指定则使用默认环境
        export_dml_to_file(output_dir, args.tables, args.output_file, args.env)
        return
    
    # DDL差异对比
    if args.diff_ddl:
        target_env = args.diff_ddl
        source_env = args.env or 'local'  # 默认使用当前环境
        output_dir = os.path.expanduser(args.output_dir if args.output_dir else 'sql/dbmate_scm')
        diff_ddl(source_env, target_env, output_dir, args.output_file)
        return
    
    if not args.sql and not args.file:
        parser.print_help()
        sys.exit(1)
    
    # 加载配置(自动处理依赖和配置缺失)
    config, env, db_type = load_config(args.config, args.env)
    
    if not args.json:
        print(f"环境: {env}")
        print(f"数据库类型: {db_type}")
        print(f"数据库: {config.get('database', 'N/A')}")
    
    # 执行 SQL
    if args.file:
        results = execute_sql_file(args.file, config, args.max_rows, db_type)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    elif args.transaction:
        # 事务模式(支持单条或多条 SQL)
        if not args.sql:
            print("错误: 事务模式需要提供 SQL 语句")
            sys.exit(1)
        result = execute_transaction(args.sql, config, args.max_rows, db_type)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        # 单条 SQL 模式
        if len(args.sql) == 1:
            # 检查单条参数中是否包含多个语句(按分号分隔)
            sql_content = args.sql[0].strip()
            
            # 移除注释
            sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
            sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
            
            # 按分号分割语句
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            if len(statements) > 1:
                # 多条语句,使用事务模式执行
                if not args.json:
                    print(f"\n检测到 {len(statements)} 条 SQL 语句,使用事务模式执行\n")
                result = execute_transaction(statements, config, args.max_rows, db_type)
                if args.json:
                    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
            else:
                # 单条语句
                result = execute_sql(args.sql[0], config, args.max_rows, db_type)
                if args.json:
                    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            # 多条 SQL 但不使用事务(逐条执行)
            print(f"\n执行 {len(args.sql)} 条 SQL(非事务模式)\n")
            results = []
            for i, sql in enumerate(args.sql, 1):
                print(f"\n{'='*60}")
                print(f"[{i}/{len(args.sql)}] {sql[:80]}{'...' if len(sql) > 80 else ''}")
                print(f"{'='*60}")
                result = execute_sql(sql, config, args.max_rows, db_type)
                results.append(result)
            
            if args.json:
                print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main()
