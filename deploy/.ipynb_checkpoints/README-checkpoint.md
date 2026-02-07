# 制药行业知识图谱 - 快速开始指南

**项目版本**: v1.0
**最后更新**: 2025-02-06
**部署环境**: autodl 云服务器

---

## 系统要求

### 硬件要求

| 资源类型 | 最低配置 | 推荐配置 |
|---------|---------|---------|
| CPU | 4核 | 8核+ |
| 内存 | 16GB | 32GB+ |
| 存储 | 200GB SSD | 500GB SSD |
| 网络 | 10Mbps | 100Mbps |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.8+ (用于脚本和工具)

---

## 快速部署

### 1. 准备工作

```bash
# 克隆项目（如果需要）
cd /root/autodl-tmp/pj-pharmaKG

# 进入部署目录
cd deploy

# 查看部署脚本
cat deploy.sh
```

### 2. 一键部署

```bash
# 执行部署脚本
chmod +x deploy.sh
./deploy.sh
```

部署脚本会自动完成以下步骤：
- 环境检查（Docker、端口占用）
- 目录初始化
- Docker Compose 服务启动
- Neo4j 启动验证
- 基础约束和索引创建

### 3. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 应该看到以下服务都在运行:
# - pharma-kg-neo4j    (Up)
# - pharma-kg-postgres (Up)
# - pharma-kg-redis    (Up)
```

### 4. 访问 Neo4j 浏览器

- **URL**: http://your-server-ip:7474
- **用户名**: neo4j
- **密码**: pharmaKG2024!

### 5. 连接 Neo4j

**使用 Bolt 协议**:
```
URL: bolt://your-server-ip:7687
用户名: neo4j
密码: pharmaKG2024!
```

**使用 Cypher Shell**:
```bash
# 连接到 Neo4j
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!

# 测试查询
MATCH (n) RETURN count(n);
```

---

## 常用操作

### 查看服务状态

```bash
cd /root/autodl-tmp/pj-pharmaKG/deploy

# 查看所有容器
docker-compose ps

# 查看 Neo4j 日志
docker-compose logs -f neo4j

# 查看服务健康状态
docker-compose ps
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止但保留数据
docker-compose stop
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart neo4j
```

### 更新服务

```bash
# 拉取最新镜像
docker-compose pull

# 重新创建容器
docker-compose up -d --force-recreate
```

### 数据备份

```bash
# 备份 Neo4j 数据
docker exec pharma-kg-neo4j neo4j-admin backup --backup-dir=/backups --from=/data --name=graph.db-backup

# 备份到宿主机
docker cp pharma-kg-neo4j:/backups /root/autodl-tmp/pj-pharmaKG/backups
```

---

## 数据导入

### 1. 准备数据文件

将数据文件放到 `data/import/` 目录：

```bash
mkdir -p data/import
cp your-data.csv data/import/
```

### 2. 使用 Cypher 导入

```bash
# 连接到 Neo4j
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!

# 导入 CSV 数据
LOAD CSV WITH HEADERS FROM 'file:///data/import/compounds.csv' AS row
CREATE (c:Compound {
    primary_id: row.id,
    name: row.name,
    smiles: row.smiles,
    inchikey: row.inchikey
})
SET c.created_at = datetime();
```

### 3. 批量导入脚本

使用提供的批量导入脚本：

```bash
# 导入 R&D 数据
python scripts/import_rd_data.py

# 导入临床数据
python scripts/import_clinical_data.py

# 导入供应链数据
python scripts/import_supply_chain_data.py

# 导入监管数据
python scripts/import_regulatory_data.py
```

---

## 开发指南

### 1. 查询示例

**基础查询**:
```cypher
// 查询所有化合物
MATCH (c:Compound)
RETURN c LIMIT 10;

// 查询化合物-靶点关系
MATCH (c:Compound)-[r:inhibits]->(t:Target)
WHERE c.development_stage = 'PCC'
RETURN c.name, t.name, r.activity_value
ORDER BY r.activity_value ASC
LIMIT 20;
```

**复杂查询**:
```cypher
// 跨域查询: R&D靶点 → 临床验证 → 监管安全性信号
MATCH (t:Target)-[:validated_in]->(ct:ClinicalTrial)
MATCH (t)-[:has_safety_signal]->(se:SafetyEvent)
WHERE t.target_id = 'EGFR'
  AND se.causality_category IN ['Related', 'PossiblyRelated']
RETURN t.name, ct.protocol_id, se.event_type, se.event_date
ORDER BY se.event_date DESC;
```

### 2. API 使用

**查询 API 端点**:

```
GET /api/v1/compounds
GET /api/v1/compounds/{id}
GET /api/v1/targets
GET /api/v1/trials
GET /api/v1/subjects
GET /api/v1/suppliers
GET /api/v1/submissions

