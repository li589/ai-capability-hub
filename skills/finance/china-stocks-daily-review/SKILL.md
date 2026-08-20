---
name: china-stocks-daily-review
version: 1.0.0
author: china-stocks-daily-review
description: |
  A股市场行情分析 Skill，支持生成三类报告：盘前市场综述、盘中市场简评、盘后复盘报告。
  【触发词】开盘前分析、盘前综述、早盘预判、今天关注什么、盘中异动、午间复盘、 收盘复盘、今日行情怎么样、市场情绪、板块轮动、主线在哪、今天主线、连板梯队、 涨停分析、北向资金、南向资金、资金动向、成交额、全天行情、A股今日、复盘报告、 今日市场、行情综述、开盘情绪、涨跌停统计、市场概况、明日策略、今日策略。
  【数据架构】三层工具降级体系：Tushare Pro 官方 API（第一优先）→ AKShare 开源库 （第二优先）→ 搜索引擎实时抓取（兜底）。每个数据项独立降级，数据缺失留空不臆想。
  【不适用场景】个股深度分析、宏观政策专项解读、选股推荐、龙虎榜席位分析、期权策略。
install_source: official
install_method: download
skill_id: official_BDVvLhnF
enabled_at: 1787231192317
name_zh: A 股市场行情分析
---

# A股市场行情分析

---

## 适用边界

**使用本技能的情形：**

- 用户询问今日/近期 A 股、港股、美股整体行情或综述
- 涉及市场情绪、风险偏好、板块轮动、热点主题
- 涉及资金动向（北向资金净额、主力净流入、融资融券）
- 涉及涨跌停统计、大宗交易
- 生成开盘前准备材料、盘中快评、收盘复盘报告

**不使用本技能的情形：**

- 聚焦某只具体个股的深度分析
- 聚焦宏观政策、财政货币政策解读
- 要求具体买卖建议或选股推荐
- 龙虎榜席位解读（使用"龙虎榜席位风格"技能）
- 北向资金行为深度分析（使用"北向资金行为"技能）

---

## 取数工具说明

本技能使用三层工具取数，按优先级依次降级：

**数据回退优先级**：

```
工具 A：Tushare Pro 官方 API（用户自有 token，第一优先）
  ├─→ Token 未配置 / 无效 / 网络不通
  │     └─→ 工具 A2：AKShare（免费开源库，第二优先）
  ├─→ 返回空数据 / 今日无数据
  │     └─→ 工具 A2：AKShare
  │           ├─→ 成功：使用 AKShare 数据继续
  │           └─→ 失败 / 空数据
  │                 └─→ 工具 B：搜索引擎（第三优先，兜底）
  ├─→ 接口报错（超时/服务异常）
  │     └─→ 工具 A2：AKShare → 若仍失败 → 工具 B：搜索引擎
  └─→ 接口 40203 权限不足（积分不够）
        ├─→ index_daily 权限不足：改用 daily 拉全市场数据统计上涨/下跌/成交额
        ├─→ limit_list_ths 权限不足：
        │     └─→ 工具 A2：stock_zt_pool_em（有连板数）→ 失败 → 工具 B 搜索连板梯队
        ├─→ moneyflow_hsgt / moneyflow_ind_ths 权限不足：
        │     └─→ 工具 A2 对应接口 → 失败 → 工具 B 搜索
        └─→ 以上所有接口均不可用：全部降级工具 B，以搜索结果为主数据源
```

**核心原则**：每个数据项独立降级，不因某一项失败而放弃整个报告。数据缺失时该项留空，不臆想填充。

---

### 工具 A：Tushare Pro 官方接口（第一优先）

直接调用官方 `http://api.tushare.pro` 接口，需用户自己的 token。

---

#### 📋 首次使用：Token 配置向导

**每次运行前先执行以下检查脚本**，若 token 未配置或无效则引导用户注册：

```python
import urllib.request, json, os, re
from collections import Counter
from pathlib import Path

# ── Step 1：读取 Token ────────────────────────────────────────
TOKEN_FILE = Path.home() / '.tushare_token'   # 存储路径：~/. tushare_token

def load_token():
    """从本地文件读取 token，未配置返回 None"""
    if TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text(encoding='utf-8').strip()
        return t if t else None
    return None

def save_token(token: str):
    TOKEN_FILE.write_text(token.strip(), encoding='utf-8')
    print(f'✅ Token 已保存至 {TOKEN_FILE}')

# ── Step 2：网络连通性检查 ────────────────────────────────────
def check_network() -> bool:
    """检查能否访问 Tushare API 服务器"""
    try:
        urllib.request.urlopen('http://api.tushare.pro', timeout=5)
        return True
    except Exception as e:
        err = str(e)
        if '400' in err or '403' in err or '401' in err:
            return True   # 服务器可达（拒绝是正常响应）
        return False

# ── Step 3：Token 有效性验证 ──────────────────────────────────
def verify_token(token: str) -> tuple[bool, str]:
    """
    用 daily 接口（积分要求最低）验证 token 是否有效。
    注意：不用 trade_cal，该接口同样需要积分，低积分账号会返回 40203 误判为无效。
    返回 (is_valid, message)
    """
    try:
        body = json.dumps({
            'api_name': 'daily',
            'token': token,
            'params': {'ts_code': '000001.SZ', 'start_date': '20240101', 'end_date': '20240103'},
            'fields': 'trade_date,close'
        }).encode()
        req = urllib.request.Request(
            'http://api.tushare.pro',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        code = result.get('code', -1)
        msg  = result.get('msg', '')
        if code == 0:
            return True, 'Token 验证通过'
        elif 'token' in msg.lower() or 'auth' in msg.lower() or code in (-1001, -2001):
            return False, f'Token 无效：{msg}'
        else:
            # 40203 等积分不足：说明 token 本身有效，只是部分接口受限，继续使用
            return True, f'Token 有效（积分受限，仅部分接口可用，msg={msg}）'
    except Exception as e:
        return False, f'网络请求失败：{e}'

# ── Step 4：启动检查入口 ──────────────────────────────────────
def startup_check() -> str | None:
    """
    执行网络 + token 完整检查。
    返回有效 token；若无法获取，返回 None（触发降级至工具 A2/B）。
    """
    # 4-1 网络检查
    if not check_network():
        print('⚠️  无法连接 Tushare 服务器（api.tushare.pro）')
        print('    请检查网络连接，或确认防火墙未拦截该域名。')
        print('    → 自动降级至 AKShare（工具 A2）')
        return None

    # 4-2 读取已保存的 token
    token = load_token()

    if token is None:
        # 首次使用，引导注册
        print('=' * 50)
        print('🔑 未检测到 Tushare Token，需要完成以下配置：')
        print()
        print('  第一步：免费注册 Tushare Pro 账号')
        print('    👉 注册地址：https://tushare.pro/register?reg=666')
        print('    （注册后即获赠基础积分，无需付费）')
        print()
        print('  第二步：登录后获取 Token')
        print('    👉 Token 页面：https://tushare.pro/user/token')
        print()
        print('  第三步：将 Token 粘贴到下方并回车：')
        print('=' * 50)
        # 非交互式环境下直接降级
        print('⚠️  当前为自动化运行环境，无法交互输入 Token。')
        print('    请先在终端运行以下命令保存 Token，再重新执行报告生成：')
        print()
        print("    python -c \"from pathlib import Path; Path.home().joinpath('.tushare_token').write_text('YOUR_TOKEN_HERE')\"")
        print()
        print('    → 本次自动降级至 AKShare（工具 A2）')
        return None

    # 4-3 验证 token 有效性
    valid, msg = verify_token(token)
    if not valid:
        print(f'⚠️  Token 验证失败：{msg}')
        print(f'    Token 文件位置：{TOKEN_FILE}')
        print('    请检查 Token 是否正确，或前往 https://tushare.pro/user/token 重新获取。')
        print('    → 自动降级至 AKShare（工具 A2）')
        return None

    print(f'✅ Tushare Pro 连接正常（{msg}）')
    return token

# ── Step 5：正式调用封装 ──────────────────────────────────────
TOKEN = startup_check()   # 每次脚本开头执行，获取有效 token

def fetch(api_name: str, params: dict, fields: str = '') -> dict | None:
    """
    调用 Tushare Pro 官方接口。
    成功返回 {'fields':[...], 'items':[[...]]}；失败/空数据返回 None（触发降级）。
    """
    if not TOKEN:
        return None   # token 不可用，直接跳过，让调用方降级
    try:
        body = json.dumps({
            'api_name': api_name,
            'token': TOKEN,
            'params': params,
            'fields': fields
        }).encode()
        req = urllib.request.Request(
            'http://api.tushare.pro',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
        if result.get('code') == 0 and result.get('data', {}).get('items'):
            return result['data']   # {'fields':[...], 'items':[[...]]}
        return None   # 空数据或错误，触发降级
    except Exception:
        return None   # 任何异常触发降级

# 使用示例：
# data = fetch('index_daily', {'ts_code': '000001.SH', 'trade_date': '20260325'})
# if data:
#     item = dict(zip(data['fields'], data['items'][0]))
# else:
#     # → 降级至工具 A2（AKShare）
```

