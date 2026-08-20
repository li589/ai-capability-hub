# 微信聊天分析助手 v2.5.0

**完全本地运行、模块化架构、AI 增强的隐私保护工具**

分析 MBTI 人格、大五人格、情感趋势、风险预警，生成可视化报告。
v2.5.0 修复 5 个真实 bug（「非常」窗口误判否定 / RAG 角色过滤失效 / msg_type 丢失 / MBTI 显示崩溃 / 无发送者行 self-other 颠倒），接入全链路友好错误提示与 `predict-v2 --seed` 可复现预测，测试 227+7 错误 → 272 全通过；
v2.4.0 修复情感分析在 jieba 下的否定/程度识别 bug，补全 4 个模块测试；
v2.3.0 新增时间感知对话预测与回复时机提示；v2.2.0 新增推演与信息解读；v2.1.0 新增 demo、环境自检、离线 HTML 报告。

## 🆕 v2.5.0 五大 bug 修复 + 友好错误 + 可复现预测

- 🐛 修复「非常开心」在长消息中「非」按错位索引误判否定（`sentiment_analyzer`）
- 🐛 修复 RAG `sender_filter="other"` 按原始昵称永远匹配不上 → 引入 `sender_role` 角色过滤 + 旧库自动降级
- 🐛 修复 `Message.from_dict` 只认 `message_type` 导致旧数据 image/voice/system 类型丢失
- 🐛 修复 MBTI 分析器失败时 `_display_v2_results` KeyError 中断报告展示
- 🐛 修复无发送者行 self/other 颠倒（注释与代码相反）+ 过滤纯时间戳行/分隔线
- 🛡 `friendly_errors.py` 接入 CLI 主入口：中文「原因+解决」提示，`--debug` 看完整堆栈
- 🎲 `predict-v2 --seed N` 可复现预测（MiroFish seeded 随机源，默认 seed=0 稳定）
- ⚡ 性能：`pseg.cut`→`jieba.cut`、情感词典首字索引、高频词 Counter 排序、二进制中文提取重写
- 🧪 测试 272 通过 / 0 失败 / 0 错误（修复 run_tests 漏跑顶层测试、缺依赖优雅跳过）

## 🆕 v2.4.0 情感分析与测试补全

- 修复「非常开心」被「非」字误判为否定、「我不开心」否定识别失效（jieba 装与不装结果一致）
- 修复立场识别「我反对」被判 neutral（正面词典单字「对」污染）
- 新增 `interpretation` / `data_manager` / `vector_store` / `rag_predictor` 共 75 个测试用例

## 🆕 v2.3.0 时间感知预测

- `core/timing.py`：统一计算消息紧急性、时间段、周末/工作日、连续对话节奏
- `predict-v2` 输出 `[回复时机]`：立即 / 尽快 / 今天内 / 隔太久先主动找回联系
- Rule 与 Ensemble 预测器都使用时间特征调整候选和置信度

---

## 🎉 v2.1.0 新特性

- 🧬 **补齐 `mirofish/` 本地图谱包** — 修复 `graph-stats` 崩溃（sqlite3 + jieba，零新依赖）
- 📄 **文件编码自动检测** — utf-8-sig / utf-8 / gb18030 自动识别，GBK 导出文件不再崩溃
- 📊 **大五人格校准** — 小样本不再轻易饱和 100%，各维度区分度更好
- 📈 **分析进度反馈** — `[i/6] xxx ... 完成 (0.12s)` 实时显示
- 💾 **结果导出** — `analyze-v2 --export result.json`
- 🌐 **单文件离线 HTML 报告** — `analyze-v2 --html report.html` / `report-v2`，零 CDN 零外部资源
- 🌟 **`demo` 一键体验** — 内置示例数据，30 秒跑完全流程
- 🧪 **`doctor` 环境自检** — 依赖/config/目录/编码逐项检查 + 修复建议
- 🧭 **交互式向导** — 无参数启动直接进入粘贴分析（`-h` 不变）
- 📝 **一句话总结** — 终端报告末尾自动生成中文摘要
- 🧠 **MBTI 稳定性提示** — 稳定性低时明确提示"结果仅供参考"
- 🔮 **predict-v2 备选去重** — 按规范化文本合并重复模板

