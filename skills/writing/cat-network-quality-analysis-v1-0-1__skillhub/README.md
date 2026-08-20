# cat-network-quality-analysis 

腾讯云云拨测（CAT）网络质量分析 Skill，基于腾讯云 ProcessAIEventsStream API 实现拨测任务网络质量分析，支持错误分析、整体分析、性能分析、抓包分析、多任务对比五种场景，结果以 Markdown 输出。

> 💡 **提示**：如果您是腾讯云内部用户，请使用**内网 API 端点** `cat.ai.internal.tencentcloudapi.com`，否则无法访问服务。

## 基本信息

| 项目 | 内容 |
|------|------|
| **名称** | cat-network-quality-analysis |
| **版本** | 1.3.0 |
| **作者** | 云拨测团队 |
| **依赖** | Python 3.10+（标准库实现 TC3 签名，零第三方依赖） |

## 适用场景

腾讯云云拨测任务网络质量分析：

- 多维度性能分析：全面呈现被拨测服务的性能指标
- 异常与错误分布定位：精准识别异常类型及错误分布规律
- 网络问题自动定界：通过横向对比有效区分运营商链路异常与服务端自身问题
- 抓包智能诊断：深度解析报文数据以精准定位问题根因
- 多任务对比：对比多个拨测任务的关键指标，快速定位任务间差异

## 功能特性

- 支持从整体性能、错误分析、抓包诊断等多维度呈现网络质量状况
- 支持网络质量分析报告自动生成与导出

## 快速开始

### 1. 安装依赖

脚本使用 Python 标准库实现 TC3-HMAC-SHA256 签名，**无需安装任何第三方包**，直接运行即可。

### 2. 配置（两级配置支持）

本 Skill 支持**两级配置**，按以下优先级加载：

```
环境变量  >  .env 文件
```

#### 配置参数列表

| 配置项 | 环境变量 | 必填 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| SecretId | `CAT_SECRET_ID` | ✅ 是 | — | 腾讯云 API 访问密钥 ID |
| SecretKey | `CAT_SECRET_KEY` | ✅ 是 | — | 腾讯云 API 访问密钥 KEY |
| Token | `CAT_TOKEN` | 否 | — | 临时凭证 Token（可选） |
| Endpoint | `CAT_ENDPOINT` | 否 | `cat.ai.tencentcloudapi.com` | API 端点地址（内部用户应使用内网端点） |

> 💡 **降级兼容**: 如果未设置 `CAT_xxx` 变量，脚本会自动降级使用 `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY` / `TENCENTCLOUD_TOKEN` / `TENCENTCLOUD_ENDPOINT`。建议优先使用 `CAT_xxx` 系列变量。

#### 如何获取 Secret ID 和 Secret Key

如果你还没有腾讯云 API 密钥（SecretId / SecretKey），请通过以下地址申请：

