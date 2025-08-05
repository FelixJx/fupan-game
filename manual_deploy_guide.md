# 手动部署指南 - 股票复盘游戏

由于网络连接问题，请按以下步骤手动部署：

## 方法1：使用阿里云控制台（推荐）

### 1. 重启ECS实例
1. 在阿里云ECS控制台
2. 找到实例 `iZbp102qh43880xme7yptlZ`
3. 点击 **"更多"** → **"实例状态"** → **"重启"**
4. 等待重启完成

### 2. 通过控制台连接
1. 点击 **"远程连接"**
2. 选择 **"通过密码认证"**
3. 用户名：`root`
4. 密码：`jx880429`

### 3. 在服务器上执行部署

连接成功后，依次执行以下命令：

```bash
# 1. 更新系统并安装必要软件
apt-get update
apt-get install -y python3.9 python3.9-venv python3-pip nginx supervisor redis-server curl git

# 2. 克隆项目
cd /opt
git clone https://github.com/FelixJx/fupan-game.git
cd fupan-game

# 3. 创建Python虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_excel.txt

# 5. 创建必要目录
mkdir -p data logs

# 6. 配置Supervisor
cat > /etc/supervisor/conf.d/fupan-game.conf << 'EOF'
[program:fupan-game]
command=/opt/fupan-game/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=/opt/fupan-game
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/fupan-game.log
environment=PATH="/opt/fupan-game/venv/bin",PYTHONUNBUFFERED="1"
EOF

# 7. 配置Nginx
cat > /etc/nginx/sites-available/fupan-game << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 8. 启用站点配置
ln -sf /etc/nginx/sites-available/fupan-game /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 9. 启动所有服务
systemctl start redis-server
systemctl enable redis-server

supervisorctl reread
supervisorctl update
supervisorctl start fupan-game

nginx -t
systemctl restart nginx

# 10. 检查服务状态
supervisorctl status
systemctl status nginx

# 11. 测试应用
curl http://localhost:8000/
```

## 方法2：使用SSH客户端

如果您有SSH客户端（如Xshell、SecureCRT等）：

1. 连接到：`47.98.233.7:22`
2. 用户名：`root`
3. 密码：`jx880429`
4. 执行上述命令

## 验证部署

部署完成后：

1. **检查服务状态**：
   ```bash
   supervisorctl status fupan-game
   ```

2. **查看应用日志**：
   ```bash
   tail -f /var/log/fupan-game.log
   ```

3. **访问应用**：
   - 浏览器打开：http://47.98.233.7
   - 应该看到股票复盘游戏界面

## 常用管理命令

```bash
# 重启应用
supervisorctl restart fupan-game

# 重启Nginx
systemctl restart nginx

# 重启Redis
systemctl restart redis-server

# 查看所有服务状态
supervisorctl status
systemctl status nginx
systemctl status redis-server

# 更新代码
cd /opt/fupan-game
git pull
supervisorctl restart fupan-game
```

## 故障排除

### 如果端口8000无法访问：
1. 检查安全组是否开放8000端口
2. 检查防火墙：`ufw status`
3. 开放端口：`ufw allow 8000`

### 如果应用启动失败：
1. 查看日志：`tail -f /var/log/fupan-game.log`
2. 手动启动测试：
   ```bash
   cd /opt/fupan-game
   source venv/bin/activate
   python main.py
   ```

### 如果依赖安装失败：
```bash
# 升级pip
pip install --upgrade pip

# 单独安装依赖
pip install fastapi uvicorn pandas numpy
```

部署完成后，您就可以通过 http://47.98.233.7 访问您的股票复盘游戏了！