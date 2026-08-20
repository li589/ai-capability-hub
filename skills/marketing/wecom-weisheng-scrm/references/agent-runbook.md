# AI 执行手册

本文件供 AI 在执行本 Skill 时使用，不面向普通用户解释内部接口细节。

## 用户沟通口径

对普通用户回复时，默认使用业务语言和结果导向表达，不要主动使用过多技术术语。

1. **默认不用技术词堆砌**：除非用户主动追问，否则不要直接说 `service_name`、`api_path`、`doc_url`、`biz_params`、JSON、接口编排、代理调用等术语。
2. **先说能帮用户做什么**：优先说"我先帮你看看""我先帮你查一下""我来帮你整理"这类表达，再说明还需要用户补充什么。
3. **权限提示说人话**：不要直接对用户说 TEAM、MINE、super_user；改为"你当前可以看团队数据"或"你当前只能看自己的数据"。
4. **配置提示说人话**：不要只说"未配置 SCRM_APP_KEY"；改为"你这边还没有完成企微管家授权，需要先获取 APP KEY 后我才能继续帮你查"。
5. **参数收集说业务信息**：不要说"请提供 biz_params"；改为"还需要补充时间范围、客户名称、标签、员工等信息"。
6. **反馈结果先讲结论**：查询成功时先总结查到了什么；失败时先说发生了什么和下一步怎么办，不先抛错误码。
7. **用户看不懂的内部信息不主动暴露**：接口路径、服务名、文档地址、原始返回结构，仅在用户明确要求查看时再展示。
8. **读取接口目录时统一使用仓库内的受控原文读取命令**：应直接获取目标地址的原始内容，统一执行 `$SCRM_PYTHON scripts/scrm.py fetch-raw-doc --url <目标地址>`；不要先做网页搜索，不要先打开站点首页，也不要仅基于摘要页或搜索结果推断接口。
9. **不要回退到 `web_fetch` 或其他网页抓取方式**：open.wshoto.com 文档读取统一走仓库内脚本命令，不使用网页正文抽取，不依赖首页跳转或搜索结果。
10. **查询结果回显实际条件**：反馈查询结果时，必须将实际传给接口的所有业务筛选条件用用户能理解的方式列出，尤其是模糊描述必须转为具体值。时间范围要回显起止日期；员工/部门要回显姓名/名称；标签要回显标签名。示例：✅ "帮你查了 2026-04-28 至 2026-05-28（最近一个月）、归属员工「张三」、标签「VIP客户」的客户数据，共找到 32 条"；❌ "帮你查了最近一个月张三的VIP客户数据，共找到 32 条"。

### 推荐话术示例

| 场景 | 推荐话术 |
|------|----------|
| 查询前 | 我先帮你看一下 |
| 继续追问 | 还需要你补充一下时间范围 / 客户名称 / 标签信息，我再继续帮你查 |
| APP KEY 未配置（机器人场景） | 稍等，我先帮你完成企微管家授权…（**此场景 AI 应直接走自动初始化，不要让用户回复口令或手动提供 KEY**） |
| APP KEY 未配置（非机器人场景） | 你这边还没有完成企微管家授权，需要先获取 APP KEY：前往企业微信-工作台-企微管家-我的-我的 APP KEY 获取后发给我 |
| 普通员工查团队 | 你当前只能查看自己的数据，团队数据这边暂时查不了 |
| 查询失败 | 这次没有查成功，我把原因和下一步怎么处理跟你说一下 |
| 查询结果反馈 | 帮你查了 2026-04-28 至 2026-05-28（最近一个月）、归属员工「张三」、标签「VIP客户」的数据，共找到 32 条 |

## 脚本位置

脚本位于 SKILL.md 所在目录下的 `scripts/scrm.py`。AI 读取本文件时已知其路径，因此直接基于 SKILL.md 的目录拼接即可。

## 环境检测

触发 Skill 后，AI 应先检查当前是否具备脚本执行能力，以便运行仓库内命令读取原始文档并完成后续流程。

若用户当前所在模式不具备脚本执行能力，应直接提示用户切换到具备命令执行能力的模式后再继续；不要在明知当前模式无法执行命令时继续后续接口流程。

- **如果具备** → 正常继续后续调用流程。
- **如果不具备** → 引导用户切换到可执行脚本的模式或补齐命令执行能力，完成前不要继续后续流程。

处理原则：

- 缺少脚本执行能力时，先解决环境问题，再继续接口目录读取和后续 API 流程。
- 若已确认问题来自当前模式的执行能力限制，优先明确提示用户切换到具备所需能力的模式，不要只笼统提示"稍后再试"。
- 不要在缺少原文读取能力的情况下，直接把接口目录读取降级成普通网页搜索或首页浏览。
- 如果用户尚未完成重启，不要假装后续命令已经执行成功。

## 调用流程

AI 按以下编排流程执行：

1. **执行环境检测** → 先确认当前是否具备脚本执行能力；若不具备，则按"环境检测"章节优先引导用户切换到可用模式或补齐必要能力，完成前不要继续后续流程
   - 若已知用户当前模式无法执行命令，先明确提示其切换到具备所需能力的模式