> **Token 安全说明**：token 仅存储在本地 `~/.tushare_token` 文件中，不上传至任何云端，不写入 SKILL.md 或代码仓库。

**核心接口速查（已实测有效，fetch() 返回 data dict 或 None）：**

```python
from datetime import datetime
trade_date = datetime.now().strftime('%Y%m%d')   # 动态当日日期，如 '20260325'
```

#### 1. 指数日线 `index_daily`

```python
# ⚠️ ts_code 必须逐个查询，不支持逗号分隔多个
index_results = {}
for code, label in [('000001.SH','上证'),('399001.SZ','深证'),
                    ('399006.SZ','创业板'),('000688.SH','科创50')]:
    data = fetch('index_daily', {'ts_code': code, 'trade_date': trade_date})
    if data:
        item = dict(zip(data['fields'], data['items'][0]))
        # 字段：ts_code, trade_date, close, open, high, low, pre_close,
        #        change, pct_chg, vol, amount
        # ⚠️ vol 单位为手；amount 单位为千元，转亿元需 /1e5
        index_results[label] = {
            'close': item['close'],
            'pct':   item['pct_chg'],       # 百分比数值，如 1.78
            'vol':   item['vol'],            # 成交量（手）
            'amt':   item['amount'] / 1e5   # 成交额（亿元）
        }
    # else: → 降级至工具 A2
```

#### 2. 涨跌停池 `limit_list_ths`

```python
data = fetch('limit_list_ths', {'trade_date': trade_date})
if data:
    items = data['items']
    # 字段（按索引）：
    # [0]trade_date [1]ts_code [2]name [3]price [4]pct_chg [5]open_num
    # [6]lu_desc(题材) [7]limit_type(涨停池/跌停池) [8]tag(连板描述)
    # [9]status(换手板/一字板) [10]limit_order [11]limit_amount
    # [12]turnover_rate [13]free_float [14]lu_limit_order(无效,全为None)
    # [15]limit_up_suc_rate [16]turnover [17]market_type

    zt = [x for x in items if '涨停' in str(x[7])]  # 涨停池
    dt = [x for x in items if '跌停' in str(x[7])]  # 跌停池

    # ⚠️ 连板天数：从 tag 字段（index 8）解析，lu_limit_order(index 14)全为None不可用
    # tag 格式示例：'首板', '2天2板', '5天3板', '10天9板'
    def parse_lianban(tag):
        m = re.search(r'(\d+)天(\d+)板', str(tag))
        return int(m.group(2)) if m else 1

    results = [(x[2], parse_lianban(x[8]), x[8], x[6], x[9]) for x in zt]
    # (名称, 连板天数, tag原文, 题材描述, 状态)
    results.sort(key=lambda x: -x[1])
    lianban_2plus = [r for r in results if r[1] >= 2]

    # 题材热度统计（涨停题材出现频次）
    tags_all = []
    for x in zt:
        if x[6]: tags_all.extend(str(x[6]).replace('，','+').split('+'))
    tag_cnt = Counter(tags_all).most_common(10)
# else: → 降级至工具 A2
```

#### 3. 北向资金 `moneyflow_hsgt`

```python
data = fetch('moneyflow_hsgt', {'trade_date': trade_date})
if data:
    item = dict(zip(data['fields'], data['items'][0]))
    # 字段：trade_date, ggt_ss(沪股通净流入,亿), ggt_sz(深股通净流入,亿),
    #        hgt, sgt, north_money(北上合计,亿), south_money(南下合计,亿)
    # ⚠️ north_money 单位已是亿元，直接用
    north = item['north_money']   # 北上净流入（亿元，正=流入，负=流出）
    sh    = item['ggt_ss']        # 沪股通
    sz    = item['ggt_sz']        # 深股通
# else: → 降级至工具 A2
```

#### 4. 板块资金流 + 涨幅 `moneyflow_ind_ths`

```python
data = fetch('moneyflow_ind_ths', {'trade_date': trade_date})
if data:
    items  = data['items']
    fields = data['fields']
    # 字段：trade_date, ts_code, industry, lead_stock(龙头股),
    #        close, pct_change(涨跌幅%), company_num, pct_change_stock,
    #        close_price, net_buy_amount, net_sell_amount, net_amount(净流入,元)

    # ⚠️ 按涨幅排序（不是按资金流）
    pct_idx  = fields.index('pct_change')
    name_idx = fields.index('industry')
    net_idx  = fields.index('net_amount')

    sorted_by_pct = sorted(items, key=lambda x: (x[pct_idx] or 0), reverse=True)
    top5_up   = sorted_by_pct[:5]    # 领涨 TOP5
    top5_down = sorted_by_pct[-5:]   # 领跌 TOP5（或涨幅最小）
# else: → 降级至工具 A2
```

#### 5. 大宗交易 `block_trade`

```python
data = fetch('block_trade', {'trade_date': trade_date})
if data:
    count = len(data['items'])
    # 字段：ts_code, price, vol, amount, buyer, seller, ...
    # 统计笔数即可
# else: → 搜索引擎补充（工具 B）
```

---

### 工具 A2：AKShare 结构化数据（第二优先，Tushare 失败时降级）

当工具 A 返回空数据或报错时，立即尝试 AKShare 获取同类数据。AKShare 为免费开源 Python 库，数据实时性略低于 Tushare，但覆盖范围全。

**环境要求**：`pip install akshare`（已安装则直接 import）

**核心接口对照（与工具 A 一一对应）：**

