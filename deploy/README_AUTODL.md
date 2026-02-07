# 制药行业知识图谱 - AutoDL 部署指南

**项目版本**: v1.0
**部署环境**: AutoDL 云服务
**最后更新**: 2025-02-06

---

## AutoDL 环境说明

AutoDL 是一个云GPU租用平台，提供预配置的深度学习环境。**重要**：AutoDL实例本身就是容器环境，因此不能使用Docker进行嵌套部署。

### AutoDL 环境特点

- 已预装：Python 3.x、CUDA/cuDNN、常用深度学习框架
- 提供JupyterLab作为主要工作界面
- 可以通过JupyterLab中的终端执行命令
- 支持SSH连接（需要开放端口）

---

## 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AutoDL 容器实例                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              JupyterLab (工作界面)                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│  │  │ Notebook    │  │ Terminal    │  │ File        │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   应用服务                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│  │  │ Neo4j       │  │ Python API   │  │ 前端界面     │    │ │
│  │  │ (直接安装)   │  │ (可选)       │  │ (可选)       │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   数据存储                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│  │  │ /root/data   │  │ /autodl-tmp │  │ 公网网盘     │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速部署指南

### 步骤 1: 准备工作

在JupyterLab中打开终端，执行以下命令：

```bash
# 切换到工作目录
cd /root/autodl-tmp/pj-pharmaKG

# 检查环境
echo "=== 环境检查 ==="
python --version
java -version  # 检查是否已安装Java（Neo4j需要）
```

### 步骤 2: 安装 Neo4j

```bash
# 创建工作目录
mkdir -p /root/autodl-tmp/pj-pharmaKG/neo4j
cd /root/autodl-tmp/pj-pharmaKG/neo4j

# 下载 Neo4j 社区版（Linux tar.gz）
wget https://dist.neo4j.org/neo4j-community-5.23.1-unix.tar.gz

# 解压
tar -xzf neo4j-community-5.23.1-unix.tar.gz

# 重命名目录
mv neo4j-community-5.23.1/ current
```

### 步骤 3: 配置 Neo4j

```bash
# 创建配置目录
mkdir -p /root/autodl-tmp/pj-pharmaKG/neo4j/conf

# 复制配置文件（已预先准备好）
cp /root/autodl-tmp/pj-pharmaKG/deploy/config/neo4j-autodl.conf \
   /root/autodl-tmp/pj-pharmaKG/neo4j/conf/neo4j.conf

# 设置环境变量
export NEO4J_HOME=/root/autodl-tmp/pj-pharmaKG/neo4j/current
export PATH=$NEO4J_HOME/bin:$PATH

# 设置初始密码
export NEO4J_AUTH=neo4j/pharmaKG2024!
```

### 步骤 4: 启动 Neo4j

```bash
# 启动 Neo4j（后台运行）
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current

# 后台启动
bin/neo4j start

# 等待启动（约30-60秒）
sleep 30

# 检查状态
bin/neo4j status

# 如果显示 "Neo4j is running" 则启动成功
```

### 步骤 5: 验证部署

```bash
# 检查 Neo4j HTTP 接口
curl http://localhost:7474

# 或使用 cypher-shell 连接
bin/cypher-shell -u neo4j -p pharmaKG2024!

# 测试查询
MATCH (n) RETURN count(n);
```

### 步骤 6: 开放外部访问（可选）

如果需要从外部访问Neo4j（如通过本地电脑连接），需要开放端口：

```bash
# 检查autodl控制台是否有开放端口功能
# 如果有，开放 7474（HTTP）和 7687（Bolt）端口

# 修改neo4j.conf，监听所有地址
# 将 dbms.default_listen_address=0.0.0.0
```

---

## 常用操作

### 启动/停止 Neo4j

```bash
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current

# 启动
bin/neo4j start

# 停止
bin/neo4j stop

# 重启
bin/neo4j restart

# 查看状态
bin/neo4j status
```

### 查看 Neo4j 日志

```bash
# 查看日志文件
tail -f logs/neo4j.log

# 查看调试日志
tail -f logs/debug.log
```

### Cypher Shell 使用

