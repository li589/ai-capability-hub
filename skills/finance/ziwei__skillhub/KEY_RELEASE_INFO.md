# 紫微斗数命盘解读 - 关键发布信息

## 📦 发布包

**文件名**: `skillpay-ziwei-v1.0.0.tar.gz`  
**文件大小**: 52.9K  
**位置**: `/Users/xy/workspace/skillhub/skillpay-ziwei/skillpay-ziwei-v1.0.0.tar.gz`

### 包含文件
```
skillpay-ziwei-v1.0.0/
├── app/
│   ├── ziwei_engine.py      # 紫微斗数计算引擎 (29.5K)
│   ├── main.py              # FastAPI 主服务 (7.2K)
│   ├── report_template.html # 报告模板 (64.2K)
│   ├── wxpay.py            # 微信支付集成 (6.2K)
│   ├── x402_signer.py      # X402 签名 (4.1K)
│   ├── store.py            # 订单存储 (3.8K)
│   └── config.py           # 配置管理 (1.6K)
├── requirements.txt         # 依赖列表
├── SKILL.md                # 技能说明文档
├── DEPLOYMENT.md           # 部署指南
├── .env.example            # 环境变量示例
├── skillpay-ziwei.service  # systemd 服务配置
└── deploy.sh               # 部署脚本
```

---

## 🎯 WorkBuddy 平台提交信息

### 基本信息
| 字段 | 值 |
|------|-----|
| 技能名称 | 紫微斗数命盘解读 |
| 技能版本 | 1.0.0 |
| 技能分类 | 命理预测 |
| 开发者 | 熵海领航 |
| 发布日期 | 2026-08-03 |

### 定价信息
| 字段 | 值 |
|------|-----|
| 定价类型 | paid |
| 价格 | 9.90 |
| 货币 | CNY |
| 计价单位 | 次 |

### 简短描述（列表展示用）
```
基于紫微斗数理论，根据出生时间生成专业命盘解读，包含性格、事业、财运、感情等全方位分析
```

### 详细描述（详情页用）
```
基于传统紫微斗数理论，结合现代 AI 技术，为用户提供专业、详细的命盘解读服务。

核心功能：
• 精准排盘：阳历转农历，准确计算命宫、身宫、十二宫位
• 十四主星：安紫微星及其他十三颗主星
• 专业解读：调用 DashScope LLM 生成通俗易懂的命盘解读（约 4800 字符）
• 全方位分析：涵盖性格特质、事业运势、财运分析、感情婚姻、健康提示
• 个性化弹窗：点击宫格查看详细解读
• 星曜亮度：显示庙/旺/得地/利/平/不/陷
• 四化标记：化禄/化权/化科/化忌
• 三方四正：关系标记（⊕）
• 流年高亮：当前流年命宫（红色边框）
• 小限标记：当月小限宫位（🌙）
```

### 标签（Tags）
```
紫微斗数, 命盘解读, 命理分析, 运势预测, 紫微星, 十四主星, 四化飞星, 三方四正
```

### 技术规格
| 字段 | 值 |
|------|-----|
| 服务地址 | https://meihua.astrakairos.com/ziwei/api/resource |
| 报告页面 | https://meihua.astrakairos.com/ziwei/report/{order_id} |
| 健康检查 | https://meihua.astrakairos.com/ziwei/api/health |
| Python 版本 | 3.8+ |
| 依赖服务 | DashScope API, 微信支付, SkillHub |

---

## 🔌 API 调用示例

