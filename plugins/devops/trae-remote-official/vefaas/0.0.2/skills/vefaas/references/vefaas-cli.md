# CLI 与版本

## 安装或升级

```bash
npm i -g @volcengine/vefaas-cli@latest
vefaas --version
```

## 版本规则

- 推荐同时执行 `vefaas update --check` 检查可用更新；如果当前版本落后，提示用户升级后再继续。
- 升级 CLI 后，建议同步更新本 skill：`npx -y skills add vefaas-dev/skills -g -y`。
- 如果 CLI 版本更旧，先升级，不要尝试兼容旧命令。
- 如果缺少 `app`、`overview`、`resource`、`whoami` 等命令，先升级 CLI，并同步更新本 skill。
- 命令或 flag 不确定时，以当前 `vefaas --help` / `vefaas <command> --help` 为准。

## 资源模型

处理用户问题前，先判断用户说的是函数、应用、沙箱应用，还是沙箱实例。函数是 veFaaS（函数服务）的核心模型；应用和沙箱都建立在函数模型之上，但面向的用户场景不同。不要把这些资源的 ID 混用。

| 用户场景 | 主要资源 | 适合使用 |
| --- | --- | --- |
| 管理一段可运行代码或镜像本身，例如拉取代码、更新配置、查看版本和实例 | 函数 | `vefaas function <command>` 或 `vefaas fn <command>`，以及 `vefaas pull/push/deploy --funcId` |
| 部署一个网站、HTTP 服务、Demo 或完整 Serverless 应用，并希望方便发布和访问 | 应用 | `vefaas init`、`vefaas link`、`vefaas deploy`、`vefaas domains`、`vefaas env`、`vefaas config` |
| 创建一类可秒级拉起的云端隔离运行环境，例如代码沙箱、模型评测环境 | 沙箱应用 | `vefaas sandbox create/info/list/update/delete` |
| 为某次任务创建、暂停、恢复、关闭一个具体运行环境，或调整它的过期时间 | 沙箱实例 | `vefaas sandbox instance create/list/info/pause/resume/kill/timeout` |

## 顶层能力

```bash
vefaas function <command>        # alias: fn
vefaas application <command>     # alias: app
vefaas sandbox <command>
vefaas gateway <command>
vefaas resource <command>        # alias: res
vefaas overview
vefaas deploy
vefaas pull
vefaas push
vefaas env <action>
vefaas init
vefaas link
vefaas login
vefaas logout
vefaas whoami
vefaas api [action]
vefaas config [action]
vefaas domains
vefaas inspect
vefaas doctor
vefaas generateCaddy
vefaas update
vefaas completion <command>
```

## Console 视角查询

以下命令不是单个 Application 的生命周期操作，而是偏 Console/账号维度的只读查询：

```bash
vefaas overview
vefaas resource list
```

- `overview` 适合快速查看控制台概览类数据。
- `resource summary/list` 适合查询资源分配和使用情况；`resource` 也可写成 `res`，裸 `vefaas res` 默认展示 summary。
