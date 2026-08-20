# 国际专利检索参考（market=world）

> 本文件是 PatSeek 国际/外文专利检索的唯一权威参考。任何任务涉及非中国专利时，**必须先读本文件**，再构造检索式。
> `market=world` 与 `market=cn` 接受相同表面语法，但底层字段映射、分析器和数据覆盖存在实质差异。不能假定同式在两库具有相同召回率或精度。

## 1. 何时使用 world 库

| 场景 | 是否用 world | 说明 |
|---|---|---|
| FTO 目标国家含 US/EP/JP/KR/DE 等 | 是 | 逐国核验，`WO`/`EP` 不代表可执行国家权利 |
| 可专利性查新需覆盖国际现有技术 | 是 | 国际文献可能构成 X/Y |
| 技术调研需国际竞品/路线布局 | 是 | 配合多语言申请人检索 |
| 仅查中国专利 | 否 | 用 `market=cn`（默认） |
| 仅查中国申请人国内布局 | 否 | 用 `market=cn` |

命令行加 `--market world` 切换。客户端不会对 world 库的 IPC 做自动规范化（仅 CN 库自动），所有 world IPC 写法须手动预检。

## 2. CN vs world 字段支持对照表

| 字段前缀 | CN 库 | world 库 | 匹配方式 | 关键差异 |
|---|---|---|---|---|
| `AP=(申请人)` | 支持 | 支持（多语言） | match_phrase | world 库可用中/英/当地语言检索，见第 5 节 |
| `IPC=(分类号)` | 支持（自动规范化） | 支持（**不自动规范化**） | match + and | world 须手动预检紧凑/带空格两种写法，见第 4 节 |
| `PID=(公开号)` | 支持 | 支持 | term 精确 | 大小写不敏感 |
| `AN=(申请号)` | 支持 | **不支持（无数据）** | match_phrase | world 库查询返回 0 条 |
| `AD` / `PD` | 支持 | 支持 | range | 语法相同 |
| `NOT=(排除)` | 支持 | 支持 | must_not | |
| `CC=(国家代码)` | **不支持** | 支持（仅 world） | prefix | 按公开号前缀两位过滤，见第 3 节 |

## 3. 国家/地区代码 CC=（仅 world 库）

基于公开号（`pid`）开头的两位国家代码做前缀匹配，大小写不敏感。

```
CC=(US)                             # 只看美国专利
CC=(US OR EP)                       # 美国 + 欧洲
CC=(US OR EP OR JP OR KR)           # 美/欧/日/韩
battery management CC=(US) IPC=(H01M)   # 关键词 + 国家 + IPC 组合
```

常用代码：

| 代码 | 国家/地区 | 代码 | 国家/地区 |
|---|---|---|---|
| US | 美国 | WO | PCT 国际申请 |
| EP | 欧洲 | JP | 日本 |
| KR | 韩国 | DE | 德国 |
| GB | 英国 | FR | 法国 |
| CA | 加拿大 | AU | 澳大利亚 |

- 多个国家用 `OR` 连接，不支持 `AND`（一件专利只有一个国家代码）
- `WO` 不是可执行国家权利，`EP` 也不能替代逐个生效国分析（FTO 必须逐国核验）
- `CN` 代码在 world 库可能存在，但通常直接用 `market=cn` 库更合适

## 4. IPC 分类号在 world 库的使用

**关键差异（2026-08-08 实测验证）**：CN 库偏好**带空格**写法（`H01M 10/0525`），客户端会自动把紧凑写法规范化为带空格；**world 库偏好紧凑写法**（`H01M10/0525`），带空格写法实测返回 0 条。

| 写法 | CN 库 | world 库（实测） |
|---|---|---|
| `IPC=(H01M10/0525)` 紧凑 | 客户端自动转为带空格 | **✅ 有命中**（推荐） |
| `IPC=(H01M 10/0525)` 带空格 | ✅ 原生格式 | **❌ 返回 0 条** |

world 库客户端**不做** IPC 自动规范化，因此紧凑写法是 world 库的首选。但不同 IPC 分类的存储格式可能不统一，复合式前仍建议预检：

```bash
# 第一步：紧凑写法预检（world 库首选）
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M10/0525)" --market world --page-size 3

# 第二步：若紧凑写法为 0，再试带空格写法
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M 10/0525)" --market world --page-size 3

# 第三步：若两种均为 0，回退到上位组（紧凑写法）
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M10)" --market world --page-size 3
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M)" --market world --page-size 3
```

