# 全平台 → 阿里云 产品映射对照表

> 本表为云产品选型专家的核心参考数据。每条映射含置信度评级（★★★★★~★☆☆☆☆）和关键差异说明。

---

## 1. AWS → 阿里云

### 1.1 计算

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| EC2 (通用型 m5) | ECS ecs.g7 | ★★★★☆ | g7为最新通用型，网络带宽更优；m5→g7跨代映射性能提升约20% | 若客户对性能敏感，建议g8i（Intel）或g8y（AMD） |
| EC2 (计算型 c5) | ECS ecs.c7 | ★★★★☆ | c7计算优化型，CPU/内存比2:1，与c5等价 | 高计算场景推荐c8i |
| EC2 (内存型 r5) | ECS ecs.r7 | ★★★★☆ | r7内存优化型，CPU/内存比1:8，与r5等价 | 大内存场景推荐r8i |
| EC2 (GPU p3/g4) | ECS GPU实例 gn7i/gn7 | ★★★☆☆ | GPU型号需逐卡对比（V100→gn6v，A10→gn7i，A100→gn7e） | 训练vs推理场景选型不同，需确认 |
| EC2 (突发型 t3) | ECS ecs.t6 | ★★★★☆ | 突发性能实例等价，均基于CPU积分机制 | t3→t6，注意基准频率差异 |
| EC2 (裸金属 i3.metal) | ECS 裸金属 ebmg7 | ★★★★☆ | 神龙架构裸金属，性能等价 | 需确认区域可用性 |
| ECS Fargate | ECI 弹性容器实例 | ★★★★☆ | 均为Serverless容器，按vCPU+内存计费 | 阿里云ECI支持Pod级别调度 |
| Auto Scaling | 弹性伸缩ESS | ★★★★★ | 功能完全等价，支持定时/动态/预测伸缩 | 配置语法不同，需重写伸缩规则 |
| Lightsail | 轻量应用服务器SWAS | ★★★★★ | 面向入门级用户的简化版云服务器 | 套餐制，按固定规格售卖 |
| Batch | 弹性高性能计算E-HPC / 批量计算 | ★★★☆☆ | AWS Batch无直接等价，E-HPC偏HPC场景 | 纯批处理可考虑ECI+自定义调度 |

### 1.2 容器与编排

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| EKS | ACK 容器服务Kubernetes版 | ★★★★☆ | 核心K8s兼容；AWS ALB Ingress Controller需替换为ALB Ingress或Nginx Ingress | ACK Serverless（ASK）对应EKS on Fargate |
| ECR | ACR 容器镜像服务 | ★★★★★ | 功能等价，支持镜像扫描、签名、多地域同步 | ACR企业版支持跨地域P2P分发 |
| ECS (容器) | ACK + ECI | ★★★★☆ | 阿里云推荐ACK统一编排，ECI作为Serverless计算底座 | 无需Fargate Profile，ECI自动调度 |

