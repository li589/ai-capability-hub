---
name: wechat-analyzer
description: >
  微信聊天分析助手 v2.8.0 — 完全本地运行的隐私保护工具。
  分析聊天记录，推断 MBTI 与大五人格，检测情感趋势，生成可视化报告。
  支持 jieba 精准分词、否定识别、反讽检测、风险预警、RAG 检索增强预测、
  多智能体博弈模拟（MiroFish），完全本地化、零数据外传。
version: 2.8.0
author: user
tags:
  - wechat
  - chat-analysis
  - mbti
  - big-five
  - sentiment
  - report-generation
  - privacy-first
  - mirofish
  - conversation-prediction
  - rag
  - local-llm
  - multi-agent
  - jieba
  - negation-detection
  - inference
  - interpretation
  - intent-recognition
  - ner
  - friendly-errors
  - reproducible-prediction
triggers:
  - "分析微信聊天记录"
  - "聊天记录分析"
  - "MBTI分析"
  - "生成聊天报告"
  - "微信记录整理"
  - "对话预测"
  - "心理分析"
  - "情感分析"
  - "微信怎么导出聊天记录"
  - "本地对话预测"
  - "群体智能分析"
  - "RAG预测"
  - "微信分析v2"
  - "推演对话走向"
  - "解读聊天内容"
  - "提取聊天意图"
  - "我要聊天分析"
  - "看看我们聊了什么"
  - "他是什么意思"
  - "分析我们关系"
  - "这段对话有什么问题"
  - "帮忙看看聊天"
  - "看看聊天记录"
  - "帮我分析一下"
  - "性格分析"
  - "猜她是什么性格"
  - "猜他是什么性格"
  - "我们聊天有什么风险"
  - "这段对话谁的问题"
  - "听一下这段对话"
  - "我们什么关系"
  - "感情走向"
  - "下一步该怎么聊"
  - "TA 内心想法"
  - "TA 是怎么想的"
  - "聊天灵感"
  - "回复建议"
  - "她是不是生气了"
  - "他最近怎么了"
  - "怎么回复他好"
  - "求分析"
---

# 微信聊天分析助手 v2.8.0

**完全本地运行、模块化架构、AI 增强的隐私保护工具**

> ## ⚠️ 分析结果仅供参考，**不是专业评估**
>
> MBTI / 大五 / 情感 / 风险 / 推演都是**启发式估计**，准确率有限。
> 不能用于专业心理评估、职业/感情决策、临床诊断。详见 [FAQ.md](FAQ.md)。

## 🆕 v2.8.0 健壮性升级 + 零警告

- **消除非法转义** — `core/utils.py` 正则因引号截断产生隐式字符串拼接，`\[` 成非法转义（DeprecationWarning，3.12+ 将变 SyntaxError），改三引号 raw string
- **Python 3.15 兼容** — `calendar_manager._parse_date` 无年份日期（"08-20"）显式补参考年份，不再依赖 strptime 默认年份（3.15 起行为变更）
- **7 处裸 except 收紧** — 按场景改为 ValueError / OSError / json.JSONDecodeError，不再吞 KeyboardInterrupt
- **全覆盖编译烟囱测试** — 自动扫描全部 .py（编译+警告升错误）+ 裸 except 防回归 + 版本一致性校验
- 测试 329 过 / Python 3.11 与 3.14 双版本零警告

## 能力矩阵

