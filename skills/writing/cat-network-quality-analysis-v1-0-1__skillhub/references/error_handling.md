# 错误处理指南

脚本常见失败场景的识别与处理。AI 收到 JSON `code=1` 后按本文档分类应对，**不要自行编造错误原因**。

## 错误分类矩阵

| # | JSON `error` 字段特征关键字 | 错误类型 | 严重性 | AI 处理方式 |
|:-:|----------------|---------|:------:|------------|
| 1 | `SSLCertVerificationError` / `CERTIFICATE_VERIFY_FAILED` / `unable to get local issuer certificate` | SSL 证书问题 | ⚠️ 配置 | 引导用户配置 certifi 或 macOS 证书修复命令 |
| 2 | `AuthFailure.SignatureFailure` / `AuthFailure.SecretIdNotFound` / `UnauthorizedOperation` | 鉴权失败 | ❌ 凭据 | 提醒检查 `CAT_SECRET_ID` / `CAT_SECRET_KEY` 配置 |
| 3 | `ClientNetworkError` / `Connection refused` / `Max retries exceeded` / `网络请求失败` | 网络连通性 | ⚠️ 网络 | 提醒检查网络/VPN/endpoint 域名是否正确 |
| 4 | `InvalidParameter` / `InvalidParameterValue` | 参数错误 | ❌ 调用方 | 检查时间戳是否毫秒、TaskID 格式是否正确 |
| 5 | `ResourceNotFound` / `task not found` | 任务不存在 | ⚠️ 数据 | 向用户确认 TaskID 是否拼写正确 |
| 6 | `未获取到分析内容` | 空响应 | ⚠️ 数据 | 可能时间范围内无数据；建议扩大时间范围 |
| 7 | `RequestLimitExceeded` / `TooManyRequests` | 限流 | ⚠️ 临时 | 提醒用户稍后重试 |
| 8 | `InternalError` / `5xx` / `HTTP 5` | 服务端故障 | ⚠️ 临时 | 提醒稍后重试；若持续则联系 CAT 支持 |
| 9 | `HTTP 4` (4xx) | 客户端 HTTP 错误 | ❌ 调用方 | 检查请求参数/鉴权；4xx 详情见 error 字段 body |
| 10 | `未找到腾讯云密钥` | 密钥缺失 | ❌ 配置 | 提醒配置 `CAT_SECRET_ID` / `CAT_SECRET_KEY` 环境变量 |
| 11 | `tcproxycli 调用失败` | tcproxycli 异常 | ⚠️ 环境 | 检查 tcproxycli 是否安装及 `TCPROXYCLI_*` 环境变量；error 含 stderr 末尾几行 |
| 12 | `SSE 调用超过 300 秒` | 超时 | ⚠️ 临时 | 提示用户分析超时，建议缩小时间范围后重试 |
| 13 | 无已知关键字 | 未知异常 | ❌ Bug | 原样返回 error 字段，建议联系维护者 |

