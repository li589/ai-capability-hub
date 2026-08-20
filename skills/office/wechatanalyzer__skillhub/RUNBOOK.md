# 🚀 RUNBOOK — 微信聊天分析助手 v2.2.0 速查手册

> **一页纸看懂所有用法。** 想用 30 秒上手 → 直接看 [§1 一句话用](#1-一句话用)；想用全部功能 → 看 [§2 完整命令速查](#2-完整命令速查)。

---

## ⚠️ 重要声明（先看这里）

**本工具的分析结果仅供参考，不是专业评估！**

- MBTI / 大五人格推断基于关键词和规则匹配
- **不能用于专业心理评估 / 职业决策 / 感情决策**
- 情感分析 / 风险检测可能误报
- 输出的报告**保密责任在你**，工具不存储你的聊天记录

详见 [SKILL.md §3 使用须知](SKILL.md) + [FAQ.md §Q13 MBTI 准吗？](FAQ.md)。

---

## 🆕 v2.2.0 新功能一览

✅ **不用记命令**，直接对加载了本 Skill 的 AI 助手说这些中文：

| 想做的事情 | 这么说就行 |
|---|---|
| 想知道这段对话接下来会怎么走 | "推演对话走向" / "分析我们关系" |
| 想知道他到底什么意思 | "他是什么意思" / "解读聊天内容" |
| 想看消息里有哪些关键信息 | "提取聊天意图" / "提取关键信息" |
| 想看有没有问题风险 | "这段对话有什么问题" / "看看我们聊了什么" |

> **零基础也可以玩** —— 启动后会进入交互式向导，跟着提示一步步走即可。

---

## 🤔 高级功能是什么？看完这页就懂

> 很多用户被"RAG / MiroFish / jieba"这些术语劝退。**这不是技术黑话**，看完下面类比就懂：

| 术语 | 通俗类比 | 不装会怎样 |
|------|---------|----------|
| **jieba** | 中文分词器。把"我今天很开心"切成"我/今天/很/开心" | 也能用，但分析准确率下降 20-30% |
| **RAG** | AI 记忆库。基于历史 1000 条对话预测下一条 | 只用模板预测，不如 RAG 个性化 |
| **MiroFish** | 8 个虚拟人陪你聊天 | 不用，但装了能模拟多种可能 |
| **本地图谱** | 替代云端数据存储的本地数据库 | 默认就是本地，无需关心 |

**结论**：核心 MBTI/情感/风险分析不需要装任何高级功能，**开箱即用**。

详细对比见 [FAQ.md §Q22-Q25](FAQ.md) 或 [references/INDEX.md](references/INDEX.md)。

---

## 1. 一句话用

### 🎯 三种最快路径（任选一个）

```bash
# 路径 A：30 秒体验（推荐第一次用）
python scripts/main.py demo
# 自动分析内置示例 + 生成 HTML 报告，直接打开就能看

# 路径 B：交互式向导（最简单）
python scripts/main.py
# 无参数启动，跟着提示粘贴聊天记录即可

# 路径 C：完整分析报告（最专业）
python scripts/main.py analyze-v2 --paste --html report.html
# 粘贴聊天 → 自动分析全部维度 → 输出可离线的 HTML 报告
```

**第二步：打开报告**
```bash
# Windows
start report.html
# Mac
open report.html
```

---

## 2. 完整命令速查

### 📊 分析类（6 种）

```bash
# 完整分析：推演 + 解读 + 所有维度
python scripts/main.py analyze-v2 --paste

# 从文件分析（自动识别 utf-8/GBK/UTF-8-sig）
python scripts/main.py analyze-v2 --input 聊天记录.txt

# 导出 JSON 结果
python scripts/main.py analyze-v2 --input 聊天.txt --export result.json

# 生成单文件 HTML 报告（离线可开）
python scripts/main.py analyze-v2 --input 聊天.txt --html 我的报告.html

# 只生成报告（基于上次 JSON）
python scripts/main.py report-v2

# 文本格式报告（终端可读）
python scripts/main.py analyze-v2 --input 聊天.txt --format text
```

### 🔮 推演类（v2.2.0 新增）

```bash
# 推演包含在 analyze-v2 的输出里，无需单独调用
# 查看报告里「🔮 推演能力」一段即可
```

### 📋 解读类（v2.2.0 新增）

```bash
# 解读同样已包含在 analyze-v2 输出
# 查看报告里「📋 信息解读」一段即可
```

### 🛠 工具类（5 种）

```bash
# 环境自检（出问题时先跑这个）
python scripts/main.py doctor

# 用最近结果生成报告
python scripts/main.py report-v2 --output my.html

# 看图谱统计（多智能体相关）
python scripts/main.py graph-stats

# 查看版本
python scripts/main.py version

# 帮助
python scripts/main.py --help
```

---

## 3. 直接调用 Python 模块

如果你想在 Jupyter / 自己的代码里调用：

```python
import sys
sys.path.insert(0, ".")  # 当前目录

from analyzers import create_default_registry
from core.message import Message
from datetime import datetime, timedelta

# 1. 创建分析器注册中心（含 8 个分析器）
registry = create_default_registry()
print(registry.list())
# ['mbti', 'bigfive', 'sentiment', 'risk', 'scenario', 'pattern', 'inference', 'interpretation']

# 2. 构造消息
now = datetime.now()
messages = [
    Message(sender="other", content="你好", timestamp=now - timedelta(days=1)),
    Message(sender="self", content="你好", timestamp=now - timedelta(days=1, hours=1)),
    # ...
]

# 3. 一行运行全部
results = registry.run_all(messages)

# 4. 查看推演结果
print(results["inference"].details["overall_verdict"])
# {'label': '🟡 观察', 'advice': '...'}

# 5. 查看解读摘要
print(results["interpretation"].details["summary"])
# '主要意图：询问；主要讨论主题：工作...'
```

---

## 4. 快速决定表

| 你的情况 | 推荐命令 | 报告类型 |
|---------|---------|---------|
| **第一次用，看个意思** | `python scripts/main.py demo` | HTML（自动生成） |
| **正式分析一段聊天** | `python scripts/main.py analyze-v2 --paste --html 报告.html` | HTML（离线可开） |
| **大批量分析（>10 段聊天）** | `python scripts/main.py analyze-v2 --input 聊天.txt --export result.json` + 批量对比 | JSON |
| **出错了想排查** | `python scripts/main.py doctor` | 终端日志 |
| **想预测对话走向** | 跑 `analyze-v2` 后看报告「🔮 推演」段 | 已包含 |
| **想知道对方在想什么** | 跑 `analyze-v2` 后看报告「📋 解读」段 | 已包含 |
| **集成到自己的代码** | `from analyzers import create_default_registry` | Python dict |

---

## 5. 常见问题（5 大坑）

### 🔴 Q1：跑命令后报 `ModuleNotFoundError: No module named 'xxx'`

**解决**：跑 `python scripts/main.py doctor` 看哪些依赖缺失，然后：
```bash
pip install -r requirements.txt

# RAG 引擎可选：
pip install -r requirements-rag.txt

# Web 仪表盘（v2.1.0 路线图）可选：
pip install -r requirements-web.txt
```

### 🟡 Q2：`jieba` 没用上，结果不准

**症状**：分析结果像没分词一样粗糙。

**原因**：`jieba` 没装。

**解决**：
```bash
pip install jieba
# 然后重启脚本
```

### 🟡 Q3：聊天记录导出格式不识别

**微信导出格式**（默认支持）：
```
张三 13:45:01
你好啊

李四 13:46:22
在的，怎么了
```

**支持的格式变体**：
- `发送者: 内容`（冒号+空格）
- `[时间] 发送者: 内容`（方括号时间）
- JSON 格式（必须是字典列表）

**不识别时怎么办**：
1. 用文本编辑器把聊天记录改成上面的格式
2. 或用 `--input 聊天.txt` 时确认编码（默认 utf-8-sig / utf-8 / gb18030 自动嗅探）

### 🟠 Q4：分析报「MiroFish 默认关闭」

**默认关闭原因**：mirofish 多智能体模拟需要更多算力。

**启用**：编辑 `config.json`，找 `"mirofish_enabled": false` 改成 `true`。

### 🔴 Q5：报告里说「样本较少，结果仅供参考」

**原因**：消息总数 < 50 条，或时间跨度 < 1 天。

**建议**：
- 累积到至少 30 天聊天
- 或增加样本量（导入更多聊天记录）
- 或把这个分析当作"试探性结论"，重要决策再人工核对

---

## 6. 输出报告章节说明

打开 HTML 报告后，你会看到这些章节：

| 章节 | 看什么 |
|------|--------|
| 📋 **总览** | 1 句话总结整体状况 + 健康度评分 |
| 🧬 **MBTI / 大五人格** | 推断的人格类型（仅供参考） |
| 💬 **情感分析** | 整体情感倾向 + 关键转折点 |
| ⚠️ **风险检测** | 是否有对抗/对抗升级信号 |
| 🎬 **场景分类** | 聊天主要是工作/家庭/感情/... |
| 📊 **对话模式** | 主动率、回复速度、活跃时段 |
| 🔮 **推演能力**（v2.2.0 新增） | 5 大子推演：话题/对手/情感/风险/走向 |
| 📋 **信息解读**（v2.2.0 新增） | 4 大解读：意图/实体/主题/立场 |
| 💡 **建议** | 系统自动生成的关系维护建议 |

---

## 7. 一行命令速记（贴桌面）

```bash
# 第一次 → demo
python scripts/main.py demo

# 出问题 → doctor
python scripts/main.py doctor

# 正式分析 → analyze-v2 + HTML
python scripts/main.py analyze-v2 --paste --html report.html && start report.html

# 仅文本/JSON
python scripts/main.py analyze-v2 --input 聊天.txt --export result.json
```

---

## 8. 文档交叉引用

- 📘 [SKILL.md](SKILL.md) — 完整规范和方法论
- 📗 [README.md](README.md) — 项目说明
- 📙 [CHANGELOG.md](CHANGELOG.md) — 历史更新
- 📕 [templates/](templates/) — 报告模板
- 🐟 [scripts/mirofish/README.md](scripts/mirofish/README.md) — 多智能体引擎

---

*最后更新：v2.2.0（2026-07-28）*
