# 飞书CLI常见问题

## 目录

1. [安装问题](#安装问题)
2. [授权问题](#授权问题)
3. [使用问题](#使用问题)
4. [权限问题](#权限问题)

---

## 安装问题

### Q1: Node.js 版本过低怎么办？

**问题**: 提示 "Node.js 版本过低，需要 >= 16.0"

**解决方案**:

**macOS**:
```bash
# 使用 Homebrew
brew install node@18

# 或使用 nvm
nvm install 18
nvm use 18
```

**Ubuntu/Debian**:
```bash
# 使用 NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows**:
- 访问 https://nodejs.org/
- 下载并安装 LTS 版本

---

### Q2: npm 权限不足怎么办？

**问题**: 提示 "EACCES permission denied"

**解决方案**:

**方案1: 使用 sudo（不推荐）**:
```bash
sudo npm install -g @larksuite/cli
```

**方案2: 修改 npm 全局目录（推荐）**:
```bash
# 创建新的全局目录
mkdir ~/.npm-global

# 配置 npm 使用新目录
npm config set prefix '~/.npm-global'

# 添加到 PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 重新安装
npm install -g @larksuite/cli
```

---

### Q3: 网络连接问题怎么办？

**问题**: 安装时网络超时或连接失败

**解决方案**:

**使用淘宝镜像**:
```bash
# 设置镜像源
npm config set registry https://registry.npmmirror.com

# 安装
npm install -g @larksuite/cli
```

**恢复官方源**:
```bash
npm config set registry https://registry.npmjs.org
```

---

### Q4: 安装后提示命令不存在？

**问题**: 运行 `lark-cli` 提示 "command not found"

**解决方案**:

1. **确认安装路径在 PATH 中**:
   ```bash
   npm root -g  # 查看全局目录
   echo $PATH   # 查看 PATH
   ```

2. **添加到 PATH**:
   ```bash
   # 假设 npm 全局目录是 /usr/local/lib/node_modules
   echo 'export PATH=/usr/local/lib/node_modules/.bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

---

## 授权问题

### Q5: 授权失败，提示"授权码已过期"？

**问题**: OAuth 授权码过期

**解决方案**:

授权码有效期只有几分钟，重新执行授权：

```bash
lark-cli auth login
```

---

### Q6: 不授权可以使用吗？

**答案**: 可以，但功能受限。

**不授权**:
- ✅ 可以发消息、创建文档等
- ❌ 无法访问你的个人数据（日程、私信、收件箱）

**授权后**:
- ✅ 可以访问你的个人日历、消息、文档
- ✅ 以你的名义执行操作

---

### Q7: 如何保持授权状态？

**问题**: 每次都要重新授权

**解决方案**:

在开发者后台开启刷新 token 能力：
1. 进入飞书开放平台
2. 选择你的应用
3. 安全设置 → 重定向 URL
4. 开启"刷新 user_access_token"

---

## 使用问题

### Q8: 调用 API 提示权限不足？

**问题**: 提示 "permission denied" 或 "insufficient permissions"

**解决方案**:

1. **查看需要的权限**:
   ```bash
   lark-cli auth login --scope "<missing_scope>"
   ```
   CLI 会告诉你缺少什么权限。

2. **在开发者后台开通权限**:
   - 进入飞书开放平台
   - 选择你的应用
   - 权限管理 → 申请权限
   - 添加需要的权限

---

### Q9: 如何查看所有命令？

**解决方案**:

```bash
# 查看命令总览
lark-cli help

# 查看具体命令用法
lark-cli <command> --help

# 查看接口详情
lark-cli schema
```

---

### Q10: 支持国际版 Lark 吗？

**答案**: 支持。

**配置方法**:
```bash
lark-cli config init
```

在配置过程中选择国际版 Lark 即可。

---

## 权限问题

### Q11: 企业管理员有办法控制权限吗？

**答案**: 有。

CLI 只是提供一键创建应用的能力，应用的管控仍然 follow 企业统一管控规则。企业管理员可以在飞书开放平台后台对应用权限进行统一管理。

---

### Q12: 如何撤销授权？

**解决方案**:

```bash
# 退出登录
lark-cli auth logout
```

或在飞书客户端：
1. 打开"设置"
2. 进入"隐私与安全"
3. 找到"授权管理"
4. 撤销对应应用的授权

---

## 更多帮助

- 📖 查看 [故障排查指南](troubleshooting.md)
- 📚 官方文档：https://github.com/larksuite/cli
- 🐛 问题反馈：https://github.com/larksuite/cli/issues
