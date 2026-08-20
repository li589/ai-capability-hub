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

### 本技能 (image-creator)

- 新增风格分发指引：写实人像 / 写真 / 商务职业照 → Nano-Banana；国风 / 汉服 / 艺术插画 → Seedream；需清晰可读文字 / 海报 → GPT-Image。
- 既有 10MiB 上传上限说明与 413 错误处理；轮询策略与生成后余额复核已落地。
