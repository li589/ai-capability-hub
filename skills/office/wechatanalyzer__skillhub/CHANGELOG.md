# 微信聊天分析助手 - 版本变更日志

## v2.8.0 (2026-08-17) - 健壮性升级：零警告 + Python 3.15 兼容 + 裸 except 收紧

### 🐛 修复

- **非法转义序列** — `core/utils.py:216`：分句正则 `r'[…""''…\[\]]+'` 中内容含 `''`，把单引号 raw string 提前截断，后半段隐式拼接成**普通字符串**，`\[` 触发 DeprecationWarning（Python 3.12+ 升级为 SyntaxWarning，未来将成 SyntaxError）。改为三引号 raw string，正则实际值不变。
- **Python 3.15 日期解析行为变更** — `scripts/calendar_manager.py:_parse_date`：`%m-%d` 无年份格式依赖 strptime 默认年份 1900 再 replace，Python 3.14 起产生 DeprecationWarning、3.15 起行为将变更。现改为正则校验月-日后用参考年份显式构造 `datetime`，语义不变（"01-01" + 参考 2026 → 2026-01-01），闰年 02-29 非法时如实返回 None。

### 🛡️ 健壮性

- **7 处裸 except 收紧**（活跃代码，archive_v1 归档不动）：
  - `scripts/text_analyzer.py` ×3（datetime.fromisoformat）→ `except ValueError`
  - `scripts/main_setup.py`（rglob 扫描）→ `except OSError`
  - `scripts/calendar_manager.py`（冗余外层 try 一并移除）
  - `scripts/mirofish/services/simulation_config_generator.py` ×2、`oasis_profile_generator.py` ×1（json.loads 修复链）→ `except json.JSONDecodeError`

### 🧪 测试强化

- 新增 `tests/test_compile_smoke.py`：
  - `test_all_modules_compile_without_warnings` — 自动扫描全部 .py，`compile()` + 警告升级为错误（非法转义无处遁形）
  - `test_no_bare_except_in_active_code` — 裸 except 防回归
  - `test_version_single_source_consistent` — `core/version.py` / config.json / SKILL.md frontmatter 三处版本一致
- 全量 **329 passed**（326→329，新增 3 项烟囱测试），Python 3.11.9 / 3.14 双版本零警告

### 📦 工程

- `clean.py` 新增 `--check` 模式：只检查不删除，退出码 1=有二进制残留（上传前必跑）
- 版本号统一至 2.8.0（core/version.py 单一来源 + config.json + SKILL.md + run_tests.py）
- 补记 CHANGELOG 缺失的 v2.7.0 条目

---

## v2.7.0 (2026-08-13) - 测试优化 + scheduler 建表修复（补记）

- **修 scheduler 缺建表 bug** — `scripts/scheduler.py` 此前 `__init__` 只初始化 APScheduler，从未建 `scheduled_tasks` 表，`add_job`/`list_jobs` 首次调用抛 `no such table`；现新增 `_init_db`
- **补 30 个测试** — `test_calendar_manager.py`（日期解析/事件类型/重要性/完整提取）+ `test_scheduler.py`（建表/增删查）
- 测试 272 → **302 通过**

---

## v2.6.0 (2026-08-13) - 上传被拒修复（.pyc / .db 二进制清理）

### 🚫 修复上传被拒

- **`.pyc` 字节码治本** — 7 个包 `__init__.py` + `scripts/main.py` + `run_tests.py` 顶部加 `sys.dont_write_bytecode = True`；`run_tests.py` 原 `os.environ.setdefault("PYTHONDONTWRITEBYTECODE","1")` 无效（CPython 仅启动时读环境变量），改为直接设 `sys` 标志。
- **`.db` 数据库治本** — 新增 `core/data_paths.py` 统一运行时路径解析，`ZepLocalGraph` / `DataManager` / `CalendarManager` / `SchedulerManager` 默认数据库路径从 `data/mirofish_graph.db`、`data/sessions/chat_history.db` 迁移到系统 tempdir（`%TEMP%/wechat-analyzer/`），支持 `WECHAT_ANALYZER_DATA_DIR` 环境变量覆盖；仅当传入绝对路径时才使用 config 的 `db_path`。
- **`clean.py` 扩展** — 新增 `clean_db()` 清理 `.db/.sqlite/.db-wal/.db-shm`，加 `--keep-db` 参数；docstring 与提示同步更新。

