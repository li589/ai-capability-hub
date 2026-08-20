# 紫微斗数命盘解读 - WorkBuddy 发布信息

## 基本信息

| 项目 | 内容 |
|------|------|
| **技能名称** | 紫微斗数命盘解读 |
| **技能版本** | 1.0.0 |
| **技能分类** | 命理预测 |
| **开发者** | 熵海领航 |
| **发布时间** | 2026-08-03 |

## 定价信息

| 项目 | 内容 |
|------|------|
| **定价类型** | 付费 (paid) |
| **价格** | ¥9.90 |
| **价格（分）** | 990 |
| **货币** | CNY |
| **计价单位** | 次 |

## 技能描述

### 简短描述（用于列表展示）
基于紫微斗数理论，根据出生时间生成专业命盘解读，包含性格、事业、财运、感情等全方位分析

### 详细描述（用于详情页）
基于传统紫微斗数理论，结合现代 AI 技术，为用户提供专业、详细的命盘解读服务。

**核心功能：**
- **精准排盘**：阳历转农历，准确计算命宫、身宫、十二宫位
- **十四主星**：安紫微星及其他十三颗主星
- **专业解读**：调用 DashScope LLM 生成通俗易懂的命盘解读
- **全方位分析**：涵盖性格特质、事业运势、财运分析、感情婚姻、健康提示

## 技术规格

### 服务地址
- **API 端点**: `https://meihua.astrakairos.com/ziwei/api/resource`
- **报告页面**: `https://meihua.astrakairos.com/ziwei/report/{order_id}`
- **健康检查**: `https://meihua.astrakairos.com/ziwei/api/health`

### 运行环境
- **服务器**: 172.31.26.203
- **端口**: 8101
- **部署路径**: /opt/skillpay-ziwei
- **Python 版本**: 3.8+
- **服务管理**: systemd

### 依赖服务
- **DashScope API**: 用于 LLM 生成解读（Qwen-Plus 模型）
- **微信支付**: 用于 X402 支付协议
- **SkillHub**: 用于技能注册和分发

## API 使用指南

### 请求示例

**第一步：提交出生信息（触发支付）**
```bash
POST https://meihua.astrakairos.com/ziwei/api/resource

{
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

**响应（402 Payment Required）：**
```json
{
  "code": "PAYMENT_REQUIRED",
  "message": "请支付后获取紫微斗数命盘解读",
  "out_trade_no": "ZW1722678400ABCD1234",
  "WeixinPay": {
    "WeixinPay-Required": "payment_code_xxx",
    "prompt": "请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay"
  }
}
```

**第二步：完成支付后重试（携带订单号）**
```bash
POST https://meihua.astrakairos.com/ziwei/api/resource
X-Out-Trade-No: ZW1722678400ABCD1234

