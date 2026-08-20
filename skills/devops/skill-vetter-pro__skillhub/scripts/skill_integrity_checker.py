#!/usr/bin/env python3
"""
Skill Integrity Checker - SHA256 哈希链校验器
确保审查过的 skill 文件在安装前未被篡改

工作流程：
  审查时 → 计算并保存哈希 → 安装时 → 重新计算 → 对比 → 判断完整性
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


def compute_sha256(filepath: str) -> str:
    """计算单个文件的 SHA256 哈希"""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR:{e}"


def compute_dir_hash(skill_path: str, exclude_patterns: list = None) -> dict:
    """
    计算 skill 目录下所有文件的 SHA256 哈希
    返回：(整体哈希, 文件哈希列表)
    """
    if exclude_patterns is None:
        exclude_patterns = ['.git', '__pycache__', '.pyc', '.DS_Store', '.gitignore']

    skill_path = Path(skill_path).resolve()
    files_hashes = []
    overall_hasher = hashlib.sha256()

    for root, dirs, files in os.walk(skill_path):
        # 过滤目录
        dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]

        for file in sorted(files):
            if any(p in file for p in exclude_patterns):
                continue

            filepath = Path(root) / file
            rel_path = str(filepath.relative_to(skill_path))
            file_hash = compute_sha256(str(filepath))

            files_hashes.append({
                'path': rel_path,
                'sha256': file_hash,
                'size': filepath.stat().st_size if filepath.exists() else 0,
                'mtime': filepath.stat().st_mtime if filepath.exists() else 0
            })

            # 纳入整体哈希（有序，保证可复现）
            overall_hasher.update(f"{rel_path}:{file_hash}".encode())

    return {
        'skill_name': skill_path.name,
        'skill_path': str(skill_path),
        'overall_hash': overall_hasher.hexdigest(),
        'files': files_hashes,
        'file_count': len(files_hashes),
        'timestamp': datetime.now().isoformat()
    }


def save_manifest(manifest: dict, output_path: str):
    """保存哈希清单到 JSON 文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def load_manifest(manifest_path: str) -> Optional[dict]:
    """加载哈希清单"""
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载清单失败: {e}", file=sys.stderr)
        return None


def verify_integrity(skill_path: str, manifest_path: str) -> dict:
    """
    验证 skill 目录的完整性
    返回：(是否完整, 差异列表)
    """
    skill_path = Path(skill_path).resolve()
    new_manifest = compute_dir_hash(str(skill_path))
    old_manifest = load_manifest(manifest_path)

    if old_manifest is None:
        return {
            'verified': False,
            'error': '无法加载清单文件',
            'new_manifest': new_manifest
        }

    differences = []

    # 1. 对比整体哈希
    if new_manifest['overall_hash'] != old_manifest['overall_hash']:
        differences.append({
            'type': 'overall_hash_mismatch',
            'old': old_manifest['overall_hash'],
            'new': new_manifest['overall_hash'],
            'detail': '整体哈希不一致，目录有变更'
        })

    # 2. 检查新增文件
    old_files = {f['path']: f for f in old_manifest['files']}
    new_files = {f['path']: f for f in new_manifest['files']}

    added = [p for p in new_files if p not in old_files]
    for path in added:
        differences.append({
            'type': 'file_added',
            'path': path,
            'sha256': new_files[path]['sha256'],
            'detail': '新增文件'
        })

    # 3. 检查删除文件
    removed = [p for p in old_files if p not in new_files]
    for path in removed:
        differences.append({
            'type': 'file_removed',
            'path': path,
            'sha256': old_files[path]['sha256'],
            'detail': '文件被删除'
        })

    # 4. 检查修改文件
    for path in old_files & new_files:
        old_sha = old_files[path]['sha256']
        new_sha = new_files[path]['sha256']
        if old_sha != new_sha:
            differences.append({
                'type': 'file_modified',
                'path': path,
                'old_sha256': old_sha,
                'new_sha256': new_sha,
                'detail': '文件内容被修改'
            })

    verified = len(differences) == 0

    return {
        'verified': verified,
        'differences': differences,
        'old_manifest': old_manifest,
        'new_manifest': new_manifest,
        'added_count': len(added),
        'removed_count': len(removed),
        'modified_count': len([d for d in differences if d['type'] == 'file_modified'])
    }


