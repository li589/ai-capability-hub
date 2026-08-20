"""
基金经理实时互动话术生成器 v2.0

核心改进：
1. 持仓按需实时抓取（EastMoney），首次查询后自动缓存到本地
2. 预热模式：后台批量抓取全量持仓（约2小时完成26446个基金）
3. 持仓缓存持久化到 fund_holdings_cache.json
4. 本地有持仓数据(speech_db)的基金经理优先使用本地数据

使用：
  python realtime_manager_talk.py <基金经理> [问题]   # 交互模式
  python realtime_manager_talk.py --warmup             # 后台预热缓存
"""
import json, re, sys, time, urllib.request, os, random
from pathlib import Path

# ============ 配置 ============
# 使用相对于脚本位置的路径，增强跨平台兼容性
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import sys as _sys; _sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from fund_advisor_paths import DATA_DIR  # noqa: E402
SPEECH_DB = os.path.join(str(DATA_DIR), "fund_managers_speech_by_company.json")
CACHE_PATH = os.path.join(str(DATA_DIR), "fund_holdings_cache.json")
BATCH_SIZE = 50       # 每批抓取数量
BATCH_DELAY = 0.3      # 批间延迟(秒)，避免限速
LIVE_DELAY = 0.2       # 单次抓取间隔(秒)

# 股票代码映射（用于实时行情）
CODE_MAP = {
    "中国石油": "sh601857", "紫金矿业": "sh601899", "贵州茅台": "sh600519",
    "长江电力": "sh600900", "宁德时代": "sz300750", "招商银行": "sh600036",
    "比亚迪": "sz002594", "恒瑞医药": "sh600276", "美的集团": "sz000333",
    "五粮液": "sz000858", "隆基绿能": "sh601012", "中国神华": "sh601088",
    "立讯精密": "sz002475", "泸州老窖": "sz000568", "山西汾酒": "sh600809",
    "分众传媒": "sz002027", "格力电器": "sz000651", "申能股份": "sh600642",
    "天德钰": "sz002641", "中国移动": "sh600941", "柳药集团": "sh603368",
    "农业银行": "sh601288", "光峰科技": "sh688007", "有研新材": "sh600206",
    "唯捷创芯": "sz688153", "陕西煤业": "sh601225", "中国银行": "sh601988",
    "工商银行": "sh601398", "腾讯控股": "hk00700", "美团": "hk03690",
    "招商轮船": "sh601872", "华工科技": "sz000988", "长源东谷": "sz603950",
    "睿创微纳": "sh688002", "北方华创": "sz002371", "长川科技": "sz300604",
    "中微公司": "sh688012", "新莱应材": "sz300260", "华海清科": "sh688521",
    "海尔智家": "sh600690", "比音勒芬": "sz002832",
}

# 板块评论（经理核心观点）
SECTOR_COMMENTS = {
    "中国石油": ("能源/原油", "油价的短期波动我不作为买卖依据，中长期逻辑清晰"),
    "紫金矿业": ("黄金/铜", "金铜价格高位震荡，但我更看重个股的质量和成本优势"),
    "贵州茅台": ("白酒消费", "茅台是消费品里的核心资产，短期情绪波动不影响长期逻辑"),
    "宁德时代": ("新能源", "宁德是全球竞争力龙头，波动不改长期方向"),
    "长江电力": ("电力/防御", "电力是防御性配置，分红稳定是我看重的"),
    "招商银行": ("银行", "银行板块当前估值低，有配置价值"),
    "比亚迪": ("新能源汽车", "比亚迪的全球化和技术储备是核心"),
    "恒瑞医药": ("医药", "创新药是我长期看好的方向"),
    "美的集团": ("家电", "家电龙头，高股息+全球化是看点"),
    "五粮液": ("白酒", "五粮液是高端白酒代表，短期需求有压力"),
    "中国神华": ("煤炭", "神华的高分红是核心吸引力，煤炭供需格局改善中"),
    "隆基绿能": ("光伏", "光伏估值在历史底部，等待行业出清"),
    "立讯精密": ("电子", "立讯的品类扩张能力是我看重的"),
    "泸州老窖": ("白酒", "老窖的高端产品线是长期看点"),
    "山西汾酒": ("白酒", "汾酒是全国化名酒，结构升级是长期逻辑"),
    "分众传媒": ("传媒", "分众的楼宇媒体有稀缺性，复苏弹性值得关注"),
    "格力电器": ("家电", "格力的空调龙头地位稳固，盈利能力稳定"),
    "美的集团": ("家电", "美的的全球化布局是长期看点，高股息有吸引力"),
    "华工科技": ("激光", "华工的激光设备在行业内有竞争力"),
    "睿创微纳": ("红外", "睿创的红外技术在国内领先，军民两用"),
    "北方华创": ("半导体设备", "北方华创是国内半导体设备的龙头"),
    "招商轮船": ("航运", "招商轮船的VLCC船队是核心资产"),
}

