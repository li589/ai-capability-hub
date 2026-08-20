# 可视化、作图与生图

本模块约束科研图形的科学正确性、信息层级、可读性和交付质量。用户或目标期刊/会议的实际要求优先；下述色板与尺寸是可复用起点，不得宣称为期刊官方标准。

分清两类图，二者规则完全不同：

- **数据图**：由真实数据计算得到（KM 曲线、森林图、ROC、火山图、热图、PCA/UMAP、箱线图等）。必须用作图代码从数据生成，**绝不能用 AI 文生图**。
- **示意图**：不承载数据的概念/机制/流程图、图形摘要、封面配图。可用绘图工具或（谨慎地）AI 文生图生成草稿。

## 一、先冻结图形契约

作图前记录用途/读者、目标载体和最终尺寸、`analysis_id`/`report_state`、分析单位与分母、视觉编码、必要不确定性、输出格式和一句话 Take-Home。Take-Home 必须在结果核验后提炼，不能先写结论再挑数据；探索性图用描述性标题，不写成确认性机制。

用户已给足信息时直接执行；只有用途、尺寸或视觉选择会实质改变产物且无法从上下文判断时，才给出简短 brief 请求确认，不强制每次填写偏好卡片。

## 二、数据图：类型与必标项

按“问题→图型”选择，并附带该图型的必要标注，主动对常见误用给出提示。

| 问题/数据 | 首选图 | 必标项 | 常见误用（需规避/提示） |
|---|---|---|---|
| 时间到事件 | Kaplan–Meier | 各时点风险集人数、删失标记、95%CI、随访轴、事件定义、HR/log-rank | 缺 number at risk；未检验比例风险；有竞争风险仍用 KM 而非累积发生 |
| 效应合并/亚组 | 森林图 | 点估计+CI、权重、合并菱形、异质性（I²/τ²）、效应类型、无效线 | 亚组“显著/不显著”对比而无交互检验；异质性高强行合并 |
| 二分类判别 | ROC | AUC+95%CI、样本/事件数、训练还是验证集、对角线 | 只报 AUC 不看校准；极不平衡用 ROC 而非 PR；训练集报性能 |
| 预测概率可靠性 | 校准曲线 | 预测 vs 实测、理想对角线、截距/斜率、Brier | 仅用 Hosmer–Lemeshow 代替可视化；不报斜率/截距 |
| 临床决策价值 | 决策曲线（DCA） | 净获益 vs 阈值概率、treat-all/none 参考线、合理阈值范围 | 阈值范围不合理；不与参考策略对比 |
| 差异表达 | 火山图 | log2FC、-log10(校正 p)、双阈值线、多重校正方法、上下调计数 | 用未校正 p；只按 p 不设 FC 阈值；事后调阈值 |
| 表达/丰度模式 | 热图 | 是否按行 z-score、聚类方法与距离、行列注释、数据变换 | 未说明标准化致误读；配色不对称误导 |
| 高维结构 | PCA / UMAP | PCA 方差解释比；UMAP 注明仅可视化、参数（n_neighbors/min_dist）、着色变量、预处理 | 把 UMAP 簇间距离/大小当定量结论 |
| 组间分布 | 箱线/小提琴+散点 | n、叠加原始点、检验方法与配对性、箱须定义、多重校正 | 小样本用箱线掩盖分布；技术重复当生物学重复 |
| 方法一致性 | Bland–Altman | 差值 vs 均值、偏倚与 95% LoA 及其 CI、比例偏倚 | 用相关系数代替一致性；忽略异方差 |
| 受试者流程 | CONSORT/STROBE 流程图 | 各阶段人数与排除原因、人数守恒 | RCT 与观察性用错模板；人数对不上 |

所有数据图统一要求：标注样本量/分母、单位、置信区间、模型与校正；不截断或选择坐标轴夸大差异；正式图保留源数据或确定性生成记录；提供可访问的替代文本。发表级图型按目标报告规范对照标注（诊断/预测对 TRIPOD+AI，试验对 CONSORT，观察性对 STROBE）。

## 三、视觉系统与导出

- **语义优先**：一张图回答一个主要问题；标题/Take-Home 是数据支持的完整观点句，图例再说明对象、方法、分母和不确定性。多面板共享字体、线宽、术语、颜色语义和可比较尺度。
- **方向准确**：机制图中激活用箭头、抑制用 T 形端；假设或未验证关系用虚线并明确标注。按已知证据表达分子、细胞、方向和因果层级，不因构图需要补画无证据通路。
- **颜色可访问**：分类色优先不超过 4 个；确需更多类别时优先分面、直接标签或从稳定色板中选 5–6 个高区分色。颜色不得是唯一通道，同时使用形状、线型、纹理或文字。避免红绿单独编码关键对比，保持灰度可辨；连续量使用感知均匀且与数据中心匹配的色阶，禁用 Rainbow/Jet。
- **专家色板起点**：论文图可用深蓝 `#1b5ba4`、橙红 `#e95217`、琥珀 `#f7ab56`、石板灰 `#475569`；复杂信息图可从 `#1b5ba4 / #e95217 / #f7ab56 / #269c39 / #8dc151 / #da000e / #d0498a / #d3d6e8 / #ed6b89 / #69348d / #cfb0d3 / #8d180c` 中按语义选取最多约 5–6 色；海报/封面可用深蓝 `#1d52a1` 与深红 `#da000e` 为骨架。仅按明确语义分配并全图复用，不把颜色天然等同于“实验/对照”“激活/抑制”或“显著/不显著”；每次仍需实测对比度、灰度和色觉缺陷可辨性。
- **最终尺寸**：依据目标刊载/展示尺寸设置标签、图例、线宽、点大小、面板间距、裁切和中文字体。正文图标签通常至少约 7–8 pt，以目标规范为准。
- **可编辑主文件**：线条图、机制图和网络图优先保留 SVG/PDF 等矢量主文件；用户需要时另提供 PNG/TIFF。位图默认从 300 dpi 起步但不替代目标规范。使用 `fig{序号}_{核心发现关键词}` 等语义化文件名，不使用 `final_v2_final`。

