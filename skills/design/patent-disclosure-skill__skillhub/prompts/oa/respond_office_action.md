# 模式 D · 审查文档 → 答复草稿

前置：配置已确认；**先检索再生成**。

## 输入（优先 PDF，禁止让用户手贴长文）

- **审查意见通知书 / 补正通知书 PDF**（用户给路径即可）  
- 可选：本申请权要/说明书 PDF 或摘录路径  
- 可选：专利类型、已知法条/缺陷标签  

Agent **必须**先跑抽取，不要让用户「先转文本再粘贴」。

```bash
# 仅抽取（可读全文做结构化）
python tools/oa/pdf_text.py -i path/to/office_action.pdf
# → 同目录 {stem}.extracted.txt + .json

# 抽取并直接检索（推荐）
python tools/oa/search_cases.py --pdf path/to/office_action.pdf \
  --patent-type invention \
  --statute "专利法第22条第3款" \
  --defect inventiveness \
  --top-k 5
```

扫描件若几乎无字：工具会 `WARN extracted_text_too_short`；告知用户换可复制文字的 PDF 或先 OCR，**仍不要**让用户手抄通知书。

## 步骤

### 1. 结构化解析

`Read` 抽取得到的 `.extracted.txt`（或 `--stdout` 预览），抽出：

- `notice_kind`、答复期限（若有）  
- 逐条缺陷：法条、审查员观点、对比文件号  
- `defect_types`、`statutes`、`patent_type`、`domain`（推断须标注）

可把结构化 YAML 落到 `outputs/oa/{案件}/notice_struct.yaml`。

### 2. 检索（必做）

优先 `--pdf`；已有抽取文件时可用 `--query-file …extracted.txt`。

```bash
python tools/oa/search_cases.py --pdf path/to/office_action.pdf \
  --patent-type invention \
  --statute "专利法第22条第3款" \
  --defect inventiveness \
  --top-k 5
# 强制仅标签：加 --tags-only
```

- 展示 `hits`，**每条带 `diff`**；同时告知 `retrieval_mode`（`vector` / `tags_only` / `tags_fallback`）。  
- 若 JSON 含 `rebuild_hint_zh`：向用户转述，确认后跑 `rebuild_vectors.py --confirm`。  
- 向量超时/失败时**不得中断**：用标签结果继续生成草稿。  
- 库为空：仅输出提纲 + 策略选项，禁止假装引用历史案。

### 3. 策略选项（人勾选）

至少给出：`仅意见陈述` / `修改权利要求` / `修改说明书` / `补正形式`；附超范围风险提示。

### 4. 生成草稿（约束）

- **逐条**对应通知书条目编号。  
- 引用命中案例时写 `case_id` + 为何可参考 + **差异**。  
- 若建议修改：每处修改须指向说明书可支持位置（未知则标「待发明人指认段落」）。  
- 落盘：`outputs/oa/{案件或日期}/意见陈述草稿_{时间戳}.md`（gitignore）。  

### 5. 人审闸门

使用 `guardrails.md` 确认话术。
