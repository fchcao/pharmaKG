# DrugBank 处理器文档
# DrugBank Processor Documentation

## 概述 / Overview

DrugBank 处理器用于从 DrugBank XML 文件中提取药物、靶点、相互作用等数据，并将其转换为制药行业知识图谱格式。

The DrugBank processor extracts drugs, targets, interactions, and other data from DrugBank XML files and converts them to the Pharmaceutical Knowledge Graph format.

## 功能特性 / Features

### 提取内容 / Extracted Content

1. **化合物实体 / Compound Entities**
   - DrugBank ID, ChEMBL ID, PubChem CID, UNII
   - 通用名称、品牌名称
   - 药物类型（SmallMolecule, Biotech, CellTherapy, Vaccine）
   - 批准状态
   - 作用机制
   - 药代动力学（吸收、分布、代谢、排泄）
   - 毒性数据
   - 剂型、给药途径
   - ATC 代码
   - 物理状态、合成参考

2. **靶点实体 / Target Entities**
   - 酶（Enzymes）
   - 转运体（Transporters）
   - 作用靶点（Therapeutic Targets）
   - UniProt 标识符
   - 基因名称

3. **关系类型 / Relationship Types**
   - `INTERACTS_WITH` - 药物-药物相互作用
   - `METABOLIZED_BY` - 化合物 → 酶
   - `TRANSPORTED_BY` - 化合物 → 转运体
   - `TARGETS` - 化合物 → 靶点（作用机制）
   - `IS_PRODRUG_OF` - 前药关系
   - `HAS_SALT` - 盐类关系
   - `HAS_BRAND` - 品牌-通用关系

## 使用方法 / Usage

### 1. 获取 DrugBank 数据

**学术许可证申请 / Academic License Application**

DrugBank 对学术研究人员提供免费许可证。访问以下地址申请：
DrugBank offers free licenses for academic researchers. Apply at:

https://go.drugbank.com/releases/latest

下载完成后，将 XML 文件放置到以下目录：
After download, place the XML file in:

```
/data/sources/drugbank/drugbank.xml
```

### 2. 基本使用 / Basic Usage

```bash
# 处理整个 DrugBank 数据库
# Process entire DrugBank database
python -m processors.drugbank_processor /path/to/drugbank.xml

# 限制提取数量
# Limit extraction count
python -m processors.drugbank_processor /path/to/drugbank.xml --limit-compounds 1000

# 只提取已批准药物
# Extract only approved drugs
python -m processors.drugbank_processor /path/to/drugbank.xml --min-approval-level approved

# 包含撤回药物
# Include withdrawn drugs
python -m processors.drugbank_processor /path/to/drugbank.xml --include-withdrawn

# 自定义输出目录
# Custom output directory
python -m processors.drugbank_processor /path/to/drugbank.xml --output /custom/output/path
```

### 3. Python API 使用 / Python API Usage

```python
from processors.drugbank_processor import DrugBankProcessor

# 创建处理器配置
# Create processor configuration
config = {
    'extraction': {
        'limit_compounds': 10000,
        'include_withdrawn': False,
        'include_experimental': True,
        'extract_interactions': True,
        'extract_pharmacokinetics': True,
        'extract_enzymes': True,
        'extract_transporters': True,
        'extract_targets': True
    }
}

# 创建处理器
# Create processor
processor = DrugBankProcessor(config)

# 处理数据
# Process data
result = processor.process(
    source_path='/path/to/drugbank.xml',
    output_to='/path/to/output',
    save_intermediate=True
)

# 检查结果
# Check results
print(f"Status: {result.status.value}")
print(f"Entities: {result.metrics.entities_extracted}")
print(f"Relationships: {result.metrics.relationships_extracted}")
```

## 配置选项 / Configuration Options

| 参数 / Parameter | 类型 / Type | 默认值 / Default | 描述 / Description |
|-----------------|------------|-----------------|-------------------|
| `batch_size` | int | 1000 | 批处理大小 / Batch processing size |
| `limit_compounds` | int | None | 化合物数量限制 / Compound count limit |
| `include_withdrawn` | bool | False | 包含撤回药物 / Include withdrawn drugs |
| `include_experimental` | bool | True | 包含实验性药物 / Include experimental drugs |
| `include_illicit` | bool | False | 包含非法药物 / Include illicit drugs |
| `min_approval_level` | str | "all" | 最低批准级别 / Minimum approval level |
| `extract_interactions` | bool | True | 提取药物相互作用 / Extract drug interactions |
| `extract_pharmacokinetics` | bool | True | 提取药代动力学 / Extract pharmacokinetics |
| `extract_enzymes` | bool | True | 提取酶 / Extract enzymes |
| `extract_transporters` | bool | True | 提取转运体 / Extract transporters |
| `extract_targets` | bool | True | 提取靶点 / Extract targets |

## 输出文件 / Output Files

处理完成后，将在输出目录生成以下文件：
After processing, the following files will be generated in the output directory:

1. **drugbank_compounds_YYYYMMDD_HHMMSS.json** - 化合物实体
2. **drugbank_targets_YYYYMMDD_HHMMSS.json** - 靶点实体
3. **drugbank_relationships_YYYYMMDD_HHMMSS.json** - 关系数据
4. **drugbank_summary_YYYYMMDD_HHMMSS.json** - 处理摘要和统计信息

## 实体结构 / Entity Structure

### 化合物实体 / Compound Entity

```json
{
  "primary_id": "DB01001",
  "identifiers": {
    "DrugBank": "DB01001",
    "ChEMBL": "CHEMBL112",
    "PubChem": "1983",
    "UNII": "362O9ITL9D"
  },
  "properties": {
    "name": "Acetaminophen",
    "generic_name": "Acetaminophen",
    "brand_names": ["Tylenol", "Panadol"],
    "drug_type": "SmallMolecule",
    "approval_status": "approved",
    "mechanism_of_action": {...},
    "pharmacokinetics": {...},
    "toxicity": {...},
    "dosage_forms": ["tablet", "capsule"],
    "routes_of_administration": ["Oral"],
    "atc_codes": [...]
  },
  "entity_type": "rd:Compound"
}
```

### 靶点实体 / Target Entity

```json
{
  "primary_id": "P35354",
  "identifiers": {
    "DrugBank": "BE0004299",
    "UniProt": "P35354"
  },
  "properties": {
    "name": "Cyclooxygenase-2",
    "target_type": "Enzyme",
    "organism": "Humans",
    "gene_names": ["PTGS2"],
    "action": "Inhibitor"
  },
  "entity_type": "rd:Target"
}
```

### 关系结构 / Relationship Structure

```json
{
  "relationship_type": "INTERACTS_WITH",
  "source_entity_id": "Compound-DB01001",
  "target_entity_id": "Compound-DB00831",
  "properties": {
    "description": "Acetaminophen may increase the anticoagulant activities of Warfarin.",
    "severity": "moderate",
    "interaction_type": "increases_effect"
  },
  "source": "DrugBank-interactions"
}
```

## 测试 / Testing

运行测试脚本以验证处理器功能：
Run the test script to verify processor functionality:

```bash
python scripts/test_drugbank_processor.py
```

测试脚本将创建一个示例 DrugBank XML 文件并处理它。
The test script will create a sample DrugBank XML file and process it.

## 性能优化 / Performance Optimization

1. **大文件处理 / Large File Processing**
   - 使用 `iterparse` 进行流式处理，避免内存溢出
   - 建议在 64GB 内存以上的服务器上处理完整 DrugBank 数据库
   - Use `iterparse` for streaming processing to avoid memory overflow
   - Recommended to process full DrugBank database on servers with 64GB+ RAM

2. **批处理 / Batch Processing**
   - 调整 `batch_size` 参数以优化性能
   - 较大的批处理大小可提高速度，但会增加内存使用
   - Adjust `batch_size` parameter to optimize performance
   - Larger batch sizes increase speed but also memory usage

3. **去重 / Deduplication**
   - 处理器自动基于 InChIKey 和 UNII 进行去重
   - 确保数据质量和一致性
   - Processor automatically deduplicates based on InChIKey and UNII
   - Ensures data quality and consistency

## 数据质量 / Data Quality

DrugBank 数据具有以下特点：
DrugBank data has the following characteristics:

- **高准确性 / High Accuracy**: 手工策划，经过同行评审
- **全面性 / Comprehensive**: 覆盖全球药物市场
- **及时更新 / Regularly Updated**: 每季度更新
- Hand-curated, peer-reviewed
- Covers global drug market
- Updated quarterly

## 错误处理 / Error Handling

处理器包含完善的错误处理机制：
The processor includes comprehensive error handling:

1. **XML 解析错误 / XML Parsing Errors**: 记录警告，跳过无效元素
2. **缺失数据 / Missing Data**: 使用默认值或跳过
3. **格式错误 / Format Errors**: 记录错误，继续处理
4. Log warnings, skip invalid elements
5. Use default values or skip
6. Log errors, continue processing

## 常见问题 / FAQ

### Q: 如何获取 DrugBank 数据？
**A**: 访问 https://go.drugbank.com/releases/latest 申请学术许可证（免费）。

### Q: 处理完整数据库需要多长时间？
**A**: 取决于硬件配置，通常需要 1-3 小时。

### Q: 内存不足怎么办？
**A**: 减小 `batch_size` 参数或使用 `--limit-compounds` 限制处理数量。

### Q: 如何将 DrugBank 数据映射到 ChEMBL？
**A**: 处理器自动基于 InChIKey 和 UNII 进行映射。

## 参考资料 / References

- DrugBank 官网: https://go.drugbank.com/
- DrugBank 文档: https://go.drugbank.com/docs
- 药物相互作用指南: https://go.drugbank.com/releases/latest#download

## 更新日志 / Changelog

### v1.0 (2024)
- 初始版本
- 支持化合物、靶点、相互作用提取
- 支持药代动力学和毒性数据
- 支持 Drug-Drug 相互作用网络提取
- Initial version
- Support for compound, target, interaction extraction
- Support for pharmacokinetics and toxicity data
- Support for drug-drug interaction network extraction
