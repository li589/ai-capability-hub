---
name: renovation
description: 页面装修与配置。用户要改商城页面组件（换图/改颜色/改间距/改标题/改SEO）、搭建商城页面布局，或从零搭建H5落地页、移动站时触发。
displayName:
  zh: 页面装修与建站
  en: Storefront Design and Site Building
displayDescription:
  zh: 装修商城页面、调整组件和页面配置，或从零搭建移动端 H5 落地页、商城站及销售演示站。
  en: Customize storefront pages and component settings, or build mobile H5 landing pages, commerce sites, and sales demo sites from scratch.
---

# 装修与配置

## 功能说明

本 skill 覆盖两类页面构建诉求，通过顶部硬路由分流到两条独立路径：

- **CMS 商城页装修**：在微盟 CMS 装修编辑器内，修改已有商城页面的组件属性、搭建页面组件布局、生成风格化页面、修改页面级配置。所有操作通过前端工具 `cmsRenovateTool` 生效。这些页面均为移动端竖屏页面（H5/小程序），组件按手机屏宽单列自上而下堆叠。
- **WAI Builder 建站**：从零创建 H5 应用、落地页、移动商城站或销售演示站点，通过 `woscli wai-builder` 命令族与 `manage_page` / `apply_page_dsl` / `update_component` 等画布工具产出可演示、可分享、可编辑的多页站点。

## 触发场景

**CMS 商城页装修（路径 A）**
- 修改/编辑某个组件的属性：改图片、换图、把第 N 张图片替换为某图（含替换为 AI 生成的图）、改颜色、改间距、改圆角、改图片尺寸、改布局样式。
- 搭建页面布局、把哪些组件放到页面上、指定组件顺序。
- 搭建一个 XX 风格的页面（大促风、节日风、电商风、极简风等）。
- 修改页面配置 / 页面属性 / 页面标题 / SEO / 分享图 / 背景图。

**WAI Builder 建站（路径 B）**
- 创建、重设计、修改、评审、商业验证或诊断 WAI Builder 移动商城、H5 应用、落地页、销售演示站点或其编辑器流程。
- 从零搭一个新站点 / 新 H5 / 新落地页。

**不触发**：写公众号文章并发布、写文案、生成小红书图文 → content-creation；查商品库存、改商品价格 → 商品类 skill；创建促销活动 → promotion。仅打招呼、闲聊或通用问题也不触发。

## 顶部硬路由（先判路径，再执行）

| 判定条件 | 路径 | 核心工具 |
|---|---|---|
| 修改**已有**商城页面的组件 / 页面属性；在 CMS 装修编辑器内搭建组件布局或风格页 | **A：CMS 装修** | `cmsRenovateTool`（`update` / `build` / `updatePage` / `getModuleVal`）+ `get_skill_reference` + `woscli image` |
| **从零**搭建新的 H5 / 落地页 / 移动站 / 销售演示站；对 WAI Builder 站点做整站重设计或评审 | **B：WAI Builder 建站** | `woscli wai-builder ...` + `manage_page` / `apply_page_dsl` / `update_component` / `apply_style_theme` / `check_completeness` / `export_page_review` |

路径判定补充：

- 页面**已存在**且用户只是调属性（边距/颜色/圆角/间距），**无论涉及一个还是全部组件**，都走路径 A 的 `update`，不要用 `build`——重新 `build` 会生成一套全新组件，导致页面出现两套重复内容。
- 只有用户明确说"重新搭建/重新布局/搭一个 XX 页面"，才走路径 A 的 `build`。
- 两条路径不得混用工具：路径 A 内**禁止**调用 `manage_page` / `apply_page_dsl`；路径 B 内**禁止**调用 `cmsRenovateTool`。
- 路径 A 下 `cmsRenovateTool` 不可用 = 用户尚未进入装修编辑页。**不要自动跳转**，直接回复：「我可以为您自动完成页面装修，但需要您先手动进入装修页面。您进入后告知我，我便会立即启动自动化搭建流程，后续操作交给我即可。」等用户告知后再继续。

## 调用方式

### 路径 A：cmsRenovateTool（前端工具）