### 1.3 数据库

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| RDS MySQL | RDS MySQL 高可用版 | ★★★★★ | 完全等价，高可用版自带主备切换 | 规格：mysql.n{CPU}.medium.2c |
| RDS PostgreSQL | RDS PostgreSQL | ★★★★★ | 完全等价，支持PostGIS等扩展 | 版本跟进较及时 |
| RDS SQL Server | RDS SQL Server | ★★★★☆ | 基本等价，部分高级特性（如Always On）需企业版 | 注意License模式差异 |
| RDS MariaDB | RDS MariaDB | ★★★★★ | 完全等价 | — |
| Aurora MySQL | PolarDB MySQL版 | ★★★★☆ | PolarDB为云原生架构，存储计算分离；Aurora无直接1:1对应 | 性能更优，但连接字符串和参数组需调整 |
| Aurora PostgreSQL | PolarDB PostgreSQL版 | ★★★★☆ | 同上，PolarDB PG兼容Oracle语法 | Oracle兼容模式可覆盖部分Oracle迁移场景 |
| DynamoDB | Lindorm / Tablestore | ★★☆☆☆ | 无完全等价产品；Lindorm偏宽表时序，Tablestore偏KV | DynamoDB GSI/LSI需重新设计；迁移需应用层改造 |
| DocumentDB | MongoDB 云数据库版 | ★★★★☆ | 兼容MongoDB协议，可迁移 | 需确认MongoDB版本兼容性 |
| Neptune | GDB 图数据库 | ★★★☆☆ | 支持Gremlin查询语言，但TinkerPop兼容性需验证 | SPARQL支持有限 |
| ElastiCache Redis | 云数据库Redis版 | ★★★★★ | 完全兼容Redis协议，支持集群/标准/读写分离架构 | 注意持久化策略差异 |
| ElastiCache Memcached | 云数据库Memcache版 | ★★★★☆ | 基本等价，阿里云正在推动客户向Redis迁移 | 新建议直接用Redis版 |
| Amazon MemoryDB | 云数据库Redis版（持久内存型） | ★★★☆☆ | 阿里云Redis持久内存型可部分覆盖MemoryDB场景 | 需确认持久化SLA |

### 1.4 存储

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| S3 Standard | OSS 标准存储 | ★★★★★ | 存储类型等价；SDK需从aws-sdk替换为oss-sdk | 生命周期规则语法有差异 |
| S3 Standard-IA | OSS 低频访问存储 | ★★★★★ | 等价，最小存储天数30天（S3为30天） | — |
| S3 Glacier | OSS 归档存储 | ★★★★★ | 解冻时间：1分钟（S3 Expedited）vs 1分钟（OSS） | 冷归档存储对应Glacier Deep Archive |
| S3 Glacier Deep Archive | OSS 冷归档存储 | ★★★★☆ | 解冻时间最长12小时（S3为12-48小时） | 价格更低于Glacier Deep Archive |
| EBS gp2/gp3 | ESSD Entry/PL0云盘 | ★★★★★ | ESSD Entry等价gp2，PL0等价gp3 | PL1-PL3逐级提升IOPS |
| EBS io1/io2 | ESSD PL2/PL3云盘 | ★★★★☆ | PL3最高100万IOPS，超越io2 | 需确认实际IOPS需求 |
| EFS | NAS 文件存储（通用型） | ★★★★★ | NFS协议兼容，支持POSIX | 极速型NAS性能更优 |
| FSx for Lustre | 并行文件存储CPFS | ★★★★☆ | HPC场景等价，CPFS基于Lustre内核 | 需确认客户端兼容性 |
| FSx for Windows | NAS SMB文件存储 | ★★★☆☆ | 阿里云NAS SMB可部分覆盖，不支持Active Directory集成 | 需评估AD依赖程度 |
| Storage Gateway | 云存储网关CSG | ★★★★★ | 功能等价，支持iSCSI/NFS/SMB协议 | 本地缓存+云端存储混合架构 |

### 1.5 网络

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| VPC | VPC 专有网络 | ★★★★★ | 完全等价，CIDR/子网/路由表概念一致 | 安全组规则语法不同 |
| ELB (CLB) | CLB 传统负载均衡 | ★★★★★ | 四层负载均衡等价 | — |
| ALB | ALB 应用型负载均衡 | ★★★★★ | 七层负载均衡等价，支持gRPC/WebSocket | 转发规则语法需重写 |
| NLB | NLB 网络型负载均衡 | ★★★★★ | 四层高性能负载均衡等价 | 基于洛神网络架构 |
| Route 53 | 云解析DNS | ★★★★☆ | DNS解析等价；Route53 Health Check需迁移为云监控自定义探测 | Private Hosted Zone用PrivateZone |
| Direct Connect | 高速通道 Express Connect | ★★★★★ | 专线接入等价，物理端口对接 | 跨地域互联用云企业网CEN |
| VPN Gateway | VPN网关 | ★★★★★ | IPsec VPN等价，支持IKEv1/v2 | — |
| NAT Gateway | NAT网关 | ★★★★★ | 等价，SNAT/DNAT功能一致 | 增强型NAT网关性能更优 |
| Transit Gateway | 云企业网CEN | ★★★★☆ | 功能类似但架构不同；CEN为Overlay方式，配置更灵活 | 多VPC互联首选CEN |
| Global Accelerator | 全球加速GA | ★★★★☆ | 等价，利用阿里云骨干网加速跨境访问 | 需确认加速区域覆盖 |
| API Gateway | API网关 | ★★★★☆ | 基本等价；AWS特有的API Key使用计划需重新配置 | Lambda集成改为FC集成 |