### 请求参数
```json
{
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

### 参数说明
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| year | int | 是 | 出生年份（公历） | 1990 |
| month | int | 是 | 出生月份（公历） | 5 |
| day | int | 是 | 出生日期（公历） | 15 |
| hour | int | 是 | 出生时辰（24小时制） | 14 |
| gender | str | 是 | 性别 | "男" |

### 调用流程
1. **首次请求**：POST /api/resource → 返回 402 + payment_code
2. **调用支付**：使用 payment_code 调用 weixinpay_pay
3. **重试请求**：携带 X-Out-Trade-No 头重新 POST → 返回 200 + result

---

## ✅ 功能验证清单

- [x] 健康检查接口正常
- [x] 支付流程完整（402 → 支付 → 200）
- [x] 命盘计算准确（14主星 + 6吉星 + 6煞星 + 33杂曜 = 59星曜）
- [x] LLM 解读生成正常（约 4800 字符）
- [x] 报告页面渲染正常
- [x] 个性化弹窗功能正常
- [x] 星曜亮度显示正确
- [x] 四化标记显示正确
- [x] 三方四正关系标记正确
- [x] 流年命宫高亮正确
- [x] 当月小限标记正确

---

## 🚀 部署信息

### 服务器信息
| 项目 | 值 |
|------|-----|
| 服务器 IP | 172.31.26.203 |
| 服务端口 | 8101 |
| 部署路径 | /opt/skillpay-ziwei |
| 服务名称 | skillpay-ziwei.service |
| 服务状态 | active (running) |

### Nginx 配置
```nginx
location /ziwei/ {
    proxy_pass http://127.0.0.1:8101/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 环境变量配置
```bash
MODE=live
BASE_URL=https://meihua.astrakairos.com/ziwei
PRICE=990
DASHSCOPE_API_KEY=***
WECHAT_MCH_ID=1115553958
WECHAT_APP_ID=wxf060ec4c70fda0a4
WECHAT_MCH_CERT_SERIAL=134A7200D98BF88F425D1A7843DA6C4D22D042A0
WECHAT_MCH_API_V3_KEY=***
WECHAT_MCH_PRIVATE_KEY_PATH=/opt/workbuddy/key/apiclient_key.pem
SKILLHUB_DEVELOPER_ID=sh-TBvkkCPT
SKILLHUB_PUB_KEY_ID=PUB_KEY_6987E03697D61C08D981732D89FAC120
SKILLHUB_PRIVATE_KEY_PATH=/opt/workbuddy/key/skillhub_private_key.pem
```

---

## 📊 测试用例

### 测试用例 1：标准男性命盘
```json
{
  "year": 1990,
  "month": 6,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

**预期结果**：
- 返回 402 + payment_code
- 支付后返回完整命盘解读
- 报告页面正常渲染
- 个性化弹窗正常工作

### 测试用例 2：标准女性命盘
```json
{
  "year": 1995,
  "month": 8,
  "day": 20,
  "hour": 9,
  "gender": "女"
}
```

**预期结果**：
- 返回 402 + payment_code
- 支付后返回完整命盘解读
- 报告页面正常渲染
- 个性化弹窗正常工作

---

## 📝 版本历史

### v1.0.0 (2026-08-03)
- ✨ 初始版本发布
- ✅ 支持紫微斗数命盘计算（14主星 + 6吉星 + 6煞星 + 33杂曜）
- ✅ 集成 DashScope LLM 生成解读（约 4800 字符）
- ✅ 支持 X402 支付协议
- ✅ 部署到生产环境
- ✅ 个性化宫格解读弹窗
- ✅ 星曜亮度显示（庙/旺/得地/利/平/不/陷）
- ✅ 四化标记（化禄/化权/化科/化忌）
- ✅ 三方四正关系标记
- ✅ 流年命宫高亮
- ✅ 当月小限标记

---

## 📞 联系方式

- **技术支持**: dev@shanghai.work
- **问题反馈**: https://github.com/entropy-ocean/skillhub/issues
- **文档地址**: https://docs.shanghai.work/skillpay-ziwei

---

## 📄 相关文档

- `SKILL.md` - 技能详细说明
- `DEPLOYMENT.md` - 部署指南
- `WORKBUDDY_RELEASE.md` - 完整发布信息
- `.env.example` - 环境变量示例
- `deploy.sh` - 部署脚本
