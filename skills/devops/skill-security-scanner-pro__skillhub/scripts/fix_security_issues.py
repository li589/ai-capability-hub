#!/usr/bin/env python3
"""
安全修复脚本
根据扫描结果修复 Skill 文件中的安全问题
"""

import argparse
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# 修复策略定义
FIX_STRATEGIES = {
    "command_execution": {
        "name": "本地命令执行",
        "fix_method": "replace_with_safe_alternative",
        "description": "使用工具调用或参数化命令替代直接命令执行",
        "safe_pattern": "考虑使用 exec_shell 工具或其他安全的替代方案",
    },
    "command_injection": {
        "name": "命令注入",
        "fix_method": "sanitize_input",
        "description": "移除或转义危险字符，使用参数化命令",
        "safe_pattern": "避免使用分号、管道符、命令替换等",
    },
    "sensitive_path_access": {
        "name": "敏感路径访问",
        "fix_method": "add_path_whitelist",
        "description": "添加路径白名单检查，限制访问范围",
        "safe_pattern": "只允许访问指定的安全路径",
    },
    "external_download": {
        "name": "外部下载与执行",
        "fix_method": "add_source_validation",
        "description": "添加来源白名单和内容验证",
        "safe_pattern": "仅从可信来源下载，验证文件内容",
    },
    "dynamic_import": {
        "name": "动态导入",
        "fix_method": "use_static_import",
        "description": "使用静态导入替代动态导入",
        "safe_pattern": "避免动态加载未知模块",
    },
    "hardcoded_credentials": {
        "name": "硬编码凭证",
        "fix_method": "use_environment_variables",
        "description": "使用环境变量或配置管理工具",
        "safe_pattern": "从环境变量读取敏感信息",
    },
    "file_traversal": {
        "name": "路径遍历",
        "fix_method": "normalize_path",
        "description": "规范化路径，检查是否在允许范围内",
        "safe_pattern": "使用 os.path.abspath() 或 Path.resolve() 并验证",
    },
    "unsafe_deserialization": {
        "name": "不安全的反序列化",
        "fix_method": "use_safe_format",
        "description": "使用安全的序列化格式（如 JSON）",
        "safe_pattern": "避免使用 pickle，改用 json 或其他安全格式",
    },
}


def create_backup(skill_dir: str) -> str:
    """创建备份目录"""
    skill_dir = Path(skill_dir)
    backup_dir = skill_dir.parent / f"{skill_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    shutil.copytree(skill_dir, backup_dir)
    print(f"已创建备份: {backup_dir}")
    
    return str(backup_dir)


