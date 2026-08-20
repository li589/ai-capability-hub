#!/usr/bin/env python3
"""
SAP 数据查询 Skill 连接测试
测试与SAP系统的连接和认证
"""

import sys
import json
from pathlib import Path

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sap_data_query_skill import SAPDataQuerySkill

def test_authentication():
    """测试认证功能"""
    print("测试认证功能...")
    print("=" * 50)
    
    skill = SAPDataQuerySkill()
    
    # 测试1: 交互式认证
    print("\\n1. 交互式认证测试")
    print("请按照提示输入身份证后六位")
    
    try:
        auth_result = skill.authenticate()
        
        if auth_result["success"]:
            print(f"✓ 认证成功!")
            print(f"   用户: {auth_result.get('user_name')}")
            print(f"   工号: {auth_result.get('work_code')}")
            print(f"   票据: {auth_result.get('ticket')[:20]}...")
            print(f"   有效期: {auth_result.get('expires_at')}")
            return True
        else:
            print(f"✗ 认证失败: {auth_result.get('error')}")
            print(f"   错误类型: {auth_result.get('error_type')}")
            print(f"   建议: {auth_result.get('suggestion')}")
            return False
            
    except KeyboardInterrupt:
        print("\\n认证已取消")
        return False
    except Exception as e:
        print(f"✗ 认证异常: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("\\n2. 测试配置加载...")
    
    skill = SAPDataQuerySkill()
    status = skill.get_status()
    
    if status.get("config_loaded"):
        print("✓ 配置加载成功")
        
        # 显示配置摘要
        from sap_data_query_skill.config.settings import get_config_summary
        from sap_data_query_skill.config.settings import SAPConfig
        
        config = SAPConfig()
        summary = get_config_summary(config)
        
        print("配置摘要:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return True
    else:
        print("✗ 配置加载失败")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\\n3. 测试API端点...")
    
    from sap_data_query_skill.config.settings import SAPConfig
    
    config = SAPConfig()
    
    print("验证API端点可达性...")
    results = config.validate_endpoints()
    
    all_success = True
    for endpoint, success in results.items():
        if success:
            print(f"✓ {endpoint}: 可达")
        else:
            print(f"✗ {endpoint}: 不可达")
            all_success = False
    
    return all_success

def test_query_builder():
    """测试查询构建器"""
    print("\\n4. 测试查询构建器...")
    
    from sap_data_query_skill.core.query_builder import SAPQueryBuilder
    
    builder = SAPQueryBuilder()
    
    # 测试物料条码格式化
    test_cases = [
        ("1234", "000000000000001234"),
        ("001234", "000000000000001234"),
        ("ABC123", "ABC123"),
        ("", "")
    ]
    
    print("测试物料条码格式化:")
    for input_val, expected in test_cases:
        result = builder.format_material_code(input_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_val}' -> '{result}' (期望: '{expected}')")
    
    # 测试生产订单号格式化
    test_cases = [
        ("5678", "000000005678"),
        ("005678", "000000005678"),
        ("PO5678", "PO5678"),
        ("", "")
    ]
    
    print("\\n测试生产订单号格式化:")
    for input_val, expected in test_cases:
        result = builder.format_production_order(input_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_val}' -> '{result}' (期望: '{expected}')")
    
    # 测试意图分析
    print("\\n测试意图分析:")
    test_intents = [
        ("查询2024年创建的原材料物料", "MARA"),
        ("获取最近30天的生产订单", "AUFK"),
        ("统计销售订单数量", "VBAK")
    ]
    
    for intent, table in test_intents:
        analysis = builder.analyze_query_intent(intent, table)
        print(f"  意图: '{intent}'")
        print(f"  识别关键词: {analysis.get('keywords')}")
        print(f"  查询类型: {analysis.get('query_type')}")
    
    return True

def test_skill_functionality():
    """测试Skill功能"""
    print("\\n5. 测试Skill功能...")
    
    skill = SAPDataQuerySkill()
    
    # 测试状态获取
    status = skill.get_status()
    print(f"Skill状态: {json.dumps(status, ensure_ascii=False)}")
    
    # 测试参数验证
    test_params = {
        "material_code": "1234",
        "order_number": "5678",
        "date": "2024-04-22"
    }
    
    print("\\n测试参数验证:")
    validation = skill.validate_query_params(test_params)
    print(f"验证结果: {json.dumps(validation, ensure_ascii=False)}")
    
    return True

def run_all_tests():
    """运行所有测试"""
    print("SAP 数据查询 Skill 连接测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行测试
    tests = [
        ("配置加载", test_config_loading),
        ("API端点", test_api_endpoints),
        ("查询构建器", test_query_builder),
        ("Skill功能", test_skill_functionality)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\\n{test_name}测试:")
            success = test_func()
            test_results.append((test_name, success))
        except Exception as e:
            print(f"✗ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 显示测试结果
    print("\\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in test_results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\\n" + "=" * 60)
    if all_passed:
        print("所有测试通过！Skill 可以正常使用。")
        print("\\n下一步:")
        print("1. 运行认证测试: python -c \"from sap_data_query_skill import SAPDataQuerySkill; s=SAPDataQuerySkill(); print(s.authenticate())\"")
        print("2. 运行示例: python examples/quickstart.py")
    else:
        print("部分测试失败，请检查配置和网络连接。")
        print("\\n常见问题:")
        print("1. 检查 .env 文件配置")
        print("2. 检查网络连接")
        print("3. 检查 Python 依赖")
    
    return all_passed

def quick_test():
    """快速测试"""
    print("快速连接测试...")
    
    skill = SAPDataQuerySkill()
    
    # 测试配置
    status = skill.get_status()
    if not status.get("config_loaded"):
        print("✗ 配置加载失败")
        return False
    
    print("✓ 配置加载成功")
    
    # 测试API端点
    from sap_data_query_skill.config.settings import SAPConfig
    config = SAPConfig()
    endpoints = config.validate_endpoints()
    
    reachable = sum(1 for success in endpoints.values() if success)
    print(f"✓ API端点: {reachable}/{len(endpoints)} 个可达")
    
    return reachable > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SAP 数据查询 Skill 连接测试")
    parser.add_argument("--quick", action="store_true", help="快速测试")
    parser.add_argument("--auth", action="store_true", help="仅测试认证")
    
    args = parser.parse_args()
    
    if args.quick:
        success = quick_test()
        sys.exit(0 if success else 1)
    elif args.auth:
        success = test_authentication()
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)