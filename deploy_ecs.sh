#!/bin/bash

# 阿里云ECS直接部署脚本（不使用容器）
# 适用于直接在ECS服务器上部署

set -e

echo "=========================================="
echo "开始在阿里云ECS上部署股票复盘游戏"
echo "=========================================="

# 1. 更新系统包
echo "步骤1: 更新系统包..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. 安装Python 3.9
echo "步骤2: 安装Python 3.9..."
sudo apt-get install -y python3.9 python3.9-venv python3.9-dev python3-pip

# 3. 安装系统依赖
echo "步骤3: 安装系统依赖..."
sudo apt-get install -y gcc g++ libgomp1 nginx supervisor redis-server

# 4. 创建应用目录
echo "步骤4: 创建应用目录..."
APP_DIR="/opt/fupan-game"
sudo mkdir -p ${APP_DIR}
sudo chown -R $USER:$USER ${APP_DIR}

# 5. 创建Python虚拟环境
echo "步骤5: 创建Python虚拟环境..."
cd ${APP_DIR}
python3.9 -m venv venv
source venv/bin/activate

# 6. 复制应用文件（需要先将文件上传到服务器）
echo "步骤6: 请确保已将应用文件上传到 ~/fupan-game-upload/"
echo "执行: scp -r ./* user@your-server:~/fupan-game-upload/"
read -p "文件已上传？按Enter继续..."

cp -r ~/fupan-game-upload/* ${APP_DIR}/

# 7. 安装Python依赖
echo "步骤7: 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_excel.txt

# 8. 配置Supervisor
echo "步骤8: 配置Supervisor..."
sudo tee /etc/supervisor/conf.d/fupan-game.conf << EOF
[program:fupan-game]
command=${APP_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=${APP_DIR}
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/fupan-game.log
environment=PATH="${APP_DIR}/venv/bin",PYTHONUNBUFFERED="1"
EOF

# 9. 配置Nginx反向代理
echo "步骤9: 配置Nginx..."
sudo tee /etc/nginx/sites-available/fupan-game << EOF
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名或IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fupan-game /etc/nginx/sites-enabled/
sudo nginx -t

# 10. 创建systemd服务（可选，替代supervisor）
echo "步骤10: 创建systemd服务..."
sudo tee /etc/systemd/system/fupan-game.service << EOF
[Unit]
Description=Stock Review Game
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=${APP_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 11. 启动服务
echo "步骤11: 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fupan-game
sudo systemctl restart nginx

# 或使用systemd
# sudo systemctl enable fupan-game
# sudo systemctl start fupan-game

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "访问地址: http://your-domain.com"
echo "查看日志: sudo tail -f /var/log/fupan-game.log"
echo "重启服务: sudo supervisorctl restart fupan-game"
echo "=========================================="