### ⚙️ 工程说明

- 验证：`python run_tests.py` 全量 **272 通过 0 失败 0 错误**，测试后无 `.pyc`/`__pycache__`/`.db` 残留。
- 机制记录：CPython `SourceFileLoader.get_code()` 在「执行模块代码之前」写 pyc，故 `__init__.py` 内 `sys.dont_write_bytecode` 拦不住其自身字节码，只能拦后续 import 的子模块——彻底清零仍需环境变量或 `clean.py` 兜底。

---

## v2.5.0 (2026-08-13) - 五大 bug 修复 + 友好错误全链路 + 性能优化

### 🐛 修复（5 个真实 bug）

- **「非常」窗口索引错位** — `analyzers/sentiment_analyzer.py`：`_is_negated` 判断「非」后是否接「常」时，`re.finditer` 的位置是相对 12 字符窗口（`context`）的，却用 `text[m.end()]` 读原文——情感词距句首 >12 字符时读到不相关字符，「非常开心」被误判否定。
- **RAG 角色过滤永不匹配** — `rag/retriever.py`：`rag_predictor` 传 `sender_filter="other"`，但索引时 metadata 存的是原始 sender 名（如「小王」），`where={"sender": "other"}` 永远匹配不上 → RAG 一直空检索回退。现索引写入 `sender_role` 元数据，`self`/`other` 按角色过滤（其他值仍按原始名精确匹配，向后兼容），旧向量库无该字段时自动去过滤重试。
- **msg_type 键名丢失** — `core/message.py`：旧生产者（file_importer/data_manager）输出 `msg_type` 键，`from_dict` 只读 `message_type`，导致 image/voice/system 消息全部静默降级为 text。现两键均接受，规范键优先。
- **MBTI 失败显示崩溃** — `scripts/main.py`：分析器异常时 `run_all` 返回 `{"error": ...}` 错误桩，`_display_v2_results` 直接 `mbti['type']` 触发 KeyError 中断整个报告展示。现错误桩降级显示「分析失败 + 原因」，同时删除永不可达的 `AnalysisResultStub`。
- **无发送者行 self/other 颠倒** — `scripts/data_manager.py`：注释说「假设没有发送者的是自己的消息」但代码写 `sender='other'`（与注释相反），导致 self/other 统计颠倒、情感/人格分析对象错误；`len(line) < 100` 在正则 `{1,20}` 下不可达一并清理。另新增：纯时间戳行（`2024-01-01 12:30:00`）与分隔线（`----`）不再被误解析为消息。

### ✨ 新增功能

- **友好错误提示全链路接入** — `friendly_errors.py`（此前写了但从未被 CLI 使用）接入 `main()` 全局异常处理：缺依赖/坏文件/权限/编码等输出中文「原因 + 解决」；`--debug` 可看完整堆栈。补充 jinja2/python-docx/python-pptx/openpyxl 缺失模式；修复「JSONDecodeError 命中前一条 'Expecting value' 模式导致缓存损坏条目不可达」的遮蔽问题。
- **`predict-v2 --seed` 可复现预测** — `predictors/mirofish_predictor.py` 用独立 seeded 随机源替代全局 `random.choice`：默认 seed=0 结果稳定，`--seed N` 指定种子，测试/报告不再 flaky。
- **版本号单一来源** — 新增 `core/version.py`，CLI 输出 / JSON 导出 / HTML 报告 / config.json 统一读取；此前十余处版本字符串（config.json 还停在 2.3.0）升级常漏改。