```bash
# 连接到 Neo4j
bin/cypher-shell -u neo4j -p pharmaKG2024!

# 执行查询
:MATCH (c:Compound) RETURN count(c);

# 退出
:exit
```

---

## Python API 连接

> **重要说明**: AutoDL 服务器已预配置 `pharmakg-api` conda 环境，包含所有必需依赖。

### 激活环境并检查依赖

```bash
# 激活预配置的环境
conda activate pharmakg-api

# 检查关键依赖是否已安装
pip list | grep -E "neo4j|py2neo|fastapi|uvicorn|pandas"

# 如果依赖缺失或需要更新，重新安装：
pip install -r /root/autodl-tmp/pj-pharmaKG/api/requirements.txt
```

### 安装 Neo4j Python 驱动

```bash
# 仅在环境中没有安装时执行
# 在 JupyterLab 的 Notebook 或 Terminal 中执行
pip install neo4j py2neo
```

### Python 连接示例

```python
from neo4j import GraphDatabase

# 连接配置
uri = "bolt://localhost:7687"
username = "neo4j"
password = "pharmaKG2024!"

# 创建驱动实例
driver = GraphDatabase.driver(uri, auth=(username, password))

# 测试查询
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(f"数据库中的节点数量: {result.single()['count']}")

driver.close()
```

---

## 数据导入

### 准备数据文件

```bash
# 在 AutoDL 中上传数据文件的方法：

# 方法1: 使用 JupyterLab 的上传功能
# - 在 JupyterLab 界面找到上传按钮
# - 上传数据文件

# 方法2: 使用公网网盘（推荐）
# - 将数据上传到autodl提供的公网网盘
# - 在实例中下载到工作目录

# 方法3: 使用 git clone
# git clone <repository-url>

# 方法4: 使用 wget
# wget <data-file-url>
```

### 导入数据到 Neo4j

```bash
# 将数据文件放到 import 目录
mkdir -p /root/autodl-tmp/pj-pharmaKG/data/import
# 上传或下载数据到这个目录

# 使用 cypher-shell 导入
bin/cypher-shell -u neo4j -p pharmaKG2024! \
  < /root/autodl-tmp/pj-pharmaKG/scripts/import_rd_data.cypher
```

---

## 性能优化

### 内存配置

根据autodl实例的GPU型号和可用内存，调整Neo4j内存配置：

```bash
# 编辑配置文件
vi /root/autodl-tmp/pj-pharmaKG/neo4j/conf/neo4j.conf

# 调整以下参数（根据实例可用内存）：
# dbms.memory.heap.initial_size=2G
# dbms.memory.heap.max_size=4G
# dbms.memory.pagecache.size=2G
```

### GPU加速（可选）

如果使用支持GPU加速的功能：

```bash
# 先激活环境
conda activate pharmakg-api

# 安装 GPU 加速库（根据CUDA版本选择）
pip install cupy-cuda11x
```

---

## 故障排除

### 问题1: Java 未安装

**症状**: 执行 `java -version` 报错

**解决方案**:
```bash
# 安装 JDK 11
conda install -c conda-forge openjdk=11

# 或下载安装
wget https://download.java.net/java/GA/jdk11/latest/jdk-11_linux-x64_bin.tar.gz
tar -xzf jdk-11_linux-x64_bin.tar.gz
export JAVA_HOME=/path/to/jdk-11
export PATH=$JAVA_HOME/bin:$PATH
```

### 问题2: 端口被占用

**症状**: 启动Neo4j时端口被占用

**解决方案**:
```bash
# 检查端口占用
lsof -i :7474
lsof -i :7687

# 修改配置使用其他端口
# 编辑 conf/neo4j.conf
# dbms.connector.http.listen_address=:7475
# dbms.connector.bolt.listen_address=:7688
```

### 问题3: 内存不足

**症状**: Neo4j启动失败或频繁崩溃

**解决方案**:
```bash
# 检查可用内存
free -h

# 减少Neo4j内存分配
# 编辑 conf/neo4j.conf，减少内存配置
# dbms.memory.heap.max_size=2G
# dbms.memory.pagecache.size=1G
```

---

## 开发工作流

### 1. 使用 JupyterLab 开发

