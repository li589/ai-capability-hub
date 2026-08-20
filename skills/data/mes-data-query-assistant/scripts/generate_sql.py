#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MES 智能问数 · 第一步：中文需求 → SQL 生成器（规则版路由）
用法：python generate_sql.py "问题"  （可多个问题，逐个生成）
流程：四要素解析 → intent 匹配（asset_index）→ 资产 SQL 复用（sql_assets_full）
       → 参数化 WHERE → 未命中用 schema 兜底模板
说明：本工具为确定性路由兜底；接入 Skill 后四要素解析由 LLM 完成，本工具负责路由与 SQL 组装。
"""
import sys, os, re, json, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _data_dir():
    # 优先使用 config.json 的 data_dir（skill 可移植时指向数据目录）
    try:
        with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
            dd = json.load(f).get("data_dir")
        if dd:
            return dd
    except Exception:
        pass
    return os.path.join(BASE, "data")

DATA = _data_dir()

def load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)

SCHEMA = load("schema.json")
ASSET = load("asset_index.json")
VIEWS = load("views_full.json")
SQL_MAP = {v["Name"]: v["MySqlSql"] for v in VIEWS if not v["sql_placeholder"] and v["MySqlSql"]}
PLACEHOLDER = {v["Name"] for v in VIEWS if v["sql_placeholder"]}

# ---------------- 委外供应商绩效资产(2026-08-17 新增,SQL 已真实库验证) ----------------
# 口径:良品率 = OK/(OK+NG)(回货验收);准时率 = 已完成单(状态3)中 最后一批回货日期<=要求回货日期的占比
#       (DELIVERY_DATE 为当天 00:00,按 DATE() 比较,当天内回货即准时;同单可分批回货,取最后一批)
# 状态:1=委外中 2=部分回货 3=全部回货;DELIVERY_DATE=1900-01-01 脏数据已过滤
# 供应商全景汇总(一张表):在手委外单(单头/单身/发货量) + 良品率 + 准时率 + 逾期
SQL_SUPPLIER_FULL = """
SELECT
  sup.SUPPLIER_ID,
  IFNULL(sup.SUPPLIER_NAME, sup.SUPPLIER_ID) AS SUPPLIER_NAME,
  -- ① 在手委外单(状态1委外中)
  IFNULL(h.ORDER_CNT, 0)   AS HANDS_ORDER_CNT,   -- 在手委外单数(单头)
  IFNULL(h.DETAIL_CNT, 0)  AS HANDS_DETAIL_CNT,  -- 在手单身数(明细行数)
  IFNULL(h.SEND_QTY, 0)    AS HANDS_SEND_QTY,    -- 在手发货数量
  -- ② 良品率(近{days}天回货验收口径)
  p.GOOD_RATE              AS GOOD_RATE,         -- 良品率
  IFNULL(p.CHECK_TOTAL_QTY, 0) AS CHECK_TOTAL_QTY, -- 验收总数
  IFNULL(p.NG_QTY, 0)      AS NG_QTY,            -- 验退不良数
  -- ③ 准时率(近{days}天,已完成单口径)
  p.ONTIME_RATE            AS ONTIME_RATE,       -- 准时率
  IFNULL(p.FINISHED_CNT, 0) AS FINISHED_CNT,     -- 已完成单数
  IFNULL(p.OVERDUE_CNT, 0) AS OVERDUE_CNT        -- 逾期单数
