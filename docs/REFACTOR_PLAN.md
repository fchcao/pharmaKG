# PharmaKG 项目重构计划

## 一、问题分析

### 当前问题
1. **节点孤立**：导入的589个节点之间没有关系，只是一堆分散的点
2. **脚本混乱**：临时脚本多，难以复用，没有清晰的分层
3. **流程缺失**：没有完整的数据分类→清洗→提取→处理→归档流程
4. **文档孤立**：文档之间没有关联关系

### 根本原因
- **数据导入只关注节点创建，忽略关系提取**
- **没有从非结构化数据中提取实体和关系**
- **ETL管道不完整**

---

## 二、重构目标

### 核心目标
1. **建立知识图谱**：节点之间通过关系连接，形成可查询的知识网络
2. **清晰的架构**：按数据类型组织脚本，分层次处理
3. **完整流程**：数据分类→清洗→提取→处理→归档
4. **文档关联**：文档之间建立引用、引用于、同类等关系

### 本体驱动
- 以本体文件中定义的实体和关系为准
- 从数据源中提取符合本体的实体和关系
- 建立跨域关联

---

## 三、新架构设计

### 3.1 目录结构重组

```
pharmaKG/
├── ontologies/                 # 本体定义（不变）
│   ├── pharma-rd-core.ttl
│   ├── pharma-clinical-core.ttl
│   ├── pharma-sc-regulatory-core.ttl
│   └── pharma-relationship-semantics.ttl
│
├── data/                       # 数据目录（重组）
│   ├── sources/                # 原始数据源（只读）
│   │   ├── regulatory/         # 监管文档
│   │   ├── clinical/           # 临床数据
│   │   ├── rd/                 # R&D数据
│   │   ├── supply_chain/       # 供应链数据
│   │   └── documents/          # 通用文档
│   │
│   ├── processed/              # 已提取/处理的数据
│   │   ├── entities/           # 提取的实体
│   │   ├── relationships/      # 提取的关系
│   │   └── documents/          # 处理后的文档
│   │
│   ├── validated/              # 验证通过的数据
│   │
│   ├── import/                 # 待导入Neo4j的数据
│   │
│   └── archive/                # 已处理归档
│       ├── processed/          # 已处理的源文件
│       └── imported/           # 已导入的批次
│
├── etl/                        # ETL框架（保持）
│   ├── config.py
│   ├── extractors/
│   ├── transformers/
│   ├── loaders/
│   └── pipelines/
│
├── processors/                 # 新增：按数据类型组织的处理器
│   ├── __init__.py
│   ├── base.py                 # 基础处理器
│   ├── regulatory_processor.py # 监管文档处理器
│   ├── clinical_processor.py   # 临床数据处理器
│   ├── rd_processor.py         # R&D数据处理器
│   ├── sc_processor.py         # 供应链数据处理器
│   └── document_processor.py   # 通用文档处理器
│
├── extractors/                 # 新增：实体和关系提取器
│   ├── __init__.py
│   ├── base.py                 # 基础提取器
│   ├── named_entity.py         # 命名实体识别
│   ├── relationship.py         # 关系提取
│   ├── attribute.py            # 属性提取
│   └── chinese_nlp.py          # 中文NLP处理
│
├── mappers/                    # 新增：本体映射器
│   ├── __init__.py
│   ├── entity_mapper.py        # 实体到本体的映射
│   ├── relationship_mapper.py  #关系到本体的映射
│   └── identifier_mapper.py    # 标识符标准化
│
├── pipelines/                  # 新增：数据处理流程
│   ├── __init__.py
│   ├── pipeline_manager.py     # 流程管理器
│   ├── regulatory_pipeline.py  # 监管数据处理流程
│   ├── clinical_pipeline.py    # 临床数据处理流程
│   ├── rd_pipeline.py          # R&D数据处理流程
│   ├── sc_pipeline.py          # 供应链数据处理流程
│   └── document_pipeline.py    # 文档处理流程
│
├── scripts/                    # 脚本重组
│   ├── setup/                  # 安装脚本
│   │   └── install_neo4j.sh
│   │
│   ├── data/                   # 数据获取脚本
│   │   ├── download_sources.py
│   │   └── verify_sources.py
│   │
│   ├── process/                # 数据处理脚本（主要）
│   │   ├── run_pipeline.py     # 运行处理流程
│   │   ├── process_regulatory.py
│   │   ├── process_clinical.py
│   │   ├── process_rd.py
│   │   ├── process_sc.py
│   │   └── process_documents.py
│   │
│   ├── import/                 # 数据导入脚本
│   │   ├── import_to_neo4j.py
│   │   └── create_constraints.py
│   │
│   └── legacy/                 # 旧脚本归档
│       ├── download_*.py
│       ├── process_all_data_sources.py
│       └── deep_scrape_regulatory_documents.py
│
├── deploy/                     # 部署相关
│   ├── neo4j/
│   └── scripts/
│       └── init_*.cypher
│
└── docs/                       # 文档
    ├── REFACTOR_PLAN.md
    ├── DATA_PROCESSING.md
    └── ONTOLOGY_MAPPING.md
```

