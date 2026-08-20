---
name: cloudnet-ai-diagnosis
display_name: "Cloudnet AI 终端智诊"
display_name_en: "Cloudnet AI Diagnostics"
description: Cloudnet AI Diagnostics针对无线场景下终端体验差、网卡、无法接入 WiFi 等问题进行排障的技能
description_zh: "Cloudnet AI Diagnostics针对无线场景下终端体验差、网卡、无法接入 WiFi 等问题进行排障的技能"
description_en: "Cloudnet AI Diagnostics is a troubleshooting capability designed for wireless scenarios, addressing issues such as poor terminal experience, network adapter problems, and inability to connect to WiFi."
version: 1.0.3
category: troubleshooting
author: Cloudnet Skills
visibility: "public"
---

# Cloudnet AI Diagnostics

针对无线场景下终端体验差、网卡、无法接入 WiFi 等问题进行排障。

## 触发条件

用户询问关于无线终端连接问题，例如：

- "XX 场所的 XX 终端上网很慢"
- "XX 场所的 XX 设备连不上 WiFi"
- "XX 场所的 XX 用户反馈网络卡"
- "XX 办公室的 XX 设备频繁掉线"
- "XX 门店的 WiFi 信号差"
- "XX 场所的 XX 终端认证失败"
- "XX 楼层的 XX 手机无法上网"
- "XX 园区的 XX 终端漫游异常"
- "XX 门店顾客反馈 WiFi 慢，MAC 地址是 XX-XX-XX-XX-XX-XX"

**不适用场景**（不应触发本 Skill）：

- 有线网络排障（如网线、交换机问题）
- 设备初始配置（如 AP 上线配置、AC 初始化）
- 网络拓扑图查询或网络规划

## 前置环境检查

### 安装 `mcporter` CLI 支持及 Skill

- 安装 mcporter：

```bash
npm install -g mcporter
```

- 然后通过 ClawHub 安装 `mcporter` Skill。

### 配置 MCP 连接参数

- `CLOUDNET_API_KEY`（必填）：需要用户提供 Cloudnet 管理平台的 API Key，可通过 Cloudnet 管理平台（网络管理 => 设置 => 开放平台）获取。
- `CLOUDNET_BASE_URL`（可选）：Cloudnet 管理平台地址，默认值：

```text
https://oasis.h3c.com
```

#### 配置环境变量

```bash
export CLOUDNET_API_KEY="<your_api_key>"
export CLOUDNET_BASE_URL="https://oasis.h3c.com"
```

#### 配置 MCP 服务

```bash
mcporter config add cloudnet-mcp \
${CLOUDNET_BASE_URL}/mcp-server/api/sse \
--header Authorization="Bearer ${CLOUDNET_API_KEY}"
```

#### 安全建议

1. **避免通过命令行明文传递 API Key。**

   优先使用 mcporter 支持的配置文件、凭据管理或环境变量引用机制，避免将实际 Token 直接作为命令行参数传递，降低凭据泄露风险。

2. **降低 Shell History 泄露风险。**

   如果当前版本必须执行上述命令，建议先执行：

   ```bash
   export HISTCONTROL=ignorespace
   ```

   并在包含敏感信息的命令前增加一个空格，以减少命令被写入 `.bash_history` 或 `.zsh_history` 的风险。

   **注意：** 此方法仅能降低 Shell History 泄露风险，无法避免命令执行期间进程参数被查看。

3. **妥善保管 API Key。**

   不要将 API Key 写入脚本、代码仓库、配置模板、文档或聊天记录。建议使用环境变量、系统凭据管理工具或企业密钥管理服务进行存储，并定期轮换、及时失效不再使用的 API Key。

