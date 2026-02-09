#!/bin/bash

#===========================================================
# 制药行业知识图谱 - 快速部署脚本
# 适用于标准 Docker 环境
#===========================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/root/autodl-tmp/pj-pharmaKG"
DEPLOY_DIR="$PROJECT_ROOT/deploy/docker"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}制药行业知识图谱 - Docker 部署脚本${NC}"
echo -e "${GREEN}============================================================${NC}"

#===========================================================
# 1. 环境检查
#===========================================================
echo -e "\n${YELLOW}[1/7] 环境检查...${NC}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装: $(docker --version)${NC}"

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}警告: docker-compose 未安装，尝试使用 docker compose...${NC}"
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi
echo -e "${GREEN}✓ Docker Compose 可用${NC}"

# 检查 Node.js (for frontend build)
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}警告: Node.js 未安装，前端容器将使用内置 Node.js${NC}"
else
    echo -e "${GREEN}✓ Node.js 已安装: $(node --version)${NC}"
fi

# 检查端口占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠ 端口 $1 已被占用${NC}"
        return 1
    fi
    return 0
}

ports=(7474 7473 7687 5432 6379 8000 80)
for port in "${ports[@]}"; do
    if ! check_port $port; then
        echo -e "${YELLOW}提示: 端口 $port 被占用，可能会导致启动失败${NC}"
    fi
done
echo -e "${GREEN}✓ 端口检查完成${NC}"

#===========================================================
# 2. 目录初始化
#===========================================================
echo -e "\n${YELLOW}[2/7] 目录初始化...${NC}"

cd "$DEPLOY_DIR"

# 创建数据目录
mkdir -p data/neo4j/data
mkdir -p data/neo4j/logs
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/import

# 设置权限
chmod -R 777 data

echo -e "${GREEN}✓ 数据目录已创建${NC}"

#===========================================================
# 3. 前端构建检查
#===========================================================
echo -e "\n${YELLOW}[3/7] 检查前端构建配置...${NC}"