### 3.2 核心概念定义

#### 实体提取层次
1. **显性实体**：数据中直接存在的实体（如公司名称、药物名称）
2. **隐性实体**：需要从文本中提取的实体（如疾病、靶点）
3. **推断实体**：通过规则推理出的实体（如文档分类）

#### 关系类型
1. **结构关系**：文档本身的引用关系（CITES, REFERENCES）
2. **语义关系**：基于内容的语义关系（TREATS, INHIBITS）
3. **关联关系**：实体间的关联（RELATED_TO, ASSOCIATED_WITH）

---

## 四、实现阶段

### 第一阶段：架构重组（Week 1）

#### 1.1 目录重组
```bash
# 创建新目录结构
mkdir -p processors extractors mappers pipelines
mkdir -p data/{sources,processed,validated,import,archive}
mkdir -p scripts/{setup,data,process,import,legacy}
mkdir -p docs

# 移动现有脚本到legacy
mv scripts/download_*.py scripts/legacy/
mv scripts/process_all_data_sources.py scripts/legacy/
mv scripts/deep_scrape_regulatory_documents.py scripts/legacy/
```

#### 1.2 创建基础框架
- `processors/base.py` - 处理器基类
- `extractors/base.py` - 提取器基类
- `mappers/entity_mapper.py` - 实体映射器
- `pipelines/pipeline_manager.py` - 流程管理器

#### 1.3 数据源分类
将 `data/sources/` 中的数据按类型重新组织：
```
data/sources/
├── regulatory/          # 监管文档
│   ├── CDE/
│   ├── FDA/
│   └── guidelines/
├── clinical/            # 临床数据
│   └── transparency_crl/
├── rd/                  # R&D数据
│   └── chembl/
├── documents/           # 通用文档
│   ├── pdfs/
│   └── guidelines/
└── supply_chain/        # 供应链数据
```

### 第二阶段：实体关系提取（Week 2-3）

#### 2.1 命名实体识别（NER）

**需要识别的实体类型**：
- **化学药物**：化合物名称、API、辅料
- **靶点**：蛋白质、基因、受体
- **疾病**：疾病名称、症状、综合征
- **公司**：制药公司、CRO、学术机构
- **监管机构**：FDA、CDE、EMA等
- **文档类型**：指南、法规、标准、指导原则

**实现方案**：
```python
# extractors/named_entity.py
class NamedEntityExtractor:
    """命名实体识别"""

    def extract_entities(self, text: str) -> List[Entity]:
        # 1. 基于规则的关键词匹配
        # 2. 基于词典的实体识别
        # 3. 基于NER模型的提取（可选）
        pass

    def extract_drug_names(self, text: str) -> List[DrugEntity]
    def extract_target_names(self, text: str) -> List[TargetEntity]
    def extract_company_names(self, text: str) -> List[CompanyEntity]
    def extract_diseases(self, text: str) -> List[DiseaseEntity]
```

#### 2.2 关系提取

**需要提取的关系类型**：
1. **文档内部关系**
   - 文档段落之间
   - 章节之间
   - 引用关系

2. **跨文档关系**
   - CITES（引用）
   - SUPERSEDES（替代）
   - COMPLEMENTS（补充）
   - CONTRADICTS（矛盾）

3. **实体关系**
   - Company MANUFACTURES Drug
   - Drug TREATS Disease
   - Drug TARGETS Target
   - RegulatoryAgency APPROVES Drug

**实现方案**：
```python
# extractors/relationship.py
class RelationshipExtractor:
    """关系提取器"""

    def extract_document_relationships(self, doc: Document) -> List[Relationship]:
        # 提取文档之间的引用关系
        pass

    def extract_entity_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
        # 提取实体之间的关系
        pass

    def extract_regulatory_relationships(self, regulatory_doc: Document) -> List[Relationship]:
        # 提取监管关系
        pass
```

#### 2.3 中文NLP处理

**中文文本处理需求**：
- 分词
- 词性标注
- 命名实体识别
- 关键词提取

