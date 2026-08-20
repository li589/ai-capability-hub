# 自学习闭环详解（v7.0 新增）

> `scripts/learning/learning_engine.py` 的配套说明。目标：让建议系统"越用越准"——每条建议留痕、事后可考、参数可调、规则可进化。

## 目录
1. 闭环流程
2. 数据格式
3. hit 判定规则
4. 校准规则
5. 策略库（playbook）进化
6. 调用时序
7. 注意事项

---

## 1. 闭环流程

```
① log_advice        建议发生时留痕（含当时参数快照）
② auto_evaluate_pending / record_outcome   到期回填真实结果
③ compute_stats     按类型/动作分组统计命中率与平均超额
④ calibrate         样本≥5 时保守调整阈值参数
⑤ playbook_update   按规则胜率启用/停用策略
⑥ apply_calibration 下次建议读取新参数 → 回到 ①
```

## 2. 数据格式

**`data/learning/advice_log.jsonl`**（每行一条，追加写）：
```json
{"advice_id": "20260720-0001", "ts": "2026-07-20 15:30:00", "client_id": "u001",
 "kind": "rebalance", "target": "110022", "action": "减持止盈",
 "confidence": 0.7, "reasons": ["累计收益+32%超30%止盈线"],
 "context": {"nav_at_log": 1.85, "consensus_star": 4.0},
 "params_used": {"profit_take_threshold": 30, "drift_threshold": 5}}
```

**`data/learning/outcomes.jsonl`**：
```json
{"advice_id": "20260720-0001", "eval_ts": "2026-08-20 15:30:00",
 "horizon_days": 30, "fund_return": -3.2, "benchmark_return": -1.0,
 "action_benefit": 2.2, "hit": true}
```

**`data/learning/calibration.json`**：
```json
{"profit_take_threshold": 35, "stop_loss_threshold": -20, "drift_threshold": 5,
 "min_confidence": 0.6, "rating_weights": {}, "updated_at": "2026-08-20",
 "stats": {"total_advice": 42, "overall_hit_rate": 0.62},
 "adjust_log": [{"ts": "...", "param": "profit_take_threshold", "old": 30, "new": 35, "reason": "止盈命中率38%<40%"}]}
```

**`data/learning/playbook.json`**：
```json
[{"rule_id": "R001", "name": "止盈30%减持", "condition": {"profit_pct_gt": 30},
  "action": "减持止盈", "enabled": true,
  "stats": {"uses": 8, "evaluated": 6, "hits": 2, "win_rate": 0.33, "avg_benefit": -0.4},
  "last_updated": "2026-08-20"}]
```

数据目录优先级：构造参数 > 环境变量 `FUND_ADVISOR_LEARNING_DIR` > `data/learning/`。playbook 首次运行自动从 `scripts/learning/playbook_default.json` 拷贝初始化。

## 3. hit 判定规则

| 建议动作类型 | hit 条件（horizon 内） | action_benefit 定义 |
|------------|----------------------|--------------------|
| 减持/止盈/止损/替换出 | fund_return < benchmark_return（避开下跌） | benchmark − fund（避免的损失） |
| 增持/买入/新建仓 | fund_return > benchmark_return | fund − benchmark |
| 持有/观望 | 组合波动小于基准或跑赢 | fund − benchmark |

默认 horizon：30 天（短期信号）/ 90 天（配置建议）。

## 4. 校准规则

- **触发门槛**：该参数关联样本 ≥5 才调整，防止小样本过拟合
- **步进**：止盈/止损 ±5，漂移 ±1，单次单参数只调一次
- **边界**：止盈 [20,50]、止损 [-30,-10]、漂移 [3,10]、min_confidence [0.5,0.9]
- **方向**：命中率 <40% → 阈值更保守（更难触发）；>70% → 更积极
- **留痕**：每次调整写入 `adjust_log`（保留最近 20 条），可审计可回滚

## 5. 策略库（playbook）进化

内置 5 条初始规则（止盈 30%、止损 -20%、漂移 5%、评级 ≤2★ 转换、经理变更检视）。

- `win_rate < 35%` 且 `evaluated ≥ 5` → `enabled=false`（停用但不删除，保留统计）
- `win_rate > 70%` → 保持启用并标记强化
- 新规则通过 `add_rule(...)` 加入，初始 enabled=true、stats 清零
- 生成建议时优先引用 enabled 规则的 condition/action 与当前 calibration 参数

## 6. 调用时序

| 时机 | 调用 |
|------|------|
| 每次给出调仓/买卖建议 | `log_advice(...)` |
| 生成建议前 | `apply_calibration({...默认参数})` |
| 周/月检视 | `auto_evaluate_pending()` → `calibrate()` → `playbook_update()` |
| 客户质疑建议质量 | `get_learning_report()` |

## 7. 注意事项

1. **不得伪造样本**：命中率的价值在于真实；清空 learning/ 目录等于失忆
2. **小样本诚实**：样本 <5 时在报告中明示"样本不足，暂未校准"
3. **校准不改变建议性质**：参数只调阈值，不产生新建议类型
4. **离线程**：所有文件操作纯标准库 json/jsonl，无锁、追加写、损坏行跳过
