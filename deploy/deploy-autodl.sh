#!/bin/bash

#===========================================================
# 制药行业知识图谱 - AutoDL 部署脚本
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
NEO4J_HOME="$PROJECT_ROOT/neo4j/current"
NEO4J_CONF="$PROJECT_ROOT/deploy/config/neo4j-autodl.conf"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}制药行业知识图谱 - AutoDL 部署脚本${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "⚠️  重要提示：AutoDL 是容器环境，不能使用Docker嵌套部署"
echo ""

#===========================================================
# 1. 环境检查
#===========================================================
echo -e "\n${YELLOW}[1/7] 环境检查...${NC}"

# 检查 Python
if command -v python &> /dev/null; then
    echo -e "${GREEN}✓ Python 已安装: $(python --version)${NC}"
else
    echo -e "${RED}✗ Python 未安装${NC}"
    exit 1
fi

# 检查 Java（Neo4j需要）
if command -v java &> /dev/null; then
    echo -e "${GREEN}✓ Java 已安装: $(java -version 2>&1 | head -1)${NC}"
else
    echo -e "${YELLOW}⚠ Java 未安装，将开始安装...${NC}"
fi

# 检查内存
echo -e "${GREEN}✓ 可用内存: $(free -h | grep Mem | awk '{print $2}')${NC}"

echo -e "${GREEN}✓ 环境检查完成${NC}"

#===========================================================
# 2. 安装 Java (如果需要)
#===========================================================
echo -e "\n${YELLOW}[2/7] 检查/安装 Java...${NC}"

if ! command -v java &> /dev/null; then
    echo "安装 JDK 11..."
    conda install -y -c conda-forge openjdk=11

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Java 安装成功${NC}"
    else
        echo -e "${RED}✗ Java 安装失败${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Java 已存在，跳过安装${NC}"
fi

#===========================================================
# 3. 创建目录结构
#===========================================================
echo -e "\n${YELLOW}[3/7] 创建目录结构...${NC}"

cd "$PROJECT_ROOT"

# 创建 Neo4j 目录
mkdir -p neo4j/current
mkdir -p neo4j/conf
mkdir -p neo4j/data
mkdir -p neo4j/logs
mkdir -p neo4j/plugins
mkdir -p data/import
mkdir -p backup

echo -e "${GREEN}✓ 目录结构创建完成${NC}"

#===========================================================
# 4. 下载 Neo4j
#===========================================================
echo -e "\n${YELLOW}[4/7] 下载 Neo4j...${NC}"

cd "$PROJECT_ROOT/neo4j"

if [ ! -d "current" ] || [ ! -f "current/bin/neo4j" ]; then
    NEO4J_VERSION="5.23.1"
    NEO4J_FILE="neo4j-community-${NEO4J_VERSION}-unix.tar.gz"

    if [ ! -f "$NEO4J_FILE" ]; then
        echo "正在下载 Neo4j ${NEO4J_VERSION}..."
        wget https://dist.neo4j.org/$NEO4J_FILE

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 下载完成${NC}"
        else
            echo -e "${RED}✗ 下载失败${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Neo4j 安装包已存在${NC}"
    fi

    # 解压
    echo "正在解压 Neo4j..."
    tar -xzf "$NEO4J_FILE"

    # 重命名目录
    if [ -d "neo4j-community-${NEO4J_VERSION}" ]; then
        mv "neo4j-community-${NEO4J_VERSION}" current
        echo -e "${GREEN}✓ 解压完成${NC}"
    fi
else
    echo -e "${GREEN}✓ Neo4j 已安装${NC}"
fi

#===========================================================
# 5. 配置 Neo4j
#===========================================================
echo -e "\n${YELLOW}[5/7] 配置 Neo4j...${NC}"

# 复制配置文件
cp "$NEO4J_CONF" conf/neo4j.conf

# 设置环境变量脚本
cat > /root/neo4j-env.sh << 'EOF'
#!/bin/bash
# Neo4j 环境变量

export NEO4J_HOME=$PROJECT_ROOT/neo4j/current
export NEO4J_CONF=$PROJECT_ROOT/deploy/config/neo4j-autodl.conf
export PATH=$NEO4J_HOME/bin:$PATH
export NEO4J_AUTH=neo4j/pharmaKG2024!

# Java 环境
export JAVA_HOME=$CONDA_PREFIX
export PATH=$JAVA_HOME/bin:$PATH
EOF

chmod +x /root/neo4j-env.sh

# 加载环境变量
source /root/neo4j-env.sh

echo -e "${GREEN}✓ 配置完成${NC}"

#===========================================================
# 6. 启动 Neo4j
#===========================================================
echo -e "\n${YELLOW}[6/7] 启动 Neo4j...${NC}"

cd "$NEO4J_HOME"

# 停止可能存在的旧实例
bin/neo4j stop 2>/dev/null || true

# 等待停止
sleep 2

# 启动 Neo4j
bin/neo4j start

# 等待启动
echo "等待 Neo4j 启动..."
for i in {1..60}; do
    if bin/neo4j status &> /dev/null; then
        echo -e "${GREEN}✓ Neo4j 已启动 (耗时 ${i} 秒)${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}✗ Neo4j 启动超时${NC}"
        echo "请检查日志: tail -f logs/neo4j.log"
        exit 1
    fi
    sleep 1
    echo -n "."
done

#===========================================================
# 7. 初始化数据库
#===========================================================
echo -e "\n${YELLOW}[7/7] 初始化数据库...${NC}"

# 等待Neo4j完全启动
sleep 10

# 创建初始化脚本
cat > /tmp/init_neo4j.cypher << 'EOF'
//===========================================================
// 初始化制药行业知识图谱数据库
//===========================================================

// 创建唯一性约束
CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (c:Compound) REQUIRE c.primary_id IS UNIQUE;
CREATE CONSTRAINT target_id IF NOT EXISTS FOR (t:Target) REQUIRE t.primary_id IS UNIQUE;
CREATE CONSTRAINT trial_id IF NOT EXISTS FOR (ct:ClinicalTrial) REQUIRE ct.trial_id IS UNIQUE;
CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (s:Subject) REQUIRE s.subject_id IS UNIQUE;

// 创建基础索引
CREATE INDEX compound_name IF NOT EXISTS FOR (c:Compound) ON (c.name);
CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name);
CREATE INDEX trial_protocol IF NOT EXISTS FOR (ct:ClinicalTrial) ON (ct.protocol_id);
CREATE INDEX subject_initials IF NOT EXISTS FOR (s:Subject) ON (s.initials);

