# 标题组件字段速查表（moduleCode: `titleModuleV2`）

> 本文件是 `titleModuleV2` 组件**唯一合法的 fieldKey 来源**。设置 values（update/build）时 key 必须取自本文件，不得猜测、不得用 CSS 名。
> key 规则：非数组字段直接用叶子 key 名，**不要加 `style.`/`content.` 前缀**；颜色用十六进制 `#RRGGBB`；枚举用整数。

---

## 组件整体效果 / 用途

**一行栏目标题**：一行（加粗）文字，用来给下方内容分区、起小标题。`styleGroup`：`1`=纯文字（只有标题），`2`=带入口（右侧多一个"查看更多"图标或文字，可点击跳转）。文字可设字号/颜色/对齐/背景。

```
纯文字(styleGroup=1)        带入口(styleGroup=2)
┌──────────────────┐      ┌──────────────────┐
│ 精选好物          │      │ 精选好物    查看更多>│
└──────────────────┘      └──────────────────┘
```

适合：分区标题、栏目分隔、带"更多"引导入口。文案 ≤10 字。

---

## 一、用户描述 → 字段key 速查表

| 用户可能说的 | 字段key | 合法值 |
|---|---|---|
| 标题文字 / 改标题内容 | `text` | 字符串，1–10 字 |
| 字号小 / 字体小 / 最小字号 / 字体调小一档 | `fontSize` | `30`（**integer，不是字符串 `"30"`**）（⚠️ 最小值是 `30`，不是 `28`；`28` 是 textModuleV2 的值） |
| 字号中 / 字体中等 | `fontSize` | `32`（**integer，不是字符串 `"32"`**） |
| 字号大 / 字体最大 / 字体放到最大 / 最大字号 | `fontSize` | `36`（**integer，不是字符串 `"36"`**） |
| 加粗 / 粗体 / 字体加粗 | `specialStyle` | `[1]`（**必须是数组，不传整数**） |
| 取消加粗 / 不加粗 / 字体不要加粗 / 去掉粗体 / 普通字重 | `specialStyle` | `[]`（**必须是空数组，不传 `0` 或其他值**） |
| 标题颜色 / 文字颜色 | `color` | 十六进制色值，如 `#212121` |
| 背景色 | `bgColor` | 十六进制色值，如 `#FFFFFF` |
| 对齐方式（居左/居中/居右） | `textAlign` | `0`=居左 / `1`=居中 / `2`=居右（**"居中"是 `1`，不是 `2`**）；带入口样式(styleGroup=2)时仅 `0`/`1` |
| 样式分组 / 是否带右侧入口 | `styleGroup` | `1`(纯文字) / `2`(带入口) |
| 右侧入口类型（仅 styleGroup=2） | `entranceType` | `0`(图标) / `1`(文字) |
| 右侧入口文字（entranceType=1） | `entranceTitle` | 字符串，1–4 字 |
| 入口文字颜色（entranceType=1） | `entranceColor` | 十六进制色值 |
| 入口图标颜色（仅 styleGroup=2 且 entranceType=0） | `iconColor` | 十六进制色值（styleGroup=1 纯文字时无图标，不传） |
| 上间距小 / 上边距无 | `topMargin` | `0` |
| 上间距中 / 上边距中 | `topMargin` | `16` |
| 上间距大 / 上边距大 | `topMargin` | `24` |
| 下间距小 / 下边距无 | `bottomMargin` | `0` |
| 下间距中 / 下边距中 | `bottomMargin` | `16` |
| 下间距大 / 下边距大 | `bottomMargin` | `24` |
| 入口跳转链接 | `link` | **固定为空对象 `{}`，不支持配置跳转**（schema 已锁死，见下） |

---

## 二、顶层字段

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `styleGroup` | integer | `1` / `2` | `1` | 1=纯文字，2=带入口（右侧带"查看更多"等入口） |

---

## 三、内容字段（content，用叶子 key）

| 字段key | 类型 | 约束 | 说明 |
|---|---|---|---|
| `text` | string | 1–10 字，必填 | 标题文字 |
| `link` | object | **恒为空对象 `{}`**（schema `const:{}`） | styleGroup=2 时需存在但固定为 `{}`，**不支持配置跳转** |

## 四、样式字段（style，用叶子 key，不要加 `style.` 前缀）

| 字段key | 类型 | 枚举/约束 | 默认 | 说明                                                  |
|---|---|---|---|-----------------------------------------------------|
| `fontSize` | **integer** | `30`(小) / `32`(中) / `36`(大) | `30` | 字号(px)；只能取这三个值；**最小值是 `30`（⚠️ 不是 `28`，`28` 是 textModuleV2 的值）**；必须传整数，传字符串前端无法处理 |
| `specialStyle` | array | `[1]`(加粗) / `[]`(不加粗) | `[1]` | **本组件唯一字体样式字段**；值必须是数组，不得传整数（如 `1`/`5` 均非法）         |
| `color` | string(color) | `#RRGGBB` | `#212121` | 文字颜色                                                |
| `bgColor` | string(color) | `#RRGGBB` | `#FFFFFF` | 背景色                                                 |
| `textAlign` | integer | `0`/`1`/`2`（styleGroup=2 仅 `0`/`1`） | `0` | `0`=居左 `1`=居中 `2`=居右（居中=1）                          |
| `topMargin` | integer | `0`(无/小) / `16`(中) / `24`(大) | `0` | 上边距；只能取这三个值，不得传其他数字                                 |
| `bottomMargin` | integer | `0`(无/小) / `16`(中) / `24`(大) | `0` | 下边距；只能取这三个值，不得传其他数字                                 |
| `entranceType` | integer | `0` / `1` | `0` | **仅 styleGroup=2**：0图标 1文字                          |
| `entranceTitle` | string | 1–4 字 | `查看更多` | **entranceType=1 必填**                               |
| `entranceColor` | string(color) | `#RRGGBB` | `#c4c4c4` | **entranceType=1 必填**：入口文字色                         |
| `iconColor` | string(color) | `#RRGGBB` | `#c4c4c4` | **entranceType=0 必填**：入口图标色                         |

> ⛔ 不存在 `fontWeight` 字段（那是 textModuleV2 的字段）。本组件加粗/取消加粗一律用 `specialStyle: [1]` / `specialStyle: []`，不得用 `fontWeight`。
> ⛔ `fontSize` 最小值是 `30`，**不存在 `28`**（`28` 是 textModuleV2 的最小字号，本组件枚举只有 `30`/`32`/`36`）。
> ⛔ **`link` 固定为空对象 `{}`**（schema `const:{}`），**不支持配置跳转链接**。用户若要求"给标题入口配跳转"→ 告知"WAI 暂不支持当前操作，请在编辑器内操作"，不自造、不调工具。

---

## 五、styleGroup 约束

| styleGroup | 含义 | 必填/约束 |
|---|---|---|
| `1` | 纯文字 | 不传 `entranceType`（无右侧入口相关字段） |
| `2` | 带入口 | 必传 `entranceType`；`link` 需存在但固定为 `{}`（不可配跳转）；`textAlign` 仅 `0`/`1`；entranceType=0 需 `iconColor`，entranceType=1 需 `entranceTitle`+`entranceColor` |
