# WAI 组件与自定义协议

组件名称、属性、默认值和枚举可能变化，Skill 不维护第二套 schema。先通过 agent 内部 shell 命令 `woscli wai-builder search-components` 按业务能力发现少量候选，再以选定 type 调用 `load-component-instructions`，读取由前端注册表生成的最新指令快照。

## 组件使用

- 常规页面传 `componentTypes` 批量加载本页候选；只有确实需要某包大多数组件时才加载 `packageIds`。
- `add_component`、`update_component`、preset 和列表 props 以最新返回为准，不凭记忆猜字段。
- JSON/list 类型按 `itemSchema` 组织；遵守 required、enum、singleton 和互斥关系。
- `wa-bottom-nav`、`wa-buy-bar`、`wa-fix-nav` 等单例以最新 instructions 为准；不要同时放互斥控件。
- 最终视觉审查使用整页概览和每个可见顶层组件的完整组件图；`components.json` 是组件图片与组件 ID、类型的精确绑定，不根据 `mapping.json` 顺序猜测。
- `wa-bottom-nav.items[].id` 是稳定的逻辑导航项 id（如 `home/rooms/booking`），`items[].href` 才指向真实物理 page id；`activeId` 必须匹配当前页对应的 `items[].id`，禁止把 `p_*` 物理 page id 直接填进 `activeId`（除非该 item.id 本身就是同一个值）。逐页完成后用 `check_completeness` 与截图确认恰好一个 tab 高亮且对应当前页。
- 图片通过 agent 内部 shell 命令 `woscli wai-builder search-assets` 或用户资产获取，逐项核对语义、比例和裁切；不编造 URL，不使用 unsplash.com。
- 功能图标优先使用 Remix Icon class，不用 emoji 或图片 URL。

## 主题与局部 token

- `apply_style_theme` 注入 `--wa-primary`、`--wa-accent`、`--wa-bg`、`--wa-text`、`--wa-radius`。
- 内置组件优先通过 props 与主题变量适配设计。
- 自定义组件可在唯一根 class 上声明额外的命名 token，例如 `--brand-surface-soft`、`--status-success`；重复颜色不要散落硬编码。
- `--wa-radius` 是基础值，不代表所有元素必须同一圆角。标签、媒体和通栏可以按 manifest 的语义层级使用 0、基础值或胶囊值。

## 组件策略：设计质量优先

`builtin`、`composition`、`custom` 是并列策略，不是强制降级链：

- 内置能力能忠实表达业务语义、关键交互和视觉目标时使用 `builtin`。
- 多个内置组件能形成清晰、可编辑且不冗余的结构时使用 `composition`。
- 品牌、媒体、布局、状态或交互目标更适合自定义时直接使用 `custom`；允许一页或全站的各业务 section 都是 custom。

即使全站使用 custom，也必须按业务 section 拆分为多个 GrapesJS 组件，保留独立 cid、稳定 type/schema、属性面板字段和局部替换边界。禁止把整页或整站退化成单一 HTML 块，也不能用 custom 绕过导航、可达性、完成度或 schema 校验。

选择标准是完整表达业务能力，不是能否拼出静态外观。页面动作会改变局部状态且无需后端时，builtin 或 composition 必须能完成可见反馈和重复操作保护；否则直接使用独立 custom section 和自包含 JS。真实后端、跨会话持久化或不可逆操作只有在用户明确要求并提供契约时才实现。

## 自定义组件协议

调用 `manage_component_definition(action=create)` 后，使用工具返回的规范化 `type` 调用 `add_component`；不要自行重拼 `wa-custom-*`。

HTML 必须有元素根节点。用 `data-prop` 声明需要在属性面板编辑的字段：

| 属性 | 取值 | 说明 |
| --- | --- | --- |
| `data-prop` | `/^[a-z][a-zA-Z0-9_]*$/` | 组件内唯一的 props key |
| `data-type` | `text` / `url` / `image` / `color` | 缺省为 `text` |
| `data-label` | 文本 | 属性面板名称 |
| `data-style-target` | `color` / `backgroundColor` | color 类型的写入目标 |

```html
<section class="quote-card">
  <h3 data-prop="title" data-label="标题">企业询价</h3>
  <img data-prop="cover" data-type="image" data-label="案例图片" src="" alt="">
  <a data-prop="link" data-type="url" data-label="提交链接" href="#/quote">提交需求</a>
</section>
```

约束：

- `text` 写入 textContent；`image` 只用于 `<img>`；`url` 只用于 `<a>` / `<area>`；`color` 写入指定 inline style。
- `text` prop 只能传纯文本，禁止传 `<small>`、`<em>`、`<span>`、`<br>` 等标签。需要不同字号或强调时，在 definition HTML 中拆成独立元素和独立 `data-prop`。
- 非法或重复 `data-prop`、未知 `data-type`、空 HTML 和错误标签必须修正后重试。
- CSS 以唯一根 class scope；`@keyframes` 使用唯一前缀。
- 可见初态必须完整存在于 definition HTML；JS 只做渐进增强，不依赖脚本生成基础列表、卡片或关键文案。
- JS 组件自包含，不污染全局；画布编辑态不执行时，以预览/导出态为准。轻量状态交互必须验证初态、状态变化、重复点击保护和刷新后的重置或持久化边界；用户未要求持久化时不得擅自引入本地存储。
- custom 的原始 definition、画布计算样式和 `export_page_review` HTML/预览必须一致；出现 CSS 丢失时按 `dev-iteration.md` 诊断。
- CSS 卫生规范：按钮/CTA/标签等单行文本元素必须 `white-space:nowrap`；flex 容器子项必须 `min-width:0` 防溢出；长文本用 `overflow:hidden;text-overflow:ellipsis;white-space:nowrap` 截断；正文与关键信息不小于 12px，自定义组件触控目标不小于 36×36px；内置组件内部的紧凑文字链接不参与点击区尺寸检查；设计稿以 375px 为基准，px 值直接写，禁止换算成 `vw`/`rpx`。
- `wa-image.items` 若使用内容图片，优先传 JSON 数组对象并填写 `name`，例如 `[{"src":"https://...","name":"湖畔客房全景"}]`；但缺少 `alt` 在销售演示 profile 中不作为 blocker 或返工理由。
- `wa-bottom-nav.items[].icon` 使用组件 instructions 列出的 key 或 `ri-*` class；未知英文词会被最终 DOM 质量门视为裸文本图标。
