# 函数管理

本页用于指导如何使用 `vefaas fn` 管理函数。重点是理解函数类型、代码形态和常见生命周期；具体参数以 `vefaas fn <command> --help` 为准。

## Function 模型

函数是 veFaaS（函数服务）的核心资源，承载代码或镜像、运行时、启动命令、端口、环境变量、CPU/内存、并发、超时、触发器、版本、实例、任务、日志和监控。

- **Function**：函数资源本身，是用户主要创建和管理的对象。
- **Revision**：函数代码/镜像和配置形成的版本快照，发布、回滚围绕 revision 展开。
- **Instance**：运行 revision 的实际执行单元，普通函数实例通常由平台按请求流量和扩缩容策略动态创建或回收。

## 函数类型

| 类型 | 适用场景 | 特点 |
| --- | --- | --- |
| `runtime` | 事件函数、轻量逻辑 | 使用 Python/Node.js/Go 等托管 runtime |
| `webserver` | HTTP Web 服务、API 服务 | 默认类型，有启动命令和监听端口 |
| `microservice` | 需要常驻的微服务 | CPU 策略默认偏常驻 |
| `job` | 异步任务、批处理 | 默认独占执行，适合长耗时任务 |

## 常见使用流程

### 1. 定位或创建函数

已有函数时，先用 `vefaas fn list` / `vefaas fn info` 确认函数 ID、类型、source、runtime、端口和当前配置。新建函数时，用 `vefaas fn create`。

### 2. 本地修改并推送代码

已有函数可以用 `vefaas fn pull` 拉取代码到本地。修改代码后用 `vefaas fn push` 上传。`push` 只负责上传，不等同于发布上线。

### 3. 更新函数配置

函数配置包括启动命令、端口、CPU/内存、并发、超时、环境变量等。简单配置可用 `vefaas fn config` 和 `vefaas fn env` 更新。

### 4. 发布

确认代码和配置无误后，用 `vefaas fn release` 发布新 revision。发布后可用 `vefaas fn revision` 查看版本信息。若发布后发现问题，用 `vefaas fn rollback` 回滚。

### 5. 测试调用

发布后用 `vefaas fn invoke` 做测试调用：

```bash
vefaas fn invoke --id <function-id> --data '{"hello":"vefaas"}'
vefaas fn invoke --id <function-id> --method GET --path /v1/ping
```

### 6. 绑定触发器并对外访问

如果函数需要对外提供访问地址，需要绑定 APIG 触发器。详见 [触发器与 APIG Route](vefaas-trigger.md)。

### 7. 查看实例日志排障

线上请求异常时，先用 `vefaas fn instances` 找到相关实例，再用 `vefaas fn logs` 查看实例日志。
