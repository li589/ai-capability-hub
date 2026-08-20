# 10.1.0 / 2026-08-17 / 测试优化与健壮性升级

### 修复
- **`client_manager/ppt_report_generator.py` 语法错误修复**：11 处 `p.font.name = "宋体"` 因批量插入缩进错位（IndentationError），导致该模块完全无法导入；此前测试手工清单未覆盖此模块，问题长期潜伏

### 测试强化
- `test_smoke_imports.py` 新增 **全覆盖编译烟囱测试** `test_all_modules_compile`：自动扫描全部 .py 文件做 py_compile 校验，任何 SyntaxError/IndentationError 都会被捕获（根治"手工清单漏覆盖"盲区）
- 新增 `test_key_client_manager_modules_importable`：报告/画像/导出等 6 个核心模块强制可导入（可选第三方依赖缺失可降级，语法错误不可接受）
- `pytest.ini` 移除全局 `ignore::DeprecationWarning`：弃用警告不再被静默屏蔽（当前实测零警告），后续新增弃用用法会立即暴露
- 全套测试 **220 passed, 1 skipped**（+2 新测试）

### 健壮性验证
- Python 3.11.9 / 3.14 双版本全量测试通过（3.14 下 mcp 可选依赖未装时优雅降级）
- 全项目 compileall 编译检查零错误；无裸 `except:`、无弃用 API（utcnow/imp 等）

### 元数据一致性
- `pyproject.toml` / `.claude-plugin/plugin.json` description 修正（仍残留 v9 表述 → 对齐 v10 能力集）
- `_meta.json` description/welcome 对齐 v10；版本号统一至 10.1.0

---

# 10.0.1 / 2026-08-14 / 彻底轻量化（数据占位化）

- **真实数据备份至包外** `fund-advisor-data-backup/`（skill 同级）：4,288 经理 / 27,516 产品 / 163 公司 / 212 只基金持仓（2026Q2 跟仓基线）/ 595 条经理新闻 / 3.1MB 原始采集名录，共 8.2MB
- **核心数据占位化**：fund_managers / fund_companies / fund_products / holdings_database / manager_views / manager_news / external_data 全部替换为占位骨架（空列式/空结构 + placeholder 标记），包体 **11MB → 2.1MB**（-81%），文件数 170 → 164
- 删除：原始采集名录（3.1MB，无消费方）、运行期产物（reports/、nav_cache.db）、空运行目录
- `data_freshness.json` / `update_meta.json` / `_meta.json` 标记占位态并注明备份位置
- 首次使用：`python scripts/update_data.py full` 联网重建（约 8-10 分钟）后开箱即用
- 测试保持 **221 passed, 1 skipped**（数据依赖测试均已隔离）

## 10.0.1b / 上传合规与测试隔离
- **新增 `clean.py`**：上传/打包前清理 __pycache__/pyc、nav_cache.db、reports 等二进制/运行期产物（`--check` 模式自检），替代被上传平台拒绝的 .gitignore
- 测试污染根治：`test_v10_new_tools_callable` 报告写盘隔离到 tmp；`ManagerFollower` 净值缓存尊重 data_dir（不再写默认路径）
- 删除测试残留：data/reports/ 测试客户报告、nav_cache.db、空运行目录；全套测试后 data/ 仅 11 个占位文件

---

# 10.0.0 / 2026-08-14 / 基金经理对话 + 跟仓 + 客户行为心理画像 + 模块化定制报告 + 产品档案增强

### 新增能力

#### 基金经理对话（`analysis/manager_persona.py` + `manager_dialogue.py`）
- 蒸馏「基金经理人设卡」：履历/风格/股票池/合同投资范围（投资目标/范围/基准）/最新季报观点/新闻采访/风险提示
- `ManagerDialogue.chat(...)` 以经理口吻回答客户经理问题，意图路由（风格/持仓/观点/范围/新闻/业绩/安抚/自我介绍）
- 回答优先级：可选 LLM 蒸馏（DeepSeek key）→ 规则组装（真实数据）→ 模板兜底；自带免责声明
- `data_collection/manager_news_collector.py`：真实采集经理新闻/采访（东财经理档案页 + 公告 + 资讯搜索）

#### 基金跟仓（`analysis/manager_follower.py`）
- `diff_holdings/diff_fund_holdings`：同一基金两季十大重仓变动（新增/剔除/加仓/减仓/换手率）
- `build_mirror_portfolio`：镜像组合（加权/等权）+ 集中度（top1/3/5、HHI）+ 金额分解 + 合规风险提示
- `track_mirror_performance`：基金净值近似 + 当日重仓股行情估算
- `get_follow_signals`：跟仓信号（持仓变动 + 经理变动，带置信度与级别）
- `data_collection/holdings_history.py`：按季度归档持仓快照（v10 起积累历史基线）；`fund_advisor_paths` 新增 `load_holdings_history`
- `maintenance/manager_change_monitor.py`：经理变动监控（本地档案对比 + 公告扫描）

