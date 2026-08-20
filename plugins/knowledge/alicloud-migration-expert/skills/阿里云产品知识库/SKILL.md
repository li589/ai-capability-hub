---
name: 阿里云产品知识库
version: 1.0.0
description: "Internal knowledge base for Alibaba Cloud products - pricing API, instance specs, regional availability"
description_zh: "阿里云产品知识库（内部引用）：产品规格、定价API调用方法、Region/AZ分布、实例族映射"
user-invocable: false
argument-hint: ""
---

# 阿里云产品知识库（内部引用）

> **本技能为内部知识库，不直接面向用户。** 其他迁移专家技能（云产品选型专家、上云架构专家、迁移交付专家等）通过引用本知识库获取阿里云产品的规格、定价、Region等事实数据。

---

## 1. 本知识库用途

本知识库为阿里云迁移专家插件中的其他技能提供以下事实数据支撑：

- **产品规格**：ECS实例族、RDS规格、OSS存储类型等核心产品参数
- **定价方法**：BSS OpenAPI调用方式，支持实时查询产品定价
- **Region与可用区**：阿里云全球Region分布、可用区数量、各Region定位与适用场景
- **跨云映射**：AWS/Azure/GCP/腾讯云/华为云实例类型到阿里云ECS的对应关系
- **SLA数据**：核心产品可用性承诺
- **迁移工具**：各场景下推荐的迁移工具及其功能定位

调用方技能在需要事实数据时，应查阅本知识库及其 `references/` 目录下的详细文档。

---

## 2. 阿里云定价API调用方法

### 2.1 BSS OpenAPI 概述

阿里云通过 BSS（Business Support System）OpenAPI 提供产品定价查询能力，核心接口：

| 接口名 | 用途 |
|--------|------|
| `QueryProductList` | 查询阿里云产品列表及子产品编码 |
| `GetPayAsYouGoPrice` | 查询按量付费产品价格 |
| `GetSubscriptionPrice` | 查询包年包月产品价格 |
| `DescribePrice` | 通用价格查询（ECS专用） |

### 2.2 基本信息

- **API Endpoint**: `business.aliyuncs.com`
- **SDK包名**: `alibabacloud-bssopenapi`（支持 Python / Java / Go）
- **认证方式**: AccessKey ID + AccessKey Secret
- **API版本**: `2017-12-14`

### 2.3 调用示例（Python）

```python
from alibabacloud_bssopenapi20171214.client import Client
from alibabacloud_bssopenapi20171214 import models
from alibabacloud_tea_openapi import models as open_api_models

# 初始化客户端
config = open_api_models.Config(
    access_key_id='<your-ak-id>',
    access_key_secret='<your-ak-secret>',
    endpoint='business.aliyuncs.com'
)
client = Client(config)

# 查询ECS按量付费价格
request = models.GetPayAsYouGoPriceRequest(
    product_code='ecs',
    product_type='ecs',
    subscription_type='PayAsYouGo',
    module_list=[
        models.GetPayAsYouGoPriceRequestModuleList(
            module_code='InstanceType',
            config='InstanceType:ecs.g7.xlarge,Region:cn-hangzhou'
        )
    ]
)
response = client.get_pay_as_you_go_price(request)
print(response.body)
```

### 2.4 包年包月价格查询示例

```python
# 查询ECS包年包月价格
request = models.GetSubscriptionPriceRequest(
    product_code='ecs',
    product_type='ecs',
    subscription_type='Subscription',
    order_type='NewOrder',
    service_period_quantity=1,
    service_period_unit='Month',
    module_list=[
        models.GetSubscriptionPriceRequestModuleList(
            module_code='InstanceType',
            config='InstanceType:ecs.g7.xlarge,Region:cn-hangzhou'
        )
    ]
)
response = client.get_subscription_price(request)
```

> 详细调用指南、常见陷阱与限流说明请参阅 `references/pricing-api.md`。

---

## 3. 阿里云Region与可用区

### 3.1 中国大陆Region

| Region ID | 名称 | 可用区数 | 定位与适用场景 |
|-----------|------|---------|--------------|
| cn-hangzhou | 杭州 | 多AZ | 阿里总部所在地，产品最全，新功能首发 |
| cn-shanghai | 上海 | 多AZ | 金融级首选，合规要求严格的项目 |
| cn-beijing | 北京 | 多AZ | 政企首选，央企/国企/政府项目 |
| cn-shenzhen | 深圳 | 多AZ | 出海业务/粤港澳大湾区 |
| cn-zhangjiakou | 张家口 | 多AZ | 冬奥遗产，冷存储/低成本大数据 |
| cn-wulanchabu | 乌兰察布 | 多AZ | 大数据/冷存储，电价低廉 |
| cn-chengdu | 成都 | 2-3AZ | 西南节点，川渝地区业务 |
| cn-heyuan | 河源 | 2AZ | 华南补充，低成本 |
| cn-guangzhou | 广州 | 多AZ | 华南主力，游戏/电商 |

### 3.2 海外Region

| Region ID | 名称 | 可用区数 | 定位与适用场景 |
|-----------|------|---------|--------------|
| ap-southeast-1 | 新加坡 | 多AZ | 东南亚首选，出海枢纽 |
| ap-southeast-5 | 雅加达 | 2AZ | 印尼市场 |
| ap-northeast-1 | 东京 | 2AZ | 日本市场 |
| us-west-1 | 美西（硅谷） | 2AZ | 北美市场 |
| us-east-1 | 美东（弗吉尼亚） | 2AZ | 北美东岸 |
| eu-central-1 | 法兰克福 | 2AZ | 欧洲市场，GDPR合规 |
| eu-west-1 | 伦敦 | 2AZ | 英国市场 |
| me-east-1 | 迪拜 | 1AZ | 中东市场 |

