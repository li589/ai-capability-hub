# 场景：Markdown 导入知识库

> 本文只讲 Markdown 导入的**方式选择**。具体上传/更新流程不在此重复，见下方指针。

## 两种方式怎么选

| 方式 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| **① 文件上传**（`file_apply_upload` 三步） | 保留版本历史，更新只需上传新版本 | 在乐享内不可直接编辑正文 | 需要版本管理、当附件留存的文档 |
| **② 转为 Block**（`entry_import_content`） | 内容变成可在乐享内编辑的 Block 结构 | 后续更新要操作 Block，较复杂 | 需要在乐享中直接编辑/排版的文档 |

> 默认推荐 ①（文件上传）；只有用户明确要"导入后还能在乐享里改正文"时才用 ②。

## 流程指针（不在此重复）

- **方式① 文件上传 / 更新已有文件**（三步：apply → PUT → commit）：见 `modules/files.md`
  - Markdown 的 `mime_type` 用 `text/markdown`
  - 更新已有文件时需传 `file_id`（即 `entry_describe_entry` 返回的 `target_id`），且 `parent_entry_id` 填文件自身 entry_id
- **方式② 转为 Block**（`entry_import_content`，`content_type="markdown"`）：见 `modules/writer.md`
- **批量上传脚本**：见 `scripts/upload-files.py`（用法见 `modules/files.md` 辅助脚本表）
