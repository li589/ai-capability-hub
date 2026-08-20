---
name: tapd-openapi
description: TAPD OpenAPI 命令行工具。将 TAPD 平台的全量 OpenAPI 封装为 tapd-cli
  命令，适用于终端脚本、自动化管线和 AI Agent调用。
version: 1.0.6
allowed-tools: Bash,Read,Glob,Grep
display_name: TAPD
display_name_en: TAPD
description_zh: TAPD 项目管理平台操作（需求、缺陷、任务、迭代、Wiki）
description_en: TAPD project management (stories, bugs, tasks, iterations, wiki)
visibility: public
disable-model-invocation: true
---

# tapd-cli Skill

TAPD OpenAPI 命令行工具，无需手动拼接 curl，直接用 `tapd-cli <entity> <subcommand> [key=value]` 调用。

## 安装

```bash
# 克隆仓库到 skills 目录
git clone https://cnb.cool/tapd.cn/skills/tapd-cli ~/.codebuddy/skills/tapd-cli
```

安装后目录结构：
```
~/.codebuddy/skills/tapd-cli/
├── skills/tapd-cli/scripts/tapd-cli.cjs   # 预构建产物（直接运行）
└── README.md # 说明文档
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `TAPD_API_ENDPOINT` | 是 | API 端点，如 `https://api.tapd.cn` |
| `TAPD_TOKEN` | 是 | Bearer Token（从 TAPD 开放平台获取） |
| `TAPD_WORKSPACE_IDS` | 建议 | 项目 ID，逗号分隔多个，第一个为默认值 |
| `TAPD_NPC_ROLE` | 否 | NPC 登录名，作为默认 creator |
| `TAPD_CLI_LOG` | 否 | 日志模式：`text`（文本）/ `json` / `silent`（默认） |

## 工具权限

- `Glob` / `Grep` 用于在本地 skill 包、README 或相关说明中查找命令、参数和示例。

## 运行方式

需要 Node.js 18+。添加以下环境变量到 `~/.bashrc` 或 `~/.zshrc`：

```bash
alias tapd-cli="node ~/.codebuddy/skills/tapd-cli/skills/tapd-cli/scripts/tapd-cli.cjs"
```

之后即可直接执行：

```bash
tapd-cli <entity> <subcommand> [key=value ...]
```

## 功能覆盖

详见仓库 [README](https://cnb.cool/tapd.cn/skills/tapd-cli)，以最新版本为准：

| 实体 | 支持操作 |
|------|---------|
| `story` | add / list / update / count / fields / custom-fields / categories / category-count / related-bugs / changes / changes-count / link / get-tcase / add-tcase / copy / link-bug / unlink-bug / all-links / batch-update |
| `bug` | add / list / update / count / fields / custom-fields / changes / changes-count / related-stories / link-tcase / copy / link-bug / unlink-bug / all-links / batch-update |
| `task` | add / list / update / count |
| `tcase` | add / batch-add / list / update / count / fields / categories / add-category / execute / assign / result / link-plan / remove-from-plan / unlink-story / count-by-category / category-count / custom-fields / story-by-tcase / import-xmind |
| `testplan` | add / list / update / count / details / progress / tcases / bugs / stories / link-story / unlink-story / by-iteration / fields / tcase-relation |
| `comment` | add / list / count |
| `iteration` | list |
| `wiki` | add / list / update / count |
| `timesheet` | add / list / update / count |
| `attachment` | list / by-entity / download / upload / upload-image / upload-image-base64 / get-image |
| `document` | download |
| `user` | info / workspaces |

## 使用示例

```bash
# 查询需求列表
tapd-cli story list workspaceid=12345678 limit=10

# 创建缺陷
tapd-cli bug add workspaceid=12345678 title="登录崩溃" severity=serious current_owner=user1

# 获取需求关联的测试用例
tapd-cli story get-tcase workspaceid=12345678 story-id=1112345678001000001

# 获取需求变更历史
tapd-cli story changes workspaceid=12345678 story-id=1112345678001000001

# 执行测试用例
tapd-cli tcase execute workspaceid=12345678 test-plan-id=456 tcase-id=789 result-status=pass last-executor=user1

# 从 xmind 导入测试用例
tapd-cli tcase import-xmind workspaceid=12345678 file=./test.xmind creator=user1
```

## 参数格式

- 所有参数使用 `key=value` 格式
- `workspaceid` 可省略（自动读取 `TAPD_WORKSPACE_IDS` 第一个值）
- 支持 `-` 和 `_` 两种分隔符：`story-id` 等价于 `story_id`

## 查看帮助

```bash
tapd-cli --help              # 所有实体
tapd-cli story --help        # 某实体子命令
tapd-cli story add --help    # 子命令详细参数
```

## 开发

如需修改源码后重新构建：

```bash
cd ~/.codebuddy/skills/tapd-cli
npm install
npm run build:bundle
# 产出：skills/tapd-cli/scripts/tapd-cli.cjs
```

## 仓库地址

https://cnb.cool/tapd.cn/skills/tapd-cli