### ⚡ 性能优化

- `core/utils.py`：`pseg.cut`（词性标注，从未消费词性）→ `jieba.cut`，分词快数倍
- `sentiment_analyzer.py`：情感词典首字索引（只扫描首字出现在文本中的词条，替代每消息全词典线性扫描）；正面/负面高频词改用 `Counter` 按频次排序（原 `set()` 输出任意顺序）
- `inference_analyzer.py`：行为信号集合预构建（原在消息 × 行为内层循环反复 `set()` 重建）
- `file_importer.py`：`.doc/.ppt` 二进制兜底的中文提取重写（原只保留 ASCII 字节，中文全丢；现 utf-8/gb18030/utf-16-le 多编码尝试 + 常见字评分）；`.xlsx` 去掉裸单元格重复计数；`except Exception` 吞异常改为具体异常
- `ensemble.py`：删除计算后从未使用的 `recent_text` 死代码；`timing.py` 简化冗余分支

### 🧪 测试与工程

- **测试基建修复**：`run_tests.py` 此前只发现 6 个子目录，`tests/test_friendly_errors.py` 从未被执行——顶层函数式测试现通过 `FunctionTestCase` 纳入；docx/pptx/xlsx 测试缺依赖时优雅跳过（此前 7 个 ERROR）
- 新增 37 个回归测试：情感「非」窗口（长/短消息）、否定窗口、高频词频次、RAG 角色过滤 7 例、Message msg_type 兼容 3 例、main 展示容错 6 例、MiroFish 确定性 3 例、友好错误新模式 6 例、二进制中文提取 5 例、data_manager 垃圾行 2 例
- 全套 **272 个测试通过，0 失败 0 错误**（v2.4.0 时为 227 通过、7 错误）

---

## v2.4.0 (2026-08-05) - 情感分析 jieba 修复 + 测试补全

### 🐛 修复

- **情感分析在 jieba 安装后失效** — `analyzers/sentiment_analyzer.py` 重写为原文扫描（不再依赖分词结果）：
  - 「非常开心」被程度副词「非常」的「非」字误判为否定 → 否定判断改为「非」仅当后不接「常」才算否定
  - 「我不开心」因 jieba 分词过滤停用词删掉否定词「不」导致否定识别失效 → 否定/程度判断改为原文字符窗口，jieba 装与不装结果一致
- **立场识别「我反对」被判 neutral** — `analyzers/interpretation_analyzer.py` 正面词典单字「对」子串命中「反对」里的「对」；移除单字「对」，改配「对的/没错/说得对」
- **词典清理** — 意图「来吧」、主题「爸妈」重复项；NER 金额正则 `[万千百千]` 错字改为 `[万亿千百]`
- **运行时 SQLite 库混入交付物** — `data/chat_history.db` 上传被文件类型校验拦截（".db 不允许"）：统一默认 db 路径到已忽略目录 `data/sessions/`（`config.json` + `data_manager.py` / `calendar_manager.py` / `scheduler.py` / `main_setup.py`），`calendar_manager`/`scheduler` 补 `mkdir(parents=True)`；`gitignore_rules.txt` 补 `data/*.db`；物理移除运行时产物

### 🧪 测试与工程

- 新增 75 个测试用例，覆盖 4 个此前无测试的模块：
  - `interpretation_analyzer`（27）：意图识别 / NER Lite / 主题抽取 / 立场识别
  - `data_manager`（16）：4 种文本格式解析 / 聊天存储读取 / 分析结果存取
  - `vector_store`（11）：metadata 清洗 / CRUD / 缺依赖友好报错（mock chromadb）
  - `rag_predictor`（21）：查询构造 / 候选提取 / 长度匹配 / 重排序去重 / 兜底降级（mock 初始化）
- 全套 **235 个测试通过，0 失败 0 错误**（v2.3.0 时为 160 通过）
- **运行优化**：安装缺失的必需依赖（jieba / flask / flask-cors），`doctor` 不再报必需项缺失，`analyze-v2` 实际跑通 8 个分析器

