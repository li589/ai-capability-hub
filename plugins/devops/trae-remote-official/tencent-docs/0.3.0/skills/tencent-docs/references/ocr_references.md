# OCR 图片识别参考

## 工具

| 工具 | 功能 | 输出 |
|---|---|---|
| `ocr.extract` | 识别单张图片文字 | 文字列表，可选坐标 |
| `ocr.toword` | 1-9 张图片转在线文档 | `file_id`、`file_url` |
| `ocr.toexcel` | 1-9 张图片表格转在线表格 | `file_id`、`file_url` |

限制：单张不超过 10MB，总计不超过 50MB，支持 PNG、JPG、JPEG、BMP 和 WEBP。

## 图片输入

`image_url` 与 `image_base64` 严格二选一：

- `image_url`：公网可直接下载的 HTTP(S) URL，不支持需要登录、内网或已过期地址。
- `image_base64`：纯 base64 字符串，不包含 `data:image/...;base64,` 前缀。

优先使用公网 URL。本地图片不要把超长 base64 内容粘贴到对话；若 Trae 当前无法安全地把本地文件内容传给 MCP，请让用户提供可访问的图片 URL。

## ocr.extract

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `image_url` | string | 二选一 | 公网图片 URL |
| `image_base64` | string | 二选一 | 纯 base64 |
| `extract_type` | string | 否 | `basic`、`accurate` 或 `efficient` |
| `with_positions` | bool | 否 | 是否返回文字坐标 |

```json
{
  "image_url": "https://example.com/invoice.png",
  "extract_type": "accurate",
  "with_positions": true
}
```

## ocr.toword / ocr.toexcel

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `images` | array | 是 | 1-9 张，每项使用 `image_url` 或 `image_base64` |
| `title` | string | 否 | 输出文档标题 |

```json
{
  "images": [
    {"image_url": "https://example.com/page-1.png"}
  ],
  "title": "会议纪要"
}
```

单图转换会启用更有针对性的矫正增强，不要为了凑批量而重复图片。同步请求处理较慢时等待返回，不要重复触发。
