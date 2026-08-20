---
name: git-github
description: Flutter 项目的 Git 和 GitHub 操作，包括分支管理、提交、推送、创建仓库、Pull Request、合并流程。当用户提到"git"、"github"、"提交"、"推送"、"分支"、"PR"、"合并"、"仓库"、"rebase"时使用此 skill。
install_source: official
install_method: download
skill_id: official_8hDRc8LN
enabled_at: 1787232436518
version: 1.0.0
name_zh: GitHub开发
---

# Git 和 GitHub 操作 (Flutter 项目)

提供 Flutter 项目的 Git 版本控制和 GitHub 仓库管理的完整工作流。

## 🤖 使用子代理执行（强烈推荐）

**为避免消耗主窗口上下文，所有 Git 操作应通过子代理执行**

### 为什么使用子代理

Git 操作（尤其是提交、PR 创建）需要：

- 读取 `git status`、`git diff`、`git log` 输出（大量 token）
- 分析变更内容、编写提交信息（上下文推理）
- 处理完后这些中间信息不再需要保留

**使用子代理的好处**：

- ✅ 节省主窗口 50-80% 的上下文消耗
- ✅ 保持主对话历史简洁
- ✅ Git 操作结果简洁返回，不污染主上下文
- ✅ 多个 Git 任务可并行执行

### 如何触发子代理

**用户请求示例**（会自动触发此 skill）：

```
"git提交当前分支的变更"
"创建PR合并到main"
"rebase到最新main分支"
"推送代码到远程"
```

**Claude 行为**：

1. **自动使用 Task 工具** 启动 `general-purpose` 子代理
2. 子代理在独立上下文中执行所有 Git 操作
3. 完成后向主窗口返回简洁结果（提交 hash、PR URL 等）
4. 主窗口继续保持低上下文消耗

### 子代理执行模板

当收到 Git 操作请求时，应该：

```typescript
// ❌ 错误：直接在主窗口执行
Bash('git status')
Bash('git diff')
// ... 消耗大量主窗口 token

// ✅ 正确：启动子代理执行
Task({
  subagent_type: 'general-purpose',
  description: '提交当前分支变更',
  prompt: `
请执行以下 Git 操作：

1. 查看当前变更状态（git status、git diff）
2. 分析变更内容并编写符合规范的提交信息
3. 使用 Conventional Commits 格式创建提交
4. 添加 Claude Code 签名
5. 返回提交 hash 和摘要

遵循 .claude/skills/git-github/SKILL.md 中的规范。
  `,
})
```

### 适合子代理执行的任务

| Git 操作                 | 推荐方式  | 原因                                        |
| ------------------------ | --------- | ------------------------------------------- |
| 提交变更 (`git commit`)  | 🤖 子代理 | 需读取 diff、status、log，消耗大量 token    |
| 创建 PR (`gh pr create`) | 🤖 子代理 | 需分析完整变更历史，编写 PR 描述            |
| Rebase 操作              | 🤖 子代理 | 可能需处理冲突，中间状态复杂                |
| 合并分支                 | 🤖 子代理 | 同上                                        |
| 查看简单状态             | 📝 主窗口 | 输出少（如 `git branch`、`gh auth status`） |

---

## ⚠️ 核心原则

**禁止直接修改 main 分支！**

- main 分支只能通过 PR 合并，不允许直接 push
- 合并前必须：
  1. ✅ 通过质量检测 (`pnpm quality`)
  2. ✅ 无冲突（已 rebase 到最新 main）
  3. ✅ PR 审核通过
- 使用 squash merge 保持提交历史整洁

## 分支命名规范

- `main` - 主分支，保持稳定可发布状态
- `feature/<name>` - 功能分支，如 `feature/user-auth`
- `fix/<name>` - 修复分支，如 `fix/login-bug`
- `hotfix/<name>` - 紧急修复分支
- `refactor/<name>` - 重构分支
- `docs/<name>` - 文档更新分支

## Feature 分支合并流程

**原则：先 rebase，后 PR，保持线性历史**

### 完整流程

```bash
# 1. 创建功能分支
git checkout main
git pull origin main
git checkout -b feature/your-feature

# 2. 开发过程中定期同步 main
git fetch origin main
git rebase origin/main

# 3. 完成开发后确保代码质量
flutter analyze
dart format .
flutter test

# 4. Rebase 到最新 main
git fetch origin main
git rebase origin/main

# 5. 解决冲突（如有）
# 编辑冲突文件后：
git add <conflicted-files>
git rebase --continue

# 6. 强制推送（rebase 后必须 force push）
git push --force-with-lease origin feature/your-feature

# 7. 创建 PR
gh pr create --base main --head feature/your-feature \
  --title "feat: 功能描述" \
  --body "$(cat <<'EOF'
## Summary
- 变更点1
- 变更点2

## Test plan
- [ ] 测试项1
- [ ] 测试项2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

# 8. 合并前检查清单
# ✅ flutter analyze 通过
# ✅ flutter test 通过
# ✅ 已 rebase 到最新 main，无冲突
# ✅ PR 已创建并审核通过

# 9. 合并 PR（推荐 squash merge）
gh pr merge <pr-number> --squash --delete-branch

# 10. 合并后清理
git checkout main
git pull origin main
```

