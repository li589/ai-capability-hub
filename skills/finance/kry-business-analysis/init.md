# 客如云经营参谋执行规则

## 执行总览

本文是规则源，不表示所有任务都必须执行全部步骤。先按任务类型选择流程：

| 步骤           | 适用条件                                         |
| -------------- | ------------------------------------------------ |
| 初始化         | 默认执行：检查 kry-cli、选择品牌和门店；         |
| 取数           | 需要接口数据时执行；已注册接口必须通过 fetch.mjs |
| 构建组件数据   | 预制场景 HTML 报告执行；自由查询按需执行         |
| 渲染 HTML 报告 | 用户需要 HTML 报告或任务要求交付 HTML 时执行     |
| 报告质检       | 只要生成或修改 HTML 报告就执行                   |
| 安全红线       | 所有任务始终适用                                 |

---

## 步骤 1 · 初始化

### 1.1 检查 kry-cli

Windows：

```bash
where.exe kry-cli
```

- powershell 中使用 `cmd /c 完整可执行文件目录\kry-cli.cmd <参数>`。
- cmd 中使用 `完整可执行文件目录\kry-cli.cmd <参数>`。

macOS / linux：

```bash
kry-cli --help
```

未安装时执行：

```bash
npm i @keruyun/cli@latest -g --registry=https://registry.npmmirror.com --foreground-scripts --loglevel error
```

### 1.2 初始化上报

检查或安装 kry-cli 后执行：

```bash
node scripts/init-report.mjs
```

该脚本上报当前技能名。

### 1.3 获取品牌

```bash
kry-cli brand
```

- 只有一个品牌时直接使用。
- 多个品牌时让用户选择品牌。

### 1.4 获取门店列表

```bash
kry-cli shop
```

- 用户指定门店范围时，先验证门店是否在列表中。
- 禁止自行扩大、缩小或替换用户指定的门店范围。
- 需要门店参数时，将 shopIds 集合传入请求参数。

---

## 步骤 2 · 取数

### 2.1 日期口径

使用 `kry-cli date` 获取今天日期、当前时间和日期计算规则，再计算用户指定日期。

- 用户说「今天」只查今天。
- 用户说「昨天」只查昨天。
- 用户给出具体日期只查该日期。
- 无数据时报告「该日期暂无数据」，询问是否改查其他日期。
- 禁止擅自切换到其他日期查询。

### 2.2 调用方式决策

执行任何 API 前，先读取 `scripts/constraints.json` 判断接口是否已注册。

| 条件                             | 调用方式                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------- |
| 接口已注册在 constraints.json    | `node scripts/fetch.mjs --api <路径> -b <brandId> -d '<JSON>' -o <output.json>` |
| 场景文件标注 `fetchMode: script` | `node scripts/fetch.mjs --api <路径> -b <brandId> -d '<JSON>' -o <output.json>` |
| 以上均不满足                     | `kry-cli call <路径> -b <brandId> -d '<JSON>'`                                  |

已注册接口 **必须通过 fetch.mjs** 获取，禁止用 kry-cli call 手动拆日期、门店或分页循环。

### 2.3 自由查询参数构造

自由查询禁止凭经验手写参数。调用 fetch.mjs 前按以下顺序构造请求体：

1. 执行 `kry-cli view <接口路径>` 查看官方参数示例。
2. 查阅 `references/field-map/_spec.md` 的请求参数常见错误。
3. 查阅接口所属 field-map 文件，确认字段路径、金额单位和易混字段。
4. 只在官方示例或 `constraints.json` 的 `defaultParams` 基础上补日期、门店、分页和查询维度。
5. 不确定字段名、字段类型或嵌套结构时，先确认再调用，禁止猜字段。

### 2.4 fetch.mjs 用法

```bash
node scripts/fetch.mjs --api <接口路径> -b <brandId> -d '<完整参数JSON>' -o <输出文件>
```

- fetch.mjs 内部处理日期拆分、门店分批和自动翻页。
- fetch.mjs 会在调用后端前做本地参数校验；结构错误会返回 `rejected=true`，并提示先核对 `kry-cli view` 与 field-map。
- 同一接口可按不同查询维度多次调用，例如 BY_BRAND 与 BY_SHOP 分别取数。
- 始终把用户要求的完整日期范围传入 `-d`，由 fetch.mjs 根据约束内部拆分。
- 禁止预先拆分日期/门店后多次绕行调用。

### 2.5 fetch.mjs 输出判定与重试

fetch.mjs 输出以 `rejected` 为第一判定字段：

| 状态          | 关键字段                                                                                                   | 处理方式                                                |
| ------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 成功          | `{ api, rejected:false, fetchedAt, strategies, totalCalls, totalRecords, declaredTotal, data, elapsedMs }` | 使用 `data` 进入构建流程                                |
| 预检/超时拒绝 | `{ api, rejected:true, reason, suggestion, totalCalls, totalRecords:0, data:[], elapsedMs }`               | 不重试、不手动拆分；HTML 中展示失败原因、建议和空态卡片 |
| 部分失败      | 成功结构 + 可选 `{ errors, coverage }`                                                                     | 读取 `errors[].reason`，修正参数后最多重试 2 次         |
| 无数据        | `rejected=false` 且 `totalRecords=0` 或 `data=[]`                                                          | 按无数据处理，生成空态卡片，不编造数字                  |

