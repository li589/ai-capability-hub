#!/usr/bin/env python3
"""
Skill 安全扫描脚本
扫描 .skill 文件及其引用文档中的安全风险内容
"""

import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple


# 安全风险模式定义
SECURITY_PATTERNS = {
    "command_execution": {
        "name": "本地命令执行",
        "severity": "high",
        "patterns": [
            r"exec_shell\s*\(",
            r"os\.system\s*\(",
            r"subprocess\.(call|run|Popen)\s*\(",
            r"eval\s*\(",
            r"exec\s*\(",
            r"os\.exec",
        ],
        "description": "检测到潜在的本地命令执行，可能导致命令注入攻击"
    },
    "command_injection": {
        "name": "命令注入",
        "severity": "critical",
        "patterns": [
            r"[;&|`$]",
            r"\$\([^)]*\)",
            r"&&\s*\w+",
            r"\|\s*\w+",
        ],
        "description": "检测到命令注入模式，攻击者可能执行任意命令"
    },
    "sensitive_path_access": {
        "name": "敏感路径访问",
        "severity": "high",
        "patterns": [
            r"/etc/(passwd|shadow|hosts)",
            r"/root/",
            r"/var/",
            r"/home/[^/]+/",
            r"\.\./",
        ],
        "description": "检测到对敏感系统路径的访问，可能导致信息泄露或越权"
    },
    "external_download": {
        "name": "外部下载与执行",
        "severity": "medium",
        "patterns": [
            r"urllib\.(request|parse)\.",
            r"requests\.(get|post|put|delete)\s*\(",
            r"wget\s+",
            r"curl\s+",
        ],
        "description": "检测到外部资源下载，需验证来源安全性"
    },
    "dynamic_import": {
        "name": "动态导入",
        "severity": "medium",
        "patterns": [
            r"__import__\s*\(",
            r"importlib\.(import_module|reload)\s*\(",
            r"exec\s*\(['\"].*import",
        ],
        "description": "检测到动态模块导入，可能导致代码注入"
    },
    "hardcoded_credentials": {
        "name": "硬编码凭证",
        "severity": "medium",
        "patterns": [
            r"(password|passwd|pwd|secret|key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]",
        ],
        "description": "检测到硬编码的敏感凭证信息"
    },
    "file_traversal": {
        "name": "路径遍历",
        "severity": "high",
        "patterns": [
            r"\.\./.*\.\.",
            r"open\s*\([^)]*\.\.",
            r"Path\s*\([^)]*\.\.",
        ],
        "description": "检测到路径遍历模式，可能访问预期外的文件"
    },
    "unsafe_deserialization": {
        "name": "不安全的反序列化",
        "severity": "high",
        "patterns": [
            r"pickle\.(loads|load)\s*\(",
            r"shelve\.open\s*\(",
            r"yaml\.unsafe_load\s*\(",
        ],
        "description": "检测到不安全的反序列化操作，可能导致远程代码执行"
    },
}


