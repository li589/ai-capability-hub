# 供应商绩效 SQL 整理（委外发货前统计说明）

> ⚠️ **数据源说明（2026-08-17 用户确认）**：本技能运行时**不再读数据库**——供应商绩效统一走接口 `getOutSourceDash`（近一年），可委外清单走 `getCanOutsourceList`，待回货清单走 `getOutSourceList`。
> 本文档的 SQL 仅作为**口径参考与开发历史**（当时基于 `emes_dev` 只读账号验证），如需还原口径可直接看 SQL，但技能脚本已全部接口化。
> 整理日期：2026-08-17 · 所有 SQL 均已在真实库执行验证
> 规范：**别名一律大写英文，中文含义用 SQL 注释（-- 中文）标注**

---

## 一、统计口径（重要）

| 指标 | 口径 | 说明 |
|------|------|------|
| **良品率** | `ΣOK_QTY / Σ(OK_QTY + NG_QTY) × 100%` | 委外回货验收口径，来自 `di_outsource_back_process`（回货时记录验收合格/验退数量） |
| **准时率** | 已完成单（状态=3）中 `最后一批回货日期 ≤ 要求回货日期` 的单数占比 | 按**单**聚合（同一委外单可分批回货，取最后一批回货时间） |
| 准时判定 | `DATE(回货时间) <= DATE(DELIVERY_DATE)` | DELIVERY_DATE 存为当天 00:00，按日期比较——**当天内回货即算准时** |
| 委外单状态 | `1=委外中 2=部分回货 3=全部回货` | `di_outsource_send_basis.OUTSOURCE_STATUS` |
| 待回货数量 | `ΣSEND_QTY − ΣBACK_QTY` | 发货明细 − 回货记录 |

**关联关系**：
- `di_outsource_send_basis`（委外发货主表：OUTSOURCE_ID / SUPPLIER_ID / OUTSOURCE_STATUS / DELIVERY_DATE）
- `di_outsource_send_detail`（发货明细：PARENT_ID→basis.ID，SEND_QTY / MO_ID / OP_SEQ / OP_ID）
- `di_outsource_back_process`（回货记录：OUTSOURCE_ID / BACK_QTY / OK_QTY / NG_QTY / CREATE_TIME）
- `ou_supplier_basis`（供应商：SUPPLIER_ID / SUPPLIER_NAME）

**数据注意点（验证中发现）**：
- 个别记录 `OK_QTY + NG_QTY ≠ BACK_QTY`（如 OU-20260730001 首条：98+1≠98），属录入异常，良品率统一用 `OK/(OK+NG)` 计算并提示
- 部分单 DELIVERY_DATE 为 `1900-01-01` 脏数据（如 OU-20260514002），**所有 SQL 已加 `DELIVERY_DATE > '2000-01-01'` 过滤**
- 状态 1 的单中大量已超要求回货日期（长期未回货），统计逾期时同时关注「在途已逾期」与「已完成逾期」

---

## 二、供应商良品率 SQL

```sql
SELECT
  s.SUPPLIER_ID,
  IFNULL(sup.SUPPLIER_NAME, s.SUPPLIER_ID) AS SUPPLIER_NAME,
  COUNT(DISTINCT b.OUTSOURCE_ID)                    AS ORDER_CNT,          -- 回货单数
  SUM(b.BACK_QTY)                                   AS BACK_TOTAL_QTY,     -- 回货总数
  SUM(b.OK_QTY)                                     AS OK_QTY,             -- 验收合格数
  SUM(b.NG_QTY)                                     AS NG_QTY,             -- 验退不良数
  SUM(b.OK_QTY + b.NG_QTY)                          AS CHECK_TOTAL_QTY,    -- 验收总数
  ROUND(SUM(b.OK_QTY) * 100.0 / NULLIF(SUM(b.OK_QTY + b.NG_QTY), 0), 2) AS GOOD_RATE  -- 良品率
FROM di_outsource_back_process b
JOIN di_outsource_send_basis s ON b.OUTSOURCE_ID = s.OUTSOURCE_ID
LEFT JOIN ou_supplier_basis sup ON s.SUPPLIER_ID = sup.SUPPLIER_ID
WHERE b.CREATE_TIME >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)   -- 近90天，可改
  AND s.DELIVERY_DATE > '2000-01-01'                          -- 过滤脏数据
GROUP BY s.SUPPLIER_ID, sup.SUPPLIER_NAME
ORDER BY GOOD_RATE ASC, ORDER_CNT DESC;
```

**验证结果（近90天）**：