```python
import akshare as ak
from datetime import datetime, timedelta

today = datetime.now().strftime("%Y%m%d")         # 20260325
today_dash = datetime.now().strftime("%Y-%m-%d")  # 2026-03-25
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

# ── A2-1. 指数行情（替代 index_daily）──────────────────────
df_idx = ak.stock_zh_index_spot_em()
# 过滤所需指数
idx_map = {'上证综指':'000001','深证成指':'399001','创业板指':'399006','科创50':'000688'}
for name, code in idx_map.items():
    row = df_idx[df_idx['代码'] == code]
    if not row.empty:
        close = row['最新价'].values[0]
        pct   = row['涨跌幅'].values[0]     # 已是百分比，如 1.78
        amt   = row['成交额'].values[0]      # 单位：元，转亿需 /1e8
        vol   = row['成交量'].values[0]      # 单位：手

# ── A2-2. 涨跌停统计（替代 limit_list_ths）────────────────
df_zt  = ak.stock_zt_pool_em(date=today)         # 涨停池（含连板数字段）
df_dt  = ak.stock_zt_pool_dtgc_em(date=today)    # 跌停池
df_zb  = ak.stock_zt_pool_zbgc_em(date=today)    # 炸板池
# df_zt 含字段：代码, 名称, 涨跌幅, 最新价, 成交额, 流通市值, 总市值,
#               换手率, 封板资金, 首次封板时间, 最后封板时间, 炸板次数,
#               涨停统计, 所属行业, 连板数
# ⚠️ 连板天数：直接读 df_zt['连板数'] 列，无需额外解析

# ── A2-3. 北向资金（替代 moneyflow_hsgt）──────────────────
# ⚠️ 注意：stock_hsgt_north_net_flow_in_em 已失效，改用下方接口
df_hsgt = ak.stock_hsgt_fund_flow_summary_em()
# 过滤北向（沪港通+深港通），取今日最新行
import datetime
today_str = datetime.date.today().strftime('%Y-%m-%d')
df_north = df_hsgt[df_hsgt['交易时间'] == today_str]
# ⚠️ "资金净流入"字段收盘当日可能为0（结算滞后），建议用次日数据或搜索引擎补充

# ── A2-4. 行业板块涨跌（替代 moneyflow_ind_ths）───────────
df_ind = ak.stock_sector_fund_flow_rank(symbol="今日", indicator="行业资金流向")
# 含字段：序号, 名称, 今日涨跌幅, 今日主力净流入-净额, 今日主力净流入-净占比 ...
# ⚠️ 按"今日涨跌幅"排序（不是按资金流）
df_ind_sorted = df_ind.sort_values('今日涨跌幅', ascending=False)
top5_up   = df_ind_sorted.head(5)
top5_down = df_ind_sorted.tail(5)

# ── A2-5. 大宗交易（替代 block_trade）─────────────────────
df_blk = ak.stock_dzjy_mrmx(type_="买入", date=today)
count = len(df_blk)

# ── A2-6. 指数历史数据（BaoStock 备用，仅在 AKShare 也失败时）
# import baostock as bs
# lg = bs.login()
# rs = bs.query_history_k_data_plus("sh.000001",
#     "date,close,pctChg,volume,amount",
#     start_date=today_dash, end_date=today_dash,
#     frequency="d", adjustflag="3")
# df_bs = rs.get_data()
# bs.logout()
# ⚠️ BaoStock: volume 单位为股（÷100=手），amount 单位为元（÷1e8=亿）
```

**工具 A2 注意事项：**
- `stock_zh_index_spot_em` 的成交额单位为**元**，转亿元需 `/1e8`（不同于 Tushare 的千元/1e5）
- `stock_zt_pool_em` 的连板天数直接读 `连板数` 列，无需解析字符串
- AKShare 行业板块排名用 `今日涨跌幅` 字段排序
- 若 AKShare 也抛异常，直接进入工具 B（搜索引擎）

---

### 工具 A2-新闻：财联社快讯（新增信息源）

**接口**：`ak.stock_info_global_cls(symbol='全部')`

- 返回最新 20 条财联社快讯，字段：`标题`（通常为空）、`内容`（实际内容在此）、`发布日期`（`datetime.date` 对象）、`发布时间`
- 用途：盘前关注事件、盘中热点催化、盘后收盘原因分析
- ⚠️ 注意：`标题` 列经常为空，内容全在 `内容` 字段；过滤今日数据需比较 `datetime.date` 对象，不能用字符串

```python
import akshare as ak
import datetime

df_cls = ak.stock_info_global_cls(symbol='全部')
today = datetime.date.today()
df_today = df_cls[df_cls['发布日期'] == today]
# 按时间倒序，取内容非空的条目
news_items = []
for _, row in df_today.iterrows():
    content = str(row.get('内容', ''))
    if content and content != 'nan':
        news_items.append(f"[{row['发布时间']}] {content}")
# news_items 即为今日财联社快讯列表
```

**在报告中的用途：**
- 盘前：补充「今日关注」板块的重大事件（政策、外盘、公司公告）
- 盘中：解释板块异动催化剂
- 盘后：补充收盘后的快讯（业绩预告、政策落地等）

---

### 工具 A2-新闻：Tushare 新闻快讯（补充，积分依赖）

**接口**：`news`（需要 Tushare 积分）

- 参数：`src`（新闻来源：`sina`/`wallstreetcn`/`eastmoney`/`yuncaijing`/`finet`/`10jqka`）
- 字段：`datetime`、`title`、`content`、`channels`
- 当前账号积分限制：接口返回 0 条（积分不足）→ 降级至财联社快讯或搜索引擎

---

### 工具 B：搜索引擎实时数据抓取（第三优先，兜底）

**触发条件（满足任一即启用）：**
1. 工具 A（Tushare）+ 工具 A2（AKShare）均返回空或报错
2. 需要补充当日重要新闻、政策背景（财联社快讯不够详细时）
3. 需要对板块异动/个股事件给出**原因解读**（工具 A/A2 均无原因字段）

**搜索数据可替代范围**：
- 实时指数点位、涨跌幅
- 实时成交额（近似值）
- 实时涨停/跌停家数
- 实时北向资金流向
- 板块涨幅排名
- 市场热点与异动原因

**搜索引擎分工（按场景选 1-2 个，避免冗余）：**

| 优先级 | 场景 | 引擎 | URL 模板 |
|-------|-----|-----|---------|
| 1 | A股当日资讯、复盘 | Bing CN | `https://cn.bing.com/search?q={关键词}&ensearch=0&tbs=qdr:d` |
| 2 | 市场热点/板块异动原因 | 东方财富 | `https://so.eastmoney.com/web/s?keyword={关键词}` |
| 3 | 市场情绪/热搜事件 | 腾讯财经 | `https://new.qq.com/search?query={关键词}` |
| 4 | 盘后个股/板块复盘 | 新浪财经 | `https://search.sina.com.cn/?q={关键词}&range=all&c=news` |
| 5 | 同花顺资讯 | 同花顺 | `https://news.10jqka.com.cn/search/?key={关键词}` |
| 6 | 港股/美股/隔夜外盘 | Bing INT | `https://cn.bing.com/search?q={关键词}&ensearch=1&tbs=qdr:d` |
| 7 | 可转债/套利 | 集思录 | `https://www.jisilu.cn/explore/?keyword={关键词}` |
| 8 | 备用 | DuckDuckGo | `https://duckduckgo.com/html/?q={关键词}` |

**BaoStock 冗余说明：**

BaoStock 为免费 Python 库（`import baostock as bs`），可作为指数历史数据的备用源。若 Tushare 指数日线数据为空，可尝试：

```python
import baostock as bs, pandas as pd
lg = bs.login()
rs = bs.query_history_k_data_plus("sh.000001",
    "date,close,pctChg,volume,amount",
    start_date="2026-03-24", end_date="2026-03-24",
    frequency="d", adjustflag="3")
df = rs.get_data()
bs.logout()
# 注意：volume 单位为股，amount 单位为元
```

