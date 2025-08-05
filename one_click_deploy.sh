#!/bin/bash

# 股票复盘游戏 - 一键部署到阿里云
# 完全自动化：构建镜像 -> 推送到阿里云 -> 部署到ECS服务器

set -e

# 配置变量
PROJECT_NAME="fupan-game"
REGISTRY_URL="crpi-gr7uqgzs6w68jo6x.cn-hangzhou.personal.cr.aliyuncs.com"
NAMESPACE="fupan-game"
IMAGE_NAME="stock-game"
IMAGE_TAG=$(date +%Y%m%d%H%M%S)
FULL_IMAGE_NAME="${REGISTRY_URL}/${NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"

# 阿里云容器镜像服务登录信息
DOCKER_USERNAME="aliyun4538628734"
DOCKER_PASSWORD="jx880429"

# ECS服务器信息
ECS_HOST="47.98.233.7"
ECS_USER="root"
ECS_PASSWORD="jx880429"

echo "🚀 开始一键部署股票复盘游戏到阿里云"
echo "=========================================="
echo "📦 项目: ${PROJECT_NAME}"
echo "🌐 服务器: ${ECS_HOST}"
echo "📺 镜像: ${FULL_IMAGE_NAME}"
echo "=========================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo "📥 正在安装sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install sshpass
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
fi

# 1. 构建Docker镜像
echo "🔨 步骤1: 构建Docker镜像..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}

# 2. 登录阿里云容器镜像服务
echo "🔐 步骤2: 登录阿里云容器镜像服务..."
echo "${DOCKER_PASSWORD}" | docker login --username=${DOCKER_USERNAME} --password-stdin ${REGISTRY_URL}

# 3. 推送镜像到阿里云
echo "📤 步骤3: 推送镜像到阿里云..."
docker push ${FULL_IMAGE_NAME}

# 4. 生成服务器部署脚本
echo "📝 步骤4: 生成服务器部署脚本..."
cat > deploy_on_server.sh << EOF
#!/bin/bash
set -e

echo "🔧 正在服务器上部署应用..."

# 安装Docker (如果未安装)
if ! command -v docker &> /dev/null; then
    echo "📦 安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    usermod -aG docker root
fi

# 安装docker-compose (如果未安装)
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装docker-compose..."
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 创建应用目录
mkdir -p /opt/fupan-game
cd /opt/fupan-game

# 登录阿里云镜像服务
echo "${DOCKER_PASSWORD}" | docker login --username=${DOCKER_USERNAME} --password-stdin ${REGISTRY_URL}

# 创建docker-compose配置
cat > docker-compose.prod.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  web:
    image: ${FULL_IMAGE_NAME}
    container_name: fupan-game
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Asia/Shanghai
    restart: unless-stopped
    networks:
      - fupan-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"] || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:alpine
    container_name: fupan-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - fupan-network
    restart: unless-stopped

networks:
  fupan-network:
    driver: bridge

volumes:
  redis-data:
COMPOSE_EOF

# 创建必要目录
mkdir -p data logs

# 停止旧容器
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# 拉取新镜像
docker-compose -f docker-compose.prod.yml pull

# 启动新容器
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "✅ 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
if docker-compose -f docker-compose.prod.yml exec -T web curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "🎉 部署成功！服务运行正常"
    echo "🌐 访问地址: http://${ECS_HOST}:8000"
else
    echo "⚠️  服务可能还在启动中，请稍后检查"
    echo "📋 查看日志: docker-compose -f docker-compose.prod.yml logs"
fi

# 配置防火墙 (如果需要)
if command -v ufw &> /dev/null; then
    ufw allow 8000/tcp
    ufw allow 80/tcp
fi

echo "=========================================="
echo "✅ 部署完成！"
echo "🌐 访问地址: http://${ECS_HOST}:8000"
echo "📋 查看日志: docker-compose -f /opt/fupan-game/docker-compose.prod.yml logs -f"
echo "🔄 重启服务: docker-compose -f /opt/fupan-game/docker-compose.prod.yml restart"
echo "=========================================="
EOF

# 5. 上传并执行部署脚本
echo "📤 步骤5: 上传部署脚本到服务器..."
sshpass -p "${ECS_PASSWORD}" scp -o StrictHostKeyChecking=no deploy_on_server.sh ${ECS_USER}@${ECS_HOST}:/tmp/

echo "🚀 步骤6: 在服务器上执行部署..."
sshpass -p "${ECS_PASSWORD}" ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} "chmod +x /tmp/deploy_on_server.sh && /tmp/deploy_on_server.sh"

# 6. 清理临时文件
rm -f deploy_on_server.sh

echo ""
echo "🎉🎉🎉 一键部署完成！🎉🎉🎉"
echo "=========================================="
echo "✅ 镜像已推送: ${FULL_IMAGE_NAME}"
echo "✅ 服务已部署到: ${ECS_HOST}"
echo "🌐 访问地址: http://${ECS_HOST}:8000"
echo "🎮 开始您的股票复盘游戏之旅吧！"
echo "=========================================="
echo ""
echo "📋 常用命令:"
echo "  查看服务状态: sshpass -p '${ECS_PASSWORD}' ssh ${ECS_USER}@${ECS_HOST} 'cd /opt/fupan-game && docker-compose -f docker-compose.prod.yml ps'"
echo "  查看日志: sshpass -p '${ECS_PASSWORD}' ssh ${ECS_USER}@${ECS_HOST} 'cd /opt/fupan-game && docker-compose -f docker-compose.prod.yml logs -f'"
echo "  重启服务: sshpass -p '${ECS_PASSWORD}' ssh ${ECS_USER}@${ECS_HOST} 'cd /opt/fupan-game && docker-compose -f docker-compose.prod.yml restart'"
echo ""