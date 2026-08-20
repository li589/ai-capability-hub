# 监控告警配置完整清单

> 本文档为云运维专家技能的补充参考，包含全部40+监控指标、阈值定义和阿里云云监控配置方法。

---

## 1. 计算类指标（ECS/ACK/FC）

### 1.1 ECS实例指标

| 编号 | 指标名称 | MetricName | Namespace | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|------------|-----------|----------|----------|----------|----------|
| C-01 | CPU利用率 | CPUUtilization | acs_ecs_dashboard | ≥80% | ≥95% | 1min | 钉钉+短信 |
| C-02 | 内存利用率 | memory_usedutilization | acs_ecs_dashboard | ≥80% | ≥95% | 1min | 钉钉+短信 |
| C-03 | 内网入带宽 | IntranetInRate | acs_ecs_dashboard | ≥70%容量 | ≥90%容量 | 1min | 钉钉 |
| C-04 | 内网出带宽 | IntranetOutRate | acs_ecs_dashboard | ≥70%容量 | ≥90%容量 | 1min | 钉钉 |
| C-05 | 外网入带宽 | InternetInRate | acs_ecs_dashboard | ≥70%容量 | ≥90%容量 | 1min | 钉钉 |
| C-06 | 外网出带宽 | InternetOutRate | acs_ecs_dashboard | ≥70%容量 | ≥90%容量 | 1min | 钉钉 |
| C-07 | 磁盘读IOPS | DiskReadIOPS | acs_ecs_dashboard | ≥70%规格 | ≥90%规格 | 1min | 钉钉 |
| C-08 | 磁盘写IOPS | DiskWriteIOPS | acs_ecs_dashboard | ≥70%规格 | ≥90%规格 | 1min | 钉钉 |
| C-09 | CPU负载(5min) | load_5m | acs_ecs_dashboard | ≥核数×0.8 | ≥核数×1.2 | 1min | 钉钉+短信 |
| C-10 | 磁盘使用率 | diskusage_utilization | acs_ecs_dashboard | ≥80% | ≥95% | 5min | 钉钉+短信 |

**云监控配置示例（CPU利用率）：**

```bash
aliyun cms PutResourceMetricRule \
  --RuleName "ECS-CPU-Warn" \
  --Namespace acs_ecs_dashboard \
  --MetricName CPUUtilization \
  --Resources '[{"instanceId":"i-xxx"}]' \
  --Escalations.Warn.ComparisonOperator GreaterThanOrEqualToThreshold \
  --Escalations.Warn.Threshold 80 \
  --Escalations.Warn.Times 3 \
  --Escalations.Warn.Statistics Average \
  --Escalations.Critical.ComparisonOperator GreaterThanOrEqualToThreshold \
  --Escalations.Critical.Threshold 95 \
  --Escalations.Critical.Times 1 \
  --Escalations.Critical.Statistics Average \
  --Period 60 \
  --Webhook "https://oapi.dingtalk.com/robot/send?access_token=xxx"
```

### 1.2 ACK集群指标

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| C-11 | 节点CPU利用率 | ≥80% | ≥95% | 1min | 钉钉 |
| C-12 | 节点内存利用率 | ≥80% | ≥95% | 1min | 钉钉 |
| C-13 | Pod重启次数 | ≥2次/h | ≥5次/h | 5min | 钉钉+短信 |
| C-14 | 异常Pod数(非Running) | ≥1个 | ≥3个 | 1min | 钉钉+短信 |
| C-15 | Pod CPU Request使用率 | ≥80% | ≥95% | 5min | 钉钉 |
| C-16 | Pod Memory Request使用率 | ≥80% | ≥95% | 5min | 钉钉 |

### 1.3 函数计算FC指标

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 |
|------|----------|----------|----------|----------|
| C-17 | 函数错误率 | >0.5% | >2% | 1min |
| C-18 | 函数执行时长P99 | >预估200% | >预估500% | 1min |
| C-19 | 并发实例数 | ≥70%限额 | ≥90%限额 | 1min |

---

## 2. 数据库类指标

### 2.1 RDS MySQL/PostgreSQL

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| D-01 | CPU利用率 | ≥70% | ≥90% | 1min | 钉钉+短信 |
| D-02 | 内存利用率 | ≥80% | ≥95% | 1min | 钉钉+短信 |
| D-03 | 磁盘使用率 | ≥75% | ≥90% | 5min | 钉钉+短信+电话 |
| D-04 | 主从延迟 | ≥10s | ≥30s | 1min | 钉钉+短信 |
| D-05 | 慢查询数 | ≥10次/min | ≥50次/min | 1min | 钉钉 |
| D-06 | 连接数使用率 | ≥80% | ≥95% | 1min | 钉钉+短信 |
| D-07 | IOPS使用率 | ≥70% | ≥90% | 1min | 钉钉 |
| D-08 | 会话数 | ≥80%上限 | ≥95%上限 | 1min | 钉钉 |
| D-09 | 备份状态 | 备份失败 | 连续2天失败 | 1天 | 钉钉+短信 |

**RDS磁盘使用率告警（严重级别为电话通知，因为磁盘满是高危风险）：**

