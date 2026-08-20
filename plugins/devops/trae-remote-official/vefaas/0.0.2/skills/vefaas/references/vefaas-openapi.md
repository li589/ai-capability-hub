# OpenAPI 调用

高阶命令无法覆盖，或用户明确要求调用 veFaaS OpenAPI action 时，使用 `vefaas api <Action>`。

## CRITICAL 调用顺序

**CRITICAL — 调用任何具体 Action 前，MUST 先运行 `vefaas api <Action> --help` 查看参数结构。不要猜测参数名、大小写、请求体结构或 ID 字段。**

推荐顺序：

1. 用高阶命令确认是否已经能完成目标；能完成就不要走 OpenAPI。
2. 确定必须调用的 Action。
3. 运行 `vefaas api <Action> --help` 查看参数结构和示例。
4. 如果 Action 涉及其它资源，先调用相关资源的查询接口获取真实 ID。
5. 再调用目标 Action。

## 探索

```bash
vefaas api --help
vefaas api GetFunction --help
vefaas api ListFunctions --PageSize 10 -o table
vefaas api GetFunction --Id <function-id> --output json
```

## 参数模式

简单参数用 flag：

```bash
vefaas api ListFunctions --PageSize 10 --output table
vefaas api GetFunction --Id <function-id> --output json
```

复杂请求体用 JSON：

```bash
vefaas api UpdateFunction --body '{"Id":"<function-id>","Description":"new description"}'
vefaas api UpdateFunction --body @request.json
```

## 输出处理

```bash
vefaas api ListFunctions --output table --fields Id,Name,Runtime --limit 5
vefaas api ListFunctions --output json --jq '.data'
```

## 规则

- 高阶命令能完成任务时，优先使用高阶命令。
- 每次调用具体 Action 前，先执行 `vefaas api <Action> --help`。
- 涉及其它资源时，先用相关查询接口获取真实标识符。
- 大 JSON 或敏感 JSON 优先使用 `--body @file` 或 `--body -`。
- 破坏性 action 不要猜参数；必须先执行 list/get/read 类 action 或查看 help。