注意：world 库返回的 `ipcs` 字段是多层级展开格式（如 `H | ELECTRICITY | H01 | ... | H01M | ...`），不是紧凑或带空格的单一格式。上述差异仅影响**检索式输入**，不影响返回展示。

**重要**：world 库 IPC 预检必须覆盖 CN 库预检过的**所有相关分类**，不得遗漏。例如 CN 库预检了 H01R 和 F16L 两个分类，world 库也必须分别预检这两个分类——不同分类覆盖不同技术角度，遗漏会导致国际文献召回不全。

常用 IPC 速查：

| 领域 | 代码 | 领域 | 代码 |
|---|---|---|---|
| 电池 | H01M | 通信 | H04L, H04W |
| 储能/充电 | H02J | 生物医药 | A61K, A61P |
| 人工智能 | G06N | 机器人 | B25J |
| 图像处理（软件） | G06T, G06V | 光学 | G02B |
| 图像采集（硬件） | G03B, H04N23 | 半导体 | H01L |
| 自动驾驶 | B60W, G05D1 | | |

## 5. 检索语言策略：优先英文

**核心原则：world 库检索应优先使用英文关键词。** 这一结论基于 2026-08-08 对 6 国（US/EP/JP/KR/TW/WO）专利的实测验证。

### 5.1 字段存储语言矩阵（实测验证）

world 库对不同国家的专利，各字段的存储语言如下：

| 国家 | title | abstract | claims | description | applicant |
|---|---|---|---|---|---|
| US | English | English | English | English | English |
| EP | English | English | English | English | English |
| JP | **English** | **English** | **Japanese** | **English** | 英文/日文混合 |
| KR | **English** | **English** | **Korean** | **English** | 英文/韩文混合 |
| TW | **English** | **English** | **中文** | **English** | 英文/中文混合 |
| WO | **English** | **English** | **当地语言** | **English** | 多语言混合 |

关键发现：
- **title、abstract、description 100% 英文存储**——无论原始专利来自哪个国家
- **claims 保持当地语言**——JP 的 claims 是日文，KR 是韩文，TW 是中文，US/EP 是英文
- **applicant 混合存储**——可能是英文（Toyota Motor Corp）、日文（株式会社村田製作所）、韩文（삼성）、中文（比亚迪股份有限公司）等

### 5.2 为什么优先英文检索

1. **覆盖面最广**：英文关键词可命中 title/abstract/description 三个字段，覆盖所有国家的专利
2. **无需猜测当地语言**：不需要把技术术语翻译成日文/韩文/中文
3. **命中量充足**：实测英文 "solid-state battery" 达 10000 上限，与日文 "全固体電池" 相同
4. **前排质量高**：英文检索前排以 US 为主（数据最完整），日文检索前排以 JP 为主

### 5.3 当地语言作为补充

当地语言关键词主要用于以下场景：
- **核对 claims 中的特定术语**：JP/KR/TW 的 claims 是当地语言，需用当地语言检索才能命中权利要求中的术语
- **补充召回当地语言变体**：某些技术术语在英文中可能有多种表述，当地语言可能有更精确的对应词
- **检索当地语言申请人**：`AP=` 字段可能是当地语言存储

```bash
# 第一步：优先英文检索（覆盖面最广）
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery electrolyte" --market world --page-size 20

# 第二步：如需核对 JP 专利的 claims，补充日文关键词
python3 <skill-dir>/scripts/patseek_client.py bool "全固体電池" --market world --page-size 10

# 第三步：英文 + 当地语言 OR 组合（最大化召回，但注意可能触达上限）
python3 <skill-dir>/scripts/patseek_client.py bool "(solid-state battery OR 全固体電池 OR 固态电池)" --market world --page-size 20
```

### 5.4 关键词语言对命中量的影响（实测）

| 关键词语言 | 检索式 | 命中量 | 前3条国家 |
|---|---|---|---|
| 英文 | `solid-state battery` | 10000（上限） | US, US, WO |
| 日文 | `全固体電池` | 10000（上限） | JP, WO, JP |
| 中文 | `固态电池` | 9141 | WO, WO, WO |
| 英文+日文 OR | `(solid-state battery OR 全固体電池)` | 10000（上限） | WO, WO, JP |

说明：
- 英文和日文均达上限，但英文检索前排以 US 为主（数据更完整），日文以 JP 为主
- 中文命中量略少（9141），前排以 WO（PCT 中文申请）为主
- **建议：常规检索用英文；需覆盖 JP claims 或中文 PCT 申请时补充当地语言**

## 6. 申请人多语言检索

**world 库的申请人字段和关键词均支持多语言**（2026-08-08 实测验证）。同一申请人可能以中文、英文、当地语言多种形式存储，应分别尝试后按 PID 合并去重。

