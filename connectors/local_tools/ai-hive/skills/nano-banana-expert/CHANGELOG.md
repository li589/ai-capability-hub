# 更新日志 (CHANGELOG)

> 本文件随 AI-HIVE Connector 包版本更新。Connector 包当前版本：**1.1.0**。
> 日期：2026-08-13

## [1.1.0] — 2026-08-13

### 全技能通用修正（cross-cutting）
- `list_models` 参数名由 `kind` 修正为 `modelType`（枚举 `TEXT` / `IMAGE` / `VIDEO`）。
- 图片类技能 `generate_image` 参考图参数由 `referenceMediaIds` 修正为 `imageMediaIds`；视频类技能保持 `referenceMediaIds`（符合后端 schema）。
- `upload_media_from_path` 的 `kind` 参数保留不变（服务端按资源类型推断，不得改名）。
- 新增上传单文件约 10MiB 上限说明：4K PNG 常超限，作为参考图传入下一张前需导出 ≤2K 或转 JPEG（≤10MiB），否则返回 413。
- 新增 413 错误处理指引。

### 本技能 (nano-banana-expert)

- 新增肖像场景触发词：写真 / 头像 / 商务人像 / 简历照 / 职业照 / portrait / headshot / LinkedIn avatar。
- 既有 10MiB 上传上限说明与 413 错误处理；轮询策略与生成后余额复核已落地。
