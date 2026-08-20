#!/usr/bin/env python3
"""
冒烟测试脚本
验证修复后的 Skill 文件是否可用
"""

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Dict, List


def check_skill_markdown(skill_dir: str) -> Dict:
    """检查 SKILL.md 文件格式"""
    skill_dir = Path(skill_dir)
    skill_md = skill_dir / "SKILL.md"
    
    result = {
        "name": "SKILL.md 格式检查",
        "status": "pass",
        "details": [],
    }
    
    if not skill_md.exists():
        result["status"] = "fail"
        result["details"].append("SKILL.md 文件不存在")
        return result
    
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查 YAML 前言区
    if not content.startswith("---"):
        result["status"] = "fail"
        result["details"].append("缺少 YAML 前言区")
    else:
        result["details"].append("YAML 前言区存在")
    
    # 检查必需字段
    required_fields = ["name", "description"]
    for field in required_fields:
        pattern = f"^{field}:"
        if re.search(pattern, content, re.MULTILINE):
            result["details"].append(f"字段 {field} 存在")
        else:
            result["status"] = "fail"
            result["details"].append(f"缺少必需字段: {field}")
    
    return result


def check_python_syntax(file_path: Path) -> Dict:
    """检查 Python 文件语法"""
    result = {
        "file": str(file_path),
        "status": "pass",
        "details": [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        result["details"].append("Python 语法正确")
    except SyntaxError as e:
        result["status"] = "fail"
        result["details"].append(f"语法错误: {e}")
    except Exception as e:
        result["status"] = "error"
        result["details"].append(f"读取错误: {e}")
    
    return result


def check_all_scripts(skill_dir: str) -> Dict:
    """检查所有 Python 脚本"""
    skill_dir = Path(skill_dir)
    scripts_dir = skill_dir / "scripts"
    
    result = {
        "name": "脚本语法检查",
        "status": "pass",
        "details": [],
        "scripts": [],
    }
    
    if not scripts_dir.exists():
        result["details"].append("scripts 目录不存在")
        return result
    
    py_files = list(scripts_dir.glob("*.py"))
    
    if not py_files:
        result["details"].append("未发现 Python 脚本")
        return result
    
    for py_file in py_files:
        check_result = check_python_syntax(py_file)
        result["scripts"].append(check_result)
        
        if check_result["status"] != "pass":
            result["status"] = "fail"
            result["details"].append(f"{py_file.name}: {check_result['details'][0]}")
        else:
            result["details"].append(f"{py_file.name}: 语法正确")
    
    return result


def check_references(skill_dir: str) -> Dict:
    """检查引用完整性"""
    skill_dir = Path(skill_dir)
    references_dir = skill_dir / "references"
    
    result = {
        "name": "引用完整性检查",
        "status": "pass",
        "details": [],
    }
    
    # 读取 SKILL.md
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result["status"] = "fail"
        result["details"].append("SKILL.md 不存在")
        return result
    
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取引用链接
    ref_links = re.findall(r'\[([^\]]+)\]\((references/[^)]+)\)', content)
    
    if not ref_links:
        result["details"].append("未发现引用链接")
        return result
    
    # 检查每个引用是否存在
    for link_text, link_path in ref_links:
        full_path = skill_dir / link_path
        if full_path.exists():
            result["details"].append(f"✓ {link_text} ({link_path})")
        else:
            result["status"] = "fail"
            result["details"].append(f"✗ {link_text} ({link_path}) 不存在")
    
    return result


def check_directory_structure(skill_dir: str) -> Dict:
    """检查目录结构"""
    skill_dir = Path(skill_dir)
    
    result = {
        "name": "目录结构检查",
        "status": "pass",
        "details": [],
    }
    
    # 检查必需目录
    required_items = ["SKILL.md"]
    for item in required_items:
        item_path = skill_dir / item
        if item_path.exists():
            result["details"].append(f"✓ {item} 存在")
        else:
            result["status"] = "fail"
            result["details"].append(f"✗ {item} 不存在")
    
    # 检查可选目录
    optional_dirs = ["scripts", "references", "assets"]
    for dir_name in optional_dirs:
        dir_path = skill_dir / dir_name
        if dir_path.exists():
            result["details"].append(f"  {dir_name}/ 存在")
    
    return result


def check_for_remaining_risks(skill_dir: str) -> Dict:
    """检查是否仍有明显的安全风险"""
    skill_dir = Path(skill_dir)
    
    result = {
        "name": "残留风险检查",
        "status": "pass",
        "details": [],
        "warnings": [],
    }
    
    # 高风险模式
    high_risk_patterns = [
        (r"eval\s*\(", "eval() 调用"),
        (r"exec\s*\(", "exec() 调用"),
        (r"__import__\s*\(", "__import__() 调用"),
        (r"os\.system\s*\(", "os.system() 调用"),
        (r"pickle\.(loads|load)\s*\(", "pickle 反序列化"),
    ]
    
    # 扫描 Python 文件
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern, desc in high_risk_patterns:
                if re.search(pattern, content):
                    result["status"] = "warning"
                    result["warnings"].append(f"{py_file.name}: 发现 {desc}")
    
    if result["warnings"]:
        result["details"].append("发现潜在风险（请人工审查）")
        for warning in result["warnings"]:
            result["details"].append(f"  ! {warning}")
    else:
        result["details"].append("未发现明显的高风险模式")
    
    return result


def generate_test_report(results: List[Dict], output_dir: str) -> str:
    """生成测试报告"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 统计结果
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    warnings = sum(1 for r in results if r["status"] == "warning")
    
    report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "overall_status": "pass" if failed == 0 else "fail",
        },
        "tests": results,
    }
    
    report_file = output_dir / "smoke-test-report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return str(report_file)


def print_test_summary(results: List[Dict]):
    """打印测试摘要"""
    print("\n" + "=" * 60)
    print("冒烟测试摘要")
    print("=" * 60)
    
    for result in results:
        status_symbol = {
            "pass": "✓",
            "fail": "✗",
            "warning": "!",
            "error": "?",
        }.get(result["status"], "?")
        
        print(f"\n{status_symbol} {result['name']}")
        for detail in result["details"]:
            print(f"  {detail}")
    
    # 统计
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    warnings = sum(1 for r in results if r["status"] == "warning")
    
    print("\n" + "=" * 60)
    print(f"总计: {total} | 通过: {passed} | 失败: {failed} | 警告: {warnings}")
    
    if failed == 0:
        print("\n✓ 所有测试通过，Skill 可用")
    else:
        print("\n✗ 存在失败项，需要修复")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Skill 冒烟测试工具")
    parser.add_argument("--skill-dir", required=True, help="Skill 目录路径")
    
    args = parser.parse_args()
    
    print(f"开始测试 Skill: {args.skill_dir}")
    
    try:
        results = []
        
        # 执行各项测试
        print("\n1. 检查 SKILL.md 格式...")
        results.append(check_skill_markdown(args.skill_dir))
        
        print("\n2. 检查脚本语法...")
        results.append(check_all_scripts(args.skill_dir))
        
        print("\n3. 检查引用完整性...")
        results.append(check_references(args.skill_dir))
        
        print("\n4. 检查目录结构...")
        results.append(check_directory_structure(args.skill_dir))
        
        print("\n5. 检查残留风险...")
        results.append(check_for_remaining_risks(args.skill_dir))
        
        # 生成报告
        report_file = generate_test_report(results, Path(args.skill_dir).parent)
        
        # 打印摘要
        print_test_summary(results)
        
        print(f"\n测试报告已保存到: {report_file}")
        
        # 根据测试结果返回退出码
        failed = sum(1 for r in results if r["status"] == "fail")
        exit(0 if failed == 0 else 1)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
