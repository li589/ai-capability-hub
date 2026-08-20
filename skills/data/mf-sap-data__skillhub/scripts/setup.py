#!/usr/bin/env python3
"""
SAP 数据查询 Skill 安装脚本
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
============================================================
                  SAP 数据查询 Skill 安装
                明辉集团内部工具 - v1.0.0
============================================================
"""
    print(banner)

def check_requirements():
    """检查系统要求"""
    print("检查系统要求...")
    
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("✗ 需要 Python 3.7 或更高版本")
        return False
    
    print(f"✓ Python 版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # 检查必要命令
    required_commands = ["pip", "python"]
    for cmd in required_commands:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print(f"✓ 命令可用: {cmd}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ 命令不可用: {cmd}")
            return False
    
    return True

def install_dependencies():
    """安装依赖包"""
    print("\n安装依赖包...")
    
    requirements = [
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "openpyxl>=3.0.0",
        "python-dotenv>=0.21.0"
    ]
    
    for package in requirements:
        try:
            print(f"安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ 安装成功: {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ 安装失败: {package}")
            print(f"错误信息: {e}")
            return False
    
    return True

def setup_directories():
    """设置目录结构"""
    print("\n设置目录结构...")
    
    directories = [
        "config",
        "logs",
        "exports",
        "examples",
        "tests",
        "temp"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ 创建目录: {directory}")
        except Exception as e:
            print(f"✗ 创建目录失败 {directory}: {e}")
            return False
    
    return True

def create_config_files():
    """创建配置文件"""
    print("\n创建配置文件...")
    
    # 创建默认配置文件
    default_config = {
        "api_endpoints": {
            "auth": "https://info02.mingfaigroup.com/api/account/agent/getticket",
            "bapi": "https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke",
            "table_columns": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns",
            "table_data": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata"
        },
        "app_info": {
            "app_name": "mf.portal.agent",
            "app_version": "1.0"
        },
        "performance": {
            "timeout": 60,
            "max_page_size": 10000,
            "default_page_size": 1000,
            "max_pages": 100
        },
        "formatting": {
            "material_code_length": 18,
            "production_order_length": 12,
            "date_format": "YYYYMMDD"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/sap_query.log",
            "max_size_mb": 10,
            "backup_count": 5
        }
    }
    
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "settings.json")
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"✓ 创建配置文件: {config_file}")
    except Exception as e:
        print(f"✗ 创建配置文件失败: {e}")
        return False
    
    # 创建环境变量示例
    env_example = """# SAP 数据查询 Skill 环境变量配置
# 复制此文件为 .env 并修改配置

# API 端点配置
# SAP_AUTH_ENDPOINT=https://info02.mingfaigroup.com/api/account/agent/getticket
# SAP_BAPI_ENDPOINT=https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke
# SAP_TABLE_COLUMNS_ENDPOINT=https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns
# SAP_TABLE_DATA_ENDPOINT=https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata

# 应用信息
SAP_APP_NAME=mf.portal.agent
SAP_APP_VERSION=1.0

# 性能配置
SAP_TIMEOUT=60
SAP_MAX_PAGE_SIZE=10000
SAP_DEFAULT_PAGE_SIZE=1000
SAP_MAX_PAGES=100

# 日志配置
SAP_LOG_LEVEL=INFO
SAP_LOG_FILE=logs/sap_query.log

# 安全配置（可选）
# SAP_ENCRYPT_SENSITIVE_DATA=true
# SAP_MASK_ERRORS=true
"""
    
    try:
        with open(".env.example", 'w', encoding='utf-8') as f:
            f.write(env_example)
        print("✓ 创建环境变量示例: .env.example")
    except Exception as e:
        print(f"✗ 创建环境变量示例失败: {e}")
        return False
    
    return True