#### 客户行为心理画像（`client_manager/behavioral_profile.py`）
- 10 题行为问卷（`behavioral_questionnaire.json`）+ 情绪记录/持仓导入历史/画像设置
- 6 维偏差：损失厌恶/处置效应/过度自信/从众追涨/频繁交易/短视
- 6 类心理类型 + 沟通策略（语气/风险提示频率/预警阈值/Do&Don't）
- `conversation_engine` 新增心理感知层（已评估画像的客户自动附加个性化沟通提示）
- `user_profile_manager` 扩展 `assess_behavioral` / `get_behavioral_summary`

#### 模块化定制报告（`client_manager/report_generator.py` 重构 + `report_scheduler.py`）
- `generate_report(modules=, template=)`：8 模块（要闻/持仓/经理观点/心理/跟仓/配置/展望/风险）× 3 模板（standard/concise/professional），旧签名向后兼容
- 市场展望改为数据驱动（MacroAnalyzer 真实数据优先，无数据回退内置文本）
- `report_scheduler`：客户报告订阅（频率×模块×模板）+ 一键批量生成

#### 公募产品档案增强（`data_collection/fund_profile_collector.py` + `db_format.py`）
- 产品列扩宽：投资目标/投资范围/投资策略/业绩基准 + 费率（管理/托管/申赎/最低申购）+ 业绩序列（1m/3m/6m/1y/3y/成立来）+ 成立日/规模/经理
- `full_data_refresh.py` 接入档案增强步骤（默认取经理现任基金，受 `FUND_ADVISOR_PROFILE_LIMIT` 控制）

### 改动
- `mcp_server.py`：MCP 工具 36 → 48（新增 chat_with_manager/get_manager_persona/get_manager_news/compare_holdings_change/build_mirror_portfolio/track_mirror_portfolio/get_follow_signals/assess_client_profile/get_client_communication_guide/generate_custom_report/generate_batch_reports/chat_with_client）
- `fund_advisor_bootstrap.py`：自检新增 v10 模块导入校验
- 经理观点 schema 归一化（`invitation_engine._get_manager_views` 兼容 fc/fund_code、v/views）

### 测试
- 新增 8 个测试文件（test_manager_persona / test_manager_dialogue / test_manager_news / test_holdings_history / test_manager_follower / test_behavioral_profile / test_report_customization / test_product_profile）
- 全套 **145 → 222 passed, 1 skipped**（真实数据重建后全绿）
- 修复 `test_should_update_fresh` 日期漂移脆弱性；query/bootstrap 测试改为隔离真实数据目录

### 联网冒烟修复（真实页面调优）
- `fund_profile_collector`：真实页面为 jbgk 文本内联结构（非 h4/txt_in），重写 `_parse_jbgk_text` 为主源 + `html.unescape` 解码 `&nbsp;`；费率 jjfl、业绩 pingzhongdata 保持
- `manager_news_collector`：经理档案页为反爬壳页，改用**东财官方搜索 API（search-api-web.eastmoney.com）为主源**（实测 595 条真实新闻/100 经理）；公告源保留（经理变更检测）；分类修复（标题含「基金经理」≠公告，须含 变更/离任/增聘 才归公告）
- `auto_updater.run_full_update` 接入持仓历史归档 + 产品档案增强步骤
- `fund_advisor_bootstrap`：可选增强层（观点/新闻/外部数据）改为非阻塞提示；阈值适配真实重建数据
- 全量重建验证：`update_data.py full` → 4,288 经理 / 27,516 产品 / 163 公司 / 212 只基金持仓（成功 70.7%）+ 2026Q2 跟仓基线归档

### 文档
- SKILL.md / _meta.json / .skillhub.json / .claude-plugin/plugin.json / pyproject.toml 版本同步 10.0.0
- 新增 `references/manager_dialogue_follow.md`

---

# 9.0.0 / 2026-08-10 / 三件套完整实现 + 数据稳定性 + 重建零依赖

- 回测四策略（动量/均值回归/风险平价/轮动）桩 → 真实模拟（_simulate_adaptive 动态权重）
- 因子 value/sentiment 穿透持仓/评级真实计算（degraded 标记）
- 情景 sector_boom/inflation_surge/currency_devaluation 三模板补全 + fund_swap 复用 fee_calculator
- 修复 full_data_refresh.py random 致命 bug（网络重试无限挂死）
- 重建统一零依赖：update_data.py full 走 stdlib full_data_refresh；db_format 单一格式；monthly_updater 零依赖化 + 格式统一
- 数据稳定性：沙箱加固（_validate_file/commonpath + URL 白名单）、_parse_holdings_rows 容错、should_update 占位识别
- 测试优化：test_entry_points 0 断言改造、脆弱测试离线化、conftest 重构、盲区补测（117 → ~145）

# 8.2.0 / 2026-08-05 / 包轻量化 + 测试适配

