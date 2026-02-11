# Neo4j 安装指南 - AutoDL 环境

**文档版本**: v1.1
**创建日期**: 2026-02-07
**最后更新**: 2026-02-07
**适用环境**: AutoDL 云服务 (Ubuntu 22.04)

---

## 当前状态

| 项目 | 状态 | 说明 |
|-----|------|------|
| Neo4j 安装 | ✅ 完成 | 版本 5.26.21 (RPM 安装) |
| Java 环境 | ✅ 完成 | OpenJDK 17.0.18 |
| 目录结构 | ✅ 完成 | `/root/autodl-tmp/pj-pharmaKG/neo4j/current/` |
| 配置文件 | ✅ 完成 | 使用 RPM 默认配置 |
| 服务状态 | ✅ 运行中 | HTTP 7474, Bolt 7687 |

---

## 快速安装（RPM 包 - 推荐）

### 方法 0: 使用 RPM 包安装（已验证）

如果您有 Neo4j RPM 包，这是最简单的安装方式：

```bash
# 1. 上传 RPM 包到 /root/autodl-tmp/
# 文件名示例: neo4j-community-5.26.21-1.noarch.rpm

# 2. 安装 Java 17（Neo4j 5.x 需要 Java 17）
apt-get update && apt-get install -y openjdk-17-jdk

# 3. 设置环境变量
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# 4. 提取 RPM 包
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
bsdtar -xf /root/autodl-tmp/neo4j-community-*.rpm

# 5. 重新组织文件结构
mv usr/share/neo4j/* .
mv etc/neo4j conf
mkdir -p data logs plugins run

# 6. 创建必要的系统目录
mkdir -p /etc/neo4j /var/log/neo4j /var/lib/neo4j/{plugins,import,data}
cp conf/user-logs.xml /etc/neo4j/
cp conf/server-logs.xml /etc/neo4j/

# 7. 设置初始密码
./bin/neo4j-admin dbms set-initial-password pharmaKG2024!

# 8. 启动 Neo4j
./bin/neo4j start

# 9. 验证状态
./bin/neo4j status
```

---

## 其他安装方法

### 方法 1: 通过 JupyterLab 网页界面上传

#### 步骤 1: 下载 Neo4j

在您的**本地电脑**上执行：

1. 访问 Neo4j 官方下载页面: https://neo4j.com/download/
2. 选择 **"Neo4j Linux Tarball"** 或 **"RPM Package"** (推荐版本: 5.x LTS)
3. 下载文件名类似: `neo4j-community-5.xx.x-unix.tar.gz` 或 `.rpm`

> **注意**: 请下载 Community Edition (免费版本)，不需要 Enterprise Edition

#### 步骤 2: 上传到 AutoDL

1. 在 JupyterLab 左侧文件浏览器中，找到上传按钮（向上箭头图标）
2. 选择您刚才下载的 Neo4j 文件
3. 上传到 `/root/autodl-tmp/` 目录

#### 步骤 3: 运行安装脚本

```bash
# 对于 tar.gz 文件
bash /root/autodl-tmp/pj-pharmaKG/scripts/install_neo4j.sh /root/autodl-tmp/neo4j-community-*.tar.gz

# 或使用 RPM 方法（见上文）
```

---

### 方法 2: 使用 FileZilla 或 scp 上传

#### 在本地电脑执行：

```bash
# 将文件路径和 AutoDL IP 替换为实际值
scp ~/Downloads/neo4j-community-* root@<your-autodl-ip>:/root/autodl-tmp/
```

#### 在 AutoDL 终端执行：

```bash
# 如果是 RPM 包，使用 RPM 方法（见上文）
# 如果是 tar.gz，使用安装脚本
bash /root/autodl-tmp/pj-pharmaKG/scripts/install_neo4j.sh /root/autodl-tmp/neo4j-community-*.tar.gz
```

---

### 方法 3: 手动解压安装（Tarball）

如果安装脚本无法运行，您可以手动安装：

```bash
# 1. 安装 Java 17
apt-get update && apt-get install -y openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# 2. 进入目标目录
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current

# 3. 解压 Neo4j（--strip-components=1 会去掉顶层目录）
tar -xzf ~/neo4j-community-*.tar.gz --strip-components=1

# 4. 配置监听地址（如需外网访问）
sed -i 's/#dbms.connector.http.listen_address=0\.0\.0\.0:7474/dbms.connector.http.listen_address=0.0.0.0:7474/' conf/neo4j.conf
sed -i 's/#dbms.connector.bolt.listen_address=0\.0\.0\.0:7687/dbms.connector.bolt.listen_address=0.0.0.0:7687/' conf/neo4j.conf

# 5. 设置初始密码
./bin/neo4j-admin dbms set-initial-password pharmaKG2024!

# 6. 启动 Neo4j
bin/neo4j start

# 7. 检查状态
bin/neo4j status
```

---

## 安装后验证

### 检查 Neo4j 状态

```bash
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
./bin/neo4j status
```

预期输出应该显示 `Neo4j is running at pid <pid>`

### 测试 Python 连接

```bash
# 激活 conda 环境
conda activate pharmakg-api

# 测试连接
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'pharmaKG2024!'))
driver.verify_connectivity()
print('✓ Neo4j 连接成功!')
driver.close()
"
```

### 运行 ETL 测试脚本

```bash
# 激活 conda 环境
conda activate pharmakg-api

# 运行测试数据导入
python3 /root/autodl-tmp/pj-pharmaKG/scripts/run_etl_test.py --all -l 10 -v
```

---

## 访问 Neo4j

### 本地访问（在 AutoDL 内部）

- **Neo4j Browser**: http://localhost:7474
- **Bolt 协议**: bolt://localhost:7687
- **用户名**: neo4j
- **密码**: pharmaKG2024!

