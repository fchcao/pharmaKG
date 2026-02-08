# UniProt API Processor Documentation

## UniProt API 处理器文档

**Version**: v1.0
**Date**: 2024-01-08
**Status**: Phase 1 Implementation

---

## Table of Contents / 目录

- [Overview / 概述](#overview--概述)
- [Features / 功能特性](#features--功能特性)
- [Architecture / 架构](#architecture--架构)
- [Installation / 安装](#installation--安装)
- [Usage / 使用方法](#usage--使用方法)
- [API Endpoints / API端点](#api-endpoints--api端点)
- [Data Model / 数据模型](#data-model--数据模型)
- [Configuration / 配置](#configuration--配置)
- [Output Format / 输出格式](#output-format--输出格式)
- [Performance / 性能](#performance--性能)
- [Troubleshooting / 故障排除](#troubleshooting--故障排除)

---

## Overview / 概述

### English

The **UniProt Processor** is a Python-based data processor that fetches and enhances target protein data from the [UniProt REST API](https://rest.uniprot.org/uniprotkb/). It integrates with the PharmaKG knowledge graph to provide comprehensive target information including:

- Enhanced target properties (protein names, gene symbols, sequences)
- Gene Ontology (GO) annotations (molecular function, biological process, cellular component)
- Disease associations
- Subcellular localization
- Druggability classification

### 中文

**UniProt 处理器**是一个基于 Python 的数据处理器，从 [UniProt REST API](https://rest.uniprot.org/uniprotkb/) 获取并增强靶点蛋白数据。它与 PharmaKG 知识图谱集成，提供全面的靶点信息，包括：

- 增强的靶点属性（蛋白名称、基因符号、序列）
- 基因本体（GO）注释（分子功能、生物过程、细胞组分）
- 疾病关联
- 亚细胞定位
- 药物可靶向性分类

---

## Features / 功能特性

### Core Features / 核心功能

#### 1. Batch Processing / 批量处理
- Process multiple UniProt IDs in batches
- Configurable batch size (default: 100)
- Efficient API request handling

#### 2. Organism Filtering / 生物体过滤
- Filter by organism taxonomy ID:
  - Human (9606)
  - Mouse (10090)
  - Rat (10116)
- Search by organism with custom queries

#### 3. Response Caching / 响应缓存
- SQLite-based local caching
- Reduces duplicate API requests
- Configurable cache location

#### 4. Rate Limiting / 速率限制
- Respectful API usage (default: 10 req/s)
- Configurable rate limits
- Exponential backoff for retries

#### 5. Progress Tracking / 进度跟踪
- Detailed metrics collection
- API request counting
- Cache hit tracking
- Processing time monitoring

#### 6. Error Handling / 错误处理
- Automatic retry with exponential backoff
- Graceful degradation on API failures
- Comprehensive error logging

### Advanced Features / 高级功能

#### GO Annotation Extraction / GO 注释提取
- Molecular Function (分子功能)
- Biological Process (生物过程)
- Cellular Component (细胞组分)

#### Disease Association Extraction / 疾病关联提取
- Disease associations (疾病关联)
- Biomarker relationships (生物标志物关系)
- Disease identifiers (MIM, OMIM, DOID, MeSH)

#### Druggability Classification / 药物可靶向性分类
- DrugBank target detection
- Target class inference
- Evidence collection

---

## Architecture / 架构

### Class Structure / 类结构

```
UniProtProcessor (BaseProcessor)
├── Configuration
│   └── UniProtExtractionConfig
├── HTTP Management
│   ├── Session management
│   ├── Retry strategy
│   └── Rate limiting
├── Cache Management
│   ├── SQLite backend
│   └── Cache operations
├── Data Extraction
│   ├── Single entry fetch
│   ├── Batch fetch
│   └── Stream endpoint
├── Data Transformation
│   ├── Target entity creation
│   ├── Disease entity creation
│   └── Relationship extraction
└── Output Generation
    ├── Entity files
    ├── Relationship files
    └── Summary statistics
```

### Processing Flow / 处理流程

```
Input (UniProt IDs or Organism Search)
    ↓
[1] Read/Scan Input
    ↓
[2] Check Cache
    ↓ (Cache Miss)
[3] Fetch from UniProt API
    ↓
[4] Transform to KG Format
    ↓
[5] Validate Data
    ↓
[6] Save Output Files
    ↓
Output (JSON files)
```

---

## Installation / 安装

### Prerequisites / 先决条件

```bash
# Python 3.8+
python3 --version

# Required packages
pip install requests urllib3
```

### Project Setup / 项目设置

```bash
# Navigate to project directory
cd /root/autodl-tmp/pj-pharmaKG

# Activate conda environment
conda activate pharmakg-api

# Install dependencies (if needed)
pip install requests urllib3
```

### File Structure / 文件结构

```
pharmakg/
├── processors/
│   ├── base.py                    # Base processor class
│   └── uniprot_processor.py       # UniProt processor
├── scripts/
│   └── test_uniprot_processor.py  # Test script
├── data/
│   ├── cache/
│   │   └── uniprot_cache.db       # Local cache
│   └── processed/
│       └── documents/
│           └── uniprot/           # Output directory
└── docs/
    └── UNIPROT_PROCESSOR.md       # This documentation
```

---

## Usage / 使用方法

### Command Line Interface / 命令行接口

#### 1. File Mode / 文件模式

Process a list of UniProt IDs from a file:

```bash
# Basic usage
python -m processors.uniprot_processor /path/to/uniprot_ids.txt

# With custom output directory
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --output /custom/output

# With specific limits
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --batch-size 50 --rate-limit 15.0
```

**Input File Format / 输入文件格式:**

```
# Uniprot ID file (one per line)
P04637
P08253
P35354
P00734
P10275
```

#### 2. Organism Search Mode / 生物体搜索模式

Search and fetch entries by organism:

```bash
# Human proteins (reviewed only)
python -m processors.uniprot_processor --organism human --limit 100

# Mouse proteins with custom query
python -m processors.uniprot_processor --organism mouse --query "kinase" --limit 50

# All organisms including unreviewed
python -m processors.uniprot_processor --organism all --min-quality all --limit 500
```

#### 3. Advanced Options / 高级选项

```bash
# Disable caching
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --no-cache

# Exclude GO annotations
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --no-go

# Exclude disease associations
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --no-diseases

# Verbose logging
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --verbose
```

### Python API / Python 接口

#### Basic Usage / 基本使用

```python
from pathlib import Path
from processors.uniprot_processor import UniProtProcessor, UniProtExtractionConfig

# Create configuration
config = {
    'extraction': {
        'batch_size': 100,
        'rate_limit': 10.0,
        'cache_enabled': True,
        'include_go_annotations': True,
        'include_diseases': True
    }
}

# Create processor
processor = UniProtProcessor(config)

# Process file
result = processor.process(
    source_path=Path('/path/to/uniprot_ids.txt'),
    output_to=Path('/custom/output'),
    save_intermediate=True
)

# Check results
print(f"Status: {result.status.value}")
print(f"Entities: {result.metrics.entities_extracted}")
print(f"Relationships: {result.metrics.relationships_extracted}")
```

#### Organism Search / 生物体搜索

```python
from processors.uniprot_processor import UniProtProcessor, OrganismFilter

# Create processor
processor = UniProtProcessor()

# Search by organism
uniprot_data = processor.fetch_by_organism(
    organism=OrganismFilter.HUMAN,
    limit=100,
    query="kinase"
)

# Transform data
raw_data = {
    'targets': uniprot_data,
    'source_file': 'organism_search_human',
    'extraction_timestamp': '2024-01-01T00:00:00'
}

transformed = processor.transform(raw_data)
validated = processor.validate(transformed)
```

### Testing / 测试

```bash
# Run all tests
python scripts/test_uniprot_processor.py

# Test specific functions
python -c "from scripts.test_uniprot_processor import test_api_endpoints; test_api_endpoints()"
```

---

## API Endpoints / API端点

### UniProt REST API / UniProt REST API

The processor uses the following UniProt REST API endpoints:

#### 1. Single Entry / 单个条目

```
GET /uniprotkb/{accession}
```

**Example / 示例:**
```
https://rest.uniprot.org/uniprotkb/P04637
```

#### 2. Search Endpoint / 搜索端点

```
GET /uniprotkb/search?query={query}&format=json&size={size}
```

**Example / 示例:**
```
https://rest.uniprot.org/uniprotkb/search?query=organism_id:9606+AND+reviewed:true&format=json&size=100
```

#### 3. Stream Endpoint / 流式端点

```
POST /uniprotkb/stream
```

Used for bulk fetching of multiple entries.

### Rate Limiting / 速率限制

- **Default Limit**: 10 requests per second
- **Recommended**: Stay under 20 req/s for sustained use
- **Unlimited**: No hard limit for reasonable use

---

## Data Model / 数据模型

### Target Entity / 靶点实体

```json
{
  "primary_id": "P04637",
  "identifiers": {
    "UniProt": "P04637",
    "UniProtKB": "UniProtKB-P04637",
    "GeneSymbol": "TP53",
    "GeneID": "7157"
  },
  "properties": {
    "name": "Cellular tumor antigen p53",
    "gene_symbol": "TP53",
    "gene_symbols": ["TP53"],
    "protein_name": "Cellular tumor antigen p53",
    "organism": "Homo sapiens",
    "organism_tax_id": "9606",
    "cellular_location": ["Nucleus", "Cytoplasm"],
    "go_annotations": {
      "molecular_function": [
        {
          "go_id": "GO:0003700",
          "term": "DNA-binding transcription factor activity"
        }
      ],
      "biological_process": [
        {
          "go_id": "0006915",
          "term": "apoptotic process"
        }
      ],
      "cellular_component": [
        {
          "go_id": "GO:0005634",
          "term": "nucleus"
        }
      ]
    },
    "druggability_classification": {
      "is_drug_target": true,
      "target_class": "Transcription factor",
      "confidence": "high",
      "evidence": ["DrugBank target"]
    },
    "sequence": "MEEPQSDPSV...",
    "sequence_length": 393,
    "sequence_mass": 43653.0,
    "protein_existence": "Evidence at protein level",
    "source": "UniProt",
    "version": "2024.01"
  },
  "entity_type": "rd:Target"
}
```

### Disease Entity / 疾病实体

```json
{
  "primary_id": "MIM:114480",
  "identifiers": {
    "MIM": "MIM:114480",
    "OMIM": "MIM:114480",
    "DOID": "DOID:1612",
    "MeSH": "D009369"
  },
  "properties": {
    "name": "Breast cancer",
    "acronym": "BC",
    "description": "A carcinoma arising from the breast...",
    "disease_type": "disease",
    "source": "UniProt",
    "version": "2024.01"
  },
  "entity_type": "rd:Disease"
}
```

### Relationship Types / 关系类型

#### 1. ASSOCIATED_WITH_DISEASE / 疾病关联

```json
{
  "relationship_type": "ASSOCIATED_WITH_DISEASE",
  "source_entity_id": "Target-P04637",
  "target_entity_id": "Disease-MIM:114480",
  "properties": {
    "association_type": "disease variant",
    "note": "The gene is involved in breast cancer...",
    "evidence": "PubMed:25656647"
  },
  "source": "UniProt-DISEASE"
}
```

#### 2. BIOMARKER_FOR / 生物标志物

```json
{
  "relationship_type": "BIOMARKER_FOR",
  "source_entity_id": "Target-P04637",
  "target_entity_id": "Disease-MIM:114480",
  "properties": {
    "association_type": "biomarker",
    "note": "Used as biomarker for cancer diagnosis",
    "evidence": "PubMed:12345678"
  },
  "source": "UniProt-DISEASE"
}
```

#### 3. ENCODED_BY / 编码基因

```json
{
  "relationship_type": "ENCODED_BY",
  "source_entity_id": "Target-P04637",
  "target_entity_id": "Gene-TP53",
  "properties": {
    "gene_symbol": "TP53",
    "gene_id": "7157"
  },
  "source": "UniProt-GENE"
}
```

---

## Configuration / 配置

### UniProtExtractionConfig / 提取配置

```python
@dataclass
class UniProtExtractionConfig:
    """UniProt 提取配置"""
    batch_size: int = 100                    # 批量大小
    rate_limit: float = 10.0                 # 速率限制（请求/秒）
    max_retries: int = 3                     # 最大重试次数
    retry_backoff: float = 1.0               # 重试退避（秒）
    timeout: int = 30                        # 请求超时（秒）
    cache_enabled: bool = True               # 启用缓存
    cache_file: str = "uniprot_cache.db"     # 缓存文件名
    include_go_annotations: bool = True      # 包含 GO 注释
    include_diseases: bool = True            # 包含疾病关联
    include_subcellular_location: bool = True # 包含亚细胞位置
    min_quality: str = "reviewed"            # 最小质量标准
```

### Environment Variables / 环境变量

No environment variables required. All configuration is done via:

1. Command-line arguments
2. Configuration dictionary
3. Default values in `UniProtExtractionConfig`

---

## Output Format / 输出格式

### Output Files / 输出文件

#### 1. uniprot_targets_TIMESTAMP.json
Enhanced target entities

```json
[
  {
    "primary_id": "P04637",
    "identifiers": {...},
    "properties": {...},
    "entity_type": "rd:Target"
  }
]
```

#### 2. uniprot_diseases_TIMESTAMP.json
Disease entities

```json
[
  {
    "primary_id": "MIM:114480",
    "identifiers": {...},
    "properties": {...},
    "entity_type": "rd:Disease"
  }
]
```

#### 3. uniprot_disease_associations_TIMESTAMP.json
Disease relationship data

```json
[
  {
    "relationship_type": "ASSOCIATED_WITH_DISEASE",
    "source_entity_id": "Target-P04637",
    "target_entity_id": "Disease-MIM:114480",
    "properties": {...},
    "source": "UniProt-DISEASE"
  }
]
```

#### 4. uniprot_summary_TIMESTAMP.json
Processing statistics and metadata

```json
{
  "processor": "UniProtProcessor",
  "source": "UniProt REST API",
  "timestamp": "20240108_120000",
  "extraction_config": {...},
  "statistics": {
    "targets_processed": 100,
    "targets_enhanced": 95,
    "diseases_extracted": 30,
    "go_annotations_extracted": 500,
    "relationships_created": 45,
    "api_requests_made": 10,
    "cache_hits": 0,
    "processing_time_seconds": 12.5
  },
  "entities_by_type": {
    "rd:Target": 95,
    "rd:Disease": 30
  },
  "total_entities": 125,
  "total_relationships": 45,
  "errors": [],
  "warnings": []
}
```

### Output Directory Structure / 输出目录结构

```
data/processed/documents/uniprot/
├── uniprot_targets_20240108_120000.json
├── uniprot_diseases_20240108_120000.json
├── uniprot_disease_associations_20240108_120000.json
└── uniprot_summary_20240108_120000.json
```

---

## Performance / 性能

### Benchmarks / 性能基准

#### Small Batch (< 100 IDs)
- **Time**: ~10-20 seconds
- **API Requests**: 1-10 requests
- **Cache Hits**: 0 (first run)

#### Medium Batch (100-1000 IDs)
- **Time**: ~1-3 minutes
- **API Requests**: 10-100 requests
- **Cache Hit Rate**: 30-50%

#### Large Batch (> 1000 IDs)
- **Time**: ~5-15 minutes
- **API Requests**: 100-1000 requests
- **Cache Hit Rate**: 50-70%

### Optimization Tips / 优化建议

1. **Enable Caching**: Reduces API calls by 50-70%
2. **Adjust Batch Size**: Larger batches = fewer requests
3. **Use Organism Search**: More efficient than individual IDs
4. **Parallel Processing**: Not currently supported (future enhancement)

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### 1. API Timeouts / API 超时

**Symptom**: Requests timing out after 30 seconds

**Solution**:
```python
config = {
    'extraction': {
        'timeout': 60,  # Increase timeout
        'max_retries': 5  # More retries
    }
}
```

#### 2. Rate Limit Errors / 速率限制错误

**Symptom**: HTTP 429 errors

**Solution**:
```python
config = {
    'extraction': {
        'rate_limit': 5.0,  # Reduce rate
        'retry_backoff': 2.0  # Increase backoff
    }
}
```

#### 3. Cache Corruption / 缓存损坏

**Symptom**: Errors reading from cache

**Solution**:
```bash
# Delete cache file
rm data/cache/uniprot_cache.db

# Or disable caching
python -m processors.uniprot_processor /path/to/ids.txt --no-cache
```

#### 4. Missing Data / 数据缺失

**Symptom**: GO annotations or diseases not extracted

**Solution**:
```bash
# Ensure these flags are NOT set
python -m processors.uniprot_processor /path/to/ids.txt --no-go --no-diseases

# Or explicitly enable in config
config = {
    'extraction': {
        'include_go_annotations': True,
        'include_diseases': True
    }
}
```

### Debug Mode / 调试模式

```bash
# Enable verbose logging
python -m processors.uniprot_processor /path/to/ids.txt --verbose

# Check cache contents
sqlite3 data/cache/uniprot_cache.db "SELECT accession, timestamp FROM uniprot_cache LIMIT 10;"
```

### Logging Levels / 日志级别

```python
import logging

# Set to DEBUG for detailed API logs
logging.basicConfig(level=logging.DEBUG)

# Set to WARNING to reduce noise
logging.basicConfig(level=logging.WARNING)
```

---

## Integration with ChEMBL / 与 ChEMBL 集成

### Mapping UniProt to ChEMBL Targets / UniProt 到 ChEMBL 靶点映射

```python
# After ChEMBL processing
chembl_targets = load_chembl_targets()

# Extract UniProt IDs
uniprot_ids = list(set([
    t['identifiers'].get('UniProt')
    for t in chembl_targets
    if t['identifiers'].get('UniProt')
]))

# Write to file
with open('uniprot_ids.txt', 'w') as f:
    for uid in uniprot_ids:
        f.write(f"{uid}\n")

# Process with UniProt processor
processor = UniProtProcessor()
result = processor.process('uniprot_ids.txt')

# Merge data
merged_targets = merge_chembl_uniprot(chembl_targets, result.entities)
```

### Example Workflow / 示例工作流程

```bash
# Step 1: Process ChEMBL data
python -m processors.chembl_processor /path/to/chembl.db --limit-targets 100

# Step 2: Extract UniProt IDs from ChEMBL targets
python scripts/extract_uniprot_from_chembl.py

# Step 3: Enhance with UniProt data
python -m processors.uniprot_processor uniprot_ids.txt

# Step 4: Merge and validate
python scripts/merge_targets.py
```

---

## Future Enhancements / 未来增强

### Planned Features / 计划功能

1. **Parallel Processing**: Multi-threaded API requests
2. **Incremental Updates**: Only fetch updated entries
3. **Alternative APIs**: Support for UniProt RDF/XML endpoints
4. **Advanced Filtering**: More sophisticated organism and taxonomy queries
5. **Relationship Inference**: Infer relationships from GO annotations
6. **Batch Export**: Support for Neo4j bulk import format

### Contribution / 贡献

To contribute enhancements:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit pull request

---

## References / 参考文献

### External Resources / 外部资源

- [UniProt REST API Documentation](https://www.uniprot.org/help/api)
- [UniProt Website](https://www.uniprot.org/)
- [Gene Ontology Consortium](http://geneontology.org/)
- [DrugBank Database](https://go.drugbank.com/)

### Internal Documentation / 内部文档

- [ChEMBL Processor Documentation](/root/autodl-tmp/pj-pharmaKG/docs/CHEMBL_PROCESSOR.md)
- [Base Processor Documentation](/root/autodl-tmp/pj-pharmaKG/processors/base.py)
- [PharmaKG Schema Design](/root/autodl-tmp/pj-pharmaKG/docs/schema/制药行业知识图谱Schema设计文档.md)

---

## Changelog / 更新日志

### v1.0 (2024-01-08)

- Initial release
- Basic UniProt API integration
- Target entity extraction
- Disease association extraction
- GO annotation extraction
- Caching support
- Rate limiting
- Command-line interface
- Test suite

---

## License / 许可证

This processor is part of the PharmaKG project and follows the same license terms.

---

## Contact / 联系

For questions or issues:
- GitHub Issues: [PharmaKG Repository]
- Documentation: See `/docs` directory
