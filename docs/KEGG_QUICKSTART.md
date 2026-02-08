# KEGG Pathway Processor - Quick Start Guide
# KEGG 通路处理器 - 快速入门指南

## 快速开始 | Quick Start

### 1. 基本使用 | Basic Usage

```bash
# 获取人类所有通路（推荐先测试少量数据）
python -m processors.kegg_processor --organism human --limit 10

# 获取特定分类的通路
python -m processors.kegg_processor --organism human --category "Metabolism" --limit 20

# 从文件处理通路 ID
python -m processors.kegg_processor /path/to/pathway_ids.txt
```

### 2. 创建通路 ID 文件 | Create Pathway ID File

创建文本文件 `pathway_ids.txt`：
Create a text file `pathway_ids.txt`:

```
path:hsa04110
path:hsa04115
path:hsa04120
path:hsa04151
path:hsa04152
```

### 3. 查看输出 | View Output

输出文件保存在：`data/processed/documents/kegg/`

Output files are saved at: `data/processed/documents/kegg/`

```bash
# 查看最新的输出
ls -lt data/processed/documents/kegg/

# 查看摘要文件
cat data/processed/documents/kegg/kegg_summary_*.json | jq .
```

## 常用场景 | Common Scenarios

### 场景 1: 研究特定通路 | Scenario 1: Study Specific Pathways

```bash
# 细胞周期相关通路
python -m processors.kegg_processor --organism human --category "Cellular" --limit 30

# 癌症相关通路
python -m processors.kegg_processor --organism human --category "Cancers" --limit 50
```

### 场景 2: 跨物种比较 | Scenario 2: Cross-species Comparison

```bash
# 人类
python -m processors.kegg_processor --organism human --limit 100 --output human_output

# 小鼠
python -m processors.kegg_processor --organism mouse --limit 100 --output mouse_output

# 大鼠
python -m processors.kegg_processor --organism rat --limit 100 --output rat_output
```

### 场景 3: 与 ChEMBL 数据集成 | Scenario 3: Integration with ChEMBL Data

```python
from processors.kegg_processor import KEGGProcessor, OrganismCode
from processors.chembl_processor import ChEMBLProcessor

# 1. 获取 KEGG 通路数据
kegg_config = {
    'extraction': {
        'batch_size': 50,
        'rate_limit': 10.0,
        'map_kegg_to_uniprot': True  # 启用 UniProt 映射
    }
}

kegg_processor = KEGGProcessor(kegg_config)
pathways_data = kegg_processor.fetch_pathways_by_organism(
    organism=OrganismCode.HUMAN,
    limit=100
)

# 2. 获取 ChEMBL 靶点数据
chembl_config = {
    'extraction': {
        'limit_targets': 1000
    }
}

chembl_processor = ChEMBLProcessor(chembl_config)
# ... 处理 ChEMBL 数据
```

## 性能优化建议 | Performance Optimization Tips

1. **启用缓存** | Enable Caching
   ```bash
   # 缓存默认启用，避免使用 --no-cache
   python -m processors.kegg_processor --organism human --limit 100
   ```

2. **调整批处理大小** | Adjust Batch Size
   ```bash
   # 网络良好时可以增加批处理大小
   python -m processors.kegg_processor --organism human --batch-size 100 --limit 500
   ```

3. **使用适当的速率限制** | Use Appropriate Rate Limit
   ```bash
   # 网络不稳定时降低速率限制
   python -m processors.kegg_processor --organism human --rate-limit 5.0 --limit 100
   ```

## 故障排除 | Troubleshooting

### 问题 1: API 连接失败

```bash
# 检查 KEGG API 是否可访问
curl -I http://rest.kegg.jp/list/pathway/hsa

# 如果失败，可能是网络问题或 KEGG API 维护
```

### 问题 2: 缓存损坏

```bash
# 删除缓存文件
rm data/cache/kegg_cache.db

# 重新运行处理
python -m processors.kegg_processor --organism human --limit 10
```

### 问题 3: 内存不足

```bash
# 减少批处理大小
python -m processors.kegg_processor --organism human --batch-size 10 --limit 50
```

## 数据验证 | Data Validation

### 检查提取的数据

```python
import json

# 读取摘要文件
with open('data/processed/documents/kegg/kegg_summary_*.json') as f:
    summary = json.load(f)

print(f"通路数量: {summary['statistics']['pathways_extracted']}")
print(f"基因数量: {summary['statistics']['genes_extracted']}")
print(f"关系数量: {summary['statistics']['relationships_created']}")

# 检查错误和警告
if summary['errors']:
    print("错误:")
    for error in summary['errors']:
        print(f"  - {error}")

if summary['warnings']:
    print("警告:")
    for warning in summary['warnings']:
        print(f"  - {warning}")
```

## 下一步 | Next Steps

1. **集成到知识图谱** | Integrate into Knowledge Graph
   - 使用 Neo4j 导入工具加载提取的数据
   - Use Neo4j import tools to load extracted data

2. **与其他数据源结合** | Combine with Other Data Sources
   - ChEMBL: 生物活性数据
   - UniProt: 蛋白质详细信息
   - ClinicalTrials.gov: 临床试验数据

3. **分析和可视化** | Analysis and Visualization
   - 使用 Neo4j Browser 查询通路数据
   - 使用 graph_analytics 模块进行图分析
   - Use Neo4j Browser to query pathway data
   - Use graph_analytics module for graph analysis

## 引用 | Citation

如果使用此处理器，请引用：

If you use this processor, please cite:

```
Kanehisa, M., Furumichi, M., Sato, Y., Kawashima, M., et al. (2024)
KEGG for representation and analysis of molecular networks
involving diseases and drugs. Nucleic Acids Res. 50:D621-D628.
```
