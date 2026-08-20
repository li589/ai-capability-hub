# ECS实例族完整映射

> 本文档为阿里云迁移专家插件内部参考资料，提供跨云实例类型到阿里云ECS的完整映射关系。

---

## 1. 阿里云ECS实例族详解

### 1.1 通用型实例族

| 实例族 | 代次 | 处理器 | vCPU范围 | 内存比 | 网络能力 | 典型场景 |
|--------|------|--------|---------|--------|---------|---------|
| g8i | 第8代 | Intel Sapphire Rapids | 1-192 | 1:4 | 最高64Gbps | 企业级应用、中间件 |
| g8a | 第8代 | AMD Genoa | 1-192 | 1:4 | 最高64Gbps | 企业级应用（成本优化） |
| g7 | 第7代 | Intel Ice Lake | 1-128 | 1:4 | 最高32Gbps | 通用工作负载 |
| g7a | 第7代 | AMD Milan | 1-128 | 1:4 | 最高32Gbps | 通用工作负载（成本优化） |
| g6 | 第6代 | Intel Cascade Lake | 1-104 | 1:4 | 最高25Gbps | 遗留系统兼容 |

### 1.2 计算型实例族

| 实例族 | 代次 | 处理器 | vCPU范围 | 内存比 | 网络能力 | 典型场景 |
|--------|------|--------|---------|--------|---------|---------|
| c8i | 第8代 | Intel Sapphire Rapids | 1-192 | 1:2 | 最高64Gbps | 批处理、HPC |
| c8a | 第8代 | AMD Genoa | 1-192 | 1:2 | 最高64Gbps | 批处理（成本优化） |
| c7 | 第7代 | Intel Ice Lake | 1-128 | 1:2 | 最高32Gbps | CPU密集型计算 |
| c7a | 第7代 | AMD Milan | 1-128 | 1:2 | 最高32Gbps | CPU密集型（成本优化） |

### 1.3 内存型实例族

| 实例族 | 代次 | 处理器 | vCPU范围 | 内存比 | 网络能力 | 典型场景 |
|--------|------|--------|---------|--------|---------|---------|
| r8i | 第8代 | Intel Sapphire Rapids | 1-192 | 1:8 | 最高64Gbps | 数据库、内存缓存 |
| r8a | 第8代 | AMD Genoa | 1-192 | 1:8 | 最高64Gbps | 数据库（成本优化） |
| r7 | 第7代 | Intel Ice Lake | 1-128 | 1:8 | 最高32Gbps | 大内存应用 |
| r7a | 第7代 | AMD Milan | 1-128 | 1:8 | 最高32Gbps | 大内存（成本优化） |

### 1.4 GPU型实例族

| 实例族 | GPU型号 | GPU数量 | vCPU范围 | 显存 | 典型场景 |
|--------|--------|--------|---------|------|---------|
| gn7i | NVIDIA A10 | 1-4 | 4-128 | 24GB/卡 | AI推理、视频渲染 |
| gn7 | NVIDIA A100 | 1-8 | 12-192 | 80GB/卡 | AI训练、大模型推理 |
| gn6v | NVIDIA V100 | 1-8 | 8-96 | 16/32GB/卡 | 深度学习训练 |
| gn6i | NVIDIA T4 | 1-4 | 4-64 | 16GB/卡 | 轻量推理、转码 |

### 1.5 本地SSD / 裸金属实例族

| 实例族 | 存储类型 | vCPU范围 | 本地盘容量 | 典型场景 |
|--------|---------|---------|-----------|---------|
| i3 | NVMe SSD | 4-128 | 最高14TB | Elasticsearch、Kafka |
| i3g | NVMe SSD | 4-64 | 最高7TB | 高IOPS数据库 |
| d2s | HDD | 16-96 | 最高168TB | Hadoop、大数据存储 |
| ebmg7 | 裸金属通用 | 128 | 无本地盘 | 无虚拟化损耗、合规 |
| ebmc7 | 裸金属计算 | 128 | 无本地盘 | 高性能计算 |
| ebmr7 | 裸金属内存 | 128 | 无本地盘 | 大型数据库 |

