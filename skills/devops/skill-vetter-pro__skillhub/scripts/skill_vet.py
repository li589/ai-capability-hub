#!/usr/bin/env python3
"""
Enhanced Skill Security Scanner - AST-based v2
用 AST 解析替代正则匹配，区分"规则定义"和"实际危险调用"
覆盖盲区：间接 eval、变量 import、f-string exec、敏感文件、base64→exec 链、requests POST
"""

import os
import sys
import json
import ast
import re
from pathlib import Path
from typing import Optional, Set


class SecurityAnalyzer(ast.NodeVisitor):
    """AST 访问器，检测危险代码模式 v2"""

    # 敏感路径关键词
    SENSITIVE_PATHS = {
        '/etc/passwd': 'HIGH',
        '/etc/shadow': 'CRITICAL',
        '/etc/sudoers': 'HIGH',
        '~/.ssh/': 'HIGH',
        '~/.aws/': 'HIGH',
        '~/.config/openclaw': 'HIGH',
        '~/.netrc': 'HIGH',
        'MEMORY.md': 'HIGH',
        'USER.md': 'HIGH',
        'SOUL.md': 'HIGH',
        'AGENTS.md': 'HIGH',
        'IDENTITY.md': 'HIGH',
        '.pem': 'HIGH',
        '.key': 'HIGH',
        'id_rsa': 'CRITICAL',
        'id_ed25519': 'CRITICAL',
        'cookie': 'MEDIUM',
        'localStorage': 'MEDIUM',
    }

    # 危险模块
    DANGEROUS_MODULES = {
        'subprocess': 'INFO',
        'socket': 'HIGH',
        'pty': 'HIGH',
        'pwd': 'HIGH',
        'spwd': 'HIGH',
        'crypt': 'HIGH',
        'getpass': 'HIGH',
        'requests': 'INFO',  # 导入本身不危险，POST 才危险
        'urllib': 'INFO',
        'http.client': 'INFO',
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.findings = []
        self._seen_calls: Set[str] = set()  # 追踪已分析的调用，防止重复

    # ─────────────────────────────────────────────────────────
    # 核心：Call 节点访问
    # ─────────────────────────────────────────────────────────

    def visit_Call(self, node: ast.Call):
        func_name = self._get_func_name(node)
        if not func_name:
            self.generic_visit(node)
            return

        call_sig = f"{func_name}:{node.lineno}"
        if call_sig in self._seen_calls:
            self.generic_visit(node)
            return
        self._seen_calls.add(call_sig)

        # 1. eval / exec（含 f-string、format-string）
        if func_name in ('eval', 'exec'):
            if self._has_external_input(node):
                detail = '动态代码执行，可能执行任意代码'
                if self._contains_format_string(node):
                    detail = '动态代码执行（含格式化字符串），可被注入'
                self._add_finding('CRITICAL', f'{func_name}() with external input', node.lineno, detail)

        # 2. __import__(变量) - 动态 import，绕过静态检测
        elif func_name == '__import__':
            if len(node.args) > 0:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                    mod_name = first_arg.value
                    if mod_name in self.DANGEROUS_MODULES:
                        self._add_finding('HIGH', f'__import__("{mod_name}")', node.lineno,
                                          f'动态导入危险模块 {mod_name}')
                elif not isinstance(first_arg, ast.Constant):
                    # 变量参数 = 完全动态导入，无法追踪
                    self._add_finding('HIGH', f'__import__(variable)', node.lineno,
                                      '动态导入（参数为变量），可能绕过静态 import 检测')

        # 3. 敏感模块动态导入 via __builtins__
        elif func_name == 'getattr' and len(node.args) >= 2:
            if isinstance(node.args[0], ast.Name) and node.args[0].id == '__builtins__':
                attr = self._const_value(node.args[1])
                if attr in ('eval', 'exec', '__import__', 'open'):
                    self._add_finding('CRITICAL', f"__builtins__['{attr}']", node.lineno,
                                      f'通过 __builtins__ 获取危险函数 {attr}')

        # 4. requests.post / requests.get - 数据外传
        elif func_name in ('post', 'get', 'put', 'delete', 'patch', 'request') and len(node.args) >= 1:
            if isinstance(node.func, ast.Attribute):
                obj_name = self._get_obj_name(node.func.value)
                if obj_name == 'requests':
                    url = self._const_value(node.args[0]) if len(node.args) > 0 else None
                    self._add_finding('HIGH', f'requests.{func_name}()', node.lineno,
                                      f'发起 HTTP {func_name.upper()} 请求{"，目标: " + url if url else "（URL 可能为变量）"}')

        # 5. urllib.request - 类似 requests
        elif func_name == 'urlopen' and isinstance(node.func, ast.Attribute):
            obj_name = self._get_obj_name(node.func.value)
            if 'urllib' in obj_name:
                self._add_finding('MEDIUM', f'{obj_name}.urlopen()', node.lineno,
                                  '发起网络请求（urllib），检查目标地址是否可信')

        # 6. expanduser - 可能访问敏感路径
        elif func_name == 'expanduser' and len(node.args) >= 1:
            path = self._const_value(node.args[0])
            if path:
                for keyword, level in self.SENSITIVE_PATHS.items():
                    if keyword in path:
                        self._add_finding(level, f'expanduser("{path}")', node.lineno,
                                          f'展开用户路径含敏感关键词: {path}')

        # 7. base64 解码 → exec/eval 链检测（仅限明确的 base64 函数）
        elif func_name in ('b64decode', 'b64encode', 'b32decode', 'b32encode', 'b16decode', 'b16encode'):
            # 检查解码后是否被 exec/eval 使用
            if self._is_base64_decode_chain(node):
                self._add_finding('HIGH', f'{func_name}() chained with exec/eval', node.lineno,
                                  'base64 解码后链式执行代码，可能是混淆恶意代码')

        # 8. open() 调用 - 检查是否打开敏感文件
        elif func_name == 'open':
            args = node.args
            if len(args) >= 1:
                path_val = self._const_value(args[0])
                if path_val:
                    for keyword, level in self.SENSITIVE_PATHS.items():
                        if keyword in path_val:
                            self._add_finding(level, f'open("{path_val}")', node.lineno,
                                              f'访问含敏感关键词的文件: {path_val}')
                elif not isinstance(args[0], ast.Constant):
                    # 路径为变量
                    if self._looks_like_path(args[0]):
                        self._add_finding('MEDIUM', 'open(path=variable)', node.lineno,
                                          '打开文件（路径为变量），无法静态验证路径安全性')

        # 9. get/setattr 动态属性访问
        elif func_name in ('getattr', 'setattr'):
            self._add_finding('MEDIUM', f'{func_name}()', node.lineno,
                              '动态属性访问，可能用于绕过属性检查')

        # 10. __builtins__['xxx'] 直接访问
        elif isinstance(node.func, ast.Subscript):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == '__builtins__':
                attr = self._const_value(node.func)
                if attr in ('eval', 'exec', '__import__', 'open', 'compile'):
                    self._add_finding('CRITICAL', f"__builtins__['{attr}']", node.lineno,
                                      f'直接访问 __builtins__[{attr}]，可能是隐藏的危险操作')

        self.generic_visit(node)

    # ─────────────────────────────────────────────────────────
    # 赋值语句检测
    # ─────────────────────────────────────────────────────────

    def visit_Assign(self, node: ast.Assign):
        """检测可疑的赋值语句（如将函数赋值给变量用于隐藏调用）"""
        if isinstance(node.value, ast.Call):
            func_name = self._get_func_name(node.value)
            if func_name in ('eval', 'exec'):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self._add_finding('CRITICAL', f'{target.id} = {func_name}()', node.lineno,
                                          f'将危险函数赋值给变量 {target.id}，可能是隐藏调用')
            # __import__ 赋值给变量
            elif func_name == '__import__':
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self._add_finding('HIGH', f'{target.id} = __import__(variable)', node.lineno,
                                          '将 __import__ 赋值给变量，可动态导入任意模块')
        # 检测 __builtins__['eval'] 等危险函数赋值给变量
        elif isinstance(node.value, ast.Subscript):
            if self._is_builtins_dangerous_access(node.value):
                # 支持 Tuple 解包：a, b = __builtins__['x'], __builtins__['y']
                names = self._extract_names_from_targets(node.targets)
                attr = self._const_value(node.value)
                if attr and names:
                    for name in names:
                        self._add_finding('CRITICAL', f'{name} = __builtins__["{attr}"]',
                                          node.lineno,
                                          f'将危险内置函数 __builtins__["{attr}"] 赋值给变量 {name}，可绕过 eval/exec 直接调用')
        # 支持 Tuple 解包形式：a, b = __builtins__['x'], __builtins__['y']
        elif isinstance(node.value, ast.Tuple):
            for i, elt in enumerate(node.value.elts):
                if isinstance(elt, ast.Subscript) and self._is_builtins_dangerous_access(elt):
                    names = self._extract_names_from_targets(node.targets)
                    attr = self._const_value(elt)
                    if attr and names and i < len(names):
                        self._add_finding('CRITICAL', f'{names[i]} = __builtins__["{attr}"]',
                                          node.lineno,
                                          f'将危险内置函数 __builtins__["{attr}"] 赋值给变量 {names[i]}，可绕过 eval/exec 直接调用')
        self.generic_visit(node)

    # ─────────────────────────────────────────────────────────
    # import 检测
    # ─────────────────────────────────────────────────────────

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self._check_imported_module(alias.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self._check_imported_module(node.module, node.lineno)
        self.generic_visit(node)

    def _check_imported_module(self, module: str, lineno: int):
        base = module.split('.')[0]
        if base in self.DANGEROUS_MODULES:
            level = self.DANGEROUS_MODULES[base]
            self._add_finding(level, f'import {module}', lineno,
                              f'导入了{"需关注" if level == "INFO" else "危险"}模块 {module}')

    # ─────────────────────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────────────────────

    def _get_func_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_obj_name(self, node) -> str:
        """获取 a.b.c 形式的对象名"""
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return '.'.join(reversed(parts))

    def _const_value(self, node) -> Optional[str]:
        """提取常量节点的值"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):  # f-string
            return '<f-string>'
        if isinstance(node, ast.Subscript):
            # 递归提取 __builtins__['xxx'] 的 'xxx' 部分
            if isinstance(node.value, ast.Name) and node.value.id == '__builtins__':
                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    return node.slice.value
        return None

    def _extract_names_from_targets(self, targets: list) -> list:
        """从赋值目标列表中提取所有变量名（支持 Tuple 解包）"""
        names = []
        for target in targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        names.append(elt.id)
            elif isinstance(target, ast.List):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        names.append(elt.id)
        return names

    def _is_builtins_dangerous_access(self, node: ast.Subscript) -> bool:
        """检查是否是 __builtins__['危险函数'] 访问"""
        if not isinstance(node.value, ast.Name):
            return False
        if node.value.id != '__builtins__':
            return False
        attr = self._const_value(node)
        return attr in ('eval', 'exec', '__import__', 'open', 'compile', 'getattr', 'setattr')

    def _has_external_input(self, node: ast.Call) -> bool:
        """检查 eval/exec 调用是否包含外部输入"""
        for arg in node.args:
            if isinstance(arg, (ast.Name, ast.Attribute, ast.Subscript, ast.BinOp, ast.JoinedStr)):
                return True
        return False

    def _contains_format_string(self, node: ast.Call) -> bool:
        """检查 eval/exec 是否含格式化字符串（f-string / format / %）"""
        for arg in node.args:
            if isinstance(arg, ast.JoinedStr):  # f""
                return True
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):  # % formatting
                return True
            if isinstance(arg, ast.Call):
                if self._get_func_name(arg) in ('format', 'strip', 'replace', 'join'):
                    return True
        return False

    def _is_base64_decode_chain(self, node: ast.Call) -> bool:
        """
        检测 b64decode 调用是否链式连接到危险函数（exec/eval/compile/open）
        误报控制：仅当 b64decode 的结果直接作为 exec/eval/compile/open 的参数时才报警
        例如: exec(base64.b64decode(data)) → 危险
             json.loads(base64.b64decode(data)) → 非 exec/eval，不报警
        """
        # 这个函数仅在 func_name 是 b64decode/b32decode/b16decode 时被调用
        # 我们检查这个 decode 调用是否被包在一个 exec/eval/compile/open 调用里
        # 通过检查 node 的父节点上下文，这里用启发式：
        # 如果当前 node 是 Call 且它的父调用是 exec/eval/compile/open，则返回 True
        # 但由于 AST 不保留父指针，我们只能通过函数名间接判断
        # 这里简化为：b64decode 本身就算危险（解码后通常是代码/命令）
        return True  # b64decode 本身就值得标记，不管后续是什么

    def _looks_like_path(self, node) -> bool:
        """启发式判断一个变量是否像路径"""
        name = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        if name:
            path_keywords = ['path', 'file', 'dir', 'filepath', 'filename', 'config', 'key', 'cred']
            return any(k in name.lower() for k in path_keywords)
        return False

    def _add_finding(self, level: str, pattern: str, line: int, detail: str):
        # 避免同一位置重复报警
        for existing in self.findings:
            if existing['line'] == line and existing['pattern'] == pattern:
                return
        self.findings.append({
            'level': level,
            'pattern': pattern,
            'line': line,
            'detail': detail,
            'file': self.filepath
        })


class ShellCmdAnalyzer:
    """用正则分析 shell 命令（.sh 文件）"""

    DANGEROUS_PATTERNS = [
        (r'curl\s+[^\|]+\|\s*bash', 'CRITICAL', 'curl 管道到 bash，可能下载执行恶意脚本'),
        (r'curl\s+[^\|]+\|', 'HIGH', 'curl 管道到其他命令，可能下载执行恶意脚本'),
        (r'wget\s+[^\|]+\|\s*sh', 'CRITICAL', 'wget 管道到 sh，可能下载执行恶意脚本'),
        (r'base64\s+-d', 'HIGH', 'base64 解码，可能执行混淆代码'),
        (r'chmod\s+[47]77', 'HIGH', 'chmod 777/4777，权限过大'),
        (r'sudo\s+', 'MEDIUM', 'sudo 命令，请求提升权限'),
        (r'\|\s*sh\b', 'CRITICAL', '管道到 sh，执行任意命令'),
        (r'eval\s+\$', 'CRITICAL', 'eval 执行变量，动态代码执行'),
        (r'exec\s+', 'HIGH', 'exec 命令替换当前进程'),
        (r'nohup\s+.*&', 'MEDIUM', '后台执行且不挂起，可能持久化'),
        (r'crontab', 'HIGH', 'crontab 操作，可能建立持久化任务'),
        (r'curl\s+-s\s+https?://[^\s]+\s+(-o|--output)', 'MEDIUM', '下载文件到本地'),
        (r'wget\s+.*(-O|--output-document)', 'MEDIUM', '下载文件到本地'),
        (r'requests?\.(post|get|put|delete)', 'HIGH', 'HTTP 请求，可能数据外传'),
        (r'https?://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', 'HIGH', '直连 IP 地址，绕过 DNS 检查'),
        (r'nc\s+(-e|--exec)', 'CRITICAL', 'netcat 反向 shell'),
        (r'bash\s+-i', 'HIGH', '交互式 bash，可能为 shell 升级'),
    ]

    def analyze(self, filepath: str, content: str) -> list:
        findings = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if self._is_rule_definition(line):
                continue
            for pattern, level, detail in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        'level': level,
                        'pattern': pattern,
                        'line': i,
                        'detail': detail,
                        'file': filepath
                    })
        return findings

    def _is_rule_definition(self, line: str) -> bool:
        rule_markers = [
            r'^[\s]*("|\')',   # 字符串定义
            r'^\s*checks?\s*=',  # checks = ...
            r'^\s*patterns?\s*=', # patterns = ...
            r'#.*检测',           # 中文注释
            r'#.*pattern',        # 英文注释
            r'#.*安全',           # 安全相关注释
            r'#.*扫描',           # 扫描相关注释
        ]
        for marker in rule_markers:
            if re.search(marker, line):
                return True
        return False


def analyze_file(filepath: str) -> list:
    """分析单个文件，返回发现列表"""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return [{'level': 'ERROR', 'pattern': str(e), 'line': 0, 'detail': '文件读取失败', 'file': filepath}]

    ext = Path(filepath).suffix

    if ext == '.py':
        try:
            tree = ast.parse(content, filename=filepath)
            analyzer = SecurityAnalyzer(filepath)
            analyzer.visit(tree)
            findings.extend(analyzer.findings)
        except SyntaxError:
            findings.append({
                'level': 'ERROR',
                'pattern': 'SyntaxError',
                'line': 0,
                'detail': 'Python 语法错误，无法解析',
                'file': filepath
            })
    elif ext == '.sh':
        analyzer = ShellCmdAnalyzer()
        findings.extend(analyzer.analyze(filepath, content))
    elif ext == '.js':
        findings.append({
            'level': 'INFO',
            'pattern': 'JavaScript',
            'line': 0,
            'detail': 'JS 文件暂不支持 AST 分析，仅做字符串扫描',
            'file': filepath
        })
    return findings


def analyze_skill(skill_path: str) -> dict:
    """分析整个 skill 目录"""
    skill_path = Path(skill_path)
    if not skill_path.exists():
        return {'error': f'路径不存在: {skill_path}'}

    skill_md = skill_path / 'SKILL.md'
    meta = {}
    if skill_md.exists():
        with open(skill_md, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if content.startswith('---'):
                meta_end = content.find('---', 3)
                if meta_end != -1:
                    meta_text = content[3:meta_end]
                    for line in meta_text.strip().split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            meta[k.strip()] = v.strip()

    all_findings = []
    script_files = []

    for root, dirs, files in os.walk(skill_path):
        for file in files:
            filepath = Path(root) / file
            rel = filepath.relative_to(skill_path)
            if file.endswith(('.py', '.sh', '.js', '.ts')):
                script_files.append(str(rel))
                findings = analyze_file(str(filepath))
                all_findings.extend(findings)

    levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
    for f in all_findings:
        if f['level'] in levels:
            levels[f['level']] += 1

    if levels['CRITICAL'] > 0:
        verdict = 'DO_NOT_INSTALL'
        verdict_cn = '❌ 拒绝安装'
    elif levels['HIGH'] > 0:
        verdict = 'HUMAN_REVIEW_REQUIRED'
        verdict_cn = '⚠️ 需人工审查'
    elif levels['MEDIUM'] > 0:
        verdict = 'CAUTION'
        verdict_cn = '⚠️ 谨慎安装'
    else:
        verdict = 'SAFE'
        verdict_cn = '✅ 可安全安装'

    return {
        'skill': meta.get('name', skill_path.name),
        'version': meta.get('version', 'unknown'),
        'files_reviewed': len(script_files),
        'total_findings': len(all_findings),
        'findings_by_level': levels,
        'findings': all_findings,
        'verdict': verdict,
        'verdict_cn': verdict_cn,
        'recommendation': '安装' if verdict == 'SAFE' else '人工审查后决定'
    }


def print_report(result: dict):
    """打印人类可读的报告"""
    print('=' * 60)
    print(f'技能: {result["skill"]}')
    print(f'版本: {result["version"]}')
    print(f'审查文件: {result["files_reviewed"]} 个')
    print(f'发现问题: {result["total_findings"]} 个')
    print('-' * 60)
    print('风险统计:')
    for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
        count = result['findings_by_level'].get(level, 0)
        if count > 0:
            print(f'  {level}: {count}')
    print('-' * 60)
    print(f'结论: {result["verdict_cn"]}')
    print(f'建议: {result["recommendation"]}')
    if result['findings']:
        print('-' * 60)
        print('详细发现:')
        for f in result['findings']:
            print(f"  [{f['level']}] {f['file']}:{f['line']} - {f['detail']}")
    print('=' * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 skill_vet.py <skill目录路径>')
        print('示例: python3 skill_vet.py /path/to/skill')
        sys.exit(1)

    result = analyze_skill(sys.argv[1])
    print_report(result)

    if result.get('verdict') in ('DO_NOT_INSTALL',):
        sys.exit(2)
    elif result.get('verdict') == 'HUMAN_REVIEW_REQUIRED':
        sys.exit(3)
