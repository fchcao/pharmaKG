# FDA Drugs@FDA API Processor Documentation

## FDA Drugs@FDA API 处理器文档

### Table of Contents / 目录

1. [Overview / 概述](#overview--概述)
2. [Features / 功能特性](#features--功能特性)
3. [Installation / 安装](#installation--安装)
4. [Configuration / 配置](#configuration--配置)
5. [Usage / 使用方法](#usage--使用方法)
6. [API Endpoints / API 端点](#api-endpoints--api-端点)
7. [Data Structure / 数据结构](#data-structure--数据结构)
8. [Cross-Domain Integration / 跨域集成](#cross-domain-integration--跨域集成)
9. [Performance Considerations / 性能考虑](#performance-considerations--性能考虑)
10. [Troubleshooting / 故障排除](#troubleshooting--故障排除)

---

## Overview / 概述

### What is the Drugs@FDA Processor? / 什么是 Drugs@FDA 处理器？

The **DrugsAtFDAProcessor** is a Python-based data processor that extracts regulatory approval data from the FDA's Drugs@FDA API (openFDA). It transforms FDA drug approval information into a knowledge graph format suitable for the PharmaKG system.

**DrugsAtFDAProcessor** 是一个基于 Python 的数据处理器，从 FDA 的 Drugs@FDA API (openFDA) 提取监管批准数据。它将 FDA 药物批准信息转换为适合 PharmaKG 系统的知识图谱格式。

### Key Features / 主要特性

- **Comprehensive Data Extraction** / 全面数据提取
  - Approvals (NDA, ANDA, BLA) / 批准
  - Submissions and Supplements / 提交和补充
  - Compounds with UNII identifiers / 带 UNII 标识符的化合物
  - Drug Products and Brands / 药物产品和品牌
  - Regulatory Agencies / 监管机构

- **Cross-Domain Integration** / 跨域集成
  - UNII to ChEMBL mapping via MyChem.info / 通过 MyChem.info 映射 UNII 到 ChEMBL
  - Clinical trial linkage via NCT numbers / 通过 NCT 号码链接临床试验
  - Disease/Condition mapping / 疾病/状况映射

- **Robust Error Handling** / 健壮的错误处理
  - Automatic retry logic / 自动重试逻辑
  - Rate limiting compliance / 速率限制合规
  - Progress tracking and resumption / 进度跟踪和恢复

- **Flexible Query Options** / 灵活的查询选项
  - Query by brand name / 按品牌名查询
  - Query by application number / 按申请号查询
  - Query by sponsor name / 按赞助商名称查询
  - Full dataset download / 完整数据集下载

---

## Features / 功能特性

### Extracted Entities / 提取的实体

1. **regulatory:Approval** / 批准
   - application_number (NDA, ANDA, BLA)
   - approval_date, tentative_approval_date
   - approval_type, approval_status
   - supplement_numbers

2. **regulatory:Submission** / 提交
   - submission_number, submission_type
   - submission_date, submission_status
   - review_priority (Standard/Priority)

3. **rd:Compound** / 化合物
   - unirot_id (UNII - Unique Ingredient Identifier)
   - drug_name, generic_name
   - chemical_type, route_of_administration
   - dosage_form

4. **rd:DrugProduct** / 药物产品
   - product_number, product_type
   - brand_name, trade_names
   - marketing_status (Prescription, OTC, Discontinued)
   - sponsor_name

5. **regulatory:RegulatoryAgency** / 监管机构
   - agency_name (FDA, CDER, CBER)
   - division, office, review_class

### Extracted Relationships / 提取的关系

1. **SUBMITTED_FOR_APPROVAL** - Submission → Approval
2. **APPROVED_PRODUCT** - RegulatoryAgency → Compound (via approval)
3. **APPROVAL_FOR** - Approval → Compound
4. **HAS_MARKETING_AUTHORIZATION** - Compound → DrugProduct
5. **MANUFACTURED_BY** - DrugProduct → Sponsor/Manufacturer
6. **HAS_SUBMISSION** - Approval → Submission

### Cross-Domain Relationships / 跨域关系

1. **TESTED_IN_CLINICAL_TRIAL** - Compound → ClinicalTrial
2. **APPROVED_FOR_DISEASE** - Compound → Condition

---

## Installation / 安装

### Prerequisites / 先决条件

```bash
# Activate conda environment / 激活 conda 环境
conda activate pharmakg-api

# Install dependencies / 安装依赖
pip install requests
```

### Files / 文件

The processor consists of: / 处理器由以下文件组成：

```
processors/
  └── drugsatfda_processor.py    # Main processor / 主处理器
scripts/
  └── test_drugsatfda_processor.py  # Test script / 测试脚本
docs/
  └── DRUGSATFDA_PROCESSOR.md    # This documentation / 本文档
```

---

## Configuration / 配置

### Extraction Configuration / 提取配置

```python
from processors.drugsatfda_processor import DrugsAtFDAProcessor

config = {
    'extraction': {
        # API Configuration / API 配置
        'api_base_url': 'https://api.fda.gov/drug/drugsfda.json',
        'request_timeout': 30,

        # Rate Limiting / 速率限制
        'rate_limit_per_second': 1.0,  # Conservative default / 保守默认值
        'rate_limit_delay': 1.0,

        # Pagination / 分页
        'page_size': 100,  # Max: 100 / 最大值：100
        'max_pages': None,
        'max_applications': None,

        # Retry Logic / 重试逻辑
        'max_retries': 3,
        'retry_backoff_factor': 2.0,
        'retry_status_codes': [429, 500, 502, 503, 504],

        # Cross-Domain Mapping / 跨域映射
        'map_unii_to_chembl': True,
        'map_to_clinical_trials': True,
        'use_mychem_api': True,

        # Deduplication / 去重
        'deduplicate_by_application_number': True,

        # Output / 输出
        'save_raw_response': False,
        'save_intermediate_batches': True
    }
}

processor = DrugsAtFDAProcessor(config)
```

---

## Usage / 使用方法

### Command Line Interface / 命令行接口

#### Fetch All Applications / 获取所有申请

```bash
# Fetch all applications (first 100 for testing) / 获取所有申请（测试时前100个）
python -m processors.drugsatfda_processor --mode all --max-applications 100

# Full download / 完整下载
python -m processors.drugsatfda_processor --mode all
```

#### Query by Brand Name / 按品牌名查询

```bash
# Query by brand name / 按品牌名查询
python -m processors.drugsatfda_processor --mode brand-name --brand-name "Lipitor"
```

#### Query by Application Number / 按申请号查询

```bash
# Query by application number / 按申请号查询
python -m processors.drugsatfda_processor --mode application-number --application-number "NDA020709"
```

#### Query by Sponsor Name / 按赞助商名称查询

```bash
# Query by sponsor name / 按赞助商名称查询
python -m processors.drugsatfda_processor --mode sponsor-name --sponsor-name "Pfizer"
```

#### Custom Output Directory / 自定义输出目录

```bash
# Custom output directory / 自定义输出目录
python -m processors.drugsatfda_processor --mode all --output /custom/output/path
```

#### Disable Cross-Domain Mapping / 禁用跨域映射

```bash
# Disable cross-domain mapping / 禁用跨域映射
python -m processors.drugsatfda_processor --mode all --no-cross-domain
```

#### Save Raw API Responses / 保存原始 API 响应

```bash
# Save raw responses / 保存原始响应
python -m processors.drugsatfda_processor --mode all --save-raw
```

### Python API / Python API

```python
from processors.drugsatfda_processor import DrugsAtFDAProcessor

# Create processor / 创建处理器
config = {'extraction': {'max_applications': 10}}
processor = DrugsAtFDAProcessor(config)

# Fetch data / 获取数据
raw_data = processor.fetch_all_applications(max_applications=10)

# Transform data / 转换数据
transformed_data = processor.transform(raw_data)

# Validate data / 验证数据
is_valid = processor.validate(transformed_data)

# Save results / 保存结果
entities = transformed_data['entities']
relationships = transformed_data['relationships']
output_path = processor.save_results(entities, relationships)
```

---

## API Endpoints / API 端点

### FDA Drugs@FDA API / FDA Drugs@FDA API

**Base URL:** `https://api.fda.gov/drug/drugsfda.json`

#### Query Parameters / 查询参数

| Parameter / 参数 | Description / 描述 | Example / 示例 |
|-----------------|-------------------|----------------|
| `search` | Search query / 搜索查询 | `search=products.brand_name:"Advil"` |
| `limit` | Number of results / 结果数量 | `limit=100` |
| `skip` | Pagination offset / 分页偏移 | `skip=100` |

#### Search Fields / 搜索字段

- `application_number` - Application number / 申请号
- `products.brand_name` - Brand name / 品牌名
- `products.generic_name` - Generic name / 通用名
- `sponsor_name` - Sponsor name / 赞助商名称
- `openfda.unii` - UNII identifier / UNII 标识符

#### Example Queries / 查询示例

```bash
# Search by brand name / 按品牌名搜索
https://api.fda.gov/drug/drugsfda.json?search=products.brand_name:"Lipitor"&limit=10

# Search by application number / 按申请号搜索
https://api.fda.gov/drug/drugsfda.json?search=application_number:"NDA020709"

# Search by sponsor / 按赞助商搜索
https://api.fda.gov/drug/drugsfda.json?search=sponsor_name:"Pfizer"&limit=100
```

### MyChem.info API / MyChem.info API

**Base URL:** `https://mychem.info/v1/query/{unii}`

Used for mapping UNII to ChEMBL IDs.

用于将 UNII 映射到 ChEMBL ID。

```bash
# Example query / 示例查询
https://mychem.info/v1/query/C2Q67M46N5
```

---

## Data Structure / 数据结构

### API Response Structure / API 响应结构

```json
{
  "meta": {
    "results": {
      "total": 123456,
      "skip": 0,
      "limit": 100
    }
  },
  "results": [
    {
      "application_number": "NDA020709",
      "products": [
        {
          "product_number": "001",
          "brand_name": "Lipitor",
          "generic_name": "Atorvastatin Calcium",
          "dosage_form": "TABLET",
          "route": "ORAL",
          "marketing_status": "Prescription",
          "approval_date": "19961217",
          "active_ingredients": [
            {
              "name": "ATORVASTATIN CALCIUM",
              "unii": "C2Q67M46N5",
              "strength": "10 mg"
            }
          ],
          "sponsor_name": "Pfizer Inc."
        }
      ],
      "submissions": [
        {
          "submission_number": "NDA020709",
          "submission_type": "Original",
          "submission_status": "Approved",
          "submission_date": "19960627",
          "review_priority": "Standard"
        }
      ]
    }
  ]
}
```

### Entity Structure / 实体结构

#### Approval Entity / 批准实体

```json
{
  "primary_id": "Approval-NDA020709",
  "identifiers": {
    "application_number": "NDA020709",
    "approval_type": "NDA"
  },
  "properties": {
    "application_number": "NDA020709",
    "approval_type": "NDA",
    "approval_date": "19961217",
    "tentative_approval_date": null,
    "approval_status": "Approved",
    "supplement_numbers": [],
    "submission_count": 1,
    "product_count": 1,
    "source": "Drugs@FDA",
    "api_version": "v1"
  },
  "entity_type": "regulatory:Approval"
}
```

#### Compound Entity / 化合物实体

```json
{
  "primary_id": "Compound-C2Q67M46N5",
  "identifiers": {
    "UNII": "C2Q67M46N5",
    "drug_name": "ATORVASTATIN CALCIUM"
  },
  "properties": {
    "unirot_id": "C2Q67M46N5",
    "drug_name": "ATORVASTATIN CALCIUM",
    "generic_name": "Atorvastatin Calcium",
    "chemical_type": "10 mg",
    "route_of_administration": "ORAL",
    "dosage_form": "TABLET",
    "strength": "10 mg",
    "source": "Drugs@FDA"
  },
  "entity_type": "rd:Compound"
}
```

### Relationship Structure / 关系结构

```json
{
  "relationship_type": "APPROVAL_FOR",
  "source_entity_id": "Approval-NDA020709",
  "target_entity_id": "Compound-C2Q67M46N5",
  "properties": {
    "approval_date": "19961217",
    "drug_name": "ATORVASTATIN CALCIUM",
    "data_source": "Drugs@FDA"
  },
  "source": "Drugs@FDA"
}
```

---

## Cross-Domain Integration / 跨域集成

### UNII to ChEMBL Mapping / UNII 到 ChEMBL 映射

The processor uses the MyChem.info API to map UNII identifiers to ChEMBL IDs:

处理器使用 MyChem.info API 将 UNII 标识符映射到 ChEMBL ID：

```python
# Example / 示例
UNII: C2Q67M46N5 → ChEMBL: CHEMBL1539
```

### Clinical Trial Linkage / 临床试验链接

The processor can link compounds to clinical trials via:

处理器可以通过以下方式将化合物链接到临床试验：

1. **Application Number** - FDA submissions often reference clinical trials
2. **Drug Name** - Matching intervention names in ClinicalTrials.gov

### Disease/Condition Mapping / 疾病/状况映射

Approved products can be linked to disease conditions through:

批准的产品可以通过以下方式链接到疾病状况：

1. **Indications** - From product labeling
2. **Therapeutic Areas** - From FDA classification

---

## Performance Considerations / 性能考虑

### Rate Limiting / 速率限制

The FDA openFDA API has rate limits. The processor uses conservative defaults:

FDA openFDA API 有速率限制。处理器使用保守的默认值：

- **Default:** 1 request/second / **默认：** 1 请求/秒
- **Recommended:** 2-4 requests/second for academic use / **推荐：** 学术使用 2-4 请求/秒
- **Maximum:** 240 requests/minute (4 requests/second) / **最大：** 240 请求/分钟 (4 请求/秒)

### Memory Usage / 内存使用

For large datasets, consider:

对于大型数据集，考虑：

1. **Batch Processing** - Process in smaller batches / **批处理** - 分批处理
2. **Incremental Updates** - Only fetch new or updated applications / **增量更新** - 仅获取新的或更新的申请
3. **Database Streaming** - Stream directly to Neo4j / **数据库流式传输** - 直接流式传输到 Neo4j

### Estimated Data Volume / 预估数据量

- **Total Applications:** ~40,000 approved products / **总申请数：** ~40,000 个批准产品
- **Processing Time:** ~2-4 hours for full download at 1 req/sec / **处理时间：** 1 请求/秒时完整下载约 2-4 小时
- **Storage:** ~500MB - 1GB for full dataset / **存储：** 完整数据集约 500MB - 1GB

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### 1. Rate Limit Errors / 速率限制错误

**Symptom / 症状:** HTTP 429 errors

**Solution / 解决方案:**

```python
# Increase delay / 增加延迟
config = {
    'extraction': {
        'rate_limit_per_second': 0.5,  # Slower / 更慢
        'rate_limit_delay': 2.0
    }
}
```

#### 2. Timeout Errors / 超时错误

**Symptom / 症状:** Request timeout errors

**Solution / 解决方案:**

```python
# Increase timeout / 增加超时时间
config = {
    'extraction': {
        'request_timeout': 60  # 60 seconds / 60 秒
    }
}
```

#### 3. No Results Returned / 没有返回结果

**Symptom / 症状:** Empty results list

**Possible Causes / 可能原因:**

1. Invalid search query / 无效的搜索查询
2. No matching applications / 没有匹配的申请
3. API endpoint issues / API 端点问题

**Solution / 解决方案:**

```python
# Verify query / 验证查询
# Try simpler search / 尝试更简单的搜索
raw_data = processor.fetch_by_brand_name("Aspirin")
```

#### 4. MyChem.info Mapping Failures / MyChem.info 映射失败

**Symptom / 症状:** No ChEMBL IDs mapped

**Solution / 解决方案:**

```python
# Disable MyChem.info API / 禁用 MyChem.info API
config = {
    'extraction': {
        'use_mychem_api': False
    }
}
```

### Logging / 日志记录

Enable verbose logging for debugging:

启用详细日志以进行调试：

```bash
python -m processors.drugsatfda_processor --mode all --verbose
```

Or in Python: / 或在 Python 中：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Testing / 测试

### Run Test Suite / 运行测试套件

```bash
# Run all tests / 运行所有测试
python scripts/test_drugsatfda_processor.py
```

### Test Coverage / 测试覆盖

The test suite includes: / 测试套件包括：

1. Basic data fetching / 基本数据获取
2. Data transformation / 数据转换
3. Validation / 验证
4. Query by brand name / 按品牌名查询
5. Query by application number / 按申请号查询
6. Cross-domain mapping / 跨域映射
7. Result saving / 结果保存
8. Deduplication / 去重
9. Error handling / 错误处理
10. Enum types / 枚举类型

---

## Output Files / 输出文件

### Entity Files / 实体文件

- `drugsatfda_regulatory_approvals_*.json` - Approval entities / 批准实体
- `drugsatfda_regulatory_submissions_*.json` - Submission entities / 提交实体
- `drugsatfda_rd_compounds_*.json` - Compound entities / 化合物实体
- `drugsatfda_rd_drugproducts_*.json` - DrugProduct entities / 药物产品实体
- `drugsatfda_regulatory_regulatoryagencies_*.json` - RegulatoryAgency entities / 监管机构实体

### Relationship Files / 关系文件

- `drugsatfda_relationships_*.json` - All relationships / 所有关系

### Summary Files / 摘要文件

- `drugsatfda_summary_*.json` - Processing statistics / 处理统计信息

---

## References / 参考资料

### FDA Resources / FDA 资源

- **Drugs@FDA Homepage:** https://www.accessdata.fda.gov/scripts/cder/daf/
- **openFDA Documentation:** https://open.fda.gov/drugs/drugsfda/
- **API Documentation:** https://api.fda.gov/

### Cross-Reference APIs / 交叉引用 APIs

- **MyChem.info:** https://mychem.info/
- **ClinicalTrials.gov API:** https://clinicaltrials.gov/api/v2/

### UNII Information / UNII 信息

- **UNII Codes:** https://fda.gov/drugs/drug-approvals-and-databases/unii-codes

---

## Changelog / 变更日志

### Version 1.0 / 版本 1.0

- Initial release / 初始版本
- Support for Drugs@FDA API v1 / 支持 Drugs@FDA API v1
- Cross-domain integration with ChEMBL and ClinicalTrials.gov / 与 ChEMBL 和 ClinicalTrials.gov 的跨域集成
- Comprehensive entity and relationship extraction / 全面的实体和关系提取
- Flexible query options / 灵活的查询选项
- Robust error handling and retry logic / 健壮的错误处理和重试逻辑

---

## Support / 支持

For issues, questions, or contributions:

对于问题、疑问或贡献：

1. **Documentation Issues:** Check this document first / **文档问题：** 首先检查本文档
2. **API Issues:** Check FDA API status / **API 问题：** 检查 FDA API 状态
3. **Code Issues:** Review test output / **代码问题：** 检查测试输出
4. **Feature Requests:** Submit to project tracker / **功能请求：** 提交到项目跟踪器

---

**Last Updated / 最后更新:** 2026-02-08

**Version / 版本:** 1.0

**Language / 语言:** English / 中文 (Bilingual / 双语)