### 3.3 Region选择决策建议

- **国内通用**: cn-hangzhou（产品最全）或 cn-shanghai（金融合规）
- **政企项目**: cn-beijing
- **出海东南亚**: ap-southeast-1（新加坡）
- **低成本计算/存储**: cn-zhangjiakou 或 cn-wulanchabu
- **GDPR合规**: eu-central-1（法兰克福）

---

## 4. ECS实例族速查

### 4.1 主力实例族

| 类别 | 实例族 | 处理器 | 适用场景 |
|------|--------|-------|---------|
| 通用型 | g7 / g8i | Intel | 均衡计算+内存，Web应用/中间件 |
| 通用型 | g7a / g8a | AMD | 均衡计算+内存，成本敏感场景 |
| 计算型 | c7 / c8i | Intel | CPU密集型，批处理/高性能计算 |
| 计算型 | c7a / c8a | AMD | CPU密集型，更低成本 |
| 内存型 | r7 / r8i | Intel | 大内存场景，数据库/缓存/大数据 |
| 内存型 | r7a / r8a | AMD | 大内存场景，成本敏感 |
| GPU型 | gn7i / gn7 | NVIDIA | AI推理/训练，视频渲染 |
| 本地SSD | i3 / i3g | Intel | 高IOPS，Elasticsearch/Kafka |
| 裸金属 | ebmg7 / ebmc7 | Intel | 无虚拟化损耗，高性能/合规 |

### 4.2 实例规格命名规则

格式：`ecs.{族}{代}.{规格}`

示例：`ecs.g7.xlarge` = ECS + 通用型第7代 + 4vCPU/16GiB

常用规格对照：

| 规格 | vCPU | 内存 | 网络带宽 |
|------|------|------|---------|
| small | 1 | 2GiB | - |
| large | 2 | 8GiB | 2Gbps |
| xlarge | 4 | 16GiB | 3Gbps |
| 2xlarge | 8 | 32GiB | 4Gbps |
| 4xlarge | 16 | 64GiB | 8Gbps |
| 8xlarge | 32 | 128GiB | 16Gbps |
| 16xlarge | 64 | 256GiB | 32Gbps |

> 完整实例族映射（含 AWS/Azure/GCP/腾讯云/华为云对应关系）请参阅 `references/instance-families.md`。

---

## 5. 关键产品SLA

| 产品 | 可用性SLA | 备注 |
|------|----------|------|
| SLB（负载均衡） | 99.99% | 四/七层均适用 |
| ECS 单实例 | 99.975% | 单AZ部署 |
| ECS 多AZ部署 | 99.995% | 跨AZ高可用架构 |
| RDS MySQL 高可用版 | 99.95% | 主备双节点 |
| RDS MySQL 三节点企业版 | RPO=0, RTO<=30s | 金融级数据一致性 |
| OSS 标准存储 | 99.995% | 数据持久性 99.9999999999%（12个9） |
| 云企业网 CEN | 99.95% | 跨Region/跨云网络 |
| NAT网关 | 99.95% | 增强型NAT |
| CDN | 99.99% | 全球加速 |
| Redis 集群版 | 99.95% | 多副本 |
| PolarDB | 99.99% | 存储计算分离 |
| 容器服务ACK | 99.95% | 托管Kubernetes |

---

## 6. 迁移工具对应

### 6.1 工具矩阵

| 工具 | 英文全称 | 迁移场景 | 关键特性 |
|------|---------|---------|---------|
| SMC | Server Migration Center | 物理机/VM -> ECS 整机迁移 | 增量同步、自动适配驱动、断点续传 |
| DTS | Data Transmission Service | 数据库迁移 + 实时同步 | 支持MySQL/PG/Oracle/MongoDB/Redis，结构+数据+增量 |
| OSS在线迁移 | OSS Online Migration | 对象存储跨云迁移 | 支持AWS S3/Azure Blob/腾讯COS等源 |
| 闪电立方 | Lightning Cube | 离线大数据迁移 | 物理设备寄送，适合TB-PB级数据 |
| CEN | Cloud Enterprise Network | 跨云/跨Region网络互通 | 专线+VPN+智能路由，迁移期网络底座 |

### 6.2 工具选型决策

```
数据量 < 100GB 且允许停机？
  -> DTS / ossutil 直接迁移

数据量 100GB-10TB 且需要低停机？
  -> DTS增量同步 / OSS在线迁移服务

数据量 > 10TB 或带宽受限？
  -> 闪电立方（离线）+ CEN（在线通道）

整机迁移（物理机/VMware/AWS EC2）？
  -> SMC 整机迁移

需要迁移期双云互通？
  -> CEN 云企业网 + VPN网关
```

### 6.3 迁移工具与源云对应

| 源平台 | 计算迁移 | 数据库迁移 | 对象存储迁移 |
|--------|---------|-----------|-------------|
| AWS | SMC (EC2->ECS) | DTS (RDS->RDS/PolarDB) | OSS在线迁移 (S3->OSS) |
| Azure | SMC (VM->ECS) | DTS (SQL/AzureDB->RDS) | OSS在线迁移 (Blob->OSS) |
| GCP | SMC (GCE->ECS) | DTS (CloudSQL->RDS) | OSS在线迁移 (GCS->OSS) |
| 腾讯云 | SMC (CVM->ECS) | DTS (TencentDB->RDS) | OSS在线迁移 (COS->OSS) |
| 华为云 | SMC (ECS->ECS) | DTS (GaussDB->RDS) | OSS在线迁移 (OBS->OSS) |
| 自建IDC | SMC (物理机/VM->ECS) | DTS (自建DB->RDS) | 闪电立方 / ossutil |