**标准搜索关键词（增强版）：**

| 报告类型 | 关键数据 | 搜索关键词 |
|---------|---------|-----------|
| **盘中实时数据** | 指数点位/涨跌幅 | `上证指数 实时 点位` `创业板指 涨跌幅` |
| **盘中实时数据** | 成交额 | `A股 成交额 今日` |
| **盘中实时数据** | 涨停/跌停家数 | `涨停 家数 今日` `跌停 家数` |
| **盘中实时数据** | 北向资金 | `北向资金 实时 净流入` |
| **盘中实时数据** | 板块涨幅 | `今日板块涨幅排名` |
| 盘前综述 | 隔夜外盘 | `美股 隔夜 收盘 {日期}` |
| 盘前综述 | 今日关注 | `A股 盘前 今日关注 {日期}` |
| 盘中热点 | 异动原因 | `A股 盘中 异动 热点 {日期}` |
| 盘后复盘 | 板块表现 | `A股 今日复盘 板块 {日期}` |

**调用原则：**
- **优先结构化数据**：工具 A / A2 能拿到的数字类数据，不用搜索引擎
- **搜索补充原因**：板块异动原因、事件背景、政策解读，必须走工具 B
- **不限制引擎数量**：为获取完整实时数据，可同时调用 2-3 个引擎
- **数据冲突处理**：数字以工具 A/A2 为准，原因分析以搜索为准

---

## 报告生成：三层漏斗模型

复盘报告的生成过程由三层架构驱动，每层有明确的输入、处理逻辑和输出产物。三层顺序执行，上层输出是下层输入。

---

### 第一层：数据获取层

**原则**：优先权威结构化数据，辅以非结构化资讯。数据按重要性分四级顺序获取：

优先级 1（核心，必须完整）
指数收盘价、涨跌幅、成交额、成交量、涨跌家数、涨停/跌停统计、南北向资金净流入/流出。
来源：工具 A（Tushare）→ 工具 A2（AKShare）→ 工具 B（搜索）。

优先级 2（重要，尽力获取）
板块异动原因、宏观政策、公司公告、机构观点。
来源：财联社快讯（stock_info_global_cls）→ 工具 B（东方财富/Bing CN）。

优先级 3（辅助，选择性获取）
市场情绪指标、热点事件（如"算力爆发"、词元概念）。
来源：涨停池聚类结果、财联社快讯、Bing CN 搜索。

优先级 4（补充，时间允许时获取）
海外市场信息、实时滚动新闻。
来源：Bing INT（港股/美股/外盘）。

---

### 第二层：逻辑清洗与筛选层

**原则**：从海量数据中提炼"信号"，过滤"噪音"。按以下 5 步执行：

Step 1 异常值剔除
剔除 ST 股、停牌股、数据异常值（如成交量=0的涨停，标记为"无效涨停"，不计入连板梯队）。

Step 2 主线识别（聚类分析）
将涨停股按所属板块归类，统计涨停家数最多的前 3 个板块，作为今日主线排序依据。
输出格式：主线1（N家涨停）> 主线2（N家）> 主线3（N家）。

Step 3 资金归因（关联分析）
将资金净流入最大的板块，与财联社快讯/搜索结果中的政策事件关联，给出驱动因子归类：
政策催化 / 业绩催化 / 资金追涨 / 外部联动 / 情绪扩散。

Step 4 情绪量化
计算以下指标并给出评级：
涨跌比 = 上涨家数 / 下跌家数（>3 为偏热，>5 为亢奋）
连板高度 = 当日最高连板数（>=6板 为亢奋信号）
炸板率 = 炸板数 / (涨停+炸板) × 100%（>20% 为情绪转弱信号）
情绪评级：亢奋 / 偏热 / 正常 / 偏冷 / 低迷。

Step 5 风险识别（反向排除）
找出跌幅榜前 3 板块、跌停家数突增板块，标记"风险警示"写入风险提示区。

---

### 第三层：结构化叙事层

**原则**：将清洗后的数据转化为可阅读的叙事，遵循"结论先行 + 数据支撑 + 逻辑推演"框架。

三类报告的核心差异：
- 盘前报告：预测与推演（基于隔夜数据 + 公告 + 预期）。核心是"今天要盯着什么看"。核心逻辑：外盘映射 → 超预期事件筛选 → 关键点位技术研判 → 剧本推演（高开/低开应对策略）
- 盘中报告：验证与修正（基于上午实际走势）。核心是"昨天的预测准不准？主线变没变？"核心逻辑：预判对比验证 → 主线延续性判断（是否电风扇？）→ 情绪周期位置 → 下午策略修正
- 盘后报告：复盘与总结（基于全天完整数据）。核心是"今日发生了什么、为什么、明天怎么看"。核心逻辑：主线聚类 → 驱动因子归因 → 情绪评级 → 策略展望

报告结构（盘前版，硬编码）：
标题行 — 核心主题（一句话概括今日关注方向）
隔夜外盘映射 — 美股/中概/A50期指/汇率 + 开盘情绪预判
核心消息面 — 政策利好/个股公告/风险预警（超预期事件优先，剔除已消化利好）
技术面关键点位 — 支撑/压力位 + 量能要求
今日策略 — 最强主线预判 + 风向标标的 + 风控预案（高开/低开/放量 三种剧本）

报告结构（盘中版，硬编码）：
标题行 — 一句话总结上午走势
上午数据 — 指数/成交额/涨跌比（与盘前预期对比：符合/超预期/不及）
主线验证 — 领涨板块 + 主线延续性判断（有无电风扇切换）
连板情绪 — 最高连板高度变化（与昨日/上午对比）+ 炸板率
下午推演 — 强弱判断 + 进攻/风险预警 + 核心观察点

报告结构（盘后版，硬编码）：
标题行 — 核心结论（如"算力爆发 + 电力共振"），一句话定性今日行情
指数表现 — 收盘价、涨跌幅、成交额逐行列出
资金动向 — 北向/南向净流入规模+方向
主线复盘 — 按主线强度排序，每条主线：龙头股 + 涨停家数 + 驱动因子
情绪指标 — 连板高度、涨停/跌停家数、炸板率、情绪评级
明日策略 — 进攻方向 + 防守方向 + 关键观察点
小结 — 一句话总结 + 风险提示

---

## 第一步：识别报告类型

根据用户输入判断报告类型，若未明确指定则依当前时间自动判断：

| 报告类型 | 触发词 | 自动判断时间 |
|---------|-------|------------|
| **盘前市场综述** | 开盘前、盘前、早盘预判、今天关注什么 | 8:00–9:25 |
| **盘中市场简评** | 盘中、现在市场、午盘、异动 | 9:30–15:00 |
| **盘后复盘报告** | 收盘、今日复盘、盘后、今天表现 | 15:00 后 |

---

## 第二步：取数执行

### 盘前取数清单

优先级顺序：优先级1（核心）→ 优先级2（消息面）→ 优先级3（情绪辅助）→ 优先级4（外盘补充）