图形摘要先把“核心主张 → 3–5 个必要元素 → 叙事路径”写成信息架构，再作图；不塞入完整方法、逐项统计或所有次要通路。海报/封面仅在用户明确要求且有已核验分析结果时生成，视觉隐喻不得改变科学含义。

## 四、用当前环境可用工具作图与输出

优先复用当前环境实际可用的表格、可视化、文档和报告工具；不要假设某个 Skill 名称必然存在。若没有专用工具，使用可审计的 R/Python/命令行代码完成，并保存数据、参数和环境。

含中文的图表使用环境中实际可用的中文字体与回退链，不硬编码未经确认的字体。图形及其本地资源写出后直接交付，不再打开、解析、检查、渲染、截图或预览。

## 五、AI 生图（文生图）边界与 query 优化

### 5.1 硬边界（先判断能不能生）

AI 文生图**只用于不承载事实的概念/示意/装饰**，且默认视为草稿。以下一律不得用文生图：

- 任何数据图（KM、统计图、ROC、火山图等）——AI 会编造数值；
- 精确解剖/组织/分子/蛋白结构、真实病理或显微图像、凝胶条带、影像学图片——存在事实错误与学术不端风险；
- 图中关键文字标签——文生图渲染文字易错，应生成无字版本后用矢量工具补标注。

发表用途须遵守目标期刊政策：主流期刊（如 Nature 系列）默认**不允许**发表生成式 AI 图像，个别例外须在图注中明确标注为“AI 生成” [Nature Portfolio AI 政策](https://www.nature.com/nature-portfolio/editorial-policies/ai)。专业机制图/通路图建议用 BioRender、Illustrator 等可精确控制的矢量工具。

### 5.2 query 结构（提高生图质量）

现代文生图模型偏好高度详细、结构化的 prompt [图像提示指南](https://help.openai.com/en/articles/8555480-dall-e-3-api)。按模块从主到次组织，帮助 agent 生成更好的图：

| 模块 | 作用 | 科研示意常用词 |
|---|---|---|
| 主体 | 画面主要对象 | cell, neuron, virus particle, signaling pathway |
| 风格 | 决定专业感 | scientific illustration, flat vector, clean line art, isometric, minimalist, textbook style |
| 构图 | 布局视角 | left-to-right flow, centered, cross-section, clear spatial hierarchy |
| 配色 | 色板 | soft pastel palette, limited 3-color scheme, blue-teal |
| 背景 | 背景处理 | plain white background, clean gradient, no clutter |
| 细节/光照 | 质感 | soft lighting, subtle shadows, smooth gradients |
| 技术参数 | 比例/清晰度 | high resolution, 1:1 或 16:9 |
| 负面提示 | 排除项 | no text errors, no gibberish, no realistic photo, no clutter, no watermark, avoid distorted anatomy |

构图遵循图形摘要惯例：单一清晰信息、从左到右叙事、删多余箭头与文字、留白充足 [Cell 图形摘要指南](https://www.cell.com/pb/assets/raw/shared/figureguidelines/GA_guide.pdf)。SDXL 类模型用独立 negative prompt 字段；DALL·E/GPT Image 类无独立负面框，用 “no…/without…” 自然语言表达 [图像提示指南](https://help.openai.com/en/articles/8555480-dall-e-3-api)。

### 5.3 可复用模板骨架（示意图，非数据图）

机制概念图（英文）：

```
A clean scientific illustration of [机制主体, e.g. a T-cell recognizing a tumor cell],
flat vector style, isometric view, no embedded text, soft pastel palette (blue and teal),
plain white background, subtle shadows, clear spatial hierarchy, textbook style, high resolution, 1:1.
No realistic photo, no text, no clutter, no watermark.
```

信号通路/流程（中文骨架）：

```
科学插画风格的[通路名称]示意图，扁平矢量风格，从左到右流程布局，
主体为[分子A]→[分子B]→[下游效应]，简洁箭头连接，柔和三色配色，纯白背景，
不嵌入文字，清晰层级关系，教科书插图质感，高分辨率，16:9。排除：写实照片、文字、多余装饰、水印。
```

图形摘要草稿（英文）：

```
A graphical abstract concept, minimalist scientific illustration, single clear message about [研究主题],
left-to-right narrative flow, isometric flat icons, limited color palette, generous white space,
clean and professional, no dense text, no chart, high resolution, landscape 16:9.
Avoid distorted shapes, avoid realistic microscopy imagery.
```

使用建议：生图视为草稿；正式发表前核对期刊 AI 政策并如实标注，用矢量工具替换文字与修正科学错误，绝不用于替代任何真实数据图或实验证据图。
