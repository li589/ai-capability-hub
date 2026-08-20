# 常见问题解答（FAQ）

> 微信聊天分析助手 v2.2.0 — 看完这页，**95% 的问题都能解决**。
> 找不到答案？ → [RUNBOOK.md](RUNBOOK.md) 看完整用法，[SKILL.md](SKILL.md) 看完整规范。

---

## 📑 目录

- [🚀 入门 3 问](#-入门-3-问)
- [🛠 安装与环境（10 问）](#-安装与环境10-问)
- [💬 分析与解读（10 问）](#-分析与解读10-问)
- [🔮 高级功能（10 问）](#-高级功能10-问)
- [🐛 错误与排查（5 问）](#-错误与排查5-问)
- [🔒 隐私与合规（5 问）](#-隐私与合规5-问)

---

## 🚀 入门 3 问

### Q1: 我完全没用过这个工具，应该从哪开始？

**答**：从 `demo` 开始。

```bash
python scripts/main.py demo
```

30 秒内你会看到：本工具分析一段内置示例聊天、生成 HTML 报告。然后你就能直接打开 `report.html` 看到效果。

### Q2: 怎么把我自己的聊天记录导进来？

**答**：3 步。

1. **导出微信聊天**：微信设置 → 聊天 → 聊天记录迁移与备份 → 导出聊天记录 → 保存为 `.txt` 文件
2. **放到工具目录**：把 `.txt` 文件复制到 wechat-analyzer 根目录
3. **跑命令**：

```bash
python scripts/main.py analyze-v2 --input 你的聊天.txt --html 报告.html
```

详细的导出格式要求见 [SKILL.md §4](SKILL.md)。

### Q3: 工具会偷偷上传我的聊天记录吗？

**答**：**100% 不会**。本工具全程本地运行：

- ✅ 所有分析代码在你自己的电脑上跑
- ✅ 不发送任何聊天内容到外部服务器
- ❌ 唯一的"网络请求"是**首次下载** RAG 的 embedding 模型（可以用 `--offline` 参数跳过）

详见 [SKILL.md §3 使用须知](SKILL.md)。

---

## 🛠 安装与环境（10 问）

### Q4: 安装时报 `ModuleNotFoundError: jieba`

**答**：jieba 是中文分词必需。

```bash
pip install jieba
```

> **jieba 是干嘛的？** 简单说：把"我今天很开心"切成"我/今天/很/开心"，让 AI 更准确理解你的语气。

### Q5: 安装时报 `ModuleNotFoundError: sentence_transformers` / `chromadb`

**答**：这两个是 **RAG 引擎的可选依赖**，**不安装也能用**核心 80% 功能。

- 不装：分析 MBTI / 大五 / 情感 / 风险 / 推演 / 解读 → ✅ 都能用
- 装了：额外支持"基于历史对话的回复预测" → 加分项

详见 [RAG 是什么？](#q22-rag-引擎是什么) 章节。

### Q6: 我不想要 LLM API，能完全离线吗？

**答**：**可以**，且默认就是离线模式。

- 默认：完全本地（jieba + 规则 + 启发式）
- 可选：配上 LLM API（如 DeepSeek、GPT）增强解读深度

```bash
# 完全本地（默认）
python scripts/main.py analyze-v2 --input 聊天.txt

# 想用 LLM 增强：编辑 config.json 里 llm.enabled = true
```

### Q7: 报"No module named 'flask'"但我不想用 Web 仪表盘

**答**：flask 是 Web 仪表盘的依赖。不想用 Web 界面就**不用装**。

```bash
# 仅核心 + 报告功能（不需要 flask）
pip install -r requirements.txt
```

### Q8: 切换到不同的 LLM 模型

**答**：编辑 `config.json`：

```json
{
  "llm": {
    "enabled": true,
    "provider": "deepseek",   // 或 "openai"
    "model": "deepseek-chat"
  }
}
```

支持：DeepSeek、OpenAI、Azure OpenAI、Anthropic（需装对应 SDK）。

### Q9: 跑 `doctor` 命令查环境

**答**：`doctor` 是诊断命令，能告诉你哪些依赖缺失：

```bash
python scripts/main.py doctor
```

输出示例：

```
✅ Python 3.11.9 (建议 ≥ 3.8)
✅ jieba 已安装
⚠️  RAG 引擎未启用（不安装 sentence_transformers 也能用核心 80% 功能）
❌ flask 未安装（如不需要 Web 界面可忽略）
```

### Q10: 在 Windows / Mac / Linux 上有差别吗？

**答**：没有，本工具**全平台兼容**。Python 3.8+ 即可。Windows 上若中文乱码，跑 `chcp 65001` 切到 UTF-8。

### Q11: 为什么推荐用 venv 虚拟环境？

**答**：避免依赖污染项目 Python。

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Q12: pip install 慢怎么办？

**答**：用国内镜像。

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 💬 分析与解读（10 问）

### Q13: MBTI 推断真的准吗？

**答**：**仅供娱乐，不可用于专业评估**。

- 准确率：样本量 > 50 条时约 60-70%
- 但 MBTI 本身就是心理学界有争议的模型
- 工具给出的"ENTJ"只是一个**统计倾向**，不是诊断
- **不要用此做职业/感情决策**

详见 [SKILL.md §3 使用须知](SKILL.md) 第 1 条警告。

### Q14: 大五人格和 MBTI 有什么区别？

**答**：

| | MBTI | 大五人格 |
|---|---|---|
| 维度数 | 4 维（2 极） | 5 维（连续光谱） |
| 输出 | 16 种类型 | 0-100 分连续值 |
| 心理学界接受度 | 争议大 | 接受度高 |
| 本工具用法 | 快速分型 | 细化分析 |

### Q15: 情感分析为什么把"我不开心"判成 positive？

**答**：早期版本的 bug，v2.0+ 已修复。

- ✅ 修复方案：加上"否定识别"（"我不开心" = negative）
- ✅ 修复方案：加上"反讽检测"（"你可真行啊" = negative）

详见 `analyzers/sentiment_analyzer.py`。

### Q16: 推演（v2.2.0 新功能）和预测有什么区别？

**答**：

- **预测（predict）**：推测**下一条消息说什么**（conversation_predictor）
- **推演（v2.2.0 inference）**：分析**对话整体走向、风险演化、对方心态**（5 大子能力）

`analyze-v2` 自动包含推演结果。

### Q17: 解读（v2.2.0 新功能）都能解读什么？

**答**：4 大子能力：

1. **意图识别**：他在问你？告知你？抱怨？道歉？
2. **实体识别**：消息里有哪些金额、日期、URL？
3. **主题抽取**：对话主要聊工作？家庭？感情？
4. **立场识别**：双方对某话题是支持还是反对？

### Q18: 风险检测能把"分手前兆"识别出来吗？

**答**：**部分能**。Risk 分析器检测：

- ⚠️ 情感疏远（"算了""无所谓"）
- ⚠️ 反讽升级（"行，你厉害"）
- ⚠️ 极端词（"滚""拉黑""报警"）

**但**：识别 ≠ 预测。要结合**整段对话上下文**才有意义。

### Q19: 报告 HTML 里图是怎么生成的？

**答**：本工具自带 SVG 渲染，无需外网 Chart.js。生成的 HTML **完全离线可开**，可直接邮件发送。

### Q20: 一段对话最少多少条才能分析？

**答**：

| 分析器 | 最低要求 |
|--------|---------|
| MBTI | 20 条 |
| 大五 | 30 条 |
| 情感 | 5 条 |
| 风险 | 5 条 |
| 场景 | 3 条 |
| **推演** | **5 条** |
| **解读** | **3 条** |

少于 5 条建议先累积对话。

### Q21: 一段对话最多能分析多少？

**答**：技术上无上限，但**建议 ≤ 500 条**。
- 超过 500 条：分析耗时长，准确率下降
- 解决：可按时间段分批跑，然后对比

---

## 🔮 高级功能（10 问）

### Q22: RAG 引擎是什么？

**答**：**Retrieval-Augmented Generation（检索增强生成）**。

- **解决什么问题**：如果你有 1000 条历史对话，predict-v2 能"基于以前的聊天风格"预测下一条，而不是套模板
- **原理**：把历史对话向量化（embedding），存到本地数据库（ChromaDB），预测时检索最相似的几条
- **需要装**：sentence-transformers + chromadb（**可选**）
- **首次使用**：会下载 ~50MB embedding 模型，之后完全离线

简单说：**让 AI 更懂你的说话方式**。

### Q23: MiroFish 是什么？

**答**：**多智能体博弈模拟器**。

- **解决什么问题**：模拟 8 个虚拟人陪你聊，模拟对方可能怎么回应
- **原理**：创建 N 个 agent，每个有自己的 MBTI，模拟他们针对你那句话的反应
- **用在**：当你不确定对方会怎么回时，可以跑 MiroFish 看多种可能
- **需要装**：额外依赖（可选）

简单说：**让 AI 模拟多个可能的"他"**。

### Q24: jieba 是什么？为什么需要它？

**答**：**中文分词工具**。

- 例：把"今天天气真好"切成"今天/天气/真/好"
- 不用 jieba：只能用正则粗切，分错"今天天气"会判成一个词
- 用了 jieba：准确分词，情感分析准 30%

**日常使用不用手动操作**，工具自动调用。

### Q25: 配置文件 `config.json` 长什么样？

**答**：

```json
{
  "analysis": {
    "mbti_enabled": true,
    "bigfive_enabled": true,
    "sentiment_enabled": true,
    "risk_detection_enabled": true,
    "inference_enabled": true,
    "interpretation_enabled": true
  },
  "llm": {
    "enabled": false,
    "provider": "deepseek",
    "model": "deepseek-chat"
  },
  "mirofish": {
    "enabled": false
  }
}
```

所有项都有默认值，第一次跑不用改。

### Q26: 大数据量（> 500 条）怎么加速？

**答**：

1. 关掉重型分析器：
   ```bash
   python scripts/main.py analyze-v2 --input big.txt --skip bigfive
   ```
2. 启用缓存（默认开启）：
   ```json
   {"cache": {"enabled": true}}
   ```
3. 拆成多段再合并报告

### Q27: Web 仪表盘怎么启动？

**答**：

```bash
# 安装额外依赖
pip install -r requirements-web.txt

# 启动
python scripts/main.py web-start  # 然后浏览器开 http://localhost:5000
```

### Q28: 怎么把报告发给别人？

**答**：

1. **HTML 报告**：直接邮件附件发送，单文件 100% 离线
2. **DOCX**：用 Word 打开，保存为 PDF
3. **JSON**：开放给开发者，可集成到其他系统

### Q29: 报告乱码怎么办？

**答**：

- **生成的 HTML 不乱码**：工具用 UTF-8 编码，浏览器自动识别
- **导出 .docx 乱码**：可能 Word 设置问题，文件本身是 UTF-8
- **TXT 输入乱码**：见 [Q30 编码](#q30-导入聊天时报编码错误unicodeerror)

### Q30: 导入聊天时报编码错误/UnicodeError

**答**：本工具自动识别 utf-8-sig / utf-8 / gb18030 三种编码。

**手动指定**：
```bash
python scripts/main.py analyze-v2 --input 聊天.txt --encoding gb18030
```

---

## 🐛 错误与排查（5 问）

### Q31: 跑命令后报 `[WinError 5] Permission denied`

**答**：文件被占用（Word / 微信正在打开它）。

**解决**：关闭 Word / 微信，或换一个文件名输出。

### Q32: 报告里说"样本较少，结果仅供参考"

**答**：正常现象。

**解决**：
- 等积累了更多对话再跑
- 或将多个 chat 文件合并后再分析
- 或修改参数降低阈值（修改 `analyzers/...` 文件）

### Q33: 跑 `demo` 后没生成 HTML

**答**：

```bash
# 显式指定输出位置
python scripts/main.py demo --html demo_report.html
```

如果仍失败，看 `data/reports/` 目录是否存在。

### Q34: 中文显示 `Module 'xxx' not found: ...(unicode error)` 等乱码

**答**：Python 解释器不是 UTF-8。

```bash
# Windows
chcp 65001

# 或在 Python 里
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### Q35: 遇到其他未知错误

**答**：

1. 跑 `python scripts/main.py doctor` 看环境
2. 看输出日志找关键错误信息
3. 把错误日志保留，提 issue

---

## 🔒 隐私与合规（5 问）

### Q36: 工具会永久保留我的聊天记录吗？

**答**：

- **处理时**：在内存中处理，**不写硬盘**（除非你指定了输出路径）
- **报告**：生成的 `.html` / `.docx` / `.json` 你自己保管
- **配置**：所有配置在 `config.json`，本地的

### Q37: 多用户共用一台电脑安全吗？

**答**：本工具不区分用户，所有报告都在 `data/reports/`。

**建议**：
- 每位用户单独跑、单独输出文件夹
- 或在共享电脑前清理 `data/reports/`

### Q38: 公司电脑能用吗？合规吗？

**答**：

- **代码层面**：100% 本地，无任何外发
- **法律层面**：取决于贵公司政策
- **建议**：与公司 IT 部门确认（重点关注聊天内容是否涉及商业机密）

### Q39: LLM API 模式下，我的聊天内容去 API 了怎么办？

**答**：当你**主动**配置了 LLM：

- 数据会发到你配置的 LLM 提供商
- 默认关闭（`llm.enabled = false`）
- 只在你**显式启用**时发生

**强烈建议**：分析私人/敏感聊天时，**关闭** LLM，只用本地规则。

### Q40: 可以彻底离线吗？

**答**：可以。

```bash
# 第一次需要联网下载模型，之后完全离线
pip install -r requirements-rag.txt
python scripts/main.py download-models  # 一次性下载 embedding 模型
# 之后：
# - 关闭网络
# - 跑 analyze-v2 / predict-v2，所有分析本地完成
```

---

## 📚 进阶问题

### Q41: 有 ChatGPT / Cursor 集成吗？

**答**：本工具本身是 CLI + 报告生成，**不内置 IDE 集成**。但 JSON 输出可被任何程序消费。

### Q42: 多语言支持吗？

**答**：中文 + 英文。其他语言识别率较低。

### Q43: 能分析群聊吗？

**答**：✅ 支持。

- `sender: content` 格式即可，可多个 sender
- 工具会按 sender 分组，分析每个参与者的特征

### Q44: 学到了但还有问题？

**答**：在 `RUNBOOK.md` 看完整用法，或 `SKILL.md` 看完整规范。

---

*最后更新：v2.2.0 (2026-07-28)*  
*反馈：项目根 README 里有渠道*
