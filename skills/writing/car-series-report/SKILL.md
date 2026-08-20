---
name: car-series-report
description: 当用户查询某款车系的详细信息时触发此技能，包括但不限于：询问某车系的基础配置、车型信息、用户口碑、经销商价格与优惠、同级竞品等。典型提问如「奥迪A6L怎么样」「特斯拉Model Y值不值得买」「大众朗逸车系详解」。此技能调用了汽车之家的专业数据，为指定车系生成包含基础信息、车型、口碑、报价与优惠及同级竞品车的完整详解报告。不适用于选车推荐、预算筛选、多车对比等场景。
description_zh: "基于汽车之家专业数据，查询指定汽车的完整信息，包括价格、口碑、配置、优惠和竞品对比，生成一目了然的详解报告。"
version: 1.0.1
displayName: 汽车之家车系解读报告
display_name: "汽车之家车系解读报告"
display_name_en: "Autohome Car Series Report"
description_en: "Query detailed car information including pricing, reviews, configurations, dealer promotions and competitor comparisons based on Autohome professional data. Generate comprehensive visual reports with radar charts."
visibility: "public"
---

# 车系详解报告

## 触发条件

当用户提问中**包含具体车系名称**，且意图是了解该车系的详细信息时触发。例如：

- "比亚迪秦PLUS DM-i怎么样"
- "特斯拉Model 3的配置参数"
- "大众朗逸车系详解"
- "本田CRV口碑如何"

---

## 边界与兜底

本 Skill **仅适用于指定车系名称**的详解报告生成。若用户的问题属于**选车推荐**（如"十万以内SUV推荐"）、**对比选型**（如"A和B怎么选"）等，应明确告知：

> 这个 Skill 适用于生成具体车系的详解报告，暂时不支持选车推荐。您可以告诉我感兴趣的车系名称，我来为您生成详细报告。

- 不要强行用报告模板套用不匹配的查询

---

## 核心铁律（违反即错误）

> **以下规则不可协商，任何偏离都视为执行错误：**

1. **脚本即唯一真相源**：所有 API 调用、数据处理、HTML 生成、SVG 计算必须在 `generate_report.py` 脚本中完成。**禁止模型在回答中手动模拟 API 调用、手动解析 JSON、手动拼接 HTML、手动计算 SVG 坐标。**
2. **修改 = 编辑脚本文件**：任何改动（雷达图样式、HTML 模板、数据字段等），必须通过 Edit 工具修改 `scripts/generate_report.py`，然后完整运行脚本。**绝对不允许在模型回答中"现场生成"报告内容。**
3. **一次运行 = 一次输出**：`python generate_report.py` 一次性完成所有工作并输出 `car_report.html`，模型只负责展示报告文件路径，不输出中间过程。
4. **脚本自包含**：仅依赖 Python 标准库（`urllib`、`json`、`math`、`datetime`、`concurrent.futures`），无需任何 pip 安装。
5. **并行请求**：车系搜索接口串行，口碑和价格接口必须用 `ThreadPoolExecutor` 并行执行。
6. **模板内嵌**：HTML 模板作为多行字符串写在脚本中，不依赖外部 HTML 文件。

---

## 执行流程（唯一正确路径）

### 第一步：提取车系名

从用户问题中提取车系名，**不含年款、配置及提问描述**。例如：
- 用户问"MODEL Y后轮驱动版怎么样" → 提取"MODEL Y"
- 用户问"26款速腾值不值得买" → 提取"速腾"

### 第二步：替换车系名变量并运行脚本

1. 读取 `scripts/generate_report.py`
2. 将脚本顶部的 `SERIES_NAME = "{{SERIES_NAME}}"` 中的 `{{SERIES_NAME}}` 替换为提取到的车系名
3. 在用户当前工作目录下，用 Bash 运行脚本：

```bash
python scripts/generate_report.py
```

