#!/bin/bash

PROJECT_DIR="/root/autodl-tmp/pj-pharmaKG"

echo "=== PharmaKG 服务停止 ==="

# 1. 停止前端
if [ -f "$PROJECT_DIR/logs/frontend.pid" ]; then
    PID=$(cat "$PROJECT_DIR/logs/frontend.pid")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo "前端已停止 (PID: $PID)"
    fi
    rm -f "$PROJECT_DIR/logs/frontend.pid"
else
    echo "前端 PID 文件不存在"
fi

# 2. 停止后端
if [ -f "$PROJECT_DIR/logs/backend.pid" ]; then
    PID=$(cat "$PROJECT_DIR/logs/backend.pid")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo "后端已停止 (PID: $PID)"
    fi
    rm -f "$PROJECT_DIR/logs/backend.pid"
else
    echo "后端 PID 文件不存在"
fi

# 3. 停止 Neo4j
echo "停止 Neo4j..."
$PROJECT_DIR/neo4j/current/bin/neo4j stop 2>/dev/null || echo "Neo4j 未运行"

echo "所有服务已停止"