### 6.1 申请人多语言检索

以"丰田"为例：

```bash
# 中文写法（实测可命中日文申请人"丰田自动车株式会社"）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(丰田) battery" --market world --page-size 5

# 英文写法（实测可命中"Toyota Motor Corp"）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(Toyota Motor) battery" --market world --page-size 5

# 日文写法
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(トヨタ) battery" --market world --page-size 5

# 韩文写法（实测 AP=(삼성) 命中"삼성 관 주식회사"，78 条）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(삼성) display" --market world --page-size 5

# 多语言组合 OR（推荐写法）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(丰田 OR Toyota OR トヨタ) battery" --market world --page-size 20
```

### 6.2 关键词多语言检索

world 库**不仅申请人支持多语言，关键词也支持**。中文、日文关键词均可命中对应语言的专利文献：

```bash
# 中文关键词（实测"固态电池"命中 9141 条，含 WO 申请）
python3 <skill-dir>/scripts/patseek_client.py bool "固态电池" --market world --page-size 5

# 日文关键词（实测"全固体電池"命中 10000 条上限，含 Toyota、日本碍子等）
python3 <skill-dir>/scripts/patseek_client.py bool "全固体電池" --market world --page-size 5

# 中英日组合检索（推荐用于国际查新）
python3 <skill-dir>/scripts/patseek_client.py bool "(固态电池 OR solid-state battery OR 全固体電池) CC=(US OR JP)" --market world --page-size 20
```

注意事项：
- 多个申请人用 `OR` 连接，不支持 `AND`
- 全称/简称效果可能不同，分别尝试
- 名称须与数据库存储一致，match_phrase 匹配
- 竞品分析时必须将同一主体的多种名称变体分别检索，按 PID/同族合并去重，不得选择命中最多的单一名称代表全部布局
- world 库包含 PCT 申请中的中文申请人（如"中国科学院物理研究所"、"比亚迪股份有限公司"），中文关键词可命中这些文献

### 6.3 外国公司跨国检索（实测验证）

分析外国公司的全球专利时，须同时检索 CN 和 world 库，且两库名称格式可能不同：

```bash
# CN 库用英文原名检索外国公司（中文名可能命中错误实体）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(NVIDIA) IPC=(G06N)" --page-size 20

# World 库用简称和全称分别检索（简称命中量可能比全称高 20 倍）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(NVIDIA) IPC=(G06N)" --market world --page-size 20
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(Nvidia Corporation)" --market world --page-size 20

# 合并两库结果后按 PID 去重
```

> **⚠️ 外国公司中文名慎用**：`AP=(英伟达)` 在 CN 库命中的是"英伟达(江苏)机床有限公司"（机床厂），不是 NVIDIA。`AP=(英伟达有限公司)` 返回 0 条。**外国公司检索优先用英文原名**，用中文名时必须核对 `applicant` 字段。详见 `technology_research_workflow.md`"跨国公司全球专利检索策略"。

## 7. 可直接复制的检索式示例

以下示例经过实测验证（2026-08-08），均可直接使用。

> **检索策略提示**：world 库 QX 三块组合检索容易触达 10000 上限。**建议优先加 `CC=(主要目标国)` 限定**，可大幅提升精度（实测从 5287 条降到 379 条，精度提升 14 倍）。FTO 检索时 CC 限定还可确保只看目标法域专利。

### 7.1 单字段检索

```bash
# 纯英文关键词
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery" --market world --page-size 20

# 国家限定
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery CC=(US)" --market world --page-size 20

# IPC 限定（须先预检写法）
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery IPC=(H01M)" --market world --page-size 20

# 申请人限定（英文）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(Toyota Motor) battery" --market world --page-size 20

# 申请人限定（中文，可命中日文申请人）
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(丰田) battery" --market world --page-size 20

# 精确公开号
python3 <skill-dir>/scripts/patseek_client.py bool "PID=(US10234567B2)" --market world --page-size 5

# 日期限定
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery AD>=2023" --market world --page-size 20

# 排除
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery NOT=(lithium)" --market world --page-size 20
```

### 7.2 组合检索