| 能力 | 说明 | 入口 |
|---|---|---|
| **MBTI / 大五人格** | 关键词规则推断 + 维度差距置信度 + 稳定性评分 | `analyze-v2` |
| **情感分析** | jieba 分词 + 否定识别 + 反讽检测 + Emoji 映射 | `analyze-v2` |
| **风险检测** | 4 类风险 + 反讽排除 + 时序突发 + 三级分级 | `analyze-v2` |
| **对话预测** | Rule + RAG + MiroFish 三层融合 | `predict-v2` |
| **时间感知** | 距最后消息时间/周末/密集节奏调整回复时机 | `predict-v2` |
| **推演 + 解读** | 5 大推演（趋势/行为/情感轨迹/风险演化/走向）+ 4 大解读 | `analyze-v2` |
| **日历事件** | 从聊天提取约会/截止/提醒/生日/付款/出行 | `calendar` |
| **定时任务** | 每日/周/月/季/年自动生成报告 | `schedule` |
| **报告生成** | 单文件离线 HTML（内联 SVG 图表） | `--html` |
| **文件导入** | txt/json/docx/pdf，编码自动检测 | `--input` |

## 使用说明

### v2 分析命令

```bash
python scripts/main.py analyze-v2 --paste                          # 粘贴分析
python scripts/main.py analyze-v2 --input 聊天记录.txt               # 文件分析（自动识别编码）
python scripts/main.py analyze-v2 --input 聊天记录.txt --html report.html   # 生成离线 HTML 报告
python scripts/main.py predict-v2 --paste                          # 三层融合对话预测
python scripts/main.py graph-stats                                 # MiroFish 本地图谱统计
```

### 其他命令

```bash
python scripts/main.py demo                    # 一键体验内置示例
python scripts/main.py doctor                  # 环境自检（依赖/config/编码）
python scripts/main.py calendar --list         # 日历事件
python scripts/main.py schedule --list         # 定时任务
python scripts/main.py version                 # 查看版本
```

### v1.2.0 命令（向后兼容）

`analyze` / `report` / `schedule` / `serve` / `calendar` 全部保留，行为不变。

## 隐私与配置

- **100% 本地计算**，零外部网络请求（首次下载 embedding 模型除外）
- **运行时数据**（数据库等）默认存系统 tempdir，`WECHAT_ANALYZER_DATA_DIR` 环境变量可覆盖
- **可选能力**：RAG（`rag.enabled=false` 关闭）/ MiroFish（`mirofish.enabled=true` 启用）/ LLM（默认禁用，隐私优先）
- **上传前** `python clean.py --check` 检查残留（退出码 1=有残留），`python clean.py` 一键清理

## 常见问题

**Q: GBK 编码读取报错？** A: v2.1.0 起自动识别 utf-8-sig / utf-8 / gb18030，直接传入即可。

**Q: 大五人格全是 100%？** A: 已修复归一化，小样本收缩到 50 附近，信号充分时落在 15~85 区间。

**Q: 首次运行很慢？** A: RAG 首次需下载 embedding 模型（50-100MB），之后秒开。

**Q: 环境出问题怎么排查？** A: `python scripts/main.py doctor` 逐项检查并给修复建议。

**Q: v2 和 v1.2.0 结果不一致？** A: 正常，v2 引入 jieba 分词、否定识别等，更准确。

## 依赖安装

```bash
pip install -r requirements.txt          # 核心（必须：jieba/Flask/docx/pptx）
pip install -r requirements-rag.txt      # RAG（可选：sentence-transformers/chromadb）
python scripts/main_setup.py             # 一键配置
```

## 版本历史

- **v2.8.0** 零警告：非法转义修复 + Python 3.15 日期兼容 + 裸 except 收紧 + 编译烟囱测试
- **v2.7.0** scheduler 建表修复 + 日历/调度测试补全（272→302）
- **v2.6.0** 上传修复（.pyc/.db 二进制治本，`core/data_paths.py` 统一路径）
- **v2.5.0** 五 bug 修复 + 友好错误全链路 + 版本号单一来源
- **v2.4.0** jieba 情感修复 + 测试补全（160→235）
- **v2.3.0** 时间感知对话预测
- **v2.2.0** 推演 + 信息解读（10 大子能力）
- **v2.1.0** 本地图谱 + 编码检测 + 单文件 HTML 报告

> 完整功能说明见 [README.md](README.md) | 新手速查见 [RUNBOOK.md](RUNBOOK.md) | 故障排查见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
