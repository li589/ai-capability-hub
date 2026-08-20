#!/usr/bin/env python3
"""
天天基金全量数据刷新脚本 v1.0
================================
从天天基金网获取：
  1. 全部基金经理信息（含任职天数、管理规模、最佳回报）
  2. 全部基金产品信息（代码、名称、类型）
  3. 基金公司信息（从经理数据聚合）
  4. 基金经理十大重仓股（从基金持仓页面爬取）

输出：
  - data/全市场基金经理名录_天天基金.json (原始数据)
  - data/fund_managers_distilled.json (蒸馏后经理档案)
  - data/fund_companies_distilled.json (公司档案)
  - data/fund_products.json (产品目录)
  - data/holdings_database.json (十大重仓)

依赖：Python 3.8+ 标准库（urllib + json + re）
网络：需要访问 fund.eastmoney.com
耗时：全量采集预计 40-60 分钟（4,000+ 经理 × 持仓页）
"""
import json
import os
import random  # v9.0: 网络重试指数退避需要（此前仅 distill_managers 局部导入，重试路径 NameError 无限挂死）
import re
import sys
import time
import hashlib
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional

# ── 路径设置 ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent))  # fund-advisor root
sys.path.insert(0, str(SCRIPT_DIR.parent))          # scripts/

try:
    from scripts.fund_advisor_paths import DATA_DIR, load_json_data, _find_base_dir, ensure_dirs
    BASE_DIR = _find_base_dir()
    DATA_PATH = DATA_DIR
except ImportError:
    BASE_DIR = SCRIPT_DIR.parent.parent
    DATA_PATH = BASE_DIR / "data"
    ensure_dirs = lambda: DATA_PATH.mkdir(parents=True, exist_ok=True)

ensure_dirs()

# ── HTTP 工具 ─────────────────────────────────────────────────────────
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REFERER = 'https://fund.eastmoney.com/'

def http_get(url, timeout=20, encoding='utf-8', retries=3, label=''):
    """带指数退避+随机抖动的 HTTP GET"""
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': USER_AGENT,
                'Referer': REFERER,
                'Accept': 'text/html,application/json,*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                return raw.decode(encoding, errors='replace')
        except urllib.error.HTTPError as e:
            last_error = f'HTTP {e.code}'
            if e.code in (403, 404, 410):
                break
        except urllib.error.URLError as e:
            last_error = f'网络错误: {e.reason}'
        except Exception as e:
            last_error = str(e)[:80]
            if attempt == retries - 1:
                raise
        if attempt < retries - 1:
            wait = (2 ** attempt) + random.uniform(0, 1)
            if label and attempt > 0:
                print(f'  [RETRY] {label} ({wait:.1f}s): {last_error}')
            time.sleep(wait)
    if label and last_error:
        print(f'  [WARN] {label}: {last_error}')
    return ''
def save_json(data, filename, compress=False):
    """保存 JSON 文件"""
    path = DATA_PATH / filename
    with open(str(path), 'w', encoding='utf-8') as f:
        if compress:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = path.stat().st_size / 1024
    return path, size_kb


# ══════════════════════════════════════════════════════════════════════
# 第一步：获取全部基金经理
# ══════════════════════════════════════════════════════════════════════

