---
name: log-analyzer
display_name: 日志分析器
description: 智能日志分析工具。支持 nginx、Apache、应用日志等多种格式，自动提取错误模式、性能指标、访问趋势，生成可视化分析报告。帮助开发者快速定位问题、优化性能。
version: 1.0.0
author: 叶建国
homepage: https://github.com/openclaw/log-analyzer
tags:
  - 日志分析
  - 运维工具
  - nginx
  - 性能监控
  - 错误排查
  - 数据分析
license: MIT
compatibility:
  - openclaw
  - skillhub
---

# 日志分析器 (Log Analyzer)

> 📊 智能分析 | 多格式支持 | 错误定位 | 性能优化

## 简介

日志分析器是一个智能日志分析工具，支持 nginx、Apache、应用日志等多种格式。自动提取错误模式、性能指标、访问趋势，生成可视化分析报告。

**适用场景**：当用户提到"分析日志"、"查看错误日志"、"nginx日志分析"、"性能瓶颈"、"排查问题"、"日志监控"时使用此 Skill。

---

## 支持的日志格式

| 类型 | 格式 | 说明 |
|------|------|------|
| **Nginx** | Combined / JSON | 访问日志、错误日志 |
| **Apache** | Common / Combined | 访问日志、错误日志 |
| **应用日志** | JSON / Plain Text | Spring Boot、Django、Node.js 等 |
| **系统日志** | Syslog | /var/log/syslog、journalctl |
| **自定义** | 可配置 | 支持自定义正则解析 |

---

## 核心功能

### 1. 错误分析

- 错误类型统计
- 错误趋势图
- 错误堆栈提取
- 高频错误 TOP10

### 2. 性能分析

- 响应时间分布
- 慢请求识别（>1s、>3s、>5s）
- 吞吐量统计
- 峰值时段分析

### 3. 访问分析

- PV/UV 统计
- 热门 URL TOP10
- 状态码分布
- 用户代理分析
- 地理位置分布（IP解析）

### 4. 安全分析

- 异常请求检测
- SQL 注入尝试识别
- XSS 攻击识别
- 暴力破解检测
- IP 黑名单建议

---

## 快速使用

### 分析 nginx 访问日志

```bash
# 基础分析
log-analyzer analyze --file /var/log/nginx/access.log --type nginx

# 指定时间范围
log-analyzer analyze --file /var/log/nginx/access.log --type nginx --from "2026-04-01" --to "2026-04-05"

# 输出报告
log-analyzer analyze --file /var/log/nginx/access.log --type nginx --output report.html
```

### 分析应用错误日志

```bash
# 分析错误日志
log-analyzer analyze --file /var/log/app/error.log --type app --level error

# 查找特定错误
log-analyzer search --file /var/log/app/error.log --pattern "Connection timeout"
```

### 实时监控

```bash
# 实时分析新增日志
log-analyzer tail --file /var/log/nginx/access.log --type nginx --alert
```

---

## 分析维度

### Nginx 访问日志分析

```
日志格式示例：
192.168.1.1 - - [04/Apr/2026:10:30:45 +0800] "GET /api/users HTTP/1.1" 200 1024 "-" "Mozilla/5.0"
```

**分析指标：**

| 指标 | 说明 |
|------|------|
| 总请求数 | 统计时间范围内的总请求 |
| 成功率 | 2xx状态码占比 |
| 错误率 | 4xx/5xx状态码占比 |
| 平均响应时间 | 所有请求的平均耗时 |
| P50/P90/P95/P99 | 响应时间分位数 |
| 吞吐量 | QPS/TPS |
| 流量统计 | 总传输字节数 |

**输出报告示例：**

```
═══════════════════════════════════════════════════
            Nginx 访问日志分析报告
═══════════════════════════════════════════════════

分析时间：2026-04-01 00:00:00 ~ 2026-04-05 23:59:59
日志行数：1,234,567

【概览】
总请求数：1,234,567
独立IP数：45,678
成功率：98.5%
错误率：1.5%
平均响应时间：45ms
吞吐量：14.3 QPS

【响应时间分布】
< 100ms：85.2%
100-500ms：12.3%
500ms-1s：1.8%
1-3s：0.5%
> 3s：0.2%

【状态码分布】
200：98.2%
404：1.2%
500：0.3%
502：0.2%
504：0.1%

【TOP 10 请求URL】
1. /api/users - 123,456次 (10.0%)
2. /api/products - 98,765次 (8.0%)
3. /static/js/main.js - 87,654次 (7.1%)
...

【TOP 10 错误URL】
1. /api/legacy/v1/data - 1,234次 (500错误)
2. /wp-admin/wp-login.php - 567次 (404错误，疑似扫描)
3. /api/payment - 345次 (502错误，下游超时)
...

【慢请求分析 (>1s)】
总数：2,345次 (0.19%)
平均耗时：2.3s
主要慢请求：
1. /api/report/export - 1,234次，平均2.5s
2. /api/data/import - 876次，平均3.1s
...

【疑似攻击IP】
192.168.100.1 - 尝试访问/wp-login.php 1,234次
192.168.100.2 - SQL注入尝试 567次
建议：加入黑名单或启用WAF

═══════════════════════════════════════════════════
```

---

### 应用错误日志分析

```
日志格式示例：
[2026-04-05 10:30:45] [ERROR] [user-service] Connection timeout after 30000ms
```

**分析指标：**

| 指标 | 说明 |
|------|------|
| 错误总数 | 各级别错误数量 |
| 错误类型分布 | 按错误类型分类 |
| 错误趋势 | 时间线趋势图 |
| 高频错误 | 出现次数最多的错误 |
| 堆栈分析 | 提取完整堆栈信息 |