### 外网访问（需开放端口）

如果您需要从外部访问 Neo4j Browser：

1. 在 AutoDL 控制台开放端口 7474 和 7687
2. 使用以下地址访问：
   - **URL**: http://<your-autodl-ip>:7474
   - **Bolt**: bolt://<your-autodl-ip>:7687

---

## 常用命令

### Neo4j 服务管理

```bash
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current

# 设置 Java 环境（每次重启后需要）
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# 启动 Neo4j
./bin/neo4j start

# 停止 Neo4j
./bin/neo4j stop

# 重启 Neo4j
./bin/neo4j restart

# 查看状态
./bin/neo4j status

# 查看日志（实时）
tail -f /var/log/neo4j/neo4j.log

# 查看最近的日志
tail -100 /var/log/neo4j/neo4j.log
```

### 数据库操作

```bash
# 使用 Cypher Shell
./bin/cypher-shell

# 在 cypher-shell 中执行查询
:play start
MATCH (n) RETURN count(n);
EXIT;
```

### Python 快速测试

```python
from neo4j import GraphDatabase

# 连接到 Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "pharmaKG2024!")
)

# 执行查询
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) AS count")
    print(f"节点数: {result.single()['count']}")

driver.close()
```

---

## 故障排除

### 问题 1: Java 版本不兼容

**症状**: `Unsupported Java 11 detected. Please use Java(TM) 17 or Java(TM) 21`

**解决方案**:

```bash
# 安装 Java 17
apt-get update && apt-get install -y openjdk-17-jdk

# 设置环境变量
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# 验证
java -version  # 应该显示 17.x.x
```

### 问题 2: Neo4j 无法启动

**症状**: `bin/neo4j start` 显示启动失败

**解决方案**:

```bash
# 1. 确认 Java 环境
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
java -version

# 2. 查看详细日志
tail -100 /var/log/neo4j/neo4j.log

# 3. 检查端口占用
netstat -tlnp | grep -E '7474|7687'

# 4. 清理锁文件（如果之前异常关闭）
rm -rf /var/lib/neo4j/data/*

# 5. 重新启动
./bin/neo4j start
```

### 问题 3: 密码认证失败

**症状**: 无法使用 neo4j/pharmaKG2024! 登录

**解决方案**:

```bash
# 1. 停止 Neo4j
./bin/neo4j stop

# 2. 删除现有数据库
rm -rf /var/lib/neo4j/data/*

# 3. 重置密码
./bin/neo4j-admin dbms set-initial-password pharmaKG2024!

# 4. 启动 Neo4j
./bin/neo4j start
```

### 问题 4: RPM 安装后找不到配置文件

**症状**: `Missing xml file for /etc/neo4j/user-logs.xml`

**解决方案**:

```bash
# 创建必要的系统目录
mkdir -p /etc/neo4j /var/log/neo4j /var/lib/neo4j/{plugins,import,data}

# 复制日志配置
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
cp conf/user-logs.xml /etc/neo4j/
cp conf/server-logs.xml /etc/neo4j/

# 重启 Neo4j
./bin/neo4j restart
```

### 问题 5: ETL 测试连接失败

**症状**: ETL 测试脚本无法连接到 Neo4j

**解决方案**:

```bash
# 1. 确认 Neo4j 正在运行
./bin/neo4j status

# 2. 测试 Python 连接
conda activate pharmakg-api
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'pharmaKG2024!'))
driver.verify_connectivity()
print('连接成功!')
driver.close()
"

# 3. 检查 Bolt 端口
netstat -tlnp | grep 7687
```

---

## 环境要求

### 软件依赖

| 组件 | 最低版本 | 推荐版本 | 安装命令 |
|------|---------|----------|----------|
| Java | 17 | 17 或 21 | `apt-get install openjdk-17-jdk` |
| Python | 3.8 | 3.11 | conda 环境 `pharmakg-api` |
| Neo4j | 5.x | 5.26+ | RPM 或 tar.gz |

### 系统资源

| 资源 | 最低配置 | 推荐配置 |
|------|---------|----------|
| 内存 | 2GB | 4GB+ |
| 磁盘 | 1GB | 10GB+ |
| CPU | 1核 | 2核+ |

---

## 自动启动配置（可选）

如果您希望 Neo4j 在服务器重启后自动启动：

```bash
# 创建启动脚本
cat > /root/start_neo4j.sh << 'SCRIPT'
#!/bin/bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
./bin/neo4j start
SCRIPT

chmod +x /root/start_neo4j.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "@reboot /root/start_neo4j.sh") | crontab -
```

---

## 卸载 Neo4j

```bash
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current

# 1. 停止 Neo4j
./bin/neo4j stop

# 2. 清理数据（可选，慎用）
rm -rf /var/lib/neo4j/data/*

# 3. 删除安装目录
cd /root/autodl-tmp/pj-pharmaKG/neo4j
rm -rf current/*
```

---

## 已知限制

1. **网络下载限制**: AutoDL 环境无法直接从 neo4j.com 下载，需要手动上传
2. **镜像不可用**: ghproxy、mirror.ghproxy 等镜像服务目前不可用
3. **GitHub Releases**: Neo4j 5.x 不在 GitHub Releases 上托管

---

## 相关文档

- [Neo4j 官方文档](https://neo4j.com/docs/)
- [Cypher 查询语言](https://neo4j.com/docs/cypher-manual/)
- [项目 README](../README.md)
- [ETL 测试脚本](../scripts/run_etl_test.py)
- [Git 工作流指南](./GIT_WORKFLOW.md)
- [变更日志](../CHANGELOG.md)

---

**维护者**: PharmaKG Team
**最后更新**: 2026-02-07