| SUPPLIER_ID | 供应商名称 | 回货单数 | 回货总数 | 验收合格 | 验退不良 | 良品率 |
|---|---|---|---|---|---|---|
| Test | 测试供应商 | 5 | 7 | 5 | 2 | 71.43% |
| A | CNC供应商 | 10 | 179 | 161 | 18 | 89.94% |
| Dessert | 客户X供应商 | 12 | 168 | 154 | 14 | 91.67% |
| A0001 | 测试供应商A | 1 | 99 | 99 | 1 | 99.00% |
| DP0001 | LK大鹏测试供应商 | 1 | 8 | 8 | 0 | 100.00% |
| FZHGYS | F供应商 | 2 | 35 | 35 | 0 | 100.00% |
| MOUSE | 鼠鼠供应商 | 3 | 7 | 7 | 0 | 100.00% |
| ZHFYS | ZH供应商 | 2 | 2 | 2 | 0 | 100.00% |

---

## 三、供应商准时率 SQL（按单口径）

```sql
SELECT
  s.SUPPLIER_ID,
  IFNULL(sup.SUPPLIER_NAME, s.SUPPLIER_ID) AS SUPPLIER_NAME,
  COUNT(*)                                  AS FINISHED_CNT,              -- 已完成单数
  SUM(CASE WHEN DATE(t.last_back_time) <= DATE(s.DELIVERY_DATE) THEN 1 ELSE 0 END) AS ONTIME_CNT,   -- 准时单数
  SUM(CASE WHEN DATE(t.last_back_time) > DATE(s.DELIVERY_DATE) THEN 1 ELSE 0 END)  AS OVERDUE_CNT,  -- 逾期单数
  ROUND(SUM(CASE WHEN DATE(t.last_back_time) <= DATE(s.DELIVERY_DATE) THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS ONTIME_RATE  -- 准时率
FROM di_outsource_send_basis s
JOIN (SELECT OUTSOURCE_ID, MAX(CREATE_TIME) AS last_back_time
      FROM di_outsource_back_process GROUP BY OUTSOURCE_ID) t
  ON t.OUTSOURCE_ID = s.OUTSOURCE_ID
LEFT JOIN ou_supplier_basis sup ON s.SUPPLIER_ID = sup.SUPPLIER_ID
WHERE s.OUTSOURCE_STATUS = 3                       -- 仅统计全部回货（已完成）单
  AND s.CREATE_TIME >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
  AND s.DELIVERY_DATE > '2000-01-01'
GROUP BY s.SUPPLIER_ID, sup.SUPPLIER_NAME
ORDER BY ONTIME_RATE ASC, FINISHED_CNT DESC;
```

**验证结果（近90天，按日期口径）**：

| SUPPLIER_ID | 供应商名称 | 已完成单数 | 准时单数 | 逾期单数 | 准时率 |
|---|---|---|---|---|---|
| MOUSE | 鼠鼠供应商 | 2 | 0 | 2 | 0.00% |
| ZHFYS | ZH供应商 | 2 | 0 | 2 | 0.00% |
| A | CNC供应商 | 10 | 4 | 6 | 40.00% |
| Test | 测试供应商 | 5 | 4 | 1 | 80.00% |
| Dessert | 客户X供应商 | 10 | 8 | 2 | 80.00% |
| FZHGYS | F供应商 | 2 | 2 | 0 | 100.00% |
| A0001 | 测试供应商A | 1 | 1 | 0 | 100.00% |
| DP0001 | LK大鹏测试供应商 | 1 | 1 | 0 | 100.00% |

> ⚠️ 首次按时间精确比较时几乎所有单"逾期"（因为 DELIVERY_DATE=00:00 而回货在当天白天），**必须按 DATE() 比较**才是正确业务口径（当天内回货即准时）。

---

## 四、供应商委外全景汇总 SQL（★推荐：一张表汇总在手单+良品率+准时率，发货前说明用）

> 将「在手委外单（单头/单身/发货量）」「良品率」「准时率/逾期」合并为**一张供应商大表**。
> 三个子查询按供应商编号关联：① 在手单（状态1委外中）② 良品率（回货验收）③ 准时率（已完成单）。

