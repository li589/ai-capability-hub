# 高级功能索引（references/INDEX.md）

> 本目录汇总**高级功能**的详细说明。  
> 如果你只是想日常用，**先看 [RUNBOOK.md](../RUNBOOK.md)** 和 [FAQ.md](../FAQ.md) 就够了。  
> 想深入了解某个模块的算法/数据结构/扩展方式，再回来看这一页。

---

## 📑 索引

| 高级功能 | 通俗解释 | 详细文档 | 是否必读 |
|---------|---------|---------|---------|
| [jieba 分词](#jieba-分词) | "我今天很开心" → 切成 "我/今天/很/开心" | [analyzers/lexicon/](../analyzers/) | ⭐⭐ |
| [RAG 检索增强预测](#rag-检索增强预测) | 让 AI 基于历史 1000 条对话预测下一条 | [`rag/`](../rag/) | ⭐⭐ |
| [MiroFish 多智能体](#mirofish-多智能体) | 模拟 8 个虚拟人陪你聊 | [scripts/mirofish/](../scripts/mirofish/README.md) | ⭐⭐⭐ |
| [本地图谱（v2.1.0）](#本地图谱v210) | 替代 Zep Cloud 的纯本地图数据库 | [`predictors/`](`../predictors/`) | ⭐⭐ |
| [三层集成预测](#三层集成预测) | Rule + RAG + MiroFish 投票融合 | [`predictors/ensemble.py`](../predictors/ensemble.py) | ⭐⭐⭐ |
| [隐私模式](#隐私模式) | 关闭所有网络请求的强化本地模式 | [v2.0.0 §3 使用须知](../SKILL.md) | ⭐ |
| [数据集训练](#数据集训练) | 用自己的 MBTI/大五标注数据集训练分析器 | [`analyzers/`](../analyzers/) | ⭐⭐⭐ |

---

## jieba 分词

**是什么**：中文分词工具，把连续中文切成"词"。

**为什么需要**：不用 jieba 时，工具只能用正则切成字符：

```
没有jieba: 我/今/天/很/开/心  (6个词,错把"今天"拆开)
有了jieba:  我/今天/很/开心   (4个词,正确分词)
```

**会装吗**：`pip install jieba`（默认推荐依赖）。

**禁用后果**：分析准确率下降 20-30%（MBTI / 大五）。

**位置**：`analyzers/` + `analyzers/lexicon/`（分词词典 + 否定词 + 程度副词 + Emoji 词典）。

---

## RAG 检索增强预测

**是什么**：让 AI 能"基于历史对话"预测下一条。

**和普通预测的差别**：

| | 普通预测 | RAG 预测 |
|---|---|---|
| 输入 | 仅当前对话 | 当前 + 历史 1000+ 条 |
| 准确度 | 取决于模板 | 取决于你的说话风格 |
| 速度 | < 1 秒 | 1-3 秒 |
| 需要联网 | ❌ | ❌（首次下载模型） |

**核心原理**：
```
1. 用 embedding 模型把每条历史对话向量化
2. 存到本地向量数据库（ChromaDB）
3. 预测时检索 Top-K 最相似的历史消息
4. 把检索结果喂给规则/AI 用于预测
```

**是否必装**：❌ **不装也能用 80% 功能**。  
**强烈推荐**：✅ 如果你想"他真的会这么回吗"级别的预测。

**首次安装**：
```bash
pip install -r requirements-rag.txt
python scripts/main.py download-models  # 一次性下载 embedding 模型（约 50MB）
```

详细代码：[`rag/embedder.py`](../rag/embedder.py) + [`rag/vector_store.py`](../rag/vector_store.py) + [`rag/retriever.py`](../rag/retriever.py)。

---

## MiroFish 多智能体

**是什么**：8 个虚拟人陪你聊，每个有自己的"性格"。

**怎么用**：
```bash
# 单次模拟
python scripts/main.py mirofish-simulate --message "我觉得最近有点累"

# 输出：
# Agent_1 (性格: INTJ) 说: "那要不要做点轻松的事？"
# Agent_3 (性格: ENFP) 说: "累就对了！周末出来玩！"
# Agent_5 (性格: ISTJ) 说: "你要注意休息啊"
# ... 共 8 个不同的回应
```

**核心原理**：
```
1. 创建 8 个 agent，每个绑定一个 MBTI 类型
2. 给定一段对话，每个 agent 独立生成"他怎么回"
3. 投票/排名最合理的回应
```

**是否必装**：❌ 默认关闭。不开也能用所有核心功能。

**开启方式**：编辑 `config.json`：
```json
{"mirofish": {"enabled": true, "agents_count": 8}}
```

**依赖**：见 `scripts/mirofish/requirements.txt`。

详细文档：[`scripts/mirofish/README.md`](../scripts/mirofish/README.md)。

---

## 本地图谱（v2.1.0）

**是什么**：用本地 SQLite 替代 Zep Cloud（云端图谱服务），实现 100% 离线。

**为什么重要**：

- Zep Cloud：商业 SaaS，要联网，要付费，要传数据
- 本地图谱：纯本地 SQLite + NetworkX，**零成本、零外发**

**用在哪**：对话实体关系追踪（如"张三给李四推荐了王五"等）。

详细代码：[`predictors/mirofish_predictor.py`](../predictors/mirofish_predictor.py)。

---

## 三层集成预测

**是什么**：综合 Rule + RAG + MiroFish 三种预测，给出**单一最可信的预测**。

**流程图**：
```
              ┌─────────┐
   输入 ───▶ │  Rule   │ ──┐
              └─────────┘   │
              ┌─────────┐   ├──▶ Ensemble ───▶ 最终预测
   输入 ───▶ │   RAG   │ ──┤                  (置信度 0-100)
              └─────────┘   │
              ┌─────────┐   │
   输入 ───▶ │ MiroFish│ ──┘
              └─────────┘
```

**权重**（默认，可调）：
- Rule: 30%
- RAG: 35%
- MiroFish: 35%

详细代码：[`predictors/ensemble.py`](../predictors/ensemble.py)。

---

## 隐私模式

**是什么**：最大化隐私保护的"超本地"模式。

**开启条件**：
1. `config.json` 中 `llm.enabled = false`（禁用云端 LLM）
2. `mirofish.enabled = false`（不需要联网）
3. 不安装 RAG（避免下载 embedding 模型时的网络请求）

**适合场景**：
- 个人隐私聊天
- 公司内部对话（涉密）
- 任何你 100% 不希望泄露的内容

详细：[`SKILL.md` §3 使用须知](../SKILL.md)。

---

## 数据集训练

**是什么**：用你自己的标注数据"教会"分析器。

**典型场景**：
- 你已经给 100 个朋友打了 MBTI 标签
- 用这些数据训练一个**个性化**的 MBTI 模型
- 比通用模型准确度高 20-30%

**如何开始**：
1. 准备 CSV：`sender, content, mbti_label`
2. 跑训练：`python scripts/main.py train --dataset my_data.csv`
3. 训练完成后，工具自动加载你的模型

代码位置：[`analyzers/`](../analyzers/)（`train.py` + `dataset.py`）。

---

## 🔗 相关文档

- 📘 [SKILL.md](../SKILL.md) — 完整规范（含 v2.1.0/v2.2.0 升级亮点）
- 📕 [RUNBOOK.md](../RUNBOOK.md) — 一页纸速查（30 秒上手）
- 📗 [FAQ.md](../FAQ.md) — 44 个常见问题
- 📙 [CHANGELOG.md](../CHANGELOG.md) — 历史更新
- 📓 [templates/](../templates/) — 报告模板（v2.2.0 单文件 HTML）

---

*最后更新：v2.2.0（2026-07-28）*  
*反馈：[README.md §支持](../README.md)*