---

## v2.3.0 (2026-08-01) - 时间感知对话预测 + 及时性提升

### ✨ 新增功能

- **`core/timing.py`**：统一提取聊天时间特征（最后消息距今、紧急度、时间段、周末/工作日、密集对话节奏）
- **Rule 预测器时间适配**：隔太久主动找回联系、即时短回复、夜间关怀、周末轻社交、连续对话延续
- **Ensemble 时间适配**：隔太久找回联系话术加分、即时/尽快场景短回复加分、夜间关怀加分
- **`predict-v2` 输出 `[回复时机]` 提示**：立即回复 / 尽快回复 / 今天内回复 / 隔太久先主动找回联系
- **新增 8 个测试**：时间特征、及时性话术、集成上下文传播

---

## v2.2.0 (2026-07-28) - 多格式导入 + 智能预测强化

### 🐛 修复

- **Word/PPT/Excel 文字导出异常** — `scripts/file_importer.py` 全面重写：
  - 旧版 `.doc` / `.ppt` 缺失解析实现且无任何降级路径，现在补齐 antiword / textract / 二进制可打印片段三层兜底
  - 旧版 `file_importer.py` 直接按 `'.doc'` 后缀走 textract（包未装就直接 `print` 后 `return []`，无任何可读结果）
  - 旧版没有 `.pptx` / `.xlsx` / `.xls` 处理分支，全部兜底为文本或直接 `return []`
  - PDF 仅 pdfplumber 单点依赖；现增加 PyPDF2 / pypdf 双兜底
  - 旧版异常时直接 `print` 后 `return []`，无 metadata 也不区分错误；现在统一返回 system 消息 + `parse_error` metadata
- **Word 解析不完整** — 现在 `.docx` 解析同时输出段落、表格、页眉、页脚、文本框，metadata 标记 `doc_section`
- **Excel 解析不完整** — `.xlsx` 现在逐单元格 + 行汇总双层输出，metadata 含 sheet 名 + 单元格坐标
- **PPT 解析不完整** — `.pptx` 现在按 slide 索引输出所有 text_frame + 表格 + 演讲者备注，metadata 含 `ppt_slide` + `ppt_section`

### ✨ 新增功能

- **多格式统一 chat 输出** — 所有 docx / xlsx / pptx / pdf 解析结果统一为
  `{timestamp, sender, content, msg_type, file_path, metadata}` 格式，
  可直接送入 `analyze-v2` / `predict-v2` 链路
- **Rule 预测器上下文感知** — `predictors/rule_predictor.py` 升级到 v2.2.0：
  - 句末意图识别：question / request / complaint / gratitude / invitation / statement 6 类
  - 风险信号检测 + 自动切换防守话术
  - 暖心/共情/防守 3 套情感话术
  - 30+ 关键词软触发（频次加权）
  - 风格适配：基于最近 5 条我方回复（短/长/疑问/感叹）做风格匹配
- **Ensemble 智能融合** — `predictors/ensemble.py` 升级到 v2.2.0：
  - 上下文匹配加成：与最近对方消息语义匹配的预测获得 +0.05 加权
  - 风险规避：风险场景下减分积极策略
  - 风格一致性：与历史我方风格不一致的预测降权
  - 多策略加成（被多种预测器独立选中 → 提升）
- **RAG 智能版** — `predictors/rag_predictor.py` 升级到 v2.2.0：
  - 智能查询构造：最近 N 条对方消息 + 关键词权重
  - 长度匹配：与最近我方回复长度相当的优先
  - 多样性去重：避免返回几乎相同的回复
  - 双检索：检索 "对方问 + 我方答" 模式
- **可读性优先** — 所有解析器失败时返回 system 类型消息 + 中文友好提示，不再裸抛 stack trace

### 🧪 测试与工程

