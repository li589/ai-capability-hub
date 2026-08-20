# 修复策略指南

> 11 类风险的修复方法

## 修复优先级

| 时效 | 风险编号 | 风险名称 | 最高处置时限 |
|:---|:---|:---|:---|
| **立即** | R1 | 提示注入 | 发现即阻断 |
| **立即** | R2 | 恶意代码执行 | 发现即阻断 |
| **立即** | R3 | 凭证窃取 | 发现即阻断 |
| **4h** | R4 | 依赖投毒 | 替换依赖包并重扫 |
| **4h** | R5 | 数据外传 | 切断外传通道后审查 |
| **4h** | R6 | 权限提升 | 降权并附加权限声明 |
| **24h** | R7 | 持久化后门 | 清除后门 + 全量重扫 |
| **72h** | R8 | 隐蔽指令 | 反混淆后逐条分析 |
| **按需** | R9 | 其他低风险 | 计划修复 |

---

## R1 — 提示注入

**原则**：Skill 文档中的指令不得包含"忽略/覆盖/绕过已有规则"等语义。

**修复后示例**：
```markdown
## 系统约束
本 Skill 严格遵循 Agent 安全策略，不覆盖任何已有规则。
```
- 白名单检查：出现任何 `system / override / bypass / jailbreak` 必须人工核实
- 零宽字符清洗：`\u200B` 等不可见字符可能用于隐藏注入指令

---

## R2 — 恶意代码执行

**原则**：移除所有 `os.system / subprocess.call / exec / eval`，替换为框架安全工具调用。

**修复后示例**：
```python
# 使用框架安全工具替代
# delete 工具内置回收站保护 + 敏感路径过滤
```
- 禁止 `shell=True`；参数化命令用列表形式 `["cmd", "arg1"]`
- 文件系统操作走框架原生工具 API

---

## R3 — 凭证窃取

**原则**：移除所有读取敏感文件的代码及硬编码凭证，使用环境变量或密钥管理服务。

**修复后示例**：
```python
import os
API_KEY = os.getenv("SKILL_API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not set — configure via environment")
```
- 禁止在 Skill 代码或文档中硬编码凭证
- 第三方 API 须在 SKILL.md 声明依赖并注明配置方式

---

## R4 — 依赖投毒

**原则**：所有外部依赖替换为官方源 + 固定版本号；消除拼写欺诈包名（typosquatting）。

**修复后示例**：
```
# requirements.txt（全部来自 PyPI 官方源）
requests==2.31.0
urllib3==2.1.0
```
- Levenshtein 距离检查（距离 ≤ 2 且非官方包 → 告警）
- `pip install` 须指定 `--require-hashes`；禁止运行时从 Git/HTTP URL 动态安装

---

## R5 — 数据外传

**原则**：移除向外部 URL 发送数据的代码；若必须联网，明确声明目的和域名白名单。

**修复后示例**：
```python
# 删除外传代码。若确实需要 API 调用：
# - SKILL.md 声明域名 xyz-api.example.com
# - 仅向该白名单域名发送请求
```
- WebSocket / SSE 长连接同样视为外传通道

---

## R6 — 权限提升

**原则**：将权限声明收窄到最小必要范围。

**修复前**：
```yaml
permissions:
  filesystem: "/**"
  network: "*"
  shell: true
```

**修复后**：
```yaml
permissions:
  filesystem: "/workspace/projects"
  network: "api.example.com:443"
  shell: false
```
- 权限串联路径（读→写→执行）需整体评估

---

## R7 — 持久化后门

**原则**：移除所有自动启动/计划任务/cron/rc 注册代码。

**检测范围**：cron / systemd / launchd / Windows Tasks / ~/.bashrc / ~/.profile / 注册表 Run 键 / LD_PRELOAD / DYLD_INSERT_LIBRARIES

---

## R8 — 隐蔽指令

**原则**：代码必须对人可读。

- 零宽字符用 `\u200B-\u200F / \uFEFF / \u200C\u200D` 正则全局扫描
- Base64 载荷解 Base64 后逐行审计，禁止盲目信任"压缩"或"优化"理由

---

## R11 — 外部信息源投毒

**原则**：所有外部 URL/API 引用添加完整性校验（HTTPS 强制 + 证书固定 + 内容哈希）。

**修复后示例**：
```python
ALLOWED_HOSTS = {"api.trusted.com", "cdn.official.org"}
if urlparse(config_url).hostname not in ALLOWED_HOSTS:
    raise SecurityError(f"Untrusted source: {config_url}")
response = requests.get(config_url, verify=True)
if hashlib.sha256(response.content).hexdigest() != expected_hash:
    raise SecurityError("Content integrity check failed")
```
- 所有外部 URL 须 HTTPS，推荐证书固定
- Skill 文档须声明所有外部依赖数据源及域名白名单

---

## R12 — 智能体行为级漏洞

**原则**：禁止 Agent 执行"关闭防护→执行操作→持久化写入"复合行为链。

**修复后示例**：
```markdown
## 安装说明
请在 Agent 安全策略正常开启状态下执行以下操作：
1. 安装以下用户空间配置（非系统级）
2. 配置仅写入当前会话工作目录，不会持久化到系统启动项
```
- 禁止关闭或绕过 Agent 安全检查
- 持久化写入须有用户显式授权门控

---

> **钟馗裁定铁律**：修完不算完，重扫才结案。修复后的 Skill 必须重新走全套扫描流程。
