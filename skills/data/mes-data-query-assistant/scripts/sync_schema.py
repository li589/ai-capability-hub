# -*- coding: utf-8 -*-
"""
Schema 同步工具：对比数据库实际表结构与知识库 data/schema.json，输出差异并按命名规范自动入库业务表。

用途：系统表结构会演进 —— 本工具负责"对准字段"：
  1. 连库读取 information_schema（只读，无需业务权限）
  2. 与知识库 schema.json 对比，按【数据库命名规范】智能分类差异：
     - 【业务前缀表】符合命名规范的（ac/ma/me/eq/en/pl/pcq/in/op/sa/wo/di/tblusr/bossapp/dataie/sys_integrate/...）
         → 自动入库 schema.json + 白名单（cn 默认来自 COLUMN_COMMENT + 表名推断）
     - 【模糊表】非业务前缀、非框架 → 待用户在 schema_pending.json 确认 cn
     - 【审计字段】CREATOR/EDITOR/CREATE_TIME 等 ABP 框架字段 → --apply 自动补全
     - 【框架/系统表】app*/event*/meta*/buffer*/tb_*/saga*/momevent/... → 跳过
     - 【缺失表/字段】提示核实（可能删除/改名/截断）
  3. 用户确认后 --apply 回写：自动入库业务表 + 合并 pending 模糊表 + 自动补审计字段

用法（必须用 venv python 跑，含 pymysql）：
  python sync_schema.py --check         # 对比并生成报告 + pending（只含模糊表）
  python sync_schema.py --apply         # 自动入库业务前缀表 + 合并 pending 模糊表 + 补审计字段
  python sync_schema.py --align         # 全面对齐（以数据库为准）：改名合并 + 清理缺失字段/表 + 自动入库
  python sync_schema.py --list          # 只打印差异汇总（含业务/模糊/框架三类）
"""
import sys, os, json, re, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CFG_PATH = os.path.join(BASE, "config.json")
SCHEMA_PATH = os.path.join(DATA, "schema.json")
ALLOWED_PATH = os.path.join(DATA, "allowed_tables.json")
PENDING_PATH = os.path.join(DATA, "schema_pending.json")
DIFF_PATH = os.path.join(DATA, "schema_diff.md")

SAMPLE_SKIP_TYPES = ("TEXT", "BLOB", "JSON", "LONGTEXT", "MEDIUMTEXT", "LONGBLOB", "GEOMETRY")

# ---- ABP 框架标准审计字段（含义固定，自动补全，无需确认）----
AUDIT_FIELD_CN = {
    "CREATOR": "创建人", "CREATOR_NAME": "创建人姓名", "CREATOR_ID": "创建人ID",
    "CREATE_TIME": "创建时间", "CREATE_BY": "创建人", "CREATE_BY_NAME": "创建人姓名",
    "EDITOR": "编辑人", "EDITOR_NAME": "编辑人姓名", "EDITOR_ID": "编辑人ID",
    "EDIT_TIME": "编辑时间", "UPDATE_TIME": "更新时间", "UPDATE_BY": "更新人",
    "REMARK": "备注", "IS_DELETED": "是否删除", "TENANT_ID": "租户ID",
    "UNIT_ID": "单位ID", "ORG_ID": "组织ID", "SORT": "排序号",
}

# ---- 业务表前缀白名单（命名规范定义的核心业务前缀，符合即业务表）----
# 来源：作业编号规则图 + 数据库表命名规则 + 现有 schema 116 表的实际分布
BUSINESS_PREFIXES = (
    # 计划系列（pc 系列）
    "pcp_", "pcd_", "pca_", "pcb_", "pcs_", "pcq_",
    # 执行/报工
    "ac_",
    # 物料
    "ma_",
    # 方法/工艺（me_ 含 op/batch/dispatch/sop/collect/scheduling/sn/andon/mo 等子表）
    "me_",
    # 设备/模具/点检/维保
    "eq_",
    # 环境（日历/班次/标签/培训/库位/规则）
    "en_",
    # 计划/工单（pl_mo 系列）
    "pl_",
    # 质检
    "in_",
    # 运营/操作
    "op_",
    # 销售/订单/客户
    "sa_",
    # 工单/排工/工资/职责
    "wo_",
    # 数据集成/外协
    "di_",
    # 业务 app
    "bossapp_",
    # 数据导入导出
    "dataie_",
    # 集成业务
    "sys_integrate_",
    # 培训课程
    "env_course",
    # 主数据（人员/部门/职称/技能）
    "tblusr", "tblusj", "tblusd", "tblusk", "tblusk_",
    # 模具命名（图中：MOLD → MOL）
    "mol_", "mold_",
    # 产品图纸/技术资料
    "tm_",
)

