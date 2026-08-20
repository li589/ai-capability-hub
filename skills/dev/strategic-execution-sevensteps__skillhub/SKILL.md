---
name: strategic-execution-sevensteps
description: 战略解码与落地。七步法：准备→洞察→定略→解码→分解→执行→复盘。触发：战略解码、战略落地、目标拆解、OGSM、年度计划、战略规划、KPI拆解、硬仗、战略会、目标管理、BSC、战略地图、OKR拆解、组织绩效、战略澄清、业务规划、资源聚焦、平衡计分卡。
---

> **版本**：v1.2.0 | 2026-07-25

# 战略解码与落地 · 付费版

将模糊战略方向转化为团队行动清单。整合 BLM、BSC、OGSM、秦杨勇五步法、吕守升 RIDER 五大方法论。

核心链路：`准备 → 洞察 → 定略 → 解码与资源 → 分解 → 执行 → 复盘（回流第一步）`

---

## 付费资源请求

> ⚠️ **付费前置检查**：仅在用户请求付费服务（见下方触发场景）时才执行。用以下命令检查 `weixinpay` 插件是否已安装：
> ```powershell
> openclaw plugin list 2>$null | Select-String -Pattern "weixinpay"
> ```
> - **有输出**：已安装，继续付费流程
> - **无输出**：向用户提示"当前 Agent 暂不支持微信支付付费能力，请联系 Agent 管理员安装 weixinpay 插件"，回退到免费咨询

当用户请求以下付费服务时，AI 通过 `exec` 工具执行 PowerShell 向商户服务端点发起 HTTP 请求：

**付费触发场景**：
- 生成战略规划报告（9大模块）
- 深度外部环境分析（政策+产业+竞品数据采集）
- 战略解码会完整引导（半日工作坊）
- 全套部门级 OGSM + 个人 PPC 合约

**请求方式**（AI 通过 exec 执行以下 PowerShell 脚本）：

```powershell
$merchantEndpoint = $env:STRATEGY_MERCHANT_ENDPOINT
if (-not $merchantEndpoint) {
    Write-Output "ERROR: STRATEGY_MERCHANT_ENDPOINT 未配置"
    exit 1
}
$body = @{
    query    = "<用户的原始请求原文>"
    skill_id = "strategic-execution-sevensteps"
    feature  = "<report_generation|strategy_decoding|ogsm分解|full_consultation>"
} | ConvertTo-Json -Compress
$response = try { Invoke-RestMethod -Uri "$merchantEndpoint/api/resource" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30 } catch { Write-Output "ERROR: 商户服务超时或不可达: $($_.Exception.Message)"; exit 1 }
$response | ConvertTo-Json -Depth 5
```

> `STRATEGY_MERCHANT_ENDPOINT` 由商户在 Agent 环境变量中配置（例：`https://merchant.example.com`）。若 `$env:STRATEGY_MERCHANT_ENDPOINT` 为空，提示用户"服务暂不可用，请确认 Agent 已配置 STRATEGY_MERCHANT_ENDPOINT 环境变量"。

---

## X402 支付流程

### 第一步：发起请求

AI 通过 `exec` 执行上述 PowerShell 脚本，将用户请求转发至商户服务端点。

### 第二步：处理 402 响应

若收到 **HTTP 402** 响应（脚本报错或返回 402 状态码），说明需要支付。`weixinpay` 插件将自动拦截并完成支付流程，**本 Skill 无需手动调用支付接口**。

402 响应中通过 Header 返回支付凭证：

| Header | 说明 |
|--------|------|
| `WeixinPay-Required` | 支付凭证码，插件用于完成微信支付 |
| `X-Out-Trade-No` | 商户订单号，履约时需要携带 |

### 第三步：支付成功后重试（⚠️ 必须执行）

支付完成后，**必须**携带支付凭证重新请求以获取实际内容。重试规则：

- **Body 不变**：与首次请求完全一致
- **通过 Header 携带支付凭证**，AI 执行以下 PowerShell 脚本：

```powershell
$merchantEndpoint = $env:STRATEGY_MERCHANT_ENDPOINT
$headers = @{
    "Content-Type"       = "application/json"
    "WeixinPay-Required" = "<payment_code>"       # ← 402 响应 Header 原样带回
    "X-Out-Trade-No"     = "<out_trade_no>"        # ← 402 响应 Header 原样带回
}
$body = @{
    query    = "<用户的原始请求原文>"
    skill_id = "strategic-execution-sevensteps"
    feature  = "<report_generation|strategy_decoding|ogsm分解|full_consultation>"
} | ConvertTo-Json -Compress
$response = try { Invoke-RestMethod -Uri "$merchantEndpoint/api/resource" -Method Post -Headers $headers -Body $body -ContentType "application/json" -TimeoutSec 30 } catch { Write-Output "ERROR: 商户服务超时或不可达: $($_.Exception.Message)"; exit 1 }
$response | ConvertTo-Json -Depth 5
```

> ⚠️ 重试时 body 内容不可修改，支付信息**仅通过 Header 传递**。

### 第四步：处理特殊响应

| 响应 code | 含义 | 处理方式 |
|-----------|------|---------|
| `SUCCESS` | 支付成功，正常返回付费内容 | 向用户展示结果 |
| `NOT_PAID` | 支付未完成 | 告知用户"支付尚未完成，请稍后重试" |
| `REFUNDED` | 商户无法提供服务，已退款 | 告知用户"抱歉，该服务暂时无法提供，已自动退款至原支付账户"，终止流程 |
| `FULFILL_AND_REFUND_FAILED` | 服务异常且退款失败 | 告知用户"服务异常且退款失败，建议联系客服处理"，终止流程 |
| `ALREADY_FULFILLED` | 订单已履约，直接返回缓存结果 | 正常向用户展示结果 |

