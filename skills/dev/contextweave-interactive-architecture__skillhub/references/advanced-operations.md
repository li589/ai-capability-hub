# 高级操作

仅在任务涉及已有图、现成 CW 文件、导出或链接注入时读取本页。

## 修改已有图

从上一轮返回 JSON 中取得 `session_id` 并复用。把当前 CW 全文放入请求文件的 `# CW` 代码块；不要只写“基于上一张图修改”。

使用 `edit_contextweave.cjs` 按 `session_id` 提交修改意图。客户端本身无状态，因此旧图上下文必须随请求明确提供。

## 导入现成 CW

用户明确提供 `.cw` 文件并要求导入时，直接调用：

```bash
node scripts/import_contextweave_code.cjs --path "<绝对文件路径>"
```

此场景禁止重新生成结构化意图文件，也禁止调用 `generate_contextweave.cjs`。

## 导出或找回 CW

用户要求导出或找回某个 `session_id` 的 CW 代码时，必须调用：

```bash
node scripts/export_contextweave_code.cjs --session_id "<session_id>"
```

不要在对话中粘贴 CW 代码来代替实际导出。

## 为节点或连线添加文件链接

绘图与链接设置必须分两步完成：

1. 调用 `generate_contextweave.cjs` 生成结构，首次请求忽略链接要求。
2. 取得 `session_id` 后，调用 `edit_contextweave.cjs` 批量注入链接。

第二步的 `# Request` 使用以下 JSON 指令：

```json
{
  "base_path": "<当前工作区绝对路径>",
  "links": [
    { "targets": ["模块A"], "link": "./src/module.py#L10-L25" },
    { "targets": ["模块A到模块B的连线"], "link": "./src/api_handler.py" }
  ]
}
```

- `base_path` 必填。
- 文件路径不加 `file:///` 前缀。
- 指向代码行时使用 `#L<起始>-L<结束>`。

## 脚本能力索引

| 脚本 | 用途 |
|---|---|
| `generate_contextweave.cjs` | 从 `input_file` 生成新图 |
| `edit_contextweave.cjs` | 基于 `session_id` 修改已有图或注入链接 |
| `import_contextweave_code.cjs` | 导入现成 `.cw` |
| `export_contextweave_code.cjs` | 导出或找回会话中的 CW |
| `export_session_asset.cjs` | 导出会话产物 |
| `recompile_contextweave.cjs` | 轮询专家处理结果；见 [异常恢复](error-recovery.md) |
| `request_quota_code.cjs` | 发送免费额度验证码；只在相关错误时使用 |
| `redeem_quota_code.cjs` | 兑换免费额度；只在相关错误时使用 |
| `submit_feedback.cjs` | 提交失败分析与用户反馈 |

需要拆分多视图时，读取 [多视图与 Scenarios](multi-view-scenarios.md)。