def load_scan_result(scan_result_file: str) -> Dict:
    """加载扫描结果"""
    with open(scan_result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def apply_fix(file_path: str, line_num: int, risk_type: str, auto_fix: bool) -> Dict:
    """应用修复到指定文件和行"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"success": False, "message": f"文件不存在: {file_path}"}
    
    if risk_type not in FIX_STRATEGIES:
        return {"success": False, "message": f"未知风险类型: {risk_type}"}
    
    strategy = FIX_STRATEGIES[risk_type]
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if line_num < 1 or line_num > len(lines):
        return {"success": False, "message": f"行号超出范围: {line_num}"}
    
    original_line = lines[line_num - 1]
    
    # 根据风险类型应用不同的修复策略
    if auto_fix:
        fixed_line = auto_fix_line(original_line, risk_type)
    else:
        # 不自动修复，仅添加注释
        fixed_line = original_line.rstrip() + f"  # TODO: 安全风险 - {strategy['name']}\n"
    
    # 更新行
    lines[line_num - 1] = fixed_line
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return {
        "success": True,
        "file": str(file_path),
        "line": line_num,
        "risk_type": risk_type,
        "original": original_line.strip(),
        "fixed": fixed_line.strip(),
        "fix_method": strategy["fix_method"],
    }


def auto_fix_line(line: str, risk_type: str) -> str:
    """自动修复单行代码"""
    line = line.rstrip()
    
    # 针对不同风险类型的自动修复策略
    if risk_type == "command_injection":
        # 移除危险字符
        line = re.sub(r'[;&|`$]', '', line)
        line = re.sub(r'\$\([^)]*\)', '', line)
    
    elif risk_type == "hardcoded_credentials":
        # 替换硬编码凭证为环境变量引用
        line = re.sub(
            r'(password|passwd|pwd|secret|key|token)\s*[:=]\s*["\'][^"\']+["\']',
            r'\1 = os.getenv("\1", "")',
            line,
            flags=re.IGNORECASE
        )
    
    elif risk_type == "file_traversal":
        # 添加路径规范化注释
        line = line + "  # TODO: 需要规范化路径并验证"
    
    else:
        # 默认策略：添加注释
        strategy = FIX_STRATEGIES.get(risk_type, {})
        line = line + f"  # TODO: 安全风险 - {strategy.get('name', risk_type)}"
    
    return line + "\n"


def fix_risks(scan_result: Dict, skill_dir: str, auto_fix: bool) -> Dict:
    """修复扫描结果中的所有风险"""
    risks = scan_result.get("risks", [])
    
    fix_report = {
        "total_risks": len(risks),
        "fixed": 0,
        "skipped": 0,
        "failed": 0,
        "details": [],
    }
    
    if not risks:
        print("\n没有需要修复的风险")
        return fix_report
    
    print(f"\n开始修复 {len(risks)} 个风险项...")
    
    # 按文件分组，避免重复打开文件
    risks_by_file = {}
    for risk in risks:
        file_path = risk["file"]
        if file_path not in risks_by_file:
            risks_by_file[file_path] = []
        risks_by_file[file_path].append(risk)
    
    # 逐文件处理
    for file_path, file_risks in risks_by_file.items():
        print(f"\n处理文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        
        # 按行号倒序处理，避免行号变化影响
        file_risks_sorted = sorted(file_risks, key=lambda x: x["line"], reverse=True)
        
        for risk in file_risks_sorted:
            line_num = risk["line"]
            risk_type = risk["type"]
            original_line = lines[line_num - 1].rstrip()
            
            print(f"  行 {line_num}: {risk_type}")
            
            if auto_fix:
                fixed_line = auto_fix_line(original_line, risk_type)
            else:
                strategy = FIX_STRATEGIES.get(risk_type, {})
                fixed_line = original_line + f"  # TODO: 安全风险 - {strategy.get('name', risk_type)}\n"
            
            # 检查是否实际修改了内容
            if original_line != fixed_line.rstrip():
                lines[line_num - 1] = fixed_line
                modified = True
                
                fix_report["details"].append({
                    "file": file_path,
                    "line": line_num,
                    "risk_type": risk_type,
                    "status": "fixed",
                    "original": original_line[:100],
                    "fixed": fixed_line[:100],
                })
                fix_report["fixed"] += 1
            else:
                fix_report["details"].append({
                    "file": file_path,
                    "line": line_num,
                    "risk_type": risk_type,
                    "status": "skipped",
                    "message": "无需修改",
                })
                fix_report["skipped"] += 1
        
        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  ✓ 文件已更新")
        else:
            print(f"  - 文件无需修改")
    
    return fix_report


def generate_fix_report(fix_report: Dict, output_dir: str):
    """生成修复报告"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / "fix-report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(fix_report, f, indent=2, ensure_ascii=False)
    
    return str(report_file)


def print_fix_summary(fix_report: Dict):
    """打印修复摘要"""
    print("\n" + "=" * 60)
    print("修复摘要")
    print("=" * 60)
    print(f"总风险数: {fix_report['total_risks']}")
    print(f"已修复: {fix_report['fixed']}")
    print(f"已跳过: {fix_report['skipped']}")
    print(f"失败: {fix_report['failed']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Skill 安全修复工具")
    parser.add_argument("--scan-result", required=True, help="扫描结果 JSON 文件路径")
    parser.add_argument("--skill-dir", required=True, help="Skill 目录路径")
    parser.add_argument("--auto-fix", action="store_true", help="自动修复（默认为添加注释）")
    
    args = parser.parse_args()
    
    print(f"加载扫描结果: {args.scan_result}")
    print(f"Skill 目录: {args.skill_dir}")
    print(f"自动修复: {args.auto_fix}")
    
    try:
        # 加载扫描结果
        scan_result = load_scan_result(args.scan_result)
        
        # 创建备份
        backup_dir = create_backup(args.skill_dir)
        
        # 执行修复
        fix_report = fix_risks(scan_result, args.skill_dir, args.auto_fix)
        
        # 生成修复报告
        report_file = generate_fix_report(fix_report, Path(args.skill_dir).parent)
        
        # 打印摘要
        print_fix_summary(fix_report)
        
        if fix_report["fixed"] > 0:
            print(f"\n修复报告已保存到: {report_file}")
            print(f"备份已保存到: {backup_dir}")
            print("\n请使用 smoke_test.py 脚本验证修复效果")
        else:
            print("\n无需修复或所有修复已跳过")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
