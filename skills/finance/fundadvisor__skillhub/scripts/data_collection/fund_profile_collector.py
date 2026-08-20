#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金产品档案采集器（fund_profile_collector.py，v10.0 新增）
============================================================
在基础产品目录（代码/名称/类型）之上，为公募基金产品补充档案字段：
  1. 基本概况页 jbgk_{code}.html   → 成立日期 / 资产规模 / 基金经理
  2. 基金概况页 jjgn_{code}.html   → 投资目标 / 投资范围 / 投资策略 / 业绩比较基准
  3. 费率页     jjfl_{code}.html   → 管理费 / 托管费 / 申购费 / 赎回费 / 最低申购金额
  4. pingzhongdata_{code}.js       → 近1月/3月/6月/1年/3年/成立以来 业绩序列（best effort）

零依赖（stdlib urllib），逐字段优雅降级：单个字段/单只基金失败不影响其余。

用法:
  python fund_profile_collector.py --codes 000001,000002,161725   # 指定代码
  python fund_profile_collector.py --limit 200                    # 从产品目录取前 N 只
  python fund_profile_collector.py --sample-mgr 30                # 从经理现任基金取 N 只（推荐）
  python fund_profile_collector.py --save                         # 合并写回 fund_products.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(SCRIPT_DIR))

from fund_advisor_paths import DATA_DIR, load_json_data  # noqa: E402
from db_format import write_products  # noqa: E402

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
REFERER = 'https://fundf10.eastmoney.com/'

# 费率页表格中的字段名 → 输出列名
_FEE_FIELD_MAP = {
    '管理费率': 'management_fee',
    '托管费率': 'custodian_fee',
    '申购费率': 'subscription_fee',
    '赎回费率': 'redemption_fee',
    '最低申购金额': 'min_subscription',
}