| 优先级 | 数据项 | 工具 A（Tushare） | 工具 A2（AKShare降级） | 工具 B（搜索兜底） |
|-------|-------|----------------|---------------------|-----------------|
| P1 | 昨日主要指数收盘 | `index_daily`（逐个查） | `stock_zh_index_spot_em` | Bing CN |
| P1 | 昨日涨跌停数量+连板 | `limit_list_ths` | `stock_zt_pool_em` / `dtgc` / `zbgc` | 搜索"涨停家数" |
| P1 | 昨日北向/南向资金 | `moneyflow_hsgt` | `stock_hsgt_fund_flow_summary_em` | 搜索"北向资金" |
| P2 | 晚间公告/政策/事件（超预期优先） | — | `stock_info_global_cls`（财联社快讯，今晚条目） | Bing CN · 东方财富 |
| P2 | 重大个股公告（业绩/重组/减持/解禁） | — | — | Bing CN 搜索"股票公告 今晚" |
| P3 | 昨日主线情绪延续性（连板高度变化） | `limit_list_ths` | `stock_zt_pool_em` | — |
| P4 | 隔夜美股三大指数、中概股 | — | — | Bing INT |
| P4 | A50期指、人民币汇率 | — | — | Bing INT · Bing CN |

取数重点说明：
- P2 消息面筛选原则：只选"超预期"事件，剔除已消化的利好（如反复提及的政策、已发布多日的公告）
- P4 隔夜外盘：时间允许时获取；若无则盘前报告外盘部分用"数据暂缺"标注，不臆想

### 盘中取数清单

优先级顺序与盘前相同，但数据均来自实时当日；额外增加"预判验证"维度

| 优先级 | 数据项 | 工具 A（Tushare） | 工具 A2（AKShare降级） | 工具 B（搜索兜底） |
|-------|-------|----------------|---------------------|-----------------|
| P1 | 当前指数实时涨跌+成交额 | `index_daily`（今日） | `stock_zh_index_spot_em` | 搜索"上证指数 实时" |
| P1 | 实时涨跌停数量+炸板 | `limit_list_ths`（今日） | `stock_zt_pool_em` / `zbgc` | 搜索"今日涨停家数" |
| P1 | 上涨/下跌家数（涨跌比计算） | `daily`（全市场统计） | — | 搜索"今日涨跌家数" |
| P1 | 实时北向/南向资金 | `moneyflow_hsgt`（今日） | `stock_hsgt_fund_flow_summary_em` | 搜索"北向资金 实时" |
| P2 | 行业板块涨幅 TOP5 + 领跌 | `moneyflow_ind_ths`（今日） | `stock_sector_fund_flow_rank(sector_type='行业资金流')` | 搜索"今日板块涨幅" |
| P2 | 盘中快讯/异动催化原因 | `news`（积分受限时降级） | `stock_info_global_cls`（财联社快讯） | 东方财富 / Bing CN |
| P3 | 连板高度变化（与上午/昨日对比） | `limit_list_ths` | `stock_zt_pool_em` | — |

### 盘后取数清单

| 数据项 | 工具 A（Tushare） | 工具 A2（AKShare降级） | 工具 B（搜索兜底） | 字段说明 |
|-------|----------------|---------------------|-----------------|---------|
| 今日各指数收盘 | `index_daily`（逐个查） | `stock_zh_index_spot_em` | Bing CN | A: amount/1e5=亿；A2: 成交额/1e8=亿 |
| 今日涨跌停/炸板/连板 | `limit_list_ths` → 失败用`daily`统计涨停家数（无连板） | `stock_zt_pool_em` 等（含连板数列） | 搜索"涨停家数 连板梯队" | A: tag解析连板；A2: 连板数列直接读；daily降级：只有涨停家数，无连板明细 |
| 今日北向/南向资金 | `moneyflow_hsgt` | `stock_hsgt_fund_flow_summary_em`（北向+南向） | 搜索"北向资金" | 使用 `成交净买额` 字段（亿元）；`资金净流入` 为额度余额不可用；北向收盘当日结算滞后显示0则不写 |
| 行业板块涨跌幅 | `moneyflow_ind_ths` | `stock_sector_fund_flow_rank(sector_type='行业资金流')` | 搜索"板块涨跌" | 均按涨幅排序，不按资金流 |
| 大宗交易笔数 | `block_trade` | `stock_dzjy_mrmx` | — | 统计条数即可 |
| 收盘后快讯/公告 | `news`（积分受限时降级） | `stock_info_global_cls`（财联社快讯，15:00后条目） | 东方财富 / Bing CN | 用于补充收盘后重大公告、业绩快报 |
| 板块异动原因 | — | `stock_info_global_cls`（财联社快讯中搜关键词） | 东方财富 / Bing CN | 工具A/A2均无原因字段，优先快讯再搜索 |

---

## 第三步：撰写报告

### 成交量与成交额区分说明（报告写作规范）

> - **成交量**（手/股）：反映成交频次，与股价无关，同一资金规模下高价股成交量小
> - **成交额**（亿元）：= 成交量 × 价格，反映实际资金流动规模，是市场活跃度的核心指标
> - 报告中需**同时列出**成交量和成交额，不可混用

### 盘前市场综述模板

⚠️ 输出格式要求：为适配微信阅读，禁止使用 Markdown 表格（不出现 | 符号）、# 标题符号、** 加粗符号、- 或 * 列表符号、━ 分隔线。改用 emoji 图标、中文数字标题、空行分段。内容丰富度不减，适当加 emoji 增强可读性。

⚙️ 生成逻辑（三层漏斗盘前版）：第一层取昨日结构化数据（P1）+ 晚间消息面（P2）+ 隔夜外盘（P4）；第二层筛选：只保留"超预期"事件，剔除已消化利好，聚焦今日潜在影响板块；第三层：结论先行（核心主题）→ 外盘映射（开盘情绪定性）→ 昨日盘面回顾 → 消息面催化筛选 → 技术点位 → 剧本推演（高开/低开/放量三种应对方案）。