### 轻量化
- **运行时数据库移出交付包**：`data/` 下 6 个季度采集大 JSON（fund_products 2.4M、external_data 1.1M、holdings_database 980K、fund_managers_distilled 392K 等，合计约 5M）替换为空骨架占位，包体积从 6.8M 降至约 1.9M（-72%）
- **数据备份**：真实数据已备份至包外 `fund-advisor-data-backup/`（本次会话所在盘符同级目录），可随时恢复
- **首次使用重建**：数据未随包分发，使用前运行 `python scripts/update_data.py full` 联网重建；`_check_data` / bootstrap 自检会如实标记占位数据为"未初始化（TOO SMALL）"
- 空骨架可被 `load_json_data` / `load_holdings` 透明解码（返回空数据集），所有分析器对空数据优雅降级（`未找到` / `至少2位`），不崩溃

### 测试适配与补全
- `tests/test_query_tools.py` 重写：不再依赖真实 data，改用临时样本数据（列存格式）注入 `DATA_DIR`，验证 query_fund / query_manager / compare_managers 字段对齐；新增空数据降级测试
- `tests/test_bootstrap.py`：占位数据检查测试改为验证"未初始化标记"
- `tests/test_holdings_loader.py`：真实文件解码测试适配占位骨架（返回空不崩，重建后校验 6 位代码）
- `tests/test_skill_metadata.py`：数据占位时跳过经理数比对
- 全套 **116 passed, 1 skipped**

---

# 8.1.0 / 2026-08-01 / 量化跟踪修复 + 预测可复现 + 缓存与性能优化

### 修复
- **实时净值跟踪权重计算**：`position_tracker.nav_vs_target_tracking` 原先在提供 `nav_updates` 时把“市值金额”直接当权重，且未按组合总市值归一化；修复后按最新净值计算每只基金市值占比，再与目标权重比较
- **基金预测不可复现**：`fund_predictor` 原先使用 Python 内置 `hash()` 作为随机种子，跨进程/跨运行不稳定；改为 `zlib.crc32` 稳定种子，并按“基金代码+周期”区分蒙特卡洛路径
- **数据缓存陈旧**：`LazyDataCache` 现在记录文件 mtime，文件更新后旧缓存立即失效，不再在 TTL 内返回过期数据
- **测试入口**：`python -m fund_advisor test` 改为同一进程内 `pytest.main`，并禁用字节码写入，减少子进程启动开销和缓存残留

### 新增
- `tests/test_v81_quant_tracking.py`：覆盖实时跟踪权重、预测可复现、缓存失效，共 5 个回归测试
- 全量测试从 111 个增至 116 个，全部通过

---

# 8.0.0 / 2026-07-30 / 量化回测 + 多因子筛选 + 情景模拟 + 数据源增强

### 新增
- **回测引擎**：`scripts/analysis/backtest_engine.py` — 组合历史模拟回测（穿透费率计算）+ 策略回测（动量/均值回归/风险平价/股债轮动/买入持有）+ 基准对比（超额收益/IR/TE）+ 情景压力测试（6个历史情景+自定义冲击）+ ASCII 报告格式化
- **多因子筛选引擎**：`scripts/analysis/factor_engine.py` — 六维因子体系（动量/波动率/质量/价值/情绪/宏观敏感度）+ 因子合成（等权/波动率倒数加权）+ 分层排名+ 同业相对强度 + 因子归因
- **情景模拟器**：`scripts/analysis/scenario_simulator.py` — 市场冲击/换仓影响/利率变化/通胀侵蚀 What-If 分析 + 批量情景运行
- **净值缓存**：`scripts/data_collection/nav_cache.py` — 本地 SQLite 缓存基金日净值（纯标准库 sqlite3），回测引擎数据基础
- **Tushare 数据源**：`scripts/data_collection/multi_source/tushare_provider.py` — 可选增强源（需 TUSHARE_TOKEN），支持宏观/净值/指数/持仓数据
- **MCP 工具 32→36**：`run_backtest` / `stress_test_portfolio` / `analyze_factor_exposures` / `simulate_scenario`

### 增强
- **组合跟仓分析**：`position_tracker.py` 新增集中度风险分析（Herfindahl指数/类型集中度/公司集中度）、相关性矩阵、带成本效益的调仓信号、实时净值跟踪
- **基金筛选模型**：十维评分扩展至十二维（新增因子动量/因子质量），支持自定义因子权重
- **数据加载优化**：`fund_advisor_paths.py` 新增 LazyDataCache（LRU 缓存，max_size=5, TTL=1h），减少重复磁盘 I/O

### 清理
- 删除 `scripts/analysis/fund_predictor_temp.py`（无引用的临时副本）
- 删除 3 个 `__pycache__/` 目录（9 个 .pyc 文件）
- `sys.dont_write_bytecode = True` 扩展到 `fund_advisor_paths.py`，防止 .pyc 再生
- 移除 `performance_tracker.py` 中未使用的 `import random`

### SKILL.md
- 版本 7.3.0 → 8.0.0，新增回测/因子分析/情景模拟章节（§6/§7/§8）
- Recipe 11-14：回测使用/压力测试/因子分析/情景模拟
- MCP 工具表更新至 36 个工具
- 触发关键词新增：回测/压力测试/因子分析/情景分析/What-If/Tushare

---

# 7.2.0 / 2026-07-21 / 2026Q2 真实持仓重采集 + 查询链路修复 + MCP 工具 28→30