# ---- ABP 框架/系统表特征（不进知识库）----
FRAMEWORK_MARKERS = (
    "appdetail", "apppage", "baseevent", "buffer", "componentpermission", "detailentity",
    "directoryentity", "dingtalkresponse", "event", "extendedindex", "filepermission",
    "genericmeta", "logentity", "memorybuffer", "metabase", "metarequired", "metaversion",
    "momevent", "saga", "sysschedulelog", "tb_", "typeless", "unit_invoked",
    "user_preference", "flow_code", "tcc_d",
)


def is_business_table(tname):
    """符合数据库命名规范的业务表：前缀在白名单内"""
    t = tname.lower()
    return t.startswith(BUSINESS_PREFIXES)


def is_framework_table(tname):
    t = tname.lower()
    return any(t.startswith(m) or m in t for m in FRAMEWORK_MARKERS)


def is_audit_field(cname):
    return cname.upper() in AUDIT_FIELD_CN


def load_cfg():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["database"]


def connect():
    import pymysql
    db = load_cfg()
    return pymysql.connect(
        host=db["host"], port=db["port"], user=db["user"], password=db["password"],
        database=db["dbname"], charset="utf8mb4", connect_timeout=10, read_timeout=30,
    )


def fetch_db_schema(conn, dbname):
    out = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, "
            "COLUMN_COMMENT FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME, ORDINAL_POSITION", (dbname,))
        for tname, cname, ctype, nullable, ckey, ccomment in cur.fetchall():
            t = out.setdefault(tname.lower(), [])
            t.append({
                "name": cname,
                "type": ctype.split("(")[0].upper(),
                "len": re.sub(r"^\w+", "", ctype) or "",
                "nullable": "是" if nullable == "YES" else "否",
                "pk": "主键" if ckey == "PRI" else "",
                "default": "",
                "lc_name": cname,
                "note": (ccomment or "").strip(),
            })
    return out


def fetch_samples(conn, tbl, cols, limit=5):
    samples = {}
    for c in cols:
        if any(sk in c["type"].upper() for sk in SAMPLE_SKIP_TYPES):
            samples[c["name"]] = []
            continue
        try:
            q = f"SELECT DISTINCT `{c['name']}` FROM `{tbl}` WHERE `{c['name']}` IS NOT NULL LIMIT {limit}"
            with conn.cursor() as cur:
                cur.execute(q)
                rows = cur.fetchall()
            vals = []
            for r in rows:
                v = r[0]
                s = str(v)
                if len(s) > 40:
                    s = s[:40] + "…"
                vals.append(s)
            samples[c["name"]] = vals
        except Exception:
            samples[c["name"]] = []
    return samples


def compare(live, schema):
    new_tables, new_cols, gone_cols, gone_tables = {}, {}, {}, {}
    live_keys = {k.lower() for k in live}
    schema_keys = {k.lower() for k in schema}

    for t in sorted(live_keys - schema_keys):
        new_tables[t] = live[t]
    for t in sorted(schema_keys - live_keys):
        gone_tables[t] = schema[t]

    for t in sorted(live_keys & schema_keys):
        live_names = {c["name"].lower() for c in live[t]}
        schema_names = {c["name"].lower() for c in schema[t]["fields"]}
        nc = [c for c in live[t] if c["name"].lower() not in schema_names]
        if nc:
            new_cols[t] = nc
        gc = [c["name"] for c in schema[t]["fields"] if c["name"].lower() not in live_names]
        if gc:
            gone_cols[t] = gc
    return new_tables, new_cols, gone_cols, gone_tables