- 新增 29 个测试用例（`tests/test_scripts/test_file_importer.py` + `tests/test_predictors/test_rule_predictor_v22.py`）
- 覆盖 docx / xlsx / pptx / pdf / txt (utf-8 + gbk) / json / 错误路径 / 上下文意图 / 风险信号 / 情感驱动 / 风格匹配
- 全部 153 个测试通过，0 失败 0 错误（v2.1.0 时为 124 通过）

## v2.1.0 (2026-07-18) - 修复补齐 + 报告与体验增强

### 🐛 修复

- **graph-stats 崩溃修复** — 补齐 README/SKILL.md 已宣传但缺失的 `mirofish/` 顶层包：
  - 新增 `mirofish/__init__.py`、`mirofish/core/__init__.py`、`mirofish/core/zep_local.py`
  - `ZepLocalGraph(db_path=None)` 默认 `data/mirofish_graph.db`，仅用 stdlib sqlite3 + jieba，零新依赖
  - 实体 = 消息发送者 + jieba 高频关键词；关系 = 同一消息内实体共现（mentions / co_occurs）；记忆 = 消息文本摘要（内容哈希去重，重复 build 幂等/增量）
  - 接口：`build_from_messages()` / `get_stats()` / `get_graph()`，兼容 main.py 现有 graph-stats 展示代码
- **输入文件编码自动检测** — `core/utils.py` 新增 `read_text_auto()` / `decode_bytes_auto()`，
  按 utf-8-sig → utf-8 → gb18030 顺序尝试解码；应用于 `scripts/main.py::_load_messages`
  的 `--input` 分支和 `scripts/file_importer.py` 的 txt/md 读取；失败时给出友好中文错误，
  GBK 导出的聊天记录不再 `UnicodeDecodeError` 崩溃
- **大五人格归一化校准** — `analyzers/bigfive_analyzer.py` 改为基于信号量的对数平滑映射
  （以 50 为中点、极性比例偏移、信号越少越收缩、最多 ±35），小样本不再轻易饱和 100%，
  示例数据各维度落在合理分散区间
- **MBTI 可解释性** — `_display_v2_results` 中稳定性 <50% 时追加中文提示
  "样本较少或特征不明显，结果仅供参考"

### ✨ 新增功能

- **分析进度反馈** — `AnalyzerRegistry.run_all` 新增可选 `progress_callback` 参数（向后兼容，
  默认 None）；`analyze-v2` / `predict-v2` 运行时逐个显示 `[i/6] sentiment ... 完成 (0.12s)`
- **`analyze-v2 --export PATH.json`** — 导出全部分析器结果（`AnalysisResult.to_dict()`）
  + 消息统计元数据（总数/双方消息数/时间跨度）为 JSON
- **`analyze-v2 --html PATH.html` + 新命令 `report-v2`** — 新增 `scripts/v2_report_generator.py`，
  生成完全自包含的单文件 HTML 报告（内联 CSS + Python 生成 SVG 雷达图/环形图/条形图，
  零 CDN、零外部资源、离线可开、中文界面）；内容含一句话总结、MBTI 卡片、大五雷达、
  情感环形图 + 正负面高频词、对话模式统计卡片、风险分级配色卡片、场景权重条形图、生成时间戳；
  `report-v2` 从 data_manager 读取最近一次 analyze-v2 结果，输出到 `data/reports/`，
  无 v2 结果时给出明确提示
- **新命令 `demo`** — 一键分析内置示例 `tests/fixtures/sample_chat.txt`，终端展示 +
  在 `data/reports/` 生成 HTML 报告并打印路径
- **新命令 `doctor`** — 环境自检：Python 版本 ≥3.8、jieba（必需）、flask/python-docx/python-pptx
  （v1 功能）、sentence-transformers/chromadb（RAG 可选）、config.json 可解析、data/ 目录可写、
  stdout 编码，逐项 OK/警告并给出修复建议
