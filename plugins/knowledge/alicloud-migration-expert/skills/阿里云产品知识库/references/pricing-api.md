# 阿里云定价API详细调用指南

> 本文档为阿里云迁移专家插件内部参考资料，提供BSS OpenAPI定价查询的完整使用方法和常见陷阱。

---

## 1. API概览与接入

阿里云定价查询通过 **BSS OpenAPI** 实现，API版本 `2017-12-14`，Endpoint: `business.aliyuncs.com`（全球统一）。

**核心接口**:
- `GetPayAsYouGoPrice` — 按量付费价格查询
- `GetSubscriptionPrice` — 包年包月价格查询
- `QueryProductList` — 产品列表查询

**SDK安装**: `pip install alibabacloud-bssopenapi20171214`（Python）/ Maven: `com.aliyun:alibabacloud-bssopenapi20171214`（Java）

---

## 2. 客户端初始化

```python
import os
from alibabacloud_bssopenapi20171214.client import Client
from alibabacloud_tea_openapi import models as open_api_models

config = open_api_models.Config(
    access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
    access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
    endpoint='business.aliyuncs.com'
)
client = Client(config)
```

---

## 3. 按量付费查询示例

```python
from alibabacloud_bssopenapi20171214 import models

# 查询单实例价格
request = models.GetPayAsYouGoPriceRequest(
    product_code='ecs', product_type='ecs', subscription_type='PayAsYouGo',
    module_list=[
        models.GetPayAsYouGoPriceRequestModuleList(
            module_code='InstanceType',
            config='InstanceType:ecs.g7.xlarge,Region:cn-hangzhou'
        )
    ]
)
response = client.get_pay_as_you_go_price(request)
# 解析: response.body.data.module_details.module_detail[0].cost_after_discount
#
# 多模块组合查询: 在 module_list 中追加 SystemDisk / DataDisk 等模块即可，例如:
#   module_code='SystemDisk', config='SystemDisk.Category:cloud_essd,SystemDisk.Size:40,Region:cn-hangzhou'
```

---

## 4. 包年包月查询示例

```python
request = models.GetSubscriptionPriceRequest(
    product_code='ecs', product_type='ecs',
    subscription_type='Subscription',
    order_type='NewOrder',           # NewOrder=新购, Renewal=续费, Upgrade=升级
    service_period_quantity=1,       # 时长数值
    service_period_unit='Month',     # Month / Year
    module_list=[
        models.GetSubscriptionPriceRequestModuleList(
            module_code='InstanceType',
            config='InstanceType:ecs.g7.xlarge,Region:cn-hangzhou'
        ),
    ]
)
response = client.get_subscription_price(request)
```

---

## 5. 常见产品编码速查

| 产品 | product_code | product_type | 常用module_code |
|------|-------------|-------------|----------------|
| ECS | ecs | ecs | InstanceType, SystemDisk, DataDisk |
| RDS MySQL | rds | rds | DBInstanceClass, DBInstanceStorage |
| SLB | slb | slb | InstanceType, Bandwidth |
| OSS | oss | oss | Storage, GetRequest, PutRequest |
| Redis | kvstore | kvstore | InstanceType, Bandwidth |
| NAT网关 | nat | nat_gw | InstanceType |
| EIP | eip | eip | Bandwidth |

---

## 6. 限流与最佳实践

**限流规则**: 账号级默认 20 QPS，建议不超过 10 并发，批量查询使用 `time.sleep(0.1)` 间隔。

**最佳实践**:
1. 结果缓存24小时（价格变动频率低）
2. `Throttling` 错误时指数退避重试（1s, 2s, 4s...）
3. 使用RAM子账号，仅授权 `AliyunBSSReadOnlyAccess`
4. 批量查询时按 Region 分组，控制并发

**常见错误码**:

| 错误码 | 含义 | 处理方式 |
|--------|------|---------|
| `Throttling` | 频率超限 | 增加请求间隔 |
| `InvalidParameter` | 参数不合法 | 检查product_code和config格式 |
| `NotApplicable` | 产品不支持 | 确认产品在BSS已上线 |
| `Forbidden` | 无权限 | 检查RAM授权 |

---

## 7. 注意事项

1. **API返回标准定价**，不含新用户折扣、促销活动等，实际购买价格可能更低
2. **国际站与国内站价格不同**，endpoint相同但AK所属账号体系不同
3. **抢占式实例（Spot）价格**不在BSS接口范围内，需通过ECS专有API `DescribePrice` 查询
4. **价格单位**通过 `currency` 字段标识（CNY/USD），注意区分
