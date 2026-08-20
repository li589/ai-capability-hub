#!/usr/bin/env python3
"""
skill_execution_monitor.py
==========================
自动执行 skill 内所有脚本，全程 strace 行为监控。

核心能力：
- 自动解析 SKILL.md，提取执行命令
- 自动推断正确参数（替换 skill 路径）
- 执行所有脚本，strace 全程监控
- 分析行为，输出完整报告

输入：skill 路径
输出：行为监控报告 + JSON 结构化结果
"""

import subprocess
import os
import sys
import json
import re
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------

def run_cmd(cmd: List[str], timeout: int = 30) -> tuple:
    """执行命令，返回 (returncode, stdout, stderr)"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                         timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def get_file_hash(path: str) -> str:
    """计算 SHA256"""
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def get_baseline(skill_path: str) -> Dict[str, Any]:
    """建立执行前基线"""
    baseline = {
        'timestamp': datetime.now().isoformat(),
        'files': {},
        'process_count': 0,
        'network_conns': []
    }

    # 文件快照
    for root, dirs, files in os.walk(skill_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                baseline['files'][fpath] = get_file_hash(fpath)
            except:
                pass

    # 进程数
    _, proc_out, _ = run_cmd(['ps', 'aux'])
    baseline['process_count'] = len(proc_out.strip().split('\n'))

    # 网络连接
    _, net_out, _ = run_cmd(['ss', '-an'])
    baseline['network_conns'] = net_out

    return baseline


def extract_commands_from_skill_md(skill_path: str) -> List[Dict[str, str]]:
    """
    从 SKILL.md 中提取所有可执行的命令模式
    自动识别参数并替换为 target_skill_path
    """
    md_path = os.path.join(skill_path, 'SKILL.md')
    if not os.path.exists(md_path):
        return []

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    commands = []

    # 匹配代码块中的命令（最可靠）
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)

    for block in code_blocks:
        for line in block.split('\n'):
            line = line.strip()
            if not line:
                continue

            # 跳过注释和空行
            if line.startswith('#') or line.startswith('//'):
                continue

            cmd = extract_command_from_line(line, skill_path)
            if cmd:
                commands.append(cmd)

    # 也匹配行内命令（如 docker run ...）
    for line in content.split('\n'):
        line = line.strip()
        if 'docker run' in line or 'python3 ' in line or 'bash ' in line:
            cmd = extract_command_from_line(line, skill_path)
            if cmd and cmd not in commands:
                commands.append(cmd)

    return commands


def extract_command_from_line(line: str, skill_path: str) -> Optional[Dict[str, str]]:
    """
    从一行中提取命令，替换路径参数
    过滤非实际命令（表格行、注释行、噪音内容）
    返回 {'raw': ..., 'exec': [...], 'type': ...}
    """
    # 过滤噪音内容
    stripped = line.strip()
    
    # 跳过空行
    if not stripped:
        return None
    
    # 跳过 Markdown 表格行（以 | 开头或结尾）
    if stripped.startswith('|') and stripped.endswith('|'):
        return None
    
    # 跳过注释行
    if stripped.startswith('#') or stripped.startswith('//'):
        return None
    
    # 跳过纯描述行（没有可执行命令关键词）
    if not any(kw in stripped for kw in ['python3', 'bash', 'docker', 'sh ']):
        return None
    
    # 提取 python3 命令
    py_match = re.search(r'python3\s+([^\s]+)', line)
    if py_match:
        script_path = py_match.group(1)
        
        # 过滤噪音 script 名（如文件名作为示例参数）
        if script_path in ['<skill路径>', '<path>', '[', ']', 'skill_vet.py路径', 'skill路径', '/skill']:
            return None
        
        # 构造执行命令
        exec_cmd = ['python3']
        if script_path.startswith('/'):
            exec_cmd.append(script_path)
        else:
            exec_cmd.append(os.path.join(skill_path, script_path))

        # 提取并替换路径参数
        args = re.findall(r'(?:/[\w\-\./]+)', line)
        for arg in args:
            if arg not in exec_cmd:
                exec_cmd.append(skill_path)
                break

        # 验证脚本文件存在
        script_full = exec_cmd[1]
        if not os.path.isfile(script_full):
            return None

        return {
            'raw': stripped[:100],
            'exec': exec_cmd,
            'type': 'python3',
            'script': script_full
        }

    # 提取 bash 命令
    bash_match = re.search(r'bash\s+([^\s]+)', line)
    if bash_match:
        script_path = bash_match.group(1)
        
        # 过滤噪音
        if script_path in ['<', '>', '|', '&', ';', '-c'] or script_path.startswith('|'):
            return None
        
        exec_cmd = ['bash']
        if script_path.startswith('/'):
            exec_cmd.append(script_path)
        else:
            exec_cmd.append(os.path.join(skill_path, script_path))

        script_full = exec_cmd[1]
        if not os.path.isfile(script_full):
            return None

        return {
            'raw': stripped[:100],
            'exec': exec_cmd,
            'type': 'bash',
            'script': script_full
        }

    return None


def find_all_scripts(skill_path: str) -> List[Dict[str, str]]:
    """
    找到 skill 内所有可执行脚本
    当 SKILL.md 没有命令时，作为 fallback
    """
    scripts_dir = os.path.join(skill_path, 'scripts')
    if not os.path.exists(scripts_dir):
        return []

    found = []
    for root, dirs, files in os.walk(scripts_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, skill_path)

            if fname.endswith('.py'):
                found.append({
                    'path': relpath,
                    'full_path': fpath,
                    'type': 'python3',
                    'exec': ['python3', fpath, skill_path]  # 假设脚本接受路径参数
                })
            elif fname.endswith('.sh'):
                found.append({
                    'path': relpath,
                    'full_path': fpath,
                    'type': 'bash',
                    'exec': ['bash', fpath]
                })

    return found


def analyze_strace_output(strace_content: str) -> Dict[str, List[str]]:
    """解析 strace 输出，提取行为"""
    findings = {
        'file_opens': [],
        'network_connects': [],
        'process_creations': [],
        'execve_calls': [],
        'commands': [],
        'suspicious_patterns': []
    }

    suspicious_patterns = [
        (r'curl.*\|.*bash', 'curl 管道到 bash'),
        (r'wget.*\|.*sh', 'wget 管道到 shell'),
        (r'/etc/passwd', '尝试读取 /etc/passwd'),
        (r'/etc/shadow', '尝试读取 /etc/shadow'),
        (r'\.ssh/id_', '尝试读取 SSH 私钥'),
        (r'base64.*-d', 'base64 解码'),
        (r'crontab', 'crontab 操作'),
        (r'nohup.*&', '后台运行进程'),
        (r'requests\.post', 'HTTP POST 请求'),
        (r'eval\s*\(', 'eval 执行'),
        (r'exec\s*\(', 'exec 执行'),
    ]

    for line in strace_content.split('\n'):
        # 文件打开
        if 'open(' in line or 'openat(' in line:
            match = re.search(r'open\([^)]+\)', line)
            if match:
                findings['file_opens'].append(match.group())

        # 网络连接
        if 'connect(' in line:
            match = re.search(r'connect\([^)]+\)', line)
            if match:
                findings['network_connects'].append(match.group())

        # 进程创建
        if 'clone(' in line or 'fork(' in line:
            findings['process_creations'].append(line.strip()[:100])

        # 执行新程序
        if 'execve(' in line:
            match = re.search(r'execve\([^)]+\)', line)
            if match:
                findings['execve_calls'].append(match.group())

        # 危险命令
        if any(cmd in line for cmd in ['curl ', 'wget ', 'bash -c', 'sh -c', 'nc ', 'netcat']):
            findings['commands'].append(line.strip()[:150])

        # 可疑模式深度匹配
        for pattern, desc in suspicious_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings['suspicious_patterns'].append(f'{desc}: {line.strip()[:100]}')


    return findings


def assess_risk(findings: Dict[str, List[str]]) -> tuple:
    """评估行为风险"""
    reasons = []
    level = 'LOW'
    details = []

    # HIGH: 可疑网络连接（非本地）
    for conn in findings.get('network_connects', []):
        if not any(private in conn for private in ['127.0.0.1', '::1', 'localhost', '0.0.0.0']):
            if any(x in conn for x in ['http', 'tcp', 'sock']):
                reasons.append(f'外部网络连接: {conn[:80]}')
                details.append(f'⚠️ 网络: {conn[:80]}')
                level = 'HIGH'

    # CRITICAL: 管道到 bash
    for cmd in findings.get('commands', []):
        if ('curl ' in cmd or 'wget ' in cmd) and '|' in cmd:
            reasons.append(f'管道命令: {cmd[:100]}')
            details.append(f'🚨 管道命令: {cmd[:100]}')
            level = 'HIGH'

    # HIGH: 可疑文件访问
    for op in findings.get('suspicious_patterns', []):
        if 'passwd' in op or 'shadow' in op or 'ssh' in op:
            reasons.append(op)
            details.append(f'🔴 {op}')
            level = 'HIGH'

    # MEDIUM: 进程创建 + 文件写入
    if findings.get('process_creations'):
        reasons.append(f'创建了 {len(findings["process_creations"])} 个新进程')
        details.append(f'⚙️ 进程: {len(findings["process_creations"])} 个新进程')

    # MEDIUM: 大量文件操作（可能正在扫描或泄露）
    if len(findings.get('file_opens', [])) > 50:
        reasons.append(f'大量文件操作: {len(findings["file_opens"])} 次')
        details.append(f'📁 文件: {len(findings["file_opens"])} 次')

    if not reasons:
        reasons.append('无异常行为')
        details.append('✅ 行为正常')

    return level, reasons, details


def execute_with_strace(
    cmd: List[str],
    output_dir: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """使用 strace 执行命令，全程监控"""
    result = {
        'cmd': ' '.join(cmd),
        'returncode': None,
        'timeout': False,
        'findings': None,
        'risk_level': 'LOW',
        'risk_reasons': [],
        'risk_details': [],
        'elapsed': 0
    }

    strace_log = os.path.join(output_dir, 'strace.log')

    strace_cmd = [
        'strace', '-f', '-tt', '-T',
        '-e', 'trace=open,openat,connect,clone,fork,execve,read,write,pipe,nanosleep',
        '-o', strace_log
    ] + cmd

    start = time.time()
    try:
        proc = subprocess.Popen(
            strace_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            proc.communicate(timeout=timeout)
            result['returncode'] = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            result['timeout'] = True
            result['returncode'] = -1
    except Exception as e:
        result['returncode'] = -1
        result['risk_reasons'].append(f'执行异常: {e}')

    result['elapsed'] = round(time.time() - start, 2)

    # 分析 strace 输出
    if os.path.exists(strace_log):
        try:
            with open(strace_log, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            result['findings'] = analyze_strace_output(content)
            level, reasons, details = assess_risk(result['findings'])
            result['risk_level'] = level
            result['risk_reasons'] = reasons
            result['risk_details'] = details
        except:
            pass

    return result


def generate_report(
    skill_path: str,
    commands: List[Dict],
    results: List[Dict],
    baseline: Dict
) -> str:
    """生成完整行为监控报告"""

    lines = []
    lines.append("=" * 60)
    lines.append("🔍 Skill 运行时行为监控报告")
    lines.append("=" * 60)
    lines.append(f"目标路径: {skill_path}")
    lines.append(f"监控时间: {datetime.now().isoformat()}")
    lines.append(f"检测命令: {len(commands)} 个")
    lines.append("")

    # 命令列表
    lines.append("## 📋 检测到的执行命令")
    for i, cmd in enumerate(commands, 1):
        lines.append(f"{i}. `{cmd['raw']}`")
        lines.append(f"   执行: `{' '.join(cmd['exec'])}`")
    lines.append("")

    # 执行结果
    lines.append("## 📜 执行结果")
    high_risk_count = 0
    for i, res in enumerate(results, 1):
        risk_icon = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴', 'CRITICAL': '⛔'}.get(res['risk_level'], '⚪')
        lines.append(f"### {i}. {risk_icon} {res['cmd']}")
        lines.append(f"- 返回码: {res['returncode']}")
        lines.append(f"- 执行时间: {res['elapsed']}秒")
        lines.append(f"- 风险等级: {res['risk_level']}")
        if res['timeout']:
            lines.append(f"- 状态: ⏱️ 超时")
        elif res['returncode'] == 0:
            lines.append(f"- 状态: ✅ 成功")
        else:
            lines.append(f"- 状态: ❌ 失败")

        for detail in res.get('risk_details', []):
            lines.append(f"  {detail}")

        if res['risk_level'] in ('HIGH', 'CRITICAL'):
            high_risk_count += 1

        lines.append("")

    # 整体评估
    lines.append("## 🚨 整体风险评估")
    if high_risk_count > 0:
        lines.append(f"⚠️ 发现 {high_risk_count} 个高风险命令")
        lines.append("建议：人工审查后再安装")
    else:
        lines.append("✅ 所有脚本行为正常，未检测到可疑活动")

    lines.append("")
    lines.append(f"报告生成: {datetime.now().isoformat()}")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 skill_execution_monitor.py <skill路径>")
        print("示例: python3 skill_execution_monitor.py /home/strong/.openclaw/workspace/skills/weather")
        sys.exit(1)

    skill_path = os.path.abspath(sys.argv[1])

    if not os.path.exists(skill_path):
        print(f"错误: 路径不存在: {skill_path}")
        sys.exit(1)

    print(f"🔍 开始行为监控: {skill_path}", flush=True)

    # 步骤1: 从 SKILL.md 提取命令
    print("[1/4] 解析 SKILL.md，提取执行命令...", flush=True)
    commands = extract_commands_from_skill_md(skill_path)

    # Fallback: 找所有脚本
    if not commands:
        print("  ⚠️ SKILL.md 中未找到命令，使用 fallback 扫描 scripts/ 目录", flush=True)
        scripts = find_all_scripts(skill_path)
        commands = [{'raw': s['path'], 'exec': s['exec'], 'type': s['type'], 'script': s['full_path']}
                   for s in scripts]
    else:
        print(f"  找到 {len(commands)} 个命令", flush=True)

    if not commands:
        print("  ❌ 未找到可执行命令，行为监控终止", flush=True)
        sys.exit(0)

    for cmd in commands:
        print(f"  - {cmd['raw'][:80]}", flush=True)

    # 步骤2: 建立基线
    print("[2/4] 建立执行前基线...", flush=True)
    baseline = get_baseline(skill_path)
    print(f"  基线: {len(baseline['files'])} 文件", flush=True)

    # 步骤3: 执行并监控
    print("[3/4] 执行命令并全程 strace 监控...", flush=True)
    output_dir = tempfile.mkdtemp(prefix='skill_exec_')
    results = []

    for i, cmd_info in enumerate(commands, 1):
        print(f"  [{i}/{len(commands)}] 执行: {cmd_info['exec']}", flush=True)
        res = execute_with_strace(cmd_info['exec'], output_dir, timeout=30)
        results.append(res)
        print(f"    返回码: {res['returncode']}, 风险: {res['risk_level']}", flush=True)

    # 步骤4: 生成报告
    print("[4/4] 生成行为监控报告...", flush=True)
    report = generate_report(skill_path, commands, results, baseline)

    print("")
    print("=" * 60)
    print("🔍 行为监控报告")
    print("=" * 60)
    print(report)

    # JSON 输出
    json_output = {
        'skill_path': skill_path,
        'commands_found': len(commands),
        'results': results,
        'high_risk_count': sum(1 for r in results if r['risk_level'] in ('HIGH', 'CRITICAL'))
    }

    print("\n--- JSON OUTPUT ---", flush=True)
    print(json.dumps(json_output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
