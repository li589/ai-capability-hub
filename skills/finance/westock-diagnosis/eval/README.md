# 持仓诊断评测集

## 概述

评测集包含 10 个模拟持仓场景，覆盖均衡分散、重仓集中、单行业、深度套牢、大幅盈利、缺失数据、跨市场等典型 case。

评测分两层：
1. **脚本层**：直接调 `diagnose.py`，验证数据获取和计算是否正确
2. **端到端层**：通过 `openclaw agent` 走完整流程（识图/解析→脚本→白话报告），验证 agent 输出质量

## 场景列表

| 文件 | 场景 | 验证点 |
|------|------|--------|
| case_01_balanced.json | 均衡分散组合（5行业8只股） | 各项应为 green |
| case_02_concentrated.json | 单只重仓（茅台占~60%） | 集中度 red |
| case_03_single_sector.json | 全科技股 | 行业 red |
| case_04_deep_loss.json | 深度套牢（多只高成本买入） | 盈亏 red/yellow |
| case_05_big_profit.json | 大幅盈利（低成本买入） | 盈亏 green + 保护利润 |
| case_06_no_cost.json | 无成本价 | 盈亏 unknown，其他正常 |
| case_07_market_value_only.json | 只有市值和盈亏（无qty/cost） | 反推逻辑验证 |
| case_08_mixed_market.json | A股+港股混合 | 跨市场处理 |
| case_09_no_code.json | 只有名称没有代码 | 自动 search 补全 |
| case_10_full_position.json | 满仓无现金 | 现金 red（--cash 0） |

## 执行方式

### 1. 脚本层测试（快速验证计算逻辑）

```bash
# 在 westock-diagnosis 目录下执行（脚本与 case 路径均相对该目录）
cd /path/to/westock-diagnosis
python3 "$(pwd)/scripts/diagnose.py" --portfolio-file eval/case_01_balanced.json --cash 100000

# 批量（见下方评测脚本）
```

### 2. 端到端评测（完整流程）

使用评测脚本 `run_eval.sh`，对每个 case 开新 session 调 openclaw agent，保存：
- agent 输出的报告文本
- 脚本输出的 JSON
- session 轨迹数据（JSONL）

```bash
cd /path/to/westock-diagnosis/eval
bash run_eval.sh
```

### 3. 查看结果

评测结果保存在 `results/<timestamp>/` 目录下：

```
results/2026-04-09_1100/
├── summary.md                    # 汇总表：每个 case 的诊断标记 + 是否调了脚本
├── case_01_balanced/
│   ├── agent_output.txt          # agent 输出的报告
│   ├── script_output.json        # diagnose.py 的 JSON 输出
│   └── session_trace.jsonl       # openclaw session 轨迹
├── case_02_concentrated/
│   ├── ...
...
```

## 评估标准

### 脚本层
- 数据获取成功（无 error）
- 计算正确（市值=现价×qty，盈亏=(现价-成本)×qty）
- 诊断标记符合预期（见场景列表的"验证点"）
- 反推逻辑正确（case_07）
- 代码补全成功（case_09）

### 端到端
- agent 调用了 diagnose.py（而不是自己去调 westock-data）
- 报告结构符合输出要求（结论→建议→数据→调仓→免责）
- 白话表达自然、结论准确
- 缺失数据场景不编造数据
- 建议具体可执行
