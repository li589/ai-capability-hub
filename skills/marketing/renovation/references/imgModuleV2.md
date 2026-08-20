# 图片组件字段速查表（moduleCode: `imgModuleV2`）

> 本文件是 `imgModuleV2` 组件**唯一合法的 fieldKey 来源**。设置 values（update/build）时 key 必须取自本文件，不得猜测、不得用 CSS 名。
> key 规则：非数组字段直接用叶子 key 名，**不要加 `style.` 前缀**；图片列表用 `items[N].子字段`（N 从 0 计）；枚举用整数。

---

## 组件整体效果 / 用途

**图片陈列区**：放一组图片，`styleGroup` 决定排布形态：
- `1`=**纵向平铺**：图片一张张**竖向**从上到下铺（不动，≤10 张），常用于卖点长图、整图陈列。
- `2`=**横向平铺**：图片**两两并排**摆成网格（每行 2 列，**不动**，≤4 张）。
- `3`=**横向滚动**：图片排成**一排**，**可左右滑动**翻看（≤10 张）。

可设圆角、图片间距、页边距。

```
纵向平铺(1)        横向平铺(2)        横向滚动(3)
┌────────┐        ┌───┬───┐        ┌──┬──┬──┬─→
│  图 1   │        │图1│图2│        │图│图│图│ 滑
├────────┤        ├───┼───┤        └──┴──┴──┘
│  图 2   │        │图3│图4│
└────────┘        └───┴───┘
```

适合：卖点长图（纵向平铺单张大图）、图片专区、多图陈列。改图/换图见图片列表字段（5-key 规则，含 `imgType: 0`）。

---

## 一、用户描述 → 字段key 速查表

| 用户可能说的 | 字段key | 合法值 |
|---|---|---|
| 上间距小 / 上边距无 | `topMargin` | `0` |
| 上间距中 / 上边距中 | `topMargin` | `16` |
| 上间距大 / 上边距大 | `topMargin` | `24` |
| 下间距小 / 下边距无 | `bottomMargin` | `0` |
| 下间距中 / 下边距中 | `bottomMargin` | `16` |
| 下间距大 / 下边距大 | `bottomMargin` | `24` |
| 圆角 / 边角样式 | `borderRadius` | `0`(直角) / `1`(圆角) / `2`(大圆角) |
| 图片间距 / 图片之间留白 / 多张图之间的缝（⚠️ 是 `imgMargin` 不是 `pageMargin`） | `imgMargin` | `0`(无间距) / `16`(有间距) |
| 页边距 / 左右留白 / 图片离屏幕左右边的距离（⚠️ 是 `pageMargin` 不是 `imgMargin`） | `pageMargin` | `0`(无,0px) / `1`(有,28px) |
| 预览大图 / 点击放大 | `previewPic` | `1`(开启) / `0`(关闭) |
| 图片大小（仅横向滚动 styleGroup=3） | `imageSize` | `1` / `2` / `3` / `4` |
| 布局样式 / 排列方式 | `styleGroup` | `1`(纵向平铺,竖向不动) / `2`(横向平铺,两两并排不动) / `3`(横向滚动,一排可左右滑)。⚠️ `2`和`3`都"横向"但不同：`2`是固定网格不滑动，`3`是单排可滑动 |
| 换图 / 改图片 / 替换图片 / 生成图片（**第 N 张**） | `items[N].imageUrl` + `items[N].name` + `items[N].width` + `items[N].height` + `items[N].imgType`（5 个同时传，`imgType` 固定 `0`，N 从 0 计） | 见第四节 |
| 增加图片 / 添加图片 / 追加一张图 / 多加几张图 | **先 `getModuleVal` 读 `items`** 感知现有图片数量，N 接着现有末尾往后排（见第四节「增加图片」） | 见第四节 |

> ⛔ **`imgMargin` ≠ `pageMargin`，别搞混**：
> - `imgMargin` = **图片之间**的间距（多张图之间的缝），枚举 `0`/`16`。用户说"图片间距/图片之间留白/图与图之间的缝"→ `imgMargin`。
> - `pageMargin` = **页边距/左右留白**（图片离屏幕左右边的距离），枚举 `0`/`1`。用户说"页边距/左右留白/图片离屏幕边的距离"→ `pageMargin`。
> - 记法：**图与图之间 = imgMargin；图与屏之间 = pageMargin**。

---

## 二、顶层字段

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `styleGroup` | integer | `1` / `2` / `3` | `1` | `1`=纵向平铺(竖向不动,≤10张)；`2`=横向平铺(两两并排网格,不动,≤4张)；`3`=横向滚动(一排可左右滑,≤10张)。⚠️ `2`和`3`都带"横向"但不同：`2`固定不滑、`3`可滑动 |

---

## 三、样式字段（用叶子 key，不要加 `style.` 前缀，值为枚举整数）