👉 **[申请 CAT API 访问权限](https://console.cloud.tencent.com/cloudapp/run/yunti/apply-auth)**

申请完成后，选择以下任意一种方式配置。

#### 方式一：使用 .env 文件（推荐）

在 `scripts/` 目录下创建或编辑 `.env` 文件：

```bash
# scripts/.env
CAT_SECRET_ID=your-secret-id
CAT_SECRET_KEY=your-secret-key
CAT_TOKEN=your-token           # 可选，使用临时凭证时提供
CAT_ENDPOINT=cat.ai.internal.tencentcloudapi.com  # 内部默认
```

> 🔒 `.env` 文件已加入 `.gitignore`，不会被提交到版本库。**切勿**将密钥硬编码在代码中。

#### 方式二：使用环境变量

```bash
export CAT_SECRET_ID='your-secret-id'
export CAT_SECRET_KEY='your-secret-key'
export CAT_TOKEN='your-token'           # 可选
export CAT_ENDPOINT='cat.ai.internal.tencentcloudapi.com'  # 可选，自定义 API 端点
```

> 💡 **提示**：两种配置方式可混合使用，环境变量优先级高于 `.env` 文件。

### 3. tcproxycli 代理模式（可选）

若已安装 `tcproxycli` 并设置了 `TCPROXYCLI_PROXY_ENDPOINT` + `TCPROXYCLI_SESSION_KEY` 环境变量，脚本会自动切换为代理模式，**无需本地云密钥**即可调用 CAT API。

```bash
# 代理模式环境变量（二选一即可，代理模式优先级高于 SDK/TC3 签名模式）
export TCPROXYCLI_PROXY_ENDPOINT="https://your-proxy-endpoint"
export TCPROXYCLI_SESSION_KEY="your-session-key"
```

> 未设置上述变量时，脚本默认走 TC3-HMAC-SHA256 签名模式（需配置 `CAT_SECRET_ID` / `CAT_SECRET_KEY`）。

### 4. 使用方式

#### 方式一：直接调用 Python 脚本

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text "进行错误分析" \
  --task-id "task-xxxxxxxx" \
  --start-time 1773734439444 \
  --end-time 1773745239444 \
  --output task-xxxxxxxx/task-xxxxxxxx_error_report_20260319.md
```

#### 方式二：通过 Skill 调用

在 CodeBuddy IDE 中，直接描述你的分析需求，例如：

```
分析最近3小时 task-xxxxxxxx 的拨测错误情况
```

## 输入参数

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `--query-text` | ✅ 是 | string | 发送给 CAT AI Console 的分析查询（按 `query_text_templates.md` 选模板；多任务对比为 `<structured_json>` 格式） |
| `--analyze-action` | 否 | string | 分析类型：`Console` / `PcapAnalysis` / `MultiTaskCompare`，缺省按 query-text 自动推断 |
| `--task-id` | ⚠️ 除多任务对比外 | string | 拨测任务 ID，格式如 `task-xxxxxxxx`（缺失必须先问用户；多任务对比场景省略） |
| `--start-time` | ✅ 是 | int | 分析起始时间（毫秒级时间戳，13 位） |
| `--end-time` | ✅ 是 | int | 分析结束时间（毫秒级时间戳，13 位） |
| `--session-id` | 否 | string | 多轮对话会话 ID（仅抓包跟进型必填） |
| `--output` / `-o` | 否 | string | 输出 Markdown 文件路径，默认 `{task_id}_{report_type}_{timestamp}.md`（report_type 由 query_text 推断） |
| `--suppress-pcap-candidates` | 否 | flag | 显式抑制抓包候选列表追加（抓包分析场景建议显式带上） |

## 输出行为

脚本全程静默执行，**流式写入 Markdown 文件**的同时，最终只输出**一行 JSON** 到 stdout：

```json
// 成功
{"code": 0, "report": "# 报告正文...", "md_path": "/abs/path/report.md", "session_id": "xxx", "json_file": "...", "pcap_candidates": [...], "incomplete": false}

// 失败
{"code": 1, "error": "错误信息"}
```

| 字段 | 成功时 | 失败时 | 说明 |
|------|--------|--------|------|
| `code` | `0` | `1` | 结果码 |
| `report` | ✅ | ❌ | 报告正文（已从第一个一级标题截取） |
| `md_path` | ✅ | ❌ | 归档 `.md` 文件路径 |
| `session_id` | ✅ 可能为空 | ❌ | 会话 ID（抓包跟进时需要） |
| `json_file` | ✅ 可能为空 | ❌ | 抓包候选 structured_json 清单文件路径 |
| `pcap_candidates` | ✅ 可能为空 | ❌ | 抓包候选列表，每项含 `task_id`/`probe_time`/`structured_json` 等，agent 取 `structured_json` 用于 `--query-text`，取 `task_id`/`probe_time` 用于三件套 |
| `incomplete` | ✅ | ❌ | `true` 表示 SSE 流未正常收到 `agent.done`，报告可能不完整 |
| `error` | ❌ | ✅ | 错误信息 |

> 当 `incomplete` 为 `true` 时，报告内容可能不全，建议缩小时间范围后重试。

## 使用示例

### 示例 1：错误分析

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text "进行错误分析" \
  --task-id "task-xxxxxxxx" \
  --start-time 1773734439444 \
  --end-time 1773745239444 \
  --output task-xxxxxxxx/task-xxxxxxxx_error_report_20260319_143025.md
```

### 示例 2：整体分析

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text "进行整体分析" \
  --task-id "task-xxxxxxxx" \
  --start-time 1773658839444 \
  --end-time 1773745239444 \
  --output task-xxxxxxxx/overall_report.md
```

### 示例 3：性能分析

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text "进行性能分析" \
  --task-id "task-xxxxxxxx" \
  --start-time 1773658839444 \
  --end-time 1773745239444 \
  --output task-xxxxxxxx/performance_report.md
```

### 示例 4：抓包分析（直达抓包）

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text "进行抓包分析" \
  --task-id "task-xxxxxxxx" \
  --start-time 1773658839444 \
  --end-time 1773745239444 \
  --suppress-pcap-candidates \
  --output task-xxxxxxxx/pcap_report.md
```

### 示例 5：抓包分析（抓包跟进，使用首次分析返回的 SessionID）

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text '<structured_json>{"task_id":"task-xxxxxxxx","probe_time":1773905195000,"code":"12929"}</structured_json>' \
  --task-id "task-xxxxxxxx" \
  --start-time 1773905195000 \
  --end-time 1773905195000 \
  --session-id "17f57xxxxxxxxxxxxxxxx5b224055354" \
  --suppress-pcap-candidates \
  --output task-xxxxxxxx/task-xxxxxxxx_pcap_report_20260319_120000.md
```

### 示例 6：多任务对比

对比多个任务时，`--query-text` 构造为 `<structured_json>`，**不传** `--task-id`：

```bash
python3 scripts/cat_network_quality_analysis.py \
  --query-text '<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>' \
  --start-time 1773658839444 \
  --end-time 1773745239444 \
  --output task-aaaabbbb/task-aaaabbbb_multitask_compare_report_20260319_143025.md
```

- `main_task_id` 为主任务（对比基准），`compare_task_ids` 为对比任务列表
- 仅 1 个 task ID 时默认它为主任务，追问要对比哪些任务；无 task ID 时追问主任务和对比任务
- **数量上限**：最多 **1 个主任务 + 5 个对比任务**，超出需告知用户重新选择
- **任务类型需一致**：主任务与对比任务的拨测任务类型必须相同，**类型不一致无法进行对比**
- `--start-time` / `--end-time` **必传**：用户指定时间范围时按指定范围，**未指定时默认最近 3 小时**（`end=当前ms`，`start=end-10800000`）
- 脚本自动推断 `AnalyzeAction=MultiTaskCompare`，跳过 TaskID 参数

## 目录结构

```
cat-network-quality-analysis/
├── SKILL.md              # Skill 定义文件（Claude Agent 运行时加载）
├── manifest.yaml         # Skill 清单
├── requirements.txt      # Python 依赖清单
├── references/           # Skill 子文档（按需查阅，不随主 prompt 加载）
│   ├── README.md
│   ├── cli_schema.md             # CLI 参数取值约束
│   ├── query_text_templates.md   # --query-text 模板与反模式
│   ├── sse_events.md             # SSE 事件语义
│   ├── error_handling.md         # 错误处理指南
│   └── branch_pcap.md            # 抓包分支完整规范
└── scripts/
    ├── cat_network_quality_analysis.py   # 主脚本
    └── .env              # 密钥配置（不纳入版本管理）
```

## 版本管理

遵循语义化版本（Semantic Versioning），格式为 `MAJOR.MINOR.PATCH`。

- **v1.3.0** (2026-08-06)
  - 新增**多任务对比**分析类型：AnalyzeAction 为 `MultiTaskCompare`，`--query-text` 使用 `<structured_json>`（`main_task_id` + `compare_task_ids`），`--task-id` 省略
  - 新增 `--analyze-action` 参数，缺省按 query-text 自动推断（多任务对比 → `MultiTaskCompare`；抓包跟进 → `PcapAnalysis`；其余 → `Console`）
  - 修复抓包跟进型 AnalyzeAction：之前固定为 `Console`，现自动推断为 `PcapAnalysis`
  - `--task-id` 改为除多任务对比外必传；缺省输出路径在多任务对比时取 `main_task_id` 作前缀
- **v1.2.0** (2026-07-23)
  - API 调用改为 TC3-HMAC-SHA256 手动签名，移除 tencentcloud-sdk-python 第三方依赖
  - 结果 JSON 新增 `incomplete` 字段，标识 SSE 流未正常收到 `agent.done` 时报告可能不完整
  - `--output` 缺省路径按 `query_text` 动态推断 report_type（原固定为 `error_report`）
  - tcproxycli 调用失败时收集 stderr 末尾几行拼进 error 信息
  - 修复 `_stream_cat_analysis` 返回值数量不一致导致调用方解包崩溃
  - 统一所有文档的三件套必传约束、structured_json 规范、错误分类矩阵
- **v1.1.1** (2026-07-21)
  - 精简 query-text 模板为统一格式
  - query-text 禁止包含时间描述和任务 ID
  - 抓包两入口均要求三件套必传
- **v1.1.0** (2026-07-16)
  - 新增性能分析场景，从整体分析中独立为 performance_report
  - 分析接口新增 CallerScene 参数
- **v1.0.0** (2026-07-07)
  - 初始版本，对齐 CSIG Skill 管理与发布规范

## 维护团队

- **Owner**: 云拨测团队

## 相关文档

- [腾讯云 CAT 官方文档](https://cloud.tencent.com/document/product/280)
- 内部设计文档：见 `references/` 目录各 `.md` 文件