**脚本内部自动完成：**
- 串行调用车系搜索接口 → 获取车系ID、基础数据、车型LIST、竞品LIST
- 并行调用口碑接口 + 价格接口（ThreadPoolExecutor，减少一次网络往返）
- 数学函数计算 7 边形雷达图 SVG（`build_radar_svg` 函数）
- 填充内嵌 HTML 模板，所有占位符替换
- 输出 `car_report.html` 到当前工作目录
- 图片加载失败由 `onerror` 属性兜底显示"暂无图片"

### 第三步：呈现报告

运行脚本后，检查输出：

1. **如果脚本正常完成**（生成了 `car_report.html`）：
   - 用 `preview_url` 工具打开生成的 `car_report.html`

2. **如果脚本输出 `[DATA_INSUFFICIENT]`**（数据不足）：
   - **不生成报告**
   - 仅输出一句固定提示语："当前车系信息较少，我改为以文字形式为您简要介绍。"
   - 紧接着由模型基于自身知识对该车系进行简要介绍
   - **严格禁止**输出任何内部过程说明，包括但不限于：
     - 提及 "脚本返回"、"DATA_INSUFFICIENT"、"恢复占位符" 等脚本执行细节
     - 解释 "为什么数据不足" 或 "为什么无法生成报告"
     - 描述 API 返回结果为空等中间状态
   - 用户只看到：固定提示语 + 车系文字介绍，没有其他

3. **如果脚本报错**（如车系未被识别）：
   - 将错误信息反馈给用户并引导确认车系全称。

---

## 修改报告时的执行流程

当需要修改报告样式、数据展示、雷达图等时，必须遵守：

1. **Read** `scripts/generate_report.py` 读取完整脚本内容
2. **Edit** 修改脚本中的 HTML 模板、CSS、SVG 函数或数据处理逻辑
3. **Bash** 运行 `python scripts/generate_report.py`，输入任意车系名验证
4. **preview_url** 打开生成的 `car_report.html` 展示结果
5. **恢复** `{{SERIES_NAME}}` 占位符（修改完成后务必恢复，避免影响下次使用）

**禁止的行为：**
- ❌ 在回答中输出大段 HTML 或 SVG 代码让用户"把这个放进文件"
- ❌ 手动构造 JSON 数据然后拼接 HTML
- ❌ 逐行解释脚本执行过程，逐行模拟 API 返回
- ❌ 用 `Write` 工具覆盖脚本文件（必须用 `Edit` 做增量修改，保持可追溯）

---

## 报告内容说明

脚本生成的报告包含以下 5 个模块：

| 模块 | 内容 | 数据来源 |
|------|------|---------|
| 基础信息 | 车系名、销售状态、头图、品牌、指导价、级别、口碑分 | 车系搜索 + 口碑接口 |
| 车型列表 | 前3个车型的名称、指导价、经销商价、详情链接 | 车系搜索 |
| 用户口碑 | 口碑分、星级、药丸标签、7维雷达图、一句话总结 | 口碑接口 |
| 经销商报价&优惠 | 经销商报价、厂商优惠标签、国家补贴标签 | 车系搜索 + 价格接口 |
| 同级竞品 | 前5个竞品（不足2个则隐藏模块） | 车系搜索 |

所有链接均带 `target="_blank"` 在新窗口打开。图片加载失败由 `onerror` 兜底。

---

## 技术架构

```
generate_report.py（自包含，仅依赖 Python 标准库）
├── http_get()          HTTP 请求封装
├── api_search()        车系搜索接口（串行）
├── api_koubei()        口碑接口 ──┐
├── api_price()         价格接口 ──┼── ThreadPoolExecutor 并行
├── build_radar_svg()   雷达图 SVG 数学计算
├── build_*_rows()      HTML 片段生成
├── fill_template()     占位符替换
├── HTML_TEMPLATE       内嵌多行字符串模板
└── main()              主流程编排
```

---

## 资源文件

| 文件 | 说明 |
|------|------|
| `scripts/generate_report.py` | 自包含的 Python 报告生成脚本（所有逻辑在此） |
| `references/api_reference.md` | API 接口字段参考文档 |
