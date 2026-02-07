# 🚀制药行业知识图谱 - AutoDL 快速部署指南

**环境**: AutoDL 云服务
**部署时间**: 约 15-30 分钟
**最后更新**: 2025-02-06

---

## ⚠️ 重要说明

**AutoDL 是容器环境，不能使用 Docker 嵌套部署！**

本指南提供直接在 AutoDL 环境中部署 Neo4j 图数据库的方案。

---

## 📋 前置要求检查

### 1. 在 JupyterLab 中打开终端

在 AutoDL 实例的 JupyterLab 页面中：
1. 点击 "File" → "New" → "Terminal"
2. 打开终端后，继续以下步骤

### 2. 检查环境

```bash
# 切换到项目目录
cd /root/autodl-tmp/pj-pharmaKG

# 检查 Python
python --version

# 检查 Java（如未安装会自动安装）
java -version
```

---

## 🚀 一键部署

### 方法1: 使用部署脚本（推荐）

```bash
# 进入部署目录
cd deploy

# 执行 AutoDL 部署脚本
chmod +x deploy-autodl.sh
./deploy-autodl.sh
```

脚本会自动完成：
- ✅ Java 安装（如需要）
- ✅ Neo4j 下载和解压
- ✅ 环境配置
- ✅ Neo4j 启动
- ✅ 数据库初始化

### 方法2: 手动部署

#### 步骤 1: 安装 Java（如需要）

```bash
# 使用 conda 安装 JDK 11
conda install -y -c conda-forge openjdk=11

# 验证安装
java -version
```

#### 步骤 2: 下载 Neo4j

```bash
cd /root/autodl-tmp/pj-pharmaKG
mkdir -p neo4j/current
cd neo4j/current

# 下载 Neo4j 5.23.1
wget https://dist.neo4j.org/neo4j-community-5.23.1-unix.tar.gz

# 解压
tar -xzf neo4j-community-5.23.1-unix.tar.gz
mv neo4j-community-5.23.1 current/
```

#### 步骤 3: 配置 Neo4j

```bash
# 复制配置文件
cp deploy/config/neo4j-autodl.conf conf/neo4j.conf

# 设置环境变量
export NEO4J_HOME=/root/autodl-tmp/pj-pharmaKG/neo4j/current
export PATH=$NEO4J_HOME/bin:$PATH
```

#### 步骤 4: 启动 Neo4j

```bash
cd $NEO4J_HOME

# 启动 Neo4j
bin/neo4j start

# 等待启动（约30秒）
sleep 30

# 检查状态
bin/neo4j status
```

#### 步骤 5: 验证部署

```bash
# 检查 HTTP 接口
curl http://localhost:7474

# 使用 Cypher Shell 连接
bin/cypher-shell -u neo4j -p pharmaKG2024!

# 测试查询
MATCH (n) RETURN count(n);
:exit
```

---

## ✅ 验证成功

部署成功后，您应该能看到：

```
============================================================
部署完成！
============================================================

✓ Neo4j HTTP 可访问: http://localhost:7474
✓ Neo4j Bolt 可访问: bolt://localhost:7687

访问信息:
  Neo4j 浏览器: http://localhost:7474
  用户名: neo4j
  密码: pharmaKG2024!
  Bolt连接: bolt://localhost:7687
```

---

## 🔧 后续配置

### 1. 创建便捷脚本

脚本已自动创建，可直接使用：

```bash
# 启动 Neo4j
/root/start-pharmakg.sh

# 停止 Neo4j
/root/stop-pharmakg.sh

# 检查状态
/root/status-pharmakg.sh
```

### 2. Python 连接

> **重要说明**: AutoDL 服务器已预配置 `pharmakg-api` conda 环境，包含所有必需依赖。

```bash
# 激活预配置的环境
conda activate pharmakg-api

# 检查依赖是否已安装（可选）
pip list | grep -E "neo4j|py2neo|fastapi|uvicorn"

# 如果依赖缺失，重新安装：
pip install -r /root/autodl-tmp/pj-pharmaKG/api/requirements.txt
```

```python
# 在 Jupyter Notebook 中

# 连接示例
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
username = "neo4j"
password = "pharmaKG2024!"

driver = GraphDatabase.driver(uri, auth=(username, password))

# 测试连接
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(f"节点数量: {result.single()['count']}")
```

### 3. 导入本体和数据

```bash
# 导入初始化约束和索引
cd /root/autodl-tmp/pj-pharmaKG
cat scripts/init_constraints.cypher | \
    neo4j/current/bin/cypher-shell -u neo4j -p pharmaKG2024!

# 导入本体文件
neo4j/current/bin/cypher-shell -u neo4j -p pharmaKG2024! \
  < ontologies/pharma-kg.ttl
```

---

## 📊 数据导入

### 上传数据到 AutoDL

**方法1: JupyterLab 上传**
1. 在 JupyterLab 中点击上传按钮
2. 选择数据文件上传
3. 文件会保存到 `/root/autodl-fs/` 目录

**方法2: 公网网盘（推荐）**
1. 在本地电脑将数据上传到 AutoDL 公网网盘
2. 在 AutoDL 控制台下载到实例
3. 移动到工作目录

**方法3: Git Clone**
```bash
git clone <repository-url>
```

### 导入数据到 Neo4j