> ⛔ **强制顺序**：涉及组件属性或页面属性的任何操作，**第一步必须** `get_skill_reference` 读对应字段速查表拿到 fieldKey，**之后**才允许调用 `cmsRenovateTool`。合法 fieldKey **只存在于速查表文件中**，不存在于工具 schema、CSS 规范、组件名或世界知识里。
>
> ⛔ 本路径**禁止**调用 `get_web_client_tool_schema`——`cmsRenovateTool` 的调用格式与全部 fieldKey 已在本文件和速查表中完整定义，调它只会拿到无 fieldKey 的空壳 schema。

```json
// action: update —— 修改指定组件属性
{ "action": "update", "data": { "id": "<组件实例 id，必填>", "moduleCode": "<组件 moduleCode>", "focus": true, "values": { "<fieldKey>": "<value>" } } }

// action: build —— 搭建组件列表（data 数组顺序 = 页面从上到下顺序；只搭骨架时 values 传 {}）
{ "action": "build", "data": [ { "moduleCode": "<code1>", "values": {} }, { "moduleCode": "<code2>", "values": {} } ] }

// action: updatePage —— 修改页面级属性
{ "action": "updatePage", "data": { "values": { "<fieldKey>": "<value>" } } }

// action: getModuleVal —— 读组件当前属性值（需要原值且不可推断时）
{ "action": "getModuleVal", "data": { "id": "<组件实例 id>", "moduleCode": "<组件 moduleCode>", "keys": ["<fieldKey 或路径 key>"] } }
```

组件 → 字段速查表映射（读哪份 reference）：

| 组件 | moduleCode | 速查表 | 关键字段（仅锚点，以文件为准） |
|---|---|---|---|
| 图片组件 | `imgModuleV2` | @references/imgModuleV2.md | `styleGroup`、`topMargin`、`bottomMargin`、`borderRadius`、`imgMargin`、`pageMargin`、`previewPic`、`imageSize`；图片 `items[N].imageUrl/name/width/height/imgType(=0)` |
| 标题组件 | `titleModuleV2` | @references/titleModuleV2.md | `text`、`fontSize`、`specialStyle`、`color`、`bgColor`、`textAlign`、`topMargin`、`bottomMargin`、`styleGroup`、`entranceType`、`entranceTitle`、`link` |
| 文本组件 | `textModuleV2` | @references/textModuleV2.md | `text`、`displayStyle`、`fontSize`、`textAlign`、`color`、`bgColor`、`fontWeight`、`topMargin`、`bottomMargin`、`link` |
| 搜索组件 | `searchModuleV2` | @references/searchModuleV2.md | `searchKey`、`searchKeyList`、`switchStore`、`showScan`、`showHotWord`、`switchCeiling`、`searchColorType`、`borderStyle`、`bgColor`、`topMargin`、`bottomMargin` |
| 轮播图 | `advPlayModuleV2` | @references/advPlayModuleV2.md | `styleGroup`、`borderRadius`、`autoplaySpeed`、`advStyle`、`previewPic`、`space`、`slidingStyle`、`pageMargin`、`haveBackground`、`topMargin`、`bottomMargin`；图片 `items[N].imageUrl/name/width/height` |
| 图文导航 | `imgTextNaviModuleV2` | @references/imgTextNaviModuleV2.md | `styleGroup`、`type`、`pictureDistribution`、`edgeCornerType`、`borderRadius`、`color`、`bgColor`、`imgSize`、`topMargin`(0/24/36)、`bottomMargin`(0/24/36)；导航项 `items[N].name/imgUrl/iconUrl/link` |
| 整页搭建（选型排序/模板） | — | @references/page-building.md | 组件目录 + 排布模型 + 页面模板 |
| 页面属性（非组件） | —（用 updatePage） | @references/page-config.md | 以文件为准 |

> ⛔ 表中**未列出**的 moduleCode = 无速查表 → 告知"该组件暂不支持装修操作"，不猜字段、不调工具。

### 路径 A：woscli image（换图 / 风格页配图）

> 组件换图、编辑图、风格页配图由本 skill 直接生成，**不要**把"换图/装修"整体转交给独立图片 skill。
> 所有 prompt 末尾必须原样追加固定禁止语：`不允许在图片上出现任何具体价格金额、满减数字、倒计时时长、折扣比例等捏造事实内容。`

