# FDA Drugs@FDA Processor - Quick Start Guide

## Quick Start Guide / 快速入门指南

### Installation / 安装

```bash
# Activate conda environment / 激活 conda 环境
conda activate pharmakg-api

# Install dependencies / 安装依赖
pip install requests
```

### Basic Usage / 基本使用

#### 1. Fetch All Applications (Test Mode) / 获取所有申请（测试模式）

```bash
# Fetch first 100 applications / 获取前 100 个申请
python -m processors.drugsatfda_processor --mode all --max-applications 100
```

**Expected Output / 预期输出:**
- 100 Approval entities / 100 个批准实体
- 500-700 Submission entities / 500-700 个提交实体
- 100-200 DrugProduct entities / 100-200 个药物产品实体
- 1 RegulatoryAgency entity / 1 个监管机构实体
- 1000-2000 relationships / 1000-2000 个关系

#### 2. Query by Brand Name / 按品牌名查询

```bash
# Query Lipitor / 查询 Lipitor
python -m processors.drugsatfda_processor --mode brand-name --brand-name "Lipitor"
```

#### 3. Query by Application Number / 按申请号查询

```bash
# Query specific application / 查询特定申请
python -m processors.drugsatfda_processor --mode application-number --application-number "NDA020709"
```

#### 4. Query by Sponsor Name / 按赞助商名称查询

```bash
# Query Pfizer products / 查询 Pfizer 产品
python -m processors.drugsatfda_processor --mode sponsor-name --sponsor-name "Pfizer"
```

### Output Files / 输出文件

Files are saved to `/root/autodl-tmp/pj-pharmaKG/data/processed/documents/drugsatfda/` by default.

默认情况下，文件保存到 `/root/autodl-tmp/pj-pharmaKG/data/processed/documents/drugsatfda/`。

```
drugsatfda_regulatory_approvals_YYYYMMDD_HHMMSS.json
drugsatfda_regulatory_submissions_YYYYMMDD_HHMMSS.json
drugsatfda_rd_compounds_YYYYMMDD_HHMMSS.json
drugsatfda_rd_drugproducts_YYYYMMDD_HHMMSS.json
drugsatfda_regulatory_regulatoryagencies_YYYYMMDD_HHMMSS.json
drugsatfda_relationships_YYYYMMDD_HHMMSS.json
drugsatfda_summary_YYYYMMDD_HHMMSS.json
```

### Python API / Python API

```python
from processors.drugsatfda_processor import DrugsAtFDAProcessor

# Initialize processor / 初始化处理器
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

### Common Options / 常用选项

| Option / 选项 | Description / 描述 | Default / 默认值 |
|--------------|-------------------|------------------|
| `--max-applications` | Maximum applications to fetch / 要获取的最大申请数 | Unlimited / 无限制 |
| `--page-size` | Results per page / 每页结果数 | 100 |
| `--rate-limit` | Requests per second / 每秒请求数 | 1.0 |
| `--output` | Output directory / 输出目录 | data/processed/documents/drugsatfda/ |
| `--no-dedup` | Disable deduplication / 禁用去重 | False / 否 |
| `--no-cross-domain` | Disable cross-domain mapping / 禁用跨域映射 | False / 否 |
| `--save-raw` | Save raw API responses / 保存原始 API 响应 | False / 否 |
| `--verbose` | Verbose output / 详细输出 | False / 否 |

### Performance Tips / 性能提示

1. **For Testing / 用于测试:** Use `--max-applications 100` for quick tests
2. **For Production / 用于生产:** Remove `--max-applications` for full download
3. **Rate Limiting / 速率限制:** Keep `--rate-limit` at 1.0 for stability
4. **Cross-Domain / 跨域:** Use `--no-cross-domain` to speed up processing

### Troubleshooting / 故障排除

#### No Results Returned / 没有返回结果

```bash
# Try a simpler query / 尝试更简单的查询
python -m processors.drugsatfda_processor --mode all --max-applications 1 --verbose
```

#### Rate Limit Errors / 速率限制错误

```bash
# Slow down requests / 减慢请求速度
python -m processors.drugsatfda_processor --mode all --rate-limit 0.5
```

#### Timeout Errors / 超时错误

Check your internet connection and try again.

检查您的网络连接并重试。

### Next Steps / 下一步

1. **Validate Output / 验证输出:** Check the summary file for statistics
2. **Import to Neo4j / 导入到 Neo4j:** Use the ETL pipeline to import data
3. **Query Data / 查询数据:** Use the API to query imported data

For more details, see [DRUGSATFDA_PROCESSOR.md](DRUGSATFDA_PROCESSOR.md)

更多详情，请参阅 [DRUGSATFDA_PROCESSOR.md](DRUGSATFDA_PROCESSOR.md)
