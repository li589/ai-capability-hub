# SQL 生成器（第一步：中文需求 → SQL）

> 工具：`scripts/generate_sql.py`（规则版路由，无需 LLM API）
> 作用：把中文问数需求解析成可执行 SQL —— 验证"知识库 → 路由 → SQL"链路正确性。
> 接入 Skill 后，四要素解析升级为 LLM 版本，本工具负责确定性路由与 SQL 组装兜底。

## 用法

```bash
python scripts/generate_sql.py "问题1" "问题2" ...
# 单个问题：
python scripts/generate_sql.py "A产品今天的产量是多少"
```

## 处理链路

```
问题 → ① 时间解析（今天/昨天/本周/上月/最近N天/日期）
     → ② 实体解析（产品/设备/车间，支持"产品M02"和"M02产品"双向词序）
     → ③ intent 匹配（asset_index.json intents.keywords 打分）
     → ④ 视图选择（intent.preferred 优先，口径验证过的视图）
     → ⑤ 参数化 WHERE（view_filters 白名单，只允许配置过的列，防误过滤）
     → 输出：解析结果 + SQL + 警告提示
```

## 已覆盖能力（实测通过）

| 需求示例 | 路由结果 | SQL 来源 |
|---------|---------|---------|
| A产品今天的产量 | product=A + output_summary | 底层表 `ac_mo_report_process`（按产品+时间最准） |
| 今天产量和昨天比 | 对比模式（当前+基准两段 SQL） | 视图 `PCQ_MO_0002`（CSDDATE 按日产量） |
| M01设备今天的状态 | equipment=M01 + eq_status | 视图 `GET_EQ_STATUS`（START_TIME/EQ_ID 过滤） |
| 螺丝今天的良率 | quality_pqc | 视图 `PCQ_QC_0001`（IS_PASS/PQC_QTY/PQC_BAD_QTY 应用层算良率） |
| 为什么今天的产量下降 | 归因模式 → 四维度并行检查 SQL | 设备点检 / 状态切换 / 工单堆积 / 不良 |
| 3号车间待派工 | ws=3 + dispatch | 视图 `PENDING_DISPATCH_LIST` |

## 设计要点（为什么这样路由）

1. **资产 SQL 优先**：142 个视图是业务验证过的口径，命中即复用；本工具只负责参数化。
2. **视图过滤白名单**（`asset_index.json.view_filters`）：只允许对配置过的视图追加 WHERE，避免像 `GET_MO_LIST`（全量派工视图）被错误按预计完工日过滤。
3. **产量类带产品 → 底层表**：视图多为"按工序/车间汇总"，按产品过滤不准确；`ac_mo_report_process` 有 EXECUTE_TIME + MA_ID，时间+产品双过滤最准。
4. **归因四维度**：问"为什么下降"时并行输出 4 条检查 SQL，命中后按影响排序。

## 已知限制（v0.1）

- 中文产品名（如"螺丝"）实体提取需 `entity_map.json` 映射（当前未建，编号类产品已支持）
- 良率需应用层计算：(PQC_QTY - PQC_BAD_QTY) / PQC_QTY
- 对比基准日默认"昨天"；周/月对比基准需扩展
- 43 个占位视图（无 SQL）自动走 schema 兜底

## 下一步

- [ ] 接数据库连接，真实执行验证 SQL 可运行性
- [ ] 枚举字典（eq_n_status/execute_type/bad_type）填充，输出中文状态
- [ ] entity_map.json 中文名称映射
- [ ] LLM 版四要素解析替换规则版（接入 Skill 时）