```
🌅 盘前市场综述 · {日期}（{星期}）
核心主题：{一句话概括今日重点，如"外盘企稳，关注新能源政策催化+昨日连板高度延续"}

🌍 一、隔夜外盘映射

美股三大指数{整体表现，如"集体收涨/收跌/涨跌互现"}：
道琼斯指数：{涨跌幅}%
标普500：{涨跌幅}%
纳斯达克：{涨跌幅}%
中概股（纳斯达克中国金龙指数）：{涨跌幅}%
A50期指：{涨跌幅}%（开盘情绪风向标）
人民币汇率：美元/人民币 {汇率}（较昨日{升/贬值}）

开盘情绪预判：{高开/低开/平开预期}，预计开盘情绪{乐观/谨慎/分化}
逻辑：{1-2句，说明外盘对A股的传导方向，如"中概涨+A50稳 → 科技/成长方向开盘偏强"}

（若外盘数据暂缺则写"隔夜外盘数据暂缺"，不臆想）

📈 二、昨日 A 股回顾

指数收盘：
上证综指：{点位}（{涨跌幅}%），成交额 {X} 亿
深证成指：{点位}（{涨跌幅}%），成交额 {X} 亿
创业板指：{点位}（{涨跌幅}%），成交额 {X} 亿
科创 50：{点位}（{涨跌幅}%），成交额 {X} 亿
沪深两市合计成交额约 {X} 亿元（较前日{增加/减少} {差值} 亿，环比{+/-}{变化幅度}%）

💰 资金动向：
北向资金：{若昨日数据结算滞后则不写；若有数据则写"净流入/流出 X亿（沪股通 X亿 / 深股通 X亿）"}
南向资金：港股通合计净买入 {X} 亿（沪港通 {X} 亿 / 深港通 {X} 亿）

情绪温度计（昨日）：
上涨 {N} 家，下跌 {N} 家（涨跌比 {上涨/下跌，保留1位小数}:1）
涨停 {N} 家 / 跌停 {N} 家 / 炸板 {N} 家（炸板率 {炸板/(涨停+炸板)×100}%）
连板高度：最高 {N} 板（{股票名}）
情绪评级：{亢奋 / 偏热 / 正常 / 偏冷 / 低迷}（{1句定性依据}）

🔥 连板梯队（昨日，2板及以上，按连板数降序，每只独立一行）：

{N}板
{股票名} — {所属行业}（{题材/催化逻辑，1句}）

{N}板
{股票名} — {所属行业}（{题材/催化逻辑，1句}）
{股票名} — {所属行业}（{题材/催化逻辑，1句}）

（2板个股较多时：先列有明确题材逻辑的，最后一行合并列出无突出题材的，格式：{名1}、{名2}、{名3} — {行业}）

🏷️ 涨停题材热度（TOP8，按频次）：
1. {题材} — {N} 家
2. {题材} — {N} 家
（以此类推）

📢 三、核心消息面梳理（仅超预期事件，已消化利好不列）

📌 政策/行业利好
{事件标题}：{简述2-3句，含受益板块+影响方向，如"设备更新新政 → 工业机械/汽车直接受益"}
（若有第二条则同格式列出；若无超预期利好则写"暂无重磅超预期政策"）

📌 个股/公司公告（超预期的）
{股票名/代码}：{事件类型，如"业绩预增300%/重大重组/定增"} — {预期判断：超预期/利空，1句逻辑}
（若无重要公告则省略此段）

⚠️ 风险预警
{风险类型}：{具体说明，如"XX股票今日解禁 X亿，关注抛压"/"某地缘事件影响大宗商品"}
（若无则省略）

📊 四、技术面关键点位

上证综指：压力位 {XXXX}，支撑位 {XXXX}（如昨日收盘价/整数关口/均线）
创业板指：压力位 {XXXX}，支撑位 {XXXX}
量能要求：今日需成交 {X} 亿以上才能支撑{上涨/突破}（依据：近期均量/前高量能）

🎯 五、今日核心策略

最强主线预判：{板块方向，如"AI算力/电力/消费"} — 逻辑：{1-2句，隔夜数据/公告/昨日连板延续}
潜在轮动方向：{如"低位补涨/消费/超跌反弹"，无则省略}

重点观察标的（2-3只，作为板块风向标）：
{股票A}：观察{XX}是否突破{XX}压力位，量能是否配合
{股票B}：观察{XX}是否抗跌，作为板块强弱风向标
{股票C}：观察{XX}是否封板，作为情绪标杆（如有则列）

剧本推演（三种开盘场景）：
若高开且放量：跟随主线，优先中军龙头，情绪偏强可适度参与
若高开但缩量：警惕诱多，避免追高，观望为主
若低开超1%：暂不操作，观察开盘后30分钟是否修复，不修复则规避当日操作

⚠️ 风险提示：{1-2条，具体说明潜在风险}

数据来源：Tushare Pro · AKShare · 财联社快讯 · 财经媒体资讯
```

### 盘中市场简评模板

⚠️ 输出格式要求：为适配微信阅读，禁止使用 Markdown 表格（不出现 | 符号）、# 标题符号、** 加粗符号、- 或 * 列表符号、━ 分隔线。改用 emoji 图标、中文数字标题、空行分段。

⚙️ 生成逻辑（三层漏斗盘中版）：第一层取上午实时数据（P1指数/涨停/资金）+ 板块异动原因（P2）；第二层：ST剔除 → 与盘前预判对比验证（符合/偏差） → 主线延续性判断（是否电风扇快速切换） → 情绪位置（连板高度对比昨日）→ 风险识别（午后跳水迹象）；第三层：结论先行（上午一句话定性）→ 数据支撑（指数/涨停/涨跌比）→ 主线验证 → 下午剧本推演。

```
🕛 午间复盘报告 · {日期}（{星期}）{时间，如11:30}
核心主题：{一句话总结上午走势，如"两市放量上涨，电力板块持续走强，盘前预判基本验证"}

📈 一、上午盘面数据

指数表现：
上证综指：{点位}（{涨跌幅}%），上午成交额 {X} 亿（vs 盘前预期：{符合/超预期/不及}）
深证成指：{点位}（{涨跌幅}%）
创业板指：{点位}（{涨跌幅}%）
科创 50：{点位}（{涨跌幅}%）
上午合计成交额 {X} 亿（预计全天约 {X} 亿，较昨日全天{增加/减少}{差值}亿）

💰 资金动向（上午）：
北向资金：{盘中实时数据；若不可用则不写}
南向资金：港股通上午净买入 {X} 亿（若有数据；无则省略）

情绪指标（上午）：
上涨 {N} 家，下跌 {N} 家（涨跌比 {上涨/下跌，保留1位小数}:1，vs 盘前情绪预期{符合/偏强/偏弱}）
涨停 {N} 家，跌停 {N} 家，炸板 {N} 家（炸板率 {炸板/(涨停+炸板)×100}%）
连板高度：上午最高 {N} 板（{股票名}），较昨日收盘{升高/持平/回落}
情绪判断：{偏强/震荡/偏弱}（{1句依据，如"涨跌比5:1+连板高度稳，情绪良好"}）

🔥 二、主线验证与板块表现

领涨板块 TOP3（按涨幅，与昨日连板主线对照验证）：
{板块名}（+{涨幅}%）：涨停 {N} 家，龙头{股票名}。逻辑：{1-2句，延续昨日/新催化}
{板块名}（+{涨幅}%）：涨停 {N} 家，龙头{股票名}。逻辑：{1-2句}
{板块名}（+{涨幅}%）：涨停 {N} 家，龙头{股票名}。逻辑：{1-2句}

领跌板块 TOP3（按跌幅）：
{板块名}（{跌幅}%）：{核心原因，如"获利回吐/利空消息"}
{板块名}（{跌幅}%）：{原因}
{板块名}（{跌幅}%）：{原因}

主线确认：
今日最强主线：{板块名称}（依据：涨停家数最多+龙头持续封板+资金流入大）
主线稳定性：{稳定/出现电风扇切换}（{说明：若出现切换，描述从哪个板块切换到哪个，资金犹豫风险}）

⚡ 三、连板情绪与个股异动

连板梯队（2板及以上，上午快照）：
{N}板
{股票名} — {所属行业}（{午前状态：封板/炸板/未触板，1句逻辑}）

核心异动个股：
{股票A}：{异动描述，如"早盘快速涨停，10:30炸板，需关注下午是否回封"}
{股票B}：{异动描述，如"午前突发利好直线拉升，新进热点"}

🎯 四、下午策略推演

进攻方向：
若主线延续：关注{板块A}的补涨股/低位股，优先{有逻辑支撑的2板标的}
若主线切换：关注{低位板块B}是否形成首板，量能是否跟上

风险预警：
若成交量午后萎缩：警惕高位股补跌，{具体说明2-3个风险标的方向}
若指数冲高回落：避免追高，等待缩量回踩支撑再介入

关键观察点：
{观察点1，如"华电辽能下午是否维持封板，决定电力板块情绪走向"}
{观察点2，如"北向资金截至15:00是净流入还是净流出"}
{观察点3，如"午后成交额能否在前一日全天成交额基础上继续放量"}

数据来源：Tushare Pro · AKShare · 财联社快讯 · 财经媒体资讯
小龙虾备注：报告生成时间{时间}。数据基于上午收盘快照。下午策略需根据13:00开盘后15分钟走势微调。
```

