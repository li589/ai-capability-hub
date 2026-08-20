#!/usr/bin/env python3
"""
Skill Behavior Monitor - 运行时行为监控器
在 Docker 容器内运行，追踪 skill 执行时的真实行为

使用 strace + inotifywait + pspy 三大工具
输出结构化 JSON 报告，供主会话解析
"""

import os
import sys
import json
import time
import subprocess
import re
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional


class BehaviorMonitor:
    """Skill 运行时行为监控器"""

    def __init__(self, skill_path: str, timeout: int = 30):
        self.skill_path = Path(skill_path).resolve()
        self.timeout = timeout
        self.findings = []
        self.baseline = {'files': set(), 'processes': set(), 'network': set()}
        self.strace_output = []

    # ─────────────────────────────────────────────────────────
    # 第一阶段：建立基线
    # ─────────────────────────────────────────────────────────

    def snapshot_baseline(self):
        """建立执行前的系统基线"""
        self.findings.append({
            'phase': 'baseline',
            'type': 'info',
            'message': '开始建立基线快照...',
            'timestamp': datetime.now().isoformat()
        })

        # 文件快照：列出 skill 目录初始状态
        if self.skill_path.exists():
            for f in self.skill_path.rglob('*'):
                if f.is_file():
                    self.baseline['files'].add(str(f))

        # 进程快照
        self.baseline['processes'] = self._get_process_list()

        # 网络快照
        self.baseline['network'] = self._get_network_connections()

        self.findings.append({
            'phase': 'baseline',
            'type': 'info',
            'message': f'基线建立完成：{len(self.baseline["files"])} 文件，'
                       f'{len(self.baseline["processes"])} 进程，'
                       f'{len(self.baseline["network"])} 网络连接',
            'timestamp': datetime.now().isoformat()
        })

    def _get_process_list(self) -> set:
        """获取当前进程列表"""
        processes = set()
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    processes.add(f"{parts[0]}:{parts[1]}")
        except Exception:
            pass
        return processes

    def _get_network_connections(self) -> set:
        """获取当前网络连接"""
        connections = set()
        try:
            for tool in ['ss', 'netstat']:
                try:
                    result = subprocess.run(
                        [tool, '-tunap'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.splitlines()[1:]:
                            connections.add(line.strip())
                        break
                except Exception:
                    continue
        except Exception:
            pass
        return connections

    # ─────────────────────────────────────────────────────────
    # 第二阶段：strace 追踪
    # ─────────────────────────────────────────────────────────

    def run_strace(self, cmd: list) -> dict:
        """
        用 strace 追踪命令执行，检测可疑系统调用
        返回：(returncode, stdout, stderr, traced_calls)
        """
        strace_output_file = tempfile.mktemp(suffix='.strace')

        strace_cmd = [
            'strace', '-f', '-tt', '-T',
            '-e', 'trace=file,desc,network,process,signal',
            '-o', strace_output_file,
        ] + cmd

        self.findings.append({
            'phase': 'strace',
            'type': 'info',
            'message': f'启动 strace 追踪: {" ".join(cmd)}',
            'timestamp': datetime.now().isoformat()
        })

        start_time = time.time()
        try:
            result = subprocess.run(
                strace_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
        except subprocess.TimeoutExpired:
            self.findings.append({
                'phase': 'strace',
                'type': 'error',
                'message': f'strace 超时（{self.timeout}秒），进程被强制终止',
                'timestamp': datetime.now().isoformat()
            })
            return {'returncode': -1, 'timeout': True, 'calls': []}
        finally:
            # 读取 strace 输出并分析
            if os.path.exists(strace_output_file):
                self._analyze_strace_output(strace_output_file)
                os.unlink(strace_output_file)

        return {
            'returncode': result.returncode,
            'stdout': result.stdout[:2000],
            'stderr': result.stderr[:2000],
            'elapsed': elapsed,
            'timeout': False
        }

    def _analyze_strace_output(self, strace_file: str):
        """分析 strace 输出，检测危险行为"""
        DANGEROUS_PATTERNS = [
            # 凭证访问
            (r'open\(["\'].*\.ssh/.*["\']', 'HIGH', '访问 SSH 密钥目录'),
            (r'open\(["\'].*\.aws/.*["\']', 'HIGH', '访问 AWS 凭证目录'),
            (r'open\(["\'].*\.config/openclaw.*["\']', 'HIGH', '访问 OpenClaw 配置'),
            (r'open\(["\'].*MEMORY\.md["\']', 'HIGH', '访问记忆文件 MEMORY.md'),
            (r'open\(["\'].*USER\.md["\']', 'HIGH', '访问用户文件 USER.md'),
            (r'open\(["\'].*SOUL\.md["\']', 'HIGH', '访问灵魂文件 SOUL.md'),
            (r'open\(["\'].*AGENTS\.md["\']', 'HIGH', '访问代理文件 AGENTS.md'),
            (r'open\(["\'].*\.netrc["\']', 'HIGH', '访问网络凭证文件'),
            # 文件写入危险路径
            (r'open\(["\'].*\/etc\/.*["\'].*O_WRONLY', 'CRITICAL', '写入 /etc 系统目录'),
            (r'open\(["\'].*\/usr\/bin\/.*["\'].*O_WRONLY', 'CRITICAL', '写入 /usr/bin 可执行目录'),
            (r'open\(["\'].*\/tmp\/.*\.sh["\'].*O_WRONLY', 'MEDIUM', '在 /tmp 写入 shell 脚本'),
            # 网络行为
            (r'connect\(.*AF_INET.*["\'](?!\.)', 'HIGH', '建立网络连接（可疑 IP）'),
            (r'connect.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'HIGH', '建立网络连接到 IP 地址'),
            # 进程操作
            (r'clone\(|fork\(|vfork\(', 'MEDIUM', '创建新进程（fork/clone）'),
            (r'execve\(', 'INFO', '执行新程序'),
            # 信号操作
            (r'kill\(', 'MEDIUM', '发送信号给进程（可能是进程终止/操控）'),
            # 内存操作
            (r'mmap.*PROT_WRITE.*PROT_EXEC', 'HIGH', '可写可执行内存映射（代码注入特征）'),
            # 隐藏行为
            (r'unlink\(["\'].*\.pyc["\']', 'MEDIUM', '删除 Python 缓存文件（隐藏痕迹？）'),
            (r'prctl\(PR_SET_DUMPABLE', 'HIGH', '修改进程 dumpable 标志（绕过调试检测）'),
        ]

        try:
            with open(strace_file, 'r', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern, level, detail in DANGEROUS_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.findings.append({
                                'phase': 'strace',
                                'type': 'security',
                                'level': level,
                                'pattern': pattern,
                                'detail': detail,
                                'line': line.strip()[:200],
                                'timestamp': datetime.now().isoformat()
                            })
        except Exception as e:
            self.findings.append({
                'phase': 'strace',
                'type': 'error',
                'message': f'strace 输出分析失败: {e}',
                'timestamp': datetime.now().isoformat()
            })

    # ─────────────────────────────────────────────────────────
    # 第三阶段：文件监控（inotifywait）
    # ─────────────────────────────────────────────────────────

    def run_inotify_watch(self, cmd: list) -> dict:
        """用 inotifywait 监控文件修改事件"""
        # inotifywait 在 Alpine 中可能需要安装
        # 如果不可用，跳过此阶段
        monitor_output = tempfile.mktemp(suffix='.inotify')

        # 先检查 inotifywait 是否可用
        try:
            subprocess.run(
                ['which', 'inotifywait'],
                capture_output=True, timeout=5
            )
        except Exception:
            self.findings.append({
                'phase': 'inotify',
                'type': 'info',
                'message': 'inotifywait 不可用，跳过文件监控',
                'timestamp': datetime.now().isoformat()
            })
            return {'available': False}

        # 在后台启动 inotifywait
        inotify_cmd = [
            'sh', '-c',
            f'inotifywait -m -r -e modify,create,delete,move '
            f'--format "%e %w%f" "{self.skill_path}" >> {monitor_output} 2>&1 & '
            f'PID=$!; sleep 0.5; '
            f'({" ".join(cmd)}); '
            f'RC=$?; kill $PID 2>/dev/null; exit $RC'
        ]

        try:
            result = subprocess.run(
                inotify_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
        except subprocess.TimeoutExpired:
            self.findings.append({
                'phase': 'inotify',
                'type': 'error',
                'message': 'inotify 监控超时',
                'timestamp': datetime.now().isoformat()
            })
            return {'available': True, 'timeout': True}

        # 分析 inotify 输出
        modified_files = []
        if os.path.exists(monitor_output):
            try:
                with open(monitor_output, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            modified_files.append(line)
                            self.findings.append({
                                'phase': 'inotify',
                                'type': 'security',
                                'level': 'MEDIUM',
                                'detail': f'文件被修改: {line}',
                                'timestamp': datetime.now().isoformat()
                            })
                os.unlink(monitor_output)
            except Exception:
                pass

        return {
            'available': True,
            'modified_files': modified_files,
            'returncode': result.returncode
        }

    # ─────────────────────────────────────────────────────────
    # 第四阶段：进程监控（pspy）
    # ─────────────────────────────────────────────────────────

    def run_pspy_check(self) -> dict:
        """检测是否有未授权的进程被启动"""
        # pspy 在容器中检测 cron/systemd 事件
        # 简化版：用 ps 快照对比检测新增进程
        after_processes = self._get_process_list()
        new_processes = after_processes - self.baseline['processes']

        suspicious = []
        for proc in new_processes:
            # 过滤掉正常的监控工具进程
            if any(x in proc for x in ['strace', 'inotify', 'pspy', 'monitor']):
                continue
            suspicious.append(proc)
            self.findings.append({
                'phase': 'pspy',
                'type': 'security',
                'level': 'INFO',
                'detail': f'检测到新进程: {proc}',
                'timestamp': datetime.now().isoformat()
            })

        return {
            'new_processes': list(new_processes),
            'suspicious': suspicious
        }

    # ─────────────────────────────────────────────────────────
    # 第五阶段：网络行为对比
    # ─────────────────────────────────────────────────────────

    def run_network_check(self) -> dict:
        """对比执行前后的网络连接，检测新增连接"""
        after_network = self._get_network_connections()
        new_connections = after_network - self.baseline['network']

        suspicious = []
        for conn in new_connections:
            # 检测可疑 IP 连接（排除本地）
            if any(x in conn for x in ['127.0.0.1', '::1', 'localhost']):
                continue
            # 检测非预期端口
            if any(x in conn for x in ['443', '80', '8080', '8443']):
                self.findings.append({
                    'phase': 'network',
                    'type': 'security',
                    'level': 'MEDIUM',
                    'detail': f'检测到 HTTP/HTTPS 连接: {conn[:100]}',
                    'timestamp': datetime.now().isoformat()
                })
            suspicious.append(conn)

        return {
            'new_connections': list(new_connections),
            'suspicious': suspicious
        }

    # ─────────────────────────────────────────────────────────
    # 主流程
    # ─────────────────────────────────────────────────────────

    def monitor_skill_execution(self, skill_cmd: list) -> dict:
        """
        对 skill 执行进行完整的行为监控
        skill_cmd: 在容器内执行的命令，如 ['python3', '/skill/SKILL.md']
        """
        self.findings.append({
            'phase': 'init',
            'type': 'info',
            'message': f'开始监控 skill 执行: {" ".join(skill_cmd)}',
            'skill_path': str(self.skill_path),
            'timestamp': datetime.now().isoformat()
        })

        # 第一步：建立基线
        self.snapshot_baseline()

        # 第二步：strace 追踪
        strace_result = self.run_strace(skill_cmd)

        # 第三步：pspy 进程检测
        pspy_result = self.run_pspy_check()

        # 第四步：网络行为检测
        network_result = self.run_network_check()

        # 汇总发现
        risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'INFO': 0}
        for f in self.findings:
            if f.get('type') == 'security' and f.get('level') in risk_counts:
                risk_counts[f['level']] += 1

        overall_risk = 'SAFE'
        if risk_counts['CRITICAL'] > 0:
            overall_risk = 'CRITICAL'
        elif risk_counts['HIGH'] > 0:
            overall_risk = 'HIGH'
        elif risk_counts['MEDIUM'] > 0:
            overall_risk = 'MEDIUM'
        elif risk_counts['INFO'] > 0:
            overall_risk = 'LOW'

        return {
            'skill_path': str(self.skill_path),
            'command': ' '.join(skill_cmd),
            'overall_risk': overall_risk,
            'strace_returncode': strace_result.get('returncode', 'N/A'),
            'risk_counts': risk_counts,
            'findings': self.findings,
            'process_snapshot': {
                'baseline_count': len(self.baseline['processes']),
                'after_count': len(pspy_result.get('new_processes', [])),
                'suspicious': pspy_result.get('suspicious', [])
            },
            'network_snapshot': {
                'baseline_count': len(self.baseline['network']),
                'new_connections': network_result.get('suspicious', [])
            },
            'timestamp': datetime.now().isoformat()
        }


def print_report(result: dict):
    """打印人类可读的行为监控报告"""
    print('=' * 60)
    print('🔍 Skill 运行时行为监控报告')
    print('=' * 60)
    print(f'目标路径: {result["skill_path"]}')
    print(f'执行命令: {result["command"]}')
    print(f'strace 返回码: {result["strace_returncode"]}')
    print(f'综合风险等级: {result["overall_risk"]}')
    print('-' * 60)
    print(f'风险统计: CRITICAL={result["risk_counts"]["CRITICAL"]} '
          f'HIGH={result["risk_counts"]["HIGH"]} '
          f'MEDIUM={result["risk_counts"]["MEDIUM"]} '
          f'INFO={result["risk_counts"]["INFO"]}')
    print('-' * 60)
    print('发现详情:')
    for f in result['findings']:
        if f.get('type') == 'security':
            lvl = f.get('level', '?')
            detail = f.get('detail', f.get('message', ''))
            phase = f.get('phase', '')
            print(f'  [{lvl}] [{phase}] {detail}')
        elif f.get('type') == 'error':
            print(f'  [ERROR] {f.get("message", "")}')
    print('=' * 60)

    # 输出 JSON（供程序解析）
    print('\n--- JSON OUTPUT ---')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python3 skill_behavior_monitor.py <skill路径> <执行命令...>')
        print('示例: python3 skill_behavior_monitor.py /skill python3 -c "import sys; print(sys.version)"')
        sys.exit(1)

    skill_path = sys.argv[1]
    skill_cmd = sys.argv[2:]

    monitor = BehaviorMonitor(skill_path, timeout=30)
    result = monitor.monitor_skill_execution(skill_cmd)
    print_report(result)

    # 根据风险等级退出
    if result['overall_risk'] == 'CRITICAL':
        sys.exit(2)
    elif result['overall_risk'] == 'HIGH':
        sys.exit(3)
    elif result['overall_risk'] == 'MEDIUM':
        sys.exit(4)
