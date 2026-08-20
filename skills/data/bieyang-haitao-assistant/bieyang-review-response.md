# 别样海淘助手 Skill 审查回复

| 项目 | 值 |
|------|---|
| Skill 名称 | bieyang-haitao-assistant |
| 显示名 | 别样海淘助手 |
| 版本 | 1.0.0 |
| 回复日期 | 2026-08-06 |
| 原审查结论 | BLOCKED — 不可上架 |

---

## 一、P0 阻断问题修复

### P0-1 核心功能不可执行 — 已修复 ✅

**原问题：** Skill 为纯 prompt 型，无 `allowed-tools` 声明，WorkBuddy 内置 WebFetch 仅支持 GET 且无法消费 SSE 流，导致 API 调用机制完全缺失。

**修复方案：** 采用 Bash + curl（Option B），无需搭建额外 MCP Server。

- `SKILL.md` frontmatter 新增 `allowed-tools: [Bash]`
- 三个执行场景（商品搜索、价格比较、图片搜索）均替换为完整可执行的 `curl` 命令，包含：
  - `--max-time 30` 超时控制
  - `X-Nst-Uid` / `X-Nst-Sig` 确定性生成算法（见 P1-4）
  - SSE 流解析管道：`grep "^data:" | sed 's/^data: //' | jq -r 'select(.type == "complete")'`

**已验证：** curl 命令已在生产环境（`nestor-api.beyondstyle.us`）实测，SSE 流正常接收，jq 过滤管道正确输出 `complete` 事件 JSON，返回真实商品数据。

---

### P0-2 字段名硬冲突 `message` vs `user_input` — 已确认无需修复 ✅

**原问题：** 审查报告指出第 69 行使用了不存在的 `message` 字段。

**说明：** 检查当前 `SKILL.md` 源文件，第 69 行已正确使用 `user_input` 字段（`在 user_input 中加入比价意图描述`），与 `api-guide.md` 定义一致。所有场景均统一使用 `user_input`，无冲突。

---

### P0-3 无容错与降级策略 — 已修复 ✅

**原问题：** 仅覆盖 HTTP 429，缺少网络超时、SSE 中断、流半途中断、未收到 complete 事件等场景。

**修复：** `SKILL.md` 新增 `## 异常处置` 章节，覆盖全部异常场景：

| 异常情况 | 触发方式 | AI 回应策略 |
|---------|---------|-----------|
| 网络超时 | curl `--max-time 30` | 告知用户超时，建议稍后重试 |
| HTTP 429 限流 | curl 返回 429 | 等待 5 秒重试一次；再次 429 则提示频繁 |
| SSE 流无 complete 事件 | jq 无输出 | 视为失败，提示重试或换关键词 |
| API 返回 error 事件 | type = "error" | 转译 content 字段，建议调整关键词 |
| 服务不可达 | curl 非零退出码 | 提示服务暂时不可用 |

同步更新 `references/api-guide.md` 错误响应章节，扩展为完整异常处置表格。

---

### P0-4 图片搜索链路断裂 — 已修复 ✅

**原问题：** `SKILL.md` 要求"已上传到 OSS 的图片 URL"，但全包无 OSS 上传机制；`api-guide.md` 仅文档了 `image_url` JSON 字段。

**发现：** 对照后端源码（`server.py:881`）确认：
- 后端**不支持** JSON body 中的 `image_url` 字段（该字段从未在 JSON 路径中被读取）
- 后端**唯一支持**的图片上传方式为 `multipart/form-data`，表单字段名为 `image`
- `api-guide.md` 原有的"含图片 URL 的请求"章节属于文档错误

**修复：**
- `api-guide.md`：删除错误的 `image_url` JSON 章节，新增"含图片文件的请求"章节，正确文档 `multipart/form-data` 格式、`image` 字段名及完整 curl 示例（使用 `-F` 标志）
- `SKILL.md`：图片搜索场景改为 multipart 上传方式，明确说明"图片搜索仅支持本地上传文件，不支持 JSON 传入 URL"，移除"已上传到 OSS"的误导性描述

---

## 二、P1 建议改进

### P1-1 首次上架来源元数据缺失（B17） — 已修复 ✅

`SKILL.md` frontmatter 新增：

```yaml
source_type: skillhub
skillhub_slug: bieyang-haitao-assistant
```

---

### P1-2 description 过短（B03） — 已修复 ✅

原描述 42 字符，更新为（51 字符，符合 50-200 要求）：

```
别样海淘助手：海外全网商品搜索、以图搜款、全网比价，自然语言查询，快速找到全网低价商品，海淘必备神器。
```

---

### P1-3 ShopGeni 与 BeyondStyle 命名不一致 — 已修复 ✅

`api-guide.md` 文档头部新增命名说明：

> 内部代号为 ShopGeni API，对外品牌名为别样（BeyondStyle）统一购物接口，两者指同一服务。

---

### P1-4 X-Nst-Uid / X-Nst-Sig 生成算法缺失 — 已修复 ✅

`api-guide.md` 请求头章节新增确定性算法说明，并在 `SKILL.md` curl 命令中直接体现：

```bash
X-Nst-Uid: workbuddy-user-$(echo -n '<WORKBUDDY_USER_ID>'   | sha256sum | cut -c1-16)
X-Nst-Sig: workbuddy-device-$(echo -n '<WORKBUDDY_SESSION_ID>' | sha256sum | cut -c1-16)
```

---

### P1-5 X-Nst-Sig 设备指纹传输说明 — 已修复 ✅

`api-guide.md` 新增隐私说明：

> X-Nst-Sig 由 WorkBuddy 会话 ID 生成，仅用于区分并发会话，**不采集任何真实设备硬件标识符**。

---

### P1-6 未声明 allowed-tools — 已随 P0-1 一并修复 ✅

`allowed-tools: [Bash]` 已在 frontmatter 显式声明。

---

### P1-7 包内含 .DS_Store — 已修复 ✅

已删除 `skills/workbuddy/.DS_Store`。重新打包时使用：

```bash
zip -r bieyang-haitao-assistant.zip . -x "*.DS_Store" -x "__MACOSX/*"
```

---

## 三、其他结构性警告

### B02 YAML 降级解析

frontmatter 所有字符串值已加双引号，避免特殊字符（冒号、括号等）触发 YAML 降级解析。

### B06 name 与目录名不一致

提交 zip 包时文件名统一为 `bieyang-haitao-assistant.zip`，内容根目录保持与 `name: bieyang-haitao-assistant` 一致。

---

## 四、额外修复（审查未覆盖）

**SSE 事件类型文档错误：** 实测发现 API 实际发送的中间事件类型为 `progress`（含 `progress: 0-100` 字段），而非 `api-guide.md` 原文档中的 `thinking`。已更正 SSE 事件流示例及响应字段说明表格，与生产环境行为保持一致。

---

## 五、修复文件清单

| 文件 | 变更类型 |
|------|---------|
| `SKILL.md` | 修改 — frontmatter、三处执行步骤、新增异常处置章节 |
| `references/api-guide.md` | 修改 — 命名说明、Header 算法、图片上传章节（重写）、SSE 示例、响应字段表、异常处置表 |
| `.DS_Store` | 删除 |

---

## 六、重审建议

```bash
python scripts/review.py skills/workbuddy --stage all --autopilot
```

所有 4 项 P0 阻断和 7 项 P1 警告均已处理，预期可通过重审。
