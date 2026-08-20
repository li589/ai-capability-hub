# WorkBuddy 运行兼容性（本 Skill 强制）

> 与 `SKILL.md` 中「WorkBuddy 运行兼容」章节一致；冲突时以本文件 + 隐私边界为准。

## CLI 入口

```bash
SL="$HOME/.slclaw/bin/sl"; [ -f "$HOME/.slclaw/bin/sl.cmd" ] && SL="$HOME/.slclaw/bin/sl.cmd"
"$SL" marketing_crm <subcommand> ...
```

| 禁止 | 原因 |
|------|------|
| PATH / `which` / `where` | WorkBuddy 环境通常无 PATH |
| Bash 写 `%USERPROFILE%\...` | PortableGit 不展开 → 失败 |
| Windows Bash 跑无 `.cmd` 的 `sl` | 常 exit 126 |
| Python/Node 脚本转发 | 统一直接调绝对路径 CLI |

PowerShell 备用时 stdout 必须直出（`Write-Output`），禁止只捕获不打印。

## 执行边界

禁止：`--verbose`/`-v`、`--header`、`--envPath`、`--body-file`、`sl token show`、动态 DataCube、可变任务 ID、`title/where`、直连 MCP/DB。

## 隐私

不向对话输出 Token/密钥/完整认证参数；不展示可绕过权限的内部实现细节。默认不做触达/发券/导出明细/改活动等写操作。
