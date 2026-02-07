#!/bin/bash

#===========================================================
# Neo4j 安装脚本 - AutoDL 环境
#===========================================================

set -e  # 遇到错误立即退出

NEO4J_DIR="/root/autodl-tmp/pj-pharmaKG/neo4j/current"
PROJECT_ROOT="/root/autodl-tmp/pj-pharmaKG"
DOCS_URL="docs/NEO4J_INSTALL_AUTODL.md"

echo "=========================================="
echo "Neo4j 安装脚本 - PharmaKG"
echo "=========================================="
echo ""

# 如果没有提供文件参数，显示安装指南
if [ -z "$1" ]; then
    echo "用法: bash scripts/install_neo4j.sh <path-to-neo4j-tar.gz>"
    echo ""
    echo "=========================================="
    echo "快速安装指南"
    echo "=========================================="
    echo ""
    echo "由于网络限制，自动下载不可用。请手动下载 Neo4j:"
    echo ""
    echo "步骤 1: 下载 Neo4j"
    echo "  - 访问: https://neo4j.com/download/"
    echo "  - 下载 'Neo4j Linux Tarball' (推荐版本: 5.x LTS)"
    echo "  - 文件名: neo4j-community-*.tar.gz"
    echo ""
    echo "步骤 2: 上传到 AutoDL"
    echo "  方法 A: JupyterLab 网页界面"
    echo "    点击上传按钮，选择文件，上传到 /root/autodl-tmp/"
    echo ""
    echo "  方法 B: 使用 scp"
    echo "    scp ~/Downloads/neo4j-community-*.tar.gz root@<autodl-ip>:/root/autodl-tmp/"
    echo ""
    echo "步骤 3: 运行此脚本"
    echo "  bash scripts/install_neo4j.sh /root/autodl-tmp/neo4j-community-*.tar.gz"
    echo ""
    echo "=========================================="
    echo ""
    echo "详细安装文档: $DOCS_URL"
    echo "在线查看: cat $DOCS_URL"
    echo ""
    exit 0
fi

# 检查文件是否存在
if [ ! -f "$1" ]; then
    echo "错误: 文件不存在: $1"
    echo ""
    echo "请确认:"
    echo "  1. 文件路径正确"
    echo "  2. 文件已上传到服务器"
    echo ""
    echo "查看详细安装指南: cat $DOCS_URL"
    exit 1
fi

# 检查文件是否是有效的 tar.gz 文件
if ! tar -tzf "$1" > /dev/null 2>&1; then
    echo "错误: 文件不是有效的 tar.gz 文件: $1"
    echo ""
    echo "请确保下载的是 Neo4j Community Edition Unix Tarball"
    exit 1
fi

echo "找到 Neo4j 安装包: $1"
echo ""

# 检查目录是否存在
if [ ! -d "$NEO4J_DIR" ]; then
    echo "创建 Neo4j 目录: $NEO4J_DIR"
    mkdir -p "$NEO4J_DIR"
fi

# 清理旧安装（如果需要）
if [ "$(ls -A $NEO4J_DIR 2>/dev/null)" ]; then
    echo "警告: Neo4j 目录不为空"
    echo "当前内容:"
    ls -la "$NEO4J_DIR"
    echo ""
    read -p "是否继续安装？这将覆盖现有文件。(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 0
    fi
fi

# 解压 Neo4j
echo "=========================================="
echo "正在解压 Neo4j..."
echo "=========================================="
tar -xzf "$1" -C "$NEO4J_DIR/" --strip-components=1

if [ $? -ne 0 ]; then
    echo "错误: 解压失败"
    exit 1
fi

echo "✓ 解压完成"
echo ""

# 复制配置文件
echo "=========================================="
echo "正在配置 Neo4j..."
echo "=========================================="

if [ -f "$PROJECT_ROOT/deploy/config/neo4j-autodl.conf" ]; then
    cp "$PROJECT_ROOT/deploy/config/neo4j-autodl.conf" "$NEO4J_DIR/conf/neo4j.conf"
    echo "✓ AutoDL 配置文件已复制"
else
    echo "警告: AutoDL 配置文件不存在，使用默认配置"
fi

# 创建必要的目录
mkdir -p "$NEO4J_DIR/data"
mkdir -p "$NEO4J_DIR/logs"
mkdir -p "$NEO4J_DIR/plugins"

echo "✓ 配置完成"
echo ""

# 检查 Java 环境
echo "=========================================="
echo "检查 Java 环境..."
echo "=========================================="

if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo "✓ Java 已安装: $JAVA_VERSION"
else
    echo "警告: 未找到 Java，Neo4j 需要 Java 11 或更高版本"
    echo ""
    echo "安装 Java:"
    echo "  conda install -c conda-forge openjdk"
    echo ""
fi

echo ""

# 设置初始密码并启动
echo "=========================================="
echo "启动 Neo4j..."
echo "=========================================="

cd "$NEO4J_DIR"

# 设置环境变量
export NEO4J_AUTH=neo4j/pharmaKG2024!

# 启动 Neo4j
bin/neo4j start

if [ $? -ne 0 ]; then
    echo "✗ Neo4j 启动失败"
    echo ""
    echo "请检查日志文件: $NEO4J_DIR/logs/neo4j.log"
    echo ""
    echo "常见问题:"
    echo "  1. Java 未安装或版本不兼容"
    echo "  2. 端口 7474 或 7687 被占用"
    echo "  3. 内存不足"
    echo ""
    echo "查看详细故障排除: cat $DOCS_URL"
    exit 1
fi

echo ""
echo "等待 Neo4j 启动..."
echo ""

# 等待 Neo4j 启动
MAX_WAIT=60
WAIT_TIME=0
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if bin/neo4j status | grep -q "running"; then
        break
    fi
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
    echo -n "."
done

echo ""
echo ""

# 验证启动状态
if bin/neo4j status | grep -q "running"; then
    echo "=========================================="
    echo "✓ Neo4j 安装并启动成功!"
    echo "=========================================="
    echo ""
    echo "访问信息:"
    echo "  Neo4j Browser: http://localhost:7474"
    echo "  Bolt 协议:    bolt://localhost:7687"
    echo "  用户名:       neo4j"
    echo "  密码:         pharmaKG2024!"
    echo ""
    echo "常用命令:"
    echo "  启动: cd $NEO4J_DIR && bin/neo4j start"
    echo "  停止: cd $NEO4J_DIR && bin/neo4j stop"
    echo "  状态: cd $NEO4J_DIR && bin/neo4j status"
    echo "  日志: tail -f $NEO4J_DIR/logs/neo4j.log"
    echo ""
    echo "下一步:"
    echo "  1. 激活 conda 环境: conda activate pharmakg-api"
    echo "  2. 运行 ETL 测试: python3 scripts/run_etl_test.py --all -l 10 -v"
    echo ""
    echo "详细文档: cat $DOCS_URL"
    echo ""
else
    echo "=========================================="
    echo "✗ Neo4j 启动失败"
    echo "=========================================="
    echo ""
    echo "请检查日志文件: $NEO4J_DIR/logs/neo4j.log"
    echo ""
    echo "查看日志:"
    echo "  tail -100 $NEO4J_DIR/logs/neo4j.log"
    echo ""
    echo "故障排除指南: cat $DOCS_URL"
    echo ""
    exit 1
fi
