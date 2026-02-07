#!/bin/bash

#===========================================================
# Neo4j 手动安装指南 - AutoDL 环境
#===========================================================

echo "=========================================="
echo "Neo4j 手动安装指南"
echo "=========================================="
echo ""
echo "由于网络限制，请手动下载 Neo4j："
echo ""
echo "方法 1: 从本地电脑上传"
echo "  1. 在本地电脑访问: https://neo4j.com/download/"
echo "  2. 下载 'Neo4j Linux Tarball' (推荐版本: 5.23.0)"
echo "  3. 通过 AutoDL 网页或 FileZilla 上传到 /root/autodl-tmp/"
echo ""
echo "方法 2: 在 JupyterLab 终端使用其他镜像"
echo "  尝试以下命令之一:"
echo "  wget https://ghproxy.com/https://github.com/neo4j/neo4j/releases/download/v5.23.0/neo4j-community-5.23.0-unix.tar.gz"
echo "  wget https://mirror.ghproxy.com/https://github.com/neo4j/neo4j/releases/download/v5.23.0/neo4j-community-5.23.0-unix.tar.gz"
echo ""
echo "上传/下载完成后，请运行:"
echo "  bash scripts/install_neo4j.sh /root/autodl-tmp/neo4j-community-5.23.0-unix.tar.gz"
echo ""
echo "或者手动解压:"
echo "  cd /root/autodl-tmp/pj-pharmaKG/neo4j"
echo "  tar -xzf ~/neo4j-community-5.23.0-unix.tar.gz -C current/"
echo "  mv current/neo4j-community-*/* current/ && rm -rf current/neo4j-community-*"
echo "  cp deploy/config/neo4j-autodl.conf current/conf/neo4j.conf"
echo "  cd current && bin/neo4j start"
echo ""

# 如果文件存在，自动安装
if [ -f "$1" ]; then
    echo "找到 Neo4j 安装包，开始自动安装..."

    NEO4J_DIR="/root/autodl-tmp/pj-pharmaKG/neo4j/current"
    PROJECT_ROOT="/root/autodl-tmp/pj-pharmaKG"

    # 解压
    echo "解压 Neo4j..."
    tar -xzf "$1" -C "$NEO4J_DIR/" --strip-components=1

    # 复制配置
    echo "复制配置文件..."
    cp "$PROJECT_ROOT/deploy/config/neo4j-autodl.conf" "$NEO4J_DIR/conf/neo4j.conf"

    # 设置初始密码
    export NEO4J_AUTH=neo4j/pharmaKG2024!

    # 启动 Neo4j
    echo "启动 Neo4j..."
    cd "$NEO4J_DIR"
    bin/neo4j start

    echo "等待 Neo4j 启动..."
    sleep 30

    # 验证
    if bin/neo4j status | grep -q "running"; then
        echo "✓ Neo4j 启动成功!"
        echo ""
        echo "访问信息:"
        echo "  Neo4j Browser: http://localhost:7474"
        echo "  用户名: neo4j"
        echo "  密码: pharmaKG2024!"
    else
        echo "✗ Neo4j 启动失败，请检查日志: logs/neo4j.log"
    fi
fi
