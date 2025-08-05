#!/bin/bash

# 一行命令安装脚本 - 可以直接在ECS上执行
# curl -fsSL https://raw.githubusercontent.com/FelixJx/fupan-game/main/install.sh | bash

echo "🎮 股票复盘游戏 - 一键安装"
echo "========================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root用户执行"
    exit 1
fi

# 停止现有服务
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true

# 安装依赖
echo "📦 安装系统依赖..."
apt update
apt install -y python3 python3-pip git curl nginx

# 下载项目
echo "📥 下载项目..."
cd /opt
rm -rf fupan-game
git clone https://github.com/FelixJx/fupan-game.git
cd fupan-game

# 安装Python依赖
echo "🐍 安装Python依赖..."
pip3 install fastapi uvicorn jinja2 pandas numpy requests websockets aiofiles schedule

# 创建目录
mkdir -p data logs

# 启动应用
echo "🚀 启动应用..."
nohup python3 main.py > logs/app.log 2>&1 &

# 配置Nginx
echo "🌐 配置Nginx..."
cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

systemctl restart nginx

sleep 5

# 测试
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "🎉 安装成功！"
    echo "🌐 访问: http://$(curl -s ifconfig.me 2>/dev/null || echo '47.98.233.7')"
else
    echo "⚠️ 安装可能有问题，请检查日志: tail -f /opt/fupan-game/logs/app.log"
fi