def split_diff(new_tables, new_cols):
    """差异分类：业务前缀(自动入库) / 模糊(待确认) / 框架(跳过) / 审计字段(自动补)"""
    biz_tables = {t: c for t, c in new_tables.items() if is_business_table(t)}
    fw_tables = {t: c for t, c in new_tables.items() if is_framework_table(t)}
    fuzzy_tables = {t: c for t, c in new_tables.items()
                    if t not in biz_tables and t not in fw_tables}
    biz_cols, audit_cols = {}, {}
    for t, cols in new_cols.items():
        for c in cols:
            (audit_cols if is_audit_field(c["name"]) else biz_cols).setdefault(t, []).append(c)
    return biz_tables, fuzzy_tables, fw_tables, biz_cols, audit_cols


def _default_field_cn(c):
    return (c.get("note") or c["name"]).strip()


def build_pending(live, fuzzy_tables, biz_cols, samples_map):
    """生成待确认文件：模糊新表(整表) + 业务新增字段(留 cn 待补)"""
    def fmt_fields(cols, tbl):
        out = []
        for c in cols:
            out.append({
                "name": c["name"],
                "type": c["type"] + c.get("len", ""),
                "pk": c["pk"],
                "cn": _default_field_cn(c),
                "comment": c["note"],
                "sample": samples_map.get(tbl, {}).get(c["name"], []),
            })
        return out

    pend = {"_说明": "本清单只含【模糊表】(非业务前缀也非框架)，业务前缀表已在 --apply 时自动入库；请为模糊表填 cn_name + 字段 cn 后运行 --apply", "新表": {}, "新增字段": {}}
    for t, cols in fuzzy_tables.items():
        pend["新表"][t] = {
            "cn_name": "", "category": "模糊新表(待确认)",
            "fields": fmt_fields(cols, t),
        }
    for t, cols in biz_cols.items():
        pend["新增字段"][t] = fmt_fields(cols, t)
    return pend


def auto_audit_fields(schema, audit_cols):
    added = 0
    for t, cols in audit_cols.items():
        if t not in schema:
            continue
        exist = {f["name"].lower() for f in schema[t]["fields"]}
        for c in cols:
            if c["name"].lower() in exist:
                continue
            cn = AUDIT_FIELD_CN.get(c["name"].upper()) or c["note"] or c["name"]
            schema[t]["fields"].append(_to_schema_field(c, cn))
            exist.add(c["name"].lower())
            added += 1
    return added


def auto_business_tables(schema, biz_tables):
    """自动入库业务前缀新表：cn_name 默认从表名推断"""
    added = []
    for t, cols in biz_tables.items():
        if t in schema:
            continue
        prefix_end = 0
        for p in BUSINESS_PREFIXES:
            if t.startswith(p):
                prefix_end = len(p)
                break
        rest = t[prefix_end:].replace("_", " ").strip()
        cn_name = rest.upper() if not rest else f"{rest}(业务前缀表)"
        fields = [_to_schema_field(c, _default_field_cn(c)) for c in cols]
        schema[t] = {
            "cn_name": cn_name, "upper": t.upper(),
            "category": "新增业务表(自动入库)",
            "origin": "sync_schema 业务前缀自动入库", "origin_mean": "",
            "fields": fields,
        }
        added.append(t)
    return added


def auto_business_columns(schema, biz_cols):
    """业务新增字段：直接用数据库注释补进 schema"""
    added = 0
    for t, cols in biz_cols.items():
        if t not in schema:
            continue
        exist = {f["name"].lower() for f in schema[t]["fields"]}
        for c in cols:
            if c["name"].lower() in exist:
                continue
            schema[t]["fields"].append(_to_schema_field(c, _default_field_cn(c)))
            exist.add(c["name"].lower())
            added += 1
    return added