```bash
# 文生图（无参考原图）—— --size 宽高两边必须都 ≥1024，默认正方形
woscli image generateImage --prompt "<画面描述>。不允许在图片上出现任何具体价格金额、满减数字、倒计时时长、折扣比例等捏造事实内容。" --size 1024x1024

# 图生图（基于原图编辑/重绘/改风格）—— 保持原尺寸，不传 --size
woscli image editImage --imageUrl "<组件当前图片URL>" --prompt "<编辑/风格描述>。不允许在图片上出现任何具体价格金额、满减数字、倒计时时长、折扣比例等捏造事实内容。"
```

两条命令返回均为 `{ "success": true, "data": { "imageUrl": "https://..." } }`。

### 路径 B：wai-builder 命令族与画布工具

```sh
woscli wai-builder search-components --query "商品列表"
woscli wai-builder load-component-instructions --componentTypes '["wa-product-list"]'
woscli wai-builder search-assets --query "童装 春季 亲子"
woscli wai-builder generate-image --prompt "具体要求" --size "1024x1024" --n 1
```

画布工具：`manage_page`（创建/切换页面）、`apply_page_dsl`（每页一次提交完整组件 + 页面 CSS + 自定义组件定义，原子预检并应用）、`update_component`（已有页面局部修改）、`apply_style_theme`（共享主题）、`check_completeness`（客观完整性检查）、`export_page_review`（导出证据）、`begin_site_review_repair`（授权定点返工）、`ask_user_question`、`write_file`。

> ⛔ 未取得目标 component type 的 schema，**不得**调用 `add_component`、`update_component` 或 `apply_page_dsl`。同页多类型先批量加载，再一次组装。组件 schema 不靠记忆猜测。

按需读取参考资料：经营模式与范围 @references/business-models.md、行业信任与合规 @references/industry-patterns.md、页面结构 @references/page-recipes.md、视觉与图片 @references/design-craft.md、组件协议 @references/components.md、可选资源 @references/resource-context.md、bridge 与保存诊断 @references/dev-iteration.md、通用设计方法论 @references/design-principles.md。

## 支持的操作

### 路径 A · Case A：修改组件属性（action: update）

1. **识别组件**：`id` 必填，取自页面上下文或上一轮 build 返回的 **`moduleLocationId`**（不是 `moduleId`）。页面上可能有多个同 moduleCode 组件，仅凭 moduleCode 无法定位；拿不到 id 就追问用户，终止。
2. **[必须] 读该组件速查表**：`get_skill_reference` 读 `references/<moduleCode>.md`，只读当前组件那一份。不读到文件内容不得进入后续步骤——**猜对也算违规**。
3. **[按需] 需要原值时先 `getModuleVal`**：修改依赖当前值且当前值未知不可推断时先读原值。典型场景：图片改暖色调/重绘（读 `items[0].imageUrl` 及 name/width/height）、给图片组件追加图片（读整个 `items` 得知现有数量，新图从 `N=count` 起排）、文案润色（读 `text`）、相对调整枚举档位（读 `fontSize`/`topMargin` 等）。用户已给完整新值（"上间距改成 16""换成这张图 <url>""标题改成 618 大促"）则跳过，直接整值替换。
4. **构建 values 并调用 update**。速查表里找不到该属性 → 告知"该属性暂不支持修改"，终止。

**换图 / 编辑图子路径**：
- "图片背景色/图片背景/背景太乱了"指的是**图片画面里的背景**，走 `editImage` 重绘，**不要**去速查表找"背景色"字段（图片类组件没有该字段）。只有用户明确说"组件背景/容器背景/模块底色"且该组件确有 `bgColor`/`haveBackground` 时才按组件样式改。
- 换成全新图 → `generateImage --size 1024x1024`；在现有图上编辑/重绘/改风格 → `editImage`（原图未知先 `getModuleVal` 读 `items[N].imageUrl`），保持原尺寸不传 `--size`。
- 下标 N 从 0 计；用户没说第几张时默认第一张 N=0。
- `width`/`height` 取实际尺寸：generateImage 传 1024x1024 → 都填 1024；editImage → 沿用原值。

### 路径 A · Case B：整页搭建（action: build）

