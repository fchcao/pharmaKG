# UniProt Processor Quick Start Guide
# UniProt 处理器快速入门指南

## Quick Reference / 快速参考

### Basic Usage / 基本使用

```bash
# File mode - process UniProt IDs from file
python -m processors.uniprot_processor /path/to/uniprot_ids.txt

# Organism search mode
python -m processors.uniprot_processor --organism human --limit 100

# Custom output directory
python -m processors.uniprot_processor /path/to/uniprot_ids.txt --output /custom/path
```

### Input File Format / 输入文件格式

Create a text file with one UniProt ID per line:

```
P04637
P08253
P35354
P00734
P10275
```

### Common Options / 常用选项

| Option / 选项 | Description / 描述 | Default / 默认值 |
|----------------|-------------------|------------------|
| `--organism` | Organism filter (human/mouse/rat/all) | human |
| `--limit` | Limit number of entries | None |
| `--batch-size` | Batch size for API requests | 100 |
| `--rate-limit` | API rate limit (req/s) | 10.0 |
| `--min-quality` | Minimum quality (reviewed/unreviewed/all) | reviewed |
| `--no-cache` | Disable caching | False |
| `--no-go` | Skip GO annotations | False |
| `--no-diseases` | Skip disease associations | False |
| `--verbose` | Enable verbose logging | False |

### Output Files / 输出文件

```
data/processed/documents/uniprot/
├── uniprot_targets_TIMESTAMP.json          # Enhanced target entities
├── uniprot_diseases_TIMESTAMP.json         # Disease entities
├── uniprot_disease_associations_TIMESTAMP.json  # Disease relationships
└── uniprot_summary_TIMESTAMP.json          # Processing summary
```

## Integration Workflow / 集成工作流程

### Step 1: Process ChEMBL Data

```bash
python -m processors.chembl_processor /path/to/chembl.db --limit-targets 100
```

### Step 2: Extract UniProt IDs

```bash
python scripts/extract_uniprot_from_chembl.py data/processed/documents/chembl/chembl_targets_*.json -o data/sources/uniprot_ids.txt
```

### Step 3: Enhance with UniProt Data

```bash
python -m processors.uniprot_processor data/sources/uniprot_ids.txt
```

### Step 4: Merge Data (Optional)

```python
# Use custom script or manual merge
python scripts/merge_targets.py
```

## Python API Examples / Python API 示例

### Example 1: Basic Processing

```python
from pathlib import Path
from processors.uniprot_processor import UniProtProcessor

# Create processor
processor = UniProtProcessor()

# Process file
result = processor.process(
    source_path=Path('data/sources/uniprot_ids.txt'),
    save_intermediate=True
)

# Check results
print(f"Status: {result.status.value}")
print(f"Entities: {result.metrics.entities_extracted}")
print(f"Relationships: {result.metrics.relationships_extracted}")
```

### Example 2: Organism Search

```python
from processors.uniprot_processor import UniProtProcessor, OrganismFilter

# Create processor
processor = UniProtProcessor()

# Search human proteins
uniprot_data = processor.fetch_by_organism(
    organism=OrganismFilter.HUMAN,
    limit=100,
    query="kinase"
)

print(f"Found {len(uniprot_data)} entries")
```

### Example 3: Custom Configuration

```python
from processors.uniprot_processor import UniProtProcessor, UniProtExtractionConfig

# Create custom config
config = {
    'extraction': {
        'batch_size': 50,
        'rate_limit': 15.0,
        'cache_enabled': True,
        'include_go_annotations': True,
        'include_diseases': True,
        'min_quality': 'reviewed'
    }
}

# Create processor with custom config
processor = UniProtProcessor(config)

# Process data
result = processor.process('data/sources/uniprot_ids.txt')
```

## Testing / 测试

```bash
# Run all tests
python scripts/test_uniprot_processor.py

# Test specific functionality
python -c "from scripts.test_uniprot_processor import test_api_endpoints; test_api_endpoints()"

# Test with sample data
python -m processors.uniprot_processor --organism human --limit 5
```

## Common UniProt IDs for Testing / 测试常用 UniProt IDs

```
# Human Proteins
P04637    # TP53 - Tumor protein p53
P08253    # MMP2 - Matrix metalloproteinase-2
P35354    # PTGS2 - Prostaglandin G/H synthase 2 (COX-2)
P00734    # F2 - Coagulation factor II (Thrombin)
P10275    # AR - Androgen receptor
P12345    # Example format (may not exist)

# Mouse Proteins
P02340    # Trp53 - Tumor protein p53
Q9R1T5    # Mmp2 - Matrix metalloproteinase-2

# Rat Proteins
P10361    # Ptgs2 - Prostaglandin G/H synthase 2
```

## Troubleshooting / 故障排除

### Issue: API Timeout / API 超时

```bash
# Increase timeout and retries
python -m processors.uniprot_processor ids.txt --batch-size 50 --rate-limit 5.0
```

### Issue: Rate Limit Errors / 速率限制错误

```bash
# Reduce rate limit
python -m processors.uniprot_processor ids.txt --rate-limit 5.0
```

### Issue: Cache Corruption / 缓存损坏

```bash
# Clear cache
rm data/cache/uniprot_cache.db

# Or disable cache
python -m processors.uniprot_processor ids.txt --no-cache
```

## Performance Tips / 性能建议

1. **Enable Caching**: Reduces API calls by 50-70%
2. **Use Organism Search**: More efficient than individual IDs
3. **Adjust Batch Size**: Larger batches = fewer requests
4. **Process in Parallel**: Not currently supported (planned)

## Data Coverage / 数据覆盖

### Human Proteins / 人类蛋白
- **Reviewed**: ~20,000 entries
- **Unreviewed**: ~120,000 entries
- **Total**: ~140,000 entries

### Mouse Proteins / 小鼠蛋白
- **Reviewed**: ~17,000 entries
- **Unreviewed**: ~60,000 entries
- **Total**: ~77,000 entries

### Rat Proteins / 大鼠蛋白
- **Reviewed**: ~8,000 entries
- **Unreviewed**: ~30,000 entries
- **Total**: ~38,000 entries

## Support / 支持

- **Documentation**: `/docs/UNIPROT_PROCESSOR.md`
- **Base Processor**: `/processors/base.py`
- **Test Script**: `/scripts/test_uniprot_processor.py`
- **Issue Tracker**: GitHub Issues

## Version History / 版本历史

- **v1.0** (2024-01-08): Initial release
  - Basic UniProt API integration
  - Target entity extraction
  - Disease association extraction
  - GO annotation extraction
  - Caching support
  - Rate limiting
