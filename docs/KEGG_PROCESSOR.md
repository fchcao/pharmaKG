# KEGG Pathway API 处理器文档
# KEGG Pathway API Processor Documentation

## 概述 | Overview

KEGG Pathway API 处理器用于从 KEGG (Kyoto Encyclopedia of Genes and Genomes) REST API 提取通路数据，包括通路信息、相关基因/蛋白质和化合物。该处理器遵循 PharmaKG 项目的处理器架构模式，支持批量处理、缓存和速率限制。

The KEGG Pathway API Processor extracts pathway data from the KEGG (Kyoto Encyclopedia of Genes and Genomes) REST API, including pathway information, related genes/proteins, and compounds. This processor follows the PharmaKG processor architecture pattern with support for batch processing, caching, and rate limiting.

## 功能特性 | Features

### 核心功能 | Core Features

1. **通路数据提取** | Pathway Data Extraction
   - 从 KEGG PATHWAY 数据库提取通路信息
   - 支持多种生物体（人类、小鼠、大鼠）
   - 支持文本和 KGML (XML) 两种格式
   - Extract pathway information from KEGG PATHWAY database
   - Support for multiple organisms (human, mouse, rat)
   - Support for both text and KGML (XML) formats

2. **基因/蛋白质关联** | Gene/Protein Associations
   - 提取通路相关基因
   - 自动映射 KEGG 基因 ID 到 UniProt 登录号
   - Extract pathway-related genes
   - Automatic mapping of KEGG gene IDs to UniProt accessions

3. **化合物关联** | Compound Associations
   - 提取通路中的小分子化合物
   - 建立通路-化合物关系
   - Extract small molecule compounds in pathways
   - Establish pathway-compound relationships

4. **关系提取** | Relationship Extraction
   - `rel:PARTICIPATES_IN` - 蛋白质 → 通路
   - `rel:REGULATES_PATHWAY` - 蛋白质 → 通路（酶、调节因子）
   - `rel:PATHWAY_HAS_COMPOUND` - 通路 → 化合物
   - `rel:PARTICIPATES_IN` - Protein → Pathway
   - `rel:REGULATES_PATHWAY` - Protein → Pathway (enzymes, regulators)
   - `rel:PATHWAY_HAS_COMPOUND` - Pathway → Compound

5. **性能优化** | Performance Optimization
   - 本地 SQLite 缓存减少 API 请求
   - 可配置的速率限制（默认 10 请求/秒）
   - 批量处理支持
   - 指数退避重试机制
   - Local SQLite caching to reduce API requests
   - Configurable rate limiting (default 10 requests/second)
   - Batch processing support
   - Exponential backoff retry mechanism

### 实体类型 | Entity Types

| 实体类型 | Entity Type | 描述 | Description |
|---------|-------------|------|-------------|
| `rd:Pathway` | Pathway | KEGG 通路实体 | KEGG pathway entity |
| `rd:Target` | Target | 蛋白质靶点（从基因转换） | Protein target (converted from genes) |
| `rd:Compound` | Compound | 小分子化合物 | Small molecule compound |

### 通路分类 | Pathway Categories

KEGG 通路按以下主要分类组织：

KEGG pathways are organized into the following main categories:

1. **Metabolism** - 代谢
   - Carbohydrate metabolism
   - Lipid metabolism
   - Amino acid metabolism
   - Nucleotide metabolism
   - Energy metabolism

2. **Genetic Information Processing** - 遗传信息处理
   - Transcription
   - Translation
   - Replication and repair

3. **Environmental Information Processing** - 环境信息处理
   - Signal transduction
   - Signaling molecules and interaction

4. **Cellular Processes** - 细胞过程
   - Cell growth and death
   - Cell motility

5. **Organismal Systems** - 有机体系统
   - Immune system
   - Nervous system
   - Endocrine system
   - Circulatory system
   - Digestive system

6. **Human Diseases** - 人类疾病
   - Cancers
   - Immune diseases
   - Neurodegenerative diseases
   - Metabolic diseases

## 使用方法 | Usage

### 命令行接口 | Command Line Interface

#### 1. 从 KEGG 通路 ID 文件处理

```bash
# 处理包含 KEGG 通路 ID 的文件
python -m processors.kegg_processor /path/to/pathway_ids.txt

# 自定义输出目录
python -m processors.kegg_processor /path/to/pathway_ids.txt --output /custom/output
```

文件格式示例 | File format example:
```
path:hsa04110
path:hsa04115
path:hsa04120
```

#### 2. 按生物体获取所有通路