### 1.6 安全

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| IAM | RAM 访问控制 | ★★★★☆ | 核心RBAC等价；IAM Policy语法与RAM Policy有差异需逐条转换 | STS临时凭证功能等价 |
| KMS | KMS 密钥管理服务 | ★★★★★ | 对称/非对称密钥管理等价；BYOK支持 | 信封加密模式等价 |
| WAF | WAF Web应用防火墙 | ★★★★★ | 规则引擎等价，支持自定义规则+托管规则 | Bot管理为增值服务 |
| Shield Standard | DDoS基础防护 | ★★★★★ | 免费DDoS防护等价 | — |
| Shield Advanced | DDoS高防 | ★★★★☆ | 高防IP支持T级别清洗；计费模式不同（按月 vs 按天） | 需确认业务峰值带宽 |
| Certificate Manager (ACM) | SSL证书服务 | ★★★★☆ | 免费证书申请等价；ACM自动续期功能阿里云暂不支持 | 需手动续期或对接API |
| Secrets Manager | KMS凭据管家 | ★★★★★ | 密钥/凭据轮转等价 | — |
| GuardDuty | 云安全中心（威胁检测） | ★★★☆☆ | 阿里云版集成度更高（含漏洞扫描/基线检查），但ML检测模型不同 | 需评估检测规则覆盖率 |

### 1.7 中间件与消息队列

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| SQS | 消息服务MNS / RocketMQ | ★★★☆☆ | MNS为轻量队列；高吞吐场景推荐RocketMQ | SQS FIFO Queue无直接等价，需RocketMQ顺序消息 |
| SNS | 消息服务MNS Topic | ★★★★☆ | Pub/Sub模型等价 | 短信/邮件推送需对接短信服务/邮件推送 |
| Amazon MQ | 消息队列RabbitMQ版 / ActiveMQ | ★★★★☆ | 托管RabbitMQ等价；ActiveMQ版可用但社区活跃度低 | — |
| MSK (Kafka) | 消息队列Kafka版 | ★★★★★ | 完全兼容Kafka协议，支持Connector | Serverless版本可选 |
| Amazon MQ (RabbitMQ) | 消息队列RabbitMQ版 | ★★★★★ | 100%兼容RabbitMQ协议 | — |
| Step Functions | Serverless工作流（FnF） | ★★★☆☆ | 语法不同（ASL vs FDL），需重写工作流定义 | 复杂编排建议用EventBridge+FC |
| EventBridge | EventBridge 事件总线 | ★★★★★ | 事件驱动架构等价，支持Schema Registry | — |