```sql
SELECT
  sup.SUPPLIER_ID,
  IFNULL(sup.SUPPLIER_NAME, sup.SUPPLIER_ID) AS SUPPLIER_NAME,
  -- ① 在手委外单(状态1委外中)
  IFNULL(h.ORDER_CNT, 0)   AS HANDS_ORDER_CNT,   -- 在手委外单数(单头)
  IFNULL(h.DETAIL_CNT, 0)  AS HANDS_DETAIL_CNT,  -- 在手单身数(明细行数)
  IFNULL(h.SEND_QTY, 0)    AS HANDS_SEND_QTY,    -- 在手发货数量
  -- ② 良品率(近90天回货验收口径)
  p.GOOD_RATE              AS GOOD_RATE,         -- 良品率
  IFNULL(p.CHECK_TOTAL_QTY, 0) AS CHECK_TOTAL_QTY, -- 验收总数
  IFNULL(p.NG_QTY, 0)      AS NG_QTY,            -- 验退不良数
  -- ③ 准时率(近90天,已完成单口径)
  p.ONTIME_RATE            AS ONTIME_RATE,       -- 准时率
  IFNULL(p.FINISHED_CNT, 0) AS FINISHED_CNT,     -- 已完成单数
  IFNULL(p.OVERDUE_CNT, 0) AS OVERDUE_CNT        -- 逾期单数
FROM (
  SELECT s.SUPPLIER_ID, IFNULL(sup.SUPPLIER_NAME, s.SUPPLIER_ID) AS SUPPLIER_NAME
  FROM di_outsource_send_basis s
  LEFT JOIN ou_supplier_basis sup ON s.SUPPLIER_ID = sup.SUPPLIER_ID
  WHERE s.DELIVERY_DATE > '2000-01-01'
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
  WHERE b.CREATE_TIME >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)   -- 近90天，可改
    AND b.CREATE_TIME <= NOW()
    AND s.DELIVERY_DATE > '2000-01-01'
  GROUP BY s.SUPPLIER_ID
) p ON p.SUPPLIER_ID = sup.SUPPLIER_ID
ORDER BY p.ONTIME_RATE IS NULL ASC, p.ONTIME_RATE ASC, p.GOOD_RATE ASC;
```

**验证结果（近90天，节选）**：

| 供应商 | 在手单 | 单身 | 在手发货量 | 良品率 | 验收 | 验退 | 准时率 | 已完成 | 逾期 |
|---|---|---|---|---|---|---|---|---|---|
| ZHFYS · ZH供应商 | 0 | 0 | 0 | 100% | 2 | 0 | 0% | 2 | 2 |
| A · CNC供应商 | 32 | 32 | 10243.97 | 89.94% | 179 | 18 | 45.45% | 11 | 6 |
| MOUSE · 鼠鼠供应商 | 1 | 1 | 90 | 100% | 7 | 0 | 50% | 2 | 2 |
| Test · 测试供应商 | 1 | 1 | 1 | 71.43% | 7 | 2 | 83.33% | 6 | 1 |
| Dessert · 客户X供应商 | 0 | 0 | 0 | 91.67% | 168 | 14 | 84.62% | 13 | 3 |
| A0001 · 测试供应商A | 0 | 0 | 0 | 99% | 100 | 1 | 100% | 2 | 0 |
| FZHGYS · F供应商 | 0 | 0 | 0 | 100% | 35 | 0 | 100% | 2 | 0 |
| DP0001 · LK大鹏 | 0 | 0 | 0 | 100% | 8 | 0 | 100% | 1 | 0 |
| YYRCL/XY/WKGYS*/GYS0003/07.01.18 | 各1~2 | 各1~4 | — | 无回货记录 | — | — | — | — | — |

> 说明：无回货记录的供应商（仅在手单）良品率/准时率为空（NULL），非 0；ZH供应商是典型"质量好但交付差"（良品率100%但准时率0%）。

---

## 五、逾期明细 SQL（发货前风险说明）

```sql
SELECT
  s.OUTSOURCE_ID,
  s.SUPPLIER_ID,
  IFNULL(sup.SUPPLIER_NAME, s.SUPPLIER_ID) AS SUPPLIER_NAME,
  DATE(s.DELIVERY_DATE)                     AS DELIVERY_DATE,     -- 要求回货日
  DATE(t.last_back_time)                    AS ACTUAL_BACK_DATE,  -- 实际回货日
  DATEDIFF(DATE(t.last_back_time), DATE(s.DELIVERY_DATE)) AS OVERDUE_DAYS,  -- 逾期天数
  t.total_back                              AS BACK_QTY           -- 回货数量
FROM di_outsource_send_basis s
JOIN (SELECT OUTSOURCE_ID, MAX(CREATE_TIME) AS last_back_time, SUM(BACK_QTY) AS total_back
      FROM di_outsource_back_process GROUP BY OUTSOURCE_ID) t
  ON t.OUTSOURCE_ID = s.OUTSOURCE_ID
LEFT JOIN ou_supplier_basis sup ON s.SUPPLIER_ID = sup.SUPPLIER_ID
WHERE s.OUTSOURCE_STATUS = 3
  AND DATE(t.last_back_time) > DATE(s.DELIVERY_DATE)
  AND s.CREATE_TIME >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
  AND s.DELIVERY_DATE > '2000-01-01'
ORDER BY OVERDUE_DAYS DESC;
```