def http_get(url: str, timeout: int = 15, encoding: str = 'utf-8') -> str:
    """带 UA/Referer 的 HTTP GET（失败返回空串，不抛异常）"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT,
            'Referer': REFERER,
            'Accept': 'text/html,application/json,*/*',
            'Accept-Encoding': 'gzip, deflate',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # 部分接口返回 GBK 编码
            return raw.decode(encoding, errors='replace')
    except Exception:
        return ''


def _strip_html(html: str) -> str:
    """去掉 HTML 标签与空白，保留段落文本（解码 HTML 实体如 &nbsp;）"""
    import html as _html
    text = re.sub(r'<[^>]+>', '', html or '')
    text = _html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _parse_h4_sections(html: str) -> Dict[str, str]:
    """解析 fundf10 页面的 <h4>标题</h4><div class="txt_in">正文</div> 结构（兼容单/双引号）"""
    out: Dict[str, str] = {}
    for m in re.finditer(
            r'<h4[^>]*>\s*([^<]{2,20}?)\s*</h4>\s*'
            r'<div[^>]*class=["\'][^"\']*txt_in[^"\']*["\'][^>]*>(.*?)</div>',
            html or '', re.DOTALL):
        title = _strip_html(m.group(1))
        body = _strip_html(m.group(2))
        if title and body:
            out[title] = body
    return out


def _parse_table_rows(html: str) -> Dict[str, str]:
    """解析 fundf10 表格的 字段名→值 键值对（th/td 结构）"""
    out: Dict[str, str] = {}
    # 结构: <th>字段</th><td>值</td> 或 <td class=...>字段</td><td>值</td>
    for m in re.finditer(r'<t[hd][^>]*>\s*([^<]{2,20}?)\s*</t[hd]>\s*<t[hd][^>]*>\s*([^<]{1,200}?)\s*</t[hd]>',
                         html or '', re.DOTALL):
        k, v = _strip_html(m.group(1)), _strip_html(m.group(2))
        if k and v and k not in out:
            out[k] = v
    return out


class FundProfileCollector:
    """公募基金产品档案采集器"""

    def __init__(self, delay: float = 0.12):
        self.delay = delay

    # ── 单基金采集 ──────────────────────────────────────────────

    @staticmethod
    def _parse_jbgk_text(text: str) -> Dict[str, Any]:
        """从 jbgk 基本概况页的纯文本中抽取档案字段（label 内联结构）"""
        out: Dict[str, Any] = {}
        t = text or ''
        # 投资目标 → 投资范围
        m = re.search(r'投资目标\s*(.{15,800}?)\s*投资范围', t, re.DOTALL)
        if m:
            out['investment_goal'] = m.group(1).strip()[:500]
        # 投资范围 → 投资策略
        m = re.search(r'投资范围\s*(.{15,2000}?)\s*投资策略', t, re.DOTALL)
        if m:
            out['investment_scope'] = m.group(1).strip()[:600]
        # 投资策略 → 业绩比较基准 / 风险收益
        m = re.search(r'投资策略\s*(.{15,2000}?)\s*(业绩比较基准|风险收益)', t, re.DOTALL)
        if m:
            out['investment_strategy'] = m.group(1).strip()[:600]
        # 业绩比较基准 → 跟踪标的 / 风险收益
        m = re.search(r'业绩比较基准\s*([\u4e00-\u9fa5A-Za-z0-9\*\+\%\.\(\)（）,\-·]{4,120}?)\s*'
                      r'(跟踪标的|风险收益|资产配置)', t)
        if m:
            out['benchmark'] = m.group(1).strip()
        # 风险收益特征（取首段）
        m = re.search(r'风险收益特征\s*(.{15,400}?)\s*(投资目标|投资范围|投资策略|§|§)', t, re.DOTALL)
        if m:
            out['risk_level'] = m.group(1).strip()[:150]
        # 成立日期（冒号可有可无）
        m = re.search(r'成立日期[:：]?\s*(\d{4}-\d{2}-\d{2})', t)
        if m:
            out['inception_date'] = m.group(1)
        # 净资产规模
        m = re.search(r'净资产规模[:：]?\s*([\d.]+)\s*亿元', t)
        if m:
            out['scale'] = m.group(1)
        # 基金经理（捕获到「类型」前；多个经理以空格分隔）
        m = re.search(r'基金经理[:：]?\s*(.{2,40}?)\s*类型', t, re.DOTALL)
        if m:
            mgr = re.sub(r'\s+', ' ', m.group(1)).strip()
            if mgr:
                out['manager'] = mgr[:40]
        # 基金类型
        m = re.search(r'类型[:：]\s*([\u4e00-\u9fa5A-Za-z\-（）\(\)]{2,30})', t)
        if m:
            out['fund_type'] = m.group(1).strip()[:30]
        return out

    def fetch_profile(self, fund_code: str) -> Dict[str, Any]:
        """采集单只基金档案（主源 jbgk 文本；费率 jjfl 表格；业绩 pingzhongdata）"""
        code = str(fund_code).strip().zfill(6)
        rec: Dict[str, Any] = {'code': code}

        # 主源：基本概况页 jbgk（含 投资目标/范围/策略/基准/成立日/规模/经理/风险）
        self._sleep()
        html = http_get(f'https://fundf10.eastmoney.com/jbgk_{code}.html')
        if html:
            rec.update(self._parse_jbgk_text(_strip_html(html)))

        # 费率 jjfl（best effort）
        self._sleep()
        html3 = http_get(f'https://fundf10.eastmoney.com/jjfl_{code}.html')
        if html3:
            rows3 = _parse_table_rows(html3)
            for label, col in _FEE_FIELD_MAP.items():
                v = rows3.get(label, '')
                if v:
                    rec[col] = v[:80]

        # 业绩序列 pingzhongdata（best effort）
        self._sleep()
        html4 = http_get(f'https://fund.eastmoney.com/pingzhongdata/{code}.js')
        rec.update(self._parse_performance(html4))

        return rec

    @staticmethod
    def _parse_performance(js: str) -> Dict[str, Any]:
        """从 pingzhongdata 的 Data_performanceEvaluation 提取区间业绩（best effort）"""
        perf: Dict[str, Any] = {}
        if not js or 'performanceEvaluation' not in js:
            return perf
        m = re.search(r'Data_performanceEvaluation\s*=\s*(\{.*?\});', js, re.DOTALL)
        if not m:
            return perf
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return perf
        # 结构不固定：兼容 {"data":[{title,values}]} 与 {"data":{"1":[{title,values}]}}
        raw = data.get('data', [])
        items: List[dict] = []
        if isinstance(raw, dict):
            for v in raw.values():
                if isinstance(v, list):
                    items.extend(v)
        elif isinstance(raw, list):
            items = raw
        label_map = {'近1月': 'perf_1m', '近3月': 'perf_3m', '近6月': 'perf_6m',
                     '近1年': 'perf_1y', '近3年': 'perf_3y', '成立来': 'perf_since',
                     '今年以来': 'perf_ytd'}
        for it in items:
            title = str(it.get('title', ''))
            col = label_map.get(title)
            if not col:
                continue
            values = it.get('values') or []
            if not values:
                continue
            last = values[-1]
            val = last[1] if isinstance(last, (list, tuple)) and len(last) > 1 else last
            perf[col] = str(val)[:20]
        return perf

    # ── 批量采集 ────────────────────────────────────────────────

    def enrich_products(self, products: List[dict], limit: Optional[int] = None,
                        progress: bool = True) -> List[dict]:
        """为产品列表补充档案字段（原地更新并返回新列表）"""
        targets = list(products or [])
        if limit:
            targets = targets[:limit]
        total = len(targets)
        enriched: List[dict] = []
        ok = 0
        for i, p in enumerate(targets):
            code = str(p.get('code') or p.get('fund_code') or '').zfill(6)
            if not code or not code.isdigit():
                continue
            rec = self.fetch_profile(code)
            # 保留基础字段（旧列名 code/name/type/pinyin/update）
            rec['name'] = p.get('name', p.get('fund_name', ''))
            rec['type'] = p.get('type', p.get('fund_type', ''))
            rec['pinyin'] = p.get('pinyin', '')
            rec['update'] = datetime.now().strftime('%Y-%m-%d')
            enriched.append(rec)
            if rec.get('investment_scope') or rec.get('management_fee'):
                ok += 1
            if progress and ((i + 1) % 50 == 0 or i == total - 1):
                print(f"  进度: {i+1}/{total} 有档案={ok} 耗时~{(i+1)*self.delay:.0f}s")
        return enriched

    def _sleep(self):
        time.sleep(self.delay)

    # ── 落库 ────────────────────────────────────────────────────

    @staticmethod
    def save_products(enriched: List[dict], meta: Optional[dict] = None) -> Path:
        """用 db_format 新列式格式写回 fund_products.json（v10 扩宽列）"""
        path = DATA_DIR / 'fund_products.json'
        write_products(path, enriched, meta={
            'type': 'products',
            'updated': datetime.now().strftime('%Y-%m-%d'),
            'source': '天天基金 fundcode_search.js + fundf10 档案',
            'profile_enriched': len(enriched),
            **(meta or {}),
        })
        return path


def _load_base_products() -> List[dict]:
    """读取现有产品目录（列式透明解码），返回行列表"""
    try:
        data = load_json_data('fund_products.json')
        return data.get('items') or data.get('products') or []
    except FileNotFoundError:
        return []


def main():
    parser = argparse.ArgumentParser(description='基金产品档案采集（投资目标/范围/费率/业绩）')
    parser.add_argument('--codes', type=str, default='', help='基金代码，逗号分隔')
    parser.add_argument('--limit', type=int, default=0, help='从产品目录取前 N 只（0=全部）')
    parser.add_argument('--sample-mgr', type=int, default=0,
                        help='从经理现任基金中随机取 N 只（避免全库 2 万只）')
    parser.add_argument('--save', action='store_true', help='合并写回 fund_products.json')
    parser.add_argument('--delay', type=float, default=0.12, help='请求间隔秒数')
    args = parser.parse_args()

    collector = FundProfileCollector(delay=args.delay)

    if args.codes:
        codes = [c.strip() for c in args.codes.split(',') if c.strip()]
        products = [{'code': c, 'name': '', 'type': '', 'pinyin': ''} for c in codes]
    else:
        products = _load_base_products()
        if args.sample_mgr:
            try:
                mgrs = load_json_data('fund_managers_distilled.json')
                mgrs = mgrs.get('items') or mgrs.get('managers') or []
                codes = sorted({str(m.get('current_fund_code', '')).zfill(6)
                                for m in mgrs
                                if str(m.get('current_fund_code', '')).isdigit()})
                if args.sample_mgr < len(codes):
                    codes = random.sample(codes, args.sample_mgr)
                products = [{'code': c, 'name': '', 'type': '', 'pinyin': ''} for c in codes]
            except Exception as e:
                print(f'[WARN] 读取经理库失败: {e}')

    if not products:
        print('[ERROR] 没有可用产品。请先运行 update_data.py full 或指定 --codes。')
        sys.exit(1)

    print(f'开始采集 {len(products)} 只基金的产品档案...')
    enriched = collector.enrich_products(products, limit=args.limit or None)
    with_profile = sum(1 for r in enriched
                       if r.get('investment_scope') or r.get('management_fee'))
    print(f'完成: {len(enriched)} 只，其中 {with_profile} 只有档案字段')

    if args.save:
        path = collector.save_products(enriched)
        print(f'已写回: {path}')
    else:
        out = DATA_DIR / 'fund_profiles_preview.json'
        out.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'预览已保存: {out}（--save 可合并写回 fund_products.json）')


if __name__ == '__main__':
    main()
