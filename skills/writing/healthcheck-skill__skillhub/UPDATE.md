# OpenClaw HealthCheck Skill - 更新流程指南

## 🔄 版本更新流程

### 第一步：本地代码更新
1. 修改 SKILL.md 中的版本号
2. 更新 CHANGELOG.md
3. 测试新功能

### 第二步：创建 ZIP 包
```bash
cd /workspace/projects/workspace/healthcheck-skill
zip -r "/tmp/healthcheck-vX.Y.Z.zip" . \
    -x "*.git*" \
    -x "healthcheck-v*.zip" \
    -x "PLAN-*.md" \
    -x "RELEASE*.md" \
    -x "CHANGELOG_DRAFT.md" \
    -x "memory/*.md" \
    -x "!memory/feedback-and-roadmap.md" \
    -x "README_GITHUB.md" \
    -x "*.log" \
    -x "api/data/*.json" \
    -x "dashboard/*" \
    -x "{scripts/*" \
    -x "PUBLISHING.md" \
    -x "XIAPING_UPDATE_REPORT.md" \
    -x "SECURITY_AUDIT*.md" \
    -x "SECURITY_FIX_SUMMARY.md" \
    -x "SECURITY_STATEMENT.md" \
    -x "VERSION_RELEASE_NOTES.md"
```

### 第三步：更新 GitHub
```bash
cd /workspace/projects/workspace/healthcheck-skill
git add .
git commit -m "Release vX.Y.Z: 更新内容描述"
git tag vX.Y.Z
git push origin main --tags
```

### 第四步：通知更新
告诉 luck："技能已更新到 vX.Y.Z，请更新 GitHub"

---

## 📊 版本号管理

### 当前版本
- **v4.6.8**（2026-04-14发布）

### 版本发布规则
- 每次更新前增加版本号：X.Y.Z → X.Y.(Z+1)
- 版本号格式：主版本.次版本.修订版本
- 例如：4.6.8 → 4.6.9 → 4.7.0 → 4.7.1

---

## 🔗 平台同步策略

### 当前平台
| 平台 | 状态 | 说明 |
|------|------|------|
| **GitHub** | ✅ 使用中 | 每次更新同步 |
| **虾评平台** | ✅ 使用中 | 每次更新上传 ZIP + 自动递增版本 |
| **SkillHub** | ❌ 已取消 | 不再使用 |
| **ClawHub** | ⏸️ 待调研 | 暂不使用 |

### 版本号同步
- **GitHub**: 完全控制，每次更新手动提交
- **虾评平台**: 每次上传后自动 +0.0.1，需要立即更新本地版本号
- **版本号一致性**：确保本地版本号与平台一致

---

## 📋 更新检查清单

### 更新前
- [ ] 确认更新内容和功能点
- [ ] 更新 SKILL.md 版本号
- [ ] 更新 CHANGELOG.md
- [ ] 测试新功能
- [ ] 创建 ZIP 包

### 更新后
- [ ] 提交到 GitHub
- [ ] 推送代码
- [ ] 打 Tag
- [ ] 上传到虾评平台
- [ ] 立即更新本地版本号
- [ ] 验证平台版本号一致

---

## 📦 技能包生成命令

```bash
# 创建 ZIP 包
cd /workspace/projects/workspace/healthcheck-skill
zip -r "/tmp/healthcheck-vX.Y.Z.zip" . \
    -x "*.git*" \
    -x "healthcheck-v*.zip" \
    -x "PLAN-*.md" \
    -x "RELEASE*.md" \
    -x "CHANGELOG_DRAFT.md" \
    -x "memory/*.md" \
    -x "!memory/feedback-and-roadmap.md" \
    -x "README_GITHUB.md" \
    -x "*.log" \
    -x "api/data/*.json" \
    -x "dashboard/*" \
    -x "{scripts/*" \
    -x "PUBLISHING.md" \
    -x "XIAPING_UPDATE_REPORT.md" \
    -x "SECURITY_AUDIT*.md" \
    -x "SECURITY_FIX_SUMMARY.md" \
    -x "SECURITY_STATEMENT.md" \
    -x "VERSION_RELEASE_NOTES.md"
```

---

## 🔍 常见问题

### Q1: GitHub 推送失败？
**A**:
```bash
cd /workspace/projects/workspace/healthcheck-skill
git status  # 查看当前状态
git pull origin main  # 先拉取最新代码
git push origin main --tags --force  # 强制推送
```

### Q2: 虾评平台版本号不一致？
**A**:
- 虾评平台每次上传后会自动 +0.0.1
- 上传后立即更新本地 SKILL.md 版本号
- 确保三个平台版本号一致

### Q3: 如何查看 GitHub 版本历史？
**A**:
```bash
cd /workspace/projects/workspace/healthcheck-skill
git log --oneline --tags
git tag -l
```

---

## 📞 联系方式

**问题反馈**：
- GitHub Issues: https://github.com/zhanghaidong-dalian/openclaw-healthcheck-skill/issues
- 飞书私信：haidong

**更新通知**：
- 每次更新后告诉我："技能已更新到 vX.Y.Z，请更新 GitHub"
- 我会立即执行 Git 提交和推送

---

*最后更新: 2026-04-16*
*状态: SkillHub 已取消，GitHub 作为主要发布平台*