**输出报告示例：**

```
═══════════════════════════════════════════════════
          应用错误日志分析报告
═══════════════════════════════════════════════════

分析时间：2026-04-05
日志行数：12,345

【错误概览】
ERROR：234次
WARN：1,234次
INFO：10,876次

【错误类型 TOP 10】
1. Connection timeout - 123次 (52.6%)
2. NullPointerException - 45次 (19.2%)
3. Database connection pool exhausted - 34次 (14.5%)
...

【错误趋势】
10:00 - 23次
11:00 - 45次 (⚠️ 峰值)
12:00 - 12次
...

【高频错误详情】

错误 #1：Connection timeout
出现次数：123次
影响服务：user-service, order-service
可能原因：下游服务响应慢或网络问题
建议：检查服务间调用超时设置，增加熔断机制

错误 #2：NullPointerException
出现次数：45次
堆栈：
  at com.example.UserService.getUser(UserService.java:45)
  at com.example.UserController.getUser(UserController.java:23)
可能原因：未处理空值情况
建议：添加空值检查，使用Optional

【时间分布】
错误集中在 11:00-12:00 时段，可能与业务高峰期相关

═══════════════════════════════════════════════════
```

---

## 安全分析

### 异常请求检测

```
【疑似攻击行为】

1. SQL注入尝试
   IP：192.168.100.10
   请求：/api/search?q=' OR '1'='1
   次数：45次
   建议：加入黑名单

2. 目录遍历尝试
   IP：192.168.100.11
   请求：/../../../etc/passwd
   次数：23次
   建议：启用WAF规则

3. 暴力破解
   IP：192.168.100.12
   目标：/admin/login
   尝试次数：567次
   建议：启用登录限速

【高危IP列表】
192.168.100.10 - 攻击类型：SQL注入 - 建议：永久封禁
192.168.100.11 - 攻击类型：目录遍历 - 建议：永久封禁
192.168.100.12 - 攻击类型：暴力破解 - 建议：限速/封禁
```

---

## 使用场景

### 场景一：排查线上问题

```
用户：服务响应很慢，帮我分析一下

分析步骤：
1. 分析 nginx 访问日志，找出慢请求
2. 分析应用日志，找出错误和超时
3. 关联分析，定位问题根源
4. 生成报告，给出优化建议
```

### 场景二：日常监控

```
用户：我想每天看看系统健康状况

分析步骤：
1. 定时分析昨日日志
2. 生成日报，发送邮件/钉钉
3. 发现异常自动告警
```

### 场景三：性能优化

```
用户：想优化系统性能，从哪里入手？

分析步骤：
1. 分析响应时间分布
2. 找出慢请求TOP10
3. 分析数据库慢查询
4. 给出优化建议
```

---

## 命令参考

### 基础命令

| 命令 | 说明 |
|------|------|
| `analyze` | 分析日志文件 |
| `search` | 搜索特定内容 |
| `tail` | 实时监控 |
| `compare` | 对比不同时期 |
| `export` | 导出报告 |

### 常用参数

| 参数 | 说明 |
|------|------|
| `--file` | 日志文件路径 |
| `--type` | 日志类型 (nginx/apache/app/syslog) |
| `--from` | 开始时间 |
| `--to` | 结束时间 |
| `--output` | 输出文件 |
| `--format` | 输出格式 (text/json/html) |

---

## 配置文件

```yaml
# log-analyzer.yml
analysis:
  # 慢请求阈值（毫秒）
  slow_threshold: 1000
  
  # 错误级别
  error_levels:
    - ERROR
    - FATAL
    - CRITICAL
  
  # 安全检测规则
  security_rules:
    sql_injection:
      patterns:
        - "(union|select|insert|update|delete|drop).*--"
        - "'\s*or\s*'"
    xss:
      patterns:
        - "<script"
        - "javascript:"
    brute_force:
      threshold: 10  # 10分钟内超过10次登录尝试
      target_paths:
        - "/admin/login"
        - "/wp-login.php"
  
  # 告警配置
  alerts:
    error_rate_threshold: 5  # 错误率超过5%告警
    slow_request_threshold: 100  # 慢请求超过100次/小时告警
    qps_threshold: 1000  # QPS超过1000告警
```

---

## 输出格式

### 文本格式（默认）

适合终端查看，简洁明了。

### JSON 格式

```json
{
  "summary": {
    "total_requests": 1234567,
    "unique_ips": 45678,
    "success_rate": 98.5,
    "error_rate": 1.5,
    "avg_response_time": 45
  },
  "top_urls": [
    {"url": "/api/users", "count": 123456, "percentage": 10.0}
  ],
  "status_codes": {
    "200": 1212345,
    "404": 14815,
    "500": 3704
  }
}
```

### HTML 报告

生成可视化图表的报告文件，适合分享和存档。

---

## 与其他工具集成

| 工具 | 集成方式 |
|------|----------|
| ELK Stack | 读取 Elasticsearch 数据 |
| Grafana | 导出 Prometheus 格式 |
| 钉钉/飞书 | Webhook 告警 |
| CI/CD | 构建时日志检查 |

---

## 注意事项

- ⚠️ 大日志文件建议先切割或使用流式分析
- ⚠️ 生产环境分析时注意性能影响
- ⚠️ 敏感信息（密码、token）会自动脱敏
- ⚠️ 定期清理生成的报告文件

---

## 更新日志

### v1.0.0 (2026-04-05)
- 初始版本发布
- 支持 nginx/Apache/应用日志分析
- 错误分析、性能分析、访问分析、安全分析
- 多格式输出（text/json/html）