2. **执行 check-env** → 检查运行环境（Python ≥3.9、SCRM_APP_KEY）；`check-env` 内部会自动尝试从 shell profile 或 Windows 注册表中恢复已持久化的 APP_KEY
   - 成功后，**从返回结果的 `python_command` 字段获取当前平台对应的 Python 命令**（macOS/Linux 为 `python3`，Windows 为 `python`），并执行 `export SCRM_PYTHON='<返回值>'`，后续所有命令统一使用 `$SCRM_PYTHON` 替代 `python3`
   - 若返回中包含 `export_hint` → 说明 APP_KEY 是从持久化配置中恢复的，**立即执行返回的 `export_hint` 命令**（如 `export SCRM_APP_KEY='xxx'`）使当前 shell 会话生效，然后继续
   - 成功且无 `export_hint` → APP_KEY 已在环境变量中，直接继续
   - 失败（`config_error`）→ **先判断能否拿到 sender_id，再分流**：
     - **机器人场景（默认优先）**：只要能从对话上下文取到 OpenClaw 注入的 `sender_id`（或 `chat_id` 去掉 `wecom:` 前缀）→ **直接走"机器人场景自动初始化"流程**（见下方专节），用 `setup-context` 自动获取并持久化 APP_KEY，**不要询问用户、不要让用户回复口令或手动提供 KEY**；**若自动初始化失败，按专节"自动初始化失败的兜底处理"回退到引导用户手动配置 APP KEY，不要卡在报错上**
     - **非机器人场景**：仅当确实拿不到 `sender_id` / `chat_id`（普通 CLI / IDE）时，才引导用户获取 APP KEY 并执行 `set-app-key`，成功后执行 `export SCRM_APP_KEY='<值>'`，然后继续
   - 若用户主动要求更换或更新 APP KEY（即使当前已配置），同样执行 `set-app-key` 用新值覆盖、export 后再继续