1. **[必须] 读 @references/page-building.md** 做选型与排序，可套用其中的页面模板再增删调序。data 数组顺序 = 页面从上到下顺序。有风格诉求（618 大促风、节日喜庆、极简黑白）时同样先读本文件。
2. **[按需] build 前完成全部准备**：先对每个需填 values 的组件读字段表，再把所有 `generateImage` 调完（允许并发），最后才 build。
   - ⛔ 禁止"先 build 空页面、再逐个 update 补值"的两步式做法，必须**一次性**完成。
   - ⛔ 并发生图时，**图片归属只按"结果与其自身所属的那次调用"配对**，禁止按返回顺序或 `image_ref://tool_result_N` 编号大小猜测归属。发起每次调用前先在思考里写明"这次是为哪个组件哪个字段生成的"，返回后只认领自己那次调用的结果。build 前在思考里逐行核对「图片分配表」。
   - 风格页预设初值：颜色字段按风格基调（大促红/橙暖色、节日喜庆暖色、极简灰/黑白），文案字段填简短风格化占位标题，图片 prompt 体现风格关键词。
3. **[必须执行] 调用一次 build**。图片生成完毕 ≠ 搭建完成——完成最后一次 `generateImage` 的那一轮必须在**同一轮内**接着调 build，不得停下等用户确认。
4. build 成功后从返回中提取各组件 `moduleLocationId`，在思考里逐行记录 `moduleCode → id`，供后续 Case A 使用。

### 路径 A · Case C：修改页面属性（action: updatePage）

1. **[必须]** `get_skill_reference` 读 @references/page-config.md 确认 fieldKey。
2. 字段表里有 → 构建 values。⚠️ **页面属性枚举值是「字符串」**（如 `bgType:"2"`、`supportShare:"1"`），不是整数；颜色用十六进制。字段表里没有 → 告知"WAI 暂不支持当前操作，请在编辑器内操作"，终止。
3. 需要为 `bgImage`/`shareSmallPic`/`shareBigPic`/`sharePosterPic` 生图时按 page-config.md 第四节建议比例传 `--size`（分享小图/海报 1:1、分享大图 5:4、背景图竖屏），两边都必须 ≥1024；背景图同时传 `bgType:"2"`；海报不要生成 SVG。

### 路径 B：WAI Builder 建站流程

1. **启动门槛**（首次画布 mutation 前确定）：品牌名（必须明确，不得编造）、行业（可可靠推导则记录依据，否则询问）、经营模式（未明确时必须用 `ask_user_question` 一次性询问纯线上单店/多门店连锁/线上+到店自提/同城配送等，"创建一个店铺"只说明交付物数量，不能作为单主体依据）、页面任务与主行动、范围与页面清单、关键约束。只问仍缺少且会实质改变结果的信息。
2. **演示闭环**：商业电商 App 或销售演示必须覆盖「浏览发现 → 商品决策 → 加购 → 购物车 → 结算/履约 → 订单/售后 → 会员复访」，搭建前在 `wai-context.md` 写出 **阶段 → 页面或状态 → 可见入口**；不得用底部导航跨页跳转代替结算/履约、订单/售后。
3. **Designer**：新建/重设计/商业演示只委派**一次**全站 Designer，且在首次 mutation 之前完成；Designer 自己写入 `design/design-direction.md`，返回后主流程不再重读，直接实施。设计环节可按需读 @references/design-principles.md 与 @references/design-craft.md。局部修复沿用现有设计。
4. **发现预算**：首次 mutation 前的组件、内置页与素材发现只用**一个**工具轮次，下一次工具调用必须包含首次画布 mutation。发现批次中任一命令失败也不得开第二个发现轮次。`woscli` 参数失败最多恢复一次，只查一次 `--help`。
5. **逐页产出**：默认整站模式下按依赖顺序逐页产出并自动继续，不等待用户确认；每完成一页立即展示并运行该页 Objective Harness。整页设计明确时每页只调一次 `apply_page_dsl`。只有用户明确要求逐页确认时才等待——沉默不是批准。
6. **页面 id 映射**：用 `manage_page` 创建页面后立即维护唯一的「页面任务 → 真实 page id」映射，所有内部链接（`href`/`link`/`url`/`cartHref`/`buyHref`/列表项链接）都从映射取值。`#/detail`、`#/cart` 等只是语义占位，提交 DSL 前必须替换为 `#/<真实 page id>`，首页用 `#/`。目标页不存在时先创建或明确交付缺口，不猜 ID、不静默跳首页。
7. **最终证据与评审**：全部页面完成后按 **`manage_page(action=switch)` → `check_completeness` → `export_page_review` → 下一页** 严格串行收集证据（共享同一个实时 currentPageId，不得并行）。证据齐全才启动**一次** Visual Reviewer。Reviewer `ready` 后交付；有 blocker/major 时只允许一次批量定点返工（先把 region 映射到实时 component id，再 `begin_site_review_repair(targets=[...])`，之后只对授权目标 `update_component`）、修改页复查和一次复验，仍未通过则停止。
8. **图片决策**：素材放入画布并经真实截图检查后才算可用。Reviewer 发现公共图质量差，或用户明确表示对某图不满意要求换图时，必须主动用 `ask_user_question` 一次性汇总页面/区域/问题询问是否用 AI 生图；**用户明确同意前不得生成**。同意后用 `woscli wai-builder generate-image`，把 `data.images[].url` 写入组件并复核。

