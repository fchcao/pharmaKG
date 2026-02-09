# PharmaKG 搜索服务文档 / Search Service Documentation

## 概述 / Overview

PharmaKG 搜索服务为知识图谱提供强大的全文搜索、模糊搜索和建议功能。该服务支持：

- **全文搜索** (Full-text Search): 使用 Neo4j 全文索引进行快速搜索
- **模糊搜索** (Fuzzy Search): 使用编辑距离算法进行模糊匹配
- **搜索建议** (Search Suggestions): 提供自动完成功能
- **聚合搜索** (Aggregate Search): 按维度分组统计搜索结果
- **多实体搜索** (Multi-entity Search): 在多个实体类型中同时搜索

## API 端点 / API Endpoints

### 1. 全文搜索 / Full-text Search

**端点 / Endpoint**: `POST /api/v1/search/fulltext`

**描述 / Description**: 使用 Neo4j 全文索引在知识图谱中搜索实体

**请求体 / Request Body**:
```json
{
  "query": "aspirin",
  "entity_types": ["Compound", "Target"],
  "limit": 20,
  "skip": 0
}
```

**参数说明 / Parameters**:
- `query` (string, 必需): 搜索查询文本
- `entity_types` (array[string], 可选): 实体类型过滤列表
- `limit` (integer, 可选): 返回结果数量限制 (默认: 20, 最大: 100)
- `skip` (integer, 可选): 跳过结果数量 (默认: 0)

**响应 / Response**:
```json
{
  "results": [
    {
      "entity_type": "Compound",
      "element_id": "4:abc123",
      "primary_id": "CHEMBL25",
      "name": "ASPIRIN",
      "score": 3.234,
      "index_name": "entity_fulltext"
    }
  ],
  "total": 15,
  "returned": 15,
  "query": "aspirin",
  "entity_types": ["Compound", "Target"],
  "skip": 0,
  "limit": 20
}
```

### 2. 模糊搜索 / Fuzzy Search

**端点 / Endpoint**: `POST /api/v1/search/fuzzy`

**描述 / Description**: 使用编辑距离算法进行模糊匹配，容忍拼写错误

**请求体 / Request Body**:
```json
{
  "query": "asprin",
  "entity_type": "Compound",
  "search_field": "name",
  "max_distance": 2,
  "limit": 20,
  "skip": 0
}
```

**参数说明 / Parameters**:
- `query` (string, 必需): 搜索查询文本
- `entity_type` (string, 必需): 实体类型
- `search_field` (string, 可选): 搜索字段 (默认: "name")
- `max_distance` (integer, 可选): 最大编辑距离 (默认: 2, 范围: 0-4)
- `limit` (integer, 可选): 返回结果数量限制 (默认: 20, 最大: 100)
- `skip` (integer, 可选): 跳过结果数量 (默认: 0)

**响应 / Response**:
```json
{
  "results": [
    {
      "entity_type": "Compound",
      "element_id": "4:abc123",
      "primary_id": "CHEMBL25",
      "name": "ASPIRIN",
      "distance": 1,
      "similarity": 0.8889,
      "method": "APOC_LEVENSHTEIN"
    }
  ],
  "total": 10,
  "returned": 10,
  "query": "asprin",
  "entity_type": "Compound",
  "search_field": "name",
  "max_distance": 2,
  "skip": 0,
  "limit": 20,
  "method": "APOC_LEVENSHTEIN"
}
```

### 3. 搜索建议 / Search Suggestions

**端点 / Endpoint**: `GET /api/v1/search/suggestions`

**描述 / Description**: 获取搜索建议，用于自动完成功能

**查询参数 / Query Parameters**:
- `prefix` (string, 必需): 搜索前缀
- `entity_type` (string, 必需): 实体类型
- `search_field` (string, 可选): 搜索字段 (默认: "name")
- `limit` (integer, 可选): 返回建议数量 (默认: 10, 最大: 50)

