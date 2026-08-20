# 盈绰服务云

盈绰服务云物业运营 CLI 工具，用于处理收费催缴、工单、多业态营收操作。

## 默认配置

发布版本通过构建产物内置正式环境地址，首次使用只需配置 `apiKey`：

```bash
./scripts/yc-cloud.sh config set apiKey <accessKey>
```

如需切换测试/生产环境，请更换对应 `make build-*` 或 `make install-*` 产物。

## macOS

支持 Apple Silicon（arm64）和 Intel Mac（x64），脚本按本机架构自动运行。

```bash
./scripts/yc-cloud.sh --help
./scripts/yc-cloud.sh config list
```

## Windows

使用 WorkBuddy 环境提供的 yc-cloud 工具运行。

```powershell
.\yc-cloud.exe --help
.\yc-cloud.exe config list
```

## 模块文档

正式 Skill 入口为 `SKILL.md`，业务模块说明在 `references/` 目录，使用前须读取对应文件：

| 文件 | 内容 |
|------|------|
| references/runtime.md | CLI 启动方式、禁止绕过启动脚本 |
| references/list-query.md | 列表筛选、分组、汇总、排行的快速查询计划 |
| references/billing-system.md | 收费催缴、应收管理、分享账单、房屋租客、员工状态、多业态营收 |
| references/workder-order.md | 5.9 工单管理（创建/派单/认领/审批/退回/评价） |
| references/travel.md | 旅游店铺权限、旅游订单列表、订单状态统计 |
| references/flash.md | 闪购日报、注册量、下单量统计 |

## 参考文档

技术文档在 `docs/` 目录，建议先看 `docs/COMMAND_SPEC.md`。