## 输出格式

### 路径 A

> ⛔ **禁止静默调用工具**。每次调 `cmsRenovateTool` 的消息必须同时带：① 一句"正在…"的面向用户简短正文（**不得说"已…"**，结果尚未返回不得预报成功），正文只留这一句；② 「字段契约」写在**思考**里（逐 key 列出字段名、值、合法值、速查表出处，与 `values` 完全一致），不写进正文。

- update：`已为图片组件追加3张图片，现在共5张。` / `已把第2张图换成新生成的猫图。` / `已将上间距改为中。` —— 用自然语言说效果，**不暴露 fieldKey**。
- build：`已为您搭建页面，组件已按顺序添加，请查看效果。`
- updatePage：`已更新页面属性，请刷新查看。`
- 部分不支持时必须同时回复两部分：**已更新**（成功写入的效果）+ **无法操作**（"XXX 暂不支持 WAI 操作，请在编辑器中完成"），不得静默跳过。
- 失败：`操作失败：<原因>。建议：<处理建议>。`

**update 失败 key 自动重试规则**：① 必须立即重读该组件速查表（即使本轮已读过）；② 不要只按报错字面改值——报错"某 key 的值非法"也可能是整个 values 的 key-value 错位；逐一核对每个 key 是否与速查表字段名完全一致、每个 value 是否真属于该字段；③ 只重传失败的 key，重试一次；④ 仍失败 → 告知"<key描述> 更新失败，该属性可能不支持 WAI 操作，请在编辑器中操作"。

### 路径 B

交付前核对每个最终页面的业务职责、主行动、跨页入口、真实截图与销售演示覆盖；确认保存结果与画布一致，无占位、断链、坏图和安全区问题。简要说明完成内容、真实缺口和可访问预览，**不把内部流程文件当成交付物**。

## 注意事项与边界

**通用**
- 两条路径工具集互斥，不得交叉调用。
- 所有图片 prompt 末尾必须原样追加固定禁止语，不得省略或改写。

**路径 A 专项**
- ⛔ **fieldKey 铁律**：① 非数组字段直接用 key 名，不加层级前缀（`topMargin` ✅ / `style.topMargin` ❌）；② 数组字段写 `items[N].子字段`，N 从 0 计（`items[0].imageUrl` ✅ / 裸 `imageUrl`、`images[1]` ❌）；③ 改图必须传齐图片字段 key（`imgModuleV2` 为 imageUrl/name/width/height/imgType=0 共 5 个，其它组件以速查表为准）；④ value 必须是速查表合法值，枚举传整数不传字符串、不带单位（`fontSize: 28` ✅ / `"28"`、`"16px"` ❌）；⑤ 速查表里找不到 → 告知"该属性暂不支持修改"，不得自造 key；⑥ 枚举字段只接受固定档位，用户说"上边距改成 10px"而该字段只有 0/16/24 时，直接回复支持的档位让用户选，**不调用工具、不自行取最近档**。
- ⛔ **跨轮固化**：本 skill 多轮对话中可能不再被加载。调 `cmsRenovateTool` 那轮必须在思考里写死字段名和已解析好的具体枚举值（依赖原值的部分才留占位），供后续轮"对账回填"。**本轮组件与历史契约组件 moduleCode 不同时，不得套用历史枚举值**（如 `titleModuleV2` 的 fontSize 是 30/32/36，`textModuleV2` 是 28/32/36），必须重读速查表。
- ⛔ **`image_ref://` 只能复用、严禁编造**：只能使用上下文中确实出现过的完整引用串（含 `user_input_*`、`tool_result_*` 等任意格式），编造的引用映射不出真实 URL。"添加 N 张图" = 调 N 次 `generateImage` 拿 N 个真实 URL，不得用编造 ref 顶替，也不得复用已有 ref 冒充新图。
- 💡 用户要加图但没给图、上下文也没有可复用 ref → **直接生成，不追问**"请提供图片链接"。例外：`editImage` 必须基于原图，原图未知时先 `getModuleVal` 读，读不到才告知"未找到原图，无法编辑"。
- ⛔ `generateImage` 的 `--size` 宽高两边都必须 ≥1024（`750x1624`、`800x800`、`1000x800` 均不合法）；默认正方形传 `1024x1024`；不确定尺寸时可不传，但绝不能传低于 1024 的值。`editImage` 保持原尺寸，不传 `--size`。
- **调用前自检清单**（缺任意一项不得调用）：已读对应速查表；每个 fieldKey 都有速查表出处；数组字段格式正确、改图 key 传齐；value 是合法值；没有调用 `get_web_client_tool_schema`；本条消息带了面向用户的简短正文；思考里的字段契约与 values 完全一致；Case B 已生成完全部图片且本轮已调 build；Case B 已核对图片分配表无串位；每个图片 URL 都是真实返回或上下文确实出现过的 ref。

