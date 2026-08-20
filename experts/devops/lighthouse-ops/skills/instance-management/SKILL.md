---
name: instance-management
description: |
  Lighthouse 实例管理。用于查看实例列表、实例详情、启动/停止/重启实例、重置密码、查询登录 URL、创建新实例。
  触发场景：用户提到"查看实例"、"启动实例"、"停止实例"、"重启实例"、"重置密码"、"实例状态"、"创建实例"、"购买服务器"。
user-invocable: true
---

# 实例管理

管理腾讯云 Lighthouse 轻量应用服务器实例。

## 支持的操作

| 操作 | 风险 | 说明 |
|------|:----:|------|
| 查询实例列表 | 🟢 | 列出当前账号下所有实例 |
| 查询实例详情 | 🟢 | 查看单个实例的配置信息 |
| 查询登录 URL | 🟢 | 获取 WebShell 登录链接 |
| 查询可用套餐 | 🟢 | 列出可购买的实例套餐 |
| 查询可用镜像 | 🟢 | 列出可用的操作系统镜像 |
| 创建新实例 | 🟡 | 创建新的 Lighthouse 实例 |
| 启动实例 | 🟡 | 启动已停止的实例 |
| 停止实例 | 🟡 | 停止运行中的实例 |
| 重启实例 | 🟡 | 重启实例 |
| 重置密码 | 🟡 | 重置实例登录密码 |
| 执行远程命令（TAT） | 🟡 | 在实例上执行 Shell/PowerShell 命令 |

## 工作流程

1. **查询实例列表** — 获取 InstanceId 列表，不使用占位 ID
2. **确认操作对象** — 从列表中确认用户要操作的具体实例
3. **执行操作** — 使用真实 InstanceId
4. **验证结果** — 操作后重新查询状态确认

## 查询实例列表（分页）

`describe_instances` 默认只返回 **20 条**，账号下实例数较多时必须分页拉取，否则会遗漏。

### 分页参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|:----:|------|
| Offset | number | 0 | 偏移量，从第几条开始返回 |
| Limit | number | 20 | 单页返回数量，最大 100 |

### 拉取策略

1. 首次调用：`Offset=0, Limit=100`，从响应中获取 `TotalCount`（总实例数）
2. 若 `Offset + Limit < TotalCount`，继续以 `Offset += Limit` 翻页
3. 循环直到所有实例拉取完毕
4. 合并所有页的实例列表后再做筛选/统计

> **重要**：当用户问"我所有实例"或跨地域汇总时，必须分页拉满，否则统计结果不正确。

## 实例状态说明

| 状态 | 说明 |
|------|------|
| RUNNING | 运行中 |
| STOPPED | 已停止 |
| STARTING | 启动中 |
| STOPPING | 停止中 |
| REBOOTING | 重启中 |
| SHUTDOWN | 已隔离（已关机并隔离，与 STOPPED 处置方式不同） |
| FREEZING | 冻结中 |
| RESCUE_MODE | 救援模式 |

## 创建新实例

当用户要求"创建"、"部署"、"开通"实例时，默认创建新实例。

### 创建流程

1. 查询可用套餐 → `describe_bundles`
2. 查询可用镜像 → `describe_blueprints`
3. 确认套餐和镜像后 → 创建实例

### 镜像（Blueprint）

镜像 ID 格式为 `lhbp-` + 8 位随机字符（如 `lhbp-nspvqrsg`、`lhbp-2cacsycc`），**不存在语义化镜像 ID**。

请始终通过 `describe_blueprints` 查询可用镜像列表，从返回结果中获取真实 BlueprintId，不要使用占位或臆测的镜像 ID。

## 重置密码

- 密码复杂度要求：8-30 位，包含大小写字母、数字和特殊字符
- 重置密码后需重启实例生效

## 常见地域

| 地域代码 | 位置 |
|---------|------|
| ap-beijing | 北京 |
| ap-shanghai | 上海 |
| ap-guangzhou | 广州 |
| ap-chengdu | 成都 |
| ap-nanjing | 南京 |
| ap-hongkong | 香港 |
| ap-singapore | 新加坡 |
| ap-tokyo | 东京 |
| ap-seoul | 首尔 |
| ap-bangkok | 曼谷 |
| ap-jakarta | 雅加达 |
| ap-qingyuan | 清远 |
| na-siliconvalley | 硅谷 |
| na-ashburn | 阿什本 |
| eu-frankfurt | 法兰克福 |
| sa-saopaulo | 圣保罗 |
| me-saudi-arabia | 沙特阿拉伯 |

> 完整地域列表请通过 `describe_regions` 查询，以接口返回为准。

## 远程命令（TAT）

实例管理中可以触发的 TAT 命令，详细用法见 `remote-command` skill：

| 场景 | 命令示例 |
|------|---------|
| 系统概览 | `uptime && df -h && free -m` |
| 网络检查 | `ss -tlnp && ip addr show` |
| 服务状态 | `systemctl list-units --type=service --state=running` |
| 磁盘排查 | `df -h && du -sh /var/log/* \| sort -rh \| head -10` |

## 注意事项

- 实例 ID 格式为 `lhins-xxxxxxxx`
- 停止实例会中断所有服务，操作前确认
- 重置密码后需重启实例生效
- TAT 命令执行超时默认 60 秒
- 创建实例是创建新资源，不是在已有实例上部署
- Lighthouse 和 CVM 是不同产品，API 不互通