### 1.8 大数据与分析

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| EMR | E-MapReduce | ★★★★★ | 基于开源Hadoop/Spark，完全等价 | 阿里云EMR on ECS/ACK两种部署模式 |
| Redshift | AnalyticDB for PostgreSQL | ★★★★☆ | MPP架构等价；SQL语法有PostgreSQL兼容差异 | 实时分析场景推荐AnalyticDB MySQL |
| Athena | Data Lake Analytics / MaxCompute | ★★★☆☆ | 按需查询用DLA（已停售），大规模分析用MaxCompute | 需评估查询模式选择方案 |
| Glue | DataWorks（数据集成+数据开发） | ★★★☆☆ | 阿里云DataWorks功能更丰富（含调度/质量/治理），但ETL语法需改写 | Spark任务可迁移至EMR |
| Kinesis Data Streams | 消息队列Kafka版 / 日志服务SLS | ★★★☆☆ | 实时流用Kafka；日志流用SLS | 需根据场景拆分 |
| Elasticsearch Service | Elasticsearch（阿里云版） | ★★★★★ | 完全兼容ES API，支持IK分词器 | X-Pack商业功能需确认License |
| QuickSight | Quick BI | ★★★★☆ | BI报表工具等价，Quick BI本地化更好 | 嵌入方式有差异 |
| Lake Formation | 数据湖构建DLF | ★★★★☆ | 数据湖元数据管理和权限控制等价 | 与DataWorks集成更紧密 |

### 1.9 AI/ML与监控

| AWS产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| SageMaker | PAI 人工智能平台 | ★★★★☆ | 模型训练/部署平台等价；算法库有差异 | DSW/DLC/EAS三种子产品 |
| CloudWatch | 云监控 + ARMS | ★★★★☆ | 基础监控用云监控；APM用ARMS（应用实时监控服务） | 告警规则需逐条迁移 |
| CloudTrail | ActionTrail 操作审计 | ★★★★★ | 审计日志等价，支持跨账号/跨地域投递 | — |
| AWS Config | 配置审计 | ★★★★☆ | 资源配置合规审计等价 | 规则库差异需逐条对比 |
| X-Ray | ARMS（链路追踪） | ★★★★☆ | 分布式链路追踪等价；SDK需替换 | 支持OpenTelemetry |
| Lambda | 函数计算FC | ★★★★★ | Serverless函数等价；运行时支持Node/Python/Java/Go/Custom | 触发器配置方式不同 |

---

## 2. Azure → 阿里云

| Azure产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|-----------|-----------|--------|----------|------|
| Virtual Machine (D/E系列) | ECS (g7/c7/r7) | ★★★★☆ | 实例族映射类似AWS，D→g7通用，E→r7内存，F→c7计算 | 注意Azure B系列突发型→ecs.t6 |
| App Service | EDAS / 函数计算FC | ★★★☆☆ | PaaS应用托管无直接等价；Java/.NET用EDAS，轻量用FC | EDAS支持Spring Cloud/Dubbo |
| Azure SQL Database | RDS SQL Server / PolarDB | ★★★★☆ | 单库用RDS SQL Server；弹性池用PolarDB | 注意License模式 |
| Azure Database for MySQL | RDS MySQL | ★★★★★ | 完全等价 | — |
| Azure Database for PostgreSQL | RDS PostgreSQL / PolarDB PG | ★★★★★ | PolarDB PG兼容Oracle语法，可覆盖部分Oracle场景 | — |
| Cosmos DB | Lindorm / Tablestore / MongoDB版 | ★★☆☆☆ | 多模型数据库无直接等价；按API选择：MongoDB API→云MongoDB，Table API→Tablestore | Cassandra API需评估Lindorm CQL兼容性 |
| Blob Storage | OSS | ★★★★★ | 等价，REST API语法不同需替换SDK | — |
| Azure Files | NAS 文件存储 (SMB) | ★★★★★ | SMB协议兼容 | — |
| Azure Disk | ESSD云盘 | ★★★★★ | 等价，Ultra Disk→ESSD PL3 | — |
| Azure Kubernetes Service (AKS) | ACK | ★★★★★ | K8s完全兼容 | — |
| Azure Container Registry (ACR) | ACR 容器镜像服务 | ★★★★★ | 等价 | — |
| Azure Functions | 函数计算FC | ★★★★★ | Serverless函数等价 | 触发器绑定方式需调整 |
| Azure Virtual Network | VPC | ★★★★★ | 等价 | NSG规则需转换为安全组 |
| Azure Load Balancer | CLB/NLB | ★★★★★ | 四层用NLB，七层用ALB | — |
| Azure Application Gateway | ALB / WAF | ★★★★☆ | ALB覆盖七层负载均衡；WAF功能需单独购买 | Azure AppGW+WAF合并架构需拆分 |
| Azure Front Door | DCDN 全站加速 / ALB | ★★★☆☆ | Front Door为全球Anycast+七层路由，阿里云用DCDN+ALB组合覆盖 | 配置复杂度较高 |
| Azure ExpressRoute | 高速通道 Express Connect | ★★★★★ | 专线接入等价 | — |
| Azure VPN Gateway | VPN网关 | ★★★★★ | 等价 | — |
| Azure Active Directory (AAD) | RAM + IDaaS | ★★★☆☆ | RAM覆盖基础权限；SSO/SAML用IDaaS（应用身份服务） | AAD功能远丰富于RAM，需评估差距 |
| Azure Key Vault | KMS | ★★★★★ | 等价 | — |
| Azure Monitor | 云监控 + ARMS + SLS | ★★★★☆ | 拆分为多个阿里云产品；Metrics→云监控，Logs→SLS，APM→ARMS | 统一看板需自行搭建 |
| Azure DevOps | 云效 DevOps | ★★★★☆ | CI/CD流水线等价；制品仓库用ACR/Packages | Pipeline YAML语法需重写 |
| Service Bus | RocketMQ | ★★★★☆ | 企业消息中间件等价；高级特性（Sessions/Dead Letter）需确认 | — |
| Event Grid | EventBridge | ★★★★☆ | 事件驱动等价 | — |
| Azure Synapse Analytics | MaxCompute + AnalyticDB | ★★★☆☆ | 阿里云拆分为离线（MaxCompute）+实时（AnalyticDB）两个产品 | 统一查询体验有差距 |