### v2.0.0 基础特性

- 🧠 **jieba 精准分词** — 替代简陋的正则分词
- 💬 **否定识别** — 修复"我不开心"被误判的 bug
- 🎭 **反讽检测** — 识别"虽然...但是..."等句式
- 📊 **新 MBTI 置信度算法** — 维度差距 + 样本量综合评估
- 📚 **本地 RAG 引擎** — sentence-transformers + ChromaDB
- 🐟 **MiroFish 多智能体** — 8 Agent × N 轮模拟 + 投票博弈
- 🔮 **三层集成预测** — Rule + RAG + MiroFish 加权融合
- 🏗️ **模块化架构** — `core/` / `analyzers/` / `predictors/` / `rag/` / `mirofish/`
- 🔒 **隐私优先** — 100% 本地处理，零数据外传
- ♻️ **完全向后兼容 v1.2.0** — 所有旧命令保留

---

## 30秒快速上手

**第一步：安装核心依赖**
```bash
pip install -r requirements.txt
```

**第二步：一键体验（推荐新用户）**
```bash
python scripts/main.py demo      # 分析内置示例 + 生成 HTML 报告
python scripts/main.py doctor    # 环境自检
```

**第三步：分析自己的聊天记录**
```bash
python scripts/main.py                              # 交互式向导
python scripts/main.py analyze-v2 --input 聊天记录.txt --html report.html
```

**完成！** 终端报告 + 离线 HTML 报告（浏览器直接打开）。

---

## 命令对照

| 功能 | 推荐命令 | v1.2.0 兼容 |
|------|-------------|-------------|
| **一键体验** | `demo` | (无) |
| **环境自检** | `doctor` | (无) |
| **分析** | `analyze-v2 --paste` | `analyze --paste` |
| **导出 JSON** | `analyze-v2 --export result.json` | (无) |
| **HTML 报告** | `analyze-v2 --html r.html` / `report-v2` | `report --report-type html` |
| **预测** | `predict-v2 --paste` | (无) |
| **图谱统计** | `graph-stats` | (无) |
| **Web** | (v1.2.0 命令) | `serve --port 5000` |
| **定时任务** | (v1.2.0 命令) | `schedule --list` |
| **日历** | (v1.2.0 命令) | `calendar --list` |

> v1.2.0 的所有命令在 v2.1.0 中保留并继续工作。

---

## 功能一览

### 分析能力

- **MBTI 推断** — 从聊天风格推断对方 MBTI 16 型人格
  - v2.0.0: 维度差距 + 样本量综合置信度，输出稳定性评分
- **大五人格** — 开放性 / 尽责性 / 外向性 / 宜人性 / 神经质
  - v2.0.0: 归一化 + 雷达图数据 + 补全 neuroticism low 词
- **情感分析** — 追踪情感变化趋势，正面/负面比例
  - v2.0.0: jieba 分词 + 否定识别 + 程度副词 + 反讽检测 + HowNet 词典 + Emoji 映射
- **风险感知** — 标记值得关注的对话模式
  - v2.0.0: 反讽识别 + 否定排除 + 时序突发 + 三级风险
- **场景分类** — 恋爱 / 工作 / 社交 / 重要事项
- **对话模式** — 回复速度、主动率、问号/感叹号比例
  - v2.0.0: 修复 v1.2.0 的 reply_speed 丢失 bug

### 预测能力（v2.0.0 新增）