## 提交信息规范

**格式**：`<type>(<scope>): <subject>`

### 类型说明

| 类型     | 说明                    |
| -------- | ----------------------- |
| feat     | 新功能                  |
| fix      | 修复 bug                |
| docs     | 文档变更                |
| style    | 代码格式（不影响逻辑）  |
| refactor | 重构（非新功能/非修复） |
| perf     | 性能优化                |
| test     | 测试相关                |
| build    | 构建/依赖变更           |
| ci       | CI 配置变更             |
| chore    | 其他杂项                |

### 提交示例

```bash
# 简单提交
git commit -m "feat: 添加用户登录功能"

# 带 scope
git commit -m "fix(api): 修复请求超时处理"

# 完整提交（使用 HEREDOC）
git commit -m "$(cat <<'EOF'
feat(auth): 添加 JWT token 刷新机制

- 添加 token 过期检测
- 实现自动刷新逻辑
- 更新请求拦截器

Closes #123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## 冲突解决策略

1. **pubspec.yaml 冲突**：保留较新的依赖版本，确保兼容性
2. **pubspec.lock 冲突**：选择一方后重新 `flutter pub get` 生成
3. **代码冲突**：根据业务逻辑手动合并，保留两边有用的改动
4. **配置文件冲突**：优先保留 main 分支的结构，合并 feature 的新增内容
5. **资源文件冲突**：检查 assets 和图片文件，避免覆盖

## PR 规范

### 标题格式

```
<type>(<scope>): <description>
```

示例：

- `feat: 添加用户认证模块`
- `fix(auth): 修复登录状态丢失问题`
- `docs: 更新 README 安装说明`

### PR 内容模板

```markdown
## Summary

- 简要描述变更内容（1-3 点）

## Test plan

- [ ] 验证项1
- [ ] 验证项2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## GitHub 操作 (gh CLI)

### 认证检查

```bash
gh auth status
```

### 创建仓库

```bash
# 创建私有仓库并推送
gh repo create <repo-name> --private --source=. --push

# 创建公开仓库
gh repo create <repo-name> --public --source=. --push

# 设置默认分支
gh repo edit --default-branch main
```

### PR 操作

```bash
# 列出 PR
gh pr list

# 查看 PR 详情
gh pr view <pr-number>

# 查看 PR 状态（JSON 格式）
gh pr view <pr-number> --json state,mergedAt

# Squash 合并并删除分支
gh pr merge <pr-number> --squash --delete-branch

# 普通合并
gh pr merge <pr-number> --merge

# Rebase 合并
gh pr merge <pr-number> --rebase
```

## 紧急修复流程

```bash
# 从 main 创建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 修复后直接推送并创建 PR
git push -u origin hotfix/critical-bug
gh pr create --base main --title "hotfix: 紧急修复描述"

# 合并后同步到其他开发分支
git checkout feature/xxx
git rebase main
```

## 常用命令速查

### 分支管理

```bash
git branch -a                    # 查看所有分支
git checkout -b feature/xxx      # 创建并切换分支
git branch -d feature/xxx        # 删除本地分支
git branch -m master main        # 重命名分支
```

### 远程操作

```bash
git remote -v                    # 查看远程仓库
git push -u origin main          # 推送并设置上游
git push --force-with-lease      # 安全强制推送
git pull --rebase origin main    # 拉取并 rebase
```

### 撤销操作

```bash
git reset --soft HEAD~1          # 撤销提交，保留更改
git reset --hard HEAD~1          # 完全撤销（慎用）
git commit --amend -m "新消息"    # 修改最近提交信息
```

### 查看历史

```bash
git log --oneline -10            # 简洁历史
git log --oneline --graph --all  # 图形化历史
git diff main..HEAD              # 查看与 main 的差异
```

## 安全提醒

- **🚫 禁止直接 push 到 main 分支** - 只能通过 PR 合并
- **🚫 禁止合并未通过质量检测的代码** - 必须先 `flutter analyze` 和 `flutter test`
- **🚫 禁止合并有冲突的 PR** - 必须先 rebase 解决冲突
- **永远不要** 提交敏感信息 (.env, android/key.properties, ios/*.p12 等)
- **永远不要** 对 main/master 使用 `--force` 推送
- **永远不要** 修改已推送到远程的公共分支历史
- **永远不要** 提交 build/ 目录和编译产物
- 使用 `--force-with-lease` 代替 `--force`（仅限 feature 分支）
- 使用 `.gitignore` 排除不需要版本控制的文件（build/, .dart_tool/, *.g.dart 等）