**验证结果（近90天，节选）**：OU-20260703001（ZHFYS，要求7/3实际7/20，**逾期17天**）、OU-20260618009（ZHFYS，逾期12天）、OU-20260605005~11（CNC供应商 6 单，各逾期10天）等。

---

## 六、委外在途/待回货清单 SQL（回货操作入口）

```sql
SELECT
  dosb.OUTSOURCE_ID,
  dosb.SUPPLIER_ID,
  IFNULL(osb.SUPPLIER_NAME, dosb.SUPPLIER_ID) AS SUPPLIER_NAME,
  CASE dosb.OUTSOURCE_STATUS WHEN 1 THEN '委外中' WHEN 2 THEN '部分回货' WHEN 3 THEN '全部回货' END AS STATUS_NAME,  -- 状态
  DATE(dosb.DELIVERY_DATE) AS DELIVERY_DATE,       -- 要求回货日
  SUM(dosd.SEND_QTY) AS SEND_QTY,                  -- 发货数量
  IFNULL(aa.TOTAL_BACK_QTY, 0) AS BACK_QTY,        -- 已回货数量
  (SUM(dosd.SEND_QTY) - IFNULL(aa.TOTAL_BACK_QTY, 0)) AS CAN_BACK_QTY,  -- 待回货数量
  CASE WHEN dosb.DELIVERY_DATE < CURDATE() AND dosb.OUTSOURCE_STATUS IN (1,2)
       THEN DATEDIFF(CURDATE(), DATE(dosb.DELIVERY_DATE)) ELSE 0 END AS OVERDUE_DAYS  -- 已逾期天数
FROM di_outsource_send_basis dosb
LEFT JOIN di_outsource_send_detail dosd ON dosb.ID = dosd.PARENT_ID
LEFT JOIN ou_supplier_basis osb ON osb.SUPPLIER_ID = dosb.SUPPLIER_ID
LEFT JOIN (
  SELECT OUTSOURCE_ID, SUM(BACK_QTY) AS TOTAL_BACK_QTY
  FROM di_outsource_back_process GROUP BY OUTSOURCE_ID
) aa ON aa.OUTSOURCE_ID = dosb.OUTSOURCE_ID
WHERE dosb.OUTSOURCE_STATUS IN (1, 2)
  AND dosb.DELIVERY_DATE > '2000-01-01'
GROUP BY dosb.OUTSOURCE_ID, dosb.SUPPLIER_ID, osb.SUPPLIER_NAME,
         dosb.OUTSOURCE_STATUS, dosb.DELIVERY_DATE
ORDER BY dosb.DELIVERY_DATE ASC;
```

---

## 七、参考：待发货清单（可委外工单）

复用系统视图 `GET_OUTSOURCE_LIST` 逻辑（基于 `ac_lot_status` 待开工量 + 工艺 `CAN_OUTSOURCE=1`），完整 SQL 见问数知识库 `sql_assets_full.md` 2457 行。本技能 `outsource_list.py --todo` 提供简化版：

```sql
SELECT
  als.MO_ID,
  pmd.MA_ID,
  mb.MATERIAL_NAME,
  mb.MATERIAL_DESCRIPTION,
  als.OP_SEQ,
  als.OP_ID,
  mob.OP_NAME,
  IFNULL(mob.SUPPLIER_ID, '') AS SUPPLIER_ID,          -- 预设供应商编号
  IFNULL(osb.SUPPLIER_NAME, '') AS SUPPLIER_NAME,      -- 预设供应商名称
  als.TO_BE_STARTED_QTY AS TO_BE_STARTED_QTY,          -- 待开工数量
  IFNULL(dosd.SEND_QTY, 0) AS SEND_QTY,                -- 已发货数量
  (als.TO_BE_STARTED_QTY - IFNULL(dosd.SEND_QTY, 0)) AS CAN_OUTSOURCE_QTY  -- 可委外数量
FROM ac_lot_status als
INNER JOIN me_op_basis mob ON als.OP_ID = mob.OP_ID AND mob.CAN_OUTSOURCE = 1
INNER JOIN pl_mo_status pms ON pms.MO_ID = als.MO_ID AND pms.MO_STATUS IN (1, 2)
LEFT JOIN pl_mo_data pmd ON als.MO_ID = pmd.MO_ID
LEFT JOIN ma_basis mb ON pmd.MA_ID = mb.MA_ID
LEFT JOIN ou_supplier_basis osb ON osb.SUPPLIER_ID = mob.SUPPLIER_ID
LEFT JOIN (
  SELECT MO_ID, OP_SEQ, OP_ID, SUM(SEND_QTY) AS SEND_QTY
  FROM di_outsource_send_detail GROUP BY MO_ID, OP_SEQ, OP_ID
) dosd ON dosd.MO_ID = als.MO_ID AND dosd.OP_SEQ = als.OP_SEQ AND dosd.OP_ID = als.OP_ID
WHERE als.TO_BE_STARTED_QTY - IFNULL(dosd.SEND_QTY, 0) > 0
ORDER BY als.MO_ID, als.OP_SEQ;
```