- **交互式向导** — `python scripts/main.py` 无参数运行时进入向导（`-h/--help` 行为不变）：
  欢迎语 → 粘贴聊天记录（END 结束）→ analyze-v2 → 询问是否生成 HTML 报告（y/N）；
  输入为空时优雅退出
- **v2 终端报告"一句话总结"** — 基于各分析器结果规则生成 1-2 句中文摘要，
  放在 `=` 分隔线内（`scripts/v2_report_generator.py::generate_v2_summary`，终端与 HTML 共用）
- **predict-v2 备选去重** — `predictors/ensemble.py` 融合时按规范化文本
  （去空白/标点/大小写差异）合并，备选列表不再出现重复模板

### 🧪 测试与工程

- 新增单元测试：`tests/test_core/test_utils.py`（编码检测）、
  `tests/test_mirofish/test_zep_local.py`（建库/统计/幂等/增量/兼容）、
  `tests/test_scripts/test_v2_report_generator.py`（HTML 报告 smoke test + 一句话总结）
- `run_tests.py` 新增 "MiroFish 图谱" 与 "脚本/报告" 套件（124 通过 / 0 失败 / 5 跳过，RAG 依赖未装跳过属正常）
- 版本号统一升级为 2.1.0：`config.json`、各 `__init__.py`、`scripts/main.py`
- 完全向后兼容：v1.2.0 / v2.0.0 所有命令行为不变；所有新终端输出走 `_safe_emoji()`

## v2.0.0 (2026-07-09) - 模块化架构 + 本地 AI 增强

### 🎉 重大升级

v2.0.0 是 v1.2.0 之后的全面重构，**完全保留 v1.2.0 兼容性**，新增模块化架构和本地 AI 能力。

### ✨ 新增功能

#### 核心抽象层（`core/`）
- **Message 统一数据模型** — 替代 v1.2.0 的 dict 形式，支持类型安全的 dataclass
- **AnalysisResult / PredictionResult 统一结果** — 所有分析器和预测器输出统一格式
- **AnalyzerBase 抽象基类** — 所有分析器实现统一接口
- **PredictorBase 抽象基类** — 所有预测器实现统一接口
- **AnalyzerRegistry 注册中心** — 统一调度多个分析器

#### 6 个独立分析器（`analyzers/`）
- **MBTIAnalyzer** — 新置信度算法（维度差距 + 样本量）
  - 旧版 `min(90, 50 + total_score * 1)` 几乎不会低于 60%
  - 新版 `50 + min_gap * 30 + size_factor * 20` 范围 20-95
  - 新增稳定性评分（基于前后半段一致性）
- **BigFiveAnalyzer** — 5 维归一化 + 雷达图数据
  - 补全 neuroticism low 词（冷静、镇定、平和、从容）
- **SentimentAnalyzer** — 完全重写，支持：
  - **jieba 精准分词**（如可用）+ 改进的 fallback 分词
  - **HowNet 情感词典**（446 正面 + 441 负面词条，含强度）
  - **否定识别**（修复 v1.2.0 的"我不开心"误判 bug）
  - **程度副词加权**（很/非常/极其/稍微...）
  - **反讽检测**（虽然...但是... / 说是...其实...）
  - **Emoji 情感映射**（约 200 个 emoji）
  - **情感时间线**（按时序输出）
- **RiskAnalyzer** — 完全重写，支持：
  - **反讽识别**（"投资个生日礼物"等无害场景）
  - **否定排除**（"不[风险词]"模式）
  - **时序突发检测**（消息突然变密集 + 风险词 → 升级告警）
  - **三级风险等级**（low / medium / high）
  - **会话级累积**（风险词 ≥3 次才升级 high）
- **ScenarioAnalyzer** — 4 场景分类（romantic/work/social/important）
- **PatternAnalyzer** — 修复 v1.2.0 的 reply_speed 丢失 bug