```json
✅ { "topMargin": 16, "borderRadius": 1 }
❌ { "style": { "topMargin": 16 } }   ❌ { "style.topMargin": 16 }   ❌ { "topMargin": "16px" }
```

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `borderRadius` | integer | `0` / `1` / `2` | `0` | 0直角 1圆角 2大圆角 |
| `imgMargin` | integer | `0` / `16` | `0` | **图片之间的间距**（多张图之间的缝）；0无间距 16有间距。⚠️ 别和 `pageMargin` 混 |
| `previewPic` | integer | `0` / `1` | `1` | 1允许预览大图，0不允许 |
| `imageSize` | integer | `1` / `2` / `3` / `4` | `3` | 图片大小，**仅 styleGroup=3 时有效**，其余 styleGroup 禁止传 |
| `pageMargin` | integer | `0` / `1` | `0` | **页边距/左右留白**（图片离屏幕左右边的距离）；0无(0px) 1有(28px)。⚠️ 别和 `imgMargin` 混 |
| `topMargin` | integer | `0`(无/小) / `16`(中) / `24`(大) | `0` | 上间距(px)；只能取这三个值，不得传其他数字 |
| `bottomMargin` | integer | `0`(无/小) / `16`(中) / `24`(大) | `0` | 下间距(px)；只能取这三个值，不得传其他数字 |

---

## 四、图片列表字段（content.items，数组）

`items[N].` 是 key 的组成部分，不是可省略的层级前缀。N：第一张=`0`、第二张=`1`、第三张=`2`…

> **用户只说"修改图片/换图"没指明第几张时，默认改第一张，即 N=0。**

### 增加图片 / 追加图片（必读，避免覆盖已有图）

用户说"增加一张图 / 添加图片 / 追加几张图 / 再多放几张"时，**不能直接用 `items[0]`/`items[1]` 写图——那样会覆盖现有图片**。必须：

1. **先 `getModuleVal` 读 `items`**（key 就传 `items`），拿到现有图片数组，得知当前有几张（`count`）。
2. 新图从 `N = count` 开始往后排（现有末尾的下一张）。如现有 2 张（`items[0]`/`items[1]`）→ 新图写 `items[2]`、`items[3]`…
3. 每张新图仍按 5-key 规则传齐（`imageUrl`/`name`/`width`/`height`/`imgType:0`）。
4. **同时核对 styleGroup 的图片数量上限**（见第五节）：`1`≤10、`2`≤4、`3`≤10。追加后超上限 → 告知"已达本布局上限，请先减少现有图或切换布局"，不强行覆盖。

> ⛔ **禁止凭空假设现有图片数量**。不读 `items` 就直接写 `items[0]` = 覆盖第一张原图，是典型错误。增加图片场景下，`getModuleVal` 读 `items` 是必做前置步骤。

**改图 / 换图 / 生成图片时，必须同时传以下 5 个 key，缺一不可**（`name` 用于回显，`width`/`height` 单位 px，`imgType` 固定 `0`）：

> 尺寸规则：**普通图片组件换图/生成图默认正方形（`width` = `height`）；编辑现有图（editImage）保持原尺寸，沿用该图原有宽高**。竖版长图（如 750×1600）只用于"用图片构建首页/风格化整页"那个 build 场景，不是普通换图的默认值。

```json
✅ 正确（修改第一张，N=0，正方形）
{
  "items[0].imageUrl": "https://xxx.com/new.jpg",
  "items[0].name":     "图片名称",
  "items[0].width":    800,
  "items[0].height":   800,
  "items[0].imgType":  0
}

✅ 正确（修改第二张，N=1，正方形）
{
  "items[1].imageUrl": "https://xxx.com/new.jpg",
  "items[1].name":     "新图片",
  "items[1].width":    800,
  "items[1].height":   800,
  "items[1].imgType":  0
}
```

**以下写法全部错误，禁止使用：**

```text
❌ { "imageUrl": "https://..." }                       // 丢了 items[N]. 前缀
❌ { "items[1]": "https://..." }                       // 缺子字段名(.imageUrl/.name/.width/.height)
❌ { "images[1].imageUrl": "..." }                     // images 字段不存在
❌ { "imgList[1].imageUrl": "..." }                    // imgList 字段不存在
❌ { "image_1": "https://..." }                        // 自造字段名
❌ { "content": { "items": [{ "imageUrl": "..." }] } } // 嵌套对象写法，不支持
❌ 只传 items[0].imageUrl 而不传 name/width/height/imgType // 5 个必须齐全
```

| 字段key | 类型 | 约束 | 默认 | 说明 |
|---|---|---|---|---|
| `items[N].name` | string | — | — | 图片名称，回显用，改图必填 |
| `items[N].imageUrl` | string(uri) | URL | — | 图片地址，改图必填 |
| `items[N].width` | number | ≥ 0 | `200` | 宽(px)，改图必填 |
| `items[N].height` | number | ≥ 0 | `200` | 高(px)，改图必填 |
| `items[N].imgType` | integer | 固定 `0` | `0` | 固定为 `0`，不可改；**改图必传**（与 imageUrl/name/width/height 同传，共 5 个） |
| `items[N].link` | object | 空对象 | `{}` | 跳转链接 |
| `items[N].hotZoneList` | array | 空数组 | `[]` | 热区列表 |

---

## 五、styleGroup 与图片数量 / imageSize 约束

| styleGroup | 含义 | 最多图片数 | `imageSize` |
|---|---|---|---|
| `1` | 纵向平铺 | 10 | **不允许**传 |
| `2` | 横向平铺 | 4 | **不允许**传 |
| `3` | 横向滚动 | 10 | **必须**传 |