# 安装说明

本技能遵循 [AgentSkills](https://agentskills.io) 常见布局：仓库根目录即技能根目录，内含 `SKILL.md`。

## Claude Code

在 **git 仓库根目录** 下安装：

```bash
mkdir -p .claude/skills
git clone <本仓库 URL> .claude/skills/patent-disclosure-skill
```

或使用本地路径复制到 `.claude/skills/patent-disclosure-skill`。

运行时环境通常会设置 **`CLAUDE_SKILL_DIR`** 指向该技能目录；`SKILL.md` 中的 `${CLAUDE_SKILL_DIR}/prompts/...` 即解析到此路径。

## Cursor

Cursor 支持 [Agent Skills](https://www.cursor.com/docs/context/skills) 约定：每个技能是一个**子文件夹**，内含根级 `SKILL.md`（`name` 字段须与文件夹名一致，本仓库为 `patent-disclosure-skill`）。可将**本仓库完整内容**（含 `prompts/`、`tools/` 等）放在下列位置之一，重启 Cursor 后在 **Settings → Rules** 中查看是否已被发现；亦可用 Agent 输入 `/` 后选择技能名。

### 用户主目录（全局，所有项目可用）

| 系统 | 推荐路径 |
|------|----------|
| Windows | `%USERPROFILE%\.cursor\skills\patent-disclosure-skill\`（即 `C:\Users\<用户名>\.cursor\skills\patent-disclosure-skill\`） |
| macOS / Linux | `~/.cursor/skills/patent-disclosure-skill/` |

示例（将仓库克隆到全局技能目录）：

```bash
mkdir -p ~/.cursor/skills
git clone <本仓库 URL> ~/.cursor/skills/patent-disclosure-skill
```

Windows（PowerShell）：

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.cursor\skills"
git clone <本仓库 URL> "$env:USERPROFILE\.cursor\skills\patent-disclosure-skill"
```

### 项目目录（仅当前仓库）

将本技能放在当前工作区下的：

`<项目根>/.cursor/skills/patent-disclosure-skill/`

（同样需包含完整仓库文件树，且 **`SKILL.md` 中 `name: patent-disclosure-skill` 与文件夹名一致**。）

### 与「仅打开文件夹」等价关系

若未使用上述 `skills/` 布局，也可**直接用 Cursor 打开本仓库根目录**作为工作区；此时将 **`CLAUDE_SKILL_DIR`** 理解为「包含 `SKILL.md` 的目录」。分步指令在：

- `prompts/disclosure/`（交底；含 `invention/`、`utility_model/`、`design/`）
- `prompts/reader/`（通俗解读）
- `prompts/shared/`（Structure / Appearance 填表）

与 `SKILL.md` 中的 **`${CLAUDE_SKILL_DIR}/prompts/...`** 同义。

Cursor 也会扫描 **`~/.claude/skills/`**、项目内 **`.claude/skills/`** 等路径；详见 Cursor 官方文档与当前版本设置项。

## 默认交底需要什么（发明主路径）

技能默认按**发明交底**走：定稿要 `.md` + `.docx`，3.2 / 3.4 框图要出 PNG，Step 5 优先国知局检索。这条路径**需要**：

1. **Python 3.9+**（及 pip）
2. 在技能根目录安装依赖（含 `python-docx`、`playwright` 等）：

   ```bash
   pip install -r requirements.txt
   ```

3. **本机 Google Chrome 或 Microsoft Edge**（推荐，多数电脑已有）。出图与查新共用，**不必**再装 Node / npm / mmdc。

探测是否已能启动浏览器：

```bash
python tools/shared/browser.py --probe
```

- `ok=true`：可直接定稿出图、跑国知局检索。
- 没有 Playwright 包：再执行一次上面的 `pip install -r requirements.txt`。
- 本机既无 Chrome 也无 Edge：才执行 `python -m playwright install chromium`（整机一次即可）。

无可用浏览器时，发明仍可先交 **Markdown**（mermaid 围栏保留）；Word 里框图可能先是代码块，补齐浏览器后重跑 `tools/shared/mermaid_render.py` 即可。

公式进 Word 走 **OMML**（`latex2mathml`，已在 `requirements.txt`）。**不要**为默认交底安装 matplotlib。仅当定稿 stderr 出现 `omml_text_fallback`、且用户回复「是」之后，才：

```bash
pip install matplotlib
python tools/shared/md_to_docx.py -i 定稿.md -o 定稿.docx --base-dir 定稿目录 --math-render
```

**实用新型 / 外观**定稿以各类型 `prompts/disclosure/utility_model|design/disclosure_builder.md` 为准：填表产出 `structure_schema`/`appearance_schema` + **`figure_plan.yaml`**，成文只嵌清单入文图（结构图或视图；docx 对实用建议、对外观可选）。不跑发明 mermaid 时，仍建议装 `requirements.txt`（扫 Word/PPT、出 docx）。

仅在编辑器里**手写** Markdown、完全不跑仓库脚本时，才不必装 Python。

细则见 **`tools/README.md`**。

## 可选：STEP 多视角解析（默认关闭）

扫描发现 **`.step` / `.stp`** 时，Agent **成文不中断**；交底 md+docx **落盘后再反问**是否开启。确认前**不安装** CadQuery。仅有 SolidWorks 等原生 CAD、无 STEP 时，在交付回复末尾提示导出中性格式。

先探测 `tools/shared/cad-env`（已就绪则**跳过安装**）：

```bash
python tools/shared/cad_venv.py
python tools/shared/bootstrap_cad_venv.py
python tools/shared/run_step_to_views.py --enable-step-parse -i model.step -o outputs/{案件}/cad_views
```

CadQuery 只进隔离 venv（Python **3.10–3.12**，本机已是 3.11/3.12 不必再装 3.10）。无系统 Cairo 时保留 SVG，用已有 Playwright 无头浏览器截 PNG。CAD 出图**不使用** matplotlib（matplotlib 只用于发明公式 PNG，见上文）。

与主 `requirements.txt` **独立**。细则见 `prompts/disclosure/project_scan.md`「CAD / STEP」、`tools/README.md`。

## 外观 / 实用新型线稿（成文前必做）

不问用户。先规划再出图。仅 `PATENT_SKILL_SKIP_LINEART=1` 或用户明确不要线稿才跳过。CAD 投影不是线稿、不得入文。

```bash
python tools/shared/image_gen.py --case-dir outputs/{案件}
python tools/shared/design_lineart_gate.py --case-dir outputs/{案件} --prepare-jobs
python tools/shared/structure_lineart_gate.py --case-dir outputs/{案件} --prepare-jobs
```

流程见 `prompts/shared/image_gen.md`、`design_lineart_assist.md`、`structure_lineart_assist.md`。结构线稿件号对齐 StructureSchema，推荐 overlay，禁止自创件号。

## 可选：国知局公布公告站抓取（Step 5 查新优先路径）

若需使用 **`tools/crawl/cnipa_epub_search.py`**（一步，推荐）或 **`tools/crawl/cnipa_epub_crawler.py`** / **`tools/crawl/cnipa_epub_parse.py`**（[epub.cnipa.gov.cn](http://epub.cnipa.gov.cn/)，见 `prompts/disclosure/prior_art_search.md`）：

```bash
pip install -r tools/crawl/requirements-cnipa.txt
python tools/shared/browser.py --probe
# 仅当 probe 显示无 Chrome/Edge 且无自带 Chromium 时：
# python -m playwright install chromium
python tools/crawl/cnipa_epub_search.py --type utility_model 卡扣
```

**Windows 终端**：定稿 / 查新脚本会把 stdout、stderr 设为 UTF-8，子进程带 `PYTHONUTF8=1`。Agent **以退出码和机读前缀为准**（`EPUB_HITS_JSON:`、`PROBE:`、`MERMAID:`、`DOCX:`、`MATH:`）；stderr 有中文或 PowerShell `NativeCommandError` **不等于**失败。不必先 `chcp 65001`。若仍乱码，可设 **`PYTHONUTF8=1`**，且不要用 **`2>&1`** 把 JSON 混进错误流。

`playwright` 已写入根目录 `requirements.txt`。若已按上文装过主依赖，**不必**再为查新单独 pip 一遍；`tools/crawl/requirements-cnipa.txt` 仅在只装爬虫、不装整份主依赖时使用。未装或探测失败时，Step 5 仍可按该 prompt 降级为 **WebSearch**（如 Google 学术）。

## 可选：审查答复案例库（模式 D，默认关闭）

显式触发「审查答复 / 案例入库 / `/oa`」后使用。配置与向量库默认在操作系统**文档**目录：`{Documents}/patent-disclosure-skill/oa/`（`PATENT_OA_HOME` 可覆盖）。**推荐**智谱 `embedding-3`；亦支持 DashScope / MiniMax / 本地 / OpenAI（`config.py set --preset …`）。

```bash
pip install -r tools/oa/requirements-oa.txt
# 例：智谱
# 环境变量 ZHIPUAI_API_KEY=…
python tools/oa/config.py recommend
python tools/oa/config.py set --preset zhipu
# 其他：--preset dashscope|minimax|local|openai
python tools/oa/ingest_case.py -i path/to/case.md
python tools/oa/refresh_vault.py   # 刷新 oa 索引 / Bases / 关联 Canvas
python tools/oa/search_cases.py --query "创造性 区别特征" --defect inventiveness --top-k 5
```

Obsidian 案例落在 `{vault}/oa/cases/history/`（另有 `pending/`、`drafts/`）。与主依赖**独立**。细则见 `prompts/oa/`、`tools/oa/README.md`、[SKILL.md](SKILL.md) 模式 D。

## 强烈建议：专利通俗解读 + Obsidian 库

**强烈建议安装并配置 Obsidian**，才能完整体验索引、Canvas 知识图谱、术语网、关系图配色与公开线索旁注。无库时可降级到 `outputs/patent_reader/`，效果会弱一截。

对话开始前由 Agent 运行探测（也可手动）：

```bash
python tools/patent_reader/vault/check_obsidian_env.py
# 自动接受唯一/当前打开的库：
python tools/patent_reader/vault/check_obsidian_env.py --auto-accept
# 手动指定并持久化（+ Windows 用户环境变量）：
python tools/patent_reader/vault/check_obsidian_env.py --set "C:\Users\你\Documents\Obsidian Vault" --setx
```

亦可仅设会话变量：

```bash
# Windows PowerShell
$env:PATENT_READER_OBSIDIAN_VAULT = "D:\Obsidian\你的库"
# 可选：库内目录，默认 Research/Patents
$env:PATENT_READER_PAPERS_DIR = "Research/Patents"
$env:PATENT_READER_GLOSSARY_DIR = "Research/术语"
```

```bash
pip install -r tools/patent_reader/requirements.txt   # PDF：pymupdf
```

**首次使用**：解读**入库时会自动**初始化库（CSS、Bases、索引、关系图配色）。用户只需安装 Obsidian、配置库路径，并（可选）在社区插件市场安装 Dataview 等——步骤与插件清单见 **`docs/obsidian-setup-guide.md`**。交付后 Agent 按 **`prompts/reader/obsidian_plugin_guide.md`** 引导可选插件。

工具链分层见 **`tools/patent_reader/README.md`**（`shared/` · `extract/` · `analyze/` · `vault/`）。常用入口：

```bash
python tools/patent_reader/extract/fetch_patent_pdf.py --pub CN… -o tmp/patent_reader/RUN
python tools/patent_reader/vault/write_patent_obsidian_note.py --help
```
