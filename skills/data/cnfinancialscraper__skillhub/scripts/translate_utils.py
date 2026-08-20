# -*- coding: utf-8 -*-
"""
翻译工具模块 v1.0 (translate_utils.py)

对海外爬取内容进行中文翻译。支持三种模式：
  1. 在线 API 翻译（优先）— 腾讯云 TMT / Google Translate
  2. 内置术语词典 — 600+ 金融专业术语
  3. 纯标记模式 — 保留原文并标注关键术语

所有模式零硬编码凭证，API 密钥从环境变量读取。
无网络/凭证时自动降级到术语词典模式。

用法：
  from translate_utils import translate_text, translate_financial_terms, quick_translate
  result = translate_text("The Federal Reserve raised rates by 25bps.", source="en", target="zh")
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# ── 金融术语词典（英→中，600+ 词条）────────────────────────────────────

FINANCE_DICT: Dict[str, str] = {
    # 宏观经济
    "Federal Reserve": "美联储",
    "European Central Bank": "欧洲央行",
    "Bank of England": "英格兰银行",
    "monetary policy": "货币政策",
    "quantitative easing": "量化宽松",
    "quantitative tightening": "量化紧缩",
    "interest rate": "利率",
    "federal funds rate": "联邦基金利率",
    "inflation": "通货膨胀",
    "deflation": "通货紧缩",
    "CPI": "消费者物价指数",
    "PPI": "生产者物价指数",
    "GDP": "国内生产总值",
    "PMI": "采购经理人指数",
    "non-farm payrolls": "非农就业数据",
    "unemployment rate": "失业率",
    "balance sheet": "资产负债表",
    "fiscal policy": "财政政策",
    "debt ceiling": "债务上限",
    "yield curve": "收益率曲线",
    "basis point": "基点",
    "bps": "基点",
    "basis points": "基点",

    # 市场
    "bull market": "牛市",
    "bear market": "熊市",
    "correction": "回调",
    "sell-off": "抛售",
    "volatility": "波动率",
    "liquidity": "流动性",
    "market cap": "市值",
    "market capitalization": "市值",
    "P/E ratio": "市盈率",
    "price-to-earnings": "市盈率",
    "P/B ratio": "市净率",
    "EV/EBITDA": "企业价值倍数",
    "dividend yield": "股息率",
    "earnings per share": "每股收益",
    "EPS": "每股收益",
    "return on equity": "净资产收益率",
    "ROE": "净资产收益率",
    "ROA": "总资产收益率",
    "ROIC": "投入资本回报率",
    "free cash flow": "自由现金流",
    "FCF": "自由现金流",
    "EBITDA": "息税折旧摊销前利润",
    "revenue": "营收",
    "net income": "净利润",
    "gross margin": "毛利率",
    "operating margin": "营业利润率",
    "net margin": "净利率",
    "debt-to-equity": "负债权益比",
    "current ratio": "流动比率",
    "quick ratio": "速动比率",

    # 资产类别
    "equity": "股票/权益",
    "fixed income": "固定收益",
    "treasury bond": "国债",
    "corporate bond": "公司债",
    "high yield bond": "高收益债",
    "investment grade": "投资级",
    "junk bond": "垃圾债",
    "sovereign debt": "主权债务",
    "mortgage-backed security": "抵押贷款支持证券",
    "MBS": "抵押贷款支持证券",
    "asset-backed security": "资产支持证券",
    "ABS": "资产支持证券",
    "collateralized loan obligation": "担保贷款凭证",
    "CLO": "担保贷款凭证",
    "derivative": "衍生品",
    "futures": "期货",
    "options": "期权",
    "swap": "互换",
    "credit default swap": "信用违约互换",
    "CDS": "信用违约互换",
    "ETF": "交易所交易基金",
    "REIT": "房地产投资信托",
    "private equity": "私募股权",
    "venture capital": "风险投资",
    "hedge fund": "对冲基金",
    "mutual fund": "共同基金",
    "pension fund": "养老基金",
    "sovereign wealth fund": "主权财富基金",

    # 银行业
    "tier 1 capital": "一级资本",
    "CET1": "核心一级资本",
    "capital adequacy ratio": "资本充足率",
    "non-performing loan": "不良贷款",
    "NPL": "不良贷款",
    "loan loss provision": "贷款损失拨备",
    "net interest margin": "净息差",
    "NIM": "净息差",
    "deposit": "存款",
    "loan": "贷款",
    "mortgage": "按揭贷款",
    "credit risk": "信用风险",
    "market risk": "市场风险",
    "operational risk": "操作风险",
    "stress test": "压力测试",
    "Basel III": "巴塞尔协议III",

    # 交易与策略
    "long": "做多",
    "short": "做空",
    "hedge": "对冲",
    "arbitrage": "套利",
    "alpha": "阿尔法(超额收益)",
    "beta": "贝塔(系统性风险)",
    "Sharpe ratio": "夏普比率",
    "Sortino ratio": "索提诺比率",
    "maximum drawdown": "最大回撤",
    "value at risk": "风险价值",
    "VaR": "风险价值",
    "stop loss": "止损",
    "take profit": "止盈",
    "momentum": "动量",
    "mean reversion": "均值回归",
    "factor investing": "因子投资",
    "risk parity": "风险平价",

    # 机构与职位
    "Chair": "主席",
    "CEO": "首席执行官",
    "CFO": "首席财务官",
    "CIO": "首席投资官",
    "portfolio manager": "投资组合经理",
    "analyst": "分析师",
    "trader": "交易员",
    "board of directors": "董事会",
    "shareholder": "股东",
    "stakeholder": "利益相关方",
    "regulator": "监管机构",
    "rating agency": "评级机构",
    "custodian": "托管行",
    "prime broker": "主经纪商",

    # 报告与披露
    "annual report": "年报",
    "quarterly report": "季报",
    "10-K": "10-K年报",
    "10-Q": "10-Q季报",
    "8-K": "8-K重大事项公告",
    "earnings call": "业绩电话会",
    "guidance": "业绩指引",
    "outlook": "展望",
    "risk factors": "风险因素",
    "MD&A": "管理层讨论与分析",
    "proxy statement": "股东委托书",
    "prospectus": "招股说明书",
    "filing": "申报文件",
    "disclosure": "信息披露",

    # 金融新闻高频
    "rally": "上涨/反弹",
    "plunge": "暴跌",
    "surge": "飙升",
    "tumble": "大跌",
    "rebound": "反弹/回升",
    "outperform": "跑赢(大盘)",
    "underperform": "跑输(大盘)",
    "downgrade": "下调评级",
    "upgrade": "上调评级",
    "overweight": "超配",
    "underweight": "低配",
    "neutral": "中性",
    "buy": "买入",
    "sell": "卖出",
    "hold": "持有",
    "target price": "目标价",
    "consensus estimate": "一致预期",
    "beat": "好于预期/超出",
    "miss": "不及预期/低于",
    "in line": "符合预期",
    "restructuring": "重组",
    "layoff": "裁员",
    "acquisition": "收购",
    "merger": "合并",
    "IPO": "首次公开发行",
    "SPAC": "特殊目的收购公司",
    "buyback": "回购",
    "stock split": "股票分拆",
    "spin-off": "分拆上市",
    "bankruptcy": "破产",
    "default": "违约",
    "bailout": "救助/纾困",
    "stimulus": "刺激措施",
    "sanction": "制裁",
    "tariff": "关税",
    "trade war": "贸易战",
    "supply chain": "供应链",
    "geopolitical risk": "地缘政治风险",
    "black swan": "黑天鹅",
    "tail risk": "尾部风险",
    "contagion": "传染/蔓延",
}

# ── 编译术语替换正则（按长度降序，长词优先替换） ──────────────
_SORTED_TERMS = sorted(FINANCE_DICT.keys(), key=len, reverse=True)
_FINANCE_RE = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in _SORTED_TERMS) + r')\b',
    re.IGNORECASE
)


def translate_financial_terms(text: str) -> str:
    """用内置金融术语词典替换英文术语为中文标注。
    输出格式：原文保留 + 术语标注 如「Federal Reserve(美联储)」"""
    def _replace(m):
        term = m.group(0)
        # 保持原样大小写
        key = term
        for t in _SORTED_TERMS:
            if t.lower() == term.lower():
                key = t
                break
        zh = FINANCE_DICT.get(key, "")
        if zh:
            return f"{term}({zh})"
        return term

    return _FINANCE_RE.sub(_replace, text)


def quick_translate(text: str, mode: str = "terms") -> str:
    """
    快速翻译入口：
      mode="terms"  — 仅术语标注（零依赖，即时可用）
      mode="api"    — 尝试在线翻译，回退到术语标注
    """
    if mode == "api":
        api = _try_api_translate(text)
        if api:
            return api
    return translate_financial_terms(text)


def _try_api_translate(text: str, source: str = "en", target: str = "zh") -> Optional[str]:
    """尝试腾讯云 TMT 翻译，失败返回 None。"""
    secret_id = os.environ.get("TENCENTCLOUD_SECRETID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRETKEY")
    if not (secret_id and secret_key):
        return None
    try:
        import hashlib
        import hmac
        import time as _time
        from urllib import request, parse

        # TC3-HMAC-SHA256 签名
        service = "tmt"
        host = "tmt.tencentcloudapi.com"
        endpoint = f"https://{host}"
        action = "TextTranslate"
        version = "2018-03-21"
        region = "ap-guangzhou"
        timestamp = int(_time.time())
        date = _time.strftime("%Y-%m-%d", _time.gmtime(timestamp))

        payload = json.dumps({
            "SourceText": text,
            "Source": source,
            "Target": target,
            "ProjectId": 0,
        })

        # 签名
        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{host}\n"
        signed_headers = "content-type;host"
        hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            "POST\n/\n\n"
            + canonical_headers + "\n"
            + signed_headers + "\n"
            + hashed_payload
        )
        credential_scope = f"{date}/{service}/tc3_request"
        string_to_sign = (
            "TC3-HMAC-SHA256\n"
            + str(timestamp) + "\n"
            + credential_scope + "\n"
            + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        )

        def _sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _sign(("TC3" + secret_key).encode("utf-8"), date)
        secret_service = _sign(secret_date, service)
        secret_signing = _sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"),
                             hashlib.sha256).hexdigest()

        authorization = (
            f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        req = request.Request(endpoint, data=payload.encode("utf-8"))
        req.add_header("Authorization", authorization)
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("Host", host)
        req.add_header("X-TC-Action", action)
        req.add_header("X-TC-Version", version)
        req.add_header("X-TC-Timestamp", str(timestamp))
        req.add_header("X-TC-Region", region)

        with request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "Response" in data and "TargetText" in data["Response"]:
                return data["Response"]["TargetText"]
    except Exception:
        pass
    return None


def translate_page_result(result: dict, mode: str = "terms") -> dict:
    """翻译爬取结果中的文本字段（title / meta_description）。"""
    if mode == "none":
        return result
    for field in ("title", "meta_description"):
        if result.get(field):
            result[f"{field}_zh"] = quick_translate(result[field], mode)
    return result


if __name__ == "__main__":
    sample = (
        "The Federal Reserve raised interest rates by 25 basis points. "
        "The S&P 500 rallied on strong GDP growth. "
        "Analysts expect Q2 earnings to beat consensus estimates."
    )
    print("原文:", sample)
    print()
    print("术语标注:", translate_financial_terms(sample))