def print_manifest_report(manifest: dict):
    """打印哈希清单报告"""
    print('=' * 60)
    print('📋 Skill 哈希清单')
    print('=' * 60)
    print(f'技能名称: {manifest["skill_name"]}')
    print(f'路径: {manifest["skill_path"]}')
    print(f'整体哈希: {manifest["overall_hash"]}')
    print(f'文件数量: {manifest["file_count"]}')
    print(f'生成时间: {manifest["timestamp"]}')
    print('-' * 60)
    print('文件哈希明细:')
    for f in manifest['files']:
        size_kb = f['size'] / 1024
        print(f'  {f["sha256"][:16]}...  {size_kb:8.2f}KB  {f["path"]}')
    print('=' * 60)


def print_verify_report(result: dict):
    """打印验证结果报告"""
    print('=' * 60)
    print('🔍 Skill 完整性验证报告')
    print('=' * 60)

    if result.get('error'):
        print(f'❌ 验证失败: {result["error"]}')
        return

    new_manifest = result['new_manifest']
    print(f'技能名称: {new_manifest["skill_name"]}')
    print(f'路径: {new_manifest["skill_path"]}')
    print(f'整体哈希（旧）: {result["old_manifest"]["overall_hash"]}')
    print(f'整体哈希（新）: {new_manifest["overall_hash"]}')
    print('-' * 60)

    if result['verified']:
        print('✅ 完整性验证通过：文件未被篡改')
    else:
        print('❌ 完整性验证失败：检测到以下变更:')
        for diff in result['differences']:
            dtype = diff['type']
            if dtype == 'file_added':
                print(f'  ➕ 新增文件: {diff["path"]}')
            elif dtype == 'file_removed':
                print(f'  ➖ 删除文件: {diff["path"]}')
            elif dtype == 'file_modified':
                print(f'  ✏️  修改文件: {diff["path"]}')
                print(f'     旧: {diff["old_sha256"][:16]}...')
                print(f'     新: {diff["new_sha256"][:16]}...')

    print('-' * 60)
    print(f'汇总: +{result["added_count"]} -{result["removed_count"]} ~{result["modified_count"]}')
    print('=' * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法:')
        print('  生成清单: python3 skill_integrity_checker.py --save <skill路径> [输出路径]')
        print('  验证完整: python3 skill_integrity_checker.py --verify <skill路径> <manifest.json>')
        print('示例:')
        print('  python3 skill_integrity_checker.py --save /path/to/skill')
        print('  python3 skill_integrity_checker.py --save /path/to/skill /path/to/manifest.json')
        print('  python3 skill_integrity_checker.py --verify /path/to/skill /path/to/manifest.json')
        sys.exit(1)

    action = sys.argv[1]

    if action == '--save':
        if len(sys.argv) < 3:
            print('错误: 需要指定 skill 路径')
            sys.exit(1)
        skill_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) >= 4 else f"{Path(skill_path).name}-manifest.json"

        manifest = compute_dir_hash(skill_path)
        save_manifest(manifest, output_path)
        print(f'✅ 清单已保存: {output_path}')
        print_manifest_report(manifest)

    elif action == '--verify':
        if len(sys.argv) < 4:
            print('错误: 需要指定 skill 路径 和 manifest 文件路径')
            sys.exit(1)
        skill_path = sys.argv[2]
        manifest_path = sys.argv[3]

        result = verify_integrity(skill_path, manifest_path)
        print_verify_report(result)

        if result['verified']:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f'未知动作: {action}')
        sys.exit(1)
