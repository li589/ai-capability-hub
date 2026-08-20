---
name: remote-command
description: |
  Lighthouse 远程命令（TAT）。用于在实例上远程执行 Shell/PowerShell 命令、查询执行结果。
  触发场景：用户提到"执行命令"、"远程命令"、"跑个命令"、"TAT"、"shell"、"诊断"、"检查磁盘"、"查看进程"。
user-invocable: true
---

# 远程命令（TAT）

通过腾讯云自动化工具（TAT）在 Lighthouse 实例上远程执行命令。

## 支持的操作

| 操作 | 风险 | 说明 |
|------|:----:|------|
| 执行命令 | 🟡 | 在实例上执行 Shell/PowerShell 命令 |
| 查询执行状态 | 🟢 | 查询命令执行是否完成 |
| 查询执行结果 | 🟢 | 获取命令执行的详细输出 |
| 查询命令列表 | 🟢 | 列出历史执行过的命令 |

## 执行命令

### 参数说明

| 参数 | 必填 | 说明 |
|------|:----:|------|
| InstanceIds | ✅ | 目标实例 ID 列表 |
| Content | ✅ | 命令内容（Shell 或 PowerShell） |
| Timeout | ❌ | 超时时间，默认 60 秒 |
| CommandType | ❌ | SHELL（默认）或 POWERSHELL |
| WorkingDirectory | ❌ | 命令工作目录 |
| Username | ❌ | 执行命令的用户 |

### 执行流程

1. 通过 `describe_instances` 获取 InstanceId
2. 通过 TAT 执行命令 → 返回 InvocationId
3. 通过 InvocationId 查询执行状态
4. 状态为成功后获取详细输出

> 命令是异步执行的，必须轮询执行状态直到完成。

## 常用诊断命令

### 系统概览

```bash
uptime && df -h && free -m && top -bn1 | head -20
```

### 网络检查

```bash
ss -tlnp && ip addr show
```

### 服务状态

```bash
systemctl list-units --type=service --state=running
```

### 磁盘使用

```bash
df -h && du -sh /var/log/* | sort -rh | head -10
```

### 进程排查

```bash
ps aux --sort=-%mem | head -20
```

### 日志排查

```bash
# 查看最近 100 行系统日志
journalctl -n 100 --no-pager

# 查看 Nginx 访问日志
tail -100 /var/log/nginx/access.log

# 查看应用日志
tail -100 /var/log/myapp/app.log
```

### 网络连通性

```bash
# 测试外网连通性
ping -c 4 8.8.8.8

# 测试端口连通性
telnet example.com 443
# 或
curl -v telnet://example.com:443
```

## 执行状态说明

| 状态 | 说明 |
|------|------|
| PENDING | 命令已下发，等待执行 |
| RUNNING | 正在执行 |
| SUCCESS | 执行成功 |
| FAILED | 执行失败 |
| TIMEOUT | 执行超时 |
| CANCELLED | 已取消 |

## 注意事项

- 命令执行是异步的，执行后需轮询状态
- 默认超时 60 秒，长时间任务需设置更大的 Timeout
- 高危命令（`rm -rf`、`dd`、`mkfs` 等）需用户二次确认
- 命令在 root 用户下执行（除非指定 Username）
- 多实例同时执行时，每个实例返回独立的执行结果