---

## 3. GCP → 阿里云

| GCP产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|---------|-----------|--------|----------|------|
| Compute Engine (N2/E2) | ECS (g7/c7/r7) | ★★★★☆ | N2→g7通用，C2→c7计算，M2→r7内存 | 自定义机型用ecs自定义规格 |
| GKE | ACK | ★★★★★ | K8s完全兼容；GCP特有Autopilot模式→ACK Serverless | — |
| Cloud SQL (MySQL/PG) | RDS MySQL / RDS PostgreSQL | ★★★★★ | 完全等价 | — |
| Cloud Spanner | PolarDB-X | ★★★☆☆ | 分布式数据库概念类似，但API和SQL完全不同 | 需应用层改造 |
| BigQuery | MaxCompute / AnalyticDB PostgreSQL | ★★★☆☆ | 离线分析用MaxCompute，实时OLAP用AnalyticDB | SQL语法差异较大 |
| Cloud Storage | OSS | ★★★★★ | 等价 | SDK需替换 |
| Cloud CDN | CDN / DCDN | ★★★★★ | 等价 | — |
| Cloud Pub/Sub | RocketMQ / MNS | ★★★★☆ | Pub/Sub模型等价；高可靠场景推荐RocketMQ | — |
| Cloud Functions | 函数计算FC | ★★★★★ | 等价 | — |
| Cloud Run | ECI + SAE | ★★★★☆ | Serverless容器部署；轻量用SAE（Serverless应用引擎），通用用ECI | — |
| Artifact Registry | ACR | ★★★★★ | 等价 | — |
| VPC | VPC | ★★★★★ | 等价 | GCP Subnet为区域级，阿里云为可用区级，需注意 |
| Cloud Load Balancing | ALB + NLB + CLB | ★★★★☆ | GCP单一LB产品覆盖4/7层，阿里云需组合 | — |
| Cloud Interconnect | 高速通道 / 云企业网 | ★★★★★ | 等价 | — |
| Cloud IAM | RAM | ★★★★☆ | 核心等价，GCP Organization→阿里云资源目录 | — |
| Secret Manager | KMS凭据管家 | ★★★★★ | 等价 | — |
| Cloud Logging | SLS 日志服务 | ★★★★★ | 功能更丰富，支持实时查询和告警 | 查询语法（SLS Query）需学习 |
| Cloud Monitoring | 云监控 | ★★★★☆ | 等价；自定义指标通过SLS/云监控API上报 | — |
| Dataflow | 实时计算Flink / EMR Spark | ★★★☆☆ | Apache Beam无直接支持；Flink覆盖流处理，Spark覆盖批处理 | — |
| Dataproc | E-MapReduce | ★★★★★ | 等价，基于Hadoop/Spark | — |
| Memorystore (Redis) | 云数据库Redis版 | ★★★★★ | 等价 | — |

