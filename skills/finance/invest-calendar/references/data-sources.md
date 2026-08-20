# 数据源详解

## 1. 华尔街见闻 API（主源）

### 端点
```
GET https://api-one-wscn.awtmt.com/apiv1/finance/macrodatas?start={unix_ts}&end={unix_ts}
```

### 参数
- `start`: 起始 Unix 时间戳（秒，UTC）
- `end`: 结束 Unix 时间戳（秒，UTC）

### 返回结构
```json
{
  "code": 20000,
  "message": "OK",
  "data": {
    "items": [
      {
        "id": 14479,
        "public_date": 1783137720,
        "country": "美国",
        "country_id": "US",
        "title": "特朗普：将于7月4日发表主题演讲",
        "importance": 4,
        "calendar_type": "FE",
        "actual": "",
        "forecast": "",
        "previous": "",
        "revised": "",
        "unit": "",
        "period": "",
        "wscn_ticker": "",
        "flag_uri": "https://..."
      }
    ]
  }
}
```

### 字段说明
| 字段 | 含义 | 取值 |
|------|------|------|
| `public_date` | 发布时间（秒级时间戳） | UTC |
| `country` | 国家中文名 | "美国"/"中国"/"欧元区"等 |
| `country_id` | 国家代码 | "US"/"CN"/"EU"等 |
| `importance` | 重要性 | 1-4（4最高） |
| `calendar_type` | 类型 | "FD"=数据型, "FE"=事件型 |
| `actual` | 实际值 | 发布后填入 |
| `forecast` | 预期值 | 分析师共识 |
| `previous` | 前值 | 上期数据 |
| `unit` | 单位 | "%"/"万人"/"亿美元" |
| `period` | 数据期 | "2026年06月" |

### 覆盖范围
- **国家**：20+ 个（美/中/日/英/欧/澳/加/意/法/德/韩/印/瑞士等）
- **类型**：FD 数据型（约86%）+ FE 事件型（约14%）
- **时间**：通常只覆盖**未来 1-2 个月**，更远为空
- **7月典型规模**：约 488 条事件

### 调用示例
```bash
# 2026年7月（UTC: 1783094400 - 1785686399）
curl -s "https://api-one-wscn.awtmt.com/apiv1/finance/macrodatas?start=1783094400&end=1785686399"
```

### 注意事项
- 无需鉴权，公开 API
- 单次请求可返回整月数据（约 300KB）
- 建议加 `User-Agent: Mozilla/5.0` 头
- 8月及更远数据通常为空，需走预排

---

## 2. 财联社投资日历（辅源）

### 端点
```
https://www.cls.cn/investkalendar
```

### 特点
- SPA 动态加载，无公开 API
- 需用 agent-browser 抓取
- 覆盖：行业展会/公司事件/政策实施（与 WSCN 互补）
- 7月典型规模：约 32 条

### 抓取方法
```bash
agent-browser open "https://www.cls.cn/investkalendar"
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```

### 互补价值
WSCN 不覆盖的事件类型：
- 行业展会（WAIC/ChinaJoy/互联网大会）
- 公司动作（产品涨价/发布会/ADR上市）
- 政策实施日（交易所规则变更）
- 流动性事件（逆回购到期）

---

## 3. 官方源（校准用）

### 中国
| 数据 | 官方源 | URL |
|------|--------|-----|
| CPI/PPI/PMI/GDP | 国家统计局 | stats.gov.cn |
| 社融/M2/MLF/LPR | 中国人民银行 | pbc.gov.cn |
| 进出口 | 海关总署 | customs.gov.cn |
| 财报/IPO/解禁 | 巨潮资讯 | cninfo.com.cn |

### 美国
| 数据 | 官方源 | URL |
|------|--------|-----|
| 非农/CPI/PPI | BLS 劳工统计局 | bls.gov |
| GDP/PCE | BEA 经济分析局 | bea.gov |
| FOMC/利率 | 美联储 | federalreserve.gov |
| 零售销售 | 普查局 | census.gov |

### 欧元区/日本
| 数据 | 官方源 | URL |
|------|--------|-----|
| 欧元区数据 | Eurostat | ec.europa.eu/eurostat |
| ECB 决议 | 欧央行 | ecb.europa.eu |
| 日本数据 | 总务省统计局 | stat.go.jp |
| BOJ 决议 | 日本央行 | boj.or.jp |

---

## 4. 数据源优先级决策树

```
用户查询某月事件
  │
  ├─ 当前月或下月 → WSCN API（最准确，含预期值）
  │                  ├─ 有数据 → 直接用
  │                  └─ 无数据 → 预排兜底
  │
  ├─ 未来2-3月 → 预排（API 无数据）
  │                + 官方源校准关键日期（FOMC/ECB）
  │
  ├─ 历史月份 → WSCN API（含实际值）
  │
  └─ 需要题材事件（展会/公司动作）→ 财联社补充
```

---

## 5. 数据质量校验

### 时间校准
- WSCN API 时间是 UTC，展示时转北京时间（+8h）
- 中国数据发布时间通常在 09:00-10:00 北京时间
- 美国数据发布时间通常在 20:30-22:00 北京时间

### 完整性校验
- 关键事件（FOMC/非农/CPI）必须交叉验证
- 预期值在发布前 1-2 周才有意义
- 实际值发布后需及时更新

### 重复去重
- WSCN 与财联社可能有少量重叠（如 OPEC+ 会议）
- 去重规则：相同日期 + 相似标题 → 保留 WSCN 版本（字段更全）
