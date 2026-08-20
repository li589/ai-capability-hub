# FDE前置部署环境验证清单

> 本文档为FDE部署专家技能的补充参考，包含环境部署后的完整验证清单、通过标准和故障排查步骤。

---

## 1. 网络连通性验证

### 1.1 专线/VPN通道

| 编号 | 检查项 | 验证命令/方法 | 通过标准 | 不通过排查 |
|------|--------|---------------|----------|------------|
| N-01 | 专线物理连接状态 | 高速通道控制台 → 物理专线 | 状态=Enabled | 联系运营商检查光纤/端口 |
| N-02 | VPN隧道状态 | VPN网关控制台 → IPsec连接 | 状态=已连接 | 检查IKE/IPsec参数是否匹配 |
| N-03 | 专线延迟 | `ping -c 100 目标端内网IP` | 延迟<5ms，丢包率=0 | 检查专线带宽是否拥塞 |
| N-04 | VPN延迟 | `ping -c 100 目标端内网IP` | 延迟<20ms，丢包率<0.1% | 检查公网质量，考虑切换线路 |
| N-05 | 带宽达标 | `iperf3 -c 目标端IP -t 30` | 实测带宽≥标称80% | 检查QoS策略/限速配置 |
| N-06 | CEN云企业网路由 | CEN控制台 → 路由信息 | 路由条目正确，无黑洞 | 检查VPC是否加入CEN |
| N-07 | 跨VPC通信 | 源端ECS → ping 目标端ECS内网IP | 可达，延迟稳定 | 检查路由表+安全组 |
| N-08 | DNS解析 | `nslookup 目标端域名` | 解析正确 | 检查DNS服务器配置/PrivateZone |

**网络连通性测试脚本模板：**

```bash
#!/bin/bash
# FDE网络连通性验证脚本

TARGET_IPS=("10.0.1.10" "10.0.2.20" "10.0.3.30")  # 目标端关键IP
TARGET_PORTS=(22 3306 6379 27017 9092 873)          # 迁移所需端口

echo "=== FDE 网络连通性验证 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

for ip in "${TARGET_IPS[@]}"; do
    echo "--- 测试 $ip ---"
    
    # Ping测试
    ping_result=$(ping -c 10 -W 2 $ip 2>&1)
    packet_loss=$(echo "$ping_result" | grep "packet loss" | awk '{print $6}')
    avg_rtt=$(echo "$ping_result" | grep "avg" | awk -F'/' '{print $5}')
    echo "  Ping: 丢包率=$packet_loss, 平均延迟=${avg_rtt}ms"
    
    # 端口测试
    for port in "${TARGET_PORTS[@]}"; do
        timeout 3 bash -c "echo > /dev/tcp/$ip/$port" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  端口 $port: ✅ 可达"
        else
            echo "  端口 $port: ❌ 不可达"
        fi
    done
    echo ""
done
```

---

## 2. 安全组规则验证

| 编号 | 检查项 | 验证方法 | 通过标准 | 不通过排查 |
|------|--------|----------|----------|------------|
| SG-01 | 迁移端口放通 | `telnet 目标端IP 端口` | 所有迁移端口可达 | 检查安全组入方向规则 |
| SG-02 | 源端IP白名单 | 安全组控制台 → 入方向规则 | 源端IP/CIDR已添加 | 确认源端出口IP是否正确 |
| SG-03 | DTS服务器IP段 | 安全组控制台 → 入方向规则 | DTS IP段已放通 | 查询DTS文档获取IP段 |
| SG-04 | 安全组出方向 | 安全组控制台 → 出方向规则 | 出方向不限制迁移流量 | 检查是否有自定义出方向限制 |
| SG-05 | 跨安全组通信 | 不同安全组实例互ping | 需要通信的实例间可达 | 配置安全组授权规则 |

---

## 3. 存储权限验证

| 编号 | 检查项 | 验证命令/方法 | 通过标准 | 不通过排查 |
|------|--------|---------------|----------|------------|
| ST-01 | OSS Bucket读写 | `ossutil ls oss://bucket-name/` | 列表成功 | 检查RAM策略/Bucket策略/加密 |
| ST-02 | OSS跨区域复制 | OSS控制台 → 跨区域复制 | 状态=已启用（如需要） | 检查源Bucket和目标Bucket配置 |
| ST-03 | NAS文件系统挂载 | `mount -t nfs NAS地址:/ /mnt/nas` | 挂载成功，可读写 | 检查NAS挂载点+安全组+VPC |
| ST-04 | ESSD云盘挂载 | `lsblk` / `df -h` | 云盘已挂载，可读写 | 检查ECS实例状态和云盘状态 |

**OSS权限验证脚本：**

```bash
#!/bin/bash
# FDE OSS权限验证

BUCKET="oss://target-migration-bucket"

echo "=== OSS权限验证 ==="

# 列表测试
echo -n "列表权限: "
ossutil ls $BUCKET --limited-num 1 > /dev/null 2>&1 && echo "✅" || echo "❌"

# 上传测试
echo -n "上传权限: "
echo "fde-test" > /tmp/fde-test.txt
ossutil cp /tmp/fde-test.txt $BUCKET/fde-test.txt > /dev/null 2>&1 && echo "✅" || echo "❌"

# 下载测试
echo -n "下载权限: "
ossutil cp $BUCKET/fde-test.txt /tmp/fde-test-dl.txt > /dev/null 2>&1 && echo "✅" || echo "❌"

# 删除测试
echo -n "删除权限: "
ossutil rm $BUCKET/fde-test.txt > /dev/null 2>&1 && echo "✅" || echo "❌"

rm -f /tmp/fde-test.txt /tmp/fde-test-dl.txt
```