```bash
# 将数据文件移到 import 目录
mv /path/to/your/data.csv /root/autodl-tmp/pj-pharmaKG/data/import/

# 使用 Cypher 导入
bin/cypher-shell -u neo4j -p pharmaKG2024! - <<EOF
LOAD CSV WITH HEADERS FROM 'file:///root/autodl-tmp/pj-pharmaKG/data/import/compounds.csv' AS row
CREATE (c:Compound {
    primary_id: row.id,
    name: row.name,
    smiles: row.smiles,
    inchikey: row.inchikey
})
SET c.created_at = datetime();
EOF
```

---

## 🔍 常用操作

### 查看 Neo4j 状态

```bash
/root/status-pharmakg.sh
# 或手动
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
bin/neo4j status
```

### 查看日志

```bash
tail -f /root/autodl-tmp/pj-pharmaKG/neo4j/current/logs/neo4j.log
```

### 重启 Neo4j

```bash
/root/stop-pharmakg.sh
/root/start-pharmakg.sh
```

---

## 📝 开发工作流

### 1. 在 JupyterLab 中开发

```python
# 创建新的 Notebook

# 在终端中先激活预配置的环境：
# conda activate pharmakg-api

# Cell 1: 检查依赖（可选）
!pip list | grep -E "neo4j|pandas|matplotlib"

# Cell 1: 安装依赖（仅在缺失时执行）
# !pip install neo4j pandas matplotlib

# Cell 2: 导入库
from neo4j import GraphDatabase
import pandas as pd
import matplotlib.pyplot as plt

# Cell 3: 连接数据库
driver = GraphDatabase.driver("bolt://localhost:7687",
                                auth=("neo4j", "pharmaKG2024!"))

# Cell 4: 执行查询
with driver.session() as session:
    result = session.run("""
        MATCH (c:Compound)-[r:inhibits]->(t:Target)
        WHERE c.development_stage = 'PCC'
        RETURN c.name, t.name, r.activity_value
        ORDER BY r.activity_value ASC
        LIMIT 10
    """)
    for record in result:
        print(record)
```

### 2. 使用 Cypher Shell

```bash
# 在终端中执行
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
bin/cypher-shell -u neo4j -p pharmaKG2024!

# 进入 Cypher Shell 后执行查询
MATCH (c:Compound) RETURN c LIMIT 5;
:help
:exit
```

---

## 🐛 故障排除

### 问题1: Java 未安装

```bash
# 安装 Java
conda install -y -c conda-forge openjdk=11

# 或使用 apt-get
apt-get update
apt-get install -y openjdk-11-jre
```

### 问题2: 端口占用

```bash
# 检查端口
lsof -i :7474
lsof -i :7687

# 修改配置使用其他端口
# 编辑 conf/neo4j.conf
# dbms.connector.http.listen_address=:7475
# dbms.connector.bolt.listen_address=:7688
```

### 问题3: 内存不足

```bash
# 检查可用内存
free -h

# 减少 Neo4j 内存分配
# 编辑 conf/neo4j.conf
# dbms.memory.heap.max_size=2G
# dbms.memory.pagecache.size=1G
```

### 问题4: Neo4j 启动失败

```bash
# 查看详细日志
tail -100 /root/autodl-tmp/pj-pharmaKG/neo4j/current/logs/neo4j.log

# 尝试修复
rm -rf /root/autodl-tmp/pj-pharmaKG/neo4j/current/data/graph.db/*
bin/neo4j start
```

---

## 💾 数据持久化

### AutoDL 数据保留规则

- ✅ 实例关机后数据保留
- ✅ 环境配置自动保存
- ⚠️  连续关机 15 天实例释放
- 💾 建议定期备份到本地或公网网盘

### 备份到本地

```bash
# 1. 在 AutoDL 中创建备份
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
bin/neo4j-admin backup --backup-dir=/root/backup \
  --from=/root/autodl-tmp/pj-pharmaKG/neo4j/data \
  --name=graph.db-backup-$(date +%Y%m%d)

# 2. 通过 AutoDL 公网网盘下载到本地
# 3. 或使用 FileZilla 等工具下载
```

---

## 📚 相关文档

- [AutoDL 快速开始](https://www.autodl.com/docs/quick_start/)
- [Schema设计文档](../docs/schema/制药行业知识图谱Schema设计文档.md)
- [实施路线图](../docs/schema/实施路线图.md)
- [完整部署指南](./README_AUTODL.md)

---

## 🎯 快速测试

### 测试 1: 查询节点数量

```cypher
MATCH (n) RETURN count(n);
```

### 测试 2: 创建测试节点

```cypher
CREATE (c:Test {name: "AutoDL Test", created: datetime()})
RETURN c;
```

### 测试 3: 查询测试节点

```cypher
MATCH (c:Test {name: "AutoDL Test"}) RETURN c;
```

### 清理测试数据

```cypher
MATCH (c:Test {name: "AutoDL Test"}) DELETE c;
```

---

## 📞 获取帮助

如遇到问题：

1. 查看 [AutoDL 常见问题](https://www.autodl.com/docs/常见问题/)
2. 查看 [Neo4j 手册](https://neo4j.com/docs/)
3. 联系项目支持

---

**文档版本**: v1.0
**最后更新**: 2025-02-06
**适用环境**: AutoDL 云服务

---

*祝您使用愉快！*