def fetch_all_managers():
    """
    从天天基金 DataPortfolio 接口获取全部基金经理
    每页 50 条，共约 85 页
    """
    print("\n" + "=" * 60)
    print("  第一步：获取全部基金经理")
    print("=" * 60)

    all_managers = []
    page = 1
    page_size = 50

    while True:
        url = (f'https://fund.eastmoney.com/Data/FundDataPortfolio_Interface.aspx'
               f'?dt=14&ft=all&pn={page_size}&pi={page}&sc=abbname&st=asc&mc=returnjson')

        try:
            text = http_get(url, timeout=25)
        except Exception as e:
            print(f"  [WARN] 第{page}页请求失败: {e}，重试...")
            time.sleep(3)
            continue

        # 解析: var returnjson= {data:[...], pages:N, record:N, curpage:N}
        # 注意：JS 对象格式（key 无引号），需要转换为 JSON
        idx = text.find('returnjson=')
        if idx < 0:
            print(f"  [ERROR] 第{page}页无法解析，前200字符: {text[:200]}")
            break
        brace_start = text.find('{', idx)
        if brace_start < 0:
            print(f"  [ERROR] 第{page}页找不到JSON起始")
            break
        # 匹配括号
        depth = 0
        brace_end = brace_start
        for i in range(brace_start, len(text)):
            if text[i] == '{': depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    brace_end = i + 1
                    break

        json_str = text[brace_start:brace_end]

        # 给无引号的 key 加上双引号（JS → JSON）
        # 匹配: 字母/下划线组成的 key 后跟冒号
        json_str = re.sub(r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:', r'"\1":', json_str)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
                print(f"  [ERROR] JSON 解析失败: {e}")
                break

        records = data.get('data', [])
        total_pages = data.get('pages', data.get('pageCount', 0))
        total_records = data.get('records', data.get('totalCount', 0))

        for rec in records:
            # 字段: [raw_id, name, manager_id, company, fund_codes, fund_names,
            #        tenure_days, best_return, current_fund_code, current_fund_name,
            #        total_scale, latest_best_return]
            if len(rec) >= 12:
                all_managers.append({
                    'raw_id': str(rec[0]),
                    'name': str(rec[1]),
                    'manager_id': str(rec[2]),
                    'company_name': str(rec[3]),
                    'fund_codes': str(rec[4]) if len(rec) > 4 else '',
                    'fund_names': str(rec[5]) if len(rec) > 5 else '',
                    'tenure_days': int(rec[6]) if len(rec) > 6 and rec[6] else 0,
                    'best_return': str(rec[7]) if len(rec) > 7 else '',
                    'current_fund_code': str(rec[8]) if len(rec) > 8 else '',
                    'current_fund_name': str(rec[9]) if len(rec) > 9 else '',
                    'total_scale': str(rec[10]) if len(rec) > 10 else '',
                    'latest_best_return': str(rec[11]) if len(rec) > 11 else '',
                })

        print(f"  第{page}/{total_pages}页: {len(records)}条 "
              f"(累计{len(all_managers)}/{total_records})")

        if page >= total_pages or len(records) < page_size:
            break

        page += 1
        time.sleep(0.3)  # 礼貌间隔

    print(f"\n  完成! 共获取 {len(all_managers)} 位基金经理")

    # 保存原始数据
    raw_path, raw_size = save_json({
        'managers': all_managers,
        'meta': {
            'total': len(all_managers),
            'source': '天天基金DataPortfolio接口',
            'fetched_at': datetime.now().isoformat(),
            'version': '1.0'
        }
    }, '全市场基金经理名录_天天基金.json')

    print(f"  原始数据已保存: {raw_path} ({raw_size:.0f} KB)")
    return all_managers


# ══════════════════════════════════════════════════════════════════════
# 第二步：获取全部基金产品
# ══════════════════════════════════════════════════════════════════════

def fetch_all_products():
    """
    从天天基金 fundcode_search.js 获取全部基金产品
    """
    print("\n" + "=" * 60)
    print("  第二步：获取全部基金产品")
    print("=" * 60)

    url = 'https://fund.eastmoney.com/js/fundcode_search.js'
    text = http_get(url, timeout=20)
    if not text:
        print("  [ERROR] 无法获取基金产品列表")
        return []

    # 格式: var r = [["000001","HXCZHH","华夏成长混合","混合型-灵活","HUAXIA..."],...]
    # 字段顺序: [基金代码, 拼音缩写, 基金名称, 基金类型, 拼音全称]
    # 提取整个数组
    m = re.search(r'var\s+r\s*=\s*(\[\[.*\]\])', text, re.DOTALL)
    if not m:
        # 备用: 可能是其他变量名
        m = re.search(r'=\s*(\[\[.*\]\])\s*;?\s*$', text, re.DOTALL)
    if not m:
        print(f"  [ERROR] 无法解析产品列表，前300字符: {text[:300]}")
        return []

    array_str = m.group(1)
    # 解析为 Python 对象
    # 注意：JS 字符串可能包含转义，需要用 json.loads
    # 把单引号替换为双引号（简单情况）
    try:
        # 直接尝试 JSON 解析（天天基金 JS 使用双引号）
        products_raw = json.loads(array_str)
    except json.JSONDecodeError:
        # 如果失败，使用更宽松的解析
        products_raw = []
        # 匹配每个子数组: ["code","name","type","pinyin"]
        for match in re.finditer(r'\["(\d{6})","([^"]*)","([^"]*)","([^"]*)"\]', array_str):
            products_raw.append([match.group(1), match.group(2),
                                match.group(3), match.group(4)])

    products = []
    for p in products_raw:
        if len(p) >= 4:
            products.append({
                'fund_code': str(p[0]),
                'fund_name': str(p[2]),
                'fund_type': str(p[3]),
                'pinyin': str(p[1]),
            })

    print(f"  共获取 {len(products)} 只基金产品")

    # 按类型统计
    type_counts = Counter(p['fund_type'] for p in products)
    for ft, cnt in type_counts.most_common(10):
        print(f"    {ft}: {cnt}")

    # 保存为 v6.1+ 新列存格式（与盘上现行格式一致，_lookup_fund 等消费方依赖 code/name/type 列名）
    today = datetime.now().strftime('%Y-%m-%d')
    compressed = {
        '_f': ['code', 'name', 'type', 'pinyin', 'update'],
        'c': [
            [p['fund_code'] for p in products],
            [p['fund_name'] for p in products],
            [p['fund_type'] for p in products],
            [p.get('pinyin', '') for p in products],
            [today] * len(products),
        ],
        'm': {
            'count': len(products),
            'source': '天天基金 fundcode_search.js',
            'updated': today
        }
    }
    path, size = save_json(compressed, 'fund_products.json', compress=True)
    print(f"  产品数据已保存: {path} ({size:.0f} KB)")
    return products


# ══════════════════════════════════════════════════════════════════════
# 第三步：聚合基金公司信息
# ══════════════════════════════════════════════════════════════════════

def build_companies(managers):
    """
    从基金经理数据聚合公司信息
    """
    print("\n" + "=" * 60)
    print("  第三步：聚合基金公司信息")
    print("=" * 60)

    companies = defaultdict(lambda: {
        'name': '',
        'manager_count': 0,
        'total_scale': 0.0,
        'manager_ids': [],
        'style_counts': Counter(),
    })

    for m in managers:
        company_name = m.get('company_name', '')
        if not company_name:
            continue

        c = companies[company_name]
        c['name'] = company_name
        c['manager_count'] += 1
        c['manager_ids'].append(m.get('manager_id', ''))

        # 解析规模
        scale_str = m.get('total_scale', '0')
        try:
            if '亿' in str(scale_str):
                scale = float(str(scale_str).replace('亿元', '').replace('亿', '').strip())
                c['total_scale'] += scale
        except (ValueError, TypeError):
            pass

    company_list = []
    for name, c in companies.items():
        # 确定主导风格
        dominant = '均衡型'
        if c['style_counts']:
            dominant = c['style_counts'].most_common(1)[0][0]

        company_list.append({
            'name': name,
            'manager_count': c['manager_count'],
            'total_scale': round(c['total_scale'], 2),
            'manager_ids': c['manager_ids'][:50],
            'style_code': 'BALANCED',
            'alt_style_codes': [],
        })

    company_list.sort(key=lambda x: -x['total_scale'])

    print(f"  共聚合 {len(company_list)} 家基金公司")
    print(f"  前10大公司:")
    for c in company_list[:10]:
        print(f"    {c['name']}: {c['manager_count']}位经理, {c['total_scale']:.0f}亿")

    # 保存为列式压缩格式
    columns = ['name', 'manager_count', 'total_scale', 'manager_ids',
               'style_code', 'alt_style_codes']
    rows = [[c['name'], c['manager_count'], c['total_scale'],
             json.dumps(c['manager_ids'], ensure_ascii=False),
             c['style_code'], json.dumps(c['alt_style_codes'], ensure_ascii=False)]
            for c in company_list]

    compressed = {
        '_f': 'c',
        'c': columns,
        'd': rows,
        'm': {
            'total_count': len(company_list),
            'last_update': datetime.now().strftime('%Y-%m-%d'),
            'source': '从基金经理数据聚合'
        }
    }
    path, size = save_json(compressed, 'fund_companies_distilled.json', compress=True)
    print(f"  公司数据已保存: {path} ({size:.0f} KB)")
    return company_list


# ══════════════════════════════════════════════════════════════════════
# 第四步：获取十大重仓股
# ══════════════════════════════════════════════════════════════════════

def _parse_holdings_from_html(html_text):
    """从天天基金持仓页面 HTML 中解析十大重仓股"""
    stocks = []
    seen_codes = set()

    # 模式1: 标准格式 <a href='.../r/1.601872'>601872</a></td><td class='to[l|c]'><a href='...'>招商轮船</a>
    pattern1 = re.compile(
        r"<a\s+href='[^']*?/r/\d\.(\d{6})'>\1</a>\s*</td>\s*"
        r"<td\s+class='to[lc]'[^>]*?>\s*<a\s+href='[^']*?'>([^<]+)</a>",
        re.DOTALL
    )
    for m in pattern1.finditer(html_text):
        code = m.group(1)
        name = m.group(2).strip()
        if code not in seen_codes:
            seen_codes.add(code)
            weight = _find_weight(html_text, m.end(), code)
            stocks.append({'stock_code': code, 'stock_name': name, 'weight': weight})

    # 模式2: QDII/特殊格式 <td class='to[lc]'>(\d{6})</td><td class='to[lc]' ...>股票名</td>
    if not stocks:
        pattern2 = re.compile(
            r"<td\s+class='to[lc]'[^>]*?>\s*<a[^>]*?>\s*(\d{6})\s*</a>\s*</td>\s*"
            r"<td\s+class='to[lc]'[^>]*?>\s*<a[^>]*?>([^<]+)</a>",
            re.DOTALL
        )
        for m in pattern2.finditer(html_text):
            code = m.group(1)
            name = m.group(2).strip()
            if code not in seen_codes and not name.startswith('<') and len(name) >= 2:
                seen_codes.add(code)
                weight = _find_weight(html_text, m.end(), code)
                stocks.append({'stock_code': code, 'stock_name': name, 'weight': weight})

    return stocks[:10]


def _find_weight(html_text, start_pos, code):
    """在HTML中查找指定股票代码附近的权重百分比"""
    search_text = html_text[start_pos:start_pos+800]
    # 权重通常在 <td class='tor'>X.XX%</td> 或类似格式
    weight_match = re.search(r"<td\s+class='to[rl]'\s*>?\s*([\d.]+%)\s*</td>", search_text)
    if not weight_match:
        weight_match = re.search(r"([\d.]+%)\s*</td>", search_text)
    if weight_match:
        try:
            return float(weight_match.group(1).replace('%', ''))
        except ValueError:
            pass
    return 0.0


def fetch_holdings_for_fund(fund_code, fund_name=''):
    """
    获取单只基金的十大重仓股
    通过 FundArchivesDatas API（主路径）+ pingzhongdata 备用路径
    """
    if not fund_code or fund_code in ('', '0', 'null'):
        return None

    lbl = f'基金{fund_code}'
    ts = int(time.time() * 1000) % 1000000
    url = (f'https://fundf10.eastmoney.com/FundArchivesDatas.aspx'
           f'?type=jjcc&code={fund_code}&topline=10&year=&month=&rt=0.{ts}')

    try:
        text = http_get(url, timeout=15, label=lbl)
        if not text or len(text) < 500:
            # 备用路径：pingzhongdata
            url2 = f'https://fund.eastmoney.com/pingzhongdata/{fund_code}.js'
            text = http_get(url2, timeout=12, label=f'{lbl}(备用)')
            if not text or len(text) < 200:
                return None
            # 从 pingzhongdata 解析持仓（格式不同，仅提取股票代码）
            stocks = []
            sc_match = __import__('re').search(r'stockCodes\s*=\s*\[(.*?)\]', text)
            if sc_match:
                codes = __import__('re').findall(r'["\'](\d+)["\']', sc_match.group(1))
                for c in codes[:10]:
                    stocks.append({'stock_code': c, 'stock_name': '', 'weight': 0.0})
            return stocks if stocks else None

        # 解析 var apidata={content:"...", ...}
        m = re.search(r'var\s+apidata\s*=\s*(\{.+?\});', text, re.DOTALL)
        if not m:
            return None

        js_str = m.group(1)
        # 给 JS key 加引号
        js_str = re.sub(r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:', r'"\1":', js_str)
        data = json.loads(js_str)

        html_content = data.get('content', '')
        if not html_content or len(html_content) < 500:
            return None

        # 检查是否包含持仓数据（"重仓"、"持仓"、"股票投资明细" 等）
        has_holdings = any(kw in html_content for kw in ['重仓', '持仓', '股票投资', '投资明细'])
        if not has_holdings:
            return None

        stocks = _parse_holdings_from_html(html_content)
        if stocks:
            return stocks
    except Exception:
        pass
    return None


def fetch_all_holdings(managers, max_funds=None, delay=0.3, quarter='2026Q2', asof='2026-06-30'):
    """
    批量获取所有基金的十大重仓股（按基金代码去重）

    参数:
        managers: 基金经理列表
        max_funds: 限制采集基金数（None=全部）
        delay: 每次请求间隔（秒）
        quarter/asof: 写入元数据的季度标识（页面默认返回最新已披露季度）
    """
    print("\n" + "=" * 60)
    print("  第四步：获取基金十大重仓股（按基金代码去重）")
    print("=" * 60)

    # 去重：同一基金代码只爬一次
    seen_funds = set()
    unique_funds = []
    for m in managers:
        fc = m.get('current_fund_code', '')
        fn = m.get('current_fund_name', '')
        if fc and fc not in ('', '0', 'null') and fc not in seen_funds:
            seen_funds.add(fc)
            unique_funds.append({
                'fund_code': fc,
                'fund_name': fn,
                'manager_name': m.get('name', ''),
                'company_name': m.get('company_name', ''),
            })

    target = unique_funds[:max_funds] if max_funds else unique_funds
    total = len(target)

    print(f"  待采集: {total} 只唯一基金")
    print(f"  预计耗时: ~{total * delay / 60:.0f} 分钟")

    all_holdings = []
    success_count = 0
    fail_count = 0
    start_time = time.time()

    for i, f in enumerate(target):
        fund_code = f['fund_code']
        stocks = fetch_holdings_for_fund(fund_code, f.get('fund_name', ''))

        if stocks:
            all_holdings.append({
                'fund_code': fund_code,
                'fund_name': f.get('fund_name', ''),
                'manager_name': f.get('manager_name', ''),
                'company_name': f.get('company_name', ''),
                'stocks': stocks,
                'fetched_at': datetime.now().isoformat(),
            })
            success_count += 1
        else:
            fail_count += 1

        # 进度显示
        if (i + 1) % 200 == 0 or i == total - 1:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (total - i - 1) / rate if rate > 0 else 0
            pct = (i + 1) / total * 100
            print(f"  进度: {i+1}/{total} ({pct:.1f}%) "
                  f"成功={success_count} 失败={fail_count} "
                  f"速率={rate:.1f}/s ETA={eta/60:.0f}min")

        time.sleep(delay)

    # 已按基金代码去重，直接使用
    unique_holdings = all_holdings

    elapsed = time.time() - start_time
    print(f"\n  完成! 耗时 {elapsed/60:.1f} 分钟")
    print(f"  成功: {success_count}/{total} ({success_count/total*100:.1f}%)")
    print(f"  唯一基金持仓: {len(unique_holdings)}")

    # 保存为 v7.2+ 紧凑格式: {"h":[{fc,fn,mg,co,ss:[[code,name,weight],...]}],"m":{...}}
    # 消费方通过 scripts/fund_advisor_paths.load_holdings() 统一解码
    compact = []
    for h in unique_holdings:
        stocks = h.get('stocks', [])
        compact.append({
            'fc': h['fund_code'],
            'fn': h['fund_name'],
            'mg': h.get('manager_name', ''),
            'co': h.get('company_name', ''),
            'ss': [[s.get('stock_code', ''), s.get('stock_name', ''),
                    round(float(s.get('weight', 0.0)), 2)] for s in stocks],
        })

    path, size = save_json({
        'h': compact,
        'm': {
            'count': len(compact),
            'quarter': quarter,
            'asof': asof,
            'fetched_at': datetime.now().isoformat(),
            'source': '天天基金 FundArchivesDatas',
            'success_rate': f'{success_count}/{total}'
        }
    }, 'holdings_database.json', compress=True)

    print(f"  持仓数据已保存: {path} ({size:.0f} KB)")
    return unique_holdings


# ══════════════════════════════════════════════════════════════════════
# 第五步：蒸馏基金经理数据（生成丰富档案）
# ══════════════════════════════════════════════════════════════════════

# 行业分类关键词
SECTOR_KEYWORDS = {
    '科技': ['科技', '软', '硬', '电子', '通信', '计算机', '半导体', '芯片', 'AI', '人工智能',
             '软件', '数据', '云计算', '互联网', '信息'],
    '新能源': ['新能源', '光伏', '锂', '电池', '储能', '电动车', '汽车', '动力', '风电',
              '充电', '太阳能', '氢能'],
    '消费': ['酒', '消费', '食品', '饮料', '家电', '商贸', '旅游', '酒店', '白酒', '啤酒',
             '乳业', '调味', '餐饮', '零售'],
    '医药': ['医药', '医疗', '生物', '疫苗', '中药', '健康', '制药', '器械', '医院'],
    '金融': ['银行', '保险', '券商', '信托', '地产', '物业', '证券', '金控'],
    '制造': ['机械', '化工', '材料', '军工', '航空', '制造', '设备', '重工', '装备',
             '钢铁', '有色', '煤炭', '矿业', '建材'],
}

# 投资建议模板
INVESTMENT_ADVICE = {
    '成长型': [
        "适合风险承受能力较强、追求长期资本增值的投资者，建议采用定投方式参与。",
        "波动较大，建议闲置资金配置，避免追涨杀跌，长期持有效果更佳。",
        "适合投资周期3年以上的投资者，可作为卫星配置。",
    ],
    '价值型': [
        "适合追求稳健收益、控制回撤的投资者，波动相对较小。",
        "建议长期持有，享受复利增长，适合养老金、教育金规划。",
        "适合1-3年中长期投资，是资产组合的压舱石。",
    ],
    '均衡型': [
        "适合大多数投资者，风险与收益平衡较好。",
        "建议作为核心配置，搭配其他风格基金构建组合。",
        "适合定投和一次性配置，投资周期2-5年。",
    ],
}

RISK_WARNINGS = {
    '成长型': "成长风格波动较大，短期可能出现较大回撤，请注意控制仓位。",
    '价值型': "价值风格在市场大涨时可能跑输大盘，需要有足够的耐心。",
    '均衡型': "均衡风格回撤可控，但在极端行情下也会有波动。",
}

SUITABLE_INVESTORS = {
    '成长型': "积极型投资者，能承受20%以上回撤，追求年化15%+收益",
    '价值型': "稳健型投资者，能承受10%以内回撤，追求年化8-12%收益",
    '均衡型': "平衡型投资者，能承受15%左右回撤，追求年化10-15%收益",
}


def detect_sector(text):
    """从文本判断行业"""
    if not text:
        return '综合'
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return sector
    return '综合'


def detect_style(fund_name, fund_type=''):
    """从基金名及类型判断投资风格"""
    name = (fund_name or '') + (fund_type or '')
    if any(kw in name for kw in ['成长', '积极', '创新', '新兴', '科技', '先锋', '进取']):
        return '成长型'
    if any(kw in name for kw in ['价值', '稳健', '红利', '低波', '蓝筹', '大盘']):
        return '价值型'
    if any(kw in name for kw in ['债券', '货币', '纯债', '短债', '中短债']):
        return '价值型'
    return '均衡型'


def determine_stage(tenure_days):
    """根据任职天数判断产品阶段"""
    if tenure_days < 180:
        return '萌芽期'
    elif tenure_days < 365 * 2:
        return '成长期'
    elif tenure_days < 365 * 5:
        return '成熟期'
    else:
        return '老牌期'


def distill_managers(managers, holdings_data=None):
    """
    蒸馏基金经理数据：添加投资风格、行业判断、投资建议等字段
    """
    print("\n" + "=" * 60)
    print("  第五步：蒸馏基金经理数据")
    print("=" * 60)

    # 建立基金代码→持仓映射
    # holdings_data 为 fetch_all_holdings 返回的基金级记录 {fund_code, stocks:[...]}，
    # 需展平为股票级行 {stock_code, stock_name, weight}
    fund_holdings = {}
    if holdings_data:
        for h in holdings_data:
            fc = h.get('fund_code', '')
            if not fc:
                continue
            rows = fund_holdings.setdefault(fc, [])
            stocks = h.get('stocks')
            if isinstance(stocks, list):
                for s in stocks:
                    if isinstance(s, dict):
                        rows.append(s)
            else:
                # 兼容股票级行格式（含 stock_name 字段）
                rows.append(h)

    distilled = []
    import random
    random.seed(42)

    for m in managers:
        fund_name = m.get('current_fund_name', '')
        fund_code = m.get('current_fund_code', '')
        fund_type = ''
        tenure_days = m.get('tenure_days', 0)

        # 投资风格
        style = detect_style(fund_name, fund_type)

        # 行业判断（从持仓中推断）
        sector_desc = ''
        sectors = set()
        holdings = fund_holdings.get(fund_code, [])
        for h in holdings:
            stock_name = h.get('stock_name', '')
            sec = detect_sector(stock_name)
            if sec and sec != '综合':
                sectors.add(sec)

        if sectors:
            top_sectors = list(sectors)[:3]
            sector_desc = f"重点布局{'、'.join(top_sectors)}行业"

        # 股票池
        stock_pool = []
        for h in holdings[:20]:
            stock_pool.append(h.get('stock_name', ''))
        stock_pool = list(set(stock_pool))  # 去重

        # 产品阶段
        stage = determine_stage(tenure_days)

        stage_desc_map = {
            '萌芽期': '基金成立不久，正处于建仓期运作，需要时间验证投资策略。',
            '成长期': '基金已度过建仓期，开始展现投资特色，业绩弹性较大。',
            '成熟期': '基金运作成熟，风格稳定，业绩归因清晰。',
            '老牌期': '老牌基金，历经多次市场周期，风格非常稳定。',
        }

        # 优势
        strengths = []
        if tenure_days > 365 * 5:
            strengths.append(f"任职{tenure_days//365}年，经验丰富")
        if stock_pool:
            strengths.append(f"持仓{len(stock_pool)}只股票，研究覆盖面广")
        if style == '成长型':
            strengths.append("擅长挖掘成长赛道机会")
        elif style == '价值型':
            strengths.append("注重估值安全边际，回撤控制好")

        record = {
            'manager_id': m.get('manager_id', ''),
            'name': m.get('name', ''),
            'company_name': m.get('company_name', ''),
            'current_fund_code': fund_code,
            'current_fund_name': fund_name,
            'tenure_days': tenure_days,
            'tenure_years': round(tenure_days / 365, 1),
            'total_scale': m.get('total_scale', ''),
            'best_return': m.get('best_return', ''),
            'investment_style': style,
            'sectors': list(sectors),
            'sector_description': sector_desc,
            'stock_pool': stock_pool,
            'bond_pool': [],
            'fund_pool': [],
            'fund_stage': stage,
            'stage_description': stage_desc_map.get(stage, ''),
            'investment_advice': random.choice(INVESTMENT_ADVICE.get(style, INVESTMENT_ADVICE['均衡型'])),
            'risk_warning': RISK_WARNINGS.get(style, RISK_WARNINGS['均衡型']),
            'suitable_investors': SUITABLE_INVESTORS.get(style, SUITABLE_INVESTORS['均衡型']),
            'investment_period': '3-5年' if style == '成长型' else ('2-3年' if style == '价值型' else '2-5年'),
            'strengths': '; '.join(strengths) if strengths else '专业背景扎实',
            'infrastructure_investment': False,
        }
        distilled.append(record)

    # 统计
    style_counts = Counter(r['investment_style'] for r in distilled)
    print(f"  共蒸馏 {len(distilled)} 位经理")
    print(f"  风格分布: {dict(style_counts)}")
    print(f"  有持仓数据的: {sum(1 for r in distilled if r['stock_pool'])} 位")

    # 保存为列式压缩格式
    columns = [
        'manager_id', 'name', 'company_name', 'current_fund_code', 'current_fund_name',
        'tenure_days', 'tenure_years', 'total_scale', 'best_return',
        'investment_style', 'sectors', 'sector_description',
        'stock_pool', 'bond_pool', 'fund_pool',
        'fund_stage', 'stage_description',
        'investment_advice', 'risk_warning', 'suitable_investors',
        'investment_period', 'strengths', 'infrastructure_investment',
        'raw_id', 'last_updated'
    ]
    rows = []
    for r in distilled:
        rows.append([
            r['manager_id'], r['name'], r['company_name'],
            r['current_fund_code'], r['current_fund_name'],
            r['tenure_days'], r['tenure_years'], r['total_scale'], r['best_return'],
            r['investment_style'], json.dumps(r['sectors'], ensure_ascii=False),
            r['sector_description'],
            json.dumps(r['stock_pool'], ensure_ascii=False),
            json.dumps(r['bond_pool'], ensure_ascii=False),
            json.dumps(r['fund_pool'], ensure_ascii=False),
            r['fund_stage'], r['stage_description'],
            r['investment_advice'], r['risk_warning'], r['suitable_investors'],
            r['investment_period'], r['strengths'],
            r['infrastructure_investment'],
            r['manager_id'], datetime.now().strftime('%Y-%m-%d'),
        ])

    compressed = {
        '_f': 'c',
        'c': columns,
        'd': rows,
        'm': {
            'total_count': len(distilled),
            'last_update': datetime.now().strftime('%Y-%m-%d'),
            'source': '天天基金 + 本地蒸馏',
            'style_distribution': dict(style_counts),
        }
    }
    path, size = save_json(compressed, 'fund_managers_distilled.json', compress=True)
    print(f"  蒸馏数据已保存: {path} ({size:.0f} KB)")
    return distilled


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  天天基金全量数据刷新")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 第1步：基金经理
    managers = fetch_all_managers()
    if not managers:
        print("[ERROR] 基金经理数据获取失败，终止。")
        return

    # 第2步：基金产品
    products = fetch_all_products()

    # 第2.5步（v10.0）：产品档案增强（投资目标/范围/费率/业绩序列）
    # 默认取经理现任基金中的前 500 只（控制总耗时），可经环境变量调整：
    #   FUND_ADVISOR_PROFILE_LIMIT=2000  或 =0 表示不增强（仅目录）
    profile_limit = os.environ.get('FUND_ADVISOR_PROFILE_LIMIT', '500')
    if str(profile_limit).strip() != '0':
        try:
            from fund_profile_collector import FundProfileCollector
            print("\n" + "=" * 60)
            print("  第2.5步：产品档案增强（投资目标/范围/费率/业绩）")
            print("=" * 60)
            mgr_codes = sorted({str(m.get('current_fund_code', '')).zfill(6)
                                for m in managers
                                if str(m.get('current_fund_code', '')).isdigit()})
            limit = int(str(profile_limit).strip()) or 500
            target_products = [{'code': c, 'name': '', 'type': '', 'pinyin': ''}
                               for c in mgr_codes[:limit]]
            collector = FundProfileCollector()
            enriched = collector.enrich_products(target_products)
            if enriched:
                from db_format import write_products
                write_products(DATA_PATH / 'fund_products.json', enriched, meta={
                    'type': 'products',
                    'updated': datetime.now().strftime('%Y-%m-%d'),
                    'source': '天天基金 fundcode_search.js + fundf10 档案',
                    'count': len(enriched),
                    'profile_enriched': len(enriched),
                })
                products = enriched
                print(f"  产品档案增强完成: {len(enriched)} 只")
            else:
                print("  [WARN] 产品档案增强失败（网络/解析），保留基础目录")
        except Exception as e:
            print(f"  [WARN] 产品档案增强跳过: {e}")

    # 第3步：基金公司
    companies = build_companies(managers)

    # 第4步：十大重仓（采集所有经理，耗时较长）
    # 默认限制采集数量以控制耗时，可改为 None 采集全部
    holdings_limit = None  # 设为 None 采集全部，或设数字限制
    # v6.0 修复: fetch_all_holdings 签名是 max_funds= 而非 max_managers=
    holdings = fetch_all_holdings(managers, max_funds=holdings_limit, delay=0.3)

    # 第5步：蒸馏基金经理
    distilled = distill_managers(managers, holdings)

    # 更新数据新鲜度
    freshness = {
        'fund_managers_distilled.json': {
            'count': len(distilled), 'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'ok', 'source': '天天基金实时采集'
        },
        'fund_companies_distilled.json': {
            'count': len(companies), 'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'ok', 'source': '从经理数据聚合'
        },
        'fund_products.json': {
            'count': len(products), 'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'ok', 'source': '天天基金 fundcode_search.js'
        },
        'holdings_database.json': {
            'count': len(holdings), 'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'ok', 'source': '天天基金持仓页面'
        },
        'manager_views.json': {
            'count': 0, 'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'ok',
            'source': '可另跑 view_collector.py 采集季报观点（需 requests/PyPDF2）'
        },
        'manager_news.json': {
            'count': 0, 'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'ok',
            'source': '可另跑 manager_news_collector.py 采集经理新闻/采访'
        },
    }
    save_json(freshness, 'data_freshness.json')

    # v10.0: 持仓季度快照归档（跟仓历史基线，见 holdings_history.py）
    try:
        from holdings_history import archive_current_holdings
        qpath = archive_current_holdings()
        if qpath:
            print(f"  持仓历史快照已归档: {qpath}")
    except Exception as e:
        print(f"  [WARN] 持仓历史归档跳过: {e}")

    # 更新元数据
    update_meta = {
        'update_count': 3,
        'last_update': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'history': [
            {'type': 'full_refresh', 'time': datetime.now().isoformat(),
             'results': {
                 'managers': len(distilled),
                 'companies': len(companies),
                 'products': len(products),
                 'holdings': len(holdings),
             }}
        ]
    }
    save_json(update_meta, 'update_meta.json')

    # 最终报告
    print("\n" + "=" * 60)
    print("  数据刷新完成!")
    print("=" * 60)
    print(f"  基金经理: {len(distilled)} 位")
    print(f"  基金产品: {len(products)} 只")
    print(f"  基金公司: {len(companies)} 家")
    print(f"  十大重仓: {len(holdings)} 只基金")
    print(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == '__main__':
    main()