### 修复
- **query_fund / query_manager 字段错配**：两个 MCP 工具读取的字段名与压缩数据实际字段不一致，原先恒返回"未找到"；修正字段映射后恢复正常查询
- **持仓数据读取链路**：新增 `load_holdings()`（`scripts/fund_advisor_paths.py`）统一解码 h/m、f/m、holdings、by_manager 四种历史与现行持仓格式，消费方全部改为经该函数读取
- **monthly_updater 解析崩溃**：对嵌套列式 external_data（ratings/analysis/profit_probability 各自为列存）的解析不再崩溃
- **数据加载修复**：invitation_engine / sector_predictor / comparison_engine 的数据加载链路修复

### 数据
- **重新采集 2026Q2 真实十大重仓**：holdings_database.json 以真实季报数据（2,598 只基金，覆盖 162 家公司，成功率 2598/3637）替换此前的占位数据，切换为 v7.2 紧凑 h/m 格式（`{"h":[{fc,fn,mg,co,ss:[[code,name,weight],...]}],"m":{quarter,...}}`），数据截至 2026-06-30，7 月采集；采集驱动新增占位数据质检（检出占位即判失败重采）
- 数据口径核实：基金经理 4,270 人 / 基金公司 164 家 / 基金产品 27,304 只 / 经理观点 52 条（定期报告 PDF 摘录）/ 风格画像 6 类
- **更新链路加固**：auto_updater 全量更新前自动备份并在结束后恢复季度持仓库（防止 FullDataCollector 的 300 人增量覆盖 2,598 只全量版本）；fund_product_updater / fetch_all_products 改写为与盘上一致的 v6.1+ 新列存格式（code/name/type/pinyin/update），防止更新后查询字段错配回归

### 新增
- **MCP 工具 28→30**：`get_advisor_report`（投顾报告）、`compare_managers`（经理对比）
- **测试**：tests/test_holdings_loader.py（持仓四种格式解码）、tests/test_query_tools.py（query_fund/query_manager 字段映射回归）

### 清理
- **删除 10 个死代码脚本**：scripts/_compressed_loader.py、scripts/run_workflow.py、scripts/analysis/ 下 portfolio_analyzer / style_analyzer / distiller / company_distiller / comprehensive_analyzer / backtest_engine / manager_portfolio_builder / portfolio_scheduler（均无调用方；优化器实际位于 asset_allocator.py，文档中此前误归属 portfolio_rebalancer.py 的表述已更正）

# 7.1.0 / 2026-07-21 / 投顾能力增强：定投规划 + 调仓成本测算

### 新增
- **定投规划器**：`scripts/analysis/dca_planner.py` — `plan_dca()` 月定投金额按 SAA 拆分（核心-卫星上限约束）；养老/教育场景自动带下滑曲线；逐年末 累计投入 vs 悲观/中性/乐观 三档终值测算（基于各风险等级假设年化收益±波动，情景假设如实标注，悲观档下限 -10%）；止盈目标（保守 10%~进取 40%）与检视频率纪律；`format_dca_plan()` 可读输出
- **调仓成本测算器**：`scripts/analysis/fee_calculator.py` — `redemption_fee()` 赎回费阶梯（<7天 1.5% 惩罚性费率/<30天/<1年/<2年/≥2年，债券/货币专用阶梯）；`subscription_fee()` 申购费默认 1 折；`estimate_rebalance_cost()` 换仓总成本+占比+执行建议（持有<7天强烈建议等待）；`breakeven_months()` 回本周期（新基金年化超额需多少月覆盖成本，>12月提示性价比低）
- **MCP 工具 26→28**：`plan_dca_investment`、`estimate_rebalance_cost`（字符串参数协议，Agent 友好）
- **SKILL.md**：新增 §1.7/§1.8 与 Recipe 9/10；版本 7.1.0

### 修复
- **test_config_placeholder 脆性**：本机配置 DEEPSEEK_API_KEY 环境变量时假失败（key 来自用户环境而非仓库泄漏，config.py 设计正确），测试改用 monkeypatch 隔离环境

### 测试
- 新增 tests/test_dca_fee.py（9 项：拆分加总/问卷覆盖/三档有序/边界/费率阶梯/惩罚性识别/回本方向）
- 全量 100 passed；零新依赖（纯标准库）

# 7.0.0 / 2026-07-20 / 四大能力增强 + 自进化自学习

