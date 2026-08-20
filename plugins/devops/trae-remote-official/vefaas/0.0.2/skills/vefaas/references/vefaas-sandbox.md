# 沙箱管理

本页用于指导如何使用 `vefaas sandbox` 管理沙箱应用和沙箱实例。重点是理解"预热镜像 -> 沙箱应用 -> 沙箱实例"的流程；具体参数以 `vefaas sandbox <command> --help` 为准。

## Sandbox 模型

沙箱是一种特殊/定制的函数。它的 Function、Revision、Instance 模型和普通函数类似，但创建和运行方式不同：

- **Sandbox application**：沙箱应用，本质上是 `FunctionType=sandbox` 的函数资源。
- **Sandbox revision**：沙箱应用的镜像和配置版本。
- **Sandbox instance**：从沙箱应用主动创建出来的隔离运行实体。
- **预热镜像**：沙箱必须基于已预热镜像创建，预热后才能达到秒级拉起实例的效果。

## 常见使用流程

### 1. 选择或预热镜像

```bash
vefaas sandbox images public
vefaas sandbox images private
vefaas sandbox images precache <image-url>
```

### 2. 创建沙箱应用

```bash
vefaas sandbox create --name <sandbox-name> --image-id <image-id>
```

### 3. 更新配置并发布 Revision

用 `vefaas sandbox config` 或 `vefaas deploy --sandboxId`，然后用 `vefaas sandbox release` 发布新 revision。

### 4. 主动创建沙箱实例

```bash
vefaas sandbox instance create --id <sandbox-application-id>
vefaas sandbox instance list --id <sandbox-application-id>
```

### 5. 管理实例生命周期

- **pause/resume**：暂停和恢复实例。
- **timeout**：查询或调整实例过期时间。
- **kill**：销毁实例（高风险操作）。
- **webshell/logs**：进入实例或查看日志。

### 6. 排障顺序

1. 确认镜像是否已预热成功。
2. 用 `vefaas sandbox info` 检查沙箱应用配置。
3. 用 `vefaas sandbox instance list` / `describe` 检查实例状态。
4. 通过实例日志或 WebShell 排查启动失败问题。
