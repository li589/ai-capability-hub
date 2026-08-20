#!/usr/bin/env python3
"""
v2.8.0 单元测试运行脚本

用法:
    python run_tests.py           # 运行所有测试
    python run_tests.py --quick   # 只跑核心测试（跳过 RAG 等重型测试）
    python run_tests.py --analyzers  # 只跑分析器测试
    python run_tests.py --predictors  # 只跑预测器测试
    python run_tests.py --core      # 只跑核心测试
    python run_tests.py --keep-pyc   # 保留 .pyc（不清理尾）

环境变量:
    PYTHONDONTWRITEBYTECODE=1  测试期间不生成 .pyc（推荐）
"""

import os
import sys
import unittest
from pathlib import Path

# v2.5.0: 测试期间禁用 .pyc 生成（避免上传/打包时混入二进制）
# 注意：运行中改环境变量无效（CPython 只在解释器启动时读一次），必须直接设 sys 标志
sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def _cleanup_pyc(verbose: bool = False) -> None:
    """测试结束后清理可能残留的 .pyc（防止环境变量失效）"""
    try:
        count = 0
        for pyc in PROJECT_ROOT.rglob("*.pyc"):
            try:
                pyc.unlink()
                count += 1
            except OSError:
                pass
        for cache_dir in sorted(PROJECT_ROOT.rglob("__pycache__"), reverse=True):
            try:
                if cache_dir.is_dir() and not any(cache_dir.iterdir()):
                    cache_dir.rmdir()
            except OSError:
                pass
        if verbose and count > 0:
            print(f"\n[清理] 删除 {count} 个 .pyc 缓存")
    except Exception:
        pass


def discover_and_run(test_dir: str, pattern: str = "test_*.py") -> unittest.TestSuite:
    """发现并加载测试"""
    loader = unittest.TestLoader()
    return loader.discover(test_dir, pattern=pattern, top_level_dir=str(PROJECT_ROOT))


def _load_top_level_tests() -> unittest.TestSuite:
    """v2.5.0：加载 tests/ 根目录下的顶层 test_*.py。

    此前 run_all 只发现 6 个子目录，tests/test_friendly_errors.py 等
    顶层测试文件从未被执行。此类文件是函数式测试（裸 test_* 函数），
    unittest 的 loadTestsFromModule 只收集 TestCase 子类，因此这里
    手动包装为 FunctionTestCase。加载失败仅警告不中断。
    """
    import importlib

    suite = unittest.TestSuite()
    for py in sorted((PROJECT_ROOT / "tests").glob("test_*.py")):
        if not py.is_file():
            continue
        module_name = f"tests.{py.stem}"
        try:
            module = importlib.import_module(module_name)
        except Exception as e:  # 单个测试文件损坏不应拖垮全量测试
            print(f"[警告] 无法导入顶层测试 {module_name}: {e}")
            continue
        loaded = 0
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            obj = getattr(module, name)
            if callable(obj):
                suite.addTest(unittest.FunctionTestCase(obj))
                loaded += 1
        if loaded == 0:
            print(f"[警告] 顶层测试 {module_name} 未发现 test_* 函数")
    return suite


def _count_result(result) -> tuple:
    """统计一个 TestResult：返回 (passed, failed, errors, skipped)"""
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    return passed, len(result.failures), len(result.errors), len(result.skipped)


def run_all():
    """运行所有测试"""
    print("=" * 60)
    print("  wechat-analyzer v2.8.0 单元测试")
    print("=" * 60)

    suites = [
        ("核心抽象层", str(PROJECT_ROOT / "tests" / "test_core")),
        ("分析器", str(PROJECT_ROOT / "tests" / "test_analyzers")),
        ("预测器", str(PROJECT_ROOT / "tests" / "test_predictors")),
        ("RAG 引擎", str(PROJECT_ROOT / "tests" / "test_rag")),
        ("MiroFish 图谱", str(PROJECT_ROOT / "tests" / "test_mirofish")),
        ("脚本/报告", str(PROJECT_ROOT / "tests" / "test_scripts")),
    ]

    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_errors = 0

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)

    for name, test_dir in suites:
        print(f"\n[{name}]")
        suite = discover_and_run(test_dir)
        result = runner.run(suite)
        passed, failed, errors, skipped = _count_result(result)
        total_passed += passed
        total_failed += failed
        total_errors += errors
        total_skipped += skipped

    # v2.5.0：tests/ 根目录顶层测试（此前被漏跑）
    print("\n[顶层测试]")
    top_suite = _load_top_level_tests()
    result = runner.run(top_suite)
    passed, failed, errors, skipped = _count_result(result)
    total_passed += passed
    total_failed += failed
    total_errors += errors
    total_skipped += skipped

    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"  通过: {total_passed}")
    print(f"  失败: {total_failed}")
    print(f"  错误: {total_errors}")
    print(f"  跳过: {total_skipped} (依赖未安装等)")
    print("=" * 60)

    if total_failed > 0 or total_errors > 0:
        _cleanup_pyc()
        return 1
    _cleanup_pyc()
    return 0


def run_quick():
    """快速测试（只跑核心 + 分析器）"""
    print("=" * 60)
    print("  wechat-analyzer v2.8.0 快速测试")
    print("=" * 60)

    suites = [
        ("核心", str(PROJECT_ROOT / "tests" / "test_core")),
        ("分析器", str(PROJECT_ROOT / "tests" / "test_analyzers")),
    ]

    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_skipped = 0

    for name, test_dir in suites:
        print(f"\n[{name}]")
        suite = discover_and_run(test_dir)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        total_passed += result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        total_failed += len(result.failures)
        total_errors += len(result.errors)
        total_skipped += len(result.skipped)

    print("\n" + "=" * 60)
    print(f"  通过: {total_passed} | 失败: {total_failed} | 错误: {total_errors} | 跳过: {total_skipped}")
    print("=" * 60)

    return 1 if (total_failed > 0 or total_errors > 0) else 0


def run_specific(test_type: str):
    """运行特定类型测试"""
    test_dir_map = {
        "core": str(PROJECT_ROOT / "tests" / "test_core"),
        "analyzers": str(PROJECT_ROOT / "tests" / "test_analyzers"),
        "predictors": str(PROJECT_ROOT / "tests" / "test_predictors"),
        "rag": str(PROJECT_ROOT / "tests" / "test_rag"),
        "mirofish": str(PROJECT_ROOT / "tests" / "test_mirofish"),
        "scripts": str(PROJECT_ROOT / "tests" / "test_scripts"),
    }

    if test_type not in test_dir_map:
        print(f"未知类型: {test_type}")
        print(f"可用: {', '.join(test_dir_map.keys())}")
        return 1

    print(f"运行 {test_type} 测试...")
    suite = discover_and_run(test_dir_map[test_type])
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    return 1 if (len(result.failures) > 0 or len(result.errors) > 0) else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--quick":
            sys.exit(run_quick())
        elif arg.startswith("--"):
            test_type = arg[2:]
            sys.exit(run_specific(test_type))
        else:
            print("用法: python run_tests.py [--quick|--core|--analyzers|--predictors|--rag|--mirofish|--scripts]")
            sys.exit(1)
    else:
        sys.exit(run_all())