`errors` 和 `coverage` 不是稳定必有字段，只能作为出现时的辅助诊断信息。

### 2.6 大数据量预检

fetch.mjs 使用三类保护：Tasks 预检、首页预检、200 秒超时兜底。预检拒绝不是接口错误，不重试，不手动拆分绕过限制。

AI 行为规则：门店数 > 200 且查套餐统计时建议选择部分门店；菜品明细月度全量建议使用中类统计；1000+ 门店品牌优先使用 BY_BRAND 聚合维度。

### 2.7 kry-cli call 直接调用

仅未注册在 `constraints.json` 中的接口可使用 kry-cli call：

- 品牌授权：`kry-cli call <接口路径> -b <brandId> -d '<JSON>'`。
- 门店授权：`kry-cli call <接口路径> -s <shopId> -d '<JSON>'`。
- 数据量过大或门店超过 10 家时，使用 `-o <tempFilePath>` 保存到临时文件。

### 2.8 字段取数

- 参照 `references/field-map/` 中定义的字段路径取值，禁止自行推断字段含义。
- 金额单位按接口契约处理：订单/团购对账接口为「分」时需 ÷100，报表类接口为「元」时直接展示。
- 遇到易混字段时，按字段契约中的「易混字段对照」选择。
- 取数后执行交叉校验，校验不通过时标记数据异常并降级展示。

---

## 步骤 3 · 构建组件数据

取数完成后、渲染 HTML 报告前，用 report-data.mjs 把原始接口数据确定性转为组件数据，避免 AI 心算。

### 3.1 工作流

1. fetch.mjs 拉数时，用 `-o <data-dir>/<文件名>.json` 按场景 manifest 的 `sources` 保存到同一目录。
2. 运行构建命令：

```bash
node scripts/report-data.mjs build --manifest scripts/manifests/<场景>.mjs --data-dir <数据目录> --out report-data.json
```

3. 输出 `{ meta, components, facts }`。
4. `components` 填充 HTML 组件，`facts` 作为洞察文本的唯一数据依据。
5. 库缺函数时先补 report-data.mjs，并运行 `node scripts/report-data.mjs --test`。

### 3.2 manifest 约定

- 每个场景一个 `scripts/manifests/<场景>.mjs`。
- 结构为 `export default { scene, sources, build(lib, data) }`。
- `sources` 声明逻辑名到 fetch 产物文件名的映射，例如 `{ brand: 'income_brand.json' }`。
- `build(lib, data)` 返回 `{ meta, components, facts }`。
- 数据文件缺失时，对应板块自动降级，不中断整个 HTML 报告。

### 3.3 记录位置约定

| 接口                                           | 记录位置         |
| ---------------------------------------------- | ---------------- |
| income/v3/list                                 | `data[]`         |
| orderItem/list、itemType/list、department/list | `data[0].item[]` |
| 其余接口                                       | `data[]`         |

### 3.4 准确性要点

- income 顶层 `orderPeopleCnt`、`avgCustomerAmtAfterDiscount`、`avgCustomerAmtPreDiscount` 在 BY_BRAND/BY_SHOP 聚合时可能为 null，真实值用 `lib.deriveIncomeMetrics()` 派生。
- combo/sale/statistics 结果可能混有 `{ totalSize }` 元数据行，消费前过滤 `comboName == null` 的脏行。
- groupCoupon 相关金额单位为分，展示前 ÷100 转元。
- booking/shopRanking 可能缺 shopName，展示时回退 `门店{shopId}`。

---

## 步骤 4 · 渲染 HTML 报告

### 4.1 通用规则

1. 数据定义遵守接口标题、功能描述、适用场景、请求参数和响应参数。
2. 数据槽位必须来自接口响应或 report-data.mjs 的确定性计算。
3. 洞察采用「条件 → 结论」表达，结论必须能追溯到 `facts`。
4. 报告结构按概览 → 专项 → 综合递进。
5. 输出单文件、可直接在浏览器打开的 HTML 报告。

全部 API 失败时仍输出 HTML 报告，但只能展示查询范围、失败原因、空态卡片和缩小范围建议；禁止填充经营数字、趋势、排名、洞察结论或经营建议。

### 4.2 标准渲染路径

标准路径使用 `references/scenes/charts/` 下的分层组件体系：

1. 先按步骤 3 产出 `report-data.json`。
2. 复制 `references/scenes/charts/report-shell.html` 作为 HTML 起点。
3. 根据场景需要读取 `components/` 下的图表、卡片和表格组件。
4. 用 `report-data.json` 的 `components` 替换组件数据槽位。
5. 用 `facts` 生成洞察和行动建议。
6. 配色和图表类型以 `references/scenes/charts/_chart-registry.md` 为准。

### 4.3 自定义渲染路径

商户明确要求个性化配色、布局或新图表类型时，可以使用自定义 HTML：

