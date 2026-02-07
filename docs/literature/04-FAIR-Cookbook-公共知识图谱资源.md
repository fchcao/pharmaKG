# FAIR Cookbook - Public Knowledge Graph Resources for Life Sciences

**来源**: https://faircookbook.elixir-europe.org/content/recipes/introduction/public-kg-resource-integration.html
**组织**: ELIXIR Europe

---

## 摘要

本文概述了生命科学领域可用的公共知识图谱资源，包括OpenTarget、Pharos、Hetionet等，以及它们在药物靶点识别、数据集成和互操作性方面的应用。

## 主要目标

1. **已知的参考知识图谱**及其集成方式
2. **不同的科学场景**
3. **对制药行业和EFPIA的影响**

## 背景：欧盟创新药物倡议（IMI）的三种主要场景

1. **识别新药物靶点**（如IMI Resolute项目）
   - 表征溶质载体
   - 识别潜在的可成药候选物

2. **开发新的治疗产品和技术**（如IMI AETIONOMY项目）
   - 针对特定疾病领域

3. **发现针对病原体的新药**（如ND4BB项目）
   - 新药用于坏细菌

## 公共知识图谱资源目录

### 1. OpenTarget

**项目性质**：公私合作伙伴关系

**核心功能**：
- 提供基于公共领域数据的中央资源
- 支持靶点识别和优先级排序
- 基于功能基因组学和GWAS数据

**方法论**：
- 全基因组、基于证据的方法
- 提供关于经验证靶点的可靠信息

**数据访问**：
- GraphQL API: https://api.genetics.opentargets.org/graphql
- Google BigQuery接口
- FTP下载
- AWS云服务

**语义资源集成**：
- **EFO**: 实验因子本体 + Open Target slim (EFO-OTAR)
- **MONDO**: 疾病
- **HPO**: 临床体征、症状和表型
- **ECO**: 证据代码本体，注释发现的置信度和可靠性

**示例GraphQL查询**：
```graphql
query genePrioritisationUsingL2G {
  studyLocus2GeneTable(studyId: "FINNGEN_R5_E4_DM2", variantId: "11_72752390_G_A") {
    rows {
      gene { symbol id }
      yProbaModel
      yProbaDistance
      yProbaInteraction
      hasColoc
    }
  }
}
```

### 2. Pharos

**项目性质**：美国NIH资助项目（欧洲OpenTarget的对应项目）

**背景项目**：
- Illuminating the Druggable Genome (IDG) 项目
- Target Central Resource Database (TCRD)

**数据整合**：来自66个不同数据源

**信息组织**：
- **疾病** (Diseases)
- **靶点** (Targets)
- **配体** (Ligands)

**API访问**：https://pharos.nih.gov/api

**本体集成**：
- **Drug Target Ontology (DTO)**: 自定义构建本体
- **DO**: Disease Ontology
- **GO**: Gene Ontology
- **BAO**: BioAssay Ontology
- **GPCRO**: GPCR Ontology

**开源**：MIT许可证，代码https://spotlite.nih.gov/ncats/pharos

### 3. Hetionet

**主要目的**：预测现有药物的新用途（Project Rephetio）

**规模**（v1.0）：
- **节点**: 47,031个，11种类型
- **关系**: 2,250,197个，24种类型
- **数据源**: 29个资源

**连接实体**：
- 化合物
- 疾病
- 基因
- 解剖
- 通路
- 生物过程
- 分子功能
- 细胞组分
- 药理学类别
- 副作用
- 症状

**格式可用**：
- JSON
- Neo4j
- TSV
- Matrix

**GitHub**: https://github.com/hetio/hetionet

**许可证**: CC0

**语义集成（本体"slims"）**：
- **DO**: 疾病本体slim，137个术语
- **MESH**: 体征和症状，438个术语
- **SIDER**: 副作用
- **GO**: 生物过程、细胞组分、分子功能
- **UBERON**: 解剖学术语

**化学信息映射**：使用InChI键明确指定化学结构

### 4. Drug Repurposing Knowledge Graph (DRKG)

**描述**：综合生物KG，关联基因、化合物、疾病、生物过程、副作用和症状

**数据源整合**（6个）：
- DrugBank
- Hetionet
- GNBR
- STRING
- IntAct
- DGIdb
- 近期出版物（特别是COVID-19相关）

**规模**：
- **实体**: 97,238个，13种实体类型
- **三元组**: 5,874,261个，107种边类型

**GitHub**: https://github.com/gnn4dr/DRKG/

**Jupyter notebooks**：展示如何使用KG通过预训练模型探索药物重定位可能性

### 5. OpenBioLink

**描述**：开放基准数据集，用于链接预测模型的训练或评估

**性质**：大型独立资源集合，通过蛋白质连接药物与疾病

**数据源**：
- STRING
- GO
- DisGeNET
- HPO
- STITCH
- CTD
- HPO
- DrugCentral
- SIDER