### 盘后复盘报告模板

⚠️ 输出格式要求：为适配微信阅读，禁止使用 Markdown 表格（不出现 | 符号）、# 标题符号、** 加粗符号、- 或 * 列表符号、━ 分隔线。改用 emoji 图标、中文数字标题、空行分段。

⚙️ 生成逻辑：遵循三层漏斗模型。第一层取数完成后，进入第二层逻辑清洗（ST剔除→主线聚类→资金归因→情绪量化→风险识别），再进入第三层结构化输出，结论先行，数据支撑，逻辑推演。

```
📊 盘后复盘报告 · {日期}（{星期}）
今日核心：{一句话结论，概括主线+情绪，如"电力算力共振，情绪偏热，量能续扩"}

📈 一、指数全天表现

上证综指：{收盘点位}（{涨跌幅}%），成交额 {X} 亿，成交量 {X} 亿手
深证成指：{收盘点位}（{涨跌幅}%），成交额 {X} 亿
创业板指：{收盘点位}（{涨跌幅}%），成交额 {X} 亿
科创 50：{收盘点位}（{涨跌幅}%），成交额 {X} 亿
沪深两市合计成交额：{X} 亿元（较昨日{增加/减少} {差值} 亿，环比{+/-}{变化幅度}%）

💰 资金动向：
北向资金：{成交净买额结算当日可能滞后；若数据为0则不写，改为"数据结算滞后，次日更新"}
南向资金：港股通合计净买入 {X} 亿（沪港通 {X} 亿 / 深港通 {X} 亿），恒生指数今日 {涨跌幅}%

🌡️ 二、市场情绪

上涨 {N} 家，下跌 {N} 家，平盘 {N} 家（涨跌比 {上涨/下跌，保留1位小数}:1）。
涨停 {N} 家，跌停 {N} 家，炸板 {N} 家（炸板率 {炸板/(涨停+炸板)×100}%）。
连板高度：最高 {N} 板（{股票名}）。
情绪评级：{亢奋 / 偏热 / 正常 / 偏冷 / 低迷}（{1句定性依据，如"涨跌比8.7:1，连板达8板，炸板率低"}）

🔥 连板梯队（2板及以上，按连板数降序，每只独立一行）

{N}板
{股票名} — {所属行业}（{题材/催化逻辑，1句}）

{N}板
{股票名} — {所属行业}（{题材/催化逻辑，1句}）
{股票名} — {所属行业}（{题材/催化逻辑，1句}）

（2板个股较多时：先列有明确题材逻辑的，最后一行合并列出无突出题材的，格式：{名1}、{名2}、{名3} — {行业}，无需重复标注2板）

🏷️ 今日涨停题材热度（TOP8）：
1. {题材} — {N} 家
2. {题材} — {N} 家
（以此类推）

📊 三、主线复盘（按强度排序）

第一主线｜{主线名称}（{涨停家数}家涨停）
驱动因子：{政策催化 / 业绩催化 / 资金追涨 / 情绪扩散}
代表龙头：{股票名}（{涨跌幅}%）
逻辑：{2-3句，含催化事件+资金流向+板块联动}

第二主线｜{主线名称}（{涨停家数}家涨停）
驱动因子：{类型}
代表龙头：{股票名}（{涨跌幅}%）
逻辑：{2-3句}

第三主线｜{主线名称（若有）}
（以此类推，无则省略）

弱势板块：
{板块名}（{涨跌幅}%）：{下跌原因，来自财经媒体，1句}⚠️
{板块名}（{涨跌幅}%）：{下跌原因}

📝 四、今日小结与明日策略

{今日市场整体定性：指数走势特征、量能变化、情绪高低、主线集中度，3-4句，结论先行}

进攻方向：
{方向1，说明催化延续性+关注个股+核心逻辑}
{方向2（如有）}

防守方向：
{高位板块风险或弱势板块避雷，1-2条}

关键观察点：
{观察点1，如"明日成交额能否维持2万亿以上"}
{观察点2，如"连板旗帜股开盘溢价或跌停"}
{观察点3（如有）}

⚠️ 风险提示：{需关注的风险因素，1-2条}。本报告仅供参考，不构成投资建议。

数据来源：Tushare Pro（全市场日线统计）· AKShare（涨停池/连板梯队/南向资金）· 财联社快讯 · 东方财富
```

---

## 第四步：输出规范

**三层漏斗强制执行顺序（三类报告通用）：**
1. 第一层（数据获取）：按优先级P1→P2→P3→P4顺序取数，每项独立降级，缺失则留空不臆想
2. 第二层（逻辑清洗）：ST剔除 → 主线聚类（涨停家数TOP3板块）→ 资金归因 → 情绪量化（涨跌比/连板高度/炸板率）→ 风险识别（跌幅前3板块）
3. 第三层（结构化输出）：结论先行（标题行一句话定性）→ 数据支撑（指数/资金/情绪数字）→ 逻辑推演（主线分析/驱动因子/明日策略）

**盘前专属规范：**
- 消息面筛选：只列"超预期"事件，已消化多日的重复利好不列入
- 剧本推演必须覆盖三种开盘场景（高开放量/高开缩量/低开1%+），给出对应操作原则
- 技术点位必须说明依据（均线/整数关口/前高前低），不可凭空给出
- 若外盘数据暂缺，外盘部分直接标注"暂缺"，不臆想

**盘中专属规范：**
- 必须与盘前预判做对比（vs盘前预期：符合/超预期/不及），体现"验证"价值
- 主线稳定性必须判断：是否出现"电风扇"（快速轮动切换），若有需明确指出风险
- 连板高度必须与昨日对比（升高/持平/回落），判断情绪周期方向
- 下午推演必须给出"若A则B"条件分支，而非单一预测

**强制要求（三类报告通用）：**
- 数字数据（点位、涨跌幅、资金额）必须来自 Tushare（工具 A），不可估算或捏造
- 板块原因分析来自搜索结果（工具 B），简要注明"据财经媒体"
- 接口报错或无数据时，自动降级至搜索引擎补充，报告内无需解释数据来源问题
- 成交量（手）与成交额（亿元）必须同时列出，不可混用
- 板块排名以涨幅为准，资金流向仅作辅助说明
- 连板天数以 tag 字段解析为准（`N天N板` 中取第二个数字）
- 主线复盘必须标注驱动因子类型（政策催化/业绩催化/资金追涨/外部联动/情绪扩散）
- 情绪评级必须附1句定性依据（不能只写"偏热"两字）

**微信可读性格式规范（强制）：**
- 禁止使用 Markdown 表格（不出现 `|` 符号）
- 禁止使用 `#`、`##`、`###` 标题符号
- 禁止使用 `**加粗**` 语法
- 禁止使用 `-` 或 `*` 作为列表符号（改用序号 1. 2. 3. 或直接换行）
- 段落分隔使用空行，禁止使用 `━` 分隔线
- 层级关系用"一、二、三"等中文数字标题体现
- 指数数据每行一条，格式：`指数名：点位（涨跌幅%），成交额X亿`
- 连板梯队格式规范：
  - 每只股票独立一行，按板数降序
  - 同板数股票各自独立成行，不合并在一行
  - 格式：`{股票名} — {所属行业}（{题材/催化逻辑，1句}）`
  - 板数标题单独占一行：`{N}板`，下方接对应股票
  - 2板个股较多（>5只）时：有明确题材的单独列出，其余用"名1、名2、名3 — 行业"合并一行