```bash
# 关键词 + 国家
python3 <skill-dir>/scripts/patseek_client.py bool "battery management system CC=(US OR EP)" --market world --page-size 20

# 关键词 + IPC + 国家
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery IPC=(H01M) CC=(US OR JP)" --market world --page-size 20

# 申请人 + IPC + 日期
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(Toyota Motor) IPC=(H01M) AD>=2022" --market world --page-size 20

# 三块组合（对象 × 机制 × 区别特征）+ 国家
python3 <skill-dir>/scripts/patseek_client.py bool "(solid-state battery) (thermal management) (phase-change material OR cooling channel) CC=(US OR EP)" --market world --page-size 20

# 申请人 + 三块组合 + 排除
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(Toyota Motor OR Samsung) (solid-state battery) (electrolyte interface) NOT=(lithium)" --market world --page-size 20

# 多语言申请人 + 关键词 + IPC
python3 <skill-dir>/scripts/patseek_client.py bool "AP=(丰田 OR Toyota OR トヨタ) (solid-state OR all-solid) IPC=(H01M)" --market world --page-size 20
```

### 7.3 翻页

```bash
# 正常翻页，不触发近似检索拦截
python3 <skill-dir>/scripts/patseek_client.py bool "solid-state battery CC=(US)" --market world --page 2
```

## 7.5 返回字段差异（2026-08-08 实测验证）

world 库不同检索方式返回的字段集不统一，下表基于 18 个实测 case 汇总：

| 检索方式 | 返回字段 | 关键差异 |
|---|---|---|
| `PID=` 精确检索 | abstract, appdate, applicant, appnum(空), claims, **description**, figures, ipcs, pid, pubdate, title | **含 description**（说明书全文） |
| 普通关键词 Bool | abstract, appdate, applicant, appnum(空), cited_cnt, claims, ipcs, pid, pubdate, title（部分含 figures） | **无 description**；cited_cnt 部分有 |
| 专利详情 `patent` 命令 | 上述全部 + **enrichment** + **aggregation** | 含发明人、法律状态、同族等增强字段 |

关键说明：
- **Bool 检索不返回 description**：需要说明书全文时用 `patent` 命令调详情
- **字段不统一**：同一批结果中，有些专利有 `figures`/`cited_cnt`，有些没有（取决于数据源覆盖）
- **appnum 始终为空**：world 库申请号字段无数据，`AN=` 检索返回 0 条
- **enrichment 完整**：world 库专利详情支持 enrichment，含 inventors、legal_status、family_count、citation_count、priority_date、pdf_url 等
- **0 结果仍扣积分**：Bool 检索返回 0 条时仍扣 1 积分（实测确认）

enrichment 字段示例（world 库 `US10234567B2` 详情）：
```
inventors: ['Yun Young Kim']
legal_status: Active
family_count: 3
citation_count: 12
priority_date: 2016-02-19
aggregation.status: complete
```

## 8. world 库零结果四层探针

world 复合式返回 0 条时，**不得直接判定目标国家无专利**。必须依次执行四层预检，只有各层均返回可核对样本后才能组合；任一层为 0 时记录字段/语言/表达式待修复。

```bash
# 第一层：对象词 + CC
python3 <skill-dir>/scripts/patseek_client.py bool "<对象词> CC=(目标国)" --market world --page-size 5

# 第二层：核心机制/关系词 + CC
python3 <skill-dir>/scripts/patseek_client.py bool "<机制词> CC=(目标国)" --market world --page-size 5

# 第三层：IPC 子类 + CC
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M) CC=(目标国)" --market world --page-size 5

# 第四层：准确 IPC 主组（world 库首选紧凑写法，带空格为备选）+ CC
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M10/0525) CC=(目标国)" --market world --page-size 5
# 若紧凑写法为 0，再试带空格
python3 <skill-dir>/scripts/patseek_client.py bool "IPC=(H01M 10/0525) CC=(目标国)" --market world --page-size 5
```

任一层为 0 时记录"该字段/语言/表达式待修复"，禁止将复合式 0 条用于 FTO 排除、低密度或技术空白结论。**注意：0 结果仍扣 1 积分**（实测确认），探针时控制调用次数。

## 9. world 库行为特征（2026-08-08 实测验证）

### 9.1 结果上限

world 库宽泛检索极易触达 10000 条显示上限。实测 18 个 case 中有 12 个触达上限。达到上限时：
- 当前命中数不可用于统计或份额分析
- 必须增加关键区别特征（结构/步骤关系、特定部件、控制逻辑或参数）
- 优先配合已验证 IPC 或日期后重检
- `CC=` 单国过滤可显著减少命中（实测 `perovskite solar cell` 从 10000 降到 `CC=(JP)` 的 6960），但仍可能达上限

### 9.2 限流

- Bool 检索名义 30 次/分钟，但实测滚动窗口更严（约 10 次/分钟后开始 429）
- 连续检索建议间隔 8 秒以上（批量探针时每批不超过 6 个，批间隔 15 秒）
- 触发 429 后客户端自动指数退避重试 3 次（1s/2s/4s）
- 429 错误信息为 `Rate limit exceeded: 10 per 1 minute`