4. **Windows 用户额外注意事项。**

   如果您使用 **PowerShell** 或 **CMD**，Shell History 的处理方式有所不同：

   **PowerShell 环境：**

   - PowerShell 默认会将命令历史保存到内存，可通过 `Get-History` 查看
   - 若使用 **PSReadLine** 模块（PowerShell 5.0+ 默认安装），命令历史会持久化到文件：
     ```powershell
     # 查看历史记录文件路径 (默认)
     (Get-PSReadLineOption).HistorySavePath
     # 通常位于: $env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
     ```
  
   **降低泄露风险的方法：**
  
   a) **临时禁用历史记录**（推荐在输入敏感命令前执行）：
      ```powershell
      Set-PSReadLineOption -HistorySaveStyle SaveNothing
      ```
      执行完敏感命令后可恢复：
      ```powershell
      Set-PSReadLineOption -HistorySaveStyle SaveIncrementally
      ```

   b) **使用环境变量方式设置凭据**，避免直接在命令行中明文传递：
      ```powershell
      $env:CLOUDNET_API_KEY = "<your_api_key>"
      $env:CLOUDNET_BASE_URL = "https://oasis.h3c.com"
      mcporter config add cloudnet-mcp "$($env:CLOUDNET_BASE_URL)/mcp-server/api/sse" --header "Authorization=Bearer $($env:CLOUDNET_API_KEY)"
      ```

   c) **清除已记录的敏感历史**：
      ```powershell
      # 手动删除历史记录文件中的敏感行，或直接清空
      Remove-Item (Get-PSReadLineOption).HistorySavePath -Force
      ```

   d) **使用 Windows 凭据管理器**（更安全的长期方案）：
      ```powershell
      # 存储凭据（需手动输入，不会出现在命令行）
      cmdkey /add CLOUDNET_API /user apikey /pass "<your_api_key>"
      # 后续通过脚本读取时不会明文暴露
      ```

   **CMD 环境：**
   - CMD 使用 `doskey` 管理命令历史，仅保存在当前会话内存中
   - 关闭 CMD 窗口后历史自动清除，但仍建议使用环境变量方式传参
   - 避免在批处理脚本（`.bat`/`.cmd`）中硬编码 API Key

   **注意：** 无论使用何种 Shell，环境变量仅在当前会话有效。对于长期使用的场景，建议将环境变量配置在系统环境变量中或使用密钥管理服务。

---

## 排障步骤

### 第零步：环境依赖检查

在开始排障前，先检查环境是否就绪：

1. **检查 mcporter 是否安装**：执行 `mcporter --version`，若未安装则提示用户执行 `npm install -g mcporter`。
2. **检查 API Key 是否配置**：确认 `CLOUDNET_API_KEY` 环境变量已设置，若未设置则提示用户参照"前置环境检查"进行配置。
3. **检查 MCP 服务是否可达**：确认 `cloudnet-mcp` 已通过 `mcporter config add` 配置。

如果以上任一条件未满足，向用户说明缺失项并给出配置指引，不继续后续步骤。

### 第一步：提取关键信息

从用户问题中提取以下信息：

| 信息       | 说明              | 示例                                    |
| -------- | --------------- | ------------------------------------- |
| **场所名**  | 必填，问题发生的场所      | "总部办公室"、"XX门店"                        |
| **终端信息** | 必填，MAC 地址或终端用户名 | MAC：`xxxx-xxxx-xxxx` 或 用户名：`zhangsan` |
| **故障时间** | 可选，用户未指定则默认当前时间 | `2026-03-24 10:00:00`                 |

**终端信息格式说明：**

- **MAC 地址**：支持 `XX-XX-XX-XX-XX-XX`（连字符）或 `XX:XX:XX:XX:XX:XX`（冒号）两种格式，系统会自动适配。
- **IP 地址**：如 `192.168.1.1`。
- **用户名**：如 `h3cuser1`、`zhangsan`。

**重要：**

如果场所名和终端信息未提取到，必须让用户补充完整后才能继续下一步。

**faultTime 约束：**

- 故障时间不能为未来时间（不能晚于当前服务器时间）。若用户指定的时间为未来时间，需提示用户使用当前或过去的时间。

### 第二步：查询场所 ID

调用 `cloudnet-mcp.getallshopsanddevofuser` 获取用户下所有场所，找到场所名对应的场所 ID，场所 ID 无需显示告诉用户。

```bash
mcporter call cloudnet-mcp.getallshopsanddevofuser
```

