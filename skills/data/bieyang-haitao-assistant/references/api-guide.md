# 别样 ShopGeni API 调用规范

> **命名说明：** 本接口内部代号为 ShopGeni API，对外品牌名为别样（BeyondStyle）统一购物接口，两者指同一服务。

本文档供 WorkBuddy AI 在执行别样海淘助手 Skill 时参考，描述如何调用别样统一购物接口。

---

## 接口基本信息

| 项目 | 值 |
|------|---|
| Endpoint | `https://nestor-api.beyondstyle.us/api/unified-shopping/stream` |
| 方法 | `POST` |
| 响应类型 | SSE（Server-Sent Events，流式响应） |
| 内容类型 | `application/json`（纯文字请求） / `multipart/form-data`（含图片文件） |

---

## 请求头

```
Content-Type: application/json          # 纯文字请求；含图片时由 curl 自动设置，不需手动指定
Accept: text/event-stream
X-Nst-Uid: workbuddy-user-<hash>       # hash = sha256(用户唯一ID)[:16]
X-Nst-Sig: workbuddy-device-<hash>     # hash = sha256(会话ID)[:16]，不采集真实设备硬件信息
X-Nst-Source: skill
```

**Header 生成算法：**

```bash
# X-Nst-Uid：基于用户标识生成，同一用户每次保持一致
X_NST_UID="workbuddy-user-$(echo -n '<WORKBUDDY_USER_ID>' | sha256sum | cut -c1-16)"

# X-Nst-Sig：基于会话 ID 生成，区分并发会话，不采集任何设备硬件信息
X_NST_SIG="workbuddy-device-$(echo -n '<WORKBUDDY_SESSION_ID>' | sha256sum | cut -c1-16)"
```

> `X-Nst-Uid` 和 `X-Nst-Sig` 用于限流和会话区分。`X-Nst-Sig` 由 WorkBuddy 会话 ID 生成，仅用于区分并发会话，**不采集任何真实设备硬件标识符**。

---

## 请求体

### 纯文字请求

```json
{
  "thread_id": "uuid-string-or-omit-for-new-session",
  "user_input": "推荐一双黑色跑鞋，预算 500 元以内"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_input` | string | ✅ | 用户的自然语言查询，中英文均支持 |
| `thread_id` | string | ❌ | 多轮对话时传入上一轮的 thread_id；首次请求可省略 |

### 含图片文件的请求（multipart/form-data）

图片搜索使用 `multipart/form-data` 格式上传图片文件。**不支持通过 JSON 传入图片 URL。**

```bash
# curl 示例（-F 标志自动设置正确的 Content-Type）
curl -s --max-time 30 -N -X POST "https://nestor-api.beyondstyle.us/api/unified-shopping/stream" \
  -H "Accept: text/event-stream" \
  -H "X-Nst-Uid: workbuddy-user-<hash>" \
  -H "X-Nst-Sig: workbuddy-device-<hash>" \
  -H "X-Nst-Source: skill" \
  -F "image=@/path/to/image.jpg" \
  -F "user_input=找类似的白色运动鞋" \
  -F "thread_id=<可选，多轮对话时传入>"
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | file | ✅ | 商品图片文件（JPEG/PNG），字段名固定为 `image` |
| `user_input` | string | ❌ | 补充文字描述，如颜色偏好、价格区间等 |
| `thread_id` | string | ❌ | 多轮对话时传入上一轮的 thread_id |

---

## 响应格式

接口以 SSE 流式返回，监听 `data:` 事件，最终以 `type: "complete"` 的事件结束。

### SSE 事件流示例

```
data: {"type":"progress","content":"Understanding your shopping preferences...\n","progress":10}

data: {"type":"progress","content":"Finding perfect recommendations for you...\n","progress":60}

data: {"type":"complete","intent":"item","content":"为您找到以下跑鞋推荐：","thread_id":"abc-123","progress":100,"recommendations":[...]}
```

### 最终 complete 事件的数据结构

```json
{
  "type": "complete",
  "intent": "item",
  "content": "为您找到以下符合条件的跑鞋：",
  "thread_id": "abc-123-uuid",
  "recommendations": [
    {
      "id": "prod-001",
      "name": "Women's Zignition Running Shoes",
      "brand": "Reebok",
      "merchant": "Amazon",
      "price": "$79.99",
      "image": "https://cdn.beyondstyle.us/img/prod-001.jpg",
      "category": "shoes",
      "product_url": "https://www.beyondstyle.us/prod?id=prod-001"
    }
  ],
  "price_comparison": {
    "candidates": [
      {
        "name": "Reebok Women's Zignition Running Shoes Black/White",
        "price": "$79.99",
        "source": "Amazon",
        "buy_url": "https://www.amazon.com/dp/..."
      },
      {
        "name": "Reebok Women's Zignition Running Shoes Black/White",
        "price": "$95.00",
        "source": "Reebok Official",
        "buy_url": "https://www.reebok.com/..."
      }
    ]
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 事件类型：`progress`（进度更新）、`complete`（完成）或 `error`（出错） |
| `progress` | number | 进度百分比（0-100）；`progress` 事件和 `complete` 事件均携带 |
| `intent` | string | AI 识别的意图：`item`（商品搜索）或 `price_comparison`（比价）；仅 `complete` 事件携带 |
| `content` | string | AI 生成的文字回复，**始终优先展示此字段** |
| `thread_id` | string | 本轮会话 ID，多轮追问时需保存并回传；仅 `complete` 事件携带 |
| `recommendations` | array | 商品推荐列表（intent 为 item 时返回） |
| `price_comparison` | object | 比价结果（intent 为 price_comparison 时返回） |

### 错误与异常响应

**API 返回的 error 事件：**
```json
{
  "type": "error",
  "content": "未能找到相关商品，请尝试更换关键词或描述更具体的产品信息。"
}
```

**完整异常处置表：**

| 异常 | 触发条件 | AI 处置方式 |
|------|---------|-----------|
| API error 事件 | `type: "error"` | 将 `content` 转达给用户，建议调整关键词 |
| HTTP 429 | 超出限流配额 | 等待 5 秒重试一次；再次 429 提示"请求频繁，请稍后再试" |
| 网络超时 | curl `--max-time 30` 触发 | 提示"网络连接超时，请稍后重试" |
| SSE 流无 complete | 30 秒内无 complete 事件 | 视为失败，提示重试或换关键词 |
| 连接拒绝 / DNS 失败 | curl 非零退出码 | 提示"别样服务暂时不可用，请稍后重试" |

---

## 比价查询技巧

比价查询的准确性高度依赖查询词的精确程度：

| 准确度 | 示例 |
|--------|------|
| ✅ 最佳 | `"find best price for Nike Air Force 1 Low Men's Sneaker White style 100074219"` |
| ✅ 较好 | `"find best price for Reebok Women's Zignition Running Shoes Black/White"` |
| ⚠️ 一般 | `"find best price for Nike Air Force 1 White"` |
| ❌ 过于模糊 | `"find best price for Nike shoes"` |

**建议：** 包含品牌 + 完整产品名 + 颜色，如有型号（style number）则一并加入。

---

## 限流说明

- 每个 `X-Nst-Uid` 限制：每分钟 20 次请求
- 超限时接口返回 HTTP 429，内容为 `{"error": "rate limit exceeded"}`
- `X-Nst-Uid` 应基于用户标识（而非设备信息）生成，避免多用户共用同一 ID
