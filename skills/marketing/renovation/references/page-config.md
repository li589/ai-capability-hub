# 页面属性字段速查表（action: updatePage）

> 本文件是 `updatePage` 操作**唯一合法的 fieldKey 来源**，对应后端 `queryEditor.pageConfigList.configFieldList.fieldKey`。
> 设置 `updatePage` 的 `values` 时 key 必须取自本表，**不得猜、不得自造**。

> ⚠️ **重要：页面属性的枚举值是「字符串」，不是整数**（如 `"1"`/`"2"`/`"0"`），和组件属性（整数枚举）不同；颜色用十六进制 `#RRGGBB`。

> ⛔ **用户要改的页面属性不在下表中 → 告知："WAI 暂不支持当前操作，请在编辑器内操作。"** 不要自造 key、不要调用 `cmsRenovateTool`。

---

## 一、用户描述 → 字段key 速查表

| 用户可能说的 | 字段key | 合法值 |
|---|---|---|
| 页面名称 / 页面标题 | `pageName` | 字符串，1–15 字 |
| 页面备注 | `pageDescription` | 字符串，≤50 字 |
| 背景类型（纯色/图片） | `bgType` | `"1"`(纯色) / `"2"`(图片) |
| 背景颜色（纯色时） | `bgColor` | 十六进制色值，如 `#ffffff` |
| 背景图片（图片背景时） | `bgImage` | 图片 URL（bgType=`"2"` 时必填） |
| 页面共享 | `pageShare` | `"1"`(共享) / `"0"`(不共享) |
| 关注公众号引导 | `showFocusOfficialAccount` | `"1"`(显示) / `"0"`(不显示) |
| 是否支持分享 | `supportShare` | `"1"`(支持) / `"0"`(不支持) |
| 分享标题 | `shareTitle` | 字符串，≤15 字 |
| 分享描述 | `shareDescription` | 字符串，≤30 字 |
| 分享小图 | `shareSmallPic` | 图片 URL，建议比例 1:1 |
| 分享大图 | `shareBigPic` | 图片 URL，建议比例 5:4 |
| 分享海报 | `sharePosterPic` | 图片 URL，建议比例 1:1，不支持 SVG |

---

## 二、字段表

| 字段key | 类型 | 枚举/约束 | 默认 | 说明 |
|---|---|---|---|---|
| `pageName` | string | 1–15 字，必填非空 | `""` | 页面名称 |
| `pageDescription` | string | ≤50 字 | `""` | 页面备注 |
| `bgType` | string | `"1"` / `"2"` | `"1"` | 背景类型：1纯色 2图片 |
| `bgColor` | string(color) | `#RRGGBB` | `#ffffff` | 背景颜色，**bgType=`"1"`(纯色)时生效** |
| `bgImage` | string | URL | `""` | 背景图片，**bgType=`"2"`(图片)时必填非空** |
| `pageShare` | string | `"0"` / `"1"` | `"0"` | 页面共享：1共享 0不共享 |
| `showFocusOfficialAccount` | string | `"0"` / `"1"` | `"0"` | 关注公众号引导：1显示 0不显示 |
| `supportShare` | string | `"0"` / `"1"` | `"1"` | 是否支持分享：1支持 0不支持 |
| `shareTitle` | string | ≤15 字 | `""` | 分享标题 |
| `shareDescription` | string | ≤30 字 | `""` | 分享描述 |
| `shareSmallPic` | string | URL，比例 1:1 | `""` | 分享小图 |
| `shareBigPic` | string | URL，比例 5:4 | `""` | 分享大图 |
| `sharePosterPic` | string | URL，比例 1:1，**不支持 SVG** | `""` | 分享海报 |

---

## 三、条件约束

- `bgType` = `"2"`（图片背景）时，`bgImage` 必填且非空。
- `bgType` = `"1"`（纯色）时，背景由 `bgColor` 决定。
- 改背景为图片：要一起传 `bgType:"2"` 和 `bgImage:"<url>"`。

---

## 四、页面属性涉及图片时的生成比例（用 woscli image generateImage）

需要为页面属性生成图片时，按下列**建议比例**传 `--size`（`宽x高`），并按 SKILL.md 图片规则在 prompt 末尾追加固定禁止语。**`--size` 宽高两边都必须 ≥1024，禁止传低于 1024 的尺寸**（下表尺寸已按比例放大到满足此下限，不要擅自改小）：

| 字段 | 建议比例 | 示例 `--size` | 备注 |
|---|---|---|---|
| `shareSmallPic` | 1:1 | `--size "1024x1024"` | 分享小图 |
| `shareBigPic` | 5:4 | `--size "1280x1024"` | 分享大图（宽:高=5:4） |
| `sharePosterPic` | 1:1 | `--size "1024x1024"` | 分享海报，**不要生成 SVG** |
| `bgImage` | 手机竖屏（schema 未限定，建议竖版长图） | `--size "1024x2218"` | 页面背景，按手机竖屏铺满 |

生成得到 URL 后，用 `updatePage` 写入对应字段（背景图同时传 `bgType:"2"`）。

---

## 调用示例

```json
{
  "action": "updatePage",
  "data": {
    "values": {
      "pageName": "618 大促会场",
      "bgType": "2",
      "bgImage": "https://xxx.com/bg.jpg",
      "supportShare": "1",
      "shareTitle": "618 超级购物节"
    }
  }
}
```