# 检查前端文件是否存在
if [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
    echo -e "${GREEN}✓ 前端 package.json 存在${NC}"
else
    echo -e "${RED}错误: 前端 package.json 不存在${NC}"
    exit 1
fi

if [ -f "$PROJECT_ROOT/frontend/Dockerfile" ]; then
    echo -e "${GREEN}✓ 前端 Dockerfile 存在${NC}"
else
    echo -e "${RED}错误: 前端 Dockerfile 不存在${NC}"
    exit 1
fi

if [ -f "$PROJECT_ROOT/frontend/nginx.conf" ]; then
    echo -e "${GREEN}✓ 前端 Nginx 配置存在${NC}"
else
    echo -e "${RED}错误: 前端 Nginx 配置不存在${NC}"
    exit 1
fi

#===========================================================
# 4. Docker Compose 启动
#===========================================================
echo -e "\n${YELLOW}[4/7] 启动 Docker 容器...${NC}"

# 停止现有容器（如果有）
echo "停止现有容器..."
$DOCKER_COMPOSE down 2>/dev/null || true

# 构建镜像
echo "构建 Docker 镜像..."
$DOCKER_COMPOSE build

# 启动服务
echo "启动服务..."
$DOCKER_COMPOSE up -d

#===========================================================
# 5. 等待服务启动
#===========================================================
echo -e "\n${YELLOW}[5/7] 等待服务启动...${NC}"

# 等待 Neo4j 启动（最多60秒）
echo "等待 Neo4j 服务启动..."
for i in {1..60}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Neo4j 已启动 (耗时 ${i} 秒)${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}错误: Neo4j 启动超时${NC}"
        echo "请检查日志: $DOCKER_COMPOSE logs neo4j"
        exit 1
    fi
    sleep 1
    echo -n "."
done

# 等待 API 启动
echo ""
echo "等待 API 服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API 已启动 (耗时 ${i} 秒)${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}警告: API 启动超时${NC}"
    fi
    sleep 1
    echo -n "."
done

# 等待前端启动
echo ""
echo "等待前端服务启动..."
for i in {1..20}; do
    if curl -s http://localhost:80/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端已启动 (耗时 ${i} 秒)${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${YELLOW}警告: 前端启动超时${NC}"
    fi
    sleep 1
    echo -n "."
done

#===========================================================
# 6. 验证服务状态
#===========================================================
echo -e "\n${YELLOW}[6/7] 验证服务状态...${NC}"

# 检查容器状态
echo "容器状态:"
$DOCKER_COMPOSE ps

# 检查 Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Neo4j HTTP 可访问: http://localhost:7474${NC}"
else
    echo -e "${RED}✗ Neo4j HTTP 不可访问${NC}"
fi

# 检查 Bolt 端口
if nc -z localhost 7687 2>/dev/null; then
    echo -e "${GREEN}✓ Neo4j Bolt 可访问: bolt://localhost:7687${NC}"
else
    echo -e "${RED}✗ Neo4j Bolt 不可访问${NC}"
fi

# 检查 PostgreSQL
if $DOCKER_COMPOSE ps | grep postgres | grep -q "Up"; then
    echo -e "${GREEN}✓ PostgreSQL 运行中${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL 未运行${NC}"
fi

# 检查 Redis
if $DOCKER_COMPOSE ps | grep redis | grep -q "Up"; then
    echo -e "${GREEN}✓ Redis 运行中${NC}"
else
    echo -e "${YELLOW}⚠ Redis 未运行${NC}"
fi

# 检查 API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API 服务可访问: http://localhost:8000${NC}"
else
    echo -e "${RED}✗ API 服务不可访问${NC}"
fi

# 检查前端
if curl -s http://localhost:80/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务可访问: http://localhost:80${NC}"
else
    echo -e "${RED}✗ 前端服务不可访问${NC}"
fi

#===========================================================
# 7. 初始化数据
#===========================================================
echo -e "\n${YELLOW}[7/7] 初始化知识图谱...${NC}"

# 创建基础约束和索引
echo "创建基础约束和索引..."
docker exec pharma-kg-neo4j cypher-shell -u neo4j -p pharmaKG2024! \
    "CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (c:Compound) REQUIRE c.primary_id IS UNIQUE;" 2>/dev/null || echo "约束已存在或将在稍后创建"

echo -e "${GREEN}✓ 基础初始化完成${NC}"

#===========================================================
# 完成
#===========================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "前端界面: ${YELLOW}http://localhost:80${NC}"
echo -e "API 文档: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "Neo4j 浏览器: ${YELLOW}http://localhost:7474${NC}"
echo ""
echo -e "Neo4j 凭证:"
echo -e "  用户名: ${YELLOW}neo4j${NC}"
echo -e "  密码: ${YELLOW}pharmaKG2024!${NC}"
echo ""
echo -e "常用命令:"
echo -e "  查看日志: ${YELLOW}cd $DEPLOY_DIR && $DOCKER_COMPOSE logs -f${NC}"
echo -e "  查看前端日志: ${YELLOW}cd $DEPLOY_DIR && $DOCKER_COMPOSE logs -f frontend${NC}"
echo -e "  查看API日志: ${YELLOW}cd $DEPLOY_DIR && $DOCKER_COMPOSE logs -f api${NC}"
echo -e "  停止服务: ${YELLOW}cd $DEPLOY_DIR && $DOCKER_COMPOSE down${NC}"
echo -e "  重启服务: ${YELLOW}cd $DEPLOY_DIR && $DOCKER_COMPOSE restart${NC}"
echo -e "  重建前端: ${YELLOW}cd $DEPLOY_DIR && $DOCKER_COMPOSE build frontend && $DOCKER_COMPOSE up -d frontend${NC}"
echo ""
echo -e "${GREEN}============================================================${NC}"
