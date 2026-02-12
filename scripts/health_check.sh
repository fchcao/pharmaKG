#!/bin/bash

PROJECT_DIR="/root/autodl-tmp/pj-pharmaKG"

echo "=== PharmaKG 健康检查 ==="
echo ""

# 检查端口和服务
echo "[端口检查]"
check_service() {
    local port=$1
    local name=$2
    local pid=$(ps aux | grep -E "$3" | grep -v grep | awk 'NR==1{print $2}')
    if [ -n "$pid" ]; then
        echo "  $name (端口 $port): ✓ PID $pid"
        return 0
    else
        echo "  $name (端口 $port): ✗ 未运行"
        return 1
    fi
}

check_service 3000 "Vite 前端" "vite"
check_service 8000 "FastAPI 后端" "uvicorn"
check_service 7474 "Neo4j HTTP" "neo4j"
check_service 7687 "Neo4j Bolt" "neo4j"

# 检查后端健康
echo ""
echo "[后端健康]"
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$HEALTH" | jq . 2>/dev/null || echo "$HEALTH"
else
    echo "  后端无响应"
fi

# 检查 Neo4j
echo ""
echo "[Neo4j 状态]"
$PROJECT_DIR/neo4j/current/bin/neo4j status 2>/dev/null || echo "Neo4j 未运行"

# 检查进程
echo ""
echo "[进程列表]"
ps aux | grep -E "uvicorn|vite|neo4j" | grep -v grep | awk '{printf "  %-10s %6s  %s\n", $1, $2, $11}'