#### 词典资源（`analyzers/lexicon/`）
- `hownet_positive.txt` — HowNet 正面情感词典（约 446 词条）
- `hownet_negative.txt` — HowNet 负面情感词典（约 441 词条）
- `negation_words.txt` — 否定词表（中文 + 英文 + 短语）
- `degree_words.txt` — 程度副词（含权重 0.5-3.0）
- `emoji_dict.txt` — Emoji 情感映射（约 200 emoji）
- `jieba_dict/user_dict.txt` — jieba 自定义词典（MBTI/网络用语/职场/投资等）

#### 3 个预测器 + 集成器（`predictors/`）
- **RulePredictor** — 16 MBTI × 5 模板 + 4 场景模板 + 12 关键词触发
- **RAGPredictor** — 基于历史相似对话的检索增强预测
- **MiroFishPredictor** — 8 性格 Agent × N 轮模拟 + 加权投票
- **EnsemblePredictor** — 加权融合：相同文本合并 + 多策略加成

#### RAG 引擎（`rag/`）
- **Embedder** — sentence-transformers 封装（支持 bge-small-zh / bge-base-zh / multilingual）
- **VectorStore** — ChromaDB 持久化
- **Retriever** — top-K 检索 + 元数据过滤 + 上下文窗口拼接
- **完全本地化** — 无需云端 LLM，零数据外传

#### MiroFish 本地化（`mirofish/`）
- **ZepLocalGraph** — 本地图谱（NetworkX + SQLite），替代 Zep Cloud
  - 实体识别（人名/事件/情绪）
  - 关系抽取（喜欢/讨厌/关心）
  - 时序关联
- **MiroFishBridge** — 统一入口
- **AgentFactory** — 8 种性格原型（主动/防守/中立/情感/幽默/理性/感性/实用）
- **Deliberation** — 多轮辩论 + 加权投票

#### 单元测试（`tests/`）
- 12 个测试文件，104 个测试用例，5 个跳过（依赖未安装）
- 关键测试：否定识别（修复 v1.2.0 bug）、MBTI 类型验证、风险检测反讽排除、reply_speed 修复等
- `run_tests.py` 一键运行

#### CLI 新命令
- `version` — 显示 v2.0.0 新特性
- `analyze-v2` — 模块化分析（jieba/否定识别/反讽）
- `predict-v2` — 三层融合预测（Rule + RAG + MiroFish）
- `graph-stats` — MiroFish 本地图谱统计

### ♻️ 重构

- **`text_analyzer.py` (588 行) → 6 个独立分析器** — 拆分为 mbti_analyzer / bigfive_analyzer / sentiment_analyzer / risk_analyzer / scenario_analyzer / pattern_analyzer
- **`conversation_predictor.py` (423 行) → 3 个预测器 + ensemble** — 拆分为 rule_predictor / rag_predictor / mirofish_predictor / ensemble
- **`scripts/main.py`** — 改为同时支持 v1.2.0 旧命令（`analyze/report/schedule/serve/calendar`）和 v2.0.0 新命令
- **`config.json`** — 加入 `rag` / `mirofish` / `privacy` 三个新配置块
- **`SKILL.md` / `README.md`** — 更新到 v2.0.0 文档

### 🐛 Bug 修复

| Bug | 修复 |
|---|---|
| `analyze_conversation_pattern` 中 reply_speed 字段计算后丢失 | PatternAnalyzer 正确返回 `reply_speed` 字段 |
| "我不开心" 被误判为 positive | SentimentAnalyzer 实现否定识别（窗口 + 子串 + 字符级 + 文本级 4 重检测）|
| 风险检测"投资理财"被误报 | RiskAnalyzer 加入 innocent_phrases（投资理财、投资个生日礼物等）|
| MBTI 置信度永远不低于 60% | 新算法 `50 + min_gap * 30 + size_factor * 20`，范围 20-95 |
| 大五 neuroticism 缺 low 词 | 补全冷静/镇定/平和/从容等 8 个 low 词 |
| 分词简陋（"我今天很开心"切成单 token） | 引入 jieba + 改进 fallback 分词（单字/2字/3字） |
| v1.2.0 MiroFish 是空壳（未真正调用） | v2.0.0 通过 MiroFishBridge 真正调用本地 Zep + Agent + Deliberation |