**异常处理：**

- **场所名匹配不到**：如果返回的场所列表中未找到用户提供的场所名，提示用户确认场所名是否正确，或列出相近的场所供用户选择。
- **多场所匹配**：如果场所名模糊匹配到多个场所，向用户列出候选项并请用户确认，例如："找到以下匹配的场所，请确认是哪一个：1. 北京朝阳店 2. 北京海淀店"。
- **MCP 服务调用失败**：如果调用超时或返回错误，提示用户检查 API Key 配置和网络连接，建议稍后重试。

### 第三步：执行终端诊断

根据提取的终端信息（MAC、用户名或 IP 地址），调用 `executeStaDiagnosis` 进行诊断。

**参数说明：**

- `clientInfo`：终端 MAC 地址（格式 `xxxx-xxxx-xxxx` 或 `xx:xx:xx:xx:xx:xx`）、终端 IP 地址（如 `192.168.1.1`）或终端用户名（如 `h3cuser1`）
- `shopId`：场所 ID（来自第二步），需要转换为字符串类型
- `faultTime`：故障时间，格式 `yyyy-MM-dd HH:mm:ss`，**不能为未来时间**（不能晚于当前服务器时间），用户未指定则使用当前时间
- `timezone`：用户时区，默认 `Asia/Shanghai`

#### MAC 地址示例

```bash
mcporter call cloudnet-mcp.executeStaDiagnosis \
clientInfo:"xxxx-xxxx-xxxx" \
shopId:"场所ID" \
faultTime:"2026-03-24 10:00:00" \
timezone:"Asia/Shanghai"
```

#### IP 地址示例

```bash
mcporter call cloudnet-mcp.executeStaDiagnosis \
clientInfo:"192.168.1.1" \
shopId:"场所ID" \
faultTime:"2026-03-24 10:00:00" \
timezone:"Asia/Shanghai"
```

#### 用户名示例

```bash
mcporter call cloudnet-mcp.executeStaDiagnosis \
clientInfo:"h3cuser1" \
shopId:"场所ID" \
faultTime:"2026-03-24 10:00:00" \
timezone:"Asia/Shanghai"
```

**异常处理：**

- **诊断时间为未来时间**：如果 API 返回"诊断时间为未来时间"错误，提示用户故障时间不能晚于当前时间，并自动使用当前时间重新执行诊断。
- **终端不存在**：如果 API 返回"Cloudnet 无此终端信息"错误，提示用户确认 MAC 地址/IP 地址/用户名是否正确，并检查终端当前是否在线。
- **MCP 服务调用失败**：如果调用超时或返回其他错误，提示用户检查网络连接和 API Key 配置，建议稍后重试。
- **诊断无数据**：如果诊断返回数据为空，提示用户该终端可能在故障时间段内无连接记录，建议用户确认故障时间或尝试其他终端标识（如用 IP 地址代替 MAC 地址）。

### 第四步：分析诊断结果

诊断返回后会包含：

- 终端连接概览数据（终端接入能力、认证方式、信号强度、丢包率、重传率等）
- 连接设备软件版本信息（AP、AC）
- 云平台操作日志
- 设备运行状态（AC、AP CPU、内存异常次数）
- 终端连接过程数据
- 终端运行状态分析（干扰、信号强度、流量、速率、丢包率、重传率等采样数据）
- AP 空口环境分析（干扰、底噪、信噪比、流量、信道利用率、接入用户数等采样数据）
- 根因推理结论（定位终端问题可能的根因）
- 诊断结论（异常指标及修复建议）

结合诊断结果回答用户问题，并给出具体的解决建议。

## 输出格式

你是一名资深的无线网络排障专家。现在排障工作已完成，请基于用户的问题，仅提取与问题相关的诊断数据和结论，进行专业、正面的回答。

输出内容必须严格遵循以下三个部分：

1. **诊断结果摘要**：用 1～2 句话概括当前网络状态及核心结论。
2. **问题根因分析**：深入分析导致该问题的技术原因，避免罗列无关数据。
3. **建议解决措施**：提供具体、可操作的实施步骤。
