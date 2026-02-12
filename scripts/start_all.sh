#!/bin/bash
set -e

PROJECT_DIR="/root/autodl-tmp/pj-pharmaKG"
cd "$PROJECT_DIR"

echo "=== PharmaKG 服务启动 ==="

# ============================================================================
# 重要: 先清理旧进程，避免端口占用和僵尸进程
# ============================================================================
echo "[清理] 清理旧进程..."
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
sleep 2

# 确认清理完成
REMAINING=$(ps aux | grep -E "uvicorn|vite" | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "警告:仍有进程运行，强制清理"
    pkill -9 -f "python3.*8000" 2>/dev/null || true
    pkill -9 -f "node.*vite" 2>/dev/null || true
    sleep 2
fi

# ============================================================================
# 1. 启动 Neo4j（必须先启动，等待完全就绪）
# ============================================================================
echo "[1/3] 启动 Neo4j..."
$PROJECT_DIR/neo4j/current/bin/neo4j start 2>/dev/null || echo "Neo4j already running"

# 等待 Neo4j 完全启动（重要！）
echo "等待 Neo4j 就绪..."
sleep 8

# ============================================================================
# 2. 启动后端（必须激活 pharmakg-api 环境）
# ============================================================================
echo "[2/3] 启动 FastAPI 后端..."
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api

cd "$PROJECT_DIR"
nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload \
    > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid
echo "后端已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 5

# ============================================================================
# 3. 启动前端
# ============================================================================
echo "[3/3] 启动 Vite 前端..."
cd "$PROJECT_DIR/frontend"

# 使用绝对路径避免路径问题
nohup npm run dev > /root/autodl-tmp/pj-pharmaKG/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /root/autodl-tmp/pj-pharmaKG/logs/frontend.pid
echo "前端已启动 (PID: $FRONTEND_PID)"

# 等待前端启动
sleep 5

# ============================================================================
# 服务状态验证
# ============================================================================
echo ""
echo "=== 服务状态 ==="

# 检查后端健康
echo -n "后端: "
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "后端无响应，检查日志: tail -f logs/backend.log"
fi

# 检查 Neo4j
echo -n "Neo4j: "
$PROJECT_DIR/neo4j/current/bin/neo4j status 2>/dev/null | grep -o "running" || echo "未运行"

# 显示进程
echo ""
echo "进程列表:"
ps aux | grep -E "uvicorn|vite|neo4j" | grep -v grep | awk '{printf "  %-6s %s\n", $2, $11}' | head -5

echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  API: http://localhost:8000/docs"
echo "  Neo4j: http://localhost:7474"
