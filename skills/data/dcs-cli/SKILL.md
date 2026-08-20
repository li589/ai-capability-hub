---
name: dcs-cli
display_name: DCS Cloud生命科学研究智能平台
display_name_en: DCS Cloud Intelligent Platform for Life‑Science Research
description: "Operate the full DCS Cloud platform via the local dcs CLI: login and config, projects/regions, data, tables, online containers, WDL workflows, offline tasks, billing, and more. Use when the user mentions DCS, the cloud platform, Files, containers, workflows, or task submission."
description_zh: "通过本机 dcs CLI 操作 华大生信分析云平台 DCS Cloud 全平台能力：登录配置、项目片区、数据、表格、在线容器、WDL 流程、离线任务、计费等。用户提到 华大、DCS、云平台、Files、容器、workflow、任务投递时使用。"
description_en: "Operate the full DCS Cloud platform via the local dcs CLI: login and config, projects/regions, data, tables, online containers, WDL workflows, offline tasks, billing, and more. Use when the user mentions DCS, the cloud platform, Files, containers, workflows, or task submission."
category: bioinformatics
version: 1.1.1
author: DCS Genpilot
---

# DCS CLI

用本机 **`dcs` CLI** 操作 DCS Cloud。所有操作通过 shell 执行 `dcs` 命令完成。

