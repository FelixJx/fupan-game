# 股票复盘游戏 - 阿里云部署指南

本文档提供了将股票复盘游戏部署到阿里云的详细步骤。提供两种部署方案：容器化部署和ECS直接部署。

## 项目概述

- **技术栈**: Python 3.9 + FastAPI + SQLite + Redis
- **前端**: HTML + JavaScript (内置)
- **服务端口**: 8000

## 方案一：容器化部署（推荐）

### 前置要求

1. 阿里云账号和容器镜像服务
2. 一台配置好Docker的ECS服务器（推荐2核4G以上）
3. 域名（可选）

### 部署步骤

#### 1. 准备阿里云容器镜像服务

1. 登录[阿里云容器镜像服务](https://cr.console.aliyun.com)
2. 创建命名空间（如：fupan-game）
3. 创建镜像仓库
4. 获取登录凭证

#### 2. 修改部署脚本配置

编辑 `deploy_aliyun.sh`，替换以下变量：

```bash
NAMESPACE="your-namespace"  # 替换为您的命名空间
# docker login 时使用您的用户名和密码
```

#### 3. 执行部署

```bash
# 在本地执行
./deploy_aliyun.sh
```

#### 4. 在ECS服务器上部署

1. 上传文件到服务器：
```bash
scp docker-compose.prod.yml deploy_on_server.sh root@your-server-ip:/opt/
```

2. SSH登录服务器并执行：
```bash
cd /opt
./deploy_on_server.sh
```

## 方案二：ECS直接部署

### 前置要求

1. 阿里云ECS服务器（Ubuntu 20.04+，推荐2核4G以上）
2. 开放端口：80, 8000

### 部署步骤

#### 1. 上传代码到服务器

```bash
# 在本地打包
tar -czf fupan-game.tar.gz --exclude='.git' --exclude='__pycache__' .

# 上传到服务器
scp fupan-game.tar.gz root@your-server-ip:~/

# 在服务器解压
ssh root@your-server-ip
mkdir ~/fupan-game-upload
cd ~/fupan-game-upload
tar -xzf ~/fupan-game.tar.gz
```

#### 2. 执行部署脚本

```bash
# 复制部署脚本到服务器
scp deploy_ecs.sh root@your-server-ip:~/

# 在服务器执行
ssh root@your-server-ip
chmod +x ~/deploy_ecs.sh
./deploy_ecs.sh
```

#### 3. 配置域名（可选）

修改 `/etc/nginx/sites-available/fupan-game` 中的 `server_name`。

## 安全组配置

在阿里云ECS控制台配置安全组规则：

| 协议 | 端口 | 说明 |
|------|------|------|
| HTTP | 80 | Web访问 |
| HTTPS | 443 | HTTPS访问（可选） |
| TCP | 8000 | FastAPI服务（仅内网） |
| TCP | 6379 | Redis（仅内网） |

## 数据库备份

### 自动备份脚本

创建 `/opt/backup_db.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# 备份SQLite数据库
cp /opt/fupan-game/fuPan_game.db $BACKUP_DIR/fuPan_game_$DATE.db
cp /opt/fupan-game/prediction_game.db $BACKUP_DIR/prediction_game_$DATE.db

# 保留最近7天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

添加到crontab：
```bash
crontab -e
# 添加：每天凌晨2点备份
0 2 * * * /opt/backup_db.sh
```

## 监控和日志

### 查看应用日志

容器化部署：
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

直接部署：
```bash
sudo tail -f /var/log/fupan-game.log
```

### 监控服务状态

```bash
# 检查服务状态
sudo supervisorctl status
# 或
sudo systemctl status fupan-game

# 检查端口
netstat -tlnp | grep 8000
```

## 性能优化

### 1. 启用Nginx缓存

在Nginx配置中添加：
```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 2. 配置Redis持久化

编辑 `/etc/redis/redis.conf`：
```
save 900 1
save 300 10
save 60 10000
```

### 3. 增加工作进程

修改启动命令：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 常见问题

### 1. 数据源API限制

某些数据源可能有IP限制，需要：
- 将ECS服务器IP添加到API白名单
- 使用阿里云NAT网关固定出口IP

### 2. 内存不足

如果遇到内存问题：
```bash
# 添加swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. 时区问题

确保服务器时区正确：
```bash
sudo timedatectl set-timezone Asia/Shanghai
```

## 升级部署

### 容器化升级

1. 重新构建并推送镜像
2. 在服务器执行：
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 直接部署升级

1. 备份数据库
2. 更新代码
3. 重启服务：
```bash
sudo supervisorctl restart fupan-game
```

## 联系支持

如遇到部署问题，请检查：
1. 服务器日志
2. 应用日志
3. 网络连接和防火墙设置

祝您部署顺利！