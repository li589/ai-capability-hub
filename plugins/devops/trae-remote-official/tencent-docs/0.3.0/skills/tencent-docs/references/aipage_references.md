# 本地 HTML 一键上云（.aipage 导入）

用于把本地 HTML 单文件或目录打包成 `.aipage`，再导入腾讯文档。

## 触发条件

- 用户提供本地 `.html` 路径并要求上传、导入或同步到腾讯文档。
- 上游流程已经生成 HTML，并提供 `html_path` 或 `html_dir`。

## 标准流程

### 1. 打包

使用本 skill 目录下的 `aipage_pack.js`。脚本是纯 Node.js 实现，不依赖 npm 包。

```bash
# 单文件
node <skill_dir>/aipage_pack.js --html "<html_path>" [--title "<title>"]

# 目录
node <skill_dir>/aipage_pack.js --dir "<html_dir>" [--title "<title>"]
```

脚本输出：

```text
AIPAGE_PATH=/tmp/example.aipage
AIPAGE_SIZE=123456
AIPAGE_MD5=abcd1234...
AIPAGE_TITLE=示例标题
```

### 2. 获取上传地址

直接调用 Trae 已加载的 `manage.pre_import`：

```json
{
  "file_name": "example.aipage",
  "file_size": 123456,
  "file_md5": "abcd1234..."
}
```

保存返回的 `upload_url`、`file_key` 和 `task_id`。

### 3. 上传文件

使用 `curl` 把 `.aipage` 文件 PUT 到 `upload_url`：

```bash
curl -sS -X PUT \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@<AIPAGE_PATH>" \
  "<upload_url>"
```

HTTP 2xx 表示上传成功。`upload_url` 可能包含临时签名，不要写入日志或最终回复。

### 4. 触发导入

直接调用 `manage.async_import`：

```json
{
  "task_id": "<task_id>",
  "file_key": "<file_key>",
  "file_name": "example.aipage",
  "file_md5": "abcd1234...",
  "file_size": 123456
}
```

随后每隔约 3 秒调用 `manage.import_progress`，最多等待 60 秒。`progress=100` 后返回 `file_id` 和 `file_url`。

## 约束

- 必须使用 `aipage_pack.js`，不要自行拼装 ZIP、`manifest.json` 或 `janus.manifest.json`。
- `pre_import`、`async_import` 或轮询失败时最多重试两次，并保留 `trace_id` 便于排查。
- 不要安装额外 MCP 客户端，不要从本地读取 connector Token。
- 成功后向用户返回腾讯文档在线链接。