> `incomplete: true`（JSON `code=0`，非失败）的处理见文末[§ 内容不完整](#8-内容不完整incomplete)章节。

## 典型错误详解

### 1. SSL 证书验证失败（macOS 常见）

**JSON `error` 样貌**：
```
SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)
```

**根因**：macOS 上用官方 pkg/Homebrew 安装的 Python 不会自动信任 Keychain 证书。

**给用户的解决方案**（按推荐度排序）：

**方案 A：运行 macOS Python 自带修复脚本**（一次性根治）
```bash
/Applications/Python\ 3.12/Install\ Certificates.command
```
（根据实际 Python 版本调整路径）

**方案 B：安装 certifi 并设置环境变量**（通用）
```bash
pip3 install certifi
export SSL_CERT_FILE=$(python3 -m certifi)
export REQUESTS_CA_BUNDLE=$(python3 -m certifi)
```
并建议写入 `~/.zshrc` 或 `~/.bashrc` 持久化。

**方案 C：公司内网场景**（仅内部 endpoint 时）
联系运维拿到腾讯内网根证书，追加到 certifi 的 `cacert.pem` 文件末尾。

### 2. 鉴权失败

**JSON `error` 样貌**：
```
HTTP 401 Unauthorized: {"Response":{"Error":{"Code":"AuthFailure.SignatureFailure","Message":"The provided credentials could not be validated."}}}
```

**给用户的解决方案**：
1. 检查 `scripts/.env`（或环境变量）中的 `CAT_SECRET_ID` / `CAT_SECRET_KEY` 是否正确（非占位符 `your-secret-id`）
2. 检查密钥是否过期或被禁用（通过 [腾讯云 CAM 控制台](https://console.cloud.tencent.com/cam/capi) 确认）
3. 如果使用临时凭据，检查 `CAT_TOKEN` 是否也已配置且未过期

### 3. 参数错误

**JSON `error` 样貌**：
```
HTTP 400 Bad Request: {"Response":{"Error":{"Code":"InvalidParameterValue","Message":"StartTime must be millisecond timestamp"}}}
```

**给用户的解决方案**：
- 时间戳需为**毫秒**（13 位），不是秒（10 位）
- `StartTime <= EndTime`
- 跨度不超过接口限制（通常 30 天）

此类错误通常是 AI 调用问题，AI 应该自查而非让用户检查。

### 4. 空响应（未获取到分析内容）

**JSON `error` 样貌**：
```
未获取到分析内容
```

**给用户的解释**：
- 指定的时间范围内任务无数据/无错误（说明任务运行正常！）
- 或 TaskID 不属于当前账号
- **建议**：扩大时间范围到最近 24/48 小时重试；或换一个有数据的 TaskID

这不一定是故障，可能是**正常情况**。语气保持中性。

### 5. 限流（TooManyRequests）

**给用户的解释**：
- CAT AI Console 触发限流
- 建议等待 1–2 分钟后重试
- 如频繁触发，联系 CAT 团队申请提高配额

### 6. 密钥缺失

**JSON `error` 样貌**：
```
未找到腾讯云密钥，请配置 CAT_SECRET_ID/CAT_SECRET_KEY 或 TENCENTCLOUD_SECRET_ID/TENCENTCLOUD_SECRET_KEY 环境变量
```

**给用户的解决方案**：
1. 在 `scripts/.env` 中配置 `CAT_SECRET_ID` 和 `CAT_SECRET_KEY`
2. 或通过环境变量导出：`export CAT_SECRET_ID=xxx && export CAT_SECRET_KEY=xxx`
3. 若使用临时凭据，还需配置 `CAT_TOKEN`

### 7. tcproxycli 调用失败

**JSON `error` 样貌**：
```
tcproxycli 调用失败（exit=1, stderr=...）
```

**给用户的解决方案**：
1. 检查 `tcproxycli` 是否在 PATH 中：`which tcproxycli`
2. 检查 `TCPROXYCLI_PROXY_ENDPOINT` 和 `TCPROXYCLI_SESSION_KEY` 环境变量是否正确配置
3. 查看 error 中的 stderr 末尾几行，确认具体原因（认证失败、endpoint 不通等）
4. 若不需要代理模式，移除 `TCPROXYCLI_*` 环境变量，自动回退到 TC3 签名模式

### 8. 内容不完整（incomplete）

**触发条件**：JSON `code=0` 且 `"incomplete": true`（SSE 流未正常收到 `agent.done`，如连接提前中断）。

**给用户的提醒**（追加在 `report` 正文末尾）：
> ⚠️ 本次分析未完整返回，内容可能不全。建议缩小时间范围后重试。

**AI 处理要点**：
- 这不是失败，而是成功但内容可能截断，**不要**当成 `code=1` 走失败汇报模板
- `report` 正文正常回复，末尾另起一行追加上述 ⚠️ 提醒
- 其他交付规则（pcap 候选等）照常执行

## 通用错误汇报模板

AI 收到 JSON `code=1` 后的标准回复格式：

```markdown
## ❌ 分析失败

**错误类型**：{分类名称}

**关键信息**：
```
{JSON error 字段中最具诊断价值的 1-3 行}
```

**可能原因**：
- {根据分类矩阵选择 1-3 条最可能的}

**建议方案**：
1. {最推荐的解决步骤}
2. {备选方案}

---
是否需要我帮您 {具体可执行的下一步}？
```

## 禁止行为

| 禁止项 | 正确做法 |
|--------|---------|
| 把整个 error 字段原样贴给用户 | 只贴最关键的 1-3 行 |
| 凭空编造错误原因 | 严格按分类矩阵；未知错误如实说明 |
| 检测到失败自动重试 | 必须先询问用户，明确错误原因后才能重试 |
| 多次收到同样错误继续重试 | 连续 2 次相同错误必须停下来与用户沟通 |
| 隐瞒非致命错误不告诉用户 | 所有错误都要如实告知，但解释要通俗 |