```bash
# 获取人类所有通路
python -m processors.kegg_processor --organism human

# 获取小鼠通路
python -m processors.kegg_processor --organism mouse

# 获取大鼠通路
python -m processors.kegg_processor --organism rat
```

#### 3. 限制数量

```bash
# 只获取前 50 个通路
python -m processors.kegg_processor --organism human --limit 50

# 按分类过滤并限制数量
python -m processors.kegg_processor --organism human --category "Metabolism" --limit 20
```

#### 4. 高级选项

```bash
# 使用 KGML (XML) 格式
python -m processors.kegg_processor --organism human --use-kgml --limit 50

# 禁用缓存
python -m processors.kegg_processor --organism human --no-cache

# 禁用 UniProt 映射
python -m processors.kegg_processor --organism human --no-uniprot-mapping

# 自定义批处理大小和速率限制
python -m processors.kegg_processor --organism human --batch-size 100 --rate-limit 5.0

# 详细输出
python -m processors.kegg_processor --organism human --limit 10 --verbose
```

### Python API 使用 | Python API Usage

```python
from processors.kegg_processor import KEGGProcessor, OrganismCode

# 初始化处理器
config = {
    'extraction': {
        'batch_size': 50,
        'rate_limit': 10.0,
        'cache_enabled': True,
        'map_kegg_to_uniprot': True
    }
}

processor = KEGGProcessor(config)

# 方法 1: 列出所有通路
pathway_ids = processor.list_pathways(organism=OrganismCode.HUMAN)
print(f"Found {len(pathway_ids)} pathways")

# 方法 2: 按生物体获取通路数据
pathways_data = processor.fetch_pathways_by_organism(
    organism=OrganismCode.HUMAN,
    category="Metabolism",
    limit=100
)

# 方法 3: 从文件处理
result = processor.process(
    source_path='/path/to/pathway_ids.txt',
    output_to='/custom/output',
    save_intermediate=True
)

# 检查结果
print(f"Status: {result.status.value}")
print(f"Entities extracted: {result.metrics.entities_extracted}")
print(f"Relationships created: {result.metrics.relationships_extracted}")
```

### 测试 | Testing

运行测试脚本：

Run the test script:

```bash
python scripts/test_kegg_processor.py
```

测试包括：
Tests include:
- 基本初始化 | Basic initialization
- 列出通路 | Listing pathways
- 获取通路详情 | Fetching pathway details
- 转换通路数据 | Transforming pathway data
- 创建关系 | Creating relationships
- KEGG 到 UniProt 映射 | KEGG to UniProt mapping
- 批量获取 | Batch fetching
- 缓存功能 | Caching functionality
- 保存结果 | Saving results

## 配置选项 | Configuration Options

### 提取配置 | Extraction Configuration

| 参数 | Parameter | 类型 | Type | 默认值 | Default | 描述 | Description |
|------|-----------|------|-------|--------|---------|------|-------------|
| `batch_size` | int | int | 50 | 批处理大小 | Batch processing size |
| `rate_limit` | float | float | 10.0 | API 请求速率（请求/秒） | API request rate (requests/second) |
| `max_retries` | int | int | 3 | 最大重试次数 | Maximum retry attempts |
| `retry_backoff` | float | float | 1.0 | 重试退避因子 | Retry backoff factor |
| `timeout` | int | int | 30 | 请求超时（秒） | Request timeout (seconds) |
| `cache_enabled` | bool | bool | True | 启用缓存 | Enable caching |
| `cache_file` | str | str | "kegg_cache.db" | 缓存文件名 | Cache file name |
| `include_genes` | bool | bool | True | 包含基因数据 | Include gene data |
| `include_proteins` | bool | bool | True | 包含蛋白质数据 | Include protein data |
| `include_compounds` | bool | bool | True | 包含化合物数据 | Include compound data |
| `map_kegg_to_uniprot` | bool | bool | True | 映射到 UniProt | Map to UniProt |
| `use_kgml` | bool | bool | False | 使用 KGML 格式 | Use KGML format |

## API 端点 | API Endpoints

KEGG REST API 端点（基础 URL: `http://rest.kegg.jp`）：

KEGG REST API endpoints (base URL: `http://rest.kegg.jp`):

| 端点 | Endpoint | 描述 | Description |
|------|-----------|------|-------------|
| `list/pathway/{organism}` | 列出指定生物体的所有通路 | List all pathways for organism |
| `get/{pathway_id}` | 获取通路详情（文本格式） | Get pathway details (text format) |
| `get/{pathway_id}/kgml` | 获取通路详情（KGML 格式） | Get pathway details (KGML format) |
| `conv/genes/uniprot/{gene_id}` | 转换基因 ID 到 UniProt | Convert gene ID to UniProt |
| `link/pathway/{organism}` | 链接基因到通路 | Link genes to pathways |
| `link/genes/{pathway_id}` | 链接通路到基因 | Link pathway to genes |