---

## 4. 腾讯云 → 阿里云

| 腾讯云产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|-----------|-----------|--------|----------|------|
| CVM (标准型S5) | ECS (g7) | ★★★★★ | 实例族直接映射，S5→g7，SA2→c7，M5→r7 | — |
| Lighthouse | 轻量应用服务器SWAS | ★★★★★ | 等价 | — |
| 云硬盘 (SSD) | ESSD云盘 | ★★★★★ | 等价 | SSD云盘→ESSD PL0，高效云盘→ESSD PL1 |
| CDB MySQL | RDS MySQL | ★★★★★ | 完全等价 | — |
| CDB PostgreSQL | RDS PostgreSQL | ★★★★★ | 完全等价 | — |
| TDSQL | PolarDB-X | ★★★★☆ | 分布式数据库等价，但SQL扩展语法有差异 | 分库分表规则需迁移 |
| Redis | 云数据库Redis版 | ★★★★★ | 等价 | — |
| MongoDB | 云数据库MongoDB版 | ★★★★★ | 等价 | — |
| COS | OSS | ★★★★★ | 等价，SDK需替换 | — |
| CFS | NAS 文件存储 | ★★★★★ | 等价 | — |
| CLB | CLB / ALB / NLB | ★★★★☆ | 腾讯云CLB同时覆盖4/7层，阿里云需拆分 | 七层用ALB，四层用NLB/CLB |
| VPC | VPC | ★★★★★ | 等价 | — |
| NAT网关 | NAT网关 | ★★★★★ | 等价 | — |
| CDN | CDN / DCDN | ★★★★★ | 等价 | — |
| 专线接入 | 高速通道 | ★★★★★ | 等价 | — |
| TKE | ACK | ★★★★★ | K8s兼容 | — |
| TCR | ACR | ★★★★★ | 等价 | — |
| SCF | 函数计算FC | ★★★★★ | 等价 | — |
| CMQ | RocketMQ / MNS | ★★★★☆ | CMQ队列→MNS，CMQ主题→MNS Topic | 高吞吐推荐RocketMQ |
| CKafka | 消息队列Kafka版 | ★★★★★ | 等价 | — |
| EMR | E-MapReduce | ★★★★★ | 等价 | — |
| 日志服务CLS | SLS 日志服务 | ★★★★★ | SLS功能更丰富 | 查询语法需适配 |
| 云监控 | 云监控 | ★★★★★ | 等价 | 告警策略需逐条迁移 |
| CAM | RAM | ★★★★★ | 等价 | Policy语法有差异 |

---

## 5. 华为云 → 阿里云

