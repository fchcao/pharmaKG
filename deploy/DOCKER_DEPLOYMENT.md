# PharmaKG Docker 部署指南

## 概述

本文档提供了 PharmaKG 项目的完整 Docker 部署指南，包括前端、后端和所有依赖服务。

## 架构组件

### 服务列表

- **Frontend**: React + Vite + Nginx (Port 80)
- **API**: FastAPI + Python 3.11 (Port 8000)
- **Neo4j**: 图数据库 (Ports 7474, 7473, 7687)
- **PostgreSQL**: 元数据库 (Port 5432)
- **Redis**: 缓存服务 (Port 6379)

## 快速开始

### 1. 前置要求

- Docker 20.10+
- Docker Compose 2.0+ (或 docker compose)
- 至少 8GB 内存
- 至少 20GB 可用磁盘空间

### 2. 标准部署（推荐）

```bash
# 克隆项目（如果还没有）
cd /root/autodl-tmp/pj-pharmaKG

# 运行部署脚本
cd deploy
chmod +x deploy.sh
./deploy.sh
```

### 3. AutoDL 部署

AutoDL 环境不支持 Docker 嵌套，使用以下方式：

```bash
# 部署后端和数据库
cd deploy
chmod +x deploy-autodl.sh
./deploy-autodl.sh

# 部署前端
chmod +x deploy-autodl-frontend.sh
./deploy-autodl-frontend.sh
```

## Docker Compose 配置

### 文件位置

```
deploy/docker/docker-compose.yml
```

### 服务配置

#### Frontend Service

```yaml
frontend:
  build:
    context: ../../frontend
    dockerfile: Dockerfile
    args:
      - VITE_API_BASE_URL=http://api:8000
  ports:
    - "80:80"
  depends_on:
    - api
```

#### API Service

```yaml
api:
  build:
    context: ../../
    dockerfile: deployment/Dockerfile
  ports:
    - "8000:8000"
  environment:
    - NEO4J_URI=bolt://neo4j:7687
    - NEO4J_USER=neo4j
    - NEO4J_PASSWORD=pharmaKG2024!
```

## 前端构建

### Dockerfile (多阶段构建)

**位置**: `frontend/Dockerfile`

#### Stage 1: Build Stage

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
```

#### Stage 2: Production Stage

```dockerfile
FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx 配置

**位置**: `frontend/nginx.conf`

主要功能：
- 静态文件服务
- API 代理到后端
- Gzip 压缩
- 缓存策略
- 健康检查

## 环境变量

### Frontend 环境变量

**文件**: `frontend/.env.production`

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_TRACKING=false
VITE_APP_NAME=PharmaKG
VITE_APP_VERSION=1.0.0
```

### API 环境变量

在 docker-compose.yml 中配置：

```yaml
environment:
  - NEO4J_URI=bolt://neo4j:7687
  - NEO4J_USER=neo4j
  - NEO4J_PASSWORD=pharmaKG2024!
  - POSTGRES_URI=postgresql://pharmakg:pharmaKG2024!@postgres:5432/pharmakg_meta
  - REDIS_URI=redis://redis:6379
```

## 部署流程

### 1. 构建镜像

```bash
cd deploy/docker
docker-compose build
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 检查状态

```bash
docker-compose ps
docker-compose logs -f
```

### 4. 健康检查

```bash
# 前端健康检查
curl http://localhost:80/health

# API 健康检查
curl http://localhost:8000/health

# Neo4j 健康检查
curl http://localhost:7474
```

## 常用命令

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f frontend
docker-compose logs -f api
docker-compose logs -f neo4j
```

### 重启服务

```bash
# 所有服务
docker-compose restart

# 特定服务
docker-compose restart frontend
docker-compose restart api
```

### 重建服务

```bash
# 重建并启动
docker-compose up -d --build frontend

# 重新构建镜像
docker-compose build --no-cache frontend
```

### 停止服务

```bash
docker-compose down
```

### 完全清理

```bash
# 停止并删除容器、网络、卷
docker-compose down -v

# 删除镜像
docker-compose down -v --rmi all
```

## 端口映射

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|----------|----------|------|
| Frontend | 80 | 80 | HTTP |
| API | 8000 | 8000 | FastAPI |
| Neo4j HTTP | 7474 | 7474 | Neo4j Browser |
| Neo4j HTTPS | 7473 | 7473 | Neo4j HTTPS |
| Neo4j Bolt | 7687 | 7687 | Bolt 协议 |
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存 |

## 数据持久化

### 卷配置

```yaml
volumes:
  - ./data/neo4j:/data
  - ./data/neo4j/logs:/logs
  - ./data/postgres:/var/lib/postgresql/data
  - ./data/redis:/data
```

### 备份

```bash
# Neo4j 备份
docker exec pharma-kg-neo4j neo4j-admin dump --database=neo4j --to=/backup/neo4j-backup.dump

# PostgreSQL 备份
docker exec pharma-kg-postgres pg_dump -U pharmakg pharmakg_meta > /backup/postgres-backup.sql
```

### 恢复

```bash
# Neo4j 恢复
docker exec pharma-kg-neo4j neo4j-admin load --from=/backup/neo4j-backup.dump --database=neo4j --force

# PostgreSQL 恢复
docker exec -i pharma-kg-postgres psql -U pharmakg pharmakg_meta < /backup/postgres-backup.sql
```

## 故障排除

### 前端无法访问

1. 检查容器状态：`docker-compose ps frontend`
2. 查看日志：`docker-compose logs frontend`
3. 检查端口占用：`lsof -i :80`
4. 重建容器：`docker-compose up -d --build frontend`

### API 连接失败

1. 检查网络：`docker network inspect deploy_pharma-kg-network`
2. 检查环境变量：`docker-compose exec api env | grep API`
3. 查看日志：`docker-compose logs api`

### Neo4j 连接问题

1. 等待启动：Neo4j 可能需要 60 秒启动
2. 检查内存：确保至少分配 2GB 堆内存
3. 查看日志：`docker-compose logs neo4j`

### 性能优化

1. 增加内存限制
2. 使用 --parallel 构建镜像
3. 启用 BuildKit

## 生产环境部署

### 1. 使用环境变量文件

```bash
# 创建 .env 文件
cat > deploy/docker/.env << EOF
NEO4J_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_secure_password
API_BASE_URL=https://api.yourdomain.com
EOF
```

### 2. 使用反向代理

建议在 Docker 前使用 Nginx 或 Traefik：

```nginx
server {
    listen 443 ssl;
    server_name pharmakg.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 安全加固

- 修改默认密码
- 限制网络访问
- 启用 HTTPS
- 定期更新镜像
- 配置防火墙规则

## 监控

### 健康检查端点

- Frontend: `http://localhost:80/health`
- API: `http://localhost:8000/health`
- Neo4j: `http://localhost:7474`

### 日志管理

```bash
# 实时查看所有日志
docker-compose logs -f --tail=100

# 导出日志
docker-compose logs > deployment.log
```

## 更新部署

### 更新前端

```bash
cd deploy/docker
docker-compose build frontend
docker-compose up -d frontend
```

### 更新 API

```bash
cd deploy/docker
docker-compose build api
docker-compose up -d api
```

### 完整更新

```bash
cd deploy/docker
docker-compose build
docker-compose up -d
```

## 参考资料

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Nginx 配置指南](https://nginx.org/en/docs/)
- [Neo4j Docker 镜像](https://hub.docker.com/_/neo4j)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
