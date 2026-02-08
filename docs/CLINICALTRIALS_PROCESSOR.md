# ClinicalTrials.gov API v2 处理器文档
# ClinicalTrials.gov API v2 Processor Documentation

**版本 / Version:** v1.0
**最后更新 / Last Updated:** 2026-02-08

---

## 目录 / Table of Contents

- [概述 / Overview](#概述--overview)
- [功能特性 / Features](#功能特性--features)
- [API 端点 / API Endpoints](#api-端点--api-endpoints)
- [实体模型 / Entity Models](#实体模型--entity-models)
- [关系模型 / Relationship Models](#关系模型--relationship-models)
- [安装配置 / Installation and Configuration](#安装配置--installation-and-configuration)
- [使用方法 / Usage](#使用方法--usage)
- [命令行接口 / CLI Reference](#命令行接口--cli-reference)
- [代码示例 / Code Examples](#代码示例--code-examples)
- [性能优化 / Performance Optimization](#性能优化--performance-optimization)
- [故障排除 / Troubleshooting](#故障排除--troubleshooting)

---

## 概述 / Overview

**ClinicalTrialsProcessor** 是 PharmaKG 项目中用于从 ClinicalTrials.gov API v2 提取临床试验数据的处理器。它支持全量下载、条件查询、增量更新等多种模式，并能够将临床试验数据转换为知识图谱格式。

The **ClinicalTrialsProcessor** is a data processor in the PharmaKG project that extracts clinical trial data from the ClinicalTrials.gov API v2. It supports multiple modes including full download, conditional queries, and incremental updates, and can transform clinical trial data into knowledge graph format.

### 主要功能 / Key Features

- ✅ **全量下载 / Full Download**: 下载所有 400K+ 临床试验数据
- ✅ **条件查询 / Query by Conditions**: 按疾病、阶段、状态等条件查询
- ✅ **增量更新 / Incremental Updates**: 只获取更新的数据
- ✅ **速率限制 / Rate Limiting**: 遵守 API 的速率限制（2 请求/秒）
- ✅ **自动重试 / Auto Retry**: 自动重试失败的请求
- ✅ **断点续传 / Resume Capability**: 支持从中断处继续下载
- ✅ **交叉域映射 / Cross-Domain Mapping**: 映射到 ChEMBL 化合物和 MONDO 疾病
- ✅ **去重处理 / Deduplication**: 自动去除重复的研究
- ✅ **批量处理 / Batch Processing**: 支持大规模数据处理

---

## 功能特性 / Features

### 1. 数据提取功能 / Data Extraction Features

#### 1.1 实体类型 / Entity Types

| 实体类型 / Entity Type | 描述 / Description | 主要属性 / Key Properties |
|------------------------|--------------------|---------------------------|
| `clinical:ClinicalTrial` | 临床试验 | NCT ID, 标题, 阶段, 状态, 日期 |
| `clinical:Intervention` | 干预措施 | 类型（药物/程序）, 名称, 描述 |
| `clinical:Condition` | 疾病条件 | 名称, MeSH 术语 |
| `clinical:StudySite` | 研究站点 | 设施名称, 位置, 联系信息 |
| `clinical:Investigator` | 研究者 | 姓名, 角色, 机构 |
| `clinical:Sponsor` | 赞助商 | 名称, 机构类型 |
| `clinical:Outcome` | 结果指标 | 类型（主要/次要）, 测量, 时间框架 |
| `clinical:EligibilityCriteria` | 入排标准 | 纳入/排除标准, 年龄, 性别 |

#### 1.2 关系类型 / Relationship Types

| 关系类型 / Relationship Type | 来源 / From | 目标 / To | 描述 / Description |
|------------------------------|-------------|-----------|---------------------|
| `TESTS_INTERVENTION` | ClinicalTrial | Intervention | 试验测试的干预措施 |
| `TRIAL_FOR_DISEASE` | ClinicalTrial | Condition | 试验针对的疾病 |
| `CONDUCTED_AT_SITE` | ClinicalTrial | StudySite | 试验进行地点 |
| `HAS_PRINCIPAL_INVESTIGATOR` | ClinicalTrial | Investigator | 主要研究者 |
| `SPONSORED_BY` | ClinicalTrial | Sponsor | 赞助商 |
| `HAS_OUTCOME` | ClinicalTrial | Outcome | 结果指标 |
| `HAS_ELIGIBILITY` | ClinicalTrial | EligibilityCriteria | 入排标准 |

#### 1.3 交叉域关系 / Cross-Domain Relationships

| 关系类型 / Relationship Type | 来源 / From | 目标 / To | 描述 / Description |
|------------------------------|-------------|-----------|---------------------|
| `TESTED_IN_CLINICAL_TRIAL` | Compound (ChEMBL) | ClinicalTrial | 化合物在临床试验中测试 |

### 2. API 功能 / API Features

- **分页支持 / Pagination**: 支持大结果集的分页处理
- **字段过滤 / Field Filtering**: 只获取需要的字段，减少数据传输
- **查询语法 / Query Syntax**: 支持 ClinicalTrials.gov API 的查询语法
- **速率控制 / Rate Control**: 自动控制请求速率，避免超限
- **错误处理 / Error Handling**: 完善的错误处理和重试机制

---

## API 端点 / API Endpoints

### 基础 URL / Base URL

```
https://clinicaltrials.gov/api/v2/studies
```

### 主要端点 / Main Endpoints

#### 1. 获取所有研究 / Get All Studies

```http
GET /api/v2/studies
```

**参数 / Parameters:**

| 参数 / Parameter | 类型 / Type | 必需 / Required | 描述 / Description |
|------------------|-------------|-----------------|---------------------|
| `format` | string | 是 | 响应格式（json） |
| `query.term` | string | 否 | 搜索词 |
| `fields` | string | 否 | 返回字段列表（逗号分隔） |
| `pageSize` | integer | 否 | 每页结果数（最大 100） |
| `pageToken` | string | 否 | 分页令牌 |
| `filter` | object | 否 | 过滤条件 |

#### 2. 获取单个研究 / Get Single Study

```http
GET /api/v2/studies/{NCT_ID}
```

**路径参数 / Path Parameters:**

| 参数 / Parameter | 类型 / Type | 描述 / Description |
|------------------|-------------|---------------------|
| `NCT_ID` | string | NCT 标识符（如 NCT00001234） |

### 响应格式 / Response Format

```json
{
  "studies": [
    {
      "protocolSection": {
        "identificationModule": {
          "nctId": "NCT00001234",
          "briefTitle": "Study Title",
          "officialTitle": "Official Study Title"
        },
        "statusModule": {
          "overallStatus": "Recruiting",
          "startDateStruct": {"date": "2024-01-01"}
        },
        "designModule": {
          "phase": "Phase 2",
          "studyType": "Interventional"
        },
        ...
      },
      "resultsSection": {
        ...
      }
    }
  ],
  "nextPageToken": "token_for_next_page",
  "totalStudies": 450000
}
```

---

## 实体模型 / Entity Models

### clinical:ClinicalTrial

```python
{
    "primary_id": "ClinicalTrial-NCT00001234",
    "identifiers": {
        "NCT": "NCT00001234",
        "org_study_id": "ORG-001",
        "secondary_ids": ["ID1", "ID2"]
    },
    "properties": {
        "nct_id": "NCT00001234",
        "brief_title": "Study of Drug X for Disease Y",
        "official_title": "A Randomized, Double-Blind, Placebo-Controlled Study...",
        "study_phase": "Phase 2",
        "study_status": "Recruiting",
        "start_date": "2024-01-01",
        "completion_date": "2025-12-31",
        "enrollment": 200,
        "study_type": "Interventional",
        "study_design": {
            "primary_purpose": "Treatment",
            "masking": "Double",
            "allocation": "Randomized"
        },
        "brief_summary": "This study will evaluate...",
        "detailed_description": "The purpose of this study is...",
        "source": "Medical Center",
        "has_results": true
    },
    "entity_type": "clinical:ClinicalTrial"
}
```

### clinical:Intervention

```python
{
    "primary_id": "Intervention-DrugX",
    "identifiers": {
        "name": "Drug X",
        "type": "Drug"
    },
    "properties": {
        "intervention_name": "Drug X",
        "intervention_type": "Drug",
        "description": "A novel therapeutic agent",
        "arm_group_labels": ["Arm 1", "Arm 2"]
    },
    "entity_type": "clinical:Intervention"
}
```

### clinical:Condition

```python
{
    "primary_id": "Condition-Diabetes",
    "identifiers": {
        "name": "Diabetes"
    },
    "properties": {
        "condition_name": "Diabetes Mellitus, Type 2",
        "mesh_terms": ["Diabetes Mellitus, Type 2", "Hyperglycemia"]
    },
    "entity_type": "clinical:Condition"
}
```

---

## 关系模型 / Relationship Models

### TESTS_INTERVENTION

```python
{
    "relationship_type": "TESTS_INTERVENTION",
    "source_entity_id": "ClinicalTrial-NCT00001234",
    "target_entity_id": "Intervention-DrugX",
    "properties": {
        "intervention_type": "Drug",
        "data_source": "ClinicalTrials.gov"
    },
    "source": "ClinicalTrials.gov"
}
```

### SPONSORED_BY

```python
{
    "relationship_type": "SPONSORED_BY",
    "source_entity_id": "ClinicalTrial-NCT00001234",
    "target_entity_id": "Sponsor-PharmaInc",
    "properties": {
        "sponsor_type": "Lead Sponsor",
        "agency_class": "Industry",
        "data_source": "ClinicalTrials.gov"
    },
    "source": "ClinicalTrials.gov"
}
```

---

## 安装配置 / Installation and Configuration

### 环境要求 / Requirements

- Python 3.8+
- requests 库
- 现有的 PharmaKG 基础设施

### 安装步骤 / Installation Steps

1. **确保处理器文件存在 / Ensure Processor File Exists**

```bash
ls -la processors/clinicaltrials_processor.py
```

2. **安装依赖 / Install Dependencies**

```bash
pip install requests
```

3. **验证安装 / Verify Installation**

```bash
python -c "from processors.clinicaltrials_processor import ClinicalTrialsProcessor; print('OK')"
```

### 配置选项 / Configuration Options

```python
config = {
    'extraction': {
        # API 配置 / API Configuration
        'api_base_url': 'https://clinicaltrials.gov/api/v2/studies',
        'api_version': 'v2',
        'request_timeout': 30,

        # 速率限制 / Rate Limiting
        'rate_limit_per_second': 2.0,  # 2 请求/秒
        'rate_limit_delay': 0.5,        # 请求间延迟

        # 分页配置 / Pagination
        'page_size': 100,               # 每页结果数
        'max_studies': None,            # 最大研究数限制
        'max_pages': None,              # 最大页数限制

        # 重试配置 / Retry Configuration
        'max_retries': 3,               # 最大重试次数
        'retry_backoff_factor': 2.0,    # 退避因子
        'retry_status_codes': [429, 500, 502, 503, 504],

        # 查询配置 / Query Configuration
        'query_term': None,             # 搜索词
        'query_filters': {},            # 过滤器

        # 去重配置 / Deduplication
        'deduplicate_by_nct_id': True,  # 按 NCT ID 去重

        # 交叉域映射 / Cross-Domain Mapping
        'map_to_chembl': True,          # 映射到 ChEMBL
        'map_to_mondo': True,           # 映射到 MONDO

        # 输出配置 / Output Configuration
        'save_raw_response': False,     # 保存原始响应
        'save_intermediate_batches': True
    }
}
```

---

## 使用方法 / Usage

### 基本使用 / Basic Usage

#### 1. 创建处理器实例 / Create Processor Instance

```python
from processors.clinicaltrials_processor import ClinicalTrialsProcessor

# 使用默认配置
processor = ClinicalTrialsProcessor()

# 使用自定义配置
config = {
    'extraction': {
        'page_size': 50,
        'rate_limit_per_second': 1.0,
        'max_studies': 1000
    }
}
processor = ClinicalTrialsProcessor(config)
```

#### 2. 全量下载 / Full Download

```python
# 下载所有研究（限制数量用于测试）
raw_data = processor.fetch_all_studies(max_studies=100)

# 转换数据
transformed_data = processor.transform(raw_data)

# 验证数据
if processor.validate(transformed_data):
    # 保存结果
    entities = transformed_data['entities']
    relationships = transformed_data['relationships']
    processor.save_results(entities, relationships)
```

#### 3. 按条件查询 / Query by Conditions

```python
# 按疾病查询
raw_data = processor.fetch_by_query("diabetes", max_studies=50)

# 按阶段查询
filters = {
    'filter': {
        'value': {'expr': {'phase': 'Phase 3'}},
        'field': 'Phase',
        'type': 'exact'
    }
}
raw_data = processor.fetch_by_query(filters=filters, max_studies=50)

# 按状态查询
filters = {
    'filter': {
        'value': {'expr': {'status': 'Recruiting'}},
        'field': 'Status',
        'type': 'exact'
    }
}
raw_data = processor.fetch_by_query(filters=filters, max_studies=50)
```

#### 4. 增量更新 / Incremental Update

```python
# 获取特定日期后更新的研究
raw_data = processor.fetch_incremental(last_update_date="2024-01-01")
```

#### 5. 获取单个研究 / Fetch Single Study

```python
# 按 NCT ID 获取
study_data = processor.fetch_by_nct_id("NCT00001234")

if study_data:
    raw_data = {'studies': [study_data]}
    transformed_data = processor.transform(raw_data)
```

---

## 命令行接口 / CLI Reference

### 基本语法 / Basic Syntax

```bash
python -m processors.clinicaltrials_processor [OPTIONS]
```

### 选项 / Options

| 选项 / Option | 类型 / Type | 描述 / Description |
|---------------|-------------|---------------------|
| `--mode` | string | 处理模式（full_download, query_by_disease, query_by_phase, query_by_status, incremental, nct_id） |
| `--query-term` | string | 搜索词 |
| `--phase` | string | 研究阶段 |
| `--status` | string | 研究状态 |
| `--nct-id` | string | NCT ID |
| `--last-update-date` | string | 最后更新日期（YYYY-MM-DD） |
| `--max-studies` | int | 最大研究数量 |
| `--max-pages` | int | 最大页数 |
| `--page-size` | int | 每页结果数（默认: 100） |
| `--rate-limit` | float | 每秒请求数（默认: 2.0） |
| `--output` | string | 输出目录 |
| `--no-dedup` | flag | 禁用去重 |
| `--no-cross-domain` | flag | 禁用交叉域映射 |
| `--save-raw` | flag | 保存原始 API 响应 |
| `--verbose` | flag | 详细输出 |

### 使用示例 / Usage Examples

#### 全量下载 / Full Download

```bash
# 下载前 1000 个研究
python -m processors.clinicaltrials_processor --mode full_download --max-studies 1000

# 下载前 10 页
python -m processors.clinicaltrials_processor --mode full_download --max-pages 10

# 自定义输出目录
python -m processors.clinicaltrials_processor --mode full_download --output /custom/path
```

#### 按条件查询 / Query by Conditions

```bash
# 按疾病查询
python -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"

# 按阶段查询
python -m processors.clinicaltrials_processor --mode query_by_phase --phase "Phase 3"

# 按状态查询
python -m processors.clinicaltrials_processor --mode query_by_status --status "Recruiting"
```

#### 增量更新 / Incremental Update

```bash
python -m processors.clinicaltrials_processor --mode incremental --last-update-date "2024-01-01"
```

#### 获取单个研究 / Fetch Single Study

```bash
python -m processors.clinicaltrials_processor --mode nct_id --nct-id "NCT00001234"
```

---

## 代码示例 / Code Examples

### 示例 1: 批量处理研究 / Example 1: Batch Process Studies

```python
from processors.clinicaltrials_processor import ClinicalTrialsProcessor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

# 创建处理器
config = {
    'extraction': {
        'page_size': 100,
        'rate_limit_per_second': 2.0,
        'max_studies': 500,
        'save_intermediate_batches': True
    }
}

processor = ClinicalTrialsProcessor(config)

# 获取数据
raw_data = processor.fetch_all_studies()

# 转换和验证
transformed_data = processor.transform(raw_data)

if processor.validate(transformed_data):
    # 保存结果
    entities = transformed_data['entities']
    relationships = transformed_data['relationships']
    output_path = processor.save_results(entities, relationships)

    print(f"结果已保存到: {output_path}")
```

### 示例 2: 处理特定疾病研究 / Example 2: Process Specific Disease Studies

```python
from processors.clinicaltrials_processor import ClinicalTrialsProcessor

processor = ClinicalTrialsProcessor()

# 定义查询
diseases = ["diabetes", "hypertension", "cancer"]

all_entities = {}
all_relationships = []

for disease in diseases:
    print(f"处理 {disease} 相关研究...")

    # 获取数据
    raw_data = processor.fetch_by_query(disease, max_studies=100)

    # 转换数据
    transformed_data = processor.transform(raw_data)

    # 合并结果
    for entity_type, entities in transformed_data['entities'].items():
        if entity_type not in all_entities:
            all_entities[entity_type] = []
        all_entities[entity_type].extend(entities)

    all_relationships.extend(transformed_data['relationships'])

# 保存合并结果
processor.save_results(all_entities, all_relationships, "output/combined")
```

### 示例 3: 增量更新流程 / Example 3: Incremental Update Workflow

```python
from processors.clinicaltrials_processor import ClinicalTrialsProcessor
from datetime import datetime, timedelta

processor = ClinicalTrialsProcessor()

# 获取上周更新的研究
last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

raw_data = processor.fetch_incremental(last_update_date=last_week)

if raw_data and 'studies' in raw_data:
    print(f"找到 {len(raw_data['studies'])} 个更新的研究")

    # 转换和保存
    transformed_data = processor.transform(raw_data)
    processor.save_results(
        transformed_data['entities'],
        transformed_data['relationships'],
        f"output/incremental/{last_week}"
    )
```

### 示例 4: 交叉域分析 / Example 4: Cross-Domain Analysis

```python
from processors.clinicaltrials_processor import ClinicalTrialsProcessor

config = {
    'extraction': {
        'map_to_chembl': True,
        'map_to_mondo': True
    }
}

processor = ClinicalTrialsProcessor(config)

# 获取数据
raw_data = processor.fetch_by_query("diabetes", max_studies=100)

# 转换数据（会创建交叉域关系）
transformed_data = processor.transform(raw_data)

# 分析交叉域关系
cross_domain_rels = [
    rel for rel in transformed_data['relationships']
    if rel['relationship_type'] == 'TESTED_IN_CLINICAL_TRIAL'
]

print(f"找到 {len(cross_domain_rels)} 个交叉域关系")

for rel in cross_domain_rels[:10]:
    print(f"  {rel['source_entity_id']} -> {rel['target_entity_id']}")
```

---

## 性能优化 / Performance Optimization

### 速率限制优化 / Rate Limiting Optimization

```python
# 调整速率限制以最大化吞吐量
config = {
    'extraction': {
        'rate_limit_per_second': 2.0,  # 不要超过 2.0
        'request_timeout': 30,          # 适当的超时
        'max_retries': 3                # 适当的重试次数
    }
}
```

### 分页优化 / Pagination Optimization

```python
# 使用较大的页面大小以减少请求次数
config = {
    'extraction': {
        'page_size': 100,  # 最大值
        'max_studies': 10000
    }
}
```

### 内存优化 / Memory Optimization

```python
# 处理大量数据时，分批保存
config = {
    'extraction': {
        'page_size': 100,
        'save_intermediate_batches': True,
        'batch_size': 1000  # 每 1000 个研究保存一次
    }
}
```

### 网络优化 / Network Optimization

```python
# 使用更短的超时和更多的重试
config = {
    'extraction': {
        'request_timeout': 15,
        'max_retries': 5,
        'retry_backoff_factor': 1.5
    }
}
```

---

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. 速率限制错误 / Rate Limit Errors

**症状 / Symptoms:**
```
Request failed with status 429
```

**解决方案 / Solutions:**
- 降低 `rate_limit_per_second` 到 1.0 或更低
- 增加 `rate_limit_delay` 到 1.0 秒或更长

#### 2. 超时错误 / Timeout Errors

**症状 / Symptoms:**
```
Request timed out
```

**解决方案 / Solutions:**
- 增加 `request_timeout` 到 60 秒或更长
- 检查网络连接
- 减少 `page_size` 以加快响应

#### 3. 内存不足 / Out of Memory

**症状 / Symptoms:**
```
MemoryError: Cannot allocate memory
```

**解决方案 / Solutions:**
- 设置 `max_studies` 限制
- 启用 `save_intermediate_batches`
- 分批处理数据

#### 4. 数据验证失败 / Data Validation Failed

**症状 / Symptoms:**
```
Data validation failed
```

**解决方案 / Solutions:**
- 检查 API 响应格式
- 验证必需字段是否存在
- 查看详细日志以确定问题

### 调试技巧 / Debugging Tips

#### 启用详细日志 / Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 保存原始响应 / Save Raw Responses

```python
config = {
    'extraction': {
        'save_raw_response': True
    }
}
```

#### 测试单个请求 / Test Single Request

```python
processor = ClinicalTrialsProcessor()
study_data = processor.fetch_by_nct_id("NCT00001234")
print(study_data)
```

---

## API 速率限制 / API Rate Limits

ClinicalTrials.gov API v2 的速率限制：

- **限制 / Limit**: 1 请求 / 0.5 秒 = 2 请求/秒
- **建议 / Recommended**: 使用 1.5-2.0 请求/秒以确保稳定性
- **惩罚 / Penalty**: 超限可能导致临时封禁

### 速率限制计算 / Rate Limit Calculation

```
总时间 = 总请求数 / 速率限制
例如：400,000 研究 / 100 每页 / 2 每秒 ≈ 33 小时
```

---

## 交叉域映射 / Cross-Domain Mapping

### ChEMBL 映射 / ChEMBL Mapping

将干预措施名称映射到 ChEMBL 化合物 ID：

```python
def _map_intervention_to_chembl(self, intervention_name: str) -> Optional[str]:
    # 实现映射逻辑
    # 1. 检查缓存
    # 2. 查询本地 ChEMBL 数据库
    # 3. 或调用 ChEMBL API
    pass
```

### MONDO 映射 / MONDO Mapping

将疾病条件映射到 MONDO 疾病 ID：

```python
def _map_condition_to_mondo(self, condition_name: str) -> Optional[str]:
    # 实现映射逻辑
    # 1. 检查缓存
    # 2. 查询 MONDO 映射表
    # 3. 或调用 MONDO API
    pass
```

---

## 输出文件结构 / Output File Structure

```
data/
├── processed/
│   ├── entities/
│   │   └── clinicaltrials/
│   │       ├── clinicaltrials_trials_20240208_120000.json
│   │       ├── clinicaltrials_interventions_20240208_120000.json
│   │       ├── clinicaltrials_conditions_20240208_120000.json
│   │       ├── clinicaltrials_sites_20240208_120000.json
│   │       ├── clinicaltrials_investigators_20240208_120000.json
│   │       ├── clinicaltrials_sponsors_20240208_120000.json
│   │       ├── clinicaltrials_outcomes_20240208_120000.json
│   │       └── clinicaltrials_eligibility_20240208_120000.json
│   ├── relationships/
│   │   └── clinicaltrials/
│   │       └── clinicaltrials_relationships_20240208_120000.json
│   └── documents/
│       └── clinicaltrials/
│           └── clinicaltrials_summary_20240208_120000.json
└── cache/
    └── clinicaltrials_progress.json
```

---

## 更新日志 / Changelog

### v1.0 (2026-02-08)

**新增功能 / New Features:**
- ✅ 完整的 ClinicalTrials.gov API v2 支持
- ✅ 全量下载、条件查询、增量更新模式
- ✅ 速率限制和自动重试机制
- ✅ 断点续传功能
- ✅ 交叉域映射（ChEMBL, MONDO）
- ✅ 去重和数据验证
- ✅ 命令行接口
- ✅ 完整的测试套件

**已知限制 / Known Limitations:**
- 交叉域映射需要额外实现
- 全量下载可能需要数小时
- 大规模数据处理需要足够的内存

---

## 贡献指南 / Contributing

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证 / License

本项目采用 MIT 许可证 - 详见 LICENSE 文件

---

## 联系方式 / Contact

- **项目主页 / Project Home**: https://github.com/your-org/pj-pharmaKG
- **问题反馈 / Issues**: https://github.com/your-org/pj-pharmaKG/issues
- **文档 / Documentation**: https://docs.pharmakg.org

---

## 参考资料 / References

- [ClinicalTrials.gov API v2 文档](https://clinicaltrials.gov/api/v2/)
- [ClinicalTrials.gov API 字段参考](https://clinicaltrials.gov/api/v2/info/v2/studies)
- [PharmaKG 项目文档](https://docs.pharmakg.org)
- [ChEMBL 数据库](https://www.ebi.ac.uk/chembl/)
- [MONDO 疾病本体](https://mondo.monarchinitiative.org/)

---

**文档版本 / Document Version:** v1.0
**最后更新 / Last Updated:** 2026-02-08
**维护者 / Maintainer:** PharmaKG Development Team
