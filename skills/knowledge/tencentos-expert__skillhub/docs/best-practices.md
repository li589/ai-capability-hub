# 最佳实践

## Prompt 编写最佳实践

### 1. 信息收集要全面

在开始诊断之前，先收集足够的上下文信息：

```bash
# 系统基本信息
uname -a
cat /etc/os-release

# 运行时间和负载
uptime

# 当前资源使用
free -h
df -h
```

### 2. 命令要有注释

```bash
# 查找占用端口的进程
ss -tlnp | grep :80

# 查看进程打开的文件数
ls -la /proc/<pid>/fd | wc -l
```

### 3. 输出格式要统一

```
=== 诊断报告 ===

检查项目: XXX
状态: [正常/异常]

发现问题:
1. ...

建议操作:
1. ...
```

### 4. 考虑各种情况

- 工具不存在时的替代方案
- 权限不足时的提示
- 异常情况的处理

## 脚本编写最佳实践

### 1. 错误处理

```bash
#!/bin/bash
set -e  # 遇错即停
set -u  # 未定义变量报错
set -o pipefail  # 管道错误

trap 'echo "Error at line $LINENO"' ERR
```

### 2. 参数验证

```bash
if [ -z "${1:-}" ]; then
    echo "Usage: $0 <pid>"
    exit 1
fi
```

### 3. 使用函数封装

```bash
collect_cpu_info() {
    local pid=$1
    # ...
}

analyze_data() {
    # ...
}

main() {
    collect_cpu_info "$1"
    analyze_data
}

main "$@"
```

### 4. 日志和调试

```bash
DEBUG=${DEBUG:-0}

debug() {
    if [ "$DEBUG" -eq 1 ]; then
        echo "[DEBUG] $*" >&2
    fi
}
```

## 安全最佳实践

### 1. 最小权限原则

只在必要时请求 root 权限。

### 2. 危险操作需确认

```bash
if [ "$action" = "delete" ]; then
    read -p "确认删除? [y/N] " confirm
    if [ "$confirm" != "y" ]; then
        exit 0
    fi
fi
```

### 3. 备份重要数据

```bash
# 修改配置前先备份
cp /etc/config /etc/config.bak.$(date +%Y%m%d)
```

### 4. 记录操作日志

```bash
exec > >(tee -a /var/log/skill.log) 2>&1
echo "$(date): Starting operation..."
```

## 性能最佳实践

### 1. 避免不必要的循环

```bash
# 不好
for file in $(find /var/log -name "*.log"); do
    wc -l "$file"
done

# 好
find /var/log -name "*.log" -exec wc -l {} +
```

### 2. 使用高效的工具

```bash
# 使用 awk 替代 grep + cut
awk -F: '/pattern/ {print $2}' file
```

### 3. 限制输出量

```bash
# 只显示前 20 条
head -20
# 限制 find 深度
find /var -maxdepth 2 -name "*.log"
```

## 文档最佳实践

### 1. 保持文档与代码同步

修改代码时同步更新文档。

### 2. 提供示例

每个功能都提供使用示例。

### 3. 说明限制

明确说明技能的适用范围和限制。

### 4. 版本更新记录

记录每个版本的变更内容。
