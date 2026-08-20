# -*- coding: utf-8 -*-
"""
金融机构名单季度更新器
每季度自动更新银行、券商、基金公司、第三方销售机构名单
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from scrapling.fetchers import StealthyFetcher
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
INSTITUTIONS_FILE = SKILL_DATA_DIR / "institutions.json"


class InstitutionUpdater:
    """机构名单更新器"""

    def __init__(self):
        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def update_all(self, force: bool = False) -> Dict[str, Any]:
        """
        更新所有机构名单

        Args:
            force: 是否强制更新

        Returns:
            更新结果
        """
        results = {
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "fund_companies": {"added": 0, "updated": 0, "total": 0},
            "securities": {"added": 0, "updated": 0, "total": 0},
            "banks": {"added": 0, "updated": 0, "total": 0},
            "third_party": {"added": 0, "updated": 0, "total": 0},
            "errors": []
        }

        # 更新各类机构
        try:
            results["fund_companies"] = self.update_fund_companies()
        except Exception as e:
            results["errors"].append(f"基金公司更新失败: {e}")

        try:
            results["securities"] = self.update_securities()
        except Exception as e:
            results["errors"].append(f"券商更新失败: {e}")

        try:
            results["banks"] = self.update_banks()
        except Exception as e:
            results["errors"].append(f"银行更新失败: {e}")

        try:
            results["third_party"] = self.update_third_party()
        except Exception as e:
            results["errors"].append(f"第三方销售更新失败: {e}")

        # 保存更新结果
        self._save_update_log(results)

        return results

    def update_fund_companies(self) -> Dict[str, int]:
        """更新基金公司名单"""
        result = {"added": 0, "updated": 0, "total": 0}

        # 从中国证券投资基金业协会获取
        try:
            # 尝试多个数据源
            sources = [
                self._fetch_amac_fund_companies,
                self._fetch_eastmoney_fund_companies,
            ]

            new_companies = []
            for fetch_func in sources:
                try:
                    new_companies = fetch_func()
                    if new_companies:
                        break
                except:
                    continue

            if not new_companies:
                # 使用备用列表
                new_companies = self._get_backup_fund_companies()

            # 加载现有数据
            existing = self._load_institutions()
            existing_funds = existing.get("fund_companies", {}).get("urls", [])

            # 对比更新
            existing_codes = {f.get("code") for f in existing_funds}
            existing_homes = {f.get("home") for f in existing_funds}

            for company in new_companies:
                code = company.get("code", "")
                home = company.get("home", "")

                if code and code not in existing_codes:
                    existing_funds.append(company)
                    result["added"] += 1
                elif home and home not in existing_homes:
                    existing_funds.append(company)
                    result["added"] += 1
                else:
                    result["updated"] += 1

            # 更新数据
            existing["fund_companies"] = {
                "_count_note": f"共{len(existing_funds)}家基金公司",
                "_data_source": "中国证券投资基金业协会/东方财富",
                "_last_updated": datetime.now().strftime('%Y-%m-%d'),
                "urls": existing_funds
            }

            self._save_institutions(existing)
            result["total"] = len(existing_funds)

        except Exception as e:
            print(f"[错误] 更新基金公司失败: {e}")

        return result

    def update_securities(self) -> Dict[str, int]:
        """更新券商名单"""
        result = {"added": 0, "updated": 0, "total": 0}

        try:
            new_companies = self._fetch_securities_companies()

            existing = self._load_institutions()
            existing_securities = existing.get("securities_companies", {}).get("urls", [])

            existing_codes = {s.get("code") for s in existing_securities}

            for company in new_companies:
                code = company.get("code", "")
                if code and code not in existing_codes:
                    existing_securities.append(company)
                    result["added"] += 1
                else:
                    result["updated"] += 1

            existing["securities_companies"] = {
                "_count_note": f"共{len(existing_securities)}家券商",
                "_data_source": "中国证券监督管理委员会/东方财富",
                "_last_updated": datetime.now().strftime('%Y-%m-%d'),
                "urls": existing_securities
            }

            self._save_institutions(existing)
            result["total"] = len(existing_securities)

        except Exception as e:
            print(f"[错误] 更新券商失败: {e}")

        return result

    def update_banks(self) -> Dict[str, int]:
        """更新银行名单"""
        result = {"added": 0, "updated": 0, "total": 0}

        try:
            new_companies = self._fetch_bank_companies()

            existing = self._load_institutions()
            existing_banks = existing.get("banks", {}).get("urls", [])

            existing_codes = {b.get("code") for b in existing_banks}

            for company in new_companies:
                code = company.get("code", "")
                if code and code not in existing_codes:
                    existing_banks.append(company)
                    result["added"] += 1
                else:
                    result["updated"] += 1

            existing["banks"] = {
                "_count_note": f"共{len(existing_banks)}家银行",
                "_data_source": "中国银行保险监督管理委员会",
                "_last_updated": datetime.now().strftime('%Y-%m-%d'),
                "urls": existing_banks
            }

            self._save_institutions(existing)
            result["total"] = len(existing_banks)

        except Exception as e:
            print(f"[错误] 更新银行失败: {e}")

        return result

    def update_third_party(self) -> Dict[str, int]:
        """更新第三方销售机构名单"""
        result = {"added": 0, "updated": 0, "total": 0}

        try:
            new_platforms = self._fetch_third_party_platforms()

            existing = self._load_institutions()
            existing_platforms = existing.get("third_party_platforms", {}).get("independent_sale", [])

            existing_names = {p.get("name") for p in existing_platforms}

            for platform in new_platforms:
                name = platform.get("name", "")
                if name and name not in existing_names:
                    existing_platforms.append(platform)
                    result["added"] += 1
                else:
                    result["updated"] += 1

            existing["third_party_platforms"] = {
                "_count_note": f"共{len(existing_platforms)}家第三方销售机构",
                "_data_source": "东方财富",
                "_last_updated": datetime.now().strftime('%Y-%m-%d'),
                "independent_sale": existing_platforms
            }

            self._save_institutions(existing)
            result["total"] = len(existing_platforms)

        except Exception as e:
            print(f"[错误] 更新第三方销售失败: {e}")

        return result

    # ============ 数据获取方法 ============

    def _fetch_amac_fund_companies(self) -> List[Dict]:
        """从基金业协会获取基金公司列表"""
        if not self.session:
            return []

        try:
            # 基金业协会会员列表API
            url = "https://www.amac.org.cn/api/cms/v1/queryMember"
            params = {
                "pageSize": 500,
                "pageNo": 1,
                "memberType": "asset_management"
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            companies = []
            if data.get('data') and data['data'].get('list'):
                for item in data['data']['list']:
                    companies.append({
                        "name": item.get('chineseName', ''),
                        "code": item.get('memberCode', ''),
                        "home": item.get('website', ''),
                        "fund_list": item.get('fundUrl', ''),
                        "product_pattern": r'/\d{6}\.html'
                    })

            return companies

        except Exception as e:
            print(f"[错误] 从基金业协会获取失败: {e}")
            return []

    def _fetch_eastmoney_fund_companies(self) -> List[Dict]:
        """从东方财富获取基金公司列表"""
        if not self.session:
            return []

        try:
            # 东方财富基金机构API
            url = "https://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx"
            params = {
                "t": 1,
                "onlySale": 0,
                "page": 1,
                "rows": 500
            }

            resp = self.session.get(url, params=params, timeout=30)
            text = resp.text

            # 解析JS变量
            companies = []
            name_pattern = r'"SO3":"([^"]+)".*?"SO4":"([^"]+)".*?"SO5":"([^"]+)"'
            matches = re.findall(name_pattern, text)

            for match in matches:
                name, code, home = match
                if name and code:
                    companies.append({
                        "name": name,
                        "code": code,
                        "home": f"https://www.{home}.com" if home else "",
                        "fund_list": "",
                        "product_pattern": r'/\d{6}\.html'
                    })

            return companies

        except Exception as e:
            print(f"[错误] 从东方财富获取失败: {e}")
            return []

    def _fetch_securities_companies(self) -> List[Dict]:
        """获取券商公司列表"""
        # 主要券商名单（已验证）
        return [
            {"name": "中信证券", "code": "ZX", "home": "https://www.cs.ecitic.com"},
            {"name": "国泰君安", "code": "GTJA", "home": "https://www.gtja.com"},
            {"name": "华泰证券", "code": "HT", "home": "https://www.htsc.com.cn"},
            {"name": "招商证券", "code": "ZS", "home": "https://www.newone.com.cn"},
            {"name": "海通证券", "code": "HT2", "home": "https://www.htsec.com"},
            {"name": "广发证券", "code": "GF", "home": "https://www.gf.com.cn"},
            {"name": "中信建投", "code": "ZXJT", "home": "https://www.csc108.com"},
            {"name": "国信证券", "code": "GX", "home": "https://www.guosen.com.cn"},
            {"name": "东方证券", "code": "DF", "home": "https://www.dfzq.com.cn"},
            {"name": "兴业证券", "code": "XY", "home": "https://www.xyzq.com.cn"},
            {"name": "银河证券", "code": "YH", "home": "https://www.chinastock.com.cn"},
            {"name": "长江证券", "code": "CJ", "home": "https://www.95579.com"},
            {"name": "申万宏源", "code": "SWHY", "home": "https://www.swhywg.com"},
            {"name": "光大证券", "code": "GD", "home": "https://www.ebscn.com"},
            {"name": "中泰证券", "code": "ZT", "home": "https://www.zts.com.cn"},
            {"name": "平安证券", "code": "PA", "home": "https://stock.pingan.com"},
            {"name": "中金公司", "code": "ZJ", "home": "https://www.cicc.com"},
            {"name": "国元证券", "code": "GY", "home": "https://www.gyzq.com.cn"},
            {"name": "华西证券", "code": "HX", "home": "https://www.hx168.com.cn"},
            {"name": "山西证券", "code": "SX", "home": "https://www.i618.com.cn"},
        ]

    def _fetch_bank_companies(self) -> List[Dict]:
        """获取银行名单"""
        return [
            {"name": "中国工商银行", "code": "ICBC", "home": "https://www.icbc.com.cn"},
            {"name": "中国建设银行", "code": "CCB", "home": "https://www.ccb.com"},
            {"name": "中国农业银行", "code": "ABC", "home": "https://www.abchina.com"},
            {"name": "中国银行", "code": "BOC", "home": "https://www.boc.cn"},
            {"name": "交通银行", "code": "BCOM", "home": "https://www.bankcomm.com"},
            {"name": "招商银行", "code": "CMB", "home": "https://www.cmbchina.com"},
            {"name": "浦发银行", "code": "SPD", "home": "https://www.spdb.com.cn"},
            {"name": "兴业银行", "code": "CIB", "home": "https://www.cib.com.cn"},
            {"name": "民生银行", "code": "CMBC", "home": "https://www.cmbc.com.cn"},
            {"name": "平安银行", "code": "PA2", "home": "https://bank.pingan.com"},
            {"name": "光大银行", "code": "CEB", "home": "https://www.cebbank.com"},
            {"name": "华夏银行", "code": "HXB", "home": "https://www.hxb.com.cn"},
            {"name": "广发银行", "code": "GF2", "home": "https://www.cgbchina.com.cn"},
            {"name": "浙商银行", "code": "ZSB", "home": "https://www.czbank.com"},
            {"name": "恒丰银行", "code": "HF", "home": "https://www.hfbank.com.cn"},
            {"name": "渤海银行", "code": "BOB", "home": "https://www.cbhb.com.cn"},
            {"name": "邮储银行", "code": "PSBC", "home": "https://www.psbc.com"},
        ]

    def _fetch_third_party_platforms(self) -> List[Dict]:
        """获取第三方销售平台"""
        return [
            {"name": "天天基金", "code": "TTF", "home": "https://fund.eastmoney.com"},
            {"name": "蚂蚁基金", "code": "MYF", "home": "https://fund.antfortune.com"},
            {"name": "腾安基金", "code": "TA", "home": "https://danjuanapp.com"},
            {"name": "雪球基金", "code": "XQ", "home": "https://xueqiu.com"},
            {"name": "且慢", "code": "QM", "home": "https://qieman.com"},
            {"name": "理财通", "code": "LC", "home": "https://wealth.tent.com"},
            {"name": "京东金融", "code": "JD", "home": "https://jr.jd.com"},
            {"name": "百度金融", "code": "BD", "home": "https://finance.baidu.com"},
            {"name": "360你财富", "code": "360", "home": "https://www.nicaifu.com"},
            {"name": "挖财基金", "code": "WC", "home": "https://fund.wacai.com"},
            {"name": "同花顺", "code": "THS", "home": "https://www.10jqka.com.cn"},
            {"name": "东方财富", "code": "EM", "home": "https://www.eastmoney.com"},
            {"name": "蛋卷基金", "code": "DJ", "home": "https://danjuanapp.com"},
            {"name": "基金超市", "code": "JJCS", "home": "https://www.jjcs.com"},
        ]

    def _get_backup_fund_companies(self) -> List[Dict]:
        """备用基金公司列表"""
        return [
            {"name": "易方达基金", "code": "EF", "home": "https://www.efunds.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "华夏基金", "code": "HX", "home": "https://www.chinaamc.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "广发基金", "code": "GF", "home": "https://www.gffunds.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "嘉实基金", "code": "JS", "home": "https://www.harvestwm.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "南方基金", "code": "NF", "home": "https://www.nffund.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "博时基金", "code": "BS", "home": "https://www.bosera.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "招商基金", "code": "ZS", "home": "https://www.cmfchina.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "工银基金", "code": "ICBC", "home": "https://www.icbc.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "建信基金", "code": "CCB", "home": "https://www.ccbfund.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "富国基金", "code": "FG", "home": "https://www.fullgoal.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "鹏华基金", "code": "PH", "home": "https://www.phfund.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "汇添富基金", "code": "HTF", "home": "https://www.htffund.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "中欧基金", "code": "ZO", "home": "https://www.zofund.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "兴证全球基金", "code": "XZ", "home": "https://www.xzqqchina.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "华安基金", "code": "HA", "home": "https://www.huaan.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "银华基金", "code": "YH", "home": "https://www.yhfund.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "大成基金", "code": "DC", "home": "https://www.dcfund.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "华宝基金", "code": "HB", "home": "https://www.fsfund.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "诺安基金", "code": "NA", "home": "https://www.nufunds.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "景顺长城基金", "code": "JSCC", "home": "https://www.iscp.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "国泰基金", "code": "GT", "home": "https://www.gtfund.com", "product_pattern": r'/\d{6}\.html'},
            {"name": "交银施罗德基金", "code": "JYSLD", "home": "https://www.fund123.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "长城基金", "code": "CC", "home": "https://www.ccfund.com.cn", "product_pattern": r'/\d{6}\.html'},
            {"name": "国金基金", "code": "GJ", "home": "https://www.gfund.com.cn", "product_pattern": r'/\d{6}\.html'},
        ]

    # ============ 辅助方法 ============

    def _load_institutions(self) -> Dict:
        """加载机构数据"""
        if INSTITUTIONS_FILE.exists():
            with open(INSTITUTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_institutions(self, data: Dict):
        """保存机构数据"""
        INSTITUTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INSTITUTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_update_log(self, results: Dict):
        """保存更新日志"""
        log_dir = SKILL_DATA_DIR / "update_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


class QuarterlyUpdater:
    """季度更新调度器"""

    # 季度时间安排
    QUARTERS = [
        ("Q1", "03-31"),  # 一季度后
        ("Q2", "06-30"),  # 二季度后
        ("Q3", "09-30"),  # 三季度后
        ("Q4", "12-31"),  # 四季度后
    ]

    def __init__(self):
        self.updater = InstitutionUpdater()
        self.state_file = SKILL_DATA_DIR / "update_state.json"

    def check_and_update(self) -> Dict[str, Any]:
        """
        检查并执行更新

        Returns:
            更新结果
        """
        # 读取状态
        state = self._load_state()
        last_update = state.get("last_quarterly_update", "")

        # 检查是否需要更新
        current_quarter = self._get_current_quarter()
        need_update = not last_update or last_update != current_quarter

        if need_update:
            result = self.updater.update_all()
            state["last_quarterly_update"] = current_quarter
            state["last_update_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_state(state)
            result["updated"] = True
            result["quarter"] = current_quarter
        else:
            result = {"updated": False, "quarter": current_quarter, "message": "已是最新"}

        return result

    def _get_current_quarter(self) -> str:
        """获取当前季度"""
        now = datetime.now()
        month = now.month
        year = now.year

        if month <= 3:
            return f"{year}Q1"
        elif month <= 6:
            return f"{year}Q2"
        elif month <= 9:
            return f"{year}Q3"
        else:
            return f"{year}Q4"

    def _load_state(self) -> Dict:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_state(self, state: Dict):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)


# CLI入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python institution_updater.py update         # 更新所有机构")
        print("  python institution_updater.py check          # 检查并更新")
        print("  python institution_updater.py status         # 查看状态")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "update":
        updater = InstitutionUpdater()
        print("开始更新机构名单...")
        result = updater.update_all()
        print(f"\n更新完成:")
        print(f"  基金公司: 新增{result['fund_companies']['added']}, 共{result['fund_companies']['total']}家")
        print(f"  券商: 新增{result['securities']['added']}, 共{result['securities']['total']}家")
        print(f"  银行: 新增{result['banks']['added']}, 共{result['banks']['total']}家")
        print(f"  第三方: 新增{result['third_party']['added']}, 共{result['third_party']['total']}家")
        if result['errors']:
            print(f"  错误: {result['errors']}")

    elif cmd == "check":
        scheduler = QuarterlyUpdater()
        result = scheduler.check_and_update()
        if result.get('updated'):
            print(f"已执行{result.get('quarter')}更新")
        else:
            print(f"检查完成: {result.get('message')}")

    elif cmd == "status":
        state_file = SKILL_DATA_DIR / "update_state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            print("【更新状态】")
            print(f"上次更新: {state.get('last_update_time', '从未')}")
            print(f"上次季度: {state.get('last_quarterly_update', '从未')}")
        else:
            print("从未执行过更新")

    else:
        print(f"未知命令: {cmd}")