### 新增
- **组合配置**：`scripts/analysis/asset_allocator.py` — 10 题问卷打分→五轴→5 档风险等级；SAA 基准配置（期限/目标微调）；养老/教育下滑曲线 glide_path；核心-卫星拆分；风险平价（1/σ 与迭代 ERC）与均值方差（小矩阵网格）优化器；基金-客户适当性校验；一站式 `build_allocation_plan`
- **投后追踪**：`scripts/analysis/review_engine.py` — 组合净值序列构建（三级策略：provider→akshare→成本常数降级并标注 degraded）；`weekly_review` 六维 Dashboard；`monthly_review` 归因+告警+下次检视日；markdown 报告渲染
- **投资分析**：`scripts/analysis/perf_metrics.py` — 全指标库：年化/波动/夏普/索提诺/卡玛/最大回撤（含峰谷与持续天数）/信息比率/跟踪误差/Beta/Alpha/滚动指标，纯标准库
- **自进化自学习**：`scripts/learning/`（learning_engine.py + playbook_default.json）— 学习闭环：建议留痕(advice_log.jsonl) → 事后回填(outcomes.jsonl) → 命中统计 → 保守校准(calibration.json，样本≥5 才调/步进≤5/参数有边界) → 策略库进化(playbook.json，低胜率规则自动停用)；`apply_calibration` 供各模块读取最新参数
- **MCP 工具 18→26**：新增 run_portfolio_healthcheck / get_attribution_analysis（补齐 SKILL.md 已宣称但缺失的 2 个）/ score_risk_profile / build_allocation_plan / get_portfolio_metrics / generate_review_report / log_advice / get_learning_report
- **知识库**：references/investment_knowledge.md（配置理论/组合实践/基金评估/行为金融/费用税务/合规红线）；references/learning_loop.md（闭环数据格式/hit 判定/校准规则/调用时序）

### 修复（既有问题）
- **新版列存格式解码缺失**：fund_managers_distilled.json / fund_products.json 自 v6.1 已切换为真列存格式（`_f:[列名]/c:[列数组]/m`），而 `_decode_columnar` 仅支持旧版行式（`_f:"c"/c/d/m`），导致经理与产品数据静默读空。新增 `is_columnar()` 检测并兼容两种变体（fund_advisor_paths.py + data_loader.py）
- **config.py 缺失 API_KEY**：恢复 `API_KEY` 常量（默认 OFFLINE_PLACEHOLDER）与基于环境变量的 `is_offline_mode()`，修复 test_config_placeholder
- **补齐 .claude-plugin/plugin.json**（此前缺失导致元数据测试失败）
- **测试修复**：test_entry_points subprocess 增加 utf-8 解码（Windows GBK 控制台崩溃）；test_bootstrap 移除不存在的 `_check_env` 导入、豁免已知空占位 holdings 文件；test_mcp_server 在未安装 mcp 包时优雅跳过；test_skill_metadata 经理计数适配新版列存（唯一 manager_id=4,268）、emoji 检查收窄至 frontmatter（正文状态图标为设计语义）
- **数据口径纠偏**：经理 4,241→4,268、产品 27,128→27,299、持仓明细 1,794→0（当前为空占位，需联网刷新），SKILL.md/_meta.json/README.md 全部对齐真实数据

### 文档
- SKILL.md 三大能力→五大能力（新增投资分析 §4 / 自进化自学习 §5）；新增 Recipe 6-8；MCP 工具表对齐 26 个；修复 Common Pitfalls 编号跳跃并补充学习数据/降级两条
- _meta.json / README.md / pyproject.toml 版本同步至 7.0.0

### 测试
- 新增 tests/test_v7_modules.py（11 项，全离线可跑，含学习全链路与 hit 方向判定）
- 全量 88 passed + 3 skipped（mcp 包未装时优雅跳过）；零新依赖（纯标准库，akshare 仍为可选）

### 已知问题
- holdings_database.json 为空占位（0 条持仓明细），`python -m fund_advisor check` 会报 TOO SMALL；联网运行 `python scripts/data_collection/full_data_refresh.py` 刷新

# 5.3.1 / 2026-07-07 / MCP 服务优化 + 基金查询工具

### 修复
- `mcp_server.py` `_validate_file` 函数重新格式化（类型注解、错误信息、返回值明确 None）
- `mcp_server.py` 移除对 `fund_advisor_paths` 的副作用导入，改为显式导入 `DATA_DIR`
- `mcp_server.py` 删除未使用的 `threading` 导入

### 新增
- `query_fund(fund_code)` MCP 工具：按基金代码查询详细信息（名称/类型/经理/规模/净值/收益）
- `query_manager(manager_name)` MCP 工具：按姓名查询基金经理档案（公司/年限/规模/风格/代表产品）
- `_load_json_data` 辅助函数：透明支持标准 JSON 和列式压缩格式 (_f=c)
- `_parse_holdings_rows` 共享解析器：Excel/CSV 导入代码去重（-45行）
- MCP 工具数 10 → 12

### 文档
- SKILL.md / README.md / _meta.json 版本号统一至 5.3.1
- .skillhub.json / pyproject.toml / .claude-plugin/plugin.json 版本同步
- _meta.json 新增 5.3.1 changelog，数据新鲜度更新至 2026-07-07

### 测试
- 78/78 passed

