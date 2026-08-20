# -*- coding: utf-8 -*-
"""
数据完整性验证工具
验证机构名单、注册表等数据文件的完整性和格式正确性

使用方式：
    python scripts/data_validator.py

功能：
    1. 验证机构注册表（institution_registry.json）
    2. 验证各类机构名单文件（*_list.json）
    3. 输出详细的验证报告
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 数据目录
SKILL_DATA_DIR = Path(__file__).parent.parent / "data"


def validate_institution_registry() -> Tuple[bool, str, Dict[str, Any]]:
    """
    验证机构注册表

    Returns:
        (是否通过, 消息, 详细信息)
    """
    registry_file = SKILL_DATA_DIR / "institution_registry.json"

    if not registry_file.exists():
        return False, "文件不存在", {"file": "institution_registry.json"}

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查格式
        if '_f' not in data:
            return False, "文件格式不正确，缺少 _f 字段", {"file": "institution_registry.json"}

        if 'd' not in data:
            return False, "文件格式不正确，缺少 d 字段", {"file": "institution_registry.json"}

        # 检查列定义
        expected_columns = ['id', 'name', 'code', 'type', 'data_source', 'update_time', 'website', 'url_source']
        actual_columns = data.get('c', [])

        if actual_columns != expected_columns:
            return False, f"列定义不匹配", {
                "expected": expected_columns,
                "actual": actual_columns
            }

        # 检查数据行数
        institutions = data['d']
        if len(institutions) == 0:
            return False, "机构数据为空", {"file": "institution_registry.json"}

        # 统计各类型机构
        type_counts = {}
        for row in institutions:
            if len(row) >= 4:
                inst_type = row[3]
                type_counts[inst_type] = type_counts.get(inst_type, 0) + 1

        return True, f"验证通过，共 {len(institutions)} 家机构", {
            "file": "institution_registry.json",
            "total": len(institutions),
            "types": type_counts
        }

    except json.JSONDecodeError as e:
        return False, f"JSON 解析错误: {e}", {"file": "institution_registry.json"}
    except Exception as e:
        return False, f"验证失败: {e}", {"file": "institution_registry.json"}


def validate_list_file(filepath: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """
    验证单个机构名单文件

    Args:
        filepath: 文件路径

    Returns:
        (是否通过, 消息, 详细信息)
    """
    filename = filepath.name

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查基本结构
        if not isinstance(data, dict):
            return False, "文件格式不正确，应为 JSON 对象", {"file": filename}

        # 检查 type 字段
        if 'type' not in data:
            return False, "缺少 type 字段", {"file": filename}

        # 检查 institutions 字段
        if 'institutions' not in data:
            return False, "缺少 institutions 字段", {"file": filename}

        institutions = data['institutions']
        if not isinstance(institutions, list):
            return False, "institutions 字段应为数组", {"file": filename}

        if len(institutions) == 0:
            return False, "机构列表为空", {"file": filename}

        # 检查每条记录
        invalid_records = []
        for i, inst in enumerate(institutions):
            if not isinstance(inst, dict):
                invalid_records.append(f"记录 {i}: 不是对象")
                continue

            if 'name' not in inst:
                invalid_records.append(f"记录 {i}: 缺少 name 字段")

        if invalid_records:
            return False, f"数据格式错误", {
                "file": filename,
                "errors": invalid_records[:5]  # 只显示前5个错误
            }

        # 提取元数据
        metadata = {
            "file": filename,
            "type": data.get('type', '未知'),
            "count": len(institutions),
            "data_source": data.get('data_source', '未知'),
            "update_time": data.get('update_time', '未知')
        }

        return True, f"验证通过，共 {len(institutions)} 家机构", metadata

    except json.JSONDecodeError as e:
        return False, f"JSON 解析错误: {e}", {"file": filename}
    except Exception as e:
        return False, f"验证失败: {e}", {"file": filename}


def validate_all_list_files() -> Dict[str, Tuple[bool, str, Dict[str, Any]]]:
    """
    验证所有机构名单文件

    Returns:
        {文件名: (是否通过, 消息, 详细信息)}
    """
    results = {}

    # 查找所有 *_list.json 文件
    list_files = sorted(SKILL_DATA_DIR.glob("*_list.json"))

    if not list_files:
        return {"_error": (False, "未找到 *_list.json 文件", {"dir": str(SKILL_DATA_DIR)})}

    for filepath in list_files:
        results[filepath.name] = validate_list_file(filepath)

    return results


def run_full_validation() -> Dict[str, Any]:
    """
    运行完整验证

    Returns:
        验证结果字典
    """
    results = {
        "registry": None,
        "list_files": {},
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "total_institutions": 0,
            "types": {}
        }
    }

    # 验证注册表
    registry_ok, registry_msg, registry_details = validate_institution_registry()
    results["registry"] = {
        "passed": registry_ok,
        "message": registry_msg,
        "details": registry_details
    }

    results["summary"]["total"] += 1
    if registry_ok:
        results["summary"]["passed"] += 1
        results["summary"]["total_institutions"] += registry_details.get("total", 0)
    else:
        results["summary"]["failed"] += 1

    # 验证名单文件
    list_results = validate_all_list_files()
    for filename, (passed, message, details) in list_results.items():
        results["list_files"][filename] = {
            "passed": passed,
            "message": message,
            "details": details
        }

        results["summary"]["total"] += 1
        if passed:
            results["summary"]["passed"] += 1
            results["summary"]["total_institutions"] += details.get("count", 0)
            inst_type = details.get("type", "未知")
            results["summary"]["types"][inst_type] = details.get("count", 0)
        else:
            results["summary"]["failed"] += 1

    return results


def print_validation_report(results: Dict[str, Any]):
    """
    打印验证报告

    Args:
        results: 验证结果
    """
    print("\n" + "=" * 60)
    print("  数据完整性验证报告")
    print("=" * 60)

    # 注册表
    registry = results["registry"]
    status = "✓" if registry["passed"] else "✗"
    print(f"\n{status} institution_registry.json: {registry['message']}")

    if registry["passed"] and "types" in registry.get("details", {}):
        types = registry["details"]["types"]
        for inst_type, count in sorted(types.items(), key=lambda x: -x[1])[:5]:
            print(f"    - {inst_type}: {count} 家")

    # 名单文件
    print("\n机构名单文件:")
    for filename, result in sorted(results["list_files"].items()):
        status = "✓" if result["passed"] else "✗"
        print(f"  {status} {filename}: {result['message']}")

    # 汇总
    summary = results["summary"]
    print(f"\n{'=' * 60}")
    print(f"  汇总")
    print(f"{'=' * 60}")
    print(f"  文件验证: {summary['passed']}/{summary['total']} 通过")
    print(f"  机构总数: {summary['total_institutions']} 家")

    if summary.get("types"):
        print(f"\n  机构类型分布:")
        for inst_type, count in sorted(summary["types"].items(), key=lambda x: -x[1]):
            print(f"    - {inst_type}: {count} 家")

    # 结论
    print(f"\n{'=' * 60}")
    if summary["failed"] == 0:
        print("  ✓ 所有数据文件验证通过！")
    else:
        print(f"  ⚠ 有 {summary['failed']} 个文件验证失败")
        print("    请检查 data/ 目录下的 JSON 文件是否完整")
    print("=" * 60)


def main():
    """主函数"""
    print("开始数据完整性验证...")

    # 运行验证
    results = run_full_validation()

    # 打印报告
    print_validation_report(results)

    # 返回状态码
    if results["summary"]["failed"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


# ── v4.6: 日期窗口核验 ──────────────────────────────────────

def validate_date_window(articles: List[Dict[str, Any]],
                          requested_days: int = 7,
                          cutoff_date: str = "") -> Dict[str, Any]:
    """验证文章列表是否在请求的日期窗口内。

    Args:
        articles: 文章列表 [{"title": ..., "publish_time": "2026-07-28", ...}, ...]
        requested_days: 请求的时间窗口（天）
        cutoff_date: 截止日期 "YYYY-MM-DD"（留空=按 requested_days 自动计算）

    Returns:
        {
          "total": 50,
          "in_window": 48,
          "out_of_window": 2,
          "unparseable": 0,
          "out_articles": [{"title": "...", "publish_time": "2026-03-15", "age_days": 137}, ...],
          "date_range_actual": {"earliest": "2026-07-24", "latest": "2026-07-30"},
          "requested_window": "2026-07-23 ~ 2026-07-30",
          "pass": True/False,  # True 表示所有文章在窗内
        }
    """
    from datetime import datetime, timedelta

    if cutoff_date:
        cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d")
    else:
        cutoff = datetime.now() - timedelta(days=requested_days)

    total = len(articles)
    in_window = 0
    out_of_window = 0
    unparseable = 0
    out_articles: List[Dict[str, Any]] = []
    dates_found: List[str] = []

    for a in articles:
        pub = a.get("publish_time", "")
        if not pub:
            unparseable += 1
            continue
        try:
            pub_str = str(pub)[:10]
            pub_dt = datetime.strptime(pub_str, "%Y-%m-%d")
            dates_found.append(pub_str)
            if pub_dt >= cutoff:
                in_window += 1
            else:
                out_of_window += 1
                out_articles.append({
                    "title": (a.get("title", "") or "")[:60],
                    "publish_time": pub,
                    "age_days": (datetime.now() - pub_dt).days,
                    "source": a.get("source", ""),
                })
        except (ValueError, IndexError):
            unparseable += 1

    actual_range = {}
    if dates_found:
        dates_found.sort()
        actual_range = {"earliest": dates_found[0], "latest": dates_found[-1]}

    return {
        "total": total,
        "in_window": in_window,
        "out_of_window": out_of_window,
        "unparseable": unparseable,
        "out_articles": out_articles[:10],
        "date_range_actual": actual_range,
        "requested_window": f"{cutoff.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}",
        "pass": out_of_window == 0,
    }


if __name__ == "__main__":
    main()
