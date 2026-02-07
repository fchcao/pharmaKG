# IntuitionLabs - Biotech Knowledge Graphs: Architecture for Data Integration

**来源**: https://intuitionlabs.ai/pdfs/biotech-knowledge-graphs-architecture-for-data-integration.pdf
**日期**: 2025-12-05
**作者**: Adrien Laurent, CEO at IntuitionLabs

---

## 执行摘要

本文详细介绍了构建综合生物技术知识图谱的架构模式和知识表示策略，该图谱语义化地链接化合物、实验、靶点和结果。

## 核心内容

### 1. 数据源与本体

#### 关键数据源/本体

| 类别 | 数据源/本体 | 内容描述 |
|-----|------------|---------|
| **化合物/药物** | ChEMBL, PubChem, DrugBank, ChEBI | 生物活性分子、小化合物、标识符（SMILES, InChI）、同义词、生物活性链接 |
| **实验/生物活性** | ChEMBL BioAssays, PubChem BioAssays, BindingDB | 实验方案、测试靶点、结果测量（IC50, Ki）及单位 |
| **靶点/蛋白质** | UniProt, Entrez Gene, Ensembl, PDBe, PharmGKB, TTD | 基因和蛋白质实体、序列、功能注释（GO域）、已知药物-靶点相互作用 |
| **通路** | Reactome, KEGG, WikiPathways, MetaCyc | 链接蛋白质、酶和过程的生物通路和网络 |
| **疾病/表型** | Disease Ontology, MeSH, MONDO, HPO, OMIM | 用于关联靶点和药物到临床结果的标准化疾病和表型术语 |
| **结果/现象** | BioAssay Ontology (BAO), SIDER, ClinVar, FAERS | 实验结果的本体描述（如IC50）；记录的临床结果或毒性 |
| **文献/基因** | PubMed, CORD-19, Bio2RDF/Linked Open Data | 通过策划或提取的关系链接实体（药物、基因）的出版物和文本挖掘 |

### 2. 架构模式

#### 批处理 vs 流式集成

| 模式 | 描述 | 优点 | 局限 |
|-----|------|------|------|
| **批处理加载 (RDF)** | 数据已为RDF或易转换；更新不频繁 | 简单，在三元组存储中支持良好；全图替换 | 加载时长时间停机；锁定图；非增量 |
| **ETL (批处理)** | 表格/JSON形式数据；离线转换为RDF然后加载 | 对转换高度控制；可使用脚本/工具 | 每次更新需要重新运行；初始开发成本 |
| **ELT (图内)** | RDF格式数据但需要模式对齐/合并 | 可使用SPARQL/OWL进行语义合并；增量更新 | 复杂查询；需要仔细的溯源跟踪 |
| **流式复制** | 持续增量更新（如新实验结果） | 近实时集成；避免大批量加载 | 需要流式基础设施；管道复杂性 |
| **虚拟化** | 外部数据库中的数据（敏感或动态）；无复制 | 始终最新；无数据重复 | 查询功能有限；连接性能差；需要严格模式 |

#### 标识符映射服务

```
统一ID系统:
├── Chemical: InChIKey (主), PubChem CID, ChEMBL ID
├── Gene: HGNC Symbol (主), Ensembl ID, Entrez ID
├── Disease: MONDO ID (主), DOID, ICD-10, SNOMED-CT
├── Drug: RxNorm CUI (主), DrugBank ID, ATC Code
└── Trial: NCT Number (主), EudraCT, JCTC
```

### 3. 语义建模与本体

#### 建模要素

**化合物和靶点分类**：
- 小分子的子类（SmallMolecule vs ChemicalEntity）
- 靶点子类（基因、蛋白质）
- 持久标识符（ChEMBL ID、PubChem CID、UniProt登录号）作为唯一节点ID
- 化学结构可存储为InChIKey属性

**实验本体**：
- 使用BAO，实验按格式（细胞基、生化、报告基因等）和终点类型分类
- 规范化的"IC50"概念确保测量IC50的实验查询能捕获所有语义等效的结果
- 本体还定义了has_assay_format、has_qc_criteria等关系

**结果表示**：
- 结果可以是定量的（如效力IC50）或分类的（活性/非活性）
- 加载实验结果时，将结果列映射到本体术语（如bao:IC50表示效力）

**溯源**：
- 通过具体化或命名图跟踪溯源（源数据集、出版物、时间戳）
- 允许用户信任或过滤断言

### 4. 案例研究

#### Open PHACTS发现平台

**数据源**：ChEMBL, ChEBI, DrugBank, ChemSpider, UniProt, GO, WikiPathways, Enzyme

**关键洞察**：
- 溯源和语义互操作性：目录化许可和数据溯源
- API + 工具：直观的API和客户端库
- 用例结果：链接简化数据简化了靶点验证和化合物探索

**示例查询**：
> "查找所有在ErbB信号通路中涉及的靶点上有活性、并且与疾病X有相关的化学化合物"

#### Chem2Bio2RDF

- 聚合DrugBank, KEGG, PDB, GO, OMIM等数据集
- 引入了链接路径生成工具帮助研究人员制定SPARQL查询
- 量化KG：约100万个三元组链接化合物、约7万个蛋白质、通路和副作用

#### FORUM知识图谱（代谢组学）