```python
# 在 Jupyter Notebook 中

# 激活预配置的环境（在终端中执行）
# conda activate pharmakg-api

# 检查依赖（可选）
# !pip list | grep -E "neo4j|py2neo|pandas"

# 安装依赖（仅在缺失时执行）
# !pip install neo4j py2neo pandas

# 导入连接
from neo4j import GraphDatabase

# 执行查询和分析
driver = GraphDatabase.driver("bolt://localhost:7687",
                                auth=("neo4j", "pharmaKG2024!"))

# 数据分析工作...
```

### 2. 使用 SSH 远程开发

```bash
# 从本地电脑 SSH 连接到 AutoDL 实例
ssh root@<autodl-instance-ip> -p <port>

# 使用 VSCode 远程开发
# 参考 AutoDL 文档中的 VSCode 配置
```

---

## 自动化脚本

### 创建启动脚本

```bash
# 创建启动脚本
cat > /root/start-neo4j.sh << 'EOF'
#!/bin/bash
export NEO4J_HOME=/root/autodl-tmp/pj-pharmaKG/neo4j/current
export PATH=$NEO4J_HOME/bin:$PATH
cd $NEO4J_HOME
bin/neo4j start
echo "Neo4j 已启动，PID: $(cat pid/neo4j.pid)"
EOF

chmod +x /root/start-neo4j.sh
```

### 创建停止脚本

```bash
# 创建停止脚本
cat > /root/stop-neo4j.sh << 'EOF'
#!/bin/bash
export NEO4J_HOME=/root/autodl-tmp/pj-pharmaKG/neo4j/current
export PATH=$NEO4J_HOME/bin:$PATH
cd $NEO4J_HOME
bin/neo4j stop
echo "Neo4j 已停止"
EOF

chmod +x /root/stop-neo4j.sh
```

---

## 数据持久化

### AutoDL 数据保留规则

- 实例关机后数据保留
- 连续关机15天实例将被释放
- 建议定期备份重要数据

### 备份策略

```bash
# 备份 Neo4j 数据
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current

# 创建备份
bin/neo4j-admin backup --backup-dir=/root/backup \
  --from=/root/autodl-tmp/pj-pharmaKG/neo4j/data \
  --name=graph.db-backup-$(date +%Y%m%d)

# 下载备份到本地
# 使用 FileZilla 或其他工具下载备份文件
```

---

## 开放端口访问

### 方案 1: AutoDL 开放端口功能

如果autodl提供开放端口功能：

1. 在控制台找到"开放端口"选项
2. 开放 7474（HTTP）和 7687（Bolt）
3. 配置安全组规则
4. 使用公网IP和端口连接

### 方案 2: SSH 隧道

从本地电脑通过SSH隧道访问：

```bash
# 在本地电脑执行
ssh -L 7474:localhost:7474 \
    -L 7687:localhost:7687 \
    root@<autodl-instance-ip> -p <port>

# 然后通过本地端口访问
# http://localhost:7474
```

---

## 与原Docker方案的差异

| 特性 | Docker方案 | AutoDL直接安装方案 |
|-----|-----------|------------------|
| 部署方式 | Docker Compose | 直接安装+配置 |
| 环境隔离 | 容器隔离 | 同一环境 |
| 数据持久化 | Docker卷 | 本地文件系统 |
| 服务管理 | docker-compose | 手动脚本 |
| 启动方式 | docker-compose up | bin/neo4j start |
| 停止方式 | docker-compose down | bin/neo4j stop |
| 配置管理 | 环境变量+配置文件 | 配置文件 |

---

## 下一步

1. **导入数据**: 参考Schema设计文档，导入各领域数据
2. **开发查询**: 在JupyterLab中开发Cypher查询
3. **API开发**: 开发Python API服务（可选）
4. **可视化**: 开发可视化界面（可选）

---

**相关文档**:
- [AutoDL快速开始](https://www.autodl.com/docs/quick_start/)
- [Schema设计文档](../docs/schema/制药行业知识图谱Schema设计文档.md)
- [实施路线图](../docs/schema/实施路线图.md)

---

**最后更新**: 2025-02-06
**适用环境**: AutoDL 云服务