FROM (
  SELECT s.SUPPLIER_ID, IFNULL(sup.SUPPLIER_NAME, s.SUPPLIER_ID) AS SUPPLIER_NAME
  FROM di_outsource_send_basis s
  LEFT JOIN ou_supplier_basis sup ON s.SUPPLIER_ID = sup.SUPPLIER_ID
  WHERE s.DELIVERY_DATE > '2000-01-01'
  {sup_filter}
  GROUP BY s.SUPPLIER_ID, sup.SUPPLIER_NAME
) sup
LEFT JOIN (
  SELECT s.SUPPLIER_ID,
    COUNT(DISTINCT s.OUTSOURCE_ID) AS ORDER_CNT,
    COUNT(d.PARENT_ID) AS DETAIL_CNT,
    SUM(d.SEND_QTY) AS SEND_QTY
  FROM di_outsource_send_basis s
  LEFT JOIN di_outsource_send_detail d ON s.ID = d.PARENT_ID
  WHERE s.OUTSOURCE_STATUS = 1 AND s.DELIVERY_DATE > '2000-01-01'
  GROUP BY s.SUPPLIER_ID
) h ON h.SUPPLIER_ID = sup.SUPPLIER_ID
LEFT JOIN (
  SELECT s.SUPPLIER_ID,
    ROUND(SUM(b.OK_QTY) * 100.0 / NULLIF(SUM(b.OK_QTY + b.NG_QTY), 0), 2) AS GOOD_RATE,
    SUM(b.OK_QTY + b.NG_QTY) AS CHECK_TOTAL_QTY,
    SUM(b.NG_QTY) AS NG_QTY,
    ROUND(SUM(CASE WHEN DATE(t.last_back_time) <= DATE(s.DELIVERY_DATE) THEN 1 ELSE 0 END)
          * 100.0 / NULLIF(SUM(CASE WHEN s.OUTSOURCE_STATUS = 3 THEN 1 ELSE 0 END), 0), 2) AS ONTIME_RATE,
    SUM(CASE WHEN s.OUTSOURCE_STATUS = 3 THEN 1 ELSE 0 END) AS FINISHED_CNT,
    SUM(CASE WHEN s.OUTSOURCE_STATUS = 3 AND DATE(t.last_back_time) > DATE(s.DELIVERY_DATE)
        THEN 1 ELSE 0 END) AS OVERDUE_CNT
  FROM di_outsource_send_basis s
  JOIN di_outsource_back_process b ON s.OUTSOURCE_ID = b.OUTSOURCE_ID
  LEFT JOIN (SELECT OUTSOURCE_ID, MAX(CREATE_TIME) AS last_back_time
             FROM di_outsource_back_process GROUP BY OUTSOURCE_ID) t ON t.OUTSOURCE_ID = s.OUTSOURCE_ID
  WHERE b.CREATE_TIME >= '{d1} 00:00:00' AND b.CREATE_TIME <= '{d2} 23:59:59'
    AND s.DELIVERY_DATE > '2000-01-01'
  GROUP BY s.SUPPLIER_ID
) p ON p.SUPPLIER_ID = sup.SUPPLIER_ID
ORDER BY p.ONTIME_RATE IS NULL ASC, p.ONTIME_RATE ASC, p.GOOD_RATE ASC
"""

# 排除"供应商"前的泛化前缀(委外供应商/外协供应商 → 表示全部,不是具体名称)
SUP_EXCLUDE = {"委外", "外协", "全部", "所有", "每个", "这家", "该", "目标",
               "意向", "合作", "合格", "优质", "重点", "长期", "现有",
               "候选", "新", "旧", "其他", "各个"}


def extract_supplier(q):
    """从问题中提取供应商编号或名称片段;无法确定返回 None(查全部)。
    支持:供应商A0001 / A0001供应商 / CNC供应商 / 客户X供应商 / FZHGYS供应商
    排除:委外供应商/外协供应商(指全部,非具体名称)"""
    m = re.search(r"(?:供应商|供方|外协厂)\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)", q)
    if m:
        return m.group(1)
    m = re.search(r"([A-Za-z0-9][A-Za-z0-9_.\-]*)\s*(?:供应商|供方|外协厂)", q)
    if m:
        return m.group(1)
    m = re.search(r"([\u4e00-\u9fa5]{2,6})供应商", q)
    if m and m.group(1) not in SUP_EXCLUDE:
        return m.group(1)
    return None


def supplier_perf_results(question, t0, t1):
    """委外供应商全景汇总(一张表):在手委外单 + 良品率 + 准时率 + 逾期。
    默认近90天,显式时间按提问;支持指定供应商过滤。"""
    explicit = any(k in question for k in ["今天", "今日", "昨天", "前天", "本周",
                                           "上周", "本月", "上月", "近", "最近"])
    if not explicit:
        d1 = TODAY - datetime.timedelta(days=89)
        d2 = TODAY
        days = 90
        tag_days = "近90天"
    else:
        d1, d2 = t0, t1
        days = (d2 - d1).days + 1
        tag_days = f"{d1.isoformat()}~{d2.isoformat()}"
    sup = extract_supplier(question)
    sup_filter = ""
    if sup:
        sup_filter = f"AND (s.SUPPLIER_ID LIKE '%{sup}%' OR sup.SUPPLIER_NAME LIKE '%{sup}%')"
    warns = []
    if sup:
        warns.append(f"按供应商过滤: {sup}(编号或名称 LIKE)")
    if not explicit:
        warns.append("未指定时间,默认统计近90天(发货/回货时间)")
    sql = SQL_SUPPLIER_FULL.format(d1=d1, d2=d2, days=days, sup_filter=sup_filter)
    return [
        {"tag": f"供应商委外全景汇总 · 在手单+良品率+准时率({tag_days})",
         "sql": sql, "warns": warns},
    ]

# ---------------- ① 时间解析 ----------------
TODAY = datetime.date.today()

def parse_time(q):
    today = TODAY
    if "今天" in q or "今日" in q:
        return today, today, "今天"
    if "昨天" in q or "昨日" in q:
        d = today - datetime.timedelta(days=1); return d, d, "昨天"
    if "前天" in q:
        d = today - datetime.timedelta(days=2); return d, d, "前天"
    if "本周" in q:
        monday = today - datetime.timedelta(days=today.weekday()); return monday, today, "本周"
    if "上周" in q:
        monday = today - datetime.timedelta(days=today.weekday() + 7)
        sunday = monday + datetime.timedelta(days=6); return monday, sunday, "上周"
    if "本月" in q or "这个月" in q:
        return today.replace(day=1), today, "本月"
    if "上月" in q:
        first = today.replace(day=1)
        prev = (first - datetime.timedelta(days=1)).replace(day=1)
        last = first - datetime.timedelta(days=1); return prev, last, "上月"
    m = re.search(r"(?:最近|近)\s*(\d+)\s*天", q)
    if m:
        n = int(m.group(1)); return today - datetime.timedelta(days=n - 1), today, f"近{n}天"
    m = re.search(r"(\d{1,2})月(\d{1,2})[日号]?", q)
    if m:
        d = today.replace(month=int(m.group(1)), day=int(m.group(2)))
        return d, d, f"{m.group(1)}月{m.group(2)}日"
    m = re.search(r"(\d{4})[-年](\d{1,2})[-月](\d{1,2})", q)
    if m:
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return d, d, d.isoformat()
    return today, today, "今天"  # 未指定时间默认今天（查询统计类更安全）

# ---------------- ② 实体解析 ----------------
def parse_entity(q):
    ent = {}
    # 设备：支持 "设备M01" / "M01设备" 两种顺序
    m = re.search(r"(?:设备|机台|机器|机床)\s*([A-Za-z0-9][A-Za-z0-9_\-]*)|([A-Za-z0-9][A-Za-z0-9_\-]*)\s*(?:设备|机台|机器|机床)", q)
    if m:
        ent["equipment"] = m.group(1) or m.group(2)
    # 产品：支持 "产品M02" / "M02产品" 两种顺序
    m = re.search(r"(?:产品|品号|品名|物料|材料|料号)\s*([A-Za-z0-9][A-Za-z0-9_\-]*)|([A-Za-z0-9][A-Za-z0-9_\-]*)\s*(?:产品|品号|品名|物料|材料|料号)", q)
    if m:
        ent["product"] = m.group(1) or m.group(2)
    else:
        # 兜底：形如 M02 / YZTEST 的产品编码（中文算 \w，不能用 \b，用负向断言）
        m = re.search(r"(?<![A-Za-z0-9_])([A-Z]{1,4}[0-9]{2,}[A-Z0-9_\-]*)(?![A-Za-z0-9_])", q)
        if m:
            ent["product"] = m.group(1)
    # 车间/产线：支持 "车间3" / "3号车间" / "3车间" 顺序
    m = re.search(r"(?:车间|产线|工位|工作站)\s*([A-Za-z0-9][A-Za-z0-9_\-]*)|(\d+)\s*(?:号)?\s*(?:车间|产线|工位|工作站)", q)
    if m:
        ent["ws"] = m.group(1) or m.group(2)
    return ent

# ---------------- ③ intent 匹配 ----------------
def match_intent(q):
    best, best_score, best_cnt = None, 0, 0
    for iid, it in ASSET["intents"].items():
        hits = [kw for kw in it["keywords"] if kw in q]
        if not hits:
            continue
        score = max(len(kw) for kw in hits)  # 最长命中词为准，防泛词累加误判
        # 平局时：命中词数更多者优先（如 "未完工的派工单" → dispatch_rate）
        if score > best_score or (score == best_score and len(hits) > best_cnt):
            best, best_score, best_cnt = iid, score, len(hits)
    return best, best_score

# ---------------- ④ 视图选择 ----------------
def pick_view(iid, ent):
    """优先 intent.preferred（资产配置的口径正确视图）；否则按打分"""
    it = ASSET["intents"].get(iid)
    if not it:
        return None
    pref = it.get("preferred")
    if pref and pref in SQL_MAP:
        return pref
    views = it.get("views", [])
    for v in views:
        if v in SQL_MAP:
            return v
    return None

# ---------------- ⑤ 参数化 WHERE ----------------
VIEW_FILTERS = ASSET.get("view_filters", {})
TIME_COLS = ["CSDDATE", "CREATE_TIME", "WORK_TIME", "EXECUTE_TIME", "START_TIME",
             "CHECK_DATE", "DISPATCH_START_TIME", "REPORT_TIME"]
PROD_COLS = ["MA_ID", "MAID", "MANAME", "MATERIAL_NAME"]
EQ_COLS = ["EQ_ID", "EQID"]

def param_sql(sql, view_name, params):
    """按 view_filters 白名单在视图顶层追加 WHERE；白名单外的视图不追加（防误过滤）"""
    warns, where = [], []
    vf = VIEW_FILTERS.get(view_name, {})
    if not vf:
        return sql, [f"视图 {view_name} 未配置过滤白名单（view_filters），返回全量；如需时间/实体过滤请用底层表生成"]
    # 时间
    tcol = vf.get("time")
    if params.get("date_from") and params.get("date_to") and tcol:
        d1, d2 = params["date_from"], params["date_to"]
        if d1 == d2:
            where.append(f"{tcol} >= '{d1} 00:00:00' AND {tcol} < '{d2 + datetime.timedelta(days=1)} 00:00:00'")
        else:
            where.append(f"{tcol} >= '{d1} 00:00:00' AND {tcol} <= '{d2} 23:59:59'")
    # 产品
    if params.get("product"):
        pcol = vf.get("product")
        if pcol:
            where.append(f"{pcol} = '{params['product']}'")
        else:
            warns.append(f"视图 {view_name} 不支持按产品过滤，需改查底层表（{', '.join(PROD_COLS)}）")
    # 设备
    if params.get("equipment"):
        ecol = vf.get("equipment")
        if ecol:
            where.append(f"{ecol} = '{params['equipment']}'")
        else:
            warns.append(f"视图 {view_name} 不支持按设备过滤，需改查底层表")
    if where:
        # WHERE 需插在 GROUP BY / ORDER BY / LIMIT 之前（聚合视图不能追加到末尾）
        wclause = "WHERE " + "\n  AND ".join(where)
        upper = sql.upper()
        cut = len(sql)
        for kw in [" GROUP BY ", " ORDER BY ", " LIMIT "]:
            p = upper.find(kw)
            if p != -1 and p < cut:
                cut = p
        base = sql.rstrip().rstrip(";")
        if cut >= len(base):
            wsql = base + "\n" + wclause + ";"
        else:
            wsql = base[:cut] + "\n" + wclause + "\n" + base[cut:].lstrip() + ";"
        return wsql, warns
    return sql, warns

# ---------------- ⑥ schema 兜底模板 ----------------
def fallback_sql(iid, ent, t, question=""):
    tpl = {
        "output_summary": (
            "SELECT DATE(r.EXECUTE_TIME) AS 日期, pm.MA_ID AS 产品, SUM(r.EXECUTE_QTY) AS 产量\n"
            "FROM ac_mo_report_process r\n"
            "LEFT JOIN pl_mo_data pm ON r.MO_ID = pm.MO_ID\n"
            "WHERE r.EXECUTE_TIME >= '{d1} 00:00:00' AND r.EXECUTE_TIME < '{d2_plus} 00:00:00'\n"
            "  AND (r.IS_CANCEL IS NULL OR r.IS_CANCEL <> 1)\n"
            "  AND r.EXECUTE_TYPE = 5"  # 口径：仅结束加工算产量（发放=PMC职责，不计）
            "{prod}{eq}\nGROUP BY DATE(r.EXECUTE_TIME), pm.MA_ID"
        ),
        "eq_status": (
            "SELECT eb.EQ_ID, eb.EQ_NAME, es.EQ_N_STATUS AS 设备状态, es.START_TIME\n"
            "FROM eq_basis eb JOIN eq_status es ON eb.ID = es.PARENT_ID\n"
            "WHERE es.EQ_N_STATUS <> 0"  # 口径：EQ_N_STATUS=0 是脏数据（初始/未上报态），统计不计
            "{eq}"
        ),
        "quality_bad": (
            "SELECT ierr.SOURCE_TYPE AS 来源,\n"
            "       COALESCE(dcd.COLLECTION_CHOICE_NAME, dcd2.COLLECTION_NAME, '未指定') AS 不良原因,\n"
            "       COALESCE(mob1.OP_NAME, mob2.OP_NAME, '') AS 工序,\n"
            "       COALESCE(spc.WS_ID, mr.WS_ID, '') AS 车间,\n"
            "       SUM(ierr.QTY) AS 不良数\n"
            "FROM in_except_reason_record ierr\n"
            "LEFT JOIN da_collection_choice_detail dcd ON ierr.BAD_REASON = dcd.ID\n"
            "LEFT JOIN da_collection_data dcd2 ON ierr.BAD_REASON = dcd2.ID\n"
            "LEFT JOIN in_spc_data spc ON ierr.SOURCE_TYPE = 2 AND ierr.PARENT_ID = spc.ID\n"
            "LEFT JOIN ac_mo_report_process mr ON ierr.SOURCE_TYPE = 1 AND ierr.PARENT_ID = mr.ID\n"
            "LEFT JOIN me_op_basis mob1 ON spc.OP_ID = mob1.OP_ID\n"
            "LEFT JOIN me_op_basis mob2 ON mr.OP_ID = mob2.OP_ID\n"
            "WHERE ierr.CREATE_TIME >= '{d1} 00:00:00' AND ierr.CREATE_TIME < '{d2_plus} 00:00:00'"
            "{prod}\nGROUP BY ierr.SOURCE_TYPE, COALESCE(dcd.COLLECTION_CHOICE_NAME, dcd2.COLLECTION_NAME, '未指定'), "
            "COALESCE(mob1.OP_NAME, mob2.OP_NAME, ''), COALESCE(spc.WS_ID, mr.WS_ID, '')\n"
            "ORDER BY 不良数 DESC"
        ),
        "mo_progress": (
            "SELECT MO_ID, MA_ID, TO_BE_STARTED_QTY, PENDING_COMPLETION_QTY, COMPLETED_QTY, IS_PAUSE\n"
            "FROM ac_lot_status\nWHERE 1=1{prod}"
        ),
    }
    if iid == "dispatch_rate":
        # 派工完成率：派工侧(d) vs 报工完成侧(累计对齐)，支持 产品/设备/派工单明细/未完工 四形态
        unfinished = any(k in question for k in ["未完工", "未完成", "没做完", "没做", "还没做"])
        if unfinished:
            sql = (
                "SELECT d.MO_ID AS 工单, pm.MA_ID AS 产品, mb.MATERIAL_NAME AS 品名,\n"
                "       d.OP_SEQ AS 工序序, d.OP_ID AS 工艺, d.DISPATCH_EQ_ID AS 设备,\n"
                "       d.DISPATCH_WO_ID AS 派工人, d.DISPATCH_QTY AS 派工量,\n"
                "       DATE(d.DISPATCH_START_TIME) AS 派工日期\n"
                "FROM dispatch_record d\n"
                "LEFT JOIN pl_mo_data pm ON d.MO_ID = pm.MO_ID\n"
                "LEFT JOIN ma_basis mb ON pm.MA_ID = mb.MA_ID\n"
                "LEFT JOIN (SELECT MO_ID, OP_SEQ, OP_ID, SUM(EXECUTE_QTY) AS 完成量\n"
                "           FROM ac_mo_report_process\n"
                "           WHERE EXECUTE_TYPE = 5 AND (IS_CANCEL IS NULL OR IS_CANCEL <> 1)\n"
                "           GROUP BY MO_ID, OP_SEQ, OP_ID) r\n"
                "  ON d.MO_ID = r.MO_ID AND d.OP_SEQ = r.OP_SEQ AND d.OP_ID = r.OP_ID\n"
                "WHERE r.MO_ID IS NULL  -- 无对应结束加工报工 = 未完工\n"
                "ORDER BY d.DISPATCH_QTY DESC\n"
                "LIMIT 30"
            )
            return sql, ["未完工派工单：派工表中无对应结束加工报工记录的派工单（完工率=0），按派工量降序"]
        if ent.get("product"):
            sql = (
                "SELECT p.产品, p.品名, p.派工量, p.派工工单数, COALESCE(c.完成量, 0) AS 完成量,\n"
                "       ROUND(COALESCE(c.完成量, 0) * 100.0 / NULLIF(p.派工量, 0), 1) AS 完工率\n"
                "FROM (SELECT pm.MA_ID AS 产品, mb.MATERIAL_NAME AS 品名, SUM(d.DISPATCH_QTY) AS 派工量, COUNT(DISTINCT d.MO_ID) AS 派工工单数\n"
                "      FROM dispatch_record d\n"
                "      LEFT JOIN pl_mo_data pm ON d.MO_ID = pm.MO_ID\n"
                "      LEFT JOIN ma_basis mb ON pm.MA_ID = mb.MA_ID\n"
                f"      WHERE 1=1 AND pm.MA_ID = '{ent['product']}'\n"
                "      GROUP BY pm.MA_ID, mb.MATERIAL_NAME) p\n"
                "LEFT JOIN (SELECT pm2.MA_ID AS 产品, SUM(r.EXECUTE_QTY) AS 完成量\n"
                "           FROM ac_mo_report_process r LEFT JOIN pl_mo_data pm2 ON r.MO_ID = pm2.MO_ID\n"
                "           WHERE r.EXECUTE_TYPE = 5 AND (r.IS_CANCEL IS NULL OR r.IS_CANCEL <> 1)\n"
                "           GROUP BY pm2.MA_ID) c ON p.产品 = c.产品\n"
                "ORDER BY p.派工量 DESC"
            )
        elif ent.get("equipment"):
            sql = (
                "SELECT p.设备, p.设备名, p.派工量, p.派工笔数, COALESCE(c.完成量, 0) AS 完成量,\n"
                "       ROUND(COALESCE(c.完成量, 0) * 100.0 / NULLIF(p.派工量, 0), 1) AS 完工率\n"
                "FROM (SELECT d.DISPATCH_EQ_ID AS 设备, eb.EQ_NAME AS 设备名, SUM(d.DISPATCH_QTY) AS 派工量, COUNT(*) AS 派工笔数\n"
                "      FROM dispatch_record d\n"
                "      LEFT JOIN eq_basis eb ON d.DISPATCH_EQ_ID = eb.EQ_ID\n"
                f"      WHERE 1=1 AND d.DISPATCH_EQ_ID = '{ent['equipment']}'\n"
                "      GROUP BY d.DISPATCH_EQ_ID, eb.EQ_NAME) p\n"
                "LEFT JOIN (SELECT r.EQ_ID AS 设备, SUM(r.EXECUTE_QTY) AS 完成量\n"
                "           FROM ac_mo_report_process r\n"
                "           WHERE r.EXECUTE_TYPE = 5 AND (r.IS_CANCEL IS NULL OR r.IS_CANCEL <> 1)\n"
                "           GROUP BY r.EQ_ID) c ON p.设备 = c.设备\n"
                "ORDER BY p.派工量 DESC"
            )
        else:
            sql = (
                "SELECT d.MO_ID AS 工单, pm.MA_ID AS 产品, d.OP_SEQ AS 工序序, d.OP_ID AS 工艺,\n"
                "       d.DISPATCH_EQ_ID AS 设备, d.DISPATCH_WO_ID AS 派工人, d.DISPATCH_QTY AS 派工量,\n"
                "       COALESCE(r.完成量, 0) AS 完成量,\n"
                "       ROUND(COALESCE(r.完成量, 0) * 100.0 / NULLIF(d.DISPATCH_QTY, 0), 1) AS 完工率\n"
                "FROM dispatch_record d\n"
                "LEFT JOIN pl_mo_data pm ON d.MO_ID = pm.MO_ID\n"
                "LEFT JOIN (SELECT MO_ID, OP_SEQ, OP_ID, SUM(EXECUTE_QTY) AS 完成量\n"
                "           FROM ac_mo_report_process\n"
                "           WHERE EXECUTE_TYPE = 5 AND (IS_CANCEL IS NULL OR IS_CANCEL <> 1)\n"
                "           GROUP BY MO_ID, OP_SEQ, OP_ID) r\n"
                "  ON d.MO_ID = r.MO_ID AND d.OP_SEQ = r.OP_SEQ AND d.OP_ID = r.OP_ID\n"
                "ORDER BY d.DISPATCH_START_TIME DESC\n"
                "LIMIT 50"
            )
        return sql, ["派工完成率：派工任务表(dispatch_record) 按 工单+工序 对齐报工完成量（结束加工），日期对不上自动落历史累计"]
    if iid == "material":
        # 物料：系统无库存，只有消耗记录（上料 use_log / 耗料 consume_detail / 领料）
        # 口径（2026-08-06 客户确认）：无库存/结存概念，"上料量-耗料量=结存"不成立
        d1, d2 = t["date_from"], t["date_to"]
        is_use = any(k in question for k in ["上料", "领料", "用料", "发料"])
        tbl_alias = "ul" if is_use else "cd"
        # 补充提取物料编码（形如 SPS0-02 / DQ001 / FWL-01，中文边界用负向断言）
        if not ent.get("product"):
            m = re.search(r"(?<![A-Za-z0-9])([A-Za-z]{1,8}\d{0,4}[-_]\d{1,6}[A-Za-z0-9_\-]*)(?![A-Za-z0-9])", question)
            if m:
                ent["product"] = m.group(1)
        ma = f" AND {tbl_alias}.MA_ID = '{ent['product']}'" if ent.get("product") else ""
        if is_use:
            sql = (
                "SELECT ul.MA_ID AS 物料, mb.MATERIAL_NAME AS 物料名,\n"
                "       COUNT(*) AS 上料笔数, SUM(ul.USE_QTY) AS 上料总量,\n"
                "       COUNT(DISTINCT ul.MO_ID) AS 涉及工单, COUNT(DISTINCT ul.BATCH_ID) AS 批号数\n"
                "FROM pl_mo_material_use_log ul\n"
                "LEFT JOIN ma_basis mb ON ul.MA_ID = mb.MA_ID\n"
                "WHERE 1=1{ma}\n"
                "GROUP BY ul.MA_ID, mb.MATERIAL_NAME\n"
                "ORDER BY 上料总量 DESC"
            ).format(ma=ma)
        else:
            sql = (
                "SELECT cd.MA_ID AS 物料, mb.MATERIAL_NAME AS 物料名,\n"
                "       COUNT(*) AS 耗料笔数, SUM(cd.USAGE_QTY) AS 耗料总量,\n"
                "       COUNT(DISTINCT cd.MO_ID) AS 涉及工单, COUNT(DISTINCT cd.BATCH_ID) AS 批号数\n"
                "FROM ma_consume_detail cd\n"
                "LEFT JOIN ma_basis mb ON cd.MA_ID = mb.MA_ID\n"
                "WHERE 1=1{ma}\n"
                "GROUP BY cd.MA_ID, mb.MATERIAL_NAME\n"
                "ORDER BY 耗料总量 DESC"
            ).format(ma=ma)
        if d1 and d2:
            # 有明确时间范围 → 加时间过滤
            d2p = (d2 + datetime.timedelta(days=1)).isoformat()
            tcol = "ul.CREATE_TIME" if is_use else "cd.CREATE_TIME"
            sql = sql.replace("WHERE 1=1", f"WHERE {tcol} >= '{d1.isoformat()} 00:00:00' AND {tcol} < '{d2p} 00:00:00'", 1)
        return sql, ["物料：系统无库存，只有消耗记录（上料/耗料）；无时间范围时查历史累计"]
    if iid not in tpl:
        return None, ["未命中资产且无兜底模板，请补充评测样例或查询口径"]
    d1, d2 = t["date_from"], t["date_to"]
    if iid == "quality_bad":
        prod, eq = "", ""  # 不良表无产品/设备列
    else:
        prod = f" AND pm.MA_ID = '{ent['product']}'" if ent.get("product") else ""
        eq = f" AND r.EQ_ID = '{ent['equipment']}'" if ent.get("equipment") else ""
    sql = tpl[iid].format(d1=d1, d2=d2, d2_plus=d2 + datetime.timedelta(days=1), prod=prod, eq=eq)
    return sql, [f"资产库未命中，基于 schema 表结构生成（{iid} 兜底模板）"]

# ---------------- 主流程 ----------------
def generate(question):
    out = {"question": question}
    t0, t1, tname = parse_time(question)
    ent = parse_entity(question)
    iid, score = match_intent(question)
    compare = any(k in question for k in ["比昨天", "对比", "环比", "同比", "相比", "和昨天"])
    why = any(k in question for k in ["为什么", "原因", "下降", "异常", "怎么回事"])

    out["parse"] = {
        "时间": tname or "未指定",
        "实体": ent or "未指定",
        "指标意图": iid,
        "对比": "是" if compare else "否",
        "归因": "是" if why else "否",
    }

    # 委外供应商绩效(2026-08-17 新增):良品率+准时率+逾期明细,固定口径
    if iid == "outsource_supplier":
        out["results"] = supplier_perf_results(question, t0, t1)
        out["note"] = ("委外供应商绩效:良品率=验收合格/(合格+验退)回货口径;"
                       "准时率=已完成单(状态3)中最后一批回货日期<=要求回货日期的占比;"
                       "同单可分批回货,按单取最后一批")
        return out

    params = {"date_from": t0, "date_to": t1, **ent}
    results = []

    if why and iid in ("output_summary", "mo_progress"):
        # 归因：输出四维度检查 SQL
        results.append({"tag": "归因检查 · 设备故障/点检", "sql": (
            "SELECT eq.EQ_NAME, ec.CHECK_DATE, ec.CHECK_FREQUENCY\n"
            "FROM eq_check_record ec LEFT JOIN eq_basis eq ON ec.EQ_ID = eq.EQ_ID\n"
            "WHERE ec.CHECK_DATE >= '{d1} 00:00:00' AND ec.CHECK_DATE < '{d2p} 00:00:00';".format(
                d1=t0, d2p=t1 + datetime.timedelta(days=1)))})
        results.append({"tag": "归因检查 · 设备状态切换(停机/稼动)", "sql": (
            "SELECT es.EQ_ID, es.EQ_N_STATUS, es.START_TIME\n"
            "FROM eq_status es\n"
            "WHERE es.START_TIME >= '{d1} 00:00:00' AND es.START_TIME < '{d2p} 00:00:00';".format(
                d1=t0, d2p=t1 + datetime.timedelta(days=1)))})
        results.append({"tag": "归因检查 · 工单状态堆积", "sql": (
            "SELECT MO_ID, OP_SEQ, TO_BE_STARTED_QTY, PENDING_COMPLETION_QTY, IS_PAUSE\n"
            "FROM ac_lot_status WHERE TO_BE_STARTED_QTY > 0 ORDER BY TO_BE_STARTED_QTY DESC LIMIT 20;" )})
        results.append({"tag": "归因检查 · 不良/报废", "sql": (
            "SELECT ierr.SOURCE_TYPE AS 来源,\n"
            "       COALESCE(dcd.COLLECTION_CHOICE_NAME, dcd2.COLLECTION_NAME, '未指定') AS 不良原因,\n"
            "       COALESCE(mob1.OP_NAME, mob2.OP_NAME, '') AS 工序,\n"
            "       SUM(ierr.QTY) AS 不良数\n"
            "FROM in_except_reason_record ierr\n"
            "LEFT JOIN da_collection_choice_detail dcd ON ierr.BAD_REASON = dcd.ID\n"
            "LEFT JOIN da_collection_data dcd2 ON ierr.BAD_REASON = dcd2.ID\n"
            "LEFT JOIN in_spc_data spc ON ierr.SOURCE_TYPE = 2 AND ierr.PARENT_ID = spc.ID\n"
            "LEFT JOIN ac_mo_report_process mr ON ierr.SOURCE_TYPE = 1 AND ierr.PARENT_ID = mr.ID\n"
            "LEFT JOIN me_op_basis mob1 ON spc.OP_ID = mob1.OP_ID\n"
            "LEFT JOIN me_op_basis mob2 ON mr.OP_ID = mob2.OP_ID\n"
            "WHERE ierr.CREATE_TIME >= '{d1} 00:00:00' AND ierr.CREATE_TIME < '{d2p} 00:00:00'\n"
            "GROUP BY ierr.SOURCE_TYPE, COALESCE(dcd.COLLECTION_CHOICE_NAME, dcd2.COLLECTION_NAME, '未指定'), "
            "COALESCE(mob1.OP_NAME, mob2.OP_NAME, '')\n"
            "ORDER BY 不良数 DESC LIMIT 20;".format(
                d1=t0, d2p=t1 + datetime.timedelta(days=1)))})
        out["results"] = results
        out["note"] = "归因模式：并行检查四个维度，命中后按影响程度排序回答"
        return out

    if not iid:
        out["results"] = [{"tag": "未识别意图", "sql": None, "warns": ["无法识别指标，请补充评测样例"]}]
        return out

    if compare:
        # 对比：当前 + 基准 两个 SQL；产量/不良/物料/派工 一律用底层表（时间过滤最准）
        if iid in ("output_summary", "quality_bad", "material", "dispatch_rate"):
            cur, w1 = fallback_sql(iid, ent, {"date_from": t0, "date_to": t1}, question)
            bd = (t0 - datetime.timedelta(days=1)) if t0 else None
            bs, w2 = fallback_sql(iid, ent, {"date_from": bd, "date_to": bd}, question)
            tagname = {"output_summary": "ac_mo_report_process", "quality_bad": "in_except_reason_record",
                       "material": "ma_consume_detail/use_log", "dispatch_rate": "dispatch_record"}[iid]
            results.append({"tag": f"对比 · {tname}（底层表 {tagname}）", "sql": cur, "warns": w1})
            results.append({"tag": f"对比 · 基准日（底层表）", "sql": bs, "warns": w2})
        else:
            vname = pick_view(iid, ent)
            base_sql = SQL_MAP.get(vname)
            if not base_sql:
                sql, warns = fallback_sql(iid, ent, {"date_from": t0, "date_to": t1}, question)
                if sql:
                    results.append({"tag": "schema 兜底", "sql": sql, "warns": warns})
                out["results"] = results
                return out
            cur, warns1 = param_sql(base_sql, vname, params)
            bd = (t0 - datetime.timedelta(days=1)) if t0 and t1 else None
            base_params = {"date_from": bd, "date_to": bd, **ent}
            bsql, warns2 = param_sql(base_sql, vname, base_params)
            results.append({"tag": f"对比 · {tname}（视图 {vname}）", "sql": cur, "warns": warns1})
            results.append({"tag": f"对比 · 基准日（视图 {vname}）", "sql": bsql, "warns": warns2})
        out["note"] = "对比：两段 SQL 分别在应用层取数后计算涨跌幅（当前 - 基准）/基准"
    else:
        # 产量/不良/派工完成率/物料 一律走底层表（准确 + 口径可控）
        if iid in ("output_summary", "quality_bad", "dispatch_rate", "material"):
            sql, warns = fallback_sql(iid, ent, {"date_from": t0, "date_to": t1}, question)
            tag = {"output_summary": "底层表 ac_mo_report_process（按产品+时间）",
                   "quality_bad": "底层表 in_except_reason_record（来源分支 JOIN）",
                   "dispatch_rate": "派工完成率（派工表 vs 报工表累计对齐）",
                   "material": "物料消耗记录（上料 use_log / 耗料 consume_detail，无库存口径）"}[iid]
            results.append({"tag": tag, "sql": sql, "warns": warns})
        else:
            vname = pick_view(iid, ent)
            base_sql = SQL_MAP.get(vname)
            if base_sql:
                sql, warns = param_sql(base_sql, vname, params)
                results.append({"tag": f"视图 {vname}", "sql": sql, "warns": warns})
            else:
                sql, warns = fallback_sql(iid, ent, {"date_from": t0, "date_to": t1}, question)
                if sql:
                    results.append({"tag": "schema 兜底", "sql": sql, "warns": warns})
                else:
                    results.append({"tag": "无匹配", "sql": None, "warns": warns})
    out["results"] = results
    return out

def fallback_pair(iid, ent, t0, t1, compare):
    return {"results": [], "note": "资产为占位且无兜底模板"}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    questions = sys.argv[1:] or ["A产品今天的产量是多少"]
    for q in questions:
        out = generate(q)
        print("=" * 66)
        print(f"问题：{out['question']}")
        print("解析：", json.dumps(out["parse"], ensure_ascii=False))
        print("-" * 66)
        for r in out.get("results", []):
            print(f"[{r['tag']}]")
            if r.get("sql"):
                print(r["sql"])
            for w in r.get("warns", []):
                print(f"  ⚠ {w}")
            print()
        if out.get("note"):
            print(f"注：{out['note']}")
        print()

if __name__ == "__main__":
    main()