- **Rule 预测** — 16 MBTI × 5 模板 + 场景 + 关键词触发
- **RAG 预测** — 检索 top-K 相似历史对话作为 few-shot
- **MiroFish 预测** — 8 Agent × N 轮模拟 + 多轮辩论 + 加权投票
- **Ensemble** — 三层加权融合

### 可视化报告

- v2.1.0：单文件离线 HTML 报告（`analyze-v2 --html` / `report-v2`），内联 SVG 图表，零外部资源
- HTML / Word (.docx) / PPTX 格式（v1.2.0 保留）

---

## 完整使用指南

### 方式一：交互式向导 / demo（v2.1.0 推荐）

```bash
python scripts/main.py            # 无参数进入向导：粘贴 → 分析 → 可选 HTML 报告
python scripts/main.py demo       # 一键体验内置示例
```

### 方式二：v2 粘贴/文件分析

```bash
python scripts/main.py analyze-v2 --paste
python scripts/main.py analyze-v2 --input 聊天记录.txt    # 自动识别 utf-8/GBK
python scripts/main.py analyze-v2 --input 聊天记录.txt --export result.json --html report.html
```

### 方式三：v2 三层预测

```bash
python scripts/main.py predict-v2 --input 聊天记录.txt
```

输出示例：
```
[最佳预测] 置信度 78.5%
  策略: rule,mirofish
  内容: 「我先确认一下情况」

[备选预测]
  1. [65%] (rag) 「好的，我跟进一下」
  2. [62%] (mirofish) 「收到，我处理一下」
```

### 方式四：v1.2.0 文件导入（保留）

```bash
python scripts/main.py analyze --file 聊天记录.txt
```

支持格式：`.txt` `.json` `.docx` `.pdf` `.jpg` `.mp3`

### 方式五：v1.2.0 Web 服务

```bash
python scripts/main.py serve
# 浏览器打开 http://localhost:5000
```

### 方式六：生成报告

```bash
# v2.1.0：单文件离线 HTML（推荐）
python scripts/main.py analyze-v2 --input 聊天记录.txt --html report.html
python scripts/main.py report-v2                       # 用最近一次 v2 结果生成

# v1.2.0：多格式报告（保留）
python scripts/main.py report --report-type html    # HTML 报告
python scripts/main.py report --report-type word    # Word 报告
python scripts/main.py report --report-type pptx    # PPTX 报告
python scripts/main.py report --report-type all     # 全部格式
```

---

## v2 分析结果示例

### 终端输出

```
  [1/6] mbti ... 完成 (0.01s) ✅
  [2/6] bigfive ... 完成 (0.00s) ✅
  [3/6] sentiment ... 完成 (0.02s) ✅
  [4/6] risk ... 完成 (0.00s) ✅
  [5/6] scenario ... 完成 (0.00s) ✅
  [6/6] pattern ... 完成 (0.00s) ✅

============================================================
   微信聊天分析报告 v2.1.0
============================================================

🧠 [MBTI] ENFP - 竞选者
  置信度: 78.5%
  特征: 外向 | 直觉 | 情感 | 感知
  稳定性: 82%

🔬 [大五] OCEAN 人格分析
  开放性: [#######...] 68%
  尽责性: [#####.....] 52%
  外向性: [#######...] 71%
  宜人性: [#######...] 73%
  神经质: [####......] 42%

💬 [情感] 趋势: [上升]
  正面: 65.5% / 负面: 22.3% / 中性: 12.2%
  [v2.0.0] 检测到 3 条反讽
  正面词: 开心, 喜欢, 期待, 不错, 哈哈
  负面词: 担心, 紧张, 压力

⚠️ [风险]
  [MEDIUM] pig_butcher
    对方可能正在实施诈骗
    命中 2 次: 投资, 充值
    [建议]: 听起来不错，但我得先研究研究

🎯 [场景] 主场景: [工作]
    work: 18
    important: 12
    social: 5

📊 [模式] 对话模式分析
  主动发起: 我 35% / TA 65%
  平均回复: 245 秒
  快速回复 (<1分钟): 23
  慢速回复 (>1小时): 5
  聊天跨度: 15 天

============================================================
```