---

## 2. 跨云实例类型映射

### 2.1 AWS EC2 -> 阿里云ECS

| AWS实例类型 | AWS规格 | 推荐阿里云实例 | 阿里云规格 | 说明 |
|------------|---------|--------------|-----------|------|
| t3.micro | 2C/1G | ecs.t6-c1m1.large | 2C/2G | 突发性能 |
| t3.medium | 2C/4G | ecs.t6-c1m2.large | 2C/4G | 突发性能 |
| m5.large | 2C/8G | ecs.g7.large | 2C/8G | 通用型 |
| m5.xlarge | 4C/16G | ecs.g7.xlarge | 4C/16G | 通用型 |
| m5.2xlarge | 8C/32G | ecs.g7.2xlarge | 8C/32G | 通用型 |
| m5.4xlarge | 16C/64G | ecs.g7.4xlarge | 16C/64G | 通用型 |
| c5.large | 2C/4G | ecs.c7.large | 2C/4G | 计算型 |
| c5.xlarge | 4C/8G | ecs.c7.xlarge | 4C/8G | 计算型 |
| c5.2xlarge | 8C/16G | ecs.c7.2xlarge | 8C/16G | 计算型 |
| r5.large | 2C/16G | ecs.r7.large | 2C/16G | 内存型 |
| r5.xlarge | 4C/32G | ecs.r7.xlarge | 4C/32G | 内存型 |
| r5.2xlarge | 8C/64G | ecs.r7.2xlarge | 8C/64G | 内存型 |
| p3.2xlarge | 8C/61G+V100 | ecs.gn6v-c8g1.2xlarge | 8C/32G+V100 | GPU |
| g4dn.xlarge | 4C/16G+T4 | ecs.gn6i-c4g1.xlarge | 4C/15G+T4 | GPU推理 |
| i3.xlarge | 4C/30.5G+NVMe | ecs.i3.xlarge | 4C/32G+NVMe | 本地SSD |

### 2.2 Azure VM -> 阿里云ECS

| Azure VM类型 | Azure规格 | 推荐阿里云实例 | 阿里云规格 | 说明 |
|-------------|----------|--------------|-----------|------|
| Standard_B2s | 2C/4G | ecs.t6-c1m2.large | 2C/4G | 突发性能 |
| Standard_D4s_v5 | 4C/16G | ecs.g7.xlarge | 4C/16G | 通用型 |
| Standard_D8s_v5 | 8C/32G | ecs.g7.2xlarge | 8C/32G | 通用型 |
| Standard_D16s_v5 | 16C/64G | ecs.g7.4xlarge | 16C/64G | 通用型 |
| Standard_F4s_v2 | 4C/8G | ecs.c7.xlarge | 4C/8G | 计算型 |
| Standard_F8s_v2 | 8C/16G | ecs.c7.2xlarge | 8C/16G | 计算型 |
| Standard_E4s_v5 | 4C/32G | ecs.r7.xlarge | 4C/32G | 内存型 |
| Standard_E8s_v5 | 8C/64G | ecs.r7.2xlarge | 8C/64G | 内存型 |
| Standard_NC6s_v3 | 6C/112G+V100 | ecs.gn6v-c8g1.2xlarge | 8C/32G+V100 | GPU |

### 2.3 GCP -> 阿里云ECS