def create_example_files():
    """创建示例文件"""
    print("\n创建示例文件...")
    
    examples_dir = "examples"
    os.makedirs(examples_dir, exist_ok=True)
    
    # 快速开始示例
    quickstart_example = '''#!/usr/bin/env python3
"""
SAP 数据查询 Skill 快速开始示例
"""

from sap_data_query_skill import SAPDataQuerySkill

def main():
    print("SAP 数据查询 Skill 快速开始")
    print("=" * 50)
    
    # 1. 创建 Skill 实例
    print("1. 创建 Skill 实例...")
    skill = SAPDataQuerySkill()
    
    # 2. 用户认证
    print("\\n2. 用户认证...")
    auth_result = skill.authenticate()
    
    if not auth_result["success"]:
        print(f"认证失败: {auth_result['error']}")
        return
    
    print(f"认证成功! 用户: {auth_result.get('user_name')}")
    
    # 3. 查询表数据
    print("\\n3. 查询物料主数据...")
    result = skill.query_table(
        table_name="MARA",
        fields=["MATNR", "MAKTX", "MEINS", "MATKL"],
        page_size=10
    )
    
    if result["success"]:
        print(f"查询成功! 共 {result['statistics']['row_count']} 行数据")
        print(f"返回 {result['statistics']['query_rows']} 行")
        
        print("\\n查询结果:")
        for i, row in enumerate(result["data"][:5], 1):
            print(f"{i}. {row.get('MATNR')} - {row.get('MAKTX')}")
        
        if result["statistics"]["query_rows"] > 5:
            print(f"... 还有 {result['statistics']['query_rows'] - 5} 行数据")
    else:
        print(f"查询失败: {result['error']}")
    
    # 4. 获取 Skill 状态
    print("\\n4. Skill 状态:")
    status = skill.get_status()
    print(f"版本: {status.get('version')}")
    print(f"认证状态: {status.get('authenticated')}")
    print(f"查询历史: {status.get('query_history_count')} 次")
    
    print("\\n快速开始示例完成!")

if __name__ == "__main__":
    main()
'''
    
    try:
        quickstart_file = os.path.join(examples_dir, "quickstart.py")
        with open(quickstart_file, 'w', encoding='utf-8') as f:
            f.write(quickstart_example)
        print(f"✓ 创建快速开始示例: {quickstart_file}")
        
        # 设置执行权限
        os.chmod(quickstart_file, 0o755)
        
    except Exception as e:
        print(f"✗ 创建示例文件失败: {e}")
        return False
    
    return True

def verify_installation():
    """验证安装"""
    print("\n验证安装...")
    
    try:
        # 添加当前目录到Python路径
        sys.path.insert(0, os.getcwd())
        
        # 尝试导入 Skill
        from sap_data_query_skill import SAPDataQuerySkill
        
        # 创建 Skill 实例
        skill = SAPDataQuerySkill()
        
        # 获取状态
        status = skill.get_status()
        
        print(f"Skill 状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        if status.get("config_loaded"):
            print("✓ Skill 加载成功")
            return True
        else:
            print("✗ Skill 配置加载失败")
            return False
            
    except ImportError as e:
        print(f"✗ 导入 Skill 失败: {e}")
        print("请确保在正确的目录中运行安装脚本")
        return False
        
    except Exception as e:
        print(f"✗ Skill 验证失败: {e}")
        return False

def print_next_steps():
    """打印下一步操作"""
    print("\n" + "=" * 60)
    print("安装完成！")
    print("=" * 60)
    
    print("\n下一步操作:")
    print("1. 配置环境变量:")
    print("   cp .env.example .env")
    print("   # 编辑 .env 文件配置 API 端点")
    
    print("\n2. 测试连接:")
    print("   python scripts/test_connection.py")
    
    print("\n3. 运行示例:")
    print("   python examples/quickstart.py")
    
    print("\n4. 查看文档:")
    print("   - README.md: 快速开始指南")
    print("   - SKILL.md: 详细功能说明")
    print("   - references/: API 规范和格式标准")
    
    print("\n5. 开始使用:")
    print("   from sap_data_query_skill import SAPDataQuerySkill")
    print("   skill = SAPDataQuerySkill()")
    print("   auth_result = skill.authenticate()")
    
    print("\n6. 常用命令:")
    print("   # 测试认证")
    print("   python -c \"from sap_data_query_skill import SAPDataQuerySkill; s=SAPDataQuerySkill(); print(s.authenticate())\"")
    
    print("   # 查询物料")
    print("   python -c \"from sap_data_query_skill import SAPDataQuerySkill; s=SAPDataQuerySkill(); s.authenticate(); r=s.query_table('MARA', page_size=5); print(r['statistics'])\"")
    
    print("\n支持与反馈:")
    print("如有问题，请查看文档或联系技术支持")
    print("邮箱: it-support@minghuigroup.com")
    print("=" * 60)

def main():
    """主函数"""
    print_banner()
    
    # 检查要求
    if not check_requirements():
        print("\n系统要求检查失败，请先满足要求")
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("\n依赖安装失败")
        sys.exit(1)
    
    # 设置目录
    if not setup_directories():
        print("\n目录设置失败")
        sys.exit(1)
    
    # 创建配置文件
    if not create_config_files():
        print("\n配置文件创建失败")
        sys.exit(1)
    
    # 创建示例文件
    if not create_example_files():
        print("\n示例文件创建失败")
        sys.exit(1)
    
    # 验证安装
    if not verify_installation():
        print("\n安装验证失败")
        sys.exit(1)
    
    # 打印下一步
    print_next_steps()

if __name__ == "__main__":
    main()