**实现方案**：
```python
# extractors/chinese_nlp.py
class ChineseTextProcessor:
    """中文文本处理器"""

    def __init__(self):
        # 使用jieba分词
        import jieba
        import jieba.posseg as pseg

    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]
    def segment_sentences(self, text: str) -> List[str]
    def extract_key_phrases(self, text: str) -> List[str]
```

### 第三阶段：数据处理器实现（Week 3-4）

#### 3.1 监管文档处理器

**功能**：
1. 解析CDE/FDA文档
2. 提取监管实体（机构、法规、指南）
3. 建立文档引用关系
4. 映射到RegulatoryDocument本体

**输入**：`data/sources/regulatory/`
**输出**：
- `data/processed/entities/regulatory/`
- `data/processed/relationships/regulatory/`

```python
# processors/regulatory_processor.py
class RegulatoryDocumentProcessor(BaseProcessor):
    """监管文档处理器"""

    def process(self, source_dir: Path) -> ProcessingResult:
        # 1. 扫描源目录
        # 2. 提取文档内容
        # 3. 识别命名实体
        # 4. 提取关系
        # 5. 映射到本体
        # 6. 输出处理结果
        pass

    def extract_references(self, doc: Document) -> List[Reference]
    def map_to_ontology(self, doc: Document) -> RegulatoryDocument
```

#### 3.2 临床数据处理器

**功能**：
1. 解析ClinicalTrials.gov数据
2. 解析FDA CRL数据
3. 提取临床试验实体
4. 建立试验关系

**输入**：`data/sources/clinical/`
**输出**：`data/processed/entities/clinical/`

#### 3.3 R&D数据处理器

**功能**：
1. 解析ChEMBL数据
2. 提取化合物和靶点
3. 建立化合物-靶点关系

**输入**：`data/sources/rd/`
**输出**：`data/processed/entities/rd/`

#### 3.4 文档处理器

**功能**：
1. 处理PDF/Word文档
2. 提取文本和元数据
3. 识别文档类型
4. 建立文档关联

**输入**：`data/sources/documents/`
**输出**：`data/processed/documents/`

### 第四阶段：关系构建（Week 4-5）

#### 4.1 文档关系网络

**关系类型**：
```cypher
// 文档引用关系
(:Document)-[:CITES]->(:Document)
(:Document)-[:REFERENCES]->(:Guideline)
(:Document)-[:SUPERSEDES]->(:Document)
(:Document)-[:COMPLEMENTS]->(:Document)

// 文档-实体关系
(:Document)-[:MENTIONS]->(:Company)
(:Document)-[:DISCUSSES]->(:Drug)
(:Document)-[:COVERS]->(:Disease)
(:Document)-[:ISSUED_BY]->(:RegulatoryAgency)
```

#### 4.2 实体关系网络

**关系类型**：
```cypher
// R&D关系
(:Compound)-[:TARGETS]->(:Target)
(:Compound)-[:TREATS]->(:Disease)
(:Target)-[:ASSOCIATED_WITH]->(:Disease)

// 临床关系
(:ClinicalTrial)-[:TESTS]->(:Drug)
(:ClinicalTrial)-[:ENROLLS]->(:Patient)
(:Drug)-[:HAS_ADVERSE_EVENT]->(:AdverseEvent)

// 监管关系
(:Company)-[:SUBMITTED]->(:RegulatorySubmission)
(:RegulatorySubmission)-[:LEADS_TO]->(:RegulatoryAction)
(:RegulatoryAction)-[:AFFECTS]->(:Drug)

// 供应链关系
(:Company)-[:MANUFACTURES]->(:Drug)
(:Supplier)-[:SUPPLIES_TO]->(:Company)
(:Drug)-[:EXPERIENCES_SHORTAGE]->(:DrugShortage)
```

#### 4.3 跨域关系

```cypher
// R&D - 临床
(:Compound)-[:TESTED_IN]->(:ClinicalTrial)

// 临床 - 监管
(:ClinicalTrial)-[:HAS_SUBMISSION]->(:RegulatorySubmission)

// R&D - 供应链
(:Compound)-[:MANUFACTURED_BY]->(:Company)

// 供应链 - 监管
(:Company)-[:INSPECTED_BY]->(:RegulatoryAgency)
```

### 第五阶段：数据导入与验证（Week 5-6）

#### 5.1 批量导入

**导入流程**：
1. 从 `data/validated/` 读取数据
2. 创建节点（按本体类型）
3. 创建关系
4. 验证导入结果
5. 归档已处理数据

