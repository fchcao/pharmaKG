# PharmaKG REST API

制药行业知识图谱 REST API 服务

## 概述

PharmaKG API 提供对制药行业知识图谱的访问，覆盖四个核心业务领域：
- **R&D 领域**: 化合物、靶点、实验数据
- **临床领域**: 临床试验、受试者、干预措施
- **供应链领域**: 制造商、药品短缺
- **监管领域**: 申报、批准、合规行动

## 快速开始

### 1. 安装依赖

```bash
cd /root/autodl-tmp/pj-pharmaKG/api
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（可选）：

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
APP_NAME=PharmaKG API
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API 端点总览

### 元数据端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/overview` | GET | 知识图谱总览 |

### R&D 领域端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/rd/compounds/count` | GET | 统计化合物数量 |
| `/rd/compounds/{compound_id}` | GET | 获取化合物详情 |
| `/rd/compounds/{compound_id}/targets` | GET | 获取化合物靶点 |
| `/rd/targets/{target_id}/compounds` | GET | 获取靶点化合物 |

### 临床领域端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/clinical/trials/count` | GET | 统计试验数量 |
| `/clinical/trials/{trial_id}` | GET | 获取试验详情 |
| `/clinical/trials/{trial_id}/subjects` | GET | 获取试验受试者 |
| `/clinical/trials/{trial_id}/adverse-events` | GET | 获取试验不良事件 |

### 供应链领域端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/sc/manufacturers/count` | GET | 统计制造商数量 |
| `/sc/manufacturers/{manufacturer_id}` | GET | 获取制造商详情 |
| `/sc/shortages/active` | GET | 获取活跃药品短缺 |
| `/sc/manufacturers/{manufacturer_id}/inspections` | GET | 获取制造商检查记录 |

### 监管领域端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/regulatory/submissions/count` | GET | 统计申报数量 |
| `/regulatory/submissions/{submission_id}` | GET | 获取申报详情 |
| `/regulatory/approvals/{approval_id}` | GET | 获取批准详情 |
| `/regulatory/inspections/{inspection_id}` | GET | 获取检查详情 |
| `/regulatory/compliance-actions` | GET | 获取合规行动 |
| `/regulatory/safety-signals` | GET | 获取安全性信号 |
| `/regulatory/agencies/{agency_id}/statistics` | GET | 获取监管机构统计 |

### 跨域查询端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/cross/drug/{drug_name}/trials` | GET | 获取药品相关试验 |
| `/cross/drug/{drug_name}/approvals` | GET | 获取药品相关批准 |
| `/cross/drug/{drug_name}/overview` | GET | 获取药品全景视图 |

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 健康检查
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 获取化合物详情
response = requests.get(f"{BASE_URL}/rd/compounds/CHEMBL123")
compound = response.json()
print(f"Compound: {compound['name']}")

# 获取化合物靶点
response = requests.get(f"{BASE_URL}/rd/compounds/CHEMBL123/targets")
targets = response.json()["targets"]
print(f"Targets: {len(targets)}")

# 获取试验详情
response = requests.get(f"{BASE_URL}/clinical/trials/NCT000001")
trial = response.json()
print(f"Trial: {trial['title']}")

# 获取活跃药品短缺
response = requests.get(f"{BASE_URL}/sc/shortages/active")
shortages = response.json()["shortages"]
print(f"Active shortages: {len(shortages)}")

# 获取药品全景视图
response = requests.get(f"{BASE_URL}/cross/drug/Aspirin/overview")
overview = response.json()
print(f"Trials: {len(overview['clinical_trials'])}")
print(f"Approvals: {len(overview['regulatory_approvals'])}")
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 获取知识图谱总览
curl http://localhost:8000/overview

# 获取化合物详情
curl http://localhost:8000/rd/compounds/CHEMBL123

# 获取化合物靶点
curl http://localhost:8000/rd/compounds/CHEMBL123/targets

# 获取试验详情
curl http://localhost:8000/clinical/trials/NCT000001

# 获取活跃药品短缺
curl http://localhost:8000/sc/shortages/active

