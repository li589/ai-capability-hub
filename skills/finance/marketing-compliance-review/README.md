# 金融营销宣传消保合规审查（marketing-compliance-review）

把一份银行 / 保险 / 基金的营销宣传材料（广告海报、文案、销售话术、培训课件、H5、短视频脚本）审成一份可归档的《消保审查意见书》（Word .docx）。审查聚焦**消费者权益保护**视角：是否误导、是否承诺收益、是否遗漏风险提示与必要披露、是否涉及特殊人群 / 个保违规等。

> ⚠️ 本工具为 **AI 辅助审查**，不能替代法律意见或监管认定；审查结论须经具备资质的人员 / 合规部门复核后方可作为正式意见。

---

## 能做什么 / 不能做什么

**能**
- 审查营销宣传材料是否违反消保相关法规；
- 输出结构化《消保审查意见书》（风险等级 / 维度 / 原文摘录 / 命中规则 / 法条依据 / 修改建议）；
- 支持图片（OCR / AI 视觉）、文档、纯文本多源素材；可引用内置监管处罚判例增强说服力。

**不能**
- ❌ 不替代法律意见或监管认定；
- ❌ 不做任何投资推荐、收益预测或"能否购买"类决策建议；
- ❌ 不保证零遗漏（罕见违规可能未被覆盖）；
- ❌ 不自动发布或阻断业务系统，仅生成审查报告。

---

## 目录结构

```
marketing-compliance-review/
├── SKILL.md                      # 技能说明与 5 步审查工作流
├── README.md                     # 本文件
├── package.json                  # 依赖声明（固定版本）
├── scripts/
│   ├── generate_review.js        # JSON → 《消保审查意见书》.docx 生成器
│   ├── ocr_extract.js            # 图片 → 文字提取（腾讯云 OCR，可选）
│   ├── fetch_kb.py               # 按文件名从 COS 拉取知识库原文（WebFetch 的命令行替代）
│   └── upload_to_cos.sh          # 将 42 篇原文上传到 COS 的运维脚本
├── references/                  # 核心规则（随包携带，离线可用）
│   ├── review-rules.md         # 禁用词库 + 审查要点速查（高频命中项）
│   ├── input-schema.md           # 脚本 JSON 输入字段与取值约定
│   ├── input-schema.json         # 机器可读 JSON Schema
│   ├── opinion-template.md       # 意见书结构模板说明
│   ├── penalty-cases.md          # 监管处罚案例线索（7 例）
│   ├── legal-mapping.md          # 违规模式 → 精确法条映射表
│   ├── legal-corpus.md           # 已核对的核心法规条文摘录
│   ├── knowledge-base.md         # 知识库 COS 托管与离线兜底说明
│   └── kb-index.md              # 42 篇原文「文件名 → COS 公网 URL」映射表
└── examples/                     # 草稿 / 归档模式脱敏示例输入
```

> **知识库全文托管于 COS**：42 篇原文（30 部法规全文 / 审查规则 / 模板 / 7 案例 / 监管原文）不在包内，按需从 `https://marketing-compliance-review-1300122096.cos.ap-guangzhou.myqcloud.com/kb/` 拉取（见 `references/kb-index.md`）。源文件位于发布侧的 `/tmp/skill_cos_upload/`，体积原因不进包。

---

## 前置依赖与安装

- **Node.js >= 18**，包管理器 npm（随 Node 自带）。
- 在 skill 目录下执行一次：

  ```bash
  cd <skill 目录>
  npm install
  ```

- `docx@9.6.1`：生成 .docx 的**必需**依赖；`tencentcloud-sdk-nodejs-ocr@4.1.268`：仅腾讯云 OCR 需要，不安装也能用 AI 视觉转录。

---

## 快速开始（5 步）

1. **收材料** — 拿到送审材料（图片 / 文档 / 文本），确认读取方式并提取原文。
2. **对规则** — 逐条对照 `references/review-rules.md` 的禁用词库 + 审查要点；需要某法规/案例全文时，按 `references/kb-index.md` 的 URL 从 COS 拉取（WebFetch 或 `python3 scripts/fetch_kb.py`）。
3. **定问题** — 对每个命中项确定：风险等级 + 维度 + 原文摘录 + 命中规则 + 法条依据 + 修改建议。
4. **填 JSON** — 把结果写成结构化 JSON（字段见 `references/input-schema.md`）。
5. **出文档** — `node scripts/generate_review.js <input.json> [output.docx]`。

最小烟测：`npm run smoke`。

---

## 知识库原文获取（COS 托管）

42 篇知识库原文托管在腾讯云 COS，不随包分发（体积超限）。获取方式：

```bash
# 方式 A：WebFetch 直接读取 kb-index.md 中对应 URL
# 方式 B：命令行
python3 scripts/fetch_kb.py 法规_04-中华人民共和国广告法.md https://<bucket>.cos.<region>.myqcloud.com/kb/
```

部署时把 `references/kb-index.md` 顶部的 `https://marketing-compliance-review-1300122096.cos.ap-guangzhou.myqcloud.com/kb/` 替换为真实公网地址，并确保该目录**公有读**（或用免签 URL）。COS 不可达时，Skill 退回本地核心规则（`review-rules` / `legal-mapping` / `legal-corpus`）兜底，并标注「原文待复核」。

上传脚本：`bash scripts/upload_to_cos.sh`（需先 `pip install coscmd` 并配置桶）。

---

## 版本

- v1.0.5：为压到平台 200KB 解压上限，将 42 篇知识库原文移出包体、托管至腾讯云 COS（按需拉取，见 `references/kb-index.md` + `scripts/fetch_kb.py`）；包内仅保留核心规则与索引，解压体积降至 ~120KB。
- v1.0.4：扁平化目录结构满足平台**两级目录限制**——知识库 42 篇全部提升至 `references/` 单层（文件名带 `法规_`/`规则_`/`模板_`/`案例_`/`原文_` 前缀区分分类），消除所有子目录嵌套。
- v1.0.3：S01 修正 `category` 为 `quality-security`、依赖与安装说明前置；S02 新增本 README。
- v1.0.2：内置知识库 42 篇完整离线快照。
- v1.0.1：基础审查能力 + 脚本生成器。
