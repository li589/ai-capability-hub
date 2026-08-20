# 风险分类体系（12 维，来源：Snyk ToxicSkills + CSA + 腾讯科恩）

> 钟馗基于 14 篇前沿论文（含 CSA 3984 Skill 审计 / 腾讯科恩），定义了 12 个核心风险分类维度。前 10 类来自学术界共识，R11/R12 由腾讯科恩在 Skill 生态真实攻击中首次系统揭露。

## R1 | 提示注入（Prompt Injection）

- **攻击向量**：SKILL.md 中隐藏越狱指令，覆盖 / 污染 Agent 安全护栏
- **检测方法**：7 种注入签名匹配（core/patterns.json C1_injection）
- **危害**：Agent 行为被远程控制或信息泄露
- **一票否决**：是
- **来源**：Greshake 2023

## R2 | 恶意代码执行（Code Execution）

- **攻击向量**：辅助脚本中含反弹 Shell / 文件篡改 / 远控逻辑
- **检测方法**：动态代码执行模式匹配（core/patterns.json C_dangerous_cmd / S1_spawn）
- **危害**：受害主机被控制
- **一票否决**：是
- **来源**：Snyk

## R3 | 凭证窃取（Credential Theft）

- **攻击向量**：诱导 Agent 读取凭据文件（.ssh/.aws/.env/API Key）后外传
- **检测方法**：凭证访问正则模式（core/patterns.json C3_credential）
- **危害**：凭据泄露导致横向移动（利基 RAG 检索）
- **一票否决**：是
- **来源**：CSA

## R4 | 依赖投毒（Dependency Poisoning）

- **攻击向量**：requirements.txt / package.json 引入恶意包（拼写欺诈 / 版本恶意回退）
- **检测方法**：依赖语义特征提取 + 包名 Levenshtein 距离检测
- **危害**：供应链污染扩散
- **来源**：Snyk, AgentPoison

## R5 | 数据外传（Data Exfiltration）

- **攻击向量**：诱导 Agent 读取敏感文件后通过 webhook 外发
- **检测方法**：外传目标模式（core/patterns.json C4_exfiltration）
- **危害**：数据泄露
- **一票否决**：是
- **来源**：CSA

## R6 | 权限提升（Privilege Escalation）

- **攻击向量**：Skill 声明过宽权限，后续指令滥用（读文件 -> 命令执行链）
- **检测方法**：权限声明自动化审计（core/patterns.json C6_privilege）
- **危害**：Agent 能力失控
- **来源**：MiniScope

## R7 | 持久化后门（Persistence）

- **攻击向量**：修改启动项 / 计划任务 / cron / shell 配置
- **检测方法**：持久化路径模式（core/patterns.json C7_persistence）
- **危害**：重启后攻击持续
- **一票否决**：是
- **来源**：Snyk

## R8 | 隐蔽指令（Covert Instruction）

- **攻击向量**：Unicode 零宽字符 / 同形异义字 / 条件触发 / 时间门控 / 多层编码
- **检测方法**：零宽字符正则 + Base64 反解审计；Layer 2 行为模拟 + 模糊测试
- **检测难度**：极高。当前扫描器仅有 < 10% 能完整检测 R8 级别攻击（CSA 2026）
- **来源**：CSA

## R9 | 数据泄露与隐私违规（Data Leak & Privacy）

- **攻击向量**：Skill 在日志 / 缓存 / 第三方分析中收集用户数据，未脱敏 PII
- **检测方法**：正则检测 email/phone/ID card 明文输出模式
- **危害**：违反 GDPR/PIPL
- **来源**：CSA

## R10 | 有害输出与内容合规（Harmful Output）

- **攻击向量**：指令生成暴力 / 违法 / 歧视性内容，或完整复述版权保护文本
- **检测方法**：内容安全关键词库 + 复述指令模式匹配
- **危害**：法律风险 + 合规风险
- **来源**：CSA

## R11 | 外部信息源投毒（External Source Poisoning）

- **攻击向量**：攻击者注册 AI 工具品牌近似域名，通过 SEO 污染智能体检索结果，使智能体通过 web search 执行仿冒站中的恶意指令
- **检测方法**：外部信息源校验（域名白名单 -> 威胁情报比对 -> Web Trust 信誉评分）
- **检出率**：Layer 1 检出率约 15%（仅靠静态规则，无法完全替代真实检索）
- **来源**：腾讯科恩 2026

## R12 | 智能体行为级漏洞（Agent Behavioral Vulnerability）

- **攻击向量**：智能体面对安全拦截时盲目重试同 URL / 工具枚举绕过黑名单 / 用户授信后再次重投
- **检测方法**：Layer 2 行为模拟（拦截绕过 + 持久化污染场景）
- **检出率**：Layer 1+2 综合检出率约 23%（T20/T21 场景）
- **来源**：腾讯科恩 2026

## 关键数据

| 来源 | 审计规模 | 缺陷率 | 恶意载荷 | 关键发现 |
|:---|:---|:---|:---|:---|
| CSA 报告 | 3984 Skill | 36.82% | 76 个 | 扫描器一致性 < 40% |
| Snyk 博客 | 未公开 | — | — | R4 依赖投毒为主要威胁面 |
| 腾讯科恩 | 主流 Skill 平台 | — | — | R11/R12 威胁面确认：81.7% Skill 携带外部信息源引用且无校验，R12 拦截绕过成功率 37%+ |
