---
name: skill-vetter-pro
version: 1.0.0
description: "🔒 专业级技能安全审查系统。四维安全审查 + 哈希链完整性校验 + 子会话稳定推送。触发词：审查技能、全面审查、深度安全审查、vetting、skill安全检查"
---

# Skill Vetter Pro 🔒🛡️

**专业级技能安全审查系统**

## 核心能力

- **四维安全审查**：静态扫描 → 行为监控 → 完整性校验 → 依赖 CVE
- **子会话推送保障**：强制 sessions_yield 绑定，解决推送失败问题
- **完整 SOP**：六阶段全链路审查，从触发到记录可追溯

## When to Use

- 安装任何 skill 前必须审查
- 第三方来源的 skill 必须全面审查
- 官方 skill 常规复审
- 收到安全告警后复审

## 四维审查体系

| 维度 | 工具 | 作用 | 可选 |
|------|------|------|------|
| 维度一 | `skill_vet.py`（AST） | 危险代码模式检测 | 必选 |
| 维度二 | `skill_behavior_monitor.py`（strace） | 运行时系统调用追踪 | 可选 |
| 维度三 | `skill_integrity_checker.py`（SHA256） | 审查后文件篡改检测 | 推荐 |
| 维度四 | `dependency_cve_checker.py`（OSV API） | 第三方依赖漏洞审计 | 可选 |

## 触发词

- "审查技能"、"全面审查"、"深度安全审查"
- "检查这个skill"、"帮我审核"
- "vetting"、"skill安全检查"
- "查这个skill有没有风险"

---

## 📋 完整执行流程 SOP

### 阶段一：接收与解析

**触发词匹配后**：

1. 确认审查目标路径
2. 判断触发类型（首次审查 / 复审 / 快速审查）
3. 根据 `policy/default-policy.md` 判断需要哪些维度

### 阶段二：依赖检查

```bash
# 检查 Docker
docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker unavailable"

# 检查镜像
docker images python:3-alpine --format "{{.Repository}}" | grep -q alpine && echo "Image OK" || echo "Image not found"

# 检查脚本
ls /home/strong/.openclaw/workspace/skills/skill-vetter-pro/scripts/skill_vet.py
```

**依赖缺失时的处理**：

| 缺失项 | 处理方式 |
|--------|---------|
| Docker | 告知用户安装，停止执行 |
| 镜像 | 自动拉取（`docker pull python:3-alpine`） |
| 脚本 | 报错，技能文件损坏 |

### 阶段三：子会话执行审查

**【关键】sessions_spawn 指令**：

```bash
sessions_spawn(
  task="对 /home/strong/.openclaw/workspace/skills/[目标skill] 进行完整安全审查。

【强制要求】
- 所有步骤完成后，必须调用 sessions_yield 推送结果
- sessions_yield 是工具调用，不是描述，禁止仅在回复中提及而不调用

【步骤1】来源验证
ls /home/strong/.openclaw/workspace/skills/[目标skill]/
head -10 /home/strong/.openclaw/workspace/skills/[目标skill]/SKILL.md
cat /home/strong/.openclaw/workspace/skills/[目标skill]/_meta.json 2>/dev/null

【步骤2】维度一：静态扫描（必须）
docker run --rm \
  -v /home/strong/.openclaw/workspace/skills/[目标skill]:/skill:ro \
  -v /home/strong/.openclaw/workspace/skills/skill-vetter-pro/scripts/skill_vet.py:/vet.py:ro \
  python:3-alpine \
  python3 /vet.py /skill

【步骤3】维度三：哈希清单生成（推荐）
python3 /home/strong/.openclaw/workspace/skills/skill-vetter-pro/scripts/skill_integrity_checker.py \
  --save /home/strong/.openclaw/workspace/skills/[目标skill] \
  /home/strong/.openclaw/workspace/skills/skill-vetter-pro/records/[目标skill]-manifest.json

【步骤4】维度四：依赖CVE检查（如有依赖文件）
python3 /home/strong/.openclaw/workspace/skills/skill-vetter-pro/scripts/dependency_cve_checker.py \
  /home/strong/.openclaw/workspace/skills/[目标skill]

【步骤5】逐文件人工审查
读取所有 .py .sh 文件，参考 references/checklist.md 逐项检查。

【步骤6】生成完整报告
格式参考 references/vetting_report_template.md

【步骤7】追加审查日志
将结论追加到 records/vetting-log.md

【步骤8】强制推送（不可跳过）
调用 sessions_yield 工具：
sessions_yield(message="[完整报告全文，不含任何占位符]")
",
  runtime="subagent",
  sessionTarget="isolated"
)
```