### 🔒 隐私升级

- `config.json` 加入 `privacy.telemetry=false`、`external_api=false`
- 所有 v2.0.0 模块完全本地化（除 RAG 首次下载 embedding 模型）
- LLM API 默认禁用
- MiroFish 默认关闭
- README 加入"100% 本地处理，零外部网络请求"声明

### 📦 依赖变化

#### 核心依赖
- 新增：`jieba>=0.42.1`（中文分词）

#### RAG 引擎（`requirements-rag.txt`，可选）
- `sentence-transformers>=2.2.2`（本地 embedding 模型）
- `chromadb>=0.4.22`（本地向量数据库）
- `numpy>=1.24.0`

#### Web 仪表盘（`requirements-web.txt`，v2.1.0 路线图）
- `fastapi>=0.104.0`
- `uvicorn>=0.24.0`

### ⏳ 延后至 v2.1.0

- FastAPI 后端 + Vue3 前端 + ECharts 可视化仪表盘
- WebSocket 实时进度推送
- 完整 ECharts 图表（情感时间线/人格雷达/热词云/关系演变图）

### 📊 测试结果

```
通过: 104
失败: 0
错误: 0
跳过: 5 (sentence-transformers/chromadb 未安装)
```

### 🗂️ 目录结构变化

```
wechat-analyzer/
├── core/                    # 🆕 核心抽象层
├── analyzers/               # 🆕 6 个独立分析器
│   └── lexicon/            # 🆕 词典资源
├── predictors/              # 🆕 3 个预测器 + Ensemble
├── rag/                     # 🆕 RAG 引擎
├── mirofish/                # 🆕 MiroFish 本地化
├── web/                     # 🆕 Web 层（v2.1.0）
├── tests/                   # 🆕 单元测试
├── scripts/                 # ♻️ 旧脚本（向后兼容）
│   └── archive_v1/          # 📦 v1.2.0 完整快照
├── config.json              # ♻️ v2.0.0 配置
├── requirements.txt         # ♻️ v2.0.0 依赖
├── requirements-rag.txt     # 🆕 RAG 独立依赖
├── requirements-web.txt     # ⏳ v2.1.0 Web 依赖
├── SKILL.md                 # ♻️ v2.0.0
├── README.md                # ♻️ v2.0.0
├── CHANGELOG.md             # 🆕 本文件
└── run_tests.py             # 🆕 测试运行脚本
```

### 🔄 迁移指南

#### 用户使用

```bash
# 旧用户（v1.2.0 兼容）
python scripts/main.py analyze --paste    # 完全兼容

# 新用户（v2.0.0 推荐）
python scripts/main.py analyze-v2 --paste # 体验新特性
python scripts/main.py predict-v2 --paste # 三层预测
```

#### 开发者

如需添加新分析器：
```python
from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult

class MyAnalyzer(AnalyzerBase):
    name = "my_analyzer"
    def validate(self, messages): ...
    def analyze(self, messages, **kwargs) -> AnalysisResult: ...
```

---

## v1.2.0 (2026-05-26) - 基础版本

- MBTI / 大五 / 情感 / 风险 / 日历 基础分析
- LLM API 增强（可选）
- MiroFish 群体智能引擎（高级功能）
- HTML / Word / PPTX 报告生成
- Flask Web 服务
- APScheduler 定时任务

### 已知 Bug（已在 v2.0.0 修复）

- `analyze_conversation_pattern` 中 reply_speed 字段计算后丢失
- "我不开心" 被误判为 positive
- MBTI 置信度永远不低于 60%
- 风险检测"投资理财"等无辜场景被误报
- v1.2.0 MiroFish 是空壳（未真正调用引擎）
- 分词简陋