## 输出文件 | Output Files

处理器生成以下文件：

The processor generates the following files:

### 1. 通路实体文件 | Pathway Entities File

**文件名 | Filename:** `kegg_pathways_<timestamp>.json`

**格式 | Format:**
```json
[
  {
    "primary_id": "path:hsa04110",
    "identifiers": {
      "KEGG": "path:hsa04110",
      "KEGG_ID": "hsa04110",
      "PathwayNumber": "4110"
    },
    "properties": {
      "name": "Cell Cycle",
      "description": "The cell cycle is the series of events...",
      "organism": "Homo sapiens",
      "pathway_type": "cellular",
      "pathway_category": "Cellular Processes",
      "associated_genes": ["10458", "673", "7157"],
      "associated_gene_symbols": ["CDC2", "BRCA1", "TP53"],
      "associated_proteins": ["Q9Y258", "P38398", "P04637"],
      "modules": [],
      "diseases": [],
      "source": "KEGG",
      "version": "2024.1"
    },
    "entity_type": "rd:Pathway"
  }
]
```

### 2. 靶点实体文件 | Target Entities File

**文件名 | Filename:** `kegg_targets_<timestamp>.json`

**格式 | Format:**
```json
[
  {
    "primary_id": "GENE-10458",
    "identifiers": {
      "KEGG_Gene": "10458",
      "GeneSymbol": "CDC2"
    },
    "properties": {
      "name": "CDC2",
      "gene_symbol": "CDC2",
      "gene_id": "10458",
      "description": "Cell division control protein 2 homolog",
      "source": "KEGG",
      "version": "2024.1"
    },
    "entity_type": "rd:Target"
  }
]
```

### 3. 化合物实体文件 | Compound Entities File

**文件名 | Filename:** `kegg_compounds_<timestamp>.json`

**格式 | Format:**
```json
[
  {
    "primary_id": "cpd:C00002",
    "identifiers": {
      "KEGG_Compound": "cpd:C00002",
      "CompoundID": "C00002"
    },
    "properties": {
      "name": "ATP",
      "compound_type": "small_molecule",
      "source": "KEGG",
      "version": "2024.1"
    },
    "entity_type": "rd:Compound"
  }
]
```

### 4. 关系文件 | Relationships File

**文件名 | Filename:** `kegg_pathway_relationships_<timestamp>.json`

**格式 | Format:**
```json
[
  {
    "relationship_type": "PARTICIPATES_IN",
    "source_entity_id": "Target-GENE-10458",
    "target_entity_id": "Pathway-path:hsa04110",
    "properties": {
      "gene_id": "10458",
      "gene_symbol": "CDC2",
      "role": "participant"
    },
    "source": "KEGG-PATHWAY"
  },
  {
    "relationship_type": "PATHWAY_HAS_COMPOUND",
    "source_entity_id": "Pathway-path:hsa04110",
    "target_entity_id": "Compound-cpd:C00002",
    "properties": {
      "compound_id": "cpd:C00002",
      "compound_name": "ATP"
    },
    "source": "KEGG-PATHWAY"
  }
]
```

### 5. 摘要文件 | Summary File

**文件名 | Filename:** `kegg_summary_<timestamp>.json`

**格式 | Format:**
```json
{
  "processor": "KEGGProcessor",
  "source": "KEGG REST API",
  "timestamp": "20240208_123456",
  "extraction_config": {
    "batch_size": 50,
    "rate_limit": 10.0,
    "cache_enabled": true,
    "map_kegg_to_uniprot": true
  },
  "statistics": {
    "pathways_processed": 100,
    "pathways_extracted": 98,
    "genes_extracted": 3250,
    "proteins_extracted": 3100,
    "compounds_extracted": 450,
    "relationships_created": 3650,
    "api_requests_made": 120,
    "cache_hits": 45,
    "processing_time_seconds": 125.5
  },
  "entities_by_type": {
    "rd:Pathway": 98,
    "rd:Target": 3100,
    "rd:Compound": 450
  },
  "total_entities": 3648,
  "total_relationships": 3650,
  "errors": [],
  "warnings": []
}
```

## 性能考虑 | Performance Considerations

### API 速率限制 | API Rate Limiting

KEGG REST API 没有严格的速率限制，但建议遵守以下最佳实践：

KEGG REST API does not have strict rate limits, but it's recommended to follow these best practices:

1. **默认速率限制** | Default Rate Limit
   - 处理器默认设置为 10 请求/秒
   - 可通过 `--rate-limit` 参数调整
   - Processor defaults to 10 requests/second
   - Adjustable via `--rate-limit` parameter

2. **学术使用** | Academic Use
   - KEGG API 仅供学术使用
   - 请确保遵守 KEGG 使用条款
   - KEGG API is for academic use only
   - Please ensure compliance with KEGG terms of use

### 缓存策略 | Caching Strategy

1. **本地缓存** | Local Cache
   - SQLite 数据库存储在 `data/cache/kegg_cache.db`
   - 缓存键是 KEGG 通路 ID
   - 可通过 `--no-cache` 禁用
   - SQLite database stored at `data/cache/kegg_cache.db`
   - Cache key is KEGG pathway ID
   - Can be disabled via `--no-cache`

2. **缓存有效期** | Cache Validity
   - 通路数据相对稳定
   - 建议定期清理缓存（例如每月）
   - Pathway data is relatively stable
   - Recommended to periodically clear cache (e.g., monthly)

### 批量处理 | Batch Processing

- 默认批处理大小：50
- 可通过 `--batch-size` 调整
- 较大的批处理可提高效率，但会增加内存使用
- Default batch size: 50
- Adjustable via `--batch-size`
- Larger batches improve efficiency but increase memory usage

## 错误处理 | Error Handling

### 常见错误 | Common Errors

1. **API 连接失败** | API Connection Failure
   ```
   Error: API request failed: Connection timeout
   ```
   - 检查网络连接
   - 确认 KEGG API 可访问
   - Check network connection
   - Verify KEGG API accessibility

2. **速率限制错误** | Rate Limit Error
   ```
   Error: Too many requests
   ```
   - 降低 `--rate-limit` 值
   - 启用缓存以减少请求
   - Reduce `--rate-limit` value
   - Enable caching to reduce requests

3. **解析错误** | Parse Error
   ```
   Error: Failed to parse pathway data
   ```
   - KEGG API 返回格式可能已更改
   - 尝试使用 `--use-kgml` 选项
   - KEGG API response format may have changed
   - Try using `--use-kgml` option

### 调试 | Debugging

使用 `--verbose` 选项获取详细日志：

Use `--verbose` option for detailed logging:

```bash
python -m processors.kegg_processor --organism human --limit 10 --verbose
```

## 与其他处理器的集成 | Integration with Other Processors

### ChEMBL 处理器 | ChEMBL Processor

```python
# 先用 KEGG 提取通路和基因
kegg_processor = KEGGProcessor(config)
kegg_result = kegg_processor.process(...)

# 使用 ChEMBL 处理器获取靶点的详细生物活性数据
chembl_processor = ChEMBLProcessor(config)
chembl_result = chembl_processor.process(...)
```

### UniProt 处理器 | UniProt Processor

```python
# KEGG 处理器自动映射基因到 UniProt
kegg_processor = KEGGProcessor({
    'extraction': {'map_kegg_to_uniprot': True}
})

# UniProt 处理器可以增强靶点数据
uniprot_processor = UniProtProcessor(config)
```

## 参考资料 | References

- [KEGG API 文档](https://www.kegg.jp/kegg/rest/keggapi.html) | [KEGG API Documentation](https://www.kegg.jp/kegg/rest/keggapi.html)
- [KEGG 通路数据库](https://www.genome.jp/kegg/pathway.html) | [KEGG Pathway Database](https://www.genome.jp/kegg/pathway.html)
- [KGML 规范](https://www.kegg.jp/kegg/xml/) | [KGML Specification](https://www.kegg.jp/kegg/xml/)

## 许可和使用条款 | License and Terms of Use

- KEGG 数据库和 API 仅供学术使用
- 商业使用需要获得 KEGG 的许可
- 引用时请引用 KEGG 数据库
- KEGG database and API are for academic use only
- Commercial use requires license from KEGG
- Please cite KEGG database when using this data

**KEGG 引用格式 | KEGG Citation Format:**

```
Kanehisa, M., Furumichi, M., Sato, Y., Kawashima, M., et al. (2024)
KEGG for representation and analysis of molecular networks
involving diseases and drugs. Nucleic Acids Res. 50:D621-D628.
```

## 更新日志 | Changelog

### v1.0 (2024-02-08)

- 初始版本发布
- 支持基本的通路数据提取
- 支持基因/蛋白质和化合物关联
- 实现 KEGG 到 UniProt 映射
- 支持文本和 KGML 格式
- 实现缓存和速率限制
- Initial release
- Basic pathway data extraction support
- Gene/protein and compound association support
- KEGG to UniProt mapping implementation
- Text and KGML format support
- Caching and rate limiting implementation
