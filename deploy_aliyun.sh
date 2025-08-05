#!/bin/bash

# 阿里云一键部署脚本 - 股票复盘游戏
# 自动构建、推送镜像并部署到ECS服务器

set -e

# 配置变量
PROJECT_NAME="fupan-game"
REGION="cn-hangzhou"
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

echo "=========================================="
echo "开始部署股票复盘游戏到阿里云"
echo "=========================================="

# 1. 构建Docker镜像
echo "步骤1: 构建Docker镜像..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}

# 2. 登录阿里云容器镜像服务
echo "步骤2: 登录阿里云容器镜像服务..."
echo "${DOCKER_PASSWORD}" | docker login --username=${DOCKER_USERNAME} --password-stdin ${REGISTRY_URL}

# 3. 推送镜像到阿里云
echo "步骤3: 推送镜像到阿里云..."
docker push ${FULL_IMAGE_NAME}

# 4. 更新docker-compose文件使用新镜像
echo "步骤4: 更新docker-compose配置..."
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  web:
    image: ${FULL_IMAGE_NAME}
    container_name: fupan-game
    ports:
      - "8000:8000"
    volumes:
      - ./fuPan_game.db:/app/fuPan_game.db
      - ./prediction_game.db:/app/prediction_game.db
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Asia/Shanghai
    restart: unless-stopped
    networks:
      - fupan-network

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
EOF

# 5. 生成部署命令
echo "步骤5: 生成部署命令..."
cat > deploy_on_server.sh << 'EOF'
#!/bin/bash
# 在服务器上执行的部署脚本

# 停止旧容器
docker-compose -f docker-compose.prod.yml down

# 拉取新镜像
docker-compose -f docker-compose.prod.yml pull

# 启动新容器
docker-compose -f docker-compose.prod.yml up -d

# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs --tail=50
EOF

chmod +x deploy_on_server.sh

echo "=========================================="
echo "部署准备完成！"
echo "=========================================="
echo "请执行以下步骤完成部署："
echo "1. 将 docker-compose.prod.yml 和 deploy_on_server.sh 上传到服务器"
echo "2. 在服务器上执行: ./deploy_on_server.sh"
echo ""
echo "镜像地址: ${FULL_IMAGE_NAME}"
echo "=========================================="