- 本文是 **全模块总览**（每个命令组都有说明）
- terminal / workflow / data 的详细流程见 [references/](references/) 下分文档
- 二进制发布页：[GitHub Releases](https://github.com/BGIResearch/dcs_cli/releases)（始终用 **latest**，不要写死版本号）

## 安装 / 下载 CLI（Agent 必做）

**安装目录固定为 `~/.dcs`**（Linux/macOS：`$HOME/.dcs`；Windows：`%USERPROFILE%\.dcs`）。下载前必须先检查该目录是否已有可执行文件；已存在则**不要重复下载**，直接使用。

### 1. 先检查是否已下载

| 平台 | 期望路径 |
|------|----------|
| Linux (amd64) | `~/.dcs/dcs` |
| Windows | `~/.dcs/dcs.exe` |

```bash
# Linux / macOS
test -x "$HOME/.dcs/dcs" && "$HOME/.dcs/dcs" --help

# 若 PATH 中已有 dcs，也可：command -v dcs && dcs --help
```

```powershell
# Windows PowerShell
$dcs = Join-Path $env:USERPROFILE ".dcs\dcs.exe"
Test-Path $dcs
if (Test-Path $dcs) { & $dcs --help }
```

- 文件存在且 `--help` 可用 → **跳过下载**，后续命令优先用该路径（或已在 PATH 中的 `dcs`）。
- 不存在或无法执行 → 进入下一步，从 GitHub **latest** 拉取（**禁止**在 URL / 文档示例里写死 `vX.Y.Z`）。

### 2. 下载最新版到 `~/.dcs`

发布资源始终走 [releases/latest](https://github.com/BGIResearch/dcs_cli/releases/latest) 的 `.../latest/download/<asset>`，由 GitHub 重定向到当前最新附件：

| 平台 | asset 名 | 落地文件 |
|------|----------|----------|
| Linux (amd64) | `dcs-linux-amd64` | `~/.dcs/dcs` |
| Windows | `dcs.exe` | `~/.dcs/dcs.exe` |

```bash
# Linux：仅当 ~/.dcs/dcs 不存在时执行
mkdir -p "$HOME/.dcs"
if [ ! -x "$HOME/.dcs/dcs" ]; then
  curl -fsSL -o "$HOME/.dcs/dcs" \
    "https://github.com/BGIResearch/dcs_cli/releases/latest/download/dcs-linux-amd64"
  chmod +x "$HOME/.dcs/dcs"
fi
export PATH="$HOME/.dcs:$PATH"
"$HOME/.dcs/dcs" --help
```

```powershell
# Windows：仅当 %USERPROFILE%\.dcs\dcs.exe 不存在时执行
$dir = Join-Path $env:USERPROFILE ".dcs"
$dcs = Join-Path $dir "dcs.exe"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
if (-not (Test-Path $dcs)) {
  Invoke-WebRequest -Uri "https://github.com/BGIResearch/dcs_cli/releases/latest/download/dcs.exe" `
    -OutFile $dcs
}
$env:Path = "$dir;$env:Path"
& $dcs --help
```

备选（与 latest release 同步的 main 分支二进制，同样**不要**带版本号）：

- Linux：`https://raw.githubusercontent.com/BGIResearch/dcs_cli/main/cli/linux/dcs-linux-amd64`
- Windows：`https://raw.githubusercontent.com/BGIResearch/dcs_cli/main/cli/win/dcs.exe`

**Agent 约定**：需要跑任何 `dcs` 业务命令前，先完成「检查 `~/.dcs` → 缺失则下 latest → 验证 `--help`」；会话内把 `~/.dcs` 加入 `PATH`，或始终用绝对路径调用。

## 全局前置

CLI 可用后，任何业务命令前必须先登录。`dcs auth login` 需要 **PAT（访问令牌）**，获取方式：

1. 打开 [DCS Cloud](https://www.dcs.cloud/) 注册 / 登录
2. 页面右上角点击 **个人资料** → **访问令牌**
3. 创建并生成令牌（仅展示一次，请妥善保存）
4. 用该令牌完成 CLI 登录（交互粘贴，或 `--token`）

```bash
dcs auth login                                 # 按提示粘贴 PAT；或 dcs auth login --token <PAT>
dcs project switch --id PXXXXXXXXXXX01   # 不要写 <P...> 尖括号
dcs project current --output json              # 确认未报 not logged in
```

登录成功后自动写入 `user_id`；`copilot_base_url` 随 `base_url` 推导，一般无需手设。`terminal` 需要**数值型** `user_id`；若报 `83011`，重新 `dcs auth login` 或 `dcs config set user_id <id>`。

---

## 命令组总览

| 命令组 | 用途 |
|--------|------|
| `auth` / `login` / `logout` | PAT 登录、登出 |
| `config` | 本地配置（base_url、client_app、语言等） |
| `region` | 片区列表、切换、当前片区 |
| `project` | 项目列表、切换、详情、创建 |
| `data` | Files 浏览、上传、下载 |
| `table` | 数据表查询 |
| `terminal` | 在线容器 open/exec/read/create/upload/download |
| `analysis` | 个性化分析离线任务（shell，非 workflow） |
| `workflow` | WDL 工作流列表、规划、投递 |
| `billing` | 计费组 |
| `history` | CLI 命令历史 |

全局 flag（任意命令可用）：见下方 [输出与入参格式](#输出与入参格式)

---

## 输出与入参格式

### 输出格式（可选，`--output`）

| 值 | 用途 |
|----|------|
| `table` | **默认**，人类可读表格 |
| `json` | **agent / 脚本推荐**，结构化 JSON（含 `exit_code`、`data`、`error`） |
| `ndjson` | 批量结果时每行一条 JSON |

```bash
dcs workflow ls --output json
dcs terminal open --output json
dcs project current --output json    # 默认 table，加 --output json 才出 JSON
```

不加 `--output` 时走 **table**，不是 JSON。

### 入参 JSON（可选，全局 `--json`）

部分命令支持用 JSON 传参（不必记全 flag）：

```bash
dcs workflow run --json '{"name":"Hello_Test", ...}'
dcs data upload --json @params.json    # @文件
# 或环境变量 DCS_JSON_PARAM
```

### 命令自省（agent 查参数）

```bash
dcs workflow plan --describe    # 参数说明
dcs workflow plan --schema      # JSON Schema
```

---

## auth — 登录 / 登出

| 命令 | 说明 |
|------|------|
| `dcs auth login` | PAT 登录（交互粘贴或 `--token`） |
| `dcs login` | 同上（顶层别名） |
| `dcs auth logout` / `dcs logout` | 登出，清除本地 token |

**获取 PAT**：登录 [https://www.dcs.cloud/](https://www.dcs.cloud/) → 右上角 **个人资料** → **访问令牌** → 创建生成令牌。

```bash
dcs auth login --token dcs_pat_xxxx --output json
```

**注意**：网页已登录 ≠ CLI 已登录；未登录时多数命令报 `83002` / `70102` / `41104`。

---

## config — 本地配置

| 命令 | 说明 |
|------|------|
| `dcs config init` | 初始化 `~/.dcs/config.yaml` |
| `dcs config show` | 查看当前配置 |
| `dcs config get <key>` | 读单个配置项 |
| `dcs config set <key> <value>` | 写配置项 |
| `dcs config language zh\|en` | 切换 CLI 语言 |

常用 key：`base_url`、`client_app`（如 `dcs-cloud-cli`）、`encrypt`

已有配置时 `config init` 失败属预期，需 `--force`；不必当 bug。

---

## region — 片区

| 命令 | 说明 |
|------|------|
| `dcs region ls` | 列出可用片区 |
| `dcs region switch <region>` | 切换当前片区 |
| `dcs region current` | 查看当前片区 |

---

## project — 项目

| 命令 | 说明 |
|------|------|
| `dcs project ls` | 列出有权限的项目 |
| `dcs project switch --id <code>` | 按 ID 切换（**不要带 `<>`**） |
| `dcs project switch --name <name>` | 按名称切换 |
| `dcs project current` | 当前项目 |
| `dcs project detail --code <code>` | 项目详情（余额等） |
| `dcs project create` | 创建个人项目 |
| `dcs project tags` / `omics` / `omics_tools` | 标签与组学元数据 |

**注意**：`terminal`、`workflow`、`data` 等依赖 `current_project`，切换项目后在线容器会话失效，需 `terminal close` 再 `open`。

---

## data — 数据管理

浏览、下载、上传。**详细说明** → [dcs-data-manager.md](references/dcs-data-manager.md)

| 命令 | 说明 |
|------|------|
| `dcs data ls` / `find` / `info` / `cd` / `pwd` / `rm` | 浏览与导航 |
| `dcs data download --type web --path <云路径> --target <本机目录>` | 下载到本机 |
| `dcs data upload --cluster-mode other --path <集群路径> --target /Files/...` | 集群文件上传到 Files |
| `dcs data copy` / `move` | 复制 / 移动 |

参数是 **`--path` / `--target`**，不是 `--source_path` / `--target_path`。

---

## table — 数据表

| 命令 | 说明 |
|------|------|
| `dcs table ls` | 列出数据表 |
| `dcs table find` | 按条件查找 |
| `dcs table info` | 查看表内容 |

---

## terminal — 在线容器

OpenSandbox 容器内 exec / 读写文件。**详细说明** → [dcs-cloud-terminal.md](references/dcs-cloud-terminal.md)

**默认镜像**（与离线 `analysis run` 统一，务必用 registry 路径传参）：

`stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0`

投递成功后任务详情里可见映射名如 `ubuntu:24.04-python3.12`，**以 registry 路径为准传参**，不要用展示名。

| 命令 | 说明 |
|------|------|
| `dcs terminal ls_resource` | 列容器规格 |
| `dcs terminal open [--resource_id <id>]` | 打开容器（默认即上述镜像环境） |
| `dcs terminal exec -c '<cmd>'` | 容器内执行 |
| `dcs terminal read/create/edit --path <容器绝对路径>` | 读写文件（read 仅文本） |
| `dcs terminal create -p <容器路径> [-c '<内容>']` | 创建/覆盖文件（`-c`/`--content` 写文本；省略则建空文件） |
| `dcs terminal upload -p <容器路径> -f <本机文件>` | 本机文件上传到容器 |
| `dcs terminal download -p <容器路径> -t <本机路径>` | 容器文件下载到本机（含二进制） |
| `dcs terminal close` | 关闭容器 |

路径用容器内绝对路径（如 `/work/{user_name}/...`），不是本机路径。大文件或二进制优先 `upload`/`download`，不要用 `read` 取二进制。

**推荐工作流**（保证在线调试与离线运行镜像一致）：

1. `dcs terminal open` → 在默认镜像环境中 `exec` 安装依赖、调试命令、准备脚本/数据（路径在 `/work/<username>/...`）
2. 调试通过后，用**同一默认镜像**投递离线任务：`dcs analysis run ... --image stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0`

需要装软件时，先在默认在线容器里装好并验证，再投离线，避免「终端里能跑、离线镜像里缺包」。

---

## analysis — 离线任务（个性化分析 shell，非 workflow）

`--image` **必填**。默认/推荐镜像：

`stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0`

不要用展示名（如 `Python 3 and R image`）、随意 tag 或纯数字 ID，易报 `imageId格式不正确` / `image_url不存在`。无 `-t s` flag，不要写。

`-l` **必须同时含 `vf` 与 `num_proc`**，且匹配当前片区机型列表（片区不同机型不同）。

```bash
dcs analysis run -i '<cmd>' -l 'vf=...,num_proc=...' \
  --image stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0 \
  -o /Files/Result/Notebook/<path>
```

实测：

- 片区 **BGI-Center（st）**：`-l vf=4g,num_proc=1` + 上述镜像 → 成功
- 片区 **DCS-North2（ve）**：无 1c 4g，需改用当地机型，如 `-l vf=8g,num_proc=4` + 同一镜像 → 成功

| 命令 | 说明 |
|------|------|
| `dcs analysis run -i '<cmd>' -l '<资源>' --image '<镜像>'` | 投递 shell 离线任务 |
| `dcs analysis ls` | 列任务 |
| `dcs analysis info <id>` / `log` / `start` / `cancel` / `rm` / `consume` | 查详情、日志、控制 |

`-l` 与 `--image` 必填；批处理可用 `-p <本机脚本文件>`（每行一条命令）。WDL 流程投递用 **`dcs workflow run`**，不要用 `analysis run`。

---

## workflow — WDL 工作流

列表、规划、查参、投递。**详细说明** → [dcs-wdl-manager.md](references/dcs-wdl-manager.md)

| 命令 | 说明 |
|------|------|
| `dcs workflow ls` | 列流程（`-p` 公共库） |
| `dcs workflow info -n <name>` | 流程详情 |
| `dcs workflow plan -n <name>` | 多步规划 |
| `dcs workflow check_parameter -n <name>` | 查参数规格 |
| `dcs workflow run -n <name>` | 投递 WDL 任务 |
| `dcs workflow tasks` / `task_info` / `task_log` / `start` / `cancel` / `rm` | 任务管理 |

标准流程：`workflow ls` → `plan` → `check_parameter` → `run`

简单流程可用。`echo_hello` 等需 `-e/--entity`（如 `-e 10010`）；不要只写会缺 Mem 的复杂示例当唯一用法。

---

## billing — 计费组

| 命令 | 说明 |
|------|------|
| `dcs billing ls` | 查看有权限的计费组 |

---

## history — 命令历史

| 命令 | 说明 |
|------|------|
| `dcs history ls` | 列历史记录 |
| `dcs history get <request_id>` | 查单条记录 |

---

## Agent 约定

- **安装**：先检查 `~/.dcs/dcs`（Windows：`%USERPROFILE%\.dcs\dcs.exe`）；缺失再从 GitHub `releases/latest/download/...` 下载，**禁止写死版本号**
- **输出**：自动化优先 `--output json`
- **查参数**：`dcs <cmd> --describe` 或 `--schema`
- **Windows CMD**：占位符 `<code>` 实际输入时**不要带尖括号**
- **路径**：容器内用 `/work/...`；Files 用 `/Files/...`；本机用 Windows 路径
- **镜像**：离线 `analysis run` 与在线 terminal **默认均为** `stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0`。推荐：`terminal open` 装软件/调试 → 同镜像 `analysis run` 离线投递
- **二进制文件**：不用 `terminal read` 取 PNG；Files 上已有文件用 `data download`

### 常见错误码

| 码 | 含义 | 处理 |
|----|------|------|
| 83002 / 70102 / 41104 | 未登录 | `dcs auth login` |
| 83003 | 未选项目 | `dcs project switch` |
| 83006 | 容器未开 | `dcs terminal open` |
| 83013 | 容器未就绪（Starting 等） | 等 3–5 秒至 Running 后重试，或 `dcs terminal open` |
| 83014 | 查询容器状态失败 | 检查网络/登录后重试 |
| 83007 | 容器内命令执行失败 | 确认容器已 Running、路径/命令正确 |
| 83011 | `user_id` 无效/非数值 | 重新 `dcs auth login` 或 `dcs config set user_id <id>` |
| 41102 | 无当前项目 | `dcs project switch` |

---

## 分模块详细文档（references）

- [在线容器 + 离线 analysis 细节](references/dcs-cloud-terminal.md)
- [Workflow 流程细节](references/dcs-wdl-manager.md)
- [数据管理细节](references/dcs-data-manager.md)

---

## 禁止

- 不编造子命令或参数名；不确定时用 `dcs <cmd> --help`
- 不用 `terminal read` 读二进制图片
- 不把本机路径当作容器内路径
- 不用 `analysis run -t s`（实际无此 flag）
- 不用已废弃的 `dcs task` / `dcs wdl`（最新 CLI 为 `dcs analysis` / `dcs workflow`）
- `--image` 不要用展示名、随意 tag 或纯数字 ID