**响应 / Response**:
```json
{
  "suggestions": [
    {
      "text": "ASPIRIN",
      "frequency": 5
    },
    {
      "text": "ASPARTIC ACID",
      "frequency": 3
    }
  ],
  "total": 2,
  "prefix": "asp",
  "entity_type": "Compound",
  "search_field": "name"
}
```

### 4. 聚合搜索 / Aggregate Search

**端点 / Endpoint**: `POST /api/v1/search/aggregate`

**描述 / Description**: 按指定维度分组统计搜索结果

**请求体 / Request Body**:
```json
{
  "query": "cancer",
  "group_by": "entity_type",
  "limit": 100
}
```

**参数说明 / Parameters**:
- `query` (string, 必需): 搜索查询文本
- `group_by` (string, 可选): 分组维度 - "entity_type" 或 "domain" (默认: "entity_type")
- `limit` (integer, 可选): 每组最大结果数 (默认: 100, 最大: 200)

**响应 / Response**:
```json
{
  "groups": [
    {
      "entity_type": "Compound",
      "count": 50,
      "entity_types": null,
      "results": [...]
    },
    {
      "entity_type": "ClinicalTrial",
      "count": 30,
      "entity_types": null,
      "results": [...]
    }
  ],
  "total_groups": 4,
  "total_results": 150,
  "query": "cancer",
  "group_by": "entity_type"
}
```

### 5. 多实体搜索 / Multi-entity Search

**端点 / Endpoint**: `POST /api/v1/search/multi-entity`

**描述 / Description**: 在多个实体类型中同时搜索

**请求体 / Request Body**:
```json
{
  "query": "kinase",
  "entities": [
    {
      "entity_type": "Compound",
      "search_field": "name"
    },
    {
      "entity_type": "Target",
      "search_field": "name"
    }
  ],
  "limit_per_entity": 10
}
```

**参数说明 / Parameters**:
- `query` (string, 必需): 搜索查询文本
- `entities` (array, 必需): 实体配置列表
  - `entity_type` (string, 必需): 实体类型
  - `search_field` (string, 可选): 搜索字段 (默认: "name")
- `limit_per_entity` (integer, 可选): 每个实体类型的结果限制 (默认: 10, 最大: 50)

**响应 / Response**:
```json
{
  "results": {
    "Compound": {
      "entity_type": "Compound",
      "search_field": "name",
      "count": 10,
      "results": [...]
    },
    "Target": {
      "entity_type": "Target",
      "search_field": "name",
      "count": 8,
      "results": [...]
    }
  },
  "total_entities": 2,
  "total_results": 18,
  "query": "kinase"
}
```

### 6. 创建搜索索引 / Create Search Indexes

**端点 / Endpoint**: `POST /api/v1/search/indexes/create`

**描述 / Description**: 创建全文搜索索引（管理员端点）

**响应 / Response**:
```json
{
  "success": true,
  "indexes_created": [
    "entity_fulltext",
    "target_fulltext",
    "pathway_fulltext"
  ],
  "errors": []
}
```

### 7. 列出搜索索引 / List Search Indexes

**端点 / Endpoint**: `GET /api/v1/search/indexes`

**描述 / Description**: 列出所有全文搜索索引

**响应 / Response**:
```json
{
  "indexes": [
    {
      "name": "entity_fulltext",
      "labelsOrTypes": ["Compound"],
      "properties": ["name", "primary_id", "smiles"]
    }
  ],
  "total": 6
}
```

## 支持的实体类型 / Supported Entity Types

搜索服务支持以下实体类型：

### R&D 领域 / R&D Domain
- `Compound`: 化合物
- `Target`: 靶点
- `Pathway`: 通路
- `Assay`: 实验

### 临床领域 / Clinical Domain
- `ClinicalTrial`: 临床试验
- `Subject`: 受试者
- `AdverseEvent`: 不良事件
- `Intervention`: 干预措施

