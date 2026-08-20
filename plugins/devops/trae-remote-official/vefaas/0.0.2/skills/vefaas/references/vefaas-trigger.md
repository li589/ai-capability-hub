# 触发器与 APIG Route

本页用于指导函数的 APIG 触发器，以及沙箱应用的网关路由配置。

## 适用场景

- 用户要绑定 APIG 触发器、查看触发器、创建访问入口。
- 用户要管理 Timer、Kafka、RocketMQ、BMQ、TLS 等函数触发器。
- 用户要修改 APIG route 的 path、method、timeout、CORS。
- 用户遇到 APIG 权限不足、route 找不到、访问地址不可用。

## 触发器列表

```bash
vefaas fn trigger list --id <function-id> -o json
vefaas sandbox trigger list --id <sandbox-application-id> -o json
```

## 绑定 APIG 触发器

绑定前确认函数已经发布。先查可用 gateway：

```bash
vefaas gateway list --first
```

为函数绑定：

```bash
vefaas trigger apig --id <function-id> --gateway-id <gateway-id>
```

为沙箱应用绑定：

```bash
vefaas sandbox trigger apig --id <sandbox-application-id> --gateway-id <gateway-id>
```

## 编辑 APIG Route

```bash
vefaas trigger apig update --route-id <route-id> --path /api --methods GET,POST
vefaas trigger apig update --route-id <route-id> --timeout 30
vefaas trigger apig update --route-id <route-id> --cors
```

## 非 APIG 函数触发器

```bash
vefaas fn trigger timer create --id <function-id> --body @timer.json
vefaas fn trigger kafka get --id <function-id> --trigger-id <trigger-id> -o json
```

## 排障顺序

1. `vefaas login --check`：确认凭据。
2. `vefaas fn info --id <function-id>`：确认资源可访问。
3. `vefaas fn trigger list --id <function-id> -o json`：确认触发器。
