# ChEMBL Processor Quick Start Guide / ChEMBL 处理器快速入门

## 快速开始 / Quick Start

### 1. 安装依赖 / Install Dependencies

```bash
# 激活 conda 环境
conda activate pharmakg-api

# 依赖已包含在环境中
pip install -r api/requirements.txt  # 如果需要
```

### 2. 准备数据 / Prepare Data

确保 ChEMBL 数据库已下载到正确位置：

```bash
# 数据库路径
/path/to/pj-pharmaKG/data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db
```

### 3. 运行处理器 / Run Processor

#### 方式一：命令行 / Command Line

```bash
# 基本使用
python -m processors.chembl_processor data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db

# 小批量测试
python -m processors.chembl_processor data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db \
    --limit-compounds 100 \
    --limit-activities 500 \
    --batch-size 100

# 完整提取
python -m processors.chembl_processor data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db \
    --min-confidence 8 \
    --batch-size 10000
```

#### 方式二：Python 代码 / Python Code

```python
from processors.chembl_processor import ChEMBLProcessor

# 创建处理器
processor = ChEMBLProcessor()

# 运行处理
result = processor.process(
    source_path='data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db'
)

# 查看结果
print(f"提取了 {result.metrics.entities_extracted} 个实体")
print(f"提取了 {result.metrics.relationships_extracted} 个关系")
```

### 4. 查看输出 / Check Output

输出文件位置：

```
data/processed/documents/chembl/
├── chembl_compounds_YYYYMMDD_HHMMSS.json
├── chembl_targets_YYYYMMDD_HHMMSS.json
├── chembl_assays_YYYYMMDD_HHMMSS.json
├── chembl_pathways_YYYYMMDD_HHMMSS.json
├── chembl_relationships_YYYYMMDD_HHMMSS.json
└── chembl_summary_YYYYMMDD_HHMMSS.json
```

## 常用参数 / Common Parameters

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--limit-compounds` | 化合物数量限制 | 无限制 |
| `--limit-activities` | 活性数据限制 | 无限制 |
| `--min-confidence` | 最小置信度 | 8 |
| `--batch-size` | 批处理大小 | 10000 |
| `--no-dedup` | 禁用去重 | 启用 |
| `--include-children` | 包含子分子 | 仅父分子 |

## 示例 / Examples

### 示例 1：提取 1000 个化合物和相关数据

```bash
python -m processors.chembl_processor \
    data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db \
    --limit-compounds 1000
```

### 示例 2：高质量数据提取（pChEMBL >= 9）

```bash
python -m processors.chembl_processor \
    data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db \
    --min-confidence 9
```

### 示例 3：快速测试

```bash
python -m processors.chembl_processor \
    data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db \
    --limit-compounds 50 \
    --limit-activities 100 \
    --batch-size 50
```

## 故障排除 / Troubleshooting

### 数据库损坏

```bash
# 重新下载 ChEMBL 数据库
cd data/sources/rd/chembl_34/chembl_34_sqlite
wget https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_34_sqlite.tar.gz
tar -xzf chembl_34_sqlite.tar.gz
```

### 内存不足

```bash
# 减小批处理大小
python -m processors.chembl_processor chembl_34.db --batch-size 1000
```

### 导入错误

```bash
# 确保在项目根目录运行
cd /root/autodl-tmp/pj-pharmaKG
python -m processors.chembl_processor data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db
```

## 下一步 / Next Steps

1. 查看详细文档：`docs/CHEMBL_PROCESSOR.md`
2. 集成到 ETL Pipeline
3. 导入到 Neo4j 知识图谱
4. 运行图分析和查询

## 获取帮助 / Get Help

```bash
# 查看命令行帮助
python -m processors.chembl_processor --help
```

## 联系 / Contact

- 项目仓库: [PharmaKG GitHub](https://github.com/your-org/pj-pharmaKG)
- 问题反馈: [GitHub Issues](https://github.com/your-org/pj-pharmaKG/issues)