**规模**：
- **实体**: 24,806个（药物、蛋白质、指征或表型）
- **三元组**: 2,358,881个，4种边类型

**GitHub**: https://openbiolink.github.io/

**使用示例**：
```python
from openbiolink.obl2021 import OBL2021Dataset

dl = OBL2021Dataset()
train = dl.training  # torch.tensor of shape(num_train,3)
valid = dl.validation  # torch.tensor of shape(num_val,3)
```

### 6. Clinical Knowledge Graph (CKG)

**描述**：开源平台，整合相关实验数据、公共数据库和文献

**规模**：
- **节点**: 超过1600万个
- **关系**: 2.2亿个

**语义资源集成**：
- **DO**: Disease Ontology
- **BTO**: Brenda Tissue Ontology（解剖实体和组织）
- **EFO**: Experimental Factor Ontology
- **HPO**: Human Phenotype Ontology
- **GO**: Gene Ontology
- **SNOMED-CT**: 定义临床术语及其关联关系

**数据可用性**：
- 可通过Neo4j图数据库加载和查询
- 数据转储：https://data.mendeley.com/datasets/mrcf7f4tc2/1

**GitHub**: https://github.com/MannLabs/CKG（MIT许可证）

### 7. AstraZeneca Biological Insights Knowledge Graph (BIKG)

**性质**：阿斯利康开发的资源

**功能**：结合公共和内部数据，支持机器学习知识发现

**构建方法**：
- 专门的信息提取管道
- 挖掘非结构化文本（全文出版物）使用NLP技术
- 从专业数据库获取信息（ChEMBL, Ensembl等）
- 整合Hetionet和Open Target数据集

**规模**（最新版本）：
- **节点**: 1090万个，22种类型
- **边**: 超过1.18亿条唯一边，59种类型，形成398种不同三元组

**特点**：第三方数据集集成能力，涉及ETL到BIKG语义模型和BIKG ULO（上本体）

**本体兼容性**：
- **UBERON**: 解剖学术语
- **GO**: 生物过程、细胞组分、分子功能

**访问方式**：
- GraphQL API
- 导出格式：RDF或Neo4j/CSV

**用例**：
1. 靶点识别
2. CRISPR筛选命中排序

### 8. PyKEEN

**性质**：Python库，用于训练和评估知识图谱嵌入模型（KGEM）

**GitHub**: https://github.com/pykeen/pykeen

**特点**：
- 整合多模态信息
- 包含许多参考KG和数据集
- 主要用于链接预测任务

**使用示例**：
```python
from pykeen.pipeline import pipeline

result = pipeline(
    model='TransE',
    dataset='nations',
)
```

## Yummydata：生命科学SPARQL端点目录

**维护者**：日本柏市的生命科学数据库中心

**功能**：
- SPARQL端点注册表
- 监控服务
- 定期检查索引资源的"健康状态"

**Umaka评分**：根据6个维度整合端点状态：
- 可用性 (Availability)
- 新鲜度 (Freshness)
- 运行 (Operation)
- 有用性 (Usefulness)
- 有效性 (Validity)
- 性能 (Performance)

**网站**: http://yummydata.org/

## 关键洞察总结

### 数据集成模式

1. **标准化本体使用**：
   - 大多数项目复用成熟本体（GO, DO, HPO等）
   - 本体"slims"用于简化大规模集成

2. **标识符策略**：
   - InChI键用于化学结构
   - UniProt用于蛋白质
   - 标准化疾病术语（DO, MONDO）

3. **访问接口多样性**：
   - SPARQL端点
   - GraphQL API
   - REST API
   - 数据下载（TSV, JSON, Neo4j）

4. **开源与开放许可**：
   - 大多数提供开源代码（MIT, Apache 2.0）
   - 数据采用开放许可（CC0, CC-BY）

### Schema设计特点

**核心实体类型**：
- 化学品/药物 (Chemicals/Drugs)
- 基因/蛋白质 (Genes/Proteins)
- 疾病 (Diseases)
- 表型 (Phenotypes)
- 通路 (Pathways)
- 解剖 (Anatomy)

**关系类型**：
- 治疗关系 (treats)
- 关联关系 (associated_with)
- 参与关系 (participates_in)
- 调节关系 (regulates)

---

## 与制药行业知识图谱的相关性

1. **药物发现阶段**：
   - OpenTarget：靶点识别和优先级排序
   - Pharos：可成药基因组知识
   - Hetionet：药物重定位

2. **数据集成策略**：
   - 多源数据整合模式
   - 本体标准化方法
   - API设计参考

3. **工具选择**：
   - Neo4j用于图存储
   - GraphQL用于API
   - PyKEEN用于图嵌入

4. **互操作性**：
   - 标准本体复用
   - 持久化标识符
   - FAIR原则实践
