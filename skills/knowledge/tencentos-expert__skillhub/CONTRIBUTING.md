# 贡献指南

感谢您对 TencentOS Expert Skills 项目的贡献！本文档将指导您如何参与项目开发。

## 🎯 贡献方式

### 1. 添加新的诊断能力

项目采用「单 Skill + references 按需加载」架构，所有诊断能力以 `references/` 文档形式存在。

#### 步骤 1：创建 reference 文档

在 `references/` 目录下，按业务域选择对应子目录创建文档（disk/ network/ performance/ memory/ system/ security/ recovery/ docs/）：

```bash
# 命名规范：小写字母和连字符
touch references/<domain>/<capability-name>.md
```

#### 步骤 2：注册能力

在 `SKILL.md` 中完成以下注册：

1. 在 **能力索引表** 对应分类中添加新条目（模块 ID、能力名、匹配关键词、文档路径）
2. 在 **文档路径映射** 表中添加映射关系
3. 在 **文档完整导航地图** 中注册文件职责和触发时机
4. 如有相关场景，在 **场景快速导航** 表中补充

#### 步骤 3：添加辅助资源（可选）

- 如需脚本支持，在 `scripts/` 目录添加脚本
- 如有子流程文档，在 `references/` 添加子文档并在 SKILL.md 中注册

#### 步骤 4：更新 README

在 `README.md` 的对应分类中添加新能力条目。

#### 步骤 5：提交 Pull Request

```bash
git checkout -b feature/add-<capability-name>
git add .
git commit -m "feat: 添加 <capability-name> 诊断能力"
git push origin feature/add-<capability-name>
```

### 2. 改进现有能力

- 修复文档错误或过时信息
- 优化诊断流程和 Prompt 质量
- 补充匹配关键词，提高路由准确率
- 完善异常处理和边界情况

### 3. 贡献辅助脚本

- 在 `scripts/` 目录添加通用诊断脚本
- 在 `SKILL.md` 的文档路径映射中注册脚本关联

## 📋 文档编写规范

### reference 文档结构

每个 `references/<name>.md` 应包含：

1. **适用场景**：说明该能力的适用范围和触发条件
2. **诊断步骤**：将诊断流程拆分为清晰的步骤
3. **命令示例**：提供具体的命令和预期输出
4. **输出解读**：说明如何解读命令输出和关键指标
5. **常见问题**：处理常见的异常情况和 FAQ
6. **报告模板**：定义诊断结论的输出格式

### 脚本编写规范

- 使用 Bash 或 Python 编写
- 脚本头部添加用途说明和使用方法注释
- 处理错误情况，使用合适的退出码
- 支持 `--help` 参数
- 考虑 TencentOS 2/3/4 的版本差异

## 🔍 代码审查

所有 Pull Request 需要通过以下检查：

1. **格式验证**：文档格式正确、链接有效
2. **代码审查**：至少一位 Reviewer 批准
3. **功能测试**：新增能力需要验证诊断流程可正常执行

## 📝 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Type 类型

- `feat`: 新功能（新诊断能力）
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```
feat: 添加 cpu-flamegraph 火焰图诊断能力

- 添加 references/performance/cpu-flamegraph.md 主诊断文档
- 添加 references/performance/cpu-flamegraph-perf.md perf 降级方案
- 在 SKILL.md 中注册能力索引和文档映射

Closes #123
```

## ❓ 常见问题

### Q: 如何确定能力应该属于哪个分类？

参考 SKILL.md 中的分类体系：

- **磁盘与存储**：磁盘空间、分区、文件系统、LVM、健康检测
- **网络**：连通性、丢包、延迟
- **性能分析**：CPU、系统调用、调度、中断、文件IO、内存
- **系统管理**：日志、服务、时间同步、软件包、软件源
- **安全**：安全基线、CVE 漏洞
- **故障恢复**：kdump、crash dump
- **产品文档**：TencentOS 官方文档查询

### Q: 如何测试我的改动？

```bash
# 运行基础验证测试
bash tests/test.sh
```

## 📞 联系方式

如有问题，请通过以下方式联系：

- 提交 [Gitee Issue](https://gitee.com/OpenCloudOS/tencentos-expert-skills/issues)
