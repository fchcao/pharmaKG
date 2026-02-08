# FDA Drug Shortages Database Processor Documentation
# FDA 药物短缺数据库处理器文档

**Version / 版本:** v1.0
**Last Updated / 最后更新:** 2026-02-08

---

## Table of Contents / 目录

- [Overview / 概述](#overview--概述)
- [Features / 功能特性](#features--功能特性)
- [API Endpoint / API 端点](#api-endpoint--api-端点)
- [Entity Models / 实体模型](#entity-models--实体模型)
- [Relationship Models / 关系模型](#relationship-models--关系模型)
- [Installation / 安装配置](#installation--安装配置)
- [Usage / 使用方法](#usage--使用方法)
- [CLI Reference / 命令行接口](#cli-reference--命令行接口)
- [Code Examples / 代码示例](#code-examples--代码示例)
- [API Response Format / API 响应格式](#api-response-format--api-响应格式)
- [Troubleshooting / 故障排除](#故障排除)

---

## Overview / 概述

**ShortageProcessor** fetches and processes drug shortage data from the FDA Drug Shortages Database API. The database contains information about current and resolved drug shortages, including affected products, manufacturers, and reasons for shortages.

**ShortageProcessor** 从 FDA 药物短缺数据库 API 获取并处理药物短缺数据。该数据库包含当前和已解决的药物短缺信息，包括受影响的产品、制造商和短缺原因。

### Key Features / 主要功能

- ✅ **API Integration / API 集成** - Direct access to FDA Drug Shortages API
- ✅ **Query Support / 查询支持** - Search by drug name, status, date range
- ✅ **Pagination / 分页支持** - Fetch all records with automatic pagination
- ✅ **Manufacturer Data / 制造商数据** - Extract manufacturer and facility information
- ✅ **Cross-Domain Mapping / 交叉域映射** - Map to ChEMBL via UNII
- ✅ **Rate Limiting / 速率限制** - Respectful API access with delays
- ✅ **Retry Logic / 重试逻辑** - Automatic retry for failed requests
- ✅ **Deduplication / 去重处理** - Automatic deduplication by shortage_id

---

## Features / 功能特性

### 1. Data Extraction Features / 数据提取功能

#### 1.1 Entity Types / 实体类型

| Entity Type / 实体类型 | Description / 描述 | Key Properties / 主要属性 |
|------------------------|--------------------|---------------------------|
| `sc:DrugShortage` | Drug shortage record | shortage_id, shortage_status, start_date, end_date, reason |
| `rd:Compound` | Affected drug product | generic_name, brand_names, ndc, dosage_form, strength |
| `sc:Manufacturer` | Manufacturing company | manufacturer_name, company_type, contact_info |
| `sc:Facility` | Manufacturing facility | facility_name, address (city, state, country) |

#### 1.2 Relationship Types / 关系类型

| Relationship Type / 关系类型 | Source / 来源 | Target / 目标 | Description / 描述 |
|------------------------------|---------------|---------------|---------------------|
| `EXPERIENCES_SHORTAGE` | Compound | DrugShortage | Links drug to shortage record |
| `CAUSED_BY_QUALITY_ISSUE` | DrugShortage | Manufacturer | Indicates manufacturer responsibility |
| `HAS_FACILITY` | Manufacturer | Facility | Links manufacturer to facilities |
| `REPORTED_TO_AGENCY` | DrugShortage | RegulatoryAgency | Links to FDA |

#### 1.3 Cross-Domain Relationships / 交叉域关系

| Relationship Type / 关系类型 | Source / 来源 | Target / 目标 | Description / 描述 |
|------------------------------|---------------|---------------|---------------------|
| `EXPERIENCES_SHORTAGE` | Compound (ChEMBL) | DrugShortage | Maps shortage drugs to ChEMBL compounds |

---

## API Endpoint / API 端点

### Base URL / 基础 URL

```
https://api.fda.gov/drug/shortages.json
```

### Query Parameters / 查询参数

| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|---------------------|
| `search` | string | No | Search query (e.g., "generic_name:epinephrine") |
| `limit` | integer | No | Number of results to return (max: 100 per request) |
| `skip` | integer | No | Number of results to skip (for pagination) |

### Search Examples / 搜索示例

```bash
# Search by drug name
https://api.fda.gov/drug/shortages.json?search=epinephrine

# Search by status
https://api.fda.gov/drug/shortages.json?search=status:"Current"

# Limit results
https://api.fda.gov/drug/shortages.json?limit=10

# Pagination
https://api.fda.gov/drug/shortages.json?skip=10&limit=10
```

---

## Entity Models / 实体模型

### sc:DrugShortage

```python
{
    "primary_id": "DrugShortage-SH-001",
    "identifiers": {
        "shortage_id": "SH-001"
    },
    "properties": {
        "shortage_id": "SH-001",
        "shortage_status": "Current Shortage",
        "shortage_start_date": "2024-01-01",
        "shortage_end_date": null,
        "shortage_type": "Shortage",
        "reason_for_shortage": "Manufacturing delay",
        "therapeutic_area": "Anaphylaxis",
        "presentation": "Autoinjector",
        "strength": "0.3 mg",
        "data_source": "FDA Drug Shortages Database"
    },
    "entity_type": "sc:DrugShortage"
}
```

### rd:Compound

```python
{
    "primary_id": "Compound-Epinephrine",
    "identifiers": {
        "generic_name": "Epinephrine",
        "brand_names": ["EpiPen", "Adrenaclick"],
        "ndc": "49502-1001-1"
    },
    "properties": {
        "generic_name": "Epinephrine",
        "brand_names": ["EpiPen", "Adrenaclick"],
        "ndc": "49502-1001-1",
        "dosage_form": "Injection",
        "strength": "0.3 mg",
        "route": "Intramuscular",
        "marketing_status": "Prescription",
        "data_source": "FDA Drug Shortages Database"
    },
    "entity_type": "rd:Compound"
}
```

### sc:Manufacturer

```python
{
    "primary_id": "Manufacturer-Viatris",
    "identifiers": {
        "name": "Viatris"
    },
    "properties": {
        "manufacturer_name": "Viatris",
        "company_type": "Manufacturer",
        "contact_info": "contact@viatris.com",
        "data_source": "FDA Drug Shortages Database"
    },
    "entity_type": "sc:Manufacturer"
}
```

### sc:Facility

```python
{
    "primary_id": "Facility-Manufacturing_Site_A",
    "identifiers": {
        "name": "Manufacturing Site A"
    },
    "properties": {
        "facility_name": "Manufacturing Site A",
        "address": {
            "city": "Morgantown",
            "state": "WV",
            "country": "USA"
        },
        "facility_type": "Manufacturing",
        "data_source": "FDA Drug Shortages Database"
    },
    "entity_type": "sc:Facility"
}
```

---

## Relationship Models / 关系模型

### EXPERIENCES_SHORTAGE

```python
{
    "relationship_type": "EXPERIENCES_SHORTAGE",
    "source_entity_id": "Compound-Epinephrine",
    "target_entity_id": "DrugShortage-SH-001",
    "properties": {
        "shortage_status": "Current Shortage",
        "data_source": "FDA Drug Shortages Database"
    },
    "source": "FDA Drug Shortages Database"
}
```

### CAUSED_BY_QUALITY_ISSUE

```python
{
    "relationship_type": "CAUSED_BY_QUALITY_ISSUE",
    "source_entity_id": "DrugShortage-SH-001",
    "target_entity_id": "Manufacturer-Viatris",
    "properties": {
        "reason": "Manufacturing delay",
        "data_source": "FDA Drug Shortages Database"
    },
    "source": "FDA Drug Shortages Database"
}
```

---

## Installation / 安装配置

### Requirements / 环境要求

- Python 3.8+
- requests library
- Internet connection for API access
- Existing PharmaKG infrastructure

### Installation Steps / 安装步骤

1. **Verify processor file / 验证处理器文件**

```bash
ls -la processors/shortage_processor.py
```

2. **Install dependencies / 安装依赖**

```bash
pip install requests
```

3. **Test API access / 测试 API 访问**

```bash
curl "https://api.fda.gov/drug/shortages.json?limit=1"
```

---

## Usage / 使用方法

### Basic Usage / 基本使用

#### 1. Create Processor Instance / 创建处理器实例

```python
from processors.shortage_processor import ShortageProcessor

# Use default configuration
processor = ShortageProcessor()

# Use custom configuration
config = {
    'extraction': {
        'limit': 100,
        'search_query': 'epinephrine',
        'map_to_chembl': True
    }
}
processor = ShortageProcessor(config)
```

#### 2. Fetch Shortage Data / 获取短缺数据

```python
# Fetch all shortages (with pagination)
raw_data = processor.fetch_all_shortages(batch_size=100)

# Fetch by search query
raw_data = processor.fetch_shortages(search_query='epinephrine')

# Fetch by status
raw_data = processor.fetch_shortages(shortage_status='Current')

# Fetch with limit
raw_data = processor.fetch_shortages(limit=50)
```

#### 3. Transform and Save / 转换和保存

```python
# Transform data
transformed_data = processor.transform(raw_data)

# Validate data
if processor.validate(transformed_data):
    # Get entities and relationships
    entities = transformed_data['entities']
    relationships = transformed_data['relationships']

    # Save results
    output_path = processor.save_results(entities, relationships)
    print(f"Results saved to: {output_path}")
```

---

## CLI Reference / 命令行接口

### Basic Syntax / 基本语法

```bash
python -m processors.shortage_processor [OPTIONS]
```

### Options / 选项

| Option / 选项 | Type / 类型 | Description / 描述 |
|---------------|-------------|---------------------|
| `--mode` | string | Processing mode: all, search, status |
| `--query` | string | Search query string |
| `--status` | string | Shortage status filter |
| `--limit` | int | Maximum records to fetch (default: 100) |
| `--batch-size` | int | Batch size for pagination (default: 100) |
| `--no-dedup` | flag | Disable deduplication |
| `--no-cross-domain` | flag | Disable cross-domain mapping |
| `--save-raw` | flag | Save raw API responses |
| `--output` | string | Custom output directory |
| `--verbose` | flag | Enable verbose output |

### Usage Examples / 使用示例

```bash
# Fetch all drug shortages
python -m processors.shortage_processor --mode all

# Fetch by drug name
python -m processors.shortage_processor --mode search --query "epinephrine"

# Fetch current shortages only
python -m processors.shortage_processor --mode status --status "Current"

# Fetch with limit
python -m processors.shortage_processor --mode all --limit 50

# Custom output directory
python -m processors.shortage_processor --mode all --output /custom/output
```

---

## Code Examples / 代码示例

### Example 1: Fetch All Shortages / 示例 1：获取所有短缺

```python
from processors.shortage_processor import ShortageProcessor
import logging

logging.basicConfig(level=logging.INFO)

processor = ShortageProcessor()

# Fetch all shortages with pagination
raw_data = processor.fetch_all_shortages(batch_size=100)

print(f"Total shortages fetched: {len(raw_data['results'])}")

# Transform and save
transformed_data = processor.transform(raw_data)
result = processor.save_results(
    transformed_data['entities'],
    transformed_data['relationships']
)

print(f"Results saved to: {result}")
```

### Example 2: Search by Drug Name / 示例 2：按药物名称搜索

```python
from processors.shortage_processor import ShortageProcessor

processor = ShortageProcessor()

# Search for specific drug
raw_data = processor.fetch_shortages(
    search_query='epinephrine',
    limit=100
)

# Transform
transformed_data = processor.transform(raw_data)

# Analyze results
shortages = transformed_data['entities']['sc:DrugShortage']
print(f"Found {len(shortages)} epinephrine shortages")

for shortage in shortages[:5]:
    print(f"  {shortage['properties']['shortage_status']}: "
          f"{shortage['properties']['reason_for_shortage']}")
```

### Example 3: Track Resolved Shortages / 示例 3：跟踪已解决短缺

```python
from processors.shortage_processor import ShortageProcessor

processor = ShortageProcessor()

# Fetch resolved shortages
raw_data = processor.fetch_shortages(shortage_status='Resolved')

transformed_data = processor.transform(raw_data)

# Get resolved shortages
shortages = transformed_data['entities']['sc:DrugShortage']

# Calculate resolution time
from datetime import datetime

resolution_times = []
for shortage in shortages:
    start = shortage['properties']['shortage_start_date']
    end = shortage['properties']['shortage_end_date']

    if start and end:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        duration = (end_date - start_date).days
        resolution_times.append(duration)

if resolution_times:
    avg_duration = sum(resolution_times) / len(resolution_times)
    print(f"Average resolution time: {avg_duration:.1f} days")
```

### Example 4: Cross-Domain Analysis / 示例 4：交叉域分析

```python
from processors.shortage_processor import ShortageProcessor

config = {
    'extraction': {
        'map_to_chembl': True
    }
}

processor = ShortageProcessor(config)

raw_data = processor.fetch_all_shortages()
transformed_data = processor.transform(raw_data)

# Find cross-domain relationships
cross_domain_rels = [
    rel for rel in transformed_data['relationships']
    if rel['source'] == 'FDA Shortages-ChEMBL-Mapping'
]

print(f"Cross-domain mappings: {len(cross_domain_rels)}")
```

---

## API Response Format / API 响应格式

### Example Response / 示例响应

```json
{
  "meta": {
    "results": {
      "total": 500,
      "skip": 0,
      "limit": 100
    }
  },
  "results": [
    {
      "shortage_id": "SH-001",
      "generic_name": "Epinephrine",
      "brand_names": ["EpiPen"],
      "ndc": "49502-1001-1",
      "dosage_form": "Injection",
      "strength": "0.3 mg",
      "route": "Intramuscular",
      "status": "Current Shortage",
      "shortage_type": "Shortage",
      "start_date": "2024-01-01",
      "end_date": null,
      "reason": "Manufacturing delay",
      "therapeutic_area": "Anaphylaxis",
      "manufacturer_name": "Viatris",
      "facility_name": "Manufacturing Site A",
      "city": "Morgantown",
      "state": "WV",
      "country": "USA"
    }
  ]
}
```

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### 1. API Access Errors / API 访问错误

**Problem / 问题:**
```
ConnectionError: Failed to establish connection
```

**Solution / 解决方案:**
- Check internet connection
- Verify API endpoint is accessible
- Try again later (API may be temporarily unavailable)

#### 2. Rate Limiting / 速率限制

**Problem / 问题:**
```
Request failed with status 429
```

**Solution / 解决方案:**
- The processor has built-in rate limiting
- Increase `rate_limit_delay` in configuration
- Wait before retrying

#### 3. No Results / 无结果

**Problem / 问题:**
```
No data fetched
```

**Solution / 解决方案:**
- Verify search query syntax
- Check if data exists for query
- Try broader search terms

---

## Data Quality Notes / 数据质量说明

### FDA Drug Shortages Database Limitations / FDA 药物短缺数据库限制

1. **Voluntary Reporting / 自愿报告** - Manufacturers report shortages voluntarily
2. **Delayed Updates / 延迟更新** - May not reflect real-time status
3. **Incomplete Information / 信息不完整** - Some fields may be missing
4. **Status Changes / 状态变化** - Shortages may resolve without database update

### Best Practices / 最佳实践

1. Verify current shortage status with manufacturer
2. Cross-reference with other shortage databases
3. Check therapeutic alternatives for critical shortages
4. Monitor shortage status regularly for updates
5. Consider impact on patient care

---

## Output Files / 输出文件

### Generated Files / 生成的文件

```
data/
├── processed/
│   ├── entities/
│   │   └── shortages/
│   │       ├── shortages_shortages_YYYYMMDD.json
│   │       ├── shortages_compounds_YYYYMMDD.json
│   │       ├── shortages_manufacturers_YYYYMMDD.json
│   │       └── shortages_facilities_YYYYMMDD.json
│   ├── relationships/
│   │   └── shortages/
│   │       └── shortages_relationships_YYYYMMDD.json
│   └── documents/
│       └── shortages/
│           └── shortages_summary_YYYYMMDD.json
```

---

## Testing / 测试

Run the test suite / 运行测试套件:

```bash
python scripts/test_shortage_processor.py
```

The test suite includes:
- Entity creation tests
- Data parsing tests
- Transform functionality tests
- API method tests (with mocking)

---

## References / 参考资料

- [FDA Drug Shortages Database](https://www.accessdata.fda.gov/scripts/drugshortages/)
- [FDA API Documentation](https://open.fda.gov/apis/drug/shortages/)
- [PharmaKG Project Documentation](https://docs.pharmakg.org)

---

**Document Version / 文档版本:** v1.0
**Last Updated / 最后更新:** 2026-02-08
**Maintainer / 维护者:** PharmaKG Development Team