- 北向/南向资金：使用 `成交净买额` 字段，单位亿元；`资金净流入` 字段为当日额度余额，不可用作净买金额；收盘当日北向数据结算滞后时不写，不臆想

**严禁出现：**
- "接口报错"、"数据未返回"、"受限制"
- "以上仅供参考"、"免责声明"、"注："
- 任何解释工具状态或数据来源问题的文字
- 个股代码或买卖建议

---

## 自动推送：定时报告机制

### 默认行为

安装本 Skill 后，**自动推送默认开启**，无需额外配置。WorkBuddy 会在每个交易日的以下三个时间点自动生成并推送对应报告：

| 时间 | 报告类型 | 说明 |
|-----|---------|------|
| 08:55 | 🌅 盘前市场综述 | 开盘前5分钟，提供外盘映射+消息面+今日策略 |
| 11:35 | 🕛 盘中市场简评 | 午间收盘后5分钟，验证盘前预判+推演下午策略 |
| 15:05 | 📊 盘后复盘报告 | 收盘后5分钟，全天主线复盘+明日展望 |

### 推送目标

报告会推送到用户在 WorkBuddy 中绑定的消息端（微信 / WhatsApp / 其他）。若未绑定任何消息端，则报告直接输出在当前对话窗口。推送逻辑：

```
检查用户已绑定的消息端
  ├─ 已绑定微信   → 推送到微信（自动适配微信可读格式）
  ├─ 已绑定其他端 → 推送到对应端
  └─ 未绑定任何端 → 在 WorkBuddy 对话中直接输出
```

### 非交易日处理

自动推送任务在执行时会先判断当日是否为 A 股交易日：
- 若为周末、法定节假日或临时休市日 → 自动跳过，不生成报告，不推送
- 判断方法：检查 AKShare `tool_trade_date_hist_sina()` 或搜索引擎确认是否为交易日

```python
import akshare as ak
from datetime import date

def is_trade_day(check_date: date = None) -> bool:
    """判断指定日期是否为A股交易日，默认检查今日"""
    if check_date is None:
        check_date = date.today()
    try:
        df = ak.tool_trade_date_hist_sina()
        trade_dates = set(df['trade_date'].astype(str).tolist())
        return check_date.strftime('%Y-%m-%d') in trade_dates
    except Exception:
        # 接口失败时：周一至周五视为交易日（保守兜底）
        return check_date.weekday() < 5

# 自动推送脚本入口调用示例
if not is_trade_day():
    print("今日非交易日，跳过报告生成。")
    exit(0)
# 继续执行报告生成逻辑...
```

### 关闭或修改自动推送

用户可随时通过以下方式管理自动推送：

- **暂停推送**：在 WorkBuddy 自动化管理页中找到对应任务，切换为「暂停」状态
- **永久关闭**：删除三个自动推送任务（盘前/盘中/盘后）
- **修改时间**：在自动化管理页编辑 rrule，调整 BYHOUR/BYMINUTE 参数
- **口令控制**（对话触发）：直接告诉 WorkBuddy「关闭盘前自动推送」/ 「暂停今日报告」

### 首次安装引导话术

当用户首次安装或首次触发本 Skill 时，输出以下引导信息（仅在首次运行时显示一次）：

```
📣 china-stocks-daily-review 已就绪

已为您开启每日自动推送（A股交易日）：
  🌅 08:55 盘前综述
  🕛 11:35 盘中简评
  📊 15:05 盘后复盘

报告将推送至您绑定的消息端。如需关闭，请说「关闭自动推送」或前往自动化管理页操作。
```

---

## 踩坑经验（实测积累）

**Tushare Pro 官方接口（工具 A）：**
- **Token 配置**：token 存于 `~/.tushare_token`，首次运行由 `startup_check()` 引导用户注册获取
- **积分要求**：免费注册可获基础积分，`limit_list_ths`、`moneyflow_ind_ths` 等接口需一定积分；若返回"权限不足"，前往 https://tushare.pro 查看积分要求
- `index_daily` / 多指数查询：**不支持逗号分隔多 ts_code**，必须逐个单独查询
- `limit_list_ths` / 连板天数：`lu_limit_order`（index 14）**全为 None 不可用**，应解析 `tag` 字段（index 8），格式 "N天N板"
- `limit_list_ths` / 涨跌停区分：用 `limit_type`（index 7）字段，含"涨停池"为涨停、含"跌停池"为跌停
- `moneyflow_ind_ths` / 板块排名：应按 `pct_change`（index 5）排序，**不是按 `net_amount`**（净流入金额）
- `index_daily` / 成交额单位：`amount` 字段单位为**千元**，转亿元需 `/1e5`
- `moneyflow_hsgt` / 北向资金：`north_money` 字段单位已为**亿元**，直接使用
- `limit_list_d` / fields 过滤：该接口 fields 参数过滤无效，改用 `limit_list_ths`

- `stock_basic` / 频率限制：免费账号每小时只能调用1次，避免在同一小时内多次调用；如名称查询失败，改用搜索引擎（东方财富 quote 页面）交叉核对代码名称
- `daily` / 全市场统计降级方案：index_daily 权限不足时，可用 `daily` 拉全市场个股数据，统计 pct_chg>=9.9% 作为涨停家数、pct_chg<=-9.9% 作为跌停家数、amount 加总/1e5 得到全市场成交额（单位亿元）

- `stock_hsgt_north_net_flow_in_em` / 北向资金：**此接口名称已失效**，改用 `stock_hsgt_fund_flow_summary_em()`，含沪港通/深港通分项，但收盘当日"资金净流入"字段结算滞后（当日显示0），建议次日取或改用搜索引擎

**AKShare（工具 A2）：**
- `stock_zh_index_spot_em` / 成交额单位：为**元**，转亿元需 `/1e8`（与 Tushare 的千元/1e5 不同，切勿混用）
- `stock_zt_pool_em` / 连板天数：直接读 `连板数` 列（整数），无需解析字符串
- `stock_sector_fund_flow_rank` / 板块排名：用 `今日涨跌幅` 列排序（非资金流列）；`sector_type` 参数正确值为 `'行业资金流'`（不是 `'行业资金流向'`）
- `stock_hsgt_north_net_flow_in_em` / 北向资金：接口名已失效，改用 `stock_hsgt_fund_flow_summary_em`
- `stock_info_global_cls` / 财联社快讯：`标题` 列通常为空，实际内容在 `内容` 列；`发布日期` 字段类型为 `datetime.date` 对象，**不能用字符串 `'2026-03-25'` 过滤**，需用 `datetime.date.today()` 比较
- `stock_board_industry_spot_em` / `stock_board_concept_spot_em` / 东方财富板块实时行情：连接稳定性差，经常 `RemoteDisconnected`；**不要依赖此接口**，替代方案：`stock_sector_fund_flow_rank(sector_type='行业资金流')` 或搜索引擎
- `news_cctv` / 新闻联播：非交易日或当日文字稿未发布时返回空列表，不影响报告生成

**Tushare（工具 A）新接口测试结果（2026-03-25）：**
- `news` / 新闻快讯：当前账号积分不足，返回 0 条，降级至 AKShare 财联社快讯
- `cctv_news` / 新闻联播：返回 0 条（当日文稿未发布），正常现象
- `stk_news` / 个股新闻：接口名称不正确（40101），不存在此接口
- `top_list` / 龙虎榜：40203 权限不足
- `hm_detail` / 游资：接口存在但当日返回 0 条（结算延迟）
