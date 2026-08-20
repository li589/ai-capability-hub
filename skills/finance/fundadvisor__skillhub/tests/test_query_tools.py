"""test_query_tools.py — query_fund / query_manager / compare_managers 字段对齐回归

防回归: v7.2 修复前 query_fund 用错的字段名（fund_code vs 实际 code）
导致恒返回"未找到"；query_manager 大半字段为空。

轻量化后 data/ 为占位骨架、真实数据库不随包分发，本测试改为：
- 用临时样本数据（列存格式）注入 DATA_DIR，验证字段对齐
- 空骨架（占位）下降级返回"未找到"而非崩溃
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fund_advisor_paths  # noqa: E402


def _write_sample_data(tmp_path: Path) -> Path:
    """写入列存格式样本数据（与真实数据 _f/c/m 结构一致）"""
    (tmp_path / "fund_products.json").write_text(json.dumps({
        "_f": ["code", "name", "type", "pinyin", "update"],
        "c": [["000858", "000001"], ["五粮液", "测试基金"], ["混合型", "股票型"],
              ["wly", "cs"], ["", ""]],
        "m": {"count": 2},
    }), encoding="utf-8")

    # 数值列类型与真实数据一致：tenure_days=int, total_scale=float, best_return=str
    (tmp_path / "fund_managers_distilled.json").write_text(json.dumps({
        "_f": ["manager_id", "name", "company_name", "tenure_days", "total_scale",
               "best_return", "current_fund_code", "current_fund_name"],
        "c": [["M1", "M2"], ["张三", "李四"], ["示例基金公司", "另一公司"],
              [3650, 730], [100.0, 50.0], ["45.5", "20.0"],
              ["000858", "000001"], ["五粮液", "测试基金"]],
        "m": {"count": 2},
    }), encoding="utf-8")

    (tmp_path / "fund_companies_distilled.json").write_text(json.dumps({
        "companies": [{"company_id": "C1", "name": "示例基金公司"},
                      {"company_id": "C2", "name": "另一公司"}],
        "meta": {},
    }), encoding="utf-8")
    return tmp_path


@pytest.fixture
def sample_data(tmp_path, monkeypatch):
    """把 DATA_DIR 指向含样本数据的临时目录"""
    sample = _write_sample_data(tmp_path)
    import analysis.comparison_engine as ce
    monkeypatch.setattr(fund_advisor_paths, "DATA_DIR", sample)
    monkeypatch.setattr(ce, "DATA_DIR", sample)
    return sample


# ── 命中样本数据 ─────────────────────────────────────────────


def test_query_fund_found(sample_data):
    import mcp_server
    out = mcp_server.query_fund('000858')
    assert '未找到' not in out, f'query_fund(000858) 应命中样本产品目录: {out}'
    assert '(000858)' in out


def test_query_manager_found_with_real_fields(sample_data):
    import mcp_server
    out = mcp_server.query_manager('张三')
    assert '未找到' not in out, f'query_manager(张三) 应命中样本经理: {out}'
    assert '所属公司' in out
    assert '从业年限' in out


def test_compare_managers_tool(sample_data):
    import mcp_server
    out = mcp_server.compare_managers('张三,李四')
    assert '对比' in out
    assert '所属公司' in out
    assert '相似度' in out


# ── 优雅降级 ─────────────────────────────────────────────────


def test_query_fund_not_found_graceful():
    import mcp_server
    out = mcp_server.query_fund('999999')
    assert '未找到' in out


def test_compare_managers_requires_two():
    import mcp_server
    out = mcp_server.compare_managers('张坤')
    assert '至少2位' in out


def test_query_graceful_on_empty_data(tmp_path, monkeypatch):
    """空骨架（占位未初始化）下应返回未找到，而非崩溃（v10: 隔离真实数据目录，不依赖占位状态）"""
    import fund_advisor_paths
    monkeypatch.setattr(fund_advisor_paths, "DATA_DIR", tmp_path)
    import mcp_server
    assert '未找到' in mcp_server.query_fund('000001')
    assert '未找到' in mcp_server.query_manager('张坤')
