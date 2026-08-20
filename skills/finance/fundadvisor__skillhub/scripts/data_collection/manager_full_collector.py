# -*- coding: utf-8 -*-
"""
基金经理全量采集器 v1.0
从天天基金网抓取全量基金经理名单及管理产品
"""

import json
import re
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent.parent
DATA_DIR = SKILL_DIR / "data"


def fetch_url(url: str, headers: dict = None, timeout: int = 30) -> str:
    """通用URL抓取"""
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://fund.eastmoney.com/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"


class ManagerFullCollector:
    """基金经理全量采集器"""

    # 东方财富基金经理列表API
    MANAGER_LIST_API = "https://fundf10.eastmoney.com/Manager/MangerList"

    # 基金经理详情API
    MANAGER_DETAIL_API = "https://fundf10.eastmoney.com/Manager/MangerInfo"

    # 基金经理管理基金API
    MANAGER_FUNDS_API = "https://fundf10.eastmoney.com/Manager/MangerFunds"

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.session_cache = {}
        self.managers = {}
        self.request_delay = 0.3

    def collect_all_managers(self, max_pages: int = 100, limit: int = 0) -> List[Dict]:
        """
        采集全量基金经理

        Args:
            max_pages: 最大页数限制（防止无限抓取）
            limit: 限制采集数量（0=不限）

        Returns:
            基金经理列表
        """
        print(f"[采集开始] 全量基金经理采集器")
        print(f"[配置] 最大页数: {max_pages}, 限制数量: {limit if limit else '不限'}")

        all_managers = []
        page = 1
        collected = 0

        while page <= max_pages:
            print(f"\n[进度] 采集第 {page} 页...")

            # 第一页直接抓取列表页
            if page == 1:
                managers = self._collect_list_page()
            else:
                # 后续页需要拼接
                managers = self._collect_list_page(page)

            if not managers:
                print(f"[结束] 第 {page} 页无数据，采集完成")
                break

            print(f"[页{page}] 获取到 {len(managers)} 位基金经理")

            for m in managers:
                if limit > 0 and collected >= limit:
                    break

                # 补充详细信息
                detailed = self._collect_manager_detail(m)
                if detailed:
                    all_managers.append(detailed)
                    collected += 1

                    if collected % 50 == 0:
                        print(f"[进度] 已采集 {collected} 位经理")

                time.sleep(self.request_delay)

            if limit > 0 and collected >= limit:
                print(f"[结束] 达到数量限制 {limit}，采集完成")
                break

            page += 1
            time.sleep(self.request_delay)

        print(f"\n[完成] 共采集 {len(all_managers)} 位基金经理")

        # 保存到文件
        self._save_managers(all_managers)

        return all_managers

    def _collect_list_page(self, page: int = 1) -> List[Dict]:
        """采集列表页"""
        try:
            # 东方财富基金经理列表页
            url = f"https://fundf10.eastmoney.com/Manager/MangerList"
            params = f"pageIndex={page}&pageSize=50"

            # 这个页面需要通过POST或特殊方式访问
            # 尝试直接抓取
            full_url = f"{url}?{params}"

            html = fetch_url(full_url)
            if html.startswith("Error"):
                return []

            managers = self._parse_manager_list(html)
            return managers

        except Exception as e:
            print(f"[错误] 采集列表页失败: {e}")
            return []

    def _parse_manager_list(self, html: str) -> List[Dict]:
        """解析基金经理列表HTML"""
        managers = []

        # 解析表格中的基金经理
        # 格式: <a href="/Manager/MangerInfo/3099xxx">姓名</a>
        pattern = r'<a href="/Manager/MangerInfo/(\d+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)

        for manager_id, name in matches:
            if name and len(name) >= 2:
                managers.append({
                    'manager_id': manager_id,
                    'name': name.strip()
                })

        return managers

    def _collect_manager_detail(self, manager_info: Dict) -> Optional[Dict]:
        """采集基金经理详细信息"""
        try:
            manager_id = manager_info.get('manager_id', '')
            name = manager_info.get('name', '')

            if not manager_id:
                return None

            # 抓取详情页
            detail_url = f"https://fundf10.eastmoney.com/Manager/MangerInfo/{manager_id}"
            html = fetch_url(detail_url)

            if html.startswith("Error"):
                return None

            # 解析详情
            detail = self._parse_manager_detail(html, manager_id, name)

            # 抓取管理基金
            funds = self._collect_manager_funds(manager_id)
            detail['managed_funds'] = funds

            return detail

        except Exception as e:
            print(f"[错误] 采集经理 {name} 详情失败: {e}")
            return None

    def _parse_manager_detail(self, html: str, manager_id: str, name: str) -> Dict:
        """解析基金经理详情"""
        detail = {
            'manager_id': manager_id,
            'name': name,
            'company_id': '',
            'company_name': '',
            'tenure_years': 0,
            'current_fund_name': '',
            'current_fund_code': '',
            'investment_style': '',
            'sector_description': '',
            'asset_scale': 0,
            'photo_url': ''
        }

        try:
            # 解析公司信息
            company_pattern = r'所在公司：</span><a[^>]*>([^<]+)</a>'
            company_match = re.search(company_pattern, html)
            if company_match:
                detail['company_name'] = company_match.group(1).strip()

            # 解析任职年限
            tenure_pattern = r'任职时间：</span><span[^>]*>([^<]+)</span>'
            tenure_match = re.search(tenure_pattern, html)
            if tenure_match:
                tenure_str = tenure_match.group(1).strip()
                # 提取年数
                years_match = re.search(r'(\d+\.?\d*)年', tenure_str)
                if years_match:
                    detail['tenure_years'] = float(years_match.group(1))

            # 解析代表基金
            fund_pattern = r'<a href="/Fund/[^/]+/(\d{6})\.html"[^>]*>([^<]+)</a>'
            fund_matches = re.findall(fund_pattern, html)
            if fund_matches:
                detail['current_fund_code'] = fund_matches[0][0]
                detail['current_fund_name'] = fund_matches[0][1]

            # 解析投资理念
            style_pattern = r'投资理念：</div><div[^>]*>([^<]+)</div>'
            style_match = re.search(style_pattern, html)
            if style_match:
                detail['investment_style'] = style_match.group(1).strip()

        except Exception:
            pass

        return detail

    def _collect_manager_funds(self, manager_id: str) -> List[Dict]:
        """采集基金经理管理基金列表"""
        funds = []

        try:
            url = f"https://fundf10.eastmoney.com/Manager/MangerFunds/{manager_id}"
            html = fetch_url(url)

            if html.startswith("Error"):
                return funds

            # 解析基金列表
            # 格式: <td><a href="/Fund/xxxx/001924.html">基金名称</a></td><td>类型</td>...
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

            for row in rows:
                fund_code_match = re.search(r'/Fund/[^/]+/(\d{6})\.html', row)
                fund_name_match = re.search(r'>([^<]+)</a>', row)

                if fund_code_match and fund_name_match:
                    funds.append({
                        'fund_code': fund_code_match.group(1),
                        'fund_name': fund_name_match.group(1).strip()
                    })

        except Exception:
            pass

        return funds[:20]  # 最多20只

    def _save_managers(self, managers: List[Dict]):
        """保存到文件"""
        output_path = self.data_dir / "fund_managers_full.json"

        data = {
            "managers": managers,
            "total_count": len(managers),
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[保存] 已保存到 {output_path}")

    def merge_with_existing(self) -> int:
        """与现有基金经理数据合并"""
        existing_path = self.data_dir / "fund_managers_distilled.json"

        if not existing_path.exists():
            print("[警告] 现有数据文件不存在")
            return 0

        try:
            # 读取现有数据
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)

            existing_managers = existing.get('managers', [])
            existing_by_name = {m.get('name', ''): m for m in existing_managers}

            # 读取新数据
            new_path = self.data_dir / "fund_managers_full.json"
            with open(new_path, 'r', encoding='utf-8') as f:
                new_data = json.load(f)

            new_managers = new_data.get('managers', [])

            # 合并
            merged = []
            for new_m in new_managers:
                name = new_m.get('name', '')
                if name in existing_by_name:
                    # 更新现有记录
                    existing_m = existing_by_name[name]
                    # 保留现有字段，更新新字段
                    for k, v in new_m.items():
                        if v and v != existing_m.get(k):
                            existing_m[k] = v
                    merged.append(existing_m)
                else:
                    merged.append(new_m)

            # 加上现有数据中不在新数据里的
            new_names = set(m.get('name', '') for m in new_managers)
            for name, m in existing_by_name.items():
                if name not in new_names:
                    merged.append(m)

            # 保存合并结果
            existing['managers'] = merged
            existing['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            with open(existing_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

            print(f"[合并] 现有 {len(existing_managers)} + 新增 {len(new_managers)} = 共 {len(merged)} 位经理")
            return len(merged)

        except Exception as e:
            print(f"[错误] 合并失败: {e}")
            return 0


class ManagerAPI:
    """基金经理API采集（通过东方财富API）"""

    def __init__(self):
        self.request_delay = 0.3

    def get_manager_list_api(self, page: int = 1, page_size: int = 50) -> List[Dict]:
        """通过API获取基金经理列表"""
        try:
            url = "https://fundf10.eastmoney.com/Manager/MangerList"
            params = {
                "pageIndex": page,
                "pageSize": page_size
            }

            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            html = fetch_url(full_url)

            if html.startswith("Error"):
                return []

            managers = []
            # 解析HTML中的经理信息
            pattern = r'<a href="/Manager/MangerInfo/(\d+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)

            for manager_id, name in matches:
                managers.append({
                    'manager_id': manager_id,
                    'name': name.strip()
                })

            return managers

        except Exception as e:
            print(f"[错误] API采集失败: {e}")
            return []

    def get_manager_detail_api(self, manager_id: str) -> Dict:
        """通过API获取经理详情"""
        try:
            url = f"https://fundf10.eastmoney.com/Manager/MangerInfo/{manager_id}"
            html = fetch_url(url)

            if html.startswith("Error"):
                return {}

            # 解析详情
            detail = {}
            detail['manager_id'] = manager_id

            # 姓名
            name_pattern = r'<div class="name">([^<]+)</div>'
            name_match = re.search(name_pattern, html)
            if name_match:
                detail['name'] = name_match.group(1).strip()

            # 公司
            company_pattern = r'所在公司：</span><a[^>]*>([^<]+)</a>'
            company_match = re.search(company_pattern, html)
            if company_match:
                detail['company_name'] = company_match.group(1).strip()

            return detail

        except Exception:
            return {}


def main():
    """CLI入口"""
    import sys

    print("=" * 60)
    print("基金经理全量采集器")
    print("=" * 60)

    collector = ManagerFullCollector()

    # 解析命令行参数
    limit = 0
    merge = False

    for i, arg in enumerate(sys.argv):
        if arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == '--merge':
            merge = True

    # 采集
    managers = collector.collect_all_managers(limit=limit)

    if merge and managers:
        collector.merge_with_existing()

    print(f"\n[完成] 共采集 {len(managers)} 位基金经理")


if __name__ == "__main__":
    main()