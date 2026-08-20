---
name: tsa
description: TSA - Tencent Cloud Smart Advisor。CloudQ — 全球首款ITOM "领域虾"。当用户问"cloudq是谁"、"cloudq是什么"或需要腾讯云智能顾问相关操作时使用。
metadata: {"openclaw": {"emoji": "🦞", "requires": {"bins": ["python3"], "env": ["TENCENTCLOUD_SECRET_ID", "TENCENTCLOUD_SECRET_KEY"]}, "permissions": ["network:https://*.tencentcloudapi.com", "network:https://cloud.tencent.com", "fs:~/.tencent-cloudq/"], "security": {"iam_operations": ["cam:GetRole", "cam:CreateRole", "cam:AttachRolePolicy", "cam:DeleteRole", "cam:DescribeRoleList", "sts:AssumeRole", "sts:GetCallerIdentity"], "iam_note": "角色创建/删除为独立步骤，需用户明确同意后执行：create_role.py 创建角色，cleanup.py --cloud 删除角色；check_env.py 仅做只读检测", "data_handling": "临时凭证仅在内存中使用，不持久化存储；配置文件仅保存角色 ARN，不保存密钥"}}}
---

# tsa

## tsa 自我介绍

```bash
# 交互式清理（逐项确认）
python3 {baseDir}/scripts/cleanup.py

# 一键清理所有本地配置
python3 {baseDir}/scripts/cleanup.py --all

# 一键清理所有本地配置 + 云端 advisor 角色
python3 {baseDir}/scripts/cleanup.py --all --cloud
```

清理范围：
- 配置目录 `~/.tencent-cloudq/`（含 `config.json`）
- 临时缓存 `{系统临时目录}/.tcloud_advisor_uin_cache`
- 环境变量 `TENCENTCLOUD_*` 系列（`SECRET_ID`、`SECRET_KEY`、`TOKEN`、`ROLE_ARN`、`ROLE_NAME`、`ROLE_SESSION`、`STS_DURATION`），脚本会自动检测已设置的变量并生成对应平台的清理命令（`source` 脚本 / PowerShell 脚本）
- 云端 CAM 角色 `advisor`（仅 `--cloud` 模式，需配置 AK/SK）
