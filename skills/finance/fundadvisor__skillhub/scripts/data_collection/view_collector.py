# -*- coding: utf-8 -*-
"""
基金经理观点采集脚本（v2026Q2 重写版）
从东方财富/天天基金获取最新定期报告中的基金经理观点：
  1. api.fund.eastmoney.com/f10/JJGG      → 最新定期报告列表（新→旧）
  2. np-cnotice-stock.eastmoney.com       → 报告 PDF 附件地址
  3. pdf.dfcfw.com                        → PDF 正文（含腾讯 EdgeOne 反爬挑战，本地求解）
  4. PyPDF2 提取 §4 管理人报告的「运作分析 / 展望」段落

当前目标报告期：2026 年二季报（2026-07 集中披露），兼顾 2026 一季报 / 2025 年报。

用法:
  python view_collector.py                 # 采集全部经理（按规模优先）
  python view_collector.py --limit 800     # 只采前 800 只基金
  python view_collector.py --workers 4     # 并发线程数（默认 4）
"""
import argparse
import io
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from PyPDF2 import PdfReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

from fund_advisor_paths import load_json_data  # noqa: E402

# 目标报告期：Q2 2026（公告集中披露于 2026-07），兼顾近两期年报/季报
REPORT_TYPES_LABEL = ['2026年二季报', '2026年一季报', '2025年年报']
MIN_REPORT_DATE = '2025-12-01'
QUARTER_TAG = '2026Q2'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 公告标题中需要排除的非正文类公告
_EXCLUDE_TITLE = ('摘要', '提示性', '英文', '取消', '更正', '补充', '公告的', '提示')
_INCLUDE_TITLE = ('年度报告', '季度报告', '中期报告', '半年报')