| 华为云产品 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|-----------|-----------|--------|----------|------|
| ECS (通用型s6) | ECS (g7) | ★★★★★ | 实例族映射：s6→g7，c6→c7，m6→r7 | — |
| EVS | ESSD云盘 | ★★★★★ | 等价 | SSD→ESSD PL0，高IO→ESSD PL1 |
| OBS | OSS | ★★★★★ | 等价，API兼容性较好 | — |
| RDS MySQL | RDS MySQL | ★★★★★ | 等价 | — |
| RDS PostgreSQL | RDS PostgreSQL | ★★★★★ | 等价 | — |
| GaussDB | PolarDB | ★★★★☆ | GaussDB for MySQL→PolarDB MySQL，GaussDB for openGauss→PolarDB PG | 分布式GaussDB→PolarDB-X |
| DCS (Redis) | 云数据库Redis版 | ★★★★★ | 等价 | — |
| DDS (MongoDB) | 云数据库MongoDB版 | ★★★★★ | 等价 | — |
| VPC | VPC | ★★★★★ | 等价 | — |
| ELB | CLB / ALB / NLB | ★★★★☆ | 华为云ELB覆盖4/7层，阿里云需拆分 | — |
| CCE | ACK | ★★★★★ | K8s兼容 | — |
| SWR | ACR | ★★★★★ | 等价 | — |
| FunctionGraph | 函数计算FC | ★★★★★ | 等价 | — |
| DMS (Kafka) | 消息队列Kafka版 | ★★★★★ | 等价 | — |
| DMS (RabbitMQ) | 消息队列RabbitMQ版 | ★★★★★ | 等价 | — |
| MRS | E-MapReduce | ★★★★★ | 等价 | — |
| DLI | MaxCompute / DLA | ★★★☆☆ | DLA已停售，大规模分析推荐MaxCompute | — |
| Cloud Eye | 云监控 | ★★★★★ | 等价 | — |
| IAM | RAM | ★★★★☆ | 核心等价，细粒度策略语法有差异 | — |
| Direct Connect | 高速通道 | ★★★★★ | 等价 | — |

---

## 6. 自建IDC → 阿里云

| 自建基础设施 | 阿里云产品 | 置信度 | 关键差异 | 备注 |
|-------------|-----------|--------|----------|------|
| 物理服务器 (通用) | ECS | ★★★★☆ | 按CPU核数×内存反推规格，向上取整到最近阿里云规格 | 例：16C64G → ecs.g7.4xlarge(16C64G) 或 ecs.g7.8xlarge(32C128G) |
| 物理服务器 (GPU) | ECS GPU实例 | ★★★☆☆ | 需确认GPU型号→阿里云GPU实例族映射 | V100→gn6v，A10→gn7i，A100→gn7e |
| VMware vSphere | SMC迁移工具 + ECS | ★★★★☆ | 使用SMC（Server Migration Center）P2V迁移 | 迁移后去除VMware依赖 |
| KVM / Hyper-V | SMC迁移工具 + ECS | ★★★★☆ | 同上，SMC支持多种虚拟化平台 | — |
| SAN存储 (FC/iSCSI) | ESSD云盘 / 块存储 | ★★★★☆ | 需评估IOPS/吞吐需求→选择ESSD等级 | 共享块存储可覆盖部分SAN场景 |
| NAS设备 | NAS 文件存储 | ★★★★★ | NFS/SMB协议兼容 | — |
| 本地Oracle RAC | PolarDB-O / RDS Oracle | ★★★☆☆ | PolarDB-O兼容Oracle语法；RDS Oracle需License | 需DBA评估兼容性 |
| 本地SQL Server | RDS SQL Server | ★★★★☆ | 等价，注意License迁移规则 | 微软License在阿里云有合规方案 |
| 本地MySQL | RDS MySQL | ★★★★★ | 等价，使用DTS迁移数据 | — |
| 硬件防火墙 | 云防火墙 / 安全组 | ★★★★☆ | 安全策略需逐条迁移；硬件F5→ALB+WAF | — |
| 硬件负载均衡 (F5) | ALB + NLB | ★★★★☆ | 软件LB替代硬件LB；F5 iRules需重写为ALB转发规则 | — |
| 专线/MPLS | 高速通道 + 云企业网 | ★★★★☆ | 物理专线对接高速通道，多分支互联用CEN | — |
| 本地DNS | 云解析DNS + PrivateZone | ★★★★★ | 公网DNS用云解析，内网DNS用PrivateZone | — |
| 本地备份 (磁带/NAS) | 云备份HBR / OSS | ★★★★☆ | HBR支持VM/数据库/文件备份 | 归档用OSS冷归档存储 |