---

## 八、供应商在手委外单汇总 SQL（委外中状态，单头+单身）

> 用途：供应商当前"在手"委外单（状态=1 委外中）的规模统计——单据数量（单头数）+ 单身数量（明细行数）+ 在手发货量
> 口径：单头 = 委外单数（按 OUTSOURCE_ID 去重）；单身 = 该单明细行数（一张单可含多行工单/工艺明细）
> 💡 该指标已并入**第四节全景汇总 SQL**（`HANDS_ORDER_CNT / HANDS_DETAIL_CNT / HANDS_SEND_QTY` 三列），独立查询时用本段。

```sql
SELECT
  s.SUPPLIER_ID,
  IFNULL(sup.SUPPLIER_NAME, s.SUPPLIER_ID) AS SUPPLIER_NAME,
  COUNT(DISTINCT s.OUTSOURCE_ID) AS ORDER_CNT,        -- 在手委外单数(单头汇总)
  COUNT(d.PARENT_ID) AS DETAIL_CNT,                   -- 单身数量(明细行数)
  IFNULL(SUM(d.SEND_QTY), 0) AS SEND_QTY              -- 在手发货数量合计
FROM di_outsource_send_basis s
LEFT JOIN di_outsource_send_detail d ON s.ID = d.PARENT_ID
LEFT JOIN ou_supplier_basis sup ON s.SUPPLIER_ID = sup.SUPPLIER_ID
WHERE s.OUTSOURCE_STATUS = 1                          -- 仅委外中(在手)单
  AND s.DELIVERY_DATE > '2000-01-01'
GROUP BY s.SUPPLIER_ID, sup.SUPPLIER_NAME
ORDER BY ORDER_CNT DESC, DETAIL_CNT DESC;
```

**验证结果（当前库）**：

| SUPPLIER_ID | 供应商名称 | 在手委外单数 | 单身数量 | 在手发货数量 |
|---|---|---|---|---|
| A | CNC供应商 | 32 | 32 | 10243.97 |
| 07.01.18 | 黑龙江拉斐特科技发展有限公司 | 2 | 4 | 173.10 |
| GYS0003 | 东莞五金精密制造有限公司 | 1 | 2 | 2.00 |
| XY | 萧炎热处理（高效） | 1 | 2 | 2.00 |
| MOUSE | 鼠鼠供应商 | 1 | 1 | 90.00 |
| Test | 测试供应商 | 1 | 1 | 1.00 |
| WKGYS002 | 广州五金精密制造有限公司 | 1 | 1 | 92.00 |
| WKGYS003 | 上海CNC外协加工厂 | 1 | 1 | 94.00 |
| YYRCL | 炎炎热处理炎炎热处理 | 1 | 1 | 2.00 |
| **合计** | — | **41** | **45** | — |

---

## 九、技能脚本对照

| 能力 | 脚本 | 参数 |
|------|------|------|
| **委外推荐（候选+绩效排序+推荐第一名）** | recommend_supplier.py | `--product X [--op X] [--mo X] --priority quality\|ontime` |
| **全景汇总（在手单+良品率+准交率）** | supplier_perf.py | `--perf [--supplier X] [--days N]` |
| 良品率 | supplier_perf.py | `--quality` |
| 准时率 | supplier_perf.py | `--ontime` |
| 逾期明细 | supplier_perf.py | `--overdue` |
| 待发货清单 | outsource_list.py | `--todo` |
| 在途/待回货 | outsource_list.py | `--intransit [--overdue] [--supplier X]` |
| 在手委外单汇总（单头+单身） | outsource_list.py | `--hands [--supplier X]` |
| 单号回货明细 | outsource_list.py | `--detail <OUTSOURCE_ID>` |

> 脚本内部 SQL 别名均为大写英文；展示层（脚本输出表头）自动映射为中文，SQL 与展示互不影响。
