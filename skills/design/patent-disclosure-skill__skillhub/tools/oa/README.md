# 模式 D · 审查答复工具

案例笔记（Obsidian）+ 可选向量检索。**向量不是必须的**。

## 对话配置（推荐）

Agent 按 `prompts/oa/configure_embedding.md` 问答；写文件命令示例：

```bash
python tools/oa/config.py recommend
python tools/oa/config.py skip-vector
# 或：预设 + Key（Key → 文档目录 embedding.secrets.yaml）
python tools/oa/config.py set --preset zhipu --api-key "sk-..."
# 或：自定义
python tools/oa/config.py set --provider openai_compatible \
  --model embedding-3 --dimensions 1024 \
  --base-url https://open.bigmodel.cn/api/paas/v4 \
  --api-key "sk-..."
# set 默认自检；也可单独：
python tools/oa/config.py selftest
python tools/oa/config.py status
python tools/oa/rebuild_vectors.py --confirm
```

- 配置：`{Documents}/patent-disclosure-skill/oa/embedding.config.yaml`  
- 密钥：同目录 `embedding.secrets.yaml`（勿提交）  
- 自检失败仍可用标签检索。

## Provider

| provider | 典型 preset |
|----------|-------------|
| `openai_compatible` | `zhipu` / `dashscope` / `openai` |
| `minimax` | `minimax` |
| `local` | `local` |

## 入库 / 检索（优先 PDF）

```bash
python tools/oa/search_cases.py --pdf notice.pdf --defect inventiveness --top-k 5
python tools/oa/ingest_case.py -i path/to/case.md
python tools/oa/refresh_vault.py   # 索引 + Bases + 关联 Canvas
```

Obsidian 结构：`oa/cases/history/` · `oa/pending/` · `oa/drafts/` + `_OA索引` / `_OA看板.base` / `_OA关联.canvas`。

见 `prompts/oa/` 与 [SKILL.md](../../SKILL.md) 模式 D。