### 供应链领域 / Supply Chain Domain
- `Manufacturer`: 制造商
- `DrugShortage`: 药品短缺
- `DrugProduct`: 药品产品
- `Facility`: 设施

### 监管领域 / Regulatory Domain
- `Submission`: 申报
- `Approval`: 批准
- `Inspection`: 检查
- `ComplianceAction`: 合规行动

## 性能优化 / Performance Optimization

### 目标性能指标 / Target Performance Metrics
- 全文搜索响应时间: < 500ms
- 模糊搜索响应时间: < 1000ms
- 搜索建议响应时间: < 200ms
- 聚合搜索响应时间: < 1500ms

### 优化策略 / Optimization Strategies
1. **索引优化**: 使用 Neo4j 全文索引加速搜索
2. **分页支持**: 所有限制结果数量的端点都支持分页
3. **缓存策略**: 考虑对热门搜索查询进行缓存
4. **异步处理**: 对于大规模搜索，考虑使用异步处理

## 错误处理 / Error Handling

所有搜索端点都遵循统一的错误响应格式：

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "detail": "Additional error details",
  "timestamp": "2025-02-08T10:30:00"
}
```

常见错误情况：
- `400 Bad Request`: 无效的查询参数
- `404 Not Found`: 指定的实体类型不存在
- `500 Internal Server Error`: 搜索服务内部错误

## 使用示例 / Usage Examples

### Python 客户端示例

```python
import requests

# API 基础 URL
BASE_URL = "http://localhost:8000"

# 全文搜索
response = requests.post(
    f"{BASE_URL}/api/v1/search/fulltext",
    json={
        "query": "aspirin",
        "entity_types": ["Compound"],
        "limit": 10
    }
)
results = response.json()

# 模糊搜索
response = requests.post(
    f"{BASE_URL}/api/v1/search/fuzzy",
    json={
        "query": "asprin",
        "entity_type": "Compound",
        "max_distance": 2,
        "limit": 10
    }
)
results = response.json()

# 搜索建议
response = requests.get(
    f"{BASE_URL}/api/v1/search/suggestions",
    params={
        "prefix": "asp",
        "entity_type": "Compound",
        "limit": 10
    }
)
suggestions = response.json()
```

### JavaScript 客户端示例

```javascript
// API 基础 URL
const BASE_URL = 'http://localhost:8000';

// 全文搜索
const response = await fetch(`${BASE_URL}/api/v1/search/fulltext`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'aspirin',
    entity_types: ['Compound'],
    limit: 10
  })
});
const results = await response.json();

// 搜索建议
const suggestions = await fetch(
  `${BASE_URL}/api/v1/search/suggestions?prefix=asp&entity_type=Compound&limit=10`
);
const suggestionsData = await suggestions.json();
```

## 配置和部署 / Configuration and Deployment

### 环境变量 / Environment Variables
在 `api/.env` 文件中配置：

```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pharmaKG2024!

# API 配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 索引初始化 / Index Initialization
全文搜索索引会在以下情况自动创建：
1. API 启动时（自动尝试创建）
2. 手动调用 `/api/v1/search/indexes/create` 端点

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

1. **索引未创建**
   - 症状: 全文搜索返回 "No fulltext indexes available"
   - 解决: 调用 `/api/v1/search/indexes/create` 创建索引

2. **模糊搜索失败**
   - 症状: 模糊搜索返回 "APOC library not available"
   - 解决: 安装 Neo4j APOC 插件

3. **搜索速度慢**
   - 症状: 搜索响应时间 > 2秒
   - 解决:
     - 检查索引是否正确创建
     - 减少返回结果数量
     - 考虑添加更多过滤条件

## 更新日志 / Changelog

### v1.0 (2025-02-08)
- 初始版本发布
- 实现全文搜索功能
- 实现模糊搜索功能
- 实现搜索建议功能
- 实现聚合搜索功能
- 实现多实体搜索功能
- 添加索引管理端点
