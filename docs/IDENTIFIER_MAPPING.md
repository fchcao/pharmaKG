# 制药行业知识图谱 - 主实体映射系统文档
# Pharmaceutical Knowledge Graph - Master Entity Mapping System Documentation

版本 / Version: v1.0
日期 / Date: 2025-02-08

---

## 目录 / Table of Contents

1. [概述 / Overview](#概述--overview)
2. [标识符系统 / Identifier Systems](#标识符系统--identifier-systems)
3. [架构设计 / Architecture Design](#架构设计--architecture-design)
4. [使用指南 / Usage Guide](#使用指南--usage-guide)
5. [外部API集成 / External API Integration](#外部api集成--external-api-integration)
6. [数据模型 / Data Model](#数据模型--data-model)
7. [Neo4j集成 / Neo4j Integration](#neo4j集成--neo4j-integration)
8. [性能优化 / Performance Optimization](#性能优化--performance-optimization)
9. [故障排查 / Troubleshooting](#故障排查--troubleshooting)

---

## 概述 / Overview

### 功能 / Purpose

主实体映射系统（Master Entity Mapping System）创建跨所有数据源的统一实体视图，通过链接不同的标识符系统来解决同一实体在不同数据源中使用不同标识符的问题。

The Master Entity Mapping System creates a unified entity view across all data sources by linking different identifier systems to solve the problem where the same entity uses different identifiers in different data sources.

### 核心功能 / Core Features

- **多标识符支持**：支持化合物、靶标、疾病、临床试验、公司等5大类实体的多种标识符
- **外部API集成**：集成UniProt、MyChem.info、MyDisease.info等外部映射服务
- **智能映射**：基于主标识符和哈希值的智能映射策略
- **增量更新**：支持增量更新模式，避免重复处理
- **缓存机制**：内置缓存机制，减少API调用次数
- **Neo4j集成**：生成MERGE_TO关系，在Neo4j中连接同一实体的不同表示

### 输入输出 / Input/Output

**输入 / Input:**
- 处理后的JSON文件（`data/processed/entities/`目录）
- 各数据源提取的实体数据

**输出 / Output:**
- `master_entity_map.db` - SQLite映射数据库
- `neo4j_merge_queries.cypher` - Neo4j合并查询
- `mapping_summary.json` - 映射统计报告

---

## 标识符系统 / Identifier Systems

### 1. 化合物标识符 / Compound Identifiers

**主标识符 / Primary Identifier:**
- **InChIKey** - 国际化学标识符哈希键（IUPAC International Chemical Identifier Key）

**次标识符 / Secondary Identifiers:**
| 标识符 | 来源 | 描述 |
|--------|------|------|
| ChEMBL ID | ChEMBL | EMBL-EBI生物活性数据库 |
| DrugBank ID | DrugBank | 综合药物数据库 |
| PubChem CID | PubChem | NCBI化合物数据库 |
| UNII | FDA | 唯一成分标识符 |
| CAS Number | CAS | 化学文摘社登记号 |
| SMILES | 化学信息学 | 简化分子线性输入规范 |

**名称匹配 / Name Matching:**
- 通用名（Generic Name）
- 品牌名（Brand Name）
- 优选名（Preferred Name）

### 2. 靶标/蛋白质标识符 / Target/Protein Identifiers

**主标识符 / Primary Identifier:**
- **UniProt Accession** - 例如：P12345

**次标识符 / Secondary Identifiers:**
| 标识符 | 来源 | 描述 |
|--------|------|------|
| Entrez ID | NCBI Gene | 基因数据库 |
| Ensembl ID | Ensembl | 基因组数据库 |
| HGNC Symbol | HGNC | 基因命名委员会 |
| RefSeq ID | NCBI | 参考序列 |

**名称匹配 / Name Matching:**
- 基因符号（Gene Symbol）
- 蛋白质名称（Protein Name）

### 3. 疾病标识符 / Disease Identifiers

**主标识符 / Primary Identifier:**
- **MONDO ID** - Monarch疾病本体论（例如：MONDO:0002020）

**次标识符 / Secondary Identifiers:**
| 标识符 | 来源 | 描述 |
|--------|------|------|
| ICD-10 | WHO | 国际疾病分类 |
| DOID | Disease Ontology | 疾病本体论 |
| MeSH | NLM | 医学主题词表 |
| OMIM | Johns Hopkins | 在线孟德尔遗传 |
| SNOMED-CT | SNOMED | 系统化医学临床术语集 |

**名称匹配 / Name Matching:**
- 疾病名称（Disease Name）
- 病症名称（Condition Name）

### 4. 临床试验标识符 / ClinicalTrial Identifiers

**主标识符 / Primary Identifier:**
- **NCT Number** - ClinicalTrials.gov标识符

**次标识符 / Secondary Identifiers:**
| 标识符 | 来源 | 地区 |
|--------|------|------|
| EudraCT | EMA | 欧盟 |
| ChiCTR | ChiCTR | 中国 |
| JMACT | JMACCT | 日本 |
| KCT | CRIS | 韩国 |

### 5. 公司/组织标识符 / Company/Organization Identifiers

**主标识符 / Primary Identifier:**
- **GRID ID** - 全球研究标识符数据库

**次标识符 / Secondary Identifiers:**
| 标识符 | 来源 | 描述 |
|--------|------|------|
| ROR ID | ROR | 研究组织注册表 |
| DUNS | Dun & Bradstreet | 数据通用编号系统 |
| LEI | GLEIF | 法律实体标识符 |

---

## 架构设计 / Architecture Design

### 系统组件 / System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Entity Mapper                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Extractor   │  │  Mapper      │  │  Generator   │      │
│  │              │  │              │  │              │      │
│  │  - Scan      │  │  - Primary   │  │  - SQLite    │      │
│  │    Files     │  │    ID        │  │    Queries   │      │
│  │  - Parse     │  │  - External  │  │  - Neo4j     │      │
│  │    JSON      │  │    APIs      │  │    Cypher    │      │
│  │  - Categorize│  │  - Cache     │  │  - Summary   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              External API Services                  │    │
│  │  - UniProt ID Mapping                               │    │
│  │  - MyChem.info (Compound cross-references)          │    │
│  │  - MyDisease.info (Disease cross-references)        │    │
│  │  - Identifiers.org (Standard resolution)            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 处理流程 / Processing Flow

1. **提取阶段 / Extraction Phase**
   - 扫描`data/processed/entities/`目录
   - 读取所有JSON文件
   - 解析实体数据
   - 分类实体类型

2. **映射阶段 / Mapping Phase**
   - 确定主标识符
   - 查询外部API获取缺失标识符
   - 生成规范ID（Canonical ID）
   - 存储到SQLite数据库

3. **生成阶段 / Generation Phase**
   - 生成Neo4j MERGE_TO关系查询
   - 生成映射统计报告
   - 计算覆盖率指标

---

## 使用指南 / Usage Guide

### 基本用法 / Basic Usage

```bash
# 激活conda环境
conda activate pharmakg-api

# 运行主实体映射
python3 -m tools.build_master_entity_map \
    --data-dir /root/autodl-tmp/pj-pharmaKG/data/processed \
    --output-dir /root/autodl-tmp/pj-pharmaKG/data/validated \
    --batch-size 100
```

### 命令行参数 / Command Line Arguments

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data-dir` | 处理后的数据目录 | `data/processed` |
| `--output-dir` | 输出目录 | `data/validated` |
| `--cache-dir` | 缓存目录 | `{output_dir}/cache` |
| `--batch-size` | 批处理大小 | 100 |
| `--incremental` | 增量更新模式 | False |

### 增量更新模式 / Incremental Update Mode

```bash
# 仅处理新文件或已修改的文件
python3 -m tools.build_master_entity_map --incremental
```

增量模式会：
- 跳过已处理的文件
- 仅更新新实体或已修改的实体
- 保留现有的映射关系

---

## 外部API集成 / External API Integration

### UniProt ID Mapping API

**端点 / Endpoint:** `https://rest.uniprot.org/idmapping/run`

**用途 / Purpose:** 蛋白质标识符交叉引用

**示例 / Example:**
```python
# 从Entrez ID映射到UniProt
POST https://rest.uniprot.org/idmapping/run
{
    "from": "NCBI GeneID",
    "to": "UniProtKB",
    "ids": "672"
}

# 响应 / Response
{
    "jobId": "job-id-123"
}

# 获取结果 / Get results
GET https://rest.uniprot.org/idmapping/status/job-id-123
```

**支持的方向 / Supported Mappings:**
- NCBI GeneID → UniProtKB
- Ensembl → UniProtKB
- HGNC Symbol → UniProtKB
- RefSeq → UniProtKB

### MyChem.info API

**端点 / Endpoint:** `https://mychem.info/v1/chembl/{chembl_id}`

**用途 / Purpose:** 化合物交叉引用

**返回的标识符 / Returned Identifiers:**
- InChIKey
- PubChem CID
- UNII
- DrugBank ID
- CAS Number

### MyDisease.info API

**端点 / Endpoint:** `https://mydisease.info/v1/query`

**用途 / Purpose:** 疾病交叉引用

**参数 / Parameters:**
```python
GET https://mydisease.info/v1/query?q=cancer&fields=mondo,doid,icd10,mesh,omim
```

**返回的标识符 / Returned Identifiers:**
- MONDO ID
- DOID
- ICD-10
- MeSH
- OMIM

---

## 数据模型 / Data Model

### SQLite数据库模式 / SQLite Database Schema

#### compound_mapping表

```sql
CREATE TABLE compound_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inchikey TEXT,
    chembl_id TEXT,
    drugbank_id TEXT,
    pubchem_cid TEXT,
    unii TEXT,
    cas TEXT,
    smiles TEXT,
    pref_name TEXT,
    generic_name TEXT,
    brand_name TEXT,
    canonical_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(inchikey, chembl_id, drugbank_id)
);
```

#### target_mapping表

```sql
CREATE TABLE target_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uniprot_id TEXT,
    entrez_id TEXT,
    ensembl_id TEXT,
    hgnc_symbol TEXT,
    refseq_id TEXT,
    gene_symbol TEXT,
    protein_name TEXT,
    canonical_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uniprot_id, entrez_id, ensembl_id)
);
```

#### disease_mapping表

```sql
CREATE TABLE disease_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mondo_id TEXT,
    icd10 TEXT,
    doid TEXT,
    mesh TEXT,
    omim TEXT,
    snomed_ct TEXT,
    disease_name TEXT,
    condition_name TEXT,
    canonical_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mondo_id, icd10, doid)
);
```

#### trial_mapping表

```sql
CREATE TABLE trial_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT,
    eudract TEXT,
    chict TEXT,
    jma_ct TEXT,
    kct TEXT,
    trial_name TEXT,
    canonical_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nct_id, eudract, chict)
);
```

#### company_mapping表

```sql
CREATE TABLE company_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grid_id TEXT,
    ror_id TEXT,
    duns TEXT,
    lei TEXT,
    company_name TEXT,
    organization_name TEXT,
    canonical_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(grid_id, ror_id, duns)
);
```

---

## Neo4j集成 / Neo4j Integration

### MERGE_TO关系

**目的 / Purpose:** 将同一实体的不同标识符表示连接到一个规范实体

**关系属性 / Relationship Properties:**
```cypher
{
    source: "master_mapping",
    confidence: 1.0,
    evidence_level: "A",
    merged_at: datetime()
}
```

### 示例查询 / Example Queries

**创建合并关系 / Create Merge Relationship:**
```cypher
// 合并化合物的不同标识符
MATCH (c:Compound {chembl_id: 'CHEMBL25'})
WHERE NOT c:Canonical
MATCH (canonical:Compound:Canonical {id: 'COMPOND:ABCDEFGHIJKLMNOP'})
MERGE (c)-[:MERGED_TO {
    source: 'master_mapping',
    confidence: 1.0,
    evidence_level: 'A',
    merged_at: datetime()
}]->(canonical);
```

**查询规范实体 / Query Canonical Entity:**
```cypher
// 获取化合物的所有标识符
MATCH (canonical:Compound:Canonical {id: 'COMPOUND:ABCDEFGHIJKLMNOP'})
<-[r:MERGED_TO]-(variant:Compound)
RETURN canonical, variant, r
```

---

## 性能优化 / Performance Optimization

### 缓存策略 / Caching Strategy

1. **文件系统缓存 / File System Cache**
   - API响应缓存为JSON文件
   - 基于键的缓存检索
   - 自动缓存过期时间（建议30天）

2. **内存缓存 / Memory Cache**
   - 批处理操作
   - 减少数据库往返

### 批处理 / Batch Processing

- 默认批处理大小：100条记录
- 可通过`--batch-size`参数调整
- 建议值：
  - 小型数据集（<10K）：50-100
  - 中型数据集（10K-100K）：100-200
  - 大型数据集（>100K）：200-500

### API速率限制 / API Rate Limiting

- 内置重试机制（最多3次）
- 指数退避策略
- 建议生产环境使用API密钥

---

## 故障排查 / Troubleshooting

### 常见问题 / Common Issues

#### 1. 数据库锁定错误 / Database Lock Error

**症状 / Symptom:**
```
sqlite3.OperationalError: database is locked
```

**解决方案 / Solution:**
- 确保没有其他进程访问数据库
- 使用WAL模式（Write-Ahead Logging）
- 减小批处理大小

#### 2. API超时 / API Timeout

**症状 / Symptom:**
```
requests.exceptions.Timeout: HTTPConnectionPool
```

**解决方案 / Solution:**
- 检查网络连接
- 增加超时时间
- 启用缓存减少API调用

#### 3. 内存不足 / Out of Memory

**症状 / Symptom:**
```
MemoryError: Unable to allocate array
```

**解决方案 / Solution:**
- 减小批处理大小
- 使用增量模式
- 分批处理大型文件

### 日志和调试 / Logging and Debugging

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看统计信息：
```bash
# 查看映射摘要
cat data/validated/mapping_summary.json | jq '.statistics'
```

---

## 附录 / Appendix

### A. 标识符优先级矩阵 / Identifier Priority Matrix

| 实体类型 | 主标识符 | 备选1 | 备选2 | 备选3 |
|----------|----------|-------|-------|-------|
| Compound | InChIKey | ChEMBL ID | DrugBank ID | Hash |
| Target | UniProt | Entrez ID | Ensembl ID | Hash |
| Disease | MONDO | DOID | ICD-10 | Hash |
| Trial | NCT | EudraCT | ChiCTR | Hash |
| Company | GRID | ROR | DUNS | Hash |

### B. API调用统计 / API Call Statistics

```bash
# 查看API调用统计
cat data/validated/mapping_summary.json | jq '.statistics.api_calls'
# 查看缓存命中率
cat data/validated/mapping_summary.json | jq '.statistics.cache_hits'
```

### C. 覆盖率报告 / Coverage Report

```bash
# 查看各标识符覆盖率
cat data/validated/mapping_summary.json | jq '.coverage'
```

---

## 参考资料 / References

1. **UniProt ID Mapping**: https://www.uniprot.org/help/id_mapping
2. **MyChem.info**: https://mychem.info/
3. **MyDisease.info**: https://mydisease.info/
4. **Identifiers.org**: https://identifiers.org/
5. **InChI Trust**: https://www.inchi-trust.org/
6. **MONDO Initiative**: https://mondo.monarchinitiative.org/

---

**文档版本 / Document Version:** v1.0
**最后更新 / Last Updated:** 2025-02-08
**维护者 / Maintainer:** PharmaKG Development Team
