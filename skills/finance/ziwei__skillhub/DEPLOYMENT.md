# 紫微斗数命盘解读 - 部署指南

## 快速部署

```bash
cd /Users/xy/workspace/skillhub/skillpay-ziwei
chmod +x deploy.sh
./deploy.sh
```

## 手动部署步骤

### 1. 准备项目文件

```bash
# 创建项目目录
sudo mkdir -p /opt/skillpay-ziwei
sudo chown $USER:$USER /opt/skillpay-ziwei

# 复制项目文件
cd /Users/xy/workspace/skillhub/skillpay-ziwei
cp -r app/ /opt/skillpay-ziwei/
cp requirements.txt /opt/skillpay-ziwei/
cp skillpay-ziwei.service /opt/skillpay-ziwei/
```

### 2. 配置环境变量

**方式 A：从 tizhi 项目复制配置（推荐）**

```bash
# 复制 tizhi 的配置
sudo cp /opt/skillpay-tizhi/.env.production /opt/skillpay-ziwei/.env

# 修改 BASE_URL
sudo sed -i 's|BASE_URL=.*|BASE_URL=https://meihua.astrakairos.com/ziwei|' /opt/skillpay-ziwei/.env

# 添加 DashScope API key
sudo nano /opt/skillpay-ziwei/.env
# 添加：DASHSCOPE_API_KEY=your_real_api_key
```

**方式 B：手动创建配置**

```bash
sudo cp .env.production /opt/skillpay-ziwei/.env
sudo nano /opt/skillpay-ziwei/.env
# 填入所有配置项
```

### 3. 安装依赖

```bash
cd /opt/skillpay-ziwei
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 设置权限

```bash
sudo chown -R www-data:www-data /opt/skillpay-ziwei
sudo chmod -R 755 /opt/skillpay-ziwei
sudo chmod 600 /opt/skillpay-ziwei/.env
mkdir -p data
```

### 5. 安装系统服务

```bash
sudo cp skillpay-ziwei.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skillpay-ziwei
sudo systemctl start skillpay-ziwei
```

### 6. 验证服务

```bash
# 检查服务状态
sudo systemctl status skillpay-ziwei

# 测试健康检查
curl http://127.0.0.1:8101/api/health
```

## 配置 Nginx

编辑 `/etc/nginx/sites-available/meihua.astrakairos.com`：

```nginx
# 在 server 块中添加
location /ziwei/ {
    proxy_pass http://127.0.0.1:8101/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

然后重载 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 常用管理命令

```bash
# 查看服务状态
sudo systemctl status skillpay-ziwei

# 重启服务
sudo systemctl restart skillpay-ziwei

# 查看实时日志
sudo journalctl -u skillpay-ziwei -f

# 查看最近 100 行日志
sudo journalctl -u skillpay-ziwei -n 100

# 停止服务
sudo systemctl stop skillpay-ziwei
```

## 配置说明

### 必需配置项

| 配置项 | 说明 | 示例 |
|--------|------|------|
| MODE | 运行模式 | live / mock |
| BASE_URL | 服务基础 URL | https://meihua.astrakairos.com/ziwei |
| PRICE | 价格（分） | 990 (= ¥9.90) |
| DASHSCOPE_API_KEY | DashScope API 密钥 | sk-xxxxxxxx |
| WECHAT_MCH_ID | 微信商户号 | 1655449109 |
| WECHAT_APP_ID | 微信应用 ID | wxd5b9c8c3f8b9a5e6 |
| WECHAT_MCH_CERT_SERIAL | 商户证书序列号 | 5C5B5E5D... |
| WECHAT_MCH_API_V3_KEY | API v3 密钥 | 32位字符串 |
| WECHAT_MCH_PRIVATE_KEY_PATH | 商户私钥路径 | /opt/workbuddy/key/apiclient_key.pem |
| SKILLHUB_DEVELOPER_ID | SkillHub 开发者 ID | sh-abc123def456 |
| SKILLHUB_PUB_KEY_ID | SkillHub 公钥 ID | pub_key_123456 |
| SKILLHUB_PRIVATE_KEY_PATH | SkillHub 私钥路径 | /opt/workbuddy/key/skillhub_private_key.pem |

### 获取 DashScope API Key

1. 访问 https://dashscope.console.aliyun.com/
2. 创建 API Key
3. 复制到 .env 文件

## 故障排查

### 服务启动失败

```bash
# 查看详细错误
sudo journalctl -u skillpay-ziwei -n 50 --no-pager

# 常见原因：
# 1. 配置文件权限不对：sudo chmod 600 /opt/skillpay-ziwei/.env
# 2. 依赖未安装：cd /opt/skillpay-ziwei && source venv/bin/activate && pip install -r requirements.txt
# 3. 端口被占用：sudo lsof -i :8101
```

### API 返回错误

```bash
# 测试本地访问
curl http://127.0.0.1:8101/api/health

# 测试通过域名访问
curl https://meihua.astrakairos.com/ziwei/api/health

# 查看应用日志
sudo journalctl -u skillpay-ziwei -f
```

### 支付相关问题

```bash
# 检查微信支付配置
cat /opt/skillpay-ziwei/.env | grep WECHAT

# 检查私钥文件是否存在
ls -la /opt/workbuddy/key/apiclient_key.pem

# 查看支付相关日志
sudo journalctl -u skillpay-ziwei | grep -i "wechat\|payment\|wxpay"
```

## 更新部署

```bash
# 1. 备份当前版本
sudo cp -r /opt/skillpay-ziwei /opt/skillpay-ziwei.backup.$(date +%Y%m%d)

# 2. 更新代码
cd /Users/xy/workspace/skillhub/skillpay-ziwei
sudo cp -r app/ /opt/skillpay-ziwei/

# 3. 更新依赖（如有）
cd /opt/skillpay-ziwei
source venv/bin/activate
pip install -r requirements.txt

# 4. 重启服务
sudo systemctl restart skillpay-ziwei

# 5. 验证
curl http://127.0.0.1:8101/api/health
```

## 卸载

```bash
sudo systemctl stop skillpay-ziwei
sudo systemctl disable skillpay-ziwei
sudo rm /etc/systemd/system/skillpay-ziwei.service
sudo systemctl daemon-reload
sudo rm -rf /opt/skillpay-ziwei
```