# 获取合规行动（包含非活跃）
curl http://localhost:8000/regulatory/compliance-actions?active_only=false

# 获取安全性信号（按状态过滤）
curl http://localhost:8000/regulatory/safety-signals?status=under_review&limit=20
```

## 响应格式

### 成功响应

```json
{
  "primary_id": "CHEMBL123",
  "name": "Aspirin",
  "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "molecular_weight": 180.16
}
```

### 错误响应

```json
{
  "error": "Not Found",
  "message": "Compound CHEMBL123 not found",
  "timestamp": "HTTPException"
}
```

## 配置选项

在 `config.py` 中可配置以下选项：

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `NEO4J_URI` | bolt://localhost:7687 | Neo4j 连接URI |
| `NEO4J_USER` | neo4j | Neo4j 用户名 |
| `NEO4J_PASSWORD` | pharmaKG2024! | Neo4j 密码 |
| `APP_NAME` | PharmaKG API | 应用名称 |
| `APP_VERSION` | 1.0.0 | 应用版本 |
| `HOST` | 0.0.0.0 | 监听地址 |
| `PORT` | 8000 | 监听端口 |
| `DEBUG` | True | 调试模式 |
| `LOG_LEVEL` | INFO | 日志级别 |

## 性能优化

### 数据库索引

确保 Neo4j 中已创建以下索引：

```cypher
// R&D 领域
CREATE INDEX compound_id IF NOT EXISTS FOR (c:Compound) ON (c.primary_id);
CREATE INDEX target_id IF NOT EXISTS FOR (t:Target) ON (t.primary_id);

// 临床领域
CREATE INDEX trial_id IF NOT EXISTS FOR (t:ClinicalTrial) ON (t.trial_id);
CREATE INDEX subject_id IF NOT EXISTS FOR (s:Subject) ON (s.subject_id);

// 供应链领域
CREATE INDEX manufacturer_id IF NOT EXISTS FOR (m:Manufacturer) ON (m.manufacturer_id);
CREATE INDEX shortage_id IF NOT EXISTS FOR (ds:DrugShortage) ON (ds.shortage_id);

// 监管领域
CREATE INDEX submission_id IF NOT EXISTS FOR (sub:Submission) ON (sub.submission_id);
CREATE INDEX approval_id IF NOT EXISTS FOR (ap:Approval) ON (ap.approval_id);
```

### 连接池配置

在 `database.py` 中已实现连接池管理：

```python
# 默认连接池配置
MAX_CONNECTION_POOL_SIZE = 50
CONNECTION_ACQUISITION_TIMEOUT = 60
```

## 故障排查

### 连接失败

```
Error: Failed to connect to Neo4j
```

**解决方案**：
1. 确认 Neo4j 服务正在运行
2. 检查连接配置 (URI, 用户名, 密码)
3. 验证网络连接

### 查询超时

```
Error: Query execution timeout
```

**解决方案**：
1. 检查查询复杂度
2. 添加适当的索引
3. 使用分页减少返回数据量

### 内存不足

```
Error: Out of memory
```

**解决方案**：
1. 减少查询返回的数据量
2. 使用 SKIP/LIMIT 进行分页
3. 优化 Cypher 查询

## 开发指南

### 添加新端点

1. 在 `models.py` 中定义数据模型
2. 在 `services/` 中添加服务方法
3. 在 `main.py` 中注册路由

```python
# 1. 定义模型
class MyResponseModel(BaseModel):
    field1: str
    field2: int

# 2. 添加服务方法
class MyService:
    def get_data(self) -> dict:
        query = "MATCH (n) RETURN n LIMIT 1"
        result = self.db.execute_query(query)
        return result.records[0]

# 3. 注册路由
@app.get("/my-endpoint", response_model=MyResponseModel)
async def my_endpoint():
    service = MyService()
    data = service.get_data()
    return MyResponseModel(**data)
```

## 许可证

Copyright © 2025 PharmaKG Project

## 联系方式

- 项目主页: [GitHub](https://github.com/pharmakg)
- 文档: [Wiki](https://github.com/pharmakg/wiki)