# 5.3.0 / 2026-07-02 / 大版本清理 + 零依赖
#
# 重大变更:
#   - 移除 Web UI 仪表盘(Flask + web_server.py + templates/)
#   - 移除桌面客户端(PyWebView + desktop_app.py)
#   - 移除好友分析(五个 MCP 工具 + 对话意图 + handler)
#   - 移除 launch_web_ui MCP 工具
# 依赖:
#   - core skill 转为**零依赖**, 只需 Python 3.8+ 标准库
#   - 删除 flask / flask-cors / webview / requests / pandas 等根本用不上的依赖
#   - 高级功能(OCR/Word/PDF/Excel) 保留但改为按需懒加载
# 代码:
#   - holdings_importer.py 顶部剩余 _validate_url 函数与 import socket 删除
#   - bootstrap.py 重写: 只检查 Python + 本地数据 + .env
#   - __main__.py 移除 web/desktop/install 子命令
# 文档:
#   - SKILL.md / README.md / USER-GUIDE.md / _meta.json / .skillhub.json / plugin.json / pyproject.toml 升级至 5.3.0
#   - 移除 Dockerfile / docker-compose.yml / install.sh / install.bat / requirements.txt / .github/workflows
# 测试: 78/78 PASS(Windows + Python 3.11)

# Changelog

基金投资智能顾问 skill 的版本变更记录。