class ViewCollector:
    """基金经理观点采集器（Q2 2026 季报版）"""

    def __init__(self, workers=4, delay=0.2):
        self.workers = workers
        self.delay = delay
        self._local = threading.local()

    # ---------------- 基础 HTTP ----------------

    @property
    def session(self):
        """每线程独立 Session（线程安全）"""
        if not hasattr(self._local, 'session'):
            s = requests.Session()
            s.headers.update({
                'User-Agent': UA,
                'Accept': '*/*',
                'Referer': 'https://fundf10.eastmoney.com/',
            })
            self._local.session = s
        return self._local.session

    def load_managers(self):
        """加载经理数据（优先蒸馏库，列式压缩格式经 load_json_data 透明解码）"""
        try:
            data = load_json_data('fund_managers_distilled.json')
            managers = data.get('items') or data.get('managers') or []
            if managers:
                return {'managers': managers}
        except Exception as e:
            print(f"读取蒸馏经理库失败: {e}")
        legacy = os.path.join(DATA_DIR, 'fund_managers.json')
        with open(legacy, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ---------------- 1. 报告列表 ----------------

    def get_recent_reports(self, fund_code, limit=2):
        """获取最新定期报告列表（原始 JJGG 接口，新→旧排序）"""
        reports = []
        try:
            resp = self.session.get(
                'http://api.fund.eastmoney.com/f10/JJGG',
                params={
                    'fundcode': fund_code,
                    'pageIndex': 1,
                    'pageSize': 20,
                    'type': 3,
                    '_': int(time.time() * 1000),
                },
                timeout=15,
            )
            data = (resp.json() or {}).get('Data') or []
            for row in data:
                title = str(row.get('TITLE', ''))
                date = str(row.get('PUBLISHDATEDesc') or row.get('PUBLISHDATE', ''))[:10]
                report_id = str(row.get('ID', ''))
                if not report_id or date < MIN_REPORT_DATE:
                    continue
                if not any(kw in title for kw in _INCLUDE_TITLE):
                    continue
                if any(kw in title for kw in _EXCLUDE_TITLE):
                    continue
                reports.append({
                    'title': title,
                    'date': date,
                    'report_id': report_id,
                    'fund_code': fund_code,
                })
                if len(reports) >= limit:
                    break
        except Exception:
            pass
        return reports

    # ---------------- 2. PDF 获取（含反爬挑战求解） ----------------

    def _get_attach_url(self, report_id):
        """从公告内容接口拿 PDF 附件地址"""
        try:
            resp = self.session.get(
                'https://np-cnotice-stock.eastmoney.com/api/content/ann',
                params={'art_code': report_id, 'client_source': 'web', 'page_index': 1},
                timeout=15,
            )
            attach = ((resp.json() or {}).get('data') or {}).get('attach_list') or []
            for a in attach:
                url = a.get('attach_url', '')
                if url.lower().endswith('.pdf') or '.pdf' in url.lower():
                    return url
        except Exception:
            pass
        return None

    def _fetch_pdf(self, url):
        """下载 PDF；遇到腾讯 EdgeOne 反爬挑战时在本地求解 cookie 后重试"""
        resp = self.session.get(url, timeout=40)
        if resp.content[:4] == b'%PDF':
            return resp.content
        text = resp.text or ''
        if 'EO_Bot_Ssid' not in text:
            return None
        # 挑战脚本：cookie EO_Bot_Ssid=<常量>；__tst_status=<三个常量之和>#
        ssid = re.search(r'case"3":t=a\[_0x649a\("0x7"\)\]\(t,(\d+)\)', text)
        nums = re.findall(r'(?:WTKkN|bOYDu|wyeCN):(\d+)', text)
        if not ssid or len(nums) < 3:
            return None
        total = sum(int(v) for v in nums)
        domain = re.sub(r'^https?://([^/]+)/.*$', r'\1', url)
        self.session.cookies.set('__tst_status', f'{total}#', domain=domain, path='/')
        self.session.cookies.set('EO_Bot_Ssid', ssid.group(1), domain=domain, path='/')
        resp2 = self.session.get(url, timeout=40)
        if resp2.content[:4] == b'%PDF':
            return resp2.content
        return None

    # ---------------- 3. 正文解析 ----------------

    @staticmethod
    def _extract_section(text, start_patterns, stop_patterns, max_len=1200):
        """从 PDF 全文中抽取指定章节段落"""
        for pat in start_patterns:
            m = re.search(pat, text)
            if not m:
                continue
            start = m.end()
            end = len(text)
            for sp in stop_patterns:
                sm = re.search(sp, text[start:start + 6000])
                if sm:
                    end = min(end, start + sm.start())
                    break
            section = text[start:end]
            section = re.sub(r'\s+', ' ', section).strip()
            # 去掉残留的章节编号/标题（如 "4.4.1 报告期内基金投资策略和运作分析"）
            section = re.sub(r'^\d+(\.\d+)*\s*[^，。；：:]{0,40}(分析|说明|展望|表现)[的说明]*[：:]*\s*', '', section)
            if len(section) >= 50:
                return section[:max_len]
        return ''

    def parse_report_text(self, text):
        """从季报 PDF 全文中提取 运作分析 / 业绩说明 / 后市展望"""
        stop_pats = [r'\n?\s*4\.[5-9]\s', r'\n?\s*§?\s*5\s*[ \u3000]?[^.\d]', r'重大\s*事项']
        analysis = self._extract_section(
            text,
            [r'报告期内基金的投资策略和运作分析[的说明]*[：:]*',
             r'报告期内基金的投资策略和业绩表现说明[：:]*'],
            stop_pats, max_len=1000)
        outlook = self._extract_section(
            text,
            [r'管理人对宏观经济[、，]?证券市场及行业走势的简要展望[：:]*',
             r'(?:后市|市场|季度)\s*展望[：:]*'],
            stop_pats, max_len=800)
        performance = self._extract_section(
            text,
            [r'报告期内基金的业绩表现[：:]*'],
            stop_pats, max_len=400)
        return {'analysis': analysis, 'outlook': outlook, 'performance': performance}

    def fetch_report_content(self, report_id, report_title=''):
        """获取单份报告的观点内容"""
        content = {'title': report_title, 'analysis': '', 'outlook': '', 'performance': ''}
        try:
            pdf_url = self._get_attach_url(report_id)
            if not pdf_url:
                return content
            pdf_bytes = self._fetch_pdf(pdf_url)
            if not pdf_bytes:
                return content
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = ''
            for p in reader.pages[:12]:  # 管理人报告在前几页，无需全文
                text += (p.extract_text() or '') + '\n'
            parsed = self.parse_report_text(text)
            content.update(parsed)
        except Exception:
            pass
        return content

    # ---------------- 4. 批量采集 ----------------

    def _collect_one(self, manager):
        """采集单个经理最新报告观点"""
        fund_code = str(manager.get('current_fund_code', ''))
        if not fund_code or len(fund_code) != 6 or not fund_code.isdigit():
            return None
        time.sleep(self.delay)
        reports = self.get_recent_reports(fund_code, limit=2)
        for report in reports:
            content = self.fetch_report_content(report['report_id'], report['title'])
            if content.get('analysis') or content.get('outlook'):
                return {
                    'manager_id': manager.get('manager_id'),
                    'manager_name': manager.get('name', ''),
                    'company': manager.get('company_name', ''),
                    'fund_code': fund_code,
                    'fund_name': manager.get('current_fund_name', ''),
                    'report_date': report.get('date', ''),
                    'report_title': report.get('title', ''),
                    'views': content.get('analysis', ''),
                    'outlook': content.get('outlook', ''),
                    'performance': content.get('performance', ''),
                    'quarter': QUARTER_TAG,
                }
        return None

    def collect_views_for_managers(self, managers, sample_size=None, sort_by_scale=True):
        """批量采集经理观点（并发）"""
        # 过滤出有效基金代码的经理，按管理规模降序（规模大的优先）
        valid = []
        for m in managers:
            fc = str(m.get('current_fund_code', ''))
            if len(fc) == 6 and fc.isdigit():
                try:
                    scale = float(str(m.get('total_scale', '0')).replace('亿', '').replace('元', '') or 0)
                except (ValueError, TypeError):
                    scale = 0.0
                valid.append((scale, m))
        if sort_by_scale:
            valid.sort(key=lambda x: -x[0])
        targets = [m for _, m in valid]
        if sample_size:
            targets = targets[:sample_size]

        total = len(targets)
        print(f"开始采集 {total} 位经理的观点（并发 {self.workers}）...")
        views_data = []
        done = 0
        fail = 0
        start = time.time()

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(self._collect_one, m): m for m in targets}
            for fut in as_completed(futures):
                try:
                    rec = fut.result()
                    if rec:
                        views_data.append(rec)
                    else:
                        fail += 1
                except Exception:
                    fail += 1
                done += 1
                if done % 50 == 0 or done == total:
                    elapsed = time.time() - start
                    rate = done / elapsed if elapsed > 0 else 0
                    eta = (total - done) / rate / 60 if rate > 0 else 0
                    print(f"进度: {done}/{total} 成功={len(views_data)} 无内容={fail} "
                          f"速率={rate:.1f}/s ETA={eta:.0f}min")

        return len(views_data), views_data

    # ---------------- 5. 保存 ----------------

    def save_views_data(self, views_data):
        """保存观点数据（替换旧占位数据，真实季报观点）"""
        views_file = os.path.join(DATA_DIR, 'manager_views.json')
        payload = {
            'views': views_data,
            'meta': {
                'total_views': len(views_data),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网/东方财富 定期报告PDF',
                'report_types': REPORT_TYPES_LABEL,
                'quarter': QUARTER_TAG,
            }
        }
        with open(views_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"观点数据已保存: {views_file} ({len(views_data)} 条)")


def main():
    parser = argparse.ArgumentParser(description='基金经理季报观点采集（2026Q2）')
    parser.add_argument('--limit', type=int, default=None, help='采集基金数上限（默认全部有效经理）')
    parser.add_argument('--workers', type=int, default=4, help='并发线程数')
    parser.add_argument('--delay', type=float, default=0.2, help='每请求间隔秒数')
    args = parser.parse_args()

    collector = ViewCollector(workers=args.workers, delay=args.delay)

    print("=" * 60)
    print("基金经理观点采集（2026年二季报为主，兼顾近两期年报/季报）")
    print("=" * 60)

    data = collector.load_managers()
    managers = data.get('managers', [])
    print(f"共 {len(managers)} 个基金经理")

    updated_count, views_data = collector.collect_views_for_managers(
        managers, sample_size=args.limit)

    collector.save_views_data(views_data)

    print("\n采集完成!")
    print(f"观点记录: {len(views_data)}")


if __name__ == "__main__":
    main()
