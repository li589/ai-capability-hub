#!/usr/bin/env python3
"""
Dependency CVE Checker - 依赖漏洞检查器
使用 OSV.dev API 检查 skill 依赖中的已知安全漏洞

支持格式：
  - requirements.txt（Python）
  - package.json（Node.js/npm）
  - Gemfile（Ruby）
  - go.mod（Go）
  - composer.json（PHP）
  - pom.xml / build.gradle（JVM）
  - Cargo.toml（Rust）
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


OSV_API = 'https://api.osv.dev/v1/query'


def query_osv(package_name: str, version: str = None, ecosystem: str = None) -> dict:
    """
    查询 OSV 数据库
    ecosystem: PyPI, npm, Go, RubyGems, Packagist, Maven, Crates.io
    """
    payload = {}

    if version:
        # 按版本查询
        payload = {
            'package': {'name': package_name, 'version': version},
            'package': {'name': package_name, 'ecosystem': ecosystem} if ecosystem else {'name': package_name},
            'version': version
        }
    else:
        # 按包名查询（列出所有已知漏洞）
        payload = {
            'package': {'name': package_name}
        }

    # OSV API 格式
    query = {
        'package': {'name': package_name}
    }
    if ecosystem:
        query['package']['ecosystem'] = ecosystem
    if version:
        query['version'] = version

    try:
        data = json.dumps(query).encode('utf-8')
        req = urllib.request.Request(
            OSV_API,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result
    except Exception as e:
        return {'error': str(e)}


def parse_requirements_txt(content: str) -> list:
    """解析 requirements.txt，提取包名和版本"""
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # 处理 ==, >=, <=, ~, <, > 等版本格式
        # 去除 extras，如 requests[security]
        name = re.split(r'[!<>=~]', line)[0].strip()
        name = re.sub(r'\[.*\]', '', name).strip()
        if name:
            version_match = re.search(r'==\s*([0-9][^\s;]*)', line)
            version = version_match.group(1) if version_match else None
            packages.append({'name': name, 'version': version, 'ecosystem': 'PyPI'})
    return packages


def parse_package_json(content: str) -> list:
    """解析 package.json，提取生产依赖"""
    try:
        data = json.loads(content)
        packages = []
        deps = data.get('dependencies', {})
        dev_deps = data.get('devDependencies', {})
        # 只检查生产依赖
        for name, version_spec in deps.items():
            # 提取版本号（去除 ^, ~, >= 等）
            version = re.sub(r'[\^~>=<!*]', '', version_spec).strip()
            if not version:
                version = None
            packages.append({'name': name, 'version': version, 'ecosystem': 'npm'})
        return packages
    except Exception:
        return []


def parse_gemfile(content: str) -> list:
    """解析 Gemfile"""
    packages = []
    for line in content.splitlines():
        m = re.match(r'\s*gem\s+["\']([^"\']+)["\'](.*)', line)
        if m:
            name = m.group(1)
            version_spec = m.group(2)
            version = re.sub(r'[\^~>=<!*]', '', version_spec).strip()
            packages.append({'name': name, 'version': version or None, 'ecosystem': 'RubyGems'})
    return packages


def parse_go_mod(content: str) -> list:
    """解析 go.mod"""
    packages = []
    in_require = False
    for line in content.splitlines():
        line = line.strip()
        if line == 'require (' or line.startswith('require ('):
            in_require = True
            continue
        if line == ')':
            in_require = False
            continue
        if in_require or (line and not line.startswith('//') and not line.startswith('module')):
            m = re.match(r'\s*([^\s]+)\s+v?([0-9]', line)
            if m:
                packages.append({'name': m.group(1), 'version': m.group(2), 'ecosystem': 'Go'})
    return packages


def parse_composer_json(content: str) -> list:
    """解析 composer.json"""
    try:
        data = json.loads(content)
        packages = []
        for name, version_spec in data.get('require', {}).items():
            if name == 'php' or name.startswith('ext-'):
                continue  # 跳过 PHP 版本和扩展
            version = re.sub(r'[\^~>=<!*]', '', version_spec).strip()
            packages.append({'name': name, 'version': version or None, 'ecosystem': 'Packagist'})
        return packages
    except Exception:
        return []


def parse_cargo_toml(content: str) -> list:
    """解析 Cargo.toml"""
    packages = []
    in_deps = False
    for line in content.splitlines():
        line = line.strip()
        if line == '[dependencies]' or line == '[dev-dependencies]':
            in_deps = True
            continue
        if line.startswith('['):
            in_deps = False
            continue
        if in_deps:
            m = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']', line)
            if m:
                version = re.sub(r'[\^~>=<!*]', '', m.group(2)).strip()
                packages.append({'name': m.group(1), 'version': version, 'ecosystem': 'Crates.io'})
    return packages


def find_dependency_files(skill_path: str) -> dict:
    """查找 skill 目录中的依赖声明文件"""
    skill_path = Path(skill_path)
    found = {}

    patterns = {
        'requirements.txt': ('python', parse_requirements_txt),
        'package.json': ('nodejs', parse_package_json),
        'Gemfile': ('ruby', parse_gemfile),
        'go.mod': ('go', parse_go_mod),
        'composer.json': ('php', parse_composer_json),
        'Cargo.toml': ('rust', parse_cargo_toml),
    }

    for filename, (lang, parser) in patterns.items():
        filepath = skill_path / filename
        if filepath.exists():
            try:
                content = filepath.read_text(encoding='utf-8')
                packages = parser(content)
                if packages:
                    found[filename] = {
                        'lang': lang,
                        'filepath': str(filepath),
                        'packages': packages
                    }
            except Exception as e:
                found[filename] = {'error': str(e)}

    return found


def check_package_vulns(package: dict, rate_limit_delay: float = 0.5) -> list:
    """检查单个包的漏洞，返回漏洞列表"""
    name = package['name']
    version = package.get('version')
    ecosystem = package.get('ecosystem')

    time.sleep(rate_limit_delay)  # 避免过快请求

    if version:
        result = query_osv(name, version, ecosystem)
    else:
        result = query_osv(name, ecosystem=ecosystem)

    vulns = []
    if 'vulns' in result and result['vulns']:
        for v in result['vulns']:
            vulns.append({
                'id': v.get('id', 'N/A'),
                'summary': v.get('summary', 'No summary'),
                'severity': _infer_severity(v),
                'aliases': v.get('aliases', []),
                'published': v.get('published', ''),
                'affected': v.get('affected', [])
            })

    return vulns


def _infer_severity(vuln: dict) -> str:
    """从 CVSS 或 severity 字段推断严重等级"""
    # 尝试从 database_specific 提取
    db_specific = vuln.get('database_specific', {})
    if 'severity' in db_specific:
        sev = db_specific['severity']
        if isinstance(sev, list) and len(sev) > 0:
            sev = sev[0]
        if isinstance(sev, dict):
            sev = sev.get('score', '').upper()
        if 'CRITICAL' in str(sev).upper():
            return 'CRITICAL'
        elif 'HIGH' in str(sev).upper():
            return 'HIGH'
        elif 'MEDIUM' in str(sev).upper() or 'MODERATE' in str(sev).upper():
            return 'MEDIUM'
        elif 'LOW' in str(sev).upper():
            return 'LOW'
    return 'MEDIUM'  # 默认


class DependencyCVEChecker:
    """依赖 CVE 检查器"""

    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.dep_files = {}
        self.vulns_found = []
        self.packages_checked = 0

    def run(self) -> dict:
        """执行完整检查"""
        results = {
            'skill_path': str(self.skill_path),
            'timestamp': datetime.now().isoformat(),
            'dep_files': {},
            'total_vulns': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'packages_checked': 0,
            'vulnerable_packages': [],
            'errors': []
        }

        # 1. 查找依赖文件
        self.dep_files = find_dependency_files(str(self.skill_path))
        results['dep_files'] = {k: {kk: vv for kk, vv in v.items() if kk != 'packages'}
                                 for k, v in self.dep_files.items()}

        # 2. 逐个检查每个包的漏洞
        for dep_file, info in self.dep_files.items():
            if 'error' in info:
                results['errors'].append(f"{dep_file}: {info['error']}")
                continue

            for pkg in info.get('packages', []):
                self.packages_checked += 1
                results['packages_checked'] = self.packages_checked

                try:
                    vulns = check_package_vulns(pkg)
                    if vulns:
                        for v in vulns:
                            severity = v.get('severity', 'MEDIUM')
                            results['by_severity'][severity] = results['by_severity'].get(severity, 0) + 1
                            results['total_vulns'] += 1
                            results['vulnerable_packages'].append({
                                'package': pkg['name'],
                                'version': pkg.get('version'),
                                'ecosystem': pkg.get('ecosystem'),
                                'dep_file': dep_file,
                                'vuln_id': v['id'],
                                'severity': severity,
                                'summary': v['summary'][:200]
                            })
                except Exception as e:
                    results['errors'].append(f"{pkg['name']}: {e}")

        # 汇总
        if results['total_vulns'] == 0:
            results['verdict'] = 'CLEAN'
        elif results['by_severity']['CRITICAL'] > 0 or results['by_severity']['HIGH'] > 3:
            results['verdict'] = 'HIGH_RISK'
        elif results['by_severity']['HIGH'] > 0 or results['by_severity']['MEDIUM'] > 3:
            results['verdict'] = 'MEDIUM_RISK'
        else:
            results['verdict'] = 'LOW_RISK'

        return results


def print_report(results: dict):
    """打印人类可读的报告"""
    print('=' * 60)
    print('🔍 依赖漏洞检查报告')
    print('=' * 60)
    print(f'技能路径: {results["skill_path"]}')
    print(f'检查时间: {results["timestamp"]}')
    print(f'依赖文件: {len(results["dep_files"])} 个')
    print(f'检查包数: {results["packages_checked"]} 个')
    print('-' * 60)
    print(f'漏洞总数: {results["total_vulns"]}')
    print(f'  CRITICAL: {results["by_severity"]["CRITICAL"]}')
    print(f'  HIGH: {results["by_severity"]["HIGH"]}')
    print(f'  MEDIUM: {results["by_severity"]["MEDIUM"]}')
    print(f'  LOW: {results["by_severity"]["LOW"]}')
    print('-' * 60)

    if results['total_vulns'] == 0:
        print('✅ 未发现已知漏洞')
    else:
        print(f'⚠️  发现 {results["total_vulns"]} 个已知漏洞:')
        for v in results['vulnerable_packages']:
            sev = v['severity']
            print(f'\n  [{sev}] {v["package"]}@{v["version"]} ({v["ecosystem"]})')
            print(f'      漏洞ID: {v["vuln_id"]}')
            print(f'      摘要: {v["summary"]}')

    if results['errors']:
        print('-' * 60)
        print(f'错误: {len(results["errors"])} 个')
        for err in results['errors'][:5]:
            print(f'  - {err}')

    print('=' * 60)
    print(f'综合判定: {results["verdict"]}')
    print()
    print('--- JSON OUTPUT ---')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 dependency_cve_checker.py <skill路径>')
        print('示例: python3 dependency_cve_checker.py /path/to/skill')
        sys.exit(1)

    skill_path = sys.argv[1]
    checker = DependencyCVEChecker(skill_path)
    results = checker.run()
    print_report(results)

    # 根据漏洞等级退出
    if results['verdict'] == 'HIGH_RISK':
        sys.exit(3)
    elif results['verdict'] == 'MEDIUM_RISK':
        sys.exit(2)
    elif results['verdict'] == 'LOW_RISK':
        sys.exit(1)
