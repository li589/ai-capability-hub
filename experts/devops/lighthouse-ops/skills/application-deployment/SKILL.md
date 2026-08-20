---
name: application-deployment
description: |
  Lighthouse 应用部署。用于在实例上部署 Web 应用、配置运行环境、检查服务状态。
  触发场景：用户提到"部署应用"、"部署程序"、"部署到 Lighthouse"、"安装软件"、"配置环境"、"Web 应用"、"Docker 部署"。
user-invocable: true
---

# 应用部署

在 Lighthouse 实例上部署应用、配置运行环境。

## 支持的操作

| 操作 | 风险 | 说明 |
|------|:----:|------|
| 部署前环境检查 | 🟢 | 检查系统版本、磁盘、端口、服务状态 |
| 安装运行环境 | 🟡 | 安装 Node.js / Python / Java / Docker 等 |
| 部署 Web 应用 | 🟡 | 部署应用代码并启动服务 |
| 配置反向代理 | 🟡 | 配置 Nginx 反向代理和域名 |
| Docker 部署 | 🟡 | 用 Docker / Docker Compose 部署应用 |
| 验证部署结果 | 🟢 | 检查服务状态、端口监听、HTTP 响应 |

## 部署前检查清单

部署前必须完成以下检查：

| 检查项 | 命令（TAT） | 说明 |
|--------|------------|------|
| 系统版本 | `cat /etc/os-release` | 确认操作系统 |
| 磁盘空间 | `df -h` | 确保有足够空间 |
| 内存 | `free -m` | 确认可用内存 |
| 端口占用 | `ss -tlnp` | 避免端口冲突 |
| 运行中的服务 | `systemctl list-units --type=service --state=running` | 避免冲突 |
| Docker 状态 | `docker ps` 2>/dev/null | 检查 Docker 是否可用 |

## 常见运行环境安装

### Node.js

```bash
# 通过 nvm 安装（推荐）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# 验证
node -v && npm -v
```

### Python

```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip python3-venv

# CentOS
yum install -y python3 python3-pip

# 验证
python3 --version && pip3 --version
```

### Java

```bash
# OpenJDK 17
apt update && apt install -y openjdk-17-jdk
# 或
yum install -y java-17-openjdk-devel

# 验证
java -version
```

### Docker

```bash
# 一键安装
curl -fsSL https://get.docker.com | bash

# 启动并设置开机自启
systemctl start docker
systemctl enable docker

# 验证
docker run hello-world
```

## Web 应用部署流程

### 通用流程

1. **环境检查** → 确认系统、磁盘、端口
2. **安装依赖** → 安装运行环境
3. **获取代码** → git clone 或上传代码包
4. **安装依赖包** → `npm install` / `pip install -r requirements.txt`
5. **配置环境变量** → `.env` 文件或 export
6. **启动服务** → `npm start` / `python app.py` / `java -jar app.jar`
7. **配置开机自启** → systemd service
8. **验证** → `curl localhost:port` 确认服务正常

### systemd 服务配置

```ini
[Unit]
Description=My App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/myapp
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 部署 systemd 服务
cp myapp.service /etc/systemd/system/
systemctl daemon-reload
systemctl start myapp
systemctl enable myapp
systemctl status myapp
```

## Docker 部署流程

### 单容器部署

```bash
# 拉取镜像
docker pull nginx:latest

# 启动容器
docker run -d \
  --name myapp \
  -p 80:80 \
  -v /opt/myapp/html:/usr/share/nginx/html:ro \
  --restart unless-stopped \
  nginx:latest

# 验证
docker ps
curl -I http://localhost:80
```

### Docker Compose 部署

```yaml
version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html:ro
    restart: unless-stopped

  app:
    image: node:20-alpine
    working_dir: /app
    volumes:
      - ./app:/app
    command: npm start
    restart: unless-stopped
    depends_on:
      - db
```

```bash
docker compose up -d
docker compose ps
docker compose logs -f
```

## Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 测试配置
nginx -t

# 重载
nginx -s reload
```

## 防火墙端口开放

部署后需要检查防火墙是否已开放对应端口：

| 常见端口 | 用途 |
|---------|------|
| 80 | HTTP |
| 443 | HTTPS |
| 3000 | Node.js 默认 |
| 8080 | 常用 Web 端口 |
| 3306 | MySQL |
| 6379 | Redis |

> 端口开放请使用 firewall-management skill 操作。

## 部署验证

部署完成后执行以下验证：

1. **进程检查** → `ps aux | grep <app>`
2. **端口检查** → `ss -tlnp | grep <port>`
3. **本地访问** → `curl -I http://localhost:<port>`
4. **外网访问** → 确认防火墙已开放端口
5. **日志检查** → `journalctl -u <service> -f`

## 注意事项

- 部署前必须检查磁盘空间，避免部署过程中空间不足
- 生产环境建议使用 systemd 或 Docker 管理进程，避免 `nohup` 方式
- 敏感配置（数据库密码等）通过环境变量注入，不硬编码在代码里
- 首次部署后建议创建快照，便于回滚