def apply_pending():
    """应用：① 自动入库业务前缀表 + 业务新字段 ② 自动补审计字段 ③ 合并 pending 模糊表"""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(ALLOWED_PATH, "r", encoding="utf-8") as f:
        allowed = set(json.load(f))

    biz_tables, biz_cols, audit_cols, fuzzy_tables = _detect_pending_diff(schema)

    added_biz_tables = auto_business_tables(schema, biz_tables)
    for t in added_biz_tables:
        allowed.add(t)
    added_biz_cols = auto_business_columns(schema, biz_cols)
    added_audit = auto_audit_fields(schema, audit_cols)

    added_fuzzy = 0
    if os.path.exists(PENDING_PATH):
        with open(PENDING_PATH, "r", encoding="utf-8") as f:
            pend = json.load(f)
        for t, spec in pend.get("新表", {}).items():
            if t in schema:
                continue
            fields = [_to_schema_field(cf, cf.get("cn")) for cf in spec.get("fields", [])]
            schema[t] = {
                "cn_name": spec.get("cn_name") or t, "upper": t.upper(),
                "category": spec.get("category") or "模糊表",
                "origin": "sync_schema 模糊表确认入库", "origin_mean": "",
                "fields": fields,
            }
            allowed.add(t)
            added_fuzzy += 1
        for t, cols in pend.get("新增字段", {}).items():
            if t not in schema:
                continue
            exist = {f["name"].lower() for f in schema[t]["fields"]}
            for cf in cols:
                if cf["name"].lower() in exist:
                    continue
                schema[t]["fields"].append(_to_schema_field(cf, cf.get("cn")))
                exist.add(cf["name"].lower())
                added_fuzzy += 1

    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=1)
    with open(ALLOWED_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(allowed), f, ensure_ascii=False, indent=1)
    print(f"✅ 已更新 schema.json:")
    print(f"   • 业务前缀表(自动入库): {len(added_biz_tables)} 张")
    if added_biz_tables:
        print(f"     {', '.join(added_biz_tables)}")
    print(f"   • 业务新增字段(自动补): {added_biz_cols} 个")
    print(f"   • 审计字段(自动补): {added_audit} 个")
    print(f"   • 模糊表/字段(从 pending 合并): {added_fuzzy} 项")
    print(f"   allowed_tables.json 白名单已同步(当前 {len(allowed)} 表)")


def align_schema():
    """全面对齐（以数据库为准）：
    ① 改名合并：知识库旧表名 → 库中相似表名（截断/改名，相似度>=0.9）
    ② 清理缺失字段：知识库有但库中已无的字段（如旧审计字段 create_by 等）
    ③ 清理缺失表：知识库有但库中已无的表
    ④ 自动入库业务前缀新表 + 业务新字段 + 审计字段
    ⑤ 同步 allowed_tables.json 白名单
    """
    import difflib
    db = load_cfg()
    conn = connect()
    try:
        live = fetch_db_schema(conn, db["dbname"])
    finally:
        conn.close()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(ALLOWED_PATH, "r", encoding="utf-8") as f:
        allowed = set(json.load(f))

    new_tables, new_cols, gone_cols, gone_tables = compare(live, schema)
    biz_tables, fuzzy_tables, fw_tables, biz_cols, audit_cols = split_diff(new_tables, new_cols)

    print("🔄 全面对齐（以数据库为准）…")

    # ① 改名合并：缺失表 → 库中相似表
    live_keys = sorted(live.keys())
    renamed = {}  # 旧表名 -> 新表名
    for t in sorted(gone_tables):
        best, best_ratio = None, 0
        for lk in live_keys:
            r = difflib.SequenceMatcher(None, t, lk).ratio()
            if r > best_ratio:
                best, best_ratio = lk, r
        if best and best_ratio >= 0.9:
            renamed[t] = best
    for old, new in renamed.items():
        print(f"   🔀 改名合并: {old} → {new}")
        # 字段合并：旧表字段并入新表（去重），旧表删除
        old_fields = {f["name"].lower(): f for f in schema.get(old, {}).get("fields", [])}
        if new in schema:
            exist = {f["name"].lower() for f in schema[new]["fields"]}
            for nm, f in old_fields.items():
                if nm not in exist:
                    schema[new]["fields"].append(f)
                    exist.add(nm)
        else:
            # 新表名不在 schema（可能被当业务新表自动入库了，或确实缺失）→ 直接用旧表定义
            if new in live:
                schema[new] = schema.get(old, {
                    "cn_name": new, "upper": new.upper(),
                    "category": "改名合并表", "origin": "sync_schema 改名合并", "origin_mean": "",
                    "fields": [],
                })
        schema.pop(old, None)
        allowed.discard(old)
        allowed.add(new)

    # ② 清理缺失字段（以库为准：知识库有但库中已无的字段删除）
    removed_cols = 0
    for t, cols in gone_cols.items():
        if t not in schema:
            continue
        keep = [f for f in schema[t]["fields"] if f["name"].lower() not in set(cols)]
        removed_cols += len(schema[t]["fields"]) - len(keep)
        schema[t]["fields"] = keep
    if removed_cols:
        print(f"   🗑️ 清理缺失字段: {removed_cols} 个（知识库有库中已无，如旧审计字段 create_by/update_by 等）")

    # ③ 清理缺失表（库中已无的业务表，从知识库移除）
    removed_tables = 0
    for t in sorted(gone_tables):
        if t in renamed:
            continue  # 已改名合并
        schema.pop(t, None)
        allowed.discard(t)
        removed_tables += 1
    if removed_tables:
        print(f"   🗑️ 清理缺失表: {removed_tables} 张（库中已不存在）")

    # ④ 自动入库业务前缀新表/字段 + 审计字段
    added_biz_tables = auto_business_tables(schema, biz_tables)
    for t in added_biz_tables:
        allowed.add(t)
    added_biz_cols = auto_business_columns(schema, biz_cols)
    added_audit = auto_audit_fields(schema, audit_cols)

    # ⑤ 写回
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=1)
    with open(ALLOWED_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(allowed), f, ensure_ascii=False, indent=1)

    print(f"\n✅ 对齐完成:")
    print(f"   🔀 改名合并: {len(renamed)} 张表")
    print(f"   ➕ 业务前缀表自动入库: {len(added_biz_tables)} 张")
    if added_biz_tables:
        print(f"     {', '.join(added_biz_tables)}")
    print(f"   ➕ 业务新字段自动补: {added_biz_cols} 个 | 审计字段: {added_audit} 个")
    print(f"   🗑️ 清理缺失字段: {removed_cols} 个 | 缺失表: {removed_tables} 张")
    print(f"   📊 schema.json 现有 {len(schema)} 表 | allowed_tables 白名单 {len(allowed)} 表")
    if fuzzy_tables:
        print(f"   ⚠️ 仍有 {len(fuzzy_tables)} 张模糊表（非业务前缀也非框架），需在 schema_pending.json 确认后 --apply")