| GCP类型 | GCP规格 | 推荐阿里云实例 | 阿里云规格 | 说明 |
|---------|--------|--------------|-----------|------|
| e2-medium | 2C/4G | ecs.t6-c1m2.large | 2C/4G | 经济型 |
| n2-standard-4 | 4C/16G | ecs.g7.xlarge | 4C/16G | 通用型 |
| n2-standard-8 | 8C/32G | ecs.g7.2xlarge | 8C/32G | 通用型 |
| n2-standard-16 | 16C/64G | ecs.g7.4xlarge | 16C/64G | 通用型 |
| c2-standard-4 | 4C/8G | ecs.c7.xlarge | 4C/8G | 计算型 |
| c2-standard-8 | 8C/16G | ecs.c7.2xlarge | 8C/16G | 计算型 |
| n2-highmem-4 | 4C/32G | ecs.r7.xlarge | 4C/32G | 内存型 |
| n2-highmem-8 | 8C/64G | ecs.r7.2xlarge | 8C/64G | 内存型 |
| a2-highgpu-1g | 12C/85G+A100 | ecs.gn7-c12g1.3xlarge | 12C+94G+A100 | GPU |

### 2.4 腾讯云CVM -> 阿里云ECS

| 腾讯云类型 | 规格 | 推荐阿里云实例 | 阿里云规格 | 说明 |
|-----------|------|--------------|-----------|------|
| S5.MEDIUM4 | 2C/4G | ecs.g7.large | 2C/8G | 通用型（内存稍大） |
| S5.LARGE8 | 4C/8G | ecs.c7.xlarge | 4C/8G | 计算型 |
| S5.LARGE16 | 4C/16G | ecs.g7.xlarge | 4C/16G | 通用型 |
| S5.2XLARGE16 | 8C/16G | ecs.c7.2xlarge | 8C/16G | 计算型 |
| S5.2XLARGE32 | 8C/32G | ecs.g7.2xlarge | 8C/32G | 通用型 |
| M5.2XLARGE | 8C/32G | ecs.g7.2xlarge | 8C/32G | 通用型 |
| R5.LARGE | 2C/16G | ecs.r7.large | 2C/16G | 内存型 |
| GN10X.LARGE20 | 20C+GPU | ecs.gn7i-c16g1.4xlarge | 16C+60G+A10 | GPU |

### 2.5 华为云ECS -> 阿里云ECS

| 华为云类型 | 规格 | 推荐阿里云实例 | 阿里云规格 | 说明 |
|-----------|------|--------------|-----------|------|
| s6.xlarge.2 | 4C/8G | ecs.c7.xlarge | 4C/8G | 计算型 |
| s6.xlarge.4 | 4C/16G | ecs.g7.xlarge | 4C/16G | 通用型 |
| s6.2xlarge.2 | 8C/16G | ecs.c7.2xlarge | 8C/16G | 计算型 |
| s6.2xlarge.4 | 8C/32G | ecs.g7.2xlarge | 8C/32G | 通用型 |
| m6.2xlarge.8 | 8C/64G | ecs.r7.2xlarge | 8C/64G | 内存型 |
| c6s.xlarge.2 | 4C/8G | ecs.c7.xlarge | 4C/8G | 计算型 |
| r6.xlarge.8 | 4C/32G | ecs.r7.xlarge | 4C/32G | 内存型 |

---

## 3. 映射注意事项

### 3.1 规格不完全匹配处理

跨云实例类型映射时，很难做到完全一致。以下为常见差异处理策略：

1. **内存差异**: 阿里云通用型g系列固定1:4内存比，若源云实例内存比不同，优先选择 >= 源规格的阿里云实例
2. **网络带宽**: 阿里云标注的"突发带宽"与AWS的"网络性能"计算方式不同，需实际压测验证
3. **本地盘**: 本地SSD实例的盘容量和IOPS需逐一比对，不可仅看vCPU/内存
4. **GPU型号**: GPU实例务必确认GPU型号和显存一致，不同GPU性能差异巨大

### 3.2 代次选择建议

- **新项目**: 优先选择第8代（g8i/c8i/r8i），性能更优、价格更优
- **兼容老系统**: 如需特定OS/驱动兼容性，可能需要回退到第6/7代
- **成本优化**: AMD系列（g8a/c8a/r8a）通常比Intel系列便宜10-20%，性能接近
