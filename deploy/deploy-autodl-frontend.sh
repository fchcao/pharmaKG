#!/bin/bash

#===========================================================
# 制药行业知识图谱 - AutoDL 前端部署脚本
# 适用于 AutoDL 云服务环境（不能使用Docker）
#===========================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/root/autodl-tmp/pj-pharmaKG"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}制药行业知识图谱 - AutoDL 前端部署脚本${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "⚠️  重要提示：AutoDL 是容器环境，本脚本使用本地开发模式"
echo ""

#===========================================================
# 1. 环境检查
#===========================================================
echo -e "\n${YELLOW}[1/6] 环境检查...${NC}"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: Node.js 未安装${NC}"
    echo "请先安装 Node.js: conda install -c conda-forge nodejs"
    exit 1
fi
echo -e "${GREEN}✓ Node.js 已安装: $(node --version)${NC}"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: npm 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm 已安装: $(npm --version)${NC}"

#===========================================================
# 2. 安装依赖
#===========================================================
echo -e "\n${YELLOW}[2/6] 安装前端依赖...${NC}"

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
else
    echo -e "${GREEN}✓ 依赖已存在，跳过安装${NC}"
fi

#===========================================================
# 3. 配置环境变量
#===========================================================
echo -e "\n${YELLOW}[3/6] 配置环境变量...${NC}"

# 创建生产环境配置
cat > .env.local << 'EOF'
# AutoDL 本地开发配置
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=PharmaKG
VITE_APP_VERSION=1.0.0
EOF

echo -e "${GREEN}✓ 环境变量配置完成${NC}"

#===========================================================
# 4. 构建前端
#===========================================================
echo -e "\n${YELLOW}[4/6] 构建前端应用...${NC}"

npm run build

if [ -d "dist" ]; then
    echo -e "${GREEN}✓ 前端构建完成${NC}"
else
    echo -e "${RED}错误: 前端构建失败${NC}"
    exit 1
fi

#===========================================================
# 5. 启动开发服务器
#===========================================================
echo -e "\n${YELLOW}[5/6] 启动前端开发服务器...${NC}"

# 检查端口 3000 是否被占用
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}警告: 端口 3000 已被占用${NC}"
    echo "正在尝试终止现有进程..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动开发服务器（后台运行）
echo "启动前端服务器（后台运行）..."
nohup npm run dev > /tmp/pharmakg-frontend.log 2>&1 &
FRONTEND_PID=$!

# 等待服务器启动
sleep 5

#===========================================================
# 6. 验证服务
#===========================================================
echo -e "\n${YELLOW}[6/6] 验证服务...${NC}"

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务已启动: http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务可能需要更多时间启动${NC}"
    echo "请检查日志: tail -f /tmp/pharmakg-frontend.log"
fi

#===========================================================
# 完成
#===========================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}前端部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "前端地址: ${YELLOW}http://localhost:3000${NC}"
echo -e "API 地址: ${YELLOW}http://localhost:8000${NC}"
echo -e "日志文件: ${YELLOW}/tmp/pharmakg-frontend.log${NC}"
echo ""
echo -e "常用命令:"
echo -e "  查看日志: ${YELLOW}tail -f /tmp/pharmakg-frontend.log${NC}"
echo -e "  停止服务: ${YELLOW}kill $FRONTEND_PID${NC}"
echo -e "  重启服务: ${YELLOW}cd $FRONTEND_DIR && npm run dev${NC}"
echo ""
echo -e "${GREEN}============================================================${NC}"