- 数据源：PubChem, MeSH, 科学文献
- 语义富集：使用ChEBI化学分类、MeSH疾病层次
- SPARQL端点可用

#### Knowledge4COVID-19

- 整合DrugBank、UMLS词汇表、CORD-19文献
- 使用RML（RDF映射语言）进行声明性映射
- NLP：NER标注文献并映射实体到模式类

### 5. 生物医学知识图谱比较

| KG名称 | 范围/用例 | 实体 | 三元组 | 关键数据源 | 显著特征 |
|-------|----------|------|--------|-----------|---------|
| **Hetionet** | 药物重定位；通用发现 | ~47K | ~2.2M | EntrezGene, DrugBank, DisGeNET, Reactome, GO | 首批药物聚焦KG之一；集成多种类型 |
| **DRKG** | COVID-19药物重定位 | ~97K | ~5.7M | STRING, DrugBank, GNBR, Hetionet | 包含预计算图嵌入 |
| **BioKG** | 通用生物医学集成 | ~105K | ~2.0M | UniProt, Reactome, OMIM, GO | 链接多个本体 |
| **PharmKG** | 药物发现KG（ML聚焦） | ~7.6K | ~0.5M | OMIM, DrugBank, PharmGKB, TTD | 紧凑、高质量；节点数值特征 |
| **OpenBioLink** | KG完成方法基准 | ~184K | ~4.7M | STRING, DisGeNET, GO, CTD等17个源 | 带负样本的基准KG |
| **PrimeKG** | 精准医学（疾病根） | ~129K | ~4.05M | DisGeNET, Mayo Clinic KB, MONDO | 多模态；包含"矛盾"边 |

### 6. 集成管道和工具

#### 类别

1. **RDF三元组存储和图数据库**：
   - RDF存储：GraphDB, Blazegraph, Apache Jena, Virtuoso
   - 属性图引擎：Neo4j, TigerGraph, AWS Neptune

2. **ETL和映射平台**：
   - Ontop（RDB-to-RDF）、TripleCandy、RDFLib
   - 工作流系统：KNIME, Apache NiFi, Pentaho

3. **标识符和本体服务**：
   - UniChem（化合物）、BioPortal、EMBL OLS
   - 本体对齐工具：OntoRefine, PROMPT

4. **API和微服务**：
   - RESTful API、GraphQL API
   - 容器化（Docker/Kubernetes）

5. **图分析和ML库**：
   - DGL, PyTorch Geometric, NetworkX
   - 图算法：聚类、嵌入、链接预测

6. **语义推理器**：
   - OWL推理器：Pellet, Hermit
   - GraphDB和Fuseki内置OWL支持

### 7. 分析能力

- **复杂查询**：多跳连接（化合物-实验-靶点-通路-不良事件）
- **链接预测**：图嵌入（node2vec, TransE, DistMult）预测新边
- **路径排序和可解释性**：元路径计数、基于路径的ML
- **ML/DL集成**：KG嵌入输入标准ML模型
- **本体推理**：BAO等本体支持演绎推理
- **统计分析**：通路富集等聚合图数据

### 8. 挑战与未来方向

#### 挑战

1. **数据质量和许可**：异构数据格式不一致、标识符不一致、许可限制
2. **可扩展性**：超大图或复杂分析的扩展性
3. **模式演化**：生物医学知识演变，KG必须适应
4. **非结构化数据集成**：文本中的知识，NLP+KG管道无损性
5. **可解释性**：基于路径的解释需要底层数据可解释
6. **隐私和安全**：临床结果或患者数据的隐私保护

#### 未来方向

1. **FAIR和开放数据**：强调可发现性和可重用性
2. **AI集成**：图神经网络、嵌入模型
3. **语义层到数据湖**：数据湖与语义层的结合
4. **基准和标准**：KG基准（OpenBioLink, Hetionet）
5. **本体集中化**：UMLS, OBO Foundry

## 架构图概念

```
数据源层         集成层           图存储        服务层
─────────────────────────────────────────────────────────
ChEMBL   │           ETL/RML  │    GraphDB    │  SPARQL
PubChem  │──────▶    Mapping  │────▶  Store  │────▶  API
UniProt  │                    │              │  GraphQL
GO       │                    │              │  工作流
                  ↑
           Ontologies & ID Services
```

## 关键洞察总结

1. **语义集成是核心**：通过持久化URI、本体映射、标识符对齐实现跨源数据统一
2. **架构模式选择**：根据数据特性（频率、量级、敏感性）选择ETL/ELT/虚拟化/流式
3. **本体驱动**：BAO、GO等本体提供语义骨干，支持推理和跨数据集查询
4. **案例验证**：Open PHACTS、Chem2Bio2RDF、FORUM、Knowledge4COVID-19等证明架构可行性
5. **工具生态**：从ETL工具到图数据库、ML库的完整工具链支持
6. **FAIR原则**：全局唯一ID、丰富元数据、标准化词汇表确保互操作性

---

## 与制药行业知识图谱的相关性

本文提供了制药行业R&D阶段知识图谱的完整架构框架：
- 多源数据集成策略（化合物、实验、靶点、疾病）
- ETL/ELT/虚拟化等架构模式的选择标准
- 标识符映射和本体对齐方案
- 从Open PHACTS等实际案例学习的经验
- 分析能力（链接预测、路径分析）的实现方法
