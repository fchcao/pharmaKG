# PharmaKG Data Collection - Quick Start Guide
# PharmaKG 数据收集 - 快速入门指南

## Table of Contents / 目录

1. [Environment Setup / 环境设置](#environment-setup)
2. [Running Individual Processors / 运行单个处理器](#running-individual-processors)
3. [Running the Full Pipeline / 运行完整流水线](#running-the-full-pipeline)
4. [Common Workflows / 常见工作流程](#common-workflows)
5. [Troubleshooting / 故障排除](#troubleshooting)

---

## Environment Setup / 环境设置

### 1. Activate Conda Environment / 激活 Conda 环境

```bash
conda activate pharmakg-api
```

### 2. Install Required Dependencies / 安装所需依赖

```bash
cd /root/autodl-tmp/pj-pharmaKG
pip install -r api/requirements.txt

# Install additional dependencies for data processing
pip install pdfplumber PyPDF2 pytesseract beautifulsoup4 lxml

# For OCR support (optional)
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

### 3. Verify Neo4j Connection / 验证 Neo4j 连接

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Or check service
systemctl status neo4j

# Test connection
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!
```

### 4. Create Configuration File / 创建配置文件

```bash
# Copy example configuration
cp api/.env.example api/.env

# Edit with your settings
nano api/.env
```

---

## Running Individual Processors / 运行单个处理器

### Phase 1: R&D Data / 阶段1：研发数据

#### ChEMBL Processor

```bash
# Process ChEMBL 36 compounds (latest version)
python3 -m processors.chembl_processor data/sources/rd/chembl_36/chembl_36_sqlite/chembl_36.db

# Test with small batch
python3 -m processors.chembl_processor data/sources/rd/chembl_36/chembl_36_sqlite/chembl_36.db --limit-compounds 1000

# With custom batch size
python3 -m processors.chembl_processor data/sources/rd/chembl_36/chembl_36_sqlite/chembl_36.db --batch-size 5000
```

**注意**: ChEMBL 36 数据库需要 v1.1+ 版本的处理器。ChEMBL 36 于 2025年7月发布，包含 2.8M+ 化合物。

#### UniProt Processor

```bash
# Process UniProt IDs from file
python3 -m processors.uniprot_processor uniprot_ids.txt

# Search by organism
python3 -m processors.uniprot_processor --organism human --limit 100

# Extract IDs from ChEMBL data first
python3 scripts/extract_uniprot_from_chembl.py data/processed/entities/chembl_targets_*.json -o uniprot_ids.txt
```

#### KEGG Pathway Processor

```bash
# Get all human pathways
python3 -m processors.kegg_processor --organism human

# Get specific category
python3 -m processors.kegg_processor --organism human --category "Metabolism"

# Test with small amount
python3 -m processors.kegg_processor --organism human --limit 10
```

### Phase 2: Clinical Data / 阶段2：临床数据

#### ClinicalTrials.gov Processor

```bash
# Download all studies (will take many hours)
python3 -m processors.clinicaltrials_processor --mode full_download

# Query by disease
python3 -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"

# Get single study
python3 -m processors.clinicaltrials_processor --mode nct-id --nct-id "NCT00001234"

# Test with small batch
python3 -m processors.clinicaltrials_processor --mode full_download --max-studies 100
```

#### FDA Drugs@FDA Processor

```bash
# Get all applications
python3 -m processors.drugsatfda_processor --mode all --max-applications 100

# Query by brand name
python3 -m processors.drugsatfda_processor --mode brand-name --brand-name "Lipitor"

# Query by application number
python3 -m processors.drugsatfda_processor --mode application-number --application-number "NDA020709"
```

### Phase 3: Safety & Supply Chain / 阶段3：安全与供应链

#### FAERS Adverse Events Processor

```bash
# Process FAERS quarterly files
python3 -m processors.faers_processor data/sources/clinical/faers --max-reports 10000

# Process serious AEs only
python3 -m processors.faers_processor data/sources/clinical/faers --serious-only --max-reports 5000
```

#### Drug Shortages Processor

```bash
# Get all shortages
python3 -m processors.shortage_processor --mode all

# Filter by status
python3 -m processors.shortage_processor --mode status --status "Current"
```

#### PDA Technical Reports Processor

```bash
# Process single PDF
python3 -m processors.pda_pdf_processor data/sources/documents/PDA\ TR\ 全集/PDA\ TR1.pdf

# Batch process with limit
python3 -m processors.pda_pdf_processor data/sources/documents/PDA\ TR\ 全集 -l 10

# Process specific TR number
python3 -m processors.pda_pdf_processor data/sources/documents/PDA\ TR\ 全集 --tr TR13
```

### Phase 4: High-Value Datasets / 阶段4：高价值数据集

#### DrugBank Processor

```bash
# Requires DrugBank XML file (after license approval)
python3 -m processors.drugbank_processor data/sources/rd/drugbank.xml

# Filter by approval status
python3 -m processors.drugbank_processor data/sources/rd/drugbank.xml --approval-filter "Approved"
```

#### DailyMed Processor

```bash
# Download from API
python3 -m processors.dailymed_processor --mode api --max-spls 100

# Process local SPL files
python3 -m processors.dailymed_processor --mode files --path data/sources/documents/dailymed_spls
```

### Phase 5: Integration & Inference / 阶段5：集成与推理

#### Master Entity Mapping

```bash
# Build identifier mappings
python3 -m tools.build_master_entity_map \
    --data-dir data/processed \
    --output-dir data/validated \
    --batch-size 100
```

#### Cross-Domain Inference

```bash
# Run inference engine
python3 -m tools.infer_cross_domain_relationships \
    --output-dir data/validated \
    --confidence-threshold 0.6

# Dry run to test
python3 -m tools.infer_cross_domain_relationships \
    --output-dir data/validated \
    --dry-run
```

---

## Running the Full Pipeline / 运行完整流水线

### Basic Usage / 基本用法

```bash
# Run all phases
python3 scripts/run_full_pipeline.py

# Run specific phase
python3 scripts/run_full_pipeline.py --phase 1

# Dry run to see what would be executed
python3 scripts/run_full_pipeline.py --dry-run
```

### Custom Configuration / 自定义配置

```bash
# Create custom configuration
cat > config/my_config.json << EOF
{
  "phase_1": {
    "chembl": {
      "enabled": true,
      "limit_compounds": 10000
    }
  },
  "phase_2": {
    "clinicaltrials": {
      "enabled": true,
      "max_studies": 5000
    }
  }
}
EOF

# Run with custom configuration
python3 scripts/run_full_pipeline.py --config config/my_config.json
```

---

## Common Workflows / 常见工作流程

### Workflow 1: Start with ChEMBL Data / 工作流程1：从 ChEMBL 数据开始

```bash
# 1. Process ChEMBL compounds (small batch first)
python3 -m processors.chembl_processor \
    data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db \
    --limit-compounds 1000

# 2. Extract UniProt IDs from targets
python3 scripts/extract_uniprot_from_chembl.py \
    data/processed/entities/chembl_targets_*.json \
    -o uniprot_ids.txt

# 3. Enhance with UniProt data
python3 -m processors.uniprot_processor uniprot_ids.txt

# 4. Get pathways for targets
python3 -m processors.kegg_processor --organism human --limit 50

# 5. Build master entity map
python3 -m tools.build_master_entity_map
```

### Workflow 2: Clinical Trial Integration / 工作流程2：临床试验集成

```bash
# 1. Download clinical trials for a disease
python3 -m processors.clinicaltrials_processor \
    --mode query_by_disease \
    --query-term "Alzheimer's" \
    --max-studies 500

# 2. Get FDA approvals for related drugs
python3 -m processors.drugsatfda_processor --mode all --max-applications 1000

# 3. Build entity map to link trials to approvals
python3 -m tools.build_master_entity_map

# 4. Run inference for drug repurposing
python3 -m tools.infer_cross_domain_relationships --confidence-threshold 0.7
```

### Workflow 3: Supply Chain Risk Analysis / 工作流程3：供应链风险分析

```bash
# 1. Get current drug shortages
python3 -m processors.shortage_processor --mode status --status "Current"

# 2. Process PDA technical reports for manufacturing knowledge
python3 -m processors.pda_pdf_processor \
    data/sources/documents/PDA\ TR\ 全集 \
    --tr TR13 --tr TR22

# 3. Build entity map
python3 -m tools.build_master_entity_map

# 4. Run supply chain risk inference
python3 -m tools.infer_cross_domain_relationships
```

---

## Troubleshooting / 故障排除

### Issue 1: Neo4j Connection Failed / 问题1：Neo4j 连接失败

```bash
# Check Neo4j is running
docker ps | grep neo4j

# If not running, start Neo4j
docker-compose up -d neo4j

# Or if using system service
sudo systemctl start neo4j

# Verify connection
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!
```

### Issue 2: Memory Issues with Large Files / 问题2：大文件内存问题

```bash
# Reduce batch size
python3 -m processors.chembl_processor chembl_34.db --batch-size 1000

# Process in chunks
python3 -m processors.chembl_processor chembl_34.db --limit-compounds 10000

# Increase Neo4j heap size
# Edit neo4j.conf: dbms.memory.heap.initial_size=16g
# Edit neo4j.conf: dbms.memory.heap.max_size=16g
```

### Issue 3: API Rate Limits / 问题3：API 速率限制

```bash
# Most processors have built-in rate limiting
# Adjust if needed by editing processor configuration

# For ClinicalTrials.gov (2 req/sec default):
# Edit processors/clinicaltrials_processor.py
# Change: DEFAULT_RATE_LIMIT = 0.5  # seconds per request

# For UniProt (10 req/sec default):
# Edit processors/uniprot_processor.py
# Change: DEFAULT_RATE_LIMIT = 0.1  # seconds per request
```

### Issue 4: PDF Processing Errors / 问题4：PDF 处理错误

```bash
# Check if PDF is readable
pdfplumber --version

# For scanned PDFs, install OCR
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Test OCR on a PDF
python3 -c "
import pytesseract
from pdf2image import convert_from_path
images = convert_from_path('test.pdf')
text = pytesseract.image_to_string(images[0])
print(text)
"
```

### Issue 5: Missing Data Files / 问题5：缺少数据文件

```bash
# Check available data
ls -lh data/sources/

# Download ChEMBL if missing
cd data/sources/rd/
wget https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/ChEMBL34/chembl_34_sqlite.tar.gz
tar -xzf chembl_34_sqlite.tar.gz

# Download DrugBank (requires license approval)
# Visit: https://go.drugbank.com/releases/latest
```

---

## Performance Tips / 性能提示

### 1. Parallel Processing / 并行处理

```bash
# Run multiple phases in parallel (if independent)
python3 scripts/run_full_pipeline.py --phase 1 &
python3 scripts/run_full_pipeline.py --phase 3 &
wait
```

### 2. Batch Sizing / 批处理大小

```bash
# For faster processing (uses more memory)
--batch-size 20000

# For lower memory usage
--batch-size 1000
```

### 3. Neo4j Optimization / Neo4j 优化

```bash
# Create indexes before importing large datasets
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024! < deploy/scripts/init_constraints.cypher

# Or via API (if endpoint available)
curl -X POST http://localhost:8000/api/v1/admin/init-schema
```

---

## Monitoring Progress / 监控进度

### Check Log Files / 检查日志文件

```bash
# Pipeline log
tail -f data_collection_pipeline.log

# Processor-specific logs
tail -f data/processed/*_summary.json
```

### Check Neo4j Statistics / 检查 Neo4j 统计信息

```bash
# Count nodes by label
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024! \
  "MATCH (n) RETURN labels(n) as label, count(*) as count ORDER BY count DESC"

# Count relationships by type
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024! \
  "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC"

# Check connection rate
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024! \
  "MATCH (n) WHERE size((n)-[]-()) > 0 RETURN count(*)"
```

---

## Getting Help / 获取帮助

### Documentation / 文档

- Complete Implementation Summary: `docs/COMPLETE_IMPLEMENTATION_SUMMARY.md`
- Individual Processor Documentation: `docs/*_PROCESSOR.md`
- API Documentation: http://localhost:8000/docs (when API is running)

### Test Processors / 测试处理器

```bash
# Run processor tests
python3 scripts/test_chembl_processor.py
python3 scripts/test_uniprot_processor.py
python3 scripts/test_clinicaltrials_processor.py
# ... etc
```

### Check Status / 检查状态

```bash
# Validate project setup
python3 scripts/check_project.py

# Check processed data
ls -lh data/processed/entities/
ls -lh data/processed/relationships/
```

---

## Quick Reference / 快速参考

### Essential Commands / 基本命令

| Task | Command |
|------|---------|
| Process ChEMBL | `python3 -m processors.chembl_processor chembl_34.db` |
| Query ClinicalTrials | `python3 -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"` |
| Get Drug Shortages | `python3 -m processors.shortage_processor --mode all` |
| Build Entity Map | `python3 -m tools.build_master_entity_map` |
| Run Inference | `python3 -m tools.infer_cross_domain_relationships` |
| Run Full Pipeline | `python3 scripts/run_full_pipeline.py` |

### Output Locations / 输出位置

| Data Type | Location |
|-----------|----------|
| Processed Entities | `data/processed/entities/` |
| Processed Relationships | `data/processed/relationships/` |
| Validated Data | `data/validated/` |
| Summary Reports | `data/processed/*_summary.json` |

---

**Last Updated:** 2026-02-08
**For Questions:** Check individual processor documentation in `docs/` directory

**最后更新：** 2026-02-08
**如有问题：** 查看 `docs/` 目录中的单个处理器文档