GET /api/v1/query/cypher
POST /api/v1/query/cross-domain
```

**API 示例**:
```bash
# 查询化合物
curl http://localhost:8080/api/v1/compounds?stage=PCC&limit=10

# 执行 Cypher 查询
curl -X POST http://localhost:8080/api/v1/query/cypher \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (c:Compound) RETURN count(c)"}'
```

### 3. 本体建模

**添加新实体类型**:

```turtle
# 创建新的实体类（在 ontologies/pharma-kg.ttl 中）
:NewEntity a owl:Class ;
    rdfs:label "NewEntity" ;
    rdfs:comment "实体描述" ;
    rdfs:subClassOf :ResearchEntity .

# 添加属性
:NewEntity
    :has_primary_id xsd:string ;
    :has_name xsd:string ;
    :created_at xsd:dateTime .
```

**添加新关系类型**:

```turtle
# 创建新的关系类型
:related_to a owl:ObjectProperty ;
    rdfs:domain :NewEntity ;
    rdfs:range :Target ;
    rdfs:label "related to" .
```

---

## 故障排除

### 问题1: Neo4j 无法启动

**症状**: 容器反复重启

**解决方案**:
```bash
# 检查日志
docker-compose logs neo4j

# 检查内存使用
docker stats pharma-kg-neo4j

# 如果内存不足，调整 neo4j.conf 中的内存设置
```

### 问题2: 端口被占用

**症状**: 启动失败，端口已被占用

**解决方案**:
```bash
# 查看端口占用
lsof -i :7474
lsof -i :7687

# 停止占用端口的服务
sudo systemctl stop <service-name>

# 或者修改 docker-compose.yml 中的端口映射
```

### 问题3: 数据导入失败

**症状**: CSV 导入报错

**解决方案**:
```bash
# 确保数据文件正确挂载
docker exec pharma-kg-neo4j ls -la /var/lib/neo4j/import

# 检查 CSV 文件格式
head -n 5 data/import/your-file.csv

# 使用 LOAD CSV 的正确路径
LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/your-file.csv' AS row
```

### 问题4: 查询性能慢

**症状**: 查询响应时间超过 10 秒

**解决方案**:
```bash
# 检查索引是否创建
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!
> SHOW INDEXES;

# 分析查询执行计划
EXPLAIN MATCH (c:Compound)-[:inhibits]->(t:Target) RETURN c,t;

# 使用 PROFILE 查看实际执行计划
PROFILE MATCH (c:Compound)-[:inhibits]->(t:Target) RETURN c,t;
```

---

## 监控和维护

### 系统监控

```bash
# 容器资源使用
docker stats

# Neo4j 数据库大小
du -sh data/neo4j/

# 磁盘使用
df -h
```

### 日志查看

```bash
# Neo4j 日志
tail -f data/neo4j/logs/neo4j.log

# 查询日志
tail -f data/neo4j/logs/query.log

# 调试日志
tail -f data/neo4j/logs/debug.log
```

### 定期维护

**每周**:
- 检查磁盘使用情况
- 检查日志文件大小
- 备份数据库

**每月**:
- 分析查询性能
- 清理不必要的日志
- 更新索引统计

**每季度**:
- 全量备份验证
- 安全审计
- 性能优化评估

---

## 安全注意事项

### 1. 修改默认密码

```bash
# 首次登录后，请立即修改密码
# 在 Neo4j 浏览器中执行:
CALL dbms.security.changePassword('neo4j', 'new_password');

# 或修改 docker-compose.yml 后重启
```

### 2. 防火墙配置

```bash
# 仅允许本地访问 Neo4j 浏览器
# 修改 docker-compose.yml:
# dbms.connector.http.listen_address=127.0.0.1:7474

# 使用 UFW 配置防火墙
sudo ufw allow from 10.0.0.0/8 to any port 7687
```

### 3. SSL/TLS 配置

生产环境建议启用 HTTPS 和 Bolt TLS：

```yaml
# 在 docker-compose.yml 中添加:
- NEO4J_dbms_connector_https_enabled=true
- NEO4J_dbms_ssl_policy_bolt_enabled=true
```

---

## 下一步

1. **导入数据**: 参考数据导入文档，开始导入实际数据
2. **开发查询**: 参考查询示例文档，开发业务查询
3. **API 集成**: 参考API文档，集成到业务系统
4. **监控部署**: 配置监控告警，确保系统稳定

---

## 相关文档

- [Schema设计文档](../docs/schema/制药行业知识图谱Schema设计文档.md)
- [实施路线图](../docs/schema/实施路线图.md)
- [API文档](../docs/api/API文档.md) (待创建)
- [查询示例](../docs/query/查询示例.md) (待创建)

---

**文档版本**: v1.0
**最后更新**: 2025-02-06

---

*如有问题，请查看故障排除章节或联系技术支持*
