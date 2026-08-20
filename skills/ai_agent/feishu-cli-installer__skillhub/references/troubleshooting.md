# 飞书CLI故障排查指南

## 目录

1. [安装故障](#安装故障)
2. [配置故障](#配置故障)
3. [授权故障](#授权故障)
4. [使用故障](#使用故障)
5. [网络故障](#网络故障)
6. [权限故障](#权限故障)

---

## 安装故障

### 故障1: npm install 失败

**症状**:
```
npm ERR! network timeout
npm ERR! errno ETIMEDOUT
```

**原因**: 网络问题或 npm registry 访问受限

**解决方案**:

1. **使用镜像源**:
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install -g @larksuite/cli
   ```

2. **使用代理**:
   ```bash
   npm config set proxy http://proxy-server:port
   npm config set https-proxy http://proxy-server:port
   npm install -g @larksuite/cli
   ```

3. **清除缓存**:
   ```bash
   npm cache clean --force
   npm install -g @larksuite/cli
   ```

---

### 故障2: 权限错误 EACCES

**症状**:
```
npm ERR! Error: EACCES: permission denied
npm ERR! syscall: mkdir
npm ERR! code: EACCES
```

**原因**: npm 全局目录无写入权限

**解决方案**:

**方案1: 使用 sudo（快速但不推荐）**:
```bash
sudo npm install -g @larksuite/cli
```

**方案2: 修改 npm 全局目录（推荐）**:
```bash
# 创建新的全局目录
mkdir ~/.npm-global

# 配置 npm
npm config set prefix '~/.npm-global'

# 添加到 PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 重新安装
npm install -g @larksuite/cli
```

---

### 故障3: Node.js 版本不兼容

**症状**:
```
error @larksuite/cli@x.x.x: The engine "node" is incompatible with this module.
```

**原因**: Node.js 版本过低

**解决方案**:

1. **检查当前版本**:
   ```bash
   node --version
   ```

2. **升级 Node.js**:
   - macOS: `brew install node@18`
   - Ubuntu: `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs`
   - 或使用 nvm: `nvm install 18 && nvm use 18`

---

## 配置故障

### 故障4: config init 失败

**症状**:
```
Error: Failed to create app
```

**原因**: 网络问题或飞书开放平台服务异常

**解决方案**:

1. **检查网络**:
   ```bash
   ping open.feishu.cn
   ```

2. **重试命令**:
   ```bash
   lark-cli config init --new
   ```

3. **手动创建应用**:
   - 访问飞书开放平台: https://open.feishu.cn/
   - 创建企业自建应用
   - 使用现有应用配置:
     ```bash
     lark-cli config init
     # 选择"使用已有应用"
     ```

---

### 故障5: Skills 安装失败

**症状**:
```
Error: Failed to add skills
```

**原因**: npx 执行失败或 GitHub 访问受限

**解决方案**:

1. **检查 npx**:
   ```bash
   npx --version
   ```

2. **手动安装**:
   ```bash
   npx skills add https://github.com/larksuite/cli -y -g
   ```

3. **使用镜像**（如果 GitHub 访问受限）:
   - 先克隆仓库
   - 本地安装 Skills

---

## 授权故障

### 故障6: 授权码过期

**症状**:
```
Error: Authorization code has expired
```

**原因**: OAuth 授权码有效期只有几分钟

**解决方案**:

重新执行授权命令：
```bash
lark-cli auth login
```

**提示**: 在生成授权链接后尽快完成授权。

---

### 故障7: 授权页面无法打开

**症状**: 授权链接无法在浏览器中打开

**原因**: 网络问题或链接格式错误

**解决方案**:

1. **检查网络**:
   - 确保能够访问 `open.feishu.cn`

2. **手动复制链接**:
   - 复制终端中显示的完整链接
   - 在浏览器中打开

3. **检查飞书客户端**:
   - 确保飞书客户端已登录
   - 确保使用正确的飞书账号

---

### 故障8: 授权后仍提示未授权

**症状**:
```
Error: Not logged in
```

**原因**: 授权信息未正确保存

**解决方案**:

1. **检查授权状态**:
   ```bash
   lark-cli auth status
   ```

2. **重新授权**:
   ```bash
   lark-cli auth logout
   lark-cli auth login
   ```

3. **检查配置文件**:
   ```bash
   lark-cli config list
   ```

---

## 使用故障

### 故障9: API 调用权限不足

**症状**:
```
Error: Insufficient permissions
```

**原因**: 应用未开通对应权限

**解决方案**:

1. **查看需要的权限**:
   ```bash
   lark-cli auth login --scope "<missing_scope>"
   ```

2. **在开发者后台开通权限**:
   - 访问飞书开放平台
   - 选择应用
   - 权限管理 → 申请权限
   - 添加需要的权限并发布版本

---

### 故障10: 命令执行失败

**症状**: 命令返回错误码

**解决方案**:

1. **查看详细错误信息**:
   ```bash
   lark-cli <command> --verbose
   ```

2. **查看命令帮助**:
   ```bash
   lark-cli <command> --help
   ```

3. **查看接口详情**:
   ```bash
   lark-cli schema
   ```

---

## 网络故障

### 故障11: 网络超时

**症状**:
```
Error: Network timeout
```

**解决方案**:

1. **检查网络连接**:
   ```bash
   ping open.feishu.cn
   ```

2. **使用代理**:
   ```bash
   export HTTP_PROXY=http://proxy-server:port
   export HTTPS_PROXY=http://proxy-server:port
   ```

3. **增加超时时间**:
   ```bash
   lark-cli config set timeout 60000  # 60秒
   ```

---

### 故障12: SSL 证书错误

**症状**:
```
Error: UNABLE_TO_VERIFY_LEAF_SIGNATURE
```

**解决方案**:

1. **更新 Node.js**（推荐）

2. **临时禁用 SSL 验证**（不推荐，仅用于测试）:
   ```bash
   NODE_TLS_REJECT_UNAUTHORIZED=0 lark-cli <command>
   ```

---

## 权限故障

### 故障13: 企业权限限制

**症状**:
```
Error: Application has been disabled by admin
```

**原因**: 企业管理员禁用了应用

**解决方案**:

联系企业管理员启用应用。

---

### 故障14: 应用被禁用

**症状**:
```
Error: App has been banned
```

**原因**: 应用违反平台规则

**解决方案**:

1. 检查飞书开放平台的通知
2. 联系飞书支持团队
3. 整改后申请恢复

---

## 故障排查步骤

### 通用排查流程

1. **检查环境**:
   ```bash
   node --version  # Node.js >= 16.0
   npm --version   # npm 可用
   lark-cli --version  # CLI 已安装
   ```

2. **检查授权**:
   ```bash
   lark-cli auth status  # 查看授权状态
   ```

3. **检查配置**:
   ```bash
   lark-cli config list  # 查看配置信息
   ```

4. **查看日志**:
   ```bash
   lark-cli <command> --verbose  # 显示详细日志
   ```

5. **重新安装**:
   ```bash
   npm uninstall -g @larksuite/cli
   npm install -g @larksuite/cli
   lark-cli config init --new
   ```

---

## 获取帮助

如果以上方案都无法解决问题：

1. **查看官方文档**: https://github.com/larksuite/cli
2. **提交 Issue**: https://github.com/larksuite/cli/issues
3. **联系飞书支持**: 通过飞书开放平台提交工单

---

**最后更新**: 2026-04-03
