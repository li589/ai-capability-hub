#!/usr/bin/env python3
"""诊断回归测试中 C7/G3 的实际输出格式"""
import sys, json
sys.path.insert(0, 'tools')
from orchestrator import _p7_check_c7
from gate_checker import gate_g3_business_flow_coverage

p5 = [
    {'id': 'req-TP-001', 'status': 'active', 'category': 'main_flow'},
    {'id': 'req-TP-002', 'status': 'active', 'category': 'main_flow'},
    {'id': 'req-TP-003', 'status': 'active', 'category': 'main_flow'},
]

case = [{
    'case_id': 'REQ-20260622-001-TC-001',
    'source_test_point': 'req-TP-002',
    'title': 'TC',
    'steps': '1. 导航\n2. 点击',
    'expected_results': '1. 加载\n2. 完成',
    'is_smoke': '是',
    'priority': 'P0'
}]

print("=== C7 完整输出 ===")
r_c7 = _p7_check_c7(case, p5)
print(json.dumps(r_c7, ensure_ascii=False, indent=2, default=str))

print("\n=== G3 完整输出 ===")
r_g3 = gate_g3_business_flow_coverage(case, p5)
print(json.dumps(r_g3, ensure_ascii=False, indent=2, default=str))