### 阶段四：报告汇总与裁决

| 风险等级 | 裁决 | 动作 |
|----------|------|------|
| 🟢 LOW | ✅ 可安全安装 | 直接执行 |
| 🟡 MEDIUM | ⚠️ 谨慎安装 | 告知用户，确认后执行 |
| 🔴 HIGH | ⚠️ 需人工审查 | 输出完整报告，明确要求批准 |
| ⛔ EXTREME | ❌ 拒绝安装 | 拒绝执行，说明原因 |

### 阶段五：安装前完整性校验

```bash
python3 skill_integrity_checker.py \
  --verify /home/strong/.openclaw/workspace/skills/[目标skill] \
  /home/strong/.openclaw/workspace/skills/skill-vetter-pro/records/[目标skill]-manifest.json

# 一致 → 执行安装
# 不一致 → 拒绝安装，报告被篡改
```

### 阶段六：记录持久化

```bash
# 审查记录已自动追加到 records/vetting-log.md
# 哈希清单已保存到 records/[目标skill]-manifest.json
```

---

## 工具脚本说明

### skill_vet.py（AST扫描器）

**自检结果**：21/21 全通过（13 恶意样本全检出，8 良性样本零误报）

**检测能力**：

| 威胁类型 | 示例 | 等级 |
|---------|------|------|
| eval/exec + 外部输入 | `eval(user_input)` | CRITICAL |
| f-string exec | `exec(f"print({x})")` | CRITICAL |
| `__builtins__['eval']` | `_eval = __builtins__['eval']` | CRITICAL |
| `__import__(变量)` | `__import__(mod)` | HIGH |
| base64 解码 | `base64.b64decode(x)` | HIGH |
| curl 管道到 bash | `curl.sh \| bash` | CRITICAL |
| 读取 /etc/passwd | `open('/etc/passwd')` | HIGH |
| 读取 SSH 私钥 | `expanduser('~/.ssh/id_rsa')` | HIGH |
| requests POST | `requests.post(url, data)` | HIGH |
| crontab 持久化 | `crontab -l ... \| crontab` | HIGH |

### skill_integrity_checker.py（SHA256 哈希链）

```bash
# 审查时保存
--save <skill路径> [manifest.json]

# 安装前验证
--verify <skill路径> <manifest.json>
```

### dependency_cve_checker.py（OSV API CVE 检查）

支持：requirements.txt、package.json、Gemfile、go.mod、composer.json、Cargo.toml

### skill_behavior_monitor.py（strace 行为监控）

```bash
# 在有 strace 的环境中使用
python3 skill_behavior_monitor.py <skill路径> <执行命令>
```

监控：系统调用、文件修改、进程创建、网络连接

### scanner_self_test.py（扫描器自检）

```bash
# 定期验证扫描器自身可信度
python3 scanner_self_test.py [skill_vet.py路径]

# 期望结果：21/21 全部通过
```

---

## 文件结构

```
skill-vetter-pro/
├── SKILL.md
├── _meta.json
├── CHANGELOG.md
├── scripts/
│   ├── skill_vet.py              # AST扫描器（21/21自检通过）
│   ├── skill_integrity_checker.py # SHA256哈希链
│   ├── dependency_cve_checker.py  # OSV API CVE检查
│   ├── skill_behavior_monitor.py  # strace行为监控
│   ├── scanner_self_test.py       # 扫描器自检
│   └── skill_checker.py          # 正则辅助扫描
├── references/
│   ├── checklist.md               # 四阶段审查清单
│   └── vetting_report_template.md # 报告模板
├── records/
│   └── vetting-log.md            # 审查历史日志
└── policy/
    └── default-policy.md         # 默认策略规则
```

---

## 记录层

所有审查结论自动追加到 `records/vetting-log.md`，包含：
- 审查时间、skill 名称、版本
- 裁决结果、风险等级、简要原因
- 报告摘要

---

## 策略层

`policy/default-policy.md` 定义：

| 规则类型 | 内容 |
|---------|------|
| 触发规则 | 什么情况必须审、什么可以跳过 |
| 隔离规则 | 什么情况必须隔离子会话 |
| 裁决规则 | 风险等级对应的动作 |
| Docker规则 | 沙箱执行规范 |

---

*安全不是功能，而是基础。* 🔒