---

## 目录结构（v2.1.0）

```
wechat-analyzer/
├── core/                       # 🆕 核心抽象层
│   ├── message.py              # 统一 Message 模型
│   ├── result.py               # 统一 Result 模型
│   ├── analyzer_base.py        # 分析器抽象基类（run_all 支持进度回调）
│   ├── predictor_base.py       # 预测器抽象基类
│   └── utils.py                # 工具（分词/停用词/logger/编码自动检测）
│
├── analyzers/                  # 🆕 6 个独立分析器
│   ├── mbti_analyzer.py
│   ├── bigfive_analyzer.py     # v2.1.0 归一化校准
│   ├── sentiment_analyzer.py   # 否定识别 + 反讽
│   ├── risk_analyzer.py
│   ├── scenario_analyzer.py
│   ├── pattern_analyzer.py
│   └── lexicon/                # 🆕 词典资源
│       ├── hownet_positive.txt
│       ├── hownet_negative.txt
│       ├── negation_words.txt
│       ├── degree_words.txt
│       ├── emoji_dict.txt
│       └── jieba_dict/
│           └── user_dict.txt
│
├── predictors/                 # 🆕 3 个预测器 + Ensemble
│   ├── rule_predictor.py
│   ├── rag_predictor.py
│   ├── mirofish_predictor.py
│   └── ensemble.py             # v2.1.0 备选规范化去重
│
├── rag/                        # 🆕 RAG 引擎
│   ├── embedder.py
│   ├── vector_store.py
│   └── retriever.py
│
├── mirofish/                   # 🆕 v2.1.0 本地图谱包
│   └── core/
│       └── zep_local.py        # ZepLocalGraph（sqlite3 + jieba，替代 Zep Cloud）
│
├── scripts/                    # ♻️ 旧脚本（向后兼容）
│   ├── main.py                 # CLI 入口（v1.2.0 + v2.0.0 + v2.1.0）
│   ├── v2_report_generator.py  # 🆕 v2.1.0 单文件离线 HTML 报告
│   ├── main_setup.py
│   ├── text_analyzer.py        # v1.2.0 保留
│   ├── conversation_predictor.py
│   ├── llm_analyzer.py
│   ├── report_generator.py
│   ├── data_manager.py
│   ├── file_importer.py        # v2.1.0 编码自动检测
│   ├── calendar_manager.py
│   ├── scheduler.py
│   ├── web_server.py
│   ├── mirofish/               # v1.2.0 高级 MiroFish
│   └── archive_v1/             # v1.2.0 完整快照
│
├── templates/                  # Web 模板
├── data/                       # 数据存储
│   ├── chat_history.db
│   ├── vector_store/           # 🆕 ChromaDB 持久化
│   ├── models/                 # 🆕 embedding 模型
│   ├── reports/                # 🆕 v2.1.0 HTML 报告输出目录
│   └── mirofish_graph.db   # 🆕 本地图谱
│
├── tests/                      # 🆕 单元测试（含 fixtures 示例数据）
├── config.json                 # v2.1.0 配置
├── requirements.txt            # 核心依赖
├── requirements-rag.txt        # 🆕 RAG 独立依赖
├── requirements-web.txt        # ⏳ 未来 Web 依赖
├── SKILL.md                    # Skill 定义
└── README.md                   # 本文件
```

---

## 使用限制

使用前请了解以下限制：

- **单次分析建议不超过 500 条消息。** 超出后分析耗时较长。
- **分析结果仅供参考。** 人格推断基于关键词匹配，不是专业心理评估。
- **RAG 首次运行需联网。** 下载 embedding 模型约 50-100MB（1-2 分钟），之后完全离线。
- **RAG 依赖未安装时自动降级。** 预测自动回退到 Rule 层，不影响其他功能。
- **v1.2.0 命令继续可用。** 行为与 v1.2.0 一致，不影响现有用户。