```bash
aliyun cms PutResourceMetricRule \
  --RuleName "RDS-Disk-Critical" \
  --Namespace acs_rds_dashboard \
  --MetricName DiskUsage \
  --Resources '[{"instanceId":"rm-xxx"}]' \
  --Escalations.Critical.ComparisonOperator GreaterThanOrEqualToThreshold \
  --Escalations.Critical.Threshold 90 \
  --Escalations.Critical.Times 1 \
  --Period 300 \
  --ContactGroups '["oncall-team"]' \
  --EnableStartTime 0 \
  --EnableEndTime 86400
```

### 2.2 Redis

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| D-10 | CPU利用率 | ≥70% | ≥90% | 1min | 钉钉 |
| D-11 | 内存使用率 | ≥80% | ≥95% | 1min | 钉钉+短信 |
| D-12 | 连接数 | ≥70%上限 | ≥90%上限 | 1min | 钉钉 |
| D-13 | 平均延迟 | ≥5ms | ≥20ms | 1min | 钉钉 |
| D-14 | 缓存命中率 | ≤90% | ≤80% | 5min | 钉钉 |
| D-15 | 内存碎片率 | ≥1.5 | ≥2.0 | 5min | 钉钉 |

### 2.3 DTS（迁移阶段专用）

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| D-16 | 数据同步延迟 | ≥60s | ≥300s | 1min | 钉钉+短信 |
| D-17 | 同步任务状态 | 状态波动 | Error | 即时 | 钉钉+短信+电话 |

---

## 3. 网络类指标（SLB/ALB/CDN）

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| N-01 | SLB活跃连接数 | ≥70%上限 | ≥90%上限 | 1min | 钉钉 |
| N-02 | 异常后端服务器数 | ≥1个 | ≥50%后端 | 1min | 钉钉+短信 |
| N-03 | 请求成功率 | ≤99% | ≤95% | 1min | 钉钉+短信 |
| N-04 | 4xx错误率 | >1% | >5% | 1min | 钉钉 |
| N-05 | 5xx错误率 | >0.1% | >1% | 1min | 钉钉+短信 |
| N-06 | 新建连接数 | ≥70%上限 | ≥90%上限 | 1min | 钉钉 |
| N-07 | 丢弃连接数 | >100/min | >500/min | 1min | 钉钉 |
| N-08 | CDN回源带宽 | ≥70%容量 | ≥90%容量 | 5min | 钉钉 |
| N-09 | CDN缓存命中率 | ≤85% | ≤70% | 5min | 钉钉 |

---

## 4. 存储类指标（ESSD/OSS/NAS）

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| S-01 | ESSD IOPS使用率 | ≥80%规格 | ≥95%规格 | 1min | 钉钉 |
| S-02 | ESSD IO等待时间 | ≥20ms | ≥50ms | 1min | 钉钉+短信 |
| S-03 | ESSD吞吐量 | ≥80%规格 | ≥95%规格 | 1min | 钉钉 |
| S-04 | OSS存储量 | ≥80%预算 | ≥95%预算 | 1天 | 钉钉 |
| S-05 | OSS 4xx请求数 | >100次/h | >500次/h | 5min | 钉钉 |
| S-06 | OSS 5xx请求数 | >10次/h | >50次/h | 5min | 钉钉+短信 |
| S-07 | NAS存储量 | ≥80%容量 | ≥95%容量 | 1天 | 钉钉 |
| S-08 | NAS读吞吐 | ≥70%规格 | ≥90%规格 | 5min | 钉钉 |
| S-09 | NAS写吞吐 | ≥70%规格 | ≥90%规格 | 5min | 钉钉 |

---

## 5. 中间件类指标

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 | 告警方式 |
|------|----------|----------|----------|----------|----------|
| M-01 | Kafka生产带宽 | ≥70%容量 | ≥90%容量 | 5min | 钉钉 |
| M-02 | Kafka消费带宽 | ≥70%容量 | ≥90%容量 | 5min | 钉钉 |
| M-03 | Kafka磁盘使用率 | ≥70% | ≥85% | 5min | 钉钉+短信 |
| M-04 | Kafka消费Lag | ≥10000 | ≥50000 | 1min | 钉钉 |
| M-05 | RocketMQ消息堆积 | ≥10000 | ≥50000 | 1min | 钉钉 |
| M-06 | Nacos配置变更 | 非预期变更 | 批量变更 | 即时 | 钉钉+短信 |
| M-07 | ES集群状态 | Yellow | Red | 1min | 钉钉+短信 |
| M-08 | ES JVM堆内存 | ≥75% | ≥90% | 1min | 钉钉 |

---

## 6. 成本告警指标

| 编号 | 指标名称 | 警告阈值 | 严重阈值 | 统计周期 |
|------|----------|----------|----------|----------|
| $-01 | 日费用环比 | 增长>20% | 增长>50% | 1天 |
| $-02 | 月费用预算 | ≥80%预算 | ≥95%预算 | 1天 |
| $-03 | 资源闲置率 | >20% | >40% | 1周 |
| $-04 | RI利用率 | <70% | <50% | 1周 |

---

## 7. 告警通知渠道配置

| 渠道 | 适用级别 | 配置方式 |
|------|----------|----------|
| 钉钉机器人 | P2/P3 | Webhook URL → 云监控告警联系人组 |
| 短信 | P1/P2 | 云监控联系人组绑定手机号 |
| 电话 | P1 | 云监控联系人组，仅绑定核心on-call人员 |
| 邮件 | P3/P4 | 云监控告警规则配置邮件通知 |
| 工单 | 自动创建 | 事件桥接EventBridge → 工单系统 |
