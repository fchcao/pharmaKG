# DailyMed 处理器文档
# DailyMed Processor Documentation

## 概述 / Overview

DailyMed 处理器用于从 DailyMed SPL（Structured Product Labels）XML 文件中提取药物标签、适应症、禁忌症、不良反应和药物基因组学数据，并将其转换为制药行业知识图谱格式。

The DailyMed processor extracts drug labels, indications, contraindications, adverse reactions, and pharmacogenomic data from DailyMed SPL (Structured Product Labels) XML files and converts them to the Pharmaceutical Knowledge Graph format.

## 功能特性 / Features

### 提取内容 / Extracted Content

1. **化合物实体 / Compound Entities**
   - SPL ID (set_id)
   - 通用名称、品牌名称
   - NDC (National Drug Code)
   - 剂型、给药途径、规格
   - 市场状态、批准日期
   - 制造商
   - 活性和非活性成分

2. **疾病/状况实体 / Condition Entities**
   - 适应症（Indications）
   - 禁忌症（Contraindications）
   - 警告（Warnings）
   - 注意事项

3. **生物标志物实体 / Biomarker Entities**
   - 药物基因组学标志物
   - 基因变异（如 CYP2D6, HLA-B*57:01）
   - 临床意义
   - 影响人群

4. **不良事件实体 / Adverse Event Entities**
   - 不良反应
   - 黑框警告
   - 严重程度分级

5. **关系类型 / Relationship Types**
   - `TREATS` - 化合物 → 疾病（适应症）
   - `CONTRAINDICATED_FOR` - 化合物 → 疾病（禁忌症）
   - `HAS_WARNING_FOR` - 化合物 → 疾病（警告）
   - `HAS_BIOMARKER` - 化合物 → 生物标志物
   - `CAUSES_ADVERSE_EVENT` - 化合物 → 不良事件
   - `HAS_BOXED_WARNING` - 化合物 → 不良事件

## 使用方法 / Usage

### 1. 获取 DailyMed 数据

**选项 A: 使用 API（推荐）/ Option A: Use API (Recommended)**

```bash
# 按查询词获取数据
# Fetch data by query
python -m processors.dailymed_processor --query "cancer" --max-files 100

# 按 NDC 获取数据
# Fetch data by NDC
python -m processors.dailymed_processor --ndc "1234-5678"

# 自定义 API URL
# Custom API URL
python -m processors.dailymed_processor --api-url "https://dailymed.nlm.nih.gov/dailymed/api/v2"
```

**选项 B: 本地文件处理 / Option B: Local File Processing**

1. 从 DailyMed FTP 下载 SPL 文件：
   Download SPL files from DailyMed FTP:
   ```
   FTP: ftp://public.nlm.nih.gov/.nlm.nih.gov/dailymed/
   ```

2. 解压并放置到项目目录：
   Extract and place in project directory:
   ```
   /data/sources/dailymed/spl_files/
   ```

3. 处理本地文件：
   Process local files:
   ```bash
   python -m processors.dailymed_processor /path/to/dailymed/files --use-api false
   ```

### 2. 基本使用 / Basic Usage

```bash
# 使用 API 获取癌症治疗药物数据
# Fetch cancer treatment drug data via API
python -m processors.dailymed_processor --query "cancer" --max-files 50

# 处理本地 SPL 文件
# Process local SPL files
python -m processors.dailymed_processor /data/sources/dailymed --use-api false --max-files 100

# 自定义输出目录
# Custom output directory
python -m processors.dailymed_processor --output /custom/output/path

# 只提取适应症和禁忌症
# Extract only indications and contraindications
python -m processors.dailymed_processor --query "diabetes" --extract-adverse-reactions false --extract-pharmacogenomics false
```

### 3. Python API 使用 / Python API Usage