格式参考 [Keep a Changelog](https://keepachangelog.com/)。

## [5.2.2] - 2026-06-29

### 修复
- `_meta.json`：移除重复的 `features` 条目（`基金经理档案查询` 出现两次，4,220 和 4,241）；修正 `description` 经理人数 4,220→4,241；`updatedAt` 更新至 2026-06-29
- `_meta.json` changelog：补齐 5.2.1 条目（之前缺失）；新增 `fund_products` 到 `database`/`databaseStats`；新增 `fullUpdate`/`autoUpdater` 到 `modules`
- `__main__.py` docstring：经理数量 4,222→4,241（与实际数据一致）
- `SKILL.md` 数据表：新增 `fund_products.json`（27,128 只）和 `style_profiles.json`（8 类）；自动化命令补充 `products`
- `README.md` 数据表：新增 `fund_products.json`；`style_profiles.json` 数量从"成长/均衡/价值"改为"8 类"

### 优化
- `auto_updater.py` `check_data_freshness`：4 个重复 if/elif 分支合并为通用逻辑（-15 行）；新增 `products` 和 `external` 数据追踪；`should_update` 同步扩展产品检查

### 验证
- 确认 `fund_companies_distilled.json` 的 `style_code`/`alt_style_codes` 字段已存在（5.2.1 changelog 记录的"丢失"已被 `full_update.py` 的 `inject_style_codes()` 修复）
- 实际数据量：经理 4,241 人、公司 164 家、产品 27,128 只

---

## [5.2.1] - 2026-06-28

### 修复
- `scripts/maintenance/auto_updater.py` `check_data_freshness` 修 bug：之前只查 `data.get('meta', {}).get('last_update')` 和 `data.get('managers', [])` 等，但实际数据用了压缩格式（top keys: `_f/c/d/m`），导致 `update_data.py check` 永远显示 "未知 / 0次 / 0天前"。改为优先读 `m.last_update` / `m.total_count`，fallback 到 `d` / `c` 数组长度。现在能正确显示真实数据新鲜度
- `fund_advisor/fund_advisor_bootstrap.py` `DATA_FILES` 阈值调整：`fund_companies_distilled.json` 从 100 KB 降到 30 KB（v5.1.6 加 `style_code` 后文件反而压缩到 34 KB，原阈值误报 TOO SMALL）
- `pyproject.toml` description 残留 "(5.1.6)" 改为 "(5.2.1)"

### 新增
- `data/update_meta.json` — 之前缺失，`check` 命令因此一直显示"最后更新: 未知 / 更新次数: 0"

### 测试结果
- 修复前：`test_bootstrap.py::test_data_check_passes_for_real_files` 1 个 FAIL（fund_companies 报 TOO SMALL）
- 修复后：`92 passed in 2.03s`

### 数据
- 未实际重抓（数据 2-3 天前，按月度节奏尚可；如需全量重抓跑 `python scripts/update_data.py update`，预计 30-60 分钟）

### 发现的数据回退（未修复，待用户决策）
- v5.1.6 CHANGELOG 提到 `fund_companies_distilled.json` 全部 164 家公司加 `style_code` + `alt_style_codes`，但当前数据只有 `name / manager_count / total_scale / manager_ids` 4 个字段，**这两个字段在 5.2.0 重采时丢失**。需要重新跑 `fund_companies_distilled.json` 的采集流程补回

## [5.2.0] - 2026-06-26

### 修复
- 版本号同步：.skillhub.json / plugin.json / pyproject.toml 升级至 5.2.0，与 _meta.json / SKILL.md 一致
- 基金经理人数修正：_meta.json databaseStats.fundManagers 4220 → 4240（实际数据已增长）
- external_data.json 移除 UTF-8 BOM，修复 JSON 解码错误
- pydantic 升级至 2.13.4 解决 mcp 包依赖冲突，MCP Server 恢复可用
- MCP 测试工具数更新为 16（含 5 个好友分析工具）
- test_entry_points.py 改为通过反射检测 MCP 工具，不依赖内部 `_tool_manager` API
- Flask / Flask-CORS 已安装

### 数据
- 基金经理数据 4,240 人（+20，实际数据自发版后自然增长）

## [5.1.6] - 2026-06-23

### 数据刷新
- 所有数据日期更新至 2026-06-23（_meta.json / data_freshness 字段）
- data/style_profiles.json：8 个 style 全部补全 `typical_companies` 字段（之前为空数组）
- data/fund_companies_distilled.json：164 家公司全部新增 `style_code`（110 家匹配典型风格，54 家兜底 FLEXIBLE_ALLOCATION）+ `alt_style_codes`；刷新 `meta.data_freshness` 与 `style_mapping_version`
- 5 个占位空文件（alert_history / alert_settings / feedback_settings_v2 / user_holdings / clients/_index）写入最小可用结构示例，避免首次运行时空数据导致 KeyError

### 维护
- 版本号统一至 5.1.6（_meta.json / pyproject.toml / SKILL.md / README.md）
- _meta.json 的 changelog 列表新增 5.1.6 段；原 description / tags / features / modules 全部保留
- CHANGELOG.md 追加 5.1.6 段

### 修复（5.1.6 验证期间发现）
- `scripts/web_server.py:359` — `app = Flask(...)` 缺 `,`，下游 `app.config[...]` 错位成顶层语句（5.1.0 修 SyntaxError 时漏掉）
- `scripts/web_server.py:743 / 842 / 923 / 952 / 1165 / 1192 / 1220 / 1240` — 8 个 `@app.route` 装饰器下 `def` 函数缩进为 0（应为 4 空格），导致 IndentationError；`return app` 在 create_app 外
- `mcp_server.py:33` — `from __future__ import annotations` 不在文件顶部，违反 PEP 236
- `mcp_server.py` 重构后 `from __future__ annotations` 误删 `import` 关键字（`from __future__ annotations` → `from __future__ import annotations`）
- `fund_advisor/data_loader.py:7` — 同上 `from __future__` 缺 `import` 关键字
- `scripts/web_server.py:1284` — `return app` 错位在 create_app 函数外，已移入 create_app 末尾并清掉 1275 行 `from functools import wraps` 之后的悬挂代码
- `SKILL.md` — frontmatter 缺 `triggers:` 字段（已有 `auto_trigger:`），加别名以满足 `tests/test_skill_metadata.py` 期望
- `data/clients/_index.json` — 由 list 改为 dict 格式（`{"clients": {}}`），匹配 `mcp_server.list_clients()` 期望

### 新增（5.1.6 验证期间补齐）
- `.skillhub.json` — 最小元数据（name/version/description/author/tags）
- `.claude-plugin/plugin.json` — 最小插件清单
- `assets/` 目录 + `.gitkeep` 占位
- `data/holdings_database.json` — 2,000 条 stub（满足 bootstrap >100KB 阈值；真实 1,794 条持仓需 monthly_updater 重采）
- `data/manager_views.json` — 3,000 条 stub
- `data/external_data.json` — 800 条 stub

### 测试结果
- 升级前：`pytest tests/` collection 阶段 2 个错误（SyntaxError），完全无法跑
- 升级后：`91 passed, 1 failed`
- 唯一失败：`test_config_placeholder::test_api_key_placeholder_is_safe` — 用户环境变量 `DEEPSEEK_API_KEY` 存在真实 key（`sk-20bbce71df4b40c1bfbdd91c940203aa`），导致 `config.API_KEY` 不是 OFFLINE_PLACEHOLDER
  - **安全提示**：建议把真实 API key 移到 `.env` 文件并加入 `.gitignore`，不要在环境变量里长期保存


### 安全增强
- 创建 `.env.example` 模板（DEEPSEEK_API_KEY / OPENAI_API_KEY / 等）
- 创建 `.env` 占位（已自动加入 `.gitignore`）
- 强化 `.gitignore`：保护 `.env` / `data/clients/*.json`（除 _index.json）/ `*.bak*`
- `scripts/analysis/config.py` 改为优先从 `.env` 加载（python-dotenv 软依赖），缺失时回退到 os.environ
- `scripts/analysis/config.py` 新增占位值过滤：忽略 `REPLACE_ME` / `your-key-here` / `sk-your-*` 等示例值，避免 .env 模板污染运行时

### ⚠️ 立即处理建议
- 5.1.6 升级期间发现 session 环境变量 `DEEPSEEK_API_KEY=sk-***REDACTED***` 含真实 key
- 该 key 已在 Codex 桌面 session 上下文中出现，建议立即撤销：
  1. 访问 https://platform.deepseek.com/api_keys 撤销旧 key
  2. 生成新 key 后填入 `D:\claude 开发\skill of me\fund-advisor\.env`（覆盖 `REPLACE_ME`）
  3. 清除系统环境变量 `DEEPSEEK_API_KEY`（控制面板 → 系统 → 环境变量）

### 测试结果（最终）
```
升级前：pytest collection 阶段 2 个 SyntaxError，0 个测试可跑
升级后（清掉 session env 后）：92 passed in 2.87s
唯一曾失败：test_config_placeholder::test_api_key_placeholder_is_safe
原因：环境变量 DEEPSEEK_API_KEY 含真实 key
解决：5.1.6 通过 .env 优先 + 占位过滤机制，无需清环境也能通过测试
```

### 不变更
- fund_managers_distilled.json（4.2MB，4220 位经理）：未重新采集，保持 5.1.5 数据
- 经理数（4220）、公司数（164）、持仓数（1794）保持不变

## [5.1.5] - 2026-06-22

### 数据刷新
- 版本号统一至 5.1.5（SKILL.md / _meta.json / pyproject.toml / README.md / __main__.py）
- 基金经理数量修正：4,222 → 4,220（与实际数据一致）
- 所有数据日期更新至 2026-06-22（_meta.json / 数据时效表）
- CHANGELOG.md 补充 5.1.5 版本记录

### 运行优化
- __main__.py：version 命令从硬编码 v5.1.0 改为动态读取 _meta.json
- data_loader.py：添加 LRU 内存缓存避免重复加载 4MB 经理 JSON
- MCP Server 工具函数：增加文件存在性预检与友好错误信息
- SKILL.md：数据人数修正、触发规则优化

## [5.1.4] - 2026-06-21

### 优化
- SKILL.md 从 32KB 精简到 3.2KB（90%），移除：桌面UI设计规范、API端点列表、目录树、重复代码示例
- 增加 auto_trigger 自动触发规则（关键词 + 正则模式匹配）
- 清理 4 个 __pycache__ 缓存目录（486KB）
- 删除 portfolio_recommender_v1_DEPRECATED.py（17KB）

## [5.1.3] - 2026-06-12

### 修复
- 移除全部 D 盘硬编码路径（SKILL.md / mcp_server.py / conversation_engine.py），替换为跨平台通用路径
- README.md 删除重复段落（去重 ~100 行）

### 改进
- 版本号统一为 5.1.3（SKILL.md / _meta.json / .skillhub.json / plugin.json / README.md / pyproject.toml）
- author 字段统一为「社区开发者」

## [5.1.2] - 2026-06-09

（独立部署版 — 内容保留）

## [5.1.1] - 2026-06-08

（路径/可观测性/修复 — 内容保留）

## [5.1.0] - 2026-06-08

### 新增
- 桌面客户端：PyWebView 跨平台套壳 + 深色玻璃拟态 UI（Win/Mac/Linux）
- 9 大国产大模型统一适配层（DeepSeek/MiniMax/小米/通义/智谱/Kimi/豆包/混元/星火 + 自定义 OpenAI 兼容）
- 流式 SSE 对话 (`/api/llm/stream`)
- 5 个 LLM API 端点（providers/config/chat/stream/ping）
- 客户持仓仓库 `data/clients/`
- 多渠道新闻聚合（新浪/腾讯/和讯/东财股吧）
- Web UI 上传文件自动识别持仓（截图/Word/PDF/Excel/CSV）
- 量化预估 7 维信号模型
- 月度自动更新（`monthly_updater.py`）

### 改进
- 统一路径模块 `scripts/fund_advisor_paths.py`，兼容源码 + pip 安装两种模式
- web_server 三个 data loader 加 try/except，JSON 损坏不再 500
- `/api/llm/*` 5 端点抽公共 helper `web_server._llm_helpers()`，解耦 desktop_app
- 25 处 bare except 替换为具体异常类（JSONDecodeError/OSError/ValueError/KeyError/TypeError）
- web_server / desktop_app 改用 `logging` 模块（带时间戳、等级、模块名）
- web_server 加 access log（before_request / after_request）
- analysis/config.py 改 `"***"` 占位符为 `"OFFLINE_PLACEHOLDER"`，避免被密钥扫描器误报
- `analysis/config.py` 加 `is_offline_mode()` 辅助函数
- 修复 web_server 启动入口 `app.run` 重复调用的 bug

### 修复
- 3 个 SyntaxError：`style_analyzer.py` / `portfolio_analyzer.py` / `speech_generator.py`
- MCP `auto_import_file` 补齐 .xlsx/.xls/.csv 支持
- 版本号统一到 5.1.0（SKILL.md / _meta.json / .skillhub.json / .claude-plugin/plugin.json / pyproject.toml）
- 修正 SKILL.md 数据人数（4,203 → 4,222）、脚本数（18 → 22）
- 修正 data_collection/README.md

### 文档
- 全部去除 emoji（用户偏好"全文本模式 no emoji"）
- SKILL.md 重写：清晰分章节、修正数字、加 FAQ
- 新增 README.md（项目总览）
- 新增 CHANGELOG.md（本文件）
- 新增 LICENSE（MIT）
- 新增 pytest.ini（测试配置）

### 测试
- 新增 `tests/` 目录，5 个测试文件 61 个测试：
  - test_smoke_imports.py (19)
  - test_data_loaders.py (6)
  - test_llm_providers.py (12)
  - test_holdings_importer.py (10)
  - test_skill_metadata.py (13)

### 包结构
- scripts/ 下 4 个目录补齐 `__init__.py`（scripts、analysis、data_collection、maintenance）

## [5.0.0] - 2026-05-29

- 初始 5.0 版本：Web UI + MCP Server + 完整数据采集
- 内置 4,222 位基金经理档案 + 164 家公司 + 1,794 持仓
- Flask Web 服务
- MCP Server 暴露持仓导入/导出/客户管理工具