# ============ 网络工具 ============
def fetch_url(url, headers=None, timeout=10):
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://fund.eastmoney.com/",
        }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"


def get_fund_holdings_realtime(fund_code):
    """从EastMoney实时抓取基金前十大持仓"""
    if not fund_code or str(fund_code) in ("None", "", "nan"):
        return []
    url = (f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx"
           f"?type=jjcc&code={fund_code}&topline=10&year=&month=&rt=0.1")
    r = fetch_url(url)
    if not r or r.startswith("Error"):
        return []
    m = re.search(r'content:"((?:[^"\\]|\\.)*)"', r)
    if not m:
        return []
    content = m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    holdings = []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)
    for row in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if len(tds) < 4:
            continue
        code_m = re.search(r">(\d{6})<", tds[1])
        name_m = re.search(r">([\u4e00-\u9fff]{2,})<", tds[2])
        weight = 0
        for td in tds:
            wm = re.search(r"([\d.]+)%", td)
            if wm:
                weight = float(wm.group(1))
                break
        if code_m and name_m:
            holdings.append({"stock_name": name_m.group(1), "stock_code": code_m.group(1), "weight": weight})
    return holdings[:10]


def get_stock_prices(stock_names):
    """批量抓取个股实时价格/涨跌幅"""
    codes = [CODE_MAP[s] for s in stock_names if s in CODE_MAP]
    if not codes:
        return {}
    r = fetch_url(f"https://hq.sinajs.cn/list={','.join(codes)}",
                  headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"})
    prices = {}
    for line in r.split("\n"):
        m = re.search(r'"([^"]+)"', line)
        if not m:
            continue
        fields = m.group(1).split(",")
        if len(fields) < 4:
            continue
        try:
            prev, curr = float(fields[2]), float(fields[3])
            pct = (curr - prev) / prev * 100 if prev else 0
            for cn, code in CODE_MAP.items():
                if code[2:] in line:
                    prices[cn] = {"price": curr, "pct": pct}
                    break
        except Exception:
            continue
    return prices


def get_fund_estimate(fund_code):
    """获取基金实时估算净值"""
    if not fund_code or str(fund_code) in ("None", "", "nan"):
        return None
    r = fetch_url(f"https://fundgz.1234567.com.cn/js/{fund_code}.js")
    m = re.search(r"jsonpgz\((.+)\)", r)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        return {
            "name": data.get("name", ""),
            "code": data.get("fundcode", ""),
            "nav": data.get("dwjz", ""),
            "estimate": data.get("gsz", ""),
            "estimate_pct": data.get("gszzl", ""),
            "date": data.get("gztime", ""),
        }
    except Exception:
        return None


def get_market_index():
    """获取大盘指数"""
    r = fetch_url("https://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006",
                  headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"})
    indices = {}
    for line in r.split("\n"):
        m = re.search(r'= "([^"]+)"', line)
        if not m:
            continue
        fields = m.group(1).split(",")
        if len(fields) < 4:
            continue
        name = ("上证指数" if "000001" in line else "深证成指" if "399001" in line else "创业板指")
        try:
            prev, curr = float(fields[2]), float(fields[3])
            pct = (curr - prev) / prev * 100 if prev else 0
            indices[name] = {"price": curr, "pct": pct}
        except Exception:
            continue
    return indices


# ============ 缓存管理 ============
def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
            pass
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


# ============ 基金经理产品介绍 ============
def introduce_fund(fund_code: str) -> str:
    """
    基金经理介绍自己管理的基金

    Args:
        fund_code: 基金代码

    Returns:
        基金介绍话术
    """
    # 获取基金经理信息
    mgr_data = get_mgr_data_by_fund(fund_code)
    if not mgr_data:
        return f"抱歉，未找到基金 {fund_code} 的信息。"

    name = mgr_data.get("name", "")
    fund_name = mgr_data.get("fund_name", "")
    style = mgr_data.get("style", "")
    tenure = mgr_data.get("tenure", "")
    holdings = mgr_data.get("holdings", [])
    holdings_source = mgr_data.get("holdings_source", "本地")

    # 获取基金基本信息
    fund_est = get_fund_estimate(fund_code)

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  🎙️ 基金经理基金介绍")
    lines.append(f"{'='*60}")

    # 基金经理自我介绍
    lines.append(f"\n👋 大家好，我是{name}。")
    lines.append(f"   我来介绍一下我管理的代表基金：")
    lines.append(f"\n   📊 {fund_name}（{fund_code}）")

    # 投资风格
    lines.append(f"\n   📈 投资风格：{style}")
    if style == "成长型":
        lines.append(f"   我的风格偏成长，主要配置高成长的科技、新能源赛道。")
    elif style == "价值型":
        lines.append(f"   我的风格偏稳健，注重估值安全边际，追求稳稳的收益。")
    else:
        lines.append(f"   我的风格比较均衡，不赌单一方向，涨时跟上跌时控回撤。")

    # 任职年限
    if tenure:
        lines.append(f"\n   ⏱️ 任职年限：{tenure}年")

    # 持仓信息
    if holdings:
        lines.append(f"\n   📋 近期持仓（前十大重仓）：")
        for i, h in enumerate(holdings[:10], 1):
            sn = h.get("stock_name", h) if isinstance(h, dict) else h
            wt = h.get("weight", "") if isinstance(h, dict) else ""
            lines.append(f"      {i}. {sn}" + (f" ({wt}%)" if wt else ""))
        lines.append(f"\n   （持仓来源：{holdings_source}，仅供参考）")
    else:
        lines.append(f"\n   📋 持仓信息暂时无法获取")

    # 今日估算
    if fund_est:
        ep = float(fund_est.get("estimate_pct", 0) or 0)
        ep_dir = "上涨" if ep > 0 else "下跌" if ep < 0 else "持平"
        lines.append(f"\n   📉 今日估算：{ep_dir} {abs(ep):.2f}%")

    # 投资目标
    lines.append(f"\n   🎯 投资目标：")
    if style == "成长型":
        lines.append(f"   追求长期资本增值，在控制回撤前提下最大化收益。")
        lines.append(f"   适合能承受较大波动、追求长期高收益的投资者。")
    elif style == "价值型":
        lines.append(f"   追求稳定绝对收益，通过基本面分析挖掘价值。")
        lines.append(f"   适合追求稳健收益、风险偏好较低的投资者。")
    else:
        lines.append(f"   追求稳健的绝对收益，强调风险控制和回撤管理。")
        lines.append(f"   适合追求稳健增值的投资者。")

    # 投资建议
    lines.append(f"\n   💡 投资建议：")
    lines.append(f"   建议持有期3年以上，避免追涨杀跌，长期持有效果更佳。")

    lines.append(f"\n{'='*60}")

    return "\n".join(lines)


def generate_fund_analysis(fund_code: str) -> str:
    """
    生成基金产品分析报告

    Args:
        fund_code: 基金代码

    Returns:
        分析报告话术
    """
    mgr_data = get_mgr_data_by_fund(fund_code)
    if not mgr_data:
        return f"抱歉，未找到基金 {fund_code} 的信息。"

    name = mgr_data.get("name", "")
    fund_name = mgr_data.get("fund_name", "")
    fund_est = get_fund_estimate(fund_code)
    market = get_market_index()

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  📊 基金产品分析报告")
    lines.append(f"{'='*60}")

    # 产品信息
    lines.append(f"\n【产品基本信息】")
    lines.append(f"  基金代码：{fund_code}")
    lines.append(f"  基金名称：{fund_name}")
    lines.append(f"  基金经理：{name}")
    lines.append(f"  投资风格：{mgr_data.get('style', '未知')}")

    # 今日表现
    lines.append(f"\n【今日表现】")
    if market:
        for idx_name, idx_data in market.items():
            pct = idx_data.get("pct", 0)
            dir_icon = "📈" if pct > 0 else "📉" if pct < 0 else "➡️"
            lines.append(f"  {idx_name}：{idx_data.get('price', 0):.0f}点 {dir_icon}{abs(pct):.2f}%")

    if fund_est:
        ep = float(fund_est.get("estimate_pct", 0) or 0)
        ep_dir = "📈 +" if ep > 0 else "📉 "
        lines.append(f"  基金估算：{ep_dir}{abs(ep):.2f}%")

    # 持仓分析
    holdings = mgr_data.get("holdings", [])
    if holdings:
        lines.append(f"\n【持仓分析】")
        lines.append(f"  前十大重仓股：")
        for i, h in enumerate(holdings[:10], 1):
            if isinstance(h, dict):
                sn = h.get("stock_name", "")
                wt = h.get("weight", "")
                if wt:
                    lines.append(f"    {i}. {sn}（持仓占比{wt}%）")
                else:
                    lines.append(f"    {i}. {sn}")
            else:
                lines.append(f"    {i}. {h}")

    # 投资风格分析
    style = mgr_data.get("style", "")
    lines.append(f"\n【投资风格】")
    lines.append(f"  风格类型：{style}")
    if style == "成长型":
        lines.append(f"  特征描述：")
        lines.append(f"    - 偏好高成长赛道（科技、新能源等）")
        lines.append(f"    - 持股集中度相对较高")
        lines.append(f"    - 波动相对较大，适合积极型投资者")
    elif style == "价值型":
        lines.append(f"  特征描述：")
        lines.append(f"    - 注重估值安全边际")
        lines.append(f"    - 持仓相对分散")
        lines.append(f"    - 波动较小，适合稳健型投资者")
    else:
        lines.append(f"  特征描述：")
        lines.append(f"    - 风格均衡，不押注单一方向")
        lines.append(f"    - 仓位管理灵活")
        lines.append(f"    - 适合平衡型投资者")

    lines.append(f"\n{'='*60}")
    lines.append(f"  以上分析仅供参考，不构成投资建议。")
    lines.append(f"{'='*60}")

    return "\n".join(lines)


# ============ 数据获取 ============

def _load_managers_index():
    cache_key = "mgr_index_v1"
    if hasattr(_load_managers_index, '_cache'):
        return _load_managers_index._cache
    import json as _json
    mgrs_path = os.path.join(str(DATA_DIR), "fund_managers_distilled.json")
    index = {}
    if os.path.exists(mgrs_path):
        with open(mgrs_path, "r", encoding="utf-8") as f:
            data = _json.load(f)
        for m in data.get("managers", []):
            fc = m.get("current_fund_code", "")
            if fc:
                index[fc] = m
    _load_managers_index._cache = index
    return index


def get_mgr_data_by_fund(fund_code: str):
    fc = str(fund_code).strip()
    if not fc or fc in ("None", "", "nan"):
        return None
    index = _load_managers_index()
    m = index.get(fc)
    if not m:
        for mm in index.values():
            if mm.get("current_fund_name", "") and fc in mm["current_fund_name"]:
                m = mm
                break
    if not m:
        return None
    return {
        "name": m.get("name", ""),
        "fund_name": m.get("current_fund_name", ""),
        "style": m.get("investment_style", ""),
        "tenure": str(m.get("tenure_years", "")),
        "holdings": [],
        "holdings_source": "本地经理档案",
    }


def get_manager_data(name, cache):
    """获取基金经理的完整数据（本地+实时）"""
    with open(SPEECH_DB, "r", encoding="utf-8") as f:
        speech_db = json.load(f)

    mgr_record = None
    for company, managers in speech_db.get("by_company", {}).items():
        for m in managers:
            if name in m.get("name", ""):
                mgr_record = m
                break
        if mgr_record:
            break

    if not mgr_record:
        return None, cache

    fund_code = str(mgr_record.get("fund_code", ""))
    sc = mgr_record.get("scenarios", {})

    # 持仓优先顺序：本地top_stocks_real > 缓存 > 实时抓取
    holdings = sc.get("top_stocks_real", [])
    source = "本地"

    if not holdings or len(holdings) == 0:
        # 尝试从缓存读取
        if fund_code and fund_code in cache:
            holdings = cache[fund_code]
            source = "缓存"
        else:
            # 实时抓取
            time.sleep(LIVE_DELAY)
            holdings = get_fund_holdings_realtime(fund_code)
            source = "实时抓取"
            # 更新缓存
            if holdings and len(holdings) > 0:
                cache[fund_code] = holdings
                save_cache(cache)

    return {
        "name": mgr_record.get("name", ""),
        "fund_name": mgr_record.get("fund_name", ""),
        "fund_code": fund_code,
        "style": mgr_record.get("style", ""),
        "tenure": mgr_record.get("tenure_years", ""),
        "aum": mgr_record.get("aum", ""),
        "holdings": holdings,
        "holdings_source": source,
    }, cache


# ============ 合成回答 ============
def synthesize(mgr_data, prices, fund_est, market, question):
    name = mgr_data["name"]
    fund_name = mgr_data["fund_name"]
    fund_code = mgr_data["fund_code"]
    style = mgr_data["style"]
    tenure = mgr_data["tenure"]
    aum = mgr_data["aum"]
    holdings = mgr_data["holdings"]
    holdings_source = mgr_data.get("holdings_source", "本地")
    top_stocks = holdings[:5]

    # 大盘
    idx_info = ""
    if market:
        main_idx = market.get("上证指数", {})
        idx_pct = main_idx.get("pct", 0)
        idx_price = main_idx.get("price", 0)
        idx_dir = "上涨" if idx_pct > 0 else "下跌" if idx_pct < 0 else "基本持平"
        idx_info = "今天上证指数%.0f点，%s%.2f%%。" % (idx_price, idx_dir, abs(idx_pct))

    # 基金估算
    fund_info = ""
    if fund_est:
        ep = float(fund_est.get("estimate_pct") or 0)
        est_dir = "涨" if ep > 0 else "跌" if ep < 0 else "平"
        fund_info = "今天我们产品估算%s%.2f%%。" % (est_dir, abs(ep))

    # 持仓动态
    stock_details = []
    for s in top_stocks:
        sn = s.get("stock_name", "")
        wt = s.get("weight", "")
        p = prices.get(sn, {})
        pct = p.get("pct", None)
        if pct is not None:
            d = chr(8593) if pct > 0 else chr(8595) if pct < 0 else chr(8594)
            stock_details.append("%s（%s）%s%.2f%%" % (sn, ("%.1f%%" % wt if wt else ""), d, abs(pct)))
        else:
            stock_details.append("%s（%s）" % (sn, ("%.1f%%" % wt if wt else "")))

    # 情绪
    mood = "分化"
    up_n = sum(1 for p in prices.values() if p.get("pct", 0) > 0)
    dn_n = sum(1 for p in prices.values() if p.get("pct", 0) < 0)
    if up_n > dn_n:
        mood = "偏强"
    elif dn_n > up_n:
        mood = "偏弱"

    big_up = [(n, p["pct"]) for n, p in prices.items() if p.get("pct", 0) > 2]
    big_dn = [(n, p["pct"]) for n, p in prices.items() if p.get("pct", 0) < -2]

    paragraphs = []

    # 市场观点路由
    if any(kw in question for kw in ["大盘", "市场", "怎么看", "观点", "股市", "行情", "今天", "分析"]):
        paragraphs.append(idx_info)
        paragraphs.append("今天市场整体%s。" % mood)
        if big_up:
            n, p = big_up[0]
            paragraphs.append("%s今天走势较强，涨了%.1f个点。" % (n, p))
        if big_dn:
            n, p = big_dn[0]
            paragraphs.append("%s今天回调了%.1f个点。" % (n, abs(p)))
        if top_stocks:
            top_name = top_stocks[0]["stock_name"]
            if top_name in SECTOR_COMMENTS:
                sector, comment = SECTOR_COMMENTS[top_name]
                paragraphs.append("%s这块，%s" % (sector, comment))
            else:
                paragraphs.append("我重点配置的成长方向，短期波动不影响我的中长期判断。")
        paragraphs.append("我不太爱频繁择时，看好方向的基本面没变，就拿着。")

    # 持仓路由
    elif any(kw in question for kw in ["持仓", "重仓", "仓位", "买了", "股票", "怎么样"]):
        paragraphs.append("你问持仓，我直接跟你说：")
        if stock_details:
            paragraphs.append("今日主要持仓：" + "，".join(stock_details))
        else:
            paragraphs.append("（%s）" % holdings_source)
        if fund_info:
            paragraphs.append(fund_info)
        if big_dn:
            n, p = big_dn[0]
            paragraphs.append("其中%s今天跌了%.1f个点，短期扰动，我不操作。" % (n, abs(p)))

    # 亏损安抚
    elif any(kw in question for kw in ["亏", "跌", "回撤", "绿"]):
        paragraphs.append("这种波动我见得多了，说实话我不慌。")
        if big_dn:
            n, p = big_dn[0]
            paragraphs.append("今天主要拖后腿的是%s，跌了%.1f个点，但它的中长期逻辑没变。" % (n, abs(p)))
        paragraphs.append("我的策略是以年度为单位，淡化短期噪音。你如果认可这个思路，拿住就好。")

    # 自我介绍
    elif any(kw in question for kw in ["你是谁", "介绍", "背景", "简历"]):
        paragraphs.append("%s，%s年管理经验，%s风格，目前在管%s。" % (name, tenure, style, fund_name))
        if aum:
            paragraphs.append("管理规模大概%s。" % aum)
        paragraphs.append("我的理念是以合理价格买优质公司，长期持有，不追热点。")

    # 默认
    else:
        if idx_info:
            paragraphs.append(idx_info)
        if fund_info:
            paragraphs.append(fund_info)
        if stock_details:
            paragraphs.append("目前前十大持仓：" + "、".join(stock_details))
        else:
            paragraphs.append("精选个股、均衡配置是我的一贯做法。")

    return "\\n".join(paragraphs), holdings_source


# ============ 预热模式 ============
def warmup_cache():
    """后台预热：批量抓取所有基金的持仓数据"""
    print("开始预热持仓缓存...")
    with open(SPEECH_DB, "r", encoding="utf-8") as f:
        speech_db = json.load(f)

    # 收集所有fund_code
    fund_codes = set()
    for company, managers in speech_db.get("by_company", {}).items():
        for m in managers:
            fc = str(m.get("fund_code", ""))
            if fc and fc not in ("None", "", "nan"):
                fund_codes.add(fc)

    # 加载现有缓存
    cache = load_cache()
    cached = set(cache.keys())
    todo = list(fund_codes - cached)
    total = len(todo)
    print(f"总待抓取: {total} 个基金，已有缓存: {len(cached)}")

    done = 0
    errors = 0
    for i in range(0, min(total, 5000), BATCH_SIZE):  # 每次最多5000个，避免单次运行太久
        batch = todo[i:i+BATCH_SIZE]
        for fc in batch:
            h = get_fund_holdings_realtime(fc)
            if h and len(h) > 0:
                cache[fc] = h
            else:
                errors += 1
            done += 1
            time.sleep(BATCH_DELAY)
            if done % 500 == 0:
                save_cache(cache)
                print(f"  进度: {done}/{total} (缓存{len(cache)}个, 失败{errors}个)")
        save_cache(cache)
        print(f"  完成批次: {i//BATCH_SIZE+1}, 累计{done}个")

    save_cache(cache)
    print(f"预热完成: 共抓取{done}个, 失败{errors}个, 缓存总计{len(cache)}个基金")
    return cache


# ============ 主程序 ============
def main():
    cache = load_cache()

    if len(sys.argv) >= 2 and sys.argv[1] == "--warmup":
        warmup_cache()
        return

    if len(sys.argv) < 2:
        print("用法:")
        print("  python realtime_manager_talk.py <基金经理> [问题]")
        print("  python realtime_manager_talk.py --warmup   # 后台预热持仓缓存")
        sys.exit(1)

    name = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else ""

    mgr_data, cache = get_manager_data(name, cache)
    if not mgr_data:
        print("错误: 找不到基金经理 %s" % name)
        sys.exit(1)

    holdings = mgr_data["holdings"]
    fund_code = mgr_data["fund_code"]

    # 批量抓取行情
    stock_names = [s["stock_name"] for s in holdings[:5]]
    prices = get_stock_prices(stock_names) if stock_names else {}
    time.sleep(0.3)
    fund_est = get_fund_estimate(fund_code) if fund_code and fund_code not in ("None", "") else None
    market = get_market_index()

    response, src = synthesize(mgr_data, prices, fund_est, market, question)

    # 输出
    print("=" * 55)
    print("[%s] 实时互动  (持仓来源: %s)\\n" % (name, src))

    if market:
        for idx, d in market.items():
            dd = chr(8593) if d["pct"] > 0 else chr(8595) if d["pct"] < 0 else chr(8594)
            print("  %s: %.0f (%s%.2f%%)" % (idx, d["price"], dd, abs(d["pct"])))

    if fund_est:
        ep = float(fund_est.get("estimate_pct") or 0)
        print("  %s 估算: %s%.2f%%" % (fund_est["name"], "+" if ep > 0 else "", ep))

    if prices:
        print()
        for sn, p in prices.items():
            dd = chr(8593) if p["pct"] > 0 else chr(8595) if p["pct"] < 0 else chr(8594)
            print("  %s: %.2f (%s%.2f%%)" % (sn, p["price"], dd, abs(p["pct"])))

    print()
    print("=" * 55)
    print(response)


if __name__ == "__main__":
    main()