**路径 A 错误码**

| 错误码 | 说明 | 处理建议 |
|---|---|---|
| `MISSING_MODULE_REF` | 未提供组件 id 或 moduleCode | 追问"请提供要修改的组件 id 或组件名称" |
| `FIELD_NOT_SUPPORTED` | 字段不在该组件速查表中 | 告知"该组件暂不支持修改此属性" |
| `COMPONENT_REF_MISSING` | 该组件尚无速查表文件 | 告知"该组件暂不支持装修操作" |
| `PAGE_FIELD_NOT_SUPPORTED` | 页面属性不在 page-config.md 中 | 告知"WAI 暂不支持当前操作，请在编辑器内操作" |
| `IMAGE_GENERATE_FAILED` | generateImage 无响应或返回空 URL | 告知"图片生成失败，请稍后重试" |
| `RENOVATE_FAILED` | `cmsRenovateTool` 返回错误或无响应 | 告知操作失败，建议稍后重试 |
| `TOOL_UNAVAILABLE` | 不在装修编辑器内 | 回复引导话术，等用户进入后继续 |

**路径 B 专项**
- 交付标准：可演示、可分享、业务适配、品牌明确、视觉完整且可编辑。真实后端、跨会话持久化和不可逆业务操作不是默认门槛；签到、领券、收藏、任务完成、Tab、弹层等无需后端的关键反馈默认实现真实前端状态变化。
- 新建或修改任务必须产生**真实画布变更**；已有方案优先局部修改，**不得覆盖人工编辑或已确认页面**。
- 每个 section 独立可编辑、可替换；**禁止把整页塞进单一不可编辑 HTML**，禁止整页图片化，不把多 section 合并成长图。
- 不得出现 `[TODO]`、`[INVALID]`、默认标题或矛盾数据；不得编造资质、背书、检测结论或客户证明。
- 图片只用用户资产、搜索返回的持久化 URL 或经允许生成的 URL。
- 375px 为主视口，360–414px 不横向溢出；文字不小于 12px，关键触控目标不小于 36×36px（内置组件内部紧凑文字链接除外）。
- 图片需要导航热区时必须实际实现为 `<a>`、`<area>` 或自定义覆盖层并在预览态验证；热区不得代替签到、领取、收藏、完成任务等会改变状态的交互。
- mutation 失败后先读实时状态，在同一 target 上正确重试或撤销；存在未恢复的 mutation 失败时不得完成，后续其他 target 成功不算恢复证据。
- 同一 blocker 连续两轮仍未消失时停止重复 inspect/update，只有新证据时再修一次。
- `check_completeness` 只阻塞 pending、错误和客观 blocker，不输出驱动画布修改的审美建议；几何识别可能有误，以最终真实截图质量为准。缺少 alt 在销售演示中不作为 blocker 或评分项。
- Reviewer 只读已有上下文、设计方向、design-craft 的图片质量审查重点和最终证据；不搜命令、不改画布，只报最多 3 个截图可证实、影响核心任务的 blocker/major。回执无效或超时只重试一次 Reviewer 并复用同一批证据，不得切页、重跑 Harness、重导出或改画布。
