# Phase 3 FDA Data Processors - Summary
# Phase 3 FDA 数据处理器 - 总结

**Created:** 2026-02-08
**Version:** v1.0

---

## Overview / 概述

This document summarizes the two FDA data processors created for Phase 3 of the PharmaKG data collection plan:
1. FDA FAERS Adverse Events Processor
2. FDA Drug Shortages Database Processor

本文档总结了为 PharmaKG 数据收集计划 Phase 3 创建的两个 FDA 数据处理器：
1. FDA FAERS 不良事件处理器
2. FDA 药物短缺数据库处理器

---

## Created Files / 创建的文件

### 1. FAERS Adverse Events Processor / FAERS 不良事件处理器

**File:** `/root/autodl-tmp/pj-pharmaKG/processors/faers_processor.py`
**Size:** ~40 KB
**Lines:** ~1,200

#### Key Features / 主要功能

- Processes FAERS quarterly ASCII/CSV files
- Handles 7 file types: DEMO, DRUG, REAC, OUTC, RPSR, THER, INDI
- Extracts adverse events, conditions (reactions), and compounds (drugs)
- Maps drug names to ChEMBL compounds
- Automatic deduplication by safetyreport_id
- Support for serious-only filtering

#### Entity Types / 实体类型

- `clinical:AdverseEvent` - Individual adverse event reports
- `clinical:Condition` - MedDRA-coded adverse reactions
- `rd:Compound` - Suspect and concomitant drugs

#### Relationship Types / 关系类型

- `ASSOCIATED_WITH` - AdverseEvent → Condition
- `CAUSED_ADVERSE_EVENT` - Compound → AdverseEvent

### 2. Drug Shortages Database Processor / 药物短缺数据库处理器

**File:** `/root/autodl-tmp/pj-pharmaKG/processors/shortage_processor.py`
**Size:** ~43 KB
**Lines:** ~1,300

#### Key Features / 主要功能

- Fetches data from FDA Drug Shortages API
- Supports search, filtering, and pagination
- Extracts shortages, compounds, manufacturers, and facilities
- Maps generic names to ChEMBL via UNII
- Automatic deduplication by shortage_id
- Built-in rate limiting and retry logic

#### Entity Types / 实体类型

- `sc:DrugShortage` - Drug shortage records
- `rd:Compound` - Affected drug products
- `sc:Manufacturer` - Manufacturing companies
- `sc:Facility` - Manufacturing facilities

#### Relationship Types / 关系类型

- `EXPERIENCES_SHORTAGE` - Compound → DrugShortage
- `CAUSED_BY_QUALITY_ISSUE` - DrugShortage → Manufacturer
- `HAS_FACILITY` - Manufacturer → Facility
- `REPORTED_TO_AGENCY` - DrugShortage → RegulatoryAgency

---

## Test Scripts / 测试脚本

### 1. FAERS Test Script / FAERS 测试脚本

**File:** `/root/autodl-tmp/pj-pharmaKG/scripts/test_faers_processor.py`
**Size:** ~13 KB

**Tests:**
- Full workflow test with mock data
- Entity creation tests
- Data parsing tests
- Statistics tracking

**Usage:**
```bash
python scripts/test_faers_processor.py
```

### 2. Shortage Test Script / 短缺测试脚本

**File:** `/root/autodl-tmp/pj-pharmaKG/scripts/test_shortage_processor.py`
**Size:** ~17 KB

**Tests:**
- Transform functionality with mock API response
- Entity creation tests
- Data parsing tests
- API method tests (mocked)
- Cross-domain mapping tests

**Usage:**
```bash
python scripts/test_shortage_processor.py
```

---

## Documentation / 文档

### 1. FAERS Processor Documentation / FAERS 处理器文档

**File:** `/root/autodl-tmp/pj-pharmaKG/docs/FAERS_PROCESSOR.md`
**Size:** ~17 KB
**Sections:**
- Overview and features
- Data source information
- Entity and relationship models
- Installation and usage
- CLI reference
- Code examples
- File format specifications
- Troubleshooting

### 2. Shortage Processor Documentation / 短缺处理器文档

**File:** `/root/autodl-tmp/pj-pharmaKG/docs/SHORTAGE_PROCESSOR.md`
**Size:** ~17 KB
**Sections:**
- Overview and features
- API endpoint information
- Entity and relationship models
- Installation and usage
- CLI reference
- Code examples
- API response format
- Troubleshooting

---

## CLI Usage Examples / CLI 使用示例

### FAERS Processor / FAERS 处理器

```bash
# Process FAERS quarterly data files
python -m processors.faers_processor /path/to/faers/data

# Process with limit
python -m processors.faers_processor /path/to/faers/data --max-reports 10000

# Include non-serious events
python -m processors.faers_processor /path/to/faers/data --include-non-serious

# Custom output directory
python -m processors.faers_processor /path/to/faers/data --output /custom/path
```