{
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "gender": "男"
}
```

**响应（200 OK）：**
```json
{
  "code": "SUCCESS",
  "message": "命盘解读生成完成",
  "out_trade_no": "ZW1722678400ABCD1234",
  "result": {
    "birth_info": { "year": 1990, "month": 5, "day": 15, "hour": 14 },
    "lunar_info": { "year": 1990, "month": 4, "day": 21 },
    "year_stem_branch": "庚午",
    "ming_gong": { "position": 5, "branch": "巳" },
    "shen_gong": { "position": 11, "branch": "亥" },
    "main_stars": { "紫微": "巳", "天机": "辰", "太阳": "卯" },
    "interpretation": "# 紫微斗数命盘解读\n\n## 命宫特质\n您的命宫位于巳宫..."
  }
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| year | int | 是 | 出生年份（公历），范围 1900-2100 | 1990 |
| month | int | 是 | 出生月份（公历），范围 1-12 | 5 |
| day | int | 是 | 出生日期（公历），范围 1-31 | 15 |
| hour | int | 是 | 出生时辰（24小时制），范围 0-23 | 14 |
| gender | str | 是 | 性别，"男" 或 "女" | "男" |

### 响应状态码

| 状态码 | code | 说明 |
|--------|------|------|
| 200 | SUCCESS | 解读生成完成 |
| 402 | PAYMENT_REQUIRED | 需要支付 |
| 200 | NOT_PAID | 支付未完成 |
| 200 | FAILED | 处理失败 |

## 部署清单

### 文件清单
- ✅ app/ziwei_engine.py (29,520 bytes) - 紫微斗数计算引擎
- ✅ app/main.py (7,170 bytes) - FastAPI 主服务
- ✅ app/report_template.html (64,164 bytes) - 报告模板（含个性化弹窗）
- ✅ app/wxpay.py (6,228 bytes) - 微信支付集成
- ✅ app/x402_signer.py (4,055 bytes) - X402 签名模块
- ✅ app/store.py (3,801 bytes) - 订单存储
- ✅ app/config.py (1,550 bytes) - 配置管理
- ✅ requirements.txt (122 bytes) - 依赖列表
- ✅ SKILL.md (6,800 bytes) - 技能说明文档
- ✅ DEPLOYMENT.md (4,900 bytes) - 部署指南
- ✅ .env.example (548 bytes) - 环境变量示例
- ✅ skillpay-ziwei.service (339 bytes) - systemd 服务配置
- ✅ deploy.sh (3,700 bytes) - 部署脚本

### 配置项清单
```bash
MODE=live
BASE_URL=https://meihua.astrakairos.com/ziwei
PRICE=990
DASHSCOPE_API_KEY=***
WECHAT_MCH_ID=1115553958
WECHAT_APP_ID=wxf060ec4c70fda0a4
WECHAT_MCH_CERT_SERIAL=134A7200D98BF88F425D1A7843DA6C4D22D042A0
WECHAT_MCH_API_V3_KEY=7kX9mP2vL5qR8wN3jT6yB4hF1cZ0dSgA7kX9mP2vL5qR8wN3jT6yB4hF1cZ0dSgA
WECHAT_MCH_PRIVATE_KEY_PATH=/opt/workbuddy/key/apiclient_key.pem
SKILLHUB_DEVELOPER_ID=sh-TBvkkCPT
SKILLHUB_PUB_KEY_ID=PUB_KEY_6987E03697D61C08D981732D89FAC120
SKILLHUB_PRIVATE_KEY_PATH=/opt/workbuddy/key/skillhub_private_key.pem
```

## 测试验证

### 功能验证清单
- ✅ 健康检查接口正常
- ✅ 支付流程完整（402 → 支付 → 200）
- ✅ 命盘计算准确（14主星 + 6吉星 + 6煞星 + 33杂曜）
- ✅ LLM 解读生成正常（约 4800 字符）
- ✅ 报告页面渲染正常
- ✅ 个性化弹窗功能正常
- ✅ 星曜亮度显示正确（庙/旺/得地/利/平/不/陷）
- ✅ 四化标记显示正确（化禄/化权/化科/化忌）
- ✅ 三方四正关系标记正确（⊕）
- ✅ 流年命宫高亮正确（红色边框）
- ✅ 当月小限标记正确（🌙）

### 测试用例
```bash
# 测试健康检查
curl https://meihua.astrakairos.com/ziwei/api/health

# 测试支付流程
curl -X POST https://meihua.astrakairos.com/ziwei/api/resource \
  -H "Content-Type: application/json" \
  -d '{"year":1990,"month":6,"day":15,"hour":14,"gender":"男"}'

# 查看报告（替换为实际订单号）
open https://meihua.astrakairos.com/ziwei/report/ZW_FULL_1785734900
```

## 已知问题与解决方案

### 1. 星曜显示为 [object Object]
- **原因**: 前端直接访问 `starBrightness[star.name]` 对象而非 `.brightness` 属性
- **解决方案**: 已修复，使用 `brightnessInfo.brightness` 正确访问属性
- **状态**: ✅ 已修复并部署

### 2. 生产环境 LLM 调用失败
- **原因**: `DASHSCOPE_API_KEY` 环境变量未加载
- **解决方案**: 添加 `dotenv` 支持，确保 API key 正确读取
- **状态**: ✅ 已修复并部署

### 3. 宫格内文字截断
- **原因**: 容器 overflow: hidden 和固定高度导致内容溢出被裁剪
- **解决方案**: 调整 overflow: visible，设置 min-height: 140px
- **状态**: ✅ 已修复并部署

## 发布检查清单

### 发布前检查
- [x] 所有功能测试通过
- [x] API 文档完整
- [x] 部署脚本可用
- [x] 配置文件示例完整
- [x] 错误处理机制完善
- [x] 性能测试通过（响应时间 < 60s）
- [x] 安全性检查通过（敏感信息加密存储）
- [x] 代码质量检查通过（无严重 lint 错误）

### 发布后检查
- [ ] WorkBuddy 平台技能列表显示正常
- [ ] 技能详情页信息完整
- [ ] 支付流程测试通过
- [ ] 报告生成测试通过
- [ ] 用户反馈收集机制就绪

## 联系方式

- **技术支持**: dev@shanghai.work
- **问题反馈**: https://github.com/entropy-ocean/skillhub/issues
- **文档地址**: https://docs.shanghai.work/skillpay-ziwei

## 版本历史

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