// 显示配置
SHOW CONSTRAINTS;
SHOW INDEXES;
EOF

# 执行初始化
bin/cypher-shell -u neo4j -p pharmaKG2024! < /tmp/init_neo4j.cypher

echo -e "${GREEN}✓ 初始化完成${NC}"

#===========================================================
# 8. 创建便捷脚本
#===========================================================

echo -e "\n${YELLOW}创建便捷脚本...${NC}"

# 启动脚本
cat > /root/start-pharmakg.sh << 'EOF'
#!/bin/bash
source /root/neo4j-env.sh
cd $NEO4J_HOME
bin/neo4j start
echo "Neo4j 已启动，访问地址: http://localhost:7474"
EOF

# 停止脚本
cat > /root/stop-pharmakg.sh << 'EOF'
#!/bin/bash
source /root/neo4j-env.sh
cd $NEO4J_HOME
bin/neo4j stop
echo "Neo4j 已停止"
EOF

# 状态检查脚本
cat > /root/status-pharmakg.sh << 'EOF'
#!/bin/bash
source /root/neo4j-env.sh
cd $NEO4J_HOME
bin/neo4j status
EOF

chmod +x /root/start-pharmakg.sh /root/stop-pharmakg.sh /root/status-pharmakg.sh

echo -e "${GREEN}✓ 便捷脚本已创建${NC}"
echo "  - /root/start-pharmakg.sh  (启动)"
echo "  - /root/stop-pharmakg.sh   (停止)"
echo "  - /root/status-pharmakg.sh  (状态检查)"

#===========================================================
# 9. 验证部署
#===========================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# 检查服务状态
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Neo4j HTTP 可访问: http://localhost:7474${NC}"
else
    echo -e "${YELLOW}⚠ Neo4j HTTP 不可访问，可能需要稍等片刻${NC}"
fi

if nc -z localhost 7687 2>/dev/null; then
    echo -e "${GREEN}✓ Neo4j Bolt 可访问: bolt://localhost:7687${NC}"
else
    echo -e "${YELLOW}⚠ Neo4j Bolt 不可访问，可能需要稍等片刻${NC}"
fi

echo ""
echo -e "访问信息:"
echo -e "  Neo4j 浏览器: ${YELLOW}http://localhost:7474${NC}"
echo -e "  用户名: ${YELLOW}neo4j${NC}"
echo -e "  密码: ${YELLOW}pharmaKG2024!${NC}"
echo -e "  Bolt连接: ${YELLOW}bolt://localhost:7687${NC}"
echo ""
echo -e "常用命令:"
echo -e "  连接Neo4j: ${YELLOW}cd $NEO4J_HOME && bin/cypher-shell -u neo4j -p pharmaKG2024!${NC}"
echo -e "  查看日志: ${YELLOW}tail -f $NEO4J_HOME/logs/neo4j.log${NC}"
echo -e "  停止服务: ${YELLOW}/root/stop-pharmakg.sh${NC}"
echo -e "  重启服务: ${YELLOW}/root/start-pharmakg.sh${NC}"
echo ""
echo -e "${GREEN}============================================================${NC}"