### Shortage Processor / 短缺处理器

```bash
# Fetch all drug shortages
python -m processors.shortage_processor --mode all

# Fetch by drug name
python -m processors.shortage_processor --mode search --query "epinephrine"

# Fetch current shortages only
python -m processors.shortage_processor --mode status --status "Current"

# Fetch with limit
python -m processors.shortage_processor --mode all --limit 50
```

---

## Output Structure / 输出结构

### FAERS Output / FAERS 输出

```
data/processed/
├── entities/faers/
│   ├── faers_adverse_events_YYYYMMDD.json
│   ├── faers_conditions_YYYYMMDD.json
│   └── faers_compounds_YYYYMMDD.json
├── relationships/faers/
│   └── faers_relationships_YYYYMMDD.json
└── documents/faers/
    └── faers_summary_YYYYMMDD.json
```

### Shortage Output / 短缺输出

```
data/processed/
├── entities/shortages/
│   ├── shortages_shortages_YYYYMMDD.json
│   ├── shortages_compounds_YYYYMMDD.json
│   ├── shortages_manufacturers_YYYYMMDD.json
│   └── shortages_facilities_YYYYMMDD.json
├── relationships/shortages/
│   └── shortages_relationships_YYYYMMDD.json
└── documents/shortages/
    └── shortages_summary_YYYYMMDD.json
```

---

## Cross-Domain Mapping / 交叉域映射

Both processors support cross-domain mapping to ChEMBL compounds:

两个处理器都支持到 ChEMBL 化合物的交叉域映射：

### FAERS / FAERS
- Maps drug names (from DRUG files) to ChEMBL IDs
- Uses fuzzy matching for drug name normalization
- Creates `TESTED_IN_CLINICAL_TRIAL` relationships

### Shortage / 短缺
- Maps generic names to ChEMBL via UNII
- Creates `EXPERIENCES_SHORTAGE` relationships to ChEMBL compounds

**Note:** The actual ChEMBL mapping implementation requires additional data sources or API access.
**注:** 实际的 ChEMBL 映射实现需要额外的数据源或 API 访问。

---

## Common Features / 共同特性

Both processors share the following features:

两个处理器共享以下特性：

1. **Inherit from BaseProcessor / 继承自 BaseProcessor**
   - Consistent API with other PharmaKG processors
   - Standard scan, extract, transform, validate workflow
   - Integrated with PharmaKG infrastructure

2. **Bilingual Documentation / 双语文档**
   - English and Chinese documentation
   - Comments in code support both languages

3. **Comprehensive Error Handling / 全面的错误处理**
   - Retry logic for API requests (Shortage)
   - Graceful handling of malformed records (FAERS)
   - Detailed error and warning tracking

4. **Statistics Tracking / 统计跟踪**
   - Processing metrics
   - Entity/relationship counts
   - Error and warning logs
   - Processing time measurements

5. **CLI Support / CLI 支持**
   - Command-line interface for easy execution
   - Multiple operation modes
   - Configurable options

6. **Deduplication / 去重处理**
   - Automatic deduplication by primary identifier
   - Configurable enable/disable

7. **Batch Processing / 批处理**
   - Support for large datasets
   - Configurable batch sizes
   - Progress tracking

---

## Next Steps / 下一步

To use these processors in production:

要在生产环境中使用这些处理器：

1. **Data Acquisition / 数据获取**
   - Download FAERS quarterly data files
   - Ensure API access for Drug Shortages Database

2. **Cross-Domain Mapping Implementation / 交叉域映射实现**
   - Implement ChEMBL mapping logic
   - Add UNII lookup functionality
   - Create mapping tables or API integrations

3. **Integration with ETL Pipeline / 与 ETL 管道集成**
   - Add to main ETL workflow
   - Schedule periodic updates
   - Set up monitoring and alerts

4. **Testing / 测试**
   - Run test scripts to verify functionality
   - Test with real data samples
   - Validate output quality

5. **Documentation / 文档**
   - Review processor documentation
   - Update with any local configurations
   - Share with team members

---

## References / 参考资料

- **FAERS Data Source:** https://fis.fda.gov/sense/app/d10be4bb-5284-4fc1-8f92-8b5f4f763062/page/FAERS/
- **Drug Shortages API:** https://api.fda.gov/drug/shortages.json
- **PharmaKG Documentation:** `/root/autodl-tmp/pj-pharmaKG/docs/`

---

**Document Version / 文档版本:** v1.0
**Created / 创建日期:** 2026-02-08
**Maintainer / 维护者:** PharmaKG Development Team