---

## 4. 迁移工具验证

| 编号 | 检查项 | 验证命令/方法 | 通过标准 | 不通过排查 |
|------|--------|---------------|----------|------------|
| MT-01 | SMC Agent安装 | SMC控制台 → 迁移源 | 迁移源在线 | 检查Agent服务状态和网络 |
| MT-02 | DTS连通性预检 | DTS控制台 → 创建任务 → 预检 | 所有预检项通过 | 按预检失败项逐一修复 |
| MT-03 | ossutil版本 | `ossutil --version` | ≥2.0 | 重新安装最新版 |
| MT-04 | ossutil配置 | `ossutil config` 并测试 | AK/SK有效，可操作 | 检查AK/SK和Endpoint |
| MT-05 | rsync版本 | `rsync --version` | ≥3.1 | 升级rsync版本 |
| MT-06 | DataWorks就绪 | DataWorks控制台 | 工作空间可用，数据源注册 | 检查工作空间和权限 |

**DTS预检失败常见原因与修复：**

| 预检失败项 | 原因 | 修复方法 |
|------------|------|----------|
| 源端连接失败 | 白名单未放通DTS IP | 添加DTS服务器IP段到数据库白名单 |
| binlog未开启 | MySQL binlog关闭 | 修改my.cnf：`log_bin=mysql-bin` |
| binlog格式错误 | binlog非ROW格式 | 修改my.cnf：`binlog_format=ROW` |
| server_id冲突 | 源端和目标端server_id相同 | 修改目标端server_id为不同值 |
| 权限不足 | 迁移账号权限不够 | 授予SELECT,REPLICATION SLAVE,REPLICATION CLIENT |
| 结构迁移失败 | 目标端已有同名库/表 | 清理目标端或使用忽略策略 |

---

## 5. 凭据有效性验证

| 编号 | 检查项 | 验证方法 | 通过标准 | 不通过排查 |
|------|--------|----------|----------|------------|
| CR-01 | RAM子账号权限 | RAM控制台 → 权限策略 | 策略覆盖所有迁移API | 检查自定义策略JSON |
| CR-02 | RAM AK有效性 | `aliyun sts GetCallerIdentity` | 返回正确身份 | 检查AK/SK是否过期/禁用 |
| CR-03 | 源端数据库连接 | `mysql -h 源端IP -u 迁移账号 -p` | 连接成功 | 检查账号密码/白名单/端口 |
| CR-04 | 源端SSH连接 | `ssh user@源端IP` | 登录成功 | 检查密钥/密码/安全组 |

**安全提醒：**
- 验证完成后，立即清理终端历史中的密码信息：`history -c`
- 不在脚本文件中硬编码密码
- 使用DTS/SMC控制台的密码输入框配置凭据，不留存明文

---

## 6. 资源状态验证

| 编号 | 检查项 | 验证方法 | 通过标准 | 不通过排查 |
|------|--------|----------|----------|------------|
| RS-01 | ECS实例状态 | ECS控制台/API | 全部Running | 检查启动失败原因 |
| RS-02 | RDS实例状态 | RDS控制台/API | 全部Running | 检查创建日志 |
| RS-03 | Redis实例状态 | Redis控制台/API | 全部Normal | 检查实例状态 |
| RS-04 | 规格确认 | 各控制台 | 与方案规格一致 | 联系SA确认规格映射 |
| RS-05 | 引擎版本 | RDS/Redis控制台 | 与源端版本兼容 | 检查版本兼容性矩阵 |
| RS-06 | 镜像可用性 | ECS控制台 → 镜像 | 自定义镜像可用 | 检查镜像复制状态 |

---

## 7. 自检报告模板

```markdown
# FDE前置部署环境自检报告

## 基本信息
- 项目名称: [项目名称]
- 自检日期: [YYYY-MM-DD]
- 执行人: [姓名]
- 目标地域: [cn-hangzhou/cn-shanghai/...]

## 自检结果汇总

| 类别 | 检查项数 | 通过 | 不通过 | 通过率 |
|------|----------|------|--------|--------|
| 网络连通性 | 8 | [n] | [n] | [x%] |
| 安全组规则 | 5 | [n] | [n] | [x%] |
| 存储权限 | 4 | [n] | [n] | [x%] |
| 迁移工具 | 6 | [n] | [n] | [x%] |
| 凭据有效性 | 4 | [n] | [n] | [x%] |
| 资源状态 | 6 | [n] | [n] | [x%] |
| **合计** | **33** | **[n]** | **[n]** | **[x%]** |

## 不通过项详情
[逐一列出不通过项、原因和修复计划]

## 结论
- [ ] 全部通过，可移交迁移工程师
- [ ] 存在不通过项，需修复后复检
- [ ] 存在阻塞项，需升级处理

## 签字
- FDE: [签字] [日期]
- 迁移工程师: [签字] [日期]
- 项目经理: [签字] [日期]
```