---

## 如何导出微信聊天记录

### 方法一：直接复制文字（最快）

1. 打开电脑端微信，进入聊天对话框
2. 鼠标选中聊天内容（可多选）
3. 按 `Ctrl + C` 复制
4. 在工具中粘贴即可

### 方法二：从微信导出文件

1. 打开电脑端微信聊天窗口
2. 点击右上角 `...` 或 `···` 按钮
3. 选择 `聊天记录` → `聊天文件`
4. 点击 `导出聊天记录`
5. 选择格式 `txt`，保存到本地
6. 使用 `python scripts/main.py analyze-v2 --input 文件路径.txt`

---

## LLM API 配置（可选，v2.0.0 默认禁用）

v2.0.0 默认禁用云端 LLM，**所有分析本地完成**。如需启用 LLM 增强：

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 填入 API Key
# LLM_API_KEY=sk-...
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat

# 3. 修改 config.json
# "llm": { "enabled": true, ... }
```

> v2.0.0 推荐使用本地 RAG 引擎替代云端 LLM（隐私更好、效果更准）。

---

## 数据隐私说明（v2.0.0 强化）

- 所有数据保存在本地 `data/` 目录
- **不向任何云端服务器发送数据**（v2.0.0 默认配置）
- 无需注册账号
- SQLite 数据库 + ChromaDB 向量库 + MiroFish 图谱，全部本地
- 无遥测、无统计、无后台网络请求
- **RAG embedding 模型本地存储**，仅首次下载
- **LLM 完全可选**（默认关闭）
- **MiroFish 默认关闭**

---

## 常见问题

**Q: v1.2.0 的命令还能用吗？**
A: 完全兼容，所有旧命令保留并继续工作。

**Q: v2.0.0 和 v1.2.0 分析结果不一致？**
A: 正常。v2.0.0 引入 jieba、否定识别等，分析更准确。

**Q: 首次运行很慢？**
A: RAG 首次需下载 embedding 模型（50-100MB），之后秒开。

**Q: 不想用 RAG？**
A: `config.json` 中设 `"rag.enabled": false`。

**Q: 不想用云端 LLM？**
A: v2.0.0 默认禁用。完全不需要 `.env` 文件。

**Q: MiroFish 怎么启用？**
A: `config.json` 中设 `"mirofish.enabled": true`，然后运行 `predict-v2`。

**Q: 如何回滚到 v1.2.0？**
A: `scripts/archive_v1/` 中有完整 v1.2.0 快照。

**Q: Web 仪表盘呢？**
A: v2.1.0 路线图。当前使用 v1.2.0 的 Flask Web。

**Q: 群聊怎么分析？**
A: 导出群聊记录时选择"全部消息"，导入后同样可以分析。

**Q: 首次安装依赖太多？**
A: 运行 `python scripts/main_setup.py` 自动完成。

---

## 依赖安装

### 核心（必须）

```bash
pip install -r requirements.txt
```

### RAG 引擎（v2.0.0 推荐）

```bash
pip install -r requirements-rag.txt
```

### 可选增强

```bash
pip install openai-whisper   # 语音转文字
pip install easyocr          # 图片 OCR
```

### Web 仪表盘（v2.1.0 路线图）

```bash
pip install -r requirements-web.txt
cd web/frontend && npm install
```

---

## 版本路线图

- ✅ **v1.2.0** — 基础 MBTI/大五/情感/风险分析，LLM 增强（云端）
- ✅ **v2.0.0** — 模块化架构、jieba 分词、本地 RAG、多智能体 MiroFish、隐私优先
- ⏳ **v2.1.0** — FastAPI + Vue3 + ECharts 仪表盘
- ⏳ **v3.0.0** — 微信 DB 解密、OCR/ASR 升级、长期记忆

---

版本: v2.5.0
