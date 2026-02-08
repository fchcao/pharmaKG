# FDA FAERS Adverse Events Processor Documentation
# FDA FAERS 不良事件处理器文档

**Version / 版本:** v1.0
**Last Updated / 最后更新:** 2026-02-08

---

## Table of Contents / 目录

- [Overview / 概述](#overview--概述)
- [Features / 功能特性](#features--功能特性)
- [Data Source / 数据源](#data-source--数据源)
- [Entity Models / 实体模型](#entity-models--实体模型)
- [Relationship Models / 关系模型](#relationship-models--关系模型)
- [Installation / 安装配置](#installation--安装配置)
- [Usage / 使用方法](#usage--使用方法)
- [CLI Reference / 命令行接口](#cli-reference--命令行接口)
- [Code Examples / 代码示例](#code-examples--代码示例)
- [File Format / 文件格式](#file-format--文件格式)
- [Troubleshooting / 故障排除](#troubleshooting--故障排除)

---

## Overview / 概述

**FAERSProcessor** extracts adverse event data from the FDA Adverse Event Reporting System (FAERS). FAERS contains spontaneous reports submitted by healthcare professionals, consumers, and manufacturers about adverse events and medication errors.

**FAERSProcessor** 从 FDA 不良事件报告系统 (FAERS) 提取不良事件数据。FAERS 包含由医疗保健专业人员、消费者和制造商提交的关于不良事件和用药错误的自发报告。

### Key Features / 主要功能

- ✅ **Quarterly Data Processing / 季度数据处理** - Process FAERS quarterly ASCII/CSV files
- ✅ **Multi-File Integration / 多文件集成** - Combine DEMO, DRUG, REAC, and OUTC files
- ✅ **MedDRA Coding / MedDRA 编码** - Extract MedDRA-coded adverse reactions
- ✅ **Drug Characterization / 药物特征化** - Identify suspect vs. concomitant drugs
- ✅ **Deduplication / 去重处理** - Automatic deduplication by safetyreport_id
- ✅ **Cross-Domain Mapping / 交叉域映射** - Map drug names to ChEMBL compounds
- ✅ **Data Quality Validation / 数据质量验证** - Validate MedDRA codes and required fields
- ✅ **Batch Processing / 批处理** - Support for large-scale data processing

---

## Features / 功能特性

### 1. Data Extraction Features / 数据提取功能

#### 1.1 Entity Types / 实体类型

| Entity Type / 实体类型 | Description / 描述 | Key Properties / 主要属性 |
|------------------------|--------------------|---------------------------|
| `clinical:AdverseEvent` | Individual adverse event report | safetyreport_id, case_number, receive_date, serious, sex, age, weight, reporter_type |
| `clinical:Condition` | Adverse reactions (MedDRA-coded) | meddra_code, meddra_term, condition_type |
| `rd:Compound` | Suspect and concomitant drugs | drug_name, medicinal_product, dose, frequency, route, drug_role |

#### 1.2 Relationship Types / 关系类型

| Relationship Type / 关系类型 | Source / 来源 | Target / 目标 | Description / 描述 |
|------------------------------|---------------|---------------|---------------------|
| `ASSOCIATED_WITH` | AdverseEvent | Condition | Links adverse event to reported reactions |
| `CAUSED_ADVERSE_EVENT` | Compound | AdverseEvent | Links suspect drugs to adverse events |

#### 1.3 Cross-Domain Relationships / 交叉域关系

| Relationship Type / 关系类型 | Source / 来源 | Target / 目标 | Description / 描述 |
|------------------------------|---------------|---------------|---------------------|
| `TESTED_IN_CLINICAL_TRIAL` | Compound (ChEMBL) | AdverseEvent | Maps FAERS drugs to ChEMBL compounds |

---

## Data Source / 数据源

### FAERS Data Files / FAERS 数据文件

The FDA releases FAERS data quarterly in ASCII/CSV format. Each quarter includes:

FDA 每季度以 ASCII/CSV 格式发布 FAERS 数据。每个季度包括：

1. **DEMO*.txt** - Demographic and administrative information
2. **DRUG*.txt** - Drug information for all reported drugs
3. **REAC*.txt** - Adverse reactions coded with MedDRA terms
4. **OUTC*.txt** - Patient outcomes
5. **RPSR*.txt** - Report source information
6. **THER*.txt** - Drug therapy dates
7. **INDI*.txt** - Drug indications

### Accessing FAERS Data / 获取 FAERS 数据

**Download Location / 下载位置:**
https://fis.fda.gov/sense/app/d10be4bb-5284-4fc1-8f92-8b5f4f763062/page/FAERS/

**Data Format / 数据格式:** ASCII text files with `$` delimiter
**Update Frequency / 更新频率:** Quarterly
**Data Volume / 数据量:** ~2 million reports per year

---

## Entity Models / 实体模型

### clinical:AdverseEvent

```python
{
    "primary_id": "AdverseEvent-FAERS-2024-001",
    "identifiers": {
        "safetyreport_id": "FAERS-2024-001",
        "case_number": "CASE001"
    },
    "properties": {
        "safetyreport_id": "FAERS-2024-001",
        "case_number": "CASE001",
        "receive_date": "2024-01-01",
        "serious": true,
        "sex": "M",
        "age": 55.0,
        "age_unit": "Year",
        "weight": 75.5,
        "weight_unit": "kg",
        "report_type": "1.0",
        "reporter_type": "Physician",
        "outcomes": ["Recovering"],
        "data_source": "FDA FAERS"
    },
    "entity_type": "clinical:AdverseEvent"
}
```

### clinical:Condition

```python
{
    "primary_id": "Condition-10009106",
    "identifiers": {
        "meddra_code": "10009106",
        "name": "Angioedema"
    },
    "properties": {
        "meddra_code": "10009106",
        "meddra_term": "Angioedema",
        "condition_type": "adverse_reaction",
        "data_source": "FDA FAERS"
    },
    "entity_type": "clinical:Condition"
}
```

### rd:Compound

```python
{
    "primary_id": "Compound-LISINOPRIL",
    "identifiers": {
        "name": "LISINOPRIL",
        "drug_seq": "1"
    },
    "properties": {
        "drug_name": "LISINOPRIL",
        "medicinal_product": "Lisinopril 10mg",
        "dose": "10 mg",
        "frequency": "Daily",
        "route": "Oral",
        "drug_role": "Suspect",
        "data_source": "FDA FAERS"
    },
    "entity_type": "rd:Compound"
}
```

---

## Relationship Models / 关系模型

### ASSOCIATED_WITH

```python
{
    "relationship_type": "ASSOCIATED_WITH",
    "source_entity_id": "AdverseEvent-FAERS-2024-001",
    "target_entity_id": "Condition-10009106",
    "properties": {
        "drug_seq": "1",
        "data_source": "FDA FAERS"
    },
    "source": "FDA FAERS"
}
```

### CAUSED_ADVERSE_EVENT

```python
{
    "relationship_type": "CAUSED_ADVERSE_EVENT",
    "source_entity_id": "Compound-LISINOPRIL",
    "target_entity_id": "AdverseEvent-FAERS-2024-001",
    "properties": {
        "drug_characterization": "1",
        "drug_seq": "1",
        "data_source": "FDA FAERS"
    },
    "source": "FDA FAERS"
}
```

---

## Installation / 安装配置

### Requirements / 环境要求

- Python 3.8+
- Existing PharmaKG infrastructure
- Sufficient disk space for FAERS data files

### Installation Steps / 安装步骤

1. **Verify processor file / 验证处理器文件**

```bash
ls -la processors/faers_processor.py
```

2. **No additional dependencies required / 无需额外依赖**

The FAERS processor uses only standard Python libraries.

3. **Prepare data directory / 准备数据目录**

```bash
mkdir -p data/sources/faers
```

4. **Download FAERS data / 下载 FAERS 数据**

Download quarterly FAERS data files from the FDA website and extract them to `data/sources/faers/`.

---

## Usage / 使用方法

### Basic Usage / 基本使用

#### 1. Create Processor Instance / 创建处理器实例

```python
from processors.faers_processor import FAERSProcessor

# Use default configuration
processor = FAERSProcessor()

# Use custom configuration
config = {
    'extraction': {
        'batch_size': 1000,
        'max_reports': 10000,
        'include_non_serious': False,
        'map_to_chembl': True
    }
}
processor = FAERSProcessor(config)
```

#### 2. Process FAERS Data / 处理 FAERS 数据

```python
# Process all FAERS files in a directory
result = processor.process('/path/to/faers/data')

# Check result
print(f"Status: {result.status}")
print(f"Adverse events: {processor.stats.adverse_events_extracted}")
print(f"Conditions: {processor.stats.conditions_extracted}")
print(f"Compounds: {processor.stats.compounds_extracted}")
```

#### 3. Access Extracted Data / 访问提取的数据

```python
# Entities are saved to JSON files
entities = result.entities

# Access by type
adverse_events = entities['clinical:AdverseEvent']
conditions = entities['clinical:Condition']
compounds = entities['rd:Compound']
```

---

## CLI Reference / 命令行接口

### Basic Syntax / 基本语法

```bash
python -m processors.faers_processor SOURCE_PATH [OPTIONS]
```

### Options / 选项

| Option / 选项 | Type / 类型 | Description / 描述 |
|---------------|-------------|---------------------|
| `source_path` | string | Path to FAERS data directory (required) |
| `--max-reports` | int | Maximum number of reports to process |
| `--batch-size` | int | Batch size for processing (default: 1000) |
| `--include-non-serious` | flag | Include non-serious adverse events |
| `--no-dedup` | flag | Disable deduplication by safetyreport_id |
| `--no-cross-domain` | flag | Disable cross-domain mapping to ChEMBL |
| `--output` | string | Custom output directory |
| `--verbose` | flag | Enable verbose output |

### Usage Examples / 使用示例

```bash
# Process FAERS data (serious events only)
python -m processors.faers_processor /path/to/faers/data

# Process with report limit
python -m processors.faers_processor /path/to/faers/data --max-reports 50000

# Include non-serious events
python -m processors.faers_processor /path/to/faers/data --include-non-serious

# Custom output directory
python -m processors.faers_processor /path/to/faers/data --output /custom/output
```

---

## Code Examples / 代码示例

### Example 1: Process Quarterly Data / 示例 1：处理季度数据

```python
from processors.faers_processor import FAERSProcessor
import logging

logging.basicConfig(level=logging.INFO)

config = {
    'extraction': {
        'batch_size': 5000,
        'max_reports': None,  # Process all
        'include_non_serious': False,  # Serious only
        'map_to_chembl': True
    }
}

processor = FAERSProcessor(config)

# Process Q1 2024 data
result = processor.process('data/sources/faers/2024Q1')

if result.status.value == 'completed':
    print(f"Processed {processor.stats.adverse_events_extracted} adverse events")
    print(f"Found {processor.stats.conditions_extracted} unique conditions")
    print(f"Identified {processor.stats.compounds_extracted} compounds")
```

### Example 2: Analyze Drug Safety Signals / 示例 2：分析药物安全信号

```python
from processors.faers_processor import FAERSProcessor

processor = FAERSProcessor()

# Process data
result = processor.process('data/sources/faers')

# Get relationships
relationships = result.relationships

# Find CAUSED_ADVERSE_EVENT relationships (suspect drugs)
causation_rels = [
    rel for rel in relationships
    if rel['relationship_type'] == 'CAUSED_ADVERSE_EVENT'
]

# Analyze drug-adverse event pairs
from collections import Counter
drug_event_pairs = Counter(
    (rel['source_entity_id'], rel['target_entity_id'])
    for rel in causation_rels
)

# Find most common pairs
for (drug, event), count in drug_event_pairs.most_common(10):
    print(f"{drug} -> {event}: {count} reports")
```

### Example 3: Cross-Domain Analysis / 示例 3：交叉域分析

```python
from processors.faers_processor import FAERSProcessor

config = {
    'extraction': {
        'map_to_chembl': True
    }
}

processor = FAERSProcessor(config)

result = processor.process('data/sources/faers')

# Find cross-domain relationships
cross_domain_rels = [
    rel for rel in result.relationships
    if rel['source'] == 'FDA FAERS-ChEMBL-Mapping'
]

print(f"Found {len(cross_domain_rels)} cross-domain mappings")
```

---

## File Format / 文件格式

### DEMO File Format / DEMO 文件格式

| Field / 字段 | Description / 描述 |
|--------------|--------------------|
| safetyreportid | Unique identifier for the adverse event report |
| caseid | Case number |
| receivedate | Date report was received (YYYYMMDD) |
| serious | Seriousness criterion (Y/N) |
| patientsex | Patient sex (M/F) |
| patientage | Patient age |
| patientageunit | Age unit (Year, Month, Day, Decade) |
| patientweight | Patient weight |
| patientweightunit | Weight unit (kg, lb) |
| safetyreportversion | Report version |
| reportertype | Reporter type (1-6) |

### DRUG File Format / DRUG 文件格式

| Field / 字段 | Description / 描述 |
|--------------|--------------------|
| safetyreportid | Link to adverse event report |
| drugseq | Drug sequence number |
| drugcharacterization | 1=Suspect, 2=Concomitant, 3=Interacting |
| drugname | Drug name |
| medicinalproduct | Product name |
| drugdosagetxt | Dose text |
| drugadministration | Administration frequency |
| drugroute | Route of administration |

### REAC File Format / REAC 文件格式

| Field / 字段 | Description / 描述 |
|--------------|--------------------|
| safetyreportid | Link to adverse event report |
| drugcharacterization | Associated drug characterization |
| reactionmeddrapt | MedDRA code for reaction |
| reactionmeddraversionpt | MedDRA term for reaction |

### OUTC File Format / OUTC 文件格式

| Field / 字段 | Description / 描述 |
|--------------|--------------------|
| safetyreportid | Link to adverse event report |
| patientoutcome | 1=Recovered, 2=Recovering, 3=Not Recovered, 4=Recovered with Sequelae, 5=Fatal, 6=Unknown |

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### 1. File Not Recognized / 文件未识别

**Problem / 问题:**
```
No FAERS files found in directory
```

**Solution / 解决方案:**
- Verify files are named correctly (DEMO*.txt, DRUG*.txt, etc.)
- Check file permissions
- Ensure correct directory path

#### 2. Memory Issues / 内存问题

**Problem / 问题:**
```
MemoryError: Cannot allocate memory
```

**Solution / 解决方案:**
- Reduce `batch_size` in configuration
- Set `max_reports` limit
- Process quarters separately

#### 3. Encoding Errors / 编码错误

**Problem / 问题:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```

**Solution / 解决方案:**
- The processor uses `errors='ignore'` for encoding issues
- Check if files are corrupted during download

---

## Data Quality Notes / 数据质量说明

### FAERS Data Limitations / FAERS 数据限制

1. **No Causality Assessment / 无因果评估** - FAERS reports do not prove causation
2. **Underreporting / 报告不足** - Not all adverse events are reported
3. **Duplicate Reports / 重复报告** - Same event may be reported multiple times
4. **Incomplete Data / 数据不完整** - Many fields may be missing or unknown
5. **No Denominator / 无分母数据** - Cannot calculate incidence rates

### Best Practices / 最佳实践

1. Always analyze FAERS data with clinical context
2. Consider reporting rates and not just raw counts
3. Use statistical methods to detect safety signals
4. Cross-reference with other data sources
5. Be aware of the limitations of spontaneous reporting systems

---

## Output Files / 输出文件

### Generated Files / 生成的文件

```
data/
├── processed/
│   ├── entities/
│   │   └── faers/
│   │       ├── faers_adverse_events_YYYYMMDD.json
│   │       ├── faers_conditions_YYYYMMDD.json
│   │       └── faers_compounds_YYYYMMDD.json
│   ├── relationships/
│   │   └── faers/
│   │       └── faers_relationships_YYYYMMDD.json
│   └── documents/
│       └── faers/
│           └── faers_summary_YYYYMMDD.json
```

---

## Testing / 测试

Run the test suite / 运行测试套件:

```bash
python scripts/test_faers_processor.py
```

The test suite includes:
- Entity creation tests
- Data parsing tests
- Transform functionality tests
- Full workflow tests

---

## References / 参考资料

- [FDA FAERS Public Dashboard](https://fis.fda.gov/sense/app/d10be4bb-5284-4fc1-8f92-8b5f4f763062/page/FAERS/)
- [FAERS Data Format Documentation](https://fis.fda.gov/content/FAERS/Data-Format-Documentation.zip)
- [MedDRA Terminology](https://www.meddra.org/)
- [PharmaKG Project Documentation](https://docs.pharmakg.org)

---

**Document Version / 文档版本:** v1.0
**Last Updated / 最后更新:** 2026-02-08
**Maintainer / 维护者:** PharmaKG Development Team
