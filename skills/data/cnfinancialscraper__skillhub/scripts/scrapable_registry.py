# -*- coding: utf-8 -*-
"""
金融机构可爬取名单注册表
维护所有中国大陆金融机构的URL映射关系，支持增量更新
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

SKILL_DIR = Path(__file__).parent.parent
REGISTRY_FILE = SKILL_DIR / "data" / "institution_registry.json"

PREDEFINED_URLS: Dict[str, str] = {
    # 国有大型商业银行
    "中国工商银行": "https://www.icbc.com.cn",
    "中国建设银行": "https://www.ccb.com",
    "中国农业银行": "https://www.abchina.com",
    "中国银行": "https://www.boc.cn",
    "交通银行": "https://www.bankcomm.com",
    "中国邮政储蓄银行": "https://www.psbc.com",
    # 股份制商业银行
    "招商银行": "https://www.cmbchina.com",
    "浦发银行": "https://www.spdb.com.cn",
    "中信银行": "https://www.citicbank.com",
    "中国光大银行": "https://www.cebbank.com",
    "华夏银行": "https://www.hxb.com.cn",
    "中国民生银行": "https://www.cmbc.com.cn",
    "广发银行": "https://www.cgbchina.com.cn",
    "兴业银行": "https://www.cib.com.cn",
    "平安银行": "https://bank.pingan.com",
    "浙商银行": "https://www.czbank.com",
    "恒丰银行": "https://www.hfbank.com.cn",
    "渤海银行": "https://www.cbhb.com.cn",
    # 政策性银行
    "国家开发银行": "https://www.cdb.com.cn",
    # 中国进出口银行（官网为政府域名，已移除）
    "中国农业发展银行": "https://www.adbc.com.cn",
    # 证券公司
    "中信证券": "https://www.cs.ecitic.com",
    "中信建投证券": "https://www.csc108.com",
    "国泰君安证券": "https://www.gtja.com",
    "华泰证券": "https://www.htsc.com.cn",
    "广发证券": "https://www.gf.com.cn",
    "招商证券": "https://www.newone.com.cn",
    "海通证券": "https://www.htsec.com",
    "国信证券": "https://www.guosen.com.cn",
    "东方证券": "https://www.dfzq.com.cn",
    "兴业证券": "https://www.xyzq.com.cn",
    "中国银河证券": "https://www.chinastock.com.cn",
    "长江证券": "https://www.95579.com",
    "中金公司": "https://www.cicc.com",
    "光大证券": "https://www.ebscn.com",
    "平安证券": "https://stock.pingan.com",
    "方正证券": "https://www.foundersc.com",
    "中泰证券": "https://www.zts.com.cn",
    "申万宏源证券": "https://www.swhysc.com",
    "国元证券": "https://www.gyzq.com.cn",
    "安信证券": "https://www.essence.com.cn",
    "开源证券": "https://www.kysec.cn",
    "华西证券": "https://www.hx168.com.cn",
    "民生证券": "https://www.mszq.com",
    "东北证券": "https://www.nesc.cn",
    "南京证券": "https://www.njzq.com",
    "长城证券": "https://www.cgws.com",
    "中银证券": "https://www.bocichina.com",
    "华安证券": "https://www.hazq.com",
    "财达证券": "https://www.s10000.com",
    "万联证券": "https://www.wlzq.com",
    "山西证券": "https://www.i618.com.cn",
    "西部证券": "https://www.westsecu.com",
    "浙商证券": "https://www.stocke.com.cn",
    "东海证券": "https://www.longone.com.cn",
    "国海证券": "https://www.ghzq.com.cn",
    "广州证券": "https://www.gzs.com.cn",
    "大同证券": "https://www.dtsbc.com.cn",
    "华融证券": "https://www.china-huarong.com",
    "中天证券": "https://www.izq.com.cn",
    # 基金管理公司
    "易方达基金": "https://www.efunds.com.cn",
    "华夏基金": "https://www.chinaamc.com",
    "广发基金": "https://www.gffunds.com.cn",
    "嘉实基金": "https://www.jsfund.cn",
    "南方基金": "https://www.nffund.com.cn",
    "博时基金": "https://www.bosera.com",
    "招商基金": "https://www.cmfchina.com",
    "工银基金": "https://www.icbcfs.com",
    "建信基金": "https://www.ccbfund.cn",
    "富国基金": "https://www.fullgoal.com.cn",
    "鹏华基金": "https://www.phfund.com.cn",
    "汇添富基金": "https://www.htffund.com",
    "中欧基金": "https://www.zofund.com",
    "兴证全球基金": "https://www.xqglobal.com",
    "景林资产": "https://www.greenpeakgroup.com",
    "高毅资产": "https://www.gao-yi.com",
    "淡水泉投资": "https://www.downspring.com",
    "明汯投资": "https://www.minghonginvestment.com",
    "幻方量化": "https://www.quantizedcapital.com",
    "九坤投资": "https://www.jiukuninvest.com",
    "灵均投资": "https://www.lingjun-invest.com",
    "天演资本": "https://www.tianyan-capital.com",
    "东方港湾": "https://www.eastport.com.cn",
    "汉和资本": "https://www.hanhecap.com",
    "同犇投资": "https://www.tongben-invest.com",
    "石锋资产": "https://www.shifengam.com",
    "趣时资产": "https://www.quishi.com",
    "聚鸣投资": "https://www.jumingsh.com",
    "泰旸资产": "https://www.taiyangam.com",
    # 保险公司
    "中国人寿": "https://www.chinalife.com.cn",
    "中国平安": "https://www.pingan.com.cn",
    "中国太平洋保险": "https://www.cpic.com.cn",
    "中国人保": "https://www.picc.com.cn",
    "新华保险": "https://www.newchina-life.com",
    "泰康保险": "https://www.taikang.com",
    "友邦保险": "https://www.aia.com.cn",
    "阳光保险": "https://www.sinosig.com",
    "合众人寿": "https://www.reformlife.com",
    "华夏保险": "https://www.huaxia-insurance.com",
    "富德生命人寿": "https://www.sino-life.com",
    "天安保险": "https://www.tiananinsurance.com",
    "中华保险": "https://www.cai-insurance.com",
    "大地保险": "https://www.95590.com",
    "中华联合保险": "https://www.cic.cn",
    "华泰保险": "https://www.ehuatai.com",
    "安华农业保险": "https://www.anohua.com",
    # 信托公司
    "中信信托": "https://www.zxxt.com.cn",
    "平安信托": "https://www.paxt.com.cn",
    "中融信托": "https://www.zhongrongtrust.com",
    "华润信托": "https://www.crhtrust.com.cn",
    "外贸信托": "https://www.fotacn.com",
    "上海信托": "https://www.shanghaitrust.com",
    "中建投信托": "https://www.cctrust.com",
    "兴业信托": "https://www.ciit.com.cn",
    "华宝信托": "https://www.hwabaotrust.com",
    "交银信托": "https://www.bankcommtrust.com",
    "光大信托": "https://www.ebtrust.com",
    "中粮信托": "https://www.cofco-trust.com",
    "昆仑信托": "https://www.kunluntrust.com",
    "五矿信托": "https://www.minmetals-trust.com",
    "中铁信托": "https://www.crec-trust.com",
    "江苏信托": "https://www.js-trust.com",
    "粤财信托": "https://www.gdyc-trust.com",
    "重庆信托": "https://www.cqitic.com",
    "华融信托": "https://www.huarongtrust.com.cn",
    # 银行理财子公司
    "工银理财": "https://www.icbc.com.cn/ICBC/FinancialManagement",
    "建信理财": "https://www.ccbfund.com.cn",
    "农银理财": "https://www.abchina.com/wealth",
    "中银理财": "https://www.boc.cn/financial",
    "交银理财": "https://www.bankcomm.com/wealth",
    "光大理财": "https://www.cebbank.com/finance",
    "招银理财": "https://www.cmbc.com.cn/wealth",
    "兴银理财": "https://www.cib.com.cn/wealth",
    "平安理财": "https://bank.pingan.com/wealth",
    "浦银理财": "https://www.spdb.com.cn/wealth",
    # 第三方销售机构
    "天天基金": "https://fund.eastmoney.com",
    "蚂蚁基金": "https://www.fund123.cn",
    "腾安基金": "https://www.tan'anfund.com",
    "雪球基金": "https://danjuanfunds.com",
    "京东基金": "https://jd.jrj.com",
    "理财通": "https://www.lct.com",
    # 外资金融机构
    "汇丰银行": "https://www.hsbc.com.cn",
    "渣打银行": "https://www.standardchartered.com.cn",
    "花旗银行": "https://www.citibank.com.cn",
    "摩根大通银行": "https://www.jpmorganchina.com.cn",
    "高盛集团": "https://www.goldmansachs.com.cn",
    "瑞银证券": "https://www.ubs.com/cn/zh.html",
    "野村证券": "https://www.nomura.com",
    "安盛保险": "https://www.axa.com.cn",
    "安联保险": "https://www.allianz.com.cn",
    "贝莱德资产管理": "https://www.blackrock.com.cn",
    "瑞银资产管理": "https://www.ubs.com/global/en/asset-management.html",
    "摩根士丹利": "https://www.morganstanley.com.cn",
    "美林证券": "https://www.ml.com",
    "德意志银行": "https://www.db.com.cn",
    "星展银行": "https://www.dbs.com.cn",
    "东亚银行": "https://www.hkbea.com.cn",
    "恒生银行": "https://www.hangseng.com",
    "华侨银行": "https://www.ocbc.com.cn",
    # ── 城市商业银行（补充） ──
    "北京银行": "https://www.bankofbeijing.com.cn",
    "上海银行": "https://www.bosc.cn",
    "江苏银行": "https://www.jsbchina.cn",
    "南京银行": "https://www.njcb.com.cn",
    "宁波银行": "https://www.nbcb.com.cn",
    "杭州银行": "https://www.hzbank.com.cn",
    "成都银行": "https://www.bocd.com.cn",
    "长沙银行": "https://www.bankofchangsha.com",
    "郑州银行": "https://www.zzbank.cn",
    "青岛银行": "https://www.qdccb.com",
    "西安银行": "https://www.xacbank.com",
    "贵阳银行": "https://www.bankgy.cn",
    "兰州银行": "https://www.lzbank.com",
    "厦门国际银行": "https://www.xib.com.cn",
    # ── 农商行 ──
    "重庆农商行": "https://www.cqrcb.com",
    "广州农商行": "https://www.grcbank.com",
    "上海农商行": "https://www.shrcb.com",
    "北京农商行": "https://www.bjrcb.com",
    "深圳农商行": "https://www.szrcb.com",
    # ── 金融科技 ──
    "蚂蚁集团": "https://www.antgroup.com",
    "京东科技": "https://www.jdcloud.com",
    "度小满金融": "https://www.duxiaoman.com",
    "陆金所": "https://www.lu.com",
    "众安保险": "https://www.zhongan.com",
    "微众银行": "https://www.webank.com",
    "网商银行": "https://www.mybank.cn",
    # ── 更多私募基金 ──
    "重阳投资": "https://www.chongyang.net",
    "凯丰投资": "https://www.kffund.com.cn",
    "敦和资管": "https://www.dunhefund.com",
    "乐瑞资产": "https://www.lowrisk.com.cn",
    "千合资本": "https://www.qhcapital.com.cn",
    "林园投资": "https://www.linyuaninvest.com",
    "星石投资": "https://www.starrockinvest.com",
    "望正资产": "https://www.wangzhengcapital.com",
    # ── 另类数据/评价平台 ──
    "好买基金": "https://www.howbuy.com",
    "私募排排网": "https://www.simuwang.com",
    "雪球": "https://xueqiu.com",
    "集思录": "https://www.jisilu.cn",
    "理杏仁": "https://www.lixinger.com",
    "韭圈儿": "https://www.funddb.cn",
    # ── 交易所 ──
    "上海证券交易所": "https://www.sse.com.cn",
    "深圳证券交易所": "https://www.szse.cn",
    "北京证券交易所": "https://www.bse.cn",
    "香港交易所": "https://www.hkex.com.hk",
    # ── 期货交易所 ──
    "上海期货交易所": "https://www.shfe.com.cn",
    "大连商品交易所": "https://www.dce.com.cn",
    "郑州商品交易所": "https://www.czce.com.cn",
    "中国金融期货交易所": "https://www.cffex.com.cn",
    "上海国际能源交易中心": "https://www.ine.cn",
    "广州期货交易所": "https://www.gfex.com.cn",
    # ── 行业协会 ──
    "中国银行业协会": "https://www.china-cba.net",
    "中国证券业协会": "https://www.sac.net.cn",
    "中国保险行业协会": "https://www.iachina.cn",
    # ── 同业市场 ──
    "中国外汇交易中心": "https://www.chinamoney.com.cn",
    "上海银行间同业拆放利率": "https://www.shibor.org",
    "中国债券信息网（中央国债登记结算公司）": "https://www.chinabond.com.cn",
    # ── 海外交易所 ──
    "纳斯达克": "https://www.nasdaq.com",
    "纽约证券交易所": "https://www.nyse.com",
    "芝加哥商品交易所": "https://www.cmegroup.com",
    "伦敦证券交易所": "https://www.londonstockexchange.com",
    "东京证券交易所": "https://www.jpx.co.jp",
    "新加坡交易所": "https://www.sgx.com",
    # ── 其他金融机构补充 ──
    "中国再保险": "https://www.chinare.com.cn",
    "中投公司": "https://www.china-inv.cn",
    "国家开发投资集团": "https://www.sdic.com.cn",
    "中国银河资产管理": "https://www.china-galaxyam.com",
}


class ScrapableRegistry:
    def __init__(self, registry_file: str = None):
        self.registry_file = Path(registry_file) if registry_file else REGISTRY_FILE
        self._registry = None
        self._load()

    def _load(self):
        if self.registry_file.exists():
            with open(self.registry_file, encoding="utf-8") as f:
                self._registry = json.load(f)
            # 解码列式格式
            if self._registry.get("_f") == "c":
                self._registry = self._decode_columnar(self._registry)
        else:
            self._registry = {}

    @staticmethod
    def _decode_columnar(data: dict) -> dict:
        """将列式格式还原为标准 dict"""
        columns = data.get("c", [])
        rows = data.get("d", [])
        meta = data.get("m", data.get("_meta", {}))
        items = []
        for row in rows:
            item = {}
            for i, col_name in enumerate(columns):
                if i < len(row):
                    item[col_name] = row[i]
            items.append(item)
        result = {"institutions": items}
        if meta:
            result["_meta"] = meta
        return result

    @property
    def institutions(self) -> List[Dict]:
        return self._registry.get("institutions", [])

    @property
    def total(self) -> int:
        return self._registry.get("_meta", {}).get("total", len(self.institutions))

    def is_scrapable(self, name: str, inst_type: str = "") -> bool:
        if name in PREDEFINED_URLS:
            return True
        return False

    def get(self, name: str, inst_type: str = "") -> Optional[Dict]:
        for inst in self.institutions:
            if inst["name"] == name:
                result = dict(inst)
                website = inst.get("website", "")
                if not website and name in PREDEFINED_URLS:
                    website = PREDEFINED_URLS[name]
                result["website"] = website
                result["scrapable"] = bool(website)
                return result
        return None

    def search(self, keyword: str) -> List[Dict]:
        results = []
        kw = keyword.lower()
        for inst in self.institutions:
            if kw in inst["name"].lower() or kw in inst.get("code", "").lower():
                results.append(self.get(inst["name"]))
        return results

    def list_scrapable(self, inst_type: str = "") -> List[Dict]:
        results = []
        for inst in self.institutions:
            if inst_type and inst["type"] != inst_type:
                continue
            info = self.get(inst["name"])
            if info and info["scrapable"]:
                results.append(info)
        return results

    def list_by_type(self, inst_type: str) -> List[Dict]:
        return [self.get(i["name"]) for i in self.institutions if i["type"] == inst_type]

    def add_url(self, name: str, url: str) -> bool:
        for inst in self.institutions:
            if inst["name"] == name:
                inst["website"] = url
                self._registry["_meta"]["with_website"] = sum(
                    1 for i in self.institutions if i.get("website")
                )
                self.save()
                return True
        return False

    def get_statistics(self) -> Dict:
        summary = self._registry.get("_type_summary", {})
        stats = {
            "total": self.total,
            "scrapable": sum(
                1 for i in self.institutions if self.is_scrapable(i["name"], i["type"])
            ),
            "by_type": {},
        }
        for inst_type, info in summary.items():
            scrapable_count = sum(
                1 for i in self.institutions
                if i["type"] == inst_type and self.is_scrapable(i["name"], inst_type)
            )
            stats["by_type"][inst_type] = {
                "total": info["total"],
                "with_url": info["with_website"],
                "scrapable": scrapable_count,
            }
        return stats

    def save(self):
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self._registry, f, ensure_ascii=False, indent=2)

    def generate_report(self) -> str:
        stats = self.get_statistics()
        lines = [
            "=" * 60,
            "金融机构可爬取名单报告",
            "=" * 60,
            f"机构总数：{stats['total']}",
            f"可爬取数：{stats['scrapable']} ({stats['scrapable']*100//stats['total']}%)",
            "",
            "按类型明细：",
        ]
        for inst_type, info in sorted(stats["by_type"].items(), key=lambda x: -x[1]["total"]):
            lines.append(
                f"  {inst_type}: {info['scrapable']}/{info['total']} 可爬取 "
                f"({info['with_url']} 有URL)"
            )
        return "\n".join(lines)

    # ── v7.0.0: API 发现引擎桥接 ────────────────────────────────

    def suggest_api(self, name_or_domain: str, limit: int = 10) -> List[Dict]:
        """查询 v7.0.0 网络拦截挖掘出的 API 注册表（data/api_registry.json）。

        机构名会先解析出官网域名，再返回该域名下已发现的 JSON 接口，
        供降级链直接 HTTP 直连（跳过浏览器渲染）。

        Args:
            name_or_domain: 机构名（如 东方财富）或域名（如 eastmoney.com）
            limit: 最多返回条数
        """
        api_file = Path(self.registry_file).parent / "api_registry.json"
        if not api_file.exists():
            return []
        try:
            doc = json.loads(api_file.read_text(encoding="utf-8"))
        except Exception:
            return []
        domain = name_or_domain
        if "." not in domain:
            inst = self.get(name_or_domain)
            if not inst or not inst.get("website"):
                return []
            domain = inst["website"].split("//")[-1].split("/")[0]
        out = [ep for ep in doc.get("endpoints", [])
               if domain and domain in ep.get("url", "")]
        out.sort(key=lambda e: -e.get("hit_count", 1))
        return out[:limit]


def main():
    import sys
    registry = ScrapableRegistry()
    args = sys.argv[1:]

    if not args:
        print(registry.generate_report())
        return

    cmd = args[0]
    if cmd == "stat":
        print(registry.generate_report())
    elif cmd == "list" and len(args) > 1:
        for info in registry.list_scrapable(args[1]):
            print(f"  {info['name']} | {info['type']} | {info.get('website', 'N/A')}")
    elif cmd == "search" and len(args) > 1:
        for info in registry.search(args[1]):
            scrapable = "OK" if info["scrapable"] else "NO"
            print(f"  [{scrapable}] {info['name']} | {info['type']} | {info.get('website', '')}")
    elif cmd == "add" and len(args) > 2:
        name, url = args[1], args[2]
        if registry.add_url(name, url):
            print(f"URL已更新: {name} -> {url}")
        else:
            print(f"机构未找到: {name}")
    elif cmd == "export":
        for inst in registry.institutions:
            info = registry.get(inst["name"])
            if info["scrapable"]:
                print(f"{info['name']}\t{info['type']}\t{info.get('website', '')}")
    else:
        print("用法:")
        print("  python scrapable_registry.py stat")
        print("  python scrapable_registry.py list <类型>")
        print("  python scrapable_registry.py search <关键词>")
        print("  python scrapable_registry.py add <名称> <URL>")
        print("  python scrapable_registry.py export")


if __name__ == "__main__":
    main()