def _detect_pending_diff(schema):
    """重连数据库检测当前业务/模糊/审计差异"""
    db = load_cfg()
    conn = connect()
    try:
        live = fetch_db_schema(conn, db["dbname"])
    finally:
        conn.close()
    new_tables, new_cols, _, _ = compare(live, schema)
    biz_tables, fuzzy_tables, _, biz_cols, audit_cols = split_diff(new_tables, new_cols)
    return biz_tables, biz_cols, audit_cols, fuzzy_tables


def _to_schema_field(cf, cn):
    note_val = cf.get("note", "")
    if not isinstance(note_val, str):
        note_val = ""
    cn_val = cn if isinstance(cn, str) and cn else (note_val or cf["name"])
    return {
        "name": cf["name"],
        "cn": cn_val,
        "type": cf["type"],
        "len": cf.get("len", ""),
        "nullable": "是",
        "pk": cf.get("pk") or "",
        "default": "",
        "lc_name": cf["name"].upper(),
        "note": note_val,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    mode = sys.argv[1]
    if mode == "--apply":
        apply_pending()
        return
    if mode == "--align":
        align_schema()
        return

    db = load_cfg()
    try:
        conn = connect()
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("   请检查 config.json 的 database 配置")
        return
    live = fetch_db_schema(conn, db["dbname"])
    conn.close()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    new_tables, new_cols, gone_cols, gone_tables = compare(live, schema)
    biz_tables, fuzzy_tables, fw_tables, biz_cols, audit_cols = split_diff(new_tables, new_cols)

    print(f"📊 Schema 对比(知识库 {len(schema)} 表 vs 数据库 {len(live)} 表)")
    print(f"\n   ✅ 业务前缀新表(按命名规范,自动入库): {len(biz_tables)} 张")
    for t in biz_tables:
        print(f"      + {t}({len(biz_tables[t])} 字段)")
    print(f"\n   ❓ 模糊新表(非业务前缀也非框架,需确认): {len(fuzzy_tables)} 张")
    for t in fuzzy_tables:
        print(f"      ? {t}({len(fuzzy_tables[t])} 字段)")
    print(f"\n   🧩 框架/系统新表(跳过): {len(fw_tables)} 张(app*/event*/meta*/buffer*/tb_* 等)")
    print(f"\n   ➕ 业务新增字段(自动补): {len(biz_cols)} 张表")
    for t, cols in biz_cols.items():
        print(f"      + {t}: {len(cols)} 个 → {', '.join(c['name'] for c in cols[:6])}")
    print(f"\n   ⚙️ 审计字段(自动补): {len(audit_cols)} 张表")
    print(f"\n   🗑️ 缺失字段: {len(gone_cols)} 张表 | 🚫 缺失表: {len(gone_tables)} 张")

    if mode == "--list":
        return

    print("\n正在抽取样例值(仅 SELECT LIMIT 5,只读)…")
    need_tables = set(biz_tables) | set(fuzzy_tables) | set(biz_cols)
    samples_map = {}
    conn = connect()
    for t in need_tables:
        tcols = biz_tables.get(t, []) + fuzzy_tables.get(t, []) + biz_cols.get(t, [])
        try:
            samples_map[t] = fetch_samples(conn, t, tcols)
        except Exception as e:
            print(f"   警告: 取 {t} 样例失败: {e}")
    conn.close()

    pend = build_pending(live, fuzzy_tables, biz_cols, samples_map)
    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(pend, f, ensure_ascii=False, indent=1)

    with open(DIFF_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Schema 差异报告({datetime.date.today()})\n\n")
        f.write(f"- 知识库 {len(schema)} 表 vs 数据库 {len(live)} 表\n")
        f.write(f"- 业务前缀新表(自动入库) {len(biz_tables)} / 模糊新表(待确认) {len(fuzzy_tables)} / 框架新表 {len(fw_tables)} / 业务新字段 {len(biz_cols)} / 审计字段 {len(audit_cols)} / 缺失字段 {len(gone_cols)} / 缺失表 {len(gone_tables)}\n\n")
        if biz_tables:
            f.write("## 一、业务前缀新表(按命名规范自动入库)\n\n")
            for t, cols in biz_tables.items():
                f.write(f"### {t}\n")
                for c in cols:
                    s = "、".join(samples_map.get(t, {}).get(c["name"], [])) or "—"
                    f.write(f"- `{c['name']}` {c['type']}{c.get('len','')}｜注释:{c['note'] or '无'}｜样例:{s}\n")
                f.write("\n")
        if fuzzy_tables:
            f.write("## 二、模糊新表(需确认含义)\n\n")
            for t, cols in fuzzy_tables.items():
                f.write(f"### {t}\n")
                for c in cols:
                    s = "、".join(samples_map.get(t, {}).get(c["name"], [])) or "—"
                    f.write(f"- `{c['name']}` {c['type']}{c.get('len','')}｜注释:{c['note'] or '无'}｜样例:{s}\n")
                f.write("\n")
        if biz_cols:
            f.write("## 三、业务新增字段(自动补,cn 取数据库注释)\n\n")
            for t, cols in biz_cols.items():
                f.write(f"- {t}: {', '.join(c['name'] for c in cols)}\n")
            f.write("\n")
        if audit_cols:
            f.write("## 四、审计字段(自动补)\n\n")
            for t, cols in audit_cols.items():
                f.write(f"- {t}: {', '.join(c['name'] for c in cols)}\n")
            f.write("\n")
        if fw_tables:
            f.write("## 五、框架/系统新表(跳过)\n\n")
            f.write(", ".join(sorted(fw_tables.keys())) + "\n\n")
        if gone_cols or gone_tables:
            f.write("## 六、缺失项(可能删除/改名)\n\n")
            for t, cs in gone_cols.items():
                f.write(f"- {t} 缺字段: {', '.join(cs)}\n")
            for t in gone_tables:
                f.write(f"- 缺表: {t}\n")
            f.write("\n")
        f.write("---\n")
        f.write("- `--apply` 自动入库:业务前缀表 + 业务新字段 + 审计字段\n")
        f.write("- 模糊表仍需编辑 `schema_pending.json` 填 cn_name/cn,再 --apply\n")

    print(f"\n📄 差异报告: {DIFF_PATH}")
    print(f"📝 待确认清单(仅模糊表): {PENDING_PATH}")
    print(f"\n👉 直接运行 --apply 可自动入库业务前缀表 + 业务新字段 + 审计字段;模糊表仍需先在 pending.json 填 cn")


if __name__ == "__main__":
    main()