---

## 使用协议（免费部分）

### 首次接触用户：必须诊断

收到任何战略相关请求时，**先做诊断，再给方案**。通过 2-3 个问题确定：

> **快速通道**：若用户主动说"我付钱出报告""生成正式战略报告""给我全套 OGSM"等已明确付费意图的话，可直接跳过 Q1-Q3 诊断，进入「付费资源请求」→「X402 支付流程」。

1. **行业 + 阶段**：什么行业？什么轮次/规模/人数？
2. **核心痛点**：最头疼的一件事情是什么？
3. **期望产出**：今天聊完希望带走什么？

诊断完成后，根据判断自动定位到对应步骤。

### 步骤定位规则

| 用户说的 | 定位 | 读取文件 |
|---------|------|---------|
| "团队不一致""组织没准备好" | 第一步·组织准备 | seven-steps.md → "第一步" |
| "方向看不清""外部什么情况" | 第二步·洞察诊断 | seven-steps.md → "第二步" |
| "3-5年规划""选A还是选B""情境推演" | 第三步·战略制定 | seven-steps.md → "第三步" |
| "一句话怎么落地""年度硬仗""预算不够" | 第四步·解码与资源配置 | seven-steps.md → "第四步" |
| "各部门各干各的""目标拆到个人" | 第五步·目标分解 | seven-steps.md → "第五步" |
| "执行没动静""建跟踪机制""月度看板" | 第六步·执行落地 | seven-steps.md → "第六步" |
| "复盘""今年打得怎么样" | 第七步·复盘总结 | seven-steps.md → "第七步" |
| "有什么坑""常见错误" | 六盏红灯 | principles.md |
| "XX行业怎么做"、"SaaS行业"、"制造业"、"跨境电商"、"金融科技" | 行业案例库 | industry-cases.md |
| AI、大模型、新消费、数字化、医疗、出海、新能源汽车、跨境电商 | 行业案例库（自动匹配 8 大行业中与用户行业特征最接近的案例，按五段结构输出） | industry-cases.md → fallback 推理 |
| "生成战略报告""战略规划报告" | 报告生成（付费） | seven-steps.md → "附录" |

### 输出规范

- **每次只聚焦当前步骤**，不强推全套方法论
- 产出必须包含：**谁、做什么、哪天交、怎么算完成**
- 表格、清单、红黄绿灯优先，减少大段论述
- 不确定时把选项摆出来让用户选，不给唯一路径
- 报告/文档类产出默认输出为 **Markdown 文件**（写入 workspace），用户要求时也可输出为腾讯文档

### 工作原则

详见 [principles.md](references/principles.md)。核心六条：

1. **先诊断再开方** — 上来就问行业、规模、痛点
2. **搭框架不做决定** — 选项摆出来，按钮在用户手里
3. **每次只聚焦一步** — 不灌方法论
4. **可分可合灵活切入** — 缺哪补哪
5. **小步快跑优于全面铺开** — 30min 到 1 个月五种起点
6. **80分被执行 > 100分束之高阁** — 以人为本

### 不做什么

- 不替用户写董事会决议、不做财务审计/薪酬核算
- 不编造公司数据，不碰具体人力资源操作
- 不建议"全面铺开"——正确姿势是小步快跑

## 快速起效：五种时间起点

| 时间 | 产出 | 付费 |
|------|------|------|
| 30分钟 | 战略落地成熟度评分 + TOP3短板 + 建议切入步骤 | 免费 |
| 2小时 | 硬仗初筛清单 + 重要性-可行性矩阵排序 | 免费 |
| 半天 | 完整战略解码会引导 + 年度硬仗清单初稿 | **付费** |
| 1周 | 全套部门级OGSM + 个人PPC合约模板 | **付费** |
| 1个月 | 月度跟踪机制跑起来（PMO模板+红黄绿看板+标准议程） | **付费** |

> **免费/付费边界说明**：诊断、方法论咨询、步骤引导始终免费。仅当用户明确要求产出**正式结构化文档**（战略报告/全套OGSM表格/工作坊引导脚本/PMO模板包）时才进入付费流程。例如"如何开好战略解码会"是免费咨询，"引导我做一场完整的战略解码会并出会议纪要"是付费服务。

## 参考文件

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| [seven-steps.md](references/seven-steps.md) | 七步法完整详解（含模板/框架/标准议程/报告生成） | 匹配到具体步骤时，**先 exec grep 搜索目标步骤标题定位行号，再用 `read offset/limit` 精读对应段落**，避免全量加载 |
| [principles.md](references/principles.md) | 六盏红灯防坑指南 + 导入建议 | 用户问"有什么坑"时 |
| [industry-cases.md](references/industry-cases.md) | 8大行业案例库（含fallback推理流程） | 用户说出行业时 |

> **大文件读取策略**：seven-steps.md 约 24KB，不一次性全读。匹配到具体步骤后，执行 `Select-String -LiteralPath "<技能目录>\references\seven-steps.md" -Pattern "^## 第"` 获取所有步骤标题及行号，再根据用户问题匹配对应步骤，用 `read offset=<行号> limit=<行数>` 只读取目标步骤段落（步骤标题格式为 `## 第一步：…` ~ `## 第七步：…`，中文数字，非阿拉伯数字）。附录（报告生成规范）同理，仅在用户要求生成报告时读取。
