#!/bin/bash

# GitHub直接部署到阿里云ECS - 超简单版本
# 在ECS服务器上执行此脚本

set -e

echo "🚀 从GitHub直接部署股票复盘游戏"
echo "================================"

# 停止可能运行的服务
echo "🛑 停止现有服务..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true

# 更新系统包
echo "📦 更新系统包..."
apt update

# 安装必要软件
echo "🔧 安装必要软件..."
apt install -y python3 python3-pip git curl nginx

# 创建应用目录
echo "📁 准备应用目录..."
mkdir -p /opt
cd /opt

# 清理旧版本
rm -rf fupan-game

# 从GitHub克隆最新代码
echo "📥 从GitHub下载最新代码..."
git clone https://github.com/FelixJx/fupan-game.git
cd fupan-game

# 安装Python依赖（只安装核心依赖）
echo "🐍 安装Python依赖..."
pip3 install fastapi uvicorn jinja2 pandas numpy requests sqlite3 websockets aiofiles

# 创建必要目录
mkdir -p data logs

# 配置Nginx反向代理
echo "🌐 配置Nginx..."
cat > /etc/nginx/sites-available/fupan-game << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
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
    }
}
EOF

# 启用Nginx站点
ln -sf /etc/nginx/sites-available/fupan-game /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 创建systemd服务
echo "⚙️ 创建系统服务..."
cat > /etc/systemd/system/fupan-game.service << 'EOF'
[Unit]
Description=Stock Review Game
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fupan-game
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable fupan-game
systemctl start fupan-game

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "✅ 检查服务状态..."
systemctl status fupan-game --no-pager || true

# 测试应用
echo "🧪 测试应用..."
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "🎉 部署成功！"
    echo "🌐 访问地址: http://$(curl -s ifconfig.me)"
    echo "🌐 或访问: http://47.98.233.7"
else
    echo "⚠️ 应用可能还在启动中..."
    echo "📋 查看日志: journalctl -u fupan-game -f"
fi

echo ""
echo "📋 常用命令:"
echo "  查看状态: systemctl status fupan-game"
echo "  查看日志: journalctl -u fupan-game -f"
echo "  重启应用: systemctl restart fupan-game"
echo "  更新代码: cd /opt/fupan-game && git pull && systemctl restart fupan-game"
echo ""
echo "🎮 开始您的股票复盘游戏之旅吧！"