- 可在 shell 基础上覆盖 CSS 变量。
- 可手写组件库未覆盖的新板块。
- 可完全手写 HTML。

自定义 HTML 仍必须通过报告质检中的技术正确性检查。

### 4.4 ECharts 数据绑定

1. `_chart-registry.md` 中的 `{{placeholder}}` 只是数据插槽，最终 HTML 必须替换为真实值。
2. `<script>` 内必须是可执行 JavaScript，`series[].data`、`xAxis.data`、`legend.data` 使用具体数组字面量。
3. 禁止残留服务端模板语法，例如 `json.dumps()`、f-string、`${}`、`{% %}`、`<?= ?>`。
4. 场景声明的图表类型必须用对应 ECharts 渲染；无数据时展示「暂无数据」空态卡片，禁止空图表容器或空 `<tbody>`。
5. 用户明确要求「图表、数据图表、趋势、对比、占比、排行、分布」时，HTML 必须包含 ECharts CDN、`.chart-box` 容器和 `echarts.init` 或 `KRY.xxx` 初始化；禁止只用纯表格、列表或文字替代任务明确要求的数据图表。
6. 自定义 HTML 也必须遵守 ECharts 数据图表规则；只有用户明确要求纯文本/表格，或接口无数据并已展示空态说明时，才可不生成 ECharts 图表。
7. **数据契约红线（防图表白屏）**：填充图表数据时必须**直接内联 `report-data.json` 里 `components.<组件>` 的数组**，严格按 `references/scenes/charts/components/_usage.md` 速查表结构取字段，**禁止自造 helper 函数猜数据结构**。典型错误：`bar-ranking` 返回 `{categories:[名称], values:[数值]}` 两个**平行数组**，误当对象数组写 `data.values.map(v => v.name)` 会得到 `[null,null,...]` → 全白屏；正确应 `yAxis.data = xxx.categories`、`series.data = xxx.values`。

---

## 步骤 5 · 报告质检

### 5.1 脚本执行

生成 HTML 报告后运行：

```bash
node scripts/check-report.mjs <报告路径>
```

也可显式指定模式：

```bash
node scripts/check-report.mjs <报告路径> --mode standard
node scripts/check-report.mjs <报告路径> --mode custom
```

退出码规则：

- `0`：无 ERROR，可交付；如有 WARN，按人工确认规则处理。
- `1`：存在 ERROR，修复后重跑。
- `2`：参数错误或文件不存在，修正命令后重跑。

### 5.2 检查模式

| 模式     | 触发方式                                            | 检查范围                                                                                         |
| -------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| standard | 标准组件 class 命中 ≥3 类，或显式 `--mode standard` | 占位符、占位注释、空表格、图表容器配对、空数据图表、JS 语法、未定义变量、HTML 结构、内容数量统计 |
| custom   | 未命中标准模板，或显式 `--mode custom`              | 占位符、空表格、空数据图表、HTML 结构、JS 语法、通用图表 DOM 引用配对                            |

custom 模式不检查标准模板专属规范，例如组件 class、占位注释和内容数量统计。内容数量仅作为统计信息，具体 KPI 卡片、洞察和行动建议是否充分，由 AI 结合报告场景、用户问题和数据复杂度判断，不设置固定数量阈值。

### 5.3 ERROR 与 WARN

| 类型  | 含义                                        | 处理方式                                 |
| ----- | ------------------------------------------- | ---------------------------------------- |
| ERROR | 会导致数据错误、图表白屏、HTML 无法正常展示 | 修复后重跑，直到退出码为 0               |
| WARN  | 可能存在体验问题，也可能是已知误报          | 人工确认；确认合理时记录原因，不机械修复 |

内容数量统计不作为 WARN 阈值判断。脚本只展示 KPI 卡片、核心洞察、行动建议和 hero-highlight 数字数量，具体多少合适由 AI 结合报告场景判断。

### 5.4 人工核对

脚本通过后，还需核对机器无法判断的业务语义：

- 金额、数量、比例是否在业务合理区间。
- 环比/同比是否有真实对比期支撑。
- 洞察和行动建议是否能追溯到 `facts`。
- 降级或数据缺失是否在 HTML 报告末尾说明。

---

## 步骤 6 · 安全红线

- **禁止绕过 fetch.mjs**：凡 `scripts/constraints.json` 中已注册的接口，只能通过 `node scripts/fetch.mjs` 执行。
- **禁止编造数据**：所有数字必须来自真实接口响应或 report-data.mjs 的确定性计算。
- **禁止编造经营建议**：建议必须基于真实数据和 `facts` 推导。
- **禁止编造环比/同比**：没有真实对比期时不展示环比/同比。
- **禁止跳过门店选择**：需要 shopIds 时必须使用用户确认的门店范围。
- **禁止代替商家执行操作**：只提供分析建议，不执行业务操作。
- **信息保密**：不输出接口地址、路由决策过程和工具内部细节。
-**敏感信息保护**：手机号等敏感信息需脱敏展示。
- **报告质检不可跳过**：任何 HTML 报告交付前都要完成步骤 5。