def extract_skill(skill_file: str, output_dir: str) -> str:
    """解压 .skill 文件到指定目录"""
    skill_file = Path(skill_file)
    output_dir = Path(output_dir)
    
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill 文件不存在: {skill_file}")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 解压文件
    with zipfile.ZipFile(skill_file, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    
    # 查找解压后的 skill 目录
    extracted_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if len(extracted_dirs) == 1:
        return str(extracted_dirs[0])
    
    return str(output_dir)


def scan_file(file_path: Path) -> List[Dict]:
    """扫描单个文件的安全风险"""
    risks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        file_ext = file_path.suffix.lower()
        
        # 扫描每一行
        for line_num, line in enumerate(lines, 1):
            for risk_type, risk_info in SECURITY_PATTERNS.items():
                for pattern in risk_info["patterns"]:
                    if re.search(pattern, line, re.IGNORECASE):
                        risks.append({
                            "file": str(file_path),
                            "line": line_num,
                            "type": risk_type,
                            "severity": risk_info["severity"],
                            "description": risk_info["description"],
                            "pattern": pattern,
                            "code_snippet": line.strip()[:100],  # 截取前100字符
                        })
                        # 同一行只记录一次风险类型
                        break
    
    except Exception as e:
        print(f"警告: 无法读取文件 {file_path}: {e}")
    
    return risks


def scan_directory(skill_dir: str) -> Tuple[List[Dict], Dict]:
    """递归扫描目录中的所有文件"""
    all_risks = []
    stats = {
        "files_scanned": 0,
        "risks_found": 0,
        "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "by_type": {},
    }
    
    skill_dir = Path(skill_dir)
    
    # 支持的文件类型
    supported_extensions = {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.sh'}
    
    for file_path in skill_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            stats["files_scanned"] += 1
            risks = scan_file(file_path)
            all_risks.extend(risks)
            
            # 更新统计信息
            for risk in risks:
                stats["risks_found"] += 1
                severity = risk["severity"]
                if severity in stats["by_severity"]:
                    stats["by_severity"][severity] += 1
                
                risk_type = risk["type"]
                stats["by_type"][risk_type] = stats["by_type"].get(risk_type, 0) + 1
    
    return all_risks, stats


def generate_scan_result(risks: List[Dict], stats: Dict, output_dir: str) -> str:
    """生成扫描结果 JSON 文件"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "scan_summary": stats,
        "risks": risks,
        "recommendations": generate_recommendations(risks, stats),
    }
    
    result_file = output_dir / "scan-result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return str(result_file)


def generate_recommendations(risks: List[Dict], stats: Dict) -> List[str]:
    """生成修复建议"""
    recommendations = []
    
    if stats["by_severity"]["critical"] > 0:
        recommendations.append("发现严重安全问题，建议立即修复")
    
    if stats["by_severity"]["high"] > 0:
        recommendations.append("发现高风险问题，建议优先处理")
    
    # 根据风险类型生成具体建议
    risk_types = set(r["type"] for r in risks)
    
    if "command_execution" in risk_types:
        recommendations.append("命令执行风险：考虑使用参数化命令或工具调用替代")
    
    if "sensitive_path_access" in risk_types:
        recommendations.append("敏感路径访问：添加路径白名单检查，限制访问范围")
    
    if "external_download" in risk_types:
        recommendations.append("外部下载：验证下载来源，添加内容完整性检查")
    
    if "hardcoded_credentials" in risk_types:
        recommendations.append("硬编码凭证：使用环境变量或配置管理工具")
    
    if stats["risks_found"] == 0:
        recommendations.append("未发现明显安全风险")
    
    return recommendations


def print_scan_summary(stats: Dict, risks: List[Dict]):
    """打印扫描摘要"""
    print("\n" + "=" * 60)
    print("安全扫描摘要")
    print("=" * 60)
    print(f"扫描文件数: {stats['files_scanned']}")
    print(f"发现风险数: {stats['risks_found']}")
    print("\n按严重程度分布:")
    for severity in ["critical", "high", "medium", "low"]:
        count = stats["by_severity"][severity]
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    
    if stats["risks_found"] > 0:
        print("\n按风险类型分布:")
        for risk_type, count in sorted(stats["by_type"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {risk_type}: {count}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Skill 安全扫描工具")
    parser.add_argument("--skill-file", required=True, help="Skill 文件路径 (.skill)")
    parser.add_argument("--output-dir", help="输出目录（默认为临时目录）")
    
    args = parser.parse_args()
    
    # 创建输出目录
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = tempfile.mkdtemp(prefix="skill-scan-")
    
    print(f"开始扫描 Skill 文件: {args.skill_file}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 解压 Skill 文件
        print("\n正在解压 Skill 文件...")
        skill_dir = extract_skill(args.skill_file, output_dir)
        print(f"解压完成: {skill_dir}")
        
        # 扫描安全风险
        print("\n正在扫描安全风险...")
        risks, stats = scan_directory(skill_dir)
        
        # 生成扫描结果
        print("\n正在生成扫描报告...")
        result_file = generate_scan_result(risks, stats, output_dir)
        
        # 打印摘要
        print_scan_summary(stats, risks)
        
        if stats["risks_found"] > 0:
            print(f"\n详细报告已保存到: {result_file}")
            print("请使用 fix_security_issues.py 脚本进行修复")
        else:
            print("\n✓ 未发现安全风险")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