```python
from processors.dailymed_processor import DailyMedProcessor

# 创建处理器配置
# Create processor configuration
config = {
    'extraction': {
        'use_api': True,
        'query': 'cancer',
        'max_files': 100,
        'extract_indications': True,
        'extract_contraindications': True,
        'extract_warnings': True,
        'extract_adverse_reactions': True,
        'extract_pharmacogenomics': True,
        'extract_boxed_warnings': True
    }
}

# 创建处理器
# Create processor
processor = DailyMedProcessor(config)

# 处理数据
# Process data
result = processor.process(
    source_path='.',  # 使用 API 时可以忽略
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
| `use_api` | bool | True | 使用 DailyMed API / Use DailyMed API |
| `api_base_url` | str | "https://dailymed.nlm.nih.gov/dailymed/api/v2" | API 基础 URL / API base URL |
| `query` | str | None | 搜索查询 / Search query |
| `ndc` | str | None | NDC 代码 / NDC code |
| `set_id` | str | None | SPL ID / SPL ID |
| `max_files` | int | 100 | 最大处理文件数 / Max files to process |
| `download_dir` | str | None | 下载文件保存目录 / Download directory |
| `extract_indications` | bool | True | 提取适应症 / Extract indications |
| `extract_contraindications` | bool | True | 提取禁忌症 / Extract contraindications |
| `extract_warnings` | bool | True | 提取警告 / Extract warnings |
| `extract_adverse_reactions` | bool | True | 提取不良反应 / Extract adverse reactions |
| `extract_pharmacogenomics` | bool | True | 提取药物基因组学 / Extract pharmacogenomics |
| `extract_boxed_warnings` | bool | True | 提取黑框警告 / Extract boxed warnings |
| `map_to_chembl` | bool | True | 映射到 ChEMBL / Map to ChEMBL |
| `map_to_drugbank` | bool | True | 映射到 DrugBank / Map to DrugBank |

## 输出文件 / Output Files

处理完成后，将在输出目录生成以下文件：
After processing, the following files will be generated in the output directory:

1. **dailymed_rd_compounds_YYYYMMDD_HHMMSS.json** - 化合物实体
2. **dailymed_clinical_conditions_YYYYMMDD_HHMMSS.json** - 疾病/状况实体
3. **dailymed_clinical_biomarkers_YYYYMMDD_HHMMSS.json** - 生物标志物实体
4. **dailymed_clinical_adverse_events_YYYYMMDD_HHMMSS.json** - 不良事件实体
5. **dailymed_relationships_YYYYMMDD_HHMMSS.json** - 关系数据
6. **dailymed_summary_YYYYMMDD_HHMMSS.json** - 处理摘要和统计信息

## 实体结构 / Entity Structure

### 化合物实体 / Compound Entity

```json
{
  "primary_id": "DAILYMED-1234",
  "identifiers": {
    "DailyMed": "test_set_id",
    "NDC": "1234-5678",
    "GenericName": "acetaminophen"
  },
  "properties": {
    "name": "acetaminophen",
    "generic_name": "acetaminophen",
    "brand_names": ["Tylenol"],
    "dosage_form": "tablet",
    "route": "Oral",
    "strength": "500 mg",
    "marketing_status": "Prescription",
    "approval_date": "2020-01-01",
    "manufacturer": "Johnson & Johnson",
    "active_ingredients": [
      {
        "name": "acetaminophen",
        "strength": "500",
        "unit": "mg"
      }
    ],
    "inactive_ingredients": ["corn starch", "magnesium stearate"]
  },
  "entity_type": "rd:Compound"
}
```

### 疾病/状况实体 / Condition Entity

```json
{
  "primary_id": "CONDITION-HEADACHE",
  "identifiers": {
    "name": "Headache"
  },
  "properties": {
    "name": "Headache",
    "condition_type": "indication",
    "description": "Temporarily relieves minor headaches..."
  },
  "entity_type": "clinical:Condition"
}
```

### 生物标志物实体 / Biomarker Entity

```json
{
  "primary_id": "BIOMARKER-CYP2E1",
  "identifiers": {
    "name": "CYP2E1"
  },
  "properties": {
    "name": "CYP2E1",
    "biomarker_type": "pharmacogenomic",
    "clinical_significance": "metabolism",
    "affected_population": "general",
    "description": "Genetic variations in CYP2E1 may affect acetaminophen metabolism"
  },
  "entity_type": "clinical:Biomarker"
}
```

### 不良事件实体 / Adverse Event Entity

```json
{
  "primary_id": "ADVERSE-EVENT-NAUSEA",
  "identifiers": {
    "name": "Nausea"
  },
  "properties": {
    "name": "Nausea",
    "severity": "mild",
    "is_boxed_warning": false,
    "description": "One of the most common adverse reactions"
  },
  "entity_type": "clinical:AdverseEvent"
}
```

### 关系结构 / Relationship Structure

```json
{
  "relationship_type": "TREATS",
  "source_entity_id": "Compound-DAILYMED-1234",
  "target_entity_id": "CONDITION-HEADACHE",
  "properties": {
    "indication_type": "primary",
    "description": "Temporarily relieves minor headaches..."
  },
  "source": "DailyMed-indications"
}
```

## 测试 / Testing

运行测试脚本以验证处理器功能：
Run the test script to verify processor functionality:

```bash
python scripts/test_dailymed_processor.py
```

测试脚本将创建一个示例 SPL XML 文件并处理它。
The test script will create a sample SPL XML file and process it.

## API 端点 / API Endpoints

DailyMed API 提供以下端点：
DailyMed API provides the following endpoints:

| 端点 / Endpoint | 描述 / Description |
|----------------|-------------------|
| `/spls` | 获取 SPL 列表 / Get SPL list |
| `/spls/{set_id}` | 获取特定 SPL / Get specific SPL |
| `/spls/search` | 搜索 SPL / Search SPL |
| `/spls/{set_id}/download` | 下载 SPL XML / Download SPL XML |

详细 API 文档：https://dailymed.nlm.nih.gov/dailymed/api/v2/
Detailed API documentation: https://dailymed.nlm.nih.gov/dailymed/api/v2/

## 数据频率 / Data Frequency

DailyMed 数据每日更新，包含最新的 FDA 批准药物标签。
DailyMed data is updated daily, containing the latest FDA-approved drug labels.

## 性能优化 / Performance Optimization

1. **API 限速 / API Rate Limiting**
   - 处理器内置请求限速，避免 API 限流
   - 使用线程池并发下载
   - Processor includes built-in rate limiting to avoid API throttling
   - Uses thread pool for concurrent downloads

2. **批处理 / Batch Processing**
   - 调整 `batch_size` 参数以优化性能
   - 较大的批处理大小可提高速度
   - Adjust `batch_size` parameter to optimize performance
   - Larger batch sizes increase speed

3. **内存优化 / Memory Optimization**
   - 使用流式 XML 解析
   - 及时清理已处理的元素
   - Uses streaming XML parsing
   - Cleans processed elements promptly

## 数据质量 / Data Quality

DailyMed 数据具有以下特点：
DailyMed data has the following characteristics:

- **权威性 / Authoritative**: FDA 官方数据源
- **实时性 / Real-time**: 每日更新
- **完整性 / Complete**: 包含所有 FDA 批准药物标签
- **结构化 / Structured**: 标准化的 SPL 格式
- Official FDA data source
- Updated daily
- Contains all FDA-approved drug labels
- Standardized SPL format

## 错误处理 / Error Handling

处理器包含完善的错误处理机制：
The processor includes comprehensive error handling:

1. **API 错误 / API Errors**: 自动重试，记录警告
2. **XML 解析错误 / XML Parsing Errors**: 记录警告，跳过无效元素
3. **缺失数据 / Missing Data**: 使用默认值或跳过
4. **网络错误 / Network Errors**: 自动重试机制
5. Automatic retry, log warnings
6. Log warnings, skip invalid elements
7. Use default values or skip
8. Automatic retry mechanism

## 常见问题 / FAQ

### Q: 如何获取 DailyMed 数据？
**A**: 可以使用 DailyMed API（推荐）或从 FTP 下载 SPL 文件。

### Q: API 有使用限制吗？
**A**: 是的，处理器内置了请求限速功能。建议每次查询限制在 1000 个文件以内。

### Q: 如何查找特定的药物标签？
**A**: 使用 `--query` 参数按药物名称搜索，或使用 `--ndc` 参数按 NDC 代码搜索。

### Q: 提取的生物标志物数据可靠吗？
**A**: DailyMed 包含 FDA 批准的药物基因组学信息，是权威数据源。

### Q: 如何处理中文药物名称？
**A**: DailyMed 主要包含英文名称。中文映射需要在后续处理中添加。

## 参考资料 / References

- DailyMed 官网: https://dailymed.nlm.nih.gov/dailymed/
- DailyMed API 文档: https://dailymed.nlm.nih.gov/dailymed/api/v2/
- DailyMed FTP: ftp://public.nlm.nih.gov/.nlm.nih.gov/dailymed/
- SPL 标准: https://www.fda.gov/drugs/drug-approvals-and-databases/structured-product-labeling-resources

## 与其他数据源的整合 / Integration with Other Data Sources

DailyMed 数据可以与以下数据源整合：
DailyMed data can be integrated with the following sources:

1. **DrugBank**: 通过通用名称和 UNII 映射
2. **ChEMBL**: 通过通用名称映射
3. **FAERS**: 通过 NDC 代码关联不良事件报告
4. **FDA Drugs@FDA**: 通过 NDC 和申请号关联
5. Map by generic name and UNII
6. Map by generic name
7. Link adverse event reports by NDC
8. Link by NDC and application number

## 更新日志 / Changelog

### v1.0 (2024)
- 初始版本
- 支持 API 和本地文件处理
- 支持适应症、禁忌症、警告、不良反应提取
- 支持药物基因组学数据提取
- 支持黑框警告提取
- Initial version
- Support for API and local file processing
- Support for indications, contraindications, warnings, adverse reactions extraction
- Support for pharmacogenomic data extraction
- Support for boxed warning extraction
