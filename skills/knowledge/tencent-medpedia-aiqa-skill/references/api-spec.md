# 腾讯医典知识库问答接口规格：POST /public/medical_qa

腾讯医典知识库问答接口。**无需任何密钥/token**：直接请求即可，凭证与签名由服务端处理。

## 基本信息

| 项 | 值 |
|---|---|
| 方法 | `POST` |
| 生产 URL | `https://h5.baike.qq.com/public/medical_qa` |
| 预发 URL | `https://preview.baike.qq.com/public/medical_qa` |
| Content-Type | `application/json` |
| 鉴权 | 无（服务端防护：限流 + 可选来源校验） |

## 入参

```json
{
  "query": "糖尿病早期有什么症状",
  "size": 6,
  "with_summary": false
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|:--:|---|
| `query` | string | ✅ | 用户健康问题，1-200 字。含"问医典/医典/腾讯医典"赘述时先删除 |
| `size` | int | - | 返回文章数，范围 1-50，默认 10；skill 固定传 6 |
| `with_summary` | bool | - | 是否返回大模型总结（summary_content），默认 false |

## 出参

```json
{
  "query": "...",
  "total": 6,
  "count": 6,
  "summary_content": "",
  "docs": [
    {
      "title": "...",
      "url": "https://h5.baike.qq.com/mobile/article.html?docid=...&adtag=wbuddy.skill.jkwd",
      "content": "# ...（Markdown 正文）",
      "score": 0.81,
      "ctype": 4,
      "ctypename": "文章",
      "reviewers": [{ "name": "...", "position": "...", "hospital": "...", "hprank": "...", "icon": "..." }],
      "authors": []
    }
  ],
  "traceid": "...",
  "retcode": 0,
  "bizcode": 0,
  "message": "success"
}
```

## 状态判定

| 条件 | 含义 |
|---|---|
| HTTP 200 && `retcode==0 && bizcode==0 && count>0` | 成功，有结果 |
| HTTP 200 && `count==0` | 成功，知识库无相关内容 |
| `retcode!=0` 或 `bizcode!=0`（含 `4004`=adtag 未白名单） | 业务错误 |
| HTTP 400 | 入参非法（query 空/超长） |
| HTTP 429 | 触发限流 |
| HTTP 401/403 | 鉴权/来源被拒 |
| HTTP 5xx / 网络错误 | 服务端瞬时问题，可重试 |

## curl 示例

```bash
curl -s -m 12 -X POST https://h5.baike.qq.com/public/medical_qa \
  -H "Content-Type: application/json" \
  -d '{"query":"糖尿病早期有什么症状","size":6}'
```
