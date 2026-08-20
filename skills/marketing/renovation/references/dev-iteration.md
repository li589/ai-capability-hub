# 开发环境直连、保存与视觉诊断

仅在模拟后端 agent、复跑基线、诊断工具链、保存/发布或 CDP 截图异常时读取。普通页面搭建不要加载。

## 1. 只走注册工具表面

开发环境通过：

```js
window.__WAI_AGENT__.call(name, args)
window.__WAI_AGENT__.run(steps, { stopOnError: true })
```

禁止把 AI 输入框当自动化入口，也不要直接操作 GrapesJS 模型绕过工具。`run` 内部仍逐次调用同一工具表面。

每次实验保存账本：序号、页面、工具名、参数、阶段、开始/结束、耗时、结果摘要和错误。失败实验保留，不覆盖历史。`batch_tool` 可能继续执行同批后续子操作；`run` 应把子结果中的失败传播为顶层失败。出现失败先核对 DSL 和实际页面归属，不只看外层 `ok`。

## 2. 页面上下文

- `manage_page(action=add)` 的具体“是否自动切页”行为可能变化；始终使用返回 id 显式 `manage_page(action=switch)`，再读 DSL。
- DSL 只显示当前页组件、页名和总页数；不能据此推断其他页内容。
- 连续建页后读取 `window.__WAI_AGENT__.status().currentPageId`，构建目标页前仍显式 switch。

## 3. 就绪、保存和冷启动

桥对象存在不代表方案已经恢复。冷启动先轮询 status，只在：

```text
ready === true
editorReady === true
pageCount 与后端快照一致
```

时调用工具，再用 `get_page_dsl` 核对总页数。兼容旧 bridge 时才回退为等待方案名称和页面列表。

首次保存不能只创建空壳：服务端分配 scheme id 后，要把当前 `pages` 与 `customComponents` 写回该 id。浏览器点击只表示事件派发；验收要等待 URL 出现新 id 或明确保存完成状态，再读取后端，不用固定 sleep 猜测。

发生 HMR 后，旧 bridge、Builder ref、React pagesRef 和自定义组件 CSS 可能来自不同代际。不要在热更新后的标签页保存或发布；打开新冷启动标签页，从已保存快照加载或按账本重放，再做 fresh-reload 验收。

## 4. 自定义 CSS 三份事实

自定义组件样式要同时在以下位置成立：

1. 原始 component definition；
2. GrapesJS canvas 计算样式；
3. `export_page_review` 生成的 HTML/CSS 与独立预览。

GrapesJS CssComposer 可能丢弃含 CSS 变量的合法声明，例如某些 gradient。不能只看 `editor.getCss()`；画布需要保留 raw custom CSS overlay，导出需要合并 custom CSS。保存/发布前冷启动逐页检查 raw style、计算样式和预览。

## 5. 固定/绝对定位控件

编辑器整页截图需要看到固定控件后的所有 section。只在 `EDITOR_ONLY_CSS` 下用 `.wa-canvas-edit` 将固定控件改为文档流；组件自身 CSS 和导出/预览行为保持原样。至少验证：

- 画布中的控件与后继 section；
- 预览中控件恢复真实定位；
- 预览不存在 editor override。

## 6. capture_canvas

直连契约：

```js
{ ok, captured, image, mimeType }
```

`image` 是 data URL；不要依赖私有 `_snapshot`。

html2canvas scale 只保持原生或向下缩放，不能把 360/375px H5 放大到 `maxWidth`。重复审计可使用较小尺寸；最终视觉证据用设计视口宽度。缩小证据不能代替逐页验证。

`check_completeness` 可发现结构、无效 props 和部分空 custom，但不能证明视觉正确。截图是视觉事实，HTML/CSS 是诊断事实，map/props 是实现事实。

## 7. 独立预览与 CDP

先在新标签用真实 HTTP(S) `previewUrl` 打开页面，再读取该标签页的 CDP capability。不要在 `about:blank` 请求 Raw CDP，也不要用 Raw CDP `Page.navigate`。

设置设计 manifest 的视口（H5 常见 375×812）：

- 完整移动验收优先 `mobile:true`，避免桌面滚动条压缩布局；
- 确认根节点 `-webkit-text-size-adjust:100%`；
- reload 后核对 `innerWidth`、`innerHeight`、`clientWidth`、`scrollWidth`、`devicePixelRatio`；
- 读取 `Page.getLayoutMetrics`。若 `layoutViewport.clientWidth / cssLayoutViewport.clientWidth !== 1`，宿主存在 backing scale，以其倒数作为 device metrics `scale` 后 reload。

截图前等待当前可见 `.wa-page` 内图片满足 `complete && naturalWidth > 0`，优先等待 `img.decode()`。`brokenImages=[]` 不证明图片已经完成加载。

使用：

```js
Page.captureScreenshot({ captureBeyondViewport: false })
```

同时核对输出像素、scrollWidth、关键标题矩形和肉眼宽度。不要用 `captureBeyondViewport` 拼整页，固定导航会重复或错位。DOM 与图片正常但截图空白/超时时，在同 URL 新标签复测，避免把 CDP 会话故障误判为页面问题。结束后清除设备指标覆盖并返回原 URL。

## 8. 媒体与横向组件

多张媒体先统一展示逻辑；原图比例不同则使用裁切能力。验收 wrapper、slide、image 与下一 section 的矩形，不只看首张图。组件具体比例以最新 instructions 为准，不在 Skill 中硬编码旧契约。

## 9. 最终证据顺序

每个目标页依次留存：

```text
get_page_dsl
check_completeness
export_page_review
```

再循环切页确认：

- custom selector 与 CSS 不丢失；
- 重复规则数量不增长；
- 单路由只显示一页；
- 跨页链接、主题作用域、图片来源和运行时无异常；
- 冷启动预览与编辑器一致。