### 9.3 申请号字段

`AN=` 在 world 库**无数据**（实测所有结果 appnum 字段均为空字符串），查询返回 0 条。需要按申请号查国际专利时：
- 改用公开号 `PID=` 检索
- 或用申请人 + 关键词 + IPC 组合召回后人工筛选

### 9.4 精确短语

world 库精确短语（如 `"liquid cushion"` 加引号）疑似不保证 match_phrase，可能按分词处理。不得把引号当作精确短语保证，须以前排原文核对为准。

## 10. 国际多语言路径独立验收

每条多语言路径（英文/日文/韩文/中文等）必须独立验收，不得互相背书：

| 验收项 | 通过标准 |
|---|---|
| 语言 | 记录原始术语和回译 |
| 国家前缀核验率 | 抽样前 10 篇的 CC 与目标国一致率 |
| 样本精确率 | 抽样中技术相关比例 |
| 关键特征可观察率 | 目标特征在前 10 原文中可定位比例 |

- 当地语路径关键特征可观察率低于 50% 时，只可取词或修订翻译，不得以英文路径结果替它背书
- 英文、日文、韩文等路径的原始命中数不得相加或互相替代
- 仅把达到相同技术边界和质量门的路径合并为"多语言已覆盖"

## 11. 与 CN 库的协同检索策略

国际检索不应孤立进行，需与 CN 库协同：

1. **CN 库先行**：用 CN 库建立技术边界、提取术语和 IPC
2. **world 库扩展**：用提取的术语和 IPC 在 world 库验证国际覆盖
3. **多语言回译**：将 CN 术语回译为目标国语言，分别检索
4. **同族追踪**：CN 命中的关键文献，用其公开号在 world 库查同族成员
5. **语义补召回**：语义检索查询须用中文描述（实测结果含国际公开号），可先用语义在 CN 召回，再用术语回到 world 验证

## 12. 常见错误与纠正

| 错误 | 后果 | 纠正 |
|---|---|---|
| 忘记加 `--market world` | 检索 CN 库，国际文献全漏 | 任务涉及国际时必须加 `--market world` |
| world 库用 `AN=` 查申请号 | 返回 0 条（appnum 字段始终为空），误判无专利 | 改用 `PID=` 或申请人+关键词组合 |
| world 库用带空格 IPC（如 `H01M 10/0525`） | **实测返回 0 条**（world 库偏好紧凑写法） | world 库首选紧凑写法 `H01M10/0525`；预检时先试紧凑 |
| 只用英文检索日本/韩国申请人 | 遗漏当地语言存储的专利 | 同时尝试中文/英文/当地语言（日文/韩文均实测有效） |
| **world 库优先用当地语言而非英文检索** | **遗漏大量专利**（title/abstract/description 100% 英文，当地语言只覆盖 claims） | **优先英文检索**；需核对 JP/KR/TW 的 claims 时再补充当地语言 |
| 只用英文关键词检索国际专利 | 遗漏中文/日文 PCT 申请 | 英文为主；中文/日文关键词作为补充（实测"固态电池"9141条、"全固体電池"10000条） |
| world 复合式 0 条直接下结论 | 漏判国际现有技术 | 执行四层探针后再判断（注意 0 结果仍扣 1 积分） |
| 把 `WO`/`EP` 当作可执行国家权利 | FTO 误判 | 逐国核验生效成员 |
| 宽泛检索 10000 条直接用 | 统计失真（实测 12/18 case 触达上限） | 增加 `CC=`/IPC/日期/三块组合收窄，不用于份额分析 |
| Bool 检索期待返回 description | 拿不到说明书全文 | **后台已更新（2026-08-09）**：Bool 命中 **<10 条时直接返回 description**（cn/world 一致），≥10 条不返回。仍需单篇全文时用 `bool "PID=(公开号)" --market world`（覆盖最全，含 DE/KR）；详情接口是子集（WO/EP/US/JP/FR/GB 可，DE/KR 返回空）。**注意：即使 <10，个别专利仍缺/空 description**（如 GB `D0` 检索报告类实测空串）——空态回退 Google Patents/官源。详见 `api_reference.md` §1/§2 |
| 连续快速 Bool 超过 10 次/分 | 触发 429（实测硬限 10 次/分钟） | 客户端已按 6.5s 间隔自动节流（≈9.2 次/分）；批量每批不超 6 个、批间停顿；详情接口独立计数 |
