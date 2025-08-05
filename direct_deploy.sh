#!/bin/bash

# 直接部署到阿里云ECS - 无需本地Docker
# 在服务器上直接构建和运行

set -e

# ECS服务器信息
ECS_HOST="47.98.233.7"
ECS_USER="root"
ECS_PASSWORD="jx880429"

echo "🚀 开始直接部署股票复盘游戏到阿里云ECS"
echo "=========================================="
echo "🌐 服务器: ${ECS_HOST}"
echo "📦 直接部署模式（无需本地Docker）"
echo "=========================================="

# 检查sshpass
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass未安装，请安装：brew install sshpass"
    exit 1
fi

# 1. 创建项目压缩包
echo "📦 步骤1: 打包项目文件..."
tar -czf fupan-game.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='img_2195.jpg' \
    --exclude='IMG_2195.JPG' \
    --exclude='*.db' \
    .

# 2. 上传项目到服务器
echo "📤 步骤2: 上传项目到服务器..."
sshpass -p "${ECS_PASSWORD}" scp -o StrictHostKeyChecking=no fupan-game.tar.gz ${ECS_USER}@${ECS_HOST}:/tmp/

# 3. 生成服务器部署脚本
echo "📝 步骤3: 生成服务器部署脚本..."
cat > server_setup.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 在服务器上设置应用环境..."

# 更新系统
apt-get update

# 安装必要软件
apt-get install -y python3.9 python3.9-venv python3-pip nginx supervisor redis-server curl

# 创建应用目录
APP_DIR="/opt/fupan-game"
mkdir -p ${APP_DIR}
cd ${APP_DIR}

# 解压应用文件
echo "📦 解压应用文件..."
tar -xzf /tmp/fupan-game.tar.gz -C ${APP_DIR}

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
python3.9 -m venv venv
source venv/bin/activate

# 安装Python依赖
echo "📚 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_excel.txt

# 创建必要目录
mkdir -p data logs

# 配置Supervisor
echo "⚙️ 配置Supervisor..."
cat > /etc/supervisor/conf.d/fupan-game.conf << SUPERVISOR_EOF
[program:fupan-game]
command=${APP_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=${APP_DIR}
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/fupan-game.log
environment=PATH="${APP_DIR}/venv/bin",PYTHONUNBUFFERED="1"
SUPERVISOR_EOF

# 配置Nginx
echo "🌐 配置Nginx..."
cat > /etc/nginx/sites-available/fupan-game << NGINX_EOF
server {
    listen 80;
    server_name _;

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
NGINX_EOF

# 启用nginx站点
ln -sf /etc/nginx/sites-available/fupan-game /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 启动服务
echo "🚀 启动服务..."
systemctl start redis-server
systemctl enable redis-server

supervisorctl reread
supervisorctl update
supervisorctl start fupan-game

nginx -t
systemctl restart nginx

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "✅ 检查服务状态..."
supervisorctl status fupan-game
systemctl status nginx --no-pager -l

# 测试应用
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "🎉 部署成功！应用运行正常"
    echo "🌐 访问地址: http://47.98.233.7"
else
    echo "⚠️  应用可能还在启动中..."
    echo "📋 查看日志: tail -f /var/log/fupan-game.log"
fi

echo "=========================================="
echo "✅ 直接部署完成！"
echo "🌐 访问地址: http://47.98.233.7"
echo "📋 应用日志: tail -f /var/log/fupan-game.log"
echo "🔄 重启应用: supervisorctl restart fupan-game"
echo "🔄 重启Nginx: systemctl restart nginx"
echo "=========================================="
EOF

# 4. 上传并执行部署脚本
echo "📤 步骤4: 上传部署脚本..."
sshpass -p "${ECS_PASSWORD}" scp -o StrictHostKeyChecking=no server_setup.sh ${ECS_USER}@${ECS_HOST}:/tmp/

echo "🚀 步骤5: 在服务器上执行部署..."
sshpass -p "${ECS_PASSWORD}" ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} "chmod +x /tmp/server_setup.sh && /tmp/server_setup.sh"

# 5. 清理临时文件
rm -f fupan-game.tar.gz server_setup.sh

echo ""
echo "🎉🎉🎉 直接部署完成！🎉🎉🎉"
echo "=========================================="
echo "✅ 应用已部署到: ${ECS_HOST}"
echo "🌐 访问地址: http://${ECS_HOST}"
echo "🎮 开始您的股票复盘游戏之旅吧！"
echo "=========================================="
echo ""
echo "📋 常用命令:"
echo "  查看应用状态: sshpass -p '${ECS_PASSWORD}' ssh ${ECS_USER}@${ECS_HOST} 'supervisorctl status fupan-game'"
echo "  查看应用日志: sshpass -p '${ECS_PASSWORD}' ssh ${ECS_USER}@${ECS_HOST} 'tail -f /var/log/fupan-game.log'"
echo "  重启应用: sshpass -p '${ECS_PASSWORD}' ssh ${ECS_USER}@${ECS_HOST} 'supervisorctl restart fupan-game'"
echo ""