**脚本**：
```python
# scripts/import/import_to_neo4j.py
def import_validated_data():
    # 1. 加载验证通过的数据
    # 2. 批量创建节点
    # 3. 批量创建关系
    # 4. 验证数据完整性
    # 5. 归档源文件
    pass
```

#### 5.2 数据验证

**验证规则**（基于SHACL）：
1. 必填属性检查
2. 标识符唯一性
3. 关系基数约束
4. 值域约束

**实现**：
```python
# etl/quality/validators.py
class DataValidator:
    def validate_entity(self, entity: Entity) -> ValidationResult
    def validate_relationship(self, rel: Relationship) -> ValidationResult
    def validate_batch(self, batch: List[Entity]) -> ValidationResult
```

### 第六阶段：优化与文档（Week 6-7）

#### 6.1 性能优化
- 批量处理优化
- 索引优化
- 查询优化

#### 6.2 文档完善
- API文档
- 使用手册
- 贡献指南

---

## 五、关键技术决策

### 5.1 NLP工具选择

**中文处理**：
- **分词**：jieba（轻量，准确）
- **关键词提取**：jieba.analyse.extract_tags
- **NER**：可选使用HanLP/spacy

**英文处理**：
- **NER**：spaCy（医学模型：en_core_sci_md）
- **关系提取**：基于规则+模型

### 5.2 实体识别策略

**分层识别**：
1. **词典匹配**（优先）：快、准确
   - 药物词典：DrugBank、ChEMBL
   - 公司词典：FDA注册公司
   - 疾病词典：ICD-10、MeSH

2. **规则提取**（次优）：
   - 正则表达式
   - 模式匹配

3. **模型预测**（补充）：
   - 仅处理复杂场景

### 5.3 关系抽取策略

**文档关系**：
- 引用检测：基于文档ID、标题匹配
- 引用解析：提取"引用"、"参见"等关键词

**实体关系**：
- 模板匹配：定义关系抽取模板
- 依存句法：解析主谓宾结构
- 知识推理：基于已知关系推理

### 5.4 数据流转设计

```
[原始数据] → [分类] → [清洗] → [提取] → [验证] → [导入] → [归档]
    ↓          ↓         ↓         ↓         ↓         ↓         ↓
sources/   classify/  clean/   extract/  validate/ import/  archive/
            raw/     cleaned/ entities/ valid/   neo4j/   processed/
                              relationships/
```

---

## 六、实施计划

### Week 1: 架构重组
- [ ] 创建新目录结构
- [ ] 实现基础框架（base classes）
- [ ] 数据源分类整理
- [ ] 旧脚本归档

### Week 2: 实体提取
- [ ] 实现命名实体识别（NER）
- [ ] 创建实体词典
- [ ] 实现中文NLP处理
- [ ] 实体到本体映射

### Week 3: 关系提取
- [ ] 实现文档关系提取
- [ ] 实现实体关系提取
- [ ] 创建关系抽取模板
- [ ] 关系到本体映射

### Week 4: 处理器实现
- [ ] 监管文档处理器
- [ ] 临床数据处理器
- [ ] R&D数据处理器
- [ ] 文档处理器

### Week 5: 关系构建
- [ ] 构建文档关系网络
- [ ] 构建实体关系网络
- [ ] 建立跨域关系
- [ ] 关系验证

### Week 6: 导入与验证
- [ ] 批量导入实现
- [ ] 数据验证框架
- [ ] 导入结果验证
- [ ] 数据归档流程

### Week 7: 优化与文档
- [ ] 性能优化
- [ ] 文档完善
- [ ] 测试覆盖
- [ ] 发布准备

---

## 七、成功指标

### 数据质量指标
- [ ] 90%以上的节点有关系连接
- [ ] 实体识别准确率>85%
- [ ] 关系抽取准确率>80%
- [ ] 数据完整性100%（必填属性）

### 知识图谱指标
- [ ] 至少3种跨域关系
- [ ] 最短路径平均长度<3
- [ ] 可回答多跳查询

### 工程指标
- [ ] 代码复用率>70%
- [ ] 测试覆盖率>60%
- [ ] 文档完整性100%

---

## 八、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| NLP准确率不足 | 关系质量低 | 多方法融合，人工校验 |
| 数据量过大 | 处理慢 | 批量处理，并行化 |
| 本体不匹配 | 映射失败 | 本体扩展，映射规则 |
| 资源限制 | 无法完成 | 分阶段实施，优先核心 |

---

**文档版本**: v1.0
**创建日期**: 2026-02-07
**最后更新**: 2026-02-07
**状态**: 待评审