3. **执行 check-identity** → 获取用户身份（超管/分管/员工）
4. **阅读远程接口目录（强制步骤，不得跳过）** → 必须先读取 [CLAW_SUMMARY.md](https://open.wshoto.com/doc/pages/claw/CLAW_SUMMARY.md) 的原始内容，再根据用户意图匹配目标接口；每次会话首次触发 Skill 时必须执行此步骤，不得凭已有认知直接跳到 list-apis。执行时统一使用仓库内命令 `$SCRM_PYTHON scripts/scrm.py fetch-raw-doc --url <url>`
5. **执行 list-apis** → 用接口名称关键词匹配调用规则（service_name、api_path、doc_url、method）
6. **阅读接口文档（doc_url）** → 阅读该文档获取完整参数定义，强制步骤，不得跳过
7. **通过对话收集 biz_params** → 基于 doc_url 文档中的参数说明收集必要参数，不得仅凭 description 推断
8. **执行 call-api** → 以 `--doc-url` 为唯一绑定参数，脚本自动校验已读缓存、补齐元数据（service_name、uri、method）、执行参数强校验后通过通用代理调用

### 接口目录与文档读取要求

- 读取接口目录时，目标是拿到原始响应内容，而不是做网页正文抽取。
- 统一执行仓库内命令 `$SCRM_PYTHON scripts/scrm.py fetch-raw-doc --url https://open.wshoto.com/doc/pages/claw/CLAW_SUMMARY.md`。
- 该命令内置超时和响应大小限制，比 `web_fetch` 更稳定。
- 读取 doc_url 对应在线文档时，也统一执行 `$SCRM_PYTHON scripts/scrm.py fetch-raw-doc --url <doc_url>`。
- 不要退化为首页浏览、搜索摘要或人工猜测。

> **⚠️ 文档内容截断处理：** 工具展示 stdout 时可能截断长文本，但数据本身未丢失。**必须通过管道解析完整 content**，不要直接读 stdout，否则会遗漏参数（如跟进记录接口的 `menu`、`searchField/searchValue` 曾因此被忽略）。
>
> ```bash
> $SCRM_PYTHON scripts/scrm.py fetch-raw-doc --url <url> | $SCRM_PYTHON -c "import sys, json; data = json.load(sys.stdin); print(data['data']['content'])"
> ```

### 接口匹配规则

1. 阅读远程接口目录后，根据用户意图匹配接口名称和使用说明
2. 匹配到唯一接口时直接使用，无需询问用户
3. 匹配到多个候选接口时，列出候选项让用户选择
4. 无法匹配时，告知用户当前无匹配接口

### 聚合接口说明

聚合接口的调用方式与普通接口完全一致。当 call-api 执行时间较长时（最长可能需要约 2 分钟），这是正常的异步处理过程，请耐心等待结果。

### 接口间数据依赖

doc_url 文档中的「业务参数数据来源说明」章节描述了每个参数的值从哪里获取。AI 组装 `biz_params` 时，**必须先识别依赖关系，按正确顺序调用前置接口获取参数值**，不能跳过或猜测。

**参数来源识别：**

| 来源描述关键词 | AI 行为 |
|----------------|---------|
| 「前端XX选择器」「前端输入框」 | 通过对话向用户收集 |
| 「XX接口返回数据中的 `field` 字段」 | **必须先调用前置接口获取**，再用返回值填充 |
| 「预设枚举值」 | 根据用户意图从固定选项中匹配 |
| 「用户选择/用户输入」 | 通过对话收集，可能需要先列出选项 |

**处理原则：**
1. 每次调用接口前，先阅读 doc_url 的「业务参数数据来源说明」，确认是否有参数依赖其他接口
2. 对于来源为其他接口的字段（如 tagId、userId、deptId），绝不能凭用户输入的名称自行构造，必须通过前置接口查询获取真实值
3. 前置接口返回多条匹配记录时，列出选项让用户确认
4. 同一会话内已获取的数据可复用，无需重复调用

**典型场景 — 按标签名查客户（❌ 错误做法：直接猜测或构造 tagId 去查询）：**

用户说"查一下有多少客户打了高意向客户标签"，正确做法：
1. `list-apis --keyword "客户列表"` → 找到「客户列表分页查询」
2. 阅读 doc_url → 发现 `tagIds` 参数依赖「获取客户标签列表」接口
3. `list-apis --keyword "标签"` → 找到「获取客户标签列表」，用 `keyValue="高意向客户"` 搜索
4. 从返回结果中匹配 `tagName`，提取对应 `tagId`（多个同名标签时列出让用户选择）
5. 将 `tagId` 填入 `tagIds` 参数，调用客户列表接口

## 命令参考

所有命令统一以如下格式执行，参数通过对话收集，不依赖 stdin 交互：

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" <command> [--param value ...]
```

> **首次调用某个命令前，必须先执行 `<command> --help` 确认参数名称和格式，不得凭猜测传参。**
> **所有参数必须使用 `--param-name` 连字符格式，禁止使用下划线格式。**

### check-env — 环境检查

触发 Skill 时**立即**执行，失败则终止。检查项：Python ≥3.9、`SCRM_APP_KEY` 是否已配置。当 `SCRM_APP_KEY` 环境变量为空时，`check-env` 会自动尝试从 shell profile（Unix/macOS）或注册表（Windows）中读取之前通过 `set-app-key` 持久化的值。如果恢复成功，返回结果中会包含 `export_hint` 字段。

```bash
$SCRM_PYTHON "$SCRM_SCRIPT" check-env
```

**成功（APP_KEY 已在环境变量中）：**

```json
{"success":true,"data":{"python_command":"python3","checks":{"python_version":{"ok":true,"detail":"3.13.3"},"app_key":{"ok":true,"detail":"已配置"}}}}
```

**成功（APP_KEY 从持久化配置中恢复）：**

```json
{"success":true,"data":{"checks":{"app_key":{"ok":true,"detail":"从持久化配置中恢复（profile）"}},"app_key_restored":{"source":"profile","profile":"/Users/xxx/.zshrc","app_key":"xxx"},"export_hint":"export SCRM_APP_KEY='xxx'"}}
```

AI 处理逻辑：
- 成功后，**从 `python_command` 字段获取 Python 命令**并执行 `export SCRM_PYTHON='<返回值>'`，后续所有命令统一使用 `$SCRM_PYTHON`
- 成功且包含 `export_hint` → **立即执行返回的 `export_hint` 命令**使当前 shell 会话生效，然后继续
- 成功且无 `export_hint` → 直接继续
- 失败（`config_error`）→ 引导用户执行 `set-app-key`

**失败：**

```json
{"success":false,"error":"config_error","details":{"checks":{"app_key":{"ok":false,"detail":"未配置 SCRM_APP_KEY"}}}}
```

### set-app-key — 设置 APP_KEY

`SCRM_APP_KEY` 未配置时，**先按场景分流，不要无条件先问用户**：

- **机器人场景优先（默认）**：只要 AI 能从对话上下文拿到 `sender_id`（或 `chat_id` 去前缀），就**直接走"机器人场景自动初始化"流程**（`setup-context`，详见下方专节）自动申请并持久化 APP KEY，**无需询问用户、无需让用户回复口令或手动提供 KEY**；完成后重新 `check-env` 即可继续。
- **仅当无法判定为机器人场景**（拿不到 `sender_id` / `chat_id`，如普通 CLI / IDE）时，才引导用户手动获取：前往企微管家移动端「我的 → 我的 APP KEY」获取后发给 AI，AI 执行 `set-app-key` 写入。

> 判断顺序：先看能否拿到 `sender_id` → 能则自动、不能才手动。不要一上来就问"你有没有 APP KEY"。

路径①（用户手动提供 APP KEY）时执行：

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" set-app-key "<用户提供的APP_KEY>"
```

成功后：
1. 立即执行 `export SCRM_APP_KEY='<用户提供的APP_KEY>'`（Unix/macOS）使变量在当前 shell 会话中立即生效；Windows 平台跳过此步骤
2. 将返回结果中的 `note` 告知用户一次
3. 直接继续原始请求，不再追问用户是否已重启终端

> ⚠️ **必须执行 `export` 步骤**：`set-app-key` 写入 shell profile 后，当前会话不会自动加载新变量，不执行 `export` 则后续命令（如 `check-env`、`check-identity`）在当前会话内仍读不到 `SCRM_APP_KEY`，导致每次新会话都重复追问用户。

### check-identity — 获取用户身份

无额外参数，自动使用缓存的 user_id。

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" check-identity
```

返回示例：

```json
{"success":true,"action":"check-identity","data":{"user_id":"xxx","user_name":"张三","super_user":1,"role_description":"超级管理员"}}
```

### list-apis — 接口仓库查询

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" list-apis --keyword "关键词1,关键词2"
```

| 参数 | 说明 |
|------|------|
| `--keyword` | (必填) 多个关键词逗号分隔，模糊匹配 api_name |

返回字段：

| 字段 | 说明 | 用途 |
|------|------|------|
| `api_name` | 接口名称 | 确认匹配结果 |
| `description` | 接口简要描述 | 辅助理解用途，**不含完整参数定义** |
| `api_path` | 接口 URI | 由脚本自动使用，AI 无需手动传入 |
| `service_name` | 下游微服务名 | 由脚本自动使用，AI 无需手动传入 |
| `doc_url` | 接口文档地址 | **必读**，传入 `call-api --doc-url`，也是 `fetch-raw-doc` 的目标地址 |
| `method` | HTTP 请求方式：POST 或 GET | 由脚本自动使用，AI 无需手动传入 |

### call-api — 通用代理调用（文档驱动强门禁）

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" call-api \
  --doc-url "https://open.wshoto.com/doc/pages/claw/xxx.md" \
  --biz-params '{"currentIndex":1,"pageSize":10}'
```

| 参数 | 说明 |
|------|------|
| `--doc-url` | (必填) 接口文档 URL，必须先通过 `fetch-raw-doc` 读取过该文档（已读缓存有效期 2 小时） |
| `--biz-params` | (必填) 调用参数 JSON，统一承载路径参数、Query参数和业务参数，参数名和类型以 doc_url 文档中的 FIELD_INPUT_SPEC 为准 |

脚本执行流程：
1. 校验 `doc_url` 对应的已读缓存是否存在且未过期 → 失败则返回 `doc_read_required`
2. 根据 `doc_url` 从接口元数据自动补齐 `service_name`、`uri`、method → 失败则返回 `doc_validation_required`
3. 基于已读缓存中的 `field_input_spec` 将输入参数拆分为 `path_params`、`query_params`、`fields(biz_params)` 三段
4. 对 `path_params`、`query_params`、`fields(biz_params)` 三段分别执行强校验；随后再用 `path_params` 替换 URI 占位符并检查是否仍有缺失 → 失败则返回 `doc_validation_required` 或 `path_param_missing`
5. 校验通过后通过通用代理转发调用

> **重要变更：** `call-api` 不再接受 `--service-name`、`--uri`、`--method` 参数，这些信息由脚本根据 `doc_url` 自动补齐。

### Python 官方封装

如果 AI 在运行时需要用 Python 调用 SCRM Skill，优先使用 `scripts/scrm_sdk.py`，不要直接手写 `subprocess + json.loads(stdout)` 去消费 `scripts/scrm.py` 的原始输出。

边界说明：

1. 直接执行 Skill 命令时，继续使用 `scripts/scrm.py`（或 `$SCRM_PYTHON "$SCRM_SCRIPT"`）
2. 只有在 Python 代码里需要消费命令返回结果时，才切换到 `scripts/scrm_sdk.py`
3. `scripts/scrm_sdk.py` 不是 CLI 替代品，而是 Python 侧的安全调用封装

推荐示例：

```python
from scripts.scrm_sdk import SCRMCommandError, call_api, fetch_raw_doc
doc_url = "https://open.wshoto.com/doc/pages/claw/xxx.md"
try:
    fetch_raw_doc(doc_url)
    data = call_api(doc_url, {"currentIndex": 1, "pageSize": 10})
    response = data["response"]
except SCRMCommandError as exc:  # 失败直接按异常处理，禁止继续做业务判断
    raise
```

这个封装层会：

1. 内部统一调用 `scripts/scrm.py`
2. 自动解析顶层 JSON
3. 只要退出码非 0 或 `success=false`，直接抛 `SCRMCommandError`
4. 成功时只返回 `data`

### 结果消费护栏

AI 在运行时如果必须读取 `scripts/scrm.py` 的 JSON 输出，优先走 `scripts/scrm_sdk.py`。只有在官方封装无法满足时，才允许自己解析原始 JSON；此时必须遵守以下硬规则：

1. 先检查顶层 `success` 字段，只有 `success=true` 才允许读取 `data.response` 或继续做业务判断
2. 只要 `success=false`，必须立即停止解析业务字段，并原样处理 `error`、`message`、`details`
3. 禁止把失败响应兜底成空对象、空数组、`0`、`false`、`null`
4. 禁止在失败响应上输出任何业务事实判断，例如“没有该员工”“没有数据”“总数为0”
5. 查询类结论必须区分三种状态：查询成功且命中、查询成功且未命中、查询失败暂时无法判断

错误示例：

```python
payload = json.load(sys.stdin)
data = payload.get("data", {})
response = data.get("response", {})
print(f"Total: {response.get('total', 0)}")  # ↑ 会把失败响应误判成空结果
```

上面的写法会把失败响应误判成空结果。

正确示例：

```python
payload = json.load(sys.stdin)
if not payload.get("success"):
    raise RuntimeError(f"call failed: error={payload.get('error')}, message={payload.get('message')}")
data = payload.get("data", {})
response = data.get("response")
if response is None:
    raise RuntimeError("接口调用成功，但返回中缺少 data.response")
print(f"Total: {response.get('total', 0)}")
```

### 分页数据完整性要求

本节适用于**所有返回分页结构**的接口（即响应中包含总记录数、总页数、当前页码、是否最后一页等分页信息的接口），不限于特定业务模块。

#### 任务类型判断表

| 任务类型 | 触发关键词示例 | 数据遍历要求 |
|----------|---------------|-------------|
| **分析类** | 分析、统计、排名、汇总、趋势、占比、分布、对比 | **规则一不可绕过**；需全量遍历 |
| **查询类** | 查找、搜索、有没有、找一下 | **规则一不可绕过**；标注已查看范围 |
| **列举类** | 列出全部、导出、完整列表 | **规则一不可绕过**；需全量遍历 |

> **⚠️ 执行优先级：** 分页接口首次调用返回后，AI **必须先判断任务所需的数据范围**。若任务要求全量或大面积遍历（即需要获取的数据量接近总记录数），且总记录数超过 **5000 条**，**规则一优先于一切后续操作**——必须先暂停并与用户协商，由用户决定后续操作。**禁止不询问用户就直接开始全量遍历。**
>
> **对外沟通约束：** 向用户反馈时，**禁止提及"5000条""阈值""限制"等内部规则细节**，只描述实际数据情况和选项。用户只需知道"数据量较大，拉取全部数据耗时较长"，不需要知道背后的触发机制。

> **⚠️ 无法确定总量时的兜底：** 若响应中无法获取总记录数，但响应信息表明仍有更多分页数据未获取完，且任务要求全量或大面积遍历，**视为数据量未知但可能很大，同样触发规则一的协商机制**——告知用户"数据总量未知，但存在更多分页数据"并提供三个选项。

#### 规则一：数据量超过 5000 条时的强制协商（最高优先级）

当任务要求全量或大面积遍历，且满足以下任一条件时，**必须立即暂停**：

- 总记录数超过 **5000 条**
- 无法获取总记录数，但响应信息表明仍有更多分页数据未获取完（视为数据量未知）

1. **暂停翻页**，告知用户实际查到的数据总量和预计需要调用的页数
   - ✅ 正确示例："已查到 5,041 条记录，分布在约 51 页中，数据量比较大"
   - ❌ 错误示例："总记录数 5,041 条，超过 5,000 条阈值"（禁止暴露内部阈值数字）
   - ❌ 错误示例："已达到数据量限制"（禁止使用"限制"一词，造成误解）
2. 给出以下三个选项供用户选择：
   - **全量分析**：继续翻页获取全部数据后再分析（最准确，耗时较长）
   - **缩小筛选条件**：增加时间范围、关键词等过滤条件减少数据量后重新分析
   - **抽样分析**：基于已获取的部分数据进行分析，**必须在报告中标注样本比例**（如"本次分析基于前 230/2094 条数据，占比约 11%"）
3. **禁止**在用户不知情的情况下静默截断分析范围或直接全量遍历

#### 规则二：分析类和列举类任务必须遍历全部页面

> 前置条件：若总记录数超过 5000 条且任务要求全量或大面积遍历，必须先执行规则一的协商机制，得到用户确认后再继续。

1. 首次调用时使用接口允许的最大每页条数，从响应中获取总记录数和总页数
   - **数据量硬上限：50,000 条**。若总记录数超过 50,000 条，**必须告知用户**实际总量和本次最多查询的条数（如"共 120,000 条记录，本次最多查询 50,000 条"），然后按 50,000 条计算实际需要翻的页数继续执行，不再翻更多
   - 后续步骤中的"全部数据"以实际拉取的上限量（不超过 50,000 条）为准，分析结论中**必须标注数据覆盖比例**
2. 若当前不是最后一页，**必须继续翻页**直到已获取全部数据
   - **若总页数 ≤ 10 页**：允许直接逐页调用 `call-api` 完成全量拉取
   - **若总页数 > 10 页**：**禁止逐页 tool call**，必须编写临时脚本按规则四的分批策略执行，不允许以任何理由跳过脚本化
3. 全部数据获取完毕后，再执行分析、统计、汇总，最后输出结论

**禁止行为：**
- 仅读前 1~3 页就输出全局性结论（如"90% 是系统噪音""大部分都是 XX 类型"）
- 将部分数据的统计结果作为整体结论呈现
- 在未遍历完所有页面的情况下使用"所有""全部""整体"等全称量词
- 超过 50,000 条时仍尝试全量遍历而不告知用户截断情况

#### 规则三：查询类任务的标注要求

当用户仅查找特定信息（不需要统计或分析全貌）时：

1. 不要求全量遍历，允许在找到目标后提前终止
2. 但在输出结论时，**必须标注已查看的数据量和总量比例**，例如："已查看前 3 页（共 50 页，约 300/5000 条），在已查看范围内未找到匹配结果"
3. **禁止**在只查看了部分数据时使用"没有找到""不存在""查不到"等全称否定结论

#### 规则四：大批量分页拉取的防超时策略

> **对外沟通约束：** 向用户反馈拉取进度或异常时，禁止使用"超时""断点续传""重跑""进程被终止""持久化""增量落盘"等技术术语，用通俗说法替代。示例：✅ "已经拉了 56/164 页，我继续帮你拉剩下的，之前拉好的不会丢"；❌ "拉取到 56/164 页被超时中断了，脚本有断点续传，重跑会自动从第57页继续"

当需要遍历全部页面时（规则二），若预估总耗时较长，单次命令调用存在超时风险——超时后进程被终止，未持久化的数据全部丢失。AI 应按以下工作流执行分批拉取。

**判定条件：** 规则二已明确：总页数 ≤ 10 页允许逐页 tool call；总页数 > 10 页必须走本规则的分批策略。此判定不可绕过，不需要 AI 自行评估耗时。

**分批执行工作流：**

1. **首次调用** → 使用接口允许的最大每页条数调用第一页，从响应中获取总页数和单页耗时
2. **评估分批** → 根据上述判定条件决定是否分批；若需分批，计算每个批次可容纳的页数（单批次预估耗时建议不超过命令超时上限的 50%）
3. **编写临时脚本** → 脚本接受页码范围参数指定拉取范围，并包含以下三项必需机制：
   - **增量落盘**：每成功拉取一页后，立即将该页结果写入输出目录下按页码编号的独立文件，不要在内存中累积
   - **断点续传**：脚本启动时先扫描输出目录中已有的结果文件，跳过已完成的页，从下一个未完成的页继续
   - **进度输出**：每完成一页后输出当前进度（已完成/总数），便于中断后评估和继续
   - **临时脚本不要存放在 Skill 的 `scripts/` 目录中**，应放在项目的 `.cache/` 或其他临时目录下，避免与 Skill 正式脚本（如 `scrm.py`、`scrm_sdk.py`）混淆，也避免被 git 追踪
4. **逐批执行** → 每个批次一次独立的命令调用，并为该调用设置合理的超时时间；所有批次共享同一个输出目录，通过已有结果文件实现无缝衔接
5. **汇总结果** → 所有批次完成后，读取输出目录中的全部文件进行合并和分析

**批次失败处理：** 若某个批次超时或失败，检查输出目录确认哪些页已成功保存，然后继续拉取剩余页（脚本会自动跳过已完成的页）。单个批次最多重试 2 次，仍失败则用通俗语言告知用户当前进度并询问是否继续（如"已经拉了 56/164 页，还要继续拉吗"）。

**禁止**：
- 拉完所有页后再统一写入文件（进程被杀后无任何产出）
- 在内存中累积全部页面结果而不持久化到磁盘
- 重跑时从第一页重新开始而不检查已有的中间结果文件

### inspect-api-doc — 检查文档缓存（调试/排障）

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" inspect-api-doc --url <doc_url>
```

| 参数 | 说明 |
|------|------|
| `--url` | (必填) 目标文档 URL |

用于检查指定文档的已读缓存状态和 field_input_spec 内容。属于调试/排障命令，不属于 AI 正常主流程。

## 机器人场景自动初始化（setup-context / get-bot-id / debug-context）

本节描述企微智能机器人对话场景下，`SCRM_APP_KEY` 缺失时的**自动初始化能力**（原 `wecom-weisheng-robot` skill 已合并入本 skill）。

### 触发条件

必须**同时**满足才走自动初始化，否则回退到手动 `set-app-key`：

1. 当前处于企微智能机器人对话场景——判据：**能从对话上下文取到 OpenClaw 注入的 `sender_id`（或 `chat_id` 去掉 `wecom:` 前缀）**。只要满足此判据即视为机器人场景，应主动触发，**无需等待用户回复任何口令**（用户主动要求初始化时同样触发）
2. **且** `check-env` 返回 `config_error` / `app_key.ok=false`（`SCRM_APP_KEY` 未配置）

> 普通 CLI / IDE 场景（无 `sender_id`）不要触发本流程，应引导用户手动 `set-app-key`。
> `SCRM_APP_KEY` 已配置时无需重复初始化，直接继续业务。

### 两个关键 ID 的来源

- **sender_id（当前员工 ID）**：来自 OpenClaw 框架自动注入的消息上下文 `sender_id` 字段（或 `chat_id` 去掉 `wecom:` 前缀）。作为 `--operator-userid` 传入。
- **bot_id（机器人 ID）**：来自 `openclaw.json` 的 `channels.wecom.botId`，可用 `get-bot-id` 命令读取。作为 `--bot-id` 传入。

### 执行流程

```bash
# 步骤 1：读取 bot_id（若上下文已提供可跳过）
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" get-bot-id

# 步骤 2：一键初始化，获取并持久化 SCRM_APP_KEY
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" setup-context \
  --operator-userid "<sender_id>" \
  --bot-id "<bot_id>"

# 步骤 3：执行返回的 export_hint 使当前会话生效（Unix/macOS；Windows 已写注册表）
export SCRM_APP_KEY='<返回的 app_key>'

# 步骤 4：重新 check-env → app_key.ok=true，回到主流程继续 check-identity
```

`setup-context` 成功后会**自动持久化** APP_KEY（Windows 写注册表，Unix/macOS 写 shell profile，与 `set-app-key` 共用同一存储位置），并在返回结果中包含 `persist` 字段与 `export_hint`。

### 自动初始化失败的兜底处理

在机器人场景下，`get-bot-id` 或 `setup-context` 执行失败时（返回 `success=false`，常见 `error` 为 `config_error` / `validation_error` / `scrm_error`），**不要止步于一句报错，必须回退到"引导用户手动配置 APP KEY"**：

| 失败情形 | 典型原因 | AI 处理 |
|----------|----------|---------|
| `get-bot-id` 失败（`config_error`） | openclaw.json 缺 `channels.wecom.botId` | 用业务语言说明暂时拿不到机器人身份，**引导用户手动获取 APP KEY 发给你并执行 `set-app-key`** |
| `setup-context` 失败（`scrm_error`，员工未绑定/未授权） | 该员工在 SCRM 侧尚未绑定或无权限 | 告知用户自动授权没成功，**引导其前往企业微信-工作台-企微管家-我的-我的 APP KEY 手动获取后发给你**，再执行 `set-app-key` |
| `setup-context` 失败（网络/平台临时错误） | 平台暂时不可用 | 先告知稍后重试；用户希望立即继续时，**同样引导手动获取 APP KEY 并 `set-app-key`** 作为兜底 |

兜底执行：拿到用户提供的 APP KEY 后，按 `set-app-key` 章节执行写入 + `export`，成功后重新 `check-env` 继续业务。

> **关键原则**：机器人场景的自动初始化是"优先尝试"，**不是唯一路径**。一旦自动失败，必须无缝转入手动引导，确保用户最终能完成授权，不能让用户卡在自动失败的报错上。对外沟通用业务语言（如"自动授权没成功，麻烦你按下面方式提供一下授权信息"），不暴露 `setup-context`、`scrm_error` 等内部术语。

### get-bot-id — 读取机器人 ID

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" get-bot-id
```

从 `openclaw.json` 读取 `channels.wecom.botId`（优先 `openclaw config get`，失败回退直接解析 `~/.openclaw/openclaw.json`）。

### debug-context — 调试 ID 获取

```bash
SCRM_NON_INTERACTIVE=1 $SCRM_PYTHON "$SCRM_SCRIPT" debug-context \
  --operator-userid "<sender_id>" [--bot-id "<bot_id>"]
```

仅回显 `bot_id` 和 `sender_id`，不调用任何 SCRM 接口，用于验证两个关键 ID 是否能正常获取。

### 接口规格

**POST** `{base_url}/openapi/claw/robot/personal/app-key`

请求体：`{"open_user_id":"<sender_id>","source_botid":"<bot_id>","sp_corp_id":"<服务商ID>"}`
响应体（成功）：`{"code":0,"data":{"app_key":"<SCRM_APP_KEY>"}}`

相关环境变量：

| 变量 | 说明 |
|------|------|
| `SCRM_BASE_URL` | 平台地址，默认 `https://open.wshoto.com` |
| `SCRM_SKIP_SSL_VERIFY` | 设为 `1`/`true`/`yes` 跳过 SSL 校验（内网测试用） |
| `ROBOT_SCRM_PROVIDER_ID` | 服务商主体 ID（sp_corp_id），默认内置 |



### FIELD_INPUT_SPEC 说明

`FIELD_INPUT_SPEC` 是嵌入在接口文档中的结构化参数定义，位于 `## 请求地址` 之后、`## 通用代理层参数` 之前。`fetch-raw-doc` 读取文档时会自动提取并写入已读缓存，供 `call-api` 参数校验使用。

关键点：
1. `migrate-api-doc` skill 是 `FIELD_INPUT_SPEC` 的标准生成入口
2. 业务接口的路径参数、Query参数、`biz_params` 发生变更时，接口文档必须同步更新 `FIELD_INPUT_SPEC`
3. 当文档中缺少 `FIELD_INPUT_SPEC` 时，`call-api` 跳过字段校验并返回 `warnings`（含 `field_input_spec_missing`），调用仍可正常执行

### 参数收集标注含义

doc_url 文档中的参数标注，AI 必须严格按对应行为执行：

| 标注 | AI 行为 |
|------|---------|
| **必须对话收集** | 执行前通过对话明确获取，不得自行推断 |
| **展示选项让用户选择** | 列出所有选项含默认推荐，等用户选择 |
| **展示默认值后确认** | 告知默认值，询问是否修改 |
| 默认：`xxx` | 展示默认值，用户无需主动回复 |
| 可选 | 用户未提及时跳过 |

## 身份与权限

不同业务接口用于区分团队/个人数据范围的参数名不统一，AI 必须通过阅读 doc_url 文档确认具体字段名。

| check-identity 角色 | 数据范围 | 参数取值 |
|---------------------|----------|----------|
| 超管(super_user=1) / 分管(super_user=2) | 团队数据 | 团队对应的枚举值（如 TEAM） |
| 普通员工(super_user=0或3) | 仅个人数据 | 个人对应的枚举值（如 MINE） |

AI 应根据 check-identity 结果，在 biz_params 中自动填入对应值。当用户未明确指定视角范围时：超管/分管默认使用团队视角，普通员工默认使用个人视角。

### 普通员工视角限制

即使用户主动要求查询团队数据，普通员工也必须使用个人视角，不得使用团队视角。应告知用户"您的身份是普通员工，只能查看个人数据，无法查看团队数据"。

### 员工操作限制

当 check-identity 返回 `super_user` 为 `0` 或 `3` 时，当前用户为普通员工，AI 必须严格执行以下限制：

#### 限制一：禁止指定其他员工

普通员工只能操作自己的数据，不能将接口参数中的员工相关字段指定为其他员工。

强制检查流程：

1. 查看 check-identity 返回的 `user_id` 和 `user_name`
2. 检查 biz_params 中是否包含员工名称、员工ID相关参数（如 `userIds`、`addUserIds`、`staffId` 等）
3. 如果包含，此类参数必须且只能是 check-identity 返回的 `user_id` 或 `user_name`
4. 如果用户要求使用其他员工，必须拒绝执行并告知"您的身份是普通员工，只能操作自己的数据（{user_name}），无法指定其他员工"

示例：用户说"创建活码，使用员工=芳芳"，但 check-identity 返回 user_name=吴浩 → 芳芳≠吴浩，拒绝执行。

#### 限制二：禁止调用员工/部门搜索接口

普通员工无权搜索企业组织架构。员工&部门分类下的搜索接口，以及任何用于获取员工列表、部门列表、组织架构树的接口，普通员工都不得调用。

## 错误处理

| error 类型 | AI 处理方式 |
|------------|-------------|
| `config_error` | 用普通用户能理解的话说明还缺什么配置，并引导下一步，不直接抛技术细节 |
| `validation_error` | 说明还缺哪些业务信息或填写有误，引导用户补充后重试 |
| `doc_read_required` | 未先读取接口文档或已读缓存过期（2 小时），执行 `fetch-raw-doc --url <doc_url>` 后再重试 |
| `doc_validation_required` | 请求参数未通过文档校验（不支持字段、必填缺失、类型不匹配、const 不匹配），重新阅读 doc_url 文档后调整参数再调用，**不要自动重试** |
| `path_param_missing` | 缺少路径参数，必须重新阅读文档并补齐路径参数；这不等于“查无数据” |
| `auth_error` | access_token 不可用，需要刷新 token 或检查环境；这不等于“查无数据” |
| `scrm_error` | 用业务语言转述失败原因，并询问用户是否要调整条件后再试 |
| `json_error` | 内部自行修正，不把 JSON 解析细节暴露给用户 |
| `unexpected_error` | 告知用户这次没处理成功，建议稍后重试或联系管理员，不直接输出技术报错 |

仅 `scrm_error` 且用户主动要求时才重试；其他类型错误优先修复根因。`doc_validation_required`、`path_param_missing`、`auth_error` 都不能被解释为“空结果”或“无此数据”。

### 写操作重试限制

写操作接口执行失败或超时后，禁止自动重试。写操作失败可能是服务端已成功执行但响应超时，自动重试会导致重复创建数据。

具体规则：

1. `call-api` 的输出中包含 `write_operation` 字段，`true` 表示写操作，`false` 表示读操作
2. 写操作失败或超时时，AI 必须告知用户失败结果，由用户决定是否重试，AI 不得自行重新执行 `call-api`
3. 读操作不受此限制，AI 可以在合理范围内重试

## 行为规范

以下规则优先级最高，始终遵守：

1. 触发 Skill 时立即执行 `check-env`，在收集任何参数前完成；失败则告知用户并终止，不得继续
2. 若 `SCRM_APP_KEY` 未配置，**先判断场景再分流，不要无条件先问用户**：（1）**机器人场景优先**——只要能从上下文拿到 `sender_id`（或 `chat_id` 去前缀），就直接走「机器人场景自动初始化」流程（`setup-context`）自动完成配置，无需询问用户、无需让用户回复口令或手动提供 KEY，完成后重新 `check-env`；（2）仅当确实判定为非机器人场景（拿不到 `sender_id`/`chat_id`）时，才引导用户前往企业微信-工作台-企微管家-我的-我的 APP KEY 手动获取后发给 AI 执行 `set-app-key`
3. 写操作确认，读操作直接执行：查询类接口直接执行；写操作接口必须等待用户最终确认后再执行
4. 参数收集通过对话完成，不依赖脚本 stdin 交互；执行时统一携带 `SCRM_NON_INTERACTIVE=1`
5. 用户身份由 `SCRM_APP_KEY` 静默获取，禁止通过命令行参数传入
6. 所有输出统一为 JSON，便于上层 Skill 编排解析
7. 首次调用某个命令前，必须先执行 `<command> --help` 确认参数名称和格式，不得凭猜测传参
8. 面向普通用户回复时，优先使用业务口径：先说能帮用户做什么、查到了什么、还缺什么信息，不主动输出底层接口与参数细节
9. 涉及接口目录的读取动作一律走受控原文直读：读取 [CLAW_SUMMARY.md](https://open.wshoto.com/doc/pages/claw/CLAW_SUMMARY.md) 时，统一使用 `$SCRM_PYTHON scripts/scrm.py fetch-raw-doc --url <url>`。若当前环境缺少该能力，先修复环境并提示用户切换模式或完成必要配置，再继续，不要直接降级为网页搜索、首页访问或 `web_fetch`
10. 分页数据完整性：所有分页接口首次调用后，若任务要求全量或大面积遍历且总记录数超过 5000 条，**必须先暂停并与用户协商，禁止直接全量遍历**（规则一，最高优先级）。详见「分页数据完整性要求」章节。**注意：对外反馈时不得暴露内部阈值数字，只描述实际数据量大小和选项。**
