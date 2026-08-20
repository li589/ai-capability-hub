# 页面编辑（Block 操作）

> 已有页面的 Block 级编辑与排版：创建/更新/删除/移动/批量编辑。

---

## 工具概览

- `block_convert_content_to_blocks` — Markdown/HTML 转 Block 结构
- `block_create_block_descendant` — 创建 Block 结构
- `block_update_block` — 单块更新
- `block_update_blocks` — 批量更新
- `block_move_blocks` — 移动 Block
- `block_delete_block_children` — 删除子节点
- `block_delete_block` — 删除指定 Block（含子孙）
- `block_describe_block` — 获取单个 Block 详情
- `block_list_block_children` — 读取 Block 内容

---

## Block 结构核心规则

### 叶子节点（不能有 children）
h1, h2, h3, h4, h5, code, image, divider, mermaid, plantuml

### 容器节点（必须指定 children）
callout, table, table_cell, column_list, column, toggle

> 详细类型定义见 `references/block-schema.md`

---

## 常见操作

### 创建结构化 Block

```
block_create_block_descendant({
  "entry_id": "doc123",
  "descendant": [
    {"block_id": "h1", "block_type": "h1", "heading1": {"elements": [{"text_run": {"content": "标题"}}]}},
    {"block_id": "tip", "block_type": "callout", "callout": {"color": "#FFF3E0"}, "children": ["tip_p"]},
    {"block_id": "tip_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "提示内容"}}]}}
  ],
  "children": ["h1", "tip"]
})
```

### 读取 Block 内容

```
block_list_block_children(entry_id="abc123", with_descendants=true)
```

### 批量更新

```
block_update_blocks({
  "entry_id": "abc123",
  "updates": {
    "block_id": {
      "update_text_elements": {
        "elements": [{"text_run": {"content": "更新后的内容"}}]
      }
    }
  }
})
```

---

## 注意事项

1. `block_id` 为客户端临时 ID，服务端返回实际 ID 映射
2. 叶子节点不支持 children 字段
3. 容器节点必须指定 children
4. 任意写入（创建/更新/删除/移动）失败必须执行下方降级方案，不允许沉默或仅口头报错

---

## ❗ Block 编辑失败降级方案（强制提供，不要等用户问）

Block 编辑与整篇导入不同：**容易部分成功部分失败**（如批量更新中某几个 block 报错）。失败时立即执行：

```
Step 0: 健康检查（whoami）失败 → 直接进入降级，不发起 block_* 调用
Step 1: 调用 block_* 工具
  ├─ ✅ 全部成功 → 返回受影响 block 概要
  ├─ ❌ 401/403 → 健康检查已失效，终止重试，进入降级
  ├─ ❌ 5xx / 超时 → 重试 1 次，仍失败进入降级
  └─ ⚠️ 部分成功（批量场景）→ 区分已成功/失败的 block，对失败部分进入降级
```

失败时的标准输出：

```markdown
❌ 页面 Block 编辑失败：[错误码 + 简短解释]
   - 目标页面：{domain}/pages/{entry_id}
   - 已成功：[N] 个 block（批量场景，列出已生效的 block_id）
   - 失败：[M] 个 block

✅ 为避免内容丢失，已把"待写入/未生效的内容"导出到本地：
📄 文件路径：{fallback_dir}/{entry_id}-blocks-{timestamp}.md
   （内容为对应 block 的 Markdown 等价表示，可人工核对）

恢复后可三选一：
1. 重跑本次 block 编辑（建议先 whoami 验证健康；批量场景只补失败部分，避免重复写入）
2. 打开页面手动粘贴该 .md 中未生效的内容
3. 复制到剪贴板：`cat <文件> | pbcopy`
```

### 降级文件落盘要求（必须真实执行）

```python
import os, datetime
fallback_dir = (
    os.environ.get("LEXIANG_FALLBACK_DIR")
    or os.environ.get("CODEX_OUTPUT_DIR")
    or os.path.expanduser("~/Desktop/lexiang-fallback")
)
os.makedirs(fallback_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
path = f"{fallback_dir}/{entry_id}-blocks-{timestamp}.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(pending_markdown)  # 未生效 block 的 Markdown 等价内容
```

> 降级目录优先级：用户指定目录 → `LEXIANG_FALLBACK_DIR` → `CODEX_OUTPUT_DIR` → `~/Desktop/lexiang-fallback`。
> 批量更新部分失败时，**只导出失败的 block**，避免与已生效内容重复。

---

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/block-schema.md` | Block 类型完整说明 |
| `references/mcp-examples.md` | 复杂 Block 结构示例 |
| `references/markdown-to-block.md` | Markdown 转 Block 指南 |
| `references/block-update.md` | 批量更新方法 |
| `references/content-reorganize.md` | 文档结构重组 |

## 辅助资源

| 资源 | 说明 |
|------|------|
| `assets/lexiang-block-schema.json` | Block Schema JSON |
| `assets/examples/` | Block 结构示例 |
| `assets/themes/` | 主题配置 |
