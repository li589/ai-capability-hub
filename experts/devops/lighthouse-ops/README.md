# Lighthouse 运维专家

腾讯云 Lighthouse（轻量应用服务器）官方运维专家，通过 WorkBuddy MCP 连接腾讯云账号后，可管理实例、防火墙、快照、监控、应用部署和远程命令。

## 功能

- **实例管理**：查询、启动、停止、重启实例，重置密码，创建新实例
- **防火墙管理**：查询、添加、删除防火墙规则
- **快照管理**：创建、查询、删除、回滚快照
- **监控告警**：查询 CPU/内存/带宽指标，查看流量包使用
- **应用部署**：部署 Web 应用、安装运行环境、Docker 部署、Nginx 反代
- **远程命令**：通过 TAT 在实例上执行 Shell/PowerShell 命令

## 连接方式

- MCP URL：`https://lightai.cloud.tencent.com/workbuddy/mcp`
- Transport：streamableHttp
- 认证：OAuth（腾讯云账号授权）

## Skills

| Skill | 说明 |
|-------|------|
| instance-management | 实例管理 |
| firewall-management | 防火墙管理 |
| snapshot-management | 快照管理 |
| monitoring | 监控告警 |
| application-deployment | 应用部署 |
| remote-command | 远程命令（TAT） |

## 版本